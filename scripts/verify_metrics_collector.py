#!/usr/bin/env python3
"""
Metrics Collector Verification Script
======================================

Verifies that the MetricsCollector extraction is complete and functional.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.architecture.metrics_collector import MetricsCollector, MetricsSnapshot


def verify_implementation():
    """Verify MetricsCollector implementation exists and works."""
    print("1. Verifying MetricsCollector implementation...")

    try:
        collector = MetricsCollector()
        print("   PASS: MetricsCollector initialized successfully")
        return True
    except Exception as e:
        print(f"   FAIL: MetricsCollector initialization failed: {e}")
        return False


def verify_basic_functionality():
    """Verify basic metrics collection functionality."""
    print("\n2. Verifying basic metrics collection...")

    try:
        collector = MetricsCollector()

        violations = {
            "connascence": [
                {"severity": "critical", "type": "CoE", "weight": 1.5},
                {"severity": "high", "type": "CoT", "weight": 1.0},
            ],
            "duplication": [
                {"similarity_score": 0.85, "functions": ["f1", "f2", "f3"]},
            ],
            "nasa": [
                {"severity": "high", "context": {"nasa_rule": "Rule4"}},
            ]
        }

        metrics = collector.collect_violation_metrics(violations)

        # Verify required fields
        required_fields = [
            "total_violations", "critical_count", "high_count",
            "connascence_index", "nasa_compliance_score",
            "duplication_score", "overall_quality_score"
        ]

        for field in required_fields:
            if field not in metrics:
                print(f"   FAIL: Missing required field: {field}")
                return False

        print(f"   PASS: All required fields present")
        print(f"   - Total Violations: {metrics['total_violations']}")
        print(f"   - Quality Score: {metrics['overall_quality_score']:.3f}")
        return True

    except Exception as e:
        print(f"   FAIL: Metrics collection failed: {e}")
        return False


def verify_quality_scoring():
    """Verify quality score calculation."""
    print("\n3. Verifying quality score calculation...")

    try:
        collector = MetricsCollector()

        test_metrics = {
            "connascence_index": 30.0,
            "nasa_compliance_score": 0.9,
            "duplication_score": 0.95
        }

        score = collector.calculate_quality_score(test_metrics)

        if not isinstance(score, float):
            print(f"   FAIL: Quality score is not float: {type(score)}")
            return False

        if not 0.0 <= score <= 1.0:
            print(f"   FAIL: Quality score out of range: {score}")
            return False

        print(f"   PASS: Quality score calculated: {score:.3f}")
        return True

    except Exception as e:
        print(f"   FAIL: Quality scoring failed: {e}")
        return False


def verify_performance_tracking():
    """Verify performance tracking."""
    print("\n4. Verifying performance tracking...")

    try:
        collector = MetricsCollector()

        perf = collector.track_performance(analysis_time=1.5, file_count=50)

        required_fields = [
            "analysis_time_ms", "files_analyzed",
            "files_per_second", "performance_rating"
        ]

        for field in required_fields:
            if field not in perf:
                print(f"   FAIL: Missing performance field: {field}")
                return False

        if perf["files_analyzed"] != 50:
            print(f"   FAIL: Incorrect file count: {perf['files_analyzed']}")
            return False

        print(f"   PASS: Performance tracking working")
        print(f"   - Files/Second: {perf['files_per_second']:.2f}")
        print(f"   - Rating: {perf['performance_rating']}")
        return True

    except Exception as e:
        print(f"   FAIL: Performance tracking failed: {e}")
        return False


def verify_snapshot_creation():
    """Verify snapshot creation."""
    print("\n5. Verifying snapshot creation...")

    try:
        collector = MetricsCollector()

        violations = {
            "connascence": [{"severity": "high", "type": "CoE", "weight": 1.0}],
            "duplication": [],
            "nasa": []
        }

        metrics = collector.collect_violation_metrics(violations)
        snapshot = collector.create_snapshot(metrics)

        if not isinstance(snapshot, MetricsSnapshot):
            print(f"   FAIL: Snapshot is not MetricsSnapshot: {type(snapshot)}")
            return False

        if len(collector.metrics_history) != 1:
            print(f"   FAIL: History not updated: {len(collector.metrics_history)}")
            return False

        print(f"   PASS: Snapshot created successfully")
        print(f"   - Timestamp: {snapshot.timestamp}")
        print(f"   - Quality: {snapshot.overall_quality_score:.3f}")
        return True

    except Exception as e:
        print(f"   FAIL: Snapshot creation failed: {e}")
        return False


def verify_trend_analysis():
    """Verify trend analysis."""
    print("\n6. Verifying trend analysis...")

    try:
        collector = MetricsCollector()

        # Create multiple snapshots
        for i in range(5):
            violations = {
                "connascence": [
                    {"severity": "high", "type": "CoE", "weight": 1.0}
                    for _ in range(5 - i)  # Decreasing
                ],
                "duplication": [],
                "nasa": []
            }

            metrics = collector.collect_violation_metrics(violations)
            collector.create_snapshot(metrics)

        trends = collector.get_trend_analysis()

        required_fields = ["trend", "direction", "quality_change", "violation_change"]

        for field in required_fields:
            if field not in trends:
                print(f"   FAIL: Missing trend field: {field}")
                return False

        print(f"   PASS: Trend analysis working")
        print(f"   - Overall Trend: {trends['trend']}")
        print(f"   - Direction: {trends['direction']}")
        return True

    except Exception as e:
        print(f"   FAIL: Trend analysis failed: {e}")
        return False


def verify_baseline_comparison():
    """Verify baseline comparison."""
    print("\n7. Verifying baseline comparison...")

    try:
        collector = MetricsCollector()

        # Set baseline
        violations = {
            "connascence": [{"severity": "high", "type": "CoE", "weight": 1.0} for _ in range(5)],
            "duplication": [],
            "nasa": []
        }

        baseline_metrics = collector.collect_violation_metrics(violations)
        collector.set_baseline(baseline_metrics)

        # Create improved snapshot
        improved_violations = {
            "connascence": [{"severity": "medium", "type": "CoN", "weight": 1.0} for _ in range(2)],
            "duplication": [],
            "nasa": []
        }

        improved_metrics = collector.collect_violation_metrics(improved_violations)
        collector.create_snapshot(improved_metrics)

        comparison = collector.get_baseline_comparison()

        if comparison is None:
            print("   FAIL: Baseline comparison returned None")
            return False

        required_fields = ["quality_delta", "violation_delta", "status"]

        for field in required_fields:
            if field not in comparison:
                print(f"   FAIL: Missing comparison field: {field}")
                return False

        print(f"   PASS: Baseline comparison working")
        print(f"   - Quality Delta: {comparison['quality_delta']:+.3f}")
        print(f"   - Status: {comparison['status']}")
        return True

    except Exception as e:
        print(f"   FAIL: Baseline comparison failed: {e}")
        return False


def verify_metrics_summary():
    """Verify metrics summary."""
    print("\n8. Verifying metrics summary...")

    try:
        collector = MetricsCollector()

        # Create snapshot
        violations = {
            "connascence": [{"severity": "high", "type": "CoE", "weight": 1.0}],
            "duplication": [],
            "nasa": []
        }

        metrics = collector.collect_violation_metrics(violations)
        collector.create_snapshot(metrics)

        summary = collector.get_metrics_summary()

        required_fields = ["current_quality", "total_violations", "analysis_count"]

        for field in required_fields:
            if field not in summary:
                print(f"   FAIL: Missing summary field: {field}")
                return False

        print(f"   PASS: Metrics summary working")
        print(f"   - Current Quality: {summary['current_quality']:.3f}")
        print(f"   - Analysis Count: {summary['analysis_count']}")
        return True

    except Exception as e:
        print(f"   FAIL: Metrics summary failed: {e}")
        return False


def verify_export_functionality():
    """Verify metrics export."""
    print("\n9. Verifying metrics export...")

    try:
        collector = MetricsCollector()

        # Create multiple snapshots
        for i in range(3):
            violations = {
                "connascence": [{"severity": "high", "type": "CoE", "weight": 1.0}],
                "duplication": [],
                "nasa": []
            }

            metrics = collector.collect_violation_metrics(violations)
            collector.create_snapshot(metrics)

        exported = collector.export_metrics_history()

        if not isinstance(exported, list):
            print(f"   FAIL: Export is not list: {type(exported)}")
            return False

        if len(exported) != 3:
            print(f"   FAIL: Wrong export count: {len(exported)}")
            return False

        # Verify export structure
        required_fields = ["timestamp", "quality_score", "violations"]

        for entry in exported:
            for field in required_fields:
                if field not in entry:
                    print(f"   FAIL: Missing export field: {field}")
                    return False

        print(f"   PASS: Metrics export working")
        print(f"   - Exported {len(exported)} snapshots")
        return True

    except Exception as e:
        print(f"   FAIL: Metrics export failed: {e}")
        return False


def verify_nasa_compliance():
    """Verify NASA Rule 4 compliance."""
    print("\n10. Verifying NASA Rule 4 compliance...")

    try:
        from analyzer.architecture.metrics_collector import MetricsCollector
        import inspect

        collector = MetricsCollector()

        # Get all methods
        methods = [
            (name, method) for name, method in inspect.getmembers(collector, inspect.ismethod)
            if not name.startswith('__')
        ]

        violations = []

        for name, method in methods:
            source = inspect.getsource(method)
            line_count = len(source.split('\n'))

            if line_count > 60:
                violations.append((name, line_count))

        if violations:
            print("   FAIL: NASA Rule 4 violations found:")
            for name, lines in violations:
                print(f"   - {name}: {lines} lines (limit: 60)")
            return False

        print(f"   PASS: All {len(methods)} methods comply with NASA Rule 4")
        print(f"   - All methods under 60 lines")
        return True

    except Exception as e:
        print(f"   FAIL: NASA compliance check failed: {e}")
        return False


def main():
    """Run all verification tests."""
    print("=" * 70)
    print("MetricsCollector Extraction Verification")
    print("=" * 70)

    tests = [
        verify_implementation,
        verify_basic_functionality,
        verify_quality_scoring,
        verify_performance_tracking,
        verify_snapshot_creation,
        verify_trend_analysis,
        verify_baseline_comparison,
        verify_metrics_summary,
        verify_export_functionality,
        verify_nasa_compliance,
    ]

    results = []

    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n   ERROR: Test failed with exception: {e}")
            results.append(False)

    print("\n" + "=" * 70)
    print("Verification Results")
    print("=" * 70)

    passed = sum(results)
    total = len(results)

    print(f"\nTests Passed: {passed}/{total}")

    if passed == total:
        print("\nSTATUS: ALL TESTS PASSED")
        print("MetricsCollector extraction is complete and functional!")
        return 0
    else:
        print(f"\nSTATUS: {total - passed} TESTS FAILED")
        print("Please review the failures above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
