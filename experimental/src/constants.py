#!/usr/bin/env python3

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
Central Constants Module

Consolidates all magic literals, exit codes, and configuration constants
to reduce Connascence of Meaning (CoM) violations across the codebase.
"""

from enum import Enum, IntEnum
from typing import Dict, List


class ExitCode(IntEnum):
    """Standard exit codes for CLI operations."""
    SUCCESS = 0
    GENERAL_ERROR = 1
    CONFIGURATION_ERROR = 2
    RUNTIME_ERROR = 3
    LICENSE_ERROR = 4
    USER_INTERRUPTED = 130


class SeverityLevel(Enum):
    """Connascence violation severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConnascenceType(Enum):
    """Types of connascence violations."""
    NAME = "CoN"
    TYPE = "CoT"
    MEANING = "CoM"
    POSITION = "CoP"
    ALGORITHM = "CoA"
    TIMING = "CoTm"
    VALUE = "CoV"
    IDENTITY = "CoI"


class AnalysisLimits:
    """Analysis threshold constants."""
    MAX_FUNCTION_PARAMETERS = 4
    MAX_CONDITIONAL_COMPLEXITY = 3
    MAX_FUNCTION_LINES = 60
    MAX_CLASS_METHODS = 20
    MAX_CLASS_LINES = 500
    MIN_MAGIC_NUMBER_THRESHOLD = 2
    MAX_COGNITIVE_COMPLEXITY = 10


class FileSizeThresholds:
    """File size thresholds for god object detection."""
    SMALL_FILE = 100
    MEDIUM_FILE = 300
    LARGE_FILE = 500
    GOD_OBJECT_FILE = 1000


class OutputFormats:
    """Supported output formats."""
    TEXT = "text"
    JSON = "json"
    SARIF = "sarif"
    MARKDOWN = "markdown"


class PolicyPresets:
    """Available policy preset names."""
    STRICT_CORE = "strict-core"
    SERVICE_DEFAULTS = "service-defaults"
    EXPERIMENTAL = "experimental"


class SafetyProfiles:
    """General Safety and safety profile constants."""
    GENERAL_SAFETY_STRICT = "general_safety_strict"
    SAFETY_LEVEL_1 = "safety_level_1"
    SAFETY_LEVEL_3 = "safety_level_3"
    MODERN_GENERAL = "modern_general"


class FrameworkProfiles:
    """Framework-specific analysis profiles."""
    DJANGO = "django"
    FASTAPI = "fastapi"
    REACT = "react"
    GENERIC = "generic"


class MCPTransports:
    """MCP server transport protocols."""
    STDIO = "stdio"
    SSE = "sse"
    WEBSOCKET = "websocket"


class AnalysisMessages:
    """Common analysis messages and descriptions."""
    MAGIC_NUMBER_DESC = "Magic number found - extract to named constant"
    POSITION_COUPLING_DESC = "Too many positional arguments - use keyword arguments"
    GOD_OBJECT_DESC = "Class exceeds size threshold - consider splitting responsibilities"
    COMPLEX_CONDITION_DESC = "Complex conditional logic - consider strategy pattern"
    HARDCODED_STRING_DESC = "Hardcoded string constant - extract to configuration"


class SkipPatterns:
    """File patterns to skip during analysis."""
    PATTERNS: List[str] = [
        "__pycache__",
        ".pytest_cache", 
        "node_modules",
        "venv",
        ".venv",
        "migrations",
        "test_",
        "_test.py",
        ".git",
        "dist",
        "build"
    ]


class DefaultPorts:
    """Default port numbers for various services."""
    MCP_SERVER = 8080
    WEBSOCKET = 8080
    SSE = 8080


class FileExtensions:
    """Programming language file extensions."""
    PYTHON: List[str] = [".py", ".pyi", ".pyw"]
    JAVASCRIPT: List[str] = [".js", ".mjs", ".jsx"]
    TYPESCRIPT: List[str] = [".ts", ".tsx", ".d.ts"]
    C_CPP: List[str] = [".c", ".cpp", ".cxx", ".cc", ".h", ".hpp", ".hxx"]


class ConfigurationDefaults:
    """Default configuration values."""
    VERBOSE_LOGGING = False
    INCREMENTAL_ANALYSIS = False
    BUDGET_CHECK = False
    DRY_RUN = True
    MAX_FIXES = 5
    CONFIDENCE_THRESHOLD = 0.7
    ANALYSIS_TIMEOUT_SECONDS = 300
    QUALITY_SCORE_WEIGHT = {
        "grammar": 0.3,
        "connascence": 0.25,
        "cohesion": 0.25,
        "magic_literals": 0.2
    }


class ValidationMessages:
    """License validation and compliance messages."""
    LICENSE_UNAVAILABLE = "License validation system not available"
    LICENSE_VALIDATION_FAILED = "License validation failed"
    LICENSE_VALIDATION_PASSED = "License validation passed"
    USE_LICENSE_VALIDATE_CMD = "Use 'connascence license validate' for detailed report"


class ReportHeaders:
    """Report formatting constants."""
    SEPARATOR = "=" * 80
    ANALYSIS_HEADER = "CONNASCENCE ANALYSIS REPORT"
    QUALITY_HEADER = "CODE QUALITY ASSESSMENT"
    BASELINE_HEADER = "BASELINE COMPARISON REPORT"


class TimingConstants:
    """Timing and performance constants."""
    MILLISECONDS_PER_SECOND = 1000
    DEFAULT_TIMEOUT_MS = 300000  # 5 minutes
    CACHE_TIMEOUT_SECONDS = 3600  # 1 hour
    ANALYSIS_POLLING_INTERVAL = 100  # ms


class NetworkDefaults:
    """Network and server defaults."""
    LOCALHOST = "localhost"
    DEFAULT_HOST = "localhost"
    CONNECTION_TIMEOUT = 30
    READ_TIMEOUT = 60


class MemoryConstants:
    """Memory management constants."""
    DEFAULT_MEMORY_LIMIT_MB = 512
    LARGE_FILE_THRESHOLD_MB = 50
    MAX_CACHE_SIZE_ENTRIES = 1000


class QualityThresholds:
    """Quality score thresholds."""
    EXCELLENT_QUALITY = 0.9
    GOOD_QUALITY = 0.8
    ACCEPTABLE_QUALITY = 0.6
    POOR_QUALITY = 0.4


# Convenience mappings for backward compatibility
EXIT_CODES = {
    "success": ExitCode.SUCCESS,
    "error": ExitCode.GENERAL_ERROR,
    "config_error": ExitCode.CONFIGURATION_ERROR,
    "runtime_error": ExitCode.RUNTIME_ERROR,
    "license_error": ExitCode.LICENSE_ERROR,
    "interrupted": ExitCode.USER_INTERRUPTED
}

SEVERITY_ORDER = {
    SeverityLevel.LOW: 0,
    SeverityLevel.MEDIUM: 1,
    SeverityLevel.HIGH: 2,
    SeverityLevel.CRITICAL: 3
}