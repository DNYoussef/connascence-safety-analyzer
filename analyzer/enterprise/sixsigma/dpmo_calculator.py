"""
DPMO Calculator - Defects Per Million Opportunities
===================================================

Calculates Six Sigma quality metrics:
- DPMO (Defects Per Million Opportunities)
- RTY (Rolled Throughput Yield)
- Sigma Level conversion
- Process capability indices (Cp, Cpk)

@module DPMOCalculator
@compliance NASA-POT10-95%
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SigmaMetrics:
    defects: int
    opportunities: int
    dpmo: float
    sigma_level: float
    yield_percent: float
    rty: float
    cp: Optional[float] = None
    cpk: Optional[float] = None


class DPMOCalculator:
    SIGMA_TABLE = [(3.4, 6.0), (233, 5.0), (6210, 4.0), (66807, 3.0), (308538, 2.0), (691462, 1.0)]

    @staticmethod
    def calculate_dpmo(defects: int, opportunities: int, units: int = 1) -> float:
        if opportunities == 0 or units == 0:
            return 0.0

        total_opportunities = opportunities * units
        dpmo = (defects / total_opportunities) * 1_000_000

        return round(dpmo, 2)

    @staticmethod
    def dpmo_to_sigma(dpmo: float) -> float:
        for dpmo_threshold, sigma_level in DPMOCalculator.SIGMA_TABLE:
            if dpmo <= dpmo_threshold:
                return sigma_level

        return 1.0

    @staticmethod
    def sigma_to_dpmo(sigma_level: float) -> float:
        if sigma_level >= 6.0:
            return 3.4
        elif sigma_level >= 5.0:
            return 233.0
        elif sigma_level >= 4.0:
            return 6210.0
        elif sigma_level >= 3.0:
            return 66807.0
        elif sigma_level >= 2.0:
            return 308538.0
        else:
            return 691462.0

    @staticmethod
    def calculate_yield(defects: int, opportunities: int) -> float:
        if opportunities == 0:
            return 0.0

        yield_percent = ((opportunities - defects) / opportunities) * 100
        return round(yield_percent, 2)

    @staticmethod
    def calculate_rty(yields: list[float]) -> float:
        if not yields:
            return 0.0

        rty = 1.0
        for y in yields:
            rty *= y / 100

        return round(rty * 100, 2)

    @staticmethod
    def calculate_process_capability(mean: float, std_dev: float, usl: float, lsl: float) -> tuple[float, float]:
        if std_dev == 0:
            return 0.0, 0.0

        cp = (usl - lsl) / (6 * std_dev)

        cpk = min((usl - mean) / (3 * std_dev), (mean - lsl) / (3 * std_dev))

        return round(cp, 3), round(cpk, 3)

    @classmethod
    def calculate_metrics(cls, defects: int, opportunities: int, units: int = 1) -> SigmaMetrics:
        dpmo = cls.calculate_dpmo(defects, opportunities, units)
        sigma_level = cls.dpmo_to_sigma(dpmo)
        yield_percent = cls.calculate_yield(defects, opportunities * units)
        rty = yield_percent

        return SigmaMetrics(
            defects=defects,
            opportunities=opportunities,
            dpmo=dpmo,
            sigma_level=sigma_level,
            yield_percent=yield_percent,
            rty=rty,
        )


def main():
    import argparse

    parser = argparse.ArgumentParser(description="DPMO and Sigma Level Calculator")
    parser.add_argument("--defects", type=int, required=True, help="Number of defects")
    parser.add_argument("--opportunities", type=int, required=True, help="Opportunities per unit")
    parser.add_argument("--units", type=int, default=1, help="Number of units")

    args = parser.parse_args()

    metrics = DPMOCalculator.calculate_metrics(args.defects, args.opportunities, args.units)

    print("\\nSix Sigma Quality Metrics:")
    print(f"  Defects: {metrics.defects}")
    print(f"  Opportunities: {metrics.opportunities}")
    print(f"  DPMO: {metrics.dpmo:,.0f}")
    print(f"  Sigma Level: {metrics.sigma_level}")
    print(f"  Yield: {metrics.yield_percent}%")
    print(f"  RTY: {metrics.rty}%")


if __name__ == "__main__":
    main()
