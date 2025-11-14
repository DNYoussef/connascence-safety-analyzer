"""
MetricsCollector Usage Example
===============================

Demonstrates how to use the MetricsCollector class for comprehensive
metrics collection, quality scoring, and trend analysis.
"""

from analyzer.architecture.metrics_collector import MetricsCollector


def example_basic_usage():
    """Basic metrics collection example."""
    print("=== Basic Metrics Collection ===\n")

    # Initialize collector
    collector = MetricsCollector()

    # Sample violations
    violations = {
        "connascence": [
            {"severity": "critical", "type": "CoE", "weight": 1.5},
            {"severity": "high", "type": "CoT", "weight": 1.0},
            {"severity": "medium", "type": "CoN", "weight": 1.0},
            {"severity": "low", "type": "CoM", "weight": 0.5},
        ],
        "duplication": [
            {"similarity_score": 0.85, "functions": ["func1", "func2", "func3"]},
            {"similarity_score": 0.65, "functions": ["func4", "func5"]},
        ],
        "nasa": [
            {"severity": "high", "context": {"nasa_rule": "Rule4"}},
            {"severity": "medium", "context": {"nasa_rule": "Rule5"}},
            {"severity": "low", "context": {"nasa_rule": "Rule7"}},
        ]
    }

    # Collect metrics
    metrics = collector.collect_violation_metrics(violations)

    print(f"Total Violations: {metrics['total_violations']}")
    print(f"Critical Count: {metrics['critical_count']}")
    print(f"High Count: {metrics['high_count']}")
    print(f"Medium Count: {metrics['medium_count']}")
    print(f"Low Count: {metrics['low_count']}")
    print(f"\nConnascence Index: {metrics['connascence_index']}")
    print(f"NASA Compliance Score: {metrics['nasa_compliance_score']}")
    print(f"Duplication Score: {metrics['duplication_score']}")
    print(f"Overall Quality Score: {metrics['overall_quality_score']}")
    print(f"\nCollection Time: {metrics['collection_time_ms']:.2f}ms")


def example_quality_scoring():
    """Quality score calculation example."""
    print("\n=== Quality Score Calculation ===\n")

    collector = MetricsCollector()

    # Scenario 1: High quality code
    high_quality_metrics = {
        "connascence_index": 10.0,
        "nasa_compliance_score": 0.95,
        "duplication_score": 0.98
    }

    score1 = collector.calculate_quality_score(high_quality_metrics)
    print(f"High Quality Code Score: {score1:.3f}")

    # Scenario 2: Poor quality code
    low_quality_metrics = {
        "connascence_index": 80.0,
        "nasa_compliance_score": 0.45,
        "duplication_score": 0.40
    }

    score2 = collector.calculate_quality_score(low_quality_metrics)
    print(f"Low Quality Code Score: {score2:.3f}")

    # Scenario 3: Medium quality code
    medium_quality_metrics = {
        "connascence_index": 35.0,
        "nasa_compliance_score": 0.75,
        "duplication_score": 0.80
    }

    score3 = collector.calculate_quality_score(medium_quality_metrics)
    print(f"Medium Quality Code Score: {score3:.3f}")


def example_performance_tracking():
    """Performance tracking example."""
    print("\n=== Performance Tracking ===\n")

    collector = MetricsCollector()

    # Track different performance scenarios
    scenarios = [
        (1.5, 50, "Fast analysis of 50 files"),
        (5.0, 100, "Medium analysis of 100 files"),
        (10.0, 150, "Slow analysis of 150 files"),
    ]

    for analysis_time, file_count, description in scenarios:
        perf = collector.track_performance(analysis_time, file_count)

        print(f"{description}:")
        print(f"  Analysis Time: {perf['analysis_time_ms']:.2f}ms")
        print(f"  Files/Second: {perf['files_per_second']:.2f}")
        print(f"  Rating: {perf['performance_rating']}")
        print()


def example_trend_analysis():
    """Trend analysis example."""
    print("\n=== Trend Analysis ===\n")

    collector = MetricsCollector()

    # Simulate improving code quality over time
    print("Simulating 5 analysis runs with improving quality...\n")

    for i in range(5):
        # Gradually reduce violations
        violations = {
            "connascence": [
                {"severity": "critical", "type": "CoE", "weight": 1.0}
                for _ in range(max(1, 5 - i))  # Decreasing violations
            ],
            "duplication": [
                {"similarity_score": 0.8, "functions": ["f1", "f2"]}
                for _ in range(max(1, 3 - i))  # Decreasing duplication
            ],
            "nasa": [
                {"severity": "high", "context": {"nasa_rule": "Rule4"}}
                for _ in range(max(1, 4 - i))  # Decreasing NASA violations
            ]
        }

        metrics = collector.collect_violation_metrics(violations)
        snapshot = collector.create_snapshot(metrics)

        print(f"Run {i+1}: Quality={snapshot.overall_quality_score:.3f}, "
              f"Violations={snapshot.total_violations}")

    # Get trend analysis
    print("\nTrend Analysis Results:")
    trends = collector.get_trend_analysis()

    print(f"  Overall Trend: {trends['trend']}")
    print(f"  Direction: {trends['direction']}")
    print(f"  Quality Change: {trends['quality_change']:.3f}")
    print(f"  Violation Change: {trends['violation_change']}")
    print(f"  Analysis: {trends['analysis']}")


