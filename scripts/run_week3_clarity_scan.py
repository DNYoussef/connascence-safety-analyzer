#!/usr/bin/env python3
"""Run Clarity Linter scan to identify Week 3 violations (thin helpers, mega-functions)"""

from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.clarity_linter import ClarityLinter


def main():
    print("=" * 80)
    print("WEEK 3 CLARITY LINTER SCAN")
    print("=" * 80)
    print("\nTarget: analyzer/ directory")
    print("Focus: CLARITY001 (thin helpers), CLARITY011 (mega-functions)")
    print()

    # Initialize linter
    linter = ClarityLinter()

    # Analyze analyzer directory
    analyzer_path = Path(__file__).parent.parent / "analyzer"

    try:
        violations = linter.analyze_project(analyzer_path)

        # Filter for Week 3 target violations
        thin_helpers = [v for v in violations if v.rule_id == "CLARITY001"]
        mega_functions = [v for v in violations if v.rule_id == "CLARITY011"]

        print(f"Total violations found: {len(violations)}")
        print(f"  - CLARITY001 (Thin Helpers): {len(thin_helpers)}")
        print(f"  - CLARITY011 (Mega-Functions): {len(mega_functions)}")
        print()

        # Print thin helpers
        if thin_helpers:
            print("\n" + "=" * 80)
            print("THIN HELPERS TO FIX (CLARITY001)")
            print("=" * 80)
            for i, v in enumerate(thin_helpers[:20], 1):
                print(f"\n{i}. {v.file_path.name}:{v.line_number}")
                print(f"   {v.message}")

        # Print mega-functions
        if mega_functions:
            print("\n" + "=" * 80)
            print("MEGA-FUNCTIONS TO FIX (CLARITY011)")
            print("=" * 80)
            for i, v in enumerate(mega_functions[:20], 1):
                print(f"\n{i}. {v.file_path.name}:{v.line_number}")
                print(f"   {v.message}")

        # Summary
        print("\n" + "=" * 80)
        print("WEEK 3 WORK IDENTIFIED")
        print("=" * 80)
        print(f"Thin helpers to inline: {len(thin_helpers)} (target: 15-20)")
        print(f"Mega-functions to split: {len(mega_functions)} (target: 8-10)")
        print(f"\nEstimated LOC reduction: {len(thin_helpers) * 10 + len(mega_functions) * 50} lines")

        return 0

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
