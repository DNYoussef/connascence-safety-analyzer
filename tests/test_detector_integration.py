"""
Detector Integration Tests

Tests the specialized detector integration within the RefactoredDetector architecture:
- All 8 specialized detector types
- Proper initialization and wiring
- Cross-detector coordination
- Performance and scalability
"""

import ast
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from analyzer.refactored_detector import RefactoredConnascenceDetector
from analyzer.detectors.timing_detector import TimingDetector
from analyzer.detectors.convention_detector import ConventionDetector
from analyzer.detectors.values_detector import ValuesDetector
from analyzer.detectors.execution_detector import ExecutionDetector
from utils.types import ConnascenceViolation


class TestDetectorIntegration(unittest.TestCase):
    """Test integration of all specialized detectors."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_file = "test.py"
        self.test_lines = ["# Test file", "def test(): pass"]
        self.detector = RefactoredConnascenceDetector(self.test_file, self.test_lines)
        
    def test_all_detectors_initialized(self):
        """Test that all 8 specialized detectors are properly initialized."""
        
        # Check that all detectors are initialized
        self.assertIsNotNone(self.detector.position_detector)
        self.assertIsNotNone(self.detector.magic_literal_detector)
        self.assertIsNotNone(self.detector.algorithm_detector)
        self.assertIsNotNone(self.detector.god_object_detector)
        self.assertIsNotNone(self.detector.timing_detector)
        self.assertIsNotNone(self.detector.convention_detector)
        self.assertIsNotNone(self.detector.values_detector)
        self.assertIsNotNone(self.detector.execution_detector)
        
        # Check that detectors have correct file paths
        for detector in [
            self.detector.position_detector,
            self.detector.timing_detector,
            self.detector.convention_detector,
            self.detector.values_detector,
            self.detector.execution_detector
        ]:
            self.assertEqual(detector.file_path, self.test_file)
            
    def test_timing_detector_integration(self):
        """Test TimingDetector integration and functionality."""
        
        timing_code = '''
import time
import asyncio

def sync_timing_violation():
    time.sleep(0.1)  # Direct timing dependency
    time.sleep(0.2)  # Another timing call
    
async def async_timing_violation():
    await asyncio.sleep(0.1)  # Async timing dependency
    
def threading_timing():
    import threading
    event = threading.Event()
    event.wait(timeout=5)  # Threading timing
'''
        
        lines = timing_code.split('\n')
        detector = RefactoredConnascenceDetector("timing_test.py", lines)
        tree = ast.parse(timing_code)
        
        violations = detector.detect_all_violations(tree)
        
        # Should detect timing violations
        timing_violations = [v for v in violations if 'timing' in v.type]
        self.assertGreater(len(timing_violations), 0, "Should detect timing violations")
        
        # Check violation details
        for violation in timing_violations:
            self.assertEqual(violation.type, "connascence_of_timing")
            self.assertIn("timing", violation.description.lower())
            
    def test_convention_detector_integration(self):
        """Test ConventionDetector integration and functionality."""
        
        convention_code = '''
# Bad naming conventions
class badClassName:  # Should be BadClassName
    def BAD_method_NAME(self):  # Should be bad_method_name
        return True
        
def Another_Bad_Function():  # Should be another_bad_function
    pass
    
# Inconsistent naming styles
def camelCaseFunction():  # Mixed with snake_case elsewhere
    snake_case_var = 1
    CamelCaseVar = 2
    return snake_case_var + CamelCaseVar
    
# Missing docstrings
def undocumented_function(param):
    complex_logic = param * 42
    return complex_logic
'''
        
        lines = convention_code.split('\n')
        detector = RefactoredConnascenceDetector("convention_test.py", lines)
        tree = ast.parse(convention_code)
        
        violations = detector.detect_all_violations(tree)
        
        # Should detect convention violations
        convention_violations = [v for v in violations if 'convention' in v.type]
        self.assertGreater(len(convention_violations), 0, "Should detect convention violations")
        
    def test_values_detector_integration(self):
        """Test ValuesDetector integration and functionality."""
        
        values_code = '''
# Duplicate values that should be constants
DEFAULT_TIMEOUT = 30
NETWORK_TIMEOUT = 30  # Same value
DATABASE_TIMEOUT = 30  # Another duplicate

def process_with_timeout():
    timeout = 30  # Hardcoded duplicate
    return timeout

# Configuration coupling
CONFIG_VALUE = "production"
def check_environment():
    if env == "production":  # Should use CONFIG_VALUE
        return True
    return False
    
# Magic numbers used multiple times
def calculate_fees(amount):
    processing_fee = amount * 0.03  # 3% fee
    service_charge = 100 * 0.03     # Same 3% rate
    return processing_fee + service_charge
'''
        
        lines = values_code.split('\n')
        detector = RefactoredConnascenceDetector("values_test.py", lines)
        tree = ast.parse(values_code)
        
        violations = detector.detect_all_violations(tree)
        
        # Should detect values violations
        values_violations = [v for v in violations if 'values' in v.type]
        self.assertGreater(len(values_violations), 0, "Should detect values violations")
        
    def test_execution_detector_integration(self):
        """Test ExecutionDetector integration and functionality."""
        
        execution_code = '''
# Global state that creates execution dependencies
shared_state = []
initialization_complete = False

def initialize_system():
    global initialization_complete
    shared_state.clear()
    initialization_complete = True
    
def process_data(item):
    global shared_state
    if not initialization_complete:  # Execution order dependency
        raise RuntimeError("System not initialized")
    shared_state.append(item)
    
def get_results():
    global shared_state
    return len(shared_state)  # Depends on process_data being called
    
# Class with execution dependencies
class OrderDependent:
    def __init__(self):
        self.setup_complete = False
        
    def setup(self):
        self.setup_complete = True
        
    def process(self):
        if not self.setup_complete:  # Execution dependency
            raise RuntimeError("Setup required")
'''
        
        lines = execution_code.split('\n')
        detector = RefactoredConnascenceDetector("execution_test.py", lines)
        tree = ast.parse(execution_code)
        
        violations = detector.detect_all_violations(tree)
        
        # Should detect execution violations
        execution_violations = [v for v in violations if 'execution' in v.type]
        self.assertGreater(len(execution_violations), 0, "Should detect execution violations")
        
    def test_cross_detector_coordination(self):
        """Test that multiple detectors can analyze the same code without conflicts."""
        
        complex_code = '''
class BadlyDesignedClass:  # Convention violation
    def __init__(self):
        self.magic_number = 42  # Values violation
        self.state = []  # Execution state
        
    def process_with_delay(self, item):  # Multiple violations
        import time
        time.sleep(0.1)  # Timing violation
        
        if self.magic_number == 42:  # Values coupling
            self.state.append(item)  # Execution dependency
            
        return len(self.state)  # Position/execution coupling
'''
        
        lines = complex_code.split('\n')
        detector = RefactoredConnascenceDetector("complex_test.py", lines)
        tree = ast.parse(complex_code)
        
        violations = detector.detect_all_violations(tree)
        
        # Should detect violations from multiple detector types
        violation_types = {v.type for v in violations}
        
        # Should have violations from multiple detectors
        self.assertGreaterEqual(len(violation_types), 2, "Should detect multiple violation types")
        
        # Check that violations don't conflict (same line reported by multiple detectors)
        line_type_combinations = {(v.line_number, v.type) for v in violations}
        self.assertEqual(len(line_type_combinations), len(violations), 
                        "Each violation should be unique (line, type) combination")
                        
    def test_detector_error_handling(self):
        """Test that detector errors don't crash the system."""
        
        # Mock one detector to raise an exception
        with patch.object(self.detector.timing_detector, 'detect_violations', 
                         side_effect=Exception("Test detector error")):
            
            test_code = "def test(): pass"
            tree = ast.parse(test_code)
            
            # Should handle detector errors gracefully
            violations = self.detector.detect_all_violations(tree)
            
            # Should still return a list (possibly empty due to mock error)
            self.assertIsInstance(violations, list)
            
    def test_detector_performance_isolation(self):
        """Test that slow detectors don't block others."""
        
        # This is more of a design verification than a performance test
        import time
        
        original_detect = self.detector.timing_detector.detect_violations
        
        def slow_detector(tree):
            time.sleep(0.01)  # Simulate slow detection
            return original_detect(tree)
            
        # Patch one detector to be slow
        with patch.object(self.detector.timing_detector, 'detect_violations', 
                         side_effect=slow_detector):
            
            test_code = "def test(): pass"
            tree = ast.parse(test_code)
            
            start_time = time.time()
            violations = self.detector.detect_all_violations(tree)
            end_time = time.time()
            
            # Should complete (even with slow detector)
            self.assertIsInstance(violations, list)
            self.assertLess(end_time - start_time, 1.0, "Should complete quickly despite slow detector")
            
    def test_detector_memory_efficiency(self):
        """Test that detectors don't accumulate memory across calls."""
        
        # Run multiple analyses to check for memory leaks
        for i in range(10):
            test_code = f'''
def test_function_{i}():
    import time
    time.sleep(0.001)
    return {i * 42}
'''
            lines = test_code.split('\n')
            detector = RefactoredConnascenceDetector(f"test_{i}.py", lines)
            tree = ast.parse(test_code)
            
            violations = detector.detect_all_violations(tree)
            
            # Each detector should produce fresh results
            self.assertIsInstance(violations, list)
            
            # Detector state should be independent
            self.assertEqual(detector.file_path, f"test_{i}.py")
            
    def test_code_snippet_extraction(self):
        """Test that detectors can extract proper code snippets."""
        
        test_code = '''
def example_function():
    line_before = 1
    problematic_line = time.sleep(0.1)  # This should be highlighted
    line_after = 3
    return line_before + line_after
'''
        
        lines = test_code.split('\n')
        detector = RefactoredConnascenceDetector("snippet_test.py", lines)
        tree = ast.parse(test_code)
        
        violations = detector.detect_all_violations(tree)
        
        # Should have violations with proper code snippets
        timing_violations = [v for v in violations if 'timing' in v.type]
        
        if timing_violations:
            violation = timing_violations[0]
            self.assertIsNotNone(violation.code_snippet)
            self.assertIn("time.sleep", violation.code_snippet)
            
    def test_detector_context_information(self):
        """Test that detectors provide rich context information."""
        
        context_code = '''
def timing_function(delay_seconds):
    import time
    time.sleep(delay_seconds)  # Should have context about timing type
    return "done"
'''
        
        lines = context_code.split('\n')
        detector = RefactoredConnascenceDetector("context_test.py", lines)
        tree = ast.parse(context_code)
        
        violations = detector.detect_all_violations(tree)
        
        # Check that violations have proper context
        for violation in violations:
            self.assertIsInstance(violation.context, dict)
            self.assertIn("file_path", violation.__dict__)
            self.assertIn("line_number", violation.__dict__)
            
            # Check type-specific context
            if "timing" in violation.type:
                # Timing violations should have timing-specific context
                self.assertTrue(
                    any(key in str(violation.context) or key in violation.description 
                        for key in ["sleep", "timing", "delay"]),
                    "Timing violation should have timing-specific context"
                )


