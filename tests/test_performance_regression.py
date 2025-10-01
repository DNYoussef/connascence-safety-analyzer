#!/usr/bin/env python3
"""
Performance regression tests for connascence analyzer.

Tests Requirements:
1. Benchmark testing against baseline performance
2. Memory usage monitoring
3. Scalability testing with different codebase sizes
4. Performance comparison before/after enhancements
"""

import gc
from pathlib import Path
import time
from typing import Any, Dict, List

import psutil
import pytest

from analyzer.check_connascence import ConnascenceAnalyzer as LegacyAnalyzer
from analyzer.constants import MAX_ANALYSIS_TIME_SECONDS
from analyzer.core import ConnascenceAnalyzer


class PerformanceMonitor:
    """Helper class for monitoring performance metrics."""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None
        self.process = psutil.Process()

    def __enter__(self):
        """Start performance monitoring."""
        gc.collect()  # Clean up before measurement

        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End performance monitoring."""
        self.end_time = time.time()
        self.end_memory = self.process.memory_info().rss

    @property
    def execution_time(self) -> float:
        """Get execution time in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

    @property
    def memory_delta(self) -> int:
        """Get memory usage delta in bytes."""
        if self.start_memory and self.end_memory:
            return self.end_memory - self.start_memory
        return 0

    @property
    def memory_delta_mb(self) -> float:
        """Get memory usage delta in MB."""
        return self.memory_delta / (1024 * 1024)


