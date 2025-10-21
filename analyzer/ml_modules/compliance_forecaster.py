"""
Compliance Forecaster
=====================

Forecasts compliance metrics and certification readiness for defense industry
standards (NASA POT10, DFARS, NIST-SSDF, etc.).

Forecasting Capabilities:
- NASA POT10 compliance trajectory
- Defense certification readiness timeline
- Compliance gap analysis and remediation estimates
- Audit risk assessment

@module ComplianceForecaster
@compliance NASA-POT10, DFARS, NIST-SSDF
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import numpy as np
    from sklearn.linear_model import LinearRegression

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available, using rule-based forecasting")


@dataclass
class ComplianceSnapshot:
    timestamp: str
    nasa_compliance: float
    code_compliance: float
    testing_compliance: float
    security_compliance: float
    documentation_compliance: float
    critical_violations: int
    high_violations: int


@dataclass
class ComplianceForecast:
    target_date: str
    forecasted_overall_compliance: float
    forecasted_category_compliance: Dict[str, float]
    certification_readiness: str
    estimated_remediation_days: int
    compliance_gaps: List[Dict[str, any]]
    recommendations: List[str]


class ComplianceForecaster:
    CERTIFICATION_THRESHOLD = 0.95
    CATEGORIES = ["code", "testing", "security", "documentation"]

    def __init__(self):
        self.history: List[ComplianceSnapshot] = []
        self.models: Dict[str, any] = {}
        self.is_fitted = False

        if SKLEARN_AVAILABLE:
            for category in ["overall", *self.CATEGORIES]:
                self.models[category] = LinearRegression()

    def add_snapshot(self, snapshot: ComplianceSnapshot):
        self.history.append(snapshot)

        if len(self.history) >= 3:
            self._fit_models()

    def _fit_models(self):
        if not SKLEARN_AVAILABLE or len(self.history) < 3:
            return

        timestamps = np.array([self._parse_timestamp(s.timestamp).timestamp() for s in self.history])
        X = timestamps.reshape(-1, 1)

        y_overall = np.array([s.nasa_compliance for s in self.history])
        self.models["overall"].fit(X, y_overall)

        y_code = np.array([s.code_compliance for s in self.history])
        self.models["code"].fit(X, y_code)

        y_testing = np.array([s.testing_compliance for s in self.history])
        self.models["testing"].fit(X, y_testing)

        y_security = np.array([s.security_compliance for s in self.history])
        self.models["security"].fit(X, y_security)

        y_documentation = np.array([s.documentation_compliance for s in self.history])
        self.models["documentation"].fit(X, y_documentation)

        self.is_fitted = True

    def forecast(self, target_date: Optional[str] = None, days_ahead: int = 30) -> ComplianceForecast:
        target_dt = self._parse_timestamp(target_date) if target_date else datetime.now() + timedelta(days=days_ahead)

        if SKLEARN_AVAILABLE and self.is_fitted:
            return self._sklearn_forecast(target_dt)
        else:
            return self._simple_forecast(target_dt)

    def _sklearn_forecast(self, target_dt: datetime) -> ComplianceForecast:
        if not self.history:
            return self._default_forecast(target_dt)

        X_future = np.array([[target_dt.timestamp()]])

        forecasted_overall = float(self.models["overall"].predict(X_future)[0])
        forecasted_overall = max(0.0, min(1.0, forecasted_overall))

        forecasted_categories = {}
        for category in self.CATEGORIES:
            pred = float(self.models[category].predict(X_future)[0])
            forecasted_categories[category] = max(0.0, min(1.0, pred))

        compliance_gaps = self._identify_gaps(forecasted_overall, forecasted_categories)

        if forecasted_overall >= self.CERTIFICATION_THRESHOLD:
            readiness = "ready"
            remediation_days = 0
        elif forecasted_overall >= 0.90:
            readiness = "nearly_ready"
            remediation_days = self._estimate_remediation_days(forecasted_overall, target_dt)
        elif forecasted_overall >= 0.80:
            readiness = "in_progress"
            remediation_days = self._estimate_remediation_days(forecasted_overall, target_dt)
        else:
            readiness = "not_ready"
            remediation_days = self._estimate_remediation_days(forecasted_overall, target_dt)

        recommendations = self._generate_recommendations(forecasted_categories, compliance_gaps)

        return ComplianceForecast(
            target_date=target_dt.isoformat(),
            forecasted_overall_compliance=forecasted_overall,
            forecasted_category_compliance=forecasted_categories,
            certification_readiness=readiness,
            estimated_remediation_days=remediation_days,
            compliance_gaps=compliance_gaps,
            recommendations=recommendations,
        )

    def _simple_forecast(self, target_dt: datetime) -> ComplianceForecast:
        if len(self.history) < 2:
            return self._default_forecast(target_dt)

        recent = self.history[-3:] if len(self.history) >= 3 else self.history

        avg_overall = sum(s.nasa_compliance for s in recent) / len(recent)
        avg_code = sum(s.code_compliance for s in recent) / len(recent)
        avg_testing = sum(s.testing_compliance for s in recent) / len(recent)
        avg_security = sum(s.security_compliance for s in recent) / len(recent)
        avg_documentation = sum(s.documentation_compliance for s in recent) / len(recent)

        if len(recent) >= 2:
            days_elapsed = (
                self._parse_timestamp(recent[-1].timestamp) - self._parse_timestamp(recent[0].timestamp)
            ).days or 1
            overall_trend = (recent[-1].nasa_compliance - recent[0].nasa_compliance) / days_elapsed

            days_to_target = (target_dt - self._parse_timestamp(recent[-1].timestamp)).days
            forecasted_overall = max(0.0, min(1.0, avg_overall + overall_trend * days_to_target))
        else:
            forecasted_overall = avg_overall

        forecasted_categories = {
            "code": avg_code,
            "testing": avg_testing,
            "security": avg_security,
            "documentation": avg_documentation,
        }

        compliance_gaps = self._identify_gaps(forecasted_overall, forecasted_categories)

        if forecasted_overall >= self.CERTIFICATION_THRESHOLD:
            readiness = "ready"
            remediation_days = 0
        elif forecasted_overall >= 0.90:
            readiness = "nearly_ready"
            remediation_days = 14
        elif forecasted_overall >= 0.80:
            readiness = "in_progress"
            remediation_days = 30
        else:
            readiness = "not_ready"
            remediation_days = 60

        recommendations = self._generate_recommendations(forecasted_categories, compliance_gaps)

        return ComplianceForecast(
            target_date=target_dt.isoformat(),
            forecasted_overall_compliance=forecasted_overall,
            forecasted_category_compliance=forecasted_categories,
            certification_readiness=readiness,
            estimated_remediation_days=remediation_days,
            compliance_gaps=compliance_gaps,
            recommendations=recommendations,
        )

    def _identify_gaps(self, overall: float, categories: Dict[str, float]) -> List[Dict[str, any]]:
        gaps = []

        if overall < self.CERTIFICATION_THRESHOLD:
            gaps.append(
                {
                    "category": "overall",
                    "current": overall,
                    "target": self.CERTIFICATION_THRESHOLD,
                    "gap": self.CERTIFICATION_THRESHOLD - overall,
                    "severity": "critical" if overall < 0.80 else "high",
                }
            )

        for category, score in categories.items():
            if score < self.CERTIFICATION_THRESHOLD:
                gaps.append(
                    {
                        "category": category,
                        "current": score,
                        "target": self.CERTIFICATION_THRESHOLD,
                        "gap": self.CERTIFICATION_THRESHOLD - score,
                        "severity": "critical" if score < 0.80 else "high" if score < 0.90 else "medium",
                    }
                )

        return sorted(gaps, key=lambda x: x["gap"], reverse=True)

    def _estimate_remediation_days(self, current_compliance: float, target_dt: datetime) -> int:
        gap = self.CERTIFICATION_THRESHOLD - current_compliance

        if gap <= 0:
            return 0

        avg_velocity = self._calculate_improvement_velocity()

        if avg_velocity > 0:
            days_needed = int(gap / avg_velocity)
            return max(0, days_needed)
        elif gap < 0.05:
            return 7
        elif gap < 0.10:
            return 21
        else:
            return 60

    def _calculate_improvement_velocity(self) -> float:
        if len(self.history) < 2:
            return 0.0

        recent = self.history[-5:] if len(self.history) >= 5 else self.history

        if len(recent) < 2:
            return 0.0

        days = (self._parse_timestamp(recent[-1].timestamp) - self._parse_timestamp(recent[0].timestamp)).days or 1
        compliance_delta = recent[-1].nasa_compliance - recent[0].nasa_compliance

        return compliance_delta / days

    def _generate_recommendations(self, categories: Dict[str, float], gaps: List[Dict[str, any]]) -> List[str]:
        recommendations = []

        for gap in gaps[:3]:
            category = gap["category"]
            severity = gap["severity"]

            if category == "code":
                if severity == "critical":
                    recommendations.append("URGENT: Address critical code quality violations immediately")
                else:
                    recommendations.append("Refactor code to meet NASA POT10 standards")

            elif category == "testing":
                if severity == "critical":
                    recommendations.append("URGENT: Increase test coverage to minimum 80%")
                else:
                    recommendations.append("Enhance test suite with edge case coverage")

            elif category == "security":
                if severity == "critical":
                    recommendations.append("URGENT: Remediate critical security vulnerabilities")
                else:
                    recommendations.append("Complete security audit and vulnerability assessment")

            elif category == "documentation":
                recommendations.append("Improve documentation coverage for compliance audit")

        if not gaps:
            recommendations.append("Maintain current compliance practices for certification readiness")

        return recommendations

    def _default_forecast(self, target_dt: datetime) -> ComplianceForecast:
        return ComplianceForecast(
            target_date=target_dt.isoformat(),
            forecasted_overall_compliance=0.85,
            forecasted_category_compliance={"code": 0.85, "testing": 0.80, "security": 0.90, "documentation": 0.80},
            certification_readiness="in_progress",
            estimated_remediation_days=30,
            compliance_gaps=[],
            recommendations=["Establish compliance baseline with more snapshots"],
        )

    def _parse_timestamp(self, timestamp: str) -> datetime:
        try:
            return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except Exception:
            return datetime.now()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Compliance Forecaster")
    parser.add_argument("--history", required=True, help="Path to compliance history JSON")
    parser.add_argument("--target-date", help="Target certification date (ISO format)")
    parser.add_argument("--days-ahead", type=int, default=30, help="Days to forecast ahead")
    parser.add_argument("--output", help="Output file for forecast")

    args = parser.parse_args()

    with open(args.history) as f:
        history_data = json.load(f)

    forecaster = ComplianceForecaster()

    for snapshot_data in history_data:
        snapshot = ComplianceSnapshot(**snapshot_data)
        forecaster.add_snapshot(snapshot)

    forecast = forecaster.forecast(target_date=args.target_date, days_ahead=args.days_ahead)

    result = {
        "target_date": forecast.target_date,
        "forecasted_overall_compliance": f"{forecast.forecasted_overall_compliance:.1%}",
        "forecasted_category_compliance": {k: f"{v:.1%}" for k, v in forecast.forecasted_category_compliance.items()},
        "certification_readiness": forecast.certification_readiness,
        "estimated_remediation_days": forecast.estimated_remediation_days,
        "compliance_gaps": forecast.compliance_gaps,
        "recommendations": forecast.recommendations,
        "snapshots_analyzed": len(forecaster.history),
    }

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Forecast saved to {args.output}")
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
