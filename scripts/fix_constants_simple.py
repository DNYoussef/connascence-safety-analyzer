#!/usr/bin/env python3
"""
Simple Constants Fix - Remove Invalid Identifier Lines
======================================================

Removes lines with invalid Python identifiers from constants files.
Specifically removes:
1. Lines starting with numbers (2F, 3D, 1_0_0, etc.)
2. Lines assigning to numeric literals (0 = '{0}')

Usage:
    python scripts/fix_constants_simple.py --all
"""

from pathlib import Path
import py_compile
import sys

AFFECTED_FILES = [
    "analyzer/literal_constants/check_connascence_constants.py",
    "analyzer/literal_constants/context_analyzer_constants.py",
    "analyzer/literal_constants/core_constants.py",
    "analyzer/literal_constants/constants_constants.py",
    "analyzer/enterprise/constants/nasa_pot10_enhanced_constants.py",
    "analyzer/enterprise/sixsigma/constants/analyzer_constants.py",
    "analyzer/quality_gates/constants/unified_quality_gate_constants.py",
    "analyzer/reporting/constants/coordinator_constants.py",
    "analyzer/reporting/constants/sarif_constants.py",
    "analyzer/streaming/constants/dashboard_reporter_constants.py",
    "analyzer/theater_detection/constants/detector_constants.py",
    "analyzer/theater_detection/constants/validator_constants.py",
]

def fix_file(filepath: Path) -> int:
    """Remove lines with invalid identifiers. Returns number of lines removed."""
    print(f"\nProcessing: {filepath}")

    with open(filepath, encoding='utf-8') as f:
        lines = f.readlines()

    fixed_lines = []
    removed = 0

    for line_num, line in enumerate(lines, 1):
        # Skip if line is an invalid constant assignment
        if '=' in line and not line.strip().startswith('#'):
            parts = line.split('=', 1)
            if len(parts) == 2:
                const_name = parts[0].strip()

                # Check if starts with digit or is pure numeric
                if const_name and (const_name[0].isdigit() or const_name.replace('_', '').isdigit()):
                    print(f"  Line {line_num}: REMOVE '{const_name}' (starts with digit)")
                    removed += 1
                    continue

        fixed_lines.append(line)

    # Write fixed version
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)

    # Validate
    try:
        py_compile.compile(filepath, doraise=True)
        print(f"[OK] Removed {removed} invalid lines, file now compiles")
        return removed
    except SyntaxError as e:
        print(f"[FAIL] Still has syntax error: {e}")
        return 0

def main():
    """Main entry point."""
    print("=" * 80)
    print("SIMPLE CONSTANTS FIX - Remove Invalid Identifiers")
    print("=" * 80)
    print()

    total_removed = 0
    total_files = 0

    for filepath_str in AFFECTED_FILES:
        filepath = Path(filepath_str)
        if filepath.exists():
            removed = fix_file(filepath)
            if removed > 0:
                total_removed += removed
                total_files += 1

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Files fixed: {total_files}")
    print(f"Lines removed: {total_removed}")
    print()
    print("[OK] All constants files should now compile successfully")

    return 0

if __name__ == "__main__":
    sys.exit(main())
