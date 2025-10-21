# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

"""
Pytest configuration and shared fixtures for connascence tests.

Provides common test fixtures, configuration, and utilities
for the entire test suite.
"""

import os
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Dict, List, Optional
from unittest.mock import Mock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import from our mock implementations instead of removed analyzer module
from utils.types import ConnascenceViolation


# Mock ThresholdConfig class for tests
class ThresholdConfig:
    def __init__(self, max_positional_params=3, god_class_methods=20, max_cyclomatic_complexity=10):
        self.max_positional_params = max_positional_params
        self.god_class_methods = god_class_methods
        self.max_cyclomatic_complexity = max_cyclomatic_complexity


@pytest.fixture
def sample_violations():
    """Create sample violations for testing."""
    return [
        ConnascenceViolation(
            id="test_magic_1",
            rule_id="CON_CoM",
            connascence_type="CoM",
            severity="medium",
            description="Magic literal '100' should be extracted to constant",
            file_path="/test/sample.py",
            line_number=10,
            weight=2.5,
        ),
        ConnascenceViolation(
            id="test_params_1",
            rule_id="CON_CoP",
            connascence_type="CoP",
            severity="high",
            description="Function has 6 positional parameters (max: 3)",
            file_path="/test/sample.py",
            line_number=15,
            weight=4.0,
        ),
        ConnascenceViolation(
            id="test_types_1",
            rule_id="CON_CoT",
            connascence_type="CoT",
            severity="medium",
            description="Function lacks type hints",
            file_path="/test/sample.py",
            line_number=20,
            weight=2.0,
        ),
        ConnascenceViolation(
            id="test_complexity_1",
            rule_id="CON_CoA",
            connascence_type="CoA",
            severity="critical",
            description="Class has 30 methods (max: 20)",
            file_path="/test/large_class.py",
            line_number=5,
            weight=5.0,
        ),
    ]


@pytest.fixture
def sample_python_code():
    """Sample Python code with various connascence violations."""
    return """
# File with multiple connascence violations

def calculate_discount(price, customer_type, season, promo_code, region, membership_level):
    '''Function with too many positional parameters (CoP violation).'''
    if price > 1000:  # Magic literal (CoM violation)
        base_discount = 0.15  # Magic literal (CoM violation)

        if customer_type == "premium":  # Magic string (CoM violation)
            if season == "winter":
                seasonal_boost = 0.05
            else:
                seasonal_boost = 0.02

            if promo_code == "SAVE20":  # Magic string (CoM violation)
                promo_discount = 0.2
            else:
                promo_discount = 0.0

            total_discount = base_discount + seasonal_boost + promo_discount
        else:
            total_discount = 0.1  # Magic literal (CoM violation)

        return price * (1 - total_discount)
    else:
        return price * 0.95  # Magic literal (CoM violation)


class OrderProcessor:
    '''God class with too many methods (CoA violation).'''

    def __init__(self):
        self.orders = []
        self.customers = {}
        self.inventory = {}
        self.shipping_rates = {}
        self.tax_rates = {}

    def validate_order(self, order):  # Missing type hints (CoT violation)
        pass

    def calculate_tax(self, amount, region):  # Missing type hints (CoT violation)
        pass

    def calculate_shipping(self, weight, destination):  # Missing type hints (CoT violation)
        pass

    def process_payment(self, payment_info):  # Missing type hints (CoT violation)
        pass

    def send_confirmation_email(self, customer_email):  # Missing type hints (CoT violation)
        pass

    def update_inventory(self, item_id, quantity):  # Missing type hints (CoT violation)
        pass

    def generate_invoice(self, order_id):  # Missing type hints (CoT violation)
        pass

    def handle_returns(self, return_request):  # Missing type hints (CoT violation)
        pass

    def calculate_loyalty_points(self, order_total):  # Missing type hints (CoT violation)
        pass

    def send_tracking_info(self, order_id, tracking_number):  # Missing type hints (CoT violation)
        pass

    def validate_promo_code(self, code):  # Missing type hints (CoT violation)
        pass

    def calculate_estimated_delivery(self, shipping_method):  # Missing type hints (CoT violation)
        pass

    def handle_order_cancellation(self, order_id):  # Missing type hints (CoT violation)
        pass

    def generate_shipping_label(self, order):  # Missing type hints (CoT violation)
        pass

    def process_bulk_orders(self, orders):  # Missing type hints (CoT violation)
        pass

    def handle_payment_failures(self, payment_id):  # Missing type hints (CoT violation)
        pass

    def calculate_seasonal_discounts(self, season):  # Missing type hints (CoT violation)
        pass

    def validate_shipping_address(self, address):  # Missing type hints (CoT violation)
        pass

    def generate_order_summary(self, order_id):  # Missing type hints (CoT violation)
        pass

    def handle_customer_complaints(self, complaint):  # Missing type hints (CoT violation)
        pass

    def process_refunds(self, refund_request):  # Missing type hints (CoT violation)
        pass

    def generate_sales_report(self, date_range):  # Missing type hints (CoT violation)
        pass

    def manage_product_catalog(self, products):  # Missing type hints (CoT violation)
        pass

    def handle_subscription_renewals(self, subscription_id):  # Missing type hints (CoT violation)
        pass

    def calculate_affiliate_commissions(self, sales_data):  # Missing type hints (CoT violation)
        pass


def untyped_function(param1, param2, param3):  # Missing type hints (CoT violation)
    '''Function without type hints.'''
    if param1 > 50:  # Magic literal (CoM violation)
        return param2 + param3 + 25  # Magic literal (CoM violation)
    return param1 * 2
"""


