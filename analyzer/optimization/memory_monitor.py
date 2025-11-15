"""
Memory Leak Detection and Monitoring System
==========================================

Real-time memory usage tracking and leak detection for the connascence analyzer.
Implements NASA Rule 7 compliance with bounded resource management and automatic
recovery procedures.

Features:
- Real-time memory usage tracking with configurable thresholds
- Memory leak detection using growth pattern analysis
- Automatic alerts and intervention when limits exceeded
- Memory profiling integration for detailed analysis
- Thread-safe monitoring for concurrent operations
"""

from collections import deque
from dataclasses import dataclass, field
import gc
import logging
import os
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

import psutil

logger = logging.getLogger(__name__)


@dataclass
class MemoryThreshold:
    """Memory threshold configuration."""

    warning_mb: int = 600  # Warning threshold in MB (increased for self-dogfooding workflow)
    critical_mb: int = 1200  # Critical threshold in MB
    maximum_mb: int = 3000  # Maximum allowed memory in MB (handles 2GB peak usage)
    growth_rate_mb_s: float = 10.0  # Maximum growth rate MB/s


@dataclass
class MemorySnapshot:
    """Memory usage snapshot at a point in time."""

    timestamp: float
    rss_mb: float  # Resident Set Size in MB
    vms_mb: float  # Virtual Memory Size in MB
    heap_objects: int  # Number of objects on heap
    process_memory_mb: float  # Process memory usage
    gc_collections: Tuple[int, int, int]  # GC collection counts

    def __post_init__(self):
        """Validate snapshot data."""
        assert self.rss_mb >= 0, "RSS memory cannot be negative"
        assert self.vms_mb >= 0, "VMS memory cannot be negative"
        assert self.heap_objects >= 0, "Heap objects cannot be negative"


@dataclass
class MemoryStats:
    """Aggregated memory statistics."""

    current_usage_mb: float = 0.0
    peak_usage_mb: float = 0.0
    average_usage_mb: float = 0.0
    leak_detected: bool = False
    growth_rate_mb_s: float = 0.0
    snapshots_count: int = 0
    last_gc_time: float = 0.0
    leak_candidates: List[str] = field(default_factory=list)


class MemoryLeakDetector:
    """
    Advanced memory leak detection using statistical analysis.

    NASA Rule 7: Uses bounded operations and automatic cleanup.
    Enhanced for streaming analysis performance monitoring.
    """

    def __init__(self, window_size: int = 50, sensitivity: float = 1.5):
        """
        Initialize leak detector.

        Args:
            window_size: Number of snapshots to analyze (bounded per NASA Rule 7)
            sensitivity: Sensitivity multiplier for leak detection
        """
        assert 10 <= window_size <= 100, "window_size must be between 10-100"
        assert 1.0 <= sensitivity <= 3.0, "sensitivity must be between 1.0-3.0"

        self.window_size = window_size
        self.sensitivity = sensitivity
        self.memory_samples: deque = deque(maxlen=window_size)
        self.baseline_memory = 0.0
        self.leak_threshold_mb = 50.0  # 50MB growth indicates potential leak

        # Streaming analysis specific tracking
        self.stream_memory_samples: deque = deque(maxlen=100)  # Longer window for streaming
        self.incremental_analysis_memory = 0.0
        self.file_processing_memory_peak = 0.0
        self.streaming_session_start_memory = 0.0

    def add_sample(self, memory_mb: float, timestamp: float) -> bool:
        """
        Add memory sample and check for leaks.

        Args:
            memory_mb: Current memory usage in MB
            timestamp: Sample timestamp

        Returns:
            True if leak detected
        """
        assert memory_mb >= 0, "memory_mb cannot be negative"
        assert timestamp > 0, "timestamp must be positive"

        self.memory_samples.append((memory_mb, timestamp))
        self.stream_memory_samples.append((memory_mb, timestamp))

        # Track streaming session peaks
        self.file_processing_memory_peak = max(self.file_processing_memory_peak, memory_mb)

        # Need minimum samples for analysis
        if len(self.memory_samples) < 10:
            return False

        # Set baseline from early samples
        if not self.baseline_memory and len(self.memory_samples) >= 10:
            early_samples = list(self.memory_samples)[:10]
            self.baseline_memory = sum(sample[0] for sample in early_samples) / 10

        return self._analyze_leak_pattern()

    def start_streaming_session(self) -> None:
        """Mark the start of a streaming analysis session."""
        if self.memory_samples:
            self.streaming_session_start_memory = self.memory_samples[-1][0]
        else:
            # Get current memory if no samples yet
            import psutil

            try:
                self.streaming_session_start_memory = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logger.debug(f"Unable to get current process memory: {e}")
                self.streaming_session_start_memory = 0.0

    def get_streaming_memory_stats(self) -> Dict[str, float]:
        """Get streaming-specific memory statistics."""
        stats = {
            "session_start_mb": self.streaming_session_start_memory,
            "current_peak_mb": self.file_processing_memory_peak,
            "incremental_memory_mb": self.incremental_analysis_memory,
            "streaming_samples_count": len(self.stream_memory_samples),
        }

        if self.stream_memory_samples:
            current_memory = self.stream_memory_samples[-1][0]
            stats["current_memory_mb"] = current_memory
            stats["session_growth_mb"] = current_memory - self.streaming_session_start_memory

        return stats

    def _analyze_leak_pattern(self) -> bool:
        """
        Analyze memory pattern for leak indicators.

        NASA Rule 4: Function under 60 lines
        NASA Rule 7: Bounded analysis operations
        """
        if not self.baseline_memory or len(self.memory_samples) < 20:
            return False

        recent_samples = list(self.memory_samples)[-20:]  # Bounded analysis
        recent_memory = [sample[0] for sample in recent_samples]

        # Calculate trend and variance
        current_avg = sum(recent_memory) / len(recent_memory)
        growth = current_avg - self.baseline_memory

        # Check for sustained growth pattern
        if growth > self.leak_threshold_mb * self.sensitivity:
            # Additional validation: check if growth is consistent
            if self._is_consistent_growth(recent_samples):
                return True

        return False

    def _is_consistent_growth(self, samples: List[Tuple[float, float]]) -> bool:
        """Check if memory growth is consistent (leak indicator)."""
        if len(samples) < 10:
            return False

        # Check if most recent samples show upward trend
        memory_values = [sample[0] for sample in samples]
        increasing_count = 0

        for i in range(1, len(memory_values)):
            if memory_values[i] > memory_values[i - 1]:
                increasing_count += 1

        # If >70% of samples show growth, likely a leak
        return (increasing_count / (len(memory_values) - 1)) > 0.7


