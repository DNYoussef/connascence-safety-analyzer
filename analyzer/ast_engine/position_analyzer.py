"""
Position Connascence Analyzer - CoP detection
Extracted from ConnascenceASTAnalyzer to reduce God Object violation.
"""

import ast
from typing import List

from ..thresholds import ConnascenceType, Severity
from .base_analyzer import BaseConnascenceAnalyzer
from .violations import Violation


class PositionAnalyzer(BaseConnascenceAnalyzer):
    """Specialized analyzer for Connascence of Position (CoP)."""
    
    def analyze_position_connascence(self, tree: ast.AST) -> List[Violation]:
        """Analyze connascence of position (CoP)."""
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Count positional parameters (excluding self/cls)
                args = node.args.args
                if args and args[0].arg in ["self", "cls"]:
                    args = args[1:]
                
                positional_count = len(args)
                
                if positional_count > self.thresholds.max_positional_params:
                    violations.append(Violation(
                        id="",
                        type=ConnascenceType.POSITION,
                        severity=Severity.HIGH,
                        file_path=self.current_file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        description=f"Function '{node.name}' has {positional_count} positional parameters (>{self.thresholds.max_positional_params})",
                        recommendation="Use keyword arguments, data classes, or parameter objects",
                        code_snippet=self.get_code_snippet(node),
                        function_name=node.name,
                        locality="same_function",
                        context={"parameter_count": positional_count}
                    ))
            
            elif isinstance(node, ast.Call):
                # Check function calls with many positional arguments
                if len(node.args) > self.thresholds.max_positional_params:
                    violations.append(Violation(
                        id="",
                        type=ConnascenceType.POSITION,
                        severity=Severity.MEDIUM,
                        file_path=self.current_file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        description=f"Function call with {len(node.args)} positional arguments",
                        recommendation="Use keyword arguments for better readability",
                        code_snippet=self.get_code_snippet(node),
                        locality="same_module",
                        context={"argument_count": len(node.args)}
                    ))
        
        return violations