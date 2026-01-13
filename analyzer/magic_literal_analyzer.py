# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors
"""
Magic Literal Analyzer Module

Specialized analyzer for detecting magic literals (Connascence of Meaning).
Provides detailed analysis of hardcoded values that should be extracted
to named constants.
"""

import ast
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class MagicLiteralViolation:
    """Represents a magic literal violation."""

    literal_value: Any
    literal_type: str  # "number", "string", "boolean"
    severity: str
    file_path: str
    line_number: int
    column: int
    context: str  # "condition", "assignment", "argument", "return"
    description: str
    suggested_name: str = ""
    recommendation: str = ""


class MagicLiteralAnalyzer:
    """
    Specialized analyzer for detecting magic literals.

    Detects:
    - Magic numbers (excluding 0, 1, -1)
    - Magic strings (excluding empty string)
    - Magic values in conditions
    - Repeated literal values
    """

    # Values that are commonly acceptable
    ALLOWED_NUMBERS = {0, 1, -1, 2, 10, 100}
    ALLOWED_STRINGS = {"", " ", "\n", "\t", ",", ".", ":"}

    # Context severity mapping (higher severity for conditions)
    CONTEXT_SEVERITY = {
        "condition": "high",
        "comparison": "high",
        "assignment": "medium",
        "argument": "medium",
        "return": "low",
        "default": "low",
    }

    def __init__(
        self,
        allowed_numbers: Optional[Set[int]] = None,
        allowed_strings: Optional[Set[str]] = None,
    ):
        self.allowed_numbers = allowed_numbers or self.ALLOWED_NUMBERS
        self.allowed_strings = allowed_strings or self.ALLOWED_STRINGS
        self.violations: List[MagicLiteralViolation] = []
        self._literal_occurrences: Dict[Any, List[Tuple[int, int]]] = {}

    def analyze_file(self, file_path: str) -> List[MagicLiteralViolation]:
        """Analyze a file for magic literal violations."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
            return self.analyze_source(source, file_path)
        except Exception:
            return []

    def analyze_source(self, source: str, file_path: str = "") -> List[MagicLiteralViolation]:
        """Analyze source code for magic literal violations."""
        self.violations = []
        self._literal_occurrences = {}

        try:
            tree = ast.parse(source)
            self._analyze_node(tree, file_path, source)
            self._detect_repeated_literals(file_path)
        except SyntaxError:
            # Intentional no-op: skip files with syntax errors.
            return self.violations

        return self.violations

    def _analyze_node(self, tree: ast.AST, file_path: str, source: str):
        """Walk the AST and detect magic literals."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant):
                self._check_constant(node, file_path, tree)
            elif isinstance(node, ast.Compare):
                self._check_comparison(node, file_path)
            elif isinstance(node, ast.BinOp):
                self._check_binary_op(node, file_path)

    def _check_constant(self, node: ast.Constant, file_path: str, tree: ast.AST):
        """Check if a constant is a magic literal."""
        value = node.value
        context = self._determine_context(node, tree)

        # Track occurrences
        if value not in self._literal_occurrences:
            self._literal_occurrences[value] = []
        self._literal_occurrences[value].append((node.lineno, node.col_offset))

        # Check numbers
        if isinstance(value, (int, float)):
            if value not in self.allowed_numbers:
                severity = self.CONTEXT_SEVERITY.get(context, "medium")
                self.violations.append(
                    MagicLiteralViolation(
                        literal_value=value,
                        literal_type="number",
                        severity=severity,
                        file_path=file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        context=context,
                        description=f"Magic number '{value}' in {context}",
                        suggested_name=self._suggest_name(value, context),
                        recommendation="Extract to a named constant",
                    )
                )

        # Check strings
        elif isinstance(value, str):
            if value and value not in self.allowed_strings:
                # Skip docstrings
                if len(value) > 50:
                    return
                severity = self.CONTEXT_SEVERITY.get(context, "low")
                self.violations.append(
                    MagicLiteralViolation(
                        literal_value=value,
                        literal_type="string",
                        severity=severity,
                        file_path=file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        context=context,
                        description=f"Magic string '{value[:20]}...' in {context}" if len(value) > 20 else f"Magic string '{value}' in {context}",
                        suggested_name=self._suggest_name(value, context),
                        recommendation="Extract to a named constant",
                    )
                )

    def _check_comparison(self, node: ast.Compare, file_path: str):
        """Check comparisons for magic literals in conditions."""
        for comparator in node.comparators:
            if isinstance(comparator, ast.Constant):
                # Already handled in _check_constant with context
                continue

    def _check_binary_op(self, node: ast.BinOp, file_path: str):
        """Check binary operations for magic literals."""
        # Already handled via _check_constant
        return None

    def _determine_context(self, node: ast.Constant, tree: ast.AST) -> str:
        """Determine the context where the literal is used."""
        # Walk parents to find context
        for parent in ast.walk(tree):
            for field, value in ast.iter_fields(parent):
                if value is node or (isinstance(value, list) and node in value):
                    if isinstance(parent, ast.If):
                        return "condition"
                    elif isinstance(parent, ast.Compare):
                        return "comparison"
                    elif isinstance(parent, ast.Assign):
                        return "assignment"
                    elif isinstance(parent, ast.Call):
                        return "argument"
                    elif isinstance(parent, ast.Return):
                        return "return"
        return "default"

    def _detect_repeated_literals(self, file_path: str):
        """Detect literals that appear multiple times."""
        for value, occurrences in self._literal_occurrences.items():
            if len(occurrences) >= 3:
                # Only report if not already a simple value
                if value not in self.allowed_numbers and value not in self.allowed_strings:
                    # Add a summary violation for repeated usage
                    self.violations.append(
                        MagicLiteralViolation(
                            literal_value=value,
                            literal_type="number" if isinstance(value, (int, float)) else "string",
                            severity="high",
                            file_path=file_path,
                            line_number=occurrences[0][0],
                            column=occurrences[0][1],
                            context="repeated",
                            description=f"Literal '{value}' appears {len(occurrences)} times - should be a constant",
                            suggested_name=self._suggest_name(value, "constant"),
                            recommendation=f"Extract to constant - used {len(occurrences)} times",
                        )
                    )

    def _suggest_name(self, value: Any, context: str) -> str:
        """Suggest a constant name for a magic literal."""
        if isinstance(value, (int, float)):
            if value > 1000:
                return "MAX_VALUE"
            elif value < 0:
                return "MIN_VALUE"
            elif context == "condition":
                return "THRESHOLD"
            else:
                return "CONSTANT_VALUE"
        elif isinstance(value, str):
            # Generate name from string content
            name = value.upper().replace(" ", "_").replace("-", "_")[:20]
            return f"{name}_VALUE" if name else "STRING_CONSTANT"
        return "CONSTANT"


def analyze_magic_literals(
    source_or_path: str, is_file: bool = True
) -> List[MagicLiteralViolation]:
    """
    Convenience function to analyze magic literals.

    Args:
        source_or_path: File path or source code string
        is_file: If True, treat as file path; if False, treat as source code

    Returns:
        List of magic literal violations
    """
    analyzer = MagicLiteralAnalyzer()
    if is_file:
        return analyzer.analyze_file(source_or_path)
    return analyzer.analyze_source(source_or_path)


__all__ = [
    "MagicLiteralAnalyzer",
    "MagicLiteralViolation",
    "analyze_magic_literals",
]
