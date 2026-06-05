"""
Identity Detector - Detects Connascence of Identity violations.

Flags excessive global variable usage as a proxy for identity coupling.

CON-007: Consolidated from src/detectors/identity_detector.py
"""

import ast
from typing import List

from utils.types import ConnascenceViolation


class IdentityDetector(ast.NodeVisitor):
    """Detects excessive global variable usage."""

    def __init__(self, file_path: str, source_lines: List[str]):
        self.file_path = file_path
        self.source_lines = source_lines
        self.violations: List[ConnascenceViolation] = []
        self._global_vars: set[str] = set()

    def visit_Global(self, node: ast.Global) -> None:
        for name in node.names:
            self._global_vars.add(name)
        self.generic_visit(node)

    def detect(self, tree: ast.AST) -> List[ConnascenceViolation]:
        self.violations.clear()
        self._global_vars.clear()
        self.visit(tree)

        if len(self._global_vars) > 5:
            self.violations.append(
                ConnascenceViolation(
                    id=f"CoI-{self.file_path}:1",
                    type="connascence_of_identity",
                    severity="high",
                    file_path=self.file_path,
                    line_number=1,
                    column=0,
                    description=f"Excessive global variable usage: {len(self._global_vars)} globals",
                    recommendation="Use dependency injection, configuration objects, or class attributes",
                    context={"global_count": len(self._global_vars), "global_vars": sorted(self._global_vars)},
                )
            )

        return self.violations
