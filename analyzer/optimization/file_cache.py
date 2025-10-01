"""
File Content Cache System
========================

Thread-safe, memory-bounded caching system for file operations and AST parsing.
Implements LRU eviction and content hash-based AST caching for performance.

Compliance:
- NASA Rule 7: Bounded memory operations (max 50MB)
- Thread-safe operations for parallel processing
- Comprehensive error handling
"""

import ast
from collections import OrderedDict
from dataclasses import dataclass, field
from functools import lru_cache
import hashlib
from pathlib import Path
import threading
from threading import RLock
import time
from typing import Dict, List, Optional, Set, Union
import weakref


@dataclass
class CacheStats:
    """Statistics for cache performance monitoring."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    memory_usage: int = 0
    max_memory: int = 50 * 1024 * 1024  # 50MB

    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    content: str
    ast_tree: Optional[ast.AST] = None
    content_hash: str = ""
    last_accessed: float = field(default_factory=time.time)
    file_size: int = 0
    parse_time: float = 0.0

    def __post_init__(self):
        """Initialize derived fields."""
        if not self.content_hash:
            self.content_hash = hashlib.sha256(self.content.encode("utf-8")).hexdigest()[:16]
        if not self.file_size:
            self.file_size = len(self.content.encode("utf-8"))


class FileContentCache:
    """
    Thread-safe LRU cache for file content and AST trees.

    Features:
    - Memory-bounded operations (NASA Rule 7 compliance)
    - Content hash-based AST caching
    - Thread-safe concurrent access
    - LRU eviction policy
    - Performance monitoring
    """

    def __init__(self, max_memory: int = 50 * 1024 * 1024):
        """
        Initialize file content cache.

        Args:
            max_memory: Maximum memory usage in bytes (default 50MB)
        """
        assert max_memory > 0, "max_memory must be positive"

        self.max_memory = max_memory
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = RLock()
        self._stats = CacheStats(max_memory=max_memory)

        # AST cache by content hash
        self._ast_cache: Dict[str, ast.AST] = {}

        # Track file modification times
        self._file_mtimes: Dict[str, float] = {}

        # Weak references for cleanup
        self._file_watchers: Set[weakref.ref] = set()

    def get_file_content(self, file_path: Union[str, Path]) -> Optional[str]:
        """
        Get file content from cache or disk.

        Args:
            file_path: Path to file

        Returns:
            File content or None if error
        """
        file_path = str(file_path)

        with self._lock:
            # Check if file exists and get mtime
            try:
                path_obj = Path(file_path)
                if not path_obj.exists():
                    return None

                current_mtime = path_obj.stat().st_mtime
                cached_mtime = self._file_mtimes.get(file_path, 0)

                # Check cache validity
                if file_path in self._cache and current_mtime <= cached_mtime:
                    entry = self._cache[file_path]
                    entry.last_accessed = time.time()
                    # Move to end (most recently used)
                    self._cache.move_to_end(file_path)
                    self._stats.hits += 1
                    return entry.content

                # Cache miss - read file
                self._stats.misses += 1

                try:
                    content = path_obj.read_text(encoding="utf-8")
                except (UnicodeDecodeError, PermissionError):
                    return None

                # Create cache entry
                entry = CacheEntry(content=content)

                # Update cache
                self._cache[file_path] = entry
                self._file_mtimes[file_path] = current_mtime

                # Update memory usage
                self._stats.memory_usage += entry.file_size

                # Ensure memory bounds
                self._enforce_memory_bounds()

                return content

            except Exception:
                return None

    def get_ast_tree(self, file_path: Union[str, Path]) -> Optional[ast.AST]:
        """
        Get parsed AST tree from cache or parse from content.

        Args:
            file_path: Path to Python file

        Returns:
            Parsed AST tree or None if error
        """
        content = self.get_file_content(file_path)
        if content is None:
            return None

        with self._lock:
            file_path = str(file_path)

            # Get content hash for AST caching
            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

            # Check AST cache
            if content_hash in self._ast_cache:
                return self._ast_cache[content_hash]

            # Parse AST
            try:
                start_time = time.time()
                tree = ast.parse(content, filename=file_path)
                parse_time = time.time() - start_time

                # Update cache entry if exists
                if file_path in self._cache:
                    entry = self._cache[file_path]
                    entry.ast_tree = tree
                    entry.parse_time = parse_time

                # Cache AST by content hash
                self._ast_cache[content_hash] = tree

                # Enforce memory bounds for AST cache too
                if len(self._ast_cache) > 100:  # Limit AST cache size
                    # Remove oldest entries (simple FIFO for AST cache)
                    old_hashes = list(self._ast_cache.keys())[:-50]
                    for old_hash in old_hashes:
                        del self._ast_cache[old_hash]

                return tree

            except SyntaxError:
                return None

    @lru_cache(maxsize=1000)
    def get_python_files(self, directory: str) -> List[str]:
        """
        Get list of Python files in directory (cached).

        Args:
            directory: Directory path to search

        Returns:
            List of Python file paths
        """
        try:
            dir_path = Path(directory)
            if not dir_path.exists() or not dir_path.is_dir():
                return []

            python_files = []
            for py_file in dir_path.rglob("*.py"):
                # Skip common non-source directories
                skip_patterns = [
                    "__pycache__",
                    ".git",
                    ".pytest_cache",
                    ".mypy_cache",
                    ".ruff_cache",
                    ".tox",
                    ".venv",
                    "venv",
                    "node_modules",
                ]
                path_str = str(py_file)
                path_parts = py_file.parts
                filename = py_file.name

                # Check system directories
                if any(pattern in path_str for pattern in skip_patterns):
                    continue

                # Skip files in /tests/ or \tests\ directories (actual test directories)
                if "tests" in path_parts:
                    continue

                # Skip files that start with test_ or end with _test.py (actual test files)
                if filename.startswith("test_") or filename.endswith("_test.py"):
                    continue

                python_files.append(str(py_file))

            return python_files

        except Exception:
            return []

    def get_file_lines(self, file_path: Union[str, Path]) -> List[str]:
        """
        Get file content as list of lines.

        Args:
            file_path: Path to file

        Returns:
            List of file lines
        """
        content = self.get_file_content(file_path)
        if content is None:
            return []
        return content.splitlines()

    def prefetch_files(self, file_paths: List[Union[str, Path]]) -> int:
        """
        Prefetch multiple files into cache.

        Args:
            file_paths: List of file paths to prefetch

        Returns:
            Number of files successfully cached
        """
        cached_count = 0
        for file_path in file_paths:
            if self.get_file_content(file_path) is not None:
                cached_count += 1
        return cached_count

    def _enforce_memory_bounds(self) -> None:
        """Enforce memory bounds by evicting LRU entries."""
        while self._stats.memory_usage > self.max_memory:
            if not self._cache:
                break

            # Evict least recently used entry
            oldest_path, oldest_entry = self._cache.popitem(last=False)
            self._stats.memory_usage -= oldest_entry.file_size
            self._stats.evictions += 1

            # Clean up associated data
            if oldest_path in self._file_mtimes:
                del self._file_mtimes[oldest_path]

    def clear_cache(self) -> None:
        """Clear all cached data."""
        with self._lock:
            self._cache.clear()
            self._ast_cache.clear()
            self._file_mtimes.clear()
            self._stats.memory_usage = 0
            # Clear LRU cache
            self.get_python_files.cache_clear()

    def get_cache_stats(self) -> CacheStats:
        """Get cache performance statistics."""
        with self._lock:
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                evictions=self._stats.evictions,
                memory_usage=self._stats.memory_usage,
                max_memory=self._stats.max_memory,
            )

    def invalidate_file(self, file_path: Union[str, Path]) -> None:
        """Invalidate cache entry for specific file."""
        file_path = str(file_path)
        with self._lock:
            if file_path in self._cache:
                entry = self._cache.pop(file_path)
                self._stats.memory_usage -= entry.file_size

            if file_path in self._file_mtimes:
                del self._file_mtimes[file_path]

    def get_memory_usage(self) -> Dict[str, int]:
        """Get detailed memory usage breakdown."""
        with self._lock:
            return {
                "file_cache_bytes": self._stats.memory_usage,
                "ast_cache_count": len(self._ast_cache),
                "file_cache_count": len(self._cache),
                "max_memory_bytes": self.max_memory,
                "utilization_percent": round((self._stats.memory_usage / self.max_memory) * 100, 2),
            }

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup if needed."""
        # Optional: clear cache on exit
        pass


# Global cache instance for module-level access
_global_cache: Optional[FileContentCache] = None
_cache_lock = threading.Lock()


def get_global_cache() -> FileContentCache:
    """Get global file cache instance (thread-safe singleton)."""
    global _global_cache

    if _global_cache is None:
        with _cache_lock:
            if _global_cache is None:
                _global_cache = FileContentCache()

    return _global_cache


def clear_global_cache() -> None:
    """Clear global cache instance."""
    global _global_cache

    if _global_cache is not None:
        _global_cache.clear_cache()


# Convenience functions for common operations
def cached_file_content(file_path: Union[str, Path]) -> Optional[str]:
    """Get file content using global cache."""
    return get_global_cache().get_file_content(file_path)


def cached_ast_tree(file_path: Union[str, Path]) -> Optional[ast.AST]:
    """Get AST tree using global cache."""
    return get_global_cache().get_ast_tree(file_path)


def cached_python_files(directory: Union[str, Path]) -> List[str]:
    """Get Python files list using global cache."""
    return get_global_cache().get_python_files(str(directory))


def cached_file_lines(file_path: Union[str, Path]) -> List[str]:
    """Get file lines using global cache."""
    return get_global_cache().get_file_lines(file_path)
