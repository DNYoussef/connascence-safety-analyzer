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

# ScorecardGenerator not yet implemented
# from .scorecard import ScorecardGenerator

__all__ = [
    "JSONReporter",
    "SARIFReporter", 
    "MarkdownReporter",
    # "ScorecardGenerator",
]