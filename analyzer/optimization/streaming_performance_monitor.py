"""
Streaming Performance Monitor
=============================

Specialized monitoring for streaming analysis performance, providing real-time
metrics for incremental processing, file change events, and memory usage
during streaming operations.

NASA Rule 7 Compliant: Bounded resource usage with automatic cleanup.
"""

import time
import logging
from collections import deque, defaultdict
from dataclasses import dataclass, field
from threading import Lock, RLock
from typing import Any, Dict, List, Optional, Tuple, Callable
import weakref

from .memory_monitor import MemoryLeakDetector, MemorySnapshot, MemoryStats

logger = logging.getLogger(__name__)


@dataclass
class StreamingMetrics:
    """Streaming analysis performance metrics."""
    files_processed: int = 0
    incremental_updates: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    processing_time_ms: float = 0.0
    queue_depth: int = 0
    backpressure_events: int = 0
    memory_peak_mb: float = 0.0
    
    # Event-specific metrics
    file_change_events: int = 0
    debounce_delays_ms: List[float] = field(default_factory=list)
    analysis_latency_ms: List[float] = field(default_factory=list)
    throughput_files_per_second: float = 0.0


@dataclass 
class StreamingSessionStats:
    """Complete streaming session statistics."""
    session_id: str
    start_time: float
    end_time: Optional[float] = None
    total_files_watched: int = 0
    total_events_processed: int = 0
    average_latency_ms: float = 0.0
    peak_memory_usage_mb: float = 0.0
    error_count: int = 0
    warnings_count: int = 0
    cache_efficiency_percent: float = 0.0


