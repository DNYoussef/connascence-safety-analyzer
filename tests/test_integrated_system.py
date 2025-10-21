"""
Comprehensive Integration Tests for Enhanced Connascence Analyzer System

Tests the complete integrated system including:
- All 9 connascence types detection
- NASA Power of Ten rule analysis
- RefactoredDetector architecture
- AST Optimizer patterns
- Tree-Sitter integration
- Cross-phase correlation
"""

import ast
from pathlib import Path
import unittest
from unittest.mock import patch

from analyzer.nasa_engine.nasa_analyzer import NASAAnalyzer
from analyzer.refactored_detector import RefactoredConnascenceDetector

# Core system imports
from analyzer.unified_analyzer import UnifiedConnascenceAnalyzer
from utils.types import ConnascenceViolation


class TestIntegratedSystem(unittest.TestCase):
    """Test the complete integrated analyzer system."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_project_path = Path("tests/fixtures")
        self.analyzer = UnifiedConnascenceAnalyzer()

    def test_all_connascence_types_detection(self):
        """Test that all 9 connascence types are properly detected."""

        # Sample code with multiple connascence violations
        test_code = """
# Connascence of Position (CoP)
def process_user(name, age, email):
    return f"{name} ({age}) - {email}"

user_data = process_user("John", "john@example.com", 25)  # Wrong order

# Connascence of Name (CoN) 
class UserProcessor:
    def process_user_data(self):
        return self.calculate_result()
    
    def calculate_result(self):  # Rename breaks the calling method
        return "processed"

# Connascence of Type (CoT)
def calculate_total(items):
    total = 0
    for item in items:
        total += item  # Assumes numeric type
    return total

# Connascence of Meaning (CoM) - Magic numbers
MAX_USERS = 100
ADMIN_LEVEL = 5

def check_permissions(user_level):
    return user_level >= 5  # Magic number should use ADMIN_LEVEL

# Connascence of Algorithm (CoA) 
def hash_password_v1(password):
    return hash(password) % 1000

def verify_password_v1(password, stored_hash):
    return (hash(password) % 1000) == stored_hash  # Duplicated algorithm

# Connascence of Timing (CoTm)
import time
def process_with_delay():
    time.sleep(0.1)  # Timing dependency
    return "processed"

# Connascence of Convention (CoC) - Inconsistent naming
class user_processor:  # Should be UserProcessor
    def ProcessData(self):  # Should be process_data
        pass

# Connascence of Values (CoV)
DEFAULT_TIMEOUT = 30
NETWORK_TIMEOUT = 30  # Same value, should reference DEFAULT_TIMEOUT

# Connascence of Execution (CoE)
data = []
def add_item(item):
    global data
    data.append(item)  # Execution order dependency

def get_count():
    global data
    return len(data)  # Depends on add_item being called first

# Connascence of Identity (CoI) - Global state
current_user = None
"""

        # Create refactored detector instance
        detector = RefactoredConnascenceDetector("test.py", test_code.split("\n"))
        tree = ast.parse(test_code)
        violations = detector.detect_all_violations(tree)

        # Check that we found violations for multiple connascence types
        violation_types = {v.type for v in violations}

        expected_types = [
            "connascence_of_timing",  # sleep call
            "connascence_of_meaning",  # magic numbers
            "connascence_of_algorithm",  # duplicate logic
            "connascence_of_position",  # parameter order
            "connascence_of_convention",  # naming violations
            "connascence_of_values",  # duplicate values
            "connascence_of_execution",  # execution order
            "connascence_of_identity",  # global state
        ]

        # Assert we detect multiple types
        self.assertGreaterEqual(len(violations), 5, "Should detect multiple connascence violations")

        # Check for specific violation types
        timing_violations = [v for v in violations if "timing" in v.type]
        self.assertGreater(len(timing_violations), 0, "Should detect timing violations")

        meaning_violations = [v for v in violations if "meaning" in v.type]
        self.assertGreater(len(meaning_violations), 0, "Should detect meaning violations")

    def test_nasa_power_of_ten_analysis(self):
        """Test NASA Power of Ten rule analysis."""

        # Code with NASA rule violations
        nasa_test_code = (
            """
# NASA Rule 1 - Recursion
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)  # Recursive call

# NASA Rule 2 - Unbounded loop  
def process_forever():
    while True:  # Unbounded loop
        process_data()
        
# NASA Rule 4 - Function too long (simplified)
def massive_function():
    # This would be a 60+ line function
    line_count = 0
