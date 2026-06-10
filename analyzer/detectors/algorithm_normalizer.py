"""Body-aware normalization for Connascence-of-Algorithm detection.

Fixes issue #37: the previous normalization reduced a function to its
top-level statement TYPE skeleton ("if|assign|if|return"), so any two
functions sharing a shape hashed identically regardless of logic. That
flagged registry/dispatch handlers -- uniform shape with DISTINCT logic,
the goal state of dispatch design -- as duplicate algorithms, while the
true target of this detector is copy-paste duplication.

This normalization hashes the FULL AST of the function body with local
identifiers abstracted: parameters and locally-assigned names become
positional placeholders (v0, v1, ...) numbered by first occurrence, so
copy-paste-with-renamed-variables still hashes equal. Everything that
carries the algorithm's identity is preserved verbatim: attribute names
(method calls), non-local/builtin call targets, constant values, operators,
and control structure. Same-shape distinct-logic functions therefore hash
differently.

The function's docstring is excluded so documentation does not make
otherwise-identical algorithms look distinct.
"""

from __future__ import annotations

import ast
import copy
from typing import Dict


def _is_docstring(stmt: ast.stmt) -> bool:
    return (
        isinstance(stmt, ast.Expr)
        and isinstance(stmt.value, ast.Constant)
        and isinstance(stmt.value.value, str)
    )


class _LocalNameCollector(ast.NodeVisitor):
    """Collect names bound locally: assignment targets, loop targets,
    with-as targets, comprehension targets, except names, inner defs."""

    def __init__(self, mapping: Dict[str, str]):
        self._mapping = mapping

    def _bind(self, name: str) -> None:
        if name not in self._mapping:
            self._mapping[name] = f"v{len(self._mapping)}"

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self._bind(node.id)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name:
            self._bind(node.name)
        self.generic_visit(node)

    def visit_arg(self, node: ast.arg) -> None:
        # Lambda / inner-def parameters inside the body.
        self._bind(node.arg)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._bind(node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._bind(node.name)
        self.generic_visit(node)


class _LocalNameRenamer(ast.NodeTransformer):
    """Rewrite locally-bound identifiers to their placeholders. Names not
    in the mapping (globals, builtins, imports) are preserved -- they are
    part of the algorithm's identity."""

    def __init__(self, mapping: Dict[str, str]):
        self._mapping = mapping

    def visit_Name(self, node: ast.Name) -> ast.Name:
        if node.id in self._mapping:
            node.id = self._mapping[node.id]
        return self.generic_visit(node)

    def visit_arg(self, node: ast.arg) -> ast.arg:
        if node.arg in self._mapping:
            node.arg = self._mapping[node.arg]
        node.annotation = None  # annotations are not algorithm
        return self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        if node.name in self._mapping:
            node.name = self._mapping[node.name]
        node.returns = None
        return self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> ast.AST:
        if node.name and node.name in self._mapping:
            node.name = self._mapping[node.name]
        return self.generic_visit(node)


def normalized_algorithm_hash(node: ast.FunctionDef) -> str:
    """Return a hash string for the function body that is stable under
    local-variable renaming but sensitive to the actual logic."""
    assert isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)), (
        "node must be a function definition"
    )

    mapping: Dict[str, str] = {}

    # Parameters bind first so identical bodies with reordered locals
    # still map consistently.
    args = node.args
    for arg in (
        list(getattr(args, "posonlyargs", []))
        + list(args.args)
        + list(args.kwonlyargs)
    ):
        if arg.arg not in mapping:
            mapping[arg.arg] = f"v{len(mapping)}"
    for special in (args.vararg, args.kwarg):
        if special is not None and special.arg not in mapping:
            mapping[special.arg] = f"v{len(mapping)}"

    body = [stmt for stmt in node.body if not _is_docstring(stmt)]

    collector = _LocalNameCollector(mapping)
    for stmt in body:
        collector.visit(stmt)

    renamer = _LocalNameRenamer(mapping)
    parts = []
    for stmt in body:
        clone = copy.deepcopy(stmt)  # never mutate the shared tree
        parts.append(ast.dump(renamer.visit(clone), annotate_fields=False))
    return "|".join(parts)
