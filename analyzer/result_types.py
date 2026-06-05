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
Result Types Module
===================

Dataclasses for analysis results and error handling.
Extracted from unified_analyzer.py for NASA Rule 4 compliance.

Contains:
- StandardError: Standard error response format
- UnifiedAnalysisResult: Complete analysis result from all phases
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

# Import constants
try:
    from .constants import ERROR_SEVERITY
except ImportError:
    from constants import ERROR_SEVERITY


@dataclass
class StandardError:
    """Standard error response format across all integrations."""

    code: int
    message: str
    severity: str
    timestamp: str
    integration: str
    error_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestions: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class UnifiedAnalysisResult:
    """Complete analysis result from all Phase 1-6 components."""

    # Core results
    connascence_violations: List[Dict[str, Any]]
    duplication_clusters: List[Dict[str, Any]]
    nasa_violations: List[Dict[str, Any]]

    # Summary metrics
    total_violations: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int

    # Quality scores
    connascence_index: float
    nasa_compliance_score: float
    duplication_score: float
    overall_quality_score: float

    # Analysis metadata
    project_path: str
    policy_preset: str
    analysis_duration_ms: int
    files_analyzed: int
    timestamp: str

    # Recommendations
    priority_fixes: List[str]
    improvement_actions: List[str]

    # Error tracking
    errors: List[StandardError] = None
    warnings: List[StandardError] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    def has_errors(self) -> bool:
        """Check if analysis has any errors."""
        return bool(self.errors)

    def has_critical_errors(self) -> bool:
        """Check if analysis has critical errors."""
        if not self.errors:
            return False
        return any(error.severity == ERROR_SEVERITY["CRITICAL"] for error in self.errors)

    def get_violation_summary(self) -> Dict[str, int]:
        """Get summary of violations by severity."""
        return {
            "critical": self.critical_count,
            "high": self.high_count,
            "medium": self.medium_count,
            "low": self.low_count,
            "total": self.total_violations,
        }

    def is_passing(self, threshold: float = 0.7) -> bool:
        """Check if analysis passes quality threshold."""
        return self.overall_quality_score >= threshold


__all__ = ["StandardError", "UnifiedAnalysisResult"]
