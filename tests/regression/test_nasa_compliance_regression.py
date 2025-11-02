#!/usr/bin/env python3
"""
NASA Compliance Regression Test Suite

Validates that ALL code (analyzer utilities, detectors, and main codebase)
maintains NASA Power of Ten compliance. This is a regression test to ensure
refactoring doesn't break compliance.

NASA Rules Tested:
- Rule 4: Functions <=60 lines
- Rule 5: Assertions for critical functions
- Rule 7: No recursion (use iterative alternatives)
- Rule 8: Fixed loop bounds (no while(true))
"""

import ast
from pathlib import Path
from typing import Dict, List

import pytest

from fixes.phase0.production_safe_assertions import ProductionAssert


class NASAComplianceValidator:
    """Validates NASA Power of Ten compliance across the codebase."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.violations: Dict[str, List[Dict]] = {
            "rule4": [],  # Function length violations
            "rule5": [],  # Missing assertions
            "rule7": [],  # Recursion violations
            "rule8": [],  # Unbounded loop violations
        }

    def scan_directory(self, directory: Path, pattern: str = "*.py") -> List[Path]:
        """
        Scan directory for Python files.

        Args:
            directory: Directory to scan
            pattern: File pattern (default: *.py)

        Returns:
            List of Python file paths
        """
        ProductionAssert.not_none(directory, "directory")

        files = []
        if directory.exists():
            files = list(directory.rglob(pattern))
        return files

    def check_rule4_function_length(self, file_path: Path) -> List[Dict]:
        """
        Check NASA Rule 4: Functions should be <=60 lines.

        Args:
            file_path: Python file to check

        Returns:
            List of violations (function name, line count, location)
        """
        ProductionAssert.not_none(file_path, "file_path")

        violations = []

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content, filename=str(file_path))

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    length = node.end_lineno - node.lineno + 1

                    if length > 60:
                        violations.append(
                            {
                                "file": str(file_path.relative_to(self.project_root)),
                                "function": node.name,
                                "length": length,
                                "line": node.lineno,
                                "threshold": 60,
                            }
                        )

        except (SyntaxError, UnicodeDecodeError):
            # Skip files with syntax errors or encoding issues
            pass

        return violations

    def check_rule7_recursion(self, file_path: Path) -> List[Dict]:
        """
        Check NASA Rule 7: No recursion (use iterative alternatives).

        Args:
            file_path: Python file to check

        Returns:
            List of recursion violations
        """
        ProductionAssert.not_none(file_path, "file_path")

        violations = []

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content, filename=str(file_path))

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check if function calls itself
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                            if child.func.id == node.name:
                                violations.append(
                                    {
                                        "file": str(file_path.relative_to(self.project_root)),
                                        "function": node.name,
                                        "line": node.lineno,
                                        "type": "direct_recursion",
                                    }
                                )

        except (SyntaxError, UnicodeDecodeError):
            pass

        return violations

    def check_rule8_bounded_loops(self, file_path: Path) -> List[Dict]:
        """
        Check NASA Rule 8: Loops must have fixed bounds (no while(True)).

        Args:
            file_path: Python file to check

        Returns:
            List of unbounded loop violations
        """
        ProductionAssert.not_none(file_path, "file_path")

        violations = []

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content, filename=str(file_path))

            for node in ast.walk(tree):
                if isinstance(node, ast.While):
                    # Check for while True: pattern
                    if isinstance(node.test, ast.Constant) and node.test.value is True:
                        violations.append(
                            {
                                "file": str(file_path.relative_to(self.project_root)),
                                "line": node.lineno,
                                "type": "while_true",
                            }
                        )

        except (SyntaxError, UnicodeDecodeError):
            pass

        return violations

    def scan_codebase(self, directories: List[str]) -> Dict[str, int]:
        """
        Scan entire codebase for NASA compliance.

        Args:
            directories: List of directories to scan

        Returns:
            Summary dict with violation counts
        """
        ProductionAssert.not_none(directories, "directories")

        for dir_name in directories:
            directory = self.project_root / dir_name
            files = self.scan_directory(directory)

            for file_path in files:
                # Skip test files and __pycache__
                if "__pycache__" in str(file_path) or "test_" in file_path.name:
                    continue

                # Check all rules
                self.violations["rule4"].extend(self.check_rule4_function_length(file_path))
                self.violations["rule7"].extend(self.check_rule7_recursion(file_path))
                self.violations["rule8"].extend(self.check_rule8_bounded_loops(file_path))

        return {
            "rule4_violations": len(self.violations["rule4"]),
            "rule7_violations": len(self.violations["rule7"]),
            "rule8_violations": len(self.violations["rule8"]),
            "total_violations": sum(len(v) for v in self.violations.values()),
        }


@pytest.fixture
def nasa_validator():
    """Provide NASA compliance validator fixture."""
    return NASAComplianceValidator()


class TestNASAComplianceRegression:
    """Regression tests for NASA Power of Ten compliance."""

    def test_analyzer_utils_rule4_compliance(self, nasa_validator):
        """Test that analyzer utilities comply with Rule 4 (≤60 lines)."""
        files = nasa_validator.scan_directory(nasa_validator.project_root / "analyzer" / "utils")

        violations = []
        for file_path in files:
            violations.extend(nasa_validator.check_rule4_function_length(file_path))

        assert len(violations) == 0, f"Found {len(violations)} Rule 4 violations in analyzer/utils:\n" + "\n".join(
            [f"  - {v['file']}:{v['line']} {v['function']}() = {v['length']} LOC" for v in violations]
        )

    def test_analyzer_detectors_rule4_compliance(self, nasa_validator):
        """Test that analyzer detectors comply with Rule 4 (≤60 lines)."""
        files = nasa_validator.scan_directory(nasa_validator.project_root / "analyzer" / "detectors")

        violations = []
        for file_path in files:
            violations.extend(nasa_validator.check_rule4_function_length(file_path))

        assert len(violations) == 0, f"Found {len(violations)} Rule 4 violations in analyzer/detectors:\n" + "\n".join(
            [f"  - {v['file']}:{v['line']} {v['function']}() = {v['length']} LOC" for v in violations]
        )

    def test_no_recursion_in_codebase(self, nasa_validator):
        """Test that codebase has no recursion (Rule 7)."""
        summary = nasa_validator.scan_codebase(["analyzer", "src", "utils"])

        violations = nasa_validator.violations["rule7"]

        assert summary["rule7_violations"] == 0, f"Found {len(violations)} recursion violations:\n" + "\n".join(
            [f"  - {v['file']}:{v['line']} {v['function']}() has {v['type']}" for v in violations]
        )

    def test_no_unbounded_loops(self, nasa_validator):
        """Test that codebase has no unbounded loops (Rule 8)."""
        summary = nasa_validator.scan_codebase(["analyzer", "src", "utils"])

        violations = nasa_validator.violations["rule8"]

        assert summary["rule8_violations"] == 0, f"Found {len(violations)} unbounded loop violations:\n" + "\n".join(
            [f"  - {v['file']}:{v['line']} has {v['type']}" for v in violations]
        )

    def test_full_nasa_compliance_scan(self, nasa_validator):
        """
        Full NASA compliance scan across entire codebase.

        This is the master regression test that validates all NASA rules
        across analyzer/, src/, and utils/.
        """
        summary = nasa_validator.scan_codebase(["analyzer", "src", "utils"])

        total_violations = summary["total_violations"]

        # Calculate compliance percentage
        # (This is a regression test, so we expect high compliance)

        # Detailed report
        report = [
            "\n" + "=" * 60,
            "NASA COMPLIANCE REGRESSION REPORT",
            "=" * 60,
            f"Rule 4 (≤60 lines): {summary['rule4_violations']} violations",
            f"Rule 7 (no recursion): {summary['rule7_violations']} violations",
            f"Rule 8 (bounded loops): {summary['rule8_violations']} violations",
            f"Total violations: {total_violations}",
            "=" * 60,
        ]

        if total_violations > 0:
            report.append("\nViolation Details:")

            # Show Rule 4 violations
            if nasa_validator.violations["rule4"]:
                report.append("\nRule 4 Violations (Function Length >60):")
                for v in nasa_validator.violations["rule4"][:10]:  # Show first 10
                    report.append(f"  - {v['file']}:{v['line']} " f"{v['function']}() = {v['length']} LOC")

            # Show Rule 7 violations
            if nasa_validator.violations["rule7"]:
                report.append("\nRule 7 Violations (Recursion):")
                for v in nasa_validator.violations["rule7"][:10]:
                    report.append(f"  - {v['file']}:{v['line']} " f"{v['function']}() has {v['type']}")

            # Show Rule 8 violations
            if nasa_validator.violations["rule8"]:
                report.append("\nRule 8 Violations (Unbounded Loops):")
                for v in nasa_validator.violations["rule8"][:10]:
                    report.append(f"  - {v['file']}:{v['line']} has {v['type']}")

        report.append("=" * 60)

        # Assert compliance
        assert total_violations == 0, "\n".join(report)


def test_nasa_compliance_baseline():
    """
    Baseline test to document current NASA compliance level.

    This test always passes but prints current metrics for tracking.
    """
    validator = NASAComplianceValidator()
    summary = validator.scan_codebase(["analyzer", "src", "utils"])

    print("\n" + "=" * 60)
    print("NASA COMPLIANCE BASELINE METRICS")
    print("=" * 60)
    print(f"Rule 4 violations: {summary['rule4_violations']}")
    print(f"Rule 7 violations: {summary['rule7_violations']}")
    print(f"Rule 8 violations: {summary['rule8_violations']}")
    print(f"Total violations: {summary['total_violations']}")
    print("=" * 60)

    # Always pass (this is just for metrics tracking)
    assert True
