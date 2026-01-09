"""
Thin Helper Detector - Code Clarity Detector

Detects thin helper functions (1-3 lines wrapping other calls with no transformation).

NASA Rule 4 Compliant: All functions under 60 lines
NASA Rule 5 Compliant: Input assertions
"""

import ast
from pathlib import Path
from typing import List, Set

from analyzer.clarity_linter.base import BaseClarityDetector
from analyzer.clarity_linter.models import ClarityViolation


class ThinHelperDetector(BaseClarityDetector):
    """
    Detects thin helper functions that add no value.

    A thin helper is a function that:
    - Has 1-3 lines of code
    - Contains only a return statement
    - Simply wraps another function call
    - Adds no transformation logic

    NASA Rule 4 Compliant: All methods under 60 lines
    NASA Rule 5 Compliant: Input assertions
    """

    rule_id = "CLARITY_THIN_HELPER"
    rule_name = "Thin Helper Function"
    default_severity = "medium"

    # Minimum lines to consider NOT thin (configurable)
    MIN_MEANINGFUL_LINES = 4

    # Patterns that indicate intentional wrappers (not violations)
    WRAPPER_EXEMPTIONS: Set[str] = {
        "__init__",
        "__enter__",
        "__exit__",
        "__str__",
        "__repr__",
        "__hash__",
        "__eq__",
        "__lt__",
        "__gt__",
        "__le__",
        "__ge__",
        "setUp",
        "tearDown",
        "setUpClass",
        "tearDownClass",
    }

    def detect(
        self,
        tree: ast.Module,
        file_path: Path
    ) -> List[ClarityViolation]:
        """
        Detect thin helper functions in AST tree.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation assertions

        Args:
            tree: Parsed AST tree to analyze
            file_path: Path to file being analyzed

        Returns:
            List of clarity violations found
        """
        # NASA Rule 5: Input validation
        assert tree is not None, "tree cannot be None"
        assert isinstance(tree, ast.Module), "tree must be ast.Module"
        assert file_path is not None, "file_path cannot be None"

        violations = []
        self._analyze_functions(tree, file_path, violations)
        return violations

    def _analyze_functions(
        self,
        tree: ast.Module,
        file_path: Path,
        violations: List[ClarityViolation]
    ) -> None:
        """
        Analyze all functions in the AST tree.

        NASA Rule 4: Function under 60 lines
        """
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if self._is_thin_helper(node):
                    violation = self._create_thin_helper_violation(node, file_path)
                    violations.append(violation)

    def _is_thin_helper(self, func: ast.FunctionDef) -> bool:
        """
        Check if function is a thin helper.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation
        """
        # NASA Rule 5: Input validation
        assert func is not None, "func cannot be None"

        # Skip exempted names
        if func.name in self.WRAPPER_EXEMPTIONS:
            return False

        # Skip decorators that might justify thin wrappers
        if self._has_justifying_decorator(func):
            return False

        # Get function body (excluding docstring)
        body = self._get_body_without_docstring(func)

        # Check line count
        if len(body) == 0 or len(body) >= self.MIN_MEANINGFUL_LINES:
            return False

        # Check if it's just a return wrapping a call
        if len(body) == 1:
            stmt = body[0]
            if isinstance(stmt, ast.Return) and stmt.value:
                return self._is_simple_call_wrapper(stmt.value)
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                return self._is_simple_call_wrapper(stmt.value)

        return False

    def _has_justifying_decorator(self, func: ast.FunctionDef) -> bool:
        """
        Check for decorators that justify thin wrappers.

        NASA Rule 4: Function under 60 lines
        """
        justifying_decorators = {
            "property", "staticmethod", "classmethod",
            "abstractmethod", "cached_property", "lru_cache",
            "pytest.fixture", "fixture", "mock.patch", "patch"
        }

        for decorator in func.decorator_list:
            name = self._get_decorator_name(decorator)
            if name in justifying_decorators:
                return True
        return False

    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """
        Extract decorator name from AST node.

        NASA Rule 4: Function under 60 lines
        """
        if isinstance(decorator, ast.Name):
            return decorator.id
        if isinstance(decorator, ast.Attribute):
            return decorator.attr
        if isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        return ""

    def _get_body_without_docstring(self, func: ast.FunctionDef) -> List[ast.stmt]:
        """
        Get function body excluding docstring.

        NASA Rule 4: Function under 60 lines
        """
        body = func.body
        if body and isinstance(body[0], ast.Expr):
            if isinstance(body[0].value, ast.Constant):
                if isinstance(body[0].value.value, str):
                    return body[1:]
        return body

    def _is_simple_call_wrapper(self, node: ast.expr) -> bool:
        """
        Check if expression is a simple function call wrapper.

        NASA Rule 4: Function under 60 lines
        """
        if isinstance(node, ast.Call):
            # Check if arguments are just passed through
            return self._are_args_passthrough(node)
        return False

    def _are_args_passthrough(self, call: ast.Call) -> bool:
        """
        Check if call arguments are simple passthrough.

        NASA Rule 4: Function under 60 lines
        """
        for arg in call.args:
            if not isinstance(arg, (ast.Name, ast.Constant)):
                return False
        for kw in call.keywords:
            if not isinstance(kw.value, (ast.Name, ast.Constant)):
                return False
        return True

    def _create_thin_helper_violation(
        self,
        func: ast.FunctionDef,
        file_path: Path
    ) -> ClarityViolation:
        """
        Create violation for thin helper function.

        NASA Rule 4: Function under 60 lines
        """
        description = (
            f"Function '{func.name}' is a thin helper that simply wraps "
            f"another function call. Consider inlining or adding meaningful logic."
        )

        recommendation = (
            "Either inline this function at call sites, or add meaningful "
            "transformation, validation, or error handling to justify its existence."
        )

        return self.create_violation(
            file_path=file_path,
            line_number=func.lineno,
            description=description,
            recommendation=recommendation,
            context={
                "function_name": func.name,
                "body_lines": len(func.body),
                "issue_type": "thin_helper"
            }
        )


__all__ = ['ThinHelperDetector']
