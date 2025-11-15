"""
Shared fixtures for unit tests.

Provides common test fixtures and utilities for all unit test modules.
"""

import ast
from unittest.mock import Mock

import pytest


@pytest.fixture
def mock_file_cache():
    """
    Create mock FileContentCache for testing.

    Returns:
        Mock FileContentCache with standard methods and attributes
    """
    cache = Mock()
    cache._content_cache = {}
    cache._ast_cache = {}
    cache._stats = Mock()
    cache._stats.memory_usage = 50 * 1024 * 1024  # 50MB
    cache._stats.max_memory = 100 * 1024 * 1024  # 100MB
    cache.get_ast_tree = Mock(return_value=None)
    cache.get_file_content = Mock(return_value=None)
    cache.get_file_lines = Mock(return_value=[])
    cache.clear_cache = Mock()
    return cache


@pytest.fixture
def sample_ast():
    """
    Create sample AST module for testing.

    Returns:
        ast.Module instance with basic structure
    """
    return ast.parse("x = 42\nprint(x)")
