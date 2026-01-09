"""
Formal Grammar Constants
========================

Extracted magic literals from formal_grammar.py for better maintainability.
Phase 5 Remediation - CoM (Connascence of Meaning) reduction.
"""

# =============================================================================
# Severity Calculation Constants
# =============================================================================

# Base severity score for magic literal violations
BASE_SEVERITY_SCORE = 5.0

# Severity multipliers for different contexts
SEVERITY_MULTIPLIER_CONSTANT = 0.3  # Constants are less problematic
SEVERITY_MULTIPLIER_CONFIGURATION = 0.5  # Config values are expected
SEVERITY_MULTIPLIER_CONDITIONAL = 1.5  # Conditionals are high-risk
SEVERITY_MULTIPLIER_BUSINESS_LOGIC = 1.3  # Business logic needs clarity
SEVERITY_MULTIPLIER_LOOP_SMALL_INT = 0.7  # Small loop counters are common
SEVERITY_MULTIPLIER_SHORT_STRING = 0.6  # Very short strings are less problematic
SEVERITY_MULTIPLIER_URL_PATH = 0.4  # URLs and paths are often legitimate

# Threshold for "small" integers in loops
SMALL_INTEGER_THRESHOLD = 10

# Threshold for "short" strings
SHORT_STRING_LENGTH = 5

# =============================================================================
# Severity Score Thresholds
# =============================================================================

# Thresholds for skip/low/medium/high severity
SEVERITY_THRESHOLD_SKIP = 2.0  # Below this, skip the violation
SEVERITY_THRESHOLD_HIGH = 8.0  # Above this, mark as high severity
SEVERITY_THRESHOLD_MEDIUM = 5.0  # Above this, mark as medium severity

# =============================================================================
# Buffer Size Constants (Powers of 2)
# =============================================================================

BUFFER_SIZE_TINY = 12
BUFFER_SIZE_SMALL = 16
BUFFER_SIZE_MEDIUM = 24
BUFFER_SIZE_DEFAULT = 32
BUFFER_SIZE_MEDIUM_LARGE = 48
BUFFER_SIZE_LARGE = 64
BUFFER_SIZE_128 = 128
BUFFER_SIZE_256 = 256
BUFFER_SIZE_512 = 512
BUFFER_SIZE_1K = 1024
BUFFER_SIZE_2K = 2048
BUFFER_SIZE_4K = 4096
BUFFER_SIZE_8K = 8192
BUFFER_SIZE_16K = 16384

# =============================================================================
# Confidence and Quality Thresholds
# =============================================================================

CONFIDENCE_THRESHOLD_LOW = 0.5
CONFIDENCE_THRESHOLD_MEDIUM = 0.7
CONFIDENCE_THRESHOLD_HIGH = 0.9

# Maximum limits
MAX_COMPLEXITY_SCORE = 100
MAX_FUNCTION_LINES_THRESHOLD = 1000

# =============================================================================
# String Pattern Indicators
# =============================================================================

URL_PATH_PATTERNS = ("http", "/", ".", "@")
