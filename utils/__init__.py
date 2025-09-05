# SPDX-License-Identifier: MIT
"""Utilities for the Connascence Safety Analyzer."""

from .config_loader import (
    ConnascenceViolation,
    ThresholdConfig,
    RateLimiter,
    load_config_defaults,
    create_rate_limiter
)
from .common import (
    format_error_output,
    validate_file_path,
    safe_get_attribute,
    normalize_severity,
    parse_version_string,
    create_unique_identifier
)

__all__ = [
    'ConnascenceViolation',
    'ThresholdConfig', 
    'RateLimiter',
    'load_config_defaults',
    'create_rate_limiter',
    'format_error_output',
    'validate_file_path',
    'safe_get_attribute',
    'normalize_severity',
    'parse_version_string',
    'create_unique_identifier'
]