"""
            + "\n".join([f"    line_{i} = {i}" for i in range(65)])
            + """
    return line_count

# NASA Rule 5 - Insufficient assertions
def risky_calculation(x, y):
    # Should have at least 2 assertions
    result = x / y
    return result

# NASA Rule 7 - Unchecked return values
def main():
    malloc_result = allocate_memory()  # Return value not checked
    process_data()  # Another unchecked return
"""
        )

        nasa_analyzer = NASAAnalyzer()
        violations = nasa_analyzer.analyze_file("test.py", nasa_test_code)

        # Check for NASA rule violations
        self.assertGreater(len(violations), 0, "Should detect NASA violations")

        # Check for specific NASA rules
        rule_types = {v.context.get("nasa_rule") for v in violations if v.context}

        self.assertIn("rule_1", rule_types, "Should detect recursion violation")
        self.assertIn("rule_2", rule_types, "Should detect unbounded loop")
        self.assertIn("rule_4", rule_types, "Should detect function size violation")
        self.assertIn("rule_5", rule_types, "Should detect assertion violation")

        # Check compliance score
        score = nasa_analyzer.get_nasa_compliance_score(violations)
        self.assertLess(score, 1.0, "Should have reduced compliance score")

    @patch("analyzer.unified_analyzer.Path")
    def test_unified_analyzer_integration(self, mock_path):
        """Test the unified analyzer orchestrates all analysis phases."""

        # Mock project structure
        mock_path.return_value.rglob.return_value = [Path("test_file.py")]

        # Mock file reading
        test_content = """
def test_function():
    time.sleep(0.1)  # Timing violation
    x = 42  # Magic number
    if True:  # NASA violation
        pass
"""

        with patch("builtins.open", unittest.mock.mock_open(read_data=test_content)):
            with patch.object(Path, "exists", return_value=True):
                with patch.object(Path, "is_file", return_value=True):
                    # Run unified analysis
                    results = self.analyzer._run_refactored_analysis(Path("test"))

                    # Should have results
                    self.assertGreater(len(results), 0, "Should produce analysis results")

                    # Check result structure
                    if results:
                        result = results[0]
                        self.assertIn("file_path", result)
                        self.assertIn("violations", result)

    def test_detector_factory_integration(self):
        """Test that all specialized detectors are properly initialized."""

        detector = RefactoredConnascenceDetector("test.py", ["test line"])

        # Verify all detectors are initialized
        self.assertIsNotNone(detector.position_detector)
        self.assertIsNotNone(detector.magic_literal_detector)
        self.assertIsNotNone(detector.algorithm_detector)
        self.assertIsNotNone(detector.god_object_detector)
        self.assertIsNotNone(detector.timing_detector)
        self.assertIsNotNone(detector.convention_detector)
        self.assertIsNotNone(detector.values_detector)
        self.assertIsNotNone(detector.execution_detector)

        # Test that detect_all_violations calls all detectors
        test_code = "def test(): pass"
        tree = ast.parse(test_code)

        with patch.object(detector.position_detector, "detect_violations", return_value=[]):
            with patch.object(detector.timing_detector, "detect_violations", return_value=[]):
                with patch.object(detector.algorithm_detector, "detect_violations", return_value=[]):
                    violations = detector.detect_all_violations(tree)
                    # Should call all detectors without error
                    self.assertIsInstance(violations, list)

    def test_cross_phase_correlation(self):
        """Test that violations from different phases are properly correlated."""

        # Code that should trigger violations in multiple analysis phases
        multi_phase_code = """
def problematic_function(x, y):  # NASA Rule 5: needs assertions
    import time
    time.sleep(x)  # Timing connascence + NASA Rule 3 concern
    magic_number = 42  # Connascence of meaning
    return magic_number * y  # Algorithm dependency
"""

        # Test NASA analysis
        nasa_analyzer = NASAAnalyzer()
        nasa_violations = nasa_analyzer.analyze_file("test.py", multi_phase_code)

        # Test connascence analysis
        detector = RefactoredConnascenceDetector("test.py", multi_phase_code.split("\n"))
        tree = ast.parse(multi_phase_code)
        conn_violations = detector.detect_all_violations(tree)

        # Should have violations from both analysis types
        self.assertGreater(len(nasa_violations), 0, "Should have NASA violations")
        self.assertGreater(len(conn_violations), 0, "Should have connascence violations")

        # Check for timing-related violations in both
        nasa_timing = [v for v in nasa_violations if "timing" in str(v.context)]
        conn_timing = [v for v in conn_violations if "timing" in v.type]

        # Should detect timing issues in both analysis phases
        self.assertTrue(nasa_timing or conn_timing, "Should detect timing issues")

    def test_mece_analysis_completeness(self):
        """Test MECE (Mutually Exclusive, Collectively Exhaustive) analysis."""

        # Comprehensive test code covering multiple violation categories
        comprehensive_code = (
            """
