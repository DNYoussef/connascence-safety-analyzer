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
Component Initialization Module
================================

Handles initialization of optional components with fallbacks.
Extracted from unified_analyzer.py for NASA Rule 4 compliance.

Contains:
- ErrorHandler: Centralized error handling
- ComponentInitializer: Component initialization with fallbacks
- MetricsCalculator: Legacy metrics wrapper
- RecommendationGenerator: Legacy recommendation wrapper
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from fixes.phase0.production_safe_assertions import ProductionAssert
try:
    from .result_types import StandardError
except ImportError:
    from result_types import StandardError

# Import constants
try:
    from .constants import ERROR_CODE_MAPPING, ERROR_SEVERITY
except ImportError:
    from constants import ERROR_CODE_MAPPING, ERROR_SEVERITY

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Centralized error handling for all integrations."""

    def __init__(self, integration: str = "analyzer"):
        self.integration = integration
        self.correlation_id = self._generate_correlation_id()

    def _generate_correlation_id(self) -> str:
        """Generate unique correlation ID for error tracking."""
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
        ProductionAssert.not_none(error, "error")

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
            from .smart_integration_engine import SmartIntegrationEngine
            return SmartIntegrationEngine()
        except ImportError:
            try:
                from smart_integration_engine import SmartIntegrationEngine
                return SmartIntegrationEngine()
            except ImportError:
                logger.debug("SmartIntegrationEngine not available")
                return None
        except Exception as e:
            logger.debug(f"SmartIntegrationEngine initialization failed: {e}")
            return None

    @staticmethod
    def init_failure_detector():
        """Initialize failure detector with fallback."""
        try:
            from .failure_detection_system import FailureDetectionSystem
            return FailureDetectionSystem()
        except ImportError:
            logger.debug("FailureDetectionSystem not available")
            return None
        except Exception as e:
            logger.debug(f"FailureDetectionSystem initialization failed: {e}")
            return None

    @staticmethod
    def init_nasa_integration():
        """Initialize NASA integration with fallback."""
        try:
            from ..mcp.nasa_integration import NASAPowerOfTenIntegration
            return NASAPowerOfTenIntegration()
        except ImportError:
            try:
                from mcp.nasa_integration import NASAPowerOfTenIntegration
                return NASAPowerOfTenIntegration()
            except ImportError:
                logger.debug("NASAPowerOfTenIntegration not available")
                return None
        except Exception as e:
            logger.debug(f"NASAPowerOfTenIntegration initialization failed: {e}")
            return None

    @staticmethod
    def init_policy_manager():
        """Initialize policy manager with fallback."""
        try:
            from ..policy.manager import PolicyManager
            return PolicyManager()
        except ImportError:
            try:
                from policy.manager import PolicyManager
                return PolicyManager()
            except ImportError:
                logger.debug("PolicyManager not available")
                return None
        except Exception as e:
            logger.debug(f"PolicyManager initialization failed: {e}")
            return None

    @staticmethod
    def init_budget_tracker():
        """Initialize budget tracker with fallback."""
        try:
            from ..policy.budgets import BudgetTracker
            return BudgetTracker()
        except ImportError:
            try:
                from policy.budgets import BudgetTracker
                return BudgetTracker()
            except ImportError:
                logger.debug("BudgetTracker not available")
                return None
        except Exception as e:
            logger.debug(f"BudgetTracker initialization failed: {e}")
            return None


class MetricsCalculator:
    """Legacy metrics calculator - delegates to MetricsCollector for compatibility."""

    def __init__(self):
        try:
            from .architecture.metrics_collector import MetricsCollector
            self.collector = MetricsCollector()
        except ImportError:
            self.collector = None

    def calculate_metrics(self, violations, nasa_integration=None):
        """Calculate metrics from violations dictionary. NASA Rule 4 compliant."""
        if self.collector:
            return self.collector.collect_violation_metrics(violations)
        # Fallback if collector not available
        return self._calculate_fallback_metrics(violations)

    def calculate_comprehensive_metrics(
        self, connascence_violations, duplication_clusters, nasa_violations, nasa_integration=None
    ):
        """Calculate comprehensive quality metrics - delegates to collector."""
        violations = {
            "connascence": connascence_violations,
            "duplication": duplication_clusters,
            "nasa": nasa_violations
        }
        return self.calculate_metrics(violations, nasa_integration)

    def _calculate_fallback_metrics(self, violations):
        """Fallback metrics calculation when collector not available."""
        connascence = violations.get("connascence", [])
        duplication = violations.get("duplication", [])
        nasa = violations.get("nasa", [])

        total = len(connascence) + len(duplication) + len(nasa)

        # Count by severity
        critical = sum(1 for v in connascence if v.get("severity") == "critical")
        high = sum(1 for v in connascence if v.get("severity") == "high")
        medium = sum(1 for v in connascence if v.get("severity") == "medium")
        low = sum(1 for v in connascence if v.get("severity") == "low")

        return {
            "total_violations": total,
            "critical_count": critical,
            "high_count": high,
            "medium_count": medium,
            "low_count": low,
            "connascence_index": max(0.0, 1.0 - (len(connascence) * 0.01)),
            "nasa_compliance_score": max(0.0, 1.0 - (len(nasa) * 0.1)),
            "duplication_score": max(0.0, 1.0 - (len(duplication) * 0.05)),
            "overall_quality_score": max(0.0, 1.0 - (total * 0.02)),
        }


class RecommendationGenerator:
    """Legacy recommendation generator - delegates to RecommendationEngine for compatibility."""

    def __init__(self):
        try:
            from .architecture.recommendation_engine import RecommendationEngine
            self.engine = RecommendationEngine()
        except ImportError:
            self.engine = None

    def generate_recommendations(self, violations, nasa_integration=None):
        """Generate recommendations from violations dictionary. NASA Rule 4 compliant."""
        connascence_violations = violations.get("connascence", [])
        duplication_clusters = violations.get("duplication", [])
        nasa_violations = violations.get("nasa", [])
        return self.generate_unified_recommendations(
            connascence_violations, duplication_clusters, nasa_violations, nasa_integration
        )

    def generate_unified_recommendations(
        self, connascence_violations, duplication_clusters, nasa_violations, nasa_integration=None
    ):
        """Generate comprehensive improvement recommendations - delegates to engine."""
        if self.engine:
            return self.engine.generate_unified_recommendations(
                connascence_violations, duplication_clusters, nasa_violations, nasa_integration
            )
        # Fallback if engine not available
        return self._generate_fallback_recommendations(
            connascence_violations, duplication_clusters, nasa_violations
        )

    def _generate_fallback_recommendations(
        self, connascence_violations, duplication_clusters, nasa_violations
    ):
        """Fallback recommendation generation when engine not available."""
        priority_fixes = []
        improvement_actions = []

        # Generate basic recommendations from violations
        for v in connascence_violations[:5]:
            if v.get("severity") in ["critical", "high"]:
                priority_fixes.append(f"Fix {v.get('type', 'unknown')} in {v.get('file_path', 'unknown')}")

        for v in nasa_violations[:3]:
            improvement_actions.append(f"Address NASA {v.get('rule_id', 'unknown')}: {v.get('message', '')}")

        if duplication_clusters:
            improvement_actions.append(f"Refactor {len(duplication_clusters)} duplication clusters")

        return {
            "priority_fixes": priority_fixes,
            "improvement_actions": improvement_actions,
            "strategic_suggestions": [],
            "technical_debt_actions": [],
        }


__all__ = [
    "ErrorHandler",
    "ComponentInitializer",
    "MetricsCalculator",
    "RecommendationGenerator",
]
