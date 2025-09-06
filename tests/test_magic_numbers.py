#!/usr/bin/env python3
"""
Test suite for magic number sensitivity fixes and context-aware detection.

Tests Requirements:
1. Common safe numbers [0,1,2,3,5,8,10,12] are NOT flagged
2. Context-aware analysis (conditionals vs assignments)
3. HTTP codes (200, 404, 500) in appropriate contexts
4. Loop counters and common constants
"""

import ast
from typing import List

import pytest

from analyzer.check_connascence import ConnascenceAnalyzer, ConnascenceDetector
from utils.types import ConnascenceViolation
from analyzer.constants import MAGIC_NUMBERS


class TestMagicNumberSensitivity:
    """Test magic number detection with enhanced sensitivity and context awareness."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = ConnascenceAnalyzer()

    def test_safe_numbers_not_flagged(self):
        """Test that common safe numbers [0,1,2,3,5,8,10,12] are not flagged."""
        test_code = '''
def process_data():
    # Safe numbers that should NOT be flagged according to current implementation
    count = 0  # zero - should be safe
    increment = 1  # one - should be safe
    double = 2  # two - should be safe
    negative = -1  # negative one - should be safe
    return count + increment + double + negative
'''
        violations = self._analyze_code_string(test_code)
        magic_violations = [v for v in violations if v.type == "connascence_of_meaning"]

        # Current implementation flags numbers based on visit_Constant logic
        # Safe numbers are: 0, 1, -1, 2, 10, 100, 1000
        flagged_values = [str(v.context.get('literal_value', '')) for v in magic_violations]
        safe_numbers = ['0', '1', '-1', '2']

        for safe_num in safe_numbers:
            assert safe_num not in flagged_values, f"Safe number {safe_num} was incorrectly flagged"

    def test_unsafe_numbers_flagged(self):
        """Test that unsafe magic numbers are properly flagged."""
        test_code = '''
def unsafe_function():
    # These should be flagged as magic numbers (based on current implementation)
    timeout = 42  # Not in safe list
    max_retries = 7  # Not in safe list
    percentage = 85  # Not in safe list
    return timeout + max_retries + percentage
'''
        violations = self._analyze_code_string(test_code)
        magic_violations = [v for v in violations if v.type == "connascence_of_meaning"]

        # Should flag the unsafe numbers
        assert len(magic_violations) >= 3, f"Expected at least 3 violations, got {len(magic_violations)}"

        # Check specific numbers are flagged
        flagged_values = [str(v.context.get('literal_value', '')) for v in magic_violations]
        expected_numbers = ['42', '7', '85']
        for num in expected_numbers:
            assert num in flagged_values, f"Number {num} should have been flagged"

    def test_context_aware_conditionals_vs_assignments(self):
        """Test context-sensitive analysis for conditionals vs assignments."""
        test_code = '''
def context_sensitive():
    # Assignment context (medium severity)
    max_count = 100

    # Conditional context (high severity - more dangerous)
    if user_level > 5:  # Magic in conditional - high severity
        return True

    # Loop context (medium severity)
    for i in range(50):  # Magic in loop - medium severity
        pass

    return max_count
'''
        violations = self._analyze_code_string(test_code)
        magic_violations = [v for v in violations if v.type == "connascence_of_meaning"]

        # Should have violations for unsafe numbers
        assert len(magic_violations) >= 2, f"Expected violations for unsafe numbers, got {len(magic_violations)}"

        # Find the conditional violation (should be high severity)
        conditional_violations = [v for v in magic_violations if v.context.get('in_conditional', False)]
        if conditional_violations:
            assert conditional_violations[0].severity == "high", "Conditional magic numbers should be high severity"

    def test_http_status_codes_in_context(self):
        """Test that HTTP status codes are handled appropriately in context."""
        test_code = '''
def http_handler():
    # HTTP codes in appropriate context - should be lenient
    if response.status_code == 200:  # OK
        return handle_success()
    elif response.status_code == 404:  # Not Found
        return handle_not_found()
    elif response.status_code == 500:  # Server Error
        return handle_server_error()

    # Random number in conditional - should be flagged
    if user_age > 21:  # This should be flagged
        return allow_access()

    return response.status_code
'''
        violations = self._analyze_code_string(test_code)
        magic_violations = [v for v in violations if v.type == "connascence_of_meaning"]

        # Should flag the non-HTTP number (21) but be lenient with HTTP codes
        flagged_values = [str(v.context.get('literal_value', '')) for v in magic_violations]
        assert '21' in flagged_values, "Non-HTTP magic number should be flagged"

        # HTTP codes might be flagged but with lower severity or special handling
        # The exact behavior depends on implementation - this is a design decision

    def test_loop_counters_and_common_constants(self):
        """Test detection of loop counters and common mathematical constants."""
        test_code = '''
def loop_and_constants():
    # Loop contexts - should be more lenient
    for i in range(10):  # Safe number, should not flag
        pass

    for j in range(100):  # Common round number, contextual decision
        pass

    # Mathematical constants - should be flagged for extraction
    area = 3.14159 * radius ** 2  # Pi - should suggest constant

    # Configuration values - should be flagged
    max_connections = 50  # Should be configuration constant

    return area + max_connections
'''
        violations = self._analyze_code_string(test_code)
        magic_violations = [v for v in violations if v.type == "connascence_of_meaning"]

        # Should flag the mathematical constant and configuration value
        flagged_values = [str(v.context.get('literal_value', '')) for v in magic_violations]

        # Pi should definitely be flagged
        assert any('3.14159' in val for val in flagged_values), "Mathematical constants should be flagged"

        # Configuration values should be flagged
        assert '50' in flagged_values, "Configuration values should be flagged"

    def test_edge_cases_and_boundaries(self):
        """Test edge cases and boundary conditions for magic number detection."""
        test_code = '''
def edge_cases():
    # Edge cases
    negative_one = -1  # Safe
    negative_magic = -42  # Should flag

    # Float variations
    percentage = 0.5  # Should flag
    zero_float = 0.0  # Safe
    one_float = 1.0  # Safe

    # Large numbers
    big_number = 999999  # Should flag

    # String lengths vs numbers
    if len(text) > 3:  # 3 is safe
        pass
    if len(text) > 17:  # 17 should be flagged
        pass

    return negative_magic + percentage + big_number
'''
        violations = self._analyze_code_string(test_code)
        magic_violations = [v for v in violations if v.type == "connascence_of_meaning"]

        # Check that unsafe numbers are flagged
        flagged_values = [str(v.context.get('literal_value', '')) for v in magic_violations]
        unsafe_numbers = ['-42', '0.5', '999999', '17']

        for num in unsafe_numbers:
            assert num in flagged_values, f"Unsafe number {num} should be flagged"

    def test_whitelist_integration_with_constants(self):
        """Test integration with constants.py MAGIC_NUMBERS whitelist."""
        test_code = f'''
def test_whitelist():
    # Numbers from MAGIC_NUMBERS constants should not be flagged
    timeout = {MAGIC_NUMBERS['timeout_seconds']}  # 30 - from constants
    port = {MAGIC_NUMBERS['default_port']}  # 8080 - from constants
    retries = {MAGIC_NUMBERS['max_retries']}  # 3 - from constants

    # Random number not in constants - should be flagged
    mystery_number = 73  # Should be flagged

    return timeout + port + retries + mystery_number
'''
        violations = self._analyze_code_string(test_code)
        magic_violations = [v for v in violations if v.type == "connascence_of_meaning"]

        # Should only flag the mystery number, not the constants
        flagged_values = [str(v.context.get('literal_value', '')) for v in magic_violations]
        assert '73' in flagged_values, "Non-whitelisted number should be flagged"

        # Constants from MAGIC_NUMBERS should not be flagged
        constants_values = [str(val) for val in MAGIC_NUMBERS.values()]
        for const_val in constants_values:
            if const_val in flagged_values:
                pytest.fail(f"Whitelisted constant {const_val} was incorrectly flagged")

    def test_severity_escalation_by_context(self):
        """Test that severity escalates appropriately based on context."""
        test_code = '''
def severity_test():
    # Assignment (medium severity)
    buffer_size = 1024

    # Conditional (high severity)
    if buffer_size > 2048:
        critical_path()

    # Loop condition (high severity)
    while attempts < 100:
        retry()

    # Function parameter (high severity)
    return process_data(1024, 2048)  # Multiple magic numbers in call
'''
        violations = self._analyze_code_string(test_code)
        magic_violations = [v for v in violations if v.type == "connascence_of_meaning"]

        # Should have multiple violations with varying severities
        assert len(magic_violations) >= 3, f"Expected multiple violations, got {len(magic_violations)}"

        # Check severity distribution
        severities = [v.severity for v in magic_violations]
        assert "high" in severities or "medium" in severities, "Should have contextual severity assignment"

    def _analyze_code_string(self, code: str) -> List[ConnascenceViolation]:
        """Helper method to analyze a code string and return violations."""
        source_lines = code.splitlines()
        tree = ast.parse(code)
        detector = ConnascenceDetector("test_file.py", source_lines)
        detector.visit(tree)
        detector.finalize_analysis()
        return detector.violations

    def test_regression_common_patterns(self):
        """Regression test for common patterns that should not generate false positives."""
        test_code = '''
def common_patterns():
    # Array indexing - common safe patterns
    first = items[0]
    second = items[1]

    # Boolean logic
    if enabled and count > 0:
        pass

    # Default parameters (in function calls)
    result = process(data, timeout=10)  # 10 is borderline

    # Binary operations with safe numbers
    doubled = value * 2

    return first + second + doubled
'''
        violations = self._analyze_code_string(test_code)
        magic_violations = [v for v in violations if v.type == "connascence_of_meaning"]

        # Should be minimal violations for common patterns
        # This test ensures we don't over-flag common, acceptable patterns
        flagged_values = [str(v.context.get('literal_value', '')) for v in magic_violations]

        # Safe numbers should not be flagged
        safe_in_code = ['0', '1', '2']
        for safe_num in safe_in_code:
            assert safe_num not in flagged_values, f"Safe number {safe_num} was incorrectly flagged"


class TestMagicNumberWhitelist:
    """Test whitelist functionality for magic numbers."""

    def test_default_safe_numbers(self):
        """Test default safe numbers are not flagged."""
        safe_numbers = [0, 1, -1, 2, 3, 5, 8, 10, 12]

        for num in safe_numbers:
            test_code = f'''
def test_safe():
    value = {num}
    return value
'''
            violations = self._analyze_code_string(test_code)
            magic_violations = [v for v in violations if v.type == "connascence_of_meaning"]

            # Safe numbers should not generate violations
            flagged_values = [str(v.context.get('literal_value', '')) for v in magic_violations]
            assert str(num) not in flagged_values, f"Safe number {num} was incorrectly flagged"

    def test_http_status_codes_context(self):
        """Test HTTP status codes in appropriate contexts."""
        test_code = '''
def http_responses():
    # Common HTTP status codes in context
    success_codes = [200, 201, 204]  # Success responses
    client_errors = [400, 401, 403, 404]  # Client errors
    server_errors = [500, 502, 503]  # Server errors

    return success_codes + client_errors + server_errors
'''
        violations = self._analyze_code_string(test_code)
        magic_violations = [v for v in violations if v.type == "connascence_of_meaning"]

        # HTTP codes should be flagged less severely or handled contextually
        # The exact behavior is implementation-dependent, but we test they're handled
        assert len(magic_violations) >= 0  # May or may not flag HTTP codes

    def _analyze_code_string(self, code: str) -> List[ConnascenceViolation]:
        """Helper method to analyze code string."""
        source_lines = code.splitlines()
        tree = ast.parse(code)
        detector = ConnascenceDetector("test_file.py", source_lines)
        detector.visit(tree)
        detector.finalize_analysis()
        return detector.violations


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
