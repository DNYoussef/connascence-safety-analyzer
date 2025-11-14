#!/usr/bin/env python3
"""Simple verification script for ISSUE-002: Fix Import Path Issues.

This script validates that E2E test modules can collect successfully,
which was the core requirement of ISSUE-002.

Usage:
    python scripts/verify-issue-002-simple.py
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Run E2E collection verification."""
    print("\n" + "="*70)
    print("ISSUE-002 Verification: E2E Test Collection")
    print("="*70 + "\n")

    e2e_modules = [
        'test_cli_workflows.py',
        'test_enterprise_scale.py',
        'test_error_handling.py',
        'test_exit_codes.py',
        'test_memory_coordination.py',
        'test_performance.py',
        'test_report_generation.py',
        'test_repository_analysis.py',
    ]

    project_root = Path(__file__).parent.parent
    tests_dir = project_root / 'tests' / 'e2e'

    if not tests_dir.exists():
        print(f"ERROR: Tests directory not found: {tests_dir}")
        return 1

    total_tests = 0
    modules_passed = 0
    modules_total = len(e2e_modules)

    for module in e2e_modules:
        module_path = tests_dir / module

        if not module_path.exists():
            print(f"SKIP {module}: File not found")
            continue

        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', str(module_path), '--collect-only', '-q'],
                capture_output=True,
                text=True,
                cwd=str(project_root),
                timeout=30
            )

            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'collected' in line.lower():
                        parts = line.split()
                        if parts:
                            try:
                                count = int(parts[0])
                                total_tests += count
                                print(f"OK   {module}: {count} tests collected")
                                modules_passed += 1
                                break
                            except (ValueError, IndexError):
                                pass
            else:
                print(f"FAIL {module}: Collection failed")

        except subprocess.TimeoutExpired:
            print(f"FAIL {module}: Collection timed out")
        except Exception as e:
            print(f"FAIL {module}: {e}")

    # Print summary
    print("\n" + "="*70)
    print(f"Results: {modules_passed}/{modules_total} modules passed")
    print(f"Total tests collected: {total_tests}")
    print("="*70)

    if modules_passed == modules_total:
        print("\nOK ISSUE-002 RESOLVED: All E2E test modules can collect")
        return 0
    else:
        print("\nFAIL ISSUE-002 NOT RESOLVED: Some E2E modules cannot collect")
        return 1

if __name__ == '__main__':
    sys.exit(main())
