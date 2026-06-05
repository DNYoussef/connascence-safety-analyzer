"""
CLI entry point for theater detection.

CLI-003: Enables claude-dev-cli quality service to invoke theater detection.

Usage:
    python -m analyzer.theater_detection --path <directory> [--format json]
"""

import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

from .core import TheaterDetector, TheaterPattern


def find_python_files(path: str) -> list[str]:
    """Recursively find all Python files in a directory."""
    python_files = []
    path_obj = Path(path)

    if path_obj.is_file() and path_obj.suffix == ".py":
        return [str(path_obj)]

    if path_obj.is_dir():
        for root, _, files in os.walk(path_obj):
            for file in files:
                if file.endswith(".py"):
                    python_files.append(os.path.join(root, file))

    return python_files


def pattern_to_dict(pattern: TheaterPattern) -> dict:
    """Convert TheaterPattern to JSON-serializable dict."""
    return {
        "pattern_type": pattern.pattern_type.value,
        "severity": pattern.severity.value,
        "file_path": pattern.file_path,
        "line_number": pattern.line_number,
        "description": pattern.description,
        "evidence": pattern.evidence,
        "recommendation": pattern.recommendation,
        "confidence": pattern.confidence,
    }


def calculate_risk(patterns: list[TheaterPattern]) -> float:
    """
    Calculate theater risk score from detected patterns.

    Risk is weighted by severity:
    - CRITICAL: 0.25 per pattern
    - HIGH: 0.15 per pattern
    - MEDIUM: 0.08 per pattern
    - LOW: 0.03 per pattern

    Capped at 1.0 (100% risk).
    """
    if not patterns:
        return 0.0

    severity_weights = {
        "critical": 0.25,
        "high": 0.15,
        "medium": 0.08,
        "low": 0.03,
    }

    total_risk = 0.0
    for pattern in patterns:
        weight = severity_weights.get(pattern.severity.value, 0.05)
        total_risk += weight * pattern.confidence

    return min(total_risk, 1.0)


def main():
    parser = argparse.ArgumentParser(
        description="Detect theater patterns in Python code"
    )
    parser.add_argument(
        "--path",
        required=True,
        help="Path to file or directory to analyze"
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format (default: json)"
    )

    args = parser.parse_args()

    if not os.path.exists(args.path):
        print(f"Error: Path does not exist: {args.path}", file=sys.stderr)
        sys.exit(1)

    detector = TheaterDetector()
    python_files = find_python_files(args.path)

    all_patterns: list[TheaterPattern] = []
    for file_path in python_files:
        patterns = detector.detect_all_patterns(file_path)
        all_patterns.extend(patterns)

    risk = calculate_risk(all_patterns)

    if args.format == "json":
        result = {
            "theater_risk": risk,
            "pattern_count": len(all_patterns),
            "files_analyzed": len(python_files),
            "patterns": [pattern_to_dict(p) for p in all_patterns],
            "summary": {
                "critical": len([p for p in all_patterns if p.severity.value == "critical"]),
                "high": len([p for p in all_patterns if p.severity.value == "high"]),
                "medium": len([p for p in all_patterns if p.severity.value == "medium"]),
                "low": len([p for p in all_patterns if p.severity.value == "low"]),
            }
        }
        print(json.dumps(result, indent=2))
    else:
        print(f"Theater Detection Results")
        print(f"========================")
        print(f"Files analyzed: {len(python_files)}")
        print(f"Patterns found: {len(all_patterns)}")
        print(f"Theater risk: {risk:.1%}")
        print()

        if all_patterns:
            print("Detected patterns:")
            for pattern in all_patterns:
                print(f"  [{pattern.severity.value.upper()}] {pattern.file_path}:{pattern.line_number}")
                print(f"    {pattern.description}")
                print(f"    Recommendation: {pattern.recommendation}")
                print()

    # Exit with code 2 if theater risk is above threshold (20%)
    if risk >= 0.20:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
