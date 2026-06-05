# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors
"""Utilities that allow the MCP server to share the CLI analyzer stack."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

from analyzer.cli_entry import SharedCLIAnalyzer, get_shared_cli_analyzer
from fixes.phase0.production_safe_assertions import ProductionAssert


class AnalyzerBridge:
    """Bridge that exposes CLI analyzer behaviour to the MCP server."""

    def __init__(self):
        self._cli_helper: SharedCLIAnalyzer = get_shared_cli_analyzer()

    def analyze_file(self, file_path: str, analysis_type: str = "full") -> Dict[str, object]:
        ProductionAssert.not_none(file_path, "file_path")
        profile = self._resolve_profile(analysis_type)
        payload = self._cli_helper.analyze_file(Path(file_path), profile)
        payload.setdefault("analysis_type", analysis_type)
        payload.setdefault("target", str(file_path))
        return payload

    def analyze_workspace(
        self,
        workspace_path: Path,
        file_paths: Iterable[Path],
        analysis_type: str,
    ) -> Dict[str, object]:
        ProductionAssert.not_none(workspace_path, "workspace_path")
        ProductionAssert.not_none(file_paths, "file_paths")
        profile = self._resolve_profile(analysis_type)
        return self._cli_helper.analyze_workspace(
            workspace_path,
            profile,
            selected_files=list(file_paths),
        )

    def health_snapshot(self) -> Dict[str, object]:
        return {
            "analyzer_available": True,
            "analyzer_type": type(self._cli_helper).__name__,
            "policy_manager": bool(self._cli_helper.policy_manager),
        }

    def _resolve_profile(self, analysis_type: str) -> str:
        mapping = {
            "full": "service-defaults",
            "connascence": "strict-connascence",
            "mece": "service-defaults",
            "nasa": "nasa-compliance",
        }
        return mapping.get(analysis_type, "service-defaults")


__all__ = ["AnalyzerBridge"]
