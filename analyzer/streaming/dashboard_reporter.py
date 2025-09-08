"""
Real-time Dashboard Reporter
============================

Generates real-time reporting data for streaming analysis dashboards.
Provides structured data for visualization of violations, performance metrics,
and system health during continuous analysis operations.

NASA Rule 7 Compliant: Bounded data structures with automatic cleanup.
"""

import json
import time
import logging
from collections import deque, defaultdict
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple, Union
from threading import RLock

from .result_aggregator import get_global_stream_aggregator, AggregatedResult
from ..optimization.streaming_performance_monitor import get_global_streaming_monitor

logger = logging.getLogger(__name__)


@dataclass
class DashboardMetrics:
    """Real-time dashboard metrics."""
    timestamp: float
    total_violations: int
    files_analyzed: int
    analysis_velocity: float  # files per minute
    cache_hit_rate: float
    memory_usage_mb: float
    processing_latency_ms: float
    active_streams: int
    queue_depth: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass  
class ViolationTrend:
    """Violation trend data point."""
    timestamp: float
    violation_type: str
    count: int
    cumulative_count: int
    files_affected: int


@dataclass
class SystemHealthMetrics:
    """System health and performance metrics."""
    cpu_usage_percent: float
    memory_usage_mb: float
    disk_io_operations: int
    network_connections: int
    gc_collections: int
    active_threads: int
    
    # Analysis-specific health
    analysis_errors: int
    cache_errors: int
    stream_disconnections: int
    backpressure_events: int


