"""
Timing Detector

Detects Connascence of Timing violations - sleep-based timing dependencies and related patterns.
"""

import ast
from typing import List

from utils.types import ConnascenceViolation

from .base import DetectorBase


class TimingDetector(DetectorBase):
    """Detects timing-based coupling and sleep dependencies."""

    SUPPORTED_EXTENSIONS = [".py"]

    def detect_violations(self, tree: ast.AST) -> List[ConnascenceViolation]:
        """
        Detect timing violations in the AST tree.
        NASA Rule 5 compliant: Added input validation assertions.

        Args:
            tree: AST tree to analyze

        Returns:
            List of timing-related violations
        """
        # NASA Rule 5: Input validation assertions
        assert tree is not None, "AST tree cannot be None"
        assert isinstance(tree, ast.AST), "Input must be valid AST object"

        self.violations.clear()

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                self._analyze_call(node)

        # NASA Rule 7: Validate return value
        assert isinstance(self.violations, list), "violations must be a list"
        return self.violations

    def _analyze_call(self, node: ast.Call) -> None:
        """Analyze function calls for timing-related patterns."""
        # NASA Rule 5: Input validation assertions
        assert node is not None, "Call node cannot be None"
        assert isinstance(node, ast.Call), "Node must be a function call"

        # NASA Rule 1: Use guard clauses to avoid nesting
        if self._is_sleep_call(node):
            self._create_sleep_violation(node)
            return

        if self._is_timing_related_call(node):
            self._create_timing_violation(node)

    def _is_sleep_call(self, node: ast.Call) -> bool:
        """Check if this is a sleep() call."""
        # Direct sleep() call
        if isinstance(node.func, ast.Name) and node.func.id == "sleep":
            return True

        # Module.sleep() call (time.sleep, asyncio.sleep, etc.)
        return bool(isinstance(node.func, ast.Attribute) and node.func.attr == "sleep")

    def _is_timing_related_call(self, node: ast.Call) -> bool:
        """Check if this is a timing-related call that might cause coupling."""
        timing_functions = ["wait", "delay", "pause", "timeout", "poll", "retry"]

        # Direct function calls
        if isinstance(node.func, ast.Name) and node.func.id in timing_functions:
            return True

        # Attribute calls
        return bool(isinstance(node.func, ast.Attribute) and node.func.attr in timing_functions)

    def _create_sleep_violation(self, node: ast.Call) -> None:
        """Create violation for sleep() calls."""
        self.violations.append(
            ConnascenceViolation(
                type="connascence_of_timing",
                severity="medium",
                file_path=self.file_path,
                line_number=node.lineno,
                column=node.col_offset,
                description="Sleep-based timing dependency detected",
                recommendation="Use proper synchronization primitives, events, or async patterns",
                code_snippet=self.get_code_snippet(node),
                context={"call_type": "sleep", "function_name": self._get_function_name(node)},
            )
        )

    def _create_timing_violation(self, node: ast.Call) -> None:
        """Create violation for other timing-related calls."""
        function_name = self._get_function_name(node)

        self.violations.append(
            ConnascenceViolation(
                type="connascence_of_timing",
                severity="low",
                file_path=self.file_path,
                line_number=node.lineno,
                column=node.col_offset,
                description=f"Timing-related call '{function_name}' may create temporal coupling",
                recommendation="Consider event-driven patterns or explicit coordination mechanisms",
                code_snippet=self.get_code_snippet(node),
                context={"call_type": "timing_related", "function_name": function_name},
            )
        )

    def _get_function_name(self, node: ast.Call) -> str:
        """Extract the function name being called."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        else:
            return "unknown"
