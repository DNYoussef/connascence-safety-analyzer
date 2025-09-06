# SPDX-License-Identifier: MIT
"""
Shared Components Across All Interfaces

Minimal shared functionality to eliminate duplication between CLI, Web, and VSCode interfaces.
"""

from pathlib import Path
import sys
from typing import Any, Dict, Optional

# Import core analyzer
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from analyzer.core import ConnascenceAnalyzer


class SharedAnalysisEngine:
    """Shared analysis engine used by all interfaces."""

    def __init__(self):
        self.analyzer = ConnascenceAnalyzer()

    def analyze_path(self, path: str, policy: str = "default", **kwargs) -> Dict[str, Any]:
        """Common analysis entry point for all interfaces."""
        return self.analyzer.analyze_path(path=path, policy=policy, **kwargs)


class SharedFormatter:
    """Shared formatting utilities for all interfaces."""

    @staticmethod
    def format_summary_stats(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and format common summary statistics."""
        summary = analysis_result.get('summary', {})
        return {
            'total_violations': summary.get('total_violations', 0),
            'critical_violations': summary.get('critical_violations', 0),
            'high_violations': summary.get('high_violations', 0),
            'medium_violations': summary.get('medium_violations', 0),
            'low_violations': summary.get('low_violations', 0),
            'files_analyzed': analysis_result.get('metrics', {}).get('files_analyzed', 0),
            'analysis_time': analysis_result.get('metrics', {}).get('analysis_time', 0)
        }

    @staticmethod
    def get_severity_color(severity: str) -> str:
        """Get color code for severity level."""
        colors = {
            'critical': '#d73a49',
            'high': '#f66a0a',
            'medium': '#dbab09',
            'low': '#28a745'
        }
        return colors.get(severity, '#6c757d')


class SharedValidation:
    """Shared validation utilities."""

    @staticmethod
    def validate_path(path: str) -> tuple[bool, Optional[str]]:
        """Validate if path exists and is analyzable."""
        path_obj = Path(path)
        if not path_obj.exists():
            return False, f"Path does not exist: {path}"

        if path_obj.is_file() and path_obj.suffix != ".py":
            return False, f"File is not a Python file: {path}"

        if path_obj.is_dir() and not any(path_obj.rglob('*.py')):
            return False, f"Directory contains no Python files: {path}"

        return True, None

    @staticmethod
    def validate_policy(policy: str) -> tuple[bool, Optional[str]]:
        """Validate policy name."""
        valid_policies = ['default', 'strict-core', 'nasa_jpl_pot10', 'lenient']
        if policy not in valid_policies:
            return False, f"Invalid policy: {policy}. Valid options: {valid_policies}"
        return True, None


# Singleton instances for shared use
analysis_engine = SharedAnalysisEngine()
formatter = SharedFormatter()
validator = SharedValidation()
