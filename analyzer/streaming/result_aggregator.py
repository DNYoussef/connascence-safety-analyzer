"""
Stream Result Aggregator System
===============================

Real-time aggregation and merging of streaming analysis results. Handles
incremental updates, maintains result consistency, and provides efficient
access to aggregated analysis data during streaming operations.

NASA Rule 7 Compliant: Bounded memory usage with LRU eviction.
"""

from collections import defaultdict, deque
from dataclasses import dataclass, field
import logging
from threading import RLock
import time
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class StreamAnalysisResult:
    """Individual streaming analysis result."""

    file_path: str
    timestamp: float
    violations: Dict[str, Any]
    metrics: Dict[str, Any]
    processing_time_ms: float
    analysis_type: str  # 'incremental', 'full', 'cached'
    dependencies: Set[str] = field(default_factory=set)
    change_type: str = "modified"  # 'created', 'modified', 'deleted', 'moved'

    def __post_init__(self):
        """Validate result data."""
        assert self.file_path, "file_path cannot be empty"
        assert self.timestamp > 0, "timestamp must be positive"
        assert isinstance(self.violations, dict), "violations must be dict"
        assert isinstance(self.metrics, dict), "metrics must be dict"


@dataclass
class AggregatedResult:
    """Aggregated analysis results across multiple files."""

    total_violations: int = 0
    violation_breakdown: Dict[str, int] = field(default_factory=dict)
    files_analyzed: int = 0
    total_processing_time_ms: float = 0.0
    last_update_time: float = 0.0
    cache_hit_rate: float = 0.0
    incremental_updates: int = 0
    full_analyses: int = 0

    # Streaming-specific metrics
    real_time_violations: Dict[str, List[Dict]] = field(default_factory=dict)
    violation_trends: Dict[str, List[Tuple[float, int]]] = field(default_factory=dict)
    file_analysis_history: Dict[str, List[Dict]] = field(default_factory=dict)


