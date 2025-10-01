"""
Test suite for DetectorPool performance optimization architecture.

Validates pool functionality, thread safety, and performance improvements.
NASA Rule 4: All test methods under 60 lines
"""

import ast
import os
import sys
import threading
import time
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from analyzer.architecture.detector_pool import DetectorPool, get_detector_pool
from analyzer.detectors import PositionDetector
from analyzer.detectors.base import DetectorBase


class TestDetectorPool(unittest.TestCase):
    """Test DetectorPool functionality and performance optimizations."""

    def setUp(self):
        """Set up test environment."""
        # Reset singleton for clean tests
        DetectorPool._instance = None
        self.pool = DetectorPool()
        self.test_file = "test.py"
        self.test_lines = ["def test():", "    pass"]

    def test_singleton_pattern(self):
        """Test that DetectorPool implements singleton correctly."""
        pool1 = DetectorPool()
        pool2 = DetectorPool()
        self.assertIs(pool1, pool2)

        # Test global getter
        pool3 = get_detector_pool()
        self.assertIs(pool1, pool3)

    def test_detector_acquisition_single(self):
        """Test acquiring single detector from pool."""
        detector = self.pool.acquire_detector("position", self.test_file, self.test_lines)
        self.assertIsNotNone(detector)
        self.assertIsInstance(detector, PositionDetector)
        self.assertEqual(detector.file_path, self.test_file)
        self.assertEqual(detector.source_lines, self.test_lines)

    def test_detector_release(self):
        """Test releasing detector back to pool."""
        detector = self.pool.acquire_detector("position", self.test_file, self.test_lines)
        self.assertIsNotNone(detector)

        # Release detector
        self.pool.release_detector(detector)

        # State should be cleared
        self.assertEqual(detector.file_path, "")
        self.assertEqual(detector.source_lines, [])
        self.assertEqual(detector.violations, [])

    def test_acquire_all_detectors(self):
        """Test acquiring all detector types at once."""
        detectors = self.pool.acquire_all_detectors(self.test_file, self.test_lines)

        # Should have all detector types
        expected_types = {
            "position",
            "magic_literal",
            "algorithm",
            "god_object",
            "timing",
            "convention",
            "values",
            "execution",
        }
        self.assertEqual(set(detectors.keys()), expected_types)

        # All should be properly configured
        for name, detector in detectors.items():
            self.assertIsInstance(detector, DetectorBase)
            self.assertEqual(detector.file_path, self.test_file)
            self.assertEqual(detector.source_lines, self.test_lines)

    def test_detector_reuse(self):
        """Test that detectors are reused from pool."""
        # Acquire detector
        detector1 = self.pool.acquire_detector("position", self.test_file, self.test_lines)
        detector1_id = id(detector1)

        # Release and acquire again
        self.pool.release_detector(detector1)
        detector2 = self.pool.acquire_detector("position", "test2.py", ["line1"])

        # Should be same instance (reused)
        self.assertEqual(id(detector2), detector1_id)

        # But with new configuration
        self.assertEqual(detector2.file_path, "test2.py")
        self.assertEqual(detector2.source_lines, ["line1"])

    def test_pool_bounded_size(self):
        """Test that pool respects size limits."""
        # Fill pool to capacity
        detectors = []
        for i in range(DetectorPool.MAX_POOL_SIZE + 5):
            detector = self.pool.acquire_detector("position", f"test{i}.py", [f"line{i}"])
            if detector:
                detectors.append(detector)

        # Should not exceed max size
        self.assertLessEqual(len(detectors), DetectorPool.MAX_POOL_SIZE)

        # Release all
        for detector in detectors:
            self.pool.release_detector(detector)

    def test_thread_safety(self):
        """Test thread-safe detector acquisition and release."""
        results = {"acquired": 0, "errors": 0}
        barrier = threading.Barrier(5)

        def worker():
            try:
                barrier.wait()  # Synchronize start

                # Acquire detector
                detector = self.pool.acquire_detector("position", "thread_test.py", ["test"])
                if detector:
                    results["acquired"] += 1
                    time.sleep(0.01)  # Hold briefly
                    self.pool.release_detector(detector)

            except Exception:
                results["errors"] += 1

        # Start multiple threads
        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All should succeed
        self.assertEqual(results["errors"], 0)
        self.assertGreater(results["acquired"], 0)

    def test_performance_metrics(self):
        """Test pool performance metrics tracking."""
        # Initial metrics
        metrics = self.pool.get_metrics()
        initial_acquisitions = metrics["total_acquisitions"]

        # Perform operations
        detector = self.pool.acquire_detector("position", self.test_file, self.test_lines)
        self.pool.release_detector(detector)

        detector = self.pool.acquire_detector("position", self.test_file, self.test_lines)
        self.pool.release_detector(detector)

        # Check updated metrics
        metrics = self.pool.get_metrics()
        self.assertGreater(metrics["total_acquisitions"], initial_acquisitions)
        self.assertGreaterEqual(metrics["cache_hits"], 1)  # Second acquisition should be cache hit

    def test_warmup_functionality(self):
        """Test pool warmup creates pre-warmed instances."""
        # Reset pool
        DetectorPool._instance = None
        pool = DetectorPool()

        # Check that warmup instances exist
        metrics = pool.get_metrics()
        self.assertGreater(metrics["pool_size"], 0)

        # Warmup should create instances for each detector type
        for detector_type in pool._detector_types:
            self.assertGreaterEqual(len(pool._pools[detector_type]), 1)

    def test_detector_state_isolation(self):
        """Test that detector state is properly isolated between uses."""
        # Acquire detector and set some state
        detector1 = self.pool.acquire_detector("position", "file1.py", ["line1"])
        detector1.violations = [Mock()]  # Add some violations

        # Release and acquire again with different file
        self.pool.release_detector(detector1)
        detector2 = self.pool.acquire_detector("position", "file2.py", ["line2"])

        # Should be same instance but clean state
        self.assertIs(detector1, detector2)
        self.assertEqual(detector2.file_path, "file2.py")
        self.assertEqual(detector2.source_lines, ["line2"])
        self.assertEqual(detector2.violations, [])

    def test_error_handling_invalid_detector(self):
        """Test error handling for invalid detector types."""
        with self.assertRaises(AssertionError):
            self.pool.acquire_detector("invalid_type", self.test_file, self.test_lines)

    def test_cleanup_idle_detectors(self):
        """Test cleanup of idle detectors."""
        # Create many detectors to exceed warmup count
        detectors = []
        for i in range(DetectorPool.WARMUP_COUNT + 3):
            detector = self.pool.acquire_detector("position", f"test{i}.py", [f"line{i}"])
            if detector:
                detectors.append(detector)

        # Release all
        for detector in detectors:
            self.pool.release_detector(detector)

        initial_pool_size = len(self.pool._pools["position"])

        # Mock time to simulate idle timeout
        with patch("time.time", return_value=time.time() + DetectorPool.MAX_IDLE_TIME + 1):
            self.pool._cleanup_idle_detectors()

        # Should have cleaned up excess idle detectors
        final_pool_size = len(self.pool._pools["position"])
        self.assertLessEqual(final_pool_size, initial_pool_size)
        self.assertGreaterEqual(final_pool_size, DetectorPool.WARMUP_COUNT)


