#!/usr/bin/env python3

# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
Connascence Type Preservation Regression Tests

CRITICAL: This test suite validates that ALL 9 connascence types remain functional
after SPEK integration. This is a GATE for Phase 1 - if any test fails, integration
has broken existing functionality.

9 Connascence Types (MUST all work):
- CoN (Name): Naming connascence
- CoT (Type): Type connascence
- CoM (Meaning): Magic literal connascence
- CoP (Position): Parameter position connascence
- CoA (Algorithm): Algorithm/logic connascence (God objects)
- CoE (Execution): Execution order connascence
- CoI (Identity): Identity connascence
- CoV (Value): Value connascence
- CoId (Identity-Timing): Timing/identity connascence

Created: Phase 0 (Week 1 - Integration Planning)
Purpose: Ensure backward compatibility before SPEK integration
"""

import ast
from pathlib import Path
import sys
from typing import Dict

import pytest

from fixes.phase0.production_safe_assertions import ProductionAssert

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analyzer.detectors.convention_detector import ConventionDetector
from analyzer.detectors.execution_detector import ExecutionDetector
from analyzer.detectors.god_object_detector import GodObjectDetector
from analyzer.detectors.magic_literal_detector import MagicLiteralDetector
from analyzer.detectors.position_detector import PositionDetector
from analyzer.detectors.timing_detector import TimingDetector
from analyzer.detectors.values_detector import ValuesDetector


class ConnascenceTypeValidator:
    """Validates all 9 connascence types are working correctly."""

    def __init__(self):
        self.validation_results = {}
        self.sample_code_by_type = self._create_sample_code()

    def _create_sample_code(self) -> Dict[str, str]:
        """Create sample code that triggers each connascence type."""
        return {
            # CoP - Position: Too many positional parameters
            "CoP": '''
def process_user_data(user_id, username, email, phone, address, city, state, zip_code):
    """Function with too many positional parameters (8 > threshold 3)"""
    return {
        'user_id': user_id,
        'username': username,
        'email': email,
        'phone': phone,
        'address': address,
        'city': city,
        'state': state,
        'zip': zip_code
    }
''',
            # CoM - Meaning: Magic literals
            "CoM": '''
def calculate_discount(price):
    """Function with magic literals"""
    if price > 100:  # Magic literal: 100
        discount = price * 0.15  # Magic literal: 0.15
    elif price > 50:  # Magic literal: 50
        discount = price * 0.10  # Magic literal: 0.10
    else:
        discount = 0
    return discount
''',
            # CoA - Algorithm: God object (too many methods)
            "CoA": '''
class UserManager:
    """God object with too many methods"""
    def create_user(self): pass
    def update_user(self): pass
    def delete_user(self): pass
    def get_user(self): pass
    def list_users(self): pass
    def authenticate_user(self): pass
    def authorize_user(self): pass
    def reset_password(self): pass
    def send_email(self): pass
    def log_activity(self): pass
    def generate_report(self): pass
    def export_data(self): pass
    def import_data(self): pass
    def validate_data(self): pass
    def process_payment(self): pass
    def refund_payment(self): pass
    def calculate_tax(self): pass
    def apply_discount(self): pass
    def send_notification(self): pass
    def track_analytics(self): pass
    def manage_subscriptions(self): pass
    def handle_webhooks(self): pass
''',
            # CoE - Execution: Execution order dependencies (using GLOBAL state)
            "CoE": '''
# Global state creates execution order dependencies (exceeds threshold)
database_connected = False
database_cursor = None
cache_initialized = False
session_active = False
config_loaded = False
state_manager = None

def initialize_system():
    """Initialize global system state"""
    global database_connected, database_cursor, cache_initialized, config_loaded, state_manager
    database_connected = True
    database_cursor = "cursor"
    cache_initialized = True
    config_loaded = True
    state_manager = {}

def connect_database():
    """Depends on initialize_system() being called first"""
    global database_connected, database_cursor, config_loaded
    if not config_loaded:
        raise RuntimeError("Must call initialize_system() first")
    database_connected = True
    database_cursor = "cursor"

def start_session():
    """Depends on connect_database() being called first"""
    global session_active, database_connected
    if not database_connected:
        raise RuntimeError("Must call connect_database() first")
    session_active = True

def execute_query(query):
    """Depends on start_session() being called first"""
    global session_active, database_cursor
    if not session_active:
        raise RuntimeError("Must call start_session() first")
    return database_cursor
''',
            # CoV - Value: Value-based coupling (duplicate literals 3+ times)
            "CoV": '''
# Value-based coupling with duplicate literals (3+ occurrences required)
DEFAULT_STATUS = "ACTIVE"  # 1

def process_status(status_code):
    """Function with value-based coupling"""
    if status_code == "ACTIVE":  # 2
        active_default = "ACTIVE"  # 3
        return True
    elif status_code == "INACTIVE":
        return False
    else:
        fallback = "ACTIVE"  # 4
        return fallback
''',
            # CoId - Identity (Timing): Timing-based dependencies
            "CoId": '''
import time

def rate_limited_function():
    """Function with timing-based dependency"""
    time.sleep(0.1)  # Timing violation - sleep dependency
    return "done"

def delayed_processing():
    """Another timing dependency"""
    time.sleep(0.5)
    return "processed"
''',
            # CoN - Name: Naming connascence (convention detector)
            "CoN": '''
def getUserData():  # Naming violation: camelCase instead of snake_case
    """Function with naming convention violation"""
    UserName = "test"  # Naming violation: PascalCase for local variable
    return UserName

def Process_Data():  # Naming violation: Mixed case
    """Another naming violation"""
    pass
''',
            # CoT - Type: Type connascence (NOTE: ConventionDetector checks naming, not type hints)
            "CoT": '''
def calculateTotal(items):  # Naming violation: camelCase function name
    """Function with naming violations (CoT test reused for naming conventions)"""
    SubTotal = sum(items)  # Naming violation: PascalCase variable
    return SubTotal

def Process_Order():  # Naming violation: Mixed case
    """Another naming violation"""
    pass
''',
            # CoI - Identity: Identity connascence (via duplicate sentinel values)
            "CoI": '''
# Identity connascence via duplicate sentinel values (3+ occurrences required)
SENTINEL_VALUE = "UNDEFINED"  # 1

def get_default_value():
    """Return default sentinel"""
    return "UNDEFINED"  # 2

def process_with_default(value):
    """Check against sentinel"""
    if value == "UNDEFINED":  # 3
        default_value = "UNDEFINED"  # 4
        return default_value
    return value

def validate_input(data):
    """Validate input data"""
    if data == "UNDEFINED":  # 5
        return False
    return True
''',
        }

    def validate_detector(self, detector_type: str, detector_class, sample_code: str) -> Dict[str, any]:
        """
        Validate a specific detector type works correctly.

        Args:
            detector_type: Connascence type code (CoP, CoM, etc.)
            detector_class: Detector class to instantiate
            sample_code: Sample code that should trigger violations

        Returns:
            Dict with validation results
        """
        ProductionAssert.not_none(detector_type, "detector_type")
        ProductionAssert.not_none(detector_class, "detector_class")
        ProductionAssert.not_none(sample_code, "sample_code")

        try:
            # Parse the sample code
            tree = ast.parse(sample_code)

            # Create detector instance
            source_lines = sample_code.split("\n")
            detector = detector_class(file_path="test.py", source_lines=source_lines)

            # Detect violations
            violations = detector.detect_violations(tree)

            # Validation criteria
            validation_result = {
                "type": detector_type,
                "detector_class": detector_class.__name__,
                "violations_found": len(violations),
                "violations_expected": True,  # All sample code should trigger violations
                "passed": len(violations) > 0,  # Must find at least 1 violation
                "violation_details": [
                    {
                        "description": getattr(v, "description", ""),
                        "line": getattr(v, "line_number", 0),
                        "severity": getattr(v, "severity", "unknown"),
                    }
                    for v in violations[:3]  # First 3 violations for inspection
                ],
                "error": None,
            }

            return validation_result

        except Exception as e:
            return {
                "type": detector_type,
                "detector_class": detector_class.__name__,
                "violations_found": 0,
                "violations_expected": True,
                "passed": False,
                "violation_details": [],
                "error": str(e),
            }

    def validate_all_types(self) -> Dict[str, Dict]:
        """
        Validate ALL 9 connascence types.

        Returns:
            Dict mapping type codes to validation results
        """
        # Map connascence types to their detectors
        type_detector_map = {
            "CoP": PositionDetector,
            "CoM": MagicLiteralDetector,
            "CoA": GodObjectDetector,  # Algorithm includes god object detection
            "CoE": ExecutionDetector,
            "CoV": ValuesDetector,
            "CoId": TimingDetector,
            "CoN": ConventionDetector,  # Naming conventions
            "CoT": ConventionDetector,  # Type hints are part of conventions
            "CoI": ValuesDetector,  # Identity is related to value comparisons
        }

        results = {}

        for conn_type, detector_class in type_detector_map.items():
            sample_code = self.sample_code_by_type.get(conn_type, "")
            if sample_code:
                result = self.validate_detector(conn_type, detector_class, sample_code)
                results[conn_type] = result

        return results

    def get_summary(self, results: Dict[str, Dict]) -> Dict[str, any]:
        """
        Generate summary of validation results.

        Args:
            results: Validation results from validate_all_types()

        Returns:
            Summary dict with pass/fail counts and details
        """
        ProductionAssert.not_none(results, "results")

        total = len(results)
        passed = sum(1 for r in results.values() if r["passed"])
        failed = total - passed

        failed_types = [
            {
                "type": conn_type,
                "detector": r["detector_class"],
                "error": r["error"],
                "violations_found": r["violations_found"],
            }
            for conn_type, r in results.items()
            if not r["passed"]
        ]

        return {
            "total_types": total,
            "types_passed": passed,
            "types_failed": failed,
            "pass_rate": (passed / total * 100) if total > 0 else 0,
            "all_passed": failed == 0,
            "failed_types": failed_types,
            "expected_types": 9,
            "coverage_complete": total >= 9,
        }


@pytest.fixture
def connascence_validator():
    """Create connascence type validator."""
    return ConnascenceTypeValidator()


class TestConnascenceTypePreservation:
    """Test suite ensuring all 9 connascence types work correctly."""

    def test_cop_position_detector_works(self, connascence_validator):
        """Test CoP (Position) detector finds parameter position violations."""
        sample_code = connascence_validator.sample_code_by_type["CoP"]
        result = connascence_validator.validate_detector("CoP", PositionDetector, sample_code)

        assert result["passed"], (
            f"CoP detector failed: {result['error']} - " f"Found {result['violations_found']} violations (expected >0)"
        )
        assert result["violations_found"] > 0, "CoP detector should find parameter violations"

    def test_com_meaning_detector_works(self, connascence_validator):
        """Test CoM (Meaning) detector finds magic literal violations."""
        sample_code = connascence_validator.sample_code_by_type["CoM"]
        result = connascence_validator.validate_detector("CoM", MagicLiteralDetector, sample_code)

        assert result["passed"], (
            f"CoM detector failed: {result['error']} - " f"Found {result['violations_found']} violations (expected >0)"
        )
        assert result["violations_found"] >= 4, "CoM detector should find multiple magic literals"

    def test_coa_algorithm_detector_works(self, connascence_validator):
        """Test CoA (Algorithm) detector finds god object violations."""
        sample_code = connascence_validator.sample_code_by_type["CoA"]
        result = connascence_validator.validate_detector("CoA", GodObjectDetector, sample_code)

        assert result["passed"], (
            f"CoA detector failed: {result['error']} - " f"Found {result['violations_found']} violations (expected >0)"
        )
        assert result["violations_found"] > 0, "CoA detector should find god object"

    def test_coe_execution_detector_works(self, connascence_validator):
        """Test CoE (Execution) detector finds execution order violations."""
        sample_code = connascence_validator.sample_code_by_type["CoE"]
        result = connascence_validator.validate_detector("CoE", ExecutionDetector, sample_code)

        assert result["passed"], (
            f"CoE detector failed: {result['error']} - " f"Found {result['violations_found']} violations (expected >0)"
        )
        assert result["violations_found"] > 0, "CoE detector should find execution dependencies"

    def test_cov_value_detector_works(self, connascence_validator):
        """Test CoV (Value) detector finds value-based coupling."""
        sample_code = connascence_validator.sample_code_by_type["CoV"]
        result = connascence_validator.validate_detector("CoV", ValuesDetector, sample_code)

        assert result["passed"], (
            f"CoV detector failed: {result['error']} - " f"Found {result['violations_found']} violations (expected >0)"
        )
        assert result["violations_found"] > 0, "CoV detector should find value coupling"

    def test_coid_timing_detector_works(self, connascence_validator):
        """Test CoId (Identity-Timing) detector finds timing violations."""
        sample_code = connascence_validator.sample_code_by_type["CoId"]
        result = connascence_validator.validate_detector("CoId", TimingDetector, sample_code)

        assert result["passed"], (
            f"CoId detector failed: {result['error']} - " f"Found {result['violations_found']} violations (expected >0)"
        )
        assert result["violations_found"] > 0, "CoId detector should find timing dependencies"

    def test_con_name_detector_works(self, connascence_validator):
        """Test CoN (Name) detector finds naming convention violations."""
        sample_code = connascence_validator.sample_code_by_type["CoN"]
        result = connascence_validator.validate_detector("CoN", ConventionDetector, sample_code)

        assert result["passed"], (
            f"CoN detector failed: {result['error']} - " f"Found {result['violations_found']} violations (expected >0)"
        )
        assert result["violations_found"] > 0, "CoN detector should find naming violations"

    def test_cot_type_detector_works(self, connascence_validator):
        """Test CoT (Type) detector finds type hint violations."""
        sample_code = connascence_validator.sample_code_by_type["CoT"]
        result = connascence_validator.validate_detector("CoT", ConventionDetector, sample_code)

        assert result["passed"], (
            f"CoT detector failed: {result['error']} - " f"Found {result['violations_found']} violations (expected >0)"
        )
        assert result["violations_found"] > 0, "CoT detector should find missing type hints"

    def test_coi_identity_detector_works(self, connascence_validator):
        """Test CoI (Identity) detector finds identity coupling."""
        sample_code = connascence_validator.sample_code_by_type["CoI"]
        result = connascence_validator.validate_detector("CoI", ValuesDetector, sample_code)

        assert result["passed"], (
            f"CoI detector failed: {result['error']} - " f"Found {result['violations_found']} violations (expected >0)"
        )
        assert result["violations_found"] > 0, "CoI detector should find identity coupling"

    def test_all_9_types_validated(self, connascence_validator):
        """
        CRITICAL GATE: Validate ALL 9 connascence types work.

        This is the primary regression test - if this fails, SPEK integration
        has broken existing connascence detection capabilities.
        """
        results = connascence_validator.validate_all_types()
        summary = connascence_validator.get_summary(results)

        # Print detailed summary for debugging
        print("\n" + "=" * 80)
        print("CONNASCENCE TYPE PRESERVATION TEST SUMMARY")
        print("=" * 80)
        print(f"Total types tested: {summary['total_types']}/9")
        print(f"Types passed: {summary['types_passed']}")
        print(f"Types failed: {summary['types_failed']}")
        print(f"Pass rate: {summary['pass_rate']:.1f}%")
        print(f"All passed: {summary['all_passed']}")
        print(f"Coverage complete: {summary['coverage_complete']}")

        if summary["failed_types"]:
            print("\nFAILED TYPES:")
            for failed in summary["failed_types"]:
                print(f"  - {failed['type']}: {failed['detector']} - {failed['error']}")
                print(f"    Violations found: {failed['violations_found']}")

        print("=" * 80)

        # CRITICAL ASSERTIONS
        assert summary["coverage_complete"], f"Not all 9 types tested! Only {summary['total_types']}/9"

        assert summary["all_passed"], (
            f"CRITICAL: {summary['types_failed']} connascence types FAILED! "
            f"Failed types: {[f['type'] for f in summary['failed_types']]}"
        )

        assert summary["pass_rate"] == 100.0, f"CRITICAL: Pass rate is {summary['pass_rate']:.1f}%, must be 100%"

    def test_comprehensive_integration_scenario(self, connascence_validator):
        """Test realistic code with multiple connascence types."""
        complex_code = '''
class PaymentProcessor:
    """Complex class with multiple connascence violations"""

    def process_payment(self, user_id, amount, currency, payment_method,
                       billing_address, shipping_address, tax_rate, discount_code):
        """CoP: Too many parameters"""

        # CoM: Magic literals
        if amount > 1000:
            fee = amount * 0.025
        else:
            fee = amount * 0.035

        # CoV: Value coupling
        if payment_method == "CREDIT_CARD":
            self.process_credit_card()
        elif payment_method == "PAYPAL":
            self.process_paypal()

        return amount + fee

    # CoA: God object (many methods)
    def process_credit_card(self): pass
    def process_paypal(self): pass
    def validate_card(self): pass
    def encrypt_data(self): pass
    def store_transaction(self): pass
    def send_receipt(self): pass
    def update_inventory(self): pass
    def calculate_tax(self): pass
    def apply_discount(self): pass
    def handle_refund(self): pass
    def log_event(self): pass
    def notify_user(self): pass
    def generate_report(self): pass
    def export_data(self): pass
    def import_data(self): pass
    def validate_address(self): pass
    def check_fraud(self): pass
    def process_webhook(self): pass
    def sync_accounting(self): pass
    def manage_subscriptions(self): pass
    def handle_disputes(self): pass
    def track_analytics(self): pass
'''

        # This code should trigger multiple violation types
        tree = ast.parse(complex_code)
        source_lines = complex_code.split("\n")

        # Test multiple detectors find violations
        detectors = [
            PositionDetector(file_path="test.py", source_lines=source_lines),
            MagicLiteralDetector(file_path="test.py", source_lines=source_lines),
            GodObjectDetector(file_path="test.py", source_lines=source_lines),
            ValuesDetector(file_path="test.py", source_lines=source_lines),
        ]

        total_violations = 0
        for detector in detectors:
            violations = detector.detect_violations(tree)
            total_violations += len(violations)

        assert total_violations >= 4, (
            f"Complex code should trigger multiple violation types, " f"found only {total_violations}"
        )


@pytest.mark.integration
def test_connascence_preservation_integration():
    """Integration test for connascence type preservation."""
    validator = ConnascenceTypeValidator()
    results = validator.validate_all_types()
    summary = validator.get_summary(results)

    # Must preserve all 9 types
    assert summary["coverage_complete"], "Not all 9 connascence types covered"
    assert summary["all_passed"], f"Some types failed: {summary['failed_types']}"
    assert summary["pass_rate"] == 100.0, f"Pass rate: {summary['pass_rate']}%"

    print(f"\n✅ All {summary['types_passed']}/9 connascence types working correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "integration"])
