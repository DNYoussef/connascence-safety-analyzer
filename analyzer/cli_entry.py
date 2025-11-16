# SPDX-License-Identifier: MIT
"""Shared entry point for CLI-compatible analyzer workflows.

This module centralizes the logic that powers the `connascence` CLI, MCP server
handlers, and local API clients.  It ensures that every surface that consumes
analysis results receives the exact same JSON schema (`findings`, `summary`,
`quality_score`, etc.) and that safety profiles / threshold handling is kept
in sync.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import time
from typing import Dict, Iterable, Iterator, List, Optional

try:  # Import heavy analyzer dependencies lazily to keep tests lightweight
    from analyzer.ast_engine.core_analyzer import ConnascenceASTAnalyzer
    from analyzer.thresholds import ThresholdConfig
except ImportError:  # pragma: no cover - handled at runtime by CLI guards
    ConnascenceASTAnalyzer = None  # type: ignore[assignment]
    ThresholdConfig = None  # type: ignore[assignment]

try:
    from policy.manager import PolicyManager
except ImportError:  # pragma: no cover - policy manager optional in tests
    PolicyManager = None  # type: ignore[assignment]


DEFAULT_FILE_PATTERNS: tuple[str, ...] = ("*.py",)


@dataclass(frozen=True)
class CliFinding:
    """Lightweight representation of a normalized finding."""

    id: str
    type: str
    severity: str
    message: str
    file: str
    line: int
    column: int
    suggestion: Optional[str] = None
    connascence_type: Optional[str] = None


class SharedCLIAnalyzer:
    """Singleton-friendly helper that powers CLI + MCP workflows."""

    def __init__(self) -> None:
        self.policy_manager = PolicyManager() if PolicyManager else None
        self._threshold_cache: Dict[str, ThresholdConfig] = {}
        self._analyzer_cache: Dict[str, ConnascenceASTAnalyzer] = {}

    # ------------------------------------------------------------------
    # Public surface consumed by CLI + MCP
    # ------------------------------------------------------------------
    def analyze_file(self, target: Path, profile: str) -> Dict[str, object]:
        analyzer = self._require_analyzer(profile)
        start = time.time()
        violations = analyzer.analyze_file(target)
        payload = self._format_analysis_result(
            violations,
            profile=profile,
            target=str(target),
            files_analyzed=1,
            analysis_time=time.time() - start,
        )
        return payload

    def analyze_workspace(
        self,
        workspace: Path,
        profile: str,
        *,
        patterns: Optional[Iterable[str]] = None,
        selected_files: Optional[Iterable[Path]] = None,
    ) -> Dict[str, object]:
        analyzer = self._require_analyzer(profile)
        files: Dict[str, Dict[str, object]] = {}
        total_score = 0.0
        file_iter = selected_files if selected_files else self._iter_workspace_files(workspace, patterns)

        for file_path in file_iter:
            start = time.time()
            violations = analyzer.analyze_file(file_path)
            file_payload = self._format_analysis_result(
                violations,
                profile=profile,
                target=str(file_path),
                files_analyzed=1,
                analysis_time=time.time() - start,
            )
            files[str(file_path)] = file_payload
            total_score += file_payload.get("quality_score", 0.0)  # type: ignore[arg-type]

        analyzed_files = len(files)
        return {
            "files": files,
            "profile": profile,
            "files_analyzed": analyzed_files,
            "overall_score": round(total_score / analyzed_files, 2) if analyzed_files else 100.0,
        }

    def serialize(self, payload: Dict[str, object]) -> str:
        """Utility used by CLI + MCP to ensure identical JSON serialization."""

        return json.dumps(payload, indent=2, sort_keys=False)

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------
    def format_analysis_result(
        self,
        violations,
        *,
        profile: str,
        files_analyzed: int,
        target: Optional[str] = None,
        analysis_time: Optional[float] = None,
    ) -> Dict[str, object]:
        return self._format_analysis_result(
            violations,
            profile=profile,
            files_analyzed=files_analyzed,
            target=target,
            analysis_time=analysis_time,
        )

    def get_threshold_config(self, profile: str) -> ThresholdConfig:
        if profile in self._threshold_cache:
            return self._threshold_cache[profile]

        if self.policy_manager:
            try:
                threshold = self.policy_manager.get_preset(profile)
            except ValueError:
                threshold = ThresholdConfig() if ThresholdConfig else None  # type: ignore[assignment]
        else:
            threshold = ThresholdConfig() if ThresholdConfig else None  # type: ignore[assignment]

        if threshold is None or not hasattr(threshold, "min_magic_literal_threshold"):
            threshold = ThresholdConfig() if ThresholdConfig else None  # type: ignore[assignment]

        if threshold is None:
            raise RuntimeError("Threshold configuration unavailable")

        self._threshold_cache[profile] = threshold
        return threshold

    def _require_analyzer(self, profile: str):
        if ConnascenceASTAnalyzer is None or ThresholdConfig is None:
            raise RuntimeError("Analyzer components are not available")

        if profile in self._analyzer_cache:
            return self._analyzer_cache[profile]

        thresholds = self.get_threshold_config(profile)
        analyzer = ConnascenceASTAnalyzer(thresholds=thresholds)
        self._analyzer_cache[profile] = analyzer
        return analyzer

    def _iter_workspace_files(self, workspace: Path, patterns: Optional[Iterable[str]]) -> Iterator[Path]:
        glob_patterns = list(patterns) if patterns else list(DEFAULT_FILE_PATTERNS)
        seen = set()
        for pattern in glob_patterns:
            for path in workspace.rglob(pattern):
                if not path.is_file():
                    continue
                real_path = path.resolve()
                if real_path in seen:
                    continue
                seen.add(real_path)
                yield path

    def _format_analysis_result(
        self,
        violations,
        *,
        profile: str,
        files_analyzed: int,
        target: Optional[str] = None,
        analysis_time: Optional[float] = None,
    ) -> Dict[str, object]:
        severity_map = {"critical": "critical", "high": "major", "medium": "minor", "low": "info"}
        severity_summary = {"critical": 0, "major": 0, "minor": 0, "info": 0}
        findings: List[Dict[str, object]] = []
        normalized_violations = list(violations or [])

        for idx, violation in enumerate(normalized_violations):
            finding = self._convert_violation(violation, idx, target)
            finding_severity = severity_map.get(str(getattr(violation, "severity", "medium")).lower(), "info")
            severity_summary[finding_severity] += 1
            finding["severity"] = finding_severity
            findings.append(finding)

        total_weight = sum((getattr(v, "weight", 1.0) or 1.0) for v in normalized_violations)
        quality_score = round(max(0.0, 100.0 - (total_weight * 5.0)), 2)
        payload: Dict[str, object] = {
            "target": target,
            "profile": profile,
            "quality_score": quality_score,
            "findings": findings,
            "summary": {"totalIssues": len(findings), "issuesBySeverity": severity_summary},
            "files_analyzed": files_analyzed,
        }

        if analysis_time is not None:
            payload["analysis_time_ms"] = int(analysis_time * 1000)

        return payload

    def _convert_violation(
        self,
        violation,
        idx: int = 0,
        default_file: Optional[str] = None,
    ) -> Dict[str, object]:
        violation_id = getattr(violation, "id", None) or f"{getattr(violation, 'type', 'violation')}-{idx}"
        conn_type = getattr(violation, "connascence_type", None) or getattr(violation, "type", "")
        severity = getattr(violation, "severity", "medium")
        description = getattr(violation, "description", "") or f"Detected {conn_type or 'connascence'}"
        recommendation = getattr(violation, "recommendation", "")
        line_number = getattr(violation, "line_number", 0) or 0

        return {
            "id": violation_id,
            "type": conn_type or getattr(violation, "type", "unknown"),
            "severity": str(severity).lower(),
            "message": description,
            "file": getattr(violation, "file_path", "") or default_file,
            "line": line_number,
            "column": getattr(violation, "column", 0) or 0,
            "suggestion": recommendation,
            "connascence_type": conn_type or getattr(violation, "type", "unknown"),
        }


_SHARED_ANALYZER: Optional[SharedCLIAnalyzer] = None


def get_shared_cli_analyzer() -> SharedCLIAnalyzer:
    """Return a singleton instance that callers can reuse to benefit from caches."""

    global _SHARED_ANALYZER
    if _SHARED_ANALYZER is None:
        _SHARED_ANALYZER = SharedCLIAnalyzer()
    return _SHARED_ANALYZER


__all__ = ["CliFinding", "SharedCLIAnalyzer", "DEFAULT_FILE_PATTERNS", "get_shared_cli_analyzer"]
