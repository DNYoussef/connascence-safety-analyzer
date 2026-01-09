# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

"""
Core AST analyzer for detecting connascence violations in Python code.

This module implements the ConnascenceASTAnalyzer class which uses Python's
AST module to analyze code and detect various forms of connascence including:
- CoM (Connascence of Meaning): Magic literals
- CoP (Connascence of Position): Parameter bombs
- CoT (Connascence of Type): Missing type hints
- CoA (Connascence of Algorithm): Cyclomatic complexity, god classes
"""

import ast
from dataclasses import dataclass, field
import hashlib
from pathlib import Path
import time
from typing import Dict, List, Optional
import uuid

from utils.types import ConnascenceViolation


@dataclass
class ThresholdConfig:
    """Configuration for analysis thresholds."""

    max_positional_params: int = 6
    max_cyclomatic_complexity: int = 10
    god_class_methods: int = 15
    max_method_lines: int = 50
    max_nesting_depth: int = 4
    min_magic_literal_threshold: float = 10.0


@dataclass
class AnalysisResult:
    """Results from analyzing code."""

    violations: List[ConnascenceViolation] = field(default_factory=list)
    total_files: int = 0
    analysis_time: float = 0.0
    connascence_index: float = 0.0

    @property
    def total_violations(self) -> int:
        """Get total number of violations."""
        return len(self.violations)

    @property
    def critical_count(self) -> int:
        """Get count of critical violations."""
        return sum(1 for v in self.violations if v.severity == "critical")

    @property
    def high_count(self) -> int:
        """Get count of high severity violations."""
        return sum(1 for v in self.violations if v.severity == "high")

    @property
    def medium_count(self) -> int:
        """Get count of medium severity violations."""
        return sum(1 for v in self.violations if v.severity == "medium")

    @property
    def low_count(self) -> int:
        """Get count of low severity violations."""
        return sum(1 for v in self.violations if v.severity == "low")

    @property
    def violations_by_type(self) -> Dict[str, int]:
        """Get violations grouped by connascence type."""
        result = {}
        for v in self.violations:
            conn_type = v.connascence_type or v.type
            result[conn_type] = result.get(conn_type, 0) + 1
        return result


