#!/usr/bin/env python3
"""
Manual CLI Integration Test

Tests that both CLIs work with Phase 0 refactored detectors.
"""

import os
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# Create test file with violations
test_code = """
# Test file with multiple connascence violations

def process_data(user_id, username, email, phone, address, city, state, zip_code):
    '''Function with 8 parameters - CoP violation'''
    MAGIC_NUMBER = 42  # CoM violation
    STATUS = "ACTIVE"  # CoM violation

    if user_id == MAGIC_NUMBER:
        return STATUS
    return None

class GodObject:
    '''Large class - potential god object'''
    def method1(self): pass
    def method2(self): pass
    def method3(self): pass
    def method4(self): pass
    def method5(self): pass
    def method6(self): pass
"""

test_file = project_root / "tests" / "cli_test_sample.py"
test_file.write_text(test_code)

print("[CLI INTEGRATION TEST]")
print("=" * 60)
print(f"Test file: {test_file}")
print(f"Project root: {project_root}")
print()

# Test 1: Main CLI with direct Python import
print("[TEST 1] Main CLI - Direct Import")
print("-" * 60)

try:
    os.chdir(project_root)
    from analyzer.check_connascence import ConnascenceCLI

    cli = ConnascenceCLI()
    print("✓ ConnascenceCLI imported successfully")
    print(f"  - CLI instance created: {type(cli).__name__}")

    # Test analyze method exists
    if hasattr(cli, "analyze_file"):
        print("  - analyze_file method: EXISTS")
    else:
        print("  - analyze_file method: MISSING")

except Exception as e:
    print(f"✗ Failed to import ConnascenceCLI: {e}")

print()

# Test 2: Minimal CLI with direct Python import
print("[TEST 2] Minimal CLI - Direct Import")
print("-" * 60)

try:
    from analyzer.check_connascence_minimal import main as minimal_main

    print("✓ check_connascence_minimal imported successfully")
    print(f"  - main function: {minimal_main.__name__}")

except Exception as e:
    print(f"✗ Failed to import check_connascence_minimal: {e}")

print()

# Test 3: Direct detector usage (bypass CLI)
print("[TEST 3] Direct Detector Usage")
print("-" * 60)

try:
    import ast

    from analyzer.detectors.magic_literal_detector import MagicLiteralDetector
    from analyzer.detectors.position_detector import PositionDetector

    # Parse test code
    tree = ast.parse(test_code)
    source_lines = test_code.split("\n")

    # Test PositionDetector
    pos_detector = PositionDetector(file_path=str(test_file), source_lines=source_lines)
    pos_violations = pos_detector.detect_violations(tree)
    print(f"✓ PositionDetector: {len(pos_violations)} violations found")

    # Test MagicLiteralDetector
    magic_detector = MagicLiteralDetector(file_path=str(test_file), source_lines=source_lines)
    magic_violations = magic_detector.detect_violations(tree)
    print(f"✓ MagicLiteralDetector: {len(magic_violations)} violations found")

    print(f"  - Total violations: {len(pos_violations) + len(magic_violations)}")

except Exception as e:
    print(f"✗ Direct detector usage failed: {e}")
    import traceback

    traceback.print_exc()

print()
print("=" * 60)
print("[INTEGRATION TEST COMPLETE]")

# Cleanup
if test_file.exists():
    test_file.unlink()
