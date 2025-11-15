# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
Metrics Collector - Centralized Metrics Collection and Analysis
================================================================

Extracted from UnifiedConnascenceAnalyzer's god object.
NASA Rule 4 Compliant: Functions under 60 lines.
Handles violation metrics collection, performance tracking, quality scoring,
and trend analysis.
"""

from dataclasses import dataclass, field
from datetime import datetime
import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MetricsSnapshot:
    """Snapshot of metrics at a specific point in time."""
    timestamp: str
    total_violations: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    connascence_index: float
    nasa_compliance_score: float
    duplication_score: float
    overall_quality_score: float
    calculation_time_ms: float
    files_analyzed: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """
    Centralized metrics collection and analysis for connascence violations.

    Responsibilities:
    - Violation metrics collection
    - Performance metrics tracking
    - Quality scoring calculation
    - Trend analysis

    NASA Rule 4 compliant: All methods under 60 lines.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize metrics collector.

        Args:
            config: Configuration dictionary with thresholds and weights
        """
        # NASA Rule 5: Input validation
        self.config = config or self._get_default_config()

        # Metrics history and tracking
        self.metrics_history: List[MetricsSnapshot] = []
        self.performance_history: List[Dict[str, float]] = []
        self.baseline_metrics: Optional[MetricsSnapshot] = None

        # Quality score components
        self.quality_weights = {
            "connascence": 0.4,
            "nasa_compliance": 0.3,
            "duplication": 0.3
        }

        # Performance tracking
        self.start_time: Optional[float] = None
        self.analysis_count = 0

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for metrics collection. NASA Rule 4 compliant."""
        return {
            "thresholds": {
                "critical_quality_score": 0.5,
                "acceptable_quality_score": 0.7,
                "excellent_quality_score": 0.9
            },
            "weights": {
                "severity": {
                    "critical": 10,
                    "high": 5,
                    "medium": 2,
                    "low": 1,
                    "info": 0.5
                },
                "connascence_types": {
                    "CoE": 2.0,  # Execution
                    "CoT": 1.8,  # Timing
                    "CoP": 1.6,  # Position
                    "CoI": 1.4,  # Identity
                    "CoA": 1.2,  # Algorithm
                    "CoN": 1.0,  # Name
                    "CoM": 0.8,  # Meaning
                    "CoL": 0.6   # Literal
                }
            },
            "history_limit": 20,  # Keep last 20 snapshots
            "trend_window": 5     # Use last 5 for trend analysis
        }

    def collect_violation_metrics(self, violations: Dict[str, List]) -> Dict[str, Any]:
        """
        Collect comprehensive metrics from violations.

        Args:
            violations: Dictionary with keys 'connascence', 'duplication', 'nasa'

        Returns:
            Dictionary containing all collected metrics

        NASA Rule 4 compliant: Under 60 lines.
        """
        # NASA Rule 5: Input validation
        assert violations is not None, "violations cannot be None"

        start_time = time.time()

        # Extract violations by type
        connascence_violations = violations.get("connascence", [])
        duplication_clusters = violations.get("duplication", [])
        nasa_violations = violations.get("nasa", [])

        # Count by severity
        severity_counts = self._count_violations_by_severity(
            connascence_violations + duplication_clusters + nasa_violations
        )

        # Calculate indexes and scores
        connascence_index = self._calculate_connascence_index(connascence_violations)
        nasa_score = self._calculate_nasa_compliance_score(nasa_violations)
        duplication_score = self._calculate_duplication_score(duplication_clusters)

        # Calculate overall quality
        overall_quality = self.calculate_quality_score({
            "connascence_index": connascence_index,
            "nasa_compliance_score": nasa_score,
            "duplication_score": duplication_score
        })

        # Build metrics result
        metrics = {
            "total_violations": severity_counts["total"],
            "critical_count": severity_counts["critical"],
            "high_count": severity_counts["high"],
            "medium_count": severity_counts["medium"],
            "low_count": severity_counts["low"],
            "info_count": severity_counts.get("info", 0),
            "connascence_index": connascence_index,
            "nasa_compliance_score": nasa_score,
            "duplication_score": duplication_score,
            "overall_quality_score": overall_quality,
            "collection_time_ms": round((time.time() - start_time) * 1000, 2),
            "timestamp": self._get_iso_timestamp()
        }

        return metrics

    def _count_violations_by_severity(self, violations: List[Dict]) -> Dict[str, int]:
        """Count violations by severity level. NASA Rule 4 compliant."""
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }

        for violation in violations:
            severity = self._normalize_severity(violation.get("severity", "medium"))
            if severity in severity_counts:
                severity_counts[severity] += 1

        # Add derived counts
        severity_counts["total"] = sum(severity_counts.values())
        severity_counts["high_priority"] = severity_counts["critical"] + severity_counts["high"]

        return severity_counts

    def _calculate_connascence_index(self, violations: List[Dict]) -> float:
        """
        Calculate weighted connascence index.

        NASA Rule 4 compliant: Under 60 lines.
        """
        if not violations:
            return 0.0

        weights = self.config["weights"]
        severity_weights = weights["severity"]
        type_weights = weights["connascence_types"]

        total_weighted_score = 0.0

        for violation in violations:
            severity = self._normalize_severity(violation.get("severity", "medium"))
            severity_weight = severity_weights.get(severity, 2)

            # Get connascence type weight
            connascence_type = violation.get("type", "CoN")
            type_weight = type_weights.get(connascence_type, 1.0)

            # Get violation-specific weight
            violation_weight = violation.get("weight", 1.0)

            total_weighted_score += severity_weight * type_weight * violation_weight

        return round(total_weighted_score, 2)

    def _calculate_nasa_compliance_score(self, nasa_violations: List[Dict]) -> float:
        """
        Calculate NASA compliance score (0-1, higher is better).

        NASA Rule 4 compliant: Under 60 lines.
        """
        if not nasa_violations:
            return 1.0

        # Rule weights based on criticality
        rule_weights = {
            "Rule1": 0.15,  # Goto - highly critical
            "Rule2": 0.12,  # Recursion - critical
            "Rule3": 0.12,  # Memory allocation - critical
            "Rule4": 0.10,  # Function length - important
            "Rule5": 0.08,  # Assertions - important
            "Rule6": 0.06,
            "Rule7": 0.06,
            "Rule8": 0.05,
            "Rule9": 0.05,
            "Rule10": 0.05
        }

        total_penalty = 0.0

        for violation in nasa_violations:
            # Extract NASA rule
            context = violation.get("context", {})
            nasa_rule = context.get("nasa_rule", "Rule10")

            # Base penalty from rule weight
            base_penalty = rule_weights.get(nasa_rule, 0.05)

            # Severity multiplier
            severity = self._normalize_severity(violation.get("severity", "medium"))
            severity_multipliers = {
                "critical": 2.0,
                "high": 1.5,
                "medium": 1.0,
                "low": 0.5,
                "info": 0.2
            }
            severity_multiplier = severity_multipliers.get(severity, 1.0)

            total_penalty += base_penalty * severity_multiplier

        score = max(0.0, 1.0 - total_penalty)
        return round(score, 3)

    def _calculate_duplication_score(self, duplication_clusters: List[Dict]) -> float:
        """
        Calculate duplication score (0-1, higher is better).

        NASA Rule 4 compliant: Under 60 lines.
        """
        if not duplication_clusters:
            return 1.0

        total_penalty = 0.0

        for cluster in duplication_clusters:
            # Base penalty per cluster
            base_penalty = 0.05

            # Similarity multiplier (higher similarity = higher penalty)
            similarity_score = cluster.get("similarity_score", 0.5)
            similarity_multiplier = similarity_score

            # Size multiplier (more duplicates = higher penalty)
            functions = cluster.get("functions", [])
            size_multiplier = min(len(functions) / 5.0, 2.0)  # Cap at 2x

            cluster_penalty = base_penalty * similarity_multiplier * size_multiplier
            total_penalty += cluster_penalty

        score = max(0.0, 1.0 - total_penalty)
        return round(score, 3)

    def calculate_quality_score(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate overall quality score from component metrics.

        Args:
            metrics: Dictionary with connascence_index, nasa_compliance_score,
                    duplication_score

        Returns:
            Overall quality score (0-1, higher is better)

        NASA Rule 4 compliant: Under 60 lines.
        """
        # NASA Rule 5: Input validation
        assert metrics is not None, "metrics cannot be None"

        connascence_index = metrics.get("connascence_index", 0.0)
        nasa_score = metrics.get("nasa_compliance_score", 1.0)
        duplication_score = metrics.get("duplication_score", 1.0)

        # Convert connascence index to score (0-1 range)
        # Lower index is better, so invert it
        connascence_score = max(0.0, 1.0 - (connascence_index * 0.01))

        # Apply dynamic weighting based on problem areas
        weights = self._calculate_dynamic_weights(
            connascence_index, nasa_score, duplication_score
        )

        # Calculate weighted average
        overall_score = (
            connascence_score * weights["connascence"]
            + nasa_score * weights["nasa_compliance"]
            + duplication_score * weights["duplication"]
        )

        return round(overall_score, 3)

    def _calculate_dynamic_weights(
        self, connascence_index: float, nasa_score: float, duplication_score: float
    ) -> Dict[str, float]:
        """
        Calculate dynamic weights based on current problem areas.

        NASA Rule 4 compliant: Under 60 lines.
        """
        weights = self.quality_weights.copy()

        # Boost weight for problem areas (scores < 0.5)
        if nasa_score < 0.5:
            weights["nasa_compliance"] += 0.1
            weights["connascence"] -= 0.05
            weights["duplication"] -= 0.05

        if duplication_score < 0.5:
            weights["duplication"] += 0.1
            weights["connascence"] -= 0.05
            weights["nasa_compliance"] -= 0.05

        if connascence_index > 50:  # High connascence
            weights["connascence"] += 0.1
            weights["nasa_compliance"] -= 0.05
            weights["duplication"] -= 0.05

        # Normalize to ensure sum = 1.0
        total = sum(weights.values())
        return {k: round(v / total, 3) for k, v in weights.items()}

    def track_performance(self, analysis_time: float, file_count: int) -> Dict[str, Any]:
        """
        Track performance metrics for an analysis run.

        Args:
            analysis_time: Analysis duration in seconds
            file_count: Number of files analyzed

        Returns:
            Performance metrics dictionary

        NASA Rule 4 compliant: Under 60 lines.
        """
        # NASA Rule 5: Input validation
        assert analysis_time >= 0, "analysis_time must be non-negative"
        assert file_count >= 0, "file_count must be non-negative"

        performance_metrics = {
            "analysis_time_ms": round(analysis_time * 1000, 2),
            "files_analyzed": file_count,
            "files_per_second": round(file_count / analysis_time, 2) if analysis_time > 0 else 0,
            "performance_rating": self._get_performance_rating(analysis_time, file_count),
            "timestamp": self._get_iso_timestamp()
        }

        # Record in history
        self.performance_history.append(performance_metrics)

        # Limit history size
        history_limit = self.config.get("history_limit", 20)
        if len(self.performance_history) > history_limit:
            self.performance_history.pop(0)

        self.analysis_count += 1

        return performance_metrics

    def _get_performance_rating(self, analysis_time: float, file_count: int) -> str:
        """Get performance rating based on analysis time. NASA Rule 4 compliant."""
        if file_count == 0:
            return "no_files"

        # Calculate files per second
        fps = file_count / analysis_time if analysis_time > 0 else 0

        # Rating thresholds
        if fps > 10:
            return "excellent"
        elif fps > 5:
            return "good"
        elif fps > 2:
            return "acceptable"
        else:
            return "slow"

    def get_trend_analysis(self) -> Dict[str, Any]:
        """
        Analyze metric trends over time.

        Returns:
            Trend analysis including direction, changes, and predictions

        NASA Rule 4 compliant: Under 60 lines.
        """
        if not self.metrics_history:
            return {
                "trend": "no_data",
                "direction": "unknown",
                "changes": {}
            }

        if len(self.metrics_history) < 2:
            return {
                "trend": "insufficient_data",
                "direction": "stable",
                "changes": {}
            }

        # Get trend window
        trend_window = self.config.get("trend_window", 5)
        recent_metrics = self.metrics_history[-trend_window:]

        # Calculate trends
        quality_trend = self._calculate_quality_trend(recent_metrics)
        violation_trend = self._calculate_violation_trend(recent_metrics)

        return {
            "trend": self._determine_overall_trend(quality_trend, violation_trend),
            "direction": quality_trend["direction"],
            "quality_change": quality_trend["change"],
            "violation_change": violation_trend["change"],
            "recent_snapshots": len(recent_metrics),
            "total_snapshots": len(self.metrics_history),
            "analysis": self._generate_trend_analysis(quality_trend, violation_trend)
        }

    def _calculate_quality_trend(self, snapshots: List[MetricsSnapshot]) -> Dict[str, Any]:
        """Calculate quality score trend. NASA Rule 4 compliant."""
        if len(snapshots) < 2:
            return {"direction": "stable", "change": 0.0}

        first_quality = snapshots[0].overall_quality_score
        last_quality = snapshots[-1].overall_quality_score
        change = last_quality - first_quality

        # Determine direction
        if change > 0.05:
            direction = "improving"
        elif change < -0.05:
            direction = "degrading"
        else:
            direction = "stable"

        return {
            "direction": direction,
            "change": round(change, 3),
            "first": round(first_quality, 3),
            "last": round(last_quality, 3)
        }

    def _calculate_violation_trend(self, snapshots: List[MetricsSnapshot]) -> Dict[str, Any]:
        """Calculate violation count trend. NASA Rule 4 compliant."""
        if len(snapshots) < 2:
            return {"direction": "stable", "change": 0}

        first_violations = snapshots[0].total_violations
        last_violations = snapshots[-1].total_violations
        change = last_violations - first_violations

        # Determine direction (increasing violations = degrading)
        if change > 5:
            direction = "degrading"
        elif change < -5:
            direction = "improving"
        else:
            direction = "stable"

        return {
            "direction": direction,
            "change": change,
            "first": first_violations,
            "last": last_violations
        }

    def _determine_overall_trend(
        self, quality_trend: Dict, violation_trend: Dict
    ) -> str:
        """Determine overall trend from component trends. NASA Rule 4 compliant."""
        # Quality improving AND violations decreasing = excellent
        if quality_trend["direction"] == "improving" and violation_trend["direction"] == "improving":
            return "excellent_progress"

        # Quality stable AND violations stable = stable
        if quality_trend["direction"] == "stable" and violation_trend["direction"] == "stable":
            return "stable"

        # Quality degrading OR violations increasing = concerning
        if quality_trend["direction"] == "degrading" or violation_trend["direction"] == "degrading":
            return "needs_attention"

        # Mixed signals
        return "mixed"

    def _generate_trend_analysis(
        self, quality_trend: Dict, violation_trend: Dict
    ) -> str:
        """Generate human-readable trend analysis. NASA Rule 4 compliant."""
        quality_dir = quality_trend["direction"]
        violation_dir = violation_trend["direction"]

        if quality_dir == "improving" and violation_dir == "improving":
            return "Code quality is improving with fewer violations"
        elif quality_dir == "degrading" and violation_dir == "degrading":
            return "Code quality is degrading with more violations"
        elif quality_dir == "stable" and violation_dir == "stable":
            return "Code quality remains stable"
        elif quality_dir == "improving":
            return "Quality scores improving despite violation changes"
        elif quality_dir == "degrading":
            return "Quality scores degrading, requires attention"
        else:
            return "Mixed trends observed, monitoring recommended"

    def create_snapshot(self, metrics: Dict[str, Any]) -> MetricsSnapshot:
        """
        Create a metrics snapshot for history tracking.

        Args:
            metrics: Metrics dictionary from collect_violation_metrics

        Returns:
            MetricsSnapshot object

        NASA Rule 4 compliant: Under 60 lines.
        """
        # NASA Rule 5: Input validation
        assert metrics is not None, "metrics cannot be None"

        snapshot = MetricsSnapshot(
            timestamp=metrics.get("timestamp", self._get_iso_timestamp()),
            total_violations=metrics.get("total_violations", 0),
            critical_count=metrics.get("critical_count", 0),
            high_count=metrics.get("high_count", 0),
            medium_count=metrics.get("medium_count", 0),
            low_count=metrics.get("low_count", 0),
            connascence_index=metrics.get("connascence_index", 0.0),
            nasa_compliance_score=metrics.get("nasa_compliance_score", 1.0),
            duplication_score=metrics.get("duplication_score", 1.0),
            overall_quality_score=metrics.get("overall_quality_score", 0.0),
            calculation_time_ms=metrics.get("collection_time_ms", 0.0),
            files_analyzed=metrics.get("files_analyzed", 0),
            metadata=metrics.get("metadata", {})
        )

        # Add to history
        self.metrics_history.append(snapshot)

        # Limit history size
        history_limit = self.config.get("history_limit", 20)
        if len(self.metrics_history) > history_limit:
            self.metrics_history.pop(0)

        return snapshot

    def set_baseline(self, metrics: Dict[str, Any]) -> None:
        """Set baseline metrics for comparison. NASA Rule 4 compliant."""
        assert metrics is not None, "metrics cannot be None"
        self.baseline_metrics = self.create_snapshot(metrics)
        logger.info(f"Baseline metrics established: quality={self.baseline_metrics.overall_quality_score}")

    def get_baseline_comparison(self) -> Optional[Dict[str, Any]]:
        """Get comparison with baseline metrics. NASA Rule 4 compliant."""
        if not self.baseline_metrics or not self.metrics_history:
            return None

        current = self.metrics_history[-1]

        return {
            "quality_delta": round(
                current.overall_quality_score - self.baseline_metrics.overall_quality_score, 3
            ),
            "violation_delta": current.total_violations - self.baseline_metrics.total_violations,
            "nasa_delta": round(
                current.nasa_compliance_score - self.baseline_metrics.nasa_compliance_score, 3
            ),
            "duplication_delta": round(
                current.duplication_score - self.baseline_metrics.duplication_score, 3
            ),
            "status": self._get_baseline_status(current)
        }

    def _get_baseline_status(self, current: MetricsSnapshot) -> str:
        """Determine baseline comparison status. NASA Rule 4 compliant."""
        if not self.baseline_metrics:
            return "no_baseline"

        quality_delta = current.overall_quality_score - self.baseline_metrics.overall_quality_score

        if quality_delta > 0.1:
            return "significantly_improved"
        elif quality_delta > 0.02:
            return "improved"
        elif quality_delta > -0.02:
            return "stable"
        elif quality_delta > -0.1:
            return "degraded"
        else:
            return "significantly_degraded"

    def _normalize_severity(self, severity: str) -> str:
        """Normalize severity levels. NASA Rule 4 compliant."""
        severity_mapping = {
            "critical": "critical",
            "high": "high",
            "medium": "medium",
            "low": "low",
            "info": "info",
            "error": "high",
            "warning": "medium",
            "notice": "low"
        }
        return severity_mapping.get(severity.lower(), "medium")

    def _get_iso_timestamp(self) -> str:
        """Get current timestamp in ISO format. NASA Rule 4 compliant."""
        return datetime.now().isoformat()

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary. NASA Rule 4 compliant."""
        if not self.metrics_history:
            return {"status": "no_data"}

        current = self.metrics_history[-1]
        trend = self.get_trend_analysis()
        baseline = self.get_baseline_comparison()

        return {
            "current_quality": current.overall_quality_score,
            "total_violations": current.total_violations,
            "high_priority_violations": current.critical_count + current.high_count,
            "trend": trend,
            "baseline_comparison": baseline,
            "analysis_count": self.analysis_count,
            "history_size": len(self.metrics_history)
        }

    def export_metrics_history(self) -> List[Dict[str, Any]]:
        """Export metrics history for reporting. NASA Rule 4 compliant."""
        return [
            {
                "timestamp": snapshot.timestamp,
                "quality_score": snapshot.overall_quality_score,
                "violations": snapshot.total_violations,
                "critical": snapshot.critical_count,
                "high": snapshot.high_count,
                "nasa_score": snapshot.nasa_compliance_score,
                "duplication_score": snapshot.duplication_score,
                "files_analyzed": snapshot.files_analyzed
            }
            for snapshot in self.metrics_history
        ]
