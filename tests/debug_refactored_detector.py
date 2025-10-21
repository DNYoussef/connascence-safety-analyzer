#!/usr/bin/env python3
"""Debug script to understand why RefactoredConnascenceDetector returns 0 violations."""

import ast

from analyzer.refactored_detector import RefactoredConnascenceDetector

test_code = """
def problematic_function():
    time.sleep(0.1)  # Both timing and NASA concern
    magic = 42  # Both meaning and NASA concern
    return magic
"""

print("[DEBUG] Testing RefactoredConnascenceDetector")
print("=" * 60)

detector = RefactoredConnascenceDetector("test.py", test_code.split("\n"))
tree = ast.parse(test_code)

print(f"File path: {detector.file_path}")
print(f"Source lines: {len(detector.source_lines)}")
print()

violations = detector.detect_all_violations(tree)

print(f"Violations found: {len(violations)}")
print()

if violations:
    for v in violations:
        print(f"  - {v}")
else:
    print("  [NO VIOLATIONS FOUND]")

print()
print("[DEBUG] Checking detector internals:")
print(f"  detector_pool: {detector._detector_pool}")
print(f"  acquired_detectors: {detector._acquired_detectors}")
print(f"  function_definitions: {list(detector.function_definitions.keys())}")
