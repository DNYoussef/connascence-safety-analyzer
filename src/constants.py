# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
Constants module for connascence analysis.

Provides shared constants and configuration values for the connascence
analysis system.
"""

# Version information
__version__ = "1.0.0"
__version_info__ = (1, 0, 0)

# Analysis constants
DEFAULT_MAX_COMPLEXITY = 10
DEFAULT_MAX_PARAMS = 4
DEFAULT_GOD_CLASS_THRESHOLD = 20

# Connascence types
CONNASCENCE_TYPES = [
    "CoN",  # Name
    "CoT",  # Type
    "CoM",  # Meaning
    "CoP",  # Position
    "CoA",  # Algorithm
    "CoE",  # Execution
    "CoTm", # Timing
    "CoV",  # Value
    "CoI",  # Identity
]

# Severity levels
SEVERITY_LEVELS = ["low", "medium", "high", "critical"]

# File patterns
PYTHON_EXTENSIONS = [".py", ".pyx", ".pyi"]
EXCLUDED_PATTERNS = [
    "__pycache__",
    ".pyc",
    ".git",
    ".venv",
    "venv",
    "node_modules",
]

# Exit codes
EXIT_SUCCESS = 0
EXIT_VIOLATIONS_FOUND = 1
EXIT_ERROR = 2
EXIT_INVALID_ARGUMENTS = 3
EXIT_CONFIGURATION_ERROR = 4
EXIT_INTERRUPTED = 130