"""Simplified constrained generator used in integration tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class SafetyViolation:
    rule: str
    message: str
    line: int


class ConstrainedGenerator:
    """Generate deterministic safety feedback based on source heuristics."""

    def __init__(self, backend) -> None:
        self.backend = backend

    def check_safety_violations(self, source: str, language: str, policy: str) -> List[dict]:
        """Return heuristic violations for integration smoke tests."""

        violations: List[SafetyViolation] = []
        lines = source.splitlines()

        for idx, line in enumerate(lines, start=1):
            lower = line.lower()
            if any(token in lower for token in {"magic", "42", "0.15", "0.10"}):
                violations.append(
                    SafetyViolation(
                        rule="magic_literals",
                        message="Magic literal detected; replace with named constant.",
                        line=idx,
                    )
                )
            if line.count("if") >= 2 or line.strip().startswith("if") and line.count("(") > 1:
                violations.append(
                    SafetyViolation(
                        rule="deep_nesting",
                        message="Nested conditional detected; refactor to reduce execution coupling.",
                        line=idx,
                    )
                )

        if source.count("if ") >= 3:
            first_if = next((i for i, l in enumerate(lines, start=1) if l.strip().startswith("if")), 1)
            violations.append(
                SafetyViolation(
                    rule="deep_nesting",
                    message="Multiple stacked conditionals detected; consider flattening complex branching.",
                    line=first_if,
                )
            )

        if not violations and source:
            violations.append(
                SafetyViolation(
                    rule="baseline",
                    message="No obvious issues detected; baseline pass.",
                    line=1,
                )
            )

        return [violation.__dict__ for violation in violations]
