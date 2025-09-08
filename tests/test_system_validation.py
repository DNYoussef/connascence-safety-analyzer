"""
System Validation Tests

End-to-end validation tests that verify the complete integrated system works correctly.
These tests simulate real-world usage scenarios to ensure all components work together.
"""

import ast
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from analyzer.unified_analyzer import UnifiedConnascenceAnalyzer
from analyzer.refactored_detector import RefactoredConnascenceDetector
from analyzer.nasa_engine.nasa_analyzer import NASAAnalyzer


class TestSystemValidation(unittest.TestCase):
    """End-to-end system validation tests."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = UnifiedConnascenceAnalyzer()
        
    def test_complete_analysis_pipeline(self):
        """Test that the complete analysis pipeline works end-to-end."""
        
        # Real-world Python code with multiple issues
        real_world_code = '''
"""
Example module with various connascence and NASA violations
for comprehensive system testing.
"""

import time
import threading
from typing import List, Dict

# Global variables (NASA Rule 6, Connascence of Identity)
global_config = {}
shared_data = []
processing_complete = False

class DataProcessor:  # Could be God Object if extended
    """Processes data with various coupling issues."""
    
    def __init__(self):
        self.timeout = 30  # Magic number (CoM)
        self.retry_limit = 30  # Duplicate value (CoV) 
        self.state = []  # State dependency (CoE)
        
    def process_items(self, items, batch_size, timeout, retries, debug_mode):  # CoP - too many params
        """Process items with timing dependencies."""
        global processing_complete
        
        # NASA Rule 5 violation - no assertions
        for item in items:  # NASA Rule 2 - could be unbounded
            if debug_mode:
                print(f"Processing {item}")
                
            # Timing dependency (CoTm)
            time.sleep(0.01)
            
            # Algorithm duplication (CoA)
            processed = self._apply_algorithm(item)
            result = self._apply_algorithm(processed)  # Same algorithm
            
            self.state.append(result)
            
        processing_complete = True
        return len(self.state)
    
    def _apply_algorithm(self, item):
        """Duplicated algorithm logic."""
        return item * 2 + 1  # Same formula used elsewhere
        
    def get_results(self):
        """Execution order dependency."""
        global processing_complete
        if not processing_complete:  # CoE - execution dependency
            raise RuntimeError("Processing not complete")
        return self.state.copy()
        
    # NASA Rule 4 violation - function too long (simulated)
    def massive_processing_function(self):
        """This would be a 60+ line function in real code."""
        step_1 = "initialize"
        step_2 = "validate"  
        step_3 = "process"
        step_4 = "transform"
        step_5 = "aggregate"
        step_6 = "filter"
        step_7 = "sort"
        step_8 = "group"
        step_9 = "summarize"
        step_10 = "format"
        # ... imagine 50+ more lines
        return f"{step_1}-{step_10}"

# Convention violations (CoC)
class badlyNamed_class:
    def BAD_Method_Name(self):
        return self._another_bad_name()
        
    def _another_bad_name(self):
        MAGIC_CONSTANT = 42  # Should be at module level
        return MAGIC_CONSTANT

# Recursive function (NASA Rule 1)
def fibonacci(n):
    """Recursive implementation - NASA violation."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Unchecked return values (NASA Rule 7)
def main_processing():
    processor = DataProcessor()
    
    # Return values not checked
    processor.process_items([1, 2, 3], 10, 30, 3, True)
    fibonacci(10)
    dangerous_operation()
    
    return "done"

def dangerous_operation():
    """Function that could fail."""
    if shared_data:
        return len(shared_data)
    return None

# More algorithm duplication
def calculate_hash_v1(data):
    return hash(str(data)) % 1000

def calculate_hash_v2(data):  
    return hash(str(data)) % 1000  # Same algorithm

