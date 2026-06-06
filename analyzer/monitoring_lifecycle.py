"""Monitoring and cleanup lifecycle support for UnifiedConnascenceAnalyzer."""

import logging
from typing import Any, Dict

try:
    from .constants import CACHE_CLEANUP_AGE_SECONDS
except ImportError:
    from constants import CACHE_CLEANUP_AGE_SECONDS

logger = logging.getLogger(__name__)


class MonitoringLifecycleMixin:
    """Memory/resource monitoring hooks extracted from the unified analyzer."""

    def _setup_monitoring_and_cleanup_hooks(self) -> None:
        """
        Setup memory monitoring and resource cleanup hooks.
        Delegates to MonitoringCoordinator if available (Phase 7 decomposition).
        """
        # Phase 7: Delegate to MonitoringCoordinator if available
        if hasattr(self, 'monitoring_coordinator') and self.monitoring_coordinator:
            self.monitoring_coordinator.setup_hooks()
            return
        # Fallback: inline implementation (legacy support)
        if not (self.memory_monitor and self.resource_manager):
            return
        self.memory_monitor.add_alert_callback(self._handle_memory_alert)
        self.memory_monitor.add_emergency_cleanup_callback(self._emergency_memory_cleanup)
        self.resource_manager.add_cleanup_hook(self._cleanup_analysis_resources)
        self.resource_manager.add_emergency_hook(self._emergency_resource_cleanup)
        self.resource_manager.add_periodic_cleanup_callback(self._periodic_cache_cleanup)
        self.memory_monitor.start_monitoring()

    def _handle_memory_alert(self, alert_type: str, context: Dict[str, Any]) -> None:
        """Handle memory alerts. Delegates to MonitoringCoordinator if available."""
        # Phase 7: Delegate to MonitoringCoordinator
        if hasattr(self, 'monitoring_coordinator') and self.monitoring_coordinator:
            self.monitoring_coordinator.handle_memory_alert(alert_type, context)
            return
        # Fallback: inline implementation
        logger.warning(f"Memory alert: {alert_type}")
        if alert_type == "MEMORY_WARNING" and self.file_cache:
            self.file_cache.clear_cache()
        elif alert_type == "MEMORY_HIGH":
            self._aggressive_cleanup()
        elif alert_type == "MEMORY_CRITICAL":
            self._emergency_memory_cleanup()
        elif alert_type == "MEMORY_LEAK":
            self._investigate_memory_leak(context)

    def _emergency_memory_cleanup(self) -> None:
        """Emergency memory cleanup procedures.
        Delegates to MonitoringCoordinator if available (Phase 7 decomposition)."""
        # Phase 7: Delegate to MonitoringCoordinator
        if hasattr(self, 'monitoring_coordinator') and self.monitoring_coordinator:
            self.monitoring_coordinator._emergency_memory_cleanup()
            return
        # Fallback: inline implementation (legacy support)
        logger.critical("Executing emergency memory cleanup")

        try:
            # Clear all caches
            if self.file_cache:
                self.file_cache.clear_cache()

            # Force garbage collection
            import gc

            for _ in range(3):
                gc.collect()

            # Cleanup all tracked resources
            if self.resource_manager:
                cleaned = self.resource_manager.cleanup_all()
                logger.info(f"Emergency cleanup: {cleaned} resources cleaned")

        except Exception as e:
            logger.error(f"Emergency cleanup failed: {e}")

    def _aggressive_cleanup(self) -> None:
        """Aggressive cleanup for high memory usage.
        Delegates to MonitoringCoordinator if available (Phase 7 decomposition)."""
        # Phase 7: Delegate to MonitoringCoordinator
        if hasattr(self, 'monitoring_coordinator') and self.monitoring_coordinator:
            self.monitoring_coordinator._aggressive_cleanup()
            return
        # Fallback: inline implementation (legacy support)
        logger.info("Executing aggressive cleanup")

        # Clear cache entries older than 2 minutes
        if self.resource_manager:
            self.resource_manager.cleanup_old_resources(max_age_seconds=CACHE_CLEANUP_AGE_SECONDS)

        # Clear large cache entries
        if self.resource_manager:
            self.resource_manager.cleanup_large_resources(min_size_mb=5.0)

    def _cleanup_analysis_resources(self) -> None:
        """Cleanup analysis-specific resources.
        Delegates to MonitoringCoordinator if available (Phase 7 decomposition)."""
        # Phase 7: Delegate to MonitoringCoordinator
        if hasattr(self, 'monitoring_coordinator') and self.monitoring_coordinator:
            self.monitoring_coordinator._cleanup_analysis_resources()
            return
        # Fallback: inline implementation (legacy support)
        try:
            # Clear analysis patterns and priorities
            self._analysis_patterns.clear()
            self._file_priorities.clear()

            # Reset cache stats
            self._cache_stats = {"hits": 0, "misses": 0, "warm_requests": 0, "batch_loads": 0}

        except Exception as e:
            logger.error(f"Analysis resource cleanup failed: {e}")

    def _emergency_resource_cleanup(self) -> None:
        """Emergency resource cleanup procedures.
        Delegates to MonitoringCoordinator if available (Phase 7 decomposition)."""
        # Phase 7: Delegate to MonitoringCoordinator
        if hasattr(self, 'monitoring_coordinator') and self.monitoring_coordinator:
            self.monitoring_coordinator._emergency_resource_cleanup()
            return
        # Fallback: inline implementation (legacy support)
        logger.warning("Executing emergency resource cleanup")

        try:
            # Clear all analysis state
            self._cleanup_analysis_resources()

            # Clear component state
            if hasattr(self, "ast_analyzer") and self.ast_analyzer:
                if hasattr(self.ast_analyzer, "clear_state"):
                    self.ast_analyzer.clear_state()

        except Exception as e:
            logger.error(f"Emergency resource cleanup failed: {e}")

    def _periodic_cache_cleanup(self) -> int:
        """Periodic cache cleanup callback.
        Delegates to MonitoringCoordinator if available (Phase 7 decomposition)."""
        # Phase 7: Delegate to MonitoringCoordinator
        if hasattr(self, 'monitoring_coordinator') and self.monitoring_coordinator:
            return self.monitoring_coordinator._periodic_cache_cleanup()
        # Fallback: inline implementation (legacy support)
        cleaned_count = 0

        try:
            import time

            # Cleanup cache entries older than 10 minutes
            if self.file_cache and hasattr(self.file_cache, "_cache"):
                old_entries = []
                current_time = time.time()

                for key, entry in self.file_cache._cache.items():
                    if hasattr(entry, "last_accessed") and (current_time - entry.last_accessed) > 600:
                        old_entries.append(key)

                for key in old_entries[:50]:  # Limit to avoid excessive cleanup
                    if key in self.file_cache._cache:
                        del self.file_cache._cache[key]
                        cleaned_count += 1

        except Exception as e:
            logger.error(f"Periodic cache cleanup failed: {e}")

        return cleaned_count

    def _investigate_memory_leak(self, context: Dict[str, Any]) -> None:
        """Investigate potential memory leak with detailed analysis.
        Delegates to MonitoringCoordinator if available (Phase 7 decomposition)."""
        # Phase 7: Delegate to MonitoringCoordinator
        if hasattr(self, 'monitoring_coordinator') and self.monitoring_coordinator:
            self.monitoring_coordinator._investigate_memory_leak(context)
            return
        # Fallback: inline implementation (legacy support)
        try:
            import gc

            # Get object counts by type
            obj_counts = {}
            for obj in gc.get_objects()[:1000]:  # Bounded analysis (NASA Rule 7)
                obj_type = type(obj).__name__
                obj_counts[obj_type] = obj_counts.get(obj_type, 0) + 1

            # Log top object types
            top_types = sorted(obj_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            logger.warning(f"Top object types during leak: {top_types}")

        except Exception as e:
            logger.error(f"Memory leak investigation failed: {e}")

    def _log_comprehensive_monitoring_report(self) -> None:
        """Log comprehensive monitoring and resource management report.
        Delegates to MonitoringCoordinator if available (Phase 7 decomposition)."""
        # Phase 7: Delegate to MonitoringCoordinator
        if hasattr(self, 'monitoring_coordinator') and self.monitoring_coordinator:
            self.monitoring_coordinator._log_comprehensive_monitoring_report()
            return
        # Fallback: inline implementation (legacy support)
        try:
            logger.info("=== COMPREHENSIVE SYSTEM MONITORING REPORT ===")

            # Memory monitoring report
            if self.memory_monitor:
                memory_report = self.memory_monitor.get_memory_report()
                logger.info("Memory Monitoring Summary:")
                logger.info(f"  Current Usage: {memory_report['current_memory_mb']:.1f}MB")
                logger.info(f"  Peak Usage: {memory_report['peak_memory_mb']:.1f}MB")
                logger.info(f"  Average Usage: {memory_report['average_memory_mb']:.1f}MB")
                logger.info(f"  Monitoring Duration: {memory_report['monitoring_duration_minutes']:.1f} minutes")
                logger.info(f"  Leak Detected: {memory_report['leak_detected']}")

                if memory_report.get("recommendations"):
                    logger.info("  Memory Recommendations:")
                    for rec in memory_report["recommendations"]:
                        logger.info(f"    • {rec}")

            # Resource management report
            if self.resource_manager:
                resource_report = self.resource_manager.get_resource_report()
                summary = resource_report["summary"]

                logger.info("Resource Management Summary:")
                logger.info(f"  Resources Created: {summary['resources_created']}")
                logger.info(f"  Resources Cleaned: {summary['resources_cleaned']}")
                logger.info(f"  Currently Tracked: {summary['currently_tracked']}")
                logger.info(f"  Peak Tracked: {summary['peak_tracked']}")
                logger.info(f"  Cleanup Success Rate: {summary['cleanup_success_rate']:.1%}")
                logger.info(f"  Resource Leaks: {summary['resource_leaks']}")
                logger.info(f"  Emergency Cleanups: {summary['emergency_cleanups']}")
                logger.info(f"  Total Size: {summary['total_size_mb']:.1f}MB")

                if resource_report.get("recommendations"):
                    logger.info("  Resource Recommendations:")
                    for rec in resource_report["recommendations"]:
                        logger.info(f"    • {rec}")

                # Log by resource type
                logger.info("  Resource Breakdown by Type:")
                for resource_type, stats in resource_report["by_type"].items():
                    logger.info(
                        f"    {resource_type}: {stats['tracked']} tracked, "
                        f"{stats['size_mb']:.1f}MB, {stats['success_rate']:.1%} cleanup rate"
                    )

        except Exception as e:
            logger.error(f"Failed to generate comprehensive monitoring report: {e}")
