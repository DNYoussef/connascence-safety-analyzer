#!/usr/bin/env python3
"""Execute the Unified Quality Gate pipeline and emit structured output."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from analyzer.quality_gates.unified_quality_gate import UnifiedQualityGate  # noqa: E402


def _summarize(results) -> dict:
    analyzer_counts = {}
    for violation in results.violations:
        source = violation.source_analyzer or "unknown"
        analyzer_counts[source] = analyzer_counts.get(source, 0) + 1

    analyzers = [
        {"name": name, "violations": count}
        for name, count in sorted(analyzer_counts.items())
    ]

    return {
        "total_violations": len(results.violations),
        "files_analyzed": results.metrics.get("files_affected", 0),
        "scores": {
            "clarity": results.clarity_score,
            "connascence": results.connascence_score,
            "nasa": results.nasa_compliance_score,
            "overall": results.overall_score,
        },
        "analyzers": analyzers,
        "metadata": results.metadata,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Unified enterprise pipeline runner")
    parser.add_argument("path", help="Path to analyze")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    parser.add_argument("--config", help="Optional quality gate config file")
    args = parser.parse_args()

    target = Path(args.path).resolve()
    if not target.exists():
        print(f"[ERROR] Path not found: {target}")
        return 2

    gate = UnifiedQualityGate(config_path=args.config)
    results = gate.analyze_project(str(target))
    summary = _summarize(results)

    if args.format == "json":
        print(json.dumps(summary, indent=2))
    else:
        print("Enterprise Pipeline Results")
        print("=" * 40)
        for analyzer in summary["analyzers"]:
            print(f"{analyzer['name']}: {analyzer['violations']} violations")
        print("-" * 40)
        print(f"Total violations: {summary['total_violations']}")
        print(f"Quality scores: {summary['scores']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
