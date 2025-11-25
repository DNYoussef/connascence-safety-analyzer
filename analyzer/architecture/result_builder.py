"""
ResultBuilder - Centralized result building for UnifiedConnascenceAnalyzer

Extracted from: analyzer/unified_analyzer.py
Purpose: Centralize all result building and formatting logic

Responsibilities:
- Build unified analysis results from components
- Convert between result formats (dict <-> object)
- Generate dashboard summaries
- Handle violation/cluster formatting
- Integrate smart analysis results
- Add enhanced metadata to results

NASA Compliance:
- Rule 4: All functions under 60 lines
- Rule 5: Input assertions and error handling
- Rule 7: Bounded resource management
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ResultBuilder:
    """
    Intelligent result builder for analysis outputs.

    Features:
    - Multiple result building strategies (direct, aggregator-based)
    - Format conversion (dict <-> UnifiedAnalysisResult)
    - Dashboard summary generation
    - Violation and cluster formatting
    - Smart results integration
    - Enhanced metadata handling

    NASA Rule 4: Class under 500 lines
    NASA Rule 7: Memory-bounded with clear resource management
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize result builder with configuration.

        Args:
            config: Configuration dictionary with builder settings
                - aggregator: Optional aggregator component for result building

        NASA Rule 5: Input validation
        """
        self.config = config or {}
        self.aggregator = self.config.get("aggregator")

        logger.info(
            f"ResultBuilder initialized (aggregator={'enabled' if self.aggregator else 'disabled'})"
        )

    def build_unified_result(
        self,
        violations: Dict,
        metrics: Dict,
        recommendations: Dict,
        project_path: Path,
        policy_preset: str,
        analysis_time: int,
        errors: Optional[List] = None,
        warnings: Optional[List] = None,
    ):
        """
        Build unified result using aggregator if available.

        Args:
            violations: Violation data by type
            metrics: Analysis metrics
            recommendations: Generated recommendations
            project_path: Project root path
            policy_preset: Policy preset name
            analysis_time: Analysis duration in ms
            errors: Optional error list
            warnings: Optional warning list

        Returns:
            UnifiedAnalysisResult object

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation
        """
        # NASA Rule 5: Input validation assertions
        assert violations is not None, "violations cannot be None"
        assert metrics is not None, "metrics cannot be None"

        if self.aggregator:
            # Delegate to aggregator component
            result_dict = self.aggregator.build_unified_result(
                violations,
                metrics,
                recommendations,
                project_path,
                policy_preset,
                analysis_time,
                errors,
                warnings,
            )
            return self.dict_to_unified_result(result_dict)
        else:
            # Use direct building
            return self.build_unified_result_direct(
                violations,
                metrics,
                recommendations,
                project_path,
                policy_preset,
                analysis_time,
                errors,
                warnings,
            )

    def build_unified_result_direct(
        self,
        violations: Dict,
        metrics: Dict,
        recommendations: Dict,
        project_path: Path,
        policy_preset: str,
        analysis_time: int,
        errors: Optional[List] = None,
        warnings: Optional[List] = None,
    ):
        """
        Build result directly without aggregator component.

        Args:
            violations: Violation data by type
            metrics: Analysis metrics
            recommendations: Generated recommendations
            project_path: Project root path
            policy_preset: Policy preset name
            analysis_time: Analysis duration in ms
            errors: Optional error list
            warnings: Optional warning list

        Returns:
            UnifiedAnalysisResult object

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation
        """
        # NASA Rule 5: Input validation assertions
        assert violations is not None, "violations cannot be None"
        assert metrics is not None, "metrics cannot be None"

        from analyzer.unified_analyzer import UnifiedAnalysisResult

        errors = errors or []
        warnings = warnings or []

        # Calculate aggregated metrics
        quality_metrics = self._calculate_quality_metrics(violations, metrics)

        # Build result object
        return self._build_result_object(
            violations,
            metrics,
            recommendations,
            quality_metrics,
            project_path,
            policy_preset,
            analysis_time,
            errors,
            warnings,
        )

    def dict_to_unified_result(self, result_dict: Dict[str, Any]):
        """
        Convert dictionary result to UnifiedAnalysisResult object.

        Args:
            result_dict: Result data as dictionary

        Returns:
            UnifiedAnalysisResult object

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation
        """
        # NASA Rule 5: Input validation
        assert result_dict is not None, "result_dict cannot be None"

        from analyzer.unified_analyzer import UnifiedAnalysisResult

        return UnifiedAnalysisResult(
            connascence_violations=result_dict.get("connascence_violations", []),
            duplication_clusters=result_dict.get("duplication_clusters", []),
            nasa_violations=result_dict.get("nasa_violations", []),
            total_violations=result_dict.get("total_violations", 0),
            critical_count=result_dict.get("critical_count", 0),
            high_count=result_dict.get("high_count", 0),
            medium_count=result_dict.get("medium_count", 0),
            low_count=result_dict.get("low_count", 0),
            connascence_index=result_dict.get("connascence_index", 0.0),
            nasa_compliance_score=result_dict.get("nasa_compliance_score", 1.0),
            duplication_score=result_dict.get("duplication_score", 1.0),
            overall_quality_score=result_dict.get("overall_quality_score", 0.8),
            project_path=result_dict.get("project_path", ""),
            policy_preset=result_dict.get("policy_preset", "service-defaults"),
            analysis_duration_ms=result_dict.get("analysis_duration_ms", 0),
            files_analyzed=result_dict.get("files_analyzed", 0),
            timestamp=result_dict.get("timestamp", self._get_iso_timestamp()),
            priority_fixes=result_dict.get("priority_fixes", []),
            improvement_actions=result_dict.get("improvement_actions", []),
            errors=result_dict.get("errors", []),
            warnings=result_dict.get("warnings", []),
        )

    def get_empty_file_result(
        self, file_path: Path, errors: List
    ) -> Dict[str, Any]:
        """
        Return empty result structure when file analysis fails.

        Args:
            file_path: Path to file that failed
            errors: List of StandardError objects

        Returns:
            Dictionary with empty result structure

        NASA Rule 4: Function under 60 lines
        """
        return {
            "file_path": str(file_path),
            "connascence_violations": [],
            "nasa_violations": [],
            "violation_count": 0,
            "nasa_compliance_score": 0.0,
            "errors": [error.to_dict() for error in errors],
            "warnings": [],
            "has_errors": True,
        }

    def get_dashboard_summary(self, analysis_result) -> Dict[str, Any]:
        """
        Generate dashboard-compatible summary from analysis result.

        Args:
            analysis_result: UnifiedAnalysisResult object

        Returns:
            Dictionary with dashboard summary data

        NASA Rule 4: Function under 60 lines
        """
        return {
            "project_info": {
                "path": analysis_result.project_path,
                "policy": analysis_result.policy_preset,
                "files_analyzed": analysis_result.files_analyzed,
                "analysis_time": analysis_result.analysis_duration_ms,
            },
            "violation_summary": {
                "total": analysis_result.total_violations,
                "by_severity": {
                    "critical": analysis_result.critical_count,
                    "high": analysis_result.high_count,
                    "medium": analysis_result.medium_count,
                    "low": analysis_result.low_count,
                },
            },
            "quality_metrics": {
                "connascence_index": analysis_result.connascence_index,
                "nasa_compliance": analysis_result.nasa_compliance_score,
                "duplication_score": analysis_result.duplication_score,
                "overall_quality": analysis_result.overall_quality_score,
            },
            "recommendations": {
                "priority_fixes": analysis_result.priority_fixes[:5],  # Top 5
                "improvement_actions": analysis_result.improvement_actions[:5],
            },
        }

    def violation_to_dict(self, violation) -> Dict[str, Any]:
        """
        Convert violation object to dictionary.

        Args:
            violation: Violation object or dict

        Returns:
            Dictionary representation

        NASA Rule 4: Function under 60 lines
        """
        if isinstance(violation, dict):
            return violation  # Already a dictionary

        # Handle both ConnascenceViolation and MCP violations
        return {
            "id": getattr(violation, "id", str(hash(str(violation)))),
            "rule_id": getattr(
                violation, "type", getattr(violation, "rule_id", "CON_UNKNOWN")
            ),
            "type": getattr(
                violation, "type", getattr(violation, "connascence_type", "unknown")
            ),
            "severity": getattr(violation, "severity", "medium"),
            "description": getattr(violation, "description", str(violation)),
            "file_path": getattr(violation, "file_path", ""),
            "line_number": getattr(violation, "line_number", 0),
            "weight": getattr(
                violation,
                "weight",
                self._severity_to_weight(getattr(violation, "severity", "medium")),
            ),
        }

    def cluster_to_dict(self, cluster) -> Dict[str, Any]:
        """
        Convert duplication cluster to dictionary.

        Args:
            cluster: Cluster object or dict

        Returns:
            Dictionary representation

        NASA Rule 4: Function under 60 lines
        """
        return {
            "id": getattr(cluster, "id", str(hash(str(cluster)))),
            "type": "duplication",
            "severity": getattr(cluster, "severity", "medium"),
            "functions": getattr(cluster, "functions", []),
            "similarity_score": getattr(cluster, "similarity_score", 0.0),
        }

    def integrate_smart_results(
        self, enhanced_recommendations: Dict, smart_results: Dict
    ) -> None:
        """
        Integrate smart analysis results into recommendations.

        Args:
            enhanced_recommendations: Recommendations dict to enhance
            smart_results: Smart analysis results to integrate

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation
        """
        # NASA Rule 5: Input validation assertions
        assert enhanced_recommendations is not None, "enhanced_recommendations cannot be None"
        assert smart_results is not None, "smart_results cannot be None"

        if smart_results.get("enhanced_recommendations"):
            enhanced_recommendations["smart_recommendations"] = smart_results[
                "enhanced_recommendations"
            ]
        if smart_results.get("correlations"):
            enhanced_recommendations["correlations"] = smart_results["correlations"]

    def create_analysis_result_object(
        self,
        violations: Dict,
        metrics: Dict,
        enhanced_recommendations: Dict,
        project_path: Path,
        policy_preset: str,
        analysis_time: int,
        errors: List,
        warnings: List,
    ):
        """
        Create the analysis result object from components.

        Args:
            violations: Violation data by type
            metrics: Analysis metrics
            enhanced_recommendations: Enhanced recommendations
            project_path: Project root path
            policy_preset: Policy preset name
            analysis_time: Analysis duration in ms
            errors: Error list
            warnings: Warning list

        Returns:
            UnifiedAnalysisResult object

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation
        """
        # NASA Rule 5: Input validation assertions
        assert violations is not None, "violations cannot be None"
        assert metrics is not None, "metrics cannot be None"

        from analyzer.unified_analyzer import UnifiedAnalysisResult

        return UnifiedAnalysisResult(
            connascence_violations=violations["connascence"],
            duplication_clusters=violations["duplication"],
            nasa_violations=violations["nasa"],
            total_violations=metrics["total_violations"],
            critical_count=metrics["critical_count"],
            high_count=metrics["high_count"],
            medium_count=metrics["medium_count"],
            low_count=metrics["low_count"],
            connascence_index=metrics["connascence_index"],
            nasa_compliance_score=metrics["nasa_compliance_score"],
            duplication_score=metrics["duplication_score"],
            overall_quality_score=metrics["overall_quality_score"],
            project_path=str(project_path),
            policy_preset=policy_preset,
            analysis_duration_ms=analysis_time,
            files_analyzed=len(violations["connascence"]),
            timestamp=self._get_iso_timestamp(),
            priority_fixes=enhanced_recommendations["priority_fixes"],
            improvement_actions=enhanced_recommendations["improvement_actions"],
            errors=errors or [],
            warnings=warnings or [],
        )

    def add_enhanced_metadata_to_result(
        self, result, violations: Dict, enhanced_recommendations: Dict
    ) -> None:
        """
        Add enhanced metadata to result object.

        Args:
            result: UnifiedAnalysisResult object to enhance
            violations: Violation data with metadata
            enhanced_recommendations: Enhanced recommendations

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation
        """
        # NASA Rule 5: Input validation assertions
        assert result is not None, "result cannot be None"
        assert violations is not None, "violations cannot be None"

        phase_metadata = violations.get("_metadata", {})

        if hasattr(result, "__dict__"):
            result.__dict__["audit_trail"] = phase_metadata.get("audit_trail", [])
            result.__dict__["correlations"] = phase_metadata.get("correlations", [])
            result.__dict__["smart_recommendations"] = enhanced_recommendations.get(
                "smart_recommendations", []
            )
            result.__dict__["cross_phase_analysis"] = (
                phase_metadata.get("smart_results", {}).get(
                    "cross_phase_analysis", False
                )
            )

    def _calculate_quality_metrics(
        self, violations: Dict, metrics: Dict
    ) -> Dict[str, float]:
        """
        Calculate quality metrics from violations and metrics data.

        Args:
            violations: Violation data by type
            metrics: Analysis metrics

        Returns:
            Dictionary with calculated quality metrics

        NASA Rule 4: Function under 60 lines
        """
        # Extract violation counts
        total_violations = sum(
            len(v) if isinstance(v, list) else (1 if v else 0)
            for v in violations.values()
        )

        # Calculate quality metrics
        connascence_index = metrics.get("connascence_index", total_violations * 0.1)
        nasa_compliance_score = metrics.get("nasa_compliance_score", 0.9)
        duplication_score = metrics.get("duplication_score", 0.95)
        overall_quality_score = (nasa_compliance_score + duplication_score) / 2.0

        return {
            "total_violations": total_violations,
            "connascence_index": connascence_index,
            "nasa_compliance_score": nasa_compliance_score,
            "duplication_score": duplication_score,
            "overall_quality_score": overall_quality_score,
        }

    def _build_result_object(
        self,
        violations: Dict,
        metrics: Dict,
        recommendations: Dict,
        quality_metrics: Dict,
        project_path: Path,
        policy_preset: str,
        analysis_time: int,
        errors: List,
        warnings: List,
    ):
        """
        Build UnifiedAnalysisResult object from components.

        Args:
            violations: Violation data by type
            metrics: Analysis metrics
            recommendations: Generated recommendations
            quality_metrics: Calculated quality metrics
            project_path: Project root path
            policy_preset: Policy preset name
            analysis_time: Analysis duration in ms
            errors: Error list
            warnings: Warning list

        Returns:
            UnifiedAnalysisResult object

        NASA Rule 4: Function under 60 lines
        """
        from analyzer.unified_analyzer import UnifiedAnalysisResult

        return UnifiedAnalysisResult(
            connascence_violations=violations.get("connascence", []),
            duplication_clusters=violations.get("duplication", []),
            nasa_violations=violations.get("nasa", []),
            total_violations=quality_metrics["total_violations"],
            critical_count=violations.get("critical_count", 0),
            high_count=violations.get("high_count", 0),
            medium_count=violations.get("medium_count", 0),
            low_count=violations.get("low_count", 0),
            connascence_index=quality_metrics["connascence_index"],
            nasa_compliance_score=quality_metrics["nasa_compliance_score"],
            duplication_score=quality_metrics["duplication_score"],
            overall_quality_score=quality_metrics["overall_quality_score"],
            project_path=str(project_path),
            policy_preset=policy_preset,
            analysis_duration_ms=analysis_time,
            files_analyzed=metrics.get("files_analyzed", 0),
            timestamp=self._get_iso_timestamp(),
            priority_fixes=recommendations.get("priority_fixes", []),
            improvement_actions=recommendations.get("improvement_actions", []),
            errors=errors,
            warnings=warnings,
        )

    def _get_iso_timestamp(self) -> str:
        """
        Get current timestamp in ISO format.

        Returns:
            ISO format timestamp string

        NASA Rule 4: Function under 60 lines
        """
        return datetime.now().isoformat()

    def _severity_to_weight(self, severity: str) -> float:
        """
        Convert severity string to numeric weight.

        Args:
            severity: Severity level string

        Returns:
            Numeric weight value

        NASA Rule 4: Function under 60 lines
        """
        weights = {"critical": 10.0, "high": 5.0, "medium": 2.0, "low": 1.0}
        return weights.get(severity, 2.0)
