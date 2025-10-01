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
Parallel Processing Enhancement for Connascence Analysis
=======================================================

Adds missing parallel processing capabilities to leverage existing infrastructure:
- Leverages existing performance tests (tests/performance/test_benchmarks.py - 449 lines)
- Integrates with existing metrics system (dashboard/metrics.py - 440 lines)
- Builds on existing concurrent testing (tests/e2e/test_performance.py - 1511 lines)

This module provides parallel analysis capabilities while maintaining compatibility
with the existing single-threaded analyzer infrastructure.
"""

from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
import logging
import multiprocessing as mp
from pathlib import Path
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import psutil

from fixes.phase0.production_safe_assertions import ProductionAssert

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import existing infrastructure
try:
    from analyzer.unified_analyzer import UnifiedAnalysisResult, UnifiedConnascenceAnalyzer
except ImportError:
    # Fallback for when unified analyzer is not available
    UnifiedConnascenceAnalyzer = None
    UnifiedAnalysisResult = None

try:
    from dashboard.metrics import DashboardMetrics
except ImportError:
    # Fallback metrics collector
    class DashboardMetrics:
        def record_performance(self, **kwargs):
            if kwargs:
                ProductionAssert.not_none(kwargs, "kwargs")

            pass


logger = logging.getLogger(__name__)


@dataclass
class ParallelAnalysisConfig:
    """Configuration for parallel analysis execution."""

    max_workers: int = field(default_factory=lambda: min(8, mp.cpu_count()))
    chunk_size: int = 5  # Files per chunk
    use_processes: bool = True  # True for CPU-bound tasks
    timeout_seconds: int = 300  # 5 minutes
    memory_limit_mb: int = 1024  # 1GB per worker
    enable_profiling: bool = False
    worker_initialization_timeout: int = 30


@dataclass
class ParallelAnalysisResult:
    """Result from parallel analysis execution."""

    # Combined results
    unified_result: UnifiedAnalysisResult

    # Performance metrics
    total_execution_time: float
    parallel_execution_time: float
    sequential_equivalent_time: float
    speedup_factor: float
    efficiency: float

    # Resource utilization
    peak_memory_mb: float
    avg_cpu_percent: float
    worker_count: int

    # Detailed breakdown
    worker_results: List[Dict[str, Any]]
    chunk_processing_times: List[float]
    coordination_overhead_ms: float


class ParallelConnascenceAnalyzer:
    """
    Enhanced analyzer with parallel processing capabilities.

    Integrates with existing infrastructure while adding parallel execution
    for improved performance on multi-core systems and large codebases.
    """

    def __init__(self, config: Optional[ParallelAnalysisConfig] = None):
        """Initialize parallel analyzer with configuration."""

        self.config = config or ParallelAnalysisConfig()
        self.base_analyzer = UnifiedConnascenceAnalyzer()
        self.metrics_collector = DashboardMetrics()

        # Performance tracking
        self.execution_stats = {}
        self.worker_pool = None
        self.resource_monitor = None

        logger.info(f"Parallel analyzer initialized with {self.config.max_workers} workers")

    def analyze_project_parallel(
        self,
        project_path: Union[str, Path],
        policy_preset: str = "service-defaults",
        options: Optional[Dict[str, Any]] = None,
    ) -> ParallelAnalysisResult:
        """
        Analyze project using parallel processing.

        Args:
            project_path: Path to project directory
            policy_preset: Policy configuration to use
            options: Additional analysis options

        Returns:
            Parallel analysis result with performance metrics
        """

        project_path = Path(project_path)
        options = options or {}
        start_time = time.time()

        logger.info(f"Starting parallel analysis of {project_path} with {self.config.max_workers} workers")

        # Start resource monitoring
        if self.config.enable_profiling:
            self.resource_monitor = ResourceMonitor()
            self.resource_monitor.start_monitoring()

        try:
            # Discover files to analyze
            files_to_analyze = self._discover_files(project_path)

            if not files_to_analyze:
                logger.warning(f"No files found to analyze in {project_path}")
                return self._create_empty_result(project_path, policy_preset, start_time)

            # Create file chunks for parallel processing
            file_chunks = self._create_file_chunks(files_to_analyze)

            logger.info(f"Processing {len(files_to_analyze)} files in {len(file_chunks)} chunks")

            # Execute parallel analysis
            chunk_results, chunk_times = self._execute_parallel_chunks(file_chunks, policy_preset, options)

            # Combine results from all chunks
            combined_result = self._combine_chunk_results(chunk_results, project_path, policy_preset, start_time)

            # Calculate performance metrics
            total_time = time.time() - start_time
            performance_metrics = self._calculate_performance_metrics(total_time, chunk_times, chunk_results)

            # Stop resource monitoring
            resource_stats = {}
            if self.resource_monitor:
                resource_stats = self.resource_monitor.stop_monitoring()

            # Create parallel analysis result
            parallel_result = ParallelAnalysisResult(
                unified_result=combined_result,
                total_execution_time=total_time,
                parallel_execution_time=performance_metrics["parallel_time"],
                sequential_equivalent_time=performance_metrics["sequential_equivalent"],
                speedup_factor=performance_metrics["speedup_factor"],
                efficiency=performance_metrics["efficiency"],
                peak_memory_mb=resource_stats.get("peak_memory_mb", 0),
                avg_cpu_percent=resource_stats.get("avg_cpu_percent", 0),
                worker_count=self.config.max_workers,
                worker_results=chunk_results,
                chunk_processing_times=chunk_times,
                coordination_overhead_ms=performance_metrics["coordination_overhead"],
            )

            # Record performance metrics
            self._record_performance_metrics(parallel_result)

            logger.info(
                f"Parallel analysis complete in {total_time:.2f}s (speedup: {performance_metrics['speedup_factor']:.1f}x)"
            )

            return parallel_result

        except Exception as e:
            logger.error(f"Parallel analysis failed: {e}")

            # Fallback to sequential analysis
            logger.info("Falling back to sequential analysis")
            return self._fallback_sequential_analysis(project_path, policy_preset, options, start_time)

    def analyze_files_batch(
        self, file_paths: List[Union[str, Path]], policy_preset: str = "service-defaults"
    ) -> Dict[str, Any]:
        """
        Analyze a batch of files in parallel.

        Args:
            file_paths: List of file paths to analyze
            policy_preset: Policy configuration to use

        Returns:
            Combined analysis results for all files
        """

        start_time = time.time()

        # Create chunks from file list
        file_chunks = self._create_file_chunks([Path(f) for f in file_paths])

        # Execute parallel analysis on chunks
        chunk_results, chunk_times = self._execute_parallel_chunks(file_chunks, policy_preset, {})

        # Combine results
        all_violations = []
        all_nasa_violations = []
        all_duplication_clusters = []

        for result in chunk_results:
            if "violations" in result:
                all_violations.extend(result["violations"])
            if "nasa_violations" in result:
                all_nasa_violations.extend(result["nasa_violations"])
            if "duplication_clusters" in result:
                all_duplication_clusters.extend(result["duplication_clusters"])

        total_time = time.time() - start_time

        return {
            "files_analyzed": len(file_paths),
            "total_violations": len(all_violations),
            "violations": all_violations,
            "nasa_violations": all_nasa_violations,
            "duplication_clusters": all_duplication_clusters,
            "execution_time_ms": total_time * 1000,
            "parallel_processing": True,
            "worker_count": self.config.max_workers,
            "chunk_count": len(file_chunks),
        }

    def benchmark_parallel_performance(self, test_project_sizes: List[int] = None) -> Dict[str, Any]:
        """
        Benchmark parallel processing performance against sequential processing.

        Args:
            test_project_sizes: List of project sizes to test (number of files)

        Returns:
            Comprehensive performance comparison results
        """

        test_sizes = test_project_sizes or [10, 25, 50, 100]
        benchmark_results = {}

        logger.info("Starting parallel processing benchmark")

        for size in test_sizes:
            logger.info(f"Benchmarking with {size} files")

            # Create test project
            test_files = self._create_test_project(size)

            # Sequential baseline
            sequential_time = self._benchmark_sequential(test_files)

            # Parallel execution
            parallel_time = self._benchmark_parallel(test_files)

            # Calculate metrics
            speedup = sequential_time / max(parallel_time, 0.001)
            efficiency = speedup / self.config.max_workers

            benchmark_results[f"files_{size}"] = {
                "file_count": size,
                "sequential_time_s": sequential_time,
                "parallel_time_s": parallel_time,
                "speedup_factor": speedup,
                "efficiency": efficiency,
                "worker_count": self.config.max_workers,
                "performance_improvement": ((sequential_time - parallel_time) / sequential_time) * 100,
            }

            logger.info(f"Size {size}: {speedup:.1f}x speedup ({efficiency:.2f} efficiency)")

        # Overall benchmark summary
        overall_speedup = sum(r["speedup_factor"] for r in benchmark_results.values()) / len(benchmark_results)
        overall_efficiency = sum(r["efficiency"] for r in benchmark_results.values()) / len(benchmark_results)

        return {
            "benchmark_timestamp": time.time(),
            "test_sizes": test_sizes,
            "individual_results": benchmark_results,
            "overall_metrics": {
                "average_speedup": overall_speedup,
                "average_efficiency": overall_efficiency,
                "optimal_worker_count": self.config.max_workers,
                "cpu_cores_available": mp.cpu_count(),
                "parallel_processing_effective": overall_speedup > 1.2,
            },
        }

    # Private implementation methods

    def _discover_files(self, project_path: Path) -> List[Path]:
        """Discover Python files to analyze in the project."""

        files = []

        # Common Python file patterns
        patterns = ["**/*.py"]

        # Exclusion patterns
        exclude_patterns = [
            "**/node_modules/**",
            "**/venv/**",
            "**/env/**",
            "**/__pycache__/**",
            "**/build/**",
            "**/dist/**",
            "**/.git/**",
        ]

        for pattern in patterns:
            for file_path in project_path.glob(pattern):
                if file_path.is_file():
                    # Check exclusions
                    should_exclude = False
                    for exclude_pattern in exclude_patterns:
                        if file_path.match(exclude_pattern):
                            should_exclude = True
                            break

                    if not should_exclude and file_path.stat().st_size < 10 * 1024 * 1024:  # Skip files > 10MB
                        files.append(file_path)

        return sorted(files)

    def _create_file_chunks(self, files: List[Path]) -> List[List[Path]]:
        """Create chunks of files for parallel processing."""

        chunks = []
        chunk_size = self.config.chunk_size

        for i in range(0, len(files), chunk_size):
            chunk = files[i : i + chunk_size]
            chunks.append(chunk)

        return chunks

    def _execute_parallel_chunks(
        self, file_chunks: List[List[Path]], policy_preset: str, options: Dict[str, Any]
    ) -> Tuple[List[Dict], List[float]]:
        """Execute analysis on file chunks in parallel."""

        chunk_results = []
        chunk_times = []

        executor_class = ProcessPoolExecutor if self.config.use_processes else ThreadPoolExecutor

        with executor_class(max_workers=self.config.max_workers) as executor:
            # Submit all chunks for processing
            future_to_chunk = {
                executor.submit(self._analyze_chunk, chunk, policy_preset, options): i
                for i, chunk in enumerate(file_chunks)
            }

            # Collect results as they complete
            for future in as_completed(future_to_chunk, timeout=self.config.timeout_seconds):
                chunk_index = future_to_chunk[future]

                try:
                    start_time = time.time()
                    result = future.result()
                    processing_time = time.time() - start_time

                    chunk_results.append(result)
                    chunk_times.append(processing_time)

                    logger.debug(f"Chunk {chunk_index} completed in {processing_time:.2f}s")

                except Exception as e:
                    logger.error(f"Chunk {chunk_index} failed: {e}")
                    # Add empty result to maintain ordering
                    chunk_results.append(
                        {"error": str(e), "violations": [], "nasa_violations": [], "duplication_clusters": []}
                    )
                    chunk_times.append(0.0)

        return chunk_results, chunk_times

    def _analyze_chunk(self, file_chunk: List[Path], policy_preset: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a chunk of files (executed in worker process/thread)."""

        try:
            # Create analyzer instance for this worker
            analyzer = UnifiedConnascenceAnalyzer()

            all_violations = []
            all_nasa_violations = []
            all_duplication_clusters = []

            for file_path in file_chunk:
                try:
                    # Analyze individual file
                    file_result = analyzer.analyze_file(file_path)

                    # Extract violations
                    if "connascence_violations" in file_result:
                        all_violations.extend(file_result["connascence_violations"])

                    if "nasa_violations" in file_result:
                        all_nasa_violations.extend(file_result["nasa_violations"])

                except Exception as e:
                    logger.warning(f"Failed to analyze {file_path}: {e}")
                    continue

            return {
                "chunk_size": len(file_chunk),
                "files_processed": len(file_chunk),
                "violations": all_violations,
                "nasa_violations": all_nasa_violations,
                "duplication_clusters": all_duplication_clusters,
                "processing_successful": True,
            }

        except Exception as e:
            logger.error(f"Chunk analysis failed: {e}")
            return {
                "chunk_size": len(file_chunk),
                "files_processed": 0,
                "violations": [],
                "nasa_violations": [],
                "duplication_clusters": [],
                "processing_successful": False,
                "error": str(e),
            }

    def _combine_chunk_results(
        self, chunk_results: List[Dict], project_path: Path, policy_preset: str, start_time: float
    ) -> UnifiedAnalysisResult:
        """Combine results from all chunks into unified result."""

        # Aggregate all violations
        all_connascence_violations = []
        all_nasa_violations = []
        all_duplication_clusters = []
        files_processed = 0

        for result in chunk_results:
            if result.get("processing_successful", False):
                all_connascence_violations.extend(result.get("violations", []))
                all_nasa_violations.extend(result.get("nasa_violations", []))
                all_duplication_clusters.extend(result.get("duplication_clusters", []))
                files_processed += result.get("files_processed", 0)

        # Calculate severity counts
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for violation in all_connascence_violations:
            severity = violation.get("severity", "medium")
            if severity in severity_counts:
                severity_counts[severity] += 1

        # Calculate quality metrics
        connascence_index = self._calculate_connascence_index(all_connascence_violations)
        nasa_compliance_score = self._calculate_nasa_compliance(all_nasa_violations)
        duplication_score = max(0.0, 1.0 - (len(all_duplication_clusters) * 0.1))

        # Overall quality score (weighted average)
        overall_quality_score = (
            (max(0.0, 1.0 - connascence_index * 0.01) * 0.4) + (nasa_compliance_score * 0.3) + (duplication_score * 0.3)
        )

        # Generate recommendations
        priority_fixes = []
        improvement_actions = []

        critical_violations = [v for v in all_connascence_violations if v.get("severity") == "critical"]
        for violation in critical_violations[:3]:
            priority_fixes.append(
                f"Fix critical {violation.get('type', 'violation')} in {violation.get('file_path', 'unknown')}"
            )

        if len(all_nasa_violations) > 0:
            improvement_actions.append(f"Address {len(all_nasa_violations)} NASA Power of Ten compliance issues")

        if len(all_duplication_clusters) > 0:
            improvement_actions.append(f"Refactor {len(all_duplication_clusters)} code duplication clusters")

        # Create unified result
        return UnifiedAnalysisResult(
            connascence_violations=all_connascence_violations,
            duplication_clusters=all_duplication_clusters,
            nasa_violations=all_nasa_violations,
            total_violations=len(all_connascence_violations),
            critical_count=severity_counts["critical"],
            high_count=severity_counts["high"],
            medium_count=severity_counts["medium"],
            low_count=severity_counts["low"],
            connascence_index=connascence_index,
            nasa_compliance_score=nasa_compliance_score,
            duplication_score=duplication_score,
            overall_quality_score=overall_quality_score,
            project_path=str(project_path),
            policy_preset=policy_preset,
            analysis_duration_ms=int((time.time() - start_time) * 1000),
            files_analyzed=files_processed,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
            priority_fixes=priority_fixes,
            improvement_actions=improvement_actions,
        )

    def _calculate_performance_metrics(
        self, total_time: float, chunk_times: List[float], chunk_results: List[Dict]
    ) -> Dict[str, Any]:
        """Calculate detailed performance metrics."""

        # Parallel execution time is the maximum chunk time (bottleneck)
        parallel_time = max(chunk_times) if chunk_times else total_time

        # Sequential equivalent is sum of all chunk times
        sequential_equivalent = sum(chunk_times)

        # Speedup and efficiency
        speedup_factor = sequential_equivalent / max(parallel_time, 0.001)
        efficiency = speedup_factor / self.config.max_workers

        # Coordination overhead
        coordination_overhead = (total_time - parallel_time) * 1000  # Convert to ms

        return {
            "parallel_time": parallel_time,
            "sequential_equivalent": sequential_equivalent,
            "speedup_factor": speedup_factor,
            "efficiency": efficiency,
            "coordination_overhead": coordination_overhead,
        }

    def _calculate_connascence_index(self, violations: List[Dict]) -> float:
        """Calculate connascence index from violations."""
        weight_map = {"critical": 10, "high": 5, "medium": 2, "low": 1}

        total_weight = 0
        for violation in violations:
            severity = violation.get("severity", "medium")
            weight = violation.get("weight", 1)
            total_weight += weight_map.get(severity, 1) * weight

        return round(total_weight, 2)

    def _calculate_nasa_compliance(self, nasa_violations: List[Dict]) -> float:
        """Calculate NASA compliance score."""
        if not nasa_violations:
            return 1.0

        # Weight violations by severity
        severity_weights = {"critical": 0.3, "high": 0.2, "medium": 0.1, "low": 0.05}

        total_penalty = 0.0
        for violation in nasa_violations:
            severity = violation.get("severity", "medium")
            penalty = severity_weights.get(severity, 0.1)
            total_penalty += penalty

        return max(0.0, 1.0 - total_penalty)

    def _record_performance_metrics(self, result: ParallelAnalysisResult):
        """Record performance metrics for analysis."""

        self.metrics_collector.record_performance(
            operation_type="parallel_analysis",
            duration=result.total_execution_time,
            file_count=result.unified_result.files_analyzed,
            violation_count=result.unified_result.total_violations,
        )

        # Log detailed performance info
        logger.info("Performance Summary:")
        logger.info(f"  Total time: {result.total_execution_time:.2f}s")
        logger.info(f"  Speedup: {result.speedup_factor:.1f}x")
        logger.info(f"  Efficiency: {result.efficiency:.2f}")
        logger.info(f"  Workers: {result.worker_count}")
        logger.info(f"  Files/sec: {result.unified_result.files_analyzed / result.total_execution_time:.1f}")

    def _create_empty_result(self, project_path: Path, policy_preset: str, start_time: float) -> ParallelAnalysisResult:
        """Create empty result when no files are found."""

        empty_unified = UnifiedAnalysisResult(
            connascence_violations=[],
            duplication_clusters=[],
            nasa_violations=[],
            total_violations=0,
            critical_count=0,
            high_count=0,
            medium_count=0,
            low_count=0,
            connascence_index=0.0,
            nasa_compliance_score=1.0,
            duplication_score=1.0,
            overall_quality_score=1.0,
            project_path=str(project_path),
            policy_preset=policy_preset,
            analysis_duration_ms=int((time.time() - start_time) * 1000),
            files_analyzed=0,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
            priority_fixes=[],
            improvement_actions=[],
        )

        return ParallelAnalysisResult(
            unified_result=empty_unified,
            total_execution_time=time.time() - start_time,
            parallel_execution_time=0.0,
            sequential_equivalent_time=0.0,
            speedup_factor=1.0,
            efficiency=1.0,
            peak_memory_mb=0.0,
            avg_cpu_percent=0.0,
            worker_count=0,
            worker_results=[],
            chunk_processing_times=[],
            coordination_overhead_ms=0.0,
        )

    def _fallback_sequential_analysis(
        self, project_path: Path, policy_preset: str, options: Dict[str, Any], start_time: float
    ) -> ParallelAnalysisResult:
        """Fallback to sequential analysis when parallel processing fails."""

        logger.info("Executing fallback sequential analysis")

        sequential_result = self.base_analyzer.analyze_project(project_path, policy_preset, options)
        total_time = time.time() - start_time

        return ParallelAnalysisResult(
            unified_result=sequential_result,
            total_execution_time=total_time,
            parallel_execution_time=total_time,
            sequential_equivalent_time=total_time,
            speedup_factor=1.0,
            efficiency=1.0,
            peak_memory_mb=0.0,
            avg_cpu_percent=0.0,
            worker_count=1,
            worker_results=[],
            chunk_processing_times=[total_time],
            coordination_overhead_ms=0.0,
        )

    def _create_test_project(self, file_count: int) -> List[Path]:
        """Create test project files for benchmarking."""

        import tempfile

        temp_dir = Path(tempfile.mkdtemp())
        test_files = []

        for i in range(file_count):
            test_file = temp_dir / f"test_file_{i:03d}.py"

            # Create file with various violations for realistic testing
            content = f"""
def test_function_{i}(param1, param2, param3, param4, param5):  # Parameter bomb
    magic_value = {100 + i * 10}  # Magic literal
    secret_key = "test_key_{i}"  # Magic string

    if param1 > magic_value:
        return param1 * {2.0 + i * 0.1}  # Magic literal
    return param1

class TestClass_{i}:
    def method_01(self): pass
    def method_02(self): pass
    def method_03(self): pass
    def method_04(self): pass
    def method_05(self): pass
    def method_06(self): pass
    def method_07(self): pass
    def method_08(self): pass
    def method_09(self): pass
    def method_10(self): pass
    def method_11(self): pass
    def method_12(self): pass
    def method_13(self): pass
    def method_14(self): pass
    def method_15(self): pass
    def method_16(self): pass
    def method_17(self): pass
    def method_18(self): pass
    def method_19(self): pass
    def method_20(self): pass
    def method_21(self): pass  # God class
"""

            test_file.write_text(content)
            test_files.append(test_file)

        return test_files

    def _benchmark_sequential(self, test_files: List[Path]) -> float:
        """Benchmark sequential processing time."""

        start_time = time.time()

        for file_path in test_files:
            self.base_analyzer.analyze_file(file_path)

        return time.time() - start_time

    def _benchmark_parallel(self, test_files: List[Path]) -> float:
        """Benchmark parallel processing time."""

        start_time = time.time()

        # Use batch analysis for parallel execution
        self.analyze_files_batch(test_files)

        return time.time() - start_time


