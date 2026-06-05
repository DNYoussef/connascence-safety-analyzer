"""Non-breaking supply-chain integration helpers."""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict

from .supply_chain_analyzer import SupplyChainAnalyzer


class SupplyChainIntegration:
    def __init__(self, config_path: str | None = None) -> None:
        self.config = {"supply_chain": {}, "integration": {"non_breaking": True}}
        self.integration_config = self.config["integration"]
        self.quality_gates = self.integration_config.get("quality_gates", {})
        self.sc_analyzer = SupplyChainAnalyzer(self.config["supply_chain"])

    def integrate_with_analyzer(
        self, analysis_callback: Callable[[Any, str], Any], project_path: str
    ) -> Dict[str, Any]:
        warnings = []
        try:
            analysis_callback(self, project_path)
        except Exception as exc:
            warnings.append(str(exc))
        return {
            "integration_status": "SUCCESS" if self.integration_config.get("non_breaking", True) else "ERROR",
            "non_breaking_mode": self.integration_config.get("non_breaking", True),
            "warnings": warnings,
        }

    def _apply_quality_gates(self, sc_results: Dict[str, Any]) -> Dict[str, Any]:
        gates = self.quality_gates
        blocking = []
        vulnerabilities = sc_results.get("vulnerabilities", {})
        summary = vulnerabilities.get("summary", {})
        if gates.get("fail_on_critical_vulnerabilities") and summary.get("critical", 0) > gates.get("max_critical_vulnerabilities", 0):
            blocking.append("Critical vulnerabilities exceed threshold")
        for violation in vulnerabilities.get("license_compliance", {}).get("violations", []):
            if gates.get("fail_on_prohibited_licenses") and violation.get("violation_type") == "prohibited":
                blocking.append(f"Prohibited license: {violation.get('license')}")
        return {
            "enabled": gates.get("enabled", False),
            "overall_status": "FAIL" if blocking else "PASS",
            "blocking_failures": blocking,
        }

    def get_integration_status(self) -> Dict[str, str]:
        return {"overall_health": "HEALTHY"}


class SupplyChainAdapter:
    def __init__(self, integration: SupplyChainIntegration) -> None:
        self.integration = integration

    def __call__(self, project_path: str) -> Dict[str, Any]:
        return self.analyze(project_path)

    def analyze(self, project_path: str) -> Dict[str, Any]:
        try:
            result = asyncio.run(self.integration.sc_analyzer.analyze_supply_chain(project_path))
            return {"integration_status": "SUCCESS", "result": result}
        except Exception as exc:
            return {"integration_status": "ERROR", "error": str(exc)}

    def is_healthy(self) -> bool:
        return self.integration.get_integration_status().get("overall_health") == "HEALTHY"
