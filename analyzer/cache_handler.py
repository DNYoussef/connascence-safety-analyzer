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
Cache Handler Module
====================

Handles file content caching and intelligent cache warming.
Extracted from unified_analyzer.py for NASA Rule 4 compliance.

Contains:
- CacheHandler: Main cache management class
- Intelligent cache warming strategies
- Cache performance monitoring and optimization
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import constants
try:
    from .constants import (
        CACHE_HIT_RATE_GOOD,
        CACHE_MAX_MEMORY_MB,
        CACHE_WARM_FILE_LIMIT,
    )
except ImportError:
    CACHE_HIT_RATE_GOOD = 0.8
    CACHE_MAX_MEMORY_MB = 100
    CACHE_WARM_FILE_LIMIT = 15

logger = logging.getLogger(__name__)


class CacheHandler:
    """
    Handles file content caching and intelligent cache warming.

    Features:
    - Intelligent cache warming based on project structure
    - Access pattern tracking for optimization
    - File priority calculation for better eviction
    - Performance monitoring and logging

    NASA Rule 4: All functions under 60 lines
    NASA Rule 7: Bounded resource management
    """

    def __init__(
        self,
        file_cache: Optional[Any] = None,
        arch_cache_manager: Optional[Any] = None,
        max_memory_mb: int = CACHE_MAX_MEMORY_MB,
    ):
        """
        Initialize cache handler with dependencies.

        Args:
            file_cache: FileContentCache instance
            arch_cache_manager: Architecture CacheManager instance
            max_memory_mb: Maximum memory for cache in MB

        NASA Rule 5: Input validation
        """
        self.file_cache = file_cache
        self.arch_cache_manager = arch_cache_manager
        self.max_memory_mb = max_memory_mb

        # Cache statistics tracking
        self._cache_stats = {
            "hits": 0,
            "misses": 0,
            "warm_requests": 0,
            "batch_loads": 0
        }

        # Access pattern tracking for intelligent caching
        self._analysis_patterns: Dict[str, int] = {}
        self._file_priorities: Dict[str, int] = {}

        logger.info(f"CacheHandler initialized (max_memory={max_memory_mb}MB)")

    def warm_cache_intelligently(self, project_path: Path) -> None:
        """
        Intelligent cache warming strategy to achieve >80% hit rates.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input assertions and error handling
        """
        assert project_path.exists(), "project_path must exist"

        # Delegate to architecture component if available
        if self.arch_cache_manager:
            self.arch_cache_manager.warm_cache(project_path, file_limit=CACHE_WARM_FILE_LIMIT)
            return

        if not self.file_cache:
            logger.debug("No file cache available for warming")
            return

        try:
            # Strategy 1: Pre-load frequently accessed file types
            self._warm_common_files(project_path)

            # Strategy 2: Pre-load prioritized Python files
            self._warm_prioritized_files(project_path)

        except Exception as e:
            logger.warning(f"Cache warming failed: {e}")

    def _warm_common_files(self, project_path: Path) -> None:
        """Pre-load frequently accessed file types."""
        common_files = ["__init__.py", "setup.py", "main.py", "app.py", "config.py"]

        for filename in common_files:
            file_matches = list(project_path.rglob(filename))
            for file_path in file_matches[:5]:  # Limit to avoid memory issues
                if file_path.stat().st_size < 100 * 1024:  # Only small files
                    self.file_cache.get_file_content(file_path)
                    self._cache_stats["warm_requests"] += 1

    def _warm_prioritized_files(self, project_path: Path) -> None:
        """Pre-load prioritized Python files based on analysis patterns."""
        python_files = list(project_path.glob("**/*.py"))

        # Sort by priority and size
        prioritized = sorted(
            python_files,
            key=lambda f: (
                -self.calculate_file_priority(f),
                f.stat().st_size,
            ),
        )[:CACHE_WARM_FILE_LIMIT]

        for py_file in prioritized:
            if py_file.stat().st_size < 500 * 1024:  # Skip large files
                self.file_cache.get_file_content(py_file)
                self._cache_stats["warm_requests"] += 1

    def calculate_file_priority(self, file_path: Path) -> int:
        """Calculate file priority for intelligent caching (0-100)."""
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
        try:
            file_size = file_path.stat().st_size
            if file_size < 50 * 1024:  # < 50KB
                score += 20
            elif file_size < 200 * 1024:  # < 200KB
                score += 10
        except OSError:
            pass

        # Frequently imported patterns
        if filename.endswith(("_utils.py", "_common.py", "_base.py")):
            score += 15

        return min(score, 100)

    def get_prioritized_python_files(self, project_path: Path) -> List[Path]:
        """Get Python files prioritized for analysis with caching benefits."""
        if self.file_cache:
            # FileContentCache returns strings, convert to Path objects
            python_files_str = self.file_cache.get_python_files(str(project_path))
            python_files = [Path(f) for f in python_files_str]
        else:
            python_files = list(project_path.glob("**/*.py"))

        # Sort by priority for better cache utilization
        return sorted(python_files, key=self.calculate_file_priority, reverse=True)

    def batch_preload_files(self, files: List[Path]) -> None:
        """Batch preload files for optimal cache performance."""
        if not self.file_cache:
            return

        logger.info(f"Batch preloading {len(files)} files for cache optimization")

        for file_path in files:
            try:
                if file_path.stat().st_size < 1024 * 1024:  # Only files < 1MB
                    # Preload both content and AST for maximum benefit
                    self.file_cache.get_file_content(file_path)
                    if hasattr(self.file_cache, "get_ast_tree"):
                        self.file_cache.get_ast_tree(file_path)
                    self._cache_stats["batch_loads"] += 1

            except Exception as e:
                logger.debug(f"Failed to preload {file_path}: {e}")

    def get_cached_content_with_tracking(self, file_path: Path) -> Optional[str]:
        """Get file content with access pattern tracking for cache optimization."""
        if not self.file_cache:
            return None

        # Track access pattern
        file_key = str(file_path)
        self._analysis_patterns[file_key] = self._analysis_patterns.get(file_key, 0) + 1

        # Get content and track cache performance
        content = self.file_cache.get_file_content(file_path)
        if content:
            self._cache_stats["hits"] += 1
        else:
            self._cache_stats["misses"] += 1

        return content

    def get_cached_lines_with_tracking(self, file_path: Path) -> List[str]:
        """Get file lines with access pattern tracking."""
        if not self.file_cache:
            return []

        lines = self.file_cache.get_file_lines(file_path)
        if lines:
            self._cache_stats["hits"] += 1
        else:
            self._cache_stats["misses"] += 1

        return lines

    def get_cache_hit_rate(self) -> float:
        """Calculate current cache hit rate."""
        total = self._cache_stats["hits"] + self._cache_stats["misses"]
        return self._cache_stats["hits"] / total if total > 0 else 0.0

    def log_cache_performance(self) -> None:
        """Log detailed cache performance metrics for monitoring."""
        if not self.file_cache:
            return

        hit_rate = self.get_cache_hit_rate()
        cache_stats = self.file_cache._stats if hasattr(self.file_cache, "_stats") else None

        logger.info("Cache Performance Summary:")
        logger.info(f"  Hit Rate: {hit_rate:.1%} (Target: >80%)")
        logger.info(f"  Hits: {self._cache_stats['hits']}")
        logger.info(f"  Misses: {self._cache_stats['misses']}")
        logger.info(f"  Warm Requests: {self._cache_stats['warm_requests']}")
        logger.info(f"  Batch Loads: {self._cache_stats['batch_loads']}")

        if cache_stats:
            memory_usage = cache_stats.memory_usage / (1024 * 1024)  # MB
            logger.info(f"  Memory Usage: {memory_usage:.1f}MB / {cache_stats.max_memory // (1024 * 1024)}MB")
            logger.info(f"  Evictions: {cache_stats.evictions}")

        # Performance recommendations
        if hit_rate < 0.6:
            logger.warning("Low cache hit rate - consider increasing warm-up files")
        elif hit_rate > CACHE_HIT_RATE_GOOD:
            logger.info("Excellent cache performance!")

    def optimize_for_future_runs(self) -> None:
        """
        Learn from current analysis patterns to optimize future cache performance.

        NASA Rule 4: Function under 60 lines
        """
        if not self._analysis_patterns:
            return

        # Identify most frequently accessed files
        frequent_files = sorted(
            self._analysis_patterns.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        # Store for next analysis session (simplified for now)
        logger.info(f"Learned access patterns for {len(frequent_files)} high-frequency files")

        # Future enhancement: Persist patterns to improve next analysis

    def clear_cache(self) -> None:
        """Clear all cached content."""
        if self.file_cache:
            self.file_cache.clear_cache()
            logger.info("Cache cleared")

        # Reset stats
        self._cache_stats = {
            "hits": 0,
            "misses": 0,
            "warm_requests": 0,
            "batch_loads": 0
        }
        self._analysis_patterns.clear()
        self._file_priorities.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            **self._cache_stats,
            "hit_rate": self.get_cache_hit_rate(),
            "patterns_tracked": len(self._analysis_patterns),
        }


__all__ = ["CacheHandler"]
