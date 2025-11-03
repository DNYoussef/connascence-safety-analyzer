"""Minimal configuration service used for integration tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class PolicyPreset:
    id: str
    unified_name: str
    description: str


class ConfigurationService:
    """Provide deterministic configuration lookups for the VS Code tests."""

    def __init__(self) -> None:
        self._presets = {
            "safety_level_1": PolicyPreset("safety_level_1", "nasa-compliance", "NASA General Safety preset"),
            "general_safety_strict": PolicyPreset("general_safety_strict", "strict", "Strict safety baseline"),
            "modern_general": PolicyPreset("modern_general", "standard", "Modern best-practice policy"),
            "safety_level_3": PolicyPreset("safety_level_3", "lenient", "Exploratory policy"),
        }

    def resolve_policy_name(self, policy: str) -> str:
        preset = self._presets.get(policy)
        if preset:
            return preset.unified_name
        return policy

    def get_enhanced_settings(self) -> Dict[str, object]:
        return {
            "enableCrossPhaseCorrelation": True,
            "enableAuditTrail": True,
            "enableSmartRecommendations": True,
            "correlationThreshold": 0.7,
        }

    def getSafetyProfile(self) -> str:
        return "general_safety_strict"
