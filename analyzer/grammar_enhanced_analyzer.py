# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors
"""
Grammar Enhanced Analyzer Module

Provides grammar-based analysis for detecting connascence violations
using formal grammar patterns and rules.

This module wraps the formal_grammar module and provides additional
grammar-based detection capabilities.
"""

import ast
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

# Import from existing formal_grammar module
try:
    from .formal_grammar import MagicLiteralDetector
except ImportError:
    MagicLiteralDetector = None


@dataclass
class GrammarPattern:
    """Represents a grammar pattern for detection."""

    name: str
    pattern_type: str  # "structural", "semantic", "naming"
    description: str
    severity: str = "medium"


@dataclass
class GrammarViolation:
    """Represents a grammar-based violation."""

    type: str
    severity: str
    file_path: str
    line_number: int
    column: int
    description: str
    pattern: str
    recommendation: str = ""


class GrammarEnhancedAnalyzer:
    """
    Analyzer that uses grammar patterns for detection.

    Detects violations based on:
    - Naming conventions
    - Structural patterns
    - Semantic patterns
    - Code organization rules
    """

    # Default patterns for detection
    DEFAULT_PATTERNS = [
        GrammarPattern(
            name="snake_case_function",
            pattern_type="naming",
            description="Function names should use snake_case",
        ),
        GrammarPattern(
            name="PascalCase_class",
            pattern_type="naming",
            description="Class names should use PascalCase",
        ),
        GrammarPattern(
            name="UPPER_CASE_constant",
            pattern_type="naming",
            description="Module-level constants should use UPPER_CASE",
        ),
        GrammarPattern(
            name="single_responsibility",
            pattern_type="structural",
            description="Functions should have a single responsibility",
            severity="high",
        ),
    ]

    def __init__(self, patterns: Optional[List[GrammarPattern]] = None):
        self.patterns = patterns or self.DEFAULT_PATTERNS
        self.violations: List[GrammarViolation] = []
        self._magic_detector = MagicLiteralDetector() if MagicLiteralDetector else None

    def analyze_file(self, file_path: str) -> List[GrammarViolation]:
        """Analyze a file for grammar-based violations."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
            return self.analyze_source(source, file_path)
        except Exception:
            return []

    def analyze_source(self, source: str, file_path: str = "") -> List[GrammarViolation]:
        """Analyze source code for grammar-based violations."""
        self.violations = []

        try:
            tree = ast.parse(source)
            self._check_naming_conventions(tree, file_path)
            self._check_structural_patterns(tree, file_path)

            # Use formal grammar magic literal detection if available
            if self._magic_detector:
                magic_violations = self._magic_detector.detect(tree)
                for v in magic_violations:
                    self.violations.append(
                        GrammarViolation(
                            type="MagicLiteral",
                            severity="medium",
                            file_path=file_path,
                            line_number=v.get("line", 0),
                            column=v.get("column", 0),
                            description=v.get("description", "Magic literal detected"),
                            pattern="magic_literal",
                            recommendation="Extract to named constant",
                        )
                    )

        except SyntaxError:
            pass

        return self.violations

    def _check_naming_conventions(self, tree: ast.AST, file_path: str):
        """Check naming convention violations."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check snake_case for functions
                if not self._is_snake_case(node.name) and not node.name.startswith("_"):
                    self.violations.append(
                        GrammarViolation(
                            type="NamingConvention",
                            severity="low",
                            file_path=file_path,
                            line_number=node.lineno,
                            column=node.col_offset,
                            description=f"Function '{node.name}' should use snake_case",
                            pattern="snake_case_function",
                            recommendation="Rename to use snake_case (e.g., my_function)",
                        )
                    )

            elif isinstance(node, ast.ClassDef):
                # Check PascalCase for classes
                if not self._is_pascal_case(node.name):
                    self.violations.append(
                        GrammarViolation(
                            type="NamingConvention",
                            severity="low",
                            file_path=file_path,
                            line_number=node.lineno,
                            column=node.col_offset,
                            description=f"Class '{node.name}' should use PascalCase",
                            pattern="PascalCase_class",
                            recommendation="Rename to use PascalCase (e.g., MyClass)",
                        )
                    )

    def _check_structural_patterns(self, tree: ast.AST, file_path: str):
        """Check structural pattern violations."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check for functions that are too long
                func_lines = getattr(node, "end_lineno", node.lineno) - node.lineno
                if func_lines > 50:
                    self.violations.append(
                        GrammarViolation(
                            type="StructuralPattern",
                            severity="medium",
                            file_path=file_path,
                            line_number=node.lineno,
                            column=node.col_offset,
                            description=f"Function '{node.name}' is {func_lines} lines (recommended max: 50)",
                            pattern="single_responsibility",
                            recommendation="Consider breaking into smaller functions",
                        )
                    )

                # Check for deeply nested code
                max_depth = self._calculate_nesting_depth(node)
                if max_depth > 4:
                    self.violations.append(
                        GrammarViolation(
                            type="StructuralPattern",
                            severity="medium",
                            file_path=file_path,
                            line_number=node.lineno,
                            column=node.col_offset,
                            description=f"Function '{node.name}' has nesting depth {max_depth} (max: 4)",
                            pattern="nesting_depth",
                            recommendation="Refactor to reduce nesting",
                        )
                    )

    def _is_snake_case(self, name: str) -> bool:
        """Check if a name follows snake_case convention."""
        if name.startswith("_"):
            name = name.lstrip("_")
        return name.islower() or "_" in name

    def _is_pascal_case(self, name: str) -> bool:
        """Check if a name follows PascalCase convention."""
        return name[0].isupper() and "_" not in name

    def _calculate_nesting_depth(self, node: ast.AST) -> int:
        """Calculate maximum nesting depth in a node."""
        max_depth = 0
        current_depth = 0

        def visit(n: ast.AST, depth: int):
            nonlocal max_depth
            if isinstance(n, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                depth += 1
                max_depth = max(max_depth, depth)
            for child in ast.iter_child_nodes(n):
                visit(child, depth)

        visit(node, 0)
        return max_depth


def analyze_with_grammar(source_or_path: str, is_file: bool = True) -> List[GrammarViolation]:
    """
    Convenience function for grammar-based analysis.

    Args:
        source_or_path: File path or source code string
        is_file: If True, treat as file path; if False, treat as source code

    Returns:
        List of grammar violations
    """
    analyzer = GrammarEnhancedAnalyzer()
    if is_file:
        return analyzer.analyze_file(source_or_path)
    return analyzer.analyze_source(source_or_path)


__all__ = [
    "GrammarEnhancedAnalyzer",
    "GrammarPattern",
    "GrammarViolation",
    "analyze_with_grammar",
]
