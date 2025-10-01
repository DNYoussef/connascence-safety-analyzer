"""
Test Theater Detection System
"""

import json
from pathlib import Path
import sys
import time

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.theater_detection import EvidenceValidator, TheaterDetector, TheaterPatternLibrary, ValidationResult
from analyzer.theater_detection.detector import QualityClaim


def test_theater_detector_initialization():
    """Test theater detector initialization"""
    detector = TheaterDetector()

    assert len(detector.theater_patterns) > 0
    assert len(detector.connascence_weights) == 9
    assert detector.validation_thresholds["confidence_threshold"] == 0.65


def test_validate_quality_claim_genuine():
    """Test validation of genuine quality claim"""
    detector = TheaterDetector()

    # Create a genuine quality claim
    claim = QualityClaim(
        claim_id="test_001",
        description="Reduced algorithm connascence violations",
        metric_name="algorithm_violations",
        baseline_value=45.0,
        improved_value=23.7,
        improvement_percent=47.3,
        measurement_method="Analyzed 150 files before and after refactoring, measured violations using AST analysis with 10 repeated runs",
        evidence_files=["baseline_report.json", "improved_report.json", "diff_analysis.txt"],
        timestamp=time.time(),
    )

    result = detector.validate_quality_claim(claim)

    assert isinstance(result, ValidationResult)
    assert result.confidence_score > 0.5
    assert len(result.genuine_indicators) > 0
    assert result.risk_level in ["low", "medium"]


def test_validate_quality_claim_theater():
    """Test detection of theater in quality claim"""
    detector = TheaterDetector()

    # Create a suspicious quality claim
    claim = QualityClaim(
        claim_id="test_002",
        description="Perfect elimination of all violations",
        metric_name="total_violations",
        baseline_value=100.0,
        improved_value=0.0,
        improvement_percent=100.0,
        measurement_method="Quick check",
        evidence_files=[],
        timestamp=time.time(),
    )

    result = detector.validate_quality_claim(claim)

    assert not result.is_valid
    assert result.confidence_score < 0.5
    assert len(result.theater_indicators) > 0
    assert "perfect_metrics" in result.theater_indicators or len(result.theater_indicators) > 0
    assert result.risk_level == "high"


def test_statistical_plausibility():
    """Test statistical plausibility validation"""
    detector = TheaterDetector()

    # Test with round number
    claim = QualityClaim(
        claim_id="test_003",
        description="Test claim",
        metric_name="test_metric",
        baseline_value=100.0,
        improved_value=50.0,
        improvement_percent=50.0,  # Suspicious round number
        measurement_method="Test",
        evidence_files=[],
        timestamp=time.time(),
    )

    score = detector._validate_statistical_plausibility(claim)
    assert score < 0.6  # Should be penalized for round number


def test_pattern_library():
    """Test theater pattern library"""
    library = TheaterPatternLibrary()

    # Test round number detection
    data = {"improvement_percent": 50.0}
    patterns = library.detect_patterns(data)
    assert "metric_manipulation" in patterns

    # Test missing baseline detection
    data = {"baseline_value": None}
    patterns = library.detect_patterns(data)
    assert "evidence_fabrication" in patterns

    # Calculate theater score
    detected = {"metric_manipulation": ["MM001", "MM002"]}
    score = library.calculate_theater_score(detected)
    assert 0.0 <= score <= 1.0


def test_evidence_validator():
    """Test evidence validator"""
    validator = EvidenceValidator()

    # Test methodology validation
    good_methodology = "Performed baseline measurements across 100 files, then repeated after refactoring. Used statistical analysis with 95% confidence interval."
    is_valid, message, score = validator.validate_measurement_methodology(good_methodology)
    assert is_valid
    assert score > 0.6

    bad_methodology = "Roughly guessed the improvement"
    is_valid, message, score = validator.validate_measurement_methodology(bad_methodology)
    assert not is_valid
    assert score < 0.4

    # Test improvement claim validation
    is_valid, message, score = validator.validate_improvement_claim(
        baseline=100.0, improved=60.0, claim_type="violations"
    )
    assert is_valid
    assert score > 0.5


def test_systemic_theater_detection():
    """Test detection of systemic theater patterns"""
    detector = TheaterDetector()

    # Create multiple suspicious claims
    claims = [
        QualityClaim(
            claim_id=f"claim_{i}",
            description=f"Improvement {i}",
            metric_name="violations",
            baseline_value=100.0,
            improved_value=50.0,
            improvement_percent=50.0,  # All same improvement
            measurement_method="Quick check",
            evidence_files=[f"report_{i}.json"],
            timestamp=time.time() + i * 60,  # Regular intervals
        )
        for i in range(3)
    ]

    systemic_result = detector.detect_systemic_theater(claims)

    assert "systemic_theater_indicators" in systemic_result
    assert len(systemic_result["systemic_theater_indicators"]) > 0
    assert systemic_result["risk_assessment"] in ["medium", "high"]


def test_connascence_specific_validation():
    """Test connascence-specific validation logic"""
    detector = TheaterDetector()

    # Test high-value connascence type
    claim = QualityClaim(
        claim_id="test_conn",
        description="Reduced timing connascence",
        metric_name="timing_connascence_violations",
        baseline_value=20.0,
        improved_value=5.0,
        improvement_percent=75.0,
        measurement_method="Comprehensive analysis of all files in codebase",
        evidence_files=["timing_analysis.json"],
        timestamp=time.time(),
    )

    score = detector._validate_connascence_claim(claim)
    assert score > 0.8  # Should get bonus for targeting high-value type


def test_risk_level_assessment():
    """Test risk level assessment"""
    detector = TheaterDetector()

    # High confidence, no theater indicators
    risk = detector._assess_risk_level(0.9, [])
    assert risk == "low"

    # Low confidence, multiple theater indicators
    risk = detector._assess_risk_level(0.2, ["fake_metrics", "no_evidence", "cherry_picking"])
    assert risk == "high"

    # Medium scenario
    risk = detector._assess_risk_level(0.5, ["minor_issue"])
    assert risk == "medium"


def test_recommendation_generation():
    """Test recommendation generation"""
    detector = TheaterDetector()

    claim = QualityClaim(
        claim_id="test_rec",
        description="Test improvement",
        metric_name="test_metric",
        baseline_value=100.0,
        improved_value=80.0,
        improvement_percent=20.0,
        measurement_method="Detailed analysis with repeated measurements",
        evidence_files=["report1.json", "report2.json"],
        timestamp=time.time(),
    )

    # Validate to get all scores
    result = detector.validate_quality_claim(claim)

    assert result.recommendation
    assert len(result.recommendation) > 10  # Should be meaningful recommendation


def test_export_validation_report():
    """Test validation report export"""
    detector = TheaterDetector()

    claims = [
        QualityClaim(
            claim_id="export_test",
            description="Test export",
            metric_name="violations",
            baseline_value=50.0,
            improved_value=30.0,
            improvement_percent=40.0,
            measurement_method="Standard analysis",
            evidence_files=["test.json"],
            timestamp=time.time(),
        )
    ]

    # Create temporary directory for report
    temp_dir = Path(".claude/.artifacts/theater_detection")
    temp_dir.mkdir(parents=True, exist_ok=True)

    report_path = detector.export_validation_report(claims)

    assert Path(report_path).exists()

    # Load and verify report structure
    with open(report_path) as f:
        report = json.load(f)

    assert "metadata" in report
    assert "summary" in report
    assert "systemic_analysis" in report
    assert "individual_results" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
