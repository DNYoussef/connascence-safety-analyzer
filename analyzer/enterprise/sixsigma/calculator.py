"""
Critical To Quality (CTQ) Calculator and Process Capability Analysis

Provides advanced Six Sigma calculations for connascence analysis.
"""

from dataclasses import dataclass
import logging
import math
import statistics
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class CTQMetric:
    """Critical To Quality metric"""

    name: str
    value: float
    target: float
    lower_spec: float
    upper_spec: float
    weight: float
    status: str  # 'pass', 'warning', 'fail'


class CTQCalculator:
    """
    Calculate Critical To Quality metrics for connascence analysis

    CTQ metrics identify the most important quality characteristics
    that directly impact customer satisfaction and system reliability.
    """

    # Default CTQ metrics for software quality
    DEFAULT_METRICS = {
        "maintainability_index": {"target": 80.0, "lower_spec": 60.0, "upper_spec": 100.0, "weight": 0.20},
        "cyclomatic_complexity": {"target": 5.0, "lower_spec": 1.0, "upper_spec": 10.0, "weight": 0.15},
        "coupling_factor": {"target": 0.2, "lower_spec": 0.0, "upper_spec": 0.5, "weight": 0.25},
        "cohesion_score": {"target": 0.8, "lower_spec": 0.5, "upper_spec": 1.0, "weight": 0.15},
        "duplication_ratio": {"target": 0.05, "lower_spec": 0.0, "upper_spec": 0.15, "weight": 0.10},
        "test_coverage": {"target": 85.0, "lower_spec": 70.0, "upper_spec": 100.0, "weight": 0.15},
    }

    def __init__(self, custom_metrics: Optional[Dict[str, Dict]] = None):
        """
        Initialize CTQ calculator

        Args:
            custom_metrics: Optional custom CTQ metrics configuration
        """
        self.metrics_config = custom_metrics or self.DEFAULT_METRICS
        self.calculated_metrics = []

    def calculate_from_violations(self, violations: List[Dict[str, Any]]) -> Dict[str, CTQMetric]:
        """
        Calculate CTQ metrics from connascence violations

        Args:
            violations: List of connascence violations

        Returns:
            Dictionary of calculated CTQ metrics
        """
        metrics = {}

        # Calculate maintainability index based on violations
        maintainability = self._calculate_maintainability(violations)
        metrics["maintainability_index"] = self._create_metric("maintainability_index", maintainability)

        # Calculate complexity from algorithm/execution violations
        complexity = self._calculate_complexity(violations)
        metrics["cyclomatic_complexity"] = self._create_metric("cyclomatic_complexity", complexity)

        # Calculate coupling from identity/type violations
        coupling = self._calculate_coupling(violations)
        metrics["coupling_factor"] = self._create_metric("coupling_factor", coupling)

        # Calculate cohesion from meaning/convention violations
        cohesion = self._calculate_cohesion(violations)
        metrics["cohesion_score"] = self._create_metric("cohesion_score", cohesion)

        # Calculate duplication from algorithm violations
        duplication = self._calculate_duplication(violations)
        metrics["duplication_ratio"] = self._create_metric("duplication_ratio", duplication)

        # Placeholder for test coverage (would need actual test data)
        test_coverage = 75.0  # Default assumption
        metrics["test_coverage"] = self._create_metric("test_coverage", test_coverage)

        self.calculated_metrics = list(metrics.values())
        return metrics

    def _create_metric(self, name: str, value: float) -> CTQMetric:
        """Create a CTQ metric with status evaluation"""
        config = self.metrics_config[name]

        # Determine status
        if config["lower_spec"] <= value <= config["upper_spec"]:
            if abs(value - config["target"]) / (config["upper_spec"] - config["lower_spec"]) < 0.1:
                status = "pass"
            else:
                status = "warning"
        else:
            status = "fail"

        return CTQMetric(
            name=name,
            value=round(value, 2),
            target=config["target"],
            lower_spec=config["lower_spec"],
            upper_spec=config["upper_spec"],
            weight=config["weight"],
            status=status,
        )

    def _calculate_maintainability(self, violations: List[Dict]) -> float:
        """Calculate maintainability index from violations"""
        if not violations:
            return 100.0  # Perfect maintainability

        # Base score of 100, reduced by violations
        score = 100.0

        severity_impact = {"critical": 10.0, "high": 5.0, "medium": 2.0, "low": 0.5}

        for violation in violations:
            severity = violation.get("severity", "low").lower()
            score -= severity_impact.get(severity, 1.0)

        return max(0.0, score)

    def _calculate_complexity(self, violations: List[Dict]) -> float:
        """Calculate complexity metric from violations"""
        # Count algorithm and execution violations as complexity indicators
        complexity_violations = [v for v in violations if v.get("type") in ["algorithm", "execution", "timing"]]

        # Estimate cyclomatic complexity
        base_complexity = 5.0
        additional = len(complexity_violations) * 0.5
        return min(20.0, base_complexity + additional)

    def _calculate_coupling(self, violations: List[Dict]) -> float:
        """Calculate coupling factor from violations"""
        # Count identity and type violations as coupling indicators
        coupling_violations = [v for v in violations if v.get("type") in ["identity", "type", "position"]]

        if not violations:
            return 0.0

        # Coupling factor = coupling violations / total violations
        return min(1.0, len(coupling_violations) / (len(violations) * 2))

    def _calculate_cohesion(self, violations: List[Dict]) -> float:
        """Calculate cohesion score from violations"""
        # Meaning and convention violations indicate poor cohesion
        cohesion_violations = [v for v in violations if v.get("type") in ["meaning", "convention", "values"]]

        if not violations:
            return 1.0  # Perfect cohesion

        # Cohesion = 1 - (cohesion violations / total violations)
        poor_cohesion_ratio = len(cohesion_violations) / len(violations)
        return max(0.0, 1.0 - poor_cohesion_ratio)

    def _calculate_duplication(self, violations: List[Dict]) -> float:
        """Calculate duplication ratio from violations"""
        # Algorithm violations often indicate duplication
        duplication_violations = [v for v in violations if v.get("type") == "algorithm"]

        if not violations:
            return 0.0

        # Rough estimate of duplication ratio
        return min(1.0, len(duplication_violations) / (len(violations) * 5))

    def calculate_composite_score(self) -> float:
        """Calculate weighted composite CTQ score"""
        if not self.calculated_metrics:
            return 0.0

        total_score = 0.0
        total_weight = 0.0

        for metric in self.calculated_metrics:
            # Normalize metric value to 0-1 scale
            range_size = metric.upper_spec - metric.lower_spec
            if range_size > 0:
                normalized = (metric.value - metric.lower_spec) / range_size
                # Invert if lower is better (like complexity)
                if metric.name in ["cyclomatic_complexity", "coupling_factor", "duplication_ratio"]:
                    normalized = 1.0 - normalized

                normalized = max(0.0, min(1.0, normalized))
                total_score += normalized * metric.weight
                total_weight += metric.weight

        if total_weight > 0:
            return round((total_score / total_weight) * 100, 2)
        return 0.0

    def get_improvement_priorities(self) -> List[Tuple[str, float]]:
        """Get prioritized list of metrics needing improvement"""
        priorities = []

        for metric in self.calculated_metrics:
            if metric.status != "pass":
                # Calculate distance from target
                distance = abs(metric.value - metric.target)
                range_size = metric.upper_spec - metric.lower_spec
                if range_size > 0:
                    normalized_distance = distance / range_size
                    # Weight by importance
                    priority_score = normalized_distance * metric.weight
                    priorities.append((metric.name, priority_score))

        return sorted(priorities, key=lambda x: x[1], reverse=True)


