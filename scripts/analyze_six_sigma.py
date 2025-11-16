#!/usr/bin/env python3
"""Run Six Sigma analysis on connascence violations for a path."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from analyzer.check_connascence import ConnascenceAnalyzer  # noqa: E402
from analyzer.enterprise.sixsigma.analyzer import SixSigmaAnalyzer  # noqa: E402


def _collect_connascence_dicts(path: Path) -> list[dict]:
    analyzer = ConnascenceAnalyzer(exclusions=[])
    if path.is_file():
        violations = analyzer.analyze_file(path)
    else:
        violations = analyzer.analyze_directory(path)
    return [v.to_dict() for v in violations]


def main() -> int:
    parser = argparse.ArgumentParser(description="Six Sigma analyzer wrapper")
    parser.add_argument("path", help="Path to analyze")
    parser.add_argument("--target", default="enterprise", help="Six Sigma quality target")
    args = parser.parse_args()

    target = Path(args.path).resolve()
    if not target.exists():
        print(f"[ERROR] Path not found: {target}")
        return 2

    violations = _collect_connascence_dicts(target)
    sixsigma = SixSigmaAnalyzer(target_level=args.target)
    result = sixsigma.analyze_violations(violations, file_path=target)

    print("Six Sigma Quality Metrics")
    print("=" * 40)
    print(f"Quality defects detected: {len(violations)}")
    print(f"DPMO: {result.dpmo:.2f} | Sigma Level: {result.sigma_level:.2f}")
    outliers = 1 if result.sigma_level < sixsigma.target_level["sigma"] else 0
    print(f"Statistical outliers (sigma shortfalls): {outliers}")
    cp, cpk = result.process_capability
    print(f"Process variation (Cp/Cpk): {cp:.2f}/{cpk:.2f}")
    print(f"Yield (RTY): {result.rty:.2f}%")

    if result.improvement_suggestions:
        print("\nImprovement suggestions:")
        for suggestion in result.improvement_suggestions:
            print(f"- {suggestion}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
