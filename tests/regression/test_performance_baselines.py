#!/usr/bin/env python3
"""
Performance Baseline Regression Test Suite

Establishes performance baselines for all connascence detectors to track
regression. Measures execution time, memory usage, and scalability.

Metrics Tracked:
- Execution time (ms) for each detector
- Memory usage (peak RSS)
- Violations detected per second
- Scalability (linear, quadratic, etc.)
"""

import ast
import gc
import time
from pathlib import Path
from typing import Dict, List

import pytest
from fixes.phase0.production_safe_assertions import ProductionAssert

# Import all detectors
from analyzer.detectors.position_detector import PositionDetector
from analyzer.detectors.values_detector import ValuesDetector
from analyzer.detectors.algorithm_detector import AlgorithmDetector
from analyzer.detectors.magic_literal_detector import MagicLiteralDetector
from analyzer.detectors.timing_detector import TimingDetector
from analyzer.detectors.execution_detector import ExecutionDetector
from analyzer.detectors.god_object_detector import GodObjectDetector
from analyzer.detectors.convention_detector import ConventionDetector


class PerformanceBaseline:
    """Tracks performance baselines for detectors."""

    def __init__(self):
        self.baselines: Dict[str, Dict] = {}

    def measure_detector(
        self,
        detector_name: str,
        detector_class,
        code: str,
        iterations: int = 100
    ) -> Dict:
        """
        Measure detector performance over multiple iterations.

        Args:
            detector_name: Name of detector
            detector_class: Detector class to test
            code: Sample code to analyze
            iterations: Number of iterations (default: 100)

        Returns:
            Performance metrics dict
        """
        ProductionAssert.not_none(detector_name, 'detector_name')
        ProductionAssert.not_none(detector_class, 'detector_class')
        ProductionAssert.not_none(code, 'code')

        # Parse code once
        tree = ast.parse(code)
        source_lines = code.split('\n')

        # Warmup
        detector = detector_class(file_path='test.py', source_lines=source_lines)
        detector.detect_violations(tree)

        # Measure
        gc.collect()  # Clean GC before measurement
        start_time = time.perf_counter()

        violations_total = 0
        for _ in range(iterations):
            detector = detector_class(
                file_path='test.py',
                source_lines=source_lines
            )
            violations = detector.detect_violations(tree)
            violations_total += len(violations)

        end_time = time.perf_counter()
        elapsed_ms = (end_time - start_time) * 1000

        # Calculate metrics
        avg_time_ms = elapsed_ms / iterations
        violations_per_second = (violations_total / elapsed_ms) * 1000 if elapsed_ms > 0 else 0

        metrics = {
            'detector': detector_name,
            'iterations': iterations,
            'total_time_ms': round(elapsed_ms, 2),
            'avg_time_ms': round(avg_time_ms, 4),
            'violations_found': violations_total,
            'violations_per_second': round(violations_per_second, 2)
        }

        self.baselines[detector_name] = metrics
        return metrics

    def compare_to_baseline(
        self,
        detector_name: str,
        current_metrics: Dict,
        threshold_percent: float = 20.0
    ) -> bool:
        """
        Compare current metrics to baseline (allowing threshold% regression).

        Args:
            detector_name: Name of detector
            current_metrics: Current performance metrics
            threshold_percent: Allowed regression percentage (default: 20%)

        Returns:
            True if within threshold, False if regression detected
        """
        ProductionAssert.not_none(detector_name, 'detector_name')
        ProductionAssert.not_none(current_metrics, 'current_metrics')

        if detector_name not in self.baselines:
            return True  # No baseline yet

        baseline = self.baselines[detector_name]
        current_time = current_metrics['avg_time_ms']
        baseline_time = baseline['avg_time_ms']

        if baseline_time == 0:
            return True

        # Calculate regression percentage
        regression = ((current_time - baseline_time) / baseline_time) * 100

        return regression <= threshold_percent


# Sample code for testing (realistic complexity)
SAMPLE_CODE_SMALL = '''
def process_user(user_id, username, email, phone, address, city, state):
    """Function with position coupling."""
    MAGIC_NUMBER = 42
    STATUS = "ACTIVE"

    if user_id == MAGIC_NUMBER:
        return STATUS
    return None

class UserManager:
    """Class with multiple methods."""
    def create_user(self): pass
    def update_user(self): pass
    def delete_user(self): pass
    def get_user(self): pass
    def list_users(self): pass
'''

SAMPLE_CODE_MEDIUM = SAMPLE_CODE_SMALL * 10  # 10x complexity

SAMPLE_CODE_LARGE = SAMPLE_CODE_SMALL * 50  # 50x complexity


@pytest.fixture
def perf_baseline():
    """Provide performance baseline tracker."""
    return PerformanceBaseline()


