# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

"""
Performance benchmarks for the connascence analyzer.

Tests performance characteristics and ensures the system
meets performance requirements for various codebase sizes.
"""

import os
import time

import pytest

from analyzer.ast_engine.core_analyzer import ConnascenceASTAnalyzer
import psutil


class TestPerformanceBenchmarks:
    """Performance benchmarks for connascence analysis."""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_small_codebase_performance(self):
        """Test performance on small codebase (< 10 files)."""
        analyzer = ConnascenceASTAnalyzer()

        # Generate small codebase
        code_samples = []
        for i in range(8):
            code = f"""
def function_{i}(a, b, c):
    if a > {i * 10}:  # Magic literal
        return b + c + {i * 100}  # Magic literal
    return a * {i + 1}
"""
            code_samples.append((code, f"file_{i}.py"))

        # Measure analysis time
        start_time = time.time()
        start_memory = psutil.Process(os.getpid()).memory_info().rss

        all_violations = []
        for code, filename in code_samples:
            violations = analyzer.analyze_string(code, filename)
            all_violations.extend(violations)

        end_time = time.time()
        end_memory = psutil.Process(os.getpid()).memory_info().rss

        analysis_time = end_time - start_time
        memory_used = (end_memory - start_memory) / 1024 / 1024  # MB

        # Performance assertions
        assert analysis_time < 2.0, f"Small codebase analysis took {analysis_time:.2f}s (should be < 2s)"
        assert memory_used < 50, f"Used {memory_used:.2f}MB memory (should be < 50MB)"
        assert len(all_violations) > 0, "Should detect violations"

        # Log performance metrics
        print("\\nSmall codebase performance:")
        print(f"  Files: {len(code_samples)}")
        print(f"  Analysis time: {analysis_time:.2f}s")
        print(f"  Memory used: {memory_used:.2f}MB")
        print(f"  Violations found: {len(all_violations)}")
        print(f"  Violations per second: {len(all_violations) / analysis_time:.1f}")

    @pytest.mark.performance
    @pytest.mark.slow
    def test_medium_codebase_performance(self):
        """Test performance on medium codebase (50-100 files)."""
        analyzer = ConnascenceASTAnalyzer()

        # Generate medium codebase with more complex code
        code_samples = []
        for i in range(75):
            # Create more complex code with various violations
            code = f"""
class Service_{i}:
    def __init__(self):
        self.config = {{"timeout": {i * 10}}}  # Magic literal
        self.retries = {i % 5 + 1}  # Magic literal

    def process(self, data, options, flags, timeout, retries):  # Too many params
        if timeout > {i * 100}:  # Magic literal
            return self._handle_timeout(data, options, flags)
        return self._process_normal(data, options, flags, retries)

    def _handle_timeout(self, data, options, flags):  # Missing types
        if flags and len(data) > {i * 50}:  # Magic literal
            return "timeout_handled"  # Magic string
        return None

    def _process_normal(self, data, options, flags, retries):  # Missing types
        result = []
        for item in data:
            if item > {i * 20}:  # Magic literal
                result.append(item * {i + 1})  # Magic literal
        return result

def utility_function_{i}(param1, param2, param3, param4):  # Missing types, many params
    threshold = {i * 25}  # Magic literal
    if param1 > threshold:
        return param2 + param3 + param4 + {i * 5}  # Magic literal
    return param1 * 2
"""
            code_samples.append((code, f"service_{i}.py"))

        # Measure analysis time
        start_time = time.time()
        start_memory = psutil.Process(os.getpid()).memory_info().rss

        all_violations = []
        for code, filename in code_samples:
            violations = analyzer.analyze_string(code, filename)
            all_violations.extend(violations)

        end_time = time.time()
        end_memory = psutil.Process(os.getpid()).memory_info().rss

        analysis_time = end_time - start_time
        memory_used = (end_memory - start_memory) / 1024 / 1024  # MB

        # Performance assertions for medium codebase
        assert analysis_time < 10.0, f"Medium codebase analysis took {analysis_time:.2f}s (should be < 10s)"
        assert memory_used < 100, f"Used {memory_used:.2f}MB memory (should be < 100MB)"
        assert len(all_violations) > len(code_samples) * 3, "Should detect multiple violations per file"

        # Log performance metrics
        print("\\nMedium codebase performance:")
        print(f"  Files: {len(code_samples)}")
        print(f"  Analysis time: {analysis_time:.2f}s")
        print(f"  Memory used: {memory_used:.2f}MB")
        print(f"  Violations found: {len(all_violations)}")
        print(f"  Files per second: {len(code_samples) / analysis_time:.1f}")
        print(f"  Violations per second: {len(all_violations) / analysis_time:.1f}")

    @pytest.mark.performance
    @pytest.mark.slow
    def test_large_file_performance(self):
        """Test performance on single large file."""
        analyzer = ConnascenceASTAnalyzer()

        # Generate large Python file (500+ lines)
        code_parts = []

        # Large class with many methods (god class)
        code_parts.append(
            """
class LargeProcessor:
    def __init__(self):
        self.data = {}
        self.config = {"max_items": 1000}  # Magic literal
        self.status = "ready"
"""
        )

        # Generate many methods
        for i in range(50):
            method_code = f"""
    def method_{i}(self, param1, param2, param3, param4, param5):  # Too many params, missing types
        threshold = {i * 10}  # Magic literal
        if param1 > threshold:
            if param2 and param3:
                result = []
                for j in range({i + 5}):  # Magic literal
                    if j % 2 == 0:
                        result.append(j * {i * 2})  # Magic literal
                    else:
                        result.append(j + {i * 3})  # Magic literal
                return result
            else:
                return param4 + param5 + {i * 100}  # Magic literal
        return {i * 50}  # Magic literal
"""
            code_parts.append(method_code)

        # Add some module-level functions
        for i in range(25):
            func_code = f"""
def process_batch_{i}(items, config, options, timeout, retries, flags):  # Too many params, missing types
    if len(items) > {i * 20}:  # Magic literal
        processed = []
        for item in items:
            if item["value"] > {i * 100}:  # Magic literal
                processed.append(item["value"] * {i + 1})  # Magic literal
        return processed
    return []
"""
            code_parts.append(func_code)

        large_code = "\\n".join(code_parts)
        lines = large_code.count("\\n") + 1

        # Measure analysis time
        start_time = time.time()
        start_memory = psutil.Process(os.getpid()).memory_info().rss

        violations = analyzer.analyze_string(large_code, "large_file.py")

        end_time = time.time()
        end_memory = psutil.Process(os.getpid()).memory_info().rss

        analysis_time = end_time - start_time
        memory_used = (end_memory - start_memory) / 1024 / 1024  # MB

        # Performance assertions for large file
        assert analysis_time < 5.0, f"Large file analysis took {analysis_time:.2f}s (should be < 5s)"
        assert memory_used < 75, f"Used {memory_used:.2f}MB memory (should be < 75MB)"
        assert len(violations) > 50, "Should detect many violations in large file"

        # Log performance metrics
        print("\\nLarge file performance:")
        print(f"  Lines of code: {lines}")
        print(f"  Analysis time: {analysis_time:.2f}s")
        print(f"  Memory used: {memory_used:.2f}MB")
        print(f"  Violations found: {len(violations)}")
        print(f"  Lines per second: {lines / analysis_time:.0f}")
        print(f"  Violations per second: {len(violations) / analysis_time:.1f}")

    @pytest.mark.performance
    def test_incremental_analysis_performance(self):
        """Test performance of incremental analysis with caching."""
        analyzer = ConnascenceASTAnalyzer()

        code = """
def sample_function(a, b, c, d, e):  # Too many params
    if a > 100:  # Magic literal
        return b + c + d + e + 200  # Magic literal
    return 0
"""

        # First analysis (cold cache)
        start_time = time.time()
        violations1 = analyzer.analyze_string(code, "cached_file.py")
        first_analysis_time = time.time() - start_time

        # Second analysis (warm cache)
        start_time = time.time()
        violations2 = analyzer.analyze_string(code, "cached_file.py")
        second_analysis_time = time.time() - start_time

        # Cache should make second analysis much faster
        speedup = first_analysis_time / second_analysis_time if second_analysis_time > 0 else float("inf")

        # Results should be identical
        assert len(violations1) == len(violations2), "Cached results should match original"
        assert second_analysis_time <= first_analysis_time, "Cached analysis should be faster or equal"

        print("\\nIncremental analysis performance:")
        print(f"  First analysis: {first_analysis_time:.4f}s")
        print(f"  Second analysis: {second_analysis_time:.4f}s")
        print(f"  Speedup: {speedup:.1f}x")

    @pytest.mark.performance
    @pytest.mark.slow
    def test_memory_usage_stability(self):
        """Test memory usage stability during extended analysis."""
        analyzer = ConnascenceASTAnalyzer()

        # Generate code samples
        code_samples = []
        for i in range(100):
            code = f"""
def function_{i}(param1, param2, param3):
    threshold = {i * 10}  # Magic literal
    if param1 > threshold:
        return param2 + param3 + {i * 100}  # Magic literal
    return param1
"""
            code_samples.append((code, f"file_{i}.py"))

        initial_memory = psutil.Process(os.getpid()).memory_info().rss
        memory_measurements = []

        # Analyze files and measure memory after each batch
        batch_size = 10
        for i in range(0, len(code_samples), batch_size):
            batch = code_samples[i : i + batch_size]

            for code, filename in batch:
                analyzer.analyze_string(code, filename)

            current_memory = psutil.Process(os.getpid()).memory_info().rss
            memory_used = (current_memory - initial_memory) / 1024 / 1024  # MB
            memory_measurements.append(memory_used)

        # Check memory stability (shouldn't grow indefinitely)
        max_memory = max(memory_measurements)
        final_memory = memory_measurements[-1]

        assert max_memory < 150, f"Maximum memory usage {max_memory:.2f}MB exceeded limit"

        # Memory shouldn't grow by more than 50% from mid-point to end
        mid_point = len(memory_measurements) // 2
        mid_memory = memory_measurements[mid_point]
        memory_growth_ratio = final_memory / mid_memory if mid_memory > 0 else 1

        assert memory_growth_ratio < 1.5, f"Memory grew {memory_growth_ratio:.1f}x from midpoint (should be < 1.5x)"

        print("\\nMemory usage stability:")
        print(f"  Files analyzed: {len(code_samples)}")
        print(f"  Max memory used: {max_memory:.2f}MB")
        print(f"  Final memory used: {final_memory:.2f}MB")
        print(f"  Memory growth ratio: {memory_growth_ratio:.2f}x")

    @pytest.mark.performance
    def test_complexity_analysis_performance(self):
        """Test performance of complexity analysis on deeply nested code."""
        analyzer = ConnascenceASTAnalyzer()

        # Generate deeply nested code
        nested_code = "def complex_function(a, b, c, d, e):\\n"
        indent = "    "

        # Create deep nesting (10 levels)
        for i in range(10):
            nested_code += f"{indent * (i + 1)}if a > {i * 10}:\\n"  # Magic literals
            nested_code += f"{indent * (i + 2)}for j in range({i + 5}):\\n"  # Magic literals
            nested_code += f"{indent * (i + 3)}if j % 2 == 0:\\n"
            nested_code += f"{indent * (i + 4)}try:\\n"
            nested_code += f"{indent * (i + 5)}result = b + c + {i * 100}\\n"  # Magic literal
            nested_code += f"{indent * (i + 4)}except Exception:\\n"
            nested_code += f"{indent * (i + 5)}continue\\n"

        nested_code += f"{indent * 11}return result\\n"

        # Measure analysis time for complex code
        start_time = time.time()
        violations = analyzer.analyze_string(nested_code, "complex.py")
        analysis_time = time.time() - start_time

        # Should handle complex code efficiently
        assert analysis_time < 2.0, f"Complex code analysis took {analysis_time:.2f}s (should be < 2s)"
        assert len(violations) > 5, "Should detect multiple violations in complex code"

        # Should detect high cyclomatic complexity
        complexity_violations = [v for v in violations if "complexity" in v.description.lower()]
        assert len(complexity_violations) > 0, "Should detect complexity violations"

        print("\\nComplexity analysis performance:")
        print(f"  Analysis time: {analysis_time:.4f}s")
        print(f"  Violations found: {len(violations)}")
        print(f"  Complexity violations: {len(complexity_violations)}")