class ProcessCapability:
    """
    Process Capability analysis for software development processes

    Calculates Cp, Cpk, Pp, Ppk and other process capability indices.
    """

    @staticmethod
    def calculate_cp(measurements: List[float], lower_spec: float, upper_spec: float) -> float:
        """
        Calculate Process Capability (Cp)

        Cp = (USL - LSL) / (6 * sigma)
        Measures the potential capability of the process
        """
        if len(measurements) < 2:
            return 0.0

        std_dev = statistics.stdev(measurements)
        if std_dev == 0:
            return float("inf")

        cp = (upper_spec - lower_spec) / (6 * std_dev)
        return round(cp, 3)

    @staticmethod
    def calculate_cpk(measurements: List[float], lower_spec: float, upper_spec: float) -> float:
        """
        Calculate Process Capability Index (Cpk)

        Cpk = min((USL - mean) / (3 * sigma), (mean - LSL) / (3 * sigma))
        Measures the actual capability considering process centering
        """
        if len(measurements) < 2:
            return 0.0

        mean_val = statistics.mean(measurements)
        std_dev = statistics.stdev(measurements)

        if std_dev == 0:
            return float("inf")

        cpu = (upper_spec - mean_val) / (3 * std_dev)
        cpl = (mean_val - lower_spec) / (3 * std_dev)
        cpk = min(cpu, cpl)

        return round(cpk, 3)

    @staticmethod
    def calculate_pp(measurements: List[float], lower_spec: float, upper_spec: float) -> float:
        """
        Calculate Process Performance (Pp)

        Similar to Cp but uses overall standard deviation
        """
        if len(measurements) < 2:
            return 0.0

        # Use overall standard deviation (population)
        mean_val = statistics.mean(measurements)
        variance = sum((x - mean_val) ** 2 for x in measurements) / len(measurements)
        std_dev = math.sqrt(variance)

        if std_dev == 0:
            return float("inf")

        pp = (upper_spec - lower_spec) / (6 * std_dev)
        return round(pp, 3)

    @staticmethod
    def calculate_ppk(measurements: List[float], lower_spec: float, upper_spec: float) -> float:
        """
        Calculate Process Performance Index (Ppk)

        Similar to Cpk but uses overall standard deviation
        """
        if len(measurements) < 2:
            return 0.0

        mean_val = statistics.mean(measurements)
        # Use overall standard deviation (population)
        variance = sum((x - mean_val) ** 2 for x in measurements) / len(measurements)
        std_dev = math.sqrt(variance)

        if std_dev == 0:
            return float("inf")

        ppu = (upper_spec - mean_val) / (3 * std_dev)
        ppl = (mean_val - lower_spec) / (3 * std_dev)
        ppk = min(ppu, ppl)

        return round(ppk, 3)

    @staticmethod
    def calculate_sigma_level_from_cpk(cpk: float) -> float:
        """
        Convert Cpk to approximate Sigma level

        Sigma Level  3 * Cpk
        """
        return round(3 * cpk, 1)

    def analyze_process(
        self, measurements: List[float], lower_spec: float, upper_spec: float, target: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive process capability analysis

        Args:
            measurements: Process measurements
            lower_spec: Lower specification limit
            upper_spec: Upper specification limit
            target: Target value (optional)

        Returns:
            Dictionary with all capability indices and interpretation
        """
        if len(measurements) < 2:
            return {"error": "Insufficient data for analysis (need at least 2 measurements)"}

        # Calculate basic statistics
        mean_val = statistics.mean(measurements)
        std_dev = statistics.stdev(measurements)
        median_val = statistics.median(measurements)

        # Calculate capability indices
        cp = self.calculate_cp(measurements, lower_spec, upper_spec)
        cpk = self.calculate_cpk(measurements, lower_spec, upper_spec)
        pp = self.calculate_pp(measurements, lower_spec, upper_spec)
        ppk = self.calculate_ppk(measurements, lower_spec, upper_spec)

        # Calculate sigma level
        sigma_level = self.calculate_sigma_level_from_cpk(cpk)

        # Process centering
        if target is None:
            target = (upper_spec + lower_spec) / 2

        centering = 1 - abs(mean_val - target) / ((upper_spec - lower_spec) / 2)
        centering = max(0, min(1, centering))

        # Interpret capability
        capability_rating = self._interpret_capability(cpk)

        # Calculate defect rate prediction
        if std_dev > 0:
            z_upper = (upper_spec - mean_val) / std_dev
            z_lower = (mean_val - lower_spec) / std_dev
            # Approximate defect rate
            defect_rate = self._estimate_defect_rate(min(z_upper, z_lower))
        else:
            defect_rate = 0.0

        return {
            "statistics": {
                "mean": round(mean_val, 3),
                "median": round(median_val, 3),
                "std_dev": round(std_dev, 3),
                "min": round(min(measurements), 3),
                "max": round(max(measurements), 3),
            },
            "capability_indices": {
                "cp": cp,
                "cpk": cpk,
                "pp": pp,
                "ppk": ppk,
                "cpm": round(cpk * centering, 3),  # Taguchi capability index
            },
            "performance": {
                "sigma_level": sigma_level,
                "process_centering": round(centering * 100, 1),
                "capability_rating": capability_rating,
                "predicted_dpmo": round(defect_rate * 1_000_000, 2),
            },
            "recommendations": self._generate_recommendations(cp, cpk, centering),
        }

    def _interpret_capability(self, cpk: float) -> str:
        """Interpret Cpk value"""
        if cpk >= 2.0:
            return "World Class"
        elif cpk >= 1.67:
            return "Excellent"
        elif cpk >= 1.33:
            return "Capable"
        elif cpk >= 1.0:
            return "Acceptable"
        elif cpk >= 0.67:
            return "Poor"
        else:
            return "Incapable"

    def _estimate_defect_rate(self, z_score: float) -> float:
        """Estimate defect rate from Z-score"""
        # Simplified normal distribution approximation
        if z_score >= 6:
            return 0.0000034  # 3.4 DPMO
        elif z_score >= 5:
            return 0.000233
        elif z_score >= 4:
            return 0.00621
        elif z_score >= 3:
            return 0.0668
        elif z_score >= 2:
            return 0.3085
        elif z_score >= 1:
            return 0.6915
        else:
            return 1.0

    def _generate_recommendations(self, cp: float, cpk: float, centering: float) -> List[str]:
        """Generate process improvement recommendations"""
        recommendations = []

        # Capability recommendations
        if cpk < 1.0:
            recommendations.append("Process is not capable - immediate improvement required")
        elif cpk < 1.33:
            recommendations.append("Improve process capability to reach industry standard (Cpk ≥ 1.33)")

        # Variation recommendations
        if cp > cpk * 1.2:
            recommendations.append("Process is off-center - adjust mean towards target")
        if cp < 1.33:
            recommendations.append("Reduce process variation to improve capability")

        # Centering recommendations
        if centering < 0.8:
            recommendations.append(f"Improve process centering (currently {centering*100:.0f}%)")

        # General recommendations
        if cpk >= 1.67:
            recommendations.append("Maintain current excellent performance")
            recommendations.append("Consider tightening specifications for continuous improvement")

        return recommendations
