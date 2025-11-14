"""
Test suite for MetricsCollector class.

Verifies metrics collection, quality scoring, trend analysis,
and performance tracking functionality.
"""

import pytest
from analyzer.architecture.metrics_collector import MetricsCollector, MetricsSnapshot


class TestMetricsCollector:
    """Test suite for MetricsCollector."""

    @pytest.fixture
    def collector(self):
        """Create MetricsCollector instance."""
        return MetricsCollector()

    @pytest.fixture
    def sample_violations(self):
        """Sample violations for testing."""
        return {
            "connascence": [
                {"severity": "critical", "type": "CoE", "weight": 1.5},
                {"severity": "high", "type": "CoT", "weight": 1.0},
                {"severity": "medium", "type": "CoN", "weight": 1.0},
            ],
            "duplication": [
                {"similarity_score": 0.85, "functions": ["func1", "func2", "func3"]},
                {"similarity_score": 0.65, "functions": ["func4", "func5"]},
            ],
            "nasa": [
                {"severity": "high", "context": {"nasa_rule": "Rule4"}},
                {"severity": "medium", "context": {"nasa_rule": "Rule5"}},
            ]
        }

    def test_initialization(self, collector):
        """Test MetricsCollector initialization."""
        assert collector is not None
        assert collector.config is not None
        assert len(collector.metrics_history) == 0
        assert collector.analysis_count == 0

    def test_collect_violation_metrics(self, collector, sample_violations):
        """Test violation metrics collection."""
        metrics = collector.collect_violation_metrics(sample_violations)

        # Verify all required fields present
        assert "total_violations" in metrics
        assert "critical_count" in metrics
        assert "high_count" in metrics
        assert "medium_count" in metrics
        assert "low_count" in metrics
        assert "connascence_index" in metrics
        assert "nasa_compliance_score" in metrics
        assert "duplication_score" in metrics
        assert "overall_quality_score" in metrics

        # Verify counts
        assert metrics["total_violations"] > 0
        assert metrics["critical_count"] >= 1
        assert metrics["high_count"] >= 1

        # Verify scores in valid range
        assert 0.0 <= metrics["nasa_compliance_score"] <= 1.0
        assert 0.0 <= metrics["duplication_score"] <= 1.0
        assert 0.0 <= metrics["overall_quality_score"] <= 1.0

    def test_quality_score_calculation(self, collector):
        """Test quality score calculation."""
        metrics = {
            "connascence_index": 30.0,
            "nasa_compliance_score": 0.9,
            "duplication_score": 0.95
        }

        quality_score = collector.calculate_quality_score(metrics)

        assert isinstance(quality_score, float)
        assert 0.0 <= quality_score <= 1.0

    def test_performance_tracking(self, collector):
        """Test performance tracking."""
        perf_metrics = collector.track_performance(analysis_time=1.5, file_count=50)

        assert "analysis_time_ms" in perf_metrics
        assert "files_analyzed" in perf_metrics
        assert "files_per_second" in perf_metrics
        assert "performance_rating" in perf_metrics

        assert perf_metrics["files_analyzed"] == 50
        assert perf_metrics["files_per_second"] > 0
        assert perf_metrics["performance_rating"] in ["excellent", "good", "acceptable", "slow"]

    def test_snapshot_creation(self, collector, sample_violations):
        """Test metrics snapshot creation."""
        metrics = collector.collect_violation_metrics(sample_violations)
        snapshot = collector.create_snapshot(metrics)

        assert isinstance(snapshot, MetricsSnapshot)
        assert snapshot.timestamp is not None
        assert snapshot.total_violations > 0
        assert 0.0 <= snapshot.overall_quality_score <= 1.0

        # Verify snapshot added to history
        assert len(collector.metrics_history) == 1

    def test_trend_analysis_no_data(self, collector):
        """Test trend analysis with no data."""
        trends = collector.get_trend_analysis()

        assert trends["trend"] == "no_data"
        assert trends["direction"] == "unknown"

    def test_trend_analysis_with_data(self, collector, sample_violations):
        """Test trend analysis with multiple snapshots."""
        # Create multiple snapshots with improving quality
        for i in range(5):
            violations = sample_violations.copy()
            # Reduce violations over time to show improvement
            violations["connascence"] = violations["connascence"][:(3-i//2)]

            metrics = collector.collect_violation_metrics(violations)
            collector.create_snapshot(metrics)

        trends = collector.get_trend_analysis()

        assert "trend" in trends
        assert "direction" in trends
        assert "quality_change" in trends
        assert "violation_change" in trends

    def test_baseline_setting(self, collector, sample_violations):
        """Test baseline metrics setting."""
        metrics = collector.collect_violation_metrics(sample_violations)
        collector.set_baseline(metrics)

        assert collector.baseline_metrics is not None
        assert isinstance(collector.baseline_metrics, MetricsSnapshot)

    def test_baseline_comparison(self, collector, sample_violations):
        """Test baseline comparison."""
        # Set baseline
        metrics1 = collector.collect_violation_metrics(sample_violations)
        collector.set_baseline(metrics1)

        # Create improved snapshot
        improved_violations = sample_violations.copy()
        improved_violations["connascence"] = improved_violations["connascence"][:1]  # Fewer violations

        metrics2 = collector.collect_violation_metrics(improved_violations)
        collector.create_snapshot(metrics2)

        comparison = collector.get_baseline_comparison()

        assert comparison is not None
        assert "quality_delta" in comparison
        assert "violation_delta" in comparison
        assert "status" in comparison

    def test_metrics_summary(self, collector, sample_violations):
        """Test comprehensive metrics summary."""
        metrics = collector.collect_violation_metrics(sample_violations)
        collector.create_snapshot(metrics)

        summary = collector.get_metrics_summary()

        assert "current_quality" in summary
        assert "total_violations" in summary
        assert "high_priority_violations" in summary
        assert "analysis_count" in summary

    def test_metrics_export(self, collector, sample_violations):
        """Test metrics history export."""
        # Create multiple snapshots
        for _ in range(3):
            metrics = collector.collect_violation_metrics(sample_violations)
            collector.create_snapshot(metrics)

        exported = collector.export_metrics_history()

        assert isinstance(exported, list)
        assert len(exported) == 3

        # Verify export structure
        for entry in exported:
            assert "timestamp" in entry
            assert "quality_score" in entry
            assert "violations" in entry

    def test_history_limit(self, collector, sample_violations):
        """Test history limit enforcement."""
        # Create more snapshots than history limit
        history_limit = collector.config["history_limit"]

        for _ in range(history_limit + 5):
            metrics = collector.collect_violation_metrics(sample_violations)
            collector.create_snapshot(metrics)

        # Verify history doesn't exceed limit
        assert len(collector.metrics_history) <= history_limit

    def test_dynamic_weights(self, collector):
        """Test dynamic weight calculation."""
        # Test with poor NASA score
        weights1 = collector._calculate_dynamic_weights(
            connascence_index=20.0,
            nasa_score=0.3,  # Poor
            duplication_score=0.9
        )

        # NASA weight should be boosted
        assert weights1["nasa_compliance"] > collector.quality_weights["nasa_compliance"]

        # Test with high duplication
        weights2 = collector._calculate_dynamic_weights(
            connascence_index=20.0,
            nasa_score=0.9,
            duplication_score=0.3  # Poor
        )

        # Duplication weight should be boosted
        assert weights2["duplication"] > collector.quality_weights["duplication"]

    def test_severity_normalization(self, collector):
        """Test severity level normalization."""
        assert collector._normalize_severity("critical") == "critical"
        assert collector._normalize_severity("error") == "high"
        assert collector._normalize_severity("warning") == "medium"
        assert collector._normalize_severity("notice") == "low"
        assert collector._normalize_severity("unknown") == "medium"

    def test_connascence_index_weighting(self, collector):
        """Test connascence index calculation with type weighting."""
        violations = [
            {"severity": "critical", "type": "CoE", "weight": 1.0},  # Execution - highest
            {"severity": "critical", "type": "CoL", "weight": 1.0},  # Literal - lowest
        ]

        index = collector._calculate_connascence_index(violations)

        # CoE should contribute more than CoL
        assert index > 0

    def test_nasa_compliance_with_critical_rules(self, collector):
        """Test NASA compliance scoring with critical rules."""
        # Test with critical rule violation
        violations_critical = [
            {"severity": "critical", "context": {"nasa_rule": "Rule1"}}  # Goto - highly critical
        ]

        score_critical = collector._calculate_nasa_compliance_score(violations_critical)

        # Test with less critical rule
        violations_low = [
            {"severity": "medium", "context": {"nasa_rule": "Rule10"}}
        ]

        score_low = collector._calculate_nasa_compliance_score(violations_low)

        # Critical rule should have lower score (higher penalty)
        assert score_critical < score_low

    def test_duplication_score_with_similarity(self, collector):
        """Test duplication score calculation with similarity weighting."""
        # High similarity cluster
        high_similarity = [
            {"similarity_score": 0.95, "functions": ["f1", "f2", "f3", "f4", "f5"]}
        ]

        score_high = collector._calculate_duplication_score(high_similarity)

        # Low similarity cluster
        low_similarity = [
            {"similarity_score": 0.5, "functions": ["f1", "f2"]}
        ]

        score_low = collector._calculate_duplication_score(low_similarity)

        # High similarity should have lower score (higher penalty)
        assert score_high < score_low

    def test_performance_rating_thresholds(self, collector):
        """Test performance rating thresholds."""
        # Excellent: >10 files/sec
        perf1 = collector.track_performance(analysis_time=1.0, file_count=15)
        assert perf1["performance_rating"] == "excellent"

        # Good: >5 files/sec
        perf2 = collector.track_performance(analysis_time=1.0, file_count=7)
        assert perf2["performance_rating"] == "good"

        # Acceptable: >2 files/sec
        perf3 = collector.track_performance(analysis_time=1.0, file_count=3)
        assert perf3["performance_rating"] == "acceptable"

        # Slow: <=2 files/sec
        perf4 = collector.track_performance(analysis_time=1.0, file_count=1)
        assert perf4["performance_rating"] == "slow"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
