"""
Base Detector Class

Provides common functionality for all specialized connascence detectors.
"""

import ast
from abc import ABC, abstractmethod
from typing import List, Dict, Any

from utils.types import ConnascenceViolation


class DetectorBase(ABC):
    """Abstract base class for all connascence detectors."""
    
    def __init__(self, file_path: str, source_lines: List[str]):
        self.file_path = file_path
        self.source_lines = source_lines
        self.violations: List[ConnascenceViolation] = []
    
    def get_code_snippet(self, node: ast.AST, context_lines: int = 2) -> str:
        """Extract code snippet around the given node."""
        if not hasattr(node, "lineno"):
            return ""

        start_line = max(0, node.lineno - context_lines - 1)
        end_line = min(len(self.source_lines), node.lineno + context_lines)

        lines = []
        for i in range(start_line, end_line):
            marker = ">>>" if i == node.lineno - 1 else "   "
            lines.append(f"{marker} {i+1:3d}: {self.source_lines[i].rstrip()}")

        return "\n".join(lines)
    
    @abstractmethod
    def detect_violations(self, tree: ast.AST) -> List[ConnascenceViolation]:
        """
        Detect violations in the given AST tree.
        
        Args:
            tree: The AST tree to analyze
            
        Returns:
            List of detected violations
        """
        pass
    
    def get_line_content(self, node: ast.AST) -> str:
        """Get the full line content containing the node."""
        if not hasattr(node, "lineno") or node.lineno > len(self.source_lines):
            return ""
        return self.source_lines[node.lineno - 1]
    
    def is_in_conditional(self, node: ast.AST) -> bool:
        """Check if node is within a conditional statement."""
        line_content = self.source_lines[node.lineno - 1] if node.lineno <= len(self.source_lines) else ""
        return any(keyword in line_content for keyword in ["if ", "elif ", "while ", "assert "])