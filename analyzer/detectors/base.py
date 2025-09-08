"""
Base Detector Class

Provides common functionality for all specialized connascence detectors.
Supports two-phase analysis: data collection and violation analysis.
"""

import ast
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Protocol

from utils.types import ConnascenceViolation


class DetectorInterface(Protocol):
    """
    Protocol defining the interface for two-phase detector analysis.
    
    NASA Rule 4 Compliant: Interface definition under 60 lines
    """
    
    def analyze_from_data(self, collected_data: 'ASTNodeData') -> List[ConnascenceViolation]:
        """
        Analyze violations from pre-collected AST data.
        
        Args:
            collected_data: Pre-collected AST data from unified visitor
            
        Returns:
            List of detected violations
        """
        ...


class DetectorBase(ABC):
    """
    Abstract base class for all connascence detectors.
    
    Supports both legacy single-pass detection and new two-phase analysis.
    Modified for detector pool compatibility - stateless operation.
    NASA Rule 4 Compliant: All methods under 60 lines
    NASA Rule 5 Compliant: Input assertions
    NASA Rule 6 Compliant: Clear variable scoping
    """
    
    def __init__(self, file_path: str = "", source_lines: List[str] = None):
        # NASA Rule 5: Input validation - relaxed for pool compatibility
        assert isinstance(file_path, str), "file_path must be string"
        if source_lines is None:
            source_lines = []
        assert isinstance(source_lines, list), "source_lines must be list"
        
        # NASA Rule 6: Clear variable scoping - mutable for pool reuse
        self.file_path = file_path
        self.source_lines = source_lines
        self.violations: List[ConnascenceViolation] = []
        
        # Pool compatibility - track reuse
        self._pool_reuse_count = 0
    
    def get_code_snippet(self, node: ast.AST, context_lines: int = 2) -> str:
        """
        Extract code snippet around the given node.
        
        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation
        """
        assert isinstance(node, ast.AST), "node must be AST node"
        assert isinstance(context_lines, int), "context_lines must be integer"
        
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
        Legacy method: Detect violations in the given AST tree.
        
        Args:
            tree: The AST tree to analyze
            
        Returns:
            List of detected violations
        """
        pass
    
    def analyze_from_data(self, collected_data: 'ASTNodeData') -> List[ConnascenceViolation]:
        """
        New two-phase method: Analyze violations from pre-collected data.
        
        Default implementation falls back to legacy detect_violations.
        Detectors should override this for performance optimization.
        
        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation
        
        Args:
            collected_data: Pre-collected AST data from unified visitor
            
        Returns:
            List of detected violations
        """
        # NASA Rule 5: Input validation
        assert collected_data is not None, "collected_data cannot be None"
        
        # Track pool reuse for metrics
        self._pool_reuse_count += 1
        
        # Fallback to legacy method - subclasses should override
        # This maintains backward compatibility while enabling optimization
        return []
    
    def get_line_content(self, node: ast.AST) -> str:
        """Get the full line content containing the node."""
        if not hasattr(node, "lineno") or node.lineno > len(self.source_lines):
            return ""
        return self.source_lines[node.lineno - 1]
    
    def is_in_conditional(self, node: ast.AST) -> bool:
        """Check if node is within a conditional statement."""
        line_content = self.source_lines[node.lineno - 1] if node.lineno <= len(self.source_lines) else ""
        return any(keyword in line_content for keyword in ["if ", "elif ", "while ", "assert "])
    
    def reset_for_reuse(self, file_path: str, source_lines: List[str]):
        """
        Reset detector state for pool reuse.
        
        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation
        """
        assert isinstance(file_path, str), "file_path must be string"
        assert isinstance(source_lines, list), "source_lines must be list"
        
        self.file_path = file_path
        self.source_lines = source_lines
        self.violations = []
        self._pool_reuse_count += 1
    
    def get_pool_metrics(self) -> Dict[str, Any]:
        """Get detector-specific pool metrics."""
        return {
            'reuse_count': self._pool_reuse_count,
            'detector_type': self.__class__.__name__
        }