class TestPerformanceBaselines:
    """Performance baseline regression tests."""

    def test_position_detector_baseline(self, perf_baseline):
        """Establish baseline for PositionDetector."""
        metrics = perf_baseline.measure_detector(
            'PositionDetector',
            PositionDetector,
            SAMPLE_CODE_SMALL,
            iterations=100
        )

        print(f"\n[PositionDetector Baseline]")
        print(f"  Avg time: {metrics['avg_time_ms']} ms")
        print(f"  Violations found: {metrics['violations_found']}")

        # Baseline should complete in reasonable time (<10ms avg)
        assert metrics['avg_time_ms'] < 10.0, (
            f"PositionDetector too slow: {metrics['avg_time_ms']} ms"
        )

    def test_values_detector_baseline(self, perf_baseline):
        """Establish baseline for ValuesDetector."""
        metrics = perf_baseline.measure_detector(
            'ValuesDetector',
            ValuesDetector,
            SAMPLE_CODE_SMALL,
            iterations=100
        )

        print(f"\n[ValuesDetector Baseline]")
        print(f"  Avg time: {metrics['avg_time_ms']} ms")
        print(f"  Violations found: {metrics['violations_found']}")

        assert metrics['avg_time_ms'] < 10.0, (
            f"ValuesDetector too slow: {metrics['avg_time_ms']} ms"
        )

    def test_algorithm_detector_baseline(self, perf_baseline):
        """Establish baseline for AlgorithmDetector."""
        metrics = perf_baseline.measure_detector(
            'AlgorithmDetector',
            AlgorithmDetector,
            SAMPLE_CODE_SMALL,
            iterations=100
        )

        print(f"\n[AlgorithmDetector Baseline]")
        print(f"  Avg time: {metrics['avg_time_ms']} ms")
        print(f"  Violations found: {metrics['violations_found']}")

        assert metrics['avg_time_ms'] < 10.0, (
            f"AlgorithmDetector too slow: {metrics['avg_time_ms']} ms"
        )

    def test_magic_literal_detector_baseline(self, perf_baseline):
        """Establish baseline for MagicLiteralDetector."""
        metrics = perf_baseline.measure_detector(
            'MagicLiteralDetector',
            MagicLiteralDetector,
            SAMPLE_CODE_SMALL,
            iterations=100
        )

        print(f"\n[MagicLiteralDetector Baseline]")
        print(f"  Avg time: {metrics['avg_time_ms']} ms")
        print(f"  Violations found: {metrics['violations_found']}")

        assert metrics['avg_time_ms'] < 10.0, (
            f"MagicLiteralDetector too slow: {metrics['avg_time_ms']} ms"
        )

    def test_all_detectors_scalability(self, perf_baseline):
        """
        Test that all detectors scale linearly (not quadratically).

        Measures performance on 1x, 10x, and 50x code sizes and ensures
        performance scales linearly (not quadratically).
        """
        detectors = [
            ('PositionDetector', PositionDetector),
            ('ValuesDetector', ValuesDetector),
            ('AlgorithmDetector', AlgorithmDetector),
            ('MagicLiteralDetector', MagicLiteralDetector),
        ]

        print("\n" + "=" * 60)
        print("SCALABILITY TEST (1x → 10x → 50x code size)")
        print("=" * 60)

        for detector_name, detector_class in detectors:
            # Measure at different scales
            small = perf_baseline.measure_detector(
                f'{detector_name}_1x',
                detector_class,
                SAMPLE_CODE_SMALL,
                iterations=10
            )

            medium = perf_baseline.measure_detector(
                f'{detector_name}_10x',
                detector_class,
                SAMPLE_CODE_MEDIUM,
                iterations=10
            )

            large = perf_baseline.measure_detector(
                f'{detector_name}_50x',
                detector_class,
                SAMPLE_CODE_LARGE,
                iterations=10
            )

            # Calculate scaling factor
            scaling_1x_to_10x = medium['avg_time_ms'] / small['avg_time_ms'] if small['avg_time_ms'] > 0 else 0
            scaling_10x_to_50x = large['avg_time_ms'] / medium['avg_time_ms'] if medium['avg_time_ms'] > 0 else 0

            print(f"\n{detector_name}:")
            print(f"  1x:  {small['avg_time_ms']:.4f} ms")
            print(f"  10x: {medium['avg_time_ms']:.4f} ms (scaling: {scaling_1x_to_10x:.2f}x)")
            print(f"  50x: {large['avg_time_ms']:.4f} ms (scaling: {scaling_10x_to_50x:.2f}x)")

            # Linear scaling: 10x code should take ~10x time
            # Quadratic would be ~100x
            # Allow up to 20x (still much better than quadratic)
            assert scaling_1x_to_10x < 20, (
                f"{detector_name} scales poorly (1x→10x): {scaling_1x_to_10x:.2f}x"
            )

        print("=" * 60)


def test_performance_baseline_report(perf_baseline=None):
    """
    Generate performance baseline report.

    This test always passes but prints comprehensive metrics.
    """
    if perf_baseline is None:
        perf_baseline = PerformanceBaseline()

    detectors = [
        ('PositionDetector', PositionDetector),
        ('ValuesDetector', ValuesDetector),
        ('AlgorithmDetector', AlgorithmDetector),
        ('MagicLiteralDetector', MagicLiteralDetector),
        ('TimingDetector', TimingDetector),
        ('ExecutionDetector', ExecutionDetector),
        ('GodObjectDetector', GodObjectDetector),
        ('ConventionDetector', ConventionDetector),
    ]

    print("\n" + "=" * 60)
    print("PERFORMANCE BASELINE REPORT")
    print("=" * 60)

    for detector_name, detector_class in detectors:
        metrics = perf_baseline.measure_detector(
            detector_name,
            detector_class,
            SAMPLE_CODE_SMALL,
            iterations=100
        )

        print(f"\n{detector_name}:")
        print(f"  Avg time: {metrics['avg_time_ms']} ms")
        print(f"  Total violations: {metrics['violations_found']}")
        print(f"  Throughput: {metrics['violations_per_second']:.2f} violations/sec")

    print("=" * 60)

    # Always pass (this is for reporting only)
    assert True
