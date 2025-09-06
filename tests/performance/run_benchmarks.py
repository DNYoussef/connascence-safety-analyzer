#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Performance Benchmark Runner Script
====================================

Command-line interface for running comprehensive performance benchmarks
on the connascence analyzer.
"""

import argparse
import logging
import os
from pathlib import Path
import sys
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analyzer.caching.ast_cache import ast_cache, clear_cache, optimize_cache
from analyzer.optimization.incremental_analyzer import get_incremental_analyzer
from tests.performance.benchmark_runner import PerformanceBenchmarker


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""

    level = logging.DEBUG if verbose else logging.INFO
    format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('tests/performance/benchmark.log')
        ]
    )


def benchmark_test_packages(output_dir: str, verbose: bool = False) -> dict:
    """Benchmark the test packages in test_packages/."""

    benchmarker = PerformanceBenchmarker(output_dir)

    results = {}
    test_packages_dir = Path("test_packages")

    if not test_packages_dir.exists():
        print("ERROR: test_packages directory not found")
        return results

    print("Benchmarking Test Packages")
    print("=" * 50)

    # Benchmark each package
    for package_dir in sorted(test_packages_dir.iterdir()):
        if package_dir.is_dir():
            print(f"\nBenchmarking {package_dir.name}...")

            try:
                result = benchmarker.benchmark_codebase(str(package_dir), package_dir.name)
                results[package_dir.name] = result

                # Print summary
                print(f"  Files: {result.file_count}")
                print(f"  Lines: {result.total_lines:,}")
                print(f"  Time: {result.execution_time_seconds:.2f}s")
                print(f"  Throughput: {result.files_per_second:.1f} files/sec")
                print(f"  Memory: {result.memory_peak_mb:.1f}MB peak")
                print(f"  Violations: {result.violations_found}")

                if verbose:
                    print(f"  Lines/sec: {result.lines_per_second:.0f}")
                    print(f"  CPU: {result.cpu_usage_percent:.1f}%")
                    print(f"  Memory/file: {result.memory_per_file_kb:.1f}KB")

            except Exception as e:
                print(f"  ERROR: {e}")
                results[package_dir.name] = {'error': str(e)}

    return results


def benchmark_parallel_scaling(output_dir: str) -> dict:
    """Benchmark parallel processing scaling."""

    import shutil
    import tempfile

    from analyzer.performance.parallel_analyzer import ParallelAnalysisConfig, ParallelConnascenceAnalyzer

    print("\nParallel Processing Scaling Benchmark")
    print("=" * 50)

    results = {}

    # Create synthetic test project
    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Create 100 test files
        for i in range(100):
            test_file = temp_dir / f"test_{i:03d}.py"
            content = f'''
def function_{i}():
    magic_number = {42 + i}
    return magic_number * 2

class TestClass_{i}:
    def __init__(self):
        self.value = {100 + i}

    def method_a(self): pass
    def method_b(self): pass
    def method_c(self): pass
    def method_d(self): pass
    def method_e(self): pass
'''
            test_file.write_text(content)

        # Test different worker counts
        worker_counts = [1, 2, 4, 8]

        for workers in worker_counts:
            print(f"\nTesting with {workers} workers...")

            config = ParallelAnalysisConfig(max_workers=workers, use_processes=True)
            parallel_analyzer = ParallelConnascenceAnalyzer(config)

            start_time = time.time()
            parallel_result = parallel_analyzer.analyze_project_parallel(str(temp_dir))
            execution_time = time.time() - start_time

            results[f"workers_{workers}"] = {
                'worker_count': workers,
                'execution_time': execution_time,
                'speedup_factor': parallel_result.speedup_factor,
                'efficiency': parallel_result.efficiency,
                'files_analyzed': parallel_result.unified_result.files_analyzed,
                'violations_found': parallel_result.unified_result.total_violations,
                'memory_peak_mb': parallel_result.peak_memory_mb
            }

            print(f"  Time: {execution_time:.2f}s")
            print(f"  Speedup: {parallel_result.speedup_factor:.2f}x")
            print(f"  Efficiency: {parallel_result.efficiency:.2f}")
            print(f"  Memory: {parallel_result.peak_memory_mb:.1f}MB")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    return results


def benchmark_caching_effectiveness(verbose: bool = False) -> dict:
    """Benchmark caching system effectiveness."""

    print("\nCaching Effectiveness Benchmark")
    print("=" * 40)

    results = {}

    # Clear cache to start fresh
    clear_cache()

    # Test on actual codebase
    test_path = "analyzer"  # Use analyzer directory as test case

    if not Path(test_path).exists():
        print(f"ERROR: Test path {test_path} not found")
        return results

    from analyzer.core import ConnascenceAnalyzer
    analyzer = ConnascenceAnalyzer()

    # Cold run (no cache)
    print("Running cold analysis (no cache)...")
    start_time = time.time()
    result1 = analyzer.analyze_path(test_path)
    cold_time = time.time() - start_time

    # Warm run (with cache)
    print("Running warm analysis (with cache)...")
    start_time = time.time()
    result2 = analyzer.analyze_path(test_path)
    warm_time = time.time() - start_time

    # Calculate cache effectiveness
    cache_speedup = cold_time / max(warm_time, 0.001)
    time_saved = cold_time - warm_time
    effectiveness_percent = (time_saved / cold_time) * 100 if cold_time > 0 else 0

    # Get cache statistics
    cache_stats = ast_cache.get_cache_statistics()

    results = {
        'cold_run_time_seconds': cold_time,
        'warm_run_time_seconds': warm_time,
        'time_saved_seconds': time_saved,
        'cache_speedup_factor': cache_speedup,
        'effectiveness_percent': effectiveness_percent,
        'violations_consistent': len(result1.get('violations', [])) == len(result2.get('violations', [])),
        'cache_statistics': cache_stats
    }

    print(f"  Cold run: {cold_time:.2f}s")
    print(f"  Warm run: {warm_time:.2f}s")
    print(f"  Speedup: {cache_speedup:.2f}x")
    print(f"  Time saved: {time_saved:.2f}s ({effectiveness_percent:.1f}%)")
    print(f"  Results consistent: {results['violations_consistent']}")
    print(f"  Cache hit rate: {cache_stats.get('hit_rate_percent', 0):.1f}%")

    if verbose:
        print(f"  Cache entries: {cache_stats.get('entries_count', 0)}")
        print(f"  Cache memory: {cache_stats.get('memory_usage_mb', 0):.1f}MB")

    return results


def benchmark_incremental_analysis(output_dir: str, verbose: bool = False) -> dict:
    """Benchmark incremental analysis performance."""

    print("\nIncremental Analysis Benchmark")
    print("=" * 40)

    results = {}

    # Use current project as test case
    project_root = Path(".")
    incremental_analyzer = get_incremental_analyzer(project_root)

    try:
        # Create baseline
        print("Creating baseline analysis...")
        baseline_start = time.time()
        baseline = incremental_analyzer.create_baseline()
        baseline_time = time.time() - baseline_start

        # Simulate incremental analysis (analyze a few files)
        test_files = list(Path("analyzer").glob("*.py"))[:5]  # First 5 files

        print("Running incremental analysis...")
        incremental_start = time.time()
        incremental_result = incremental_analyzer.analyze_changes(
            changed_files=[str(f) for f in test_files]
        )
        incremental_time = time.time() - incremental_start

        # Calculate performance improvement
        full_analysis_estimate = baseline_time  # Baseline is full analysis
        time_saved = full_analysis_estimate - incremental_time
        speedup = full_analysis_estimate / max(incremental_time, 0.001)

        results = {
            'baseline_time_seconds': baseline_time,
            'baseline_violations': len(baseline.get('violations', [])),
            'incremental_time_seconds': incremental_time,
            'incremental_speedup': speedup,
            'time_saved_seconds': time_saved,
            'files_in_scope': incremental_result.analyzed_files_count,
            'files_skipped': incremental_result.skipped_files_count,
            'skip_percentage': (incremental_result.skipped_files_count / incremental_result.total_files_in_project) * 100,
            'new_violations': len(incremental_result.new_violations),
            'resolved_violations': len(incremental_result.resolved_violations)
        }

        print(f"  Baseline time: {baseline_time:.2f}s")
        print(f"  Incremental time: {incremental_time:.2f}s")
        print(f"  Speedup: {speedup:.2f}x")
        print(f"  Time saved: {time_saved:.2f}s")
        print(f"  Files analyzed: {incremental_result.analyzed_files_count}")
        print(f"  Files skipped: {incremental_result.skipped_files_count} ({results['skip_percentage']:.1f}%)")

        if verbose:
            print(f"  Cache hit rate: {incremental_result.cache_hit_rate:.1f}%")
            print(f"  New violations: {len(incremental_result.new_violations)}")
            print(f"  Resolved violations: {len(incremental_result.resolved_violations)}")

    except Exception as e:
        print(f"  ERROR: {e}")
        results = {'error': str(e)}

    return results


def generate_performance_report(all_results: dict, output_dir: str):
    """Generate comprehensive performance report."""

    report_file = Path(output_dir) / f"performance_report_{time.strftime('%Y%m%d_%H%M%S')}.md"

    with open(report_file, 'w') as f:
        f.write("# Connascence Analyzer Performance Report\n\n")
        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # System information
        import platform

        import psutil

        f.write("## System Information\n\n")
        f.write(f"- **OS**: {platform.system()} {platform.release()}\n")
        f.write(f"- **CPU**: {platform.processor()}\n")
        f.write(f"- **Cores**: {os.cpu_count()}\n")
        f.write(f"- **Memory**: {psutil.virtual_memory().total / (1024**3):.1f} GB\n")
        f.write(f"- **Python**: {platform.python_version()}\n\n")

        # Test package results
        if 'test_packages' in all_results:
            f.write("## Test Package Benchmarks\n\n")
            f.write("| Package | Files | Lines | Time (s) | Throughput (files/s) | Memory (MB) | Violations |\n")
            f.write("|---------|-------|-------|----------|---------------------|-------------|------------|\n")

            for name, result in all_results['test_packages'].items():
                if isinstance(result, dict) and 'error' not in result:
                    f.write(f"| {name} | {result.file_count} | {result.total_lines:,} | "
                           f"{result.execution_time_seconds:.2f} | {result.files_per_second:.1f} | "
                           f"{result.memory_peak_mb:.1f} | {result.violations_found} |\n")
                else:
                    f.write(f"| {name} | - | - | ERROR | - | - | - |\n")
            f.write("\n")

        # Parallel scaling results
        if 'parallel_scaling' in all_results:
            f.write("## Parallel Processing Scaling\n\n")
            f.write("| Workers | Time (s) | Speedup | Efficiency | Memory (MB) |\n")
            f.write("|---------|----------|---------|------------|-------------|\n")

            for workers_key, result in all_results['parallel_scaling'].items():
                if isinstance(result, dict) and 'error' not in result:
                    workers = result['worker_count']
                    f.write(f"| {workers} | {result['execution_time']:.2f} | "
                           f"{result['speedup_factor']:.2f}x | {result['efficiency']:.2f} | "
                           f"{result.get('memory_peak_mb', 0):.1f} |\n")
            f.write("\n")

        # Caching effectiveness
        if 'caching' in all_results:
            cache_result = all_results['caching']
            if 'error' not in cache_result:
                f.write("## Caching Effectiveness\n\n")
                f.write(f"- **Cold run time**: {cache_result['cold_run_time_seconds']:.2f}s\n")
                f.write(f"- **Warm run time**: {cache_result['warm_run_time_seconds']:.2f}s\n")
                f.write(f"- **Speedup**: {cache_result['cache_speedup_factor']:.2f}x\n")
                f.write(f"- **Time saved**: {cache_result['time_saved_seconds']:.2f}s ({cache_result['effectiveness_percent']:.1f}%)\n")
                f.write(f"- **Results consistent**: {cache_result['violations_consistent']}\n\n")

        # Incremental analysis
        if 'incremental' in all_results:
            inc_result = all_results['incremental']
            if 'error' not in inc_result:
                f.write("## Incremental Analysis Performance\n\n")
                f.write(f"- **Baseline time**: {inc_result['baseline_time_seconds']:.2f}s\n")
                f.write(f"- **Incremental time**: {inc_result['incremental_time_seconds']:.2f}s\n")
                f.write(f"- **Speedup**: {inc_result['incremental_speedup']:.2f}x\n")
                f.write(f"- **Files skipped**: {inc_result['files_skipped']} ({inc_result['skip_percentage']:.1f}%)\n")
                f.write(f"- **Time saved**: {inc_result['time_saved_seconds']:.2f}s\n\n")

        # Performance targets assessment
        f.write("## Performance Target Assessment\n\n")

        # Check if targets are met based on test package results
        if 'test_packages' in all_results:
            targets_met = []

            for name, result in all_results['test_packages'].items():
                if isinstance(result, dict) and 'error' not in result:
                    if result.file_count > 1000:  # Large codebase
                        target_met = result.execution_time_seconds < 300  # 5 minutes
                        targets_met.append(f"Large codebase ({name}): {'✅ PASS' if target_met else '❌ FAIL'} ({result.execution_time_seconds:.1f}s)")
                    elif result.file_count > 100:  # Medium codebase
                        target_met = result.execution_time_seconds < 30  # 30 seconds
                        targets_met.append(f"Medium codebase ({name}): {'✅ PASS' if target_met else '❌ FAIL'} ({result.execution_time_seconds:.1f}s)")
                    else:  # Small codebase
                        target_met = result.execution_time_seconds < 5  # 5 seconds
                        targets_met.append(f"Small codebase ({name}): {'✅ PASS' if target_met else '❌ FAIL'} ({result.execution_time_seconds:.1f}s)")

            for target in targets_met:
                f.write(f"- {target}\n")
            f.write("\n")

        # Recommendations
        f.write("## Performance Recommendations\n\n")

        recommendations = []

        # Analyze results and generate recommendations
        if 'parallel_scaling' in all_results:
            parallel_results = all_results['parallel_scaling']
            best_efficiency = 0
            best_workers = 1

            for workers_key, result in parallel_results.items():
                if isinstance(result, dict) and 'efficiency' in result and result['efficiency'] > best_efficiency:
                    best_efficiency = result['efficiency']
                    best_workers = result['worker_count']

            recommendations.append(f"Optimal worker count: {best_workers} (efficiency: {best_efficiency:.2f})")

        if 'caching' in all_results and 'error' not in all_results['caching']:
            cache_result = all_results['caching']
            if cache_result['cache_speedup_factor'] > 2.0:
                recommendations.append("Caching is highly effective - ensure it's enabled in production")
            elif cache_result['cache_speedup_factor'] < 1.5:
                recommendations.append("Consider implementing more aggressive caching strategies")

        if 'incremental' in all_results and 'error' not in all_results['incremental']:
            inc_result = all_results['incremental']
            if inc_result['skip_percentage'] > 80:
                recommendations.append("Incremental analysis is highly effective for CI/CD pipelines")
            elif inc_result['skip_percentage'] < 50:
                recommendations.append("Consider improving dependency analysis for better incremental performance")

        # Default recommendations
        if not recommendations:
            recommendations = [
                "Performance appears acceptable for current workloads",
                "Consider implementing incremental analysis for CI/CD pipelines",
                "Monitor performance trends over time"
            ]

        for i, rec in enumerate(recommendations, 1):
            f.write(f"{i}. {rec}\n")

        f.write("\n---\n\n*Report generated by connascence analyzer performance benchmarker*\n")

    print(f"\nDetailed report saved to: {report_file}")


def main():
    """Main entry point."""

    parser = argparse.ArgumentParser(description="Run performance benchmarks")
    parser.add_argument('--output', '-o', default='tests/performance/results',
                       help='Output directory for results')
    parser.add_argument('--test-packages', action='store_true',
                       help='Benchmark test packages')
    parser.add_argument('--parallel', action='store_true',
                       help='Benchmark parallel processing')
    parser.add_argument('--caching', action='store_true',
                       help='Benchmark caching effectiveness')
    parser.add_argument('--incremental', action='store_true',
                       help='Benchmark incremental analysis')
    parser.add_argument('--comprehensive', action='store_true',
                       help='Run all benchmarks')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--optimize-cache', action='store_true',
                       help='Optimize cache before benchmarks')

    args = parser.parse_args()

    # Setup
    setup_logging(args.verbose)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Optimize cache if requested
    if args.optimize_cache:
        print("Optimizing cache...")
        optimize_cache()

    all_results = {}

    # Run selected benchmarks
    if args.comprehensive or args.test_packages:
        print("Running test package benchmarks...")
        all_results['test_packages'] = benchmark_test_packages(str(output_dir), args.verbose)

    if args.comprehensive or args.parallel:
        print("Running parallel scaling benchmarks...")
        all_results['parallel_scaling'] = benchmark_parallel_scaling(str(output_dir))

    if args.comprehensive or args.caching:
        print("Running caching effectiveness benchmark...")
        all_results['caching'] = benchmark_caching_effectiveness(args.verbose)

    if args.comprehensive or args.incremental:
        print("Running incremental analysis benchmark...")
        all_results['incremental'] = benchmark_incremental_analysis(str(output_dir), args.verbose)

    # Generate comprehensive report
    if all_results:
        generate_performance_report(all_results, str(output_dir))
        print("\nBenchmark completed successfully!")
    else:
        print("No benchmarks selected. Use --help for options.")


if __name__ == "__main__":
    main()