class MemoryMonitor:
    """
    Comprehensive memory monitoring system with leak detection and automatic recovery.

    Thread-safe monitoring suitable for concurrent analysis operations.
    NASA Rule 7 compliant with bounded resource usage.
    """

    def __init__(
        self, thresholds: Optional[MemoryThreshold] = None, monitoring_interval: float = 5.0, max_snapshots: int = 1000
    ):
        """
        Initialize memory monitor.

        Args:
            thresholds: Memory threshold configuration
            monitoring_interval: Seconds between memory checks
            max_snapshots: Maximum snapshots to retain (NASA Rule 7)
        """
        assert 1.0 <= monitoring_interval <= 60.0, "monitoring_interval must be 1-60 seconds"
        assert 100 <= max_snapshots <= 5000, "max_snapshots must be 100-5000"

        self.thresholds = thresholds or MemoryThreshold()
        self.monitoring_interval = monitoring_interval
        self.max_snapshots = max_snapshots

        # Monitoring state
        self._snapshots: deque = deque(maxlen=max_snapshots)
        self._stats = MemoryStats()
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()

        # Leak detection
        self._leak_detector = MemoryLeakDetector()
        self._alert_callbacks: List[Callable[[str, Dict], None]] = []

        # Process monitoring
        try:
            self._process = psutil.Process(os.getpid())
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Fallback for testing environments or restricted access
            self._process = None
        self._start_time = time.time()
        self._emergency_cleanup_callbacks: List[Callable[[], None]] = []

    def start_monitoring(self) -> None:
        """Start background memory monitoring."""
        with self._lock:
            if self._monitoring:
                logger.warning("Memory monitoring already active")
                return

            self._monitoring = True
            self._monitor_thread = threading.Thread(target=self._monitoring_loop, name="MemoryMonitor", daemon=True)
            self._monitor_thread.start()
            logger.info("Memory monitoring started")

    def stop_monitoring(self) -> None:
        """Stop background memory monitoring."""
        with self._lock:
            if not self._monitoring:
                return

            self._monitoring = False
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=5.0)

        logger.info("Memory monitoring stopped")

    def add_alert_callback(self, callback: Callable[[str, Dict], None]) -> None:
        """Add callback for memory alerts."""
        assert callable(callback), "callback must be callable"
        self._alert_callbacks.append(callback)

    def add_emergency_cleanup_callback(self, callback: Callable[[], None]) -> None:
        """Add callback for emergency cleanup procedures."""
        assert callable(callback), "callback must be callable"
        self._emergency_cleanup_callbacks.append(callback)

    def _monitoring_loop(self) -> None:
        """Main monitoring loop (runs in background thread)."""
        logger.info("Memory monitoring loop started")

        while self._monitoring:
            try:
                self._take_snapshot()
                time.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Memory monitoring error: {e}")
                time.sleep(self.monitoring_interval * 2)  # Back off on errors

        logger.info("Memory monitoring loop ended")

    def _take_snapshot(self) -> None:
        """Take memory usage snapshot and analyze."""
        try:
            # Get process memory info
            if self._process:
                try:
                    memory_info = self._process.memory_info()
                    memory_percent = self._process.memory_percent()
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    logger.debug(f"Process no longer exists or access denied: {e}")
                    # Fallback to default values
                    memory_info = type('MemInfo', (), {'rss': 0, 'vms': 0})()
                    memory_percent = 0.0
                    self._process = None  # Clear invalid process reference
            else:
                # Fallback when process is not available
                memory_info = type('MemInfo', (), {'rss': 0, 'vms': 0})()
                memory_percent = 0.0

            # Get system memory info
            system_memory = psutil.virtual_memory()

            # Get garbage collection stats
            gc.get_stats() if hasattr(gc, "get_stats") else []
            gc_collections = (
                gc.get_count()[0] if gc.get_count() else 0,
                gc.get_count()[1] if len(gc.get_count()) > 1 else 0,
                gc.get_count()[2] if len(gc.get_count()) > 2 else 0,
            )

            snapshot = MemorySnapshot(
                timestamp=time.time(),
                rss_mb=memory_info.rss / (1024 * 1024),
                vms_mb=memory_info.vms / (1024 * 1024),
                heap_objects=len(gc.get_objects()),
                process_memory_mb=(system_memory.total * memory_percent / 100) / (1024 * 1024),
                gc_collections=gc_collections,
            )

            with self._lock:
                self._snapshots.append(snapshot)
                self._update_stats(snapshot)
                self._check_thresholds(snapshot)

        except Exception as e:
            logger.error(f"Failed to take memory snapshot: {e}")

    def _update_stats(self, snapshot: MemorySnapshot) -> None:
        """Update aggregated statistics."""
        self._stats.current_usage_mb = snapshot.rss_mb
        self._stats.peak_usage_mb = max(self._stats.peak_usage_mb, snapshot.rss_mb)
        self._stats.snapshots_count += 1

        # Calculate average (bounded to recent samples)
        recent_snapshots = list(self._snapshots)[-100:]  # NASA Rule 7: bounded
        if recent_snapshots:
            self._stats.average_usage_mb = sum(s.rss_mb for s in recent_snapshots) / len(recent_snapshots)

        # Check for memory leaks
        leak_detected = self._leak_detector.add_sample(snapshot.rss_mb, snapshot.timestamp)

        if leak_detected and not self._stats.leak_detected:
            self._stats.leak_detected = True
            self._trigger_alert(
                "MEMORY_LEAK",
                {
                    "current_mb": snapshot.rss_mb,
                    "baseline_mb": self._leak_detector.baseline_memory,
                    "growth_mb": snapshot.rss_mb - self._leak_detector.baseline_memory,
                },
            )

    def _check_thresholds(self, snapshot: MemorySnapshot) -> None:
        """Check memory thresholds and trigger alerts."""
        memory_mb = snapshot.rss_mb

        if memory_mb > self.thresholds.maximum_mb:
            self._trigger_alert(
                "MEMORY_CRITICAL",
                {"current_mb": memory_mb, "limit_mb": self.thresholds.maximum_mb, "action": "emergency_cleanup"},
            )
            self._trigger_emergency_cleanup()

        elif memory_mb > self.thresholds.critical_mb:
            self._trigger_alert(
                "MEMORY_HIGH",
                {"current_mb": memory_mb, "limit_mb": self.thresholds.critical_mb, "action": "garbage_collection"},
            )
            # Force garbage collection
            gc.collect()

        elif memory_mb > self.thresholds.warning_mb:
            self._trigger_alert("MEMORY_WARNING", {"current_mb": memory_mb, "limit_mb": self.thresholds.warning_mb})

    def _trigger_alert(self, alert_type: str, context: Dict[str, Any]) -> None:
        """Trigger memory alert to registered callbacks."""
        logger.warning(f"Memory alert: {alert_type} - {context}")

        for callback in self._alert_callbacks:
            try:
                callback(alert_type, context)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")

    def _trigger_emergency_cleanup(self) -> None:
        """Trigger emergency cleanup procedures."""
        logger.critical("Triggering emergency memory cleanup")

        for callback in self._emergency_cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Emergency cleanup callback failed: {e}")

        # Force aggressive garbage collection
        for _ in range(3):
            gc.collect()

    def get_current_stats(self) -> MemoryStats:
        """Get current memory statistics."""
        with self._lock:
            # Create copy to avoid concurrent modification
            return MemoryStats(
                current_usage_mb=self._stats.current_usage_mb,
                peak_usage_mb=self._stats.peak_usage_mb,
                average_usage_mb=self._stats.average_usage_mb,
                leak_detected=self._stats.leak_detected,
                growth_rate_mb_s=self._stats.growth_rate_mb_s,
                snapshots_count=self._stats.snapshots_count,
                last_gc_time=self._stats.last_gc_time,
                leak_candidates=self._stats.leak_candidates.copy(),
            )

    def get_memory_report(self) -> Dict[str, Any]:
        """Generate comprehensive memory report."""
        with self._lock:
            stats = self.get_current_stats()
            recent_snapshots = list(self._snapshots)[-20:]  # Last 20 snapshots

            return {
                "monitoring_duration_minutes": (time.time() - self._start_time) / 60,
                "current_memory_mb": stats.current_usage_mb,
                "peak_memory_mb": stats.peak_usage_mb,
                "average_memory_mb": stats.average_usage_mb,
                "snapshots_analyzed": stats.snapshots_count,
                "leak_detected": stats.leak_detected,
                "thresholds": {
                    "warning_mb": self.thresholds.warning_mb,
                    "critical_mb": self.thresholds.critical_mb,
                    "maximum_mb": self.thresholds.maximum_mb,
                },
                "recent_trend": [s.rss_mb for s in recent_snapshots],
                "gc_objects_count": recent_snapshots[-1].heap_objects if recent_snapshots else 0,
                "recommendations": self._generate_recommendations(stats),
            }

    def _generate_recommendations(self, stats: MemoryStats) -> List[str]:
        """Generate memory optimization recommendations."""
        recommendations = []

        if stats.leak_detected:
            recommendations.append("Memory leak detected - investigate object retention patterns")

        if stats.peak_usage_mb > self.thresholds.critical_mb:
            recommendations.append("Peak memory usage high - consider increasing cache limits or reducing batch sizes")

        if stats.current_usage_mb > stats.average_usage_mb * 1.5:
            recommendations.append("Current memory usage above average - consider manual garbage collection")

        return recommendations

    def __enter__(self):
        """Context manager entry."""
        self.start_monitoring()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.stop_monitoring()


