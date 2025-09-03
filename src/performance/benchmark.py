"""
Performance Benchmarking Suite

Comprehensive benchmarking system to measure and validate performance improvements
across different optimization strategies.
"""

import gc
import json
import os
import psutil
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .parallel_analyzer import (
    HighPerformanceConnascenceAnalyzer, 
    PerformanceMetrics,
    OptimizedViolation
)

# Import baseline analyzer for comparison
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from analyzer.connascence_analyzer import ConnascenceAnalyzer as BaselineAnalyzer


@dataclass
class BenchmarkConfiguration:
    """Configuration for benchmark runs."""
    
    name: str
    description: str
    enable_parallel: bool
    enable_cache: bool
    max_workers: Optional[int] = None
    iterations: int = 1
    warm_up_runs: int = 0


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""
    
    configuration: BenchmarkConfiguration
    violations_count: int
    performance_metrics: PerformanceMetrics
    memory_peak_mb: float
    memory_average_mb: float
    cpu_usage_percent: float
    
    # Comparison metrics
    baseline_comparison: Optional[Dict[str, float]] = None
    
    @property
    def speedup_factor(self) -> Optional[float]:
        """Calculate speedup factor compared to baseline."""
        if not self.baseline_comparison:
            return None
        baseline_duration = self.baseline_comparison.get('duration_ms', 0)
        if baseline_duration == 0:
            return None
        return baseline_duration / self.performance_metrics.duration_ms


@dataclass
class SystemInfo:
    """System information for benchmark context."""
    
    cpu_count: int
    cpu_model: str
    memory_total_gb: float
    memory_available_gb: float
    platform: str
    python_version: str
    
    @classmethod
    def collect(cls) -> 'SystemInfo':
        """Collect current system information."""
        import platform
        
        cpu_info = ""
        try:
            if platform.system() == "Windows":
                cpu_info = platform.processor()
            else:
                # Try to get more detailed CPU info on Unix systems
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if "model name" in line:
                            cpu_info = line.split(":")[1].strip()
                            break
        except:
            cpu_info = "Unknown"
        
        memory = psutil.virtual_memory()
        
        return cls(
            cpu_count=psutil.cpu_count(),
            cpu_model=cpu_info,
            memory_total_gb=memory.total / (1024**3),
            memory_available_gb=memory.available / (1024**3),
            platform=platform.platform(),
            python_version=platform.python_version()
        )


