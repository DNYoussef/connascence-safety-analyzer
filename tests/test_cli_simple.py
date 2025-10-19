#!/usr/bin/env python3
"""
Simple CLI Integration Test

Direct test of detectors to verify Phase 0 integration works.
"""

import sys
import ast
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test code with violations
test_code = """
def process_data(user_id, username, email, phone, address, city, state, zip_code):
    '''8 parameters - CoP violation'''
    MAGIC = 42  # CoM violation
    return MAGIC

class BigClass:
    '''Multiple methods'''
    def m1(self): pass
    def m2(self): pass
    def m3(self): pass
    def m4(self): pass
    def m5(self): pass
"""

print("[CLI INTEGRATION TEST - Phase 1.2]")
print("=" * 60)

# Test all 8 detectors
detectors = [
    ('PositionDetector', 'analyzer.detectors.position_detector'),
    ('ValuesDetector', 'analyzer.detectors.values_detector'),
    ('AlgorithmDetector', 'analyzer.detectors.algorithm_detector'),
    ('MagicLiteralDetector', 'analyzer.detectors.magic_literal_detector'),
    ('TimingDetector', 'analyzer.detectors.timing_detector'),
    ('ExecutionDetector', 'analyzer.detectors.execution_detector'),
    ('GodObjectDetector', 'analyzer.detectors.god_object_detector'),
    ('ConventionDetector', 'analyzer.detectors.convention_detector'),
]

tree = ast.parse(test_code)
source_lines = test_code.split('\n')

total_violations = 0
detectors_passed = 0
detectors_failed = 0

for detector_name, module_path in detectors:
    try:
        # Import detector
        parts = module_path.rsplit('.', 1)
        module = __import__(parts[0], fromlist=[detector_name])
        detector_class = getattr(module, detector_name)

        # Instantiate and run
        detector = detector_class(file_path='test.py', source_lines=source_lines)
        violations = detector.detect_violations(tree)

        # Report
        status = "PASS" if isinstance(violations, list) else "FAIL"
        print(f"[{status}] {detector_name:25s} - {len(violations)} violations")

        if status == "PASS":
            detectors_passed += 1
            total_violations += len(violations)
        else:
            detectors_failed += 1

    except Exception as e:
        print(f"[FAIL] {detector_name:25s} - ERROR: {str(e)[:50]}")
        detectors_failed += 1

print("=" * 60)
print(f"Detectors Passed: {detectors_passed}/8")
print(f"Detectors Failed: {detectors_failed}/8")
print(f"Total Violations: {total_violations}")
print("=" * 60)

if detectors_failed == 0:
    print("[SUCCESS] All detectors operational")
    sys.exit(0)
else:
    print(f"[FAILURE] {detectors_failed} detector(s) failed")
    sys.exit(1)