class ResourceMonitor:
    """Monitor system resources during parallel analysis."""

    def __init__(self):
        self.monitoring_active = False
        self.resource_samples = []
        self.monitoring_thread = None

    def start_monitoring(self):
        """Start resource monitoring in background thread."""
        self.monitoring_active = True
        self.resource_samples = []

        self.monitoring_thread = threading.Thread(target=self._monitor_resources)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()

    def stop_monitoring(self) -> Dict[str, Any]:
        """Stop monitoring and return resource usage summary."""
        self.monitoring_active = False

        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)

        if not self.resource_samples:
            return {"error": "No resource samples collected"}

        # Calculate statistics
        memory_samples = [s["memory_mb"] for s in self.resource_samples]
        cpu_samples = [s["cpu_percent"] for s in self.resource_samples]

        return {
            "samples_collected": len(self.resource_samples),
            "peak_memory_mb": max(memory_samples) if memory_samples else 0,
            "avg_memory_mb": sum(memory_samples) / len(memory_samples) if memory_samples else 0,
            "avg_cpu_percent": sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0,
            "max_cpu_percent": max(cpu_samples) if cpu_samples else 0,
        }

    def _monitor_resources(self):
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
                time.sleep(0.5)  # Sample every 500ms

            except Exception:
                break


# Global instance for easy access
parallel_analyzer = ParallelConnascenceAnalyzer()
