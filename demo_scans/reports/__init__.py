"""
Enterprise Reporting System

This module provides comprehensive reporting capabilities for connascence analysis,
supporting multiple output formats required by different tools and workflows.

Supported Formats:
- SARIF 2.1.0: For GitHub Code Scanning, Azure DevOps, and other security platforms  
- JSON: Machine-readable format for tools and agents
- Markdown: Human-readable summaries for PR comments
- HTML: Rich interactive reports
- CSV: For data analysis and metrics tracking

Key Features:
- Stable fingerprints for violation deduplication
- Rich context and metadata
- Trend analysis and scorecards
- Integration-ready outputs
"""

from .json_export import JSONReporter
from .sarif_export import SARIFReporter
from .md_summary import MarkdownReporter
from .scorecard import ScorecardGenerator

__all__ = [
    "JSONReporter",
    "SARIFReporter", 
    "MarkdownReporter",
    "ScorecardGenerator",
]