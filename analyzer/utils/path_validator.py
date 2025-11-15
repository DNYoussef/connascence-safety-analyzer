"""
Path Validator Utility - Ensures consistent Path type handling.

This module provides utilities to safely convert path inputs to Path objects,
resolving architectural inconsistencies across analyzer modules.

Author: Week 5 Day 3 RCA Fix
Date: 2025-11-14
Issue: RCA-2 (Orchestrator Path Type Inconsistency)
"""

from pathlib import Path
from typing import Union


def ensure_path(path: Union[str, Path]) -> Path:
    """
    Safely convert any path input to Path object.

    This function resolves the architectural flaw where some analyzer modules
    expect Path objects while others expect strings, leading to TypeError
    when attempting path operations like division (path / "file.py").

    Args:
        path: File path as string or Path object

    Returns:
        Path: Normalized Path object

    Raises:
        TypeError: If path is neither str nor Path

    Examples:
        >>> ensure_path("/tmp/project")
        PosixPath('/tmp/project')

        >>> ensure_path(Path("/tmp/project"))
        PosixPath('/tmp/project')

        >>> ensure_path(123)
        Traceback (most recent call last):
        ...
        TypeError: Path must be str or Path, got <class 'int'>
    """
    if isinstance(path, Path):
        return path
    elif isinstance(path, str):
        return Path(path)
    else:
        raise TypeError(f"Path must be str or Path, got {type(path)}")
