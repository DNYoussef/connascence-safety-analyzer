# SPDX-License-Identifier: MIT
"""
AST Caching System
==================

Intelligent caching system for AST parsing and analysis results
to improve performance on repeated analysis runs.
"""

import ast
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import hashlib
import logging
from pathlib import Path
import pickle
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Union

from fixes.phase0.production_safe_assertions import ProductionAssert

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Single cache entry with metadata."""

    key: str
    data: Any
    file_path: str
    file_mtime: float
    file_size: int
    created_at: float
    accessed_at: float
    access_count: int = 0
    analysis_duration_ms: float = 0.0

    def is_valid(self) -> bool:
        """Check if cache entry is still valid."""
        try:
            file_path = Path(self.file_path)
            if not file_path.exists():
                return False

            current_stat = file_path.stat()
            return abs(current_stat.st_mtime - self.file_mtime) < 1.0 and current_stat.st_size == self.file_size
        except Exception:
            return False

    def update_access(self):
        """Update access statistics."""
        self.accessed_at = time.time()
        self.access_count += 1


class ASTCache:
    """
    Intelligent AST and analysis result caching system.

    Features:
    - File-based persistence
    - Automatic cache invalidation
    - LRU eviction policy
    - Thread-safe operations
    - Compression support
    - Performance metrics
    """

    def __init__(
        self,
        cache_dir: str = ".connascence_cache",
        max_size_mb: int = 500,
        max_entries: int = 10000,
        enable_persistence: bool = True,
        enable_compression: bool = True,
    ):
        """Initialize AST cache."""

        self.cache_dir = Path(cache_dir)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_entries = max_entries
        self.enable_persistence = enable_persistence
        self.enable_compression = enable_compression

        # In-memory cache
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.cache_stats = {"hits": 0, "misses": 0, "invalidations": 0, "evictions": 0, "size_bytes": 0}

        # Thread safety
        self.cache_lock = threading.RLock()

        # Initialize cache directory
        if self.enable_persistence:
            self.cache_dir.mkdir(exist_ok=True)
            self._load_cache_index()

        logger.info(f"AST cache initialized: {self.cache_dir}, max {max_size_mb}MB, {max_entries} entries")

    def get_ast(self, file_path: Union[str, Path]) -> Optional[ast.AST]:
        """Get cached AST for file, or None if not cached/invalid."""

        file_path = Path(file_path)
        cache_key = self._generate_cache_key(file_path, "ast")

        with self.cache_lock:
            entry = self.memory_cache.get(cache_key)

            if entry and entry.is_valid():
                entry.update_access()
                self.cache_stats["hits"] += 1
                logger.debug(f"Cache hit for AST: {file_path}")
                return entry.data
            elif entry:
                # Invalid entry, remove it
                self._remove_entry(cache_key)
                self.cache_stats["invalidations"] += 1

            self.cache_stats["misses"] += 1
            return None

    def put_ast(self, file_path: Union[str, Path], ast_tree: ast.AST, analysis_duration_ms: float = 0.0):
        """Cache AST for file."""

        ProductionAssert.not_none(file_path, "file_path")

        ProductionAssert.not_none(file_path, "file_path")

        ProductionAssert.not_none(ast_tree, "ast_tree")

        ProductionAssert.not_none(analysis_duration_ms, "analysis_duration_ms")

        ProductionAssert.not_none(file_path, "file_path")

        ProductionAssert.not_none(file_path, "file_path")

        ProductionAssert.not_none(ast_tree, "ast_tree")

        ProductionAssert.not_none(analysis_duration_ms, "analysis_duration_ms")

        file_path = Path(file_path)
        cache_key = self._generate_cache_key(file_path, "ast")

        try:
            file_stat = file_path.stat()

            entry = CacheEntry(
                key=cache_key,
                data=ast_tree,
                file_path=str(file_path),
                file_mtime=file_stat.st_mtime,
                file_size=file_stat.st_size,
                created_at=time.time(),
                accessed_at=time.time(),
                analysis_duration_ms=analysis_duration_ms,
            )

            with self.cache_lock:
                self._add_entry(cache_key, entry)
                self._enforce_cache_limits()

            logger.debug(f"Cached AST for: {file_path}")

        except Exception as e:
            logger.warning(f"Failed to cache AST for {file_path}: {e}")

    def get_analysis_result(
        self, file_path: Union[str, Path], analysis_type: str = "connascence"
    ) -> Optional[Dict[str, Any]]:
        """Get cached analysis result for file."""

        file_path = Path(file_path)
        cache_key = self._generate_cache_key(file_path, f"analysis_{analysis_type}")

        with self.cache_lock:
            entry = self.memory_cache.get(cache_key)

            if entry and entry.is_valid():
                entry.update_access()
                self.cache_stats["hits"] += 1
                logger.debug(f"Cache hit for {analysis_type} analysis: {file_path}")
                return entry.data
            elif entry:
                self._remove_entry(cache_key)
                self.cache_stats["invalidations"] += 1

            self.cache_stats["misses"] += 1
            return None

    def put_analysis_result(
        self,
        file_path: Union[str, Path],
        result: Dict[str, Any],
        analysis_type: str = "connascence",
        analysis_duration_ms: float = 0.0,
    ):
        """Cache analysis result for file."""

        file_path = Path(file_path)
        cache_key = self._generate_cache_key(file_path, f"analysis_{analysis_type}")

        try:
            file_stat = file_path.stat()

            entry = CacheEntry(
                key=cache_key,
                data=result,
                file_path=str(file_path),
                file_mtime=file_stat.st_mtime,
                file_size=file_stat.st_size,
                created_at=time.time(),
                accessed_at=time.time(),
                analysis_duration_ms=analysis_duration_ms,
            )

            with self.cache_lock:
                self._add_entry(cache_key, entry)
                self._enforce_cache_limits()

            logger.debug(f"Cached {analysis_type} analysis for: {file_path}")

        except Exception as e:
            logger.warning(f"Failed to cache analysis result for {file_path}: {e}")

    def invalidate_file(self, file_path: Union[str, Path]):
        """Invalidate all cache entries for a specific file."""

        ProductionAssert.not_none(file_path, "file_path")

        ProductionAssert.not_none(file_path, "file_path")

        ProductionAssert.not_none(file_path, "file_path")

        ProductionAssert.not_none(file_path, "file_path")

        file_path = Path(file_path)

        with self.cache_lock:
            keys_to_remove = [key for key, entry in self.memory_cache.items() if entry.file_path == str(file_path)]

            for key in keys_to_remove:
                self._remove_entry(key)
                self.cache_stats["invalidations"] += 1

        logger.debug(f"Invalidated cache for: {file_path}")

    def clear_cache(self):
        """Clear all cache entries."""

        with self.cache_lock:
            if self.enable_persistence:
                # Remove all cache files
                for cache_file in self.cache_dir.glob("*.cache"):
                    try:
                        cache_file.unlink()
                    except Exception as e:
                        logger.warning(f"Failed to delete cache file {cache_file}: {e}")

            self.memory_cache.clear()
            self.cache_stats = {"hits": 0, "misses": 0, "invalidations": 0, "evictions": 0, "size_bytes": 0}

        logger.info("Cache cleared")

    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache performance statistics."""

        with self.cache_lock:
            total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
            hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0

            # Calculate memory usage
            memory_usage_mb = self.cache_stats["size_bytes"] / (1024 * 1024)

            # Entry statistics
            if self.memory_cache:
                access_counts = [entry.access_count for entry in self.memory_cache.values()]
                avg_access_count = sum(access_counts) / len(access_counts)

                durations = [
                    entry.analysis_duration_ms for entry in self.memory_cache.values() if entry.analysis_duration_ms > 0
                ]
                avg_analysis_time = sum(durations) / len(durations) if durations else 0
            else:
                avg_access_count = 0
                avg_analysis_time = 0

            return {
                "hit_rate_percent": hit_rate,
                "total_requests": total_requests,
                "cache_hits": self.cache_stats["hits"],
                "cache_misses": self.cache_stats["misses"],
                "invalidations": self.cache_stats["invalidations"],
                "evictions": self.cache_stats["evictions"],
                "entries_count": len(self.memory_cache),
                "memory_usage_mb": memory_usage_mb,
                "memory_limit_mb": self.max_size_bytes / (1024 * 1024),
                "memory_utilization_percent": (memory_usage_mb / (self.max_size_bytes / (1024 * 1024))) * 100,
                "avg_access_count": avg_access_count,
                "avg_analysis_time_ms": avg_analysis_time,
            }

    def optimize_cache(self):
        """Optimize cache by removing stale entries and defragmenting."""

        logger.info("Starting cache optimization")
        start_time = time.time()

        with self.cache_lock:
            initial_count = len(self.memory_cache)

            # Remove invalid entries
            invalid_keys = [key for key, entry in self.memory_cache.items() if not entry.is_valid()]

            for key in invalid_keys:
                self._remove_entry(key)
                self.cache_stats["invalidations"] += 1

            # Enforce cache limits
            self._enforce_cache_limits()

            # Persist cache index
            if self.enable_persistence:
                self._save_cache_index()

        optimization_time = time.time() - start_time
        final_count = len(self.memory_cache)
        removed_count = initial_count - final_count

        logger.info(
            f"Cache optimization complete: removed {removed_count} entries, "
            f"{final_count} remaining, took {optimization_time:.2f}s"
        )

    def warm_cache(self, file_paths: List[Union[str, Path]], max_workers: int = 4):
        """Pre-warm cache by analyzing multiple files in parallel."""

        ProductionAssert.not_none(file_paths, "file_paths")

        ProductionAssert.not_none(file_paths, "file_paths")

        ProductionAssert.not_none(max_workers, "max_workers")

        ProductionAssert.not_none(file_paths, "file_paths")

        ProductionAssert.not_none(file_paths, "file_paths")

        ProductionAssert.not_none(max_workers, "max_workers")

        logger.info(f"Warming cache for {len(file_paths)} files with {max_workers} workers")
        start_time = time.time()

        def analyze_and_cache(file_path):
            """Analyze file and cache results."""

            ProductionAssert.not_none(file_path, "file_path")

            ProductionAssert.not_none(file_path, "file_path")

            file_path = Path(file_path)

            try:
                # Check if already cached
                if self.get_ast(file_path) is not None:
                    return f"already_cached: {file_path}"

                # Parse AST
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                ast_start = time.time()
                ast_tree = ast.parse(content, filename=str(file_path))
                ast_duration = (time.time() - ast_start) * 1000

                # Cache AST
                self.put_ast(file_path, ast_tree, ast_duration)

                return f"cached: {file_path}"

            except Exception as e:
                logger.warning(f"Failed to warm cache for {file_path}: {e}")
                return f"failed: {file_path}"

        # Process files in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(analyze_and_cache, file_paths))

        # Summarize results
        cached_count = sum(1 for r in results if r.startswith("cached:"))
        already_cached_count = sum(1 for r in results if r.startswith("already_cached:"))
        failed_count = sum(1 for r in results if r.startswith("failed:"))

        warm_time = time.time() - start_time

        logger.info(
            f"Cache warming complete: {cached_count} cached, "
            f"{already_cached_count} already cached, {failed_count} failed, "
            f"took {warm_time:.2f}s"
        )

    # Private implementation methods

    def _generate_cache_key(self, file_path: Path, cache_type: str) -> str:
        """Generate cache key for file and analysis type."""

        # Include file path and type in hash for uniqueness
        key_data = f"{file_path.absolute()}:{cache_type}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _add_entry(self, key: str, entry: CacheEntry):
        """Add entry to cache."""

        # Calculate entry size (rough estimate)
        try:
            entry_size = len(pickle.dumps(entry.data))
        except Exception:
            entry_size = 1024  # Default estimate

        self.memory_cache[key] = entry
        self.cache_stats["size_bytes"] += entry_size

        # Persist to disk if enabled
        if self.enable_persistence:
            self._persist_entry(key, entry)

    def _remove_entry(self, key: str):
        """Remove entry from cache."""

        if key in self.memory_cache:
            entry = self.memory_cache[key]

            # Estimate size reduction
            try:
                entry_size = len(pickle.dumps(entry.data))
            except Exception:
                entry_size = 1024

            del self.memory_cache[key]
            self.cache_stats["size_bytes"] -= entry_size

            # Remove from disk if enabled
            if self.enable_persistence:
                cache_file = self.cache_dir / f"{key}.cache"
                try:
                    if cache_file.exists():
                        cache_file.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete cache file {cache_file}: {e}")

    def _enforce_cache_limits(self):
        """Enforce cache size and entry count limits."""

        # Check entry count limit
        if len(self.memory_cache) > self.max_entries:
            # Remove least recently used entries
            lru_entries = sorted(self.memory_cache.items(), key=lambda x: (x[1].accessed_at, x[1].access_count))

            entries_to_remove = len(self.memory_cache) - self.max_entries
            for key, _ in lru_entries[:entries_to_remove]:
                self._remove_entry(key)
                self.cache_stats["evictions"] += 1

        # Check memory size limit
        if self.cache_stats["size_bytes"] > self.max_size_bytes:
            # Remove entries until under limit
            lru_entries = sorted(self.memory_cache.items(), key=lambda x: (x[1].accessed_at, x[1].access_count))

            for key, _ in lru_entries:
                if self.cache_stats["size_bytes"] <= self.max_size_bytes * 0.9:
                    break
                self._remove_entry(key)
                self.cache_stats["evictions"] += 1

    def _persist_entry(self, key: str, entry: CacheEntry):
        """Persist cache entry to disk."""

        try:
            cache_file = self.cache_dir / f"{key}.cache"

            with open(cache_file, "wb") as f:
                if self.enable_compression:
                    import gzip

                    with gzip.open(f, "wb") as gf:
                        pickle.dump(entry, gf)
                else:
                    pickle.dump(entry, f)

        except Exception as e:
            logger.warning(f"Failed to persist cache entry {key}: {e}")

    def _load_cache_index(self):
        """Load cache entries from disk."""

        if not self.cache_dir.exists():
            return

        loaded_count = 0
        failed_count = 0

        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                key = cache_file.stem

                with open(cache_file, "rb") as f:
                    if self.enable_compression:
                        import gzip

                        with gzip.open(f, "rb") as gf:
                            entry = pickle.load(gf)
                    else:
                        entry = pickle.load(f)

                # Validate entry
                if entry.is_valid():
                    self.memory_cache[key] = entry
                    loaded_count += 1
                else:
                    # Remove invalid cache file
                    cache_file.unlink()
                    failed_count += 1

            except Exception as e:
                logger.warning(f"Failed to load cache file {cache_file}: {e}")
                failed_count += 1

        if loaded_count > 0:
            logger.info(f"Loaded {loaded_count} cache entries from disk ({failed_count} invalid)")

    def _save_cache_index(self):
        """Save current cache entries to disk."""

        saved_count = 0

        for key, entry in self.memory_cache.items():
            try:
                self._persist_entry(key, entry)
                saved_count += 1
            except Exception as e:
                logger.warning(f"Failed to save cache entry {key}: {e}")

        logger.debug(f"Saved {saved_count} cache entries to disk")

    def get_python_files(self, project_path: str) -> List[Path]:
        """
        Get all Python files in project directory.
        This method is required by UnifiedConnascenceAnalyzer.
        """
        ProductionAssert.not_none(project_path, "project_path")

        project_path_obj = Path(project_path)

        if not project_path_obj.exists():
            logger.warning(f"Project path does not exist: {project_path}")
            return []

        if not project_path_obj.is_dir():
            logger.warning(f"Project path is not a directory: {project_path}")
            return []

        # Use glob to find all Python files recursively
        try:
            python_files = list(project_path_obj.glob("**/*.py"))
            logger.debug(f"Found {len(python_files)} Python files in {project_path}")
            return python_files
        except Exception as e:
            logger.error(f"Failed to find Python files in {project_path}: {e}")
            return []


