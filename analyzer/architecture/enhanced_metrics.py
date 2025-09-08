# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
Enhanced Metrics Calculator - Quality Score and Performance Metrics
===================================================================

Extracted from UnifiedConnascenceAnalyzer's god object.
NASA Rule 4 Compliant: Functions under 60 lines.
Handles quality score calculations, performance tracking, and compliance scoring.
"""

import logging
import time
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EnhancedMetricsCalculator:
    """Calculates comprehensive quality metrics with performance tracking."""

    def __init__(self):
        """Initialize metrics calculator with performance tracking."""
        self.calculation_history = []
        self.performance_metrics = {}
        self.baseline_metrics = None

    def calculate_comprehensive_metrics(
        self,
        connascence_violations: List[Dict[str, Any]],
        duplication_clusters: List[Dict[str, Any]],
        nasa_violations: List[Dict[str, Any]],
        nasa_integration=None,
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive quality metrics with performance tracking.
        NASA Rule 4 Compliant: Under 60 lines.
        """
        # NASA Rule 5: Input validation assertions
        assert connascence_violations is not None, "connascence_violations cannot be None"
        assert duplication_clusters is not None, "duplication_clusters cannot be None"
        assert nasa_violations is not None, "nasa_violations cannot be None"

        start_time = time.time()
        
        # Calculate base metrics
        all_violations = connascence_violations + duplication_clusters
        severity_counts = self._count_by_severity(all_violations)
        
        # Calculate individual scores with performance tracking
        connascence_index = self._calculate_connascence_index_enhanced(connascence_violations)
        nasa_compliance_score = self._calculate_nasa_score_enhanced(nasa_violations, nasa_integration)
        duplication_score = self._calculate_duplication_score_enhanced(duplication_clusters)
        
        # Calculate overall quality with weighting
        overall_quality_score = self._calculate_weighted_quality_score(
            connascence_index, nasa_compliance_score, duplication_score
        )
        
        # Performance and trend analysis
        performance_score = self._calculate_performance_score(start_time)
        trend_analysis = self._analyze_metrics_trends(severity_counts)
        
        metrics = self._build_metrics_result(
            severity_counts, connascence_index, nasa_compliance_score, 
            duplication_score, overall_quality_score, performance_score, trend_analysis
        )
        
        self._record_calculation_history(metrics, time.time() - start_time)
        return metrics

    def _count_by_severity(self, violations: List[Dict]) -> Dict[str, int]:
        """Count violations by severity with enhanced categorization. NASA Rule 4 compliant."""
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        
        for violation in violations:
            severity = self._normalize_severity(violation.get("severity", "medium"))
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        # Add derived metrics
        severity_counts["total"] = sum(severity_counts.values())
        severity_counts["high_priority"] = severity_counts["critical"] + severity_counts["high"]
        
        return severity_counts

    def _calculate_connascence_index_enhanced(self, connascence_violations: List[Dict]) -> float:
        """Calculate enhanced connascence index with type weighting. NASA Rule 4 compliant."""
        if not connascence_violations:
            return 0.0

        # Enhanced weight mapping with connascence type considerations
        severity_weights = {"critical": 10, "high": 5, "medium": 2, "low": 1, "info": 0.5}
        type_multipliers = {
            "CoE": 2.0,  # Execution - highest impact
            "CoT": 1.8,  # Timing - high impact
            "CoP": 1.6,  # Position - medium-high impact
            "CoI": 1.4,  # Identity - medium impact
            "CoA": 1.2,  # Algorithm - medium impact
            "CoN": 1.0,  # Name - baseline
            "CoM": 0.8,  # Meaning - lower impact
            "CoL": 0.6,  # Literal - lowest impact
        }

        total_weighted_score = 0.0
        for violation in connascence_violations:
            severity_weight = severity_weights.get(violation.get("severity", "medium"), 2)
            type_multiplier = type_multipliers.get(violation.get("type", "CoN"), 1.0)
            violation_weight = violation.get("weight", 1.0)
            
            total_weighted_score += severity_weight * type_multiplier * violation_weight

        return round(total_weighted_score, 2)

    def _calculate_nasa_score_enhanced(self, nasa_violations: List[Dict], nasa_integration=None) -> float:
        """Calculate enhanced NASA compliance score. NASA Rule 4 compliant."""
        if nasa_integration:
            try:
                base_score = nasa_integration.calculate_nasa_compliance_score(nasa_violations)
                return self._enhance_nasa_score_with_context(base_score, nasa_violations)
            except Exception as e:
                logger.warning(f"NASA integration scoring failed: {e}")

        # Enhanced fallback calculation
        return self._calculate_fallback_nasa_score(nasa_violations)

    def _enhance_nasa_score_with_context(self, base_score: float, nasa_violations: List[Dict]) -> float:
        """Enhance NASA score with contextual factors. NASA Rule 4 compliant."""
        if not nasa_violations:
            return base_score

        # Apply penalties for critical NASA rules
        critical_rule_penalty = 0.0
        critical_rules = ["Rule1", "Rule2", "Rule3", "Rule4"]  # Most critical rules
        
        for violation in nasa_violations:
            nasa_rule = violation.get("context", {}).get("nasa_rule", "")
            if nasa_rule in critical_rules and violation.get("severity") == "critical":
                critical_rule_penalty += 0.1

        enhanced_score = max(0.0, base_score - critical_rule_penalty)
        return round(enhanced_score, 3)

    def _calculate_fallback_nasa_score(self, nasa_violations: List[Dict]) -> float:
        """Calculate fallback NASA score with rule weighting. NASA Rule 4 compliant."""
        if not nasa_violations:
            return 1.0

        # Rule weights based on safety criticality
        rule_weights = {
            "Rule1": 0.15,  # Goto - highly critical
            "Rule2": 0.12,  # Recursion - critical
            "Rule3": 0.12,  # Memory allocation - critical
            "Rule4": 0.10,  # Function length - important
            "Rule5": 0.08,  # Assertions - important
        }

        total_penalty = 0.0
        for violation in nasa_violations:
            nasa_rule = violation.get("context", {}).get("nasa_rule", "Rule10")
            penalty = rule_weights.get(nasa_rule, 0.05)  # Default penalty
            
            # Adjust penalty by severity
            severity_multiplier = {"critical": 2.0, "high": 1.5, "medium": 1.0, "low": 0.5}.get(
                violation.get("severity", "medium"), 1.0
            )
            
            total_penalty += penalty * severity_multiplier

        score = max(0.0, 1.0 - total_penalty)
        return round(score, 3)

    def _calculate_duplication_score_enhanced(self, duplication_clusters: List[Dict]) -> float:
        """Calculate enhanced duplication score with similarity weighting. NASA Rule 4 compliant."""
        if not duplication_clusters:
            return 1.0

        total_penalty = 0.0
        for cluster in duplication_clusters:
            # Base penalty
            base_penalty = 0.05
            
            # Adjust by similarity score
            similarity_score = cluster.get("similarity_score", 0.5)
            similarity_multiplier = similarity_score  # Higher similarity = higher penalty
            
            # Adjust by cluster size
            functions = cluster.get("functions", [])
            size_multiplier = min(len(functions) / 5.0, 2.0)  # Cap at 2x penalty
            
            cluster_penalty = base_penalty * similarity_multiplier * size_multiplier
            total_penalty += cluster_penalty

        score = max(0.0, 1.0 - total_penalty)
        return round(score, 3)

    def _calculate_weighted_quality_score(
        self, connascence_index: float, nasa_compliance_score: float, duplication_score: float
    ) -> float:
        """Calculate weighted overall quality score. NASA Rule 4 compliant."""
        # Dynamic weights based on project characteristics
        weights = self._calculate_dynamic_weights(connascence_index, nasa_compliance_score, duplication_score)
        
        # Convert connascence index to score (0-1 range)
        connascence_score = max(0.0, 1.0 - (connascence_index * 0.01))
        
        overall_score = (
            connascence_score * weights["connascence"] +
            nasa_compliance_score * weights["nasa"] +
            duplication_score * weights["duplication"]
        )
        
        return round(overall_score, 3)

    def _calculate_dynamic_weights(
        self, connascence_index: float, nasa_score: float, duplication_score: float
    ) -> Dict[str, float]:
        """Calculate dynamic weights based on current metrics. NASA Rule 4 compliant."""
        base_weights = {"connascence": 0.4, "nasa": 0.3, "duplication": 0.3}
        
        # Adjust weights based on problem areas
        if nasa_score < 0.5:  # Poor NASA compliance
            base_weights["nasa"] += 0.1
            base_weights["connascence"] -= 0.05
            base_weights["duplication"] -= 0.05
        
        if duplication_score < 0.5:  # High duplication
            base_weights["duplication"] += 0.1
            base_weights["connascence"] -= 0.05
            base_weights["nasa"] -= 0.05
        
        return base_weights

    def _calculate_performance_score(self, start_time: float) -> Dict[str, Any]:
        """Calculate performance metrics for this calculation. NASA Rule 4 compliant."""
        calculation_time = time.time() - start_time
        
        performance_score = {
            "calculation_time_ms": round(calculation_time * 1000, 2),
            "performance_rating": self._get_performance_rating(calculation_time),
            "timestamp": self._get_iso_timestamp(),
        }
        
        # Track performance trends
        self.performance_metrics[self._get_iso_timestamp()] = calculation_time
        
        return performance_score

    def _analyze_metrics_trends(self, current_severity_counts: Dict[str, int]) -> Dict[str, Any]:
        """Analyze trends in metrics over time. NASA Rule 4 compliant."""
        if not self.calculation_history:
            return {"trend": "initial", "change": "none"}

        # Compare with last calculation
        last_calculation = self.calculation_history[-1]
        last_counts = last_calculation.get("severity_counts", {})
        
        trend_analysis = {
            "total_change": current_severity_counts.get("total", 0) - last_counts.get("total", 0),
            "critical_change": current_severity_counts.get("critical", 0) - last_counts.get("critical", 0),
            "trend_direction": "stable"
        }
        
        # Determine trend direction
        if trend_analysis["total_change"] > 5:
            trend_analysis["trend_direction"] = "worsening"
        elif trend_analysis["total_change"] < -5:
            trend_analysis["trend_direction"] = "improving"
        
        return trend_analysis

    def _build_metrics_result(
        self, severity_counts: Dict, connascence_index: float, nasa_score: float,
        duplication_score: float, overall_score: float, performance: Dict, trends: Dict
    ) -> Dict[str, Any]:
        """Build comprehensive metrics result. NASA Rule 4 compliant."""
        return {
            "total_violations": severity_counts["total"],
            "critical_count": severity_counts["critical"],
            "high_count": severity_counts["high"],
            "medium_count": severity_counts["medium"],
            "low_count": severity_counts["low"],
            "info_count": severity_counts["info"],
            "high_priority_count": severity_counts["high_priority"],
            "connascence_index": connascence_index,
            "nasa_compliance_score": nasa_score,
            "duplication_score": duplication_score,
            "overall_quality_score": overall_score,
            "performance_metrics": performance,
            "trend_analysis": trends,
            "calculation_timestamp": self._get_iso_timestamp(),
        }

    def _record_calculation_history(self, metrics: Dict[str, Any], calculation_time: float) -> None:
        """Record calculation in history for trend analysis. NASA Rule 4 compliant."""
        history_record = {
            "timestamp": self._get_iso_timestamp(),
            "calculation_time": calculation_time,
            "severity_counts": {
                "total": metrics["total_violations"],
                "critical": metrics["critical_count"],
                "high": metrics["high_count"],
            },
            "quality_scores": {
                "overall": metrics["overall_quality_score"],
                "nasa": metrics["nasa_compliance_score"],
                "duplication": metrics["duplication_score"],
            }
        }
        
        self.calculation_history.append(history_record)
        
        # Keep only last 10 calculations for trend analysis
        if len(self.calculation_history) > 10:
            self.calculation_history.pop(0)

    def _normalize_severity(self, severity: str) -> str:
        """Normalize severity levels. NASA Rule 4 compliant."""
        severity_mapping = {
            "critical": "critical",
            "high": "high",
            "medium": "medium",
            "low": "low",
            "info": "info",
            "error": "high",
            "warning": "medium",
            "notice": "low",
        }
        return severity_mapping.get(severity.lower(), "medium")

    def _get_performance_rating(self, calculation_time: float) -> str:
        """Get performance rating based on calculation time. NASA Rule 4 compliant."""
        if calculation_time < 1.0:
            return "excellent"
        elif calculation_time < 5.0:
            return "good"
        elif calculation_time < 15.0:
            return "acceptable"
        else:
            return "poor"

    def _get_iso_timestamp(self) -> str:
        """Get current timestamp in ISO format. NASA Rule 4 compliant."""
        return datetime.now().isoformat()

    def set_baseline_metrics(self, metrics: Dict[str, Any]) -> None:
        """Set baseline metrics for comparison."""
        self.baseline_metrics = metrics.copy()
        logger.info("Baseline metrics established")

    def get_calculation_history(self) -> List[Dict[str, Any]]:
        """Get calculation history for analysis."""
        return self.calculation_history.copy()

    def get_performance_trends(self) -> Dict[str, Any]:
        """Get performance trend analysis."""
        if not self.performance_metrics:
            return {"trend": "no_data"}
        
        times = list(self.performance_metrics.values())
        if len(times) < 2:
            return {"trend": "insufficient_data", "average_time": times[0] if times else 0}
        
        recent_avg = sum(times[-3:]) / min(3, len(times))  # Last 3 calculations
        overall_avg = sum(times) / len(times)
        
        return {
            "trend": "improving" if recent_avg < overall_avg else "stable",
            "recent_average_ms": round(recent_avg * 1000, 2),
            "overall_average_ms": round(overall_avg * 1000, 2),
        }