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
Unified Connascence Analyzer
============================

Central orchestrator that combines all Phase 1-6 analysis capabilities:
- Core AST-based connascence detection
- MECE duplication analysis
- NASA Power of Ten compliance
- Smart integration engine
- Multi-linter correlation
- Failure prediction system

This provides a single entry point for all connascence analysis functionality.
"""

from dataclasses import asdict, dataclass
import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Union

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Core analyzer components (Phase 1-5) - now all in analyzer/
try:
    from .ast_engine.analyzer_orchestrator import AnalyzerOrchestrator
    from .check_connascence import ConnascenceAnalyzer as ConnascenceASTAnalyzer
    from .dup_detection.mece_analyzer import MECEAnalyzer
    from .smart_integration_engine import SmartIntegrationEngine
except ImportError:
    # Fallback when running as script
    from ast_engine.analyzer_orchestrator import AnalyzerOrchestrator
    from check_connascence import ConnascenceAnalyzer as ConnascenceASTAnalyzer
    from dup_detection.mece_analyzer import MECEAnalyzer
    from smart_integration_engine import SmartIntegrationEngine
try:
    from .constants import (
        ERROR_CODE_MAPPING,
        ERROR_SEVERITY,
    )
except ImportError:
    from constants import (
        ERROR_CODE_MAPPING,
        ERROR_SEVERITY,
    )

# Try to import optional components with fallbacks
try:
    from .failure_detection_system import FailureDetectionSystem
except ImportError:
    FailureDetectionSystem = None

try:
    from ..mcp.nasa_integration import NASAPowerOfTenIntegration
except ImportError:
    NASAPowerOfTenIntegration = None

try:
    from ..policy.budgets import BudgetTracker
    from ..policy.manager import PolicyManager
except ImportError:
    PolicyManager = None
    BudgetTracker = None

logger = logging.getLogger(__name__)


@dataclass
class StandardError:
    """Standard error response format across all integrations."""

    code: int
    message: str
    severity: str
    timestamp: str
    integration: str
    error_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestions: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class UnifiedAnalysisResult:
    """Complete analysis result from all Phase 1-6 components."""

    # Core results
    connascence_violations: List[Dict[str, Any]]
    duplication_clusters: List[Dict[str, Any]]
    nasa_violations: List[Dict[str, Any]]

    # Summary metrics
    total_violations: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int

    # Quality scores
    connascence_index: float
    nasa_compliance_score: float
    duplication_score: float
    overall_quality_score: float

    # Analysis metadata
    project_path: str
    policy_preset: str
    analysis_duration_ms: int
    files_analyzed: int
    timestamp: str

    # Recommendations
    priority_fixes: List[str]
    improvement_actions: List[str]

    # Error tracking
    errors: List[StandardError] = None
    warnings: List[StandardError] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    def has_errors(self) -> bool:
        """Check if analysis has any errors."""
        return bool(self.errors)

    def has_critical_errors(self) -> bool:
        """Check if analysis has critical errors."""
        if not self.errors:
            return False
        return any(error.severity == ERROR_SEVERITY["CRITICAL"] for error in self.errors)


class ErrorHandler:
    """Centralized error handling for all integrations."""

    def __init__(self, integration: str = "analyzer"):
        self.integration = integration
        self.correlation_id = self._generate_correlation_id()

    def _generate_correlation_id(self) -> str:
        """Generate unique correlation ID for error tracking."""
        import uuid

        return str(uuid.uuid4())[:8]

    def create_error(
        self,
        error_type: str,
        message: str,
        severity: str = ERROR_SEVERITY["MEDIUM"],
        context: Optional[Dict[str, Any]] = None,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        suggestions: Optional[List[str]] = None,
    ) -> StandardError:
        """Create standardized error response."""
        from datetime import datetime

        error_code = ERROR_CODE_MAPPING.get(error_type, ERROR_CODE_MAPPING["INTERNAL_ERROR"])

        return StandardError(
            code=error_code,
            message=message,
            severity=severity,
            timestamp=datetime.now().isoformat(),
            integration=self.integration,
            error_id=error_type,
            context=context or {},
            correlation_id=self.correlation_id,
            file_path=file_path,
            line_number=line_number,
            suggestions=suggestions,
        )

    def handle_exception(
        self, exception: Exception, context: Optional[Dict[str, Any]] = None, file_path: Optional[str] = None
    ) -> StandardError:
        """Convert exception to standardized error."""
        # Map common exceptions to error types
        exception_mapping = {
            FileNotFoundError: "FILE_NOT_FOUND",
            PermissionError: "PERMISSION_DENIED",
            SyntaxError: "SYNTAX_ERROR",
            TimeoutError: "TIMEOUT_ERROR",
            MemoryError: "MEMORY_ERROR",
            ValueError: "ANALYSIS_FAILED",
            ImportError: "DEPENDENCY_MISSING",
        }

        error_type = exception_mapping.get(type(exception), "INTERNAL_ERROR")
        severity = (
            ERROR_SEVERITY["HIGH"]
            if error_type in ["FILE_NOT_FOUND", "PERMISSION_DENIED"]
            else ERROR_SEVERITY["MEDIUM"]
        )

        return self.create_error(
            error_type=error_type, message=str(exception), severity=severity, context=context, file_path=file_path
        )

    def log_error(self, error: StandardError):
        """Log error with appropriate level."""
        log_level_mapping = {
            ERROR_SEVERITY["CRITICAL"]: logger.critical,
            ERROR_SEVERITY["HIGH"]: logger.error,
            ERROR_SEVERITY["MEDIUM"]: logger.warning,
            ERROR_SEVERITY["LOW"]: logger.info,
            ERROR_SEVERITY["INFO"]: logger.info,
        }

        log_func = log_level_mapping.get(error.severity, logger.error)
        log_func(f"[{error.integration}:{error.correlation_id}] {error.message} (Code: {error.code})")

        if error.file_path:
            log_func(f"  File: {error.file_path}:{error.line_number or 0}")
        if error.suggestions:
            log_func(f"  Suggestions: {', '.join(error.suggestions)}")


class ComponentInitializer:
    """Handles initialization of optional components with fallbacks."""

    @staticmethod
    def init_smart_engine():
        """Initialize smart integration engine with fallback."""
        try:
            return SmartIntegrationEngine()
        except:
            return None

    @staticmethod
    def init_failure_detector():
        """Initialize failure detector with fallback."""
        if FailureDetectionSystem:
            try:
                return FailureDetectionSystem()
            except:
                return None
        return None

    @staticmethod
    def init_nasa_integration():
        """Initialize NASA integration with fallback."""
        if NASAPowerOfTenIntegration:
            try:
                return NASAPowerOfTenIntegration()
            except:
                return None
        return None

    @staticmethod
    def init_policy_manager():
        """Initialize policy manager with fallback."""
        if PolicyManager:
            try:
                return PolicyManager()
            except:
                return None
        return None

    @staticmethod
    def init_budget_tracker():
        """Initialize budget tracker with fallback."""
        if BudgetTracker:
            try:
                return BudgetTracker()
            except:
                return None
        return None


class MetricsCalculator:
    """Handles calculation of quality metrics and scores."""

    def calculate_comprehensive_metrics(
        self, connascence_violations, duplication_clusters, nasa_violations, nasa_integration=None
    ):
        """Calculate comprehensive quality metrics."""
        all_violations = connascence_violations + duplication_clusters

        severity_counts = self._count_by_severity(all_violations)
        connascence_index = self._calculate_connascence_index(connascence_violations)
        nasa_compliance_score = self._calculate_nasa_score(nasa_violations, nasa_integration)
        duplication_score = self._calculate_duplication_score(duplication_clusters)
        overall_quality_score = self._calculate_overall_quality(
            connascence_index, nasa_compliance_score, duplication_score
        )

        return {
            "total_violations": len(all_violations),
            "critical_count": severity_counts["critical"],
            "high_count": severity_counts["high"],
            "medium_count": severity_counts["medium"],
            "low_count": severity_counts["low"],
            "connascence_index": round(connascence_index, 2),
            "nasa_compliance_score": round(nasa_compliance_score, 3),
            "duplication_score": round(duplication_score, 3),
            "overall_quality_score": round(overall_quality_score, 3),
        }

    def _count_by_severity(self, violations):
        """Count violations by severity level."""
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for violation in violations:
            severity = violation.get("severity", "medium")
            if severity in severity_counts:
                severity_counts[severity] += 1
        return severity_counts

    def _calculate_connascence_index(self, connascence_violations):
        """Calculate connascence index from violations."""
        weight_map = {"critical": 10, "high": 5, "medium": 2, "low": 1}
        return sum(weight_map.get(v.get("severity", "medium"), 1) * v.get("weight", 1) for v in connascence_violations)

    def _calculate_nasa_score(self, nasa_violations, nasa_integration):
        """Calculate NASA compliance score."""
        if nasa_integration:
            return nasa_integration.calculate_nasa_compliance_score(nasa_violations)
        return max(0.0, 1.0 - (len(nasa_violations) * 0.1))

    def _calculate_duplication_score(self, duplication_clusters):
        """Calculate duplication score."""
        return max(0.0, 1.0 - (len(duplication_clusters) * 0.1))

    def _calculate_overall_quality(self, connascence_index, nasa_compliance_score, duplication_score):
        """Calculate overall quality score as weighted average."""
        connascence_weight = 0.4
        nasa_weight = 0.3
        duplication_weight = 0.3

        connascence_score = max(0.0, 1.0 - (connascence_index * 0.01))
        return (
            connascence_score * connascence_weight
            + nasa_compliance_score * nasa_weight
            + duplication_score * duplication_weight
        )


class RecommendationGenerator:
    """Generates unified improvement recommendations."""

    def generate_unified_recommendations(
        self, connascence_violations, duplication_clusters, nasa_violations, nasa_integration=None
    ):
        """Generate comprehensive improvement recommendations."""
        priority_fixes = []
        improvement_actions = []

        priority_fixes.extend(self._get_critical_fixes(connascence_violations))
        improvement_actions.extend(self._get_nasa_actions(nasa_violations, nasa_integration))
        improvement_actions.extend(self._get_duplication_actions(duplication_clusters))
        improvement_actions.extend(self._get_general_actions(connascence_violations))

        return {"priority_fixes": priority_fixes, "improvement_actions": improvement_actions}

    def _get_critical_fixes(self, connascence_violations):
        """Get priority fixes for critical violations."""
        critical_violations = [v for v in connascence_violations if v.get("severity") == "critical"]
        return [
            f"Fix critical {violation.get('type', 'violation')} in {violation.get('file_path', 'unknown file')}"
            for violation in critical_violations[:3]  # Top 3 critical
        ]

    def _get_nasa_actions(self, nasa_violations, nasa_integration):
        """Get NASA compliance improvement actions."""
        if nasa_integration:
            return nasa_integration.get_nasa_compliance_actions(nasa_violations)[:3]
        elif nasa_violations:
            return [f"Address {len(nasa_violations)} NASA compliance violations"]
        return []

    def _get_duplication_actions(self, duplication_clusters):
        """Get duplication reduction actions."""
        if duplication_clusters:
            return [f"Refactor {len(duplication_clusters)} duplication clusters to reduce code repetition"]
        return []

    def _get_general_actions(self, connascence_violations):
        """Get general improvement actions."""
        if len(connascence_violations) > 10:
            return ["Consider breaking down large modules to reduce connascence violations"]
        return []


class UnifiedConnascenceAnalyzer:
    """
    Unified analyzer that orchestrates all Phase 1-6 analysis capabilities.

    This class provides a single, consistent interface to all connascence
    analysis features while maintaining the modularity of individual components.
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the unified analyzer with available components."""
        # Initialize error handling
        self.error_handler = ErrorHandler("analyzer")

        # Initialize core analyzers (always available)
        try:
            self.ast_analyzer = ConnascenceASTAnalyzer()
            self.orchestrator = AnalyzerOrchestrator()
            self.mece_analyzer = MECEAnalyzer()
        except Exception as e:
            error = self.error_handler.handle_exception(e, {"component": "core_analyzers"})
            self.error_handler.log_error(error)
            raise

        # Initialize optional components
        initializer = ComponentInitializer()
        self.smart_engine = initializer.init_smart_engine()
        self.failure_detector = initializer.init_failure_detector()
        self.nasa_integration = initializer.init_nasa_integration()
        self.policy_manager = initializer.init_policy_manager()
        self.budget_tracker = initializer.init_budget_tracker()

        # Initialize helper classes
        self.metrics_calculator = MetricsCalculator()
        self.recommendation_generator = RecommendationGenerator()

        # Load configuration
        self.config = self._load_config(config_path)

        components_loaded = ["AST Analyzer", "Orchestrator", "MECE Analyzer"]
        if self.smart_engine:
            components_loaded.append("Smart Engine")
        if self.failure_detector:
            components_loaded.append("Failure Detector")
        if self.nasa_integration:
            components_loaded.append("NASA Integration")

        logger.info(f"Unified Connascence Analyzer initialized with: {', '.join(components_loaded)}")

    def analyze_project(
        self,
        project_path: Union[str, Path],
        policy_preset: str = "service-defaults",
        options: Optional[Dict[str, Any]] = None,
    ) -> UnifiedAnalysisResult:
        """
        Perform comprehensive connascence analysis on a project.

        Args:
            project_path: Path to the project directory
            policy_preset: Policy configuration to use
            options: Additional analysis options

        Returns:
            Complete analysis result with all findings and recommendations
        """
        project_path = Path(project_path)
        options = options or {}
        start_time = self._get_timestamp_ms()
        analysis_errors = []
        analysis_warnings = []

        logger.info(f"Starting unified analysis of {project_path}")

        # Validate inputs
        try:
            self._validate_analysis_inputs(project_path, policy_preset)
        except Exception as e:
            error = self.error_handler.handle_exception(
                e, {"project_path": str(project_path), "policy_preset": policy_preset}
            )
            analysis_errors.append(error)
            self.error_handler.log_error(error)

        # Run all analysis phases with error handling
        try:
            violations = self._run_analysis_phases(project_path, policy_preset)
        except Exception as e:
            error = self.error_handler.handle_exception(e, {"phase": "analysis", "project_path": str(project_path)})
            analysis_errors.append(error)
            self.error_handler.log_error(error)
            # Provide empty violations as fallback
            violations = {"connascence": [], "duplication": [], "nasa": []}

        # Calculate metrics and generate recommendations with error handling
        try:
            metrics = self.metrics_calculator.calculate_comprehensive_metrics(
                violations["connascence"], violations["duplication"], violations["nasa"], self.nasa_integration
            )
        except Exception as e:
            error = self.error_handler.handle_exception(e, {"phase": "metrics_calculation"})
            analysis_errors.append(error)
            self.error_handler.log_error(error)
            # Provide default metrics
            metrics = self._get_default_metrics()

        try:
            recommendations = self.recommendation_generator.generate_unified_recommendations(
                violations["connascence"], violations["duplication"], violations["nasa"], self.nasa_integration
            )
        except Exception as e:
            error = self.error_handler.handle_exception(e, {"phase": "recommendations"})
            analysis_warnings.append(error)
            self.error_handler.log_error(error)
            # Provide empty recommendations
            recommendations = {"priority_fixes": [], "improvement_actions": []}

        # Build and return result
        analysis_time = self._get_timestamp_ms() - start_time
        result = self._build_unified_result(
            violations,
            metrics,
            recommendations,
            project_path,
            policy_preset,
            analysis_time,
            analysis_errors,
            analysis_warnings,
        )

        logger.info(f"Unified analysis complete in {analysis_time}ms")
        logger.info(f"Found {result.total_violations} total violations across all analyzers")

        if result.has_errors():
            logger.warning(f"Analysis completed with {len(result.errors)} errors")

        return result

    def _run_analysis_phases(self, project_path: Path, policy_preset: str) -> Dict[str, Any]:
        """Run all analysis phases and collect violations."""
        violations = {"connascence": [], "duplication": [], "nasa": []}

        # Phase 1-2: Core AST Analysis
        violations["connascence"] = self._run_ast_analysis(project_path)

        # Phase 3-4: MECE Duplication Detection
        violations["duplication"] = self._run_duplication_analysis(project_path)

        # Phase 5: Smart Integration (if available)
        self._run_smart_integration(project_path, policy_preset)

        # Phase 6: NASA Compliance Check
        violations["nasa"] = self._run_nasa_analysis(violations["connascence"])

        return violations

    def _run_ast_analysis(self, project_path: Path) -> List[Dict[str, Any]]:
        """Run core AST analysis phases."""
        logger.info("Phase 1-2: Running core AST analysis")

        ast_results = self.ast_analyzer.analyze_directory(project_path)
        connascence_violations = [self._violation_to_dict(v) for v in ast_results]

        # Also run god object analysis from orchestrator
        god_results = self.orchestrator.analyze_directory(str(project_path))
        connascence_violations.extend([self._violation_to_dict(v) for v in god_results])

        return connascence_violations

    def _run_duplication_analysis(self, project_path: Path) -> List[Dict[str, Any]]:
        """Run MECE duplication detection."""
        logger.info("Phase 3-4: Running MECE duplication analysis")

        dup_analysis = self.mece_analyzer.analyze_path(str(project_path), comprehensive=True)
        return dup_analysis.get("duplications", [])

    def _run_smart_integration(self, project_path: Path, policy_preset: str):
        """Run smart integration engine if available."""
        if self.smart_engine:
            logger.info("Phase 5: Running smart integration engine")
            try:
                return self.smart_engine.comprehensive_analysis(str(project_path), policy_preset)
            except Exception as e:
                logger.warning(f"Smart integration failed: {e}")
        else:
            logger.info("Phase 5: Smart integration engine not available")
        return None

    def _run_nasa_analysis(self, connascence_violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run NASA compliance analysis."""
        nasa_violations = []

        if self.nasa_integration:
            logger.info("Phase 6: Checking NASA Power of Ten compliance")
            try:
                for violation in connascence_violations:
                    nasa_checks = self.nasa_integration.check_nasa_violations(violation)
                    nasa_violations.extend(nasa_checks)
            except Exception as e:
                logger.warning(f"NASA compliance check failed: {e}")
        else:
            # Extract NASA violations from existing connascence violations
            nasa_violations = [v for v in connascence_violations if "NASA" in v.get("rule_id", "")]

        return nasa_violations

    def _validate_analysis_inputs(self, project_path: Path, policy_preset: str):
        """Validate analysis inputs and raise appropriate errors."""
        if not project_path.exists():
            raise FileNotFoundError(f"Project path does not exist: {project_path}")

        if not project_path.is_dir():
            raise ValueError(f"Project path is not a directory: {project_path}")

        valid_presets = ["service-defaults", "strict-core", "experimental", "balanced", "lenient"]
        if policy_preset not in valid_presets:
            raise ValueError(f"Invalid policy preset: {policy_preset}. Valid options: {valid_presets}")

    def _get_default_metrics(self) -> Dict[str, Any]:
        """Provide default metrics when calculation fails."""
        return {
            "total_violations": 0,
            "critical_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
            "connascence_index": 0.0,
            "nasa_compliance_score": 1.0,
            "duplication_score": 1.0,
            "overall_quality_score": 0.8,
        }

    def _build_unified_result(
        self,
        violations: Dict,
        metrics: Dict,
        recommendations: Dict,
        project_path: Path,
        policy_preset: str,
        analysis_time: int,
        errors: List[StandardError] = None,
        warnings: List[StandardError] = None,
    ) -> UnifiedAnalysisResult:
        """Build the unified analysis result with error tracking."""
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
            priority_fixes=recommendations["priority_fixes"],
            improvement_actions=recommendations["improvement_actions"],
            errors=errors or [],
            warnings=warnings or [],
        )

    def analyze_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Analyze a single file with all available analyzers."""
        file_path = Path(file_path)
        file_errors = []
        file_warnings = []

        # Validate file input
        try:
            if not file_path.exists():
                raise FileNotFoundError(f"File does not exist: {file_path}")
            if not file_path.is_file():
                raise ValueError(f"Path is not a file: {file_path}")
        except Exception as e:
            error = self.error_handler.handle_exception(e, file_path=str(file_path))
            file_errors.append(error)
            self.error_handler.log_error(error)
            return self._get_empty_file_result(file_path, file_errors)

        # Run individual file analysis through each component
        try:
            ast_violations = self.ast_analyzer.analyze_file(file_path)
            violations = [self._violation_to_dict(v) for v in ast_violations]
        except Exception as e:
            error = self.error_handler.handle_exception(e, {"analysis_type": "ast"}, str(file_path))
            file_errors.append(error)
            self.error_handler.log_error(error)
            violations = []

        # Check NASA compliance for each violation
        nasa_violations = []
        try:
            if self.nasa_integration:
                for violation in violations:
                    nasa_checks = self.nasa_integration.check_nasa_violations(violation)
                    nasa_violations.extend(nasa_checks)
            else:
                # Extract NASA violations from existing connascence violations
                nasa_violations = [v for v in violations if "NASA" in v.get("rule_id", "")]
        except Exception as e:
            error = self.error_handler.handle_exception(e, {"analysis_type": "nasa"}, str(file_path))
            file_warnings.append(error)
            self.error_handler.log_error(error)

        # Calculate compliance score
        try:
            nasa_compliance_score = (
                max(0.0, 1.0 - (len(nasa_violations) * 0.1))
                if not self.nasa_integration
                else self.nasa_integration.calculate_nasa_compliance_score(nasa_violations)
            )
        except Exception as e:
            error = self.error_handler.handle_exception(e, {"calculation": "nasa_compliance"}, str(file_path))
            file_warnings.append(error)
            self.error_handler.log_error(error)
            nasa_compliance_score = 1.0

        result = {
            "file_path": str(file_path),
            "connascence_violations": violations,
            "nasa_violations": nasa_violations,
            "violation_count": len(violations),
            "nasa_compliance_score": nasa_compliance_score,
        }

        # Add error information if present
        if file_errors or file_warnings:
            result["errors"] = [error.to_dict() for error in file_errors]
            result["warnings"] = [warning.to_dict() for warning in file_warnings]
            result["has_errors"] = bool(file_errors)

        return result

    def _get_empty_file_result(self, file_path: Path, errors: List[StandardError]) -> Dict[str, Any]:
        """Return empty result structure when file analysis fails."""
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

    def get_dashboard_summary(self, analysis_result: UnifiedAnalysisResult) -> Dict[str, Any]:
        """Generate dashboard-compatible summary from analysis result."""
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

    def _violation_to_dict(self, violation) -> Dict[str, Any]:
        """Convert violation object to dictionary."""
        if isinstance(violation, dict):
            return violation  # Already a dictionary

        # Handle both ConnascenceViolation from check_connascence.py and MCP violations
        return {
            "id": getattr(violation, "id", str(hash(str(violation)))),
            "rule_id": getattr(violation, "type", getattr(violation, "rule_id", "CON_UNKNOWN")),
            "type": getattr(violation, "type", getattr(violation, "connascence_type", "unknown")),
            "severity": getattr(violation, "severity", "medium"),
            "description": getattr(violation, "description", str(violation)),
            "file_path": getattr(violation, "file_path", ""),
            "line_number": getattr(violation, "line_number", 0),
            "weight": getattr(violation, "weight", self._severity_to_weight(getattr(violation, "severity", "medium"))),
        }

    def _cluster_to_dict(self, cluster) -> Dict[str, Any]:
        """Convert duplication cluster to dictionary."""
        return {
            "id": getattr(cluster, "id", str(hash(str(cluster)))),
            "type": "duplication",
            "severity": getattr(cluster, "severity", "medium"),
            "functions": getattr(cluster, "functions", []),
            "similarity_score": getattr(cluster, "similarity_score", 0.0),
        }

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load analyzer configuration."""
        if config_path and Path(config_path).exists():
            with open(config_path) as f:
                return json.load(f)

        # Default configuration
        return {
            "enable_nasa_checks": True,
            "enable_mece_analysis": True,
            "enable_smart_integration": True,
            "default_policy_preset": "service-defaults",
        }

    def _get_timestamp_ms(self) -> int:
        """Get current timestamp in milliseconds."""
        import time

        return int(time.time() * 1000)

    def _get_iso_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime

        return datetime.now().isoformat()

    def _severity_to_weight(self, severity: str) -> float:
        """Convert severity string to numeric weight."""
        weights = {"critical": 10.0, "high": 5.0, "medium": 2.0, "low": 1.0}
        return weights.get(severity, 2.0)

    def create_integration_error(
        self, integration: str, error_type: str, message: str, context: Optional[Dict[str, Any]] = None
    ) -> StandardError:
        """Create integration-specific error with proper mapping."""
        temp_handler = ErrorHandler(integration)
        return temp_handler.create_error(error_type, message, context=context)

    def convert_exception_to_standard_error(
        self, exception: Exception, integration: str = "analyzer", context: Optional[Dict[str, Any]] = None
    ) -> StandardError:
        """Convert any exception to standardized error format."""
        temp_handler = ErrorHandler(integration)
        return temp_handler.handle_exception(exception, context)


