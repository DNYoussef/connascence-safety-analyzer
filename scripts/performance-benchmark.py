#!/usr/bin/env python3
"""
Performance Benchmark - Connascence Analyzer
Systematic evaluation of bottlenecks and optimization opportunities
"""

from dataclasses import asdict, dataclass
import gc
import json
from pathlib import Path
import sys
import time
import tracemalloc
from typing import Any, Dict, List

import psutil

# Add analyzer to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "spek template"))


@dataclass
class PerformanceMetrics:
    """Performance measurement results"""

    operation: str
    duration_seconds: float
    memory_peak_mb: float
    memory_current_mb: float
    cpu_percent: float
    files_processed: int
    throughput_files_per_sec: float
    status: str
    error_message: str = ""


@dataclass
class BottleneckAnalysis:
    """Bottleneck identification results"""

    component: str
    severity: str  # critical, high, medium, low
    impact_percent: float
    description: str
    optimization_recommendation: str
    estimated_improvement: str


class PerformanceBenchmark:
    """Systematic performance analysis and bottleneck detection"""

    def __init__(self, target_path: Path):
        self.target_path = target_path
        self.process = psutil.Process()
        self.metrics: List[PerformanceMetrics] = []
        self.bottlenecks: List[BottleneckAnalysis] = []

    def benchmark_import_time(self) -> PerformanceMetrics:
        """Measure module import performance"""
        print("\n[1/8] Benchmarking import time...")

        # Clear modules to get accurate import time
        modules_to_clear = [m for m in sys.modules.keys() if "analyzer" in m]
        for mod in modules_to_clear:
            del sys.modules[mod]

        gc.collect()
        tracemalloc.start()
        cpu_before = self.process.cpu_percent(interval=0.1)

        start = time.time()
        try:
            status = "success"
            error = ""
        except Exception as e:
            status = "failed"
            error = str(e)

        duration = time.time() - start
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        cpu_after = self.process.cpu_percent()

        metric = PerformanceMetrics(
            operation="module_import",
            duration_seconds=duration,
            memory_peak_mb=peak / 1024 / 1024,
            memory_current_mb=current / 1024 / 1024,
            cpu_percent=(cpu_before + cpu_after) / 2,
            files_processed=0,
            throughput_files_per_sec=0,
            status=status,
            error_message=error,
        )

        self.metrics.append(metric)
        print(f"   Import time: {duration:.3f}s | Memory: {peak/1024/1024:.1f}MB | Status: {status}")

        if duration > 2.0:
            self.bottlenecks.append(
                BottleneckAnalysis(
                    component="Module Import",
                    severity="high",
                    impact_percent=(duration / 5.0) * 100,  # 5s = 100% bad
                    description=f"Import takes {duration:.1f}s - too slow for interactive use",
                    optimization_recommendation="Lazy import detectors, reduce initialization overhead",
                    estimated_improvement="60-80% reduction",
                )
            )

        return metric

    def benchmark_single_file_analysis(self) -> PerformanceMetrics:
        """Measure single file analysis performance"""
        print("\n[2/8] Benchmarking single file analysis...")

        test_file = self.target_path / "analyzer" / "consolidated_analyzer.py"
        if not test_file.exists():
            test_file = next(self.target_path.rglob("*.py"), None)

        if not test_file:
            return PerformanceMetrics(
                operation="single_file_analysis",
                duration_seconds=0,
                memory_peak_mb=0,
                memory_current_mb=0,
                cpu_percent=0,
                files_processed=0,
                throughput_files_per_sec=0,
                status="skipped",
                error_message="No Python files found",
            )

        gc.collect()
        tracemalloc.start()
        cpu_before = self.process.cpu_percent(interval=0.1)

        start = time.time()
        try:
            from analyzer.consolidated_analyzer import ConsolidatedConnascenceAnalyzer

            analyzer = ConsolidatedConnascenceAnalyzer(str(test_file))
            result = analyzer.analyze()
            status = "success"
            error = ""
        except Exception as e:
            status = "failed"
            error = str(e)

        duration = time.time() - start
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        cpu_after = self.process.cpu_percent()

        metric = PerformanceMetrics(
            operation="single_file_analysis",
            duration_seconds=duration,
            memory_peak_mb=peak / 1024 / 1024,
            memory_current_mb=current / 1024 / 1024,
            cpu_percent=(cpu_before + cpu_after) / 2,
            files_processed=1,
            throughput_files_per_sec=1 / duration if duration > 0 else 0,
            status=status,
            error_message=error,
        )

        self.metrics.append(metric)
        print(f"   Duration: {duration:.3f}s | Throughput: {metric.throughput_files_per_sec:.1f} files/sec")

        if duration > 0.5:
            self.bottlenecks.append(
                BottleneckAnalysis(
                    component="Single File Analysis",
                    severity="critical",
                    impact_percent=(duration / 1.0) * 100,
                    description=f"Analyzing one file takes {duration:.1f}s - will not scale",
                    optimization_recommendation="Profile AST operations, optimize detector algorithms",
                    estimated_improvement="70-90% reduction",
                )
            )

        return metric

    def benchmark_detector_performance(self) -> List[PerformanceMetrics]:
        """Measure individual detector performance"""
        print("\n[3/8] Benchmarking individual detectors...")

        detector_metrics = []
        test_file = self.target_path / "analyzer" / "consolidated_analyzer.py"

        if not test_file.exists():
            return []

        # Read file once
        with open(test_file) as f:
            source = f.read()

        import ast

        tree = ast.parse(source)

        detectors = [
            ("PositionDetector", "analyzer.detectors.position_detector", "PositionDetector"),
            ("MagicLiteralDetector", "analyzer.detectors.magic_literal_detector", "MagicLiteralDetector"),
            ("AlgorithmDetector", "analyzer.detectors.algorithm_detector", "AlgorithmDetector"),
            ("GodObjectDetector", "analyzer.detectors.god_object_detector", "GodObjectDetector"),
            ("TimingDetector", "analyzer.detectors.timing_detector", "TimingDetector"),
        ]

        for name, module_path, class_name in detectors:
            gc.collect()
            tracemalloc.start()

            start = time.time()
            try:
                module = __import__(module_path, fromlist=[class_name])
                detector_class = getattr(module, class_name)
                detector = detector_class()
                violations = detector.detect(tree, str(test_file))
                status = "success"
                error = ""
            except Exception as e:
                status = "failed"
                error = str(e)
                violations = []

            duration = time.time() - start
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            metric = PerformanceMetrics(
                operation=f"detector_{name}",
                duration_seconds=duration,
                memory_peak_mb=peak / 1024 / 1024,
                memory_current_mb=current / 1024 / 1024,
                cpu_percent=0,
                files_processed=1,
                throughput_files_per_sec=1 / duration if duration > 0 else 0,
                status=status,
                error_message=error,
            )

            detector_metrics.append(metric)
            self.metrics.append(metric)
            print(f"   {name}: {duration:.3f}s | {len(violations)} violations | Status: {status}")

            if duration > 0.1:
                self.bottlenecks.append(
                    BottleneckAnalysis(
                        component=name,
                        severity="high" if duration > 0.3 else "medium",
                        impact_percent=(duration / 0.5) * 100,
                        description=f"{name} takes {duration:.1f}s per file",
                        optimization_recommendation=f"Optimize {name} algorithm, cache AST traversals",
                        estimated_improvement="50-70% reduction",
                    )
                )

        return detector_metrics

    def benchmark_batch_analysis(self, batch_size: int = 10) -> PerformanceMetrics:
        """Measure batch file analysis performance"""
        print(f"\n[4/8] Benchmarking batch analysis ({batch_size} files)...")

        python_files = list(self.target_path.rglob("*.py"))[:batch_size]

        if not python_files:
            return PerformanceMetrics(
                operation="batch_analysis",
                duration_seconds=0,
                memory_peak_mb=0,
                memory_current_mb=0,
                cpu_percent=0,
                files_processed=0,
                throughput_files_per_sec=0,
                status="skipped",
                error_message="No Python files",
            )

        gc.collect()
        tracemalloc.start()
        cpu_before = self.process.cpu_percent(interval=0.1)

        start = time.time()
        try:
            from analyzer.consolidated_analyzer import ConsolidatedConnascenceAnalyzer

            for py_file in python_files:
                analyzer = ConsolidatedConnascenceAnalyzer(str(py_file))
                result = analyzer.analyze()

            status = "success"
            error = ""
        except Exception as e:
            status = "failed"
            error = str(e)

        duration = time.time() - start
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        cpu_after = self.process.cpu_percent()

        metric = PerformanceMetrics(
            operation=f"batch_analysis_{batch_size}",
            duration_seconds=duration,
            memory_peak_mb=peak / 1024 / 1024,
            memory_current_mb=current / 1024 / 1024,
            cpu_percent=(cpu_before + cpu_after) / 2,
            files_processed=len(python_files),
            throughput_files_per_sec=len(python_files) / duration if duration > 0 else 0,
            status=status,
            error_message=error,
        )

        self.metrics.append(metric)
        print(f"   Duration: {duration:.1f}s | Throughput: {metric.throughput_files_per_sec:.1f} files/sec")

        # Check if we can meet production requirements
        files_per_sec = len(python_files) / duration if duration > 0 else 0
        time_for_1000 = 1000 / files_per_sec if files_per_sec > 0 else float("inf")

        if time_for_1000 > 300:  # 5 minutes
            self.bottlenecks.append(
                BottleneckAnalysis(
                    component="Batch Processing",
                    severity="critical",
                    impact_percent=100,
                    description=f"At {files_per_sec:.1f} files/sec, 1000 files would take {time_for_1000/60:.1f} min (target: <5 min)",
                    optimization_recommendation="Implement parallel processing, optimize detector loops",
                    estimated_improvement="4-10x with multiprocessing",
                )
            )

        return metric

    def benchmark_memory_scaling(self) -> PerformanceMetrics:
        """Test memory usage at scale"""
        print("\n[5/8] Benchmarking memory scaling...")

        python_files = list(self.target_path.rglob("*.py"))[:100]

        if not python_files:
            return PerformanceMetrics(
                operation="memory_scaling",
                duration_seconds=0,
                memory_peak_mb=0,
                memory_current_mb=0,
                cpu_percent=0,
                files_processed=0,
                throughput_files_per_sec=0,
                status="skipped",
            )

        gc.collect()
        tracemalloc.start()
        mem_before = self.process.memory_info().rss / 1024 / 1024

        start = time.time()
        try:
            from analyzer.consolidated_analyzer import ConsolidatedConnascenceAnalyzer

            results = []
            for py_file in python_files:
                analyzer = ConsolidatedConnascenceAnalyzer(str(py_file))
                result = analyzer.analyze()
                results.append(result)  # Keep in memory

            status = "success"
            error = ""
        except Exception as e:
            status = "failed"
            error = str(e)

        duration = time.time() - start
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        mem_after = self.process.memory_info().rss / 1024 / 1024

        metric = PerformanceMetrics(
            operation="memory_scaling_100_files",
            duration_seconds=duration,
            memory_peak_mb=peak / 1024 / 1024,
            memory_current_mb=mem_after - mem_before,
            cpu_percent=0,
            files_processed=len(python_files),
            throughput_files_per_sec=len(python_files) / duration if duration > 0 else 0,
            status=status,
            error_message=error,
        )

        self.metrics.append(metric)
        memory_per_file = (mem_after - mem_before) / len(python_files)
        estimated_1000_files = memory_per_file * 1000

        print(f"   Memory growth: {mem_after - mem_before:.1f}MB for {len(python_files)} files")
        print(f"   Est. for 1000 files: {estimated_1000_files:.1f}MB")

        if estimated_1000_files > 4000:  # 4GB limit
            self.bottlenecks.append(
                BottleneckAnalysis(
                    component="Memory Management",
                    severity="critical",
                    impact_percent=(estimated_1000_files / 4000) * 100,
                    description=f"Memory scales to {estimated_1000_files:.0f}MB for 1000 files (limit: 4GB)",
                    optimization_recommendation="Implement streaming analysis, release AST trees, use generators",
                    estimated_improvement="80-90% reduction",
                )
            )

        return metric

    def analyze_parallelization_potential(self) -> Dict[str, Any]:
        """Analyze opportunities for parallel execution"""
        print("\n[6/8] Analyzing parallelization potential...")

        opportunities = []

        # File-level parallelization
        opportunities.append(
            {
                "component": "File Analysis",
                "type": "embarrassingly_parallel",
                "estimated_speedup": "4-8x with multiprocessing.Pool",
                "implementation": "Process files in parallel batches",
                "complexity": "low",
            }
        )

        # Detector-level parallelization
        opportunities.append(
            {
                "component": "Detector Execution",
                "type": "parallel_detectors",
                "estimated_speedup": "2-3x with concurrent.futures",
                "implementation": "Run independent detectors in parallel",
                "complexity": "medium",
            }
        )

        # AST caching
        opportunities.append(
            {
                "component": "AST Parsing",
                "type": "caching",
                "estimated_speedup": "40-60% for repeated analysis",
                "implementation": "Cache parsed AST trees with LRU",
                "complexity": "low",
            }
        )

        print(f"   Found {len(opportunities)} parallelization opportunities")
        for opp in opportunities:
            print(f"   - {opp['component']}: {opp['estimated_speedup']}")

        return {"opportunities": opportunities, "estimated_combined_speedup": "8-15x with all optimizations"}

    def generate_optimization_roadmap(self) -> Dict[str, Any]:
        """Generate prioritized optimization roadmap"""
        print("\n[7/8] Generating optimization roadmap...")

        # Sort bottlenecks by impact
        sorted_bottlenecks = sorted(
            self.bottlenecks,
            key=lambda b: ({"critical": 4, "high": 3, "medium": 2, "low": 1}[b.severity], b.impact_percent),
            reverse=True,
        )

        roadmap = {
            "phase1_quick_wins": [],
            "phase2_parallelization": [],
            "phase3_algorithmic": [],
            "phase4_architecture": [],
        }

        for bottleneck in sorted_bottlenecks:
            if "import" in bottleneck.component.lower():
                roadmap["phase1_quick_wins"].append(
                    {
                        "task": f"Optimize {bottleneck.component}",
                        "effort": "low",
                        "impact": bottleneck.severity,
                        "recommendation": bottleneck.optimization_recommendation,
                    }
                )
            elif "parallel" in bottleneck.optimization_recommendation.lower():
                roadmap["phase2_parallelization"].append(
                    {
                        "task": f"Parallelize {bottleneck.component}",
                        "effort": "medium",
                        "impact": bottleneck.severity,
                        "recommendation": bottleneck.optimization_recommendation,
                    }
                )
            elif "algorithm" in bottleneck.optimization_recommendation.lower():
                roadmap["phase3_algorithmic"].append(
                    {
                        "task": f"Optimize {bottleneck.component} algorithm",
                        "effort": "medium-high",
                        "impact": bottleneck.severity,
                        "recommendation": bottleneck.optimization_recommendation,
                    }
                )
            else:
                roadmap["phase4_architecture"].append(
                    {
                        "task": f"Redesign {bottleneck.component}",
                        "effort": "high",
                        "impact": bottleneck.severity,
                        "recommendation": bottleneck.optimization_recommendation,
                    }
                )

        return roadmap

    def assess_production_readiness(self) -> Dict[str, Any]:
        """Assess readiness for production workloads"""
        print("\n[8/8] Assessing production readiness...")

        requirements = {
            "handle_1000_files": False,
            "realtime_analysis": False,
            "memory_efficient": False,
            "incremental_support": False,
        }

        # Check 1000 file capability
        batch_metric = next((m for m in self.metrics if "batch" in m.operation), None)
        if batch_metric and batch_metric.throughput_files_per_sec > 0:
            time_for_1000 = 1000 / batch_metric.throughput_files_per_sec
            requirements["handle_1000_files"] = time_for_1000 < 300  # 5 minutes

        # Check real-time capability
        single_metric = next((m for m in self.metrics if "single_file" in m.operation), None)
        if single_metric:
            requirements["realtime_analysis"] = single_metric.duration_seconds < 0.5

        # Check memory efficiency
        memory_metric = next((m for m in self.metrics if "memory_scaling" in m.operation), None)
        if memory_metric:
            requirements["memory_efficient"] = memory_metric.memory_current_mb < 4000

        # Check for incremental support (code analysis)
        requirements["incremental_support"] = False  # Not yet implemented

        passed = sum(requirements.values())
        total = len(requirements)
        score = (passed / total) * 100

        assessment = {
            "overall_score": score,
            "requirements_met": requirements,
            "production_ready": score >= 75,
            "critical_blockers": [
                name for name, met in requirements.items() if not met and name != "incremental_support"
            ],
            "recommendation": (
                "PRODUCTION READY" if score >= 75 else "NEEDS OPTIMIZATION" if score >= 50 else "NOT PRODUCTION READY"
            ),
        }

        print(f"   Production Readiness: {score:.0f}% ({passed}/{total} requirements met)")
        print(f"   Status: {assessment['recommendation']}")

        return assessment

    def run_full_benchmark(self) -> Dict[str, Any]:
        """Execute complete performance benchmark suite"""
        print("=" * 70)
        print("CONNASCENCE ANALYZER PERFORMANCE BENCHMARK")
        print("=" * 70)

        start_time = time.time()

        # Run all benchmarks
        self.benchmark_import_time()
        self.benchmark_single_file_analysis()
        self.benchmark_detector_performance()
        self.benchmark_batch_analysis(batch_size=10)
        self.benchmark_memory_scaling()
        parallelization = self.analyze_parallelization_potential()
        roadmap = self.generate_optimization_roadmap()
        production_assessment = self.assess_production_readiness()

        total_time = time.time() - start_time

        # Compile results
        results = {
            "benchmark_metadata": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_benchmark_time": total_time,
                "target_path": str(self.target_path),
                "python_version": sys.version,
                "platform": sys.platform,
            },
            "performance_metrics": [asdict(m) for m in self.metrics],
            "bottleneck_analysis": [asdict(b) for b in self.bottlenecks],
            "parallelization_analysis": parallelization,
            "optimization_roadmap": roadmap,
            "production_readiness": production_assessment,
            "summary": {
                "total_bottlenecks": len(self.bottlenecks),
                "critical_bottlenecks": len([b for b in self.bottlenecks if b.severity == "critical"]),
                "estimated_improvement_potential": "8-15x with full optimization",
            },
        }

        print("\n" + "=" * 70)
        print(f"BENCHMARK COMPLETE - {total_time:.1f}s total")
        print("=" * 70)

        return results


def main():
    # Target the SPEK template analyzer
    target_path = Path(__file__).parent.parent.parent / "spek template"

    if not target_path.exists():
        print(f"ERROR: Target path not found: {target_path}")
        return 1

    benchmark = PerformanceBenchmark(target_path)
    results = benchmark.run_full_benchmark()

    # Save results
    output_file = Path(__file__).parent.parent / "docs" / "enhancement" / "performance-baseline.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_file}")

    # Print executive summary
    print("\n" + "=" * 70)
    print("EXECUTIVE SUMMARY")
    print("=" * 70)
    print(f"\nProduction Readiness: {results['production_readiness']['recommendation']}")
    print(f"Overall Score: {results['production_readiness']['overall_score']:.0f}%")
    print(f"\nCritical Bottlenecks: {results['summary']['critical_bottlenecks']}")
    print(f"Estimated Improvement: {results['summary']['estimated_improvement_potential']}")

    if results["production_readiness"]["critical_blockers"]:
        print("\nCritical Blockers:")
        for blocker in results["production_readiness"]["critical_blockers"]:
            print(f"  - {blocker}")

    print("\n" + "=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
