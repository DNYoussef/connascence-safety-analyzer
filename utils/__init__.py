# SPDX-License-Identifier: MIT
"""Utilities for the Connascence Safety Analyzer."""

from .common import (
    create_unique_identifier,
    format_error_output,
    normalize_severity,
    parse_version_string,
    safe_get_attribute,
    validate_file_path,
)
from .config_loader import RateLimiter, ThresholdConfig, create_rate_limiter, load_config_defaults
from .types import ConnascenceViolation, Violation, ViolationDict, create_violation

__all__ = [
    "ConnascenceViolation",
    "RateLimiter",
    "ThresholdConfig",
    "Violation",
    "ViolationDict",
    "create_rate_limiter",
    "create_unique_identifier",
    "create_violation",
    "format_error_output",
    "load_config_defaults",
    "normalize_severity",
    "parse_version_string",
    "safe_get_attribute",
    "validate_file_path",
]
