#!/usr/bin/env python3
"""Lightweight clarity analyzer for thin helpers and call chains."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path
from typing import Dict, List, Tuple


class ClarityIssue:
    def __init__(self, issue_type: str, message: str, file_path: Path, line_number: int):
        self.issue_type = issue_type
        self.message = message
        self.file_path = file_path
        self.line_number = line_number

    def __str__(self) -> str:  # pragma: no cover - for pretty printing only
        return f"{self.issue_type}: {self.message} ({self.file_path}:{self.line_number})"


def _gather_python_files(target: Path) -> List[Path]:
    if target.is_file() and target.suffix == ".py":
        return [target]
    return sorted(target.rglob("*.py"))


def _find_thin_helpers(tree: ast.AST, file_path: Path) -> List[ClarityIssue]:
    issues: List[ClarityIssue] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            body = [stmt for stmt in node.body if not isinstance(stmt, ast.Pass)]
            if len(body) == 1 and isinstance(body[0], ast.Return):
                ret_expr = body[0].value
                if isinstance(ret_expr, (ast.BinOp, ast.Call, ast.Attribute, ast.Name)):
                    issues.append(
                        ClarityIssue(
                            "thin_helper",
                            f"Thin helper '{node.name}' simply forwards a call or expression",
                            file_path,
                            node.lineno,
                        )
                    )
    return issues


def _build_call_graph(tree: ast.AST) -> Dict[str, List[str]]:
    graph: Dict[str, List[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            callees: List[str] = []
            for stmt in node.body:
                if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Call):
                    if isinstance(stmt.value.func, ast.Name):
                        callees.append(stmt.value.func.id)
            if callees:
                graph[node.name] = callees
    return graph


def _longest_chain(graph: Dict[str, List[str]]) -> Tuple[int, List[str]]:
    longest: Tuple[int, List[str]] = (0, [])

    def dfs(node: str, visited: List[str]):
        nonlocal longest
        if node in visited:
            return
        path = visited + [node]
        if len(path) > longest[0]:
            longest = (len(path), path)
        for neighbor in graph.get(node, []):
            dfs(neighbor, path)

    for start in graph:
        dfs(start, [])
    return longest


def _find_call_chain_issues(tree: ast.AST, file_path: Path) -> List[ClarityIssue]:
    graph = _build_call_graph(tree)
    length, path = _longest_chain(graph)
    if length >= 5:
        return [
            ClarityIssue(
                "call_chain",
                f"Deep call chain detected ({length} levels): {' -> '.join(path)}",
                file_path,
                1,
            )
        ]
    return []


def _find_cognitive_load(tree: ast.AST, file_path: Path) -> List[ClarityIssue]:
    issues: List[ClarityIssue] = []

    def _depth(node: ast.AST, current_depth: int = 0) -> int:
        depth = current_depth + 1 if isinstance(node, (ast.If, ast.For, ast.While, ast.With)) else current_depth
        max_depth = depth
        for child in ast.iter_child_nodes(node):
            max_depth = max(max_depth, _depth(child, depth))
        return max_depth

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            depth = _depth(node)
            if depth >= 6:
                issues.append(
                    ClarityIssue(
                        "cognitive_load",
                        f"Function '{node.name}' has high cognitive load (nesting depth {depth})",
                        file_path,
                        node.lineno,
                    )
                )
    return issues


def analyze_path(target: Path) -> List[ClarityIssue]:
    issues: List[ClarityIssue] = []
    for py_file in _gather_python_files(target):
        source = py_file.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(py_file))
        issues.extend(_find_thin_helpers(tree, py_file))
        issues.extend(_find_call_chain_issues(tree, py_file))
        issues.extend(_find_cognitive_load(tree, py_file))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Run clarity heuristics")
    parser.add_argument("path", help="Path to analyze")
    args = parser.parse_args()

    target = Path(args.path).resolve()
    if not target.exists():
        print(f"[ERROR] Path not found: {target}")
        return 2

    issues = analyze_path(target)
    thin_helpers = [issue for issue in issues if issue.issue_type == "thin_helper"]
    call_chains = [issue for issue in issues if issue.issue_type == "call_chain"]
    cognitive = [issue for issue in issues if issue.issue_type == "cognitive_load"]

    print("Clarity Analyzer Results")
    print("=" * 40)
    for issue in issues:
        print(f"{issue.issue_type.upper()}: {issue.message} ({issue.file_path}:{issue.line_number})")
    print("-" * 40)
    print(f"Thin helpers detected: {len(thin_helpers)}")
    print(f"Call chain depth alerts: {len(call_chains)}")
    print(f"Cognitive load warnings: {len(cognitive)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
