"""
Constants for connascence analysis - Extracted to reduce CoM (Magic Literals)

This module centralizes magic literals that were scattered throughout the codebase,
reducing Connascence of Meaning and improving maintainability.
"""

from typing import Set

# Threshold defaults
DEFAULT_MAX_POSITIONAL_PARAMS = 4
DEFAULT_GOD_CLASS_METHODS = 20
DEFAULT_MAX_CYCLOMATIC_COMPLEXITY = 10
DEFAULT_MAX_METHOD_LINES = 50
DEFAULT_MAX_CLASS_LINES = 300
DEFAULT_GOD_CLASS_LINES = 300

# Weight configuration defaults
DEFAULT_CRITICAL_WEIGHT = 5.0
DEFAULT_HIGH_WEIGHT = 3.0
DEFAULT_MEDIUM_WEIGHT = 2.0
DEFAULT_LOW_WEIGHT = 1.0

# Locality multipliers
LOCALITY_SAME_FUNCTION = 1.0
LOCALITY_SAME_CLASS = 1.2
LOCALITY_SAME_MODULE = 1.5
LOCALITY_CROSS_MODULE = 2.0

# Type multipliers
TYPE_MULTIPLIER_NAME = 0.9
TYPE_MULTIPLIER_TYPE = 0.8
TYPE_MULTIPLIER_MEANING = 1.1
TYPE_MULTIPLIER_POSITION = 1.3
TYPE_MULTIPLIER_ALGORITHM = 1.4
TYPE_MULTIPLIER_IDENTITY = 1.5

# Magic literal exceptions (common acceptable values)
MAGIC_LITERAL_EXCEPTIONS: Set = {0, 1, -1, 2, '', None, True, False}

# Policy preset names
STRICT_CORE_POLICY = "strict-core"
SERVICE_DEFAULTS_POLICY = "service-defaults"
EXPERIMENTAL_POLICY = "experimental"

# Severity ordering
SEVERITY_ORDER = {
    'low': 0,
    'medium': 1,
    'high': 2,
    'critical': 3
}

# Analysis configuration limits
MAX_COMPLEXITY_CRITICAL = 15
MAX_COMPLEXITY_HIGH = 10
MAX_PARAMETERS_CRITICAL = 8
MAX_PARAMETERS_HIGH = 5

# File analysis defaults
DEFAULT_ANALYSIS_TIMEOUT_MS = 30000
DEFAULT_FILE_SIZE_LIMIT_MB = 10
MAX_VIOLATIONS_PER_FILE = 1000