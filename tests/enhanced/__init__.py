# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
Enhanced Pipeline Integration Tests
==================================

Comprehensive test suite for enhanced pipeline integration across all interfaces:

- test_infrastructure.py: Enhanced test datasets, utilities, and mock analyzers
- test_vscode_integration.py: VSCode extension enhanced pipeline integration tests  
- test_mcp_server_integration.py: MCP server enhanced pipeline integration tests
- test_web_dashboard_integration.py: Web dashboard enhanced visualization tests
- test_cli_integration.py: CLI interface enhanced features integration tests

This test suite validates the complete enhanced pipeline integration including:
- Cross-phase correlation analysis
- Smart architectural recommendations
- Analysis audit trails with timing data
- Enhanced AI-powered fix generation
- Real-time visualization and data streaming
"""

__version__ = "1.0.0"
__author__ = "Connascence Safety Analyzer Contributors"

# Import key test infrastructure for easy access
from .test_infrastructure import (
    EnhancedTestDatasets,
    MockEnhancedAnalyzer, 
    EnhancedTestUtilities,
    MockCorrelation,
    MockSmartRecommendation,
    MockAuditTrailEntry,
    integration_test,
    performance_test
)

__all__ = [
    "EnhancedTestDatasets",
    "MockEnhancedAnalyzer",
    "EnhancedTestUtilities", 
    "MockCorrelation",
    "MockSmartRecommendation",
    "MockAuditTrailEntry",
    "integration_test",
    "performance_test"
]