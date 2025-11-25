# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors
"""
AST Visitor Pattern Implementations

Provides base visitor classes and concrete implementations for
traversing Python AST nodes during connascence analysis.
"""

import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


@dataclass
class VisitorContext:
    """Context passed to visitors during AST traversal."""

    file_path: str = ""
    source_code: str = ""
    current_class: Optional[str] = None
    current_function: Optional[str] = None
    scope_stack: List[str] = field(default_factory=list)
    findings: List[Dict[str, Any]] = field(default_factory=list)


class BaseConnascenceVisitor(ast.NodeVisitor, ABC):
    """
    Base visitor class for connascence detection.

    Subclasses should implement specific detection logic for
    different types of connascence.
    """

    def __init__(self):
        self.context: Optional[VisitorContext] = None
        self.violations: List[Dict[str, Any]] = []

    def visit_with_context(self, node: ast.AST, context: VisitorContext) -> List[Dict[str, Any]]:
        """Visit AST with provided context and return violations."""
        self.context = context
        self.violations = []
        self.visit(node)
        return self.violations

    @abstractmethod
    def get_violation_type(self) -> str:
        """Return the connascence type this visitor detects."""
        pass

    def add_violation(
        self,
        node: ast.AST,
        description: str,
        severity: str = "medium",
        recommendation: str = "",
    ):
        """Add a violation to the findings list."""
        self.violations.append(
            {
                "type": self.get_violation_type(),
                "severity": severity,
                "line_number": getattr(node, "lineno", 0),
                "column": getattr(node, "col_offset", 0),
                "description": description,
                "recommendation": recommendation,
                "file_path": self.context.file_path if self.context else "",
            }
        )


class MagicLiteralVisitor(BaseConnascenceVisitor):
    """Visitor that detects magic literals (Connascence of Meaning)."""

    ALLOWED_LITERALS = {0, 1, -1, "", True, False, None}

    def get_violation_type(self) -> str:
        return "CoM"

    def visit_Constant(self, node: ast.Constant):
        """Check for magic literal constants."""
        if node.value not in self.ALLOWED_LITERALS:
            if isinstance(node.value, (int, float)) and abs(node.value) > 1:
                self.add_violation(
                    node,
                    f"Magic literal '{node.value}' should be extracted to a named constant",
                    severity="medium",
                    recommendation="Extract to a named constant with descriptive name",
                )
        self.generic_visit(node)


class ParameterPositionVisitor(BaseConnascenceVisitor):
    """Visitor that detects position coupling (Connascence of Position)."""

    MAX_POSITIONAL_PARAMS = 4

    def get_violation_type(self) -> str:
        return "CoP"

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Check function parameter count."""
        positional_params = [
            arg
            for arg in node.args.args
            if arg.arg not in ("self", "cls")
        ]
        if len(positional_params) > self.MAX_POSITIONAL_PARAMS:
            self.add_violation(
                node,
                f"Function '{node.name}' has {len(positional_params)} positional parameters (max: {self.MAX_POSITIONAL_PARAMS})",
                severity="high",
                recommendation="Use keyword-only arguments or a configuration object",
            )
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef


class GodObjectVisitor(BaseConnascenceVisitor):
    """Visitor that detects god objects (excessive class complexity)."""

    MAX_METHODS = 20
    MAX_ATTRIBUTES = 15

    def get_violation_type(self) -> str:
        return "CoA"

    def visit_ClassDef(self, node: ast.ClassDef):
        """Check class complexity."""
        methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        if len(methods) > self.MAX_METHODS:
            self.add_violation(
                node,
                f"Class '{node.name}' has {len(methods)} methods (max: {self.MAX_METHODS})",
                severity="critical",
                recommendation="Split into smaller, focused classes",
            )
        self.generic_visit(node)


class ComplexityVisitor(BaseConnascenceVisitor):
    """Visitor that detects high cyclomatic complexity."""

    MAX_COMPLEXITY = 10

    def get_violation_type(self) -> str:
        return "CoA"

    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a node."""
        complexity = 1  # Base complexity
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Check function complexity."""
        complexity = self._calculate_complexity(node)
        if complexity > self.MAX_COMPLEXITY:
            self.add_violation(
                node,
                f"Function '{node.name}' has cyclomatic complexity {complexity} (max: {self.MAX_COMPLEXITY})",
                severity="high",
                recommendation="Refactor to reduce branching and nesting",
            )
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef


class CompositeVisitor(ast.NodeVisitor):
    """Visitor that combines multiple connascence visitors."""

    def __init__(self, visitors: Optional[List[BaseConnascenceVisitor]] = None):
        self.visitors = visitors or [
            MagicLiteralVisitor(),
            ParameterPositionVisitor(),
            GodObjectVisitor(),
            ComplexityVisitor(),
        ]

    def visit_with_context(self, node: ast.AST, context: VisitorContext) -> List[Dict[str, Any]]:
        """Run all visitors and collect violations."""
        all_violations = []
        for visitor in self.visitors:
            violations = visitor.visit_with_context(node, context)
            all_violations.extend(violations)
        return all_violations


# Convenience functions
def analyze_ast(tree: ast.AST, file_path: str = "", source_code: str = "") -> List[Dict[str, Any]]:
    """Analyze an AST tree for connascence violations."""
    context = VisitorContext(file_path=file_path, source_code=source_code)
    composite = CompositeVisitor()
    return composite.visit_with_context(tree, context)


def analyze_code(source_code: str, file_path: str = "") -> List[Dict[str, Any]]:
    """Analyze source code string for connascence violations."""
    tree = ast.parse(source_code)
    return analyze_ast(tree, file_path, source_code)


__all__ = [
    "BaseConnascenceVisitor",
    "CompositeVisitor",
    "ComplexityVisitor",
    "GodObjectVisitor",
    "MagicLiteralVisitor",
    "ParameterPositionVisitor",
    "VisitorContext",
    "analyze_ast",
    "analyze_code",
]