class DashboardReporter:
    """
    Real-time dashboard data generation for streaming analysis.
    
    Features:
    - Live metrics aggregation and reporting
    - Violation trend tracking and forecasting
    - System health monitoring integration
    - Performance bottleneck identification
    - Historical data retention with efficient storage
    - WebSocket-ready data streaming format
    """
    
    def __init__(self, 
                 metrics_retention_minutes: int = 60,
                 trend_sampling_interval_seconds: float = 5.0,
                 health_check_interval_seconds: float = 10.0):
        """
        Initialize dashboard reporter.
        
        Args:
            metrics_retention_minutes: How long to retain metrics (NASA Rule 7)
            trend_sampling_interval_seconds: Interval for trend data sampling
            health_check_interval_seconds: System health check interval
        """
        assert 5 <= metrics_retention_minutes <= 1440, "Retention must be 5min-24hrs"
        assert 1.0 <= trend_sampling_interval_seconds <= 60.0, "Interval must be 1-60s"
        assert 5.0 <= health_check_interval_seconds <= 300.0, "Health interval must be 5s-5min"
        
        self.metrics_retention_minutes = metrics_retention_minutes
        self.trend_sampling_interval = trend_sampling_interval_seconds
        self.health_check_interval = health_check_interval_seconds
        
        # Thread-safe data storage
        self._lock = RLock()
        
        # Historical metrics (bounded retention)
        max_metrics = int((metrics_retention_minutes * 60) / self.trend_sampling_interval)
        self.metrics_history: deque = deque(maxlen=max_metrics)
        
        # Violation trends by type
        self.violation_trends: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=max_metrics)
        )
        
        # System health history
        self.health_history: deque = deque(maxlen=int(metrics_retention_minutes * 6))  # Every 10s
        
        # Real-time aggregation state
        self.current_dashboard_state = {
            "last_update": 0.0,
            "active_sessions": 0,
            "total_files_watching": 0,
            "alerts": [],
            "system_status": "healthy"
        }
        
        # Performance tracking
        self.report_generation_times: deque = deque(maxlen=100)
        self.dashboard_requests_count = 0
        
        logger.info(f"DashboardReporter initialized with {metrics_retention_minutes}min retention")
    
    def generate_real_time_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive real-time dashboard report.
        
        Returns:
            Complete dashboard data structure
        """
        with self._lock:
            start_time = time.perf_counter()
            
            # Get current aggregated data
            aggregator = get_global_stream_aggregator()
            streaming_monitor = get_global_streaming_monitor()
            
            aggregated_result = aggregator.get_aggregated_result()
            performance_report = streaming_monitor.get_performance_report()
            
            # Generate dashboard sections
            dashboard_data = {
                "metadata": self._generate_metadata(),
                "summary": self._generate_summary(aggregated_result, performance_report),
                "violations": self._generate_violations_data(aggregated_result),
                "performance": self._generate_performance_data(performance_report),
                "trends": self._generate_trends_data(),
                "system_health": self._generate_system_health(),
                "files": self._generate_files_data(aggregated_result),
                "alerts": self._generate_alerts(aggregated_result, performance_report)
            }
            
            # Update current state
            self.current_dashboard_state["last_update"] = time.time()
            self.dashboard_requests_count += 1
            
            # Track report generation performance
            generation_time = (time.perf_counter() - start_time) * 1000
            self.report_generation_times.append(generation_time)
            
            logger.debug(f"Generated dashboard report in {generation_time:.2f}ms")
            
            return dashboard_data
    
    def add_metrics_sample(self, 
                          violations: int,
                          files_analyzed: int,
                          performance_data: Dict[str, Any]) -> None:
        """Add new metrics sample to history."""
        with self._lock:
            timestamp = time.time()
            
            metrics = DashboardMetrics(
                timestamp=timestamp,
                total_violations=violations,
                files_analyzed=files_analyzed,
                analysis_velocity=performance_data.get("files_per_minute", 0.0),
                cache_hit_rate=performance_data.get("cache_hit_rate", 0.0),
                memory_usage_mb=performance_data.get("memory_usage_mb", 0.0),
                processing_latency_ms=performance_data.get("average_latency_ms", 0.0),
                active_streams=performance_data.get("active_streams", 0),
                queue_depth=performance_data.get("queue_depth", 0)
            )
            
            self.metrics_history.append(metrics)
    
    def add_violation_trend(self, 
                           violation_type: str,
                           count: int,
                           cumulative_count: int,
                           files_affected: int) -> None:
        """Add violation trend data point."""
        with self._lock:
            timestamp = time.time()
            
            trend = ViolationTrend(
                timestamp=timestamp,
                violation_type=violation_type,
                count=count,
                cumulative_count=cumulative_count,
                files_affected=files_affected
            )
            
            self.violation_trends[violation_type].append(trend)
    
    def get_metrics_history(self, 
                           time_window_minutes: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get metrics history for specified time window."""
        with self._lock:
            if not time_window_minutes:
                return [m.to_dict() for m in self.metrics_history]
            
            cutoff_time = time.time() - (time_window_minutes * 60)
            filtered_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
            
            return [m.to_dict() for m in filtered_metrics]
    
    def get_violation_trends(self, 
                           violation_type: Optional[str] = None,
                           time_window_minutes: int = 30) -> Dict[str, List[Dict[str, Any]]]:
        """Get violation trend data."""
        with self._lock:
            cutoff_time = time.time() - (time_window_minutes * 60)
            trends_data = {}
            
            violation_types = [violation_type] if violation_type else self.violation_trends.keys()
            
            for v_type in violation_types:
                if v_type in self.violation_trends:
                    filtered_trends = [
                        asdict(trend) for trend in self.violation_trends[v_type]
                        if trend.timestamp >= cutoff_time
                    ]
                    trends_data[v_type] = filtered_trends
            
            return trends_data
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for dashboard."""
        with self._lock:
            if not self.metrics_history:
                return {"status": "no_data"}
            
            recent_metrics = list(self.metrics_history)[-10:]  # Last 10 samples
            
            avg_velocity = sum(m.analysis_velocity for m in recent_metrics) / len(recent_metrics)
            avg_cache_hit_rate = sum(m.cache_hit_rate for m in recent_metrics) / len(recent_metrics)
            avg_latency = sum(m.processing_latency_ms for m in recent_metrics) / len(recent_metrics)
            
            return {
                "average_velocity_fpm": round(avg_velocity, 2),
                "average_cache_hit_rate": round(avg_cache_hit_rate, 1),
                "average_latency_ms": round(avg_latency, 2),
                "report_generation_time_ms": self.report_generation_times[-1] if self.report_generation_times else 0,
                "dashboard_requests": self.dashboard_requests_count
            }
    
    def _generate_metadata(self) -> Dict[str, Any]:
        """Generate dashboard metadata."""
        return {
            "generated_at": time.time(),
            "version": "1.0.0",
            "retention_minutes": self.metrics_retention_minutes,
            "sampling_interval_seconds": self.trend_sampling_interval,
            "data_points_available": len(self.metrics_history)
        }
    
    def _generate_summary(self, 
                         aggregated_result: AggregatedResult,
                         performance_report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary dashboard section."""
        current_metrics = performance_report.get("current_metrics", {})
        
        return {
            "total_violations": aggregated_result.total_violations,
            "files_analyzed": aggregated_result.files_analyzed,
            "cache_hit_rate": current_metrics.get("cache_hit_rate", 0.0),
            "analysis_velocity_fpm": current_metrics.get("throughput_fps", 0.0) * 60,
            "average_latency_ms": current_metrics.get("average_latency_ms", 0.0),
            "queue_depth": current_metrics.get("queue_depth", 0),
            "active_sessions": performance_report.get("session_summary", {}).get("active_sessions", 0),
            "last_analysis": aggregated_result.last_update_time,
            "system_status": self._calculate_system_status(performance_report)
        }
    
    def _generate_violations_data(self, aggregated_result: AggregatedResult) -> Dict[str, Any]:
        """Generate violations dashboard section."""
        violation_breakdown = aggregated_result.violation_breakdown
        
        # Calculate violation severity distribution  
        severity_distribution = self._calculate_violation_severity(violation_breakdown)
        
        # Get top violation types
        top_violations = sorted(
            violation_breakdown.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        return {
            "breakdown": violation_breakdown,
            "top_types": [{"type": vtype, "count": count} for vtype, count in top_violations],
            "severity_distribution": severity_distribution,
            "trends_available": list(self.violation_trends.keys()),
            "real_time_violations": len(aggregated_result.real_time_violations)
        }
    
    def _generate_performance_data(self, performance_report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance dashboard section."""
        current_metrics = performance_report.get("current_metrics", {})
        memory_metrics = performance_report.get("memory_metrics", {})
        timing_analysis = performance_report.get("timing_analysis", {})
        
        return {
            "current": {
                "throughput_fps": current_metrics.get("throughput_fps", 0.0),
                "cache_hit_rate": current_metrics.get("cache_hit_rate", 0.0),
                "average_latency_ms": current_metrics.get("average_latency_ms", 0.0),
                "queue_depth": current_metrics.get("queue_depth", 0),
                "backpressure_events": current_metrics.get("backpressure_events", 0)
            },
            "memory": {
                "peak_usage_mb": memory_metrics.get("peak_usage_mb", 0.0),
                "current_usage_mb": memory_metrics.get("current_usage_mb", 0.0),
                "session_growth_mb": memory_metrics.get("session_growth_mb", 0.0),
                "leak_detected": memory_metrics.get("leak_detected", False)
            },
            "timing": {
                "p95_latency_ms": timing_analysis.get("p95_latency_ms", 0.0),
                "min_latency_ms": timing_analysis.get("min_latency_ms", 0.0),
                "max_latency_ms": timing_analysis.get("max_latency_ms", 0.0),
                "average_debounce_ms": timing_analysis.get("average_debounce_ms", 0.0)
            }
        }
    
    def _generate_trends_data(self) -> Dict[str, Any]:
        """Generate trends dashboard section."""
        # Get recent trends (last 30 minutes)
        trends_data = self.get_violation_trends(time_window_minutes=30)
        
        # Calculate trend direction for each violation type
        trend_directions = {}
        for vtype, trends in trends_data.items():
            if len(trends) >= 5:  # Need minimum points for trend analysis
                recent_counts = [t["count"] for t in trends[-5:]]
                early_avg = sum(recent_counts[:2]) / 2 if len(recent_counts) >= 2 else 0
                late_avg = sum(recent_counts[-2:]) / 2 if len(recent_counts) >= 2 else 0
                
                if late_avg > early_avg * 1.1:
                    direction = "increasing"
                elif late_avg < early_avg * 0.9:
                    direction = "decreasing"
                else:
                    direction = "stable"
                
                trend_directions[vtype] = {
                    "direction": direction,
                    "change_percent": ((late_avg - early_avg) / max(early_avg, 1)) * 100
                }
        
        return {
            "violation_trends": trends_data,
            "trend_directions": trend_directions,
            "metrics_history_points": len(self.metrics_history),
            "oldest_data_age_minutes": self._get_oldest_data_age_minutes()
        }
    
    def _generate_system_health(self) -> Dict[str, Any]:
        """Generate system health dashboard section."""
        try:
            import psutil
            
            # Get current system metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk_io = psutil.disk_io_counters()
            
            health_metrics = {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_mb": memory.used / (1024 * 1024),
                "memory_available_mb": memory.available / (1024 * 1024),
                "disk_read_ops": disk_io.read_count if disk_io else 0,
                "disk_write_ops": disk_io.write_count if disk_io else 0,
                "system_load_1min": psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0.0
            }
            
            # Calculate system health score (0-100)
            health_score = self._calculate_health_score(health_metrics)
            
            return {
                "score": health_score,
                "status": "healthy" if health_score > 80 else "warning" if health_score > 60 else "critical",
                "metrics": health_metrics,
                "recommendations": self._generate_health_recommendations(health_metrics)
            }
            
        except ImportError:
            return {
                "score": 75,
                "status": "unknown",
                "metrics": {},
                "recommendations": ["Install psutil for detailed system monitoring"]
            }
    
    def _generate_files_data(self, aggregated_result: AggregatedResult) -> Dict[str, Any]:
        """Generate files dashboard section."""
        file_analysis_history = aggregated_result.file_analysis_history
        
        # Get files with most recent activity
        recent_files = []
        for file_path, history in file_analysis_history.items():
            if history:
                latest_analysis = max(history, key=lambda x: x["timestamp"])
                recent_files.append({
                    "file_path": file_path,
                    "last_analyzed": latest_analysis["timestamp"],
                    "violation_count": latest_analysis["violation_count"],
                    "analysis_type": latest_analysis["analysis_type"],
                    "processing_time_ms": latest_analysis["processing_time_ms"]
                })
        
        # Sort by most recent activity
        recent_files.sort(key=lambda x: x["last_analyzed"], reverse=True)
        
        return {
            "total_files_tracked": len(file_analysis_history),
            "recent_activity": recent_files[:20],  # Top 20 recent files
            "analysis_type_breakdown": self._calculate_analysis_type_breakdown(file_analysis_history)
        }
    
    def _generate_alerts(self, 
                        aggregated_result: AggregatedResult,
                        performance_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate system alerts for dashboard."""
        alerts = []
        current_time = time.time()
        
        # Memory usage alerts
        memory_metrics = performance_report.get("memory_metrics", {})
        if memory_metrics.get("leak_detected", False):
            alerts.append({
                "type": "memory_leak",
                "severity": "critical",
                "message": "Memory leak detected in streaming analysis",
                "timestamp": current_time,
                "action": "Consider restarting streaming session"
            })
        
        # High queue depth alert
        current_metrics = performance_report.get("current_metrics", {})
        queue_depth = current_metrics.get("queue_depth", 0)
        if queue_depth > 100:
            alerts.append({
                "type": "high_queue_depth", 
                "severity": "warning",
                "message": f"High queue depth detected: {queue_depth} items",
                "timestamp": current_time,
                "action": "Check processing performance and consider scaling"
            })
        
        # Low cache hit rate alert
        cache_hit_rate = current_metrics.get("cache_hit_rate", 100.0)
        if cache_hit_rate < 50.0:
            alerts.append({
                "type": "low_cache_efficiency",
                "severity": "warning", 
                "message": f"Low cache hit rate: {cache_hit_rate:.1f}%",
                "timestamp": current_time,
                "action": "Review caching strategy and file change patterns"
            })
        
        # High latency alert
        avg_latency = current_metrics.get("average_latency_ms", 0.0)
        if avg_latency > 5000:  # 5 seconds
            alerts.append({
                "type": "high_latency",
                "severity": "warning",
                "message": f"High processing latency: {avg_latency:.0f}ms",
                "timestamp": current_time,
                "action": "Check system resources and optimize analysis pipeline"
            })
        
        return alerts
    
    def _calculate_system_status(self, performance_report: Dict[str, Any]) -> str:
        """Calculate overall system status."""
        memory_metrics = performance_report.get("memory_metrics", {})
        current_metrics = performance_report.get("current_metrics", {})
        
        # Check for critical issues
        if memory_metrics.get("leak_detected", False):
            return "critical"
        
        # Check for warnings
        if (current_metrics.get("queue_depth", 0) > 100 or
            current_metrics.get("cache_hit_rate", 100) < 30 or
            current_metrics.get("average_latency_ms", 0) > 10000):
            return "warning"
        
        return "healthy"
    
    def _calculate_violation_severity(self, violation_breakdown: Dict[str, int]) -> Dict[str, int]:
        """Calculate violation severity distribution."""
        # Simple severity mapping based on violation type names
        severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        
        severity_mapping = {
            "timing": "high",
            "position": "medium", 
            "algorithm": "high",
            "god_object": "critical",
            "magic_literal": "low",
            "execution": "critical",
            "values": "medium"
        }
        
        for violation_type, count in violation_breakdown.items():
            severity = severity_mapping.get(violation_type, "medium")
            severity_counts[severity] += count
        
        return severity_counts
    
    def _calculate_analysis_type_breakdown(self, 
                                         file_analysis_history: Dict[str, List[Dict]]) -> Dict[str, int]:
        """Calculate breakdown of analysis types."""
        type_counts = {"incremental": 0, "full": 0, "cached": 0}
        
        for file_path, history in file_analysis_history.items():
            for analysis in history:
                analysis_type = analysis.get("analysis_type", "full")
                type_counts[analysis_type] = type_counts.get(analysis_type, 0) + 1
        
        return type_counts
    
    def _calculate_health_score(self, health_metrics: Dict[str, Any]) -> int:
        """Calculate system health score (0-100)."""
        score = 100
        
        # Penalize high CPU usage
        cpu_usage = health_metrics.get("cpu_usage_percent", 0)
        if cpu_usage > 80:
            score -= 20
        elif cpu_usage > 60:
            score -= 10
        
        # Penalize high memory usage
        memory_used = health_metrics.get("memory_usage_mb", 0)
        memory_available = health_metrics.get("memory_available_mb", 1000)
        memory_usage_percent = (memory_used / (memory_used + memory_available)) * 100
        
        if memory_usage_percent > 90:
            score -= 25
        elif memory_usage_percent > 80:
            score -= 15
        elif memory_usage_percent > 70:
            score -= 5
        
        return max(0, min(100, score))
    
    def _generate_health_recommendations(self, health_metrics: Dict[str, Any]) -> List[str]:
        """Generate health improvement recommendations."""
        recommendations = []
        
        cpu_usage = health_metrics.get("cpu_usage_percent", 0)
        if cpu_usage > 80:
            recommendations.append("High CPU usage detected - consider reducing analysis frequency")
        
        memory_used = health_metrics.get("memory_usage_mb", 0)
        memory_available = health_metrics.get("memory_available_mb", 1000)
        memory_usage_percent = (memory_used / (memory_used + memory_available)) * 100
        
        if memory_usage_percent > 85:
            recommendations.append("High memory usage - consider increasing cache eviction rate")
        
        return recommendations
    
    def _get_oldest_data_age_minutes(self) -> float:
        """Get age of oldest data in minutes."""
        if not self.metrics_history:
            return 0.0
        
        oldest_timestamp = self.metrics_history[0].timestamp
        return (time.time() - oldest_timestamp) / 60.0


# Global dashboard reporter instance
_global_dashboard_reporter: Optional[DashboardReporter] = None
_reporter_lock = RLock()


def get_global_dashboard_reporter() -> DashboardReporter:
    """Get or create global dashboard reporter."""
    global _global_dashboard_reporter
    with _reporter_lock:
        if _global_dashboard_reporter is None:
            _global_dashboard_reporter = DashboardReporter()
        return _global_dashboard_reporter


def generate_dashboard_report() -> Dict[str, Any]:
    """Generate dashboard report using global reporter."""
    reporter = get_global_dashboard_reporter()
    return reporter.generate_real_time_report()


def add_dashboard_metrics_sample(violations: int, 
                                files_analyzed: int,
                                performance_data: Dict[str, Any]) -> None:
    """Add metrics sample to global dashboard reporter."""
    reporter = get_global_dashboard_reporter()
    reporter.add_metrics_sample(violations, files_analyzed, performance_data)