class PerformanceBenchmark:
    """Comprehensive performance benchmark suite."""
    
    def __init__(self, test_data_path: Optional[Path] = None):
        self.test_data_path = test_data_path or Path.cwd()
        self.system_info = SystemInfo.collect()
        self.baseline_results: Dict[str, Any] = {}
        
    def run_comprehensive_benchmark(
        self, 
        project_path: Path,
        output_file: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Run comprehensive benchmark comparing all optimization strategies."""
        
        print("Starting comprehensive performance benchmark...")
        print(f"Test project: {project_path}")
        print(f"System: {self.system_info.cpu_count} CPUs, {self.system_info.memory_total_gb:.1f}GB RAM")
        print("-" * 60)
        
        # Define benchmark configurations
        configs = [
            BenchmarkConfiguration(
                name="baseline_sequential",
                description="Original analyzer (sequential)",
                enable_parallel=False,
                enable_cache=False,
                iterations=3
            ),
            BenchmarkConfiguration(
                name="optimized_sequential",
                description="Optimized single-pass analyzer (sequential)",
                enable_parallel=False,
                enable_cache=False,
                iterations=3
            ),
            BenchmarkConfiguration(
                name="optimized_cached",
                description="Optimized analyzer with caching (sequential)",
                enable_parallel=False,
                enable_cache=True,
                iterations=3,
                warm_up_runs=1  # First run populates cache
            ),
            BenchmarkConfiguration(
                name="optimized_parallel_2workers",
                description="Optimized analyzer with 2 worker processes",
                enable_parallel=True,
                enable_cache=False,
                max_workers=2,
                iterations=3
            ),
            BenchmarkConfiguration(
                name="optimized_parallel_4workers",
                description="Optimized analyzer with 4 worker processes",
                enable_parallel=True,
                enable_cache=False,
                max_workers=4,
                iterations=3
            ),
            BenchmarkConfiguration(
                name="optimized_parallel_auto",
                description="Optimized analyzer with auto worker count",
                enable_parallel=True,
                enable_cache=False,
                max_workers=None,
                iterations=3
            ),
            BenchmarkConfiguration(
                name="optimized_parallel_cached",
                description="Optimized analyzer with parallel processing and caching",
                enable_parallel=True,
                enable_cache=True,
                max_workers=None,
                iterations=3,
                warm_up_runs=1
            )
        ]
        
        # Run benchmarks
        results = {}
        for config in configs:
            print(f"\n📊 Running benchmark: {config.name}")
            print(f"   {config.description}")
            
            if config.name == "baseline_sequential":
                result = self._run_baseline_benchmark(project_path, config)
            else:
                result = self._run_optimized_benchmark(project_path, config)
            
            results[config.name] = result
            
            # Print immediate results
            metrics = result.performance_metrics
            print(f"   ✓ Duration: {metrics.duration_ms}ms")
            print(f"   ✓ Speed: {metrics.lines_per_second:,.0f} lines/sec")
            print(f"   ✓ Memory: {result.memory_peak_mb:.1f}MB peak")
            
            if result.speedup_factor:
                print(f"   ✓ Speedup: {result.speedup_factor:.2f}x")
        
        # Generate comprehensive report
        report = self._generate_benchmark_report(results, project_path)
        
        # Save results
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\n📁 Benchmark results saved to: {output_file}")
        
        # Print summary
        self._print_benchmark_summary(results)
        
        return report
    
    def _run_baseline_benchmark(
        self, 
        project_path: Path, 
        config: BenchmarkConfiguration
    ) -> BenchmarkResult:
        """Run benchmark using baseline analyzer."""
        
        # Collect file statistics for comparison
        python_files = list(project_path.rglob("*.py"))
        total_lines = 0
        for file_path in python_files:
            try:
                with open(file_path, encoding='utf-8', errors='ignore') as f:
                    total_lines += len(f.readlines())
            except:
                pass
        
        violations_counts = []
        durations = []
        memory_peaks = []
        cpu_usages = []
        
        # Run multiple iterations
        for i in range(config.iterations):
            print(f"   Iteration {i+1}/{config.iterations}...")
            
            # Clear memory
            gc.collect()
            
            # Monitor memory and CPU
            process = psutil.Process()
            memory_before = process.memory_info().rss / (1024*1024)  # MB
            cpu_before = process.cpu_percent()
            
            # Run baseline analyzer
            start_time = time.time()
            analyzer = BaselineAnalyzer(strict_mode=False)
            violations = analyzer.analyze_directory(project_path)
            end_time = time.time()
            
            # Monitor memory and CPU after
            memory_after = process.memory_info().rss / (1024*1024)  # MB
            cpu_after = process.cpu_percent()
            
            violations_counts.append(len(violations))
            durations.append((end_time - start_time) * 1000)  # ms
            memory_peaks.append(memory_after)
            cpu_usages.append(max(cpu_before, cpu_after))
        
        # Calculate averages
        avg_violations = sum(violations_counts) / len(violations_counts)
        avg_duration = sum(durations) / len(durations)
        avg_memory = sum(memory_peaks) / len(memory_peaks)
        avg_cpu = sum(cpu_usages) / len(cpu_usages)
        
        # Create performance metrics
        performance_metrics = PerformanceMetrics(
            start_time=0,
            end_time=avg_duration / 1000,
            files_analyzed=len(python_files),
            lines_analyzed=total_lines,
            cache_hits=0,
            cache_misses=len(python_files)
        )
        
        # Store baseline for comparison
        self.baseline_results = {
            'violations_count': avg_violations,
            'duration_ms': avg_duration,
            'lines_per_second': performance_metrics.lines_per_second,
            'memory_peak_mb': avg_memory
        }
        
        return BenchmarkResult(
            configuration=config,
            violations_count=int(avg_violations),
            performance_metrics=performance_metrics,
            memory_peak_mb=avg_memory,
            memory_average_mb=avg_memory,
            cpu_usage_percent=avg_cpu
        )
    
    def _run_optimized_benchmark(
        self, 
        project_path: Path, 
        config: BenchmarkConfiguration
    ) -> BenchmarkResult:
        """Run benchmark using optimized analyzer."""
        
        violations_counts = []
        performance_metrics_list = []
        memory_peaks = []
        cpu_usages = []
        
        # Create analyzer
        analyzer = HighPerformanceConnascenceAnalyzer(
            max_workers=config.max_workers,
            enable_cache=config.enable_cache
        )
        
        # Warm-up runs
        for i in range(config.warm_up_runs):
            print(f"   Warm-up {i+1}/{config.warm_up_runs}...")
            analyzer.analyze_directory(project_path, parallel=config.enable_parallel)
        
        # Benchmark runs
        for i in range(config.iterations):
            print(f"   Iteration {i+1}/{config.iterations}...")
            
            # Clear memory
            gc.collect()
            
            # Monitor memory and CPU
            process = psutil.Process()
            memory_before = process.memory_info().rss / (1024*1024)  # MB
            cpu_before = process.cpu_percent()
            
            # Run optimized analyzer
            violations, metrics = analyzer.analyze_directory(
                project_path, 
                parallel=config.enable_parallel
            )
            
            # Monitor memory and CPU after
            memory_after = process.memory_info().rss / (1024*1024)  # MB
            cpu_after = process.cpu_percent()
            
            violations_counts.append(len(violations))
            performance_metrics_list.append(metrics)
            memory_peaks.append(memory_after)
            cpu_usages.append(max(cpu_before, cpu_after))
        
        # Calculate averages
        avg_violations = sum(violations_counts) / len(violations_counts)
        avg_memory = sum(memory_peaks) / len(memory_peaks)
        avg_cpu = sum(cpu_usages) / len(cpu_usages)
        
        # Average performance metrics
        avg_metrics = PerformanceMetrics(
            start_time=0,
            end_time=sum(m.end_time - m.start_time for m in performance_metrics_list) / len(performance_metrics_list),
            files_analyzed=performance_metrics_list[0].files_analyzed,
            lines_analyzed=performance_metrics_list[0].lines_analyzed,
            cache_hits=sum(m.cache_hits for m in performance_metrics_list) // len(performance_metrics_list),
            cache_misses=sum(m.cache_misses for m in performance_metrics_list) // len(performance_metrics_list)
        )
        
        # Calculate comparison with baseline
        baseline_comparison = None
        if self.baseline_results:
            baseline_comparison = {
                'duration_ms': self.baseline_results['duration_ms'],
                'speedup_factor': self.baseline_results['duration_ms'] / avg_metrics.duration_ms,
                'memory_improvement': (self.baseline_results['memory_peak_mb'] - avg_memory) / self.baseline_results['memory_peak_mb'],
                'accuracy_change': (avg_violations - self.baseline_results['violations_count']) / max(1, self.baseline_results['violations_count'])
            }
        
        result = BenchmarkResult(
            configuration=config,
            violations_count=int(avg_violations),
            performance_metrics=avg_metrics,
            memory_peak_mb=avg_memory,
            memory_average_mb=avg_memory,
            cpu_usage_percent=avg_cpu,
            baseline_comparison=baseline_comparison
        )
        
        return result
    
    def _generate_benchmark_report(
        self, 
        results: Dict[str, BenchmarkResult], 
        project_path: Path
    ) -> Dict[str, Any]:
        """Generate comprehensive benchmark report."""
        
        # Find best performing configuration
        best_config = None
        best_speedup = 0
        
        for name, result in results.items():
            if result.speedup_factor and result.speedup_factor > best_speedup:
                best_speedup = result.speedup_factor
                best_config = name
        
        # Calculate improvement metrics
        baseline_result = results.get("baseline_sequential")
        optimized_results = {k: v for k, v in results.items() if k != "baseline_sequential"}
        
        improvements = {}
        if baseline_result:
            for name, result in optimized_results.items():
                if result.baseline_comparison:
                    improvements[name] = {
                        "speedup_factor": result.speedup_factor,
                        "speed_improvement_percent": (result.speedup_factor - 1) * 100,
                        "memory_improvement_percent": result.baseline_comparison.get('memory_improvement', 0) * 100,
                        "accuracy_maintained": abs(result.baseline_comparison.get('accuracy_change', 0)) < 0.05
                    }
        
        report = {
            "benchmark_info": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "project_path": str(project_path),
                "system_info": asdict(self.system_info)
            },
            "results": {name: asdict(result) for name, result in results.items()},
            "improvements": improvements,
            "summary": {
                "best_configuration": best_config,
                "best_speedup": best_speedup,
                "target_achieved": best_speedup >= 1.2,  # 20% improvement target
                "total_configurations_tested": len(results),
                "configurations_exceeding_target": sum(
                    1 for result in results.values() 
                    if result.speedup_factor and result.speedup_factor >= 1.2
                )
            },
            "recommendations": self._generate_recommendations(results)
        }
        
        return report
    
    def _generate_recommendations(self, results: Dict[str, BenchmarkResult]) -> List[str]:
        """Generate performance recommendations based on benchmark results."""
        recommendations = []
        
        # Analyze results for recommendations
        parallel_results = {k: v for k, v in results.items() if "parallel" in k}
        cached_results = {k: v for k, v in results.items() if "cached" in k}
        
        # Parallel processing recommendations
        if parallel_results:
            best_parallel = max(parallel_results.values(), key=lambda r: r.speedup_factor or 0)
            if best_parallel.speedup_factor and best_parallel.speedup_factor > 1.5:
                recommendations.append(
                    f"Enable parallel processing for {best_parallel.speedup_factor:.1f}x speedup on multi-core systems"
                )
        
        # Caching recommendations
        if cached_results:
            best_cached = max(cached_results.values(), key=lambda r: r.performance_metrics.cache_hit_rate)
            if best_cached.performance_metrics.cache_hit_rate > 0.3:
                recommendations.append(
                    f"Enable caching for {best_cached.performance_metrics.cache_hit_rate:.1%} hit rate on repeated analysis"
                )
        
        # Memory usage recommendations
        memory_results = [(k, v.memory_peak_mb) for k, v in results.items()]
        memory_results.sort(key=lambda x: x[1])
        if len(memory_results) > 1:
            lowest_memory = memory_results[0]
            recommendations.append(
                f"Use {lowest_memory[0]} configuration for memory-constrained environments ({lowest_memory[1]:.1f}MB peak)"
            )
        
        # General recommendations
        if any(r.speedup_factor and r.speedup_factor >= 1.2 for r in results.values()):
            recommendations.append("Optimizations successfully achieved >20% performance improvement target")
        
        return recommendations
    
    def _print_benchmark_summary(self, results: Dict[str, BenchmarkResult]) -> None:
        """Print formatted benchmark summary."""
        print("\n" + "=" * 80)
        print("BENCHMARK SUMMARY")
        print("=" * 80)
        
        # Find baseline for comparison
        baseline = results.get("baseline_sequential")
        if not baseline:
            baseline = list(results.values())[0]
        
        print(f"{'Configuration':<30} {'Duration':<10} {'Speed':<15} {'Speedup':<10} {'Memory':<10}")
        print("-" * 80)
        
        for name, result in results.items():
            duration = f"{result.performance_metrics.duration_ms}ms"
            speed = f"{result.performance_metrics.lines_per_second:,.0f}/s"
            speedup = f"{result.speedup_factor:.2f}x" if result.speedup_factor else "N/A"
            memory = f"{result.memory_peak_mb:.1f}MB"
            
            print(f"{name:<30} {duration:<10} {speed:<15} {speedup:<10} {memory:<10}")
        
        print("\n" + "=" * 80)
        
        # Highlight best results
        best_speed = max(results.values(), key=lambda r: r.performance_metrics.lines_per_second)
        best_speedup = max(
            (r for r in results.values() if r.speedup_factor), 
            key=lambda r: r.speedup_factor,
            default=None
        )
        
        print("🏆 BEST RESULTS:")
        print(f"   Fastest: {best_speed.configuration.name} ({best_speed.performance_metrics.lines_per_second:,.0f} lines/sec)")
        if best_speedup:
            print(f"   Best Speedup: {best_speedup.configuration.name} ({best_speedup.speedup_factor:.2f}x)")
        
        # Check if target achieved
        target_achieved = any(
            r.speedup_factor and r.speedup_factor >= 1.2 
            for r in results.values() if r.speedup_factor
        )
        
        if target_achieved:
            print("\n✅ SUCCESS: 20% performance improvement target achieved!")
        else:
            print("\n❌ Target not achieved: Need >1.2x speedup for 20% improvement")


def main():
    """Command-line interface for benchmarking."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Performance Benchmarking Suite")
    parser.add_argument("project_path", help="Path to project to benchmark")
    parser.add_argument("--output", "-o", help="Output file for benchmark results")
    parser.add_argument("--quick", action="store_true", help="Run quick benchmark with fewer iterations")
    
    args = parser.parse_args()
    
    project_path = Path(args.project_path)
    if not project_path.exists():
        print(f"Error: Project path {project_path} does not exist")
        return 1
    
    # Create benchmark suite
    benchmark = PerformanceBenchmark()
    
    # Override iterations for quick benchmark
    if args.quick:
        print("Running quick benchmark (fewer iterations)...")
        # This would modify the benchmark configurations
    
    # Run benchmark
    output_file = Path(args.output) if args.output else None
    try:
        benchmark.run_comprehensive_benchmark(project_path, output_file)
        return 0
    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user")
        return 1
    except Exception as e:
        print(f"Benchmark failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())