class TestPerformanceRegression:
    """Performance regression tests for the analyzer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.project_root = Path(__file__).parent.parent
        self.analyzer = ConnascenceAnalyzer()
        self.legacy_analyzer = LegacyAnalyzer()

        # Performance thresholds (adjust based on baseline measurements)
        self.performance_thresholds = {
            "small_file_time": 2.0,  # seconds for small file (< 100 lines)
            "medium_file_time": 5.0,  # seconds for medium file (100-500 lines)
            "large_file_time": 15.0,  # seconds for large file (500+ lines)
            "directory_time": 30.0,  # seconds for directory analysis
            "memory_limit_mb": 100.0,  # MB memory increase limit
            "files_per_second": 1.0,  # minimum files processed per second
        }

    def test_small_file_performance(self):
        """Test performance on small files."""
        small_file_code = '''
def simple_function():
    """A simple function for testing."""
    magic_number = 42  # Should trigger violation
    return magic_number * 2

class SimpleClass:
    """A simple class for testing."""

    def __init__(self):
        self.value = 10

    def get_value(self):
        return self.value

    def set_value(self, value):
        self.value = value
'''

        with PerformanceMonitor() as monitor:
            violations = self._analyze_code_string(small_file_code)

        # Performance assertions
        assert (
            monitor.execution_time < self.performance_thresholds["small_file_time"]
        ), f"Small file analysis too slow: {monitor.execution_time:.3f}s"

        assert (
            monitor.memory_delta_mb < self.performance_thresholds["memory_limit_mb"]
        ), f"Memory usage too high: {monitor.memory_delta_mb:.2f}MB"

        # Should find violations quickly
        assert len(violations) > 0, "Should find at least one violation"

        print(f"Small file performance: {monitor.execution_time:.3f}s, {monitor.memory_delta_mb:.2f}MB")

    def test_medium_file_performance(self):
        """Test performance on medium-sized files."""
        # Generate a medium-sized file (100-200 lines)
        medium_file_code = self._generate_test_code(lines=150)

        with PerformanceMonitor() as monitor:
            self._analyze_code_string(medium_file_code)

        # Performance assertions
        assert (
            monitor.execution_time < self.performance_thresholds["medium_file_time"]
        ), f"Medium file analysis too slow: {monitor.execution_time:.3f}s"

        assert (
            monitor.memory_delta_mb < self.performance_thresholds["memory_limit_mb"]
        ), f"Memory usage too high: {monitor.memory_delta_mb:.2f}MB"

        print(f"Medium file performance: {monitor.execution_time:.3f}s, {monitor.memory_delta_mb:.2f}MB")

    def test_large_file_performance(self):
        """Test performance on large files."""
        # Generate a large file (500+ lines)
        large_file_code = self._generate_test_code(lines=600)

        with PerformanceMonitor() as monitor:
            self._analyze_code_string(large_file_code)

        # Performance assertions
        assert (
            monitor.execution_time < self.performance_thresholds["large_file_time"]
        ), f"Large file analysis too slow: {monitor.execution_time:.3f}s"

        assert (
            monitor.memory_delta_mb < self.performance_thresholds["memory_limit_mb"]
        ), f"Memory usage too high: {monitor.memory_delta_mb:.2f}MB"

        print(f"Large file performance: {monitor.execution_time:.3f}s, {monitor.memory_delta_mb:.2f}MB")

    def test_directory_analysis_performance(self):
        """Test performance on directory analysis."""
        analyzer_dir = self.project_root / "analyzer"

        if not analyzer_dir.exists():
            pytest.skip("Analyzer directory not found")

        with PerformanceMonitor() as monitor:
            result = self.analyzer.analyze_path(path=str(analyzer_dir), policy="standard")

        # Performance assertions
        assert (
            monitor.execution_time < self.performance_thresholds["directory_time"]
        ), f"Directory analysis too slow: {monitor.execution_time:.3f}s"

        # Calculate files per second
        files_analyzed = result.get("metrics", {}).get("files_analyzed", 1)
        files_per_second = files_analyzed / monitor.execution_time if monitor.execution_time > 0 else 0

        assert (
            files_per_second >= self.performance_thresholds["files_per_second"]
        ), f"Processing rate too slow: {files_per_second:.2f} files/second"

        print("Directory analysis performance:")
        print(f"  Time: {monitor.execution_time:.3f}s")
        print(f"  Memory: {monitor.memory_delta_mb:.2f}MB")
        print(f"  Files: {files_analyzed}")
        print(f"  Rate: {files_per_second:.2f} files/second")

    def test_memory_scalability(self):
        """Test memory usage scaling with different file sizes."""
        memory_measurements = []

        # Test different file sizes
        file_sizes = [50, 100, 200, 400, 800]

        for size in file_sizes:
            test_code = self._generate_test_code(lines=size)

            with PerformanceMonitor() as monitor:
                violations = self._analyze_code_string(test_code)

            memory_measurements.append(
                {
                    "lines": size,
                    "time": monitor.execution_time,
                    "memory_mb": monitor.memory_delta_mb,
                    "violations": len(violations),
                }
            )

        # Check that memory usage doesn't grow excessively
        for measurement in memory_measurements:
            assert (
                measurement["memory_mb"] < self.performance_thresholds["memory_limit_mb"]
            ), f"Memory usage too high for {measurement['lines']} lines: {measurement['memory_mb']:.2f}MB"

        # Print memory scaling results
        print("Memory scalability results:")
        for m in memory_measurements:
            print(
                f"  {m['lines']:3d} lines: {m['time']:.3f}s, {m['memory_mb']:5.2f}MB, {m['violations']:3d} violations"
            )

    def test_performance_constants_compliance(self):
        """Test compliance with performance constants from constants.py."""
        analyzer_dir = self.project_root / "analyzer"

        if not analyzer_dir.exists():
            pytest.skip("Analyzer directory not found")

        with PerformanceMonitor() as monitor:
            result = self.analyzer.analyze_path(path=str(analyzer_dir), policy="standard")

        # Check against MAX_ANALYSIS_TIME_SECONDS
        assert (
            monitor.execution_time < MAX_ANALYSIS_TIME_SECONDS
        ), f"Analysis exceeded maximum time: {monitor.execution_time}s > {MAX_ANALYSIS_TIME_SECONDS}s"

        # Verify no files over MAX_FILE_SIZE_KB were processed
        # (This would be logged/tracked by the analyzer)
        assert result["success"] is True, "Analysis should succeed within time limits"

    def test_concurrent_analysis_performance(self):
        """Test performance of concurrent analysis operations."""
        import concurrent.futures

        # Create multiple small analysis tasks
        test_codes = [self._generate_test_code(lines=50) for _ in range(5)]

        def analyze_code(code):
            return self._analyze_code_string(code)

        # Test sequential execution
        with PerformanceMonitor() as sequential_monitor:
            [analyze_code(code) for code in test_codes]

        # Test concurrent execution
        with PerformanceMonitor() as concurrent_monitor:
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                list(executor.map(analyze_code, test_codes))

        # Concurrent should not be significantly slower than sequential
        # (and might be faster for I/O bound operations)
        time_ratio = concurrent_monitor.execution_time / sequential_monitor.execution_time

        # Should not be more than 2x slower (allowing for overhead)
        assert time_ratio < 2.0, f"Concurrent execution too slow: {time_ratio:.2f}x"

        print("Concurrency performance:")
        print(f"  Sequential: {sequential_monitor.execution_time:.3f}s")
        print(f"  Concurrent: {concurrent_monitor.execution_time:.3f}s")
        print(f"  Ratio: {time_ratio:.2f}x")

    def test_memory_cleanup_after_analysis(self):
        """Test that memory is properly cleaned up after analysis."""
        initial_memory = psutil.Process().memory_info().rss

        # Run several analysis operations
        for i in range(10):
            test_code = self._generate_test_code(lines=200)
            self._analyze_code_string(test_code)

        # Force garbage collection
        gc.collect()

        final_memory = psutil.Process().memory_info().rss
        memory_increase = (final_memory - initial_memory) / (1024 * 1024)  # MB

        # Memory increase should be minimal after cleanup
        assert memory_increase < 50.0, f"Memory not properly cleaned up: {memory_increase:.2f}MB increase"

        print(f"Memory cleanup test: {memory_increase:.2f}MB net increase")

    def test_analysis_caching_performance(self):
        """Test performance benefits of any internal caching."""
        test_code = self._generate_test_code(lines=300)

        # First analysis (cold)
        with PerformanceMonitor() as cold_monitor:
            violations1 = self._analyze_code_string(test_code)

        # Second analysis (potentially warm cache)
        with PerformanceMonitor() as warm_monitor:
            violations2 = self._analyze_code_string(test_code)

        # Results should be identical
        assert len(violations1) == len(violations2), "Cached results should be identical"

        # Warm analysis should not be significantly slower
        if warm_monitor.execution_time > cold_monitor.execution_time * 2:
            pytest.fail(
                f"Warm analysis unexpectedly slow: {warm_monitor.execution_time:.3f}s vs {cold_monitor.execution_time:.3f}s"
            )

        print("Caching performance:")
        print(f"  Cold: {cold_monitor.execution_time:.3f}s")
        print(f"  Warm: {warm_monitor.execution_time:.3f}s")

    def test_large_violation_count_performance(self):
        """Test performance when many violations are found."""
        # Generate code with many intentional violations
        violation_heavy_code = """
