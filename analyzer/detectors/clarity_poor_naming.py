"""
Poor Naming Detector - Code Clarity Detector

Detects unclear variable and function names.

NASA Rule 4 Compliant: All functions under 60 lines
NASA Rule 5 Compliant: Input assertions
"""

import ast
import re
from pathlib import Path
from typing import List, Set

from analyzer.clarity_linter.base import BaseClarityDetector
from analyzer.clarity_linter.models import ClarityViolation


class PoorNamingDetector(BaseClarityDetector):
    """
    Detects poor variable and function naming patterns.

    Patterns detected:
    - Single-letter names (except i, j, k in loops)
    - Abbreviations without context
    - Names too short (<3 chars)
    - Generic names like 'data', 'temp', 'foo'
    - Hungarian notation

    NASA Rule 4 Compliant: All methods under 60 lines
    NASA Rule 5 Compliant: Input assertions
    """

    rule_id = "CLARITY_POOR_NAMING"
    rule_name = "Poor Naming"
    default_severity = "low"

    # Minimum name length
    MIN_NAME_LENGTH = 3

    # Allowed single-letter names in specific contexts
    ALLOWED_SINGLE_LETTERS: Set[str] = {
        "i", "j", "k", "n", "x", "y", "z",
        "_",  # Placeholder
        "e",  # Exception
        "f",  # File
        "s",  # String
    }

    # Generic names to flag
    GENERIC_NAMES: Set[str] = {
        "data", "temp", "tmp", "foo", "bar", "baz",
        "val", "value", "item", "thing", "stuff",
        "obj", "object", "result", "ret", "res",
        "var", "var1", "var2", "x1", "x2",
    }

    # Hungarian notation prefixes to detect
    HUNGARIAN_PREFIXES = re.compile(
        r"^(str|int|flt|dbl|bool|lst|dict|arr|obj|ptr|fn|cb|evt)[A-Z]"
    )

    # Common abbreviations that are unclear
    UNCLEAR_ABBREVIATIONS: Set[str] = {
        "mgr", "ctx", "cfg", "db", "srv", "req", "resp",
        "btn", "lbl", "txt", "msg", "num", "cnt", "idx",
        "ptr", "buf", "len", "sz", "cb", "fn", "evt",
    }

    def detect(
        self,
        tree: ast.Module,
        file_path: Path
    ) -> List[ClarityViolation]:
        """
        Detect poor naming in AST tree.

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
        self._analyze_variables(tree, file_path, violations)
        return violations

    def _analyze_functions(
        self,
        tree: ast.Module,
        file_path: Path,
        violations: List[ClarityViolation]
    ) -> None:
        """
        Analyze function and parameter names.

        NASA Rule 4: Function under 60 lines
        """
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Check function name
                issue = self._check_name(node.name, "function")
                if issue:
                    violations.append(
                        self._create_naming_violation(
                            file_path, node.lineno, node.name, "function", issue
                        )
                    )

                # Check parameter names
                for arg in node.args.args:
                    if arg.arg == "self" or arg.arg == "cls":
                        continue
                    issue = self._check_name(arg.arg, "parameter")
                    if issue:
                        violations.append(
                            self._create_naming_violation(
                                file_path, node.lineno, arg.arg, "parameter", issue
                            )
                        )

    def _analyze_variables(
        self,
        tree: ast.Module,
        file_path: Path,
        violations: List[ClarityViolation]
    ) -> None:
        """
        Analyze variable names.

        NASA Rule 4: Function under 60 lines
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        # Skip constants (UPPER_CASE)
                        if target.id.isupper():
                            continue
                        issue = self._check_name(target.id, "variable")
                        if issue:
                            violations.append(
                                self._create_naming_violation(
                                    file_path, node.lineno, target.id, "variable", issue
                                )
                            )

    def _check_name(self, name: str, context: str) -> str:
        """
        Check if name has issues.

        NASA Rule 4: Function under 60 lines
        """
        # Skip private/dunder names
        if name.startswith("_"):
            return ""

        # Check length
        if len(name) == 1:
            if name not in self.ALLOWED_SINGLE_LETTERS:
                return "single_letter"
        elif len(name) < self.MIN_NAME_LENGTH:
            return "too_short"

        # Check for generic names
        if name.lower() in self.GENERIC_NAMES:
            return "generic"

        # Check for Hungarian notation
        if self.HUNGARIAN_PREFIXES.match(name):
            return "hungarian"

        # Check for unclear abbreviations
        if name.lower() in self.UNCLEAR_ABBREVIATIONS:
            return "abbreviation"

        return ""

    def _create_naming_violation(
        self,
        file_path: Path,
        line_number: int,
        name: str,
        name_type: str,
        issue: str
    ) -> ClarityViolation:
        """
        Create violation for poor naming.

        NASA Rule 4: Function under 60 lines
        """
        issue_messages = {
            "single_letter": f"Single-letter {name_type} name '{name}'",
            "too_short": f"{name_type.capitalize()} name '{name}' is too short",
            "generic": f"Generic {name_type} name '{name}'",
            "hungarian": f"Hungarian notation in {name_type} name '{name}'",
            "abbreviation": f"Unclear abbreviation in {name_type} name '{name}'",
        }

        description = issue_messages.get(
            issue, f"Poor {name_type} name '{name}'"
        )

        recommendation = self._get_recommendation(issue, name_type)

        return self.create_violation(
            file_path=file_path,
            line_number=line_number,
            description=description,
            recommendation=recommendation,
            context={
                "name": name,
                "name_type": name_type,
                "issue": issue,
                "issue_type": "poor_naming"
            }
        )

    def _get_recommendation(self, issue: str, name_type: str) -> str:
        """
        Get recommendation based on issue type.

        NASA Rule 4: Function under 60 lines
        """
        recommendations = {
            "single_letter": (
                f"Use a descriptive {name_type} name that explains its purpose."
            ),
            "too_short": (
                f"Use a longer, more descriptive {name_type} name."
            ),
            "generic": (
                f"Replace with a specific name that describes what it contains."
            ),
            "hungarian": (
                "Remove the type prefix. Python uses duck typing."
            ),
            "abbreviation": (
                "Spell out the full word for clarity."
            ),
        }
        return recommendations.get(issue, f"Use a more descriptive {name_type} name.")


__all__ = ['PoorNamingDetector']
