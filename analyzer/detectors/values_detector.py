"""
Values Detector - Simplified Implementation

Detects Connascence of Values violations (duplicate literals, magic numbers).
Simplified to eliminate broken API dependencies while maintaining core functionality.
"""

import ast
from collections import defaultdict
from typing import Dict, List

from analyzer.utils.ast_utils import ASTUtils
from analyzer.utils.violation_factory import ViolationFactory
from utils.types import ConnascenceViolation

from .base import DetectorBase


class ValuesDetector(DetectorBase):
    """
    Detects value-based coupling and shared constant dependencies.
    Simplified implementation focusing on duplicate literals and magic numbers.
    """

    SUPPORTED_EXTENSIONS = [".py"]

    def __init__(self, file_path: str, source_lines: List[str]):
        super().__init__(file_path, source_lines)

        # Track shared values
        self.string_literals: Dict[str, List[ast.AST]] = defaultdict(list)
        self.numeric_literals: Dict[str, List[ast.AST]] = defaultdict(list)

        # Common exclusions
        self.excluded_strings = {"", " ", "\n", "\t", "True", "False", "None"}
        self.excluded_numbers = {0, 1, -1, 2, 10, 100, 1000}

    def detect_violations(self, tree: ast.AST) -> List[ConnascenceViolation]:
        """
        Detect value coupling violations in the AST tree.

        Args:
            tree: AST tree to analyze

        Returns:
            List of ConnascenceViolation objects
        """
        self.violations.clear()

        # Reset tracked literals for each analysis run to avoid cross-file leakage
        # when detectors are pooled and reused across files.
        self.string_literals.clear()
        self.numeric_literals.clear()

        # Find all Constant nodes (Python 3.8+ unified constant handling)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant):
                self._track_constant(node)

        # Check for duplicate literals (min 3 occurrences)
        self._check_duplicate_literals()

        return self.violations

    def _track_constant(self, node: ast.Constant) -> None:
        """Track constant literals for duplication detection."""
        value = node.value

        # Track strings
        if isinstance(value, str):
            if value not in self.excluded_strings and len(value) > 1:
                self.string_literals[value].append(node)

        # Track numbers
        elif isinstance(value, (int, float)) and value not in self.excluded_numbers:
            value_str = str(value)
            self.numeric_literals[value_str].append(node)

    def _check_duplicate_literals(self) -> None:
        """Check for duplicate literals (minimum 3 occurrences)."""
        min_occurrences = 3

        # Check string literals
        for literal_value, nodes in self.string_literals.items():
            if len(nodes) >= min_occurrences:
                self._create_duplicate_literal_violation(nodes[0], literal_value, "string", len(nodes))

        # Check numeric literals
        for literal_value, nodes in self.numeric_literals.items():
            if len(nodes) >= min_occurrences:
                self._create_duplicate_literal_violation(nodes[0], literal_value, "numeric", len(nodes))

    def _create_duplicate_literal_violation(self, node: ast.AST, value: str, value_type: str, usage_count: int) -> None:
        """Create violation for duplicate literal."""
        severity = "medium" if usage_count >= 5 else "low"
        location = ASTUtils.get_node_location(node, self.file_path)
        code_snippet = ASTUtils.extract_code_snippet(self.source_lines, node)

        violation = ViolationFactory.create_violation(
            violation_type="CoV",
            severity=severity,
            location=location,
            description=f"Duplicate {value_type} literal '{value}' used {usage_count} times",
            recommendation=f"Extract '{value}' to a named constant to reduce value coupling",
            code_snippet=code_snippet,
            context={
                "violation_type": "duplicate_literal",
                "value": value,
                "value_type": value_type,
                "usage_count": usage_count,
            },
        )
        self.violations.append(violation)