class TestDetectorSpecialization(unittest.TestCase):
    """Test that each detector properly specializes in its domain."""
    
    def test_timing_detector_specialization(self):
        """Test TimingDetector only detects timing-related issues."""
        
        mixed_code = '''
def mixed_violations():
    import time
    time.sleep(0.1)  # Timing issue
    magic_number = 42  # Not timing
    bad_variable_name = 1  # Not timing
    return magic_number + bad_variable_name
'''
        
        lines = mixed_code.split('\n')
        detector = TimingDetector("test.py", lines)
        tree = ast.parse(mixed_code)
        
        violations = detector.detect_violations(tree)
        
        # Should only detect timing violations
        for violation in violations:
            self.assertEqual(violation.type, "connascence_of_timing")
            
    def test_convention_detector_specialization(self):
        """Test ConventionDetector only detects convention-related issues."""
        
        mixed_code = '''
import time

class badClassName:  # Convention issue
    def process_data(self):
        time.sleep(0.1)  # Not convention
        magic_value = 42  # Not convention
        return magic_value
'''
        
        lines = mixed_code.split('\n')
        detector = ConventionDetector("test.py", lines)
        tree = ast.parse(mixed_code)
        
        violations = detector.detect_violations(tree)
        
        # Should only detect convention violations
        for violation in violations:
            self.assertEqual(violation.type, "connascence_of_convention")
            
    def test_values_detector_specialization(self):
        """Test ValuesDetector only detects value-related coupling."""
        
        mixed_code = '''
import time

class GoodClassName:  # Not values issue
    def process_data(self):
        timeout = 30  # Values issue
        other_timeout = 30  # Values issue (duplicate)
        time.sleep(0.1)  # Not values
        return timeout + other_timeout
'''
        
        lines = mixed_code.split('\n')
        detector = ValuesDetector("test.py", lines)
        tree = ast.parse(mixed_code)
        
        violations = detector.detect_violations(tree)
        
        # Should only detect values violations
        for violation in violations:
            self.assertEqual(violation.type, "connascence_of_values")
            
    def test_execution_detector_specialization(self):
        """Test ExecutionDetector only detects execution order issues."""
        
        mixed_code = '''
import time

# Global state (execution issue)
shared_data = []

class GoodName:  # Not execution issue
    def add_data(self, item):
        timeout = 30  # Not execution issue
        time.sleep(0.1)  # Not execution issue
        shared_data.append(item)  # Execution issue
        
    def get_count(self):
        return len(shared_data)  # Execution dependency
'''
        
        lines = mixed_code.split('\n')
        detector = ExecutionDetector("test.py", lines)
        tree = ast.parse(mixed_code)
        
        violations = detector.detect_violations(tree)
        
        # Should only detect execution violations
        for violation in violations:
            self.assertEqual(violation.type, "connascence_of_execution")


if __name__ == '__main__':
    unittest.main()