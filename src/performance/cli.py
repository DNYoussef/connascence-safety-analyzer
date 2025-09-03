"""
Enhanced CLI for High-Performance Connascence Analysis

Provides command-line interface with all performance optimizations including
parallel processing, caching, and benchmarking capabilities.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

from .parallel_analyzer import HighPerformanceConnascenceAnalyzer, OptimizedViolation
from .benchmark import PerformanceBenchmark


class ProgressReporter:
    """Progress reporting for command-line interface."""
    
    def __init__(self, show_progress: bool = True):
        self.show_progress = show_progress
        self.last_percent = -1
    
    def __call__(self, current: int, total: int, filename: str) -> None:
        """Progress callback function."""
        if not self.show_progress:
            return
        
        percent = int((current / total) * 100)
        if percent != self.last_percent:
            bar_length = 40
            filled_length = int(bar_length * current // total)
            bar = '█' * filled_length + '-' * (bar_length - filled_length)
            
            print(f'\r[{bar}] {percent}% ({current}/{total}) {filename[:30]:<30}', end='', flush=True)
            self.last_percent = percent
        
        if current == total:
            print()  # New line when complete


def create_html_report(violations: list, metrics: dict, output_path: Path) -> None:
    """Create HTML report for violations."""
    
    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connascence Analysis Report</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                 color: white; padding: 20px; border-radius: 8px; margin-bottom: 30px; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                  gap: 20px; margin-bottom: 30px; }
        .metric-card { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }
        .metric-value { font-size: 2em; font-weight: bold; color: #495057; }
        .metric-label { color: #6c757d; text-transform: uppercase; font-size: 0.8em; }
        .violation { background: white; border: 1px solid #dee2e6; margin-bottom: 15px; 
                    border-radius: 8px; padding: 15px; }
        .violation-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .violation-type { background: #6f42c1; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; }
        .severity-high { background: #dc3545; }
        .severity-medium { background: #fd7e14; }
        .severity-low { background: #28a745; }
        .severity-critical { background: #6f42c1; }
        .file-location { color: #6c757d; font-family: monospace; }
        .description { margin: 10px 0; }
        .recommendation { background: #e7f3ff; padding: 10px; border-radius: 4px; border-left: 4px solid #0066cc; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 Connascence Analysis Report</h1>
        <p>Performance-optimized analysis results</p>
    </div>
    
    <div class="metrics">
        <div class="metric-card">
            <div class="metric-value">{total_violations}</div>
            <div class="metric-label">Total Violations</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{files_analyzed}</div>
            <div class="metric-label">Files Analyzed</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{duration_ms}ms</div>
            <div class="metric-label">Analysis Time</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{lines_per_second:,.0f}</div>
            <div class="metric-label">Lines/Second</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{cache_hit_rate:.1%}</div>
            <div class="metric-label">Cache Hit Rate</div>
        </div>
    </div>
    
    <h2>Violations by Severity</h2>
    {severity_summary}
    
    <h2>Detailed Violations</h2>
    {violation_details}
</body>
</html>
"""
    
    # Calculate metrics
    total_violations = len(violations)
    severity_counts = {}
    for v in violations:
        severity_counts[v.severity] = severity_counts.get(v.severity, 0) + 1
    
    # Generate severity summary
    severity_summary = "<div class='metrics'>"
    for severity, count in severity_counts.items():
        severity_summary += f"""
        <div class="metric-card">
            <div class="metric-value">{count}</div>
            <div class="metric-label">{severity.title()}</div>
        </div>
        """
    severity_summary += "</div>"
    
    # Generate violation details
    violation_details = ""
    for i, violation in enumerate(violations, 1):
        violation_details += f"""
        <div class="violation">
            <div class="violation-header">
                <span class="violation-type severity-{violation.severity}">{violation.type}</span>
                <span class="file-location">{violation.file_path}:{violation.line_number}</span>
            </div>
            <div class="description">{violation.description}</div>
            <div class="recommendation">
                <strong>Recommendation:</strong> {violation.recommendation}
            </div>
        </div>
        """
    
    # Format HTML
    html_content = html_template.format(
        total_violations=total_violations,
        files_analyzed=metrics.get('files_analyzed', 0),
        duration_ms=metrics.get('duration_ms', 0),
        lines_per_second=metrics.get('lines_per_second', 0),
        cache_hit_rate=metrics.get('cache_hit_rate', 0),
        severity_summary=severity_summary,
        violation_details=violation_details
    )
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="High-Performance Connascence Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s analyze ./my_project --parallel --cache
  %(prog)s benchmark ./my_project --output benchmark.json
  %(prog)s analyze ./my_project --output report.json --html report.html
  %(prog)s clear-cache
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze project for connascence')
    analyze_parser.add_argument('path', help='Path to project to analyze')
    analyze_parser.add_argument(
        '--parallel', '-p', action='store_true',
        help='Enable parallel processing (recommended for large projects)'
    )
    analyze_parser.add_argument(
        '--workers', '-w', type=int, metavar='N',
        help='Number of worker processes (default: auto-detect)'
    )
    analyze_parser.add_argument(
        '--cache', '-c', action='store_true',
        help='Enable file caching for faster repeated analysis'
    )
    analyze_parser.add_argument(
        '--cache-dir', metavar='DIR',
        help='Custom cache directory (default: ~/.connascence_cache)'
    )
    analyze_parser.add_argument(
        '--output', '-o', metavar='FILE',
        help='Output JSON file for results'
    )
    analyze_parser.add_argument(
        '--html', metavar='FILE',
        help='Generate HTML report'
    )
    analyze_parser.add_argument(
        '--quiet', '-q', action='store_true',
        help='Suppress progress output'
    )
    analyze_parser.add_argument(
        '--profile', action='store_true',
        help='Enable performance profiling'
    )
    
    # Benchmark command
    benchmark_parser = subparsers.add_parser('benchmark', help='Run performance benchmarks')
    benchmark_parser.add_argument('path', help='Path to project to benchmark')
    benchmark_parser.add_argument(
        '--output', '-o', metavar='FILE',
        help='Output file for benchmark results'
    )
    benchmark_parser.add_argument(
        '--quick', action='store_true',
        help='Run quick benchmark with fewer iterations'
    )
    
    # Cache management commands
    cache_parser = subparsers.add_parser('clear-cache', help='Clear analysis cache')
    cache_parser.add_argument(
        '--cache-dir', metavar='DIR',
        help='Custom cache directory to clear'
    )
    
    # If no command provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return 1
    
    args = parser.parse_args()
    
    try:
        if args.command == 'analyze':
            return analyze_command(args)
        elif args.command == 'benchmark':
            return benchmark_command(args)
        elif args.command == 'clear-cache':
            return clear_cache_command(args)
        else:
            parser.print_help()
            return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        if '--debug' in sys.argv:
            import traceback
            traceback.print_exc()
        return 1


