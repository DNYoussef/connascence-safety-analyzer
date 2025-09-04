"""
Comprehensive Failure Detection System for NASA Rules and MECE Analysis
Validates that all integrated rules can effectively detect known violations.
"""

import ast
import tempfile
import os
from typing import List, Dict, Any, Tuple
from pathlib import Path

from .ast_engine.connascence_ast_analyzer import ConnascenceASTAnalyzer
from .dup_detection.mece_analyzer import MECEAnalyzer
from .smart_integration_engine import SmartIntegrationEngine
from .ast_engine.violations import Violation


class FailureDetectionSystem:
    """System to validate that our analyzers can detect all expected violations."""
    
    def __init__(self):
        self.ast_analyzer = ConnascenceASTAnalyzer()
        self.mece_analyzer = MECEAnalyzer()
        self.integration_engine = SmartIntegrationEngine()
        
        # Test cases for each NASA rule
        self.nasa_test_cases = {
            "nasa_rule_1": self._create_recursion_test_cases(),
            "nasa_rule_2": self._create_dynamic_memory_test_cases(),
            "nasa_rule_3": self._create_heap_after_init_test_cases(),
            "nasa_rule_4": self._create_function_size_test_cases(),
            "nasa_rule_5": self._create_assertion_density_test_cases(),
            "nasa_rule_6": self._create_variable_scope_test_cases(),
            "nasa_rule_7": self._create_preprocessor_test_cases(),
            "nasa_rule_8": self._create_function_pointer_test_cases(),
            "nasa_rule_9": self._create_pointer_restriction_test_cases(),
            "nasa_rule_10": self._create_compiler_warning_test_cases()
        }
        
        # Test cases for MECE analysis
        self.mece_test_cases = self._create_mece_test_cases()
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run complete validation of all failure detection capabilities."""
        results = {
            "nasa_rules": {},
            "mece_analysis": {},
            "integration_tests": {},
            "summary": {}
        }
        
        # Test NASA rules
        nasa_results = self._test_nasa_rules()
        results["nasa_rules"] = nasa_results
        
        # Test MECE analysis
        mece_results = self._test_mece_analysis()
        results["mece_analysis"] = mece_results
        
        # Test integration
        integration_results = self._test_integration()
        results["integration_tests"] = integration_results
        
        # Generate summary
        results["summary"] = self._generate_summary(nasa_results, mece_results, integration_results)
        
        return results
    
    def _test_nasa_rules(self) -> Dict[str, Any]:
        """Test all NASA Power of Ten rules for violation detection."""
        results = {}
        
        for rule_name, test_cases in self.nasa_test_cases.items():
            rule_results = {
                "total_tests": len(test_cases),
                "detected": 0,
                "missed": 0,
                "false_positives": 0,
                "test_details": []
            }
            
            for i, (code, expected_violations) in enumerate(test_cases):
                violations = self._analyze_code(code)
                
                # Filter violations for this specific NASA rule
                nasa_violations = [v for v in violations if self._is_nasa_rule_violation(v, rule_name)]
                
                detected_count = len(nasa_violations)
                expected_count = expected_violations
                
                if detected_count >= expected_count:
                    rule_results["detected"] += 1
                    status = "PASS"
                else:
                    rule_results["missed"] += 1
                    status = "FAIL"
                
                rule_results["test_details"].append({
                    "test_case": i + 1,
                    "status": status,
                    "expected_violations": expected_count,
                    "detected_violations": detected_count,
                    "violations": [self._violation_to_dict(v) for v in nasa_violations]
                })
            
            results[rule_name] = rule_results
        
        return results
    
    def _test_mece_analysis(self) -> Dict[str, Any]:
        """Test MECE analysis for detecting code duplication."""
        results = {
            "total_tests": len(self.mece_test_cases),
            "detected": 0,
            "missed": 0,
            "test_details": []
        }
        
        for i, (code, expected_duplications) in enumerate(self.mece_test_cases):
            violations = self._analyze_code_with_mece(code)
            
            detected_count = len(violations)
            expected_count = expected_duplications
            
            if detected_count >= expected_count:
                results["detected"] += 1
                status = "PASS"
            else:
                results["missed"] += 1
                status = "FAIL"
            
            results["test_details"].append({
                "test_case": i + 1,
                "status": status,
                "expected_duplications": expected_count,
                "detected_duplications": detected_count,
                "duplications": [self._violation_to_dict(v) for v in violations]
            })
        
        return results
    
    def _test_integration(self) -> Dict[str, Any]:
        """Test smart integration engine."""
        results = {
            "correlation_tests": 0,
            "severity_enhancement_tests": 0,
            "context_generation_tests": 0,
            "total_passed": 0
        }
        
        # Test correlation between different analyzers
        complex_code = '''
def process_data():
    data = []  # NASA Rule 2/3: Dynamic allocation
    for i in range(1000000):  # NASA Rule 2: Unbounded loop
        result = calculate(data.items.values.keys)  # NASA Rule 9: Deep access
        data.append(result)  # Multiple violations
    return data

def process_data_duplicate():  # MECE: Duplicate function
    items = []
    for j in range(1000000):
        res = calculate(items.items.values.keys)
        items.append(res)
    return items
'''
        
        violations = self._analyze_code(complex_code)
        mece_violations = self._analyze_code_with_mece(complex_code)
        
        # Test if integration engine can correlate violations
        integrated_results = self.integration_engine.analyze_with_correlation(
            violations + mece_violations,
            complex_code
        )
        
        if integrated_results:
            results["correlation_tests"] = 1
            results["total_passed"] += 1
        
        return results
    
    def _create_recursion_test_cases(self) -> List[Tuple[str, int]]:
        """Create test cases for NASA Rule 1: No Recursion."""
        return [
            # Direct recursion
            ('''
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
''', 2),  # Two recursive calls
            
            # Indirect recursion
            ('''
def function_a(x):
    if x > 0:
        return function_b(x - 1)
    return 0

def function_b(x):
    if x > 0:
        return function_a(x - 1)
    return 1
''', 2),  # Two functions in cycle
            
            # No recursion (should not detect)
            ('''
def iterative_fibonacci(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for i in range(2, n + 1):
        a, b = b, a + b
    return b
''', 0)
        ]
    
    def _create_dynamic_memory_test_cases(self) -> List[Tuple[str, int]]:
        """Create test cases for NASA Rule 2: Fixed loop bounds."""
        return [
            # Unbounded loop with dynamic allocation
            ('''
def process_data():
    results = []  # Dynamic allocation
    data = {}     # Dynamic allocation
    while True:   # Unbounded loop
        item = get_next_item()
        if not item:
            break
        results.append(item)
    return results
''', 3),  # 2 allocations + unbounded loop
            
            # List comprehension
            ('''
def filter_data(items):
    return [x for x in items if condition(x)]
''', 1),  # Dynamic list comprehension
            
            # Pre-sized allocation (better)
            ('''
def initialize_data():
    MAX_SIZE = 1000
    results = [None] * MAX_SIZE  # Pre-sized
    return results
''', 0)  # Should not detect (pre-sized)
        ]
    
    def _create_heap_after_init_test_cases(self) -> List[Tuple[str, int]]:
        """Create test cases for NASA Rule 3: No heap after init."""
        return [
            # Heap allocation in runtime function
            ('''
def __init__(self):
    self.data = []  # OK in init

def process_request(self):
    temp_data = []  # NASA Rule 3 violation
    results = {}    # NASA Rule 3 violation
    return process(temp_data, results)
''', 2),  # 2 allocations in runtime
            
            # Allocation in init (OK)
            ('''
def initialize_system():
    global_data = []
    config = {}
    return setup(global_data, config)
''', 0)  # Should not detect (init function)
        ]
    
    def _create_function_size_test_cases(self) -> List[Tuple[str, int]]:
        """Create test cases for NASA Rule 4: Function size limit."""
        return [
            # Large function (>60 lines)
            (self._generate_large_function(80), 1),
            
            # Normal function
            ('''
def small_function():
    x = 1
    y = 2
    return x + y
''', 0)
        ]
    
    def _create_assertion_density_test_cases(self) -> List[Tuple[str, int]]:
        """Create test cases for NASA Rule 5: Assertion density."""
        return [
            # Function with no assertions
            ('''
def process_data(data, size):
    if size > 0:
        result = []
        for i in range(size):
            item = data[i]
            processed = transform(item)
            result.append(processed)
        return result
    return None
''', 1),  # Should detect low assertion density
            
            # Function with adequate assertions
            ('''
def safe_process_data(data, size):
    assert data is not None, "Data cannot be None"
    assert size >= 0, "Size must be non-negative"
    assert len(data) >= size, "Data too small"
    
    result = []
    for i in range(size):
        item = data[i]
        assert item is not None, "Item cannot be None"
        processed = transform(item)
        result.append(processed)
    
    assert len(result) == size, "Result size mismatch"
    return result
''', 0)  # Should not detect (good assertion density)
        ]
    
    def _create_variable_scope_test_cases(self) -> List[Tuple[str, int]]:
        """Create test cases for NASA Rule 6: Variable scope."""
        return [
            # Too many global variables
            (f'''
{"".join([f"global_var_{i} = {i}\n" for i in range(15)])}

def use_globals():
    return global_var_0 + global_var_1
''', 1),  # Too many globals
            
            # Class attribute used in only one method
            ('''
class DataProcessor:
    def __init__(self):
        self.temp_data = []  # Used only in one method
        
    def process(self):
        self.temp_data.append(1)
        return len(self.temp_data)
    
    def other_method(self):
        return "done"
''', 1)  # Scope can be reduced
        ]
    
    def _create_preprocessor_test_cases(self) -> List[Tuple[str, int]]:
        """Create test cases for NASA Rule 7: Preprocessor restrictions."""
        return [
            # eval/exec usage
            ('''
def dynamic_execution(code_str):
    result = eval(code_str)
    exec("import sys")
    return result
''', 2),  # eval + exec
            
            # Normal code
            ('''
def normal_function():
    return "no dynamic execution"
''', 0)
        ]
    
    def _create_function_pointer_test_cases(self) -> List[Tuple[str, int]]:
        """Create test cases for NASA Rule 8: Function pointer restrictions."""
        return [
            # Dynamic function calls
            ('''
def call_dynamic(obj, method_name):
    method = getattr(obj, method_name)
    return method()

def import_dynamic(module_name):
    module = __import__(module_name)
    return module
''', 2),  # getattr + __import__
            
            # Static calls
            ('''
def static_call(obj):
    return obj.known_method()
''', 0)
        ]
    
    def _create_pointer_restriction_test_cases(self) -> List[Tuple[str, int]]:
        """Create test cases for NASA Rule 9: Pointer restrictions."""
        return [
            # Deep attribute access
            ('''
def deep_access(obj):
    value = obj.data.items.metadata.info.value  # 5 levels deep
    return obj.config.settings.display.color    # 4 levels deep
''', 2),  # Two deep access chains
            
            # Complex subscripts
            ('''
def complex_indexing(data):
    return data[i * 2 + 1][j - offset]  # Complex subscript
''', 1),
            
            # Simple access
            ('''
def simple_access(obj):
    return obj.value  # Only 1 level
''', 0)
        ]
    
    def _create_compiler_warning_test_cases(self) -> List[Tuple[str, int]]:
        """Create test cases for NASA Rule 10: Compiler warnings."""
        return [
            # Code that would generate warnings
            ('''
def problematic_function():
    unused_var = 42
    
    if True:
        return "unreachable code follows"
        print("this is unreachable")
    
    def missing_return_annotation():
        pass  # No return annotation
''', 3),  # Multiple warning indicators
            
            # Clean code
            ('''
def clean_function(param: int) -> str:
    result = str(param)
    return result
''', 0)
        ]
    
    def _create_mece_test_cases(self) -> List[Tuple[str, int]]:
        """Create test cases for MECE analysis."""
        return [
            # Duplicate functions
            ('''
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total

def add_numbers(values):  # Duplicate functionality
    result = 0
    for val in values:
        result += val
    return result

def compute_total(data):  # Another duplicate
    sum_val = 0
    for item in data:
        sum_val += item
    return sum_val
''', 2),  # 2 duplicate pairs
            
            # Overlapping classes
            ('''
class UserManager:
    def create_user(self, name):
        return {"name": name}
    
    def delete_user(self, user_id):
        pass

class PersonHandler:  # Overlapping functionality
    def create_person(self, name):
        return {"name": name}
    
    def remove_person(self, person_id):
        pass
''', 1),  # 1 overlapping class pair
            
            # Unique functions
            ('''
def unique_function_one():
    return "one"

def unique_function_two():
    return "two"
''', 0)
        ]
    
    def _generate_large_function(self, line_count: int) -> str:
        """Generate a function with specified line count."""
        lines = ["def large_function():"]
        for i in range(line_count - 2):
            lines.append(f"    var_{i} = {i}")
        lines.append("    return var_0")
        return "\n".join(lines)
    
    def _analyze_code(self, code: str) -> List[Violation]:
        """Analyze code using AST analyzer."""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                f.flush()
                
                violations = self.ast_analyzer.analyze_file(f.name)
                
                # Clean up
                os.unlink(f.name)
                
                return violations
        except Exception as e:
            print(f"Error analyzing code: {e}")
            return []
    
    def _analyze_code_with_mece(self, code: str) -> List[Violation]:
        """Analyze code using MECE analyzer."""
        try:
            tree = ast.parse(code)
            violations = self.mece_analyzer.analyze_mece_violations(tree)
            return violations
        except Exception as e:
            print(f"Error in MECE analysis: {e}")
            return []
    
    def _is_nasa_rule_violation(self, violation: Violation, rule_name: str) -> bool:
        """Check if violation matches specific NASA rule."""
        if not hasattr(violation, 'context') or not violation.context:
            return False
        
        nasa_rule_key = violation.context.get('nasa_rule', '')
        rule_mapping = {
            "nasa_rule_1": "Rule_1",
            "nasa_rule_2": "Rule_2", 
            "nasa_rule_3": "Rule_3",
            "nasa_rule_4": "Rule_4",
            "nasa_rule_5": "Rule_5",
            "nasa_rule_6": "Rule_6",
            "nasa_rule_7": "Rule_7",
            "nasa_rule_8": "Rule_8",
            "nasa_rule_9": "Rule_9",
            "nasa_rule_10": "Rule_10"
        }
        
        expected_rule_prefix = rule_mapping.get(rule_name, '')
        return nasa_rule_key.startswith(expected_rule_prefix)
    
    def _violation_to_dict(self, violation: Violation) -> Dict[str, Any]:
        """Convert violation to dictionary for reporting."""
        return {
            "type": violation.type.name if hasattr(violation.type, 'name') else str(violation.type),
            "severity": violation.severity.name if hasattr(violation.severity, 'name') else str(violation.severity),
            "description": violation.description,
            "line": violation.line_number,
            "context": getattr(violation, 'context', {})
        }
    
    def _generate_summary(self, nasa_results: Dict, mece_results: Dict, integration_results: Dict) -> Dict[str, Any]:
        """Generate comprehensive summary of validation results."""
        total_nasa_tests = sum(r["total_tests"] for r in nasa_results.values())
        total_nasa_passed = sum(r["detected"] for r in nasa_results.values())
        
        nasa_success_rate = (total_nasa_passed / total_nasa_tests * 100) if total_nasa_tests > 0 else 0
        mece_success_rate = (mece_results["detected"] / mece_results["total_tests"] * 100) if mece_results["total_tests"] > 0 else 0
        
        return {
            "overall_status": "PASS" if nasa_success_rate >= 90 and mece_success_rate >= 90 else "NEEDS_IMPROVEMENT",
            "nasa_rules": {
                "total_tests": total_nasa_tests,
                "passed": total_nasa_passed,
                "success_rate": f"{nasa_success_rate:.1f}%",
                "rules_with_issues": [rule for rule, results in nasa_results.items() if results["missed"] > 0]
            },
            "mece_analysis": {
                "total_tests": mece_results["total_tests"],
                "passed": mece_results["detected"],
                "success_rate": f"{mece_success_rate:.1f}%"
            },
            "integration": {
                "correlation_working": integration_results["correlation_tests"] > 0,
                "total_integration_tests": sum(integration_results.values())
            },
            "recommendations": self._generate_recommendations(nasa_results, mece_results)
        }
    
    def _generate_recommendations(self, nasa_results: Dict, mece_results: Dict) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        for rule, results in nasa_results.items():
            if results["missed"] > 0:
                recommendations.append(f"Improve {rule} detection - missed {results['missed']} out of {results['total_tests']} tests")
        
        if mece_results["missed"] > 0:
            recommendations.append(f"Enhance MECE analysis - missed {mece_results['missed']} duplications")
        
        if not recommendations:
            recommendations.append("All systems functioning well - consider adding more edge case tests")
        
        return recommendations


def main():
    """Run failure detection system validation."""
    detector = FailureDetectionSystem()
    results = detector.run_comprehensive_validation()
    
    print("=" * 80)
    print("COMPREHENSIVE FAILURE DETECTION VALIDATION REPORT")
    print("=" * 80)
    
    print(f"Overall Status: {results['summary']['overall_status']}")
    print(f"NASA Rules Success Rate: {results['summary']['nasa_rules']['success_rate']}")
    print(f"MECE Analysis Success Rate: {results['summary']['mece_analysis']['success_rate']}")
    
    print("\nDETAILED RESULTS:")
    print("-" * 40)
    
    for rule, rule_results in results["nasa_rules"].items():
        status = "✅" if rule_results["missed"] == 0 else "❌"
        print(f"{status} {rule}: {rule_results['detected']}/{rule_results['total_tests']} passed")
    
    mece_results = results["mece_analysis"]
    mece_status = "✅" if mece_results["missed"] == 0 else "❌"
    print(f"{mece_status} MECE Analysis: {mece_results['detected']}/{mece_results['total_tests']} passed")
    
    print("\nRECOMMENDATIONS:")
    for rec in results['summary']['recommendations']:
        print(f"• {rec}")
    
    return results


if __name__ == "__main__":
    main()