def violation_heavy_function():
    # Many magic numbers
    a = 42
    b = 73
    c = 123
    d = 456
    e = 789
    f = 999
    g = 1234
    h = 5678

    # Many parameters (position coupling)
    def many_params(p1, p2, p3, p4, p5, p6, p7, p8, p9, p10):
        return p1 + p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9 + p10

    return a + b + c + d + e + f + g + h + many_params(1,2,3,4,5,6,7,8,9,10)

class ViolationHeavyClass:
    def method1(self): pass
    def method2(self): pass
    def method3(self): pass
    def method4(self): pass
    def method5(self): pass
    def method6(self): pass
    def method7(self): pass
    def method8(self): pass
    def method9(self): pass
    def method10(self): pass
    def method11(self): pass
    def method12(self): pass
    def method13(self): pass
    def method14(self): pass
    def method15(self): pass
    def method16(self): pass
    def method17(self): pass
    def method18(self): pass
    def method19(self): pass
    def method20(self): pass
    def method21(self): pass
    def method22(self): pass
    def method23(self): pass
"""

        with PerformanceMonitor() as monitor:
            violations = self._analyze_code_string(violation_heavy_code)

        # Should handle many violations efficiently
        assert monitor.execution_time < 5.0, f"High-violation analysis too slow: {monitor.execution_time:.3f}s"
        assert len(violations) > 10, "Should find many violations in violation-heavy code"

        print(f"High-violation performance: {monitor.execution_time:.3f}s, {len(violations)} violations")

    def _analyze_code_string(self, code: str) -> List[Dict[str, Any]]:
        """Helper method to analyze code string using legacy analyzer."""
        import ast

        from analyzer.check_connascence import ConnascenceDetector

        source_lines = code.splitlines()
        tree = ast.parse(code)
        detector = ConnascenceDetector("test_file.py", source_lines)
        detector.visit(tree)
        detector.finalize_analysis()
        return [self._violation_to_dict(v) for v in detector.violations]

    def _violation_to_dict(self, violation) -> Dict[str, Any]:
        """Convert violation to dictionary."""
        return {
            "type": violation.type,
            "severity": violation.severity,
            "file_path": violation.file_path,
            "line_number": violation.line_number,
            "description": violation.description,
        }

    def _generate_test_code(self, lines: int) -> str:
        """Generate test code with specified number of lines."""
        code_lines = [
            "# Generated test code",
            "import os",
            "import sys",
            "",
            "class TestClass:",
            '    """A test class for performance testing."""',
            "    ",
            "    def __init__(self):",
            "        self.value = 0",
            "",
        ]

        # Add methods to reach desired line count
        method_template = '''    def method_{i}(self):
        """Method {i} for testing."""
        magic_num = {magic}  # Magic number violation
        return magic_num * 2
    '''

        i = 1
        while len(code_lines) < lines:
            method_code = method_template.format(i=i, magic=42 + i).splitlines()
            code_lines.extend(method_code)
            code_lines.append("")
            i += 1

        return "\n".join(code_lines[:lines])


class TestPerformanceBenchmarks:
    """Benchmark tests to establish performance baselines."""

    def setup_method(self):
        """Set up benchmark fixtures."""
        self.project_root = Path(__file__).parent.parent
        self.analyzer = ConnascenceAnalyzer()

    def test_baseline_benchmark_small_project(self):
        """Establish baseline performance for small projects."""
        # Use a small subset of the analyzer code
        test_files = [self.project_root / "analyzer" / "constants.py", self.project_root / "analyzer" / "thresholds.py"]

        existing_files = [f for f in test_files if f.exists()]
        if not existing_files:
            pytest.skip("Benchmark files not found")

        total_time = 0.0
        total_violations = 0

        for file_path in existing_files:
            with PerformanceMonitor() as monitor:
                result = self.analyzer.analyze_path(str(file_path), policy="standard")

            total_time += monitor.execution_time
            total_violations += len(result.get("violations", []))

        avg_time_per_file = total_time / len(existing_files)

        print("Small project benchmark:")
        print(f"  Files: {len(existing_files)}")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Avg per file: {avg_time_per_file:.3f}s")
        print(f"  Total violations: {total_violations}")

        # Record baseline (adjust these based on actual measurements)
        assert avg_time_per_file < 3.0, f"Baseline performance regression: {avg_time_per_file:.3f}s per file"

    def test_baseline_benchmark_medium_project(self):
        """Establish baseline performance for medium projects."""
        analyzer_dir = self.project_root / "analyzer"

        if not analyzer_dir.exists():
            pytest.skip("Analyzer directory not found")

        with PerformanceMonitor() as monitor:
            result = self.analyzer.analyze_path(str(analyzer_dir), policy="standard")

        files_analyzed = result.get("metrics", {}).get("files_analyzed", 1)
        violations_found = len(result.get("violations", []))

        print("Medium project benchmark:")
        print(f"  Analysis time: {monitor.execution_time:.3f}s")
        print(f"  Files analyzed: {files_analyzed}")
        print(f"  Violations found: {violations_found}")
        print(f"  Time per file: {monitor.execution_time/files_analyzed:.3f}s")
        print(f"  Memory used: {monitor.memory_delta_mb:.2f}MB")

        # Record baseline
        assert monitor.execution_time < 60.0, f"Baseline performance regression: {monitor.execution_time:.3f}s"
        assert files_analyzed > 5, f"Expected to analyze more files: {files_analyzed}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
