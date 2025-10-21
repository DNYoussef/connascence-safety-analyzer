#!/usr/bin/env python3
"""
Sandbox test to reverse-engineer why detectors find 0 violations.

This is a systematic execution verification test to understand the actual
behavior of the detection pipeline.
"""

import ast
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 80)
print("DETECTOR PIPELINE FUNCTIONALITY AUDIT")
print("=" * 80)

# Test 1: Can we import detectors?
print("\n[TEST 1] Import Test")
print("-" * 40)

try:
    from analyzer.detectors.position_detector import PositionDetector

    print("[PASS] PositionDetector imported successfully")
except Exception as e:
    print(f"[FAIL] PositionDetector import failed: {e}")
    sys.exit(1)

try:

    print("[PASS] MagicLiteralDetector imported successfully")
except Exception as e:
    print(f"[FAIL] MagicLiteralDetector import failed: {e}")

try:

    print("[PASS] GodObjectDetector imported successfully")
except Exception as e:
    print(f"[FAIL] GodObjectDetector import failed: {e}")

# Test 2: Can we instantiate detectors?
print("\n[TEST 2] Instantiation Test")
print("-" * 40)

sample_code = """
def test_function(a, b, c, d, e, f, g, h):
    '''Function with 8 parameters - should trigger CoP'''
    magic_number = 42  # Magic literal
    magic_float = 3.14  # Magic literal
    return a + b + magic_number + magic_float
"""

source_lines = sample_code.split("\n")
file_path = "test.py"

try:
    detector = PositionDetector(file_path=file_path, source_lines=source_lines)
    print("[PASS] PositionDetector instantiated")
    print(f"   - file_path: {detector.file_path}")
    print(f"   - source_lines count: {len(detector.source_lines)}")
    print(f"   - max_positional_params: {getattr(detector, 'max_positional_params', 'NOT SET')}")
except Exception as e:
    print(f"[FAIL] PositionDetector instantiation failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# Test 3: Can we parse code?
print("\n[TEST 3] AST Parsing Test")
print("-" * 40)

try:
    tree = ast.parse(sample_code)
    print("[PASS] Code parsed successfully")
    print(f"   - AST type: {type(tree)}")
    print(f"   - Body length: {len(tree.body)}")

    # Find function nodes
    func_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    print(f"   - Functions found: {len(func_nodes)}")
    for func in func_nodes:
        args_count = len(func.args.args)
        print(f"     - {func.name}: {args_count} parameters")
except Exception as e:
    print(f"[FAIL] AST parsing failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# Test 4: Can detectors detect violations?
print("\n[TEST 4] Detection Execution Test")
print("-" * 40)

try:
    violations = detector.detect_violations(tree)
    print("[PASS] detect_violations() executed")
    print(f"   - Return type: {type(violations)}")
    print(f"   - Violations count: {len(violations)}")

    if len(violations) == 0:
        print("   [WARN]  WARNING: 0 violations found (expected >0)")
        print("   Investigating why...")

        # Check if detector has necessary methods
        print("\n   Detector methods:")
        for attr in dir(detector):
            if not attr.startswith("_") and callable(getattr(detector, attr)):
                print(f"     - {attr}")

        # Check detector attributes
        print("\n   Detector attributes:")
        for attr in ["file_path", "source_lines", "max_positional_params", "context"]:
            value = getattr(detector, attr, "NOT FOUND")
            print(f"     - {attr}: {value}")

    else:
        print(f"   [PASS] Found {len(violations)} violations:")
        for i, v in enumerate(violations[:3], 1):
            print(f"      {i}. Type: {type(v)}")
            print(f"         - description: {getattr(v, 'description', 'N/A')}")
            print(f"         - line: {getattr(v, 'line_number', 'N/A')}")
            print(f"         - severity: {getattr(v, 'severity', 'N/A')}")

except Exception as e:
    print(f"[FAIL] Detection execution failed: {e}")
    import traceback

    traceback.print_exc()

    # Try to understand what went wrong
    print("\n   Debugging information:")
    print(f"   - Detector class: {detector.__class__.__name__}")
    print(f"   - Has detect_violations: {hasattr(detector, 'detect_violations')}")

    if hasattr(detector, "detect_violations"):
        import inspect

        sig = inspect.signature(detector.detect_violations)
        print(f"   - detect_violations signature: {sig}")

# Test 5: Try calling detect_violations with detailed tracing
print("\n[TEST 5] Detailed Execution Trace")
print("-" * 40)

# Add monkey-patch to trace execution
original_detect = detector.detect_violations


def traced_detect(tree):
    print(f"   → detect_violations() called with tree type: {type(tree)}")
    try:
        result = original_detect(tree)
        print(f"   ← detect_violations() returned: {type(result)} with {len(result)} items")
        return result
    except Exception as e:
        print(f"   ← detect_violations() raised exception: {e}")
        raise


detector.detect_violations = traced_detect

try:
    violations = detector.detect_violations(tree)
    print(f"\n   Final result: {len(violations)} violations")
except Exception as e:
    print(f"\n   Execution failed: {e}")

# Test 6: Check source code of detect_violations
print("\n[TEST 6] Source Code Inspection")
print("-" * 40)

try:
    import inspect

    source = inspect.getsource(PositionDetector.detect_violations)
    print("   detect_violations source code (first 50 lines):")
    lines = source.split("\n")[:50]
    for i, line in enumerate(lines, 1):
        print(f"   {i:3d} | {line}")
except Exception as e:
    print(f"   Could not get source: {e}")

print("\n" + "=" * 80)
print("AUDIT COMPLETE")
print("=" * 80)
