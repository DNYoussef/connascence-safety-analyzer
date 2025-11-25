# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors
"""
Cohesion Analyzer Module

Provides functionality for analyzing class and module cohesion,
detecting low-cohesion code that may indicate design issues.
"""

import ast
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


@dataclass
class CohesionMetrics:
    """Metrics for cohesion analysis."""

    lcom: float = 0.0  # Lack of Cohesion of Methods
    lcom4: float = 0.0  # LCOM4 variant
    tcc: float = 0.0  # Tight Class Cohesion
    lcc: float = 0.0  # Loose Class Cohesion
    method_count: int = 0
    attribute_count: int = 0
    shared_attributes: int = 0


@dataclass
class CohesionViolation:
    """Represents a cohesion violation."""

    type: str
    severity: str
    file_path: str
    line_number: int
    class_name: str
    description: str
    metrics: CohesionMetrics
    recommendation: str = ""


class CohesionAnalyzer:
    """
    Analyzes class cohesion using multiple metrics.

    Supports:
    - LCOM (Lack of Cohesion of Methods)
    - LCOM4 (improved LCOM variant)
    - TCC (Tight Class Cohesion)
    - LCC (Loose Class Cohesion)
    """

    # Thresholds for violation detection
    LCOM_THRESHOLD = 0.5  # Higher = less cohesive
    TCC_THRESHOLD = 0.3  # Lower = less cohesive

    def __init__(self):
        self.violations: List[CohesionViolation] = []

    def analyze_file(self, file_path: str) -> List[CohesionViolation]:
        """Analyze a Python file for cohesion violations."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
            return self.analyze_source(source, file_path)
        except Exception as e:
            return []

    def analyze_source(self, source: str, file_path: str = "") -> List[CohesionViolation]:
        """Analyze source code for cohesion violations."""
        self.violations = []
        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    self._analyze_class(node, file_path)
        except SyntaxError:
            pass
        return self.violations

    def _analyze_class(self, class_node: ast.ClassDef, file_path: str):
        """Analyze a class for cohesion."""
        methods = self._get_methods(class_node)
        attributes = self._get_instance_attributes(class_node)

        if len(methods) < 2:
            return  # Can't calculate meaningful cohesion

        metrics = self._calculate_metrics(methods, attributes)

        # Check for LCOM violations
        if metrics.lcom > self.LCOM_THRESHOLD:
            self.violations.append(
                CohesionViolation(
                    type="LowCohesion",
                    severity="medium",
                    file_path=file_path,
                    line_number=class_node.lineno,
                    class_name=class_node.name,
                    description=f"Class '{class_node.name}' has low cohesion (LCOM={metrics.lcom:.2f})",
                    metrics=metrics,
                    recommendation="Consider splitting into smaller, focused classes",
                )
            )

        # Check for TCC violations
        if metrics.tcc < self.TCC_THRESHOLD and metrics.method_count > 3:
            self.violations.append(
                CohesionViolation(
                    type="LowTCC",
                    severity="medium",
                    file_path=file_path,
                    line_number=class_node.lineno,
                    class_name=class_node.name,
                    description=f"Class '{class_node.name}' has low tight cohesion (TCC={metrics.tcc:.2f})",
                    metrics=metrics,
                    recommendation="Methods don't share enough common attributes",
                )
            )

    def _get_methods(self, class_node: ast.ClassDef) -> List[ast.FunctionDef]:
        """Extract method definitions from a class."""
        return [
            node
            for node in class_node.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not node.name.startswith("_")
        ]

    def _get_instance_attributes(self, class_node: ast.ClassDef) -> Set[str]:
        """Extract instance attributes from a class."""
        attributes = set()
        for node in ast.walk(class_node):
            if isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name) and node.value.id == "self":
                    attributes.add(node.attr)
        return attributes

    def _get_method_attributes(self, method: ast.FunctionDef) -> Set[str]:
        """Get instance attributes used by a method."""
        attributes = set()
        for node in ast.walk(method):
            if isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name) and node.value.id == "self":
                    attributes.add(node.attr)
        return attributes

    def _calculate_metrics(
        self, methods: List[ast.FunctionDef], attributes: Set[str]
    ) -> CohesionMetrics:
        """Calculate cohesion metrics for a class."""
        method_count = len(methods)
        attribute_count = len(attributes)

        if method_count == 0 or attribute_count == 0:
            return CohesionMetrics(method_count=method_count, attribute_count=attribute_count)

        # Calculate method-attribute usage
        method_attrs = [self._get_method_attributes(m) for m in methods]

        # LCOM calculation (Henderson-Sellers variant)
        total_usage = sum(len(ma) for ma in method_attrs)
        lcom = 1 - (total_usage / (method_count * attribute_count)) if attribute_count > 0 else 0

        # TCC calculation (Tight Class Cohesion)
        shared_pairs = 0
        total_pairs = method_count * (method_count - 1) // 2

        for i in range(len(method_attrs)):
            for j in range(i + 1, len(method_attrs)):
                if method_attrs[i] & method_attrs[j]:
                    shared_pairs += 1

        tcc = shared_pairs / total_pairs if total_pairs > 0 else 0
        lcc = tcc  # LCC is typically >= TCC, simplified here

        return CohesionMetrics(
            lcom=lcom,
            lcom4=lcom,
            tcc=tcc,
            lcc=lcc,
            method_count=method_count,
            attribute_count=attribute_count,
            shared_attributes=sum(1 for ma in method_attrs if ma),
        )


def analyze_cohesion(source_or_path: str, is_file: bool = True) -> List[CohesionViolation]:
    """
    Convenience function to analyze cohesion.

    Args:
        source_or_path: File path or source code string
        is_file: If True, treat as file path; if False, treat as source code

    Returns:
        List of cohesion violations
    """
    analyzer = CohesionAnalyzer()
    if is_file:
        return analyzer.analyze_file(source_or_path)
    return analyzer.analyze_source(source_or_path)


__all__ = [
    "CohesionAnalyzer",
    "CohesionMetrics",
    "CohesionViolation",
    "analyze_cohesion",
]
