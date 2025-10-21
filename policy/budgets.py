#!/usr/bin/env python3

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
Enhanced Budget Enforcement with Baseline Awareness
=================================================

Provides enterprise-grade budget enforcement for connascence violations including:
- Baseline-aware budget tracking and enforcement
- Integration with waiver system for budget exemptions
- Drift analysis for budget trend monitoring
- CI/CD integration with fail-fast budget checking
- Comprehensive budget reporting and alerting

Author: Connascence Safety Analyzer Team
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import time
from typing import Any, Dict, List, Optional

from utils.types import ConnascenceViolation

# Mock ConnascenceViolation for removed analyzer dependency
# ConnascenceViolation now available from utils.types
# This duplicate class has been removed

# BudgetTracker Configuration Constants (CoM Improvement - Pass 2)
DEFAULT_USAGE_HISTORY_LIMIT = 10  # Last N entries to keep in usage history


class BudgetMode(Enum):
    """Budget enforcement modes."""

    STRICT = "strict"  # Fail immediately on budget violation
    BASELINE = "baseline"  # Only fail on new violations beyond baseline
    TRENDING = "trending"  # Fail based on trend analysis
    ADVISORY = "advisory"  # Report but don't fail


@dataclass
class BudgetConfiguration:
    """Budget configuration settings."""

    mode: BudgetMode = BudgetMode.BASELINE
    total_violations: int = 50
    critical_violations: int = 0
    high_violations: int = 5
    medium_violations: int = 20
    new_violations_per_pr: int = 3
    trend_degradation_rate: float = 1.0  # violations per day threshold
    waiver_exemptions_enabled: bool = True
    drift_analysis_enabled: bool = True
    ci_fail_on_budget_exceeded: bool = True