class StreamingPerformanceMonitor:
    """
    Real-time performance monitoring for streaming analysis operations.
    
    Features:
    - Event-driven metrics collection
    - Memory usage tracking during streaming
    - Latency and throughput measurement
    - Backpressure and queue depth monitoring
    - Cache performance analysis
    - Session-based statistics aggregation
    """
    
    def __init__(self, 
                 max_metrics_history: int = 1000,
                 memory_sample_interval: float = 1.0):
        """
        Initialize streaming performance monitor.
        
        Args:
            max_metrics_history: Maximum metrics samples to retain (NASA Rule 7)
            memory_sample_interval: Memory sampling interval in seconds
        """
        assert 100 <= max_metrics_history <= 10000, "History must be 100-10000 samples"
        assert 0.1 <= memory_sample_interval <= 10.0, "Interval must be 0.1-10.0 seconds"
        
        self.max_metrics_history = max_metrics_history
        self.memory_sample_interval = memory_sample_interval
        
        # Thread-safe metrics storage
        self._lock = RLock()
        self.current_metrics = StreamingMetrics()
        self.metrics_history: deque = deque(maxlen=max_metrics_history)
        
        # Session management
        self.active_sessions: Dict[str, StreamingSessionStats] = {}
        self.completed_sessions: deque = deque(maxlen=100)  # Bounded history
        
        # Performance tracking
        self.event_timings: defaultdict = defaultdict(list)
        self.processing_times: deque = deque(maxlen=500)
        self.memory_samples: deque = deque(maxlen=1000)
        
        # Memory leak detector for streaming operations
        self.memory_detector = MemoryLeakDetector(window_size=100, sensitivity=1.2)
        
        # Event callbacks for real-time monitoring
        self.event_callbacks: List[Callable] = []
        
        logger.info(f"StreamingPerformanceMonitor initialized with {max_metrics_history} sample history")
    
    def start_session(self, session_id: str, watched_files: int = 0) -> None:
        """Start a new streaming analysis session."""
        with self._lock:
            session = StreamingSessionStats(
                session_id=session_id,
                start_time=time.time(),
                total_files_watched=watched_files
            )
            self.active_sessions[session_id] = session
            
            # Reset current metrics for new session
            self.current_metrics = StreamingMetrics()
            self.memory_detector.start_streaming_session()
            
            logger.info(f"Started streaming session {session_id} with {watched_files} watched files")
    
    def end_session(self, session_id: str) -> StreamingSessionStats:
        """End streaming session and return final stats."""
        with self._lock:
            if session_id not in self.active_sessions:
                logger.warning(f"Session {session_id} not found")
                return None
            
            session = self.active_sessions.pop(session_id)
            session.end_time = time.time()
            
            # Calculate final statistics
            session.total_events_processed = self.current_metrics.file_change_events
            if self.current_metrics.analysis_latency_ms:
                session.average_latency_ms = sum(self.current_metrics.analysis_latency_ms) / len(self.current_metrics.analysis_latency_ms)
            session.peak_memory_usage_mb = self.current_metrics.memory_peak_mb
            
            # Cache efficiency calculation
            total_cache_ops = self.current_metrics.cache_hits + self.current_metrics.cache_misses
            if total_cache_ops > 0:
                session.cache_efficiency_percent = (self.current_metrics.cache_hits / total_cache_ops) * 100
            
            self.completed_sessions.append(session)
            logger.info(f"Ended streaming session {session_id}")
            return session
    
    def record_file_event(self, event_type: str, file_path: str, processing_time_ms: float) -> None:
        """Record a file change event and processing time."""
        with self._lock:
            current_time = time.time()
            
            self.current_metrics.file_change_events += 1
            self.current_metrics.processing_time_ms += processing_time_ms
            self.current_metrics.analysis_latency_ms.append(processing_time_ms)
            
            # Keep latency list bounded (NASA Rule 7)
            if len(self.current_metrics.analysis_latency_ms) > 500:
                self.current_metrics.analysis_latency_ms = self.current_metrics.analysis_latency_ms[-400:]
            
            # Track event timing patterns
            self.event_timings[event_type].append((current_time, processing_time_ms))
            if len(self.event_timings[event_type]) > 100:
                self.event_timings[event_type] = self.event_timings[event_type][-80:]
            
            # Update throughput calculation
            self._update_throughput()
            
            # Notify callbacks
            self._notify_event_callbacks(event_type, file_path, processing_time_ms)
    
    def record_cache_operation(self, hit: bool, operation_type: str = "file_content") -> None:
        """Record cache hit or miss."""
        with self._lock:
            if hit:
                self.current_metrics.cache_hits += 1
            else:
                self.current_metrics.cache_misses += 1
    
    def record_memory_sample(self, memory_mb: float) -> None:
        """Record memory usage sample."""
        with self._lock:
            timestamp = time.time()
            
            # Update peak memory
            if memory_mb > self.current_metrics.memory_peak_mb:
                self.current_metrics.memory_peak_mb = memory_mb
            
            # Add to memory detector
            leak_detected = self.memory_detector.add_sample(memory_mb, timestamp)
            if leak_detected:
                logger.warning(f"Memory leak detected during streaming: {memory_mb:.1f}MB")
            
            # Store sample for analysis
            self.memory_samples.append((timestamp, memory_mb))
    
    def record_queue_metrics(self, queue_depth: int, backpressure: bool = False) -> None:
        """Record queue depth and backpressure events."""
        with self._lock:
            self.current_metrics.queue_depth = queue_depth
            if backpressure:
                self.current_metrics.backpressure_events += 1
    
    def record_debounce_delay(self, delay_ms: float) -> None:
        """Record debounce delay for file change events."""
        with self._lock:
            self.current_metrics.debounce_delays_ms.append(delay_ms)
            
            # Keep bounded (NASA Rule 7)
            if len(self.current_metrics.debounce_delays_ms) > 200:
                self.current_metrics.debounce_delays_ms = self.current_metrics.debounce_delays_ms[-150:]
    
    def get_current_metrics(self) -> StreamingMetrics:
        """Get current streaming metrics snapshot."""
        with self._lock:
            # Create deep copy to avoid race conditions
            metrics = StreamingMetrics()
            metrics.files_processed = self.current_metrics.files_processed
            metrics.incremental_updates = self.current_metrics.incremental_updates
            metrics.cache_hits = self.current_metrics.cache_hits
            metrics.cache_misses = self.current_metrics.cache_misses
            metrics.processing_time_ms = self.current_metrics.processing_time_ms
            metrics.queue_depth = self.current_metrics.queue_depth
            metrics.backpressure_events = self.current_metrics.backpressure_events
            metrics.memory_peak_mb = self.current_metrics.memory_peak_mb
            metrics.file_change_events = self.current_metrics.file_change_events
            metrics.debounce_delays_ms = self.current_metrics.debounce_delays_ms.copy()
            metrics.analysis_latency_ms = self.current_metrics.analysis_latency_ms.copy()
            metrics.throughput_files_per_second = self.current_metrics.throughput_files_per_second
            
            return metrics
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        with self._lock:
            metrics = self.get_current_metrics()
            streaming_memory = self.memory_detector.get_streaming_memory_stats()
            
            report = {
                "current_metrics": {
                    "files_processed": metrics.files_processed,
                    "events_processed": metrics.file_change_events,
                    "cache_hit_rate": self._calculate_cache_hit_rate(),
                    "average_latency_ms": self._calculate_average_latency(),
                    "throughput_fps": metrics.throughput_files_per_second,
                    "queue_depth": metrics.queue_depth,
                    "backpressure_events": metrics.backpressure_events
                },
                "memory_metrics": {
                    "peak_usage_mb": metrics.memory_peak_mb,
                    "current_usage_mb": streaming_memory.get("current_memory_mb", 0),
                    "session_growth_mb": streaming_memory.get("session_growth_mb", 0),
                    "leak_detected": False  # Will be enhanced with leak detector status
                },
                "timing_analysis": {
                    "average_debounce_ms": self._calculate_average_debounce(),
                    "p95_latency_ms": self._calculate_p95_latency(),
                    "min_latency_ms": min(metrics.analysis_latency_ms) if metrics.analysis_latency_ms else 0,
                    "max_latency_ms": max(metrics.analysis_latency_ms) if metrics.analysis_latency_ms else 0
                },
                "session_summary": {
                    "active_sessions": len(self.active_sessions),
                    "completed_sessions": len(self.completed_sessions),
                    "total_events_all_sessions": sum(s.total_events_processed for s in self.completed_sessions)
                }
            }
            
            return report
    
    def add_event_callback(self, callback: Callable[[str, str, float], None]) -> None:
        """Add callback for real-time event notifications."""
        self.event_callbacks.append(callback)
    
    def _update_throughput(self) -> None:
        """Update throughput calculation based on recent events."""
        if len(self.current_metrics.analysis_latency_ms) < 10:
            return
            
        # Calculate events per second over last 60 seconds
        current_time = time.time()
        recent_events = [(t, _) for event_list in self.event_timings.values() 
                        for t, _ in event_list if current_time - t <= 60.0]
        
        if recent_events:
            self.current_metrics.throughput_files_per_second = len(recent_events) / 60.0
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate percentage."""
        total_ops = self.current_metrics.cache_hits + self.current_metrics.cache_misses
        if total_ops == 0:
            return 0.0
        return (self.current_metrics.cache_hits / total_ops) * 100.0
    
    def _calculate_average_latency(self) -> float:
        """Calculate average analysis latency."""
        if not self.current_metrics.analysis_latency_ms:
            return 0.0
        return sum(self.current_metrics.analysis_latency_ms) / len(self.current_metrics.analysis_latency_ms)
    
    def _calculate_average_debounce(self) -> float:
        """Calculate average debounce delay."""
        if not self.current_metrics.debounce_delays_ms:
            return 0.0
        return sum(self.current_metrics.debounce_delays_ms) / len(self.current_metrics.debounce_delays_ms)
    
    def _calculate_p95_latency(self) -> float:
        """Calculate 95th percentile latency."""
        if not self.current_metrics.analysis_latency_ms:
            return 0.0
        sorted_latencies = sorted(self.current_metrics.analysis_latency_ms)
        p95_index = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[p95_index] if p95_index < len(sorted_latencies) else sorted_latencies[-1]
    
    def _notify_event_callbacks(self, event_type: str, file_path: str, processing_time_ms: float) -> None:
        """Notify registered callbacks of events."""
        for callback in self.event_callbacks:
            try:
                callback(event_type, file_path, processing_time_ms)
            except Exception as e:
                logger.warning(f"Event callback failed: {e}")


# Global streaming performance monitor instance
_global_streaming_monitor: Optional[StreamingPerformanceMonitor] = None
_monitor_lock = Lock()


def get_global_streaming_monitor() -> StreamingPerformanceMonitor:
    """Get or create global streaming performance monitor."""
    global _global_streaming_monitor
    with _monitor_lock:
        if _global_streaming_monitor is None:
            _global_streaming_monitor = StreamingPerformanceMonitor()
        return _global_streaming_monitor


def start_streaming_monitoring(session_id: str, watched_files: int = 0) -> None:
    """Start global streaming monitoring session."""
    monitor = get_global_streaming_monitor()
    monitor.start_session(session_id, watched_files)


def stop_streaming_monitoring(session_id: str) -> StreamingSessionStats:
    """Stop global streaming monitoring session."""
    monitor = get_global_streaming_monitor()
    return monitor.end_session(session_id)


def record_streaming_event(event_type: str, file_path: str, processing_time_ms: float) -> None:
    """Record streaming event in global monitor."""
    monitor = get_global_streaming_monitor()
    monitor.record_file_event(event_type, file_path, processing_time_ms)


def get_streaming_performance_report() -> Dict[str, Any]:
    """Get global streaming performance report."""
    monitor = get_global_streaming_monitor()
    return monitor.get_performance_report()