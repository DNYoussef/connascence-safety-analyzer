"""
Position Detector - Refactored to Eliminate Connascence Violations

Detects Connascence of Position violations using standardized interfaces
and configuration-driven thresholds to reduce parameter order coupling.
"""

import ast
from typing import List

from utils.types import ConnascenceViolation
from analyzer.utils.ast_utils import ASTUtils
from analyzer.utils.violation_factory import ViolationFactory
from analyzer.utils.detector_result import DetectorResult, AnalysisContext

from .base import DetectorBase


class PositionDetector(DetectorBase):
    """
    Detects functions with excessive positional parameters.
    Refactored to eliminate Connascence of Position through configuration and
    standardized parameter handling.
    """

    def __init__(self, file_path: str, source_lines: List[str]):
        super().__init__(file_path, source_lines)

        # Use hardcoded threshold (avoiding broken configuration system)
        self.max_positional_params = 3

    def detect_violations(self, tree: ast.AST) -> List[ConnascenceViolation]:
        """
        Detect functions with too many positional parameters using standardized interface.

        Args:
            tree: AST tree to analyze

        Returns:
            List of ConnascenceViolation objects
        """
        self.violations.clear()

        # Use common patterns to find function definitions
        functions = ASTUtils.find_nodes_by_type(tree, ast.FunctionDef)

        for node in functions:
            self._check_function_parameters(node)

        return self.violations

    def analyze_from_data(self, collected_data) -> List[ConnascenceViolation]:
        """
        Optimized two-phase analysis: Analyze from pre-collected data.

        This method provides backwards compatibility with RefactoredConnascenceDetector
        which uses UnifiedASTVisitor to pre-collect data for performance optimization.

        Args:
            collected_data: Pre-collected AST data with function_params dict

        Returns:
            List of position-related violations
        """
        violations = []

        # Use pre-collected parameter data
        if hasattr(collected_data, 'function_params'):
            for func_name, param_count in collected_data.function_params.items():
                if param_count > self.max_positional_params:
                    # Get function node for location info
                    func_node = collected_data.functions.get(func_name)
                    if not func_node:
                        continue

                    severity = self._calculate_severity(param_count)
                    location = ASTUtils.get_node_location(func_node, self.file_path)
                    code_snippet = ASTUtils.extract_code_snippet(
                        self.source_lines, func_node
                    )

                    violation = ViolationFactory.create_cop_violation(
                        location=location,
                        function_name=func_name,
                        param_count=param_count,
                        threshold=self.max_positional_params
                    )

                    violation["severity"] = severity
                    violation["recommendation"] = self._get_recommendation(param_count)
                    violation["code_snippet"] = code_snippet
                    violation["context"] = {
                        "parameter_count": param_count,
                        "function_name": func_name,
                        "threshold": self.max_positional_params,
                        "analysis_method": "pre_collected"
                    }

                    violations.append(violation)

        return violations

    def _check_function_parameters(self, node: ast.FunctionDef) -> None:
        """
        Check if function has too many positional parameters using standardized patterns.
        """
        # Use common utility to get parameter information instead of duplicating logic
        param_info = ASTUtils.get_function_parameters(node)
        positional_count = param_info["positional_count"]

        # Use guard clause with configurable threshold
        if positional_count <= self.max_positional_params:
            return

        # Determine severity based on how far over the threshold we are
        severity = self._calculate_severity(positional_count)

        # Create violation using standardized factory
        location = ASTUtils.get_node_location(node, self.file_path)
        code_snippet = ASTUtils.extract_code_snippet(self.source_lines, node)

        violation = ViolationFactory.create_cop_violation(
            location=location,
            function_name=node.name,
            param_count=positional_count,
            threshold=self.max_positional_params
        )

        # Override severity if needed (create_cop_violation uses default logic)
        violation["severity"] = severity
        violation["recommendation"] = self._get_recommendation(positional_count)
        violation["code_snippet"] = code_snippet
        violation["context"] = {
            "parameter_count": positional_count,
            "function_name": node.name,
            "threshold": self.max_positional_params,
            "parameter_details": param_info,
        }

        self.violations.append(violation)

    def _calculate_severity(self, parameter_count: int) -> str:
        """Calculate severity based on how far over the threshold the parameter count is."""
        # Simple severity calculation without config dependencies
        if parameter_count <= self.max_positional_params + 3:
            return "medium"
        elif parameter_count <= self.max_positional_params + 7:
            return "high"
        else:
            return "critical"

    def _get_recommendation(self, parameter_count: int) -> str:
        """Get contextual recommendation based on parameter count."""
        if parameter_count <= 6:
            return "Consider using keyword arguments or a parameter object"
        elif parameter_count <= 10:
            return "Consider using a data class or configuration object to group related parameters"
        else:
            return (
                "Function has excessive parameters - consider breaking into smaller functions or using builder pattern"
            )