# Global cache instance
ast_cache = ASTCache()


def get_cached_ast(file_path: Union[str, Path]) -> Optional[ast.AST]:
    """Get cached AST for file (convenience function)."""
    return ast_cache.get_ast(file_path)


def cache_ast(file_path: Union[str, Path], ast_tree: ast.AST, analysis_duration_ms: float = 0.0):
    """Cache AST for file (convenience function)."""

    ProductionAssert.not_none(file_path, "file_path")

    ProductionAssert.not_none(file_path, "file_path")

    ProductionAssert.not_none(ast_tree, "ast_tree")

    ProductionAssert.not_none(analysis_duration_ms, "analysis_duration_ms")

    ProductionAssert.not_none(file_path, "file_path")

    ProductionAssert.not_none(file_path, "file_path")

    ProductionAssert.not_none(ast_tree, "ast_tree")

    ProductionAssert.not_none(analysis_duration_ms, "analysis_duration_ms")

    ast_cache.put_ast(file_path, ast_tree, analysis_duration_ms)


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics (convenience function)."""
    return ast_cache.get_cache_statistics()


def optimize_cache():
    """Optimize cache (convenience function)."""
    ast_cache.optimize_cache()


def clear_cache():
    """Clear cache (convenience function)."""
    ast_cache.clear_cache()
