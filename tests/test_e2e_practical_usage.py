"""
End-to-End Practical Usage Tests for Six Sigma + Theater Detection
Tests real-world scenarios with actual connascence analysis integration
"""

import json
from pathlib import Path
import sys
import tempfile

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.enterprise.sixsigma.integration import ConnascenceSixSigmaIntegration
from analyzer.theater_detection import TheaterDetector
from analyzer.theater_detection.detector import QualityClaim


class TestPracticalE2EScenarios:
    """Test practical real-world usage scenarios"""

    def test_complete_code_quality_audit(self):
        """Test complete code quality audit workflow"""
        # Initialize systems
        six_sigma = ConnascenceSixSigmaIntegration(target_sigma_level=4.0)
        theater_detector = TheaterDetector()

        # Step 1: Initial codebase analysis (baseline)
        baseline_violations = [
            # Critical issues
            {"type": "algorithm", "severity": "critical", "file": "core/processor.py", "line": 45},
            {"type": "timing", "severity": "critical", "file": "async/worker.py", "line": 120},
            # High severity
            {"type": "identity", "severity": "high", "file": "auth/handler.py", "line": 23},
            {"type": "execution", "severity": "high", "file": "runner.py", "line": 89},
            # Medium/Low
            {"type": "meaning", "severity": "medium", "file": "config.py", "line": 12},
            {"type": "type", "severity": "low", "file": "utils.py", "line": 67},
        ]

        baseline_analysis = {
            "violations": baseline_violations,
            "summary": {"total_violations": len(baseline_violations), "files_analyzed": 6},
        }

        # Step 2: Process baseline with Six Sigma
        baseline_six_sigma = six_sigma.process_analysis_results(baseline_analysis)
        baseline_sigma_level = baseline_six_sigma["six_sigma"]["sigma_level"]
        baseline_dpmo = baseline_six_sigma["six_sigma"]["dpmo"]

        print("\n=== BASELINE QUALITY ===")
        print(f"Sigma Level: {baseline_sigma_level}")
        print(f"DPMO: {baseline_dpmo}")
        print(f"Quality Level: {baseline_six_sigma['six_sigma']['quality_level']}")

        # Step 3: Simulate refactoring (improved state)
        improved_violations = [
            {"type": "meaning", "severity": "medium", "file": "config.py", "line": 12},
            {"type": "type", "severity": "low", "file": "utils.py", "line": 67},
        ]

        improved_analysis = {
            "violations": improved_violations,
            "summary": {"total_violations": len(improved_violations), "files_analyzed": 6},
        }

        # Step 4: Process improved state
        improved_six_sigma = six_sigma.process_analysis_results(improved_analysis)
        improved_sigma_level = improved_six_sigma["six_sigma"]["sigma_level"]
        improved_dpmo = improved_six_sigma["six_sigma"]["dpmo"]

        print("\n=== IMPROVED QUALITY ===")
        print(f"Sigma Level: {improved_sigma_level}")
        print(f"DPMO: {improved_dpmo}")
        print(f"Quality Level: {improved_six_sigma['six_sigma']['quality_level']}")

        # Step 5: Create quality improvement claim
        improvement_pct = ((len(baseline_violations) - len(improved_violations)) / len(baseline_violations)) * 100

        claim = QualityClaim(
            claim_id="audit_001",
            description="Eliminated critical connascence violations through refactoring",
            metric_name="total_violations",
            baseline_value=float(len(baseline_violations)),
            improved_value=float(len(improved_violations)),
            improvement_percent=improvement_pct,
            measurement_method="Comprehensive AST-based connascence analysis before and after refactoring. Analyzed 6 files with repeated measurements.",
            evidence_files=["baseline_report.json", "improved_report.json", "refactoring_diff.txt"],
            timestamp=0,
        )

        # Step 6: Validate with theater detection
        validation = theater_detector.validate_quality_claim(claim)

        print("\n=== THEATER VALIDATION ===")
        print(f"Valid: {validation.is_valid}")
        print(f"Confidence: {validation.confidence_score:.2f}")
        print(f"Risk Level: {validation.risk_level}")
        print(f"Recommendation: {validation.recommendation}")

        # Step 7: Generate quality gate decision
        gate_decision = six_sigma.generate_quality_gate_decision(improved_analysis)

        print("\n=== QUALITY GATE ===")
        print(f"Decision: {gate_decision['decision']}")
        print(f"Criteria: {gate_decision['criteria']}")

        # Assertions
        assert improved_sigma_level > baseline_sigma_level
        assert improved_dpmo < baseline_dpmo
        assert validation.is_valid
        assert validation.confidence_score > 0.65
        assert "decision" in gate_decision

    def test_continuous_improvement_tracking(self):
        """Test tracking multiple improvement cycles"""
        six_sigma = ConnascenceSixSigmaIntegration(target_sigma_level=4.0)
        theater_detector = TheaterDetector()

        cycles = []

        # Simulate 5 cycles of improvement
        initial_violations = 50
        for cycle_num in range(5):
            # Realistic gradual improvement with some variance
            violations_count = max(5, initial_violations - (cycle_num * 9) + (cycle_num % 3))

            analysis = {
                "violations": [
                    {"type": ["identity", "algorithm", "timing"][i % 3], "severity": ["low", "medium", "high"][i % 3]}
                    for i in range(violations_count)
                ],
                "summary": {"total_violations": violations_count, "files_analyzed": 10},
            }

            # Process with Six Sigma
            six_sigma_result = six_sigma.process_analysis_results(analysis)

            # Create claim
            prev_violations = initial_violations if cycle_num == 0 else cycles[-1]["violations_count"]
            improvement = ((prev_violations - violations_count) / prev_violations * 100) if prev_violations > 0 else 0

            claim = QualityClaim(
                claim_id=f"cycle_{cycle_num}",
                description=f"Improvement cycle {cycle_num}",
                metric_name="violations",
                baseline_value=float(prev_violations),
                improved_value=float(violations_count),
                improvement_percent=improvement,
                measurement_method=f"Cycle {cycle_num} comprehensive analysis with automated testing",
                evidence_files=[f"cycle_{cycle_num}_report.json"],
                timestamp=cycle_num * 86400,
            )

            validation = theater_detector.validate_quality_claim(claim)

            cycles.append(
                {
                    "cycle": cycle_num,
                    "violations_count": violations_count,
                    "sigma_level": six_sigma_result["six_sigma"]["sigma_level"],
                    "dpmo": six_sigma_result["six_sigma"]["dpmo"],
                    "validation": validation,
                    "claim": claim,
                }
            )

            print(
                f"\nCycle {cycle_num}: {violations_count} violations, "
                f"Sigma={six_sigma_result['six_sigma']['sigma_level']:.2f}, "
                f"Valid={validation.is_valid}"
            )

        # Check systemic patterns
        all_claims = [c["claim"] for c in cycles[1:]]  # Skip baseline
        systemic = theater_detector.detect_systemic_theater(all_claims)

        print("\n=== SYSTEMIC ANALYSIS ===")
        print(f"Indicators: {systemic.get('systemic_theater_indicators', [])}")
        print(f"Risk: {systemic.get('risk_assessment', 'N/A')}")

        # Assertions
        assert len(cycles) == 5
        assert cycles[-1]["sigma_level"] > cycles[0]["sigma_level"]  # Quality improved
        assert all(c["validation"].confidence_score >= 0 for c in cycles)

    def test_multi_project_quality_comparison(self):
        """Test comparing quality across multiple projects"""
        six_sigma = ConnascenceSixSigmaIntegration()

        projects = {
            "legacy_system": {
                "violations": [
                    {"type": t, "severity": s}
                    for t in ["algorithm", "timing", "execution"] * 10
                    for s in ["critical", "high"]
                ]
            },
            "microservice_a": {
                "violations": [
                    {"type": t, "severity": s} for t in ["identity", "meaning"] * 5 for s in ["medium", "low"]
                ]
            },
            "new_api": {"violations": [{"type": "type", "severity": "low"} for _ in range(3)]},
        }

        results = {}
        for project_name, project_data in projects.items():
            analysis = {
                "violations": project_data["violations"],
                "summary": {"total_violations": len(project_data["violations"]), "files_analyzed": 20},
            }

            six_sigma_result = six_sigma.process_analysis_results(analysis)
            results[project_name] = six_sigma_result["six_sigma"]

            print(f"\n=== {project_name.upper()} ===")
            print(f"Sigma: {results[project_name]['sigma_level']:.2f}")
            print(f"DPMO: {results[project_name]['dpmo']:.0f}")
            print(f"Quality: {results[project_name]['quality_level']}")

        # Assertions - verify quality ranking
        # New API should have best quality (fewest violations)
        assert results["new_api"]["sigma_level"] > results["microservice_a"]["sigma_level"]
        # Legacy system and microservice quality depends on severity weighting
        # Both should be lower than new_api
        assert results["new_api"]["sigma_level"] > results["legacy_system"]["sigma_level"]

    def test_export_and_persistence(self):
        """Test exporting results for reporting and persistence"""
        six_sigma = ConnascenceSixSigmaIntegration()
        theater_detector = TheaterDetector()

        # Create analysis
        analysis = {"violations": [{"type": "algorithm", "severity": "high"}, {"type": "timing", "severity": "medium"}]}

        # Process and export
        six_sigma_result = six_sigma.process_analysis_results(analysis)
        dashboard_data = six_sigma.export_dashboard_data(analysis)
        exec_report = six_sigma.generate_executive_report(analysis)

        # Create claim and validate
        claim = QualityClaim(
            claim_id="export_001",
            description="Quality improvement",
            metric_name="violations",
            baseline_value=10.0,
            improved_value=2.0,
            improvement_percent=80.0,
            measurement_method="Comprehensive analysis",
            evidence_files=["report.json"],
            timestamp=0,
        )

        validation = theater_detector.validate_quality_claim(claim)

        # Export theater validation
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = theater_detector.export_validation_report([claim])

            # Verify export
            assert Path(report_path).exists()

            with open(report_path) as f:
                report_data = json.load(f)

            print("\n=== EXPORTED DATA ===")
            print(f"Dashboard gauges: {list(dashboard_data['gauges'].keys())}")
            print(f"Report sections: {list(report_data.keys())}")
            print(f"Executive report length: {len(exec_report)} chars")

            # Assertions
            assert "metadata" in report_data
            assert "summary" in dashboard_data
            assert "EXECUTIVE SUMMARY" in exec_report

    def test_quality_gate_enforcement(self):
        """Test strict quality gate enforcement"""
        six_sigma = ConnascenceSixSigmaIntegration(target_sigma_level=4.5)
        theater_detector = TheaterDetector()

        # Test case: High quality (should pass)
        high_quality = {"violations": [{"type": "type", "severity": "low"}]}

        gate_high = six_sigma.generate_quality_gate_decision(high_quality)
        print("\n=== HIGH QUALITY GATE ===")
        print(f"Decision: {gate_high['decision']}")

        # Test case: Low quality (should fail)
        low_quality = {
            "violations": [{"type": t, "severity": "critical"} for t in ["algorithm", "timing", "execution"] * 3]
        }

        gate_low = six_sigma.generate_quality_gate_decision(low_quality)
        print("\n=== LOW QUALITY GATE ===")
        print(f"Decision: {gate_low['decision']}")

        # Validate claims
        high_claim = QualityClaim(
            claim_id="hq_001",
            description="High quality improvement",
            metric_name="violations",
            baseline_value=5.0,
            improved_value=1.0,
            improvement_percent=80.0,
            measurement_method="Detailed analysis with comprehensive testing",
            evidence_files=["analysis.json", "tests.json"],
            timestamp=0,
        )

        low_claim = QualityClaim(
            claim_id="lq_001",
            description="Perfect quality",
            metric_name="violations",
            baseline_value=10.0,
            improved_value=0.0,
            improvement_percent=100.0,
            measurement_method="Quick check",
            evidence_files=[],
            timestamp=0,
        )

        high_validation = theater_detector.validate_quality_claim(high_claim)
        low_validation = theater_detector.validate_quality_claim(low_claim)

        print(
            f"\nHigh quality validation: {high_validation.is_valid} (confidence: {high_validation.confidence_score:.2f})"
        )
        print(f"Low quality validation: {low_validation.is_valid} (confidence: {low_validation.confidence_score:.2f})")

        # Assertions
        assert "decision" in gate_high
        assert "decision" in gate_low
        assert not low_validation.is_valid  # Should fail due to suspicious claims


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s to show print statements
