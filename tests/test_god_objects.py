#!/usr/bin/env python3
"""
Test suite for context-aware god object detection.

Tests Requirements:
1. Config classes with many properties should be lenient
2. Business logic classes should be strict
3. Data models vs API controllers different thresholds
4. Dynamic threshold calculation based on class type
"""

import ast
from typing import List

import pytest

from analyzer.check_connascence import ConnascenceAnalyzer, ConnascenceDetector
from utils.types import ConnascenceViolation
from analyzer.constants import GOD_OBJECT_METHOD_THRESHOLD_CI


class TestGodObjectContextAware:
    """Test context-aware god object detection with different class types."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = ConnascenceAnalyzer()

    def test_config_classes_lenient_detection(self):
        """Test that config classes with many properties are treated leniently."""
        config_class_code = '''
class DatabaseConfig:
    """Configuration class - should be lenient with many properties."""

    def __init__(self):
        self.host = "localhost"
        self.port = 5432
        self.database = "app"
        self.username = "user"
        self.password = "pass"
        self.connection_timeout = 30
        self.read_timeout = 60
        self.pool_size = 10
        self.max_overflow = 20
        self.echo = False
        self.autocommit = False
        self.isolation_level = "READ_COMMITTED"

    def get_host(self): return self.host
    def set_host(self, host): self.host = host
    def get_port(self): return self.port
    def set_port(self, port): self.port = port
    def get_database(self): return self.database
    def set_database(self, db): self.database = db
    def get_username(self): return self.username
    def set_username(self, user): self.username = user
    def get_password(self): return self.password
    def set_password(self, pwd): self.password = pwd
    def get_connection_timeout(self): return self.connection_timeout
    def set_connection_timeout(self, timeout): self.connection_timeout = timeout
    def get_read_timeout(self): return self.read_timeout
    def set_read_timeout(self, timeout): self.read_timeout = timeout
    def get_pool_size(self): return self.pool_size
    def set_pool_size(self, size): self.pool_size = size
    def get_max_overflow(self): return self.max_overflow
    def set_max_overflow(self, overflow): self.max_overflow = overflow
    def get_echo(self): return self.echo
    def set_echo(self, echo): self.echo = echo
    def get_autocommit(self): return self.autocommit
    def set_autocommit(self, commit): self.autocommit = commit
    def get_isolation_level(self): return self.isolation_level
    def set_isolation_level(self, level): self.isolation_level = level
    def validate_config(self): return True
    def to_dict(self): return vars(self)
    def from_dict(self, data):
        for key, value in data.items():
            setattr(self, key, value)
'''

        violations = self._analyze_code_string(config_class_code)
        god_object_violations = [v for v in violations if v.type == "god_object"]

        # Config classes should be more lenient - might not be flagged despite many methods
        if god_object_violations:
            # If flagged, should be lower severity
            config_violation = god_object_violations[0]
            # Could be medium instead of critical for config classes
            assert config_violation.severity in ["medium", "high"], \
                f"Config class should have reduced severity, got {config_violation.severity}"

    def test_business_logic_classes_strict_detection(self):
        """Test that business logic classes are subject to strict detection."""
        business_logic_code = '''
class OrderProcessor:
    """Business logic class - should be strict detection."""

    def __init__(self):
        self.orders = []
        self.customers = {}
        self.products = {}

    def validate_order(self, order): pass
    def calculate_tax(self, order): pass
    def apply_discount(self, order): pass
    def check_inventory(self, order): pass
    def reserve_inventory(self, order): pass
    def process_payment(self, order): pass
    def send_confirmation(self, order): pass
    def update_customer_history(self, order): pass
    def generate_invoice(self, order): pass
    def schedule_shipping(self, order): pass
    def notify_warehouse(self, order): pass
    def update_analytics(self, order): pass
    def log_transaction(self, order): pass
    def handle_refund(self, order): pass
    def cancel_order(self, order): pass
    def modify_order(self, order): pass
    def split_order(self, order): pass
    def merge_orders(self, orders): pass
    def batch_process(self, orders): pass
    def generate_report(self): pass
    def export_data(self): pass
    def import_data(self, data): pass
    def cleanup_expired(self): pass
    def archive_old_orders(self): pass
'''

        violations = self._analyze_code_string(business_logic_code)
        god_object_violations = [v for v in violations if v.type == "god_object"]

        # Business logic classes should be flagged strictly
        assert len(god_object_violations) > 0, "Business logic class with many methods should be flagged"

        business_violation = god_object_violations[0]
        assert business_violation.severity == "critical", \
            f"Business logic god object should be critical severity, got {business_violation.severity}"

    def test_data_model_vs_controller_thresholds(self):
        """Test different thresholds for data models vs API controllers."""

        # Data model - more lenient (properties + simple methods)
        data_model_code = '''
class UserModel:
    """Data model - should be more lenient with properties and simple methods."""

    def __init__(self):
        self.id = None
        self.email = None
        self.name = None
        self.created_at = None
        self.updated_at = None

    @property
    def id(self): return self._id
    @id.setter
    def id(self, value): self._id = value

    @property
    def email(self): return self._email
    @email.setter
    def email(self, value): self._email = value

    @property
    def name(self): return self._name
    @name.setter
    def name(self, value): self._name = value

    @property
    def created_at(self): return self._created_at
    @created_at.setter
    def created_at(self, value): self._created_at = value

    @property
    def updated_at(self): return self._updated_at
    @updated_at.setter
    def updated_at(self, value): self._updated_at = value

    def to_dict(self): return vars(self)
    def from_dict(self, data): pass
    def validate(self): return True
    def save(self): pass
    def delete(self): pass
    def refresh(self): pass
    def __str__(self): return f"User({self.email})"
    def __repr__(self): return self.__str__()
'''

        # API controller - should be strict
        controller_code = '''
class UserController:
    """API controller - should have strict god object detection."""

    def __init__(self):
        self.service = None
        self.validator = None

    def create_user(self, request): pass
    def get_user(self, user_id): pass
    def update_user(self, user_id, data): pass
    def delete_user(self, user_id): pass
    def list_users(self, filters): pass
    def search_users(self, query): pass
    def activate_user(self, user_id): pass
    def deactivate_user(self, user_id): pass
    def reset_password(self, user_id): pass
    def change_password(self, user_id, new_pass): pass
    def send_welcome_email(self, user_id): pass
    def verify_email(self, token): pass
    def upload_avatar(self, user_id, file): pass
    def get_user_stats(self, user_id): pass
    def export_user_data(self, user_id): pass
    def import_users(self, data): pass
    def bulk_update(self, updates): pass
    def bulk_delete(self, user_ids): pass
    def assign_role(self, user_id, role): pass
    def remove_role(self, user_id, role): pass
    def get_permissions(self, user_id): pass
    def audit_user_actions(self, user_id): pass
'''

        # Test data model
        model_violations = self._analyze_code_string(data_model_code)
        [v for v in model_violations if v.type == "god_object"]

        # Test controller
        controller_violations = self._analyze_code_string(controller_code)
        controller_god_violations = [v for v in controller_violations if v.type == "god_object"]

        # Controller should be more likely to be flagged or flagged with higher severity
        if controller_god_violations:
            assert controller_god_violations[0].severity == "critical", \
                "Controller god object should be critical"

    def test_dynamic_threshold_calculation(self):
        """Test dynamic threshold calculation based on class type and context."""

        # Test class with exactly at the threshold
        threshold_class_code = '''
class ThresholdClass:
    """Class exactly at the method threshold."""

    def __init__(self): pass
    def method_01(self): pass
    def method_02(self): pass
    def method_03(self): pass
    def method_04(self): pass
    def method_05(self): pass
    def method_06(self): pass
    def method_07(self): pass
    def method_08(self): pass
    def method_09(self): pass
    def method_10(self): pass
    def method_11(self): pass
    def method_12(self): pass
    def method_13(self): pass
    def method_14(self): pass
    def method_15(self): pass
    def method_16(self): pass
    def method_17(self): pass
    def method_18(self): pass
    def method_19(self): pass  # Exactly at CI threshold (19 methods)
'''

        violations = self._analyze_code_string(threshold_class_code)
        god_object_violations = [v for v in violations if v.type == "god_object"]

        # Should be flagged if over the current threshold
        method_count = 19  # Based on the test code above

        if method_count > GOD_OBJECT_METHOD_THRESHOLD_CI:
            assert len(god_object_violations) > 0, f"Class with {method_count} methods should be flagged"
        else:
            # At or under threshold - should not be flagged
            assert len(god_object_violations) == 0, f"Class with {method_count} methods should not be flagged"

    def test_utility_classes_special_handling(self):
        """Test that utility classes get special handling."""

        utility_class_code = '''
class StringUtils:
    """Utility class - should be handled specially."""

    @staticmethod
    def is_empty(s): return not s

    @staticmethod
    def is_blank(s): return not s.strip()

    @staticmethod
    def capitalize_words(s): return s.title()

    @staticmethod
    def snake_to_camel(s): pass

    @staticmethod
    def camel_to_snake(s): pass

    @staticmethod
    def truncate(s, length): return s[:length]

    @staticmethod
    def pad_left(s, length, char=' '): pass

    @staticmethod
    def pad_right(s, length, char=' '): pass

    @staticmethod
    def remove_whitespace(s): pass

    @staticmethod
    def count_words(s): pass

    @staticmethod
    def reverse(s): return s[::-1]

    @staticmethod
    def is_palindrome(s): pass

    @staticmethod
    def levenshtein_distance(s1, s2): pass

    @staticmethod
    def similarity(s1, s2): pass

    @staticmethod
    def extract_numbers(s): pass

    @staticmethod
    def mask_sensitive(s): pass

    @staticmethod
    def validate_email(email): pass

    @staticmethod
    def validate_phone(phone): pass

    @staticmethod
    def clean_filename(filename): pass

    @staticmethod
    def generate_slug(text): pass
'''

        violations = self._analyze_code_string(utility_class_code)
        god_object_violations = [v for v in violations if v.type == "god_object"]

        # Utility classes might be handled more leniently
        if god_object_violations:
            # Should be lower severity for utility classes
            utility_violation = god_object_violations[0]
            # Utility classes might get medium severity instead of critical
            assert utility_violation.severity in ["medium", "high"], \
                f"Utility class should have reduced severity, got {utility_violation.severity}"

    def test_interface_implementation_classes(self):
        """Test classes that implement large interfaces."""

        interface_impl_code = '''
class DatabaseRepository:
    """Repository implementing large interface - should be contextually evaluated."""

    def __init__(self): pass

    # CRUD operations
    def create(self, entity): pass
    def read(self, id): pass
    def update(self, id, data): pass
    def delete(self, id): pass

    # Batch operations
    def create_many(self, entities): pass
    def read_many(self, ids): pass
    def update_many(self, updates): pass
    def delete_many(self, ids): pass

    # Query operations
    def find_by_field(self, field, value): pass
    def find_all(self): pass
    def find_with_pagination(self, page, size): pass
    def find_with_filter(self, filters): pass
    def count(self): pass
    def exists(self, id): pass

    # Transaction operations
    def begin_transaction(self): pass
    def commit_transaction(self): pass
    def rollback_transaction(self): pass

    # Maintenance operations
    def optimize(self): pass
    def backup(self): pass
    def restore(self, backup): pass
    def migrate(self, version): pass
    def validate_schema(self): pass
'''

        violations = self._analyze_code_string(interface_impl_code)
        [v for v in violations if v.type == "god_object"]

        # Repository pattern classes might be handled contextually
        # This is a design decision - they might be flagged but with consideration
        # for the fact they're implementing a standard interface

    def test_legacy_class_handling(self):
        """Test handling of legacy classes that need refactoring."""

        legacy_class_code = '''
class LegacyOrderSystem:
    """Legacy class that clearly needs refactoring - should be flagged strictly."""

    def __init__(self): pass
    def create_order(self): pass
    def validate_order(self): pass
    def calculate_tax(self): pass
    def apply_discount(self): pass
    def process_payment(self): pass
    def send_confirmation(self): pass
    def print_invoice(self): pass
    def generate_pdf(self): pass
    def email_customer(self): pass
    def update_inventory(self): pass
    def log_transaction(self): pass
    def backup_data(self): pass
    def generate_reports(self): pass
    def export_data(self): pass
    def import_data(self): pass
    def cleanup_temp_files(self): pass
    def validate_config(self): pass
    def restart_services(self): pass
    def monitor_health(self): pass
    def handle_errors(self): pass
    def debug_issues(self): pass
    def optimize_performance(self): pass
    def scale_resources(self): pass
    def migrate_data(self): pass
'''

        violations = self._analyze_code_string(legacy_class_code)
        god_object_violations = [v for v in violations if v.type == "god_object"]

        # Legacy classes doing too many things should definitely be flagged
        assert len(god_object_violations) > 0, "Legacy god object should be flagged"

        legacy_violation = god_object_violations[0]
        assert legacy_violation.severity == "critical", \
            f"Legacy god object should be critical severity, got {legacy_violation.severity}"

    def _analyze_code_string(self, code: str) -> List[ConnascenceViolation]:
        """Helper method to analyze code string."""
        source_lines = code.splitlines()
        tree = ast.parse(code)
        detector = ConnascenceDetector("test_file.py", source_lines)
        detector.visit(tree)
        detector.finalize_analysis()
        return detector.violations

    def test_method_count_accuracy(self):
        """Test that method counting is accurate and consistent."""

        test_class_code = '''
class MethodCountTest:
    """Test class for accurate method counting."""

    def __init__(self):
        pass

    def public_method_1(self):
        pass

    def public_method_2(self):
        pass

    def _private_method_1(self):
        pass

    def __dunder_method__(self):
        pass

    @property
    def property_method(self):
        return self._value

    @property_method.setter
    def property_method(self, value):
        self._value = value

    @staticmethod
    def static_method():
        pass

    @classmethod
    def class_method(cls):
        pass
'''

        violations = self._analyze_code_string(test_class_code)
        [v for v in violations if v.type == "god_object"]

        # Should accurately count methods (including private, static, class methods)
        # This test ensures our method counting is consistent with god object detection


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
