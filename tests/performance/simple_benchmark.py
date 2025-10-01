#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Simple Performance Benchmark
=============================

A simplified benchmark script that works with the current codebase
without complex dependencies.
"""

from pathlib import Path
import sys
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analyzer.core import ConnascenceAnalyzer


def benchmark_codebase(path: str, name: str = None):
    """Simple benchmark of analyzer performance."""

    path = Path(path)
    name = name or path.name

    print(f"\nBenchmarking: {name}")
    print("-" * 40)

    if not path.exists():
        print(f"ERROR: Path does not exist: {path}")
        return None

    # Count files
    if path.is_file():
        files = [path]
    else:
        files = list(path.glob("**/*.py")) + list(path.glob("**/*.js")) + list(path.glob("**/*.ts"))

    file_count = len(files)

    # Count lines
    total_lines = 0
    for file_path in files:
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                lines = sum(1 for line in f if line.strip())
                total_lines += lines
        except Exception:
            pass

    print(f"Files: {file_count}")
    print(f"Lines: {total_lines:,}")

    # Initialize analyzer
    analyzer = ConnascenceAnalyzer()

    # Run analysis with timing
    print("Running analysis...")
    start_time = time.time()

    try:
        result = analyzer.analyze_path(str(path))

        execution_time = time.time() - start_time

        # Extract results
        violations = result.get("violations", [])
        violation_count = len(violations)

        # Calculate metrics
        files_per_second = file_count / execution_time if execution_time > 0 else 0
        lines_per_second = total_lines / execution_time if execution_time > 0 else 0

        # Print results
        print(f"Time: {execution_time:.2f} seconds")
        print(f"Violations: {violation_count}")
        print(f"Throughput: {files_per_second:.1f} files/sec")
        print(f"Throughput: {lines_per_second:.0f} lines/sec")

        # Check performance targets
        if file_count > 1000:  # Large codebase
            target_time = 300  # 5 minutes
            status = "PASS" if execution_time < target_time else "FAIL"
            print(f"Large codebase target (<5min): {status}")
        elif file_count > 100:  # Medium codebase
            target_time = 30  # 30 seconds
            status = "PASS" if execution_time < target_time else "FAIL"
            print(f"Medium codebase target (<30sec): {status}")
        else:  # Small codebase
            target_time = 5  # 5 seconds
            status = "PASS" if execution_time < target_time else "FAIL"
            print(f"Small codebase target (<5sec): {status}")

        return {
            "name": name,
            "file_count": file_count,
            "total_lines": total_lines,
            "execution_time": execution_time,
            "violation_count": violation_count,
            "files_per_second": files_per_second,
            "lines_per_second": lines_per_second,
            "success": True,
        }

    except Exception as e:
        execution_time = time.time() - start_time
        print(f"ERROR: {e}")
        print(f"Time before failure: {execution_time:.2f} seconds")

        return {
            "name": name,
            "file_count": file_count,
            "total_lines": total_lines,
            "execution_time": execution_time,
            "error": str(e),
            "success": False,
        }


def main():
    """Main entry point."""

    print("Simple Performance Benchmark")
    print("=" * 50)

    # Test paths to benchmark
    test_paths = ["test_packages/curl", "test_packages/express", "analyzer", "tests"]

    results = []

    for test_path in test_paths:
        if Path(test_path).exists():
            result = benchmark_codebase(test_path)
            if result:
                results.append(result)
        else:
            print(f"\nSkipping {test_path} (not found)")

    # Summary
    print("\n" + "=" * 50)
    print("BENCHMARK SUMMARY")
    print("=" * 50)

    if not results:
        print("No benchmarks completed successfully")
        return

    # Print summary table
    print(f"{'Name':<15} {'Files':<8} {'Lines':<10} {'Time(s)':<8} {'Files/s':<8} {'Status':<8}")
    print("-" * 65)

    for result in results:
        if result["success"]:
            name = result["name"][:14]
            files = result["file_count"]
            lines = result["total_lines"]
            time_s = result["execution_time"]
            throughput = result["files_per_second"]

            # Determine status based on performance
            if (files > 100 and time_s > 30) or (files <= 100 and time_s > 5):
                status = "SLOW"
            else:
                status = "OK"

            print(f"{name:<15} {files:<8} {lines:<10} {time_s:<8.2f} {throughput:<8.1f} {status:<8}")
        else:
            print(f"{result['name'][:14]:<15} {'ERROR':<40}")

    # Calculate totals
    successful_results = [r for r in results if r["success"]]
    if successful_results:
        total_files = sum(r["file_count"] for r in successful_results)
        total_lines = sum(r["total_lines"] for r in successful_results)
        total_time = sum(r["execution_time"] for r in successful_results)
        avg_throughput = sum(r["files_per_second"] for r in successful_results) / len(successful_results)

        print("-" * 65)
        print(f"{'TOTAL':<15} {total_files:<8} {total_lines:<10} {total_time:<8.2f} {avg_throughput:<8.1f}")

        print("\nOverall Performance:")
        print(f"  Total files analyzed: {total_files:,}")
        print(f"  Total lines analyzed: {total_lines:,}")
        print(f"  Total time: {total_time:.2f} seconds")
        print(f"  Average throughput: {avg_throughput:.1f} files/sec")

        # Performance assessment
        if avg_throughput > 10:
            print("  Performance: GOOD ✅")
        elif avg_throughput > 5:
            print("  Performance: ACCEPTABLE ⚠️")
        else:
            print("  Performance: NEEDS IMPROVEMENT ❌")


if __name__ == "__main__":
    main()
