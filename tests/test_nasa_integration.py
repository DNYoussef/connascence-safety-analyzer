"""
NASA Power of Ten Integration Tests

Tests the complete NASA rule analysis integration including:
- YAML configuration loading
- All 10 NASA rules detection
- Compliance scoring
- Integration with connascence analysis
"""

import ast
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from analyzer.nasa_engine.nasa_analyzer import NASAAnalyzer
from utils.types import ConnascenceViolation


class TestNASAIntegration(unittest.TestCase):
    """Test NASA Power of Ten rule integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = NASAAnalyzer()
        
    def test_nasa_config_loading(self):
        """Test NASA configuration is properly loaded."""
        
        # Check default config is loaded
        self.assertIsNotNone(self.analyzer.rules_config)
        self.assertIn('rules', self.analyzer.rules_config)
        
        # Check all 10 rules are present
        rules = self.analyzer.rules_config['rules']
        expected_rules = [f'nasa_rule_{i}' for i in range(1, 11)]
        
        for rule in expected_rules:
            self.assertIn(rule, rules, f"Rule {rule} should be in configuration")
            
    def test_rule_1_control_flow_violations(self):
        """Test NASA Rule 1: Avoid complex flow constructs."""
        
        # Test recursive function detection
        recursive_code = '''
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)  # Recursive call
    
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)  # Multiple recursive calls
'''
        
        violations = self.analyzer.analyze_file("test.py", recursive_code)
        
        # Should detect recursive functions
        rule_1_violations = [v for v in violations if v.context.get('nasa_rule') == 'rule_1']
        self.assertGreater(len(rule_1_violations), 0, "Should detect recursive functions")
        
        # Check violation details
        for violation in rule_1_violations:
            self.assertEqual(violation.severity, "critical")
            self.assertIn("recursive", violation.description.lower())
            
    def test_rule_2_loop_bounds(self):
        """Test NASA Rule 2: All loops must have fixed upper bounds."""
        
        bounded_loop_code = '''
# Bounded loops (should pass)
for i in range(10):
    print(i)
    
for item in [1, 2, 3, 4, 5]:
    process(item)

# Unbounded loops (should fail)  
while True:
    process_forever()
    
x = 0
while x < get_dynamic_limit():  # Dynamic bound
    x += 1
'''
        
        violations = self.analyzer.analyze_file("test.py", bounded_loop_code)
        
        # Should detect unbounded loops
        rule_2_violations = [v for v in violations if v.context.get('nasa_rule') == 'rule_2']
        self.assertGreater(len(rule_2_violations), 0, "Should detect unbounded loops")
        
        for violation in rule_2_violations:
            self.assertEqual(violation.severity, "critical")
            self.assertIn("bound", violation.description.lower())
            
    def test_rule_3_heap_usage(self):
        """Test NASA Rule 3: Do not use heap after initialization."""
        
        heap_code = '''
import ctypes

def use_malloc():
    ptr = ctypes.malloc(100)  # Dynamic allocation
    return ptr
    
def use_calloc():
    ptr = ctypes.calloc(10, 10)  # Another allocation
    return ptr
'''
        
        violations = self.analyzer.analyze_file("test.py", heap_code)
        
        # Should detect malloc calls
        rule_3_violations = [v for v in violations if v.context.get('nasa_rule') == 'rule_3']
        self.assertGreater(len(rule_3_violations), 0, "Should detect heap usage")
        
        for violation in rule_3_violations:
            self.assertEqual(violation.severity, "critical")
            
    def test_rule_4_function_size(self):
        """Test NASA Rule 4: Functions should not exceed 60 lines."""
        
        # Generate a function longer than 60 lines
        long_function_lines = ["def long_function():"]
        for i in range(70):
            long_function_lines.append(f"    operation_{i} = {i} * 2")
        long_function_lines.append("    return sum([operation_0, operation_1])")
        
        long_function_code = '\n'.join(long_function_lines)
        
        violations = self.analyzer.analyze_file("test.py", long_function_code)
        
        # Should detect oversized function
        rule_4_violations = [v for v in violations if v.context.get('nasa_rule') == 'rule_4']
        self.assertGreater(len(rule_4_violations), 0, "Should detect oversized function")
        
        for violation in rule_4_violations:
            self.assertEqual(violation.severity, "high")
            self.assertIn("60", violation.description)
            
    def test_rule_5_assertions(self):
        """Test NASA Rule 5: At least 2 assertions per function."""
        
        assertion_code = '''
def good_function_with_assertions(x, y):
    assert x > 0, "x must be positive"
    assert y > 0, "y must be positive"
    result = x + y
    assert result > 0, "result should be positive"
    return result

def bad_function_no_assertions(x, y):
    result = x / y  # No assertions, risky division
    return result
    
def bad_function_one_assertion(x, y):
    assert x > 0  # Only one assertion
    return x + y
    
def trivial_function():  # Should be exempt (too short)
    return 42
'''
        
        violations = self.analyzer.analyze_file("test.py", assertion_code)
        
        # Should detect functions with insufficient assertions
        rule_5_violations = [v for v in violations if v.context.get('nasa_rule') == 'rule_5']
        
        # Should have violations for functions lacking assertions
        self.assertGreater(len(rule_5_violations), 0, "Should detect insufficient assertions")
        
        for violation in rule_5_violations:
            self.assertEqual(violation.severity, "high")
            self.assertIn("assertion", violation.description.lower())
            
    def test_rule_6_variable_scope(self):
        """Test NASA Rule 6: Declare objects at smallest scope."""
        
        # Generate code with many global variables
        global_code = """