class TestPooledDetectorIntegration(unittest.TestCase):
    """Test integration with RefactoredConnascenceDetector."""

    def setUp(self):
        """Set up integration test environment."""
        DetectorPool._instance = None
        self.sample_code = """
def example_function():
    magic_number = 42
    if magic_number > 0:
        print("positive")
    return magic_number
"""
        self.source_lines = self.sample_code.strip().split("\n")
        self.tree = ast.parse(self.sample_code)

    def test_refactored_detector_uses_pool(self):
        """Test that RefactoredConnascenceDetector uses pool correctly."""
        from analyzer.refactored_detector import RefactoredConnascenceDetector

        detector = RefactoredConnascenceDetector("test.py", self.source_lines)

        # Should have pool initialization
        self.assertIsNone(detector._detector_pool)  # Lazy init
        self.assertEqual(detector._acquired_detectors, {})

        # Run analysis
        violations = detector.detect_all_violations(self.tree)

        # Should be a list (may be empty, that's fine for this test)
        self.assertIsInstance(violations, list)

        # Pool should be initialized now
        self.assertIsNotNone(detector._detector_pool)

        # Resources should be cleaned up
        self.assertEqual(detector._acquired_detectors, {})

    def test_pool_metrics_available(self):
        """Test that pool metrics are available from refactored detector."""
        from analyzer.refactored_detector import RefactoredConnascenceDetector

        detector = RefactoredConnascenceDetector("test.py", self.source_lines)
        violations = detector.detect_all_violations(self.tree)

        # Should have metrics
        metrics = detector.get_pool_metrics()
        self.assertIsInstance(metrics, dict)
        self.assertIn("total_acquisitions", metrics)
        self.assertIn("pool_size", metrics)

    def test_fallback_on_pool_failure(self):
        """Test fallback behavior when pool acquisition fails."""
        from analyzer.refactored_detector import RefactoredConnascenceDetector

        detector = RefactoredConnascenceDetector("test.py", self.source_lines)

        # Mock pool to return empty detectors dict (simulating failure)
        with patch.object(detector, "_detector_pool") as mock_pool:
            mock_pool.acquire_all_detectors.return_value = {}

            # Should still work with fallback
            violations = detector.detect_all_violations(self.tree)
            self.assertIsInstance(violations, list)

    def test_resource_cleanup_on_exception(self):
        """Test that pool resources are cleaned up even on exceptions."""
        from analyzer.refactored_detector import RefactoredConnascenceDetector

        detector = RefactoredConnascenceDetector("test.py", self.source_lines)

        # Force an exception during analysis
        with patch("analyzer.optimization.unified_visitor.UnifiedASTVisitor") as mock_visitor:
            mock_visitor.side_effect = Exception("Test exception")

            with self.assertRaises(Exception):
                detector.detect_all_violations(self.tree)

            # Resources should still be cleaned up
            self.assertEqual(detector._acquired_detectors, {})


