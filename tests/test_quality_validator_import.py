"""
Test import and basic functionality of quality_validator library component.
"""

import sys
from pathlib import Path

# Add src to path for import
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


def test_import_quality_validator():
    """Test that quality_validator can be imported."""
    from library.validation import QualityValidator
    assert QualityValidator is not None


def test_import_all_exports():
    """Test that all exported classes can be imported."""
    from library.validation import (
        QualityValidator,
        QualityClaim,
        QualityValidationResult,
        ValidationResult,
        Violation,
        AnalysisResult,
        EvidenceQuality,
        RiskLevel,
        Severity,
    )
    # All imports should be valid classes
    assert QualityValidator is not None
    assert QualityClaim is not None
    assert QualityValidationResult is not None
    assert ValidationResult is not None
    assert Violation is not None
    assert AnalysisResult is not None
    assert EvidenceQuality is not None
    assert RiskLevel is not None
    assert Severity is not None


def test_quality_validator_instantiation():
    """Test that QualityValidator can be instantiated."""
    from library.validation import QualityValidator

    validator = QualityValidator()
    assert validator is not None
    assert hasattr(validator, "add_violation")
    assert hasattr(validator, "calculate_score")
    assert hasattr(validator, "check_gate")


def test_add_violation():
    """Test adding a violation."""
    from library.validation import QualityValidator

    validator = QualityValidator()
    violation = validator.add_violation(
        rule_id="TEST-001",
        message="Test violation",
        file="test.py",
        line=10,
        severity="medium",
    )

    assert violation is not None
    assert violation.rule_id == "TEST-001"
    assert len(validator.violations) == 1


def test_calculate_score():
    """Test score calculation."""
    from library.validation import QualityValidator

    validator = QualityValidator()
    score = validator.calculate_score()
    assert score == 100.0  # No violations = perfect score

    # Add a violation and check score decreases
    validator.add_violation(
        rule_id="TEST-001",
        message="Test violation",
        file="test.py",
        line=10,
        severity="medium",
    )
    new_score = validator.calculate_score()
    assert new_score < 100.0


def test_check_gate():
    """Test quality gate check."""
    from library.validation import QualityValidator

    validator = QualityValidator()
    assert validator.check_gate() is True  # No violations = gate passes

    # Add critical violation and check gate fails
    validator.add_violation(
        rule_id="TEST-001",
        message="Critical test violation",
        file="test.py",
        line=10,
        severity="critical",
    )
    assert validator.check_gate() is False


def test_analyze():
    """Test full analysis."""
    from library.validation import QualityValidator

    validator = QualityValidator()
    validator.add_violation(
        rule_id="TEST-001",
        message="Test violation",
        file="test.py",
        line=10,
        severity="low",
    )

    result = validator.analyze(project_path="D:/Projects/connascence")
    assert result is not None
    assert hasattr(result, "violations")
    assert hasattr(result, "overall_score")
    assert hasattr(result, "quality_gate_passed")
    assert len(result.violations) == 1


if __name__ == "__main__":
    # Run basic tests
    test_import_quality_validator()
    test_import_all_exports()
    test_quality_validator_instantiation()
    test_add_violation()
    test_calculate_score()
    test_check_gate()
    test_analyze()
    print("All quality_validator import tests passed!")
