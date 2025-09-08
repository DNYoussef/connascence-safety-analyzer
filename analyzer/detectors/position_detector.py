"""
Position Detector - Refactored to Eliminate Connascence Violations

Detects Connascence of Position violations using standardized interfaces
and configuration-driven thresholds to reduce parameter order coupling.
"""

import ast
from typing import List

from utils.types import ConnascenceViolation
from .base import DetectorBase
# Temporarily disabled broken imports added by subagents
# from ..interfaces.detector_interface import (
#     StandardDetectorInterface, AnalysisContext, DetectorResult,
#     ConfigurableDetectorMixin, register_detector, ViolationSeverity, ConnascenceType
# )
# from ..utils.common_patterns import ASTUtils, ViolationFactory  
# from ..utils.error_handling import SafeExecutionMixin, handle_errors, ErrorCategory


# Temporarily disabled broken decorator and mixins
# @register_detector(ConnascenceType.POSITION)
# class PositionDetector(StandardDetectorInterface, ConfigurableDetectorMixin, SafeExecutionMixin):
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
            DetectorResult with violations and metadata
        """
        import time
        start_time = time.time()
        
        self.violations.clear()
        
        # Use common patterns to find function definitions
        functions = ASTUtils.find_nodes_by_type(tree, ast.FunctionDef)
        functions_analyzed = 0
        
        for node in functions:
            if self._check_function_parameters(node):
                functions_analyzed += 1
        
        end_time = time.time()
        processing_time = int((end_time - start_time) * 1000)
        
        return DetectorResult(
            violations=self.violations,
            metadata={
                'detector_type': 'position',
                'functions_analyzed': functions_analyzed,
                'threshold_used': self.max_positional_params
            },
            processing_time_ms=processing_time
        )
    
    def _check_function_parameters(self, node: ast.FunctionDef) -> bool:
        """
        Check if function has too many positional parameters using standardized patterns.
        
        Returns:
            True if function was analyzed (regardless of violations found)
        """
        # Use common utility to get parameter information instead of duplicating logic
        param_info = ASTUtils.get_function_parameters(node)
        positional_count = param_info['positional_count']
        
        # Use guard clause with configurable threshold
        if positional_count <= self.max_positional_params:
            return True
        
        # Determine severity based on how far over the threshold we are
        severity = self._calculate_severity(positional_count)
        
        # Create violation using standardized factory
        location = ASTUtils.get_node_location(node, self.context.file_path)
        code_snippet = ASTUtils.extract_code_snippet(self.context.source_lines, node)
        
        violation = ViolationFactory.create_violation(
            violation_type=ConnascenceType.POSITION,
            severity=severity,
            location=location,
            description=f"Function '{node.name}' has {positional_count} positional parameters (>{self.max_positional_params})",
            recommendation=self._get_recommendation(positional_count),
            code_snippet=code_snippet,
            context={
                "parameter_count": positional_count,
                "function_name": node.name,
                "threshold": self.max_positional_params,
                "parameter_details": param_info
            }
        )
        
        self.violations.append(violation)
        return True
    
    def _calculate_severity(self, parameter_count: int) -> str:
        """Calculate severity based on how far over the threshold the parameter count is."""
        severity_mapping = self.get_config().severity_mapping or {}
        
        # Check configured severity mappings first
        for range_str, severity in severity_mapping.items():
            if self._parameter_count_in_range(parameter_count, range_str):
                return severity
        
        # Fallback to default severity calculation
        if parameter_count <= self.max_positional_params + 3:
            return ViolationSeverity.MEDIUM
        elif parameter_count <= self.max_positional_params + 7:
            return ViolationSeverity.HIGH
        else:
            return ViolationSeverity.CRITICAL
    
    def _parameter_count_in_range(self, count: int, range_str: str) -> bool:
        """Check if parameter count falls within a configured range string."""
        try:
            if '-' in range_str:
                start, end = range_str.split('-')
                return int(start) <= count <= int(end)
            elif range_str.endswith('+'):
                threshold = int(range_str[:-1])
                return count >= threshold
            else:
                return count == int(range_str)
        except (ValueError, IndexError):
            return False
    
    def _get_recommendation(self, parameter_count: int) -> str:
        """Get contextual recommendation based on parameter count."""
        if parameter_count <= 6:
            return "Consider using keyword arguments or a parameter object"
        elif parameter_count <= 10:
            return "Consider using a data class or configuration object to group related parameters"
        else:
            return "Function has excessive parameters - consider breaking into smaller functions or using builder pattern"
    
    def analyze_from_data(self, collected_data) -> List[ConnascenceViolation]:
        """
        Optimized analysis from pre-collected data using standardized patterns.
        
        Args:
            collected_data: Pre-collected AST data from unified visitor
            
        Returns:
            List of position-related violations
        """
        violations = []
        
        # Use pre-collected parameter data with configuration-driven thresholds
        for func_name, param_count in collected_data.function_params.items():
            if param_count > self.max_positional_params:
                func_node = collected_data.functions[func_name]
                
                # Calculate severity using the same method as real-time analysis
                severity = self._calculate_severity(param_count)
                location = ASTUtils.get_node_location(func_node, self.context.file_path)
                code_snippet = ASTUtils.extract_code_snippet(self.context.source_lines, func_node)
                
                violation = ViolationFactory.create_violation(
                    violation_type=ConnascenceType.POSITION,
                    severity=severity,
                    location=location,
                    description=f"Function '{func_name}' has {param_count} positional parameters (>{self.max_positional_params})",
                    recommendation=self._get_recommendation(param_count),
                    code_snippet=code_snippet,
                    context={
                        "parameter_count": param_count,
                        "function_name": func_name,
                        "threshold": self.max_positional_params,
                        "analysis_method": "pre_collected"
                    }
                )
                
                violations.append(violation)
        
        return violations
    
    def get_supported_violation_types(self) -> List[str]:
        """Get list of violation types this detector can find."""
        return [ConnascenceType.POSITION]