def example_baseline_comparison():
    """Baseline comparison example."""
    print("\n=== Baseline Comparison ===\n")

    collector = MetricsCollector()

    # Set baseline with initial code quality
    baseline_violations = {
        "connascence": [
            {"severity": "high", "type": "CoE", "weight": 1.0}
            for _ in range(10)
        ],
        "duplication": [
            {"similarity_score": 0.75, "functions": ["f1", "f2"]}
            for _ in range(5)
        ],
        "nasa": [
            {"severity": "medium", "context": {"nasa_rule": "Rule5"}}
            for _ in range(8)
        ]
    }

    baseline_metrics = collector.collect_violation_metrics(baseline_violations)
    collector.set_baseline(baseline_metrics)

    print(f"Baseline Quality Score: {baseline_metrics['overall_quality_score']:.3f}")
    print(f"Baseline Total Violations: {baseline_metrics['total_violations']}")

    # Simulate improved code
    improved_violations = {
        "connascence": [
            {"severity": "medium", "type": "CoN", "weight": 1.0}
            for _ in range(5)  # Reduced and less severe
        ],
        "duplication": [
            {"similarity_score": 0.6, "functions": ["f1", "f2"]}
            for _ in range(2)  # Reduced
        ],
        "nasa": [
            {"severity": "low", "context": {"nasa_rule": "Rule7"}}
            for _ in range(4)  # Reduced and less severe
        ]
    }

    improved_metrics = collector.collect_violation_metrics(improved_violations)
    collector.create_snapshot(improved_metrics)

    print(f"\nImproved Quality Score: {improved_metrics['overall_quality_score']:.3f}")
    print(f"Improved Total Violations: {improved_metrics['total_violations']}")

    # Compare with baseline
    comparison = collector.get_baseline_comparison()

    print("\nBaseline Comparison:")
    print(f"  Quality Delta: {comparison['quality_delta']:+.3f}")
    print(f"  Violation Delta: {comparison['violation_delta']:+d}")
    print(f"  NASA Score Delta: {comparison['nasa_delta']:+.3f}")
    print(f"  Duplication Score Delta: {comparison['duplication_delta']:+.3f}")
    print(f"  Status: {comparison['status']}")


def example_metrics_summary():
    """Comprehensive metrics summary example."""
    print("\n=== Comprehensive Metrics Summary ===\n")

    collector = MetricsCollector()

    # Run several analyses
    for i in range(3):
        violations = {
            "connascence": [
                {"severity": "high", "type": "CoE", "weight": 1.0}
                for _ in range(5 - i)
            ],
            "duplication": [
                {"similarity_score": 0.7, "functions": ["f1", "f2"]}
            ],
            "nasa": [
                {"severity": "medium", "context": {"nasa_rule": "Rule5"}}
                for _ in range(3)
            ]
        }

        metrics = collector.collect_violation_metrics(violations)
        collector.create_snapshot(metrics)
        collector.track_performance(analysis_time=1.5, file_count=50)

    # Get comprehensive summary
    summary = collector.get_metrics_summary()

    print(f"Current Quality: {summary['current_quality']:.3f}")
    print(f"Total Violations: {summary['total_violations']}")
    print(f"High Priority Violations: {summary['high_priority_violations']}")
    print(f"Analysis Count: {summary['analysis_count']}")
    print(f"History Size: {summary['history_size']}")

    print("\nTrend Information:")
    trend = summary['trend']
    print(f"  Overall Trend: {trend['trend']}")
    print(f"  Direction: {trend['direction']}")


def example_export_history():
    """Metrics history export example."""
    print("\n=== Metrics History Export ===\n")

    collector = MetricsCollector()

    # Create multiple snapshots
    for i in range(3):
        violations = {
            "connascence": [
                {"severity": "high", "type": "CoE", "weight": 1.0}
            ],
            "duplication": [],
            "nasa": []
        }

        metrics = collector.collect_violation_metrics(violations)
        metrics["files_analyzed"] = 50 + i * 10
        collector.create_snapshot(metrics)

    # Export history
    history = collector.export_metrics_history()

    print(f"Exported {len(history)} snapshots:\n")

    for i, snapshot in enumerate(history, 1):
        print(f"Snapshot {i}:")
        print(f"  Quality Score: {snapshot['quality_score']:.3f}")
        print(f"  Violations: {snapshot['violations']}")
        print(f"  Files Analyzed: {snapshot['files_analyzed']}")
        print(f"  Timestamp: {snapshot['timestamp']}")
        print()


def main():
    """Run all examples."""
    example_basic_usage()
    example_quality_scoring()
    example_performance_tracking()
    example_trend_analysis()
    example_baseline_comparison()
    example_metrics_summary()
    example_export_history()

    print("\n" + "="*60)
    print("All examples completed successfully!")
    print("="*60)


if __name__ == "__main__":
    main()
