#!/usr/bin/env python3
"""Run the MECE duplication analyzer over a path."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from analyzer.dup_detection.mece_analyzer import MECEAnalyzer  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="MECE duplication analyzer wrapper")
    parser.add_argument("path", help="Path to analyze")
    parser.add_argument("--comprehensive", action="store_true", help="Use comprehensive mode")
    parser.add_argument("--threshold", type=float, default=0.75, help="Similarity threshold")
    args = parser.parse_args()

    target = Path(args.path).resolve()
    if not target.exists():
        print(f"[ERROR] Path not found: {target}")
        return 2

    analyzer = MECEAnalyzer(threshold=args.threshold)
    result = analyzer.analyze_path(str(target), comprehensive=args.comprehensive)

    if not result.get("success"):
        print(f"[ERROR] MECE analysis failed: {result.get('error')}")
        return 1

    duplications = result.get("duplications", [])
    print("MECE Duplication Analyzer Results")
    print("=" * 40)
    for cluster in duplications:
        description = cluster.get("description", "Code duplication detected")
        similarity = cluster.get("similarity_score", 0.0)
        print(
            f"DUPLICATE cluster {cluster.get('id', 'n/a')}: {description} "
            f"(similarity {similarity:.2f})"
        )
        if cluster.get("functions"):
            print(f"  Similar functions: {', '.join(cluster['functions'])}")
        if cluster.get("overlap_lines"):
            print(f"  Overlapping logic spans: {cluster['overlap_lines']}")

    print("-" * 40)
    print(f"Total duplicate clusters: {len(duplications)}")
    print(json.dumps(result.get("summary", {}), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
