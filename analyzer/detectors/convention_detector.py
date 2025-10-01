"""
Convention Detector

Detects Connascence of Convention violations - naming conventions, style violations, 
and documentation pattern inconsistencies.
"""

import ast
import re
from typing import List

from utils.types import ConnascenceViolation

from .base import DetectorBase


class ConventionDetector(DetectorBase):
    """Detects convention-based coupling and naming inconsistencies."""

    def __init__(self, file_path: str, source_lines: List[str]):
        super().__init__(file_path, source_lines)

        # Naming convention patterns
        self.snake_case_pattern = re.compile(r"^[a-z_][a-z0-9_]*$")
        self.camel_case_pattern = re.compile(r"^[a-z][a-zA-Z0-9]*$")
        self.pascal_case_pattern = re.compile(r"^[A-Z][a-zA-Z0-9]*$")
        self.constant_pattern = re.compile(r"^[A-Z_][A-Z0-9_]*$")

        # Documentation patterns
        self.docstring_patterns = [
            re.compile(r'""".*?"""', re.DOTALL),
            re.compile(r"'''.*?'''", re.DOTALL),
        ]

    def detect_violations(self, tree: ast.AST) -> List[ConnascenceViolation]:
        """
        Detect convention violations in the AST tree.

        Args:
            tree: AST tree to analyze

        Returns:
            List of convention-related violations
        """
        self.violations.clear()

        # Track naming patterns for consistency analysis
        self.function_names = []
        self.class_names = []
        self.variable_names = []
        self.constant_names = []

        # Walk the AST to collect names and check conventions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self._analyze_function_conventions(node)
            elif isinstance(node, ast.ClassDef):
                self._analyze_class_conventions(node)
            elif isinstance(node, ast.Name):
                self._analyze_variable_conventions(node)
            elif isinstance(node, ast.Assign):
                self._analyze_assignment_conventions(node)

        # Check for inconsistent naming patterns
        self._check_naming_consistency()

        return self.violations

    def _analyze_function_conventions(self, node: ast.FunctionDef) -> None:
        """Analyze function naming and documentation conventions."""
        func_name = node.name
        self.function_names.append(func_name)

        # Check function naming convention (should be snake_case)
        if not self.snake_case_pattern.match(func_name) and not func_name.startswith("_"):
            self._create_naming_violation(
                node, func_name, "function", "Functions should use snake_case naming convention"
            )

        # Check for missing docstrings on non-private functions
        if not func_name.startswith("_") and not self._has_docstring(node):
            # Only flag if function is longer than 5 lines
            if len(node.body) > 5:
                self._create_documentation_violation(
                    node,
                    "Missing docstring for non-trivial function",
                    "Add docstring describing function purpose and parameters",
                )

        # Check for overly abbreviated function names
        if len(func_name) < 3 and func_name not in ["id", "ok", "run", "get", "set", "add", "pop"]:
            self._create_naming_violation(
                node, func_name, "function", "Function name too abbreviated - use descriptive names"
            )

    def _analyze_class_conventions(self, node: ast.ClassDef) -> None:
        """Analyze class naming and structure conventions."""
        class_name = node.name
        self.class_names.append(class_name)

        # Check class naming convention (should be PascalCase)
        if not self.pascal_case_pattern.match(class_name):
            self._create_naming_violation(node, class_name, "class", "Classes should use PascalCase naming convention")

        # Check for missing class docstrings
        if not self._has_docstring(node):
            self._create_documentation_violation(
                node, "Missing docstring for class", "Add docstring describing class purpose and usage"
            )

    def _analyze_variable_conventions(self, node: ast.Name) -> None:
        """Analyze variable naming conventions."""
        if isinstance(node.ctx, ast.Store):  # Variable assignment
            var_name = node.id
            self.variable_names.append(var_name)

            # Check for single letter variables (except common ones)
            if len(var_name) == 1 and var_name not in ["i", "j", "k", "x", "y", "z", "e", "f", "_"]:
                self._create_naming_violation(
                    node, var_name, "variable", "Avoid single-letter variable names except for common cases"
                )

    def _analyze_assignment_conventions(self, node: ast.Assign) -> None:
        """Analyze assignment conventions for constants."""
        # Check for potential constants (all uppercase assignments)
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id

                # If variable name is all uppercase, treat as constant
                if var_name.isupper() and len(var_name) > 1:
                    self.constant_names.append(var_name)

                    # Check constant naming pattern
                    if not self.constant_pattern.match(var_name):
                        self._create_naming_violation(
                            target, var_name, "constant", "Constants should use UPPER_SNAKE_CASE naming"
                        )

    def _check_naming_consistency(self) -> None:
        """Check for inconsistent naming patterns across the file."""
        # Check function naming consistency
        snake_case_functions = [name for name in self.function_names if self.snake_case_pattern.match(name)]
        camel_case_functions = [name for name in self.function_names if self.camel_case_pattern.match(name)]

        if len(snake_case_functions) > 0 and len(camel_case_functions) > 0:
            # Mixed naming patterns detected
            violation = ConnascenceViolation(
                type="connascence_of_convention",
                severity="medium",
                file_path=self.file_path,
                line_number=1,
                column=0,
                description="Inconsistent function naming: mixed snake_case and camelCase",
                recommendation="Choose one naming convention and apply consistently",
                code_snippet="Mixed naming patterns detected",
                context={
                    "snake_case_count": len(snake_case_functions),
                    "camel_case_count": len(camel_case_functions),
                    "mixed_patterns": True,
                },
            )
            self.violations.append(violation)

    def _has_docstring(self, node: ast.FunctionDef | ast.ClassDef) -> bool:
        """Check if function or class has a docstring."""
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            return True
        return False

    def _create_naming_violation(self, node: ast.AST, name: str, name_type: str, message: str) -> None:
        """Create violation for naming convention issues."""
        self.violations.append(
            ConnascenceViolation(
                type="connascence_of_convention",
                severity="low",
                file_path=self.file_path,
                line_number=node.lineno,
                column=node.col_offset,
                description=f"Naming convention violation: {message}",
                recommendation=f"Rename '{name}' to follow {name_type} naming conventions",
                code_snippet=self.get_code_snippet(node),
                context={"violation_type": "naming_convention", "name": name, "name_type": name_type},
            )
        )

    def _create_documentation_violation(self, node: ast.AST, message: str, recommendation: str) -> None:
        """Create violation for documentation issues."""
        self.violations.append(
            ConnascenceViolation(
                type="connascence_of_convention",
                severity="low",
                file_path=self.file_path,
                line_number=node.lineno,
                column=node.col_offset,
                description=message,
                recommendation=recommendation,
                code_snippet=self.get_code_snippet(node),
                context={"violation_type": "documentation", "missing_docstring": True},
            )
        )
