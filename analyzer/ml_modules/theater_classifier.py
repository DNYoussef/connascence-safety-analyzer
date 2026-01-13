"""
ML Theater Classifier
=====================

Machine learning classifier for detecting performance theater patterns
in code quality reports and development workflows.

Features:
- Pattern-based feature extraction from theater detection
- Supervised classification (theater vs authentic)
- Confidence scoring with probability estimates
- Training from historical theater patterns
- Real-time prediction on new code changes

Models:
- Gradient Boosting (primary)
- Random Forest (ensemble)
- Logistic Regression (baseline)

@module TheaterClassifier
@requires scikit-learn>=1.0.0
"""

from dataclasses import dataclass
import json
import logging
from pathlib import Path
import pickle
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

try:
    import numpy as np
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import classification_report, confusion_matrix
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available, using rule-based fallback")


@dataclass
class TheaterFeatures:
    test_gaming_score: float = 0.0
    error_masking_score: float = 0.0
    metrics_inflation_score: float = 0.0
    documentation_theater_score: float = 0.0
    quality_facade_score: float = 0.0

    empty_test_ratio: float = 0.0
    assert_true_ratio: float = 0.0
    bare_except_ratio: float = 0.0
    hardcoded_metrics_ratio: float = 0.0
    cosmetic_changes_ratio: float = 0.0

    total_violations: int = 0
    critical_violations: int = 0
    violation_density: float = 0.0

    def to_vector(self) -> List[float]:
        return [
            self.test_gaming_score,
            self.error_masking_score,
            self.metrics_inflation_score,
            self.documentation_theater_score,
            self.quality_facade_score,
            self.empty_test_ratio,
            self.assert_true_ratio,
            self.bare_except_ratio,
            self.hardcoded_metrics_ratio,
            self.cosmetic_changes_ratio,
            float(self.total_violations),
            float(self.critical_violations),
            self.violation_density,
        ]


@dataclass
class ClassificationResult:
    is_theater: bool
    confidence: float
    probabilities: Dict[str, float]
    features_used: List[str]
    model_type: str