class ConnascenceASTAnalyzer:
    """
    AST-based analyzer for detecting connascence violations in Python code.

    This analyzer uses Python's AST module to parse and analyze code,
    detecting various forms of connascence and code quality issues.
    """

    def __init__(self, thresholds: Optional[ThresholdConfig] = None):
        """Initialize the analyzer with optional custom thresholds."""
        self.thresholds = thresholds or ThresholdConfig()
        self._cache: Dict[str, List[ConnascenceViolation]] = {}

    def analyze_string(self, code: str, file_path: str = "unknown.py") -> List[ConnascenceViolation]:
        """
        Analyze a string of Python code for connascence violations.

        Args:
            code: Python source code to analyze
            file_path: Path to the file (for reporting purposes)

        Returns:
            List of ConnascenceViolation objects
        """
        # Check cache
        cache_key = hashlib.md5(f"{file_path}:{code}".encode()).hexdigest()
        if cache_key in self._cache:
            return self._cache[cache_key]

        violations = []

        # Handle empty files
        if not code.strip():
            self._cache[cache_key] = violations
            return violations

        # Parse the code
        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Handle syntax errors gracefully
            self._cache[cache_key] = violations
            return violations

        # Run all detection passes
        violations.extend(self._detect_magic_literals(tree, file_path))
        violations.extend(self._detect_parameter_bombs(tree, file_path))
        violations.extend(self._detect_missing_type_hints(tree, file_path))
        violations.extend(self._detect_god_classes(tree, file_path))
        violations.extend(self._detect_complex_methods(tree, file_path))

        # Cache results
        self._cache[cache_key] = violations
        return violations

    def analyze_file(self, file_path: Path) -> List[ConnascenceViolation]:
        """
        Analyze a Python file for connascence violations.

        Args:
            file_path: Path to the Python file

        Returns:
            List of ConnascenceViolation objects
        """
        with open(file_path, encoding="utf-8") as f:
            code = f.read()
        return self.analyze_string(code, str(file_path))

    def analyze_directory(self, dir_path: Path) -> AnalysisResult:
        """
        Analyze all Python files in a directory.

        Args:
            dir_path: Path to the directory

        Returns:
            AnalysisResult with all violations found
        """
        start_time = time.time()
        all_violations = []
        file_count = 0

        for py_file in dir_path.rglob("*.py"):
            try:
                violations = self.analyze_file(py_file)
                all_violations.extend(violations)
                file_count += 1
            except Exception:
                # Skip files that can't be analyzed
                continue

        analysis_time = time.time() - start_time

        # Calculate connascence index
        total_weight = sum(v.weight for v in all_violations)

        return AnalysisResult(
            violations=all_violations, total_files=file_count, analysis_time=analysis_time, connascence_index=total_weight
        )

    def _detect_magic_literals(self, tree: ast.AST, file_path: str) -> List[ConnascenceViolation]:
        """Detect magic literals (CoM - Connascence of Meaning)."""
        violations = []

        # Skip constants definition files entirely
        file_name_lower = file_path.lower()
        constants_file_patterns = ["constants", "config", "settings", "defaults"]
        if any(pattern in file_name_lower for pattern in constants_file_patterns):
            return violations

        # Track constant assignments to skip values inside them
        constant_assignments = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper() and len(target.id) > 1:
                        constant_assignments.add(id(node.value))
                        # Also mark any dict/list/set values as constant containers
                        if isinstance(node.value, (ast.Dict, ast.List, ast.Set, ast.Tuple)):
                            for child in ast.walk(node.value):
                                constant_assignments.add(id(child))

        for node in ast.walk(tree):
            # Skip nodes that are part of constant assignments
            if id(node) in constant_assignments:
                continue

            # Check for numeric constants
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                # Skip common literals (0, 1, -1, 2)
                if node.value in (0, 1, -1, 2):
                    continue

                # Check if it's a significant magic number
                if abs(node.value) >= self.thresholds.min_magic_literal_threshold or (
                    isinstance(node.value, float) and 0 < abs(node.value) < 1
                ):
                    severity = "critical" if abs(node.value) > 1000000 else "medium"
                    violations.append(
                        ConnascenceViolation(
                            id=str(uuid.uuid4()),
                            rule_id="CON_CoM",
                            connascence_type="CoM",
                            severity=severity,
                            description=f"Magic literal: {node.value}",
                            file_path=file_path,
                            line_number=node.lineno,
                            weight=10.0 if severity == "critical" else 2.0,
                        )
                    )

        return violations

    def _detect_parameter_bombs(self, tree: ast.AST, file_path: str) -> List[ConnascenceViolation]:
        """Detect functions with too many parameters (CoP - Connascence of Position)."""
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Count positional parameters (excluding self/cls)
                param_count = len(node.args.args)
                if param_count > 0 and node.args.args[0].arg in ("self", "cls"):
                    param_count -= 1

                if param_count > self.thresholds.max_positional_params:
                    # Determine severity based on parameter count
                    if param_count > 10:
                        severity = "critical"
                    elif param_count > 8:
                        severity = "high"
                    else:
                        severity = "medium"

                    violations.append(
                        ConnascenceViolation(
                            id=str(uuid.uuid4()),
                            rule_id="CON_CoP",
                            connascence_type="CoP",
                            severity=severity,
                            description=f"Function '{node.name}' has {param_count} parameters (max: {self.thresholds.max_positional_params})",
                            file_path=file_path,
                            line_number=node.lineno,
                            weight=10.0 if severity == "critical" else (5.0 if severity == "high" else 2.0),
                        )
                    )

        return violations

    def _detect_missing_type_hints(self, tree: ast.AST, file_path: str) -> List[ConnascenceViolation]:
        """Detect functions missing type hints (CoT - Connascence of Type)."""
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function has type hints
                has_param_hints = any(arg.annotation is not None for arg in node.args.args)
                has_return_hint = node.returns is not None

                # Skip if function has no parameters
                if not node.args.args:
                    continue

                # Report missing type hints
                if not has_param_hints and not has_return_hint:
                    violations.append(
                        ConnascenceViolation(
                            id=str(uuid.uuid4()),
                            rule_id="CON_CoT",
                            connascence_type="CoT",
                            severity="medium",
                            description=f"Function '{node.name}' missing type hints",
                            file_path=file_path,
                            line_number=node.lineno,
                            weight=2.0,
                        )
                    )

        return violations

    def _detect_god_classes(self, tree: ast.AST, file_path: str) -> List[ConnascenceViolation]:
        """Detect god classes (CoA - Connascence of Algorithm)."""
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Count methods in the class
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                method_count = len(methods)

                if method_count > self.thresholds.god_class_methods:
                    severity = "critical" if method_count > 30 else "high"
                    violations.append(
                        ConnascenceViolation(
                            id=str(uuid.uuid4()),
                            rule_id="CON_CoA",
                            connascence_type="CoA",
                            severity=severity,
                            description=f"God class '{node.name}' has {method_count} methods (max: {self.thresholds.god_class_methods})",
                            file_path=file_path,
                            line_number=node.lineno,
                            weight=10.0 if severity == "critical" else 5.0,
                        )
                    )

        return violations

    def _detect_complex_methods(self, tree: ast.AST, file_path: str) -> List[ConnascenceViolation]:
        """Detect methods with high cyclomatic complexity (CoA - Connascence of Algorithm)."""
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_complexity(node)

                if complexity > self.thresholds.max_cyclomatic_complexity:
                    severity = "high" if complexity > 15 else "medium"
                    violations.append(
                        ConnascenceViolation(
                            id=str(uuid.uuid4()),
                            rule_id="CON_CoA",
                            connascence_type="CoA",
                            severity=severity,
                            description=f"Function '{node.name}' has cyclomatic complexity of {complexity} (max: {self.thresholds.max_cyclomatic_complexity})",
                            file_path=file_path,
                            line_number=node.lineno,
                            weight=5.0 if severity == "high" else 2.0,
                        )
                    )

        return violations

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            # Each decision point adds to complexity
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # Each boolean operator in a condition
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.Break, ast.Continue)):
                # Break and continue add to complexity
                complexity += 1

        return complexity


class Violation:
    """Legacy compatibility class."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


__all__ = ["AnalysisResult", "ConnascenceASTAnalyzer", "ConnascenceViolation", "ThresholdConfig", "Violation"]