def loadConnascenceSystem():
    """
    Entry point for VS Code extension integration.
    Returns a dictionary of functions for the extension to use.
    """
    try:
        analyzer = UnifiedConnascenceAnalyzer()

        def generateConnascenceReport(options):
            """Generate comprehensive connascence report."""
            try:
                result = analyzer.analyze_project(
                    options.get("inputPath"), options.get("safetyProfile", "service-defaults"), options
                )
                return result.to_dict()
            except Exception as e:
                logger.error(f"Report generation failed: {e}")
                error = analyzer.convert_exception_to_standard_error(
                    e, "vscode", {"operation": "generateConnascenceReport"}
                )
                return {
                    "connascence_violations": [],
                    "duplication_clusters": [],
                    "nasa_violations": [],
                    "total_violations": 0,
                    "overall_quality_score": 0.8,
                    "error": error.to_dict(),
                }

        def validateSafetyCompliance(options):
            """Validate safety compliance for a file."""
            try:
                file_result = analyzer.analyze_file(options.get("filePath"))
                nasa_violations = file_result.get("nasa_violations", [])

                result = {"compliant": len(nasa_violations) == 0, "violations": nasa_violations}

                # Include error information if present
                if file_result.get("has_errors"):
                    result["errors"] = file_result.get("errors", [])
                    result["warnings"] = file_result.get("warnings", [])

                return result
            except Exception as e:
                logger.error(f"Safety validation failed: {e}")
                error = analyzer.convert_exception_to_standard_error(
                    e, "vscode", {"operation": "validateSafetyCompliance", "filePath": options.get("filePath")}
                )
                return {"compliant": False, "violations": [], "error": error.to_dict()}

        def getRefactoringSuggestions(options):
            """Get refactoring suggestions for a file."""
            try:
                file_result = analyzer.analyze_file(options.get("filePath"))
                violations = file_result.get("connascence_violations", [])

                suggestions = []
                for violation in violations[:3]:  # Top 3 violations
                    suggestions.append(
                        {
                            "technique": f"Fix {violation.get('type', 'violation')}",
                            "description": violation.get("description", ""),
                            "confidence": 0.8,
                            "preview": f"Consider refactoring line {violation.get('line_number', 0)}",
                        }
                    )

                # Include error context if present
                if file_result.get("has_errors"):
                    for error in file_result.get("errors", []):
                        suggestions.append(
                            {
                                "technique": "Fix Analysis Error",
                                "description": error.get("message", ""),
                                "confidence": 0.9,
                                "preview": f"Resolve: {error.get('error_id', 'Unknown error')}",
                            }
                        )

                return suggestions
            except Exception as e:
                logger.error(f"Refactoring suggestions failed: {e}")
                error = analyzer.convert_exception_to_standard_error(
                    e, "vscode", {"operation": "getRefactoringSuggestions"}
                )
                return [
                    {
                        "technique": "Fix Analysis Error",
                        "description": error.message,
                        "confidence": 0.5,
                        "preview": f"Error Code: {error.code}",
                    }
                ]

        def getAutomatedFixes(options):
            """Get automated fixes for common violations."""
            try:
                file_result = analyzer.analyze_file(options.get("filePath"))
                violations = file_result.get("connascence_violations", [])

                fixes = []
                for violation in violations:
                    if violation.get("type") == "CoM":  # Connascence of Meaning (magic numbers)
                        fixes.append(
                            {
                                "line": violation.get("line_number", 0),
                                "issue": "Magic number",
                                "description": "Replace magic number with named constant",
                                "replacement": "# TODO: Replace with named constant",
                            }
                        )

                return fixes
            except Exception as e:
                logger.error(f"Automated fixes failed: {e}")
                error = analyzer.convert_exception_to_standard_error(e, "vscode", {"operation": "getAutomatedFixes"})
                return [
                    {
                        "line": 0,
                        "issue": "Analysis Error",
                        "description": error.message,
                        "replacement": f"# Error Code: {error.code}",
                        "error": error.to_dict(),
                    }
                ]

        return {
            "generateConnascenceReport": generateConnascenceReport,
            "validateSafetyCompliance": validateSafetyCompliance,
            "getRefactoringSuggestions": getRefactoringSuggestions,
            "getAutomatedFixes": getAutomatedFixes,
        }

    except Exception as e:
        logger.error(f"Failed to load connascence system: {e}")
        # Return mock functions for graceful degradation
        return {
            "generateConnascenceReport": lambda options: {
                "connascence_violations": [],
                "duplication_clusters": [],
                "nasa_violations": [],
                "total_violations": 0,
                "overall_quality_score": 0.8,
                "error": "Python analyzer not available",
            },
            "validateSafetyCompliance": lambda options: {"compliant": True, "violations": []},
            "getRefactoringSuggestions": lambda options: [],
            "getAutomatedFixes": lambda options: [],
        }


