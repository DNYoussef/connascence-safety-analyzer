# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors
"""Utilities that allow the MCP server to share the CLI analyzer stack."""

from __future__ import annotations

import logging
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from fixes.phase0.production_safe_assertions import ProductionAssert

try:  # Import the canonical analyzer pipeline used by the CLI
    from analyzer.unified_analyzer import UnifiedAnalyzer
except ImportError:  # pragma: no cover - fallback for stripped test envs
    UnifiedAnalyzer = None  # type: ignore[assignment]

try:
    from analyzer.ast_engine.core_analyzer import ConnascenceASTAnalyzer
except ImportError:  # pragma: no cover - fallback for stripped test envs
    ConnascenceASTAnalyzer = None  # type: ignore[assignment]

try:
    from policy.manager import PolicyManager, ThresholdConfig
except ImportError:  # pragma: no cover - fallback for stripped test envs
    PolicyManager = None  # type: ignore[assignment]
    ThresholdConfig = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class AnalyzerBridge:
    """Bridge that exposes CLI analyzer behaviour to the MCP server."""

    def __init__(self):
        self._analyzer = self._load_analyzer()
        self.policy_manager = self._load_policy_manager()

    def analyze_file(self, file_path: str, analysis_type: str = "full") -> Dict[str, Any]:
        """Run CLI-grade analysis for a single file and normalize output."""

        ProductionAssert.not_none(file_path, "file_path")
        start_time = time.time()
        analyzer_raw = self._analyzer.analyze_file(file_path)
        analyzer_result = self._ensure_result_mapping(analyzer_raw, file_path)

        violations = self._normalize_violations(analyzer_result.get("connascence_violations", []))
        nasa_violations = self._normalize_violations(analyzer_result.get("nasa_violations", []))
        severity_counts = self._count_by_severity(violations)

        summary = {
            "total_violations": len(violations),
            "by_severity": severity_counts,
        }

        nasa_score = analyzer_result.get("nasa_compliance_score", 1.0)
        nasa_compliance = {
            "score": nasa_score,
            "violations": nasa_violations,
            "passing": nasa_score >= 0.8,
        }

        mece_analysis = {
            "score": 1.0,
            "duplications": [],
            "passing": True,
        }

        policy_name, policy_thresholds = self._resolve_policy_snapshot(analysis_type)
        metadata = {
            "analysis_type": analysis_type,
            "file_path": str(file_path),
            "timestamp": time.time(),
            "policy": policy_name,
            "policy_thresholds": policy_thresholds,
        }

        metrics = {
            "files_analyzed": 1,
            "analysis_time": time.time() - start_time,
            "timestamp": metadata["timestamp"],
        }

        return {
            "success": True,
            "file_path": str(file_path),
            "analysis_type": analysis_type,
            "violations": violations,
            "summary": summary,
            "nasa_compliance": nasa_compliance,
            "mece_analysis": mece_analysis,
            "metadata": metadata,
            "metrics": metrics,
        }

    def analyze_workspace(self, workspace_path: Path, file_paths: List[Path], analysis_type: str) -> Dict[str, Any]:
        """Analyze all files collected by the server for the workspace tool."""

        ProductionAssert.not_none(workspace_path, "workspace_path")
        ProductionAssert.not_none(file_paths, "file_paths")

        aggregated_results: List[Dict[str, Any]] = []
        total_violations = 0
        severity_totals: Dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        start_time = time.time()

        for file_path in file_paths:
            file_result = self.analyze_file(str(file_path), analysis_type=analysis_type)
            aggregated_results.append(file_result)
            total_violations += len(file_result.get("violations", []))
            file_severities = file_result.get("summary", {}).get("by_severity", {})
            for severity, count in file_severities.items():
                severity_totals[severity] = severity_totals.get(severity, 0) + count

        summary = {
            "total_files_analyzed": len(file_paths),
            "total_violations": total_violations,
            "severity_totals": severity_totals,
            "analysis_time": time.time() - start_time,
        }

        return {
            "success": True,
            "workspace_path": str(workspace_path),
            "analysis_type": analysis_type,
            "file_results": aggregated_results,
            "summary": summary,
        }

    def health_snapshot(self) -> Dict[str, Any]:
        """Return metadata describing the analyzer stack."""

        return {
            "analyzer_available": self._analyzer is not None,
            "analyzer_type": type(self._analyzer).__name__ if self._analyzer else "unavailable",
            "policy_manager": self.policy_manager is not None,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_analyzer(self):
        """Mirror the CLI loading order."""

        if UnifiedAnalyzer is not None:
            try:
                return UnifiedAnalyzer()
            except Exception as exc:  # pragma: no cover - only hit when deps missing
                logger.warning("UnifiedAnalyzer unavailable: %s", exc)

        if ConnascenceASTAnalyzer is not None:
            try:
                return ConnascenceASTAnalyzer()
            except Exception as exc:  # pragma: no cover - only hit when deps missing
                logger.warning("ConnascenceASTAnalyzer unavailable: %s", exc)

        raise RuntimeError("No analyzer implementation available for MCP server")

    def _load_policy_manager(self):
        if PolicyManager is None:
            return None
        try:
            return PolicyManager()
        except Exception as exc:  # pragma: no cover - should not happen in prod envs
            logger.warning("PolicyManager unavailable: %s", exc)
            return None

    def _normalize_violations(self, violations: List[Any]) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        for violation in violations:
            if hasattr(violation, "to_dict"):
                data = violation.to_dict()  # type: ignore[assignment]
            elif isinstance(violation, dict):
                data = violation
            else:
                data = asdict(violation) if hasattr(violation, "__dict__") else {}

            normalized.append(
                {
                    "id": data.get("id") or data.get("rule_id") or data.get("violation_id") or "unknown",
                    "rule_id": data.get("rule_id") or data.get("id") or "unknown",
                    "type": data.get("type") or data.get("connascence_type") or data.get("category", "unknown"),
                    "severity": data.get("severity", data.get("severity_level", "medium")),
                    "description": data.get("description") or data.get("message", ""),
                    "file_path": data.get("file_path") or data.get("path"),
                    "line_number": data.get("line_number") or data.get("line"),
                    "weight": data.get("weight", 1.0),
                }
            )
        return normalized

    def _count_by_severity(self, violations: List[Dict[str, Any]]) -> Dict[str, int]:
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for violation in violations:
            severity = violation.get("severity", "medium")
            counts[severity] = counts.get(severity, 0) + 1
        return counts

    def _resolve_policy_snapshot(self, analysis_type: str) -> (str, Optional[Dict[str, Any]]):
        if self.policy_manager is None or ThresholdConfig is None:
            return "standard", None

        mapping = {
            "full": "standard",
            "connascence": "strict",
            "mece": "lenient",
            "nasa": "nasa-compliance",
        }
        policy_name = mapping.get(analysis_type, "standard")

        try:
            preset = self.policy_manager.get_preset(policy_name)
        except Exception as exc:  # pragma: no cover - only triggered when presets missing
            logger.warning("Failed to load preset %s: %s", policy_name, exc)
            return policy_name, None

        thresholds = {
            "max_positional_params": getattr(preset, "max_positional_params", None),
            "god_class_methods": getattr(preset, "god_class_methods", None),
            "max_cyclomatic_complexity": getattr(preset, "max_cyclomatic_complexity", None),
        }
        return policy_name, thresholds

    def _ensure_result_mapping(self, analyzer_result: Any, file_path: str) -> Dict[str, Any]:
        """Normalize analyzer outputs into a dict structure."""

        if isinstance(analyzer_result, dict):
            result = dict(analyzer_result)
            if "connascence_violations" not in result and "violations" in result:
                result["connascence_violations"] = result.get("violations", [])
            result.setdefault("nasa_violations", [])
            result.setdefault("nasa_compliance_score", 1.0)
            result.setdefault("file_path", file_path)
            return result

        if isinstance(analyzer_result, list):
            return {
                "file_path": file_path,
                "connascence_violations": analyzer_result,
                "nasa_violations": [],
                "nasa_compliance_score": 1.0,
            }

        return {
            "file_path": file_path,
            "connascence_violations": [],
            "nasa_violations": [],
            "nasa_compliance_score": 1.0,
        }


__all__ = ["AnalyzerBridge"]
