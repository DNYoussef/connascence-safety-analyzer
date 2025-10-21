#!/usr/bin/env python3
"""
Sandbox Functionality Test for Phase 1 Utilities

Tests that ast_utils.py, violation_factory.py, and detector_result.py
actually work as expected with real AST nodes and data.
"""

import ast
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.utils.ast_utils import ASTUtils
from analyzer.utils.detector_result import AnalysisContext, DetectorResult
from analyzer.utils.violation_factory import ViolationFactory


def test_ast_utils():
    """Test ASTUtils functionality."""
    print("\n[TEST] ASTUtils Functionality")
    print("=" * 60)

    # Sample code with function
    code = """
def example_function(a, b, c, d, e):
    '''Function with 5 parameters'''
    return a + b + c + d + e
"""

    tree = ast.parse(code)

    # Test 1: find_nodes_by_type
    functions = ASTUtils.find_nodes_by_type(tree, ast.FunctionDef)
    assert len(functions) == 1, f"Expected 1 function, got {len(functions)}"
    print("[PASS] find_nodes_by_type() works")

    # Test 2: get_function_parameters
    func = functions[0]
    params = ASTUtils.get_function_parameters(func)
    assert params["positional_count"] == 5, f"Expected 5 params, got {params['positional_count']}"
    assert params["total_count"] == 5, f"Expected total 5, got {params['total_count']}"
    assert "a" in params["parameter_names"], "Expected 'a' in parameter names"
    print(f"[PASS] get_function_parameters() works: {params}")

    # Test 3: get_node_location
    location = ASTUtils.get_node_location(func, "test.py")
    assert location["file"] == "test.py", "Expected file='test.py'"
    assert location["line"] == 2, f"Expected line=2, got {location['line']}"
    print(f"[PASS] get_node_location() works: {location}")

    # Test 4: get_node_type_name
    type_name = ASTUtils.get_node_type_name(func)
    assert type_name == "FunctionDef", f"Expected 'FunctionDef', got '{type_name}'"
    print(f"[PASS] get_node_type_name() works: {type_name}")

    print("[PASS] All ASTUtils tests passed")
    return True


def test_violation_factory():
    """Test ViolationFactory functionality."""
    print("\n[TEST] ViolationFactory Functionality")
    print("=" * 60)

    # Test 1: create_violation (generic)
    location = {"file": "test.py", "line": 10, "column": 5}
    violation = ViolationFactory.create_violation(
        violation_type="CoP", severity="high", location=location, description="Test violation", recommendation="Fix it"
    )

    assert violation["type"] == "CoP", f"Expected type='CoP', got '{violation['type']}'"
    assert violation["severity"] == "high", "Expected severity='high'"
    assert violation["file_path"] == "test.py", "Expected file_path='test.py'"
    assert violation["line_number"] == 10, "Expected line_number=10"
    assert violation["description"] == "Test violation", "Expected description match"
    print(f"[PASS] create_violation() works: {violation['type']} at line {violation['line_number']}")

    # Test 2: create_cop_violation
    cop_violation = ViolationFactory.create_cop_violation(
        location=location, function_name="test_func", param_count=5, threshold=3
    )

    assert cop_violation["type"] == "CoP", "Expected CoP violation"
    assert cop_violation["severity"] == "medium", "Expected medium severity (5 params)"
    assert "test_func" in cop_violation["description"], "Expected function name in description"
    print(f"[PASS] create_cop_violation() works: {cop_violation['description']}")

    # Test 3: create_com_violation
    com_violation = ViolationFactory.create_com_violation(location=location, literal_value=42, literal_type="number")

    assert com_violation["type"] == "CoM", "Expected CoM violation"
    assert "42" in com_violation["description"], "Expected literal value in description"
    print(f"[PASS] create_com_violation() works: {com_violation['description']}")

    # Test 4: create_cot_violation
    cot_violation = ViolationFactory.create_cot_violation(
        location=location, element_name="my_function", missing_types="return type"
    )

    assert cot_violation["type"] == "CoT", "Expected CoT violation"
    assert "my_function" in cot_violation["description"], "Expected element name in description"
    print(f"[PASS] create_cot_violation() works: {cot_violation['description']}")

    print("[PASS] All ViolationFactory tests passed")
    return True


