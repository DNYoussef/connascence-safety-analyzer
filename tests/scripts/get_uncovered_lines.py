#!/usr/bin/env python3
"""
Script to identify truly uncovered lines in architecture components.
Clears corrupted coverage database and generates fresh report.
"""

from pathlib import Path
import subprocess
import sys

# Change to project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def clean_coverage_db():
    """Remove corrupted coverage database."""
    coverage_files = list(project_root.glob(".coverage*"))
    for f in coverage_files:
        try:
            f.unlink()
            print(f"Removed: {f}")
        except Exception as e:
            print(f"Could not remove {f}: {e}")

def run_coverage():
    """Run coverage analysis."""
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/unit/test_cache_manager.py",
        "tests/unit/test_stream_processor.py",
        "tests/unit/test_metrics_collector.py",
        "tests/unit/test_report_generator.py",
        "--cov=analyzer/architecture",
        "--cov-report=term-missing",
        "--cov-report=json",
        "-v"
    ]

    result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    return result.returncode

if __name__ == "__main__":
    print("=== Cleaning Coverage Database ===")
    clean_coverage_db()

    print("\n=== Running Coverage Analysis ===")
    exit_code = run_coverage()

    print(f"\nExit code: {exit_code}")
    sys.exit(exit_code)
