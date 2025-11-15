# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
Comprehensive Unit Tests for MetricsCollector
==============================================

Test coverage for all 23 metrics methods including:
- collect_violation_metrics() with dict/list violations
- Quality score calculation (weighted severity)
- Snapshot creation for trend analysis
- Severity normalization (Critical=4, High=2, etc.)
- NASA compliance scoring
- Duplication metrics

Target: 95%+ coverage for MetricsCollector
"""


import pytest

from analyzer.architecture.metrics_collector import MetricsCollector, MetricsSnapshot

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def default_collector():
    """Create MetricsCollector with default config."""
    return MetricsCollector()


@pytest.fixture
def custom_collector():
    """Create MetricsCollector with custom config."""
    config = {
        "thresholds": {
            "critical_quality_score": 0.6,
            "acceptable_quality_score": 0.8,
            "excellent_quality_score": 0.95
        },
        "weights": {
            "severity": {
                "critical": 20,
                "high": 10,
                "medium": 5,
                "low": 2,
                "info": 1
            },
            "connascence_types": {
                "CoE": 3.0,
                "CoT": 2.5,
                "CoP": 2.0,
                "CoI": 1.5,
                "CoA": 1.3,
                "CoN": 1.0,
                "CoM": 0.9,
                "CoL": 0.7
            }
        },
        "history_limit": 10,
        "trend_window": 3
    }
    return MetricsCollector(config)


@pytest.fixture
def sample_violations_dict():
    """Sample violations in dict format."""
    return {
        "connascence": [
            {
                "type": "CoE",
                "severity": "critical",
                "weight": 1.5,
                "file": "test.py",
                "line": 42
            },
            {
                "type": "CoP",
                "severity": "high",
                "weight": 1.0,
                "file": "test.py",
                "line": 100
            },
            {
                "type": "CoN",
                "severity": "medium",
                "weight": 1.0,
                "file": "test.py",
                "line": 200
            }
        ],
        "duplication": [
            {
                "similarity_score": 0.85,
                "functions": [
                    {"name": "func1", "file": "a.py"},
                    {"name": "func2", "file": "b.py"},
                    {"name": "func3", "file": "c.py"}
                ]
            },
            {
                "similarity_score": 0.65,
                "functions": [
                    {"name": "func4", "file": "d.py"},
                    {"name": "func5", "file": "e.py"}
                ]
            }
        ],
        "nasa": [
            {
                "severity": "high",
                "context": {"nasa_rule": "Rule1"},
                "file": "test.py",
                "line": 50
            },
            {
                "severity": "medium",
                "context": {"nasa_rule": "Rule4"},
                "file": "test.py",
                "line": 150
            }
        ]
    }


@pytest.fixture
def empty_violations():
    """Empty violations dictionary."""
    return {
        "connascence": [],
        "duplication": [],
        "nasa": []
    }


@pytest.fixture
def large_violations():
    """Large set of violations for stress testing."""
    return {
        "connascence": [
            {"type": "CoE", "severity": "critical", "weight": 1.0}
            for _ in range(50)
        ],
        "duplication": [
            {
                "similarity_score": 0.9,
                "functions": [{"name": f"func{i}", "file": f"file{i}.py"} for i in range(10)]
            }
            for _ in range(20)
        ],
        "nasa": [
            {"severity": "high", "context": {"nasa_rule": "Rule1"}}
            for _ in range(30)
        ]
    }


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

class TestMetricsCollectorInit:
    """Test MetricsCollector initialization."""

    def test_default_initialization(self, default_collector):
        """Test initialization with default config."""
        assert default_collector.config is not None
        assert default_collector.metrics_history == []
        assert default_collector.performance_history == []
        assert default_collector.baseline_metrics is None
        assert default_collector.analysis_count == 0

    def test_custom_initialization(self, custom_collector):
        """Test initialization with custom config."""
        assert custom_collector.config["thresholds"]["critical_quality_score"] == 0.6
        assert custom_collector.config["weights"]["severity"]["critical"] == 20
        assert custom_collector.config["history_limit"] == 10
        assert custom_collector.config["trend_window"] == 3

    def test_quality_weights_default(self, default_collector):
        """Test default quality weights."""
        weights = default_collector.quality_weights
        assert weights["connascence"] == 0.4
        assert weights["nasa_compliance"] == 0.3
        assert weights["duplication"] == 0.3
        assert sum(weights.values()) == pytest.approx(1.0)

    def test_none_config_uses_default(self):
        """Test that None config uses default."""
        collector = MetricsCollector(None)
        assert collector.config is not None
        assert "thresholds" in collector.config
        assert "weights" in collector.config


# ============================================================================
# VIOLATION METRICS COLLECTION TESTS
# ============================================================================

class TestCollectViolationMetrics:
    """Test collect_violation_metrics() method."""

    def test_collect_metrics_with_violations(self, default_collector, sample_violations_dict):
        """Test collecting metrics with sample violations."""
        metrics = default_collector.collect_violation_metrics(sample_violations_dict)

        assert "total_violations" in metrics
        assert metrics["total_violations"] == 5  # 3 connascence + 2 nasa
        assert "critical_count" in metrics
        assert "high_count" in metrics
        assert "medium_count" in metrics
        assert "low_count" in metrics
        assert "connascence_index" in metrics
        assert "nasa_compliance_score" in metrics
        assert "duplication_score" in metrics
        assert "overall_quality_score" in metrics
        assert "collection_time_ms" in metrics
        assert "timestamp" in metrics

    def test_collect_metrics_empty_violations(self, default_collector, empty_violations):
        """Test collecting metrics with no violations."""
        metrics = default_collector.collect_violation_metrics(empty_violations)

        assert metrics["total_violations"] == 0
        assert metrics["critical_count"] == 0
        assert metrics["high_count"] == 0
        assert metrics["connascence_index"] == 0.0
        assert metrics["nasa_compliance_score"] == 1.0  # Perfect compliance
        assert metrics["duplication_score"] == 1.0  # No duplication

    def test_collect_metrics_none_assertion(self, default_collector):
        """Test that None violations raises assertion."""
        with pytest.raises(AssertionError):
            default_collector.collect_violation_metrics(None)

    def test_collect_metrics_timing(self, default_collector, sample_violations_dict):
        """Test that collection time is recorded."""
        metrics = default_collector.collect_violation_metrics(sample_violations_dict)

        assert metrics["collection_time_ms"] >= 0
        assert isinstance(metrics["collection_time_ms"], float)

    def test_collect_metrics_large_dataset(self, default_collector, large_violations):
        """Test collecting metrics with large violation set."""
        metrics = default_collector.collect_violation_metrics(large_violations)

        assert metrics["total_violations"] == 80  # 50 + 30
        assert metrics["critical_count"] == 50
        assert metrics["high_count"] == 30

    @pytest.mark.parametrize("missing_key", ["connascence", "duplication", "nasa"])
    def test_collect_metrics_missing_keys(self, default_collector, missing_key):
        """Test handling of missing violation keys."""
        violations = {
            "connascence": [],
            "duplication": [],
            "nasa": []
        }
        violations.pop(missing_key)

        metrics = default_collector.collect_violation_metrics(violations)
        assert metrics["total_violations"] == 0


# ============================================================================
# SEVERITY NORMALIZATION TESTS
# ============================================================================

class TestSeverityNormalization:
    """Test _normalize_severity() method."""

    @pytest.mark.parametrize("input_severity,expected", [
        ("critical", "critical"),
        ("CRITICAL", "critical"),
        ("Critical", "critical"),
        ("high", "high"),
        ("HIGH", "high"),
        ("medium", "medium"),
        ("MEDIUM", "medium"),
        ("low", "low"),
        ("LOW", "low"),
        ("info", "info"),
        ("INFO", "info"),
        ("error", "high"),  # Maps to high
        ("ERROR", "high"),
        ("warning", "medium"),  # Maps to medium
        ("WARNING", "medium"),
        ("notice", "low"),  # Maps to low
        ("NOTICE", "low"),
        ("unknown", "medium"),  # Default
        ("invalid", "medium"),  # Default
        ("", "medium"),  # Default
    ])
    def test_normalize_severity(self, default_collector, input_severity, expected):
        """Test severity normalization with various inputs."""
        result = default_collector._normalize_severity(input_severity)
        assert result == expected


# ============================================================================
# SEVERITY COUNTING TESTS
# ============================================================================

class TestCountViolationsBySeverity:
    """Test _count_violations_by_severity() method."""

    def test_count_by_severity(self, default_collector):
        """Test counting violations by severity."""
        violations = [
            {"severity": "critical"},
            {"severity": "critical"},
            {"severity": "high"},
            {"severity": "medium"},
            {"severity": "medium"},
            {"severity": "medium"},
            {"severity": "low"},
            {"severity": "info"}
        ]

        counts = default_collector._count_violations_by_severity(violations)

        assert counts["critical"] == 2
        assert counts["high"] == 1
        assert counts["medium"] == 3
        assert counts["low"] == 1
        assert counts["info"] == 1
        assert counts["total"] == 8
        assert counts["high_priority"] == 3  # critical + high

    def test_count_empty_list(self, default_collector):
        """Test counting with empty violations list."""
        counts = default_collector._count_violations_by_severity([])

        assert counts["total"] == 0
        assert counts["high_priority"] == 0

    def test_count_missing_severity(self, default_collector):
        """Test counting with missing severity defaults to medium."""
        violations = [
            {},  # No severity field
            {"other": "field"}  # No severity field
        ]

        counts = default_collector._count_violations_by_severity(violations)
        assert counts["medium"] == 2


# ============================================================================
# CONNASCENCE INDEX TESTS
# ============================================================================

class TestConnascenceIndex:
    """Test _calculate_connascence_index() method."""

    def test_connascence_index_empty(self, default_collector):
        """Test connascence index with no violations."""
        index = default_collector._calculate_connascence_index([])
        assert index == 0.0

    def test_connascence_index_single_violation(self, default_collector):
        """Test connascence index with single violation."""
        violations = [
            {"type": "CoE", "severity": "critical", "weight": 1.0}
        ]

        index = default_collector._calculate_connascence_index(violations)

        # Critical (10) * CoE (2.0) * weight (1.0) = 20.0
        assert index == 20.0

    def test_connascence_index_multiple_violations(self, default_collector):
        """Test connascence index with multiple violations."""
        violations = [
            {"type": "CoE", "severity": "critical", "weight": 1.0},  # 10 * 2.0 * 1.0 = 20
            {"type": "CoP", "severity": "high", "weight": 1.5},      # 5 * 1.6 * 1.5 = 12
            {"type": "CoN", "severity": "medium", "weight": 1.0}     # 2 * 1.0 * 1.0 = 2
        ]

        index = default_collector._calculate_connascence_index(violations)

        expected = 20 + 12 + 2  # 34.0
        assert index == expected

    def test_connascence_index_missing_fields(self, default_collector):
        """Test connascence index with missing optional fields."""
        violations = [
            {},  # Missing everything, should use defaults
            {"type": "CoN"},  # Missing severity and weight
            {"severity": "high"}  # Missing type and weight
        ]

        index = default_collector._calculate_connascence_index(violations)
        assert index > 0  # Should still calculate with defaults


# ============================================================================
# NASA COMPLIANCE SCORE TESTS
# ============================================================================

class TestNASAComplianceScore:
    """Test _calculate_nasa_compliance_score() method."""

    def test_nasa_score_no_violations(self, default_collector):
        """Test NASA score with no violations (perfect compliance)."""
        score = default_collector._calculate_nasa_compliance_score([])
        assert score == 1.0

    def test_nasa_score_single_violation(self, default_collector):
        """Test NASA score with single violation."""
        violations = [
            {"severity": "critical", "context": {"nasa_rule": "Rule1"}}
        ]

        score = default_collector._calculate_nasa_compliance_score(violations)

        # Rule1 weight (0.15) * critical multiplier (2.0) = 0.3 penalty
        # Score = 1.0 - 0.3 = 0.7
        assert score == 0.7

    def test_nasa_score_multiple_violations(self, default_collector):
        """Test NASA score with multiple violations."""
        violations = [
            {"severity": "critical", "context": {"nasa_rule": "Rule1"}},  # 0.15 * 2.0 = 0.3
            {"severity": "high", "context": {"nasa_rule": "Rule4"}},      # 0.10 * 1.5 = 0.15
            {"severity": "medium", "context": {"nasa_rule": "Rule5"}}     # 0.08 * 1.0 = 0.08
        ]

        score = default_collector._calculate_nasa_compliance_score(violations)

        # Total penalty: 0.3 + 0.15 + 0.08 = 0.53
        # Score = 1.0 - 0.53 = 0.47
        expected = max(0.0, 1.0 - 0.53)
        assert score == pytest.approx(expected, rel=0.01)

    def test_nasa_score_cannot_go_negative(self, default_collector):
        """Test that NASA score cannot go below 0."""
        # Create violations with massive penalties
        violations = [
            {"severity": "critical", "context": {"nasa_rule": "Rule1"}}
            for _ in range(100)
        ]

        score = default_collector._calculate_nasa_compliance_score(violations)
        assert score >= 0.0

    def test_nasa_score_missing_context(self, default_collector):
        """Test NASA score with missing context (uses default rule)."""
        violations = [
            {"severity": "high"}  # Missing context
        ]

        score = default_collector._calculate_nasa_compliance_score(violations)
        assert score < 1.0  # Should still apply penalty


# ============================================================================
# DUPLICATION SCORE TESTS
# ============================================================================

class TestDuplicationScore:
    """Test _calculate_duplication_score() method."""

    def test_duplication_score_no_clusters(self, default_collector):
        """Test duplication score with no clusters (perfect score)."""
        score = default_collector._calculate_duplication_score([])
        assert score == 1.0

    def test_duplication_score_single_cluster(self, default_collector):
        """Test duplication score with single cluster."""
        clusters = [
            {
                "similarity_score": 0.8,
                "functions": [
                    {"name": "func1", "file": "a.py"},
                    {"name": "func2", "file": "b.py"}
                ]
            }
        ]

        score = default_collector._calculate_duplication_score(clusters)

        # Base penalty (0.05) * similarity (0.8) * size_multiplier (2/5=0.4) = 0.016
        # Score = 1.0 - 0.016 = 0.984
        assert score > 0.95

    def test_duplication_score_multiple_clusters(self, default_collector):
        """Test duplication score with multiple clusters."""
        clusters = [
            {
                "similarity_score": 0.9,
                "functions": [{"name": f"f{i}", "file": f"f{i}.py"} for i in range(10)]
            },
            {
                "similarity_score": 0.7,
                "functions": [{"name": "g1", "file": "g1.py"}, {"name": "g2", "file": "g2.py"}]
            }
        ]

        score = default_collector._calculate_duplication_score(clusters)
        assert 0.0 <= score <= 1.0

    def test_duplication_score_cannot_go_negative(self, default_collector):
        """Test that duplication score cannot go below 0."""
        # Create clusters with massive penalties
        clusters = [
            {
                "similarity_score": 1.0,
                "functions": [{"name": f"f{i}", "file": f"f{i}.py"} for i in range(100)]
            }
            for _ in range(50)
        ]

        score = default_collector._calculate_duplication_score(clusters)
        assert score >= 0.0

    def test_duplication_score_size_multiplier_capped(self, default_collector):
        """Test that size multiplier is capped at 2x."""
        clusters = [
            {
                "similarity_score": 1.0,
                "functions": [{"name": f"f{i}", "file": f"f{i}.py"} for i in range(100)]  # >> 5
            }
        ]

        score = default_collector._calculate_duplication_score(clusters)
        # Base (0.05) * similarity (1.0) * capped_size (2.0) = 0.1 penalty
        # Score = 1.0 - 0.1 = 0.9
        assert score == pytest.approx(0.9, rel=0.01)


# ============================================================================
# QUALITY SCORE CALCULATION TESTS
# ============================================================================

class TestQualityScoreCalculation:
    """Test calculate_quality_score() method."""

    def test_quality_score_perfect(self, default_collector):
        """Test quality score with perfect metrics."""
        metrics = {
            "connascence_index": 0.0,
            "nasa_compliance_score": 1.0,
            "duplication_score": 1.0
        }

        score = default_collector.calculate_quality_score(metrics)
        assert score == pytest.approx(1.0, rel=0.01)

    def test_quality_score_poor(self, default_collector):
        """Test quality score with poor metrics."""
        metrics = {
            "connascence_index": 100.0,  # Very high
            "nasa_compliance_score": 0.0,
            "duplication_score": 0.0
        }

        score = default_collector.calculate_quality_score(metrics)
        assert score < 0.5

    def test_quality_score_mixed(self, default_collector):
        """Test quality score with mixed metrics."""
        metrics = {
            "connascence_index": 25.0,
            "nasa_compliance_score": 0.7,
            "duplication_score": 0.8
        }

        score = default_collector.calculate_quality_score(metrics)
        assert 0.0 <= score <= 1.0

    def test_quality_score_none_assertion(self, default_collector):
        """Test that None metrics raises assertion."""
        with pytest.raises(AssertionError):
            default_collector.calculate_quality_score(None)

    def test_quality_score_missing_fields_uses_defaults(self, default_collector):
        """Test quality score with missing fields uses defaults."""
        metrics = {}  # Empty dict

        score = default_collector.calculate_quality_score(metrics)
        # connascence_index defaults to 0.0 (score 1.0)
        # nasa_compliance_score defaults to 1.0
        # duplication_score defaults to 1.0
        # Overall should be high
        assert score > 0.9


# ============================================================================
# DYNAMIC WEIGHTS TESTS
# ============================================================================

class TestDynamicWeights:
    """Test _calculate_dynamic_weights() method."""

    def test_dynamic_weights_normal_scores(self, default_collector):
        """Test dynamic weights with normal scores."""
        weights = default_collector._calculate_dynamic_weights(25.0, 0.8, 0.8)

        # No problem areas, should be close to defaults
        assert sum(weights.values()) == pytest.approx(1.0, rel=0.01)
        assert all(0 <= w <= 1 for w in weights.values())

    def test_dynamic_weights_low_nasa_score(self, default_collector):
        """Test dynamic weights with low NASA score boosts nasa_compliance weight."""
        weights = default_collector._calculate_dynamic_weights(10.0, 0.3, 0.8)

        # NASA compliance should get boosted
        assert weights["nasa_compliance"] > 0.3
        assert sum(weights.values()) == pytest.approx(1.0, rel=0.01)

    def test_dynamic_weights_low_duplication_score(self, default_collector):
        """Test dynamic weights with low duplication score boosts duplication weight."""
        weights = default_collector._calculate_dynamic_weights(10.0, 0.8, 0.3)

        # Duplication should get boosted
        assert weights["duplication"] > 0.3
        assert sum(weights.values()) == pytest.approx(1.0, rel=0.01)

    def test_dynamic_weights_high_connascence(self, default_collector):
        """Test dynamic weights with high connascence boosts connascence weight."""
        weights = default_collector._calculate_dynamic_weights(60.0, 0.8, 0.8)

        # Connascence should get boosted
        assert weights["connascence"] > 0.4
        assert sum(weights.values()) == pytest.approx(1.0, rel=0.01)

    def test_dynamic_weights_all_problems(self, default_collector):
        """Test dynamic weights with all problem areas."""
        weights = default_collector._calculate_dynamic_weights(60.0, 0.4, 0.4)

        # All weights should be adjusted but still sum to 1.0
        assert sum(weights.values()) == pytest.approx(1.0, rel=0.01)


# ============================================================================
# SNAPSHOT CREATION TESTS
# ============================================================================

class TestSnapshotCreation:
    """Test create_snapshot() method."""

    def test_create_snapshot_basic(self, default_collector):
        """Test creating a basic snapshot."""
        metrics = {
            "timestamp": "2024-01-01T12:00:00",
            "total_violations": 10,
            "critical_count": 2,
            "high_count": 3,
            "medium_count": 4,
            "low_count": 1,
            "connascence_index": 25.5,
            "nasa_compliance_score": 0.85,
            "duplication_score": 0.9,
            "overall_quality_score": 0.82,
            "collection_time_ms": 15.5,
            "files_analyzed": 5,
            "metadata": {"key": "value"}
        }

        snapshot = default_collector.create_snapshot(metrics)

        assert isinstance(snapshot, MetricsSnapshot)
        assert snapshot.timestamp == "2024-01-01T12:00:00"
        assert snapshot.total_violations == 10
        assert snapshot.critical_count == 2
        assert snapshot.high_count == 3
        assert snapshot.medium_count == 4
        assert snapshot.low_count == 1
        assert snapshot.connascence_index == 25.5
        assert snapshot.nasa_compliance_score == 0.85
        assert snapshot.duplication_score == 0.9
        assert snapshot.overall_quality_score == 0.82
        assert snapshot.calculation_time_ms == 15.5
        assert snapshot.files_analyzed == 5
        assert snapshot.metadata == {"key": "value"}

    def test_create_snapshot_adds_to_history(self, default_collector):
        """Test that creating snapshot adds to history."""
        metrics = {
            "total_violations": 5,
            "critical_count": 1,
            "high_count": 1,
            "medium_count": 2,
            "low_count": 1,
            "connascence_index": 10.0,
            "nasa_compliance_score": 0.9,
            "duplication_score": 0.95,
            "overall_quality_score": 0.88
        }

        assert len(default_collector.metrics_history) == 0

        default_collector.create_snapshot(metrics)
        assert len(default_collector.metrics_history) == 1

    def test_create_snapshot_history_limit(self, custom_collector):
        """Test that snapshot history respects limit."""
        # Custom collector has history_limit = 10
        metrics = {
            "total_violations": 5,
            "critical_count": 1,
            "high_count": 1,
            "medium_count": 2,
            "low_count": 1,
            "connascence_index": 10.0,
            "nasa_compliance_score": 0.9,
            "duplication_score": 0.95,
            "overall_quality_score": 0.88
        }

        # Create 15 snapshots (exceeds limit of 10)
        for i in range(15):
            metrics["total_violations"] = i
            custom_collector.create_snapshot(metrics)

        assert len(custom_collector.metrics_history) == 10  # Capped at limit

    def test_create_snapshot_none_assertion(self, default_collector):
        """Test that None metrics raises assertion."""
        with pytest.raises(AssertionError):
            default_collector.create_snapshot(None)

    def test_create_snapshot_missing_fields_uses_defaults(self, default_collector):
        """Test snapshot with missing fields uses defaults."""
        metrics = {}  # Empty dict

        snapshot = default_collector.create_snapshot(metrics)

        assert snapshot.total_violations == 0
        assert snapshot.critical_count == 0
        assert snapshot.connascence_index == 0.0
        assert snapshot.nasa_compliance_score == 1.0
        assert snapshot.duplication_score == 1.0


# ============================================================================
# PERFORMANCE TRACKING TESTS
# ============================================================================

class TestPerformanceTracking:
    """Test track_performance() method."""

    def test_track_performance_basic(self, default_collector):
        """Test basic performance tracking."""
        perf = default_collector.track_performance(1.5, 10)

        assert perf["analysis_time_ms"] == 1500.0
        assert perf["files_analyzed"] == 10
        assert perf["files_per_second"] == pytest.approx(10 / 1.5, rel=0.01)
        assert "performance_rating" in perf
        assert "timestamp" in perf

    def test_track_performance_rating_excellent(self, default_collector):
        """Test performance rating: excellent (>10 fps)."""
        perf = default_collector.track_performance(0.5, 20)  # 40 fps
        assert perf["performance_rating"] == "excellent"

    def test_track_performance_rating_good(self, default_collector):
        """Test performance rating: good (5-10 fps)."""
        perf = default_collector.track_performance(1.0, 8)  # 8 fps
        assert perf["performance_rating"] == "good"

    def test_track_performance_rating_acceptable(self, default_collector):
        """Test performance rating: acceptable (2-5 fps)."""
        perf = default_collector.track_performance(1.0, 3)  # 3 fps
        assert perf["performance_rating"] == "acceptable"

    def test_track_performance_rating_slow(self, default_collector):
        """Test performance rating: slow (<2 fps)."""
        perf = default_collector.track_performance(2.0, 3)  # 1.5 fps
        assert perf["performance_rating"] == "slow"

    def test_track_performance_zero_files(self, default_collector):
        """Test performance tracking with zero files."""
        perf = default_collector.track_performance(1.0, 0)

        assert perf["files_per_second"] == 0
        assert perf["performance_rating"] == "no_files"

    def test_track_performance_adds_to_history(self, default_collector):
        """Test that performance tracking adds to history."""
        assert len(default_collector.performance_history) == 0

        default_collector.track_performance(1.0, 10)
        assert len(default_collector.performance_history) == 1

    def test_track_performance_history_limit(self, default_collector):
        """Test that performance history respects limit."""
        # Default history_limit = 20
        for i in range(25):
            default_collector.track_performance(1.0, 10)

        assert len(default_collector.performance_history) == 20

    def test_track_performance_increments_count(self, default_collector):
        """Test that analysis_count increments."""
        assert default_collector.analysis_count == 0

        default_collector.track_performance(1.0, 10)
        assert default_collector.analysis_count == 1

        default_collector.track_performance(1.0, 10)
        assert default_collector.analysis_count == 2

    def test_track_performance_negative_time_assertion(self, default_collector):
        """Test that negative time raises assertion."""
        with pytest.raises(AssertionError):
            default_collector.track_performance(-1.0, 10)

    def test_track_performance_negative_files_assertion(self, default_collector):
        """Test that negative file count raises assertion."""
        with pytest.raises(AssertionError):
            default_collector.track_performance(1.0, -5)


# ============================================================================
# TREND ANALYSIS TESTS
# ============================================================================

class TestTrendAnalysis:
    """Test get_trend_analysis() method."""

    def test_trend_analysis_no_data(self, default_collector):
        """Test trend analysis with no data."""
        trend = default_collector.get_trend_analysis()

        assert trend["trend"] == "no_data"
        assert trend["direction"] == "unknown"

    def test_trend_analysis_insufficient_data(self, default_collector):
        """Test trend analysis with insufficient data (< 2 snapshots)."""
        metrics = {
            "total_violations": 5,
            "critical_count": 1,
            "high_count": 1,
            "medium_count": 2,
            "low_count": 1,
            "connascence_index": 10.0,
            "nasa_compliance_score": 0.9,
            "duplication_score": 0.95,
            "overall_quality_score": 0.88
        }

        default_collector.create_snapshot(metrics)

        trend = default_collector.get_trend_analysis()
        assert trend["trend"] == "insufficient_data"
        assert trend["direction"] == "stable"

    def test_trend_analysis_improving(self, default_collector):
        """Test trend analysis showing improvement."""
        # Create snapshots with improving quality
        for i in range(5):
            metrics = {
                "total_violations": 10 - i,  # Decreasing violations
                "critical_count": 2 - (i // 2),
                "high_count": 3 - (i // 2),
                "medium_count": 4,
                "low_count": 1,
                "connascence_index": 30.0 - i * 2,
                "nasa_compliance_score": 0.7 + i * 0.05,
                "duplication_score": 0.75 + i * 0.05,
                "overall_quality_score": 0.7 + i * 0.08  # Improving >0.05
            }
            default_collector.create_snapshot(metrics)

        trend = default_collector.get_trend_analysis()
        assert trend["direction"] == "improving"
        assert trend["quality_change"] > 0.05

    def test_trend_analysis_degrading(self, default_collector):
        """Test trend analysis showing degradation."""
        # Create snapshots with degrading quality
        for i in range(5):
            metrics = {
                "total_violations": 10 + i * 2,  # Increasing violations
                "critical_count": 2 + i,
                "high_count": 3 + i,
                "medium_count": 4,
                "low_count": 1,
                "connascence_index": 30.0 + i * 5,
                "nasa_compliance_score": 0.9 - i * 0.05,
                "duplication_score": 0.9 - i * 0.05,
                "overall_quality_score": 0.85 - i * 0.08  # Degrading >0.05
            }
            default_collector.create_snapshot(metrics)

        trend = default_collector.get_trend_analysis()
        assert trend["direction"] == "degrading"
        assert trend["quality_change"] < -0.05

    def test_trend_analysis_stable(self, default_collector):
        """Test trend analysis showing stability."""
        # Create snapshots with stable quality
        for i in range(5):
            metrics = {
                "total_violations": 10,
                "critical_count": 2,
                "high_count": 3,
                "medium_count": 4,
                "low_count": 1,
                "connascence_index": 30.0,
                "nasa_compliance_score": 0.8,
                "duplication_score": 0.85,
                "overall_quality_score": 0.8  # Stable within 0.05
            }
            default_collector.create_snapshot(metrics)

        trend = default_collector.get_trend_analysis()
        assert trend["direction"] == "stable"

    def test_trend_analysis_excellent_progress(self, default_collector):
        """Test overall trend: excellent progress."""
        # Quality improving AND violations decreasing
        for i in range(5):
            metrics = {
                "total_violations": 20 - i * 3,  # Decreasing >5
                "critical_count": 4 - i,
                "high_count": 5 - i,
                "medium_count": 6,
                "low_count": 2,
                "connascence_index": 40.0 - i * 3,
                "nasa_compliance_score": 0.7 + i * 0.06,
                "duplication_score": 0.7 + i * 0.06,
                "overall_quality_score": 0.7 + i * 0.08
            }
            default_collector.create_snapshot(metrics)

        trend = default_collector.get_trend_analysis()
        assert trend["trend"] == "excellent_progress"

    def test_trend_analysis_needs_attention(self, default_collector):
        """Test overall trend: needs attention."""
        # Quality degrading OR violations increasing
        for i in range(5):
            metrics = {
                "total_violations": 10 + i * 3,  # Increasing >5
                "critical_count": 2 + i,
                "high_count": 3 + i,
                "medium_count": 4,
                "low_count": 1,
                "connascence_index": 30.0 + i * 5,
                "nasa_compliance_score": 0.8 - i * 0.08,
                "duplication_score": 0.8 - i * 0.08,
                "overall_quality_score": 0.8 - i * 0.08
            }
            default_collector.create_snapshot(metrics)

        trend = default_collector.get_trend_analysis()
        assert trend["trend"] == "needs_attention"


# ============================================================================
# BASELINE COMPARISON TESTS
# ============================================================================

class TestBaselineComparison:
    """Test baseline setting and comparison."""

    def test_set_baseline(self, default_collector):
        """Test setting baseline metrics."""
        metrics = {
            "total_violations": 10,
            "critical_count": 2,
            "high_count": 3,
            "medium_count": 4,
            "low_count": 1,
            "connascence_index": 25.0,
            "nasa_compliance_score": 0.85,
            "duplication_score": 0.9,
            "overall_quality_score": 0.82
        }

        assert default_collector.baseline_metrics is None

        default_collector.set_baseline(metrics)

        assert default_collector.baseline_metrics is not None
        assert default_collector.baseline_metrics.overall_quality_score == 0.82

    def test_get_baseline_comparison_no_baseline(self, default_collector):
        """Test baseline comparison with no baseline set."""
        comparison = default_collector.get_baseline_comparison()
        assert comparison is None

    def test_get_baseline_comparison_no_history(self, default_collector):
        """Test baseline comparison with no history."""
        metrics = {
            "total_violations": 10,
            "critical_count": 2,
            "high_count": 3,
            "medium_count": 4,
            "low_count": 1,
            "connascence_index": 25.0,
            "nasa_compliance_score": 0.85,
            "duplication_score": 0.9,
            "overall_quality_score": 0.82
        }

        default_collector.set_baseline(metrics)
        # Clear history
        default_collector.metrics_history = []

        comparison = default_collector.get_baseline_comparison()
        assert comparison is None

    def test_get_baseline_comparison_improved(self, default_collector):
        """Test baseline comparison showing improvement."""
        baseline_metrics = {
            "total_violations": 15,
            "critical_count": 3,
            "high_count": 5,
            "medium_count": 5,
            "low_count": 2,
            "connascence_index": 35.0,
            "nasa_compliance_score": 0.7,
            "duplication_score": 0.75,
            "overall_quality_score": 0.7
        }

        current_metrics = {
            "total_violations": 8,
            "critical_count": 1,
            "high_count": 2,
            "medium_count": 4,
            "low_count": 1,
            "connascence_index": 20.0,
            "nasa_compliance_score": 0.85,
            "duplication_score": 0.9,
            "overall_quality_score": 0.85
        }

        default_collector.set_baseline(baseline_metrics)
        default_collector.create_snapshot(current_metrics)

        comparison = default_collector.get_baseline_comparison()

        assert comparison["quality_delta"] > 0  # Improved
        assert comparison["violation_delta"] < 0  # Fewer violations
        assert comparison["status"] in ["improved", "significantly_improved"]

    def test_get_baseline_comparison_degraded(self, default_collector):
        """Test baseline comparison showing degradation."""
        baseline_metrics = {
            "total_violations": 5,
            "critical_count": 1,
            "high_count": 1,
            "medium_count": 2,
            "low_count": 1,
            "connascence_index": 15.0,
            "nasa_compliance_score": 0.9,
            "duplication_score": 0.95,
            "overall_quality_score": 0.88
        }

        current_metrics = {
            "total_violations": 20,
            "critical_count": 5,
            "high_count": 8,
            "medium_count": 5,
            "low_count": 2,
            "connascence_index": 50.0,
            "nasa_compliance_score": 0.6,
            "duplication_score": 0.65,
            "overall_quality_score": 0.65
        }

        default_collector.set_baseline(baseline_metrics)
        default_collector.create_snapshot(current_metrics)

        comparison = default_collector.get_baseline_comparison()

        assert comparison["quality_delta"] < 0  # Degraded
        assert comparison["violation_delta"] > 0  # More violations
        assert comparison["status"] in ["degraded", "significantly_degraded"]

    @pytest.mark.parametrize("quality_delta,expected_status", [
        (0.15, "significantly_improved"),
        (0.05, "improved"),
        (0.01, "stable"),
        (-0.01, "stable"),
        (-0.05, "degraded"),
        (-0.15, "significantly_degraded")
    ])
    def test_baseline_status_thresholds(self, default_collector, quality_delta, expected_status):
        """Test baseline status determination thresholds."""
        baseline_metrics = {
            "total_violations": 10,
            "critical_count": 2,
            "high_count": 3,
            "medium_count": 4,
            "low_count": 1,
            "connascence_index": 25.0,
            "nasa_compliance_score": 0.8,
            "duplication_score": 0.85,
            "overall_quality_score": 0.7
        }

        current_metrics = baseline_metrics.copy()
        current_metrics["overall_quality_score"] = 0.7 + quality_delta

        default_collector.set_baseline(baseline_metrics)
        default_collector.create_snapshot(current_metrics)

        comparison = default_collector.get_baseline_comparison()
        assert comparison["status"] == expected_status


# ============================================================================
# METRICS SUMMARY TESTS
# ============================================================================

class TestMetricsSummary:
    """Test get_metrics_summary() method."""

    def test_metrics_summary_no_data(self, default_collector):
        """Test metrics summary with no data."""
        summary = default_collector.get_metrics_summary()
        assert summary["status"] == "no_data"

    def test_metrics_summary_with_data(self, default_collector):
        """Test metrics summary with data."""
        metrics = {
            "total_violations": 12,
            "critical_count": 3,
            "high_count": 4,
            "medium_count": 4,
            "low_count": 1,
            "connascence_index": 28.0,
            "nasa_compliance_score": 0.8,
            "duplication_score": 0.85,
            "overall_quality_score": 0.78
        }

        default_collector.create_snapshot(metrics)

        summary = default_collector.get_metrics_summary()

        assert summary["current_quality"] == 0.78
        assert summary["total_violations"] == 12
        assert summary["high_priority_violations"] == 7  # critical + high
        assert "trend" in summary
        assert summary["analysis_count"] == 0
        assert summary["history_size"] == 1

    def test_metrics_summary_with_baseline(self, default_collector):
        """Test metrics summary includes baseline comparison."""
        baseline_metrics = {
            "total_violations": 10,
            "critical_count": 2,
            "high_count": 3,
            "medium_count": 4,
            "low_count": 1,
            "connascence_index": 25.0,
            "nasa_compliance_score": 0.8,
            "duplication_score": 0.85,
            "overall_quality_score": 0.75
        }

        current_metrics = {
            "total_violations": 8,
            "critical_count": 1,
            "high_count": 2,
            "medium_count": 4,
            "low_count": 1,
            "connascence_index": 20.0,
            "nasa_compliance_score": 0.85,
            "duplication_score": 0.9,
            "overall_quality_score": 0.82
        }

        default_collector.set_baseline(baseline_metrics)
        default_collector.create_snapshot(current_metrics)

        summary = default_collector.get_metrics_summary()

        assert summary["baseline_comparison"] is not None
        assert summary["baseline_comparison"]["quality_delta"] > 0


# ============================================================================
# EXPORT METRICS HISTORY TESTS
# ============================================================================

class TestExportMetricsHistory:
    """Test export_metrics_history() method."""

    def test_export_empty_history(self, default_collector):
        """Test exporting empty history."""
        exported = default_collector.export_metrics_history()
        assert exported == []

    def test_export_metrics_history(self, default_collector):
        """Test exporting metrics history."""
        # Create multiple snapshots
        for i in range(3):
            metrics = {
                "total_violations": 10 + i,
                "critical_count": 2 + i,
                "high_count": 3,
                "medium_count": 4,
                "low_count": 1,
                "connascence_index": 25.0 + i * 2,
                "nasa_compliance_score": 0.8 + i * 0.05,
                "duplication_score": 0.85 + i * 0.05,
                "overall_quality_score": 0.8 + i * 0.05,
                "files_analyzed": 5 + i
            }
            default_collector.create_snapshot(metrics)

        exported = default_collector.export_metrics_history()

        assert len(exported) == 3
        assert all("timestamp" in item for item in exported)
        assert all("quality_score" in item for item in exported)
        assert all("violations" in item for item in exported)
        assert exported[0]["violations"] == 10
        assert exported[1]["violations"] == 11
        assert exported[2]["violations"] == 12


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_very_large_connascence_index(self, default_collector):
        """Test handling of very large connascence index."""
        violations = [
            {"type": "CoE", "severity": "critical", "weight": 100.0}
            for _ in range(100)
        ]

        index = default_collector._calculate_connascence_index(violations)
        assert index > 0  # Should handle large numbers

    def test_zero_analysis_time(self, default_collector):
        """Test performance tracking with zero analysis time."""
        perf = default_collector.track_performance(0.0, 10)

        # Should not divide by zero
        assert perf["files_per_second"] == 0

    def test_snapshot_with_all_defaults(self, default_collector):
        """Test snapshot creation with all default values."""
        metrics = {}

        snapshot = default_collector.create_snapshot(metrics)

        # Should use all defaults without errors
        assert snapshot.total_violations == 0
        assert snapshot.overall_quality_score == 0.0

    def test_multiple_collectors_independent(self):
        """Test that multiple collectors are independent."""
        collector1 = MetricsCollector()
        collector2 = MetricsCollector()

        metrics = {
            "total_violations": 10,
            "critical_count": 2,
            "high_count": 3,
            "medium_count": 4,
            "low_count": 1,
            "connascence_index": 25.0,
            "nasa_compliance_score": 0.8,
            "duplication_score": 0.85,
            "overall_quality_score": 0.8
        }

        collector1.create_snapshot(metrics)

        assert len(collector1.metrics_history) == 1
        assert len(collector2.metrics_history) == 0  # Independent


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests combining multiple methods."""

    def test_full_workflow(self, default_collector, sample_violations_dict):
        """Test full workflow: collect -> snapshot -> trend -> summary."""
        # Step 1: Collect metrics
        metrics = default_collector.collect_violation_metrics(sample_violations_dict)
        assert "total_violations" in metrics

        # Step 2: Create snapshot
        snapshot = default_collector.create_snapshot(metrics)
        assert isinstance(snapshot, MetricsSnapshot)

        # Step 3: Set baseline
        default_collector.set_baseline(metrics)

        # Step 4: Collect more metrics (improved)
        improved_violations = {
            "connascence": sample_violations_dict["connascence"][:1],  # Fewer
            "duplication": [],  # No duplication
            "nasa": []  # No NASA violations
        }

        metrics2 = default_collector.collect_violation_metrics(improved_violations)
        default_collector.create_snapshot(metrics2)

        # Step 5: Get trend analysis
        trend = default_collector.get_trend_analysis()
        assert trend["trend"] in ["excellent_progress", "mixed", "stable"]

        # Step 6: Get summary
        summary = default_collector.get_metrics_summary()
        assert "current_quality" in summary
        assert "baseline_comparison" in summary

        # Step 7: Export history
        exported = default_collector.export_metrics_history()
        assert len(exported) == 2

    def test_continuous_monitoring_scenario(self, default_collector):
        """Test continuous monitoring scenario with multiple analyses."""
        # Simulate 10 analysis runs with varying quality
        for i in range(10):
            violations = {
                "connascence": [
                    {"type": "CoE", "severity": "critical", "weight": 1.0}
                    for _ in range(max(0, 5 - i // 2))  # Decreasing over time
                ],
                "duplication": [],
                "nasa": [
                    {"severity": "medium", "context": {"nasa_rule": "Rule4"}}
                    for _ in range(max(0, 3 - i // 3))
                ]
            }

            metrics = default_collector.collect_violation_metrics(violations)
            default_collector.create_snapshot(metrics)
            default_collector.track_performance(0.5 + i * 0.1, 10 + i)

        # Should have 10 snapshots (within history limit)
        assert len(default_collector.metrics_history) == 10

        # Analysis count should be 10
        assert default_collector.analysis_count == 10

        # Trend should show improvement
        trend = default_collector.get_trend_analysis()
        assert trend["direction"] in ["improving", "stable"]

        # Summary should have complete data
        summary = default_collector.get_metrics_summary()
        assert summary["history_size"] == 10


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Performance-related tests."""

    def test_collect_metrics_performance(self, default_collector, large_violations):
        """Test metrics collection performance with large dataset."""
        import time

        start = time.time()
        metrics = default_collector.collect_violation_metrics(large_violations)
        duration = time.time() - start

        # Should complete in reasonable time (<1 second for 100 violations)
        assert duration < 1.0
        assert metrics["collection_time_ms"] > 0

    def test_snapshot_creation_performance(self, default_collector):
        """Test snapshot creation performance with many snapshots."""
        import time

        metrics = {
            "total_violations": 10,
            "critical_count": 2,
            "high_count": 3,
            "medium_count": 4,
            "low_count": 1,
            "connascence_index": 25.0,
            "nasa_compliance_score": 0.8,
            "duplication_score": 0.85,
            "overall_quality_score": 0.8
        }

        start = time.time()
        for _ in range(100):
            default_collector.create_snapshot(metrics)
        duration = time.time() - start

        # Should complete 100 snapshots quickly (<0.5 seconds)
        assert duration < 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