def test_detector_result():
    """Test DetectorResult functionality."""
    print("\n[TEST] DetectorResult Functionality")
    print("=" * 60)

    # Test 1: Create empty result
    result = DetectorResult(file_path="test.py")
    assert result.file_path == "test.py", "Expected file_path='test.py'"
    assert result.violation_count == 0, "Expected 0 violations initially"
    assert not result.has_errors, "Expected no errors initially"
    print(f"[PASS] DetectorResult creation works: {result.file_path}")

    # Test 2: Add violation
    violation = {"type": "CoP", "severity": "high", "description": "Test"}
    result.add_violation(violation)
    assert result.violation_count == 1, f"Expected 1 violation, got {result.violation_count}"
    print(f"[PASS] add_violation() works: {result.violation_count} violations")

    # Test 3: Add error
    result.add_error("Test error")
    assert result.has_errors, "Expected has_errors=True"
    assert len(result.errors) == 1, "Expected 1 error"
    print(f"[PASS] add_error() works: {result.errors[0]}")

    # Test 4: Add warning
    result.add_warning("Test warning")
    assert result.has_warnings, "Expected has_warnings=True"
    assert len(result.warnings) == 1, "Expected 1 warning"
    print(f"[PASS] add_warning() works: {result.warnings[0]}")

    # Test 5: to_dict()
    result_dict = result.to_dict()
    assert "file_path" in result_dict, "Expected 'file_path' in dict"
    assert "violation_count" in result_dict, "Expected 'violation_count' in dict"
    assert result_dict["violation_count"] == 1, "Expected violation_count=1 in dict"
    print(f"[PASS] to_dict() works: {result_dict.keys()}")

    print("[PASS] All DetectorResult tests passed")
    return True


def test_analysis_context():
    """Test AnalysisContext functionality."""
    print("\n[TEST] AnalysisContext Functionality")
    print("=" * 60)

    # Test 1: Create context
    source_lines = ["# Line 1", "def example():", "    return 42", "# Line 4"]
    context = AnalysisContext(file_path="test.py", source_lines=source_lines)

    assert context.file_path == "test.py", "Expected file_path='test.py'"
    assert context.line_count == 4, f"Expected 4 lines, got {context.line_count}"
    print(f"[PASS] AnalysisContext creation works: {context.line_count} lines")

    # Test 2: get_line (1-indexed)
    line2 = context.get_line(2)
    assert line2 == "def example():", f"Expected 'def example():', got '{line2}'"
    print(f"[PASS] get_line() works: line 2 = '{line2}'")

    # Test 3: get_lines (range)
    lines = context.get_lines(2, 3)
    assert len(lines) == 2, f"Expected 2 lines, got {len(lines)}"
    assert lines[0] == "def example():", "Expected first line to be 'def example():'"
    print(f"[PASS] get_lines() works: {len(lines)} lines returned")

    # Test 4: to_dict()
    context_dict = context.to_dict()
    assert "file_path" in context_dict, "Expected 'file_path' in dict"
    assert "line_count" in context_dict, "Expected 'line_count' in dict"
    assert context_dict["line_count"] == 4, "Expected line_count=4 in dict"
    print(f"[PASS] to_dict() works: {context_dict.keys()}")

    print("[PASS] All AnalysisContext tests passed")
    return True


def main():
    """Run all sandbox tests."""
    print("\n" + "=" * 60)
    print("PHASE 1 FUNCTIONALITY VALIDATION")
    print("=" * 60)

    tests = [
        ("ASTUtils", test_ast_utils),
        ("ViolationFactory", test_violation_factory),
        ("DetectorResult", test_detector_result),
        ("AnalysisContext", test_analysis_context),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"[FAIL] {test_name} test failed: {e}")
            import traceback

            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("[PASS] All Phase 1 utilities are functional")
        return 0
    else:
        print(f"[FAIL] {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
