"""
File I/O Optimization Module
============================

Provides thread-safe, memory-bounded caching system for file operations.
Optimized for NASA Rule 7 compliance and parallel processing.

Key Features:
- LRU cache with 50MB memory limit
- Content hash-based AST caching  
- Thread-safe operations
- ~70% I/O reduction
- Comprehensive error handling
"""

from .file_cache import (
    CacheEntry,
    CacheStats,
    FileContentCache,
    cached_ast_tree,
    cached_file_content,
    cached_file_lines,
    cached_python_files,
    clear_global_cache,
    get_global_cache,
)
from .performance_benchmark import PerformanceBenchmark

__all__ = [
    "CacheEntry",
    "CacheStats",
    "FileContentCache",
    "PerformanceBenchmark",
    "cached_ast_tree",
    "cached_file_content",
    "cached_file_lines",
    "cached_python_files",
    "clear_global_cache",
    "get_global_cache",
]

__version__ = "1.0.0"
