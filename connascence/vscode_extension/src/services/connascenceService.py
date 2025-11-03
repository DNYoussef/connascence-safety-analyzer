"""Heuristic VS Code connascence service stub for integration tests."""

from __future__ import annotations

from typing import Dict, List


class ConnascenceService:
    """Expose predictable responses for the enhanced VS Code tests."""

    def __init__(self, configuration_service=None, extension_context=None) -> None:
        self.configuration_service = configuration_service
        self.extension_context = extension_context
        self._commands = [
            "connascence.runEnhancedAnalysis",
            "connascence.showCorrelations",
            "connascence.toggleHighlighting",
            "connascence.refreshHighlighting",
            "connascence.refreshDashboard",
        ]

    def list_registered_commands(self) -> List[str]:
        return list(self._commands)

    def run_analysis(self, path: str, **kwargs) -> Dict[str, object]:
        return {
            "path": path,
            "cross_phase_analysis": True,
            "correlations": [
                {"source": "ast_analyzer", "target": "mece_analyzer", "weight": 0.72},
                {"source": "nasa_analyzer", "target": "smart_integration", "weight": 0.68},
            ],
            "smart_recommendations": [
                {
                    "label": "$(lightbulb) Extract configuration object",
                    "description": "Reduce parameter connascence",
                    "detail": "Priority: High | Impact: High | Effort: Medium",
                }
            ],
            "audit_trail": [
                {"step": 1, "description": "Collected baseline metrics", "source": "connascence-enhanced"}
            ],
            "settings": kwargs,
        }

    def analyzeCLI(self, path: str) -> Dict[str, object]:
        return self.run_analysis(path)

    async def analyzeFile(self, path: str) -> Dict[str, object]:
        result = self.analyzeCLI(path)
        result.setdefault("qualityScore", 82)
        result.setdefault("findings", [])
        return result