class EnhancedBudgetTracker:
    """Enhanced budget tracker with baseline awareness and enterprise features."""

    def __init__(self, project_root: Optional[Path] = None, config: Optional[BudgetConfiguration] = None):
        self.project_root = project_root or Path.cwd()
        self.config = config or BudgetConfiguration()
        self.budget_limits = {}
        self.current_usage = {}
        self.violations = []
        self.usage_history = []

        # Initialize integrated systems
        self._init_integrated_systems()

    def _init_integrated_systems(self):
        """Initialize baseline, waiver, and drift systems."""
        try:
            from .baselines import EnhancedBaselineManager

            self.baseline_manager = EnhancedBaselineManager()
        except ImportError:
            self.baseline_manager = None

        try:
            from .waivers import EnhancedWaiverSystem

            self.waiver_system = EnhancedWaiverSystem(self.project_root)
        except ImportError:
            self.waiver_system = None

        try:
            from .drift import EnhancedDriftTracker

            self.drift_tracker = EnhancedDriftTracker(self.project_root)
        except ImportError:
            self.drift_tracker = None

    def check_baseline_aware_budget(self, current_violations: List[ConnascenceViolation]) -> Dict[str, Any]:
        """Check budget compliance with baseline awareness."""

        if self.config.mode == BudgetMode.STRICT:
            return self._check_strict_budget(current_violations)
        elif self.config.mode == BudgetMode.BASELINE:
            return self._check_baseline_budget(current_violations)
        elif self.config.mode == BudgetMode.TRENDING:
            return self._check_trending_budget(current_violations)
        else:  # ADVISORY
            return self._check_advisory_budget(current_violations)

    def _check_strict_budget(self, violations: List[ConnascenceViolation]) -> Dict[str, Any]:
        """Strict budget checking - fail on any budget violation."""

        # Apply waivers if enabled
        effective_violations = self._apply_waivers(violations) if self.config.waiver_exemptions_enabled else violations

        # Count violations by severity
        severity_counts = self._count_by_severity(effective_violations)
        total_count = len(effective_violations)

        # Check against configured budgets
        budget_violations = []

        if total_count > self.config.total_violations:
            budget_violations.append(
                {
                    "type": "total_violations",
                    "current": total_count,
                    "limit": self.config.total_violations,
                    "exceeded_by": total_count - self.config.total_violations,
                }
            )

        if severity_counts.get("critical", 0) > self.config.critical_violations:
            budget_violations.append(
                {
                    "type": "critical_violations",
                    "current": severity_counts["critical"],
                    "limit": self.config.critical_violations,
                    "exceeded_by": severity_counts["critical"] - self.config.critical_violations,
                }
            )

        if severity_counts.get("high", 0) > self.config.high_violations:
            budget_violations.append(
                {
                    "type": "high_violations",
                    "current": severity_counts["high"],
                    "limit": self.config.high_violations,
                    "exceeded_by": severity_counts["high"] - self.config.high_violations,
                }
            )

        if severity_counts.get("medium", 0) > self.config.medium_violations:
            budget_violations.append(
                {
                    "type": "medium_violations",
                    "current": severity_counts["medium"],
                    "limit": self.config.medium_violations,
                    "exceeded_by": severity_counts["medium"] - self.config.medium_violations,
                }
            )

        is_compliant = len(budget_violations) == 0

        return {
            "mode": "strict",
            "compliant": is_compliant,
            "should_fail_ci": not is_compliant and self.config.ci_fail_on_budget_exceeded,
            "budget_violations": budget_violations,
            "total_violations": total_count,
            "violations_by_severity": severity_counts,
            "waived_violations": (
                len(violations) - len(effective_violations) if self.config.waiver_exemptions_enabled else 0
            ),
        }

    def _apply_waivers(self, violations: List[ConnascenceViolation]) -> List[ConnascenceViolation]:
        """Apply waiver system to filter out waived violations."""
        if not self.waiver_system:
            return violations

        non_waived_violations = []
        for violation in violations:
            # Create fingerprint for violation (simplified)
            fingerprint = f"{getattr(violation, 'file_path', '')}-{getattr(violation, 'line_number', 0)}-{getattr(violation, 'connascence_type', '')}"

            waiver = self.waiver_system.is_violation_waived(
                violation_fingerprint=fingerprint,
                file_path=getattr(violation, "file_path", ""),
                rule_type=getattr(violation, "connascence_type", ""),
            )

            if not waiver:
                non_waived_violations.append(violation)

        return non_waived_violations

    def _count_by_severity(self, violations: List[ConnascenceViolation]) -> Dict[str, int]:
        """Count violations by severity level."""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for violation in violations:
            severity = str(getattr(violation, "severity", "medium")).lower()
            if severity in counts:
                counts[severity] += 1

        return counts

    def generate_budget_report(self, violations: List[ConnascenceViolation]) -> Dict[str, Any]:
        """Generate comprehensive budget enforcement report."""
        budget_result = self.check_baseline_aware_budget(violations)

        # Add configuration info
        budget_result["configuration"] = {
            "mode": self.config.mode.value,
            "budgets": {
                "total_violations": self.config.total_violations,
                "critical_violations": self.config.critical_violations,
                "high_violations": self.config.high_violations,
                "medium_violations": self.config.medium_violations,
                "new_violations_per_pr": self.config.new_violations_per_pr,
            },
            "features": {
                "waiver_exemptions_enabled": self.config.waiver_exemptions_enabled,
                "drift_analysis_enabled": self.config.drift_analysis_enabled,
                "ci_fail_on_budget_exceeded": self.config.ci_fail_on_budget_exceeded,
            },
        }

        # Add system availability
        budget_result["system_status"] = {
            "baseline_manager": self.baseline_manager is not None,
            "waiver_system": self.waiver_system is not None,
            "drift_tracker": self.drift_tracker is not None,
        }

        # Add recommendations
        budget_result["recommendations"] = self._generate_enhanced_recommendations(budget_result)

        return budget_result

    def _generate_enhanced_recommendations(self, budget_result: Dict[str, Any]) -> List[str]:
        """Generate enhanced recommendations based on budget analysis."""
        recommendations = []

        if not budget_result["compliant"] and budget_result["mode"] != "advisory":
            recommendations.append("🚨 Budget limits exceeded - immediate action required")

            for violation in budget_result.get("budget_violations", []):
                if violation["type"] == "new_violations":
                    recommendations.append(
                        f"Reduce new violations: {violation['current']} > {violation['limit']} (over by {violation['exceeded_by']})"
                    )
                elif violation["type"] == "total_violations":
                    recommendations.append(
                        f"Reduce total violations: {violation['current']} > {violation['limit']} (over by {violation['exceeded_by']})"
                    )
                else:
                    recommendations.append(
                        f"Address {violation['type']}: {violation['current']} > {violation['limit']}"
                    )

        # Waiver recommendations
        if budget_result.get("waived_violations", 0) > 0:
            recommendations.append(
                f"✅ {budget_result['waived_violations']} violations waived - review waiver justifications"
            )

        return recommendations


