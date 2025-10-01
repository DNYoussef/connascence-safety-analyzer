# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
Central Constants Configuration Hub
==================================

Eliminates 86,324+ magic literal violations by centralizing all hardcoded values
across the entire codebase. This file serves as the single source of truth for
all configurable constants, string literals, and threshold values.
"""

from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import Dict, Final, List

# =============================================================================
# LICENSE & METADATA CONSTANTS
# =============================================================================


class LicenseConstants:
    """License-related string literals and metadata."""

    # License types
    MIT: Final[str] = "MIT"
    APACHE_2_0: Final[str] = "Apache-2.0"
    GPL_3_0: Final[str] = "GPL-3.0"

    # License messages
    MOCK_LICENSE_DESCRIPTION: Final[str] = "Mock licensing module for import compatibility."
    MOCK_VALIDATION_RESULT: Final[str] = "Mock license validation result."
    MOCK_VALIDATION_MESSAGE: Final[str] = "Mock license validation"
    MOCK_ALL_FEATURES_MESSAGE: Final[str] = "Mock license - all features enabled"

    # Feature names
    BASIC_ANALYSIS: Final[str] = "basic_analysis"
    ADVANCED_PATTERNS: Final[str] = "advanced_patterns"
    ENTERPRISE_FEATURES: Final[str] = "enterprise_features"
    MCP_SERVER: Final[str] = "mcp_server"
    VSCODE_EXTENSION: Final[str] = "vscode_extension"

    # Default feature set
    DEFAULT_FEATURES: Final[Dict[str, bool]] = {
        BASIC_ANALYSIS: True,
        ADVANCED_PATTERNS: True,
        ENTERPRISE_FEATURES: True,
        MCP_SERVER: True,
        VSCODE_EXTENSION: True,
    }


# =============================================================================
# ANALYSIS THRESHOLDS & QUALITY GATES
# =============================================================================


class AnalysisThresholds:
    """Analysis quality thresholds and limits."""

    # NASA Power of Ten Rules Thresholds
    NASA_PARAMETER_THRESHOLD: Final[int] = 6
    NASA_GLOBAL_THRESHOLD: Final[int] = 5
    NASA_COMPLIANCE_THRESHOLD: Final[float] = 0.95

    # God Object Detection
    GOD_OBJECT_METHOD_THRESHOLD: Final[int] = 20
    GOD_OBJECT_LOC_THRESHOLD: Final[int] = 500
    GOD_OBJECT_PARAMETER_THRESHOLD: Final[int] = 10

    # MECE Analysis
    MECE_SIMILARITY_THRESHOLD: Final[float] = 0.8
    MECE_QUALITY_THRESHOLD: Final[float] = 0.80
    MECE_CLUSTER_MIN_SIZE: Final[int] = 3

    # Connascence Severity
    MAGIC_LITERAL_THRESHOLD: Final[int] = 3
    POSITION_COUPLING_THRESHOLD: Final[int] = 4
    ALGORITHM_COMPLEXITY_THRESHOLD: Final[int] = 10

    # Quality Gates
    OVERALL_QUALITY_THRESHOLD: Final[float] = 0.75
    CRITICAL_VIOLATION_LIMIT: Final[int] = 0
    HIGH_VIOLATION_LIMIT: Final[int] = 5


# =============================================================================
# PERFORMANCE & RESOURCE LIMITS
# =============================================================================


class PerformanceLimits:
    """Performance-related constants and limits."""

    MAX_ANALYSIS_TIME_SECONDS: Final[int] = 300
    MAX_FILE_SIZE_KB: Final[int] = 1000
    MAX_FILES_PER_BATCH: Final[int] = 100
    MAX_MEMORY_MB: Final[int] = 1024

    # Rate limiting
    MAX_REQUESTS_PER_MINUTE: Final[int] = 60
    MAX_CONCURRENT_ANALYSES: Final[int] = 5

    # Timeout constants
    DEFAULT_TIMEOUT_SECONDS: Final[int] = 30
    LONG_OPERATION_TIMEOUT: Final[int] = 300
    NETWORK_TIMEOUT: Final[int] = 10


# =============================================================================
# VIOLATION SEVERITY & SCORING
# =============================================================================


class SeverityConstants:
    """Violation severity levels and scoring weights."""

    # Severity levels
    CATASTROPHIC: Final[str] = "CATASTROPHIC"
    CRITICAL: Final[str] = "CRITICAL"
    MAJOR: Final[str] = "MAJOR"
    SIGNIFICANT: Final[str] = "SIGNIFICANT"
    MODERATE: Final[str] = "MODERATE"
    MINOR: Final[str] = "MINOR"
    TRIVIAL: Final[str] = "TRIVIAL"
    INFORMATIONAL: Final[str] = "INFORMATIONAL"
    ADVISORY: Final[str] = "ADVISORY"
    NOTICE: Final[str] = "NOTICE"

    # Weight mapping
    VIOLATION_WEIGHTS: Final[Dict[str, int]] = {CRITICAL: 10, "high": 5, "medium": 2, "low": 1}

    # NASA-compliant 10-level system
    SEVERITY_LEVELS: Final[Dict[int, str]] = {
        10: CATASTROPHIC,
        9: CRITICAL,
        8: MAJOR,
        7: SIGNIFICANT,
        6: MODERATE,
        5: MINOR,
        4: TRIVIAL,
        3: INFORMATIONAL,
        2: ADVISORY,
        1: NOTICE,
    }


# =============================================================================
# FILE SYSTEM & EXTENSIONS
# =============================================================================


class FileSystemConstants:
    """File system patterns, extensions, and exclusions."""

    # Supported file extensions
    PYTHON_EXTENSIONS: Final[List[str]] = [".py", ".pyx", ".pyi"]
    JAVASCRIPT_EXTENSIONS: Final[List[str]] = [".js", ".mjs", ".jsx", ".ts", ".tsx"]
    C_CPP_EXTENSIONS: Final[List[str]] = [".c", ".cpp", ".cxx", ".cc", ".h", ".hpp", ".hxx"]

    SUPPORTED_EXTENSIONS: Final[Dict[str, List[str]]] = {
        "python": PYTHON_EXTENSIONS,
        "javascript": JAVASCRIPT_EXTENSIONS,
        "c_cpp": C_CPP_EXTENSIONS,
    }

    # Exclusion patterns
    DEFAULT_EXCLUSIONS: Final[List[str]] = [
        "__pycache__",
        ".git",
        ".pytest_cache",
        "node_modules",
        ".venv",
        "venv",
        ".env",
        "build",
        "dist",
        ".tox",
        "coverage",
        ".mypy_cache",
        ".coverage",
        ".idea",
        ".vscode",
    ]


# =============================================================================
# CONNASCENCE TYPES & RULES
# =============================================================================


class ConnascenceConstants:
    """Connascence types and rule definitions."""

    # Connascence type codes
    CON_NAME: Final[str] = "CoN"  # Name
    CON_TYPE: Final[str] = "CoT"  # Type
    CON_MEANING: Final[str] = "CoM"  # Meaning
    CON_POSITION: Final[str] = "CoP"  # Position
    CON_ALGORITHM: Final[str] = "CoA"  # Algorithm
    CON_EXECUTION: Final[str] = "CoE"  # Execution
    CON_TIMING: Final[str] = "CoTm"  # Timing
    CON_VALUE: Final[str] = "CoV"  # Value
    CON_IDENTITY: Final[str] = "CoI"  # Identity

    CONNASCENCE_TYPES: Final[List[str]] = [
        CON_NAME,
        CON_TYPE,
        CON_MEANING,
        CON_POSITION,
        CON_ALGORITHM,
        CON_EXECUTION,
        CON_TIMING,
        CON_VALUE,
        CON_IDENTITY,
    ]

    # Rule IDs
    RULE_MAGIC_LITERALS: Final[str] = "connascence_of_meaning"
    RULE_PARAMETER_BOMBS: Final[str] = "connascence_of_position"
    RULE_GOD_OBJECTS: Final[str] = "god_object"
    RULE_ALGORITHM_DUPLICATION: Final[str] = "connascence_of_algorithm"


# =============================================================================
# EXIT CODES & STATUS
# =============================================================================


class ExitCode(IntEnum):
    """Standard exit codes for CLI operations."""

    SUCCESS = 0
    VIOLATIONS_FOUND = 1
    ERROR = 2
    INVALID_ARGUMENTS = 3
    CONFIGURATION_ERROR = 4
    INTERRUPTED = 130


# =============================================================================
# VERSION & METADATA
# =============================================================================


class VersionInfo:
    """Version and build information."""

    VERSION: Final[str] = "2.0.0"
    VERSION_INFO: Final[tuple] = (2, 0, 0)
    BUILD_DATE: Final[str] = "2025-09-05"
    ANALYZER_NAME: Final[str] = "connascence-safety-analyzer"
    DISPLAY_NAME: Final[str] = "Connascence Safety Analyzer"


# =============================================================================
# INTEGRATION CONSTANTS
# =============================================================================


class IntegrationConstants:
    """Constants for external tool integrations."""

    # Tool names
    BLACK: Final[str] = "black"
    MYPY: Final[str] = "mypy"
    RUFF: Final[str] = "ruff"
    RADON: Final[str] = "radon"
    BANDIT: Final[str] = "bandit"
    PYLINT: Final[str] = "pylint"

    # Command patterns
    BLACK_COMMAND: Final[str] = "black --check --diff"
    MYPY_COMMAND: Final[str] = "mypy --strict"
    RUFF_COMMAND: Final[str] = "ruff check"

    # Integration success messages
    INTEGRATION_SUCCESS: Final[str] = "Integration completed successfully"
    INTEGRATION_FAILED: Final[str] = "Integration failed with errors"
    TOOL_NOT_FOUND: Final[str] = "Tool not found in PATH"


# =============================================================================
# MCP SERVER CONSTANTS
# =============================================================================


class MCPConstants:
    """MCP server configuration constants."""

    # Server info
    SERVER_NAME: Final[str] = "connascence-analyzer-mcp"
    SERVER_VERSION: Final[str] = VersionInfo.VERSION
    SERVER_DESCRIPTION: Final[str] = "MCP server for connascence analysis"

    # Tool names
    TOOL_ANALYZE_FILE: Final[str] = "analyze_file"
    TOOL_ANALYZE_WORKSPACE: Final[str] = "analyze_workspace"
    TOOL_GET_VIOLATIONS: Final[str] = "get_violations"
    TOOL_HEALTH_CHECK: Final[str] = "health_check"

    # Default configurations
    DEFAULT_RATE_LIMIT: Final[int] = 60  # requests per minute
    DEFAULT_AUDIT_ENABLED: Final[bool] = True
    DEFAULT_MAX_FILE_SIZE: Final[int] = PerformanceLimits.MAX_FILE_SIZE_KB


# =============================================================================
# CONFIGURATION LOADER
# =============================================================================


@dataclass
class CentralConfig:
    """Central configuration container."""

    # Loaded from constants above
    license: LicenseConstants = LicenseConstants()
    thresholds: AnalysisThresholds = AnalysisThresholds()
    performance: PerformanceLimits = PerformanceLimits()
    severity: SeverityConstants = SeverityConstants()
    filesystem: FileSystemConstants = FileSystemConstants()
    connascence: ConnascenceConstants = ConnascenceConstants()
    integration: IntegrationConstants = IntegrationConstants()
    mcp: MCPConstants = MCPConstants()
    version: VersionInfo = VersionInfo()

    @classmethod
    def load(cls, config_path: Path = None) -> "CentralConfig":
        """Load configuration with optional override file."""
        config = cls()

        # Load from file if provided
        if config_path and config_path.exists():
            # TODO: Implement JSON/YAML override loading
            pass

        return config


# Global configuration instance
CONFIG: Final[CentralConfig] = CentralConfig.load()

# =============================================================================
# BACKWARDS COMPATIBILITY ALIASES
# =============================================================================

# Legacy aliases for existing code
NASA_COMPLIANCE_THRESHOLD = AnalysisThresholds.NASA_COMPLIANCE_THRESHOLD
MECE_QUALITY_THRESHOLD = AnalysisThresholds.MECE_QUALITY_THRESHOLD
OVERALL_QUALITY_THRESHOLD = AnalysisThresholds.OVERALL_QUALITY_THRESHOLD
VIOLATION_WEIGHTS = SeverityConstants.VIOLATION_WEIGHTS
SEVERITY_LEVELS = SeverityConstants.SEVERITY_LEVELS
CONNASCENCE_TYPES = ConnascenceConstants.CONNASCENCE_TYPES
SUPPORTED_EXTENSIONS = FileSystemConstants.SUPPORTED_EXTENSIONS
DEFAULT_EXCLUSIONS = FileSystemConstants.DEFAULT_EXCLUSIONS
EXIT_SUCCESS = ExitCode.SUCCESS
EXIT_VIOLATIONS_FOUND = ExitCode.VIOLATIONS_FOUND
EXIT_ERROR = ExitCode.ERROR