class TestScalabilityBenchmarks:
    """Test scalability characteristics."""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_linear_scaling_hypothesis(self):
        """Test that analysis time scales roughly linearly with code size."""
        analyzer = ConnascenceASTAnalyzer()

        # Test different code sizes
        sizes = [10, 25, 50, 100]  # Number of functions
        times = []

        for size in sizes:
            # Generate code of specific size
            code_parts = []
            for i in range(size):
                code_parts.append(
                    f"""
def function_{i}(a, b, c):
    if a > {i * 10}:  # Magic literal
        return b + c + {i * 100}  # Magic literal
    return a
"""
                )

            code = "\\n".join(code_parts)

            # Measure analysis time
            start_time = time.time()
            violations = analyzer.analyze_string(code, f"test_{size}.py")
            analysis_time = time.time() - start_time

            times.append(analysis_time)

            print(f"  Size {size}: {analysis_time:.4f}s, {len(violations)} violations")

        # Check that time scaling is reasonable (not exponential)
        # Time should not more than double when size doubles
        for i in range(1, len(times)):
            size_ratio = sizes[i] / sizes[i - 1]
            time_ratio = times[i] / times[i - 1] if times[i - 1] > 0 else 1

            # Allow some variance, but time scaling should be reasonable
            assert (
                time_ratio <= size_ratio * 1.5
            ), f"Time scaling {time_ratio:.2f}x too high for size scaling {size_ratio:.2f}x"

        print("\\nScaling analysis:")
        for i in range(len(sizes)):
            print(f"  {sizes[i]} functions: {times[i]:.4f}s")

    @pytest.mark.performance
    def test_concurrent_analysis_performance(self):
        """Test performance characteristics under concurrent load."""
        import queue
        import threading

        analyzer = ConnascenceASTAnalyzer()
        results_queue = queue.Queue()

        def analyze_code(thread_id):
            code = f"""
def function_in_thread_{thread_id}(a, b, c, d):
    if a > {thread_id * 100}:  # Magic literal
        return b + c + d + {thread_id * 50}  # Magic literal
    return a * {thread_id}  # Magic literal
"""

            start_time = time.time()
            violations = analyzer.analyze_string(code, f"thread_{thread_id}.py")
            end_time = time.time()

            results_queue.put(
                {"thread_id": thread_id, "analysis_time": end_time - start_time, "violation_count": len(violations)}
            )

        # Start multiple threads
        num_threads = 5
        threads = []

        start_time = time.time()

        for i in range(num_threads):
            thread = threading.Thread(target=analyze_code, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        total_time = time.time() - start_time

        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())

        assert len(results) == num_threads, "All threads should complete"

        # Calculate average analysis time per thread
        avg_thread_time = sum(r["analysis_time"] for r in results) / len(results)

        print("\\nConcurrent analysis performance:")
        print(f"  Threads: {num_threads}")
        print(f"  Total time: {total_time:.4f}s")
        print(f"  Average thread time: {avg_thread_time:.4f}s")
        print(f"  Efficiency: {(avg_thread_time * num_threads) / total_time:.2f}x")
