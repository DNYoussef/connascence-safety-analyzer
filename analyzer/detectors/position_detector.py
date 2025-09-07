"""
Position Detector

Detects Connascence of Position violations - functions with too many positional parameters.
"""

import ast
from typing import List

from utils.types import ConnascenceViolation
from base import DetectorBase


class PositionDetector(DetectorBase):
    """Detects functions with excessive positional parameters."""
    
    MAX_POSITIONAL_PARAMS = 3
    
    def detect_violations(self, tree: ast.AST) -> List[ConnascenceViolation]:
        """
        Detect functions with too many positional parameters.
        
        Args:
            tree: AST tree to analyze
            
        Returns:
            List of position-related violations
        """
        self.violations.clear()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self._check_function_parameters(node)
        
        return self.violations
    
    def _check_function_parameters(self, node: ast.FunctionDef) -> None:
        """Check if function has too many positional parameters."""
        # Count non-underscore positional parameters
        positional_count = sum(1 for arg in node.args.args if not arg.arg.startswith("_"))
        
        if positional_count > self.MAX_POSITIONAL_PARAMS:
            self.violations.append(
                ConnascenceViolation(
                    type="connascence_of_position",
                    severity="high",
                    file_path=self.file_path,
                    line_number=node.lineno,
                    column=node.col_offset,
                    description=f"Function '{node.name}' has {positional_count} positional parameters (>{self.MAX_POSITIONAL_PARAMS})",
                    recommendation="Consider using keyword arguments, data classes, or parameter objects",
                    code_snippet=self.get_code_snippet(node),
                    context={
                        "parameter_count": positional_count,
                        "function_name": node.name,
                        "threshold": self.MAX_POSITIONAL_PARAMS
                    },
                )
            )