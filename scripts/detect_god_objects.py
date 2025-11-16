#!/usr/bin/env python3
"""Detect god objects inside a directory tree."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from analyzer.detectors.god_object_detector import GodObjectDetector  # noqa: E402


def _collect_python_files(target: Path) -> list[Path]:
    if target.is_file() and target.suffix == ".py":
        return [target]
    return sorted(target.rglob("*.py"))


def _analyze_file(file_path: Path) -> list:
    source = file_path.read_text(encoding="utf-8")
    lines = source.splitlines()
    tree = ast.parse(source, filename=str(file_path))
    detector = GodObjectDetector(str(file_path), lines)
    return detector.detect_violations(tree)


def main() -> int:
    parser = argparse.ArgumentParser(description="God object detector wrapper")
    parser.add_argument("path", help="Path to analyze for god objects")
    args = parser.parse_args()

    target = Path(args.path).resolve()
    if not target.exists():
        print(f"[ERROR] Path not found: {target}")
        return 2

    total_god_objects = 0
    excessive_methods = 0
    high_complexity = 0

    for py_file in _collect_python_files(target):
        try:
            violations = _analyze_file(py_file)
        except SyntaxError:
            continue

        for violation in violations:
            total_god_objects += 1
            method_count = violation.context.get("method_count") if violation.context else None
            loc = violation.context.get("estimated_loc") if violation.context else None
            print(
                f"GOD OBJECT: {py_file.name}:{violation.line_number} "
                f"-> {violation.description} ({method_count} methods, ~{loc} LOC)"
            )
            if method_count and method_count >= GodObjectDetector.DEFAULT_METHOD_THRESHOLD:
                excessive_methods += 1
            if loc and loc >= GodObjectDetector.DEFAULT_LOC_THRESHOLD:
                high_complexity += 1

    print("=" * 40)
    print(f"God objects detected: {total_god_objects}")
    print(f"High-complexity classes flagged: {high_complexity}")
    print(f"Excessive methods warnings: {excessive_methods}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