def analyze_command(args) -> int:
    """Handle analyze command."""
    project_path = Path(args.path)
    if not project_path.exists():
        print(f"Error: Path {project_path} does not exist")
        return 1
    
    if not project_path.is_dir():
        print(f"Error: Path {project_path} is not a directory")
        return 1
    
    print(f"🔍 Analyzing project: {project_path}")
    
    # Configure analyzer
    cache_dir = Path(args.cache_dir) if args.cache_dir else None
    analyzer = HighPerformanceConnascenceAnalyzer(
        max_workers=args.workers,
        enable_cache=args.cache,
        cache_dir=cache_dir
    )
    
    # Setup progress reporting
    progress_reporter = ProgressReporter(show_progress=not args.quiet)
    
    # Profile if requested
    if args.profile:
        import cProfile
        import pstats
        profiler = cProfile.Profile()
        profiler.enable()
    
    # Run analysis
    print("Starting analysis...")
    violations, metrics = analyzer.analyze_directory(
        project_path, 
        parallel=args.parallel,
        progress_callback=progress_reporter
    )
    
    if args.profile:
        profiler.disable()
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        print("\n" + "="*60)
        print("PERFORMANCE PROFILE")
        print("="*60)
        stats.print_stats(20)
    
    # Generate report
    cache_stats = analyzer.get_cache_stats()
    
    report = {
        "summary": {
            "total_violations": len(violations),
            "violations_by_type": {},
            "violations_by_severity": {},
            "files_analyzed": metrics.files_analyzed,
            "lines_analyzed": metrics.lines_analyzed,
            "analysis_duration_ms": metrics.duration_ms,
            "lines_per_second": metrics.lines_per_second,
            "cache_hit_rate": metrics.cache_hit_rate,
            "cache_hits": cache_stats.get("hits", 0),
            "cache_misses": cache_stats.get("misses", 0)
        },
        "violations": [violation.__dict__ for violation in violations],
        "performance_metrics": {
            "duration_ms": metrics.duration_ms,
            "files_analyzed": metrics.files_analyzed,
            "lines_analyzed": metrics.lines_analyzed,
            "lines_per_second": metrics.lines_per_second,
            "cache_hit_rate": metrics.cache_hit_rate
        }
    }
    
    # Calculate summary statistics
    for violation in violations:
        # By type
        v_type = violation.type
        report["summary"]["violations_by_type"][v_type] = (
            report["summary"]["violations_by_type"].get(v_type, 0) + 1
        )
        
        # By severity
        v_severity = violation.severity
        report["summary"]["violations_by_severity"][v_severity] = (
            report["summary"]["violations_by_severity"].get(v_severity, 0) + 1
        )
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"📁 Results saved to: {args.output}")
    
    if args.html:
        create_html_report(violations, report["performance_metrics"], Path(args.html))
        print(f"📄 HTML report saved to: {args.html}")
    
    if not args.output and not args.html:
        # Print to stdout
        print(json.dumps(report, indent=2))
    
    # Print summary to stderr
    print(f"\n📊 Analysis Summary:", file=sys.stderr)
    print(f"   Files analyzed: {metrics.files_analyzed:,}", file=sys.stderr)
    print(f"   Lines analyzed: {metrics.lines_analyzed:,}", file=sys.stderr)
    print(f"   Total violations: {len(violations):,}", file=sys.stderr)
    print(f"   Analysis time: {metrics.duration_ms}ms", file=sys.stderr)
    print(f"   Speed: {metrics.lines_per_second:,.0f} lines/sec", file=sys.stderr)
    
    if args.cache:
        print(f"   Cache hit rate: {metrics.cache_hit_rate:.1%}", file=sys.stderr)
    
    if args.parallel:
        print(f"   Parallel processing: {analyzer.max_workers} workers", file=sys.stderr)
    
    # Show severity breakdown
    severity_counts = report["summary"]["violations_by_severity"]
    if severity_counts:
        print(f"   Severity breakdown:", file=sys.stderr)
        for severity, count in sorted(severity_counts.items()):
            print(f"     {severity}: {count}", file=sys.stderr)
    
    return 0


def benchmark_command(args) -> int:
    """Handle benchmark command."""
    project_path = Path(args.path)
    if not project_path.exists():
        print(f"Error: Path {project_path} does not exist")
        return 1
    
    benchmark = PerformanceBenchmark()
    output_file = Path(args.output) if args.output else None
    
    print(f"🚀 Running performance benchmark on: {project_path}")
    
    try:
        benchmark.run_comprehensive_benchmark(project_path, output_file)
        return 0
    except Exception as e:
        print(f"Benchmark failed: {e}")
        return 1


def clear_cache_command(args) -> int:
    """Handle clear-cache command."""
    from .parallel_analyzer import FileCache
    
    cache_dir = Path(args.cache_dir) if args.cache_dir else None
    cache = FileCache(cache_dir)
    
    print(f"🗑️  Clearing cache directory: {cache.cache_dir}")
    cache.clear()
    print("✅ Cache cleared successfully")
    
    return 0


if __name__ == "__main__":
    exit(main())