@pytest.fixture
def temp_project_dir():
    """Create temporary project directory with sample files."""
    temp_dir = tempfile.mkdtemp()
    project_path = Path(temp_dir)

    # Create directory structure
    (project_path / "src").mkdir()
    (project_path / "tests").mkdir()
    (project_path / "docs").mkdir()

    # Create Python files with various issues
    (project_path / "src" / "main.py").write_text(
        """
def main(arg1, arg2, arg3, arg4, arg5):  # Too many params
    threshold = 100  # Magic literal
    if arg1 > threshold:
        return True
    return False
"""
    )

    (project_path / "src" / "utils.py").write_text(
        """
def clean_function(x: int) -> int:
    return x * 2

def problematic_function(a, b, c):  # Missing types
    return a + b + 999  # Magic literal
"""
    )

    (project_path / "tests" / "test_main.py").write_text(
        """
import pytest

def test_main():
    assert True
"""
    )

    yield project_path

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_analyzer():
    """Create mock analyzer for testing."""
    analyzer = Mock()
    analyzer.analyze_file.return_value = []
    analyzer.analyze_directory.return_value = []
    analyzer.analyze_string.return_value = []
    return analyzer


@pytest.fixture
def threshold_configs():
    """Create various threshold configurations for testing."""
    return {
        "strict": ThresholdConfig(max_positional_params=2, god_class_methods=15, max_cyclomatic_complexity=8),
        "balanced": ThresholdConfig(max_positional_params=3, god_class_methods=20, max_cyclomatic_complexity=10),
        "lenient": ThresholdConfig(max_positional_params=5, god_class_methods=30, max_cyclomatic_complexity=15),
    }


@pytest.fixture
def budget_limits():
    """Create sample budget limits for testing."""
    return {
        "CoM": 5,  # Magic literals
        "CoP": 3,  # Parameter bombs
        "CoT": 8,  # Type issues
        "CoA": 2,  # Algorithm/complexity issues
        "total_violations": 20,
        "critical": 0,  # No critical violations allowed
        "high": 5,  # Max 5 high severity
        "medium": 15,  # Max 15 medium severity
    }


@pytest.fixture
def sample_policy_config():
    """Create sample policy configuration."""
    return {
        "name": "test-policy",
        "description": "Test policy for unit tests",
        "thresholds": {
            "max_positional_params": 4,
            "god_class_methods": 25,
            "max_cyclomatic_complexity": 12,
            "max_method_lines": 50,
            "max_class_lines": 300,
        },
        "budget_limits": {"CoM": 10, "CoP": 5, "CoT": 15, "CoA": 3, "total_violations": 50, "critical": 1, "high": 8},
        "exclusions": ["tests/*", "deprecated/*", "*.test.py"],
        "frameworks": ["pytest", "django"],
    }


