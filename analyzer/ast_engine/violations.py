"""
Violation and Result data structures
Extracted from core_analyzer.py to support refactoring.
"""

import ast
import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..thresholds import ConnascenceType, Severity


@dataclass
class Violation:
    """Represents a detected connascence violation."""
    
    id: str                          # Unique fingerprint
    type: ConnascenceType           
    severity: Severity
    file_path: str
    line_number: int
    column: int
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    
    # Context information
    description: str = ""
    recommendation: str = ""
    code_snippet: str = ""
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    
    # Metrics
    weight: float = 1.0
    locality: str = "same_module"  # same_function, same_class, same_module, cross_module
    
    # Additional context
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}
        
        # Generate stable fingerprint
        if not self.id:
            self.id = self._generate_fingerprint()
    
    def _generate_fingerprint(self) -> str:
        """Generate stable fingerprint for violation deduplication."""
        components = [
            self.type.value,
            self.file_path,
            str(self.line_number),
            str(self.column),
            self.description[:50],  # First 50 chars of description
        ]
        content = "|".join(components)
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    @property
    def connascence_type(self) -> str:
        """Backward compatibility property for tests."""
        return self.type.value
    
    @property
    def rule_id(self) -> str:
        """Generate rule ID for compatibility."""
        return f"CON_{self.type.value}"


@dataclass
class AnalysisResult:
    """Results of connascence analysis."""
    
    violations: List[Violation]
    total_files: int = 0
    analysis_time: float = 0.0
    connascence_index: float = 0.0
    
    # Advanced fields
    timestamp: str = ""
    project_root: str = ""
    total_files_analyzed: int = 0
    analysis_duration_ms: int = 0
    file_stats: Dict[str, Dict[str, Any]] = None
    summary_metrics: Dict[str, Any] = None
    policy_preset: Optional[str] = None
    budget_status: Optional[Dict[str, Any]] = None
    baseline_comparison: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.file_stats is None:
            self.file_stats = {}
        if self.summary_metrics is None:
            self.summary_metrics = {}
        # Backward compatibility
        if self.total_files == 0:
            self.total_files = self.total_files_analyzed
        if self.analysis_time == 0.0:
            self.analysis_time = self.analysis_duration_ms / 1000.0
    
    @property
    def total_violations(self) -> int:
        """Total number of violations."""
        return len(self.violations)
    
    @property
    def critical_count(self) -> int:
        """Number of critical violations."""
        return len([v for v in self.violations if v.severity == Severity.CRITICAL])
    
    @property
    def high_count(self) -> int:
        """Number of high severity violations."""
        return len([v for v in self.violations if v.severity == Severity.HIGH])
    
    @property
    def medium_count(self) -> int:
        """Number of medium severity violations."""
        return len([v for v in self.violations if v.severity == Severity.MEDIUM])
    
    @property
    def low_count(self) -> int:
        """Number of low severity violations."""
        return len([v for v in self.violations if v.severity == Severity.LOW])
    
    @property
    def violations_by_type(self) -> Dict[str, int]:
        """Count violations by type."""
        counts = {}
        for violation in self.violations:
            type_key = violation.type.value
            counts[type_key] = counts.get(type_key, 0) + 1
        return counts