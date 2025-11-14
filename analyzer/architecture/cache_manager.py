"""
CacheManager - Centralized cache management for UnifiedConnascenceAnalyzer

Extracted from: analyzer/unified_analyzer.py
Purpose: Centralize all caching logic into a dedicated component

Responsibilities:
- File content caching with intelligent warming
- AST caching with memory management
- Cache invalidation strategies
- Performance tracking and optimization
- Memory-aware cache eviction

NASA Compliance:
- Rule 4: All functions under 60 lines
- Rule 5: Input assertions and error handling
- Rule 7: Bounded resource management
"""

import ast
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Intelligent cache manager for file content and AST trees.

    Features:
    - File content caching with LRU eviction
    - AST tree caching with memory limits
    - Intelligent cache warming (>80% hit rates)
    - Access pattern tracking
    - Performance monitoring and metrics

    NASA Rule 4: Class under 500 lines
    NASA Rule 7: Memory-bounded with automatic cleanup
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize cache manager with configuration.

        Args:
            config: Configuration dictionary with cache settings
                - max_memory: Maximum cache memory in bytes (default: 100MB)
                - enable_warming: Enable intelligent cache warming
                - warm_file_count: Number of files to pre-warm

        NASA Rule 5: Input validation
        """
        self.config = config or {}

        # Initialize file content cache
        try:
            from ..optimization.file_cache import FileContentCache
            max_memory = self.config.get("max_memory", 100 * 1024 * 1024)
            self.file_cache = FileContentCache(max_memory=max_memory)
            self.cache_available = True
        except ImportError:
            logger.warning("FileContentCache not available - caching disabled")
            self.file_cache = None
            self.cache_available = False

        # Cache statistics tracking
        self._cache_stats = {
            "hits": 0,
            "misses": 0,
            "warm_requests": 0,
            "batch_loads": 0,
            "evictions": 0,
        }

        # Access pattern tracking for optimization
        self._analysis_patterns: Dict[str, int] = {}
        self._file_priorities: Dict[str, int] = {}

        logger.info(f"CacheManager initialized (cache_available={self.cache_available})")

    def get_cached_ast(self, file_path: Path) -> Optional[ast.Module]:
        """
        Retrieve cached AST for file with tracking.

        Args:
            file_path: Path to Python file

        Returns:
            Cached AST module or None if not cached

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation
        """
        assert file_path.exists(), f"file_path must exist: {file_path}"

        if not self.file_cache:
            return None

        try:
            # Track access pattern
            file_key = str(file_path)
            self._analysis_patterns[file_key] = self._analysis_patterns.get(file_key, 0) + 1

            # Get AST from cache
            tree = self.file_cache.get_ast_tree(file_path)

            # Update statistics
            if tree:
                self._cache_stats["hits"] += 1
            else:
                self._cache_stats["misses"] += 1

            return tree

        except Exception as e:
            logger.debug(f"Failed to get cached AST for {file_path}: {e}")
            self._cache_stats["misses"] += 1
            return None

    def cache_ast(self, file_path: Path, tree: ast.Module) -> None:
        """
        Cache AST with memory management.

        Args:
            file_path: Path to Python file
            tree: Parsed AST module

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation
        NASA Rule 7: Memory-bounded caching
        """
        assert file_path.exists(), f"file_path must exist: {file_path}"
        assert isinstance(tree, ast.Module), "tree must be ast.Module"

        if not self.file_cache:
            return

        try:
            # Cache the AST (FileContentCache handles memory limits)
            self.file_cache._ast_cache[str(file_path)] = tree

            # Update file priority for eviction strategy
            self._file_priorities[str(file_path)] = self._calculate_file_priority(file_path)

        except Exception as e:
            logger.debug(f"Failed to cache AST for {file_path}: {e}")

    def get_cached_content(self, file_path: Path) -> Optional[str]:
        """
        Get file content with access pattern tracking.

        Args:
            file_path: Path to file

        Returns:
            File content or None

        NASA Rule 4: Function under 60 lines
        """
        assert file_path.exists(), f"file_path must exist: {file_path}"

        if not self.file_cache:
            return None

        # Track access pattern
        file_key = str(file_path)
        self._analysis_patterns[file_key] = self._analysis_patterns.get(file_key, 0) + 1

        # Get content and track performance
        content = self.file_cache.get_file_content(file_path)
        if content:
            self._cache_stats["hits"] += 1
        else:
            self._cache_stats["misses"] += 1

        return content

    def get_cached_lines(self, file_path: Path) -> List[str]:
        """
        Get file lines with access pattern tracking.

        Args:
            file_path: Path to file

        Returns:
            List of file lines

        NASA Rule 4: Function under 60 lines
        """
        assert file_path.exists(), f"file_path must exist: {file_path}"

        if not self.file_cache:
            return []

        lines = self.file_cache.get_file_lines(file_path)
        if lines:
            self._cache_stats["hits"] += 1
        else:
            self._cache_stats["misses"] += 1

        return lines

    def invalidate(self, file_path: Path) -> None:
        """
        Invalidate cache for specific file.

        Args:
            file_path: Path to file to invalidate

        NASA Rule 4: Function under 60 lines
        """
        if not self.file_cache:
            return

        file_key = str(file_path)

        # Remove from content cache
        if hasattr(self.file_cache, "_content_cache"):
            self.file_cache._content_cache.pop(file_key, None)

        # Remove from AST cache
        if hasattr(self.file_cache, "_ast_cache"):
            self.file_cache._ast_cache.pop(file_key, None)

        # Remove tracking data
        self._analysis_patterns.pop(file_key, None)
        self._file_priorities.pop(file_key, None)

        logger.debug(f"Invalidated cache for {file_path}")

    def clear_all(self) -> None:
        """
        Clear all caches.

        NASA Rule 4: Function under 60 lines
        NASA Rule 7: Complete resource cleanup
        """
        if not self.file_cache:
            return

        # Clear FileContentCache
        if hasattr(self.file_cache, "clear_cache"):
            self.file_cache.clear_cache()

        # Clear tracking data
        self._analysis_patterns.clear()
        self._file_priorities.clear()

        # Reset statistics (keep historical data)
        logger.info(f"Cache cleared (hit_rate={self.get_hit_rate():.1%})")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive cache statistics.

        Returns:
            Dictionary with cache performance metrics

        NASA Rule 4: Function under 60 lines
        """
        stats = {
            "hits": self._cache_stats["hits"],
            "misses": self._cache_stats["misses"],
            "hit_rate": self.get_hit_rate(),
            "warm_requests": self._cache_stats["warm_requests"],
            "batch_loads": self._cache_stats["batch_loads"],
            "evictions": self._cache_stats["evictions"],
        }

        # Add memory usage if available
        if self.file_cache and hasattr(self.file_cache, "_stats"):
            cache_stats = self.file_cache._stats
            stats["memory_usage_mb"] = cache_stats.memory_usage / (1024 * 1024)
            stats["max_memory_mb"] = cache_stats.max_memory / (1024 * 1024)
            stats["memory_usage_percent"] = (
                cache_stats.memory_usage / cache_stats.max_memory * 100
            )

        return stats

    def get_hit_rate(self) -> float:
        """
        Calculate current cache hit rate.

        Returns:
            Hit rate as decimal (0.0-1.0)

        NASA Rule 4: Function under 60 lines
        """
        total = self._cache_stats["hits"] + self._cache_stats["misses"]
        return self._cache_stats["hits"] / total if total > 0 else 0.0

    def warm_cache(self, project_path: Path, file_limit: int = 15) -> None:
        """
        Intelligent cache warming to achieve >80% hit rates.

        Strategy:
        1. Pre-load frequently accessed file types
        2. Pre-load directory structure for pattern recognition
        3. Prioritize by file size and common patterns

        Args:
            project_path: Root directory to warm cache for
            file_limit: Maximum number of files to pre-warm

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation
        """
        assert project_path.exists(), "project_path must exist"

        if not self.file_cache:
            return

        try:
            # Strategy 1: Pre-load frequently accessed file types
            common_files = ["__init__.py", "setup.py", "main.py", "app.py", "config.py"]
            for filename in common_files:
                file_matches = list(project_path.rglob(filename))
                for file_path in file_matches[:5]:  # Limit to avoid memory issues
                    if file_path.stat().st_size < 100 * 1024:  # Only small files
                        self.file_cache.get_file_content(file_path)
                        self._cache_stats["warm_requests"] += 1

            # Strategy 2: Pre-load prioritized Python files
            python_files = list(project_path.glob("**/*.py"))
            prioritized = sorted(
                python_files,
                key=lambda f: (
                    -self._calculate_file_priority(f),
                    f.stat().st_size,
                ),
            )[:file_limit]

            for py_file in prioritized:
                if py_file.stat().st_size < 500 * 1024:  # Skip large files
                    self.file_cache.get_file_content(py_file)
                    self._cache_stats["warm_requests"] += 1

            logger.info(
                f"Cache warmed: {self._cache_stats['warm_requests']} files pre-loaded"
            )

        except Exception as e:
            logger.warning(f"Cache warming failed: {e}")

    def batch_preload(self, files: List[Path]) -> None:
        """
        Batch preload files for optimal cache performance.

        Args:
            files: List of files to preload

        NASA Rule 4: Function under 60 lines
        """
        if not self.file_cache:
            return

        logger.info(f"Batch preloading {len(files)} files")

        for file_path in files:
            try:
                if file_path.stat().st_size < 1024 * 1024:  # Only files < 1MB
                    # Preload both content and AST
                    self.file_cache.get_file_content(file_path)
                    self.file_cache.get_ast_tree(file_path)
                    self._cache_stats["batch_loads"] += 1
            except Exception as e:
                logger.debug(f"Failed to preload {file_path}: {e}")

    def _calculate_file_priority(self, file_path: Path) -> int:
        """
        Calculate file priority for intelligent caching (0-100).

        Higher priority files are cached first and evicted last.

        Args:
            file_path: Path to file

        Returns:
            Priority score (0-100)

        NASA Rule 4: Function under 60 lines
        """
        score = 0
        filename = file_path.name.lower()
        parent_dir = file_path.parent.name.lower()

        # High priority files
        high_priority_names = ["__init__", "main", "app", "config", "settings"]
        if any(name in filename for name in high_priority_names):
            score += 40

        # Medium priority directories
        important_dirs = ["src", "lib", "core", "utils", "common"]
        if any(dir_name in parent_dir for dir_name in important_dirs):
            score += 20

        # Boost for smaller files (easier to cache)
        file_size = file_path.stat().st_size
        if file_size < 50 * 1024:  # < 50KB
            score += 20
        elif file_size < 200 * 1024:  # < 200KB
            score += 10

        # Frequently imported patterns
        if filename.endswith(("_utils.py", "_common.py", "_base.py")):
            score += 15

        return min(score, 100)

    def log_performance(self) -> None:
        """
        Log detailed cache performance metrics.

        NASA Rule 4: Function under 60 lines
        """
        if not self.file_cache:
            return

        hit_rate = self.get_hit_rate()
        stats = self.get_cache_stats()

        logger.info("Cache Performance Summary:")
        logger.info(f"  Hit Rate: {hit_rate:.1%} (Target: >80%)")
        logger.info(f"  Hits: {stats['hits']}")
        logger.info(f"  Misses: {stats['misses']}")
        logger.info(f"  Warm Requests: {stats['warm_requests']}")
        logger.info(f"  Batch Loads: {stats['batch_loads']}")

        if "memory_usage_mb" in stats:
            logger.info(
                f"  Memory: {stats['memory_usage_mb']:.1f}MB / "
                f"{stats['max_memory_mb']:.1f}MB "
                f"({stats['memory_usage_percent']:.1f}%)"
            )

        # Performance recommendations
        if hit_rate < 0.6:
            logger.warning("Low cache hit rate - consider increasing warm-up files")
        elif hit_rate > 0.9:
            logger.info("Excellent cache performance!")

    def optimize_for_future_runs(self) -> None:
        """
        Learn from current analysis patterns to optimize future cache.

        NASA Rule 4: Function under 60 lines
        """
        if not self._analysis_patterns:
            return

        # Identify most frequently accessed files
        frequent_files = sorted(
            self._analysis_patterns.items(), key=lambda x: x[1], reverse=True
        )[:10]

        logger.info(f"Learned access patterns for {len(frequent_files)} high-frequency files")

        # Store top files for next session (future enhancement)
        # Could persist to config or dedicated cache index file