@pytest.fixture
def sample_autofix_patches():
    """Create sample autofix patches for testing."""
    # from autofix.patch_api import PatchSuggestion
    # Mock PatchSuggestion for testing
    from dataclasses import dataclass
    from typing import Any, Dict, Tuple

    @dataclass
    class PatchSuggestion:
        violation_id: str
        confidence: float
        description: str
        old_code: str
        new_code: str
        file_path: str
        line_range: Tuple[int, int]
        safety_level: str = "safe"
        rollback_info: Dict[str, Any] = None

        def __post_init__(self):
            if self.rollback_info is None:
                self.rollback_info = {}

    return [
        PatchSuggestion(
            violation_id="magic_literal_1",
            confidence=0.85,
            description="Extract magic literal '100' to constant MAX_THRESHOLD",
            old_code="if value > 100:",
            new_code="MAX_THRESHOLD = 100\\nif value > MAX_THRESHOLD:",
            file_path="/test/sample.py",
            line_range=(10, 10),
            safety_level="safe",
            rollback_info={},
        ),
        PatchSuggestion(
            violation_id="param_bomb_1",
            confidence=0.72,
            description="Convert function to use keyword-only parameters",
            old_code="def func(a, b, c, d, e):",
            new_code="def func(a, b, *, c, d, e):",
            file_path="/test/sample.py",
            line_range=(15, 15),
            safety_level="moderate",
            rollback_info={},
        ),
        PatchSuggestion(
            violation_id="type_hints_1",
            confidence=0.90,
            description="Add type hints to function parameters",
            old_code="def process_data(data, options):",
            new_code="def process_data(data: Any, options: Dict[str, Any]) -> Any:",
            file_path="/test/sample.py",
            line_range=(20, 20),
            safety_level="safe",
            rollback_info={},
        ),
    ]


@pytest.fixture(scope="session")
def test_data_dir():
    """Directory containing test data files."""
    return Path(__file__).parent / "test_data"


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "autofix: marks tests related to autofix functionality")
    config.addinivalue_line("markers", "mcp: marks tests related to MCP server functionality")


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location."""
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid or "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)

        # Mark autofix tests
        if "autofix" in item.nodeid:
            item.add_marker(pytest.mark.autofix)

        # Mark MCP tests
        if "mcp" in item.nodeid:
            item.add_marker(pytest.mark.mcp)

        # Mark slow tests
        if "slow" in item.keywords or "performance" in item.nodeid:
            item.add_marker(pytest.mark.slow)


# Helper functions for tests
def create_temp_file(content: str, suffix: str = ".py") -> Path:
    """Create temporary file with given content."""
    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False)
    temp_file.write(content)
    temp_file.close()
    return Path(temp_file.name)


def assert_violation_present(
    violations: List[ConnascenceViolation],
    connascence_type: str,
    severity: Optional[str] = None,
    description_contains: Optional[str] = None,
) -> bool:
    """Assert that a specific type of violation is present in the list."""
    matching_violations = [v for v in violations if v.connascence_type == connascence_type]

    assert len(matching_violations) > 0, f"No {connascence_type} violations found"

    if severity:
        severity_matches = [v for v in matching_violations if v.severity == severity]
        assert len(severity_matches) > 0, f"No {connascence_type} violations with severity {severity}"

    if description_contains:
        description_matches = [v for v in matching_violations if description_contains.lower() in v.description.lower()]
        assert len(description_matches) > 0, f"No {connascence_type} violations containing '{description_contains}'"

    return True


def count_violations_by_type(violations: List[ConnascenceViolation]) -> Dict[str, int]:
    """Count violations by connascence type."""
    counts = {}
    for violation in violations:
        conn_type = violation.connascence_type
        counts[conn_type] = counts.get(conn_type, 0) + 1
    return counts


def count_violations_by_severity(violations: List[ConnascenceViolation]) -> Dict[str, int]:
    """Count violations by severity level."""
    counts = {}
    for violation in violations:
        severity = violation.severity
        counts[severity] = counts.get(severity, 0) + 1
    return counts
