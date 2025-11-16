#!/usr/bin/env python3
"""Run NASA Power of Ten safety analysis over a target path."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from analyzer.nasa_engine.nasa_analyzer import NASAAnalyzer  # noqa: E402

VIOLATION_MAP = {
    "goto_statement": "goto",
    "recursive_function": "recursion",
    "unbounded_loop": "loop bound",
    "malloc_after_init": "heap allocation",
    "function_too_long": "loop bound",
    "insufficient_assertions": "assertion",
    "variable_scope_too_wide": "scope",
    "unchecked_return_value": "assertion",
}


def _gather_violations(analyzer: NASAAnalyzer, target: Path) -> list:
    violations = []
    if target.is_file() and target.suffix == ".py":
        violations.extend(analyzer.analyze_file(str(target)))
        return violations

    for py_file in target.rglob("*.py"):
        violations.extend(analyzer.analyze_file(str(py_file)))
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="NASA Power of Ten analyzer")
    parser.add_argument("path", help="Path to analyze")
    args = parser.parse_args()

    target = Path(args.path).resolve()
    if not target.exists():
        print(f"[ERROR] Path not found: {target}")
        return 2

    analyzer = NASAAnalyzer()
    violations = _gather_violations(analyzer, target)

    counts = Counter()
    for violation in violations:
        label = VIOLATION_MAP.get(violation.type, violation.type)
        counts[label] += 1

    print("NASA Power of Ten Results")
    print("=" * 40)
    print(f"Loop bound issues: {counts.get('loop bound', 0)}")
    print(f"Recursion violations: {counts.get('recursion', 0)}")
    print(f"Goto statements detected: {counts.get('goto', 0)}")
    print(f"Heap allocation flags: {counts.get('heap allocation', 0)}")
    print(f"Assertion density issues: {counts.get('assertion', 0)}")
    print(f"Unchecked scope violations: {counts.get('scope', 0)}")
    print(f"Total NASA rule alerts: {sum(counts.values())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
