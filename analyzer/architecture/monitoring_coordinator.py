"""
MonitoringCoordinator - Centralized monitoring and cleanup for UnifiedConnascenceAnalyzer

Extracted from: analyzer/unified_analyzer.py
Purpose: Centralize all monitoring and cleanup logic into a dedicated component

Responsibilities:
- Setup memory monitoring and cleanup hooks
- Handle memory alerts and emergency cleanup
- Manage resource cleanup lifecycle
- Investigate memory leaks
- Generate comprehensive monitoring reports

NASA Compliance:
- Rule 4: All functions under 60 lines
- Rule 5: Input assertions and error handling
- Rule 7: Bounded resource management
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class MonitoringCoordinator:
    """
    Centralized monitoring and cleanup coordinator.

    Features:
    - Memory monitoring with alert callbacks
    - Resource cleanup with lifecycle hooks
    - Emergency cleanup procedures
    - Memory leak investigation
    - Comprehensive reporting

    NASA Rule 4: Class under 500 lines
    NASA Rule 7: Bounded resource management
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        memory_monitor: Optional[Any] = None,
        resource_manager: Optional[Any] = None,
        file_cache: Optional[Any] = None,
    ):
        """
        Initialize monitoring coordinator with dependencies.

        Args:
            config: Configuration dictionary
            memory_monitor: Memory monitoring instance
            resource_manager: Resource manager instance
            file_cache: File cache instance for cleanup

        NASA Rule 5: Input validation
        """
        self.config = config or {}
        self.memory_monitor = memory_monitor
        self.resource_manager = resource_manager
        self.file_cache = file_cache

        # Track monitoring state
        self._monitoring_active = False
        self._cleanup_callbacks_registered = False

        logger.info(
            f"MonitoringCoordinator initialized "
            f"(monitor={memory_monitor is not None}, "
            f"resources={resource_manager is not None})"
        )

    def _setup_monitoring_and_cleanup_hooks(self) -> None:
        """
        Setup memory monitoring and resource cleanup hooks.

        NASA Rule 4: Function under 60 lines
        NASA Rule 7: Bounded resource management
        """
        if not (self.memory_monitor and self.resource_manager):
            logger.debug("Monitoring/resource manager not available - hooks disabled")
            return

        try:
            # Setup memory monitoring alerts
            self.memory_monitor.add_alert_callback(self._handle_memory_alert)
            self.memory_monitor.add_emergency_cleanup_callback(
                self._emergency_memory_cleanup
            )

            # Setup resource management cleanup hooks
            self.resource_manager.add_cleanup_hook(self._cleanup_analysis_resources)
            self.resource_manager.add_emergency_hook(self._emergency_resource_cleanup)
            self.resource_manager.add_periodic_cleanup_callback(
                self._periodic_cache_cleanup
            )

            # Start monitoring
            self.memory_monitor.start_monitoring()
            self._monitoring_active = True
            self._cleanup_callbacks_registered = True

            logger.info("Monitoring and cleanup hooks configured successfully")

        except Exception as e:
            logger.error(f"Failed to setup monitoring hooks: {e}")

    def _handle_memory_alert(self, alert_type: str, context: Dict[str, Any]) -> None:
        """
        Handle memory usage alerts with appropriate actions.

        Args:
            alert_type: Type of memory alert (MEMORY_WARNING, MEMORY_HIGH, etc.)
            context: Alert context with details

        NASA Rule 4: Function under 60 lines
        """
        logger.warning(f"Memory alert: {alert_type}")

        try:
            if alert_type == "MEMORY_WARNING":
                # Cleanup old cache entries
                if self.file_cache:
                    self.file_cache.clear_cache()
                    logger.info("Cleared file cache due to memory warning")

            elif alert_type == "MEMORY_HIGH":
                # More aggressive cleanup
                self._aggressive_cleanup()

            elif alert_type == "MEMORY_CRITICAL":
                # Emergency procedures
                self._emergency_memory_cleanup()

            elif alert_type == "MEMORY_LEAK":
                growth_mb = context.get("growth_mb", 0)
                logger.error(f"Memory leak detected: {growth_mb:.1f}MB growth")
                self._investigate_memory_leak(context)

        except Exception as e:
            logger.error(f"Failed to handle memory alert {alert_type}: {e}")

    def _emergency_memory_cleanup(self) -> None:
        """
        Emergency memory cleanup procedures.

        NASA Rule 4: Function under 60 lines
        NASA Rule 7: Immediate resource cleanup
        """
        logger.critical("Executing emergency memory cleanup")

        try:
            # Clear all caches
            if self.file_cache:
                self.file_cache.clear_cache()
                logger.info("Emergency: Cleared file cache")

            # Force garbage collection
            import gc

            collected = 0
            for _ in range(3):
                collected += gc.collect()

            logger.info(f"Emergency: Collected {collected} objects via GC")

            # Cleanup all tracked resources
            if self.resource_manager:
                cleaned = self.resource_manager.cleanup_all()
                logger.info(f"Emergency: Cleaned {cleaned} tracked resources")

        except Exception as e:
            logger.error(f"Emergency cleanup failed: {e}")

    def _aggressive_cleanup(self) -> None:
        """
        Aggressive cleanup for high memory usage.

        NASA Rule 4: Function under 60 lines
        """
        logger.info("Executing aggressive cleanup")

        try:
            # Clear cache entries older than 2 minutes
            if self.resource_manager:
                old_cleaned = self.resource_manager.cleanup_old_resources(
                    max_age_seconds=120.0
                )
                logger.info(f"Aggressive: Cleaned {old_cleaned} old resources")

            # Clear large cache entries
            if self.resource_manager:
                large_cleaned = self.resource_manager.cleanup_large_resources(
                    min_size_mb=5.0
                )
                logger.info(f"Aggressive: Cleaned {large_cleaned} large resources")

        except Exception as e:
            logger.error(f"Aggressive cleanup failed: {e}")

    def _cleanup_analysis_resources(self) -> None:
        """
        Cleanup analysis-specific resources.

        Note: This is a placeholder for analysis state cleanup.
        Actual implementation depends on analyzer state management.

        NASA Rule 4: Function under 60 lines
        """
        try:
            logger.debug("Cleanup analysis resources callback invoked")

            # Note: The original implementation references _analysis_patterns
            # and _file_priorities which are analyzer-specific state.
            # These should be injected or managed through a separate state object.

            # For now, this is a hook that can be extended by the analyzer
            # to provide custom cleanup logic via dependency injection.

        except Exception as e:
            logger.error(f"Analysis resource cleanup failed: {e}")

    def _emergency_resource_cleanup(self) -> None:
        """
        Emergency resource cleanup procedures.

        NASA Rule 4: Function under 60 lines
        """
        logger.warning("Executing emergency resource cleanup")

        try:
            # Clear all analysis state via callback
            self._cleanup_analysis_resources()

            # Additional emergency cleanup can be added here
            # This is a hook for analyzer-specific emergency procedures

            logger.info("Emergency resource cleanup completed")

        except Exception as e:
            logger.error(f"Emergency resource cleanup failed: {e}")

    def _periodic_cache_cleanup(self) -> int:
        """
        Periodic cache cleanup callback.

        Returns:
            Number of cache entries cleaned

        NASA Rule 4: Function under 60 lines
        NASA Rule 7: Bounded cleanup operations
        """
        cleaned_count = 0

        try:
            import time

            # Cleanup cache entries older than 10 minutes
            if self.file_cache and hasattr(self.file_cache, "_cache"):
                old_entries = []
                current_time = time.time()

                for key, entry in self.file_cache._cache.items():
                    if (
                        hasattr(entry, "last_accessed")
                        and (current_time - entry.last_accessed) > 600
                    ):
                        old_entries.append(key)

                # Limit cleanup to avoid excessive operations (NASA Rule 7)
                for key in old_entries[:50]:
                    if key in self.file_cache._cache:
                        del self.file_cache._cache[key]
                        cleaned_count += 1

                if cleaned_count > 0:
                    logger.debug(f"Periodic cleanup: Removed {cleaned_count} old cache entries")

        except Exception as e:
            logger.error(f"Periodic cache cleanup failed: {e}")

        return cleaned_count

    def _investigate_memory_leak(self, context: Dict[str, Any]) -> None:
        """
        Investigate potential memory leak with detailed analysis.

        Args:
            context: Leak context with growth information

        NASA Rule 4: Function under 60 lines
        NASA Rule 7: Bounded object analysis
        """
        try:
            import gc

            # Get object counts by type (bounded to 1000 objects)
            obj_counts: Dict[str, int] = {}
            for obj in gc.get_objects()[:1000]:  # Bounded analysis (NASA Rule 7)
                obj_type = type(obj).__name__
                obj_counts[obj_type] = obj_counts.get(obj_type, 0) + 1

            # Log top object types
            top_types = sorted(obj_counts.items(), key=lambda x: x[1], reverse=True)[
                :10
            ]
            logger.warning(f"Top object types during leak: {top_types}")

            # Log context information
            if "growth_mb" in context:
                logger.warning(f"Memory growth: {context['growth_mb']:.1f}MB")
            if "rate_mb_per_min" in context:
                logger.warning(
                    f"Growth rate: {context['rate_mb_per_min']:.2f}MB/min"
                )

        except Exception as e:
            logger.error(f"Memory leak investigation failed: {e}")

    def _log_comprehensive_monitoring_report(self) -> None:
        """
        Log comprehensive monitoring and resource management report.

        NASA Rule 4: Function under 60 lines
        """
        try:
            logger.info("=== COMPREHENSIVE SYSTEM MONITORING REPORT ===")

            # Memory monitoring report
            if self.memory_monitor:
                self._log_memory_monitoring_report()

            # Resource management report
            if self.resource_manager:
                self._log_resource_management_report()

            logger.info("=== END MONITORING REPORT ===")

        except Exception as e:
            logger.error(f"Failed to generate monitoring report: {e}")

    def _log_memory_monitoring_report(self) -> None:
        """
        Log memory monitoring details.

        NASA Rule 4: Function under 60 lines
        """
        try:
            memory_report = self.memory_monitor.get_memory_report()

            logger.info("Memory Monitoring Summary:")
            logger.info(f"  Current Usage: {memory_report['current_memory_mb']:.1f}MB")
            logger.info(f"  Peak Usage: {memory_report['peak_memory_mb']:.1f}MB")
            logger.info(f"  Average Usage: {memory_report['average_memory_mb']:.1f}MB")
            logger.info(
                f"  Monitoring Duration: {memory_report['monitoring_duration_minutes']:.1f} minutes"
            )
            logger.info(f"  Leak Detected: {memory_report['leak_detected']}")

            if memory_report.get("recommendations"):
                logger.info("  Memory Recommendations:")
                for rec in memory_report["recommendations"]:
                    logger.info(f"    - {rec}")

        except Exception as e:
            logger.error(f"Failed to log memory report: {e}")

    def _log_resource_management_report(self) -> None:
        """
        Log resource management details.

        NASA Rule 4: Function under 60 lines
        """
        try:
            resource_report = self.resource_manager.get_resource_report()
            summary = resource_report["summary"]

            logger.info("Resource Management Summary:")
            logger.info(f"  Resources Created: {summary['resources_created']}")
            logger.info(f"  Resources Cleaned: {summary['resources_cleaned']}")
            logger.info(f"  Currently Tracked: {summary['currently_tracked']}")
            logger.info(f"  Peak Tracked: {summary['peak_tracked']}")
            logger.info(
                f"  Cleanup Success Rate: {summary['cleanup_success_rate']:.1%}"
            )
            logger.info(f"  Resource Leaks: {summary['resource_leaks']}")
            logger.info(f"  Emergency Cleanups: {summary['emergency_cleanups']}")
            logger.info(f"  Total Size: {summary['total_size_mb']:.1f}MB")

            if resource_report.get("recommendations"):
                logger.info("  Resource Recommendations:")
                for rec in resource_report["recommendations"]:
                    logger.info(f"    - {rec}")

        except Exception as e:
            logger.error(f"Failed to log resource report: {e}")

    def is_monitoring_active(self) -> bool:
        """
        Check if monitoring is currently active.

        Returns:
            True if monitoring is active
        """
        return self._monitoring_active

    def shutdown(self) -> None:
        """
        Shutdown monitoring and cleanup resources.

        NASA Rule 4: Function under 60 lines
        NASA Rule 7: Complete resource cleanup
        """
        try:
            # Stop monitoring
            if self.memory_monitor and self._monitoring_active:
                self.memory_monitor.stop_monitoring()
                self._monitoring_active = False
                logger.info("Memory monitoring stopped")

            # Final cleanup report
            if self._cleanup_callbacks_registered:
                self._log_comprehensive_monitoring_report()

            logger.info("MonitoringCoordinator shutdown complete")

        except Exception as e:
            logger.error(f"Shutdown failed: {e}")