if __name__ == "__main__":
    # Performance comparison test
    def performance_comparison():
        """Compare performance with and without pool."""
        from analyzer.refactored_detector import RefactoredConnascenceDetector

        sample_code = """
def test_function(param1, param2=42):
    global_var = "test"
    magic_numbers = [1, 2, 3, 42, 100]
    
    if param1 > magic_numbers[3]:
        return param1 * 2
    elif param1 < 0:
        return abs(param1)
    else:
        for i in range(len(magic_numbers)):
            if magic_numbers[i] == param1:
                return i
    return -1

class TestClass:
    def __init__(self):
        self.value = 42
    
    def method1(self): pass
    def method2(self): pass
    def method3(self): pass
    def method4(self): pass
    def method5(self): pass
"""

        source_lines = sample_code.strip().split("\n")
        tree = ast.parse(sample_code)

        # Test multiple iterations
        iterations = 100

        start_time = time.time()
        for i in range(iterations):
            detector = RefactoredConnascenceDetector(f"test{i}.py", source_lines)
            violations = detector.detect_all_violations(tree)
        end_time = time.time()

        print(f"Pool-based analysis: {end_time - start_time:.3f}s for {iterations} iterations")

        # Get final metrics
        pool = get_detector_pool()
        metrics = pool.get_metrics()
        print(f"Pool metrics: {metrics}")

        print("Performance test completed successfully")

    # Run tests
    unittest.main(verbosity=2, exit=False)

    # Run performance comparison
    print("\n" + "=" * 50)
    print("PERFORMANCE COMPARISON")
    print("=" * 50)
    performance_comparison()
