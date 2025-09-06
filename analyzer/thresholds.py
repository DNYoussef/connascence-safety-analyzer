# SPDX-License-Identifier: MIT
"""
Connascence Type Definitions and Thresholds

Defines the various types of connascence and their severity thresholds.
"""

from enum import Enum


class ConnascenceType(Enum):
    """Types of connascence for analysis."""
    
    # Static Connascence (easier to detect and fix)
    NAME = "CoN"           # Connascence of Name
    TYPE = "CoT"           # Connascence of Type  
    MEANING = "CoM"        # Connascence of Meaning (magic numbers/strings)
    POSITION = "CoP"       # Connascence of Position (parameter order)
    ALGORITHM = "CoA"      # Connascence of Algorithm
    
    # Dynamic Connascence (harder to detect and fix)
    EXECUTION = "CoE"      # Connascence of Execution (timing)
    VALUE = "CoV"          # Connascence of Value (shared state)
    IDENTITY = "CoI"       # Connascence of Identity (shared objects)
    
    # Derived types commonly used in analysis
    PARAMETER = "CoParam"  # Parameter-related connascence
    STATE = "CoState"      # State-related connascence
    TIMING = "CoTiming"    # Timing-related connascence


class SeverityLevel(Enum):
    """Severity levels for violations."""
    
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Default severity mappings for connascence types
DEFAULT_SEVERITY_MAP = {
    ConnascenceType.NAME: SeverityLevel.MEDIUM,
    ConnascenceType.TYPE: SeverityLevel.MEDIUM,
    ConnascenceType.MEANING: SeverityLevel.HIGH,
    ConnascenceType.POSITION: SeverityLevel.HIGH,
    ConnascenceType.ALGORITHM: SeverityLevel.CRITICAL,
    ConnascenceType.EXECUTION: SeverityLevel.CRITICAL,
    ConnascenceType.VALUE: SeverityLevel.HIGH,
    ConnascenceType.IDENTITY: SeverityLevel.HIGH,
    ConnascenceType.PARAMETER: SeverityLevel.MEDIUM,
    ConnascenceType.STATE: SeverityLevel.HIGH,
    ConnascenceType.TIMING: SeverityLevel.CRITICAL,
}


# Weight values for calculating connascence index
DEFAULT_WEIGHT_MAP = {
    SeverityLevel.CRITICAL: 10.0,
    SeverityLevel.HIGH: 5.0,
    SeverityLevel.MEDIUM: 2.0,
    SeverityLevel.LOW: 1.0,
}


def get_connascence_severity(conn_type: ConnascenceType) -> SeverityLevel:
    """Get default severity level for a connascence type."""
    return DEFAULT_SEVERITY_MAP.get(conn_type, SeverityLevel.MEDIUM)


def get_severity_weight(severity: SeverityLevel) -> float:
    """Get numerical weight for a severity level."""
    return DEFAULT_WEIGHT_MAP.get(severity, 1.0)


# NASA Power of Ten rule mappings
NASA_POT_MAPPINGS = {
    "POT10_1": ConnascenceType.ALGORITHM,    # No gotos
    "POT10_2": ConnascenceType.EXECUTION,    # No dynamic memory allocation  
    "POT10_3": ConnascenceType.STATE,        # No recursive functions
    "POT10_4": ConnascenceType.PARAMETER,    # Function parameters
    "POT10_5": ConnascenceType.MEANING,      # Magic numbers
    "POT10_6": ConnascenceType.TYPE,         # Strong typing
    "POT10_7": ConnascenceType.VALUE,        # Shared variables
    "POT10_8": ConnascenceType.TIMING,       # Real-time constraints
    "POT10_9": ConnascenceType.IDENTITY,     # Object identity
    "POT10_10": ConnascenceType.NAME,        # Naming conventions
}