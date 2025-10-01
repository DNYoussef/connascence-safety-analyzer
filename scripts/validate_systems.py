#!/usr/bin/env python3
"""
Quick validation script to verify Six Sigma and Theater Detection systems
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def validate_imports():
    """Validate all required imports are accessible"""
    print("=== Validating Imports ===\n")

    try:
        from analyzer.enterprise.sixsigma import (
            SixSigmaAnalyzer,
            SixSigmaTelemetry,
            CTQCalculator,
            ProcessCapability,
            QualityLevel
        )
        print("✅ Six Sigma core imports: OK")
    except ImportError as e:
        print(f"❌ Six Sigma core imports: FAILED - {e}")
        return False

    try:
        from analyzer.enterprise.sixsigma.integration import ConnascenceSixSigmaIntegration
        print("✅ Six Sigma integration import: OK")
    except ImportError as e:
        print(f"❌ Six Sigma integration import: FAILED - {e}")
        return False

    try:
        from analyzer.theater_detection import (
            TheaterDetector,
            TheaterPattern,
            ValidationResult,
            TheaterPatternLibrary,
            EvidenceValidator
        )
        print("✅ Theater Detection core imports: OK")
    except ImportError as e:
        print(f"❌ Theater Detection core imports: FAILED - {e}")
        return False

    try:
        from analyzer.theater_detection.detector import QualityClaim
        print("✅ Theater Detection QualityClaim import: OK")
    except ImportError as e:
        print(f"❌ Theater Detection QualityClaim import: FAILED - {e}")
        return False

    return True

def test_basic_functionality():
    """Test basic functionality of both systems"""
    print("\n=== Testing Basic Functionality ===\n")

    from analyzer.enterprise.sixsigma.integration import ConnascenceSixSigmaIntegration
    from analyzer.theater_detection import TheaterDetector
    from analyzer.theater_detection.detector import QualityClaim

    # Test Six Sigma
    try:
        six_sigma = ConnascenceSixSigmaIntegration(target_sigma_level=4.0)

        test_analysis = {
            'violations': [
                {'type': 'algorithm', 'severity': 'high'},
                {'type': 'timing', 'severity': 'medium'}
            ],
            'summary': {'total_violations': 2, 'files_analyzed': 1}
        }

        result = six_sigma.process_analysis_results(test_analysis)

        assert 'six_sigma' in result
        assert 'sigma_level' in result['six_sigma']
        assert 'dpmo' in result['six_sigma']

        print(f"✅ Six Sigma processing: OK")
        print(f"   Sigma Level: {result['six_sigma']['sigma_level']:.2f}")
        print(f"   DPMO: {result['six_sigma']['dpmo']:.1f}")
    except Exception as e:
        print(f"❌ Six Sigma processing: FAILED - {e}")
        return False

    # Test Theater Detection
    try:
        detector = TheaterDetector()

        claim = QualityClaim(
            claim_id="test_001",
            description="Test improvement",
            metric_name="violations",
            baseline_value=10.0,
            improved_value=2.0,
            improvement_percent=80.0,
            measurement_method="Comprehensive analysis with repeated measurements",
            evidence_files=["report.json"],
            timestamp=0
        )

        validation = detector.validate_quality_claim(claim)

        assert hasattr(validation, 'is_valid')
        assert hasattr(validation, 'confidence_score')
        assert hasattr(validation, 'risk_level')

        print(f"✅ Theater Detection processing: OK")
        print(f"   Valid: {validation.is_valid}")
        print(f"   Confidence: {validation.confidence_score:.2f}")
        print(f"   Risk: {validation.risk_level}")
    except Exception as e:
        print(f"❌ Theater Detection processing: FAILED - {e}")
        return False

    return True

def test_integration():
    """Test integration between systems"""
    print("\n=== Testing System Integration ===\n")

    from analyzer.enterprise.sixsigma.integration import ConnascenceSixSigmaIntegration
    from analyzer.theater_detection import TheaterDetector
    from analyzer.theater_detection.detector import QualityClaim

    try:
        six_sigma = ConnascenceSixSigmaIntegration()
        detector = TheaterDetector()

        # Baseline analysis
        baseline = {
            'violations': [
                {'type': 'identity', 'severity': 'critical'},
                {'type': 'algorithm', 'severity': 'high'},
                {'type': 'timing', 'severity': 'medium'}
            ]
        }

        # Improved analysis
        improved = {
            'violations': [
                {'type': 'timing', 'severity': 'medium'}
            ]
        }

        # Process both
        baseline_result = six_sigma.process_analysis_results(baseline)
        improved_result = six_sigma.process_analysis_results(improved)

        # Create quality claim
        claim = QualityClaim(
            claim_id="integration_test",
            description="Reduced connascence violations",
            metric_name="total_violations",
            baseline_value=3.0,
            improved_value=1.0,
            improvement_percent=66.67,
            measurement_method="Connascence analysis before and after refactoring",
            evidence_files=["baseline.json", "improved.json"],
            timestamp=0
        )

        # Validate
        validation = detector.validate_quality_claim(claim)

        # Check integration
        baseline_sigma = baseline_result['six_sigma']['sigma_level']
        improved_sigma = improved_result['six_sigma']['sigma_level']

        assert improved_sigma > baseline_sigma, "Quality should improve"
        assert validation.confidence_score > 0, "Should have confidence score"

        print(f"✅ System integration: OK")
        print(f"   Baseline Sigma: {baseline_sigma:.2f}")
        print(f"   Improved Sigma: {improved_sigma:.2f}")
        print(f"   Validation Confidence: {validation.confidence_score:.2f}")

        return True
    except Exception as e:
        print(f"❌ System integration: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main validation function"""
    print("\n" + "="*60)
    print("Six Sigma & Theater Detection System Validation")
    print("="*60 + "\n")

    all_ok = True

    # Test imports
    if not validate_imports():
        all_ok = False

    # Test basic functionality
    if not test_basic_functionality():
        all_ok = False

    # Test integration
    if not test_integration():
        all_ok = False

    # Summary
    print("\n" + "="*60)
    if all_ok:
        print("✅ ALL VALIDATIONS PASSED - Systems are operational")
        print("="*60 + "\n")
        return 0
    else:
        print("❌ SOME VALIDATIONS FAILED - Check errors above")
        print("="*60 + "\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())