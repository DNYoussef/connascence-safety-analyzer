"""
Base Connascence Analyzer - Core functionality
Extracted from ConnascenceASTAnalyzer to reduce God Object violation.
"""

import ast
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..thresholds import (
    ThresholdConfig, WeightConfig, PolicyPreset, 
    DEFAULT_THRESHOLDS, DEFAULT_WEIGHTS
)
from .violations import Violation, AnalysisResult

logger = logging.getLogger(__name__)


class BaseConnascenceAnalyzer:
    """Base class providing core analysis infrastructure."""
    
    def __init__(
        self, 
        thresholds: Optional[ThresholdConfig] = None,
        weights: Optional[WeightConfig] = None,
        policy_preset: Optional[PolicyPreset] = None,
        exclusions: Optional[List[str]] = None
    ):
        self.thresholds = thresholds or DEFAULT_THRESHOLDS
        self.weights = weights or DEFAULT_WEIGHTS
        self.policy_preset = policy_preset
        self.exclusions = exclusions or self._default_exclusions()
        
        # Analysis state
        self.violations: List[Violation] = []
        self.file_stats: Dict[str, Dict[str, Any]] = {}
        self.current_file_path: str = ""
        self.current_source_lines: List[str] = []
        
        # Performance tracking
        self.analysis_start_time = 0.0
    
    def _default_exclusions(self) -> List[str]:
        """Default exclusion patterns."""
        return [
            "test_*", "tests/", "*_test.py", "conftest.py",
            "deprecated/", "archive/", "experimental/",
            "__pycache__/", ".git/", "build/", "dist/",
            "*.egg-info/", "venv*/", "*env*/", "node_modules/",
            # Exclude third-party demonstration code from quality analysis
            "third-party/", "**/third-party/**", "demonstrations/third-party/**",
            # Exclude legacy sales/demo directories (now consolidated)
            "sale/demos/*/", "demo_scans/", "data-room/demo/",
            # Focus analysis on our core production code
        ]
    
    def should_analyze_file(self, file_path: Path) -> bool:
        """Check if file should be analyzed based on exclusions."""
        path_str = str(file_path).replace("\\", "/")  # Normalize path separators
        
        for exclusion in self.exclusions:
            if exclusion.endswith("/"):
                if exclusion[:-1] in path_str:
                    return False
            elif "*" in exclusion:
                import fnmatch
                if fnmatch.fnmatch(path_str, exclusion):
                    return False
            elif exclusion in path_str:
                return False
        return True
    
    def get_code_snippet(self, node: ast.AST, context_lines: int = 2) -> str:
        """Extract code snippet around the given node."""
        if not hasattr(node, "lineno"):
            return ""
        
        start_line = max(0, node.lineno - context_lines - 1)
        end_line = min(len(self.current_source_lines), node.lineno + context_lines)
        
        lines = []
        for i in range(start_line, end_line):
            marker = ">>>" if i == node.lineno - 1 else "   "
            lines.append(f"{marker} {i+1:3d}: {self.current_source_lines[i]}")
        
        return "\n".join(lines)
    
    def get_context_lines(self, line_number: int, context: int = 2) -> str:
        """Get context lines around the given line number."""
        start = max(0, line_number - context - 1)
        end = min(len(self.current_source_lines), line_number + context)
        return "\n".join(self.current_source_lines[start:end])
    
    def calculate_file_stats(self, tree: ast.AST, violations: List[Violation]) -> Dict[str, Any]:
        """Calculate statistics for the analyzed file."""
        stats = {
            "violations_count": len(violations),
            "violations_by_type": {},
            "violations_by_severity": {},
            "functions_count": 0,
            "classes_count": 0,
            "lines_of_code": len(self.current_source_lines),
        }
        
        # Count violations by type and severity
        for violation in violations:
            type_key = violation.type.value
            severity_key = violation.severity.value
            
            stats["violations_by_type"][type_key] = stats["violations_by_type"].get(type_key, 0) + 1
            stats["violations_by_severity"][severity_key] = stats["violations_by_severity"].get(severity_key, 0) + 1
        
        # Count AST elements
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                stats["functions_count"] += 1
            elif isinstance(node, ast.ClassDef):
                stats["classes_count"] += 1
        
        return stats
    
    def calculate_summary_metrics(self, violations: List[Violation]) -> Dict[str, Any]:
        """Calculate overall summary metrics."""
        total_violations = len(violations)
        total_weight = sum(v.weight for v in violations)
        
        metrics = {
            "total_violations": total_violations,
            "total_weight": total_weight,
            "average_weight": total_weight / max(1, total_violations),
            "violations_by_type": {},
            "violations_by_severity": {},
            "violations_by_locality": {},
        }
        
        for violation in violations:
            # By type
            type_key = violation.type.value
            metrics["violations_by_type"][type_key] = metrics["violations_by_type"].get(type_key, 0) + 1
            
            # By severity
            severity_key = violation.severity.value
            metrics["violations_by_severity"][severity_key] = metrics["violations_by_severity"].get(severity_key, 0) + 1
            
            # By locality
            locality_key = violation.locality
            metrics["violations_by_locality"][locality_key] = metrics["violations_by_locality"].get(locality_key, 0) + 1
        
        return metrics