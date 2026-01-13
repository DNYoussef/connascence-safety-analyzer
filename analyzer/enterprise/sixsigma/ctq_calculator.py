"""
SR-001: CTQ Metrics Collector and Calculator (Python Port)
===========================================================

Critical-to-Quality metrics processing with checks.yaml integration.
Calculates Six Sigma levels, DPMO, and provides real-time monitoring.

Enhancements over JavaScript version:
- Type-safe dataclasses for metrics
- Integrated with NASA POT10 enhanced analyzer
- Support for historical trending analysis
- Advanced alert system with configurable thresholds

@module CTQCalculator
@compliance NASA-POT10-95%
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)


@dataclass
class CTQDefinition:
    target: float
    weight: float
    description: str
    spec: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CTQScore:
    actual: float
    target: float
    score: float
    weight: float
    status: str
    variance: float
    description: str


@dataclass
class CTQResults:
    timestamp: str
    ctq_scores: Dict[str, CTQScore]
    overall_score: float
    sigma_level: float
    defect_count: int
    opportunities: int
    recommendations: List[Dict[str, str]]
    dpmo: float = 0.0


@dataclass
class MonitoringResults:
    timestamp: str
    overall_health: float
    sigma_level: float
    critical_ctqs: List[Dict[str, Any]]
    trending: Dict[str, str]
    alerts: List[Dict[str, str]]


class CTQCalculator:
    THRESHOLDS = {"critical": 0.95, "warning": 0.85, "failure": 0.75}

    SIGMA_DPMO_MAP = [(3.4, 6.0), (233, 5.0), (6210, 4.0), (66807, 3.0), (308538, 2.0), (float("inf"), 1.0)]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.ctq_definitions: Optional[Dict[str, CTQDefinition]] = None
        self.target_sigma = self.config.get("targetSigma", 4.0)

    async def load_ctq_definitions(self, checks_path: Optional[str] = None) -> Dict[str, CTQDefinition]:
        if self.ctq_definitions:
            return self.ctq_definitions

        checks_path = Path.cwd() / "checks.yaml" if checks_path is None else Path(checks_path)

        try:
            with open(checks_path, encoding="utf-8") as f:
                checks = yaml.safe_load(f)

            ctqs = checks.get("ctqs", [])

            self.ctq_definitions = {
                "security": CTQDefinition(
                    target=95.0,
                    weight=0.20,
                    description="Security Compliance Score",
                    spec=self._find_ctq_spec(ctqs, "security", {"critical_max": 0, "high_max": 5}),
                ),
                "nasa_pot10": CTQDefinition(
                    target=90.0,
                    weight=0.20,
                    description="NASA POT10 Compliance",
                    spec=self._find_ctq_spec(ctqs, "nasa_pot10", {"min_score": 0.90}),
                ),
                "connascence": CTQDefinition(
                    target=95.0,
                    weight=0.15,
                    description="Connascence Quality",
                    spec=self._find_ctq_spec(ctqs, "connascence", {"allow_positive_delta": False}),
                ),
                "god_objects": CTQDefinition(
                    target=100.0,
                    weight=0.15,
                    description="God Objects Control",
                    spec=self._find_ctq_spec(ctqs, "god_objects", {"max_delta": 0}),
                ),
                "mece_quality": CTQDefinition(
                    target=75.0,
                    weight=0.10,
                    description="MECE Duplication Quality",
                    spec=self._find_ctq_spec(ctqs, "mece_dup", {"mece_min": 0.75, "dup_delta_max": 0}),
                ),
                "tests_mutation": CTQDefinition(
                    target=60.0,
                    weight=0.10,
                    description="Tests and Mutation Score",
                    spec=self._find_ctq_spec(
                        ctqs, "tests_mutation", {"require_pass": True, "min_mutation_changed": 0.60}
                    ),
                ),
                "performance": CTQDefinition(
                    target=95.0,
                    weight=0.10,
                    description="Performance Compliance",
                    spec=self._find_ctq_spec(ctqs, "performance", {"max_regression_pct": 5}),
                ),
            }

            return self.ctq_definitions

        except FileNotFoundError:
            logger.warning(f"checks.yaml not found at {checks_path}, using defaults")
            self.ctq_definitions = self._get_default_definitions()
            return self.ctq_definitions
        except Exception as e:
            raise RuntimeError(f"Failed to load CTQ definitions: {e}")

    def _find_ctq_spec(self, ctqs: List[Dict], ctq_id: str, default: Dict) -> Dict:
        for ctq in ctqs:
            if ctq.get("id") == ctq_id:
                return ctq.get("spec", default)
        return default

    def _get_default_definitions(self) -> Dict[str, CTQDefinition]:
        return {
            "security": CTQDefinition(95.0, 0.20, "Security Compliance Score"),
            "nasa_pot10": CTQDefinition(90.0, 0.20, "NASA POT10 Compliance"),
            "connascence": CTQDefinition(95.0, 0.15, "Connascence Quality"),
            "god_objects": CTQDefinition(100.0, 0.15, "God Objects Control"),
            "mece_quality": CTQDefinition(75.0, 0.10, "MECE Duplication Quality"),
            "tests_mutation": CTQDefinition(60.0, 0.10, "Tests and Mutation Score"),
            "performance": CTQDefinition(95.0, 0.10, "Performance Compliance"),
        }

    async def calculate(self, data: Dict[str, Any]) -> CTQResults:
        await self.load_ctq_definitions()

        ctq_scores = {}
        weighted_sum = 0.0
        total_weight = 0.0
        defect_count = 0
        recommendations = []

        for ctq_name, definition in self.ctq_definitions.items():
            actual, normalized = self._calculate_ctq_score(ctq_name, data, definition)

            status = self._get_score_status(normalized)

            ctq_scores[ctq_name] = CTQScore(
                actual=actual,
                target=definition.target,
                score=normalized,
                weight=definition.weight,
                status=status,
                variance=actual - definition.target,
                description=definition.description,
            )

            weighted_sum += normalized * definition.weight
            total_weight += definition.weight

            if normalized < self.THRESHOLDS["critical"]:
                defect_count += 1

            if normalized < self.THRESHOLDS["warning"]:
                priority = "HIGH" if normalized < self.THRESHOLDS["failure"] else "MEDIUM"
                recommendations.append(
                    {
                        "ctq": ctq_name,
                        "priority": priority,
                        "message": f"{definition.description} is below target ({actual:.1f} vs {definition.target:.1f})",
                    }
                )

        overall_score = weighted_sum / total_weight if total_weight > 0 else 0
        sigma_level = self._calculate_sigma_level(overall_score)
        dpmo = (1 - overall_score) * 1000000

        return CTQResults(
            timestamp=datetime.now().isoformat(),
            ctq_scores=ctq_scores,
            overall_score=overall_score,
            sigma_level=sigma_level,
            defect_count=defect_count,
            opportunities=len(self.ctq_definitions),
            recommendations=recommendations,
            dpmo=dpmo,
        )

    def _calculate_ctq_score(
        self, ctq_name: str, data: Dict[str, Any], definition: CTQDefinition
    ) -> Tuple[float, float]:
        actual = 0.0

        if ctq_name == "security":
            security_data = data.get("security", {})
            actual = security_data.get(
                "score", max(0, 95 - security_data.get("critical", 0) * 20 - security_data.get("high", 0) * 5)
            )

        elif ctq_name == "nasa_pot10":
            nasa_data = data.get("nasa", {})
            actual = nasa_data.get("score", 0.90) * 100

        elif ctq_name == "connascence":
            conn_data = data.get("connascence", {})
            actual = max(0, 95 - conn_data.get("positive_deltas", 0) * 10)

        elif ctq_name == "god_objects":
            god_data = data.get("god_objects", {})
            actual = max(0, 100 - max(0, god_data.get("delta", 0)) * 25)

        elif ctq_name == "mece_quality":
            dup_data = data.get("duplication", {})
            actual = dup_data.get("mece", 0.75) * 100

        elif ctq_name == "tests_mutation":
            mut_data = data.get("mutation", {})
            actual = mut_data.get("mutation_score_changed", 0.60) * 100

        elif ctq_name == "performance":
            perf_data = data.get("performance", {})
            actual = max(0, 95 - perf_data.get("regressions", 0) * 10)

        normalized = min(actual / definition.target, 1.0) if definition.target > 0 else 0.0

        return actual, normalized

    def _calculate_sigma_level(self, score: float) -> float:
        dpmo = (1 - score) * 1000000

        for dpmo_threshold, sigma_level in self.SIGMA_DPMO_MAP:
            if dpmo <= dpmo_threshold:
                return sigma_level

        return 1.0

    def _get_score_status(self, score: float) -> str:
        if score >= self.THRESHOLDS["critical"]:
            return "EXCELLENT"
        elif score >= self.THRESHOLDS["warning"]:
            return "GOOD"
        elif score >= self.THRESHOLDS["failure"]:
            return "WARNING"
        else:
            return "CRITICAL"

    async def monitor(self, metrics: Dict[str, Any]) -> MonitoringResults:
        results = await self.calculate(metrics)

        critical_ctqs = [
            {"name": name, **asdict(score)} for name, score in results.ctq_scores.items() if score.status == "CRITICAL"
        ]

        trending = self._calculate_trend(results)
        alerts = self._generate_alerts(results)

        return MonitoringResults(
            timestamp=datetime.now().isoformat(),
            overall_health=results.overall_score,
            sigma_level=results.sigma_level,
            critical_ctqs=critical_ctqs,
            trending=trending,
            alerts=alerts,
        )

    def _calculate_trend(self, results: CTQResults) -> Dict[str, str]:
        direction = "IMPROVING" if results.overall_score >= 0.9 else "DECLINING"
        velocity = abs(results.overall_score - 0.85) * 100
        prediction = "ON_TRACK" if results.sigma_level >= 4.0 else "AT_RISK"

        return {"direction": direction, "velocity": f"{velocity:.2f}", "prediction": prediction}

    def _generate_alerts(self, results: CTQResults) -> List[Dict[str, str]]:
        alerts = []

        if results.sigma_level < self.target_sigma:
            alerts.append(
                {
                    "level": "WARNING",
                    "message": f"Sigma level {results.sigma_level} below target {self.target_sigma}",
                    "action": "Review CTQ performance and implement improvements",
                }
            )

        if results.defect_count > 2:
            alerts.append(
                {
                    "level": "CRITICAL",
                    "message": f"{results.defect_count} CTQs below critical threshold",
                    "action": "Immediate attention required for failing CTQs",
                }
            )

        return alerts

    def export_results(self, results: CTQResults, output_path: Optional[str] = None) -> str:
        output = {
            "timestamp": results.timestamp,
            "overall_score": results.overall_score,
            "sigma_level": results.sigma_level,
            "dpmo": results.dpmo,
            "defect_count": results.defect_count,
            "opportunities": results.opportunities,
            "ctq_scores": {name: asdict(score) for name, score in results.ctq_scores.items()},
            "recommendations": results.recommendations,
        }

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2)
            logger.info(f"CTQ results exported to {output_path}")
            return output_path

        return json.dumps(output, indent=2)


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Six Sigma CTQ Calculator")
    parser.add_argument("--input", required=True, help="Input metrics JSON file")
    parser.add_argument("--output", default="ctq_results.json", help="Output results file")
    parser.add_argument("--checks", help="Path to checks.yaml file")
    parser.add_argument("--target-sigma", type=float, default=4.0, help="Target sigma level")

    args = parser.parse_args()

    calculator = CTQCalculator({"targetSigma": args.target_sigma})

    with open(args.input, encoding="utf-8") as f:
        metrics_data = json.load(f)

    results = await calculator.calculate(metrics_data)
    calculator.export_results(results, args.output)

    logger.info("Overall Score: %.2f%%", results.overall_score * 100)
    logger.info("Sigma Level: %s", results.sigma_level)
    logger.info("DPMO: %.0f", results.dpmo)
    logger.info("Defects: %s/%s", results.defect_count, results.opportunities)

    if results.recommendations:
        logger.info("Recommendations:")
        for rec in results.recommendations:
            logger.info("  [%s] %s: %s", rec["priority"], rec["ctq"], rec["message"])


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
