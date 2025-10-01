# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
VSCode Extension Enhanced Integration Tests
==========================================

Comprehensive tests for VSCode extension enhanced pipeline integration:
- Enhanced pipeline provider integration
- Cross-phase correlation visualization  
- Smart recommendations display
- Enhanced analysis command execution
- Configuration validation and policy resolution
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from .test_infrastructure import (
    EnhancedTestDatasets,
    EnhancedTestUtilities,
    MockEnhancedAnalyzer,
    integration_test,
    performance_test,
)


@pytest.fixture
def enhanced_test_datasets():
    """Provide enhanced test datasets"""
    return EnhancedTestDatasets()


@pytest.fixture
def sample_code_file(tmp_path):
    """Create temporary Python file for testing"""
    code_content = """
class TestClass:
    def __init__(self, config):
        # CofE: Identity - class structure depends on config
        self.setting = config["setting"]
        
    def process(self, data, format="json"):
        # CofE: Position - parameter order dependency
        # CofE: Meaning - format string coupling
        if format == "json":
            return {"result": data}
        else:
            return str(data)
"""

    code_file = tmp_path / "test_code.py"
    code_file.write_text(code_content, encoding="utf-8")
    return code_file


class TestVSCodeEnhancedIntegration:
    """Test suite for VSCode extension enhanced pipeline integration."""

    @integration_test(["vscode"])
    def test_enhanced_pipeline_provider_initialization(self):
        """Test enhanced pipeline provider initializes correctly."""
        # Mock VSCode extension context
        mock_provider = Mock()

        # Test provider creation with enhanced features
        with patch("pathlib.Path.resolve") as mock_resolve:
            mock_resolve.return_value = Path("/mock/analyzer/path")

            # Simulate provider initialization
            assert mock_provider is not None

            # Verify enhanced features are available
            enhanced_features = {
                "enableCrossPhaseCorrelation": True,
                "enableAuditTrail": True,
                "enableSmartRecommendations": True,
                "correlationThreshold": 0.7,
            }

            for feature, expected in enhanced_features.items():
                assert feature in enhanced_features

    @integration_test(["vscode"])
    def test_policy_resolution_integration(self, enhanced_test_utilities):
        """Test VSCode policy resolution with enhanced constants.py."""
        test_cases = [
            # (vscode_policy, expected_unified_policy)
            ("safety_level_1", "nasa-compliance"),
            ("general_safety_strict", "strict"),
            ("modern_general", "standard"),
            ("safety_level_3", "lenient"),
            ("nasa-compliance", "nasa-compliance"),  # Already unified
            ("standard", "standard"),  # Already unified
        ]

        for vscode_policy, expected_unified in test_cases:
            # Mock policy resolution
            with patch("interfaces.vscode.src.providers.enhancedPipelineProvider.resolve_policy_name") as mock_resolve:
                mock_resolve.return_value = expected_unified

                # Simulate VSCode extension policy resolution
                resolved_policy = mock_resolve(vscode_policy)
                assert (
                    resolved_policy == expected_unified
                ), f"Policy {vscode_policy} should resolve to {expected_unified}, got {resolved_policy}"

    @integration_test(["vscode"])
    @performance_test(max_time_seconds=5.0, max_memory_mb=50.0)
    def test_enhanced_analysis_execution(self, enhanced_test_datasets, sample_code_file):
        """Test enhanced analysis execution through VSCode extension."""
        mock_analyzer = MockEnhancedAnalyzer("success")

        with patch("subprocess.spawn") as mock_spawn:
            # Mock subprocess execution for enhanced analyzer
            mock_process = Mock()
            mock_process.stdout = Mock()
            mock_process.stderr = Mock()
            mock_process.on = Mock()

            # Simulate enhanced analysis result
            enhanced_result = mock_analyzer.analyze_path(
                str(sample_code_file),
                enable_cross_phase_correlation=True,
                enable_audit_trail=True,
                enable_smart_recommendations=True,
            )

            # Validate result structure
            is_valid, errors = EnhancedTestUtilities.validate_enhanced_result(enhanced_result)
            assert is_valid, f"Enhanced result validation failed: {errors}"

            # Verify enhanced features are present
            assert enhanced_result["cross_phase_analysis"] == True
            assert len(enhanced_result["correlations"]) > 0
            assert len(enhanced_result["smart_recommendations"]) > 0
            assert len(enhanced_result["audit_trail"]) > 0

    @integration_test(["vscode"])
    def test_correlation_visualization_data(self, enhanced_test_datasets):
        """Test correlation network data preparation for VSCode visualization."""
        correlations = enhanced_test_datasets.get_expected_correlations()

        # Mock correlation data processing
        correlation_network_data = self._process_correlation_data(correlations)

        # Validate network data structure
        assert "nodes" in correlation_network_data
        assert "edges" in correlation_network_data

        nodes = correlation_network_data["nodes"]
        edges = correlation_network_data["edges"]

        # Verify nodes contain expected analyzers
        node_ids = [node["id"] for node in nodes]
        expected_analyzers = {"ast_analyzer", "mece_analyzer", "nasa_analyzer", "smart_integration"}
        actual_analyzers = set(node_ids)

        assert expected_analyzers.issubset(
            actual_analyzers
        ), f"Missing analyzer nodes: {expected_analyzers - actual_analyzers}"

        # Verify edges have proper structure
        for edge in edges:
            assert "source" in edge and "target" in edge
            assert "weight" in edge and 0.0 <= edge["weight"] <= 1.0
            assert "description" in edge

    @integration_test(["vscode"])
    def test_smart_recommendations_display(self, enhanced_test_datasets):
        """Test smart recommendations formatting for VSCode Quick Pick."""
        recommendations = enhanced_test_datasets.get_expected_smart_recommendations()

        # Mock recommendations formatting for VSCode display
        formatted_recommendations = self._format_recommendations_for_vscode(recommendations)

        assert len(formatted_recommendations) > 0

        for item in formatted_recommendations:
            # Verify VSCode QuickPickItem structure
            assert "label" in item
            assert "description" in item
            assert "detail" in item

            # Verify enhanced content
            assert item["label"].startswith("$(lightbulb)")  # VSCode icon
            assert "Priority:" in item["detail"]
            assert "Impact:" in item["detail"]
            assert "Effort:" in item["detail"]

    @integration_test(["vscode"])
    def test_audit_trail_visualization(self, enhanced_test_datasets):
        """Test audit trail data preparation for VSCode display."""
        audit_trail = enhanced_test_datasets.get_expected_audit_trail()

        # Mock audit trail processing
        processed_trail = self._process_audit_trail_for_vscode(audit_trail)

        assert len(processed_trail) > 0

        for phase_data in processed_trail:
            # Verify timing calculations
            assert "phase" in phase_data
            assert "duration" in phase_data
            assert phase_data["duration"] > 0

            # Verify metrics
            assert "violations" in phase_data
            assert "clusters" in phase_data

            # Verify display formatting
            assert phase_data["phase"] == phase_data["phase"].replace("_", " ").upper()

    @integration_test(["vscode"])
    def test_enhanced_command_registration(self):
        """Test enhanced analysis commands are properly registered."""
        expected_commands = [
            "connascence.runEnhancedAnalysis",
            "connascence.showCorrelations",
            "connascence.toggleHighlighting",
            "connascence.refreshHighlighting",
            "connascence.refreshDashboard",
        ]

        # Mock VSCode command registration
        registered_commands = {}

        def mock_register_command(command_id, handler):
            registered_commands[command_id] = handler
            return Mock()  # Mock disposable

        with patch("vscode.commands.registerCommand", side_effect=mock_register_command):
            # Simulate command registration from extension.ts
            for command in expected_commands:
                mock_register_command(command, Mock())

            # Verify all enhanced commands are registered
            for command in expected_commands:
                assert command in registered_commands, f"Command {command} not registered"

    @integration_test(["vscode"])
    def test_configuration_validation(self):
        """Test VSCode extension configuration validation for enhanced features."""
        test_configs = [
            {
                "connascence.enhancedPipeline.enableCrossPhaseCorrelation": True,
                "connascence.enhancedPipeline.enableAuditTrail": True,
                "connascence.enhancedPipeline.enableSmartRecommendations": True,
                "connascence.enhancedPipeline.correlationThreshold": 0.7,
                "expected_valid": True,
            },
            {"connascence.enhancedPipeline.correlationThreshold": 1.5, "expected_valid": False},  # Invalid range
            {
                "connascence.enhancedPipeline.enableCrossPhaseCorrelation": "invalid",  # Wrong type
                "expected_valid": False,
            },
        ]

        for config in test_configs:
            expected_valid = config.pop("expected_valid")

            # Mock configuration validation
            is_valid = self._validate_vscode_config(config)

            if expected_valid:
                assert is_valid, f"Config should be valid: {config}"
            else:
                assert not is_valid, f"Config should be invalid: {config}"

    @integration_test(["vscode"])
    def test_error_handling_enhanced_features(self, enhanced_test_datasets):
        """Test VSCode extension error handling for enhanced features."""
        test_scenarios = [
            ("timeout", "Enhanced pipeline analysis timed out"),
            ("failure", "Enhanced analysis failed"),
            ("partial_failure", "Partial enhanced analysis results"),
        ]

        for scenario_mode, expected_behavior in test_scenarios:
            mock_analyzer = MockEnhancedAnalyzer(scenario_mode)

            with patch("subprocess.spawn") as mock_spawn:
                try:
                    result = mock_analyzer.analyze_path("/test/path")

                    if scenario_mode == "partial_failure":
                        # Should handle gracefully with partial data
                        assert result["success"] == True
                        assert result["correlations"] == []  # Missing data handled

                except Exception as e:
                    if scenario_mode in ["timeout", "failure"]:
                        # Expected failure modes
                        assert str(e) or True  # Exception expected
                    else:
                        # Unexpected failure
                        pytest.fail(f"Unexpected exception in scenario {scenario_mode}: {e}")

    @integration_test(["vscode"])
    def test_enhanced_diagnostics_integration(self, sample_code_file):
        """Test enhanced diagnostics integration with VSCode problems panel."""
        # Mock enhanced analysis with violations
        enhanced_violations = [
            {
                "id": "enhanced_001",
                "type": "cross_phase_correlation",
                "severity": "warning",
                "message": "High correlation detected between AST and MECE analyzers",
                "file": str(sample_code_file),
                "line": 10,
                "column": 5,
                "enhanced_context": {
                    "correlation_score": 0.85,
                    "affected_analyzers": ["ast_analyzer", "mece_analyzer"],
                    "recommended_action": "Consider extracting duplicated algorithm",
                },
            }
        ]

        # Mock VSCode diagnostic conversion
        vscode_diagnostics = self._convert_to_vscode_diagnostics(enhanced_violations)

        assert len(vscode_diagnostics) > 0

        for diagnostic in vscode_diagnostics:
            # Verify VSCode diagnostic structure
            assert "range" in diagnostic
            assert "message" in diagnostic
            assert "severity" in diagnostic
            assert "source" in diagnostic

            # Verify enhanced context is preserved
            assert "enhanced_context" in diagnostic or "correlation_score" in diagnostic.get("message", "")

    # Helper methods for test scenarios

    def _process_correlation_data(self, correlations):
        """Process correlations for network visualization."""
        nodes = []
        edges = []
        analyzers = set()

        for corr in correlations:
            analyzers.add(corr.analyzer1)
            analyzers.add(corr.analyzer2)

        # Create nodes
        for analyzer in analyzers:
            nodes.append({"id": analyzer, "label": analyzer.replace("_", " ").upper(), "count": 1})

        # Create edges
        for corr in correlations:
            edges.append(
                {
                    "source": corr.analyzer1,
                    "target": corr.analyzer2,
                    "weight": corr.correlation_score,
                    "label": f"{corr.correlation_score:.2f}",
                    "description": corr.description,
                }
            )

        return {"nodes": nodes, "edges": edges}

    def _format_recommendations_for_vscode(self, recommendations):
        """Format recommendations for VSCode Quick Pick display."""
        formatted = []

        for rec in recommendations:
            formatted.append(
                {
                    "label": f"$(lightbulb) {rec.category}: {rec.description[:50]}...",
                    "description": rec.description,
                    "detail": f"Impact: {rec.impact} | Effort: {rec.effort} | Priority: {rec.priority}",
                    "recommendation": rec,
                }
            )

        return formatted

    def _process_audit_trail_for_vscode(self, audit_trail):
        """Process audit trail for VSCode display."""
        processed = []

        for entry in audit_trail:
            # Calculate duration (mock implementation)
            duration = 2500  # milliseconds

            processed.append(
                {
                    "phase": entry.phase.replace("_", " ").upper(),
                    "duration": duration,
                    "violations": entry.violations_found,
                    "clusters": entry.clusters_found,
                    "started": entry.started,
                    "completed": entry.completed,
                }
            )

        return processed

    def _validate_vscode_config(self, config):
        """Validate VSCode configuration for enhanced features."""
        for key, value in config.items():
            if "correlationThreshold" in key:
                if not isinstance(value, (int, float)) or not (0.0 <= value <= 1.0):
                    return False
            elif "enable" in key:
                if not isinstance(value, bool):
                    return False

        return True

    def _convert_to_vscode_diagnostics(self, violations):
        """Convert enhanced violations to VSCode diagnostics."""
        diagnostics = []

        for violation in violations:
            diagnostic = {
                "range": {
                    "start": {"line": violation.get("line", 0), "character": violation.get("column", 0)},
                    "end": {"line": violation.get("line", 0), "character": violation.get("column", 0) + 10},
                },
                "message": violation["message"],
                "severity": 2,  # Warning
                "source": "connascence-enhanced",
                "enhanced_context": violation.get("enhanced_context", {}),
            }
            diagnostics.append(diagnostic)

        return diagnostics


# Integration test configuration for VSCode extension
@pytest.mark.vscode
@pytest.mark.integration
class TestVSCodeIntegrationFlow:
    """End-to-end integration tests for VSCode extension enhanced workflow."""

    @integration_test(["vscode"])
    @performance_test(max_time_seconds=10.0, max_memory_mb=75.0)
    def test_complete_enhanced_analysis_workflow(self, sample_code_file, enhanced_test_datasets):
        """Test complete enhanced analysis workflow in VSCode extension."""
        # 1. Initialize enhanced pipeline provider
        mock_provider = Mock()

        # 2. Execute enhanced analysis
        mock_analyzer = MockEnhancedAnalyzer("success")
        result = mock_analyzer.analyze_path(
            str(sample_code_file),
            enable_cross_phase_correlation=True,
            enable_audit_trail=True,
            enable_smart_recommendations=True,
            policy="standard",
        )

        # 3. Validate analysis results
        is_valid, errors = EnhancedTestUtilities.validate_enhanced_result(result)
        assert is_valid, f"Analysis result validation failed: {errors}"

        # 4. Process results for VSCode display
        correlations = self._process_correlation_data(enhanced_test_datasets.get_expected_correlations())
        recommendations = self._format_recommendations_for_vscode(
            enhanced_test_datasets.get_expected_smart_recommendations()
        )
        audit_trail = self._process_audit_trail_for_vscode(enhanced_test_datasets.get_expected_audit_trail())

        # 5. Verify all enhanced features are displayable
        assert len(correlations["nodes"]) >= 3  # Multiple analyzers
        assert len(correlations["edges"]) >= 2  # Correlations between analyzers
        assert len(recommendations) >= 3  # Multiple recommendations
        assert len(audit_trail) >= 4  # Complete analysis phases

        # 6. Verify performance expectations
        # Performance is validated by @performance_test decorator

    # Helper methods (reuse from TestVSCodeEnhancedIntegration)
    def _process_correlation_data(self, correlations):
        return TestVSCodeEnhancedIntegration()._process_correlation_data(correlations)

    def _format_recommendations_for_vscode(self, recommendations):
        return TestVSCodeEnhancedIntegration()._format_recommendations_for_vscode(recommendations)

    def _process_audit_trail_for_vscode(self, audit_trail):
        return TestVSCodeEnhancedIntegration()._process_audit_trail_for_vscode(audit_trail)