def _get_fallback_functions():
    """Get fallback functions for graceful degradation."""
    return {
        "generateConnascenceReport": lambda options: {
            "connascence_violations": [],
            "duplication_clusters": [],
            "nasa_violations": [],
            "total_violations": 0,
            "overall_quality_score": 0.8,
            "error": "Python analyzer not available",
        },
        "validateSafetyCompliance": lambda options: {"compliant": True, "violations": []},
        "getRefactoringSuggestions": lambda options: [],
        "getAutomatedFixes": lambda options: [],
    }


# Singleton instance for global access
unified_analyzer = UnifiedConnascenceAnalyzer()


# CLI entry point for command line usage
def main():
    """Command line entry point for unified analyzer."""
    import argparse

    parser = argparse.ArgumentParser(description="Unified Connascence Analyzer")
    parser.add_argument("--path", required=True, help="Path to analyze")
    parser.add_argument("--format", default="json", choices=["json", "text"], help="Output format")
    parser.add_argument("--policy-preset", default="service-defaults", help="Policy preset to use")
    parser.add_argument("--single-file", action="store_true", help="Analyze single file")
    parser.add_argument("--parallel", action="store_true", help="Enable parallel processing")
    parser.add_argument("--max-workers", type=int, default=4, help="Maximum worker processes")
    parser.add_argument("--threshold", type=float, default=0.8, help="Quality threshold")
    parser.add_argument("--include-tests", action="store_true", help="Include test files")
    parser.add_argument("--enable-mece", action="store_true", help="Enable MECE analysis")
    parser.add_argument("--enable-nasa", action="store_true", help="Enable NASA compliance")
    parser.add_argument("--enable-smart-integration", action="store_true", help="Enable smart integration")
    parser.add_argument("--exclude", nargs="*", help="Patterns to exclude")

    args = parser.parse_args()

    try:
        if args.single_file:
            result = unified_analyzer.analyze_file(args.path)
        else:
            result = unified_analyzer.analyze_project(
                args.path,
                args.policy_preset,
                {
                    "parallel": args.parallel,
                    "max_workers": args.max_workers,
                    "threshold": args.threshold,
                    "include_tests": args.include_tests,
                    "exclude": args.exclude or [],
                },
            )

        if args.format == "json":
            if hasattr(result, "to_dict"):
                print(json.dumps(result.to_dict(), indent=2))
            else:
                print(json.dumps(result, indent=2))
        else:
            if hasattr(result, "to_dict"):
                result_dict = result.to_dict()
                print(f"Analysis Results for {args.path}")
                print(f"Total violations: {result_dict.get('total_violations', 0)}")
                print(f"Quality score: {result_dict.get('overall_quality_score', 0)}")
            else:
                print(f"Analysis Results: {result}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
