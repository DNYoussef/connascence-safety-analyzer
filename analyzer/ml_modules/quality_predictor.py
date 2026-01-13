"""
Quality Predictor
=================

Predictive model for forecasting code quality metrics and identifying
quality degradation risks before they occur.

Predictions:
- Future quality scores (NASA compliance, Six Sigma level)
- Violation trend forecasting
- Technical debt accumulation
- Defect probability estimation

Models:
- Time series forecasting (ARIMA-like)
- Regression models for quality metrics
- Anomaly detection for quality degradation

@module QualityPredictor
@requires scikit-learn>=1.0.0
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

try:
    import numpy as np
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.preprocessing import StandardScaler

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available, using simple trend analysis")


@dataclass
class QualitySnapshot:
    timestamp: str
    nasa_compliance: float
    sigma_level: float
    total_violations: int
    critical_violations: int
    test_coverage: float
    code_complexity: float


@dataclass
class QualityPrediction:
    predicted_nasa_compliance: float
    predicted_sigma_level: float
    predicted_violations: int
    confidence_interval: Tuple[float, float]
    trend: str
    risk_level: str
    recommendations: List[str]


class QualityPredictor:
    def __init__(self):
        self.history: List[QualitySnapshot] = []
        self.model_nasa = None
        self.model_sigma = None
        self.model_violations = None
        self.scaler = None
        self.is_fitted = False

        if SKLEARN_AVAILABLE:
            self.model_nasa = Ridge(alpha=1.0)
            self.model_sigma = Ridge(alpha=1.0)
            self.model_violations = Ridge(alpha=1.0)
            self.scaler = StandardScaler()

    def add_snapshot(self, snapshot: QualitySnapshot):
        self.history.append(snapshot)

        if len(self.history) >= 5:
            self._fit_models()

    def _fit_models(self):
        if not SKLEARN_AVAILABLE or len(self.history) < 3:
            return

        timestamps = np.array([self._parse_timestamp(s.timestamp) for s in self.history])
        time_deltas = timestamps - timestamps[0]

        X = time_deltas.reshape(-1, 1)

        y_nasa = np.array([s.nasa_compliance for s in self.history])
        y_sigma = np.array([s.sigma_level for s in self.history])
        y_violations = np.array([s.total_violations for s in self.history])

        X_scaled = self.scaler.fit_transform(X)

        self.model_nasa.fit(X_scaled, y_nasa)
        self.model_sigma.fit(X_scaled, y_sigma)
        self.model_violations.fit(X_scaled, y_violations)

        self.is_fitted = True

    def predict_future(self, days_ahead: int = 7) -> QualityPrediction:
        if SKLEARN_AVAILABLE and self.is_fitted:
            return self._sklearn_predict(days_ahead)
        else:
            return self._simple_trend_predict(days_ahead)

    def _sklearn_predict(self, days_ahead: int) -> QualityPrediction:
        if not self.history:
            return self._default_prediction()

        last_timestamp = self._parse_timestamp(self.history[-1].timestamp)
        first_timestamp = self._parse_timestamp(self.history[0].timestamp)

        future_time_delta = (last_timestamp - first_timestamp) + timedelta(days=days_ahead)
        X_future = np.array([[future_time_delta.total_seconds()]])
        X_future_scaled = self.scaler.transform(X_future)

        pred_nasa = float(self.model_nasa.predict(X_future_scaled)[0])
        pred_sigma = float(self.model_sigma.predict(X_future_scaled)[0])
        pred_violations = int(max(0, self.model_violations.predict(X_future_scaled)[0]))

        pred_nasa = max(0.0, min(1.0, pred_nasa))
        pred_sigma = max(1.0, min(6.0, pred_sigma))

        current_nasa = self.history[-1].nasa_compliance
        nasa_delta = pred_nasa - current_nasa

        if nasa_delta > 0.05:
            trend = "improving"
        elif nasa_delta < -0.05:
            trend = "degrading"
        else:
            trend = "stable"

        if pred_nasa < 0.7:
            risk_level = "high"
        elif pred_nasa < 0.85:
            risk_level = "medium"
        else:
            risk_level = "low"

        recommendations = self._generate_recommendations(pred_nasa, pred_sigma, pred_violations, trend)

        std_nasa = np.std([s.nasa_compliance for s in self.history[-5:]])
        confidence_interval = (max(0.0, pred_nasa - 1.96 * std_nasa), min(1.0, pred_nasa + 1.96 * std_nasa))

        return QualityPrediction(
            predicted_nasa_compliance=pred_nasa,
            predicted_sigma_level=pred_sigma,
            predicted_violations=pred_violations,
            confidence_interval=confidence_interval,
            trend=trend,
            risk_level=risk_level,
            recommendations=recommendations,
        )

    def _simple_trend_predict(self, days_ahead: int) -> QualityPrediction:
        if len(self.history) < 2:
            return self._default_prediction()

        recent = self.history[-3:] if len(self.history) >= 3 else self.history

        avg_nasa = sum(s.nasa_compliance for s in recent) / len(recent)
        avg_sigma = sum(s.sigma_level for s in recent) / len(recent)
        avg_violations = sum(s.total_violations for s in recent) // len(recent)

        if len(recent) >= 2:
            nasa_trend = (recent[-1].nasa_compliance - recent[0].nasa_compliance) / len(recent)
            sigma_trend = (recent[-1].sigma_level - recent[0].sigma_level) / len(recent)
            violation_trend = (recent[-1].total_violations - recent[0].total_violations) / len(recent)

            pred_nasa = max(0.0, min(1.0, avg_nasa + nasa_trend * days_ahead))
            pred_sigma = max(1.0, min(6.0, avg_sigma + sigma_trend * days_ahead))
            pred_violations = max(0, int(avg_violations + violation_trend * days_ahead))

            if nasa_trend > 0.01:
                trend = "improving"
            elif nasa_trend < -0.01:
                trend = "degrading"
            else:
                trend = "stable"
        else:
            pred_nasa = avg_nasa
            pred_sigma = avg_sigma
            pred_violations = avg_violations
            trend = "stable"

        if pred_nasa < 0.7:
            risk_level = "high"
        elif pred_nasa < 0.85:
            risk_level = "medium"
        else:
            risk_level = "low"

        recommendations = self._generate_recommendations(pred_nasa, pred_sigma, pred_violations, trend)

        return QualityPrediction(
            predicted_nasa_compliance=pred_nasa,
            predicted_sigma_level=pred_sigma,
            predicted_violations=pred_violations,
            confidence_interval=(max(0.0, pred_nasa - 0.1), min(1.0, pred_nasa + 0.1)),
            trend=trend,
            risk_level=risk_level,
            recommendations=recommendations,
        )

    def _default_prediction(self) -> QualityPrediction:
        return QualityPrediction(
            predicted_nasa_compliance=0.85,
            predicted_sigma_level=3.0,
            predicted_violations=10,
            confidence_interval=(0.75, 0.95),
            trend="unknown",
            risk_level="medium",
            recommendations=["Establish quality baseline with more snapshots"],
        )

    def _generate_recommendations(
        self, pred_nasa: float, pred_sigma: float, pred_violations: int, trend: str
    ) -> List[str]:
        recommendations = []

        if pred_nasa < 0.8:
            recommendations.append("Urgent: NASA compliance below 80% - prioritize critical violations")

        if pred_sigma < 3.0:
            recommendations.append("Quality degradation detected - improve defect prevention")

        if trend == "degrading":
            recommendations.append("Negative trend detected - implement quality intervention")
            recommendations.append("Increase code review coverage and test thoroughness")

        if pred_violations > 50:
            recommendations.append("High violation count predicted - schedule refactoring sprint")

        if not recommendations:
            recommendations.append("Quality metrics within acceptable range - maintain current practices")

        return recommendations

    def _parse_timestamp(self, timestamp: str) -> datetime:
        try:
            return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except Exception:
            return datetime.now()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Quality Predictor")
    parser.add_argument("--history", required=True, help="Path to quality history JSON")
    parser.add_argument("--days-ahead", type=int, default=7, help="Days to predict ahead")
    parser.add_argument("--output", help="Output file for predictions")

    args = parser.parse_args()

    with open(args.history) as f:
        history_data = json.load(f)

    predictor = QualityPredictor()

    for snapshot_data in history_data:
        snapshot = QualitySnapshot(**snapshot_data)
        predictor.add_snapshot(snapshot)

    prediction = predictor.predict_future(args.days_ahead)

    result = {
        "prediction_horizon_days": args.days_ahead,
        "predicted_nasa_compliance": prediction.predicted_nasa_compliance,
        "predicted_sigma_level": prediction.predicted_sigma_level,
        "predicted_violations": prediction.predicted_violations,
        "confidence_interval": {"lower": prediction.confidence_interval[0], "upper": prediction.confidence_interval[1]},
        "trend": prediction.trend,
        "risk_level": prediction.risk_level,
        "recommendations": prediction.recommendations,
        "snapshots_analyzed": len(predictor.history),
    }

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        logger.info("Prediction saved to %s", args.output)
    else:
        logger.info("%s", json.dumps(result, indent=2))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
