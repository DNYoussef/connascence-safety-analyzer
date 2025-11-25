# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors
"""
CLI Command Handlers Facade Module

This module provides a backward-compatible facade for CLI command handlers,
re-exporting handlers from their actual location in interfaces.cli.connascence.

This allows legacy imports like:
    from src.cli_handlers import ScanCommandHandler

To work by delegating to the actual implementation.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Re-export command handlers from their actual location
from interfaces.cli.connascence import (
    BaseCommandHandler,
    ScanCommandHandler,
    BaselineCommandHandler,
    AutofixCommandHandler,
    MCPCommandHandler,
    ScanDiffCommandHandler,
)

# LicenseCommandHandler was planned but not implemented
# Create a stub for backward compatibility
class LicenseCommandHandler(BaseCommandHandler):
    """
    Stub for LicenseCommandHandler.

    License validation was planned but not fully implemented.
    This stub exists for API compatibility.
    """

    def __init__(self, cli_instance=None):
        super().__init__(cli_instance)
        self._available = False

    def execute(self, args):
        """Execute license validation (not implemented)."""
        print("License validation is not available in this version.")
        return 1

    def is_available(self):
        """Check if license validation is available."""
        return self._available


__all__ = [
    "BaseCommandHandler",
    "ScanCommandHandler",
    "LicenseCommandHandler",
    "BaselineCommandHandler",
    "AutofixCommandHandler",
    "MCPCommandHandler",
    "ScanDiffCommandHandler",
]
