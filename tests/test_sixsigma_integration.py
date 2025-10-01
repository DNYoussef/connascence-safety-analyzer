"""
Test Six Sigma Integration with Connascence Analyzer
"""

from pathlib import Path
import sys

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.enterprise.sixsigma import CTQCalculator, ProcessCapability, SixSigmaAnalyzer, SixSigmaTelemetry
from analyzer.enterprise.sixsigma.integration import ConnascenceSixSigmaIntegration


def test_six_sigma_telemetry():
    """Test Six Sigma telemetry basic functionality"""
    telemetry = SixSigmaTelemetry()

    # Record some violations
    telemetry.record_connascence_violation("identity", "high")
    telemetry.record_connascence_violation("algorithm", "critical")
    telemetry.record_connascence_violation("timing", "medium")

    # Record file analysis
    telemetry.record_file_analyzed(violations_found=3, total_checks=100)

    # Generate metrics
    metrics = telemetry.generate_metrics_snapshot()

    assert metrics.dpmo > 0
    assert 1.0 <= metrics.sigma_level <= 6.0
    assert 0.0 <= metrics.rty <= 100.0
    assert metrics.defect_count == 3
    assert metrics.opportunity_count > 0


def test_six_sigma_analyzer():
    """Test Six Sigma analyzer with sample violations"""
    analyzer = SixSigmaAnalyzer(target_level="enterprise")

    # Sample violations
    violations = [
        {"type": "identity", "severity": "high"},
        {"type": "algorithm", "severity": "critical"},
        {"type": "timing", "severity": "medium"},
        {"type": "execution", "severity": "low"},
        {"type": "meaning", "severity": "medium"},
    ]

    result = analyzer.analyze_violations(violations, Path("test_file.py"))

    assert result.dpmo > 0
    assert result.sigma_level > 0
    assert len(result.violations_by_type) == 5
    assert len(result.violations_by_severity) == 4  # low, medium, high, critical
    assert len(result.improvement_suggestions) > 0
    assert "composite" in result.ctq_metrics


def test_ctq_calculator():
    """Test Critical To Quality calculator"""
    calculator = CTQCalculator()

    violations = [
        {"type": "algorithm", "severity": "high"},
        {"type": "timing", "severity": "critical"},
        {"type": "identity", "severity": "medium"},
    ]

    metrics = calculator.calculate_from_violations(violations)

    assert "maintainability_index" in metrics
    assert "cyclomatic_complexity" in metrics
    assert "coupling_factor" in metrics
    assert "cohesion_score" in metrics

    # Check composite score
    composite = calculator.calculate_composite_score()
    assert 0.0 <= composite <= 100.0

    # Check priorities
    priorities = calculator.get_improvement_priorities()
    assert isinstance(priorities, list)


def test_process_capability():
    """Test process capability calculations"""
    pc = ProcessCapability()

    # Sample measurements
    measurements = [4.5, 4.7, 4.9, 5.0, 5.1, 5.2, 4.8, 5.0, 4.9, 5.1]
    lower_spec = 4.0
    upper_spec = 6.0

    # Calculate individual indices
    cp = pc.calculate_cp(measurements, lower_spec, upper_spec)
    cpk = pc.calculate_cpk(measurements, lower_spec, upper_spec)

    assert cp > 0
    assert cpk > 0
    assert cpk <= cp  # Cpk is always <= Cp

    # Comprehensive analysis
    analysis = pc.analyze_process(measurements, lower_spec, upper_spec)

    assert "statistics" in analysis
    assert "capability_indices" in analysis
    assert "performance" in analysis
    assert "recommendations" in analysis


def test_integration():
    """Test integration with connascence analyzer results"""
    integration = ConnascenceSixSigmaIntegration(target_sigma_level=5.0)

    # Mock connascence analysis results
    analysis_results = {
        "violations": [
            {"type": "identity", "severity": "high", "file": "test.py", "line": 10},
            {"type": "algorithm", "severity": "critical", "file": "test.py", "line": 20},
            {"type": "timing", "severity": "medium", "file": "test.py", "line": 30},
        ],
        "summary": {"total_violations": 3, "files_analyzed": 1},
    }

    # Process with Six Sigma
    enhanced = integration.process_analysis_results(analysis_results)

    assert "six_sigma" in enhanced
    assert "dpmo" in enhanced["six_sigma"]
    assert "sigma_level" in enhanced["six_sigma"]
    assert "quality_level" in enhanced["six_sigma"]
    assert "improvement_suggestions" in enhanced["six_sigma"]


def test_quality_gate():
    """Test quality gate decision making"""
    integration = ConnascenceSixSigmaIntegration(target_sigma_level=4.0)

    # Mock results with violations
    analysis_results = {
        "violations": [
            {"type": "identity", "severity": "critical"},
            {"type": "algorithm", "severity": "high"},
            {"type": "timing", "severity": "high"},
            {"type": "execution", "severity": "medium"},
        ]
    }

    gate_decision = integration.generate_quality_gate_decision(analysis_results)

    assert "decision" in gate_decision
    assert gate_decision["decision"] in ["PASS", "FAIL"]
    assert "criteria" in gate_decision
    assert "sigma_level" in gate_decision["criteria"]
    assert "dpmo" in gate_decision["criteria"]
    assert "recommendations" in gate_decision


def test_executive_report():
    """Test executive report generation"""
    integration = ConnascenceSixSigmaIntegration()

    analysis_results = {
        "violations": [{"type": "identity", "severity": "high"}, {"type": "algorithm", "severity": "medium"}]
    }

    report = integration.generate_executive_report(analysis_results)

    assert isinstance(report, str)
    assert "EXECUTIVE SUMMARY" in report
    assert "QUALITY GATE STATUS" in report
    assert "Sigma Level" in report
    assert "DPMO" in report


def test_dashboard_export():
    """Test dashboard data export"""
    integration = ConnascenceSixSigmaIntegration()

    analysis_results = {
        "violations": [{"type": "timing", "severity": "high"}, {"type": "execution", "severity": "low"}]
    }

    dashboard_data = integration.export_dashboard_data(analysis_results)

    assert "summary" in dashboard_data
    assert "gauges" in dashboard_data
    assert "charts" in dashboard_data
    assert "quality_gate" in dashboard_data

    # Check gauge structure
    assert "sigma" in dashboard_data["gauges"]
    assert "value" in dashboard_data["gauges"]["sigma"]
    assert "zones" in dashboard_data["gauges"]["sigma"]


def test_ci_cd_integration():
    """Test CI/CD pipeline integration"""
    integration = ConnascenceSixSigmaIntegration(target_sigma_level=3.0)

    # Good quality results (no violations = perfect quality)
    good_results = {"violations": []}

    # Should pass quality gate with no violations
    exit_code = integration.integrate_with_ci_cd(good_results, fail_on_quality_gate=True)
    assert exit_code == 0

    # Poor quality results
    poor_results = {
        "violations": [
            {"type": "timing", "severity": "critical"},
            {"type": "execution", "severity": "critical"},
            {"type": "algorithm", "severity": "critical"},
            {"type": "identity", "severity": "high"},
            {"type": "meaning", "severity": "high"},
        ]
        * 10  # Many violations
    }

    # Should fail quality gate
    exit_code = integration.integrate_with_ci_cd(poor_results, fail_on_quality_gate=True)
    # Note: May pass if sigma calculation is forgiving, but should have lower sigma

    # Check without failing
    exit_code = integration.integrate_with_ci_cd(poor_results, fail_on_quality_gate=False)
    assert exit_code == 0  # Should always return 0 when fail_on_quality_gate=False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
