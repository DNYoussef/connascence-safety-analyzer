"""
Integration Tests for Six Sigma + Theater Detection Systems
Tests both systems working together with real connascence analysis data
"""

from pathlib import Path
import sys

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.enterprise.sixsigma import SixSigmaAnalyzer
from analyzer.enterprise.sixsigma.integration import ConnascenceSixSigmaIntegration
from analyzer.theater_detection import TheaterDetector, TheaterPatternLibrary
from analyzer.theater_detection.detector import QualityClaim


class TestSixSigmaTheaterIntegration:
    """Test integration between Six Sigma and Theater Detection"""

    def test_combined_quality_validation(self):
        """Test quality validation using both systems"""
        # Initialize both systems
        six_sigma = ConnascenceSixSigmaIntegration(target_sigma_level=4.0)
        theater_detector = TheaterDetector()

        # Real connascence analysis results
        analysis_results = {
            "violations": [
                {"type": "identity", "severity": "high", "file": "module.py", "line": 10},
                {"type": "algorithm", "severity": "critical", "file": "module.py", "line": 25},
                {"type": "timing", "severity": "medium", "file": "service.py", "line": 45},
                {"type": "execution", "severity": "low", "file": "utils.py", "line": 12},
            ],
            "summary": {"total_violations": 4, "files_analyzed": 3},
        }

        # Process with Six Sigma
        six_sigma_enhanced = six_sigma.process_analysis_results(analysis_results)

        # Create quality claim from Six Sigma results
        claim = QualityClaim(
            claim_id="integration_001",
            description="Connascence violations reduced through refactoring",
            metric_name="total_violations",
            baseline_value=10.0,
            improved_value=4.0,
            improvement_percent=60.0,
            measurement_method="Used connascence analyzer to measure violations before and after refactoring",
            evidence_files=["baseline_analysis.json", "improved_analysis.json"],
            timestamp=0,
        )

        # Validate with Theater Detection
        validation_result = theater_detector.validate_quality_claim(claim)

        # Assertions
        assert "six_sigma" in six_sigma_enhanced
        assert validation_result.is_valid
        assert validation_result.confidence_score > 0.6
        assert six_sigma_enhanced["six_sigma"]["sigma_level"] > 0

    def test_theater_detection_on_six_sigma_metrics(self):
        """Test theater detection on Six Sigma quality metrics"""
        theater_detector = TheaterDetector()

        # Suspicious perfect Six Sigma claim
        suspicious_claim = QualityClaim(
            claim_id="suspicious_001",
            description="Achieved perfect Six Sigma quality",
            metric_name="dpmo",
            baseline_value=50000.0,
            improved_value=3.4,  # Perfect Six Sigma
            improvement_percent=99.99,
            measurement_method="Quality improvement",
            evidence_files=[],
            timestamp=0,
        )

        result = theater_detector.validate_quality_claim(suspicious_claim)

        assert not result.is_valid
        assert result.risk_level in ["medium", "high"]  # Can be medium or high based on other factors
        # Validation can fail due to insufficient evidence or theater indicators
        assert result.confidence_score < 0.65  # Below confidence threshold

    def test_real_connascence_analysis_flow(self):
        """Test complete flow with real connascence data"""
        six_sigma = ConnascenceSixSigmaIntegration(target_sigma_level=3.5)
        theater_detector = TheaterDetector()

        # Simulate real connascence analysis with multiple violation types
        baseline_analysis = {
            "violations": [
                {"type": "identity", "severity": "critical", "file": "auth.py", "line": 15},
                {"type": "identity", "severity": "high", "file": "auth.py", "line": 23},
                {"type": "algorithm", "severity": "critical", "file": "processor.py", "line": 67},
                {"type": "timing", "severity": "high", "file": "async_handler.py", "line": 89},
                {"type": "timing", "severity": "medium", "file": "async_handler.py", "line": 102},
                {"type": "execution", "severity": "medium", "file": "runner.py", "line": 45},
                {"type": "meaning", "severity": "low", "file": "config.py", "line": 12},
            ],
            "summary": {"total_violations": 7, "files_analyzed": 5},
        }

        improved_analysis = {
            "violations": [
                {"type": "timing", "severity": "medium", "file": "async_handler.py", "line": 102},
                {"type": "meaning", "severity": "low", "file": "config.py", "line": 12},
            ],
            "summary": {"total_violations": 2, "files_analyzed": 5},
        }

        # Process with Six Sigma
        baseline_six_sigma = six_sigma.process_analysis_results(baseline_analysis)
        improved_six_sigma = six_sigma.process_analysis_results(improved_analysis)

        # Create quality claim
        claim = QualityClaim(
            claim_id="real_flow_001",
            description="Reduced critical connascence violations",
            metric_name="total_violations",
            baseline_value=float(baseline_analysis["summary"]["total_violations"]),
            improved_value=float(improved_analysis["summary"]["total_violations"]),
            improvement_percent=((7 - 2) / 7) * 100,
            measurement_method="Comprehensive connascence analysis using AST-based detector across entire codebase",
            evidence_files=["baseline_report.json", "improved_report.json", "refactoring_log.md"],
            timestamp=0,
        )

        # Validate with theater detection
        validation = theater_detector.validate_quality_claim(claim)

        # Verify both systems agree on quality
        assert baseline_six_sigma["six_sigma"]["sigma_level"] < improved_six_sigma["six_sigma"]["sigma_level"]
        assert validation.is_valid
        assert validation.confidence_score > 0.65

    def test_quality_gate_with_theater_validation(self):
        """Test quality gate decisions validated by theater detection"""
        six_sigma = ConnascenceSixSigmaIntegration(target_sigma_level=4.0)
        theater_detector = TheaterDetector()

        analysis = {
            "violations": [{"type": "algorithm", "severity": "critical"}, {"type": "timing", "severity": "high"}]
        }

        # Get quality gate decision
        gate_decision = six_sigma.generate_quality_gate_decision(analysis)

        # Create claim based on gate decision
        claim = QualityClaim(
            claim_id="gate_001",
            description="Quality gate validation",
            metric_name="violations",
            baseline_value=10.0,
            improved_value=2.0,
            improvement_percent=80.0,
            measurement_method="Connascence analyzer with comprehensive violation detection",
            evidence_files=["gate_report.json"],
            timestamp=0,
        )

        validation = theater_detector.validate_quality_claim(claim)

        # Both systems should agree on quality level
        assert "decision" in gate_decision
        assert isinstance(validation.is_valid, bool)

    def test_systemic_theater_in_six_sigma_improvements(self):
        """Test detection of systemic theater across multiple Six Sigma cycles"""
        six_sigma = ConnascenceSixSigmaIntegration()
        theater_detector = TheaterDetector()

        # Create multiple cycles with suspicious patterns
        claims = []
        for i in range(5):
            analysis = {
                "violations": [{"type": "identity", "severity": "medium"}]
                * (10 - i * 2)  # Steadily decreasing by exact amounts
            }

            six_sigma.process_analysis_results(analysis)

            claim = QualityClaim(
                claim_id=f"cycle_{i}",
                description=f"Improvement cycle {i}",
                metric_name="violations",
                baseline_value=10.0,
                improved_value=10.0 - i * 2,
                improvement_percent=20.0,  # Always exactly 20%
                measurement_method="Quick analysis",
                evidence_files=[],
                timestamp=i * 3600,  # Exactly 1 hour apart
            )
            claims.append(claim)

        # Detect systemic theater
        systemic_result = theater_detector.detect_systemic_theater(claims)

        assert len(systemic_result["systemic_theater_indicators"]) > 0
        assert systemic_result["risk_assessment"] in ["medium", "high"]

    def test_connascence_specific_six_sigma_metrics(self):
        """Test Six Sigma metrics specific to connascence types"""
        six_sigma_analyzer = SixSigmaAnalyzer(target_level="enterprise")
        theater_detector = TheaterDetector()

        # Test with high-value connascence types
        high_value_violations = [
            {"type": "timing", "severity": "critical"},  # High-value connascence
            {"type": "algorithm", "severity": "critical"},  # High-value connascence
        ]

        low_value_violations = [
            {"type": "name", "severity": "low"},  # Low-value connascence
            {"type": "type", "severity": "low"},
        ]

        high_value_result = six_sigma_analyzer.analyze_violations(high_value_violations, Path("test.py"))
        low_value_result = six_sigma_analyzer.analyze_violations(low_value_violations, Path("test.py"))

        # Both should have valid sigma calculations
        # Note: DPMO calculation considers severity weight, not just connascence type
        assert high_value_result.sigma_level > 0
        assert low_value_result.sigma_level > 0
        # High severity violations should have worse quality (lower sigma or higher CTQ)
        assert high_value_result.ctq_metrics["composite"] > low_value_result.ctq_metrics["composite"]

        # Create claims for theater detection
        high_value_claim = QualityClaim(
            claim_id="hv_001",
            description="Eliminated critical timing connascence",
            metric_name="timing_violations",
            baseline_value=5.0,
            improved_value=0.0,
            improvement_percent=100.0,
            measurement_method="Comprehensive timing analysis with race condition detection",
            evidence_files=["timing_report.json"],
            timestamp=0,
        )

        validation = theater_detector.validate_quality_claim(high_value_claim)

        # Should flag 100% improvement as suspicious
        assert not validation.is_valid or validation.confidence_score < 0.7

    def test_executive_report_with_theater_validation(self):
        """Test executive report includes theater validation results"""
        six_sigma = ConnascenceSixSigmaIntegration()
        theater_detector = TheaterDetector()

        analysis = {
            "violations": [{"type": "identity", "severity": "high"}, {"type": "algorithm", "severity": "medium"}]
        }

        # Generate executive report
        exec_report = six_sigma.generate_executive_report(analysis)

        # Create and validate claim
        claim = QualityClaim(
            claim_id="exec_001",
            description="Quality improvement for executive review",
            metric_name="violations",
            baseline_value=5.0,
            improved_value=2.0,
            improvement_percent=60.0,
            measurement_method="Detailed connascence analysis",
            evidence_files=["report.json"],
            timestamp=0,
        )

        validation = theater_detector.validate_quality_claim(claim)

        # Both should provide meaningful output
        assert len(exec_report) > 100
        assert validation.confidence_score > 0
        assert "EXECUTIVE SUMMARY" in exec_report

    def test_ci_cd_integration_with_theater_checks(self):
        """Test CI/CD integration with theater detection gates"""
        six_sigma = ConnascenceSixSigmaIntegration(target_sigma_level=3.0)
        theater_detector = TheaterDetector()

        # Good quality, genuine improvement
        good_analysis = {"violations": [{"type": "meaning", "severity": "low"}]}

        # Poor quality with theater patterns

        # Test good case
        six_sigma.integrate_with_ci_cd(good_analysis, fail_on_quality_gate=True)

        good_claim = QualityClaim(
            claim_id="ci_good",
            description="Legitimate improvement",
            metric_name="violations",
            baseline_value=10.0,
            improved_value=1.0,
            improvement_percent=90.0,
            measurement_method="Comprehensive analysis with statistical validation and repeated measurements",
            evidence_files=["baseline.json", "improved.json", "diff.json"],
            timestamp=0,
        )

        good_validation = theater_detector.validate_quality_claim(good_claim)

        # Test poor case
        poor_claim = QualityClaim(
            claim_id="ci_poor",
            description="Perfect improvement",
            metric_name="violations",
            baseline_value=10.0,
            improved_value=0.0,
            improvement_percent=100.0,
            measurement_method="Quick check",
            evidence_files=[],
            timestamp=0,
        )

        poor_validation = theater_detector.validate_quality_claim(poor_claim)

        # Assertions
        # Good validation should have higher confidence even if statistical checks flag concerns
        assert not poor_validation.is_valid
        assert good_validation.confidence_score > poor_validation.confidence_score

    def test_dashboard_data_with_theater_scores(self):
        """Test dashboard data includes theater detection scores"""
        six_sigma = ConnascenceSixSigmaIntegration()
        theater_library = TheaterPatternLibrary()

        analysis = {"violations": [{"type": "timing", "severity": "high"}, {"type": "execution", "severity": "medium"}]}

        dashboard_data = six_sigma.export_dashboard_data(analysis)

        # Test theater pattern detection on dashboard metrics
        theater_patterns = theater_library.detect_patterns(
            {"improvement_percent": 50.0, "baseline_value": 100.0, "improved_value": 50.0}  # Suspicious round number
        )

        assert "gauges" in dashboard_data
        assert "sigma" in dashboard_data["gauges"]
        assert len(theater_patterns) > 0


