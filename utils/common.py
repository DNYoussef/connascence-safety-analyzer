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
Common utility functions used across the Connascence Safety Analyzer.

Small utility functions that were duplicated across multiple files.
"""

import re
from typing import Any, Dict, Optional


def format_error_output(error_message: str, context: Optional[Dict[str, Any]] = None) -> str:
    """Format error message with optional context."""
    if context:
        return f"{error_message}: {context}"
    return error_message


def validate_file_path(file_path: str) -> bool:
    """Validate if a file path is acceptable for processing."""
    if not file_path or not isinstance(file_path, str):
        return False

    # Basic validation - no path traversal attempts
    return not (".." in file_path or file_path.startswith("/"))


def safe_get_attribute(obj: Any, attr_name: str, default: Any = None) -> Any:
    """Safely get an attribute from an object with a default fallback."""
    try:
        return getattr(obj, attr_name, default)
    except (AttributeError, TypeError):
        return default


def normalize_severity(severity: str) -> str:
    """Normalize severity strings to standard values."""
    severity_map = {
        "low": "low",
        "medium": "medium",
        "moderate": "medium",
        "high": "high",
        "critical": "critical",
        "error": "high",
        "warning": "medium",
        "info": "low",
    }

    return severity_map.get(severity.lower(), "medium")


def parse_version_string(version_output: str) -> str:
    """Parse version number from tool output."""
    # Common version patterns
    patterns = [
        r"(\d+\.\d+\.\d+)",  # x.y.z
        r"(\d+\.\d+)",  # x.y
        r"v(\d+\.\d+\.\d+)",  # vx.y.z
        r"version (\d+\.\d+\.\d+)",  # version x.y.z
    ]

    for pattern in patterns:
        match = re.search(pattern, version_output)
        if match:
            return match.group(1)

    return version_output.strip()


def create_unique_identifier(prefix: str = "", length: int = 8) -> str:
    """Create a unique identifier with optional prefix."""
    import random
    import string

    chars = string.ascii_letters + string.digits
    unique_part = "".join(random.choice(chars) for _ in range(length))

    return f"{prefix}{unique_part}" if prefix else unique_part