# Global memory monitor instance
_global_monitor: Optional[MemoryMonitor] = None
_monitor_lock = threading.Lock()


def get_global_memory_monitor() -> MemoryMonitor:
    """Get or create global memory monitor instance."""
    global _global_monitor

    with _monitor_lock:
        if _global_monitor is None:
            _global_monitor = MemoryMonitor()

    return _global_monitor


def start_global_monitoring() -> None:
    """Start global memory monitoring."""
    monitor = get_global_memory_monitor()
    monitor.start_monitoring()


def stop_global_monitoring() -> None:
    """Stop global memory monitoring."""
    global _global_monitor

    with _monitor_lock:
        if _global_monitor:
            _global_monitor.stop_monitoring()


def get_memory_report() -> Dict[str, Any]:
    """Get comprehensive memory report from global monitor."""
    monitor = get_global_memory_monitor()
    return monitor.get_memory_report()


# Context manager for temporary memory monitoring
class MemoryWatcher:
    """Context manager for temporary memory monitoring during analysis."""

    def __init__(self, name: str = "analysis"):
        self.name = name
        self.monitor = MemoryMonitor(monitoring_interval=2.0)  # More frequent monitoring
        self.start_memory = 0.0

    def __enter__(self):
        try:
            self.start_memory = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.debug(f"Unable to get start memory for {self.name}: {e}")
            self.start_memory = 0.0

        self.monitor.start_monitoring()
        return self.monitor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.monitor.stop_monitoring()

        try:
            end_memory = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
            logger.info(f"{self.name} memory usage: {end_memory - self.start_memory:.1f}MB")
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.debug(f"Unable to get end memory for {self.name}: {e}")
