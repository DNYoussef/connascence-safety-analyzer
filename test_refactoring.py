#!/usr/bin/env python3
"""
Test script to verify the refactored detector classes work correctly.
"""

import ast
import sys
from pathlib import Path

# Add analyzer and detectors to path
sys.path.insert(0, str(Path(__file__).parent / "analyzer"))
sys.path.insert(0, str(Path(__file__).parent / "analyzer" / "detectors"))

from refactored_detector import RefactoredConnascenceDetector
from check_connascence import ConnascenceDetector


def test_sample_code():
    """Test both detectors on sample code with known violations."""
    
    sample_code = '''
def bad_function(a, b, c, d, e, f):  # Too many parameters
    if a == 42:  # Magic literal
        time.sleep(1)  # Timing violation
        return True
    return False

def duplicate_function(x, y, z, w, q, r):  # Duplicate algorithm + params
    if x == 42:  # Same magic literal
        time.sleep(1)  # Same timing
        return True
    return False

class GodClass:  # This would be detected as god object in real analysis
    def method1(self): pass
    def method2(self): pass
    def method3(self): pass
    # ... many more methods would be here
'''
    
    source_lines = sample_code.strip().split('\n')
    tree = ast.parse(sample_code)
    
    # Test original detector
    print("Testing Original ConnascenceDetector...")
    original_detector = ConnascenceDetector("test.py", source_lines)
    original_detector.visit(tree)
    original_detector.finalize_analysis()
    
    print(f"Original detector found {len(original_detector.violations)} violations:")
    for v in original_detector.violations:
        print(f"  - {v.type}: {v.description}")
    
    print("\nTesting Refactored ConnascenceDetector...")
    refactored_detector = RefactoredConnascenceDetector("test.py", source_lines)
    refactored_violations = refactored_detector.detect_all_violations(tree)
    
    print(f"Refactored detector found {len(refactored_violations)} violations:")
    for v in refactored_violations:
        print(f"  - {v.type}: {v.description}")
    
    return len(original_detector.violations), len(refactored_violations)


def test_individual_detectors():
    """Test individual detector classes."""
    
    sample_code = '''
def test_func(a, b, c, d, e):  # Position violation
    x = 42  # Magic literal
    time.sleep(1)  # Timing violation
    return x == 100  # Another magic literal
'''
    
    source_lines = sample_code.strip().split('\n')
    tree = ast.parse(sample_code)
    
    # Test individual detectors
    from position_detector import PositionDetector
    from magic_literal_detector import MagicLiteralDetector 
    from timing_detector import TimingDetector
    
    print("Testing Individual Detectors...")
    
    # Position detector
    pos_detector = PositionDetector("test.py", source_lines)
    pos_violations = pos_detector.detect_violations(tree)
    print(f"Position detector: {len(pos_violations)} violations")
    
    # Magic literal detector
    magic_detector = MagicLiteralDetector("test.py", source_lines) 
    magic_violations = magic_detector.detect_violations(tree)
    print(f"Magic literal detector: {len(magic_violations)} violations")
    
    # Timing detector
    timing_detector = TimingDetector("test.py", source_lines)
    timing_violations = timing_detector.detect_violations(tree)
    print(f"Timing detector: {len(timing_violations)} violations")
    
    total_individual = len(pos_violations) + len(magic_violations) + len(timing_violations)
    print(f"Total individual violations: {total_individual}")
    
    return total_individual


if __name__ == "__main__":
    print("="*60)
    print("REFACTORING TEST")
    print("="*60)
    
    try:
        original_count, refactored_count = test_sample_code()
        print(f"\nSummary:")
        print(f"Original detector violations: {original_count}")
        print(f"Refactored detector violations: {refactored_count}")
        
        if refactored_count > 0:
            print("[PASS] Refactored detector is working!")
        else:
            print("[FAIL] Refactored detector may have issues")
        
        print("\n" + "="*60)
        individual_count = test_individual_detectors()
        print(f"Individual detectors total: {individual_count}")
        
        if individual_count > 0:
            print("[PASS] Individual detectors are working!")
        else:
            print("[FAIL] Individual detectors may have issues")
            
    except Exception as e:
        print(f"[ERROR] Test failed with error: {e}")
        import traceback
        traceback.print_exc()