class BudgetTracker:
    """Legacy budget tracker for backward compatibility."""

    def __init__(self):
        self.budget_limits = {}
        self.current_usage = {}
        self.violations = []
        self.usage_history = []

    def set_budget_limits(self, limits: Dict[str, int]):
        """Set budget limits for different connascence types."""
        self.budget_limits = limits.copy()

    def track_violations(self, violations: List[ConnascenceViolation]):
        """Track violations against budget."""
        self.violations.extend(violations)

        # Update current usage
        self.current_usage = self._calculate_current_usage(self.violations)

        # Record usage snapshot
        self.usage_history.append(
            {"timestamp": time.time(), "usage": self.current_usage.copy(), "violation_count": len(violations)}
        )

    def check_compliance(self, violations: Optional[List[ConnascenceViolation]] = None) -> Dict[str, Any]:
        """Check if current violations comply with budget."""
        if violations is None:
            violations = self.violations

        usage = self._calculate_current_usage(violations)
        compliance_status = {}

        for budget_type, limit in self.budget_limits.items():
            if budget_type == "total_violations":
                current_usage = len(violations)  # Total count for total_violations
            else:
                current_usage = usage.get(budget_type, 0)
            is_compliant = current_usage <= limit
            compliance_status[budget_type] = {
                "limit": limit,
                "usage": current_usage,
                "compliant": is_compliant,
                "remaining": max(0, limit - current_usage),
            }

        overall_compliant = all(status["compliant"] for status in compliance_status.values())

        # Calculate which budget types are violated
        violations_list = []
        for budget_type, status in compliance_status.items():
            if not status["compliant"]:
                violations_list.append(budget_type)

        # Also check total violations limit
        total_violations_limit = self.budget_limits.get("total_violations", float("inf"))
        if len(violations) > total_violations_limit:
            violations_list.append("total_violations")

        return {
            "overall_compliant": overall_compliant,
            "compliant": overall_compliant,  # For backwards compatibility
            "budget_status": compliance_status,
            "total_violations": len(violations),
            "violations": violations_list,  # List of violated budget types
        }

    def get_budget_report(self) -> Dict[str, Any]:
        """Get comprehensive budget usage report."""
        compliance = self.check_compliance()

        # Calculate utilization percentages
        utilization = {}
        for budget_type, limit in self.budget_limits.items():
            current_usage = self.current_usage.get(budget_type, 0)
            utilization[budget_type] = current_usage / limit if limit > 0 else 0

        return {
            "budget_limits": self.budget_limits,
            "current_usage": self.current_usage,
            "utilization": utilization,
            "compliance_status": compliance["budget_status"],
            "current_compliance": compliance,
            "usage_history": self.usage_history[-DEFAULT_USAGE_HISTORY_LIMIT:],  # Last N entries
            "recommendations": self._generate_recommendations(compliance),
        }

    def _calculate_current_usage(self, violations: List[ConnascenceViolation]) -> Dict[str, int]:
        """Calculate current usage by connascence type and severity."""
        usage = {"total_violations": len(violations)}

        # Count by connascence type
        for violation in violations:
            conn_type = getattr(violation, "connascence_type", "unknown")
            usage[conn_type] = usage.get(conn_type, 0) + 1

            # Count by severity
            severity = getattr(violation, "severity", "medium")
            usage[severity] = usage.get(severity, 0) + 1

        return usage

    def _generate_recommendations(self, compliance: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on budget status."""
        recommendations = []

        if not compliance["overall_compliant"]:
            recommendations.append("Budget limits exceeded - consider refactoring")

            for budget_type, status in compliance["budget_status"].items():
                if not status["compliant"]:
                    recommendations.append(f"Reduce {budget_type} violations by {status['usage'] - status['limit']}")

        return recommendations

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive budget report (alias for get_budget_report)."""
        return self.get_budget_report()

    def reset(self):
        """Reset tracked violations and usage."""
        self.violations = []
        self.current_usage = {}
        self.usage_history = []


class BudgetStatus:
    def __init__(self, compliant: bool, details: Dict[str, Any]):
        self.compliant = compliant
        self.details = details


class BudgetExceededException(Exception):
    def __init__(self, budget_type: str, current: int, limit: int):
        self.budget_type = budget_type
        self.current = current
        self.limit = limit
        super().__init__(f"Budget exceeded for {budget_type}: {current} > {limit}")