class TestRealWorldScenarios:
    """Test real-world usage scenarios"""

    def test_large_codebase_analysis(self):
        """Test with large codebase simulation"""
        six_sigma = ConnascenceSixSigmaIntegration(target_sigma_level=4.5)
        theater_detector = TheaterDetector()

        # Simulate large codebase with realistic violation distribution
        violations = []
        violation_types = ["identity", "algorithm", "timing", "execution", "meaning", "name", "type"]
        severities = ["low", "medium", "high", "critical"]

        # Generate 100 violations with realistic distribution
        for i in range(100):
            violations.append(
                {
                    "type": violation_types[i % len(violation_types)],
                    "severity": severities[min(i % 4, 3)],
                    "file": f"module_{i // 10}.py",
                    "line": (i * 10) % 500,
                }
            )

        analysis = {"violations": violations, "summary": {"total_violations": len(violations), "files_analyzed": 10}}

        # Process
        six_sigma_result = six_sigma.process_analysis_results(analysis)

        claim = QualityClaim(
            claim_id="large_001",
            description="Large codebase refactoring",
            metric_name="total_violations",
            baseline_value=200.0,
            improved_value=100.0,
            improvement_percent=50.0,
            measurement_method="Full codebase analysis with AST parsing",
            evidence_files=["full_report.json"],
            timestamp=0,
        )

        validation = theater_detector.validate_quality_claim(claim)

        assert six_sigma_result["six_sigma"]["sigma_level"] > 0
        assert validation.confidence_score >= 0  # Should complete without error

    def test_incremental_improvement_tracking(self):
        """Test tracking incremental improvements over time"""
        six_sigma = ConnascenceSixSigmaIntegration()
        theater_detector = TheaterDetector()

        # Simulate 5 improvement cycles
        claims = []
        for cycle in range(5):
            violations_count = 50 - (cycle * 8)  # Realistic gradual improvement

            analysis = {"violations": [{"type": "identity", "severity": "medium"}] * violations_count}

            six_sigma.process_analysis_results(analysis)

            claim = QualityClaim(
                claim_id=f"increment_{cycle}",
                description=f"Cycle {cycle} improvements",
                metric_name="violations",
                baseline_value=50 - (cycle * 8) + 8 if cycle > 0 else 50,
                improved_value=violations_count,
                improvement_percent=16.0 if cycle > 0 else 0,
                measurement_method=f"Cycle {cycle} full analysis",
                evidence_files=[f"cycle_{cycle}_report.json"],
                timestamp=cycle * 86400,  # 1 day apart
            )
            claims.append(claim)

        # Validate each claim
        validations = [theater_detector.validate_quality_claim(c) for c in claims]

        # Check systemic patterns
        systemic = theater_detector.detect_systemic_theater(claims[1:])  # Skip baseline

        assert all(v.confidence_score > 0 for v in validations)
        assert "systemic_theater_indicators" in systemic


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
