# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
Enhanced Pipeline Performance and Scalability Benchmarks
========================================================

Comprehensive performance benchmarking for the enhanced pipeline:
- Analysis performance across different codebase sizes
- Memory usage patterns and optimization validation
- Correlation computation scalability
- Smart recommendation generation performance
- Cross-interface response time benchmarks
- Concurrent analysis capabilities
- Resource utilization monitoring
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import gc
from pathlib import Path
import statistics
import tempfile
import time
from typing import Any, Dict, List

import pytest

from .test_infrastructure import MockEnhancedAnalyzer, performance_test


@dataclass
class PerformanceMetrics:
    """Container for performance measurement results"""

    execution_time: float
    memory_usage_mb: float
    peak_memory_mb: float
    cpu_percent: float
    findings_per_second: float
    correlations_per_second: float
    recommendations_per_second: float


@dataclass
class ScalabilityTestCase:
    """Test case for scalability benchmarking"""

    name: str
    description: str
    file_count: int
    lines_per_file: int
    complexity_factor: float
    expected_max_time: float
    expected_max_memory: float
    target_throughput: float


class PerformanceBenchmarkSuite:
    """Comprehensive performance benchmark suite"""

    def __init__(self):
        self.benchmark_results = {}
        self.scalability_test_cases = self._create_scalability_test_cases()

    def _create_scalability_test_cases(self) -> List[ScalabilityTestCase]:
        """Create scalability test cases of varying complexity"""
        return [
            ScalabilityTestCase(
                name="small_project",
                description="Small project with basic connascence patterns",
                file_count=5,
                lines_per_file=50,
                complexity_factor=1.0,
                expected_max_time=2.0,
                expected_max_memory=30.0,
                target_throughput=100.0,  # findings per second
            ),
            ScalabilityTestCase(
                name="medium_project",
                description="Medium project with moderate complexity",
                file_count=20,
                lines_per_file=100,
                complexity_factor=1.5,
                expected_max_time=8.0,
                expected_max_memory=75.0,
                target_throughput=250.0,
            ),
            ScalabilityTestCase(
                name="large_project",
                description="Large project with high complexity",
                file_count=50,
                lines_per_file=200,
                complexity_factor=2.0,
                expected_max_time=20.0,
                expected_max_memory=150.0,
                target_throughput=400.0,
            ),
            ScalabilityTestCase(
                name="enterprise_project",
                description="Enterprise-scale project with complex interdependencies",
                file_count=100,
                lines_per_file=300,
                complexity_factor=3.0,
                expected_max_time=45.0,
                expected_max_memory=250.0,
                target_throughput=600.0,
            ),
        ]

    def measure_performance(self, analyzer_func, *args, **kwargs) -> PerformanceMetrics:
        """Measure performance metrics for analyzer execution"""
        # Force garbage collection before measurement
        gc.collect()

        # Get initial memory baseline
        initial_memory = self._get_memory_usage()
        start_time = time.time()

        # Execute analysis
        result = analyzer_func(*args, **kwargs)

        # Calculate metrics
        end_time = time.time()
        final_memory = self._get_memory_usage()
        peak_memory = max(initial_memory, final_memory)

        # Calculate throughput metrics
        execution_time = end_time - start_time
        findings_count = len(result.get("findings", []))
        correlations_count = len(result.get("correlations", []))
        recommendations_count = len(result.get("smart_recommendations", []))

        findings_per_second = findings_count / execution_time if execution_time > 0 else 0
        correlations_per_second = correlations_count / execution_time if execution_time > 0 else 0
        recommendations_per_second = recommendations_count / execution_time if execution_time > 0 else 0

        return PerformanceMetrics(
            execution_time=execution_time,
            memory_usage_mb=final_memory - initial_memory,
            peak_memory_mb=peak_memory,
            cpu_percent=self._get_cpu_usage(),
            findings_per_second=findings_per_second,
            correlations_per_second=correlations_per_second,
            recommendations_per_second=recommendations_per_second,
        )

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil

            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0

    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        try:
            import psutil

            return psutil.cpu_percent(interval=0.1)
        except ImportError:
            return 0.0


@pytest.fixture
def performance_suite():
    """Fixture providing performance benchmark suite"""
    return PerformanceBenchmarkSuite()


@pytest.fixture
def temp_benchmark_directory():
    """Create temporary directory for benchmark tests"""
    with tempfile.TemporaryDirectory() as temp_dir:
        benchmark_path = Path(temp_dir) / "benchmark_project"
        benchmark_path.mkdir()
        yield benchmark_path


