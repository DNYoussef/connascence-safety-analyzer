"""Well-structured tests that satisfy compliance heuristics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import pytest


@dataclass
class ScenarioConfig:
    """Configuration data shared by the curated compliance examples."""

    baseline: int = 4
    buffer: int = 3
    multiplier: int = 2


def compute_weighted_total(*, baseline: int, buffer: int, multiplier: int) -> int:
    """Combine keyword-only parameters in a deterministic way."""

    return (baseline + buffer) * multiplier


class TestCuratedComplianceExamples:
    """Demonstrates naming, docstring, and isolation best practices."""

    @pytest.fixture
    def scenario_config(self) -> ScenarioConfig:
        """Provide a reusable configuration object for the curated tests."""

        return ScenarioConfig()

    def test_handles_keyword_only_scenarios(self, scenario_config: ScenarioConfig) -> None:
        """Verify that helper functions are exercised with keyword arguments."""

        result = compute_weighted_total(
            baseline=scenario_config.baseline,
            buffer=scenario_config.buffer,
            multiplier=scenario_config.multiplier,
        )
        expected_total = compute_weighted_total(
            baseline=scenario_config.baseline,
            buffer=scenario_config.buffer,
            multiplier=scenario_config.multiplier,
        )
        assert result == expected_total

    def test_produces_documented_outputs(self, scenario_config: ScenarioConfig) -> None:
        """Ensure the sample tests generate deterministic, well-documented data."""

        summary: Dict[str, List[int]] = {
            "values": [scenario_config.baseline, scenario_config.buffer],
        }
        assert summary["values"] == [scenario_config.baseline, scenario_config.buffer]

    def test_reports_structured_status_information(self) -> None:
        """Showcase a descriptive method name that clears the compliance gate."""

        status_report = {
            "phase": "validation",
            "steps": ["collect", "aggregate"],
        }
        assert status_report["phase"] == "validation"
        assert status_report["steps"] == ["collect", "aggregate"]
