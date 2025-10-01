# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
Violation Aggregator - Result Processing and Aggregation
========================================================

Extracted from UnifiedConnascenceAnalyzer's god object.
NASA Rule 4 Compliant: Functions under 60 lines.
Handles violation formatting, standardization, and metrics coordination.
"""

from datetime import datetime
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ViolationAggregator:
    """Aggregates and processes analysis results with standardization."""

    def __init__(self):
        """Initialize aggregator with minimal state."""
        self.aggregation_metadata = {}

    def build_unified_result(
        self,
        violations: Dict[str, Any],
        metrics: Dict[str, Any],
        recommendations: Dict[str, Any],
        project_path: Path,
        policy_preset: str,
        analysis_time: int,
        errors: Optional[List] = None,
        warnings: Optional[List] = None,
    ) -> Dict[str, Any]:
        """
        Build unified analysis result with comprehensive aggregation.
        NASA Rule 4 Compliant: Under 60 lines.
        """
        # NASA Rule 5: Input validation assertions
        assert violations is not None, "violations cannot be None"
        assert metrics is not None, "metrics cannot be None"
        assert project_path is not None, "project_path cannot be None"
        assert analysis_time >= 0, "analysis_time must be non-negative"

        # Process and standardize violations
        standardized_violations = self._standardize_violations(violations)

        # Enhance recommendations with metadata
        enhanced_recommendations = self._enhance_recommendations(violations, recommendations)

        # Build result object
        result = self._create_result_structure(
            standardized_violations,
            metrics,
            enhanced_recommendations,
            project_path,
            policy_preset,
            analysis_time,
            errors,
            warnings,
        )

        # Add enhanced metadata
        self._add_metadata_to_result(result, violations, enhanced_recommendations)

        return result

    def _standardize_violations(self, violations: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize violations format. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation
        assert violations is not None, "violations cannot be None"

        standardized = {
            "connascence": self._standardize_connascence_violations(violations.get("connascence", [])),
            "duplication": self._standardize_duplication_violations(violations.get("duplication", [])),
            "nasa": self._standardize_nasa_violations(violations.get("nasa", [])),
        }

        # Preserve metadata if present
        if "_metadata" in violations:
            standardized["_metadata"] = violations["_metadata"]

        return standardized

    def _standardize_connascence_violations(self, violations: List[Dict]) -> List[Dict]:
        """Standardize connascence violation format. NASA Rule 4 compliant."""
        standardized_violations = []

        for violation in violations:
            standardized = self._create_standard_violation_format(violation, "connascence")
            standardized_violations.append(standardized)

        return standardized_violations

    def _standardize_duplication_violations(self, violations: List[Dict]) -> List[Dict]:
        """Standardize duplication violation format. NASA Rule 4 compliant."""
        standardized_violations = []

        for violation in violations:
            standardized = self._create_standard_violation_format(violation, "duplication")
            standardized_violations.append(standardized)

        return standardized_violations

    def _standardize_nasa_violations(self, violations: List[Dict]) -> List[Dict]:
        """Standardize NASA violation format. NASA Rule 4 compliant."""
        standardized_violations = []

        for violation in violations:
            standardized = self._create_standard_violation_format(violation, "nasa_compliance")
            # Add NASA-specific context
            standardized = self._add_nasa_context(standardized, violation)
            standardized_violations.append(standardized)

        return standardized_violations

    def _create_standard_violation_format(self, violation: Dict, category: str) -> Dict[str, Any]:
        """Create standard violation format. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation
        assert violation is not None, "violation cannot be None"
        assert category is not None, "category cannot be None"

        return {
            "id": violation.get("id", self._generate_violation_id(violation)),
            "rule_id": violation.get("rule_id", f"{category.upper()}_UNKNOWN"),
            "type": violation.get("type", "unknown"),
            "category": category,
            "severity": self._normalize_severity(violation.get("severity", "medium")),
            "description": violation.get("description", f"{category} violation detected"),
            "file_path": violation.get("file_path", ""),
            "line_number": violation.get("line_number", 0),
            "column": violation.get("column", 0),
            "weight": self._calculate_violation_weight(violation),
            "context": violation.get("context", {}),
            "standardized_at": self._get_iso_timestamp(),
        }

    def _add_nasa_context(self, standardized: Dict, original: Dict) -> Dict[str, Any]:
        """Add NASA-specific context to violation. NASA Rule 4 compliant."""
        nasa_context = {
            "nasa_rule": original.get("context", {}).get("nasa_rule", "unknown"),
            "violation_type": original.get("context", {}).get("violation_type", "unknown"),
            "recommendation": original.get("context", {}).get("recommendation", ""),
            "compliance_impact": self._calculate_compliance_impact(original),
        }

        standardized["context"].update(nasa_context)
        return standardized

    def _enhance_recommendations(self, violations: Dict, recommendations: Dict) -> Dict[str, Any]:
        """Enhance recommendations with violation metadata. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation
        assert violations is not None, "violations cannot be None"
        assert recommendations is not None, "recommendations cannot be None"

        enhanced = recommendations.copy()
        phase_metadata = violations.get("_metadata", {})

        # Add smart integration results
        if phase_metadata.get("smart_results"):
            enhanced = self._integrate_smart_recommendations(enhanced, phase_metadata["smart_results"])

        # Add correlation-based recommendations
        if phase_metadata.get("correlations"):
            enhanced = self._add_correlation_recommendations(enhanced, phase_metadata["correlations"])

        return enhanced

    def _integrate_smart_recommendations(self, enhanced: Dict, smart_results: Dict) -> Dict:
        """Integrate smart analysis recommendations. NASA Rule 4 compliant."""
        if smart_results.get("enhanced_recommendations"):
            enhanced["smart_recommendations"] = smart_results["enhanced_recommendations"]

        if smart_results.get("correlations"):
            enhanced["correlations"] = smart_results["correlations"]

        enhanced["smart_integration_enabled"] = True
        return enhanced

    def _add_correlation_recommendations(self, enhanced: Dict, correlations: List) -> Dict:
        """Add correlation-based recommendations. NASA Rule 4 compliant."""
        if correlations:
            correlation_actions = [
                f"Review correlated violations in {correlation.get('files', ['unknown'])[0]}"
                for correlation in correlations[:3]  # Top 3 correlations
            ]
            enhanced["correlation_actions"] = correlation_actions

        return enhanced

    def _create_result_structure(
        self,
        violations: Dict,
        metrics: Dict,
        recommendations: Dict,
        project_path: Path,
        policy_preset: str,
        analysis_time: int,
        errors: Optional[List],
        warnings: Optional[List],
    ) -> Dict[str, Any]:
        """Create result structure. NASA Rule 4 compliant."""
        return {
            "connascence_violations": violations["connascence"],
            "duplication_clusters": violations["duplication"],
            "nasa_violations": violations["nasa"],
            "total_violations": metrics["total_violations"],
            "critical_count": metrics["critical_count"],
            "high_count": metrics["high_count"],
            "medium_count": metrics["medium_count"],
            "low_count": metrics["low_count"],
            "connascence_index": metrics["connascence_index"],
            "nasa_compliance_score": metrics["nasa_compliance_score"],
            "duplication_score": metrics["duplication_score"],
            "overall_quality_score": metrics["overall_quality_score"],
            "project_path": str(project_path),
            "policy_preset": policy_preset,
            "analysis_duration_ms": analysis_time,
            "files_analyzed": self._count_analyzed_files(violations),
            "timestamp": self._get_iso_timestamp(),
            "priority_fixes": recommendations["priority_fixes"],
            "improvement_actions": recommendations["improvement_actions"],
            "errors": errors or [],
            "warnings": warnings or [],
        }

    def _add_metadata_to_result(self, result: Dict, violations: Dict, recommendations: Dict) -> None:
        """Add enhanced metadata to result. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation
        assert result is not None, "result cannot be None"
        assert violations is not None, "violations cannot be None"

        phase_metadata = violations.get("_metadata", {})

        # Add audit trail and correlation data
        result["audit_trail"] = phase_metadata.get("audit_trail", [])
        result["correlations"] = phase_metadata.get("correlations", [])
        result["smart_recommendations"] = recommendations.get("smart_recommendations", [])
        result["cross_phase_analysis"] = phase_metadata.get("smart_results", {}).get("cross_phase_analysis", False)

        # Add aggregation metadata
        result["aggregation_metadata"] = {
            "standardized_at": self._get_iso_timestamp(),
            "aggregation_version": "1.0",
            "violations_processed": self._count_total_violations(violations),
        }

    def _generate_violation_id(self, violation: Dict) -> str:
        """Generate unique violation ID. NASA Rule 4 compliant."""
        base = f"{violation.get('type', 'unknown')}_{violation.get('line_number', 0)}"
        return f"violation_{hash(str(violation)) % 100000}_{base}"

    def _normalize_severity(self, severity: str) -> str:
        """Normalize severity levels. NASA Rule 4 compliant."""
        severity_mapping = {
            "critical": "critical",
            "high": "high",
            "medium": "medium",
            "low": "low",
            "error": "high",
            "warning": "medium",
            "info": "low",
        }
        return severity_mapping.get(severity.lower(), "medium")

    def _calculate_violation_weight(self, violation: Dict) -> float:
        """Calculate violation weight. NASA Rule 4 compliant."""
        severity = violation.get("severity", "medium")
        weight_map = {"critical": 10.0, "high": 5.0, "medium": 2.0, "low": 1.0}
        base_weight = weight_map.get(severity, 2.0)

        # Add context-based weight adjustments
        context_weight = violation.get("context", {}).get("weight_modifier", 1.0)
        return base_weight * context_weight

    def _calculate_compliance_impact(self, violation: Dict) -> str:
        """Calculate NASA compliance impact. NASA Rule 4 compliant."""
        severity = violation.get("severity", "medium")
        nasa_rule = violation.get("context", {}).get("nasa_rule", "unknown")

        if severity == "critical":
            return "high_impact"
        elif nasa_rule in ["Rule1", "Rule2", "Rule3"]:  # Critical NASA rules
            return "medium_impact"
        else:
            return "low_impact"

    def _count_analyzed_files(self, violations: Dict) -> int:
        """Count number of analyzed files. NASA Rule 4 compliant."""
        file_paths = set()

        for category in ["connascence", "duplication", "nasa"]:
            for violation in violations.get(category, []):
                if violation.get("file_path"):
                    file_paths.add(violation["file_path"])

        return len(file_paths)

    def _count_total_violations(self, violations: Dict) -> int:
        """Count total violations across categories. NASA Rule 4 compliant."""
        return (
            len(violations.get("connascence", []))
            + len(violations.get("duplication", []))
            + len(violations.get("nasa", []))
        )

    def _get_iso_timestamp(self) -> str:
        """Get current timestamp in ISO format. NASA Rule 4 compliant."""
        return datetime.now().isoformat()

    def get_aggregation_stats(self) -> Dict[str, Any]:
        """Get aggregation statistics."""
        return self.aggregation_metadata.copy()
