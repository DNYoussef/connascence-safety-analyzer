# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
Recommendation Engine - Intelligent Analysis Suggestions
========================================================

Extracted from UnifiedConnascenceAnalyzer's god object.
NASA Rule 4 Compliant: Functions under 60 lines.
Handles action prioritization, NASA/connascence/duplication-specific recommendations.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Generates intelligent improvement recommendations with priority analysis."""

    def __init__(self):
        """Initialize recommendation engine with rule mappings."""
        self.priority_rules = self._initialize_priority_rules()
        self.recommendation_cache = {}

    def generate_unified_recommendations(
        self,
        connascence_violations: List[Dict[str, Any]],
        duplication_clusters: List[Dict[str, Any]],
        nasa_violations: List[Dict[str, Any]],
        nasa_integration=None,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive improvement recommendations.
        NASA Rule 4 Compliant: Under 60 lines.
        """
        # NASA Rule 5: Input validation assertions
        assert connascence_violations is not None, "connascence_violations cannot be None"
        assert duplication_clusters is not None, "duplication_clusters cannot be None"
        assert nasa_violations is not None, "nasa_violations cannot be None"

        recommendations = {
            "priority_fixes": [],
            "improvement_actions": [],
            "strategic_suggestions": [],
            "technical_debt_actions": [],
        }

        # Generate priority fixes for critical violations
        recommendations["priority_fixes"] = self._generate_priority_fixes(connascence_violations, nasa_violations)

        # Generate improvement actions by category
        recommendations["improvement_actions"].extend(self._generate_nasa_actions(nasa_violations, nasa_integration))
        recommendations["improvement_actions"].extend(self._generate_duplication_actions(duplication_clusters))
        recommendations["improvement_actions"].extend(self._generate_connascence_actions(connascence_violations))

        # Generate strategic suggestions
        recommendations["strategic_suggestions"] = self._generate_strategic_suggestions(
            connascence_violations, duplication_clusters, nasa_violations
        )

        return recommendations

    def _initialize_priority_rules(self) -> Dict[str, Dict]:
        """Initialize priority classification rules. NASA Rule 4 compliant."""
        return {
            "critical_nasa_rules": ["Rule1", "Rule2", "Rule3", "Rule4"],  # NASA Power of Ten critical rules
            "high_impact_connascence": ["CoP", "CoE", "CoT"],  # Position, Execution, Timing
            "medium_impact_connascence": ["CoI", "CoA", "CoN"],  # Identity, Algorithm, Name
            "refactoring_priorities": {
                "god_object": 10,
                "long_function": 8,
                "complex_condition": 6,
                "duplication": 7,
            },
        }

    def _generate_priority_fixes(self, connascence_violations: List[Dict], nasa_violations: List[Dict]) -> List[str]:
        """Generate priority fixes for critical violations. NASA Rule 4 compliant."""
        priority_fixes = []

        # Critical NASA violations (highest priority)
        critical_nasa = [v for v in nasa_violations if v.get("severity") == "critical"]
        for violation in critical_nasa[:2]:  # Top 2 critical NASA
            fix = self._create_nasa_priority_fix(violation)
            if fix:
                priority_fixes.append(fix)

        # Critical connascence violations
        critical_connascence = [v for v in connascence_violations if v.get("severity") == "critical"]
        for violation in critical_connascence[:3]:  # Top 3 critical connascence
            fix = self._create_connascence_priority_fix(violation)
            if fix:
                priority_fixes.append(fix)

        return priority_fixes

    def _create_nasa_priority_fix(self, violation: Dict) -> Optional[str]:
        """Create NASA-specific priority fix. NASA Rule 4 compliant."""
        nasa_rule = violation.get("context", {}).get("nasa_rule", "unknown")
        file_path = violation.get("file_path", "unknown file")
        line_number = violation.get("line_number", 0)

        nasa_fix_templates = {
            "Rule1": "Eliminate goto statement",
            "Rule2": "Limit recursion depth",
            "Rule3": "Remove dynamic memory allocation",
            "Rule4": "Reduce function length to <60 lines",
            "Rule5": "Add assertion for input validation",
        }

        template = nasa_fix_templates.get(nasa_rule, f"Fix NASA {nasa_rule} violation")
        return f"CRITICAL: {template} in {file_path}:{line_number}"

    def _create_connascence_priority_fix(self, violation: Dict) -> Optional[str]:
        """Create connascence-specific priority fix. NASA Rule 4 compliant."""
        connascence_type = violation.get("type", "unknown")
        file_path = violation.get("file_path", "unknown file")
        line_number = violation.get("line_number", 0)

        connascence_fix_templates = {
            "CoP": "Fix position dependency - reorder parameters",
            "CoE": "Fix execution dependency - remove shared state",
            "CoT": "Fix timing dependency - add synchronization",
            "CoI": "Fix identity dependency - use value comparison",
            "CoA": "Fix algorithm dependency - standardize implementation",
            "CoN": "Fix naming dependency - use consistent naming",
            "CoM": "Fix meaning dependency - replace magic numbers with constants",
        }

        template = connascence_fix_templates.get(connascence_type, f"Fix {connascence_type} violation")
        return f"HIGH: {template} in {file_path}:{line_number}"

    def _generate_nasa_actions(self, nasa_violations: List[Dict], nasa_integration=None) -> List[str]:
        """Generate NASA compliance improvement actions. NASA Rule 4 compliant."""
        if not nasa_violations:
            return []

        actions = []

        # Use NASA integration for intelligent recommendations
        if nasa_integration:
            try:
                intelligent_actions = nasa_integration.get_nasa_compliance_actions(nasa_violations)
                actions.extend(intelligent_actions[:3])  # Top 3 NASA actions
            except Exception as e:
                logger.warning(f"NASA integration failed: {e}")

        # Fallback to rule-based recommendations
        if not actions:
            actions = self._generate_fallback_nasa_actions(nasa_violations)

        return actions

    def _generate_fallback_nasa_actions(self, nasa_violations: List[Dict]) -> List[str]:
        """Generate fallback NASA actions. NASA Rule 4 compliant."""
        actions = []
        rule_counts = {}

        # Count violations by NASA rule
        for violation in nasa_violations:
            nasa_rule = violation.get("context", {}).get("nasa_rule", "unknown")
            rule_counts[nasa_rule] = rule_counts.get(nasa_rule, 0) + 1

        # Generate actions for most frequent rules
        for rule, count in sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[:3]:
            action = f"Address {count} violations of NASA {rule} - {self._get_nasa_rule_description(rule)}"
            actions.append(action)

        return actions

    def _generate_duplication_actions(self, duplication_clusters: List[Dict]) -> List[str]:
        """Generate duplication reduction actions. NASA Rule 4 compliant."""
        if not duplication_clusters:
            return []

        actions = []

        # Analyze duplication patterns
        high_similarity_clusters = [c for c in duplication_clusters if c.get("similarity_score", 0) > 0.8]

        if high_similarity_clusters:
            actions.append(
                f"Refactor {len(high_similarity_clusters)} high-similarity duplication clusters (>80% similar)"
            )

        # Overall duplication strategy
        if len(duplication_clusters) > 5:
            actions.append(f"Implement systematic deduplication strategy for {len(duplication_clusters)} clusters")

        return actions

    def _generate_connascence_actions(self, connascence_violations: List[Dict]) -> List[str]:
        """Generate connascence improvement actions. NASA Rule 4 compliant."""
        if not connascence_violations:
            return []

        actions = []

        # Analyze by connascence type
        type_counts = {}
        for violation in connascence_violations:
            conn_type = violation.get("type", "unknown")
            type_counts[conn_type] = type_counts.get(conn_type, 0) + 1

        # Generate actions for most frequent types
        for conn_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:3]:
            description = self._get_connascence_description(conn_type)
            actions.append(f"Reduce {count} instances of {conn_type} - {description}")

        return actions

    def _generate_strategic_suggestions(
        self, connascence_violations: List[Dict], duplication_clusters: List[Dict], nasa_violations: List[Dict]
    ) -> List[str]:
        """Generate high-level strategic suggestions. NASA Rule 4 compliant."""
        suggestions = []
        total_violations = len(connascence_violations) + len(duplication_clusters) + len(nasa_violations)

        # Architecture-level suggestions
        if total_violations > 50:
            suggestions.append("Consider architectural refactoring to reduce overall coupling")

        if len(nasa_violations) > 10:
            suggestions.append("Implement NASA Power of Ten compliance review process")

        if len(duplication_clusters) > 15:
            suggestions.append("Establish code reuse patterns and shared libraries")

        # Quality gate suggestions
        critical_violations = self._count_critical_violations(connascence_violations, nasa_violations)
        if critical_violations > 5:
            suggestions.append("Implement pre-commit hooks to prevent critical violations")

        return suggestions

    def _get_nasa_rule_description(self, rule: str) -> str:
        """Get NASA rule description. NASA Rule 4 compliant."""
        descriptions = {
            "Rule1": "avoid goto statements",
            "Rule2": "limit recursion and dynamic calls",
            "Rule3": "avoid dynamic memory allocation",
            "Rule4": "limit function length to 60 lines",
            "Rule5": "use assertions for parameter validation",
            "Rule6": "declare variables at smallest scope",
            "Rule7": "check return values",
            "Rule8": "limit preprocessor use",
            "Rule9": "limit pointer use",
            "Rule10": "compile with all warnings enabled",
        }
        return descriptions.get(rule, "unknown rule")

    def _get_connascence_description(self, connascence_type: str) -> str:
        """Get connascence type description. NASA Rule 4 compliant."""
        descriptions = {
            "CoN": "use consistent naming patterns",
            "CoT": "reduce shared mutable state",
            "CoL": "minimize literal value dependencies",
            "CoM": "replace magic numbers with constants",
            "CoA": "standardize algorithms across modules",
            "CoE": "remove execution order dependencies",
            "CoT": "eliminate timing dependencies",
            "CoV": "reduce shared value dependencies",
            "CoI": "use value equality instead of identity",
            "CoP": "minimize parameter position dependencies",
        }
        return descriptions.get(connascence_type, "reduce coupling")

    def _count_critical_violations(self, connascence_violations: List[Dict], nasa_violations: List[Dict]) -> int:
        """Count critical violations. NASA Rule 4 compliant."""
        critical_count = 0

        # Count critical connascence violations
        critical_count += len([v for v in connascence_violations if v.get("severity") == "critical"])

        # Count critical NASA violations
        critical_count += len([v for v in nasa_violations if v.get("severity") == "critical"])

        return critical_count

    def generate_file_specific_recommendations(self, file_path: str, violations: List[Dict]) -> List[str]:
        """Generate file-specific recommendations. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation
        assert file_path is not None, "file_path cannot be None"
        assert violations is not None, "violations cannot be None"

        recommendations = []

        # Check cache first
        cache_key = f"{file_path}_{len(violations)}"
        if cache_key in self.recommendation_cache:
            return self.recommendation_cache[cache_key]

        # Group violations by type for file-specific advice
        type_groups = {}
        for violation in violations:
            v_type = violation.get("type", "unknown")
            if v_type not in type_groups:
                type_groups[v_type] = []
            type_groups[v_type].append(violation)

        # Generate file-specific recommendations
        for v_type, group_violations in type_groups.items():
            if len(group_violations) > 3:  # Multiple instances of same type
                rec = f"File has {len(group_violations)} {v_type} violations - consider refactoring patterns"
                recommendations.append(rec)

        # Cache and return
        self.recommendation_cache[cache_key] = recommendations
        return recommendations

    def clear_cache(self) -> None:
        """Clear recommendation cache."""
        self.recommendation_cache.clear()

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {"cached_recommendations": len(self.recommendation_cache)}
