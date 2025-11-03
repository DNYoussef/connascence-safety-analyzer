"""Provide deterministic sales demo metadata for integration tests."""

from __future__ import annotations

from pathlib import Path
from typing import Dict


class MasterDemoRunner:
    """Expose demo metadata required by the regression suite."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or Path.cwd()
        self.demos: Dict[str, Dict[str, object]] = self._build_demo_catalogue()

    def _build_demo_catalogue(self) -> Dict[str, Dict[str, object]]:
        return {
            "celery": {
                "proof_points": [
                    "False-positive rate under 5%",
                    "Autofix success rate above 60%",
                ],
            },
            "curl": {
                "proof_points": [
                    "General Safety compliance >= 90%",
                    "Recursion eliminated from security paths",
                ],
            },
            "express": {
                "proof_points": [
                    "MCP workflow exercises full remediation loop",
                    "Semgrep integration enabled for policy mirroring",
                ],
            },
        }

    def generate_sales_artifacts(self) -> Dict[str, str]:
        return {
            "one_pager": "Connascence Analyzer overview",
            "slide_deck": "Executive-ready pitch deck",
            "case_study": "Detailed remediation walkthrough",
        }
