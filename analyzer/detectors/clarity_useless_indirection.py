"""
Useless Indirection Detector - Code Clarity Detector

Detects unnecessary indirection patterns that add complexity without value.

NASA Rule 4 Compliant: All functions under 60 lines
NASA Rule 5 Compliant: Input assertions
"""

import ast
from pathlib import Path
from typing import List, Dict, Any, Set

from analyzer.clarity_linter.base import BaseClarityDetector
from analyzer.clarity_linter.models import ClarityViolation


class UselessIndirectionDetector(BaseClarityDetector):
    """
    Detects unnecessary indirection patterns.

    Patterns detected:
    - Pass-through methods that just call another method
    - Wrapper functions that add no value
    - Unnecessary abstraction layers
    - Delegate methods with no transformation

    NASA Rule 4 Compliant: All methods under 60 lines
    NASA Rule 5 Compliant: Input assertions
    """

    rule_id = "CLARITY_USELESS_INDIRECTION"
    rule_name = "Useless Indirection"
    default_severity = "medium"

    # Method name patterns that are intentional pass-through
    INTENTIONAL_PATTERNS: Set[str] = {
        "delegate", "forward", "proxy", "dispatch",
        "handle", "process", "execute", "run",
    }

    def detect(
        self,
        tree: ast.Module,
        file_path: Path
    ) -> List[ClarityViolation]:
        """
        Detect useless indirection patterns in AST tree.

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
        self._analyze_classes(tree, file_path, violations)
        self._analyze_functions(tree, file_path, violations)
        return violations

    def _analyze_classes(
        self,
        tree: ast.Module,
        file_path: Path,
        violations: List[ClarityViolation]
    ) -> None:
        """
        Analyze classes for useless indirection.

        NASA Rule 4: Function under 60 lines
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self._check_class_methods(node, file_path, violations)

    def _analyze_functions(
        self,
        tree: ast.Module,
        file_path: Path,
        violations: List[ClarityViolation]
    ) -> None:
        """
        Analyze module-level functions for useless indirection.

        NASA Rule 4: Function under 60 lines
        """
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if self._is_useless_wrapper(node):
                    violation = self._create_wrapper_violation(node, file_path)
                    violations.append(violation)

    def _check_class_methods(
        self,
        class_def: ast.ClassDef,
        file_path: Path,
        violations: List[ClarityViolation]
    ) -> None:
        """
        Check class methods for useless indirection.

        NASA Rule 4: Function under 60 lines
        """
        for node in class_def.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if self._is_passthrough_method(node):
                    violation = self._create_passthrough_violation(
                        node, file_path, class_def.name
                    )
                    violations.append(violation)

    def _is_passthrough_method(self, func: ast.FunctionDef) -> bool:
        """
        Check if method is a pass-through to another method.

        NASA Rule 4: Function under 60 lines
        """
        # Skip if intentional pattern
        if self._is_intentional_pattern(func.name):
            return False

        # Skip magic methods and properties
        if func.name.startswith("_"):
            return False

        # Get body without docstring
        body = self._get_body_without_docstring(func)
        if len(body) != 1:
            return False

        stmt = body[0]
        if isinstance(stmt, ast.Return) and stmt.value:
            return self._is_self_method_call(stmt.value, func)
        return False

    def _is_self_method_call(self, node: ast.expr, func: ast.FunctionDef) -> bool:
        """
        Check if expression is a self method call with same args.

        NASA Rule 4: Function under 60 lines
        """
        if not isinstance(node, ast.Call):
            return False

        # Check if calling self.method
        if not isinstance(node.func, ast.Attribute):
            return False

        if not isinstance(node.func.value, ast.Name):
            return False

        if node.func.value.id != "self":
            return False

        # Check if passing same arguments
        return self._has_same_arguments(node, func)

    def _has_same_arguments(self, call: ast.Call, func: ast.FunctionDef) -> bool:
        """
        Check if call uses same arguments as function definition.

        NASA Rule 4: Function under 60 lines
        """
        # Get function args (skip self)
        func_args = [arg.arg for arg in func.args.args[1:]]

        # Get call args
        call_arg_names = []
        for arg in call.args:
            if isinstance(arg, ast.Name):
                call_arg_names.append(arg.id)
            else:
                return False

        return func_args == call_arg_names

    def _is_useless_wrapper(self, func: ast.FunctionDef) -> bool:
        """
        Check if function is a useless wrapper.

        NASA Rule 4: Function under 60 lines
        """
        if self._is_intentional_pattern(func.name):
            return False

        body = self._get_body_without_docstring(func)
        if len(body) != 1:
            return False

        stmt = body[0]
        if isinstance(stmt, ast.Return) and stmt.value:
            if isinstance(stmt.value, ast.Call):
                return self._is_simple_forwarding(stmt.value, func)
        return False

    def _is_simple_forwarding(self, call: ast.Call, func: ast.FunctionDef) -> bool:
        """
        Check if call simply forwards arguments.

        NASA Rule 4: Function under 60 lines
        """
        # Get function args
        func_args = [arg.arg for arg in func.args.args]

        # Get call args
        for arg in call.args:
            if not isinstance(arg, ast.Name):
                return False
            if arg.id not in func_args:
                return False

        return True

    def _is_intentional_pattern(self, name: str) -> bool:
        """
        Check if name suggests intentional indirection.

        NASA Rule 4: Function under 60 lines
        """
        name_lower = name.lower()
        return any(pattern in name_lower for pattern in self.INTENTIONAL_PATTERNS)

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

    def _create_passthrough_violation(
        self,
        func: ast.FunctionDef,
        file_path: Path,
        class_name: str
    ) -> ClarityViolation:
        """
        Create violation for pass-through method.

        NASA Rule 4: Function under 60 lines
        """
        description = (
            f"Method '{class_name}.{func.name}' is a pass-through that simply "
            f"delegates to another method without transformation."
        )

        recommendation = (
            "Consider removing this indirection and calling the target method "
            "directly, or add meaningful logic to justify the wrapper."
        )

        return self.create_violation(
            file_path=file_path,
            line_number=func.lineno,
            description=description,
            recommendation=recommendation,
            context={
                "class_name": class_name,
                "method_name": func.name,
                "issue_type": "passthrough_method"
            }
        )

    def _create_wrapper_violation(
        self,
        func: ast.FunctionDef,
        file_path: Path
    ) -> ClarityViolation:
        """
        Create violation for useless wrapper function.

        NASA Rule 4: Function under 60 lines
        """
        description = (
            f"Function '{func.name}' is a useless wrapper that simply forwards "
            f"to another function without transformation."
        )

        recommendation = (
            "Either remove this wrapper and call the target function directly, "
            "or add meaningful logic like validation, logging, or error handling."
        )

        return self.create_violation(
            file_path=file_path,
            line_number=func.lineno,
            description=description,
            recommendation=recommendation,
            context={
                "function_name": func.name,
                "issue_type": "useless_wrapper"
            }
        )


__all__ = ['UselessIndirectionDetector']
