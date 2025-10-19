#!/usr/bin/env python3
"""
Validate that detector pool fix resolved the 0 violations issue.
"""

import ast
from analyzer.refactored_detector import RefactoredConnascenceDetector

# Test code with violations for all 9 connascence types
test_code = """
import time

# CoP - Position (too many parameters)
def process_data(user_id, username, email, phone, address, city, state, zip_code):
    MAGIC = 42  # CoM - Meaning (magic literal)
    result = MAGIC * user_id
    return result

# CoT - Timing
def timing_function():
    time.sleep(0.1)  # Timing dependency
    return "done"

# CoN - Name (convention violations)
class badClassName:
    def BAD_METHOD_name(self):
        pass

# CoE - Execution (global state)
global_state = []
def modify_state():
    global global_state
    global_state.append(1)
"""

print("[DETECTOR POOL FIX VALIDATION]")
print("=" * 60)

detector = RefactoredConnascenceDetector("test.py", test_code.split("\n"))
tree = ast.parse(test_code)

violations = detector.detect_all_violations(tree)

print(f"\nTotal violations detected: {len(violations)}")
print(f"Violation types: {type(violations[0]) if violations else 'N/A'}")

# Group violations by type
violation_types = {}
for v in violations:
    if hasattr(v, 'type'):
        vtype = v.type
    elif isinstance(v, dict):
        vtype = v.get('type', 'unknown')
    else:
        vtype = str(type(v))

    violation_types[vtype] = violation_types.get(vtype, 0) + 1

print("\nViolations by type:")
for vtype, count in sorted(violation_types.items()):
    print(f"  {vtype}: {count}")

print("\n" + "=" * 60)
if len(violations) > 0:
    print("[SUCCESS] Detector pool is working! Violations detected.")
    print(f"Pool metrics: {detector.get_pool_metrics()}")
    exit(0)
else:
    print("[FAILURE] No violations detected. Pool may still be broken.")
    exit(1)