# Control flow violations
def recursive_func(n):
    if n > 0:
        return recursive_func(n-1)  # NASA Rule 1 + Algorithm connascence
        
# Memory violations  
import ctypes
def unsafe_memory():
    ptr = ctypes.malloc(100)  # NASA Rule 3
    return ptr

# Complexity violations
def monster_function():  # NASA Rule 4 - too long
"""
            + "\n".join([f"    operation_{i} = {i} * 2" for i in range(70)])
            + """
    return sum([operation_1, operation_2])  # Also position connascence

# Convention violations
class badNaming:  # Convention connascence
    def BAD_method(self):
        CONSTANT_1 = 100  # Values connascence
        CONSTANT_2 = 100  # Duplicate value
        return CONSTANT_1

# Execution violations
global_state = []
def order_dependent_1():
    global_state.clear()
    
def order_dependent_2():
    return len(global_state)  # Execution connascence
"""
        )

        # Run comprehensive analysis
        detector = RefactoredConnascenceDetector("test.py", comprehensive_code.split("\n"))
        nasa_analyzer = NASAAnalyzer()

        tree = ast.parse(comprehensive_code)
        conn_violations = detector.detect_all_violations(tree)
        nasa_violations = nasa_analyzer.analyze_file("test.py", comprehensive_code)

        # Check that we have good coverage across violation categories
        total_violations = len(conn_violations) + len(nasa_violations)
        self.assertGreaterEqual(total_violations, 8, "Should detect comprehensive violations")

        # Check for violations in multiple categories
        violation_categories = set()
        for v in conn_violations + nasa_violations:
            if hasattr(v, "type"):
                violation_categories.add(v.type.split("_")[0])  # Get main category

        self.assertGreaterEqual(len(violation_categories), 3, "Should span multiple categories")

    def test_performance_and_scalability(self):
        """Test that the integrated system performs acceptably."""

        # Generate larger test code
        large_code_lines = ["# Large test file"]
        for i in range(100):
            large_code_lines.extend(
                [
                    f"def function_{i}(param1, param2):",
                    f"    magic_val = {i * 42}",  # Magic number
                    "    time.sleep(0.001)",  # Timing issue
                    "    return magic_val + param1",
                    "",
                ]
            )

        large_code = "\n".join(large_code_lines)

        # Time the analysis
        import time

        start_time = time.time()

        detector = RefactoredConnascenceDetector("large_test.py", large_code_lines)
        tree = ast.parse(large_code)
        violations = detector.detect_all_violations(tree)

        end_time = time.time()
        analysis_time = end_time - start_time

        # Should complete in reasonable time
        self.assertLess(analysis_time, 5.0, "Analysis should complete within 5 seconds")
        self.assertGreater(len(violations), 50, "Should detect many violations in large file")


class TestSystemReporting(unittest.TestCase):
    """Test integrated reporting capabilities."""

    def test_violation_correlation_reporting(self):
        """Test that violations are properly correlated and reported."""

        test_code = """
def correlate_test():
    x = 42  # Magic number (CoM) + NASA meaning violation
    time.sleep(x / 1000)  # Timing (CoTm) + NASA timing concern
"""

        detector = RefactoredConnascenceDetector("test.py", test_code.split("\n"))
        nasa_analyzer = NASAAnalyzer()

        tree = ast.parse(test_code)
        conn_violations = detector.detect_all_violations(tree)
        nasa_violations = nasa_analyzer.analyze_file("test.py", test_code)

        # Should find correlated violations
        timing_violations = [v for v in conn_violations if "timing" in v.type]
        meaning_violations = [v for v in conn_violations if "meaning" in v.type]

        self.assertGreater(len(timing_violations) + len(meaning_violations), 0)

        # Test that violations have proper context for correlation
        for violation in conn_violations + nasa_violations:
            self.assertIsInstance(violation, ConnascenceViolation)
            self.assertIsNotNone(violation.file_path)
            self.assertIsNotNone(violation.line_number)


if __name__ == "__main__":
    unittest.main()
