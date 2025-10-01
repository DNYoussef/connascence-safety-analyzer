"""
Resource Cleanup Automation System
==================================

Comprehensive resource management system for automatic cleanup and recovery.
Provides context managers, cleanup hooks, and emergency procedures to prevent
resource leaks and ensure NASA Rule 7 compliance.

Features:
- Context managers for guaranteed resource cleanup
- Automatic file handle and AST tree cleanup
- Thread-safe resource tracking and cleanup
- Emergency cleanup procedures for out-of-memory conditions
- Resource usage monitoring and optimization
"""

import ast
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
import gc
import logging
from pathlib import Path
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Set, Union
import weakref

from fixes.phase0.production_safe_assertions import ProductionAssert

logger = logging.getLogger(__name__)


@dataclass
class ResourceTracker:
    """Track resource usage and cleanup operations."""

    resource_type: str
    resource_id: str
    created_at: float
    size_bytes: int = 0
    cleanup_callback: Optional[Callable[[], None]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def cleanup(self) -> bool:
        """Execute cleanup callback if available."""
        try:
            if self.cleanup_callback:
                self.cleanup_callback()
                return True
        except Exception as e:
            logger.error(f"Cleanup failed for {self.resource_type}:{self.resource_id}: {e}")
            return False
        return True


@dataclass
class ResourceStats:
    """Resource usage statistics."""

    total_created: int = 0
    total_cleaned: int = 0
    currently_tracked: int = 0
    peak_tracked: int = 0
    total_size_bytes: int = 0
    cleanup_failures: int = 0
    emergency_cleanups: int = 0

    @property
    def cleanup_success_rate(self) -> float:
        """Calculate cleanup success rate."""
        total_attempted = self.total_cleaned + self.cleanup_failures
        if total_attempted == 0:
            return 1.0
        return self.total_cleaned / total_attempted

    @property
    def resource_leak_count(self) -> int:
        """Calculate potential resource leaks."""
        return self.total_created - self.total_cleaned - self.currently_tracked


class ResourceManager:
    """
    Comprehensive resource management system with automatic cleanup.

    Thread-safe resource tracking with guaranteed cleanup procedures.
    NASA Rule 7 compliant with bounded resource usage and monitoring.
    """

    def __init__(self, max_tracked_resources: int = 10000):
        """
        Initialize resource manager.

        Args:
            max_tracked_resources: Maximum resources to track (NASA Rule 7)
        """
        assert 1000 <= max_tracked_resources <= 50000, "max_tracked_resources must be 1000-50000"

        self.max_tracked_resources = max_tracked_resources

        # Resource tracking
        self._resources: Dict[str, ResourceTracker] = {}
        self._resources_by_type: Dict[str, Set[str]] = defaultdict(set)
        self._stats_by_type: Dict[str, ResourceStats] = defaultdict(ResourceStats)
        self._lock = threading.RLock()

        # Cleanup callbacks and hooks
        self._cleanup_hooks: List[Callable[[], None]] = []
        self._emergency_hooks: List[Callable[[], None]] = []
        self._periodic_cleanup_callbacks: List[Callable[[], int]] = []

        # Periodic cleanup
        self._cleanup_thread: Optional[threading.Thread] = None
        self._cleanup_active = False
        self._cleanup_interval = 30.0  # 30 seconds

        # Weak reference tracking for automatic cleanup
        self._weak_refs: Dict[str, weakref.ref] = {}

    def start_periodic_cleanup(self) -> None:
        """Start background periodic cleanup."""
        with self._lock:
            if self._cleanup_active:
                return

            self._cleanup_active = True
            self._cleanup_thread = threading.Thread(
                target=self._periodic_cleanup_loop, name="ResourceCleanup", daemon=True
            )
            self._cleanup_thread.start()
            logger.info("Periodic resource cleanup started")

    def stop_periodic_cleanup(self) -> None:
        """Stop background periodic cleanup."""
        with self._lock:
            if not self._cleanup_active:
                return

            self._cleanup_active = False
            if self._cleanup_thread and self._cleanup_thread.is_alive():
                self._cleanup_thread.join(timeout=5.0)

        logger.info("Periodic resource cleanup stopped")

    def register_resource(
        self,
        resource_type: str,
        resource_id: str,
        resource_obj: Any = None,
        size_bytes: int = 0,
        cleanup_callback: Optional[Callable[[], None]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Register resource for tracking and cleanup.

        Args:
            resource_type: Type of resource (e.g., 'file', 'ast_tree', 'cache_entry')
            resource_id: Unique identifier for resource
            resource_obj: Optional resource object for weak reference tracking
            size_bytes: Size of resource in bytes
            cleanup_callback: Callback for resource cleanup
            metadata: Additional metadata

        Returns:
            Resource tracking ID
        """
        assert resource_type, "resource_type cannot be empty"
        assert resource_id, "resource_id cannot be empty"
        assert size_bytes >= 0, "size_bytes cannot be negative"

        with self._lock:
            # Enforce bounded resource tracking (NASA Rule 7)
            if len(self._resources) >= self.max_tracked_resources:
                self._emergency_cleanup()

            tracking_id = f"{resource_type}:{resource_id}"

            # Create resource tracker
            tracker = ResourceTracker(
                resource_type=resource_type,
                resource_id=resource_id,
                created_at=time.time(),
                size_bytes=size_bytes,
                cleanup_callback=cleanup_callback,
                metadata=metadata or {},
            )

            # Store tracker
            self._resources[tracking_id] = tracker
            self._resources_by_type[resource_type].add(tracking_id)

            # Update statistics
            stats = self._stats_by_type[resource_type]
            stats.total_created += 1
            stats.currently_tracked += 1
            stats.peak_tracked = max(stats.peak_tracked, stats.currently_tracked)
            stats.total_size_bytes += size_bytes

            # Set up weak reference for automatic cleanup
            if resource_obj is not None:
                try:
                    self._weak_refs[tracking_id] = weakref.ref(
                        resource_obj, lambda ref, tid=tracking_id: self._cleanup_resource(tid)
                    )
                except TypeError:
                    # Object doesn't support weak references
                    pass

            return tracking_id

    def cleanup_resource(self, tracking_id: str) -> bool:
        """
        Manually cleanup specific resource.

        Args:
            tracking_id: Resource tracking ID

        Returns:
            True if cleanup successful
        """
        return self._cleanup_resource(tracking_id)

    def _cleanup_resource(self, tracking_id: str) -> bool:
        """Internal resource cleanup implementation."""
        with self._lock:
            tracker = self._resources.get(tracking_id)
            if not tracker:
                return True  # Already cleaned up

            # Execute cleanup
            cleanup_success = tracker.cleanup()

            # Remove from tracking
            self._resources.pop(tracking_id, None)
            self._resources_by_type[tracker.resource_type].discard(tracking_id)

            # Remove weak reference
            self._weak_refs.pop(tracking_id, None)

            # Update statistics
            stats = self._stats_by_type[tracker.resource_type]
            stats.currently_tracked -= 1
            stats.total_size_bytes -= tracker.size_bytes

            if cleanup_success:
                stats.total_cleaned += 1
            else:
                stats.cleanup_failures += 1

            return cleanup_success

    def cleanup_by_type(self, resource_type: str) -> int:
        """
        Cleanup all resources of specified type.

        Args:
            resource_type: Type of resources to cleanup

        Returns:
            Number of resources cleaned up
        """
        with self._lock:
            tracking_ids = list(self._resources_by_type.get(resource_type, set()))
            cleaned_count = 0

            for tracking_id in tracking_ids:
                if self._cleanup_resource(tracking_id):
                    cleaned_count += 1

            return cleaned_count

    def cleanup_old_resources(self, max_age_seconds: float = 300.0) -> int:
        """
        Cleanup resources older than specified age.

        Args:
            max_age_seconds: Maximum age in seconds

        Returns:
            Number of resources cleaned up
        """
        current_time = time.time()
        old_resources = []

        with self._lock:
            for tracking_id, tracker in self._resources.items():
                if current_time - tracker.created_at > max_age_seconds:
                    old_resources.append(tracking_id)

        cleaned_count = 0
        for tracking_id in old_resources:
            if self._cleanup_resource(tracking_id):
                cleaned_count += 1

        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old resources (age > {max_age_seconds}s)")

        return cleaned_count

    def cleanup_large_resources(self, min_size_mb: float = 50.0) -> int:
        """
        Cleanup resources larger than specified size.

        Args:
            min_size_mb: Minimum size in MB

        Returns:
            Number of resources cleaned up
        """
        min_size_bytes = int(min_size_mb * 1024 * 1024)
        large_resources = []

        with self._lock:
            for tracking_id, tracker in self._resources.items():
                if tracker.size_bytes >= min_size_bytes:
                    large_resources.append(tracking_id)

        cleaned_count = 0
        for tracking_id in large_resources:
            if self._cleanup_resource(tracking_id):
                cleaned_count += 1

        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} large resources (size > {min_size_mb}MB)")

        return cleaned_count

    def _emergency_cleanup(self) -> int:
        """Emergency cleanup when resource limits exceeded."""
        logger.warning("Executing emergency resource cleanup")

        cleaned_count = 0

        # First: cleanup old resources
        cleaned_count += self.cleanup_old_resources(max_age_seconds=120.0)

        # Second: cleanup large resources
        cleaned_count += self.cleanup_large_resources(min_size_mb=10.0)

        # Third: execute emergency hooks
        for hook in self._emergency_hooks:
            try:
                hook()
                cleaned_count += 1
            except Exception as e:
                logger.error(f"Emergency hook failed: {e}")

        # Fourth: force garbage collection
        gc.collect()

        # Update emergency cleanup statistics
        for stats in self._stats_by_type.values():
            stats.emergency_cleanups += 1

        logger.warning(f"Emergency cleanup completed: {cleaned_count} resources cleaned")
        return cleaned_count

    def _periodic_cleanup_loop(self) -> None:
        """Background periodic cleanup loop."""
        logger.info("Resource cleanup loop started")

        while self._cleanup_active:
            try:
                self._perform_periodic_cleanup()
                time.sleep(self._cleanup_interval)
            except Exception as e:
                logger.error(f"Periodic cleanup error: {e}")
                time.sleep(self._cleanup_interval * 2)  # Back off on errors

        logger.info("Resource cleanup loop ended")

    def _perform_periodic_cleanup(self) -> None:
        """Perform periodic cleanup operations."""
        # Cleanup old resources (> 5 minutes)
        cleaned_old = self.cleanup_old_resources(max_age_seconds=300.0)

        # Cleanup large resources if memory pressure detected
        total_size_mb = sum(stats.total_size_bytes for stats in self._stats_by_type.values()) / (1024 * 1024)

        if total_size_mb > 500:  # More than 500MB tracked
            cleaned_large = self.cleanup_large_resources(min_size_mb=20.0)
        else:
            cleaned_large = 0

        # Execute periodic cleanup callbacks
        callback_cleaned = 0
        for callback in self._periodic_cleanup_callbacks:
            try:
                callback_cleaned += callback()
            except Exception as e:
                logger.error(f"Periodic cleanup callback failed: {e}")

        total_cleaned = cleaned_old + cleaned_large + callback_cleaned
        if total_cleaned > 0:
            logger.debug(f"Periodic cleanup: {total_cleaned} resources cleaned")

    def add_cleanup_hook(self, callback: Callable[[], None]) -> None:
        """Add cleanup hook for shutdown procedures."""
        assert callable(callback), "callback must be callable"
        self._cleanup_hooks.append(callback)

    def add_emergency_hook(self, callback: Callable[[], None]) -> None:
        """Add emergency cleanup hook."""
        assert callable(callback), "callback must be callable"
        self._emergency_hooks.append(callback)

    def add_periodic_cleanup_callback(self, callback: Callable[[], int]) -> None:
        """Add periodic cleanup callback that returns number of items cleaned."""
        assert callable(callback), "callback must be callable"
        self._periodic_cleanup_callbacks.append(callback)

    def cleanup_all(self) -> int:
        """Cleanup all tracked resources."""
        with self._lock:
            tracking_ids = list(self._resources.keys())

        cleaned_count = 0
        for tracking_id in tracking_ids:
            if self._cleanup_resource(tracking_id):
                cleaned_count += 1

        # Execute cleanup hooks
        for hook in self._cleanup_hooks:
            try:
                hook()
            except Exception as e:
                logger.error(f"Cleanup hook failed: {e}")

        logger.info(f"Cleaned up all resources: {cleaned_count} resources")
        return cleaned_count

    def get_resource_stats(self) -> Dict[str, ResourceStats]:
        """Get resource statistics by type."""
        with self._lock:
            return {
                resource_type: ResourceStats(
                    total_created=stats.total_created,
                    total_cleaned=stats.total_cleaned,
                    currently_tracked=stats.currently_tracked,
                    peak_tracked=stats.peak_tracked,
                    total_size_bytes=stats.total_size_bytes,
                    cleanup_failures=stats.cleanup_failures,
                    emergency_cleanups=stats.emergency_cleanups,
                )
                for resource_type, stats in self._stats_by_type.items()
            }

    def get_resource_report(self) -> Dict[str, Any]:
        """Generate comprehensive resource management report."""
        stats_by_type = self.get_resource_stats()

        total_stats = ResourceStats()
        for stats in stats_by_type.values():
            total_stats.total_created += stats.total_created
            total_stats.total_cleaned += stats.total_cleaned
            total_stats.currently_tracked += stats.currently_tracked
            total_stats.peak_tracked += stats.peak_tracked
            total_stats.total_size_bytes += stats.total_size_bytes
            total_stats.cleanup_failures += stats.cleanup_failures
            total_stats.emergency_cleanups += stats.emergency_cleanups

        return {
            "summary": {
                "resources_created": total_stats.total_created,
                "resources_cleaned": total_stats.total_cleaned,
                "currently_tracked": total_stats.currently_tracked,
                "peak_tracked": total_stats.peak_tracked,
                "cleanup_success_rate": total_stats.cleanup_success_rate,
                "resource_leaks": total_stats.resource_leak_count,
                "emergency_cleanups": total_stats.emergency_cleanups,
                "total_size_mb": total_stats.total_size_bytes / (1024 * 1024),
            },
            "by_type": {
                resource_type: {
                    "created": stats.total_created,
                    "cleaned": stats.total_cleaned,
                    "tracked": stats.currently_tracked,
                    "size_mb": stats.total_size_bytes / (1024 * 1024),
                    "success_rate": stats.cleanup_success_rate,
                    "leaks": stats.resource_leak_count,
                }
                for resource_type, stats in stats_by_type.items()
            },
            "recommendations": self._generate_resource_recommendations(total_stats),
        }

    def _generate_resource_recommendations(self, stats: ResourceStats) -> List[str]:
        """Generate resource management recommendations."""
        recommendations = []

        if stats.resource_leak_count > 0:
            recommendations.append(
                f"Potential resource leaks detected: {stats.resource_leak_count} resources not cleaned up"
            )

        if stats.cleanup_success_rate < 0.95:
            recommendations.append(
                f"Low cleanup success rate ({stats.cleanup_success_rate:.1%}) - review cleanup callbacks"
            )

        if stats.emergency_cleanups > 0:
            recommendations.append(
                f"Emergency cleanups triggered ({stats.emergency_cleanups}x) - consider increasing cleanup frequency"
            )

        if stats.currently_tracked > self.max_tracked_resources * 0.8:
            recommendations.append("High resource tracking usage - consider more aggressive periodic cleanup")

        return recommendations

    def __enter__(self):
        """Context manager entry."""
        self.start_periodic_cleanup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.stop_periodic_cleanup()
        self.cleanup_all()


# Context managers for specific resource types


@contextmanager
def managed_file_handle(file_path: Union[str, Path], mode: str = "r", **kwargs):
    """Context manager for automatic file handle cleanup."""
    ProductionAssert.not_none(file_path, "file_path")
    ProductionAssert.not_none(mode, "mode")

    resource_manager = get_global_resource_manager()
    file_handle = None
    tracking_id = None

    try:
        file_handle = open(file_path, mode, **kwargs)
        tracking_id = resource_manager.register_resource(
            resource_type="file_handle",
            resource_id=str(file_path),
            resource_obj=file_handle,
            cleanup_callback=lambda: file_handle.close() if not file_handle.closed else None,
        )
        yield file_handle

    finally:
        if file_handle and not file_handle.closed:
            file_handle.close()
        if tracking_id:
            resource_manager.cleanup_resource(tracking_id)


@contextmanager
def managed_ast_tree(file_path: Union[str, Path], source_code: Optional[str] = None):
    """Context manager for automatic AST tree cleanup."""
    ProductionAssert.not_none(file_path, "file_path")

    resource_manager = get_global_resource_manager()
    tree = None
    tracking_id = None

    try:
        if source_code is None:
            with open(file_path, encoding="utf-8") as f:
                source_code = f.read()

        tree = ast.parse(source_code)

        # Estimate AST size (rough approximation)
        ast_size = len(source_code) * 2  # AST typically 2x source size

        tracking_id = resource_manager.register_resource(
            resource_type="ast_tree",
            resource_id=str(file_path),
            resource_obj=tree,
            size_bytes=ast_size,
            cleanup_callback=lambda: setattr(tree, "_fields", []) if tree else None,  # Clear AST
        )

        yield tree

    finally:
        if tracking_id:
            resource_manager.cleanup_resource(tracking_id)


@contextmanager
def managed_cache_entry(cache_key: str, cache_obj: Any, size_bytes: int = 0):
    """Context manager for automatic cache entry cleanup."""
    ProductionAssert.not_none(cache_key, "cache_key")
    ProductionAssert.not_none(cache_obj, "cache_obj")
    ProductionAssert.not_none(size_bytes, "size_bytes")

    ProductionAssert.not_none(cache_key, "cache_key")
    ProductionAssert.not_none(cache_obj, "cache_obj")
    ProductionAssert.not_none(size_bytes, "size_bytes")

    resource_manager = get_global_resource_manager()

    tracking_id = resource_manager.register_resource(
        resource_type="cache_entry",
        resource_id=cache_key,
        resource_obj=cache_obj,
        size_bytes=size_bytes,
        cleanup_callback=lambda: cache_obj.clear() if hasattr(cache_obj, "clear") else None,
    )

    try:
        yield cache_obj
    finally:
        resource_manager.cleanup_resource(tracking_id)


# Global resource manager instance
_global_resource_manager: Optional[ResourceManager] = None
_manager_lock = threading.Lock()


def get_global_resource_manager() -> ResourceManager:
    """Get or create global resource manager instance."""
    global _global_resource_manager

    with _manager_lock:
        if _global_resource_manager is None:
            _global_resource_manager = ResourceManager()
            _global_resource_manager.start_periodic_cleanup()

    return _global_resource_manager


def cleanup_all_resources() -> int:
    """Cleanup all tracked resources globally."""
    manager = get_global_resource_manager()
    return manager.cleanup_all()


def get_resource_report() -> Dict[str, Any]:
    """Get comprehensive resource management report."""
    manager = get_global_resource_manager()
    return manager.get_resource_report()


def shutdown_resource_management() -> None:
    """Shutdown global resource management."""
    global _global_resource_manager

    with _manager_lock:
        if _global_resource_manager:
            _global_resource_manager.stop_periodic_cleanup()
            _global_resource_manager.cleanup_all()
            _global_resource_manager = None