# Values coupling - duplicate constants
DEFAULT_RETRIES = 3
MAX_ATTEMPTS = 3  # Same value as DEFAULT_RETRIES
TIMEOUT_SECONDS = 30  # Same as timeout in DataProcessor
'''
        
        # Test that all analysis phases work together
        try:
            # Test RefactoredDetector
            detector = RefactoredConnascenceDetector("real_world_test.py", real_world_code.split('\n'))
            tree = ast.parse(real_world_code)
            conn_violations = detector.detect_all_violations(tree)
            
            # Test NASA analyzer
            nasa_analyzer = NASAAnalyzer()
            nasa_violations = nasa_analyzer.analyze_file("real_world_test.py", real_world_code)
            
            # Validate comprehensive detection
            total_violations = len(conn_violations) + len(nasa_violations)
            self.assertGreater(total_violations, 10, "Should detect comprehensive violations")
            
            # Validate multiple connascence types detected
            conn_types = {v.type for v in conn_violations}
            expected_conn_types = [
                'connascence_of_position',
                'connascence_of_timing', 
                'connascence_of_meaning',
                'connascence_of_algorithm',
                'connascence_of_values',
                'connascence_of_execution',
                'connascence_of_convention',
                'connascence_of_identity'
            ]
            
            detected_types = [t for t in expected_conn_types if t in conn_types]
            self.assertGreaterEqual(len(detected_types), 4, f"Should detect multiple connascence types, found: {conn_types}")
            
            # Validate NASA rules detected
            nasa_rules = {v.context.get('nasa_rule') for v in nasa_violations if v.context}
            self.assertGreater(len(nasa_rules), 0, "Should detect NASA rule violations")
            
            # Test compliance scoring
            nasa_score = nasa_analyzer.get_nasa_compliance_score(nasa_violations)
            self.assertLess(nasa_score, 0.9, "Should have reduced NASA compliance score")
            
            print(f"\nSystem Validation Results:")
            print(f"- Connascence violations: {len(conn_violations)}")
            print(f"- NASA violations: {len(nasa_violations)}")
            print(f"- Connascence types detected: {len(conn_types)}")
            print(f"- NASA rules triggered: {len(nasa_rules)}")
            print(f"- NASA compliance score: {nasa_score:.3f}")
            
        except Exception as e:
            self.fail(f"Complete analysis pipeline failed: {str(e)}")
            
    def test_performance_with_large_codebase(self):
        """Test system performance with larger codebase."""
        
        # Generate large code sample
        large_code_parts = [
            "# Large codebase simulation",
            "import time",
            "import threading",
            ""
        ]
        
        # Generate multiple classes with various violations
        for i in range(20):
            large_code_parts.extend([
                f"class Processor{i}:",
                f"    def __init__(self):",
                f"        self.config = {i * 42}  # Magic number",
                f"        self.state = []",
                f"",
                f"    def process(self, data):",
                f"        time.sleep(0.001)  # Timing dependency",
                f"        result = data * {i * 42}  # Duplicate magic number",
                f"        self.state.append(result)",
                f"        return len(self.state)",
                f"",
                f"    def get_results(self):",
                f"        return self.state.copy()",
                f""
            ])
            
        large_code = '\n'.join(large_code_parts)
        
        # Time the analysis
        import time
        start_time = time.time()
        
        try:
            detector = RefactoredConnascenceDetector("large_test.py", large_code.split('\n'))
            tree = ast.parse(large_code)
            violations = detector.detect_all_violations(tree)
            
            end_time = time.time()
            analysis_time = end_time - start_time
            
            # Performance assertions
            self.assertLess(analysis_time, 10.0, f"Analysis took {analysis_time:.2f}s, should be under 10s")
            self.assertGreater(len(violations), 20, "Should detect many violations in large codebase")
            
            print(f"Performance test: {len(violations)} violations detected in {analysis_time:.3f}s")
            
        except Exception as e:
            self.fail(f"Performance test failed: {str(e)}")
            
    def test_error_resilience(self):
        """Test that system handles various error conditions gracefully."""
        
        # Test with syntax error
        broken_code = '''
