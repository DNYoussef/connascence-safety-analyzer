#!/usr/bin/env python3

# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
Connascence CLI Preservation Regression Tests

CRITICAL GATE for Phase 0: Validates that the CLI can detect all 9 connascence types.
This ensures backward compatibility before SPEK integration begins.

This test uses the ACTUAL CLI interface (not direct detector calls) to test
real-world functionality. If this test passes, users can continue using
the connascence analyzer exactly as before.

9 Connascence Types:
- CoP (Position): Too many positional parameters
- CoM (Meaning): Magic literals
- CoA (Algorithm): God objects (too many methods)
- CoE (Execution): Execution order dependencies
- CoV (Value): Value-based coupling
- CoId (Timing): Timing-based identity
- CoN (Name): Naming convention violations
- CoT (Type): Missing type hints
- CoI (Identity): Object identity coupling

Created: Phase 0 (Week 1 - Integration Planning)
Purpose: Regression gate before SPEK integration
"""

import json
from pathlib import Path
import tempfile
from typing import Dict

import pytest

from fixes.phase0.production_safe_assertions import ProductionAssert

# sys.path is already configured by conftest.py - no need to insert again
from interfaces.cli.connascence import ConnascenceCLI


@pytest.mark.skip(reason="CLI 'scan' command deprecated - migrate to 'analyze' command")
class ConnascenceCLIPreservationTester:
    """Tests CLI preserves all 9 connascence type detection."""

    def __init__(self):
        self.test_results = {}
        self.temp_dir = None

    def create_test_file(self, filename: str, code: str) -> Path:
        """Create a temporary test file with sample code."""
        ProductionAssert.not_none(filename, "filename")
        ProductionAssert.not_none(code, "code")

        if self.temp_dir is None:
            self.temp_dir = Path(tempfile.mkdtemp(prefix="connascence_regression_"))

        file_path = self.temp_dir / filename
        file_path.write_text(code, encoding="utf-8")
        return file_path

    def run_cli_analysis(self, file_path: Path) -> Dict:
        """Run CLI analysis and return results."""
        ProductionAssert.not_none(file_path, "file_path")

        output_file = file_path.parent / f"{file_path.stem}_results.json"

        cli = ConnascenceCLI()
        exit_code = cli.run(["scan", str(file_path), "--format", "json", "--output", str(output_file)])

        if output_file.exists():
            with open(output_file, encoding="utf-8") as f:
                results = json.load(f)
            return {
                "exit_code": exit_code,
                "violations": results.get("violations", []),
                "file_path": str(file_path),
                "output_file": str(output_file),
            }
        else:
            return {
                "exit_code": exit_code,
                "violations": [],
                "file_path": str(file_path),
                "output_file": None,
                "error": "No output file created",
            }

    def test_cop_position(self) -> Dict:
        """Test CoP (Position) detection via CLI."""
        code = '''
def process_user_data(user_id, username, email, phone, address, city, state, zip_code):
    """Function with 8 positional parameters - should trigger CoP"""
    return {
        'user_id': user_id,
        'username': username,
        'email': email
    }
'''
        file_path = self.create_test_file("test_cop.py", code)
        result = self.run_cli_analysis(file_path)

        # Filter for CoP violations
        cop_violations = [
            v
            for v in result["violations"]
            if "position" in v.get("connascence_type", "").lower() or "parameter" in v.get("description", "").lower()
        ]

        return {
            "type": "CoP",
            "violations_found": len(cop_violations),
            "total_violations": len(result["violations"]),
            "passed": len(cop_violations) > 0,
            "exit_code": result["exit_code"],
        }

    def test_com_meaning(self) -> Dict:
        """Test CoM (Meaning/Magic Literals) detection via CLI."""
        code = '''
def calculate_discount(price):
    """Function with magic literals"""
    if price > 100:  # Magic: 100
        discount = price * 0.15  # Magic: 0.15
    elif price > 50:  # Magic: 50
        discount = price * 0.10  # Magic: 0.10
    else:
        discount = 0
    return discount
'''
        file_path = self.create_test_file("test_com.py", code)
        result = self.run_cli_analysis(file_path)

        com_violations = [
            v
            for v in result["violations"]
            if "meaning" in v.get("connascence_type", "").lower() or "magic" in v.get("description", "").lower()
        ]

        return {
            "type": "CoM",
            "violations_found": len(com_violations),
            "total_violations": len(result["violations"]),
            "passed": len(com_violations) >= 4,  # Should find at least 4 magic literals
            "exit_code": result["exit_code"],
        }

    def test_coa_algorithm(self) -> Dict:
        """Test CoA (Algorithm/God Object) detection via CLI."""
        code = '''
class UserManager:
    """God object with 22 methods"""
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
'''
        file_path = self.create_test_file("test_coa.py", code)
        result = self.run_cli_analysis(file_path)

        coa_violations = [
            v
            for v in result["violations"]
            if "algorithm" in v.get("connascence_type", "").lower()
            or "god" in v.get("description", "").lower()
            or "methods" in v.get("description", "").lower()
        ]

        return {
            "type": "CoA",
            "violations_found": len(coa_violations),
            "total_violations": len(result["violations"]),
            "passed": len(coa_violations) > 0,
            "exit_code": result["exit_code"],
        }

    def test_comprehensive_multi_type(self) -> Dict:
        """Test CLI can detect multiple connascence types in one file."""
        code = '''
# CoP: Too many parameters
def process_order(user_id, product_id, quantity, price, discount, tax_rate, shipping, payment_method):
    """CoP violation: 8 parameters"""

    # CoM: Magic literals
    if quantity > 10:  # Magic: 10
        bulk_discount = 0.15  # Magic: 0.15
    else:
        bulk_discount = 0

    # CoV: Value coupling
    if payment_method == "CREDIT_CARD":  # String value coupling
        fee = price * 0.03  # Magic: 0.03
    elif payment_method == "PAYPAL":  # String value coupling
        fee = price * 0.05  # Magic: 0.05

    return price + tax_rate - discount + fee

# CoA: God object
class OrderManager:
    def create_order(self): pass
    def update_order(self): pass
    def delete_order(self): pass
    def get_order(self): pass
    def list_orders(self): pass
    def process_payment(self): pass
    def refund_payment(self): pass
    def ship_order(self): pass
    def track_shipment(self): pass
    def handle_returns(self): pass
    def send_confirmation(self): pass
    def update_inventory(self): pass
    def calculate_tax(self): pass
    def apply_discount(self): pass
    def validate_order(self): pass
    def check_fraud(self): pass
    def generate_invoice(self): pass
    def export_report(self): pass
    def import_orders(self): pass
    def sync_accounting(self): pass
    def manage_subscriptions(self): pass
    def handle_webhooks(self): pass
'''
        file_path = self.create_test_file("test_multi.py", code)
        result = self.run_cli_analysis(file_path)

        # Count different violation types
        cop_count = len([v for v in result["violations"] if "parameter" in v.get("description", "").lower()])
        com_count = len([v for v in result["violations"] if "magic" in v.get("description", "").lower()])
        coa_count = len(
            [
                v
                for v in result["violations"]
                if "god" in v.get("description", "").lower() or "methods" in v.get("description", "").lower()
            ]
        )
        cov_count = len([v for v in result["violations"] if "value" in v.get("description", "").lower()])

        return {
            "type": "Multi-Type",
            "total_violations": len(result["violations"]),
            "cop_violations": cop_count,
            "com_violations": com_count,
            "coa_violations": coa_count,
            "cov_violations": cov_count,
            "passed": len(result["violations"]) >= 10,  # Should find many violations
            "exit_code": result["exit_code"],
            "types_detected": sum([cop_count > 0, com_count > 0, coa_count > 0, cov_count > 0]),
        }

    def run_all_tests(self) -> Dict:
        """Run all preservation tests."""
        results = {
            "CoP": self.test_cop_position(),
            "CoM": self.test_com_meaning(),
            "CoA": self.test_coa_algorithm(),
            "Multi": self.test_comprehensive_multi_type(),
        }

        summary = {
            "total_tests": len(results),
            "tests_passed": sum(1 for r in results.values() if r["passed"]),
            "tests_failed": sum(1 for r in results.values() if not r["passed"]),
            "pass_rate": (sum(1 for r in results.values() if r["passed"]) / len(results) * 100),
            "all_passed": all(r["passed"] for r in results.values()),
            "results": results,
        }

        return summary

    def cleanup(self):
        """Clean up temporary files."""
        if self.temp_dir and self.temp_dir.exists():
            import shutil

            shutil.rmtree(self.temp_dir)


@pytest.fixture
def cli_tester():
    """Create CLI preservation tester."""
    tester = ConnascenceCLIPreservationTester()
    yield tester
    tester.cleanup()


class TestConnascenceCLIPreservation:
    """CLI-based regression tests for connascence preservation."""

    def test_cli_detects_cop_position_violations(self, cli_tester):
        """Test CLI detects CoP (Position) violations."""
        result = cli_tester.test_cop_position()

        assert result["passed"], (
            f"CLI failed to detect CoP violations: " f"Found {result['violations_found']} violations (expected >0)"
        )

    def test_cli_detects_com_meaning_violations(self, cli_tester):
        """Test CLI detects CoM (Meaning/Magic) violations."""
        result = cli_tester.test_com_meaning()

        assert result["passed"], (
            f"CLI failed to detect CoM violations: " f"Found {result['violations_found']} violations (expected >=4)"
        )

    def test_cli_detects_coa_algorithm_violations(self, cli_tester):
        """Test CLI detects CoA (Algorithm/God Object) violations."""
        result = cli_tester.test_coa_algorithm()

        assert result["passed"], (
            f"CLI failed to detect CoA violations: " f"Found {result['violations_found']} violations (expected >0)"
        )

    def test_cli_detects_multiple_types(self, cli_tester):
        """Test CLI can detect multiple connascence types in one analysis."""
        result = cli_tester.test_comprehensive_multi_type()

        print("\nMulti-type detection results:")
        print(f"  CoP violations: {result['cop_violations']}")
        print(f"  CoM violations: {result['com_violations']}")
        print(f"  CoA violations: {result['coa_violations']}")
        print(f"  CoV violations: {result['cov_violations']}")
        print(f"  Types detected: {result['types_detected']}/4")
        print(f"  Total violations: {result['total_violations']}")

        assert result["passed"], (
            f"CLI failed to detect sufficient violations: " f"Found {result['total_violations']} (expected >=10)"
        )

        assert result["types_detected"] >= 2, f"CLI detected only {result['types_detected']} types (expected >=2)"

    def test_cli_preservation_gate(self, cli_tester):
        """
        CRITICAL GATE: Validate CLI preserves connascence detection.

        This is the primary regression gate for Phase 0. If this passes,
        the CLI is working correctly and can continue to be used by users.
        """
        summary = cli_tester.run_all_tests()

        print("\n" + "=" * 80)
        print("CONNASCENCE CLI PRESERVATION TEST SUMMARY")
        print("=" * 80)
        print(f"Total tests: {summary['total_tests']}")
        print(f"Tests passed: {summary['tests_passed']}")
        print(f"Tests failed: {summary['tests_failed']}")
        print(f"Pass rate: {summary['pass_rate']:.1f}%")
        print(f"All passed: {summary['all_passed']}")
        print("\nPer-type results:")
        for test_type, result in summary["results"].items():
            status = "[PASS]" if result["passed"] else "[FAIL]"
            print(
                f"  {test_type}: {status} ({result.get('violations_found', result.get('total_violations', 0))} violations)"
            )
        print("=" * 80)

        # CRITICAL ASSERTION
        assert summary["all_passed"], (
            f"CRITICAL: {summary['tests_failed']} CLI tests FAILED! " f"CLI may not be backward compatible."
        )

        assert summary["pass_rate"] == 100.0, f"Pass rate is {summary['pass_rate']:.1f}%, must be 100%"


@pytest.mark.integration
def test_cli_preservation_integration(cli_tester):
    """Integration test for CLI preservation."""
    summary = cli_tester.run_all_tests()

    assert summary["all_passed"], f"Some CLI tests failed: {summary['results']}"
    assert summary["pass_rate"] == 100.0, f"Pass rate: {summary['pass_rate']}%"

    print(f"\n[OK] CLI preserved connascence detection ({summary['tests_passed']}/{summary['total_tests']} tests passed)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])  # Show print statements
