# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
Backward compatibility module for constants.

This module re-exports constants from analyzer.constants for backward compatibility.
All new code should import from analyzer.constants directly.
"""

import sys
from pathlib import Path

# Add parent directory to path to import from analyzer
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.constants import (
    EXIT_CODES,
    EXIT_CONFIGURATION_ERROR,
    EXIT_ERROR,
    EXIT_INTERRUPTED,
    EXIT_INVALID_ARGUMENTS,
    EXIT_SUCCESS,
    EXIT_VIOLATIONS_FOUND,
    ExitCode,
)

__all__ = [
    "ExitCode",
    "EXIT_CODES",
    "EXIT_SUCCESS",
    "EXIT_VIOLATIONS_FOUND",
    "EXIT_ERROR",
    "EXIT_INVALID_ARGUMENTS",
    "EXIT_CONFIGURATION_ERROR",
    "EXIT_INTERRUPTED",
]
