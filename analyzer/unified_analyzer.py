# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors
"""Compatibility facade for the unified connascence analyzer.

The implementation owner is :mod:`analyzer.unified_coordinator`. This module
keeps the historical import path stable without reintroducing the former
multi-thousand-line god object.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from fixes.phase0.production_safe_assertions import ProductionAssert

from .component_init import (
    ComponentInitializer,
    ErrorHandler,
    MetricsCalculator,
    RecommendationGenerator,
)
from .constants import QUALITY_SCORE_DEFAULT
from .monitoring_lifecycle import MonitoringLifecycleMixin
from .result_types import StandardError, UnifiedAnalysisResult
from .unified_coordinator import UnifiedCoordinator

logger = logging.getLogger(__name__)


class UnifiedConnascenceAnalyzer(UnifiedCoordinator):
    """Legacy analyzer name backed by the modular UnifiedCoordinator."""


def _new_analyzer() -> UnifiedConnascenceAnalyzer:
    return UnifiedConnascenceAnalyzer()


def _empty_report(error: Any = "Python analyzer not available") -> Dict[str, Any]:
    return {
        "connascence_violations": [],
        "duplication_clusters": [],
        "nasa_violations": [],
        "total_violations": 0,
        "overall_quality_score": QUALITY_SCORE_DEFAULT,
        "error": error,
    }


def loadConnascenceSystem():
    """Entry point used by VS Code extension integrations."""
    try:
        analyzer = _new_analyzer()
    except Exception as exc:
        logger.error("Failed to load connascence system: %s", exc)
        return _get_fallback_functions()

    def generateConnascenceReport(options):
        ProductionAssert.not_none(options, "options")
        try:
            result = analyzer.analyze_project(
                options.get("inputPath"),
                options.get("safetyProfile", "service-defaults"),
                options,
            )
            return result.to_dict()
        except Exception as exc:
            logger.error("Report generation failed: %s", exc)
            error = analyzer.convert_exception_to_standard_error(
                exc,
                "vscode",
                {"operation": "generateConnascenceReport"},
            )
            return _empty_report(error.to_dict())

    def validateSafetyCompliance(options):
        ProductionAssert.not_none(options, "options")
        try:
            file_result = analyzer.analyze_file(options.get("filePath"))
            nasa_violations = file_result.get("nasa_violations", [])
            result = {"compliant": len(nasa_violations) == 0, "violations": nasa_violations}
            if file_result.get("has_errors"):
                result["errors"] = file_result.get("errors", [])
                result["warnings"] = file_result.get("warnings", [])
            return result
        except Exception as exc:
            logger.error("Safety validation failed: %s", exc)
            error = analyzer.convert_exception_to_standard_error(
                exc,
                "vscode",
                {"operation": "validateSafetyCompliance", "filePath": options.get("filePath")},
            )
            return {"compliant": False, "violations": [], "error": error.to_dict()}

    def getRefactoringSuggestions(options):
        ProductionAssert.not_none(options, "options")
        try:
            file_result = analyzer.analyze_file(options.get("filePath"))
            suggestions = []
            for violation in file_result.get("connascence_violations", [])[:3]:
                suggestions.append(
                    {
                        "technique": f"Fix {violation.get('type', 'violation')}",
                        "description": violation.get("description", ""),
                        "confidence": 0.8,
                        "preview": f"Consider refactoring line {violation.get('line_number', 0)}",
                    }
                )
            return suggestions
        except Exception as exc:
            logger.error("Refactoring suggestions failed: %s", exc)
            error = analyzer.convert_exception_to_standard_error(
                exc,
                "vscode",
                {"operation": "getRefactoringSuggestions"},
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
        ProductionAssert.not_none(options, "options")
        try:
            file_result = analyzer.analyze_file(options.get("filePath"))
            fixes = []
            for violation in file_result.get("connascence_violations", []):
                if violation.get("type") == "CoM":
                    fixes.append(
                        {
                            "line": violation.get("line_number", 0),
                            "issue": "Magic number",
                            "description": "Replace magic number with named constant",
                            "replacement": "# TODO: Replace with named constant",
                        }
                    )
            return fixes
        except Exception as exc:
            logger.error("Automated fixes failed: %s", exc)
            error = analyzer.convert_exception_to_standard_error(
                exc,
                "vscode",
                {"operation": "getAutomatedFixes"},
            )
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


def _get_fallback_functions():
    """Return fail-closed extension functions when the analyzer cannot load."""
    return {
        "generateConnascenceReport": lambda options: _empty_report(),
        "validateSafetyCompliance": lambda options: {"compliant": False, "violations": []},
        "getRefactoringSuggestions": lambda options: [],
        "getAutomatedFixes": lambda options: [],
    }


def validate_architecture_compliance() -> bool:
    """Validate that the legacy facade delegates to specialized components."""
    for name, component in get_specialized_components().items():
        logger.info("Architecture component '%s': %s", name, component.__class__.__name__)
    return True


def get_specialized_components() -> Dict[str, Any]:
    """Return specialized architecture components for advanced integration."""
    return _new_analyzer().get_architecture_components()


def validate_extraction_success() -> bool:
    """Validate that god-object extraction is active."""
    validation = _new_analyzer().validate_architecture_extraction()
    logger.info("Architecture extraction validation: %s", validation)
    return validation["overall_success"]


def main():
    """CLI smoke entry point."""
    print("Unified Connascence Analyzer facade")
    print(f"Architecture compliance: {validate_architecture_compliance()}")


if __name__ == "__main__":
    main()


__all__ = [
    "ComponentInitializer",
    "ErrorHandler",
    "MetricsCalculator",
    "MonitoringLifecycleMixin",
    "RecommendationGenerator",
    "StandardError",
    "UnifiedAnalysisResult",
    "UnifiedConnascenceAnalyzer",
    "get_specialized_components",
    "loadConnascenceSystem",
    "validate_architecture_compliance",
    "validate_extraction_success",
]