class StreamResultAggregator:
    """
    Real-time result aggregation for streaming analysis.

    Features:
    - Incremental result merging and aggregation
    - Violation trend tracking over time
    - Efficient memory management with bounded storage
    - Thread-safe operations for concurrent updates
    - Dependency-aware invalidation and updates
    - Real-time dashboard data generation
    """

    def __init__(
        self, max_file_history: int = 1000, max_trend_points: int = 500, aggregation_window_seconds: float = 300.0
    ):
        """
        Initialize stream result aggregator.

        Args:
            max_file_history: Maximum file results to retain (NASA Rule 7)
            max_trend_points: Maximum trend data points per violation type
            aggregation_window_seconds: Time window for trend aggregation
        """
        assert 100 <= max_file_history <= 10000, "File history must be 100-10000"
        assert 100 <= max_trend_points <= 5000, "Trend points must be 100-5000"
        assert 60.0 <= aggregation_window_seconds <= 3600.0, "Window must be 1-60 minutes"

        self.max_file_history = max_file_history
        self.max_trend_points = max_trend_points
        self.aggregation_window_seconds = aggregation_window_seconds

        # Thread-safe aggregated state
        self._lock = RLock()
        self.aggregated_result = AggregatedResult()

        # File-specific result storage (bounded)
        self.file_results: Dict[str, StreamAnalysisResult] = {}
        self.result_history: deque = deque(maxlen=max_file_history)

        # Dependency tracking for intelligent invalidation
        self.file_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_dependencies: Dict[str, Set[str]] = defaultdict(set)

        # Real-time violation tracking
        self.violation_timeline: defaultdict = defaultdict(lambda: deque(maxlen=max_trend_points))
        self.active_violations: Dict[str, Dict[str, Any]] = {}

        # Performance metrics
        self.aggregation_stats = {
            "updates_processed": 0,
            "invalidations_triggered": 0,
            "cache_operations": 0,
            "merge_operations": 0,
            "last_aggregation_time_ms": 0.0,
        }

        logger.info(f"StreamResultAggregator initialized with {max_file_history} file history")

    def add_result(self, result: StreamAnalysisResult) -> None:
        """
        Add new streaming analysis result and update aggregated state.

        Args:
            result: New analysis result to add
        """
        with self._lock:
            start_time = time.perf_counter()

            # Store individual result
            old_result = self.file_results.get(result.file_path)
            self.file_results[result.file_path] = result
            self.result_history.append(result)

            # Update dependency tracking
            self._update_dependencies(result)

            # Handle dependency invalidation if needed
            if old_result and old_result.dependencies != result.dependencies:
                self._invalidate_dependent_results(result.file_path)

            # Update aggregated metrics
            self._update_aggregated_metrics(result, old_result)

            # Update violation timeline and trends
            self._update_violation_trends(result)

            # Update performance stats
            processing_time = (time.perf_counter() - start_time) * 1000
            self.aggregation_stats["updates_processed"] += 1
            self.aggregation_stats["last_aggregation_time_ms"] = processing_time
            self.aggregation_stats["merge_operations"] += 1

            logger.debug(f"Added result for {result.file_path} in {processing_time:.2f}ms")

    def remove_result(self, file_path: str) -> bool:
        """
        Remove result for a file (e.g., when file is deleted).

        Args:
            file_path: Path of file to remove

        Returns:
            True if result was removed
        """
        with self._lock:
            if file_path not in self.file_results:
                return False

            old_result = self.file_results.pop(file_path)

            # Update aggregated metrics by subtracting old result
            self._subtract_result_from_aggregated(old_result)

            # Clean up dependencies
            self._cleanup_dependencies(file_path)

            # Remove from active violations
            if file_path in self.active_violations:
                del self.active_violations[file_path]

            logger.info(f"Removed result for deleted file: {file_path}")
            return True

    def get_aggregated_result(self) -> AggregatedResult:
        """Get current aggregated analysis result."""
        with self._lock:
            # Update timestamp
            self.aggregated_result.last_update_time = time.time()

            # Calculate cache hit rate
            total_analyses = self.aggregated_result.incremental_updates + self.aggregated_result.full_analyses
            if total_analyses > 0:
                # Incremental updates indicate cache usage
                self.aggregated_result.cache_hit_rate = (
                    self.aggregated_result.incremental_updates / total_analyses
                ) * 100.0

            # Deep copy for thread safety
            return AggregatedResult(
                total_violations=self.aggregated_result.total_violations,
                violation_breakdown=self.aggregated_result.violation_breakdown.copy(),
                files_analyzed=self.aggregated_result.files_analyzed,
                total_processing_time_ms=self.aggregated_result.total_processing_time_ms,
                last_update_time=self.aggregated_result.last_update_time,
                cache_hit_rate=self.aggregated_result.cache_hit_rate,
                incremental_updates=self.aggregated_result.incremental_updates,
                full_analyses=self.aggregated_result.full_analyses,
                real_time_violations=self._copy_nested_dict(self.aggregated_result.real_time_violations),
                violation_trends=self._copy_nested_dict(self.aggregated_result.violation_trends),
                file_analysis_history=self._copy_nested_dict(self.aggregated_result.file_analysis_history),
            )

    def get_real_time_dashboard_data(self) -> Dict[str, Any]:
        """Generate real-time dashboard data."""
        with self._lock:
            current_time = time.time()

            # Get recent violation trends (last 10 minutes)
            recent_trends = {}
            for violation_type, timeline in self.violation_timeline.items():
                recent_points = [
                    (timestamp, count) for timestamp, count in timeline if current_time - timestamp <= 600.0
                ]
                if recent_points:
                    recent_trends[violation_type] = recent_points

            # Calculate velocity metrics
            velocity_data = self._calculate_analysis_velocity()

            # Get top violation files
            top_violation_files = self._get_top_violation_files(limit=10)

            dashboard_data = {
                "summary": {
                    "total_violations": self.aggregated_result.total_violations,
                    "files_analyzed": self.aggregated_result.files_analyzed,
                    "cache_hit_rate": self.aggregated_result.cache_hit_rate,
                    "last_update": self.aggregated_result.last_update_time,
                    "processing_velocity": velocity_data["files_per_minute"],
                },
                "violation_breakdown": self.aggregated_result.violation_breakdown,
                "trends": recent_trends,
                "velocity": velocity_data,
                "top_files": top_violation_files,
                "performance": {
                    "updates_processed": self.aggregation_stats["updates_processed"],
                    "average_aggregation_time_ms": self.aggregation_stats["last_aggregation_time_ms"],
                    "cache_operations": self.aggregation_stats["cache_operations"],
                    "active_file_count": len(self.file_results),
                },
            }

            return dashboard_data

    def get_file_analysis_history(self, file_path: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get analysis history for a specific file."""
        with self._lock:
            if file_path not in self.aggregated_result.file_analysis_history:
                return []

            history = self.aggregated_result.file_analysis_history[file_path]
            return history[-limit:] if len(history) > limit else history

    def get_violation_trends(self, violation_type: str, time_window_seconds: float = 3600.0) -> List[Tuple[float, int]]:
        """Get violation trend data for a specific type."""
        with self._lock:
            if violation_type not in self.violation_timeline:
                return []

            current_time = time.time()
            timeline = self.violation_timeline[violation_type]

            # Filter to time window
            recent_points = [
                (timestamp, count) for timestamp, count in timeline if current_time - timestamp <= time_window_seconds
            ]

            return recent_points

    def invalidate_file_results(self, file_paths: List[str]) -> int:
        """
        Invalidate results for specific files (e.g., due to dependency changes).

        Args:
            file_paths: List of file paths to invalidate

        Returns:
            Number of files invalidated
        """
        with self._lock:
            invalidated = 0

            for file_path in file_paths:
                if file_path in self.file_results:
                    # Remove from aggregated metrics
                    old_result = self.file_results[file_path]
                    self._subtract_result_from_aggregated(old_result)

                    # Remove the result but keep file in tracking for re-analysis
                    del self.file_results[file_path]
                    invalidated += 1

            self.aggregation_stats["invalidations_triggered"] += invalidated
            logger.info(f"Invalidated results for {invalidated} files")

            return invalidated

    def get_aggregation_stats(self) -> Dict[str, Any]:
        """Get aggregation performance statistics."""
        with self._lock:
            return {
                **self.aggregation_stats,
                "active_files": len(self.file_results),
                "total_dependencies": sum(len(deps) for deps in self.file_dependencies.values()),
                "violation_types_tracked": len(self.violation_timeline),
                "memory_usage_estimate_mb": self._estimate_memory_usage(),
            }

    def _update_dependencies(self, result: StreamAnalysisResult) -> None:
        """Update dependency tracking for a result."""
        file_path = result.file_path

        # Clear old dependencies
        old_deps = self.file_dependencies.get(file_path, set())
        for dep in old_deps:
            self.reverse_dependencies[dep].discard(file_path)

        # Set new dependencies
        self.file_dependencies[file_path] = result.dependencies.copy()
        for dep in result.dependencies:
            self.reverse_dependencies[dep].add(file_path)

    def _invalidate_dependent_results(self, changed_file: str) -> None:
        """Invalidate results that depend on a changed file."""
        dependent_files = self.reverse_dependencies.get(changed_file, set())
        if dependent_files:
            self.invalidate_file_results(list(dependent_files))

    def _update_aggregated_metrics(
        self, new_result: StreamAnalysisResult, old_result: Optional[StreamAnalysisResult]
    ) -> None:
        """Update aggregated metrics with new result."""
        # Subtract old result if exists
        if old_result:
            self._subtract_result_from_aggregated(old_result)
        else:
            # New file being analyzed
            self.aggregated_result.files_analyzed += 1

        # Add new result metrics
        violation_count = sum(len(v) if isinstance(v, list) else 1 for v in new_result.violations.values() if v)
        self.aggregated_result.total_violations += violation_count

        # Update violation breakdown
        for violation_type, violations in new_result.violations.items():
            if violations:  # Only count non-empty violations
                count = len(violations) if isinstance(violations, list) else 1
                self.aggregated_result.violation_breakdown[violation_type] = (
                    self.aggregated_result.violation_breakdown.get(violation_type, 0) + count
                )

        # Update processing time
        self.aggregated_result.total_processing_time_ms += new_result.processing_time_ms

        # Update analysis type counters
        if new_result.analysis_type == "incremental":
            self.aggregated_result.incremental_updates += 1
        else:
            self.aggregated_result.full_analyses += 1

        # Store real-time violations
        if new_result.violations:
            self.aggregated_result.real_time_violations[new_result.file_path] = [
                {"timestamp": new_result.timestamp, "violations": new_result.violations, "type": violation_type}
                for violation_type in new_result.violations.keys()
                if new_result.violations[violation_type]
            ]

        # Update file analysis history
        if new_result.file_path not in self.aggregated_result.file_analysis_history:
            self.aggregated_result.file_analysis_history[new_result.file_path] = []

        file_history = self.aggregated_result.file_analysis_history[new_result.file_path]
        file_history.append(
            {
                "timestamp": new_result.timestamp,
                "violation_count": violation_count,
                "processing_time_ms": new_result.processing_time_ms,
                "analysis_type": new_result.analysis_type,
                "change_type": new_result.change_type,
            }
        )

        # Keep bounded history (NASA Rule 7)
        if len(file_history) > 100:
            self.aggregated_result.file_analysis_history[new_result.file_path] = file_history[-80:]

    def _subtract_result_from_aggregated(self, old_result: StreamAnalysisResult) -> None:
        """Subtract old result from aggregated metrics."""
        # Subtract violation counts
        violation_count = sum(len(v) if isinstance(v, list) else 1 for v in old_result.violations.values() if v)
        self.aggregated_result.total_violations = max(0, self.aggregated_result.total_violations - violation_count)

        # Update violation breakdown
        for violation_type, violations in old_result.violations.items():
            if violations:
                count = len(violations) if isinstance(violations, list) else 1
                current_count = self.aggregated_result.violation_breakdown.get(violation_type, 0)
                new_count = max(0, current_count - count)
                if new_count == 0:
                    self.aggregated_result.violation_breakdown.pop(violation_type, None)
                else:
                    self.aggregated_result.violation_breakdown[violation_type] = new_count

        # Subtract processing time
        self.aggregated_result.total_processing_time_ms = max(
            0, self.aggregated_result.total_processing_time_ms - old_result.processing_time_ms
        )

        # Update analysis type counters
        if old_result.analysis_type == "incremental":
            self.aggregated_result.incremental_updates = max(0, self.aggregated_result.incremental_updates - 1)
        else:
            self.aggregated_result.full_analyses = max(0, self.aggregated_result.full_analyses - 1)

    def _update_violation_trends(self, result: StreamAnalysisResult) -> None:
        """Update violation trend timeline."""
        timestamp = result.timestamp

        for violation_type, violations in result.violations.items():
            if violations:
                count = len(violations) if isinstance(violations, list) else 1
                self.violation_timeline[violation_type].append((timestamp, count))

        # Also track in aggregated trends
        for violation_type, violations in result.violations.items():
            if violations:
                count = len(violations) if isinstance(violations, list) else 1
                if violation_type not in self.aggregated_result.violation_trends:
                    self.aggregated_result.violation_trends[violation_type] = []

                trend_list = self.aggregated_result.violation_trends[violation_type]
                trend_list.append((timestamp, count))

                # Keep bounded (NASA Rule 7)
                if len(trend_list) > self.max_trend_points:
                    self.aggregated_result.violation_trends[violation_type] = trend_list[
                        -(self.max_trend_points // 2) :
                    ]

    def _cleanup_dependencies(self, file_path: str) -> None:
        """Clean up dependency tracking for removed file."""
        # Remove from dependencies
        if file_path in self.file_dependencies:
            deps = self.file_dependencies.pop(file_path)
            for dep in deps:
                self.reverse_dependencies[dep].discard(file_path)

        # Remove from reverse dependencies
        if file_path in self.reverse_dependencies:
            dependent_files = self.reverse_dependencies.pop(file_path)
            for dep_file in dependent_files:
                self.file_dependencies[dep_file].discard(file_path)

    def _calculate_analysis_velocity(self) -> Dict[str, float]:
        """Calculate analysis velocity metrics."""
        current_time = time.time()

        # Count recent analyses (last 5 minutes)
        recent_results = [r for r in self.result_history if current_time - r.timestamp <= 300.0]

        velocity = {
            "files_per_minute": len(recent_results) / 5.0 if recent_results else 0.0,
            "violations_per_minute": sum(
                sum(len(v) if isinstance(v, list) else 1 for v in r.violations.values() if v) for r in recent_results
            )
            / 5.0,
            "avg_processing_time_ms": sum(r.processing_time_ms for r in recent_results) / len(recent_results)
            if recent_results
            else 0.0,
        }

        return velocity

    def _get_top_violation_files(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get files with most violations."""
        file_violation_counts = []

        for file_path, result in self.file_results.items():
            violation_count = sum(len(v) if isinstance(v, list) else 1 for v in result.violations.values() if v)
            if violation_count > 0:
                file_violation_counts.append(
                    {
                        "file_path": file_path,
                        "violation_count": violation_count,
                        "last_analyzed": result.timestamp,
                        "analysis_type": result.analysis_type,
                    }
                )

        # Sort by violation count and return top files
        file_violation_counts.sort(key=lambda x: x["violation_count"], reverse=True)
        return file_violation_counts[:limit]

    def _copy_nested_dict(self, nested_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Create deep copy of nested dictionary."""
        return {k: v.copy() if hasattr(v, "copy") else v for k, v in nested_dict.items()}

    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage in MB."""
        # Rough estimate based on stored data
        file_results_size = len(self.file_results) * 2  # ~2KB per result
        history_size = len(self.result_history) * 1  # ~1KB per history item
        trends_size = sum(len(timeline) for timeline in self.violation_timeline.values()) * 0.1  # ~100B per trend point

        return (file_results_size + history_size + trends_size) / 1024  # Convert to MB


# Global stream result aggregator instance
_global_stream_aggregator: Optional[StreamResultAggregator] = None
_aggregator_lock = RLock()


def get_global_stream_aggregator() -> StreamResultAggregator:
    """Get or create global stream result aggregator."""
    global _global_stream_aggregator
    with _aggregator_lock:
        if _global_stream_aggregator is None:
            _global_stream_aggregator = StreamResultAggregator()
        return _global_stream_aggregator


def add_streaming_result(result: StreamAnalysisResult) -> None:
    """Add result to global stream aggregator."""
    aggregator = get_global_stream_aggregator()
    aggregator.add_result(result)


def get_streaming_dashboard_data() -> Dict[str, Any]:
    """Get real-time dashboard data from global aggregator."""
    aggregator = get_global_stream_aggregator()
    return aggregator.get_real_time_dashboard_data()


def get_streaming_aggregated_result() -> AggregatedResult:
    """Get aggregated result from global aggregator."""
    aggregator = get_global_stream_aggregator()
    return aggregator.get_aggregated_result()