class TheaterClassifier:
    FEATURE_NAMES = [
        "test_gaming_score",
        "error_masking_score",
        "metrics_inflation_score",
        "documentation_theater_score",
        "quality_facade_score",
        "empty_test_ratio",
        "assert_true_ratio",
        "bare_except_ratio",
        "hardcoded_metrics_ratio",
        "cosmetic_changes_ratio",
        "total_violations",
        "critical_violations",
        "violation_density",
    ]

    def __init__(self, model_type: str = "gradient_boosting"):
        self.model_type = model_type
        self.model = None
        self.scaler = None
        self.is_trained = False

        if SKLEARN_AVAILABLE:
            self._initialize_sklearn_model()
        else:
            logger.info("Using rule-based classification (scikit-learn unavailable)")

    def _initialize_sklearn_model(self):
        if self.model_type == "gradient_boosting":
            self.model = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
        elif self.model_type == "random_forest":
            self.model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
        elif self.model_type == "logistic":
            self.model = LogisticRegression(max_iter=1000, random_state=42)

        self.scaler = StandardScaler()

    def extract_features_from_theater_report(self, theater_report: Dict[str, Any]) -> TheaterFeatures:
        features = TheaterFeatures()

        type_breakdown = theater_report.get("type_breakdown", {})
        features.test_gaming_score = type_breakdown.get("test_gaming", 0) / max(
            1, theater_report.get("total_patterns", 1)
        )
        features.error_masking_score = type_breakdown.get("error_masking", 0) / max(
            1, theater_report.get("total_patterns", 1)
        )
        features.metrics_inflation_score = type_breakdown.get("metrics_inflation", 0) / max(
            1, theater_report.get("total_patterns", 1)
        )
        features.documentation_theater_score = type_breakdown.get("documentation_theater", 0) / max(
            1, theater_report.get("total_patterns", 1)
        )
        features.quality_facade_score = type_breakdown.get("quality_facade", 0) / max(
            1, theater_report.get("total_patterns", 1)
        )

        patterns = theater_report.get("patterns", [])
        if patterns:
            empty_tests = len([p for p in patterns if "empty test" in p.get("description", "").lower()])
            assert_true = len([p for p in patterns if "assert True" in p.get("description", "")])
            bare_except = len([p for p in patterns if "bare except" in p.get("description", "").lower()])
            hardcoded = len([p for p in patterns if "hardcoded" in p.get("description", "").lower()])
            cosmetic = len([p for p in patterns if "cosmetic" in p.get("description", "").lower()])

            total = len(patterns)
            features.empty_test_ratio = empty_tests / total
            features.assert_true_ratio = assert_true / total
            features.bare_except_ratio = bare_except / total
            features.hardcoded_metrics_ratio = hardcoded / total
            features.cosmetic_changes_ratio = cosmetic / total

        features.total_violations = theater_report.get("total_patterns", 0)

        severity_breakdown = theater_report.get("severity_breakdown", {})
        features.critical_violations = severity_breakdown.get("critical", 0)

        lines_scanned = theater_report.get("lines_scanned", 1000)
        features.violation_density = features.total_violations / max(1, lines_scanned / 1000)

        return features

    def train(self, training_data: List[Tuple[TheaterFeatures, bool]]) -> Dict[str, float]:
        if not SKLEARN_AVAILABLE:
            logger.warning("Cannot train: scikit-learn not available")
            return {"error": "sklearn_not_available"}

        if len(training_data) < 10:
            logger.warning(f"Insufficient training data: {len(training_data)} samples (min 10)")
            return {"error": "insufficient_data", "samples": len(training_data)}

        X = np.array([features.to_vector() for features, _ in training_data])
        y = np.array([int(is_theater) for _, is_theater in training_data])

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True

        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)

        y_pred = self.model.predict(X_test_scaled)
        report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

        return {
            "train_accuracy": train_score,
            "test_accuracy": test_score,
            "precision": report.get("1", {}).get("precision", 0.0),
            "recall": report.get("1", {}).get("recall", 0.0),
            "f1_score": report.get("1", {}).get("f1-score", 0.0),
            "samples_used": len(training_data),
        }

    def predict(self, features: TheaterFeatures) -> ClassificationResult:
        if SKLEARN_AVAILABLE and self.is_trained:
            return self._sklearn_predict(features)
        else:
            return self._rule_based_predict(features)

    def _sklearn_predict(self, features: TheaterFeatures) -> ClassificationResult:
        X = np.array([features.to_vector()])
        X_scaled = self.scaler.transform(X)

        prediction = self.model.predict(X_scaled)[0]
        probabilities = self.model.predict_proba(X_scaled)[0]

        return ClassificationResult(
            is_theater=bool(prediction),
            confidence=max(probabilities),
            probabilities={"authentic": float(probabilities[0]), "theater": float(probabilities[1])},
            features_used=self.FEATURE_NAMES,
            model_type=self.model_type,
        )

    def _rule_based_predict(self, features: TheaterFeatures) -> ClassificationResult:
        theater_indicators = 0
        total_checks = 0

        checks = [
            (features.test_gaming_score > 0.3, "test_gaming"),
            (features.error_masking_score > 0.2, "error_masking"),
            (features.metrics_inflation_score > 0.2, "metrics_inflation"),
            (features.empty_test_ratio > 0.5, "empty_tests"),
            (features.assert_true_ratio > 0.3, "trivial_assertions"),
            (features.bare_except_ratio > 0.2, "error_suppression"),
            (features.cosmetic_changes_ratio > 0.6, "cosmetic_work"),
            (features.critical_violations > 5, "critical_issues"),
        ]

        for check, _ in checks:
            total_checks += 1
            if check:
                theater_indicators += 1

        theater_score = theater_indicators / total_checks
        is_theater = theater_score > 0.4

        return ClassificationResult(
            is_theater=is_theater,
            confidence=abs(theater_score - 0.5) * 2,
            probabilities={"authentic": 1.0 - theater_score, "theater": theater_score},
            features_used=["rule_based_heuristics"],
            model_type="rule_based",
        )

    def save_model(self, output_path: str):
        if not SKLEARN_AVAILABLE or not self.is_trained:
            logger.warning("Cannot save: model not trained or sklearn unavailable")
            return

        model_data = {
            "model": self.model,
            "scaler": self.scaler,
            "model_type": self.model_type,
            "feature_names": self.FEATURE_NAMES,
        }

        with open(output_path, "wb") as f:
            pickle.dump(model_data, f)

        logger.info(f"Model saved to {output_path}")

    def load_model(self, model_path: str):
        if not SKLEARN_AVAILABLE:
            logger.warning("Cannot load: scikit-learn unavailable")
            return

        with open(model_path, "rb") as f:
            model_data = pickle.load(f)

        self.model = model_data["model"]
        self.scaler = model_data["scaler"]
        self.model_type = model_data["model_type"]
        self.is_trained = True

        logger.info(f"Model loaded from {model_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="ML Theater Classifier")
    parser.add_argument("--mode", choices=["train", "predict"], required=True)
    parser.add_argument("--training-data", help="Path to training data JSON")
    parser.add_argument("--theater-report", help="Path to theater detection report")
    parser.add_argument("--model-path", default="theater_classifier.pkl", help="Model file path")
    parser.add_argument(
        "--model-type", choices=["gradient_boosting", "random_forest", "logistic"], default="gradient_boosting"
    )

    args = parser.parse_args()

    classifier = TheaterClassifier(model_type=args.model_type)

    if args.mode == "train":
        if not args.training_data:
            logger.error("--training-data required for training mode")
            return

        with open(args.training_data) as f:
            training_data_raw = json.load(f)

        training_data = []
        for item in training_data_raw:
            features = TheaterFeatures(**item["features"])
            is_theater = item["is_theater"]
            training_data.append((features, is_theater))

        logger.info("Training on %s samples...", len(training_data))
        metrics = classifier.train(training_data)

        logger.info("Training Results:")
        for key, value in metrics.items():
            logger.info("  %s: %s", key, f"{value:.3f}" if isinstance(value, float) else value)

        classifier.save_model(args.model_path)
        logger.info("Model saved to %s", args.model_path)

    elif args.mode == "predict":
        if not args.theater_report:
            logger.error("--theater-report required for prediction mode")
            return

        if Path(args.model_path).exists():
            classifier.load_model(args.model_path)

        with open(args.theater_report) as f:
            theater_report = json.load(f)

        features = classifier.extract_features_from_theater_report(theater_report)
        result = classifier.predict(features)

        logger.info("Classification Result:")
        logger.info("  Theater Detected: %s", result.is_theater)
        logger.info("  Confidence: %.2f%%", result.confidence * 100)
        logger.info("  Probabilities:")
        logger.info("    Authentic: %.2f%%", result.probabilities["authentic"] * 100)
        logger.info("    Theater: %.2f%%", result.probabilities["theater"] * 100)
        logger.info("  Model: %s", result.model_type)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