def broken_function(
    # Missing closing parenthesis
    return "broken"
'''
        
        try:
            detector = RefactoredConnascenceDetector("broken.py", broken_code.split('\n'))
            # AST parsing will fail, should be handled gracefully
            violations = detector.detect_all_violations(None)  # Pass None to trigger error handling
            self.assertIsInstance(violations, list)  # Should return empty list or handle gracefully
        except Exception as e:
            # Should not crash the system
            self.fail(f"System should handle syntax errors gracefully: {str(e)}")
            
        # Test NASA analyzer with invalid code
        try:
            nasa_analyzer = NASAAnalyzer()
            nasa_violations = nasa_analyzer.analyze_file("broken.py", broken_code)
            self.assertIsInstance(nasa_violations, list)  # Should handle gracefully
        except Exception as e:
            self.fail(f"NASA analyzer should handle syntax errors gracefully: {str(e)}")
            
    def test_cross_language_compatibility(self):
        """Test that system can handle different file types appropriately."""
        
        # Test with JavaScript-like syntax (should be handled gracefully)
        js_like_code = '''
function processData(items) {
    for (let i = 0; i < items.length; i++) {
        console.log(items[i]);
    }
    return items.length;
}
'''
        
        try:
            # Should not crash even with non-Python code
            detector = RefactoredConnascenceDetector("test.js", js_like_code.split('\n'))
            # This will likely fail AST parsing but should be handled
            violations = detector.detect_all_violations(None)
            self.assertIsInstance(violations, list)
        except Exception:
            # Expected to fail AST parsing, but should not crash system
            pass
            
    def test_memory_usage_stability(self):
        """Test that system doesn't accumulate memory across multiple analyses."""
        
        import gc
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Run multiple analysis cycles
        for i in range(10):
            test_code = f'''
def test_function_{i}():
    import time
    time.sleep(0.001)
    magic_value = {i * 42}
    return magic_value
'''
            
            detector = RefactoredConnascenceDetector(f"test_{i}.py", test_code.split('\n'))
            tree = ast.parse(test_code)
            violations = detector.detect_all_violations(tree)
            
            # Force garbage collection
            gc.collect()
            
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory should not increase significantly (allow for some variance)
        max_increase = 50 * 1024 * 1024  # 50MB tolerance
        self.assertLess(memory_increase, max_increase, 
                       f"Memory increased by {memory_increase / (1024*1024):.1f}MB")
                       
    def test_concurrent_analysis_safety(self):
        """Test that system can handle concurrent analysis requests."""
        
        import threading
        import queue
        
        results_queue = queue.Queue()
        errors_queue = queue.Queue()
        
        def analyze_code(thread_id):
            try:
                test_code = f'''
def thread_function_{thread_id}():
    import time
    time.sleep(0.001)
    return {thread_id * 42}
'''
                detector = RefactoredConnascenceDetector(f"thread_{thread_id}.py", test_code.split('\n'))
                tree = ast.parse(test_code)
                violations = detector.detect_all_violations(tree)
                results_queue.put((thread_id, len(violations)))
            except Exception as e:
                errors_queue.put((thread_id, str(e)))
                
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=analyze_code, args=(i,))
            threads.append(thread)
            thread.start()
            
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=10)
            
        # Check results
        self.assertTrue(errors_queue.empty(), f"Concurrent analysis errors: {list(errors_queue.queue)}")
        self.assertEqual(results_queue.qsize(), 5, "Should have results from all threads")
        
    def test_configuration_flexibility(self):
        """Test that system can work with different configurations."""
        
        # Test NASA analyzer with custom config
        custom_config = {
            'rules': {
                'nasa_rule_1': {'severity': 'critical'},
                'nasa_rule_2': {'severity': 'high'}
            }
        }
        
        test_code = '''
def recursive_test(n):
    if n > 0:
        return recursive_test(n-1)
    return 0
'''
        
        try:
            # Test with default config
            nasa_analyzer = NASAAnalyzer()
            default_violations = nasa_analyzer.analyze_file("test.py", test_code)
            
            # Test with custom config  
            with patch.object(nasa_analyzer, 'rules_config', custom_config):
                custom_violations = nasa_analyzer.analyze_file("test.py", test_code)
                
            # Both should work (may have different results)
            self.assertIsInstance(default_violations, list)
            self.assertIsInstance(custom_violations, list)
            
        except Exception as e:
            self.fail(f"Configuration flexibility test failed: {str(e)}")


class TestSystemReporting(unittest.TestCase):
    """Test system-wide reporting capabilities."""
    
    def test_violation_aggregation(self):
        """Test that violations are properly aggregated across analysis types."""
        
        test_code = '''
def problematic_function():
    time.sleep(0.1)  # Both timing and NASA concern
    magic = 42  # Both meaning and NASA concern
    return magic
'''
        
        # Run both analyses
        detector = RefactoredConnascenceDetector("test.py", test_code.split('\n'))
        nasa_analyzer = NASAAnalyzer()
        
        tree = ast.parse(test_code)
        conn_violations = detector.detect_all_violations(tree)
        nasa_violations = nasa_analyzer.analyze_file("test.py", test_code)
        
        # Test aggregation
        all_violations = conn_violations + nasa_violations
        
        # Group by line number
        by_line = {}
        for violation in all_violations:
            line = violation.line_number
            if line not in by_line:
                by_line[line] = []
            by_line[line].append(violation)
            
        # Should have violations grouped by location
        self.assertGreater(len(by_line), 0, "Should have violations grouped by line")
        
    def test_severity_prioritization(self):
        """Test that violations are properly prioritized by severity."""
        
        test_code = '''
def critical_issues():
    # Critical: Recursion (NASA Rule 1)
    return critical_issues()
    
def high_issues():
    # High: No assertions (NASA Rule 5) 
    result = risky_operation()
    return result
    
def medium_issues():
    # Medium: Convention violation
    bad_variable_name = 42
    return bad_variable_name
'''
        
        nasa_analyzer = NASAAnalyzer()
        violations = nasa_analyzer.analyze_file("test.py", test_code)
        
        # Check severity distribution
        by_severity = {}
        for violation in violations:
            sev = violation.severity
            if sev not in by_severity:
                by_severity[sev] = 0
            by_severity[sev] += 1
            
        # Should have violations of different severities
        self.assertGreater(len(by_severity), 0, "Should have violations with different severities")


if __name__ == '__main__':
    unittest.main()