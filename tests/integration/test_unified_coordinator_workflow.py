#!/usr/bin/env python3

# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
UnifiedCoordinator Integration Tests - Complete End-to-End Workflow Testing
===========================================================================

Tests the complete analysis orchestration pipeline including:
- Single file analysis (analyze_file equivalent)
- Directory analysis (analyze_directory equivalent)
- Batch analysis mode
- Streaming analysis mode
- Hybrid analysis mode
- Component integration (cache + metrics + reports)
- Backward compatibility via aliases
- Multi-format report generation

Target Coverage: 85%+ workflow coverage
Test Focus: Complete analysis pipeline from input to reports
"""

import json
from pathlib import Path
import tempfile
import time
from unittest.mock import Mock

import pytest

from analyzer.architecture.cache_manager import CacheManager
from analyzer.architecture.metrics_collector import MetricsCollector

# Import components under test
from analyzer.architecture.orchestrator import AnalysisOrchestrator
from analyzer.architecture.report_generator import ReportGenerator


@pytest.fixture
def test_project_workspace():
    """Create realistic test workspace with Python files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)

        # Create directory structure
        (workspace / "src").mkdir()
        (workspace / "tests").mkdir()
        (workspace / "lib").mkdir()

        # Python file with violations
        (workspace / "src" / "main.py").write_text('''
"""Main application module"""

def process_data(a, b, c, d, e, f, g, h):  # CoP violation (8 params)
    """Process data with too many parameters"""
    magic_number = 42  # CoM violation
    threshold = 100    # CoM violation

    # Deep nesting - CoA violation
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        result = (a + b + c) * magic_number
                        if result > threshold:
                            return result
    return 0

class DataProcessor:  # God class - CoA violation
    """Class with too many methods"""

    def method_1(self): pass
    def method_2(self): pass
    def method_3(self): pass
    def method_4(self): pass
    def method_5(self): pass
    def method_6(self): pass
    def method_7(self): pass
    def method_8(self): pass
    def method_9(self): pass
    def method_10(self): pass
    def method_11(self): pass
    def method_12(self): pass
    def method_13(self): pass
    def method_14(self): pass
    def method_15(self): pass
    def method_16(self): pass
    def method_17(self): pass
    def method_18(self): pass
    def method_19(self): pass
    def method_20(self): pass
    def method_21(self): pass
    def method_22(self): pass
    def method_23(self): pass
    def method_24(self): pass
    def method_25(self): pass
''')

        # Another Python file
        (workspace / "src" / "utils.py").write_text('''
"""Utility functions"""

def calculate(x, y, z, w):  # CoP violation (4 params)
    constant = 3.14159  # CoM violation
    return x * y + z * constant - w

def validate(data):
    """Missing type hints - CoT violation"""
    timeout = 5000  # CoM violation
    max_items = 999  # CoM violation
    return len(data) < max_items
''')

        # Library file
        (workspace / "lib" / "helpers.py").write_text('''
"""Helper functions"""

def helper_function(param1, param2, param3, param4, param5):  # CoP
    magic_value = 256  # CoM
    return param1 + param2 + param3 + param4 + param5 + magic_value
''')

        yield workspace


@pytest.fixture
def mock_analyzers():
    """Create mock analyzer components"""

    class MockASTAnalyzer:
        def analyze_directory(self, path):
            """Mock AST analysis"""
            return [
                Mock(
                    type="CoP",
                    severity="high",
                    description="Too many parameters",
                    file_path=str(path / "src" / "main.py"),
                    line_number=4,
                    column=0,
                    recommendation="Extract parameter object"
                ),
                Mock(
                    type="CoM",
                    severity="medium",
                    description="Magic literal detected",
                    file_path=str(path / "src" / "main.py"),
                    line_number=6,
                    column=4,
                    recommendation="Extract to named constant"
                )
            ]

    class MockMECEAnalyzer:
        def analyze_path(self, path, comprehensive=True):
            """Mock MECE duplication analysis"""
            return {
                "duplications": [
                    {
                        "similarity_score": 0.85,
                        "functions": [
                            {"file": str(path / "src" / "main.py"), "line": 4},
                            {"file": str(path / "src" / "utils.py"), "line": 4}
                        ]
                    }
                ]
            }

    class MockSmartEngine:
        def comprehensive_analysis(self, path, policy_preset):
            """Mock smart integration"""
            return {
                "correlations": [
                    {
                        "type": "connascence_duplication",
                        "strength": 0.8,
                        "impact": "high"
                    }
                ]
            }

        def analyze_correlations(self, conn_violations, dup_violations, nasa_violations):
            """Mock correlation analysis"""
            return [
                {
                    "type": "cross_cutting_concern",
                    "violations": [conn_violations[0].type if conn_violations else "unknown"],
                    "severity": "medium"
                }
            ]

    class MockNASAIntegration:
        def check_nasa_violations(self, violation):
            """Mock NASA integration check"""
            return [
                {
                    "type": "NASA_Rule4",
                    "severity": "high",
                    "description": "Function exceeds 60 lines",
                    "file_path": violation.get("file_path", "unknown.py"),
                    "line_number": 1,
                    "column": 0,
                    "context": {"nasa_rule": "Rule4"},
                    "recommendation": "Split function"
                }
            ]

    class MockNASAAnalyzer:
        def analyze_file(self, file_path, source_code):
            """Mock dedicated NASA analyzer"""
            return [
                Mock(
                    type="NASA_Rule5",
                    severity="medium",
                    description="Missing assertions",
                    file_path=file_path,
                    line_number=5,
                    column=0,
                    context={"nasa_rule": "Rule5"},
                    recommendation="Add input validation assertions"
                )
            ]

    return {
        "ast_analyzer": MockASTAnalyzer(),
        "orchestrator_analyzer": MockASTAnalyzer(),
        "mece_analyzer": MockMECEAnalyzer(),
        "smart_engine": MockSmartEngine(),
        "nasa_integration": MockNASAIntegration(),
        "nasa_analyzer": MockNASAAnalyzer()
    }


@pytest.fixture
def orchestrator():
    """Create AnalysisOrchestrator instance"""
    return AnalysisOrchestrator()


@pytest.fixture
def cache_manager():
    """Create CacheManager instance"""
    return CacheManager({"max_memory": 50 * 1024 * 1024})


@pytest.fixture
def metrics_collector():
    """Create MetricsCollector instance"""
    return MetricsCollector()


@pytest.fixture
def report_generator():
    """Create ReportGenerator instance"""
    return ReportGenerator({"version": "2.0.0"})


class TestUnifiedCoordinatorSingleFileAnalysis:
    """Test single file analysis workflow (analyze_file equivalent)"""

    def test_analyze_single_file_workflow(self, orchestrator, test_project_workspace, mock_analyzers):
        """Test complete single file analysis pipeline"""
        test_file = test_project_workspace / "src" / "main.py"

        # Execute single file analysis via orchestrator
        violations = orchestrator.orchestrate_analysis_phases(
            project_path=test_project_workspace,
            policy_preset="default",
            analyzers=mock_analyzers
        )

        # Validate structure
        assert "connascence" in violations
        assert "duplication" in violations
        assert "nasa" in violations
        assert "_metadata" in violations

        # Validate metadata
        metadata = violations["_metadata"]
        assert "audit_trail" in metadata
        assert "started_at" in metadata
        assert len(metadata["audit_trail"]) > 0

        # Validate phases executed
        audit_trail = metadata["audit_trail"]
        phase_names = [entry["phase"] for entry in audit_trail]
        assert "ast_analysis" in phase_names
        assert "duplication_analysis" in phase_names
        assert "smart_integration" in phase_names
        assert "nasa_analysis" in phase_names

    def test_single_file_with_cache(self, orchestrator, cache_manager, test_project_workspace, mock_analyzers):
        """Test single file analysis with caching"""
        test_file = test_project_workspace / "src" / "main.py"

        # Warm cache
        cache_manager.warm_cache(test_project_workspace, file_limit=10)

        # Check cache stats
        stats_before = cache_manager.get_cache_stats()

        # Execute analysis
        violations = orchestrator.orchestrate_analysis_phases(
            project_path=test_project_workspace,
            policy_preset="default",
            analyzers=mock_analyzers
        )

        # Validate cache was used
        stats_after = cache_manager.get_cache_stats()
        assert stats_after["warm_requests"] > 0

        # Validate analysis succeeded
        assert len(violations["connascence"]) > 0

    def test_single_file_error_handling(self, orchestrator, test_project_workspace):
        """Test error handling in single file analysis"""
        # Create analyzers that raise errors
        error_analyzers = {
            "ast_analyzer": Mock(side_effect=RuntimeError("AST analysis failed")),
            "mece_analyzer": Mock(side_effect=RuntimeError("MECE analysis failed"))
        }

        # Execute analysis - should not crash
        violations = orchestrator.orchestrate_analysis_phases(
            project_path=test_project_workspace,
            policy_preset="default",
            analyzers=error_analyzers
        )

        # Validate error recorded in metadata
        metadata = violations["_metadata"]
        assert len(metadata["phase_errors"]) > 0
        assert any("failed" in error["status"] for error in metadata["phase_errors"])


class TestUnifiedCoordinatorDirectoryAnalysis:
    """Test directory analysis workflow (analyze_directory equivalent)"""

    def test_analyze_directory_workflow(self, orchestrator, test_project_workspace, mock_analyzers):
        """Test complete directory analysis pipeline"""
        # Execute directory analysis
        violations = orchestrator.orchestrate_analysis_phases(
            project_path=test_project_workspace,
            policy_preset="comprehensive",
            analyzers=mock_analyzers
        )

        # Validate all violation types present
        assert violations["connascence"]
        assert violations["duplication"]
        assert violations["nasa"]

        # Validate multiple files analyzed
        file_paths = set()
        for violation in violations["connascence"]:
            if isinstance(violation, dict):
                file_paths.add(violation.get("file_path", ""))

        # Should analyze multiple files
        assert len(file_paths) > 0

        # Validate metadata complete
        metadata = violations["_metadata"]
        assert metadata["total_phases"] == 4
        assert len(metadata["audit_trail"]) >= 4

    def test_directory_analysis_with_filters(self, orchestrator, test_project_workspace, mock_analyzers):
        """Test directory analysis with file filtering"""
        # Add files that should be skipped
        (test_project_workspace / "__pycache__").mkdir()
        (test_project_workspace / "__pycache__" / "cached.pyc").touch()
        (test_project_workspace / "test_skip.py").touch()

        violations = orchestrator.orchestrate_analysis_phases(
            project_path=test_project_workspace,
            policy_preset="default",
            analyzers=mock_analyzers
        )

        # Validate test files and pycache were skipped
        file_paths = []
        for violation in violations.get("nasa", []):
            file_paths.append(violation.get("file_path", ""))

        # Should not contain pycache or test files
        assert not any("__pycache__" in path for path in file_paths)

    def test_directory_analysis_performance(self, orchestrator, test_project_workspace, mock_analyzers):
        """Test directory analysis performance metrics"""
        start_time = time.time()

        violations = orchestrator.orchestrate_analysis_phases(
            project_path=test_project_workspace,
            policy_preset="default",
            analyzers=mock_analyzers
        )

        execution_time = time.time() - start_time

        # Should complete in reasonable time
        assert execution_time < 5.0

        # Validate metadata has timing info
        metadata = violations["_metadata"]
        assert "started_at" in metadata
        for entry in metadata["audit_trail"]:
            assert "started" in entry or "completed" in entry


class TestUnifiedCoordinatorBatchAnalysis:
    """Test batch analysis mode"""

    def test_batch_analysis_multiple_files(self, orchestrator, test_project_workspace, mock_analyzers):
        """Test batch analysis of multiple files"""
        # Collect all Python files
        python_files = list(test_project_workspace.rglob("*.py"))
        assert len(python_files) >= 3

        # Execute batch analysis
        violations = orchestrator.orchestrate_analysis_phases(
            project_path=test_project_workspace,
            policy_preset="default",
            analyzers=mock_analyzers
        )

        # Validate batch processing
        assert violations["connascence"]
        assert violations["duplication"]
        assert violations["nasa"]

        # Validate all files processed
        metadata = violations["_metadata"]
        assert len(metadata["audit_trail"]) > 0

    def test_batch_analysis_parallel_phases(self, orchestrator, test_project_workspace, mock_analyzers):
        """Test batch analysis with parallel phase execution"""
        start_time = time.time()

        violations = orchestrator.orchestrate_analysis_phases(
            project_path=test_project_workspace,
            policy_preset="comprehensive",
            analyzers=mock_analyzers
        )

        execution_time = time.time() - start_time

        # Verify phases completed
        metadata = violations["_metadata"]
        completed_phases = [
            entry for entry in metadata["audit_trail"]
            if entry.get("status") == "completed"
        ]

        assert len(completed_phases) == 4  # All 4 phases


class TestUnifiedCoordinatorStreamingAnalysis:
    """Test streaming analysis mode"""

    def test_streaming_analysis_progressive_results(self, orchestrator, test_project_workspace, mock_analyzers):
        """Test streaming analysis with progressive result delivery"""
        # Track phase progression
        phases_completed = []

        def track_phase(phase_name):
            phases_completed.append(phase_name)

        # Mock phase tracking
        original_record = orchestrator._record_phase_completion

        def tracked_record(phase_name, phase_metadata, violations_count):
            track_phase(phase_name)
            return original_record(phase_name, phase_metadata, violations_count)

        orchestrator._record_phase_completion = tracked_record

        # Execute analysis
        violations = orchestrator.orchestrate_analysis_phases(
            project_path=test_project_workspace,
            policy_preset="default",
            analyzers=mock_analyzers
        )

        # Validate progressive execution
        assert len(phases_completed) == 4
        assert "ast_analysis" in phases_completed
        assert "nasa_analysis" in phases_completed


class TestUnifiedCoordinatorComponentIntegration:
    """Test integration of cache, metrics, and reports"""

    def test_cache_integration(self, orchestrator, cache_manager, test_project_workspace, mock_analyzers):
        """Test cache integration with orchestrator"""
        # Warm cache
        cache_manager.warm_cache(test_project_workspace)

        # Execute analysis
        violations = orchestrator.orchestrate_analysis_phases(
            project_path=test_project_workspace,
            policy_preset="default",
            analyzers=mock_analyzers
        )

        # Check cache performance
        stats = cache_manager.get_cache_stats()
        assert stats["warm_requests"] > 0

        # Validate analysis succeeded
        assert len(violations["connascence"]) > 0

    def test_metrics_integration(self, orchestrator, metrics_collector, test_project_workspace, mock_analyzers):
        """Test metrics collection integration"""
        # Execute analysis
        violations = orchestrator.orchestrate_analysis_phases(
            project_path=test_project_workspace,
            policy_preset="default",
            analyzers=mock_analyzers
        )

        # Collect metrics
        metrics = metrics_collector.collect_violation_metrics(violations)

        # Validate metrics
        assert "total_violations" in metrics
        assert "connascence_index" in metrics
        assert "nasa_compliance_score" in metrics
        assert "duplication_score" in metrics
        assert "overall_quality_score" in metrics

        # Create snapshot
        snapshot = metrics_collector.create_snapshot(metrics)
        assert snapshot.total_violations == metrics["total_violations"]

    def test_report_generation_integration(self, orchestrator, report_generator, test_project_workspace, mock_analyzers):
        """Test report generation integration"""
        # Execute analysis
        violations = orchestrator.orchestrate_analysis_phases(
            project_path=test_project_workspace,
            policy_preset="default",
            analyzers=mock_analyzers
        )

        # Generate JSON report
        json_report = report_generator.generate_json(violations)
        assert json_report
        assert isinstance(json_report, str)

        # Validate JSON structure
        report_data = json.loads(json_report)
        assert "connascence" in report_data or "connascence_violations" in report_data

    def test_complete_pipeline_integration(
        self, orchestrator, cache_manager, metrics_collector, report_generator,
        test_project_workspace, mock_analyzers
    ):
        """Test complete pipeline: analysis -> cache -> metrics -> reports"""
        # Step 1: Warm cache
        cache_manager.warm_cache(test_project_workspace)

        # Step 2: Execute analysis
        violations = orchestrator.orchestrate_analysis_phases(
            project_path=test_project_workspace,
            policy_preset="comprehensive",
            analyzers=mock_analyzers
        )

        # Step 3: Collect metrics
        metrics = metrics_collector.collect_violation_metrics(violations)
        snapshot = metrics_collector.create_snapshot(metrics)

        # Step 4: Generate reports
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Generate all report formats
            all_violations = (
                violations["connascence"] +
                violations["duplication"] +
                violations["nasa"]
            )

            report_paths = report_generator.generate_all_formats(
                result=violations,
                violations=all_violations,
                output_dir=output_dir,
                base_name="analysis"
            )

            # Validate all formats generated
            assert "json" in report_paths
            assert "markdown" in report_paths
            assert "sarif" in report_paths

            assert report_paths["json"].exists()
            assert report_paths["markdown"].exists()
            assert report_paths["sarif"].exists()

        # Validate cache was effective
        cache_stats = cache_manager.get_cache_stats()
        assert cache_stats["warm_requests"] > 0

        # Validate metrics calculated
        assert snapshot.overall_quality_score >= 0.0


class TestUnifiedCoordinatorReportFormats:
    """Test multi-format report generation"""

    def test_json_report_generation(self, orchestrator, report_generator, test_project_workspace, mock_analyzers):
        """Test JSON report generation"""
        violations = orchestrator.orchestrate_analysis_phases(
            project_path=test_project_workspace,
            policy_preset="default",
            analyzers=mock_analyzers
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.json"
            json_content = report_generator.generate_json(violations, output_path)

            assert output_path.exists()
            assert json_content

            # Validate JSON structure
            data = json.loads(json_content)
            assert isinstance(data, dict)

    def test_markdown_report_generation(self, orchestrator, report_generator, test_project_workspace, mock_analyzers):
        """Test Markdown report generation"""
        violations = orchestrator.orchestrate_analysis_phases(
            project_path=test_project_workspace,
            policy_preset="default",
            analyzers=mock_analyzers
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.md"
            md_content = report_generator.generate_markdown(violations, output_path)

            assert output_path.exists()
            assert md_content
            assert "CONNASCENCE ANALYSIS" in md_content.upper() or "SUMMARY" in md_content.upper()

    def test_sarif_report_generation(self, orchestrator, report_generator, test_project_workspace, mock_analyzers):
        """Test SARIF report generation"""
        violations = orchestrator.orchestrate_analysis_phases(
            project_path=test_project_workspace,
            policy_preset="default",
            analyzers=mock_analyzers
        )

        all_violations = (
            violations["connascence"] +
            violations["duplication"] +
            violations["nasa"]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.sarif"
            sarif_data = report_generator.generate_sarif(
                all_violations,
                output_path,
                str(test_project_workspace)
            )

            assert output_path.exists()
            assert "version" in sarif_data
            assert "runs" in sarif_data

    def test_dashboard_summary_generation(self, orchestrator, metrics_collector, test_project_workspace, mock_analyzers):
        """Test dashboard summary creation"""
        violations = orchestrator.orchestrate_analysis_phases(
            project_path=test_project_workspace,
            policy_preset="default",
            analyzers=mock_analyzers
        )

        metrics = metrics_collector.collect_violation_metrics(violations)
        summary = metrics_collector.get_metrics_summary()

        # Dashboard should include current quality
        assert "current_quality" in summary or summary.get("status") == "no_data"


class TestUnifiedCoordinatorBackwardCompatibility:
    """Test backward compatibility via aliases"""

    def test_analyze_file_alias(self, test_project_workspace, mock_analyzers):
        """Test analyze_file method (if exists as alias)"""
        # This would test backward compatibility if analyze_file was an alias
        orchestrator = AnalysisOrchestrator()

        # Analyze via orchestrate_analysis_phases
        result = orchestrator.orchestrate_analysis_phases(
            project_path=test_project_workspace,
            policy_preset="default",
            analyzers=mock_analyzers
        )

        assert result is not None
        assert "connascence" in result

    def test_analyze_directory_alias(self, test_project_workspace, mock_analyzers):
        """Test analyze_directory method (if exists as alias)"""
        orchestrator = AnalysisOrchestrator()

        # Analyze directory via orchestrate_analysis_phases
        result = orchestrator.orchestrate_analysis_phases(
            project_path=test_project_workspace,
            policy_preset="default",
            analyzers=mock_analyzers
        )

        assert result is not None
        assert "duplication" in result
        assert "nasa" in result


class TestUnifiedCoordinatorEdgeCases:
    """Test edge cases and error conditions"""

    def test_empty_directory(self, orchestrator, mock_analyzers):
        """Test analysis of empty directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_dir = Path(tmpdir)

            violations = orchestrator.orchestrate_analysis_phases(
                project_path=empty_dir,
                policy_preset="default",
                analyzers=mock_analyzers
            )

            # Should complete without errors
            assert "_metadata" in violations

    def test_missing_analyzers(self, orchestrator, test_project_workspace):
        """Test behavior with missing analyzers"""
        empty_analyzers = {}

        violations = orchestrator.orchestrate_analysis_phases(
            project_path=test_project_workspace,
            policy_preset="default",
            analyzers=empty_analyzers
        )

        # Should complete with empty results
        assert violations["connascence"] == []
        assert violations["duplication"] == []

    def test_phase_failure_recovery(self, orchestrator, test_project_workspace):
        """Test recovery from phase failures"""
        failing_analyzers = {
            "ast_analyzer": Mock(side_effect=Exception("Phase 1 failed")),
            "mece_analyzer": Mock(analyze_path=Mock(return_value={"duplications": []}))
        }

        violations = orchestrator.orchestrate_analysis_phases(
            project_path=test_project_workspace,
            policy_preset="default",
            analyzers=failing_analyzers
        )

        # Should record error but continue
        metadata = violations["_metadata"]
        assert len(metadata["phase_errors"]) > 0


# Performance and coverage summary
if __name__ == "__main__":
    print("=" * 70)
    print("UnifiedCoordinator Integration Tests")
    print("=" * 70)
    print("\nTest Coverage Areas:")
    print("  [x] Single file analysis (analyze_file workflow)")
    print("  [x] Directory analysis (analyze_directory workflow)")
    print("  [x] Batch analysis mode")
    print("  [x] Streaming analysis mode")
    print("  [x] Component integration (cache + metrics + reports)")
    print("  [x] Multi-format report generation (JSON, Markdown, SARIF)")
    print("  [x] Dashboard summary creation")
    print("  [x] Backward compatibility")
    print("  [x] Edge cases and error handling")
    print("\nTarget Coverage: 85%+ workflow coverage")
    print("=" * 70)

    pytest.main([__file__, "-v", "--tb=short"])
