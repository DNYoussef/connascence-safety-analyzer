#!/usr/bin/env python3
"""Run the Connascence Analyzer across a target path and emit Co* summaries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Dict

# Ensure project root is on the path so we can import analyzer modules
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from analyzer.check_connascence import ConnascenceAnalyzer  # noqa: E402

# Mapping between analyzer violation types and Connascence shorthand codes
TYPE_TO_CODE = {
    "connascence_of_position": "CoP",
    "connascence_of_name": "CoN",
    "connascence_of_type": "CoT",
    "connascence_of_meaning": "CoM",
    "connascence_of_algorithm": "CoA",
    "connascence_of_execution": "CoE",
    "connascence_of_values": "CoV",
    "connascence_of_identity": "CoI",
    "connascence_of_timing": "CoTiming",
    "connascence_of_convention": "CoConvention",
}

ORDERED_CODES = [
    "CoP",
    "CoN",
    "CoT",
    "CoM",
    "CoA",
    "CoE",
    "CoV",
    "CoI",
    "CoTiming",
    "CoConvention",
]


def _collect_connascence(path: Path) -> list:
    """Collect connascence violations for a given path."""

    analyzer = ConnascenceAnalyzer(exclusions=[])  # include test files intentionally
    if path.is_file():
        return analyzer.analyze_file(path)
    return analyzer.analyze_directory(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Connascence Analyzer wrapper")
    parser.add_argument("path", help="Path to analyze (file or directory)")
    args = parser.parse_args()

    target = Path(args.path).resolve()
    if not target.exists():
        print(f"[ERROR] Path not found: {target}")
        return 2

    violations = _collect_connascence(target)

    counts: Dict[str, int] = {code: 0 for code in ORDERED_CODES}
    counts["Other"] = 0

    for violation in violations:
        vtype = violation.type or violation.connascence_type or ""
        shorthand = TYPE_TO_CODE.get(vtype, "Other")
        counts.setdefault(shorthand, 0)
        counts[shorthand] += 1

    total = sum(counts.values())

    print("Connascence Analyzer Results")
    print("=" * 40)
    for code in ORDERED_CODES:
        print(f"{code}: {counts.get(code, 0)} violations")
    print(f"Other/auxiliary findings: {counts.get('Other', 0)}")
    print("-" * 40)
    print(f"Total connascence findings: {total}")

    # Emit JSON summary for downstream tooling
    summary = {
        "total": total,
        "violations": {code: counts.get(code, 0) for code in ORDERED_CODES},
    }
    print("\nJSON Summary:")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
