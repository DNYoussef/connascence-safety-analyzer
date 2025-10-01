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
Tests for the policy management system.

Tests policy loading, validation, budget tracking, and baseline management
for the connascence analysis system.
"""

from pathlib import Path
import tempfile

import pytest
import yaml

from policy.baselines import BaselineManager
from policy.budgets import BudgetTracker
from policy.manager import PolicyManager, ThresholdConfig
from utils.types import ConnascenceViolation


class TestPolicyManager:
    """Test the policy management system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.policy_manager = PolicyManager()

    def test_default_presets_loading(self):
        """Test loading of default policy presets."""
        # Test strict-core preset
        strict_policy = self.policy_manager.get_preset("strict-core")
        assert strict_policy is not None
        assert strict_policy.max_positional_params == 2
        assert strict_policy.god_class_methods == 15

        # Test service-defaults preset
        service_policy = self.policy_manager.get_preset("service-defaults")
        assert service_policy is not None
        assert service_policy.max_positional_params == 3
        assert service_policy.god_class_methods == 20

        # Test experimental preset
        experimental_policy = self.policy_manager.get_preset("experimental")
        assert experimental_policy is not None
        assert experimental_policy.max_positional_params == 4

    def test_invalid_preset_name(self):
        """Test handling of invalid preset names."""
        with pytest.raises(ValueError) as exc_info:
            self.policy_manager.get_preset("non-existent-preset")

        assert "preset not found" in str(exc_info.value).lower()

    def test_custom_policy_loading(self):
        """Test loading custom policy from file."""
        # Create temporary policy file
        custom_policy = {
            "name": "test-policy",
            "description": "Test policy configuration",
            "thresholds": {"max_positional_params": 5, "god_class_methods": 30, "max_cyclomatic_complexity": 15},
            "budget_limits": {"CoM": 10, "CoP": 5, "total_violations": 50},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(custom_policy, f)
            policy_file = Path(f.name)

        try:
            # Load custom policy
            loaded_policy = self.policy_manager.load_from_file(policy_file)

            assert loaded_policy.max_positional_params == 5
            assert loaded_policy.god_class_methods == 30
            assert loaded_policy.max_cyclomatic_complexity == 15

        finally:
            policy_file.unlink()

    def test_policy_validation(self):
        """Test policy configuration validation."""
        # Valid policy should pass
        valid_config = ThresholdConfig(max_positional_params=3, god_class_methods=20, max_cyclomatic_complexity=10)

        assert self.policy_manager.validate_policy(valid_config) is True

        # Invalid policy should fail
        invalid_config = ThresholdConfig(
            max_positional_params=-1,  # Invalid negative value
            god_class_methods=0,  # Invalid zero value
            max_cyclomatic_complexity=1000,  # Unreasonably high
        )

        assert self.policy_manager.validate_policy(invalid_config) is False

    def test_policy_inheritance(self):
        """Test policy inheritance and customization."""
        # Load base policy
        base_policy = self.policy_manager.get_preset("service-defaults")

        # Create custom overrides
        overrides = {
            "max_positional_params": 2,  # Stricter than base
            "max_cyclomatic_complexity": 15,  # More lenient than base
        }

        # Apply overrides
        custom_policy = self.policy_manager.create_custom_policy(base_policy, overrides)

        assert custom_policy.max_positional_params == 2  # Overridden
        assert custom_policy.max_cyclomatic_complexity == 15  # Overridden
        assert custom_policy.god_class_methods == base_policy.god_class_methods  # Inherited

    def test_policy_serialization(self):
        """Test policy serialization and deserialization."""
        policy = self.policy_manager.get_preset("strict-core")

        # Serialize to dict
        policy_dict = self.policy_manager.serialize_policy(policy)

        assert isinstance(policy_dict, dict)
        assert "max_positional_params" in policy_dict
        assert policy_dict["max_positional_params"] == policy.max_positional_params

        # Deserialize back to policy
        restored_policy = self.policy_manager.deserialize_policy(policy_dict)

        assert restored_policy.max_positional_params == policy.max_positional_params
        assert restored_policy.god_class_methods == policy.god_class_methods


class TestBudgetTracker:
    """Test the budget tracking system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.budget_tracker = BudgetTracker()

        # Sample budget limits
        self.budget_limits = {
            "CoM": 5,  # Magic literals
            "CoP": 3,  # Parameter bombs
            "CoA": 2,  # Algorithm violations
            "total_violations": 15,
            "critical": 0,  # No critical violations allowed
            "high": 3,
        }

    def test_budget_initialization(self):
        """Test budget tracker initialization."""
        assert self.budget_tracker.budget_limits == {}
        assert self.budget_tracker.current_usage == {}

        # Set budget limits
        self.budget_tracker.set_budget_limits(self.budget_limits)

        assert self.budget_tracker.budget_limits == self.budget_limits

    def test_violation_tracking(self):
        """Test tracking violations against budget."""
        self.budget_tracker.set_budget_limits(self.budget_limits)

        # Create test violations
        violations = [
            ConnascenceViolation(
                id="test1",
                rule_id="CON_CoM",
                connascence_type="CoM",
                severity="medium",
                description="Magic literal",
                file_path="test.py",
                line_number=1,
                weight=2.0,
            ),
            ConnascenceViolation(
                id="test2",
                rule_id="CON_CoM",
                connascence_type="CoM",
                severity="high",
                description="Another magic literal",
                file_path="test.py",
                line_number=2,
                weight=3.0,
            ),
            ConnascenceViolation(
                id="test3",
                rule_id="CON_CoP",
                connascence_type="CoP",
                severity="critical",
                description="Parameter bomb",
                file_path="test.py",
                line_number=3,
                weight=5.0,
            ),
        ]

        # Track violations
        self.budget_tracker.track_violations(violations)

        # Check usage
        usage = self.budget_tracker.current_usage
        assert usage["CoM"] == 2  # Two CoM violations
        assert usage["CoP"] == 1  # One CoP violation
        assert usage["total_violations"] == 3
        assert usage["critical"] == 1
        assert usage["high"] == 1

    def test_budget_compliance_check(self):
        """Test budget compliance checking."""
        self.budget_tracker.set_budget_limits(self.budget_limits)

        # Within budget violations
        within_budget_violations = [
            ConnascenceViolation(
                id="test1",
                rule_id="CON_CoM",
                connascence_type="CoM",
                severity="medium",
                description="Magic literal",
                file_path="test.py",
                line_number=1,
                weight=2.0,
            ),
            ConnascenceViolation(
                id="test2",
                rule_id="CON_CoP",
                connascence_type="CoP",
                severity="medium",
                description="Parameter issue",
                file_path="test.py",
                line_number=2,
                weight=2.0,
            ),
        ]

        self.budget_tracker.track_violations(within_budget_violations)
        compliance_result = self.budget_tracker.check_compliance()

        assert compliance_result["compliant"] is True
        assert len(compliance_result["violations"]) == 0

        # Reset and test over-budget
        self.budget_tracker.reset()

        over_budget_violations = [
            ConnascenceViolation(
                id=f"test{i}",
                rule_id="CON_CoM",
                connascence_type="CoM",
                severity="medium",
                description=f"Magic literal {i}",
                file_path="test.py",
                line_number=i,
                weight=2.0,
            )
            for i in range(10)  # 10 CoM violations > budget of 5
        ]

        self.budget_tracker.track_violations(over_budget_violations)
        compliance_result = self.budget_tracker.check_compliance()

        assert compliance_result["compliant"] is False
        assert "CoM" in compliance_result["violations"]
        # 10 violations is within total_violations limit of 15, so total_violations should not be violated
        assert "total_violations" not in compliance_result["violations"]

    def test_budget_reporting(self):
        """Test budget usage reporting."""
        self.budget_tracker.set_budget_limits(self.budget_limits)

        violations = [
            ConnascenceViolation(
                id="test1",
                rule_id="CON_CoM",
                connascence_type="CoM",
                severity="high",
                description="Magic literal",
                file_path="test.py",
                line_number=1,
                weight=3.0,
            ),
            ConnascenceViolation(
                id="test2",
                rule_id="CON_CoP",
                connascence_type="CoP",
                severity="medium",
                description="Parameter issue",
                file_path="test.py",
                line_number=2,
                weight=2.0,
            ),
        ]

        self.budget_tracker.track_violations(violations)
        report = self.budget_tracker.generate_report()

        assert "budget_limits" in report
        assert "current_usage" in report
        assert "utilization" in report
        assert "compliance_status" in report

        # Check utilization calculations
        utilization = report["utilization"]
        assert utilization["CoM"] == 1 / 5  # 1 violation / 5 limit = 20%
        assert utilization["CoP"] == 1 / 3  # 1 violation / 3 limit = 33%

    def test_progressive_budget_tracking(self):
        """Test progressive budget tracking over multiple scans."""
        self.budget_tracker.set_budget_limits(self.budget_limits)

        # First batch of violations
        batch1 = [
            ConnascenceViolation(
                id="batch1_1",
                rule_id="CON_CoM",
                connascence_type="CoM",
                severity="medium",
                description="First batch",
                file_path="file1.py",
                line_number=1,
                weight=2.0,
            )
        ]

        self.budget_tracker.track_violations(batch1)
        assert self.budget_tracker.current_usage["CoM"] == 1

        # Second batch of violations
        batch2 = [
            ConnascenceViolation(
                id="batch2_1",
                rule_id="CON_CoM",
                connascence_type="CoM",
                severity="medium",
                description="Second batch",
                file_path="file2.py",
                line_number=1,
                weight=2.0,
            ),
            ConnascenceViolation(
                id="batch2_2",
                rule_id="CON_CoM",
                connascence_type="CoM",
                severity="medium",
                description="Second batch",
                file_path="file2.py",
                line_number=2,
                weight=2.0,
            ),
        ]

        self.budget_tracker.track_violations(batch2)
        assert self.budget_tracker.current_usage["CoM"] == 3  # Cumulative
        assert self.budget_tracker.current_usage["total_violations"] == 3


class TestBaselineManager:
    """Test the baseline management system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.baseline_manager = BaselineManager()

    def test_baseline_creation(self):
        """Test creating quality baselines."""
        # Sample violations for baseline
        baseline_violations = [
            ConnascenceViolation(
                id="baseline1",
                rule_id="CON_CoM",
                connascence_type="CoM",
                severity="medium",
                description="Existing magic literal",
                file_path="legacy.py",
                line_number=10,
                weight=2.0,
            ),
            ConnascenceViolation(
                id="baseline2",
                rule_id="CON_CoP",
                connascence_type="CoP",
                severity="high",
                description="Legacy parameter issue",
                file_path="legacy.py",
                line_number=20,
                weight=4.0,
            ),
        ]

        # Create baseline
        baseline_id = self.baseline_manager.create_baseline(
            violations=baseline_violations, description="Initial legacy code baseline", version="1.0.0"
        )

        assert baseline_id is not None

        # Verify baseline was stored
        baseline = self.baseline_manager.get_baseline(baseline_id)
        assert baseline is not None
        assert baseline["description"] == "Initial legacy code baseline"
        assert baseline["version"] == "1.0.0"
        assert len(baseline["violations"]) == 2

    def test_baseline_comparison(self):
        """Test comparing current violations against baseline."""
        # Create baseline
        baseline_violations = [
            ConnascenceViolation(
                id="legacy1",
                rule_id="CON_CoM",
                connascence_type="CoM",
                severity="medium",
                description="Legacy magic literal",
                file_path="old_code.py",
                line_number=5,
                weight=2.0,
            )
        ]

        baseline_id = self.baseline_manager.create_baseline(violations=baseline_violations, description="Test baseline")

        # Current violations (some new, some from baseline)
        current_violations = [
            ConnascenceViolation(
                id="legacy1",
                rule_id="CON_CoM",
                connascence_type="CoM",
                severity="medium",
                description="Legacy magic literal",
                file_path="old_code.py",
                line_number=5,
                weight=2.0,  # Same as baseline
            ),
            ConnascenceViolation(
                id="new1",
                rule_id="CON_CoP",
                connascence_type="CoP",
                severity="high",
                description="New parameter issue",
                file_path="new_code.py",
                line_number=10,
                weight=4.0,  # New violation
            ),
        ]

        # Compare against baseline
        comparison = self.baseline_manager.compare_against_baseline(current_violations, baseline_id)

        assert "new_violations" in comparison
        assert "resolved_violations" in comparison
        assert "unchanged_violations" in comparison

        # Should detect one new violation
        assert len(comparison["new_violations"]) == 1
        assert comparison["new_violations"][0]["id"] == "new1"

        # Should have one unchanged violation
        assert len(comparison["unchanged_violations"]) == 1
        assert comparison["unchanged_violations"][0]["id"] == "legacy1"

    def test_baseline_filtering(self):
        """Test filtering violations based on baseline."""
        # Create baseline with known violations
        baseline_violations = [
            ConnascenceViolation(
                id="known1",
                rule_id="CON_CoM",
                connascence_type="CoM",
                severity="medium",
                description="Known issue",
                file_path="legacy.py",
                line_number=1,
                weight=2.0,
            ),
            ConnascenceViolation(
                id="known2",
                rule_id="CON_CoA",
                connascence_type="CoA",
                severity="high",
                description="Known complexity",
                file_path="legacy.py",
                line_number=20,
                weight=4.0,
            ),
        ]

        baseline_id = self.baseline_manager.create_baseline(
            violations=baseline_violations, description="Known issues baseline"
        )

        # Current scan results
        current_violations = [
            ConnascenceViolation(
                id="known1",
                rule_id="CON_CoM",
                connascence_type="CoM",
                severity="medium",
                description="Known issue",
                file_path="legacy.py",
                line_number=1,
                weight=2.0,  # In baseline
            ),
            ConnascenceViolation(
                id="new_issue",
                rule_id="CON_CoT",
                connascence_type="CoT",
                severity="medium",
                description="New type issue",
                file_path="feature.py",
                line_number=15,
                weight=2.0,  # Not in baseline
            ),
        ]

        # Filter out baseline violations
        filtered_violations = self.baseline_manager.filter_new_violations(current_violations, baseline_id)

        # Should only contain new violations
        assert len(filtered_violations) == 1
        assert filtered_violations[0]["id"] == "new_issue"

    def test_baseline_versioning(self):
        """Test baseline versioning and history."""
        violations_v1 = [
            ConnascenceViolation(
                id="v1_issue",
                rule_id="CON_CoM",
                connascence_type="CoM",
                severity="medium",
                description="Version 1 issue",
                file_path="code.py",
                line_number=1,
                weight=2.0,
            )
        ]

        violations_v2 = [
            ConnascenceViolation(
                id="v1_issue",
                rule_id="CON_CoM",
                connascence_type="CoM",
                severity="medium",
                description="Version 1 issue",
                file_path="code.py",
                line_number=1,
                weight=2.0,
            ),
            ConnascenceViolation(
                id="v2_issue",
                rule_id="CON_CoP",
                connascence_type="CoP",
                severity="high",
                description="Version 2 issue",
                file_path="code.py",
                line_number=10,
                weight=4.0,
            ),
        ]

        # Create version 1 baseline
        self.baseline_manager.create_baseline(
            violations=violations_v1, description="Version 1.0 baseline", version="1.0.0"
        )

        # Create version 2 baseline
        self.baseline_manager.create_baseline(
            violations=violations_v2, description="Version 2.0 baseline", version="2.0.0"
        )

        # List all baselines
        baselines = self.baseline_manager.list_baselines()

        assert len(baselines) >= 2

        # Find our baselines
        v1_baseline = next(b for b in baselines if b["version"] == "1.0.0")
        v2_baseline = next(b for b in baselines if b["version"] == "2.0.0")

        assert len(v1_baseline["violations"]) == 1
        assert len(v2_baseline["violations"]) == 2

    def test_baseline_cleanup(self):
        """Test baseline cleanup and maintenance."""
        # Create multiple baselines
        baseline_ids = []
        for i in range(5):
            violations = [
                ConnascenceViolation(
                    id=f"test{i}",
                    rule_id="CON_CoM",
                    connascence_type="CoM",
                    severity="medium",
                    description=f"Test {i}",
                    file_path="test.py",
                    line_number=i,
                    weight=2.0,
                )
            ]

            baseline_id = self.baseline_manager.create_baseline(
                violations=violations, description=f"Test baseline {i}", version=f"1.0.{i}"
            )
            baseline_ids.append(baseline_id)

        # Clean up old baselines (keep only latest 3)
        self.baseline_manager.cleanup_old_baselines(keep_count=3)

        # Check remaining baselines
        remaining_baselines = self.baseline_manager.list_baselines()
        assert len(remaining_baselines) <= 3

        # Should keep the most recent ones
        versions = [b["version"] for b in remaining_baselines]
        assert "1.0.4" in versions  # Most recent should be kept
        assert "1.0.3" in versions
        assert "1.0.2" in versions


class TestPolicyIntegration:
    """Integration tests for policy system components."""

    def test_end_to_end_policy_workflow(self):
        """Test complete policy workflow from loading to enforcement."""
        # Step 1: Load policy
        policy_manager = PolicyManager()
        policy = policy_manager.get_preset("strict-core")

        # Step 2: Set up budget tracking
        budget_tracker = BudgetTracker()
        budget_limits = {"CoM": 3, "CoP": 2, "critical": 0, "total_violations": 10}
        budget_tracker.set_budget_limits(budget_limits)

        # Step 3: Create baseline
        baseline_manager = BaselineManager()
        baseline_violations = [
            ConnascenceViolation(
                id="legacy",
                rule_id="CON_CoA",
                connascence_type="CoA",
                severity="high",
                description="Legacy complexity",
                file_path="legacy.py",
                line_number=1,
                weight=4.0,
            )
        ]
        baseline_id = baseline_manager.create_baseline(baseline_violations, "Legacy baseline")

        # Step 4: Analyze new code violations
        new_violations = [
            ConnascenceViolation(
                id="new1",
                rule_id="CON_CoM",
                connascence_type="CoM",
                severity="medium",
                description="New magic literal",
                file_path="new.py",
                line_number=5,
                weight=2.0,
            ),
            ConnascenceViolation(
                id="new2",
                rule_id="CON_CoP",
                connascence_type="CoP",
                severity="high",
                description="New parameter issue",
                file_path="new.py",
                line_number=10,
                weight=4.0,
            ),
        ]

        # Step 5: Filter against baseline (exclude legacy issues)
        filtered_violations = baseline_manager.filter_new_violations(new_violations, baseline_id)

        # Step 6: Check budget compliance
        budget_tracker.track_violations(filtered_violations)
        compliance = budget_tracker.check_compliance()

        # Verify results
        assert len(filtered_violations) == 2  # No legacy issues
        assert compliance["compliant"] is True  # Within budget

        # Step 7: Generate policy report
        policy_report = {
            "policy_used": "strict-core",
            "baseline_filtered": len(baseline_violations),
            "new_violations": len(filtered_violations),
            "budget_compliance": compliance,
            "policy_thresholds": {
                "max_positional_params": policy.max_positional_params,
                "god_class_methods": policy.god_class_methods,
            },
        }

        assert policy_report["policy_used"] == "strict-core"
        assert policy_report["budget_compliance"]["compliant"] is True

    def test_policy_violation_categorization(self):
        """Test categorization of violations by policy rules."""
        policy_manager = PolicyManager()
        strict_policy = policy_manager.get_preset("strict-core")

        # Violations that should be flagged under strict policy
        violations = [
            ConnascenceViolation(
                id="param_violation",
                rule_id="CON_CoP",
                connascence_type="CoP",
                severity="high",
                description="4 positional parameters",  # > strict limit of 2
                file_path="test.py",
                line_number=1,
                weight=4.0,
            ),
            ConnascenceViolation(
                id="acceptable_params",
                rule_id="CON_CoP",
                connascence_type="CoP",
                severity="low",
                description="2 positional parameters",  # = strict limit
                file_path="test.py",
                line_number=5,
                weight=1.0,
            ),
            ConnascenceViolation(
                id="god_class",
                rule_id="CON_CoA",
                connascence_type="CoA",
                severity="critical",
                description="25 methods in class",  # > strict limit of 15
                file_path="test.py",
                line_number=10,
                weight=5.0,
            ),
        ]

        # Categorize violations based on policy
        categorized = policy_manager.categorize_violations(violations, strict_policy)

        assert "policy_violations" in categorized
        assert "acceptable_violations" in categorized

        # Should flag violations that exceed strict thresholds
        policy_violations = categorized["policy_violations"]
        violation_ids = [v["id"] for v in policy_violations]

        assert "param_violation" in violation_ids  # 4 params > 2 limit
        assert "god_class" in violation_ids  # 25 methods > 15 limit

        # Should accept violations within thresholds
        acceptable_violations = categorized["acceptable_violations"]
        acceptable_ids = [v["id"] for v in acceptable_violations]

        assert "acceptable_params" in acceptable_ids  # 2 params = 2 limit