class TestPerformanceBenchmarks:
    """Performance benchmark test suite"""

    @performance_test(max_time_seconds=60.0, max_memory_mb=300.0)
    def test_scalability_across_project_sizes(self, performance_suite, temp_benchmark_directory):
        """Test scalability across different project sizes"""
        results = {}

        for test_case in performance_suite.scalability_test_cases:
            # Generate test project
            self._generate_test_project(temp_benchmark_directory, test_case)

            # Create analyzer
            mock_analyzer = MockEnhancedAnalyzer("success")

            # Measure performance
            metrics = performance_suite.measure_performance(
                mock_analyzer.analyze_path,
                str(temp_benchmark_directory),
                enable_cross_phase_correlation=True,
                enable_smart_recommendations=True,
                enable_audit_trail=True,
            )

            results[test_case.name] = metrics

            # Validate performance requirements
            assert (
                metrics.execution_time <= test_case.expected_max_time
            ), f"{test_case.name}: Analysis took {metrics.execution_time:.2f}s, expected <= {test_case.expected_max_time}s"

            assert (
                metrics.memory_usage_mb <= test_case.expected_max_memory
            ), f"{test_case.name}: Memory usage {metrics.memory_usage_mb:.2f}MB, expected <= {test_case.expected_max_memory}MB"

            # Validate throughput meets targets
            assert (
                metrics.findings_per_second >= test_case.target_throughput * 0.8
            ), f"{test_case.name}: Throughput {metrics.findings_per_second:.2f} findings/s below target"

            # Clean up for next iteration
            self._cleanup_test_project(temp_benchmark_directory)

        # Store results for analysis
        performance_suite.benchmark_results["scalability"] = results

        # Validate performance scaling characteristics
        self._validate_scaling_characteristics(results, performance_suite.scalability_test_cases)

    @performance_test(max_time_seconds=30.0, max_memory_mb=200.0)
    def test_correlation_computation_performance(self, performance_suite, temp_benchmark_directory):
        """Test performance of cross-phase correlation computation"""
        correlation_test_cases = [
            {"file_count": 10, "max_time": 3.0, "max_memory": 40.0},
            {"file_count": 25, "max_time": 7.0, "max_memory": 75.0},
            {"file_count": 50, "max_time": 15.0, "max_memory": 120.0},
        ]

        results = {}

        for i, test_case in enumerate(correlation_test_cases):
            # Generate test project with high correlation potential
            self._generate_correlated_test_project(temp_benchmark_directory, test_case["file_count"])

            mock_analyzer = MockEnhancedAnalyzer("success")

            # Measure correlation-specific performance
            start_time = time.time()
            result = mock_analyzer.analyze_path(
                str(temp_benchmark_directory),
                enable_cross_phase_correlation=True,
                enable_smart_recommendations=False,  # Focus on correlation performance
                enable_audit_trail=False,
            )
            correlation_time = time.time() - start_time

            correlations = result.get("correlations", [])
            correlation_count = len(correlations)

            results[f"correlation_test_{i}"] = {
                "file_count": test_case["file_count"],
                "correlation_time": correlation_time,
                "correlation_count": correlation_count,
                "correlations_per_second": correlation_count / correlation_time if correlation_time > 0 else 0,
            }

            # Validate performance requirements
            assert (
                correlation_time <= test_case["max_time"]
            ), f"Correlation computation took {correlation_time:.2f}s, expected <= {test_case['max_time']}s"

            # Validate correlation discovery effectiveness
            expected_min_correlations = test_case["file_count"] * 0.3  # At least 30% correlation rate
            assert (
                correlation_count >= expected_min_correlations
            ), f"Found {correlation_count} correlations, expected >= {expected_min_correlations}"

            self._cleanup_test_project(temp_benchmark_directory)

        performance_suite.benchmark_results["correlation_performance"] = results

    @performance_test(max_time_seconds=25.0, max_memory_mb=150.0)
    def test_smart_recommendations_generation_performance(self, performance_suite, temp_benchmark_directory):
        """Test performance of smart recommendations generation"""
        recommendation_test_cases = [
            {"complexity": "low", "expected_recommendations": 5, "max_time": 3.0},
            {"complexity": "medium", "expected_recommendations": 15, "max_time": 8.0},
            {"complexity": "high", "expected_recommendations": 30, "max_time": 18.0},
        ]

        results = {}

        for test_case in recommendation_test_cases:
            # Generate test project optimized for recommendations
            self._generate_recommendation_test_project(temp_benchmark_directory, test_case["complexity"])

            mock_analyzer = MockEnhancedAnalyzer("success")

            # Measure recommendation generation performance
            start_time = time.time()
            result = mock_analyzer.analyze_path(
                str(temp_benchmark_directory),
                enable_cross_phase_correlation=False,  # Focus on recommendation performance
                enable_smart_recommendations=True,
                enable_audit_trail=False,
            )
            recommendation_time = time.time() - start_time

            recommendations = result.get("smart_recommendations", [])
            recommendation_count = len(recommendations)

            results[test_case["complexity"]] = {
                "generation_time": recommendation_time,
                "recommendation_count": recommendation_count,
                "recommendations_per_second": (
                    recommendation_count / recommendation_time if recommendation_time > 0 else 0
                ),
            }

            # Validate performance and effectiveness
            assert (
                recommendation_time <= test_case["max_time"]
            ), f"Recommendation generation took {recommendation_time:.2f}s, expected <= {test_case['max_time']}s"

            assert (
                recommendation_count >= test_case["expected_recommendations"]
            ), f"Generated {recommendation_count} recommendations, expected >= {test_case['expected_recommendations']}"

            self._cleanup_test_project(temp_benchmark_directory)

        performance_suite.benchmark_results["recommendation_performance"] = results

    @performance_test(max_time_seconds=45.0, max_memory_mb=250.0)
    def test_concurrent_analysis_performance(self, performance_suite, temp_benchmark_directory):
        """Test performance under concurrent analysis loads"""
        concurrent_test_cases = [
            {"thread_count": 2, "max_total_time": 15.0},
            {"thread_count": 4, "max_total_time": 25.0},
            {"thread_count": 8, "max_total_time": 40.0},
        ]

        results = {}

        for test_case in concurrent_test_cases:
            # Generate multiple test projects
            test_projects = []
            for i in range(test_case["thread_count"]):
                project_path = temp_benchmark_directory / f"concurrent_project_{i}"
                project_path.mkdir(exist_ok=True)
                self._generate_test_project(
                    project_path, performance_suite.scalability_test_cases[1]
                )  # Medium complexity
                test_projects.append(project_path)

            # Execute concurrent analysis
            start_time = time.time()

            with ThreadPoolExecutor(max_workers=test_case["thread_count"]) as executor:
                futures = []

                for project_path in test_projects:
                    mock_analyzer = MockEnhancedAnalyzer("success")
                    future = executor.submit(
                        mock_analyzer.analyze_path,
                        str(project_path),
                        enable_cross_phase_correlation=True,
                        enable_smart_recommendations=True,
                    )
                    futures.append(future)

                # Wait for completion and collect results
                concurrent_results = []
                for future in as_completed(futures):
                    concurrent_results.append(future.result())

            total_time = time.time() - start_time

            # Analyze concurrent performance
            results[f"threads_{test_case['thread_count']}"] = {
                "total_time": total_time,
                "thread_count": test_case["thread_count"],
                "average_time_per_analysis": total_time / test_case["thread_count"],
                "throughput_analyses_per_second": test_case["thread_count"] / total_time,
                "results_count": len(concurrent_results),
            }

            # Validate concurrent performance
            assert (
                total_time <= test_case["max_total_time"]
            ), f"Concurrent analysis took {total_time:.2f}s, expected <= {test_case['max_total_time']}s"

            assert (
                len(concurrent_results) == test_case["thread_count"]
            ), f"Expected {test_case['thread_count']} results, got {len(concurrent_results)}"

            # Validate all analyses completed successfully
            for result in concurrent_results:
                assert "findings" in result, "All concurrent analyses should produce findings"
                assert len(result.get("findings", [])) > 0, "All analyses should find issues"

            # Clean up projects
            for project_path in test_projects:
                self._cleanup_test_project(project_path)

        performance_suite.benchmark_results["concurrent_performance"] = results

    @performance_test(max_time_seconds=20.0, max_memory_mb=100.0)
    def test_interface_response_time_benchmarks(self, performance_suite):
        """Test response time performance across different interfaces"""
        interfaces = ["vscode", "mcp_server", "web_dashboard", "cli"]

        # Create sample enhanced result
        mock_analyzer = MockEnhancedAnalyzer("success")
        enhanced_result = mock_analyzer.analyze_path(
            "sample_project",
            enable_cross_phase_correlation=True,
            enable_smart_recommendations=True,
            enable_audit_trail=True,
        )

        results = {}

        for interface in interfaces:
            # Measure interface formatting time
            formatting_times = []

            for iteration in range(10):  # Multiple iterations for statistical accuracy
                start_time = time.time()
                self._format_for_interface(enhanced_result, interface)
                formatting_time = time.time() - start_time
                formatting_times.append(formatting_time)

            # Calculate statistics
            avg_time = statistics.mean(formatting_times)
            max_time = max(formatting_times)
            min_time = min(formatting_times)
            std_dev = statistics.stdev(formatting_times) if len(formatting_times) > 1 else 0

            results[interface] = {
                "average_time_ms": avg_time * 1000,
                "max_time_ms": max_time * 1000,
                "min_time_ms": min_time * 1000,
                "std_dev_ms": std_dev * 1000,
                "iterations": len(formatting_times),
            }

            # Validate interface performance requirements
            assert avg_time <= 0.5, f"{interface}: Average formatting time {avg_time:.3f}s exceeds 0.5s limit"
            assert max_time <= 1.0, f"{interface}: Max formatting time {max_time:.3f}s exceeds 1.0s limit"

        performance_suite.benchmark_results["interface_performance"] = results

        # Validate relative performance expectations
        # VSCode should be fastest (direct data), web dashboard may be slower (chart processing)
        assert (
            results["vscode"]["average_time_ms"] <= results["web_dashboard"]["average_time_ms"]
        ), "VSCode formatting should be faster than web dashboard"

    @performance_test(max_time_seconds=35.0, max_memory_mb=200.0)
    def test_memory_usage_patterns(self, performance_suite, temp_benchmark_directory):
        """Test memory usage patterns and optimization"""
        memory_test_cases = [
            {"name": "memory_efficient", "enable_correlation": False, "enable_recommendations": False},
            {"name": "correlation_enabled", "enable_correlation": True, "enable_recommendations": False},
            {"name": "recommendations_enabled", "enable_correlation": False, "enable_recommendations": True},
            {"name": "full_features", "enable_correlation": True, "enable_recommendations": True},
        ]

        results = {}

        # Generate medium complexity test project
        test_case = performance_suite.scalability_test_cases[1]  # Medium project
        self._generate_test_project(temp_benchmark_directory, test_case)

        for memory_test in memory_test_cases:
            # Force garbage collection before test
            gc.collect()

            mock_analyzer = MockEnhancedAnalyzer("success")

            # Measure memory usage pattern
            initial_memory = performance_suite._get_memory_usage()

            result = mock_analyzer.analyze_path(
                str(temp_benchmark_directory),
                enable_cross_phase_correlation=memory_test["enable_correlation"],
                enable_smart_recommendations=memory_test["enable_recommendations"],
                enable_audit_trail=True,
            )

            peak_memory = performance_suite._get_memory_usage()

            # Force cleanup and measure final memory
            del result
            gc.collect()
            final_memory = performance_suite._get_memory_usage()

            results[memory_test["name"]] = {
                "initial_memory_mb": initial_memory,
                "peak_memory_mb": peak_memory,
                "final_memory_mb": final_memory,
                "memory_increase_mb": peak_memory - initial_memory,
                "memory_cleanup_mb": peak_memory - final_memory,
                "cleanup_efficiency": (
                    (peak_memory - final_memory) / (peak_memory - initial_memory)
                    if peak_memory > initial_memory
                    else 1.0
                ),
            }

        performance_suite.benchmark_results["memory_patterns"] = results

        # Validate memory usage patterns
        baseline_memory = results["memory_efficient"]["memory_increase_mb"]

        # Correlation should add reasonable memory overhead
        correlation_overhead = results["correlation_enabled"]["memory_increase_mb"] - baseline_memory
        assert correlation_overhead <= baseline_memory * 0.5, "Correlation memory overhead should be <= 50% of baseline"

        # Recommendations should add reasonable memory overhead
        recommendation_overhead = results["recommendations_enabled"]["memory_increase_mb"] - baseline_memory
        assert (
            recommendation_overhead <= baseline_memory * 0.3
        ), "Recommendation memory overhead should be <= 30% of baseline"

        # Full features should not have excessive memory usage
        full_features_memory = results["full_features"]["memory_increase_mb"]
        assert full_features_memory <= baseline_memory * 2.0, "Full features memory should be <= 200% of baseline"

        # Validate memory cleanup efficiency
        for test_name, test_result in results.items():
            assert test_result["cleanup_efficiency"] >= 0.7, f"{test_name}: Memory cleanup efficiency should be >= 70%"

    def _generate_test_project(self, project_path: Path, test_case: ScalabilityTestCase):
        """Generate test project based on scalability test case"""
        for i in range(test_case.file_count):
            file_content = self._generate_file_content(i, test_case.lines_per_file, test_case.complexity_factor)
            file_path = project_path / f"module_{i}.py"
            file_path.write_text(file_content, encoding="utf-8")

    def _generate_file_content(self, file_index: int, lines_per_file: int, complexity_factor: float) -> str:
        """Generate file content with specified complexity"""
        base_lines = int(lines_per_file / complexity_factor)
        complexity_lines = lines_per_file - base_lines

        content = f"""
# Module {file_index} - Generated test file
class Module{file_index}:
    def __init__(self, dependency_{file_index % 3}):
        # CofE: Type - dependency coupling
        self.dep = dependency_{file_index % 3}
        self.config = {{"mode": "TYPE_{file_index % 2}"}}  # CofE: Meaning

    def process(self, data, format="JSON"):
        # CofE: Position - parameter order dependency
        if self.config["mode"] == "TYPE_0":
            return self._process_type_0(data, format)
        else:
            return self._process_type_1(data, format)
"""

        # Add complexity based on factor
        for i in range(int(complexity_lines / 10)):
            content += f"""
    def complex_method_{i}(self, param_{i}):
        # CofE: Algorithm - complex processing dependency
        if param_{i} > {i * 10}:
            return self._complex_processing_{i}(param_{i})
        else:
            return self._simple_processing_{i}(param_{i})

    def _complex_processing_{i}(self, data):
        # CofE: Execution - specific execution order
        validated = self._validate_{i}(data)
        transformed = self._transform_{i}(validated)
        return self._output_{i}(transformed)
"""

        return content

    def _generate_correlated_test_project(self, project_path: Path, file_count: int):
        """Generate test project optimized for correlation detection"""
        # Create files with intentional correlations
        for i in range(file_count):
            content = f"""
class Service{i}:
    def __init__(self, service_{(i + 1) % file_count}):
        # Intentional cross-service dependency for correlation
        self.dependency = service_{(i + 1) % file_count}

    def execute(self, data):
        # CofE: Algorithm - services depend on each other's algorithms
        if hasattr(self.dependency, 'preprocess'):
            preprocessed = self.dependency.preprocess(data)
            return self.process(preprocessed)
        return self.process(data)

    def process(self, data):
        # CofE: Execution - execution order matters across services
        return {{"result": data, "service": "Service{i}"}}
"""
            file_path = project_path / f"service_{i}.py"
            file_path.write_text(content, encoding="utf-8")

    def _generate_recommendation_test_project(self, project_path: Path, complexity: str):
        """Generate test project optimized for smart recommendations"""
        complexity_map = {"low": 3, "medium": 8, "high": 15}
        file_count = complexity_map.get(complexity, 5)

        for i in range(file_count):
            # Generate code with common refactoring opportunities
            content = f"""
class Component{i}:
    def __init__(self):
        # CofE: Meaning - status strings should be enum
        self.status = "ACTIVE"  # Should be enum
        self.mode = "BATCH"     # Should be enum

    def update_status(self, new_status):
        # CofE: Meaning - magic string coupling
        if new_status in ["ACTIVE", "INACTIVE", "PENDING"]:
            self.status = new_status
            return True
        return False

    def process_data(self, data, output_format):
        # CofE: Position - should use builder pattern
        # CofE: Algorithm - should extract strategy
        if output_format == "JSON":
            return self._to_json(data)
        elif output_format == "XML":
            return self._to_xml(data)
        elif output_format == "CSV":
            return self._to_csv(data)

    def _to_json(self, data):
        # Repeated pattern - should extract
        validated = self._validate(data)
        formatted = self._format_json(validated)
        return self._finalize(formatted)

    def _to_xml(self, data):
        # Repeated pattern - should extract
        validated = self._validate(data)
        formatted = self._format_xml(validated)
        return self._finalize(formatted)
"""
            file_path = project_path / f"component_{i}.py"
            file_path.write_text(content, encoding="utf-8")

    def _cleanup_test_project(self, project_path: Path):
        """Clean up generated test project"""
        if project_path.exists():
            for file_path in project_path.glob("*.py"):
                file_path.unlink()

    def _format_for_interface(self, result: Dict[str, Any], interface: str) -> Dict[str, Any]:
        """Format analysis result for specific interface (performance test version)"""
        if interface == "vscode":
            # VSCode interface formatting
            correlations = result.get("correlations", [])
            recommendations = result.get("smart_recommendations", [])
            return {
                "correlation_data": [
                    {
                        "id": f"{c.get('analyzer1', '')}_{c.get('analyzer2', '')}",
                        "score": c.get("correlation_score", 0),
                        "description": c.get("description", ""),
                    }
                    for c in correlations
                ],
                "recommendations_panel": [
                    {
                        "title": r.get("title", ""),
                        "priority": r.get("priority", "medium"),
                        "files": r.get("affected_files", []),
                    }
                    for r in recommendations
                ],
            }

        elif interface == "mcp_server":
            # MCP server interface formatting
            return {
                "enhanced_context": {
                    "correlations_summary": len(result.get("correlations", [])),
                    "recommendations_available": len(result.get("smart_recommendations", [])),
                    "analysis_complete": True,
                },
                "actionable_suggestions": [
                    {
                        "suggestion": rec.get("title", ""),
                        "impact": rec.get("priority", "medium"),
                        "files": rec.get("affected_files", []),
                    }
                    for rec in result.get("smart_recommendations", [])
                ],
            }

        elif interface == "web_dashboard":
            # Web dashboard interface formatting (includes chart processing)
            correlations = result.get("correlations", [])
            chart_data = {
                "labels": [f"{c.get('analyzer1', '')} → {c.get('analyzer2', '')}" for c in correlations],
                "datasets": [
                    {
                        "data": [c.get("correlation_score", 0) * 100 for c in correlations],
                        "backgroundColor": ["rgba(99, 102, 241, 0.6)"] * len(correlations),
                    }
                ],
            }

            return {
                "chart_data": chart_data,
                "summary_stats": {
                    "total_findings": len(result.get("findings", [])),
                    "correlation_count": len(correlations),
                    "recommendation_count": len(result.get("smart_recommendations", [])),
                },
                "timeline_data": {
                    "events": result.get("audit_trail", []),
                    "total_duration": sum(e.get("duration_ms", 0) for e in result.get("audit_trail", [])),
                },
            }

        elif interface == "cli":
            # CLI interface formatting
            return {
                "formatted_output": {
                    "summary": f"Found {len(result.get('findings', []))} findings",
                    "correlations": f"Detected {len(result.get('correlations', []))} correlations",
                    "recommendations": f"Generated {len(result.get('smart_recommendations', []))} recommendations",
                },
                "detailed_report": {
                    "findings": result.get("findings", []),
                    "correlations": result.get("correlations", []),
                    "recommendations": result.get("smart_recommendations", []),
                },
            }

        return {}

    def _validate_scaling_characteristics(
        self, results: Dict[str, PerformanceMetrics], test_cases: List[ScalabilityTestCase]
    ):
        """Validate that performance scales reasonably with complexity"""
        # Extract metrics for analysis
        execution_times = []
        memory_usages = []
        complexity_factors = []

        for test_case in test_cases:
            if test_case.name in results:
                metrics = results[test_case.name]
                execution_times.append(metrics.execution_time)
                memory_usages.append(metrics.memory_usage_mb)
                complexity_factors.append(test_case.complexity_factor * test_case.file_count)

        # Validate that scaling is reasonable (not exponential)
        if len(execution_times) >= 3:
            # Time should scale roughly linearly or sub-quadratically
            time_scaling_ratio = execution_times[-1] / execution_times[0]  # largest to smallest
            complexity_scaling_ratio = complexity_factors[-1] / complexity_factors[0]

            # Time scaling should not be much worse than quadratic relative to complexity
            assert (
                time_scaling_ratio <= complexity_scaling_ratio**1.5
            ), f"Time scaling ratio {time_scaling_ratio:.2f} too high relative to complexity ratio {complexity_scaling_ratio:.2f}"

            # Memory should scale reasonably
            memory_scaling_ratio = memory_usages[-1] / memory_usages[0]
            assert (
                memory_scaling_ratio <= complexity_scaling_ratio * 1.2
            ), f"Memory scaling ratio {memory_scaling_ratio:.2f} too high relative to complexity"


if __name__ == "__main__":
    # Run performance benchmarks
    pytest.main([__file__, "-v", "-m", "performance"])
