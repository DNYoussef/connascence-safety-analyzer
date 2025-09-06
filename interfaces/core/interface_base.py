# SPDX-License-Identifier: MIT
"""
Base Interface Class

Common functionality and patterns shared across all interface types.
Provides consistent API for CLI, Web, and VSCode interfaces.
"""

import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# Import analyzer components
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from analyzer.core import ConnascenceAnalyzer


@dataclass
class InterfaceConfig:
    """Configuration for interface implementations."""
    interface_type: str
    theme: str = "default"
    verbose: bool = False
    output_format: str = "json"
    policy_preset: str = "service-defaults"
    enable_autofix: bool = True
    enable_ci_integration: bool = False


class InterfaceBase(ABC):
    """Base class for all interface implementations."""
    
    def __init__(self, config: InterfaceConfig):
        self.config = config
        self.analyzer = ConnascenceAnalyzer()
        self._setup_interface()
    
    def _setup_interface(self):
        """Initialize interface-specific setup."""
        pass
    
    @abstractmethod
    def display_results(self, analysis_result: Dict[str, Any]) -> None:
        """Display analysis results in interface-appropriate format."""
        pass
    
    @abstractmethod
    def handle_error(self, error: Exception) -> None:
        """Handle errors in interface-appropriate way."""
        pass
    
    def analyze_path(self, path: str, **kwargs) -> Dict[str, Any]:
        """Common analysis entry point for all interfaces."""
        try:
            return self.analyzer.analyze_path(
                path=path,
                policy=self.config.policy_preset,
                **kwargs
            )
        except Exception as e:
            self.handle_error(e)
            return {
                'success': False,
                'error': str(e),
                'violations': [],
                'summary': {'total_violations': 0}
            }
    
    def get_supported_formats(self) -> List[str]:
        """Get supported output formats for this interface."""
        return ['json', 'sarif', 'markdown', 'text']
    
    def format_summary(self, analysis_result: Dict[str, Any]) -> str:
        """Create a formatted summary appropriate for this interface."""
        if not analysis_result.get('success', True):
            return f"Analysis failed: {analysis_result.get('error', 'Unknown error')}"
        
        summary = analysis_result.get('summary', {})
        total = summary.get('total_violations', 0)
        critical = summary.get('critical_violations', 0)
        
        if total == 0:
            return "✅ No connascence violations found"
        elif critical > 0:
            return f"❌ {total} violations found ({critical} critical)"
        else:
            return f"⚠️  {total} violations found"
    
    def _load_theme(self, theme_name: str) -> Dict[str, Any]:
        """Load theme configuration."""
        themes = {
            'default': {
                'colors': {
                    'critical': '#d73a49',
                    'high': '#f66a0a', 
                    'medium': '#dbab09',
                    'low': '#28a745',
                    'success': '#28a745',
                    'warning': '#f66a0a',
                    'error': '#d73a49'
                }
            },
            'dark': {
                'colors': {
                    'critical': '#ff6b6b',
                    'high': '#ffa500',
                    'medium': '#ffeb3b',
                    'low': '#4caf50',
                    'success': '#4caf50',
                    'warning': '#ffa500', 
                    'error': '#ff6b6b'
                }
            }
        }
        return themes.get(theme_name, themes['default'])


class OutputFormatter:
    """Unified output formatting across interfaces."""
    
    @staticmethod
    def format_violation(violation: Dict[str, Any], interface_type: str) -> str:
        """Format a single violation for display."""
        severity = violation.get('severity', 'medium')
        description = violation.get('description', 'Unknown violation')
        file_path = violation.get('file_path', '')
        line_number = violation.get('line_number', 0)
        
        if interface_type == 'cli':
            return f"[{severity.upper()}] {file_path}:{line_number} - {description}"
        elif interface_type == 'web':
            return f'<div class="violation {severity}">{description}<br><small>{file_path}:{line_number}</small></div>'
        else:  # vscode or other
            return f"{severity}: {description} ({file_path}:{line_number})"
    
    @staticmethod
    def format_summary_table(summary: Dict[str, Any], interface_type: str) -> str:
        """Format summary statistics as table."""
        total = summary.get('total_violations', 0)
        critical = summary.get('critical_violations', 0)
        high = summary.get('high_violations', 0)
        medium = summary.get('medium_violations', 0)
        low = summary.get('low_violations', 0)
        
        if interface_type == 'cli':
            return f"""
Summary:
  Total: {total}
  Critical: {critical}
  High: {high}
  Medium: {medium} 
  Low: {low}
"""
        elif interface_type == 'web':
            return f"""
<table class="summary-table">
  <tr><td>Total</td><td>{total}</td></tr>
  <tr><td>Critical</td><td class="critical">{critical}</td></tr>
  <tr><td>High</td><td class="high">{high}</td></tr>
  <tr><td>Medium</td><td class="medium">{medium}</td></tr>
  <tr><td>Low</td><td class="low">{low}</td></tr>
</table>
"""
        else:
            return f"Total: {total}, Critical: {critical}, High: {high}, Medium: {medium}, Low: {low}"