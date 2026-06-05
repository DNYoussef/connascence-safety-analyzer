"""Supply-chain configuration loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml


class SupplyChainConfigLoader:
    def __init__(self, config_path: str | None = None) -> None:
        self.config_path = config_path
        self.config: Dict[str, Any] = {}

    def load_config(self) -> Dict[str, Any]:
        if self.config_path and Path(self.config_path).exists():
            self.config = yaml.safe_load(Path(self.config_path).read_text()) or {}
        else:
            self.config = {"supply_chain": {"enabled": True}}
        return self.config

    def create_component_config(self, component: str) -> Dict[str, Any]:
        config = self.config or self.load_config()
        supply_chain = config.get("supply_chain", {})
        component_config = dict(supply_chain.get(component, {}))
        component_config.setdefault("output_dir", supply_chain.get("output_dir", ".artifacts/supply_chain"))
        if component == "sbom":
            component_config.setdefault("formats", supply_chain.get("sbom", {}).get("formats", []))
        return component_config

    def validate_config(self) -> Dict[str, Any]:
        config = self.config or self.load_config()
        return {"valid": "supply_chain" in config, "warnings": [], "errors": []}
