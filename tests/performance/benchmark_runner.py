# SPDX-License-Identifier: MIT
"""
Performance Benchmark Runner
============================

Comprehensive benchmarking framework for the connascence analyzer.
Tests performance on real codebases and synthetic projects.
"""

from dataclasses import asdict, dataclass
import json
import logging
import os
from pathlib import Path
import shutil
import statistics
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional

import psutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analyzer.core import ConnascenceAnalyzer
from analyzer.performance.parallel_analyzer import ParallelAnalysisConfig, ParallelConnascenceAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""

    # Test configuration
    test_name: str
    codebase_path: str
    file_count: int
    total_lines: int

    # Performance metrics
    execution_time_seconds: float
    memory_peak_mb: float
    memory_avg_mb: float
    cpu_usage_percent: float

    # Analysis results
    violations_found: int
    files_analyzed: int
    analysis_accuracy: float

    # Throughput metrics
    files_per_second: float
    lines_per_second: float
    violations_per_second: float

    # Resource efficiency
    memory_per_file_kb: float
    cpu_time_per_file_ms: float

    # Additional metadata
    analyzer_mode: str
    parallel_workers: int
    cache_enabled: bool
    timestamp: str


class PerformanceBenchmarker:
    """Comprehensive performance benchmarking system."""

    def __init__(self, output_dir: str = "tests/performance/results"):
        """Initialize benchmarker with output directory."""

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.sequential_analyzer = ConnascenceAnalyzer()
        self.parallel_analyzer = ParallelConnascenceAnalyzer()

        # Benchmark configuration
        self.warmup_runs = 2
        self.benchmark_runs = 5
        self.timeout_seconds = 300  # 5 minutes max per test

        logger.info(f"Performance benchmarker initialized, results -> {self.output_dir}")

    def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """Run complete performance benchmark suite."""

        benchmark_start = time.time()
        logger.info("Starting comprehensive performance benchmark suite")

        results = {
            "benchmark_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "system_info": self._get_system_info(),
            "test_results": {},
            "performance_summary": {},
            "recommendations": [],
        }

        # Test suites to run
        test_suites = [
            ("real_codebases", self._benchmark_real_codebases),
            ("synthetic_projects", self._benchmark_synthetic_projects),
            ("parallel_scaling", self._benchmark_parallel_scaling),
            ("memory_stress", self._benchmark_memory_stress),
            ("caching_effectiveness", self._benchmark_caching),
        ]

        for suite_name, suite_function in test_suites:
            logger.info(f"Running {suite_name} benchmark suite")

            try:
                suite_results = suite_function()
                results["test_results"][suite_name] = suite_results

                logger.info(f"Completed {suite_name}: {len(suite_results)} tests")

            except Exception as e:
                logger.error(f"Failed to run {suite_name}: {e}")
                results["test_results"][suite_name] = {"error": str(e)}

        # Generate performance summary and recommendations
        results["performance_summary"] = self._generate_performance_summary(results["test_results"])
        results["recommendations"] = self._generate_recommendations(results["test_results"])

        total_time = time.time() - benchmark_start
        results["total_benchmark_time"] = total_time

        # Save comprehensive results
        self._save_benchmark_results(results)

        logger.info(f"Comprehensive benchmark completed in {total_time:.2f} seconds")
        return results

    def benchmark_codebase(self, codebase_path: str, test_name: Optional[str] = None) -> BenchmarkResult:
        """Benchmark analyzer performance on a specific codebase."""

        codebase_path = Path(codebase_path)
        test_name = test_name or codebase_path.name

        logger.info(f"Benchmarking codebase: {codebase_path}")

        # Discover files
        files_to_analyze = self._discover_files(codebase_path)
        file_count = len(files_to_analyze)

        if file_count == 0:
            logger.warning(f"No files found in {codebase_path}")
            return self._create_empty_result(test_name, str(codebase_path))

        # Count total lines
        total_lines = self._count_total_lines(files_to_analyze)

        logger.info(f"Found {file_count} files, {total_lines} lines total")

        # Run performance benchmark
        start_time = time.time()

        # Start resource monitoring
        resource_monitor = ResourceMonitor()
        resource_monitor.start_monitoring()

        try:
            # Run analysis
            analysis_result = self.sequential_analyzer.analyze_path(str(codebase_path), policy="default")

            execution_time = time.time() - start_time

            # Stop monitoring
            resource_stats = resource_monitor.stop_monitoring()

            # Extract analysis metrics
            violations_found = len(analysis_result.get("violations", []))
            files_analyzed = analysis_result.get("metrics", {}).get("files_analyzed", file_count)

            # Calculate throughput metrics
            files_per_second = files_analyzed / execution_time if execution_time > 0 else 0
            lines_per_second = total_lines / execution_time if execution_time > 0 else 0
            violations_per_second = violations_found / execution_time if execution_time > 0 else 0

            # Calculate efficiency metrics
            memory_per_file_kb = (resource_stats["peak_memory_mb"] * 1024) / files_analyzed if files_analyzed > 0 else 0
            cpu_time_per_file_ms = (execution_time * 1000) / files_analyzed if files_analyzed > 0 else 0

            result = BenchmarkResult(
                test_name=test_name,
                codebase_path=str(codebase_path),
                file_count=file_count,
                total_lines=total_lines,
                execution_time_seconds=execution_time,
                memory_peak_mb=resource_stats["peak_memory_mb"],
                memory_avg_mb=resource_stats["avg_memory_mb"],
                cpu_usage_percent=resource_stats["avg_cpu_percent"],
                violations_found=violations_found,
                files_analyzed=files_analyzed,
                analysis_accuracy=1.0,  # Assume 100% accuracy for baseline
                files_per_second=files_per_second,
                lines_per_second=lines_per_second,
                violations_per_second=violations_per_second,
                memory_per_file_kb=memory_per_file_kb,
                cpu_time_per_file_ms=cpu_time_per_file_ms,
                analyzer_mode="sequential",
                parallel_workers=1,
                cache_enabled=False,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            )

            logger.info(f"Benchmark complete: {files_per_second:.1f} files/sec, {violations_found} violations")
            return result

        except Exception as e:
            logger.error(f"Benchmark failed: {e}")
            execution_time = time.time() - start_time
            resource_monitor.stop_monitoring()

            return BenchmarkResult(
                test_name=f"{test_name}_failed",
                codebase_path=str(codebase_path),
                file_count=file_count,
                total_lines=total_lines,
                execution_time_seconds=execution_time,
                memory_peak_mb=0,
                memory_avg_mb=0,
                cpu_usage_percent=0,
                violations_found=0,
                files_analyzed=0,
                analysis_accuracy=0,
                files_per_second=0,
                lines_per_second=0,
                violations_per_second=0,
                memory_per_file_kb=0,
                cpu_time_per_file_ms=0,
                analyzer_mode="failed",
                parallel_workers=0,
                cache_enabled=False,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            )

    def _benchmark_real_codebases(self) -> Dict[str, BenchmarkResult]:
        """Benchmark analyzer on real codebases in test_packages/."""

        results = {}
        test_packages_dir = Path("test_packages")

        if not test_packages_dir.exists():
            logger.warning("test_packages directory not found")
            return results

        # Find all package directories
        for package_dir in test_packages_dir.iterdir():
            if package_dir.is_dir():
                logger.info(f"Benchmarking real codebase: {package_dir.name}")

                try:
                    result = self.benchmark_codebase(str(package_dir), package_dir.name)
                    results[package_dir.name] = asdict(result)

                except Exception as e:
                    logger.error(f"Failed to benchmark {package_dir.name}: {e}")
                    results[package_dir.name] = {"error": str(e)}

        return results

    def _benchmark_synthetic_projects(self) -> Dict[str, BenchmarkResult]:
        """Benchmark analyzer on synthetic projects of various sizes."""

        results = {}
        test_sizes = [10, 25, 50, 100, 250, 500]

        for size in test_sizes:
            logger.info(f"Benchmarking synthetic project: {size} files")

            try:
                # Create synthetic project
                project_dir = self._create_synthetic_project(size)

                try:
                    result = self.benchmark_codebase(str(project_dir), f"synthetic_{size}")
                    results[f"synthetic_{size}"] = asdict(result)

                finally:
                    # Clean up
                    shutil.rmtree(project_dir, ignore_errors=True)

            except Exception as e:
                logger.error(f"Failed to benchmark synthetic_{size}: {e}")
                results[f"synthetic_{size}"] = {"error": str(e)}

        return results

    def _benchmark_parallel_scaling(self) -> Dict[str, Any]:
        """Benchmark parallel processing scalability."""

        results = {}

        # Test different worker counts
        worker_counts = [1, 2, 4, 8]
        test_project = self._create_synthetic_project(100)

        try:
            for workers in worker_counts:
                logger.info(f"Benchmarking parallel scaling: {workers} workers")

                config = ParallelAnalysisConfig(max_workers=workers, use_processes=True)
                parallel_analyzer = ParallelConnascenceAnalyzer(config)

                # Run benchmark
                start_time = time.time()
                parallel_result = parallel_analyzer.analyze_project_parallel(str(test_project))
                execution_time = time.time() - start_time

                results[f"workers_{workers}"] = {
                    "worker_count": workers,
                    "execution_time": execution_time,
                    "speedup_factor": parallel_result.speedup_factor,
                    "efficiency": parallel_result.efficiency,
                    "files_analyzed": parallel_result.unified_result.files_analyzed,
                    "violations_found": parallel_result.unified_result.total_violations,
                }

        finally:
            shutil.rmtree(test_project, ignore_errors=True)

        return results

    def _benchmark_memory_stress(self) -> Dict[str, Any]:
        """Benchmark memory usage under stress conditions."""

        results = {}

        # Test progressively larger projects
        project_sizes = [100, 500, 1000, 2000]

        for size in project_sizes:
            logger.info(f"Memory stress test: {size} files")

            project_dir = self._create_synthetic_project(size)

            try:
                # Monitor memory usage
                resource_monitor = ResourceMonitor()
                resource_monitor.start_monitoring()

                start_time = time.time()
                self.sequential_analyzer.analyze_path(str(project_dir))
                execution_time = time.time() - start_time

                resource_stats = resource_monitor.stop_monitoring()

                results[f"files_{size}"] = {
                    "file_count": size,
                    "execution_time": execution_time,
                    "peak_memory_mb": resource_stats["peak_memory_mb"],
                    "avg_memory_mb": resource_stats["avg_memory_mb"],
                    "memory_growth_mb": resource_stats["peak_memory_mb"] - resource_stats.get("initial_memory_mb", 0),
                    "memory_efficiency_kb_per_file": (resource_stats["peak_memory_mb"] * 1024) / size,
                }

            except Exception as e:
                logger.error(f"Memory stress test failed for {size} files: {e}")
                results[f"files_{size}"] = {"error": str(e)}

            finally:
                shutil.rmtree(project_dir, ignore_errors=True)

        return results

    def _benchmark_caching(self) -> Dict[str, Any]:
        """Benchmark caching effectiveness."""

        results = {}

        # Create test project
        test_project = self._create_synthetic_project(100)

        try:
            # Benchmark without caching (first run)
            logger.info("Benchmarking without caching (cold run)")
            start_time = time.time()
            result_nocache = self.sequential_analyzer.analyze_path(str(test_project))
            cold_time = time.time() - start_time

            # Benchmark with caching (second run on same project)
            logger.info("Benchmarking with caching (warm run)")
            start_time = time.time()
            result_cache = self.sequential_analyzer.analyze_path(str(test_project))
            warm_time = time.time() - start_time

            # Calculate cache effectiveness
            cache_speedup = cold_time / max(warm_time, 0.001)
            cache_effectiveness = ((cold_time - warm_time) / cold_time) * 100 if cold_time > 0 else 0

            results = {
                "cold_run_time": cold_time,
                "warm_run_time": warm_time,
                "cache_speedup": cache_speedup,
                "cache_effectiveness_percent": cache_effectiveness,
                "violations_consistent": len(result_nocache.get("violations", []))
                == len(result_cache.get("violations", [])),
            }

        except Exception as e:
            logger.error(f"Caching benchmark failed: {e}")
            results = {"error": str(e)}

        finally:
            shutil.rmtree(test_project, ignore_errors=True)

        return results

    def _create_synthetic_project(self, file_count: int) -> Path:
        """Create synthetic Python project for testing."""

        project_dir = Path(tempfile.mkdtemp(prefix="perf_test_"))

        # Create realistic directory structure
        src_dir = project_dir / "src"
        tests_dir = project_dir / "tests"
        src_dir.mkdir()
        tests_dir.mkdir()

        # Generate files with various patterns and violations
        for i in range(file_count):
            if i % 4 == 0:
                file_path = src_dir / f"module_{i:03d}.py"
            elif i % 4 == 1:
                file_path = tests_dir / f"test_{i:03d}.py"
            else:
                subdir = src_dir / f"package_{i // 10}"
                subdir.mkdir(exist_ok=True)
                file_path = subdir / f"component_{i:03d}.py"

            # Generate content with connascence violations
            content = self._generate_file_content(i, file_count)
            file_path.write_text(content)

        return project_dir

    def _generate_file_content(self, file_index: int, total_files: int) -> str:
        """Generate Python file content with realistic violations."""

        # Vary complexity based on file index
        complexity_factor = (file_index % 5) + 1

        content = f'''#!/usr/bin/env python3
"""
Generated test file {file_index} for performance benchmarking.
Contains various connascence violations for realistic testing.
"""

import os
import sys
import time
from typing import List, Dict, Any

# Configuration constants (potential magic literals)
MAX_RETRIES = {3 + file_index % 5}
TIMEOUT_SECONDS = {30 + file_index * 2}
BUFFER_SIZE = {1024 * (file_index % 8 + 1)}
DEFAULT_PORT = {8000 + file_index}

'''

        # Add functions with parameter coupling
        for func_idx in range(complexity_factor):
            param_count = min(2 + func_idx, 8)  # Vary parameter count
            params = [f"param_{j}" for j in range(param_count)]

            content += f'''
def process_data_{func_idx}({", ".join(params)}):
    """Function with {param_count} parameters (CoD - Connascence of Data)."""

    # Magic literals (CoL - Connascence of Literal)
    magic_value = {42 + file_index + func_idx * 10}
    threshold = {100 + file_index * 5}

    result = []

    # Position-dependent operations (CoP - Connascence of Position)
    if len(params) >= 3:
        combined = {params[0]} * {params[1]} + {params[2]}
        result.append(combined)

    # Type coupling (CoT - Connascence of Type)
    if isinstance({params[0]}, (int, float)):
        result.append({params[0]} * magic_value)
    elif isinstance({params[0]}, str):
        result.append({params[0]} + "_processed")

    return result
'''

        # Add a class with many methods (potential god object)
        method_count = min(5 + complexity_factor * 3, 25)

        content += f'''

class DataProcessor_{file_index}:
    """
    Data processing class (potential god object with {method_count} methods).
    Demonstrates various connascence types.
    """

    def __init__(self, config_dict: Dict[str, Any]):
        # Algorithm coupling (CoA - Connascence of Algorithm)
        self.config = config_dict
        self.retry_count = config_dict.get("retries", MAX_RETRIES)
        self.timeout = config_dict.get("timeout", TIMEOUT_SECONDS)
        self.buffer_size = BUFFER_SIZE

        # Execution order coupling (CoX - Connascence of Execution)
        self._initialize_resources()
        self._validate_config()
        self._setup_connections()

    def _initialize_resources(self):
        """Must be called first."""
        self.resource_pool = []
        self.connection_map = {{}}

    def _validate_config(self):
        """Must be called after initialize_resources."""
        if not hasattr(self, 'resource_pool'):
            raise RuntimeError("Resources not initialized")

    def _setup_connections(self):
        """Must be called after validate_config."""
        if not hasattr(self, 'connection_map'):
            raise RuntimeError("Config not validated")
'''

        # Add many methods to create potential god object
        for method_idx in range(method_count):
            content += f'''
    def method_{method_idx:02d}(self, data):
        """Method {method_idx} with potential violations."""
        # Magic literals and coupling
        processed = data * {10 + method_idx} if isinstance(data, (int, float)) else str(data)
        return processed
'''

        # Add module-level coupling
        content += f'''

# Global state (potential coupling issues)
GLOBAL_CACHE = {{}}
SHARED_COUNTER = {file_index}

def update_global_state(key: str, value: Any) -> None:
    """Function that modifies global state (CoR - Connascence of Reference)."""
    global SHARED_COUNTER
    GLOBAL_CACHE[key] = value
    SHARED_COUNTER += 1

def get_shared_data() -> Dict[str, Any]:
    """Function dependent on global state."""
    return {{
        "cache_size": len(GLOBAL_CACHE),
        "counter": SHARED_COUNTER,
        "file_id": {file_index}
    }}

# Timing-dependent code (CoT - Connascence of Timing)
def time_sensitive_operation():
    """Operation that depends on timing."""
    start_time = time.time()
    # Simulate work
    time.sleep(0.001 * {file_index % 10 + 1})
    return time.time() - start_time > 0.005

if __name__ == "__main__":
    # Entry point with coupling
    processor = DataProcessor_{file_index}({{"retries": MAX_RETRIES}})
    result = processor.method_00("test_data")
    print(f"Processed: {{result}}")
'''

        return content

    def _discover_files(self, directory: Path) -> List[Path]:
        """Discover Python files to analyze."""

        files = []
        patterns = ["**/*.py", "**/*.js", "**/*.ts", "**/*.jsx", "**/*.tsx"]

        for pattern in patterns:
            for file_path in directory.glob(pattern):
                if (
                    file_path.is_file()
                    and not any(part.startswith(".") for part in file_path.parts)
                    and file_path.stat().st_size < 10 * 1024 * 1024
                ):  # Skip files > 10MB
                    files.append(file_path)

        return sorted(files)

    def _count_total_lines(self, files: List[Path]) -> int:
        """Count total lines of code."""

        total_lines = 0

        for file_path in files:
            try:
                with open(file_path, encoding="utf-8", errors="ignore") as f:
                    lines = sum(1 for line in f if line.strip())
                    total_lines += lines
            except Exception:
                pass  # Skip files that can't be read

        return total_lines

    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for benchmark context."""

        return {
            "cpu_count": os.cpu_count(),
            "cpu_freq_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else "unknown",
            "memory_total_gb": psutil.virtual_memory().total / (1024**3),
            "python_version": sys.version,
            "platform": sys.platform,
            "architecture": os.uname().machine if hasattr(os, "uname") else "unknown",
        }

    def _generate_performance_summary(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance summary from test results."""

        summary = {
            "overall_performance": "unknown",
            "bottlenecks_identified": [],
            "performance_targets_met": {},
            "scalability_assessment": "unknown",
        }

        # Analyze real codebase performance
        if "real_codebases" in test_results:
            real_results = test_results["real_codebases"]

            sum(r.get("file_count", 0) for r in real_results.values() if isinstance(r, dict) and "file_count" in r)
            avg_throughput = (
                statistics.mean(
                    [
                        r.get("files_per_second", 0)
                        for r in real_results.values()
                        if isinstance(r, dict) and r.get("files_per_second", 0) > 0
                    ]
                )
                if real_results
                else 0
            )

            # Check performance targets
            summary["performance_targets_met"] = {
                "large_codebases_under_5min": all(
                    r.get("execution_time_seconds", float("inf")) < 300
                    for r in real_results.values()
                    if isinstance(r, dict) and r.get("file_count", 0) > 1000
                ),
                "medium_codebases_under_30sec": all(
                    r.get("execution_time_seconds", float("inf")) < 30
                    for r in real_results.values()
                    if isinstance(r, dict) and 100 <= r.get("file_count", 0) <= 1000
                ),
                "small_codebases_under_5sec": all(
                    r.get("execution_time_seconds", float("inf")) < 5
                    for r in real_results.values()
                    if isinstance(r, dict) and r.get("file_count", 0) < 100
                ),
                "average_throughput_acceptable": avg_throughput > 10,  # files per second
            }

        # Analyze memory usage
        if "memory_stress" in test_results:
            memory_results = test_results["memory_stress"]

            memory_growth_rates = [
                r.get("memory_efficiency_kb_per_file", 0)
                for r in memory_results.values()
                if isinstance(r, dict) and "memory_efficiency_kb_per_file" in r
            ]

            if memory_growth_rates:
                avg_memory_per_file = statistics.mean(memory_growth_rates)
                if avg_memory_per_file > 1024:  # > 1MB per file
                    summary["bottlenecks_identified"].append("High memory usage per file")

        # Analyze parallel scaling
        if "parallel_scaling" in test_results:
            parallel_results = test_results["parallel_scaling"]

            speedup_factors = [
                r.get("speedup_factor", 1.0)
                for r in parallel_results.values()
                if isinstance(r, dict) and "speedup_factor" in r
            ]

            if speedup_factors:
                max_speedup = max(speedup_factors)
                summary["scalability_assessment"] = (
                    "excellent"
                    if max_speedup > 3.0
                    else "good" if max_speedup > 2.0 else "moderate" if max_speedup > 1.5 else "poor"
                )

        return summary

    def _generate_recommendations(self, test_results: Dict[str, Any]) -> List[str]:
        """Generate performance optimization recommendations."""

        recommendations = []

        # Analyze results and generate specific recommendations
        if "real_codebases" in test_results:
            real_results = test_results["real_codebases"]

            slow_analyses = [
                name
                for name, result in real_results.items()
                if isinstance(result, dict) and result.get("files_per_second", 0) < 5
            ]

            if slow_analyses:
                recommendations.append(f"Consider parallel processing for slow analyses: {', '.join(slow_analyses)}")

        if "memory_stress" in test_results:
            memory_results = test_results["memory_stress"]

            high_memory_tests = [
                name
                for name, result in memory_results.items()
                if isinstance(result, dict) and result.get("memory_efficiency_kb_per_file", 0) > 512
            ]

            if high_memory_tests:
                recommendations.append("Implement memory optimization for large codebases")

        if "parallel_scaling" in test_results:
            parallel_results = test_results["parallel_scaling"]

            best_workers = (
                max(
                    (int(name.split("_")[1]), result.get("efficiency", 0))
                    for name, result in parallel_results.items()
                    if isinstance(result, dict) and "efficiency" in result
                )[0]
                if parallel_results
                else 1
            )

            recommendations.append(f"Optimal worker count appears to be {best_workers} for this system")

        if "caching_effectiveness" in test_results:
            cache_result = test_results["caching_effectiveness"]

            if isinstance(cache_result, dict):
                speedup = cache_result.get("cache_speedup", 1.0)
                if speedup < 1.5:
                    recommendations.append("Consider implementing more aggressive caching strategies")
                elif speedup > 3.0:
                    recommendations.append("Caching is highly effective - ensure it's enabled in production")

        # Generic recommendations if no specific bottlenecks found
        if not recommendations:
            recommendations = [
                "Performance appears acceptable - monitor in production",
                "Consider implementing incremental analysis for CI/CD pipelines",
                "Add performance regression tests to prevent degradation",
            ]

        return recommendations

    def _create_empty_result(self, test_name: str, codebase_path: str) -> BenchmarkResult:
        """Create empty benchmark result."""

        return BenchmarkResult(
            test_name=test_name,
            codebase_path=codebase_path,
            file_count=0,
            total_lines=0,
            execution_time_seconds=0.0,
            memory_peak_mb=0.0,
            memory_avg_mb=0.0,
            cpu_usage_percent=0.0,
            violations_found=0,
            files_analyzed=0,
            analysis_accuracy=0.0,
            files_per_second=0.0,
            lines_per_second=0.0,
            violations_per_second=0.0,
            memory_per_file_kb=0.0,
            cpu_time_per_file_ms=0.0,
            analyzer_mode="empty",
            parallel_workers=0,
            cache_enabled=False,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        )

    def _save_benchmark_results(self, results: Dict[str, Any]):
        """Save benchmark results to files."""

        timestamp = time.strftime("%Y%m%d_%H%M%S")

        # Save detailed JSON results
        json_file = self.output_dir / f"benchmark_results_{timestamp}.json"
        with open(json_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        # Save summary report
        summary_file = self.output_dir / f"benchmark_summary_{timestamp}.txt"
        with open(summary_file, "w") as f:
            f.write("Performance Benchmark Summary\n")
            f.write("=" * 50 + "\n\n")

            f.write(f"Benchmark Date: {results['benchmark_timestamp']}\n")
            f.write(f"Total Time: {results.get('total_benchmark_time', 0):.2f} seconds\n\n")

            # System info
            system_info = results.get("system_info", {})
            f.write("System Information:\n")
            f.write(f"  CPU Cores: {system_info.get('cpu_count', 'unknown')}\n")
            f.write(f"  Memory: {system_info.get('memory_total_gb', 0):.1f} GB\n")
            f.write(f"  Python: {system_info.get('python_version', 'unknown').split()[0]}\n\n")

            # Performance summary
            perf_summary = results.get("performance_summary", {})
            f.write("Performance Targets:\n")
            targets = perf_summary.get("performance_targets_met", {})
            for target, met in targets.items():
                status = "✓ PASS" if met else "✗ FAIL"
                f.write(f"  {target.replace('_', ' ').title()}: {status}\n")
            f.write("\n")

            # Recommendations
            recommendations = results.get("recommendations", [])
            f.write("Recommendations:\n")
            for i, rec in enumerate(recommendations, 1):
                f.write(f"  {i}. {rec}\n")
            f.write("\n")

        logger.info(f"Benchmark results saved to {json_file} and {summary_file}")


class ResourceMonitor:
    """Monitor system resources during benchmarking."""

    def __init__(self):
        self.monitoring_active = False
        self.resource_samples = []
        self.initial_memory = None

    def start_monitoring(self):
        """Start resource monitoring."""
        self.monitoring_active = True
        self.resource_samples = []

        # Record initial memory
        process = psutil.Process()
        self.initial_memory = process.memory_info().rss / 1024 / 1024

        # Start monitoring thread
        import threading

        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop_monitoring(self) -> Dict[str, float]:
        """Stop monitoring and return statistics."""
        self.monitoring_active = False

        if hasattr(self, "monitor_thread"):
            self.monitor_thread.join(timeout=2)

        if not self.resource_samples:
            return {
                "peak_memory_mb": self.initial_memory or 0,
                "avg_memory_mb": self.initial_memory or 0,
                "avg_cpu_percent": 0.0,
                "initial_memory_mb": self.initial_memory or 0,
            }

        memory_samples = [s["memory_mb"] for s in self.resource_samples]
        cpu_samples = [s["cpu_percent"] for s in self.resource_samples]

        return {
            "peak_memory_mb": max(memory_samples),
            "avg_memory_mb": sum(memory_samples) / len(memory_samples),
            "avg_cpu_percent": sum(cpu_samples) / len(cpu_samples),
            "initial_memory_mb": self.initial_memory or 0,
        }

    def _monitor_loop(self):
        """Monitor resources in background."""
        process = psutil.Process()

        while self.monitoring_active:
            try:
                memory_info = process.memory_info()
                cpu_percent = process.cpu_percent()

                sample = {
                    "timestamp": time.time(),
                    "memory_mb": memory_info.rss / 1024 / 1024,
                    "cpu_percent": cpu_percent,
                }

                self.resource_samples.append(sample)
                time.sleep(0.2)  # Sample every 200ms

            except Exception:
                break


def main():
    """Main entry point for benchmark runner."""

    import argparse

    parser = argparse.ArgumentParser(description="Performance Benchmark Runner")
    parser.add_argument("--output", "-o", default="tests/performance/results", help="Output directory for results")
    parser.add_argument("--codebase", "-c", help="Benchmark specific codebase path")
    parser.add_argument("--comprehensive", action="store_true", help="Run comprehensive benchmark suite")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Configure logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    benchmarker = PerformanceBenchmarker(args.output)

    if args.codebase:
        # Benchmark specific codebase
        result = benchmarker.benchmark_codebase(args.codebase)
        print(f"Benchmark Result: {result.files_per_second:.1f} files/sec, {result.violations_found} violations")

    elif args.comprehensive:
        # Run comprehensive benchmark
        results = benchmarker.run_comprehensive_benchmark()
        print("Comprehensive benchmark completed")
        print(f"Results saved to: {benchmarker.output_dir}")

    else:
        # Default: benchmark test packages
        print("Benchmarking test packages...")
        results = benchmarker._benchmark_real_codebases()

        for name, result in results.items():
            if isinstance(result, dict) and "files_per_second" in result:
                print(f"{name}: {result['files_per_second']:.1f} files/sec")
            else:
                print(f"{name}: Error or no data")


if __name__ == "__main__":
    main()