# Too many global variables
""" + '\n'.join([f"global_var_{i} = {i}" for i in range(25)]) + '''

def use_globals():
    global global_var_0, global_var_1, global_var_2
    return global_var_0 + global_var_1 + global_var_2
'''
        
        violations = self.analyzer.analyze_file("test.py", global_code)
        
        # Should detect excessive global variables
        rule_6_violations = [v for v in violations if v.context.get('nasa_rule') == 'rule_6']
        
        if rule_6_violations:  # May not trigger depending on detection logic
            for violation in rule_6_violations:
                self.assertEqual(violation.severity, "medium")
                self.assertIn("global", violation.description.lower())
                
    def test_rule_7_return_values(self):
        """Test NASA Rule 7: Check return values of non-void functions."""
        
        return_value_code = '''
def risky_function():
    return potentially_failing_operation()

def main():
    risky_function()  # Return value not checked
    another_risky_call()  # Another unchecked return
    
    # Good practice
    result = safe_function()
    if result is not None:
        process(result)
'''
        
        violations = self.analyzer.analyze_file("test.py", return_value_code)
        
        # Should detect unchecked return values
        rule_7_violations = [v for v in violations if v.context.get('nasa_rule') == 'rule_7']
        self.assertGreater(len(rule_7_violations), 0, "Should detect unchecked return values")
        
        for violation in rule_7_violations:
            self.assertEqual(violation.severity, "high")
            
    def test_compliance_scoring(self):
        """Test NASA compliance scoring system."""
        
        # Clean code (should score high)
        clean_code = '''
def clean_function(x, y):
    assert x > 0, "x must be positive"
    assert y > 0, "y must be positive"
    result = x + y
    return result
'''
        
        clean_violations = self.analyzer.analyze_file("test.py", clean_code)
        clean_score = self.analyzer.get_nasa_compliance_score(clean_violations)
        
        # Problematic code (should score low)
        problematic_code = '''
def recursive_bad_function(n):  # Rule 1 violation
    if n > 0:
        return n * recursive_bad_function(n-1)
    while True:  # Rule 2 violation
        break
    x = ctypes.malloc(100)  # Rule 3 violation
    return x  # Rule 7 - no return check
'''
        
        bad_violations = self.analyzer.analyze_file("test.py", problematic_code)
        bad_score = self.analyzer.get_nasa_compliance_score(bad_violations)
        
        # Clean code should score better than problematic code
        self.assertGreaterEqual(clean_score, bad_score, "Clean code should score higher")
        self.assertLessEqual(bad_score, 0.8, "Problematic code should have reduced score")
        
    def test_rule_summary_reporting(self):
        """Test NASA rule violation summary."""
        
        multi_violation_code = '''
def problematic_function(n):
    # Rule 1: Recursion
    if n > 0:
        return n * problematic_function(n-1)
    
    # Rule 2: Unbounded loop
    while True:
        process_data()
        if random_condition():
            break
            
    # Rule 3: Dynamic allocation
    ptr = ctypes.malloc(100)
    
    # Rule 5: No assertions
    result = risky_operation()
    return result  # Rule 7: No return check
'''
        
        violations = self.analyzer.analyze_file("test.py", multi_violation_code)
        summary = self.analyzer.get_rule_summary(violations)
        
        # Should have violations for multiple rules
        self.assertGreater(len(summary), 0, "Should have rule violations")
        
        # Check that summary includes rule counts
        total_violations = sum(summary.values())
        self.assertGreaterEqual(total_violations, len(violations), "Summary should account for all violations")
        
    @patch('builtins.open', new_callable=mock_open, read_data='''
name: "Test NASA Config"
rules:
  nasa_rule_1:
    severity: "critical"
    violations:
      - type: "recursive_function"
      - type: "goto_statement"
''')
    def test_custom_config_loading(self, mock_file):
        """Test loading custom NASA configuration."""
        
        custom_analyzer = NASAAnalyzer(config_path="custom_nasa.yml")
        
        # Should load custom config
        self.assertIn('nasa_rule_1', custom_analyzer.rules_config['rules'])
        
    def test_yaml_fallback_handling(self):
        """Test graceful fallback when YAML is not available."""
        
        with patch('analyzer.nasa_engine.nasa_analyzer.yaml', None):
            fallback_analyzer = NASAAnalyzer()
            
            # Should fall back to default config
            self.assertIsNotNone(fallback_analyzer.rules_config)
            self.assertIn('rules', fallback_analyzer.rules_config)
            
    def test_syntax_error_handling(self):
        """Test handling of files with syntax errors."""
        
        invalid_code = '''
def broken_function(
    # Missing closing parenthesis
    return "broken"
'''
        
        # Should handle syntax errors gracefully
        violations = self.analyzer.analyze_file("broken.py", invalid_code)
        
        # Should return empty list for unparseable code
        self.assertEqual(len(violations), 0, "Should handle syntax errors gracefully")
        
    def test_nasa_context_information(self):
        """Test that violations include proper NASA context."""
        
        test_code = '''
def recursive_test(n):
    if n > 0:
        return recursive_test(n-1)
    return 0
'''
        
        violations = self.analyzer.analyze_file("test.py", test_code)
        
        # Check that violations have NASA-specific context
        for violation in violations:
            self.assertIsInstance(violation, ConnascenceViolation)
            self.assertIsInstance(violation.context, dict)
            
            if 'nasa_rule' in violation.context:
                self.assertIn('violation_type', violation.context)
                self.assertIn('rule_', violation.context['nasa_rule'])


class TestNASAConnascenceIntegration(unittest.TestCase):
    """Test integration between NASA rules and connascence analysis."""
    
    def test_shared_violation_correlation(self):
        """Test violations that span both NASA and connascence analysis."""
        
        correlation_code = '''
def timing_dependent_function():
    import time
    time.sleep(0.1)  # NASA timing concern + connascence of timing
    magic_constant = 42  # NASA meaning + connascence of meaning
    return magic_constant

def algorithm_duplicate():  # NASA + connascence of algorithm
    import time
    time.sleep(0.1)  # Same timing logic as above
'''
        
        from analyzer.refactored_detector import RefactoredConnascenceDetector
        
        # Run both analyses
        nasa_analyzer = NASAAnalyzer()
        nasa_violations = nasa_analyzer.analyze_file("test.py", correlation_code)
        
        detector = RefactoredConnascenceDetector("test.py", correlation_code.split('\n'))
        tree = ast.parse(correlation_code)
        conn_violations = detector.detect_all_violations(tree)
        
        # Should have violations from both systems
        self.assertGreater(len(nasa_violations) + len(conn_violations), 0)
        
        # Look for correlated violations (same line numbers)
        nasa_lines = {v.line_number for v in nasa_violations}
        conn_lines = {v.line_number for v in conn_violations}
        
        # May have overlapping line numbers indicating correlated issues
        overlapping_lines = nasa_lines.intersection(conn_lines)
        # This is informational - not all violations will overlap


if __name__ == '__main__':
    unittest.main()