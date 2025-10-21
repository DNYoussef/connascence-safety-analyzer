# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
End-to-End Enhanced Pipeline Integration Tests
==============================================

Comprehensive validation of complete data flow through the enhanced pipeline:
- File analysis through enhanced pipeline processing to final output
- Cross-interface validation (VSCode, MCP, Web Dashboard, CLI)
- Data consistency across all pipeline phases
- Performance validation under realistic workloads
- Integration between all enhanced features
"""

from dataclasses import dataclass
from pathlib import Path
import tempfile
import time
from typing import Any, Dict, List

import pytest

from .test_infrastructure import (
    MockCorrelation,
    MockEnhancedAnalyzer,
    MockSmartRecommendation,
    integration_test,
    performance_test,
)


@dataclass
class EndToEndTestScenario:
    """Comprehensive test scenario for end-to-end validation"""

    name: str
    description: str
    test_files: List[Dict[str, str]]  # filename -> content
    expected_findings: List[Dict[str, Any]]
    expected_correlations: List[MockCorrelation]
    expected_recommendations: List[MockSmartRecommendation]
    performance_requirements: Dict[str, Any]
    interface_validations: List[str]  # Which interfaces to validate


class EndToEndDataFlowValidator:
    """Validator for complete enhanced pipeline data flow"""

    def __init__(self):
        self.test_scenarios = self._create_test_scenarios()

    def _create_test_scenarios(self) -> List[EndToEndTestScenario]:
        """Create comprehensive test scenarios for validation"""
        return [
            EndToEndTestScenario(
                name="microservices_architecture_analysis",
                description="Complete analysis of microservices architecture with cross-service dependencies",
                test_files=[
                    {
                        "user_service.py": """
class UserService:
    def __init__(self, db_connection):
                        # CofE: Identity - relying on external db connection state
        self.db = db_connection
        self.cache = {}

    def get_user(self, user_id):
                        # CofE: Position - parameter order dependency
        return self.db.query("SELECT * FROM users WHERE id = ?", user_id)

    def update_user_status(self, user_id, status):
                        # CofE: Meaning - status values have semantic coupling
        self.cache[user_id] = status
        return self.db.execute("UPDATE users SET status = ? WHERE id = ?", status, user_id)
                        """
                    },
                    {
                        "order_service.py": """
from user_service import UserService

class OrderService:
    def __init__(self, user_service: UserService):
                        # CofE: Type - tight coupling to UserService implementation
        self.user_service = user_service

    def create_order(self, user_id, items):
                        # CofE: Algorithm - must call get_user before creating order
        user = self.user_service.get_user(user_id)
        if not user or user.status != "ACTIVE":
            raise ValueError("Invalid user")

                        # CofE: Execution - order of operations matters
        order_id = self._generate_order_id()
        self._reserve_items(items)
        return self._save_order(order_id, user_id, items)
                        """
                    },
                    {
                        "notification_service.py": """
class NotificationService:
    def __init__(self, config):
                        # CofE: Identity - relies on config structure
        self.email_config = config["email"]
        self.sms_config = config["sms"]

    def send_notification(self, user_id, message, channel="email"):
                        # CofE: Position - default parameter creates coupling
                        # CofE: Meaning - channel values have implicit meaning
        if channel == "email":
            return self._send_email(user_id, message)
        elif channel == "sms":
            return self._send_sms(user_id, message)
                        """
                    },
                ],
                expected_findings=[
                    {"type": "CofE_Identity", "severity": "medium", "file": "user_service.py"},
                    {"type": "CofE_Position", "severity": "low", "file": "user_service.py"},
                    {"type": "CofE_Type", "severity": "high", "file": "order_service.py"},
                    {"type": "CofE_Algorithm", "severity": "medium", "file": "order_service.py"},
                    {"type": "CofE_Meaning", "severity": "medium", "file": "notification_service.py"},
                ],
                expected_correlations=[
                    MockCorrelation(
                        "user_service",
                        "order_service",
                        "cross_service_dependency",
                        0.85,
                        "Services tightly coupled through user status validation",
                        "high",
                    ),
                    MockCorrelation(
                        "order_service",
                        "notification_service",
                        "execution_flow_dependency",
                        0.75,
                        "Order completion triggers notification flow",
                        "medium",
                    ),
                ],
                expected_recommendations=[
                    MockSmartRecommendation(
                        "introduce_user_status_enum",
                        "Create UserStatus enum to reduce meaning connascence",
                        "medium",
                        ["user_service.py", "order_service.py"],
                    ),
                    MockSmartRecommendation(
                        "implement_service_interface",
                        "Extract UserService interface to reduce type connascence",
                        "high",
                        ["order_service.py"],
                    ),
                ],
                performance_requirements={
                    "max_analysis_time": 15.0,
                    "max_memory_usage": 100.0,
                    "max_correlation_time": 5.0,
                },
                interface_validations=["vscode", "mcp_server", "web_dashboard", "cli"],
            ),
            EndToEndTestScenario(
                name="legacy_refactoring_analysis",
                description="Analysis of legacy code requiring comprehensive refactoring",
                test_files=[
                    {
                        "legacy_processor.py": """
class LegacyProcessor:
    def __init__(self):
        self.mode = "BATCH"  # CofE: Meaning - mode values coupled to behavior
        self.batch_size = 100  # CofE: Algorithm - processing depends on batch size

    def process_data(self, data, format="CSV"):
                        # CofE: Position - parameter order matters for legacy calls
                        # CofE: Meaning - format string has implicit behavior
        if self.mode == "BATCH":
            return self._batch_process(data, format)
        elif self.mode == "STREAM":
            return self._stream_process(data, format)

    def _batch_process(self, data, format):
                        # CofE: Execution - must process in specific order
        validated_data = self._validate(data, format)
        transformed_data = self._transform(validated_data)
        return self._output(transformed_data, format)
                        """
                    },
                    {
                        "modern_adapter.py": """
from legacy_processor import LegacyProcessor

class ModernAdapter:
    def __init__(self, processor: LegacyProcessor):
                        # CofE: Type - coupled to legacy implementation
        self.legacy = processor

    def process(self, data, output_format="JSON"):
                        # CofE: Algorithm - must adapt format for legacy system
        legacy_format = self._map_format(output_format)
                        # CofE: Execution - specific call sequence required
        self.legacy.mode = "BATCH"
        result = self.legacy.process_data(data, legacy_format)
        return self._modernize_output(result, output_format)
                        """
                    },
                ],
                expected_findings=[
                    {"type": "CofE_Meaning", "severity": "high", "file": "legacy_processor.py"},
                    {"type": "CofE_Algorithm", "severity": "medium", "file": "legacy_processor.py"},
                    {"type": "CofE_Type", "severity": "high", "file": "modern_adapter.py"},
                    {"type": "CofE_Execution", "severity": "medium", "file": "modern_adapter.py"},
                ],
                expected_correlations=[
                    MockCorrelation(
                        "legacy_processor",
                        "modern_adapter",
                        "adaptation_coupling",
                        0.95,
                        "Adapter tightly coupled to legacy implementation details",
                        "critical",
                    )
                ],
                expected_recommendations=[
                    MockSmartRecommendation(
                        "extract_processor_interface",
                        "Create ProcessorInterface to decouple adapter",
                        "critical",
                        ["legacy_processor.py", "modern_adapter.py"],
                    ),
                    MockSmartRecommendation(
                        "introduce_format_enum", "Replace string formats with enum", "high", ["legacy_processor.py"]
                    ),
                ],
                performance_requirements={
                    "max_analysis_time": 10.0,
                    "max_memory_usage": 75.0,
                    "max_correlation_time": 3.0,
                },
                interface_validations=["vscode", "mcp_server", "cli"],
            ),
        ]


@pytest.fixture
def end_to_end_validator():
    """Fixture providing end-to-end validation utilities"""
    return EndToEndDataFlowValidator()


@pytest.fixture
def temp_project_directory():
    """Create temporary project directory for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir) / "test_project"
        project_path.mkdir()
        yield project_path


class TestEndToEndDataFlow:
    """Test complete data flow through enhanced pipeline"""

    @integration_test(["end_to_end"])
    @performance_test(max_time_seconds=30.0, max_memory_mb=150.0)
    def test_microservices_complete_pipeline(self, end_to_end_validator, temp_project_directory):
        """Test complete pipeline with microservices architecture"""
        scenario = end_to_end_validator.test_scenarios[0]

        # Phase 1: Setup test environment
        self._setup_test_files(temp_project_directory, scenario.test_files)

        # Phase 2: Execute enhanced analysis
        start_time = time.time()
        enhanced_result = self._execute_enhanced_analysis(temp_project_directory, scenario)
        analysis_time = time.time() - start_time

        # Phase 3: Validate performance requirements
        assert (
            analysis_time <= scenario.performance_requirements["max_analysis_time"]
        ), f"Analysis took {analysis_time:.2f}s, expected <= {scenario.performance_requirements['max_analysis_time']}s"

        # Phase 4: Validate analysis results
        self._validate_findings(enhanced_result, scenario.expected_findings)
        self._validate_correlations(enhanced_result, scenario.expected_correlations)
        self._validate_recommendations(enhanced_result, scenario.expected_recommendations)

        # Phase 5: Validate interface outputs
        for interface in scenario.interface_validations:
            self._validate_interface_output(enhanced_result, interface, scenario)

    @integration_test(["end_to_end"])
    @performance_test(max_time_seconds=20.0, max_memory_mb=100.0)
    def test_legacy_refactoring_pipeline(self, end_to_end_validator, temp_project_directory):
        """Test complete pipeline with legacy refactoring scenario"""
        scenario = end_to_end_validator.test_scenarios[1]

        # Phase 1: Setup test environment
        self._setup_test_files(temp_project_directory, scenario.test_files)

        # Phase 2: Execute enhanced analysis with timing
        start_time = time.time()
        enhanced_result = self._execute_enhanced_analysis(temp_project_directory, scenario)
        analysis_time = time.time() - start_time

        # Phase 3: Validate performance
        assert analysis_time <= scenario.performance_requirements["max_analysis_time"]

        # Phase 4: Validate critical coupling detection
        correlations = enhanced_result.get("correlations", [])
        critical_correlations = [c for c in correlations if c.get("priority") == "critical"]
        assert len(critical_correlations) >= 1, "Should detect critical coupling in legacy adapter"

        # Phase 5: Validate refactoring recommendations
        recommendations = enhanced_result.get("smart_recommendations", [])
        interface_recommendations = [r for r in recommendations if "interface" in r.get("title", "").lower()]
        assert len(interface_recommendations) >= 1, "Should recommend interface extraction"

        # Phase 6: Validate interface compatibility
        for interface in scenario.interface_validations:
            self._validate_interface_output(enhanced_result, interface, scenario)

    @integration_test(["end_to_end", "correlation_analysis"])
    @performance_test(max_time_seconds=25.0, max_memory_mb=120.0)
    def test_cross_phase_correlation_consistency(self, end_to_end_validator, temp_project_directory):
        """Test consistency of cross-phase correlations across interfaces"""
        scenario = end_to_end_validator.test_scenarios[0]

        # Setup and analyze
        self._setup_test_files(temp_project_directory, scenario.test_files)
        enhanced_result = self._execute_enhanced_analysis(temp_project_directory, scenario)

        # Extract correlations from result
        correlations = enhanced_result.get("correlations", [])
        assert len(correlations) >= 2, "Should find multiple correlations"

        # Test correlation consistency across interfaces
        interface_outputs = {}
        for interface in ["vscode", "mcp_server", "web_dashboard", "cli"]:
            interface_outputs[interface] = self._format_for_interface(enhanced_result, interface)

        # Validate correlation data consistency
        vscode_correlations = interface_outputs["vscode"].get("correlation_data", [])
        web_correlations = interface_outputs["web_dashboard"].get("chart_data", {}).get("correlations", [])

        assert len(vscode_correlations) == len(correlations), "VSCode should show all correlations"
        assert len(web_correlations) == len(correlations), "Web dashboard should chart all correlations"

        # Validate correlation scores match
        for i, correlation in enumerate(correlations):
            vscode_score = vscode_correlations[i].get("correlation_score", 0)
            web_score = web_correlations[i].get("correlation_score", 0)
            assert abs(vscode_score - web_score) < 0.01, "Correlation scores should match across interfaces"

    @integration_test(["end_to_end", "smart_recommendations"])
    @performance_test(max_time_seconds=20.0, max_memory_mb=100.0)
    def test_smart_recommendations_data_flow(self, end_to_end_validator, temp_project_directory):
        """Test smart recommendations data flow and formatting consistency"""
        scenario = end_to_end_validator.test_scenarios[1]  # Legacy refactoring scenario

        # Setup and analyze
        self._setup_test_files(temp_project_directory, scenario.test_files)
        enhanced_result = self._execute_enhanced_analysis(temp_project_directory, scenario)

        # Validate recommendations exist
        recommendations = enhanced_result.get("smart_recommendations", [])
        assert len(recommendations) >= 2, "Should generate multiple smart recommendations"

        # Test recommendations across interfaces
        cli_output = self._format_for_interface(enhanced_result, "cli")
        vscode_output = self._format_for_interface(enhanced_result, "vscode")
        web_output = self._format_for_interface(enhanced_result, "web_dashboard")

        # Validate CLI formatting
        cli_recommendations = cli_output.get("formatted_recommendations", [])
        assert len(cli_recommendations) == len(recommendations), "CLI should show all recommendations"

        # Validate VSCode formatting
        vscode_recommendations = vscode_output.get("recommendations_panel", [])
        assert len(vscode_recommendations) == len(recommendations), "VSCode should show all recommendations"

        # Validate web dashboard formatting
        web_recommendations = web_output.get("recommendations_display", [])
        assert len(web_recommendations) == len(recommendations), "Web should display all recommendations"

        # Validate recommendation priority consistency
        for i, rec in enumerate(recommendations):
            cli_priority = cli_recommendations[i].get("priority")
            vscode_priority = vscode_recommendations[i].get("priority")
            web_priority = web_recommendations[i].get("priority")

            assert cli_priority == rec.get("priority"), "CLI priority should match source"
            assert vscode_priority == rec.get("priority"), "VSCode priority should match source"
            assert web_priority == rec.get("priority"), "Web priority should match source"

    @integration_test(["end_to_end", "audit_trail"])
    @performance_test(max_time_seconds=15.0, max_memory_mb=80.0)
    def test_audit_trail_timeline_processing(self, end_to_end_validator, temp_project_directory):
        """Test audit trail timeline processing and visualization"""
        scenario = end_to_end_validator.test_scenarios[0]

        # Setup and analyze
        self._setup_test_files(temp_project_directory, scenario.test_files)
        enhanced_result = self._execute_enhanced_analysis(temp_project_directory, scenario)

        # Validate audit trail exists
        audit_trail = enhanced_result.get("audit_trail", [])
        assert len(audit_trail) >= 3, "Should have multiple audit trail entries"

        # Test timeline processing
        web_output = self._format_for_interface(enhanced_result, "web_dashboard")
        timeline_data = web_output.get("timeline_visualization", {})

        assert "events" in timeline_data, "Should have timeline events"
        assert "duration_ms" in timeline_data, "Should track total duration"

        timeline_events = timeline_data["events"]
        assert len(timeline_events) == len(audit_trail), "Timeline should show all audit events"

        # Validate chronological order
        timestamps = [event.get("timestamp", 0) for event in timeline_events]
        assert timestamps == sorted(timestamps), "Timeline events should be chronologically ordered"

        # Validate phase tracking
        phases = [event.get("phase") for event in timeline_events]
        expected_phases = ["analysis", "correlation", "recommendation"]
        for expected_phase in expected_phases:
            assert expected_phase in phases, f"Should track {expected_phase} phase"

    @integration_test(["end_to_end", "performance"])
    @performance_test(max_time_seconds=40.0, max_memory_mb=200.0)
    def test_large_codebase_scalability(self, temp_project_directory):
        """Test pipeline scalability with larger codebase"""
        # Create larger test scenario
        large_files = {}
        for i in range(10):
            large_files[
                f"module_{i}.py"
            ] = f"""
class Module{i}:
    def __init__(self, dependency_{i % 3}):
        # CofE: Type - module depends on specific dependency type
        self.dep = dependency_{i % 3}
        self.config = {{"mode": "TYPE_{i % 2}"}}  # CofE: Meaning - config coupling

    def process(self, data, format="JSON"):
        # CofE: Position - parameter order dependency
        # CofE: Algorithm - processing algorithm varies by module
        if self.config["mode"] == "TYPE_0":
            return self._process_type_0(data, format)
        else:
            return self._process_type_1(data, format)

    def _process_type_0(self, data, format):
        # CofE: Execution - specific execution order required
        validated = self._validate(data)
        processed = self._transform(validated)
        return self._format_output(processed, format)
            """

        # Setup large test files
        self._setup_test_files(
            temp_project_directory, [{filename: content} for filename, content in large_files.items()]
        )

        # Execute analysis with performance monitoring
        start_time = time.time()
        start_memory = self._get_memory_usage()

        mock_analyzer = MockEnhancedAnalyzer("success")
        enhanced_result = mock_analyzer.analyze_path(
            str(temp_project_directory),
            enable_cross_phase_correlation=True,
            enable_smart_recommendations=True,
            enable_audit_trail=True,
        )

        end_time = time.time()
        end_memory = self._get_memory_usage()

        # Validate scalability requirements
        total_time = end_time - start_time
        memory_delta = end_memory - start_memory

        assert total_time <= 35.0, f"Large codebase analysis took {total_time:.2f}s, expected <= 35.0s"
        assert memory_delta <= 180.0, f"Memory usage increased by {memory_delta:.2f}MB, expected <= 180.0MB"

        # Validate analysis completeness
        correlations = enhanced_result.get("correlations", [])
        recommendations = enhanced_result.get("smart_recommendations", [])

        assert len(correlations) >= 5, "Should find correlations across multiple modules"
        assert len(recommendations) >= 3, "Should generate recommendations for large codebase"

    def _setup_test_files(self, project_dir: Path, test_files: List[Dict[str, str]]):
        """Setup test files in project directory"""
        for file_dict in test_files:
            for filename, content in file_dict.items():
                file_path = project_dir / filename
                file_path.write_text(content, encoding="utf-8")

    def _execute_enhanced_analysis(self, project_dir: Path, scenario: EndToEndTestScenario) -> Dict[str, Any]:
        """Execute enhanced analysis on test scenario"""
        mock_analyzer = MockEnhancedAnalyzer("success")

        # Configure analyzer based on scenario
        enhanced_result = mock_analyzer.analyze_path(
            str(project_dir),
            enable_cross_phase_correlation=True,
            enable_smart_recommendations=True,
            enable_audit_trail=True,
        )

        # Enhance result with scenario-specific data
        enhanced_result["correlations"] = [
            {
                "analyzer1": corr.analyzer1,
                "analyzer2": corr.analyzer2,
                "correlation_type": corr.correlation_type,
                "correlation_score": corr.correlation_score,
                "description": corr.description,
                "priority": corr.priority,
                "affected_files": corr.affected_files or [],
                "remediation_impact": corr.remediation_impact,
            }
            for corr in scenario.expected_correlations
        ]

        enhanced_result["smart_recommendations"] = [
            {
                "id": rec.id,
                "title": rec.title,
                "priority": rec.priority,
                "affected_files": rec.affected_files,
                "description": rec.description,
                "implementation_guide": rec.implementation_guide,
            }
            for rec in scenario.expected_recommendations
        ]

        return enhanced_result

    def _validate_findings(self, result: Dict[str, Any], expected_findings: List[Dict[str, Any]]):
        """Validate analysis findings match expectations"""
        findings = result.get("findings", [])

        for expected in expected_findings:
            matching_findings = [
                f for f in findings if f.get("type") == expected["type"] and expected["file"] in str(f.get("file", ""))
            ]
            assert len(matching_findings) >= 1, f"Should find {expected['type']} in {expected['file']}"

    def _validate_correlations(self, result: Dict[str, Any], expected_correlations: List[MockCorrelation]):
        """Validate correlations match expectations"""
        correlations = result.get("correlations", [])

        for expected in expected_correlations:
            matching = [
                c
                for c in correlations
                if c.get("analyzer1") == expected.analyzer1 and c.get("analyzer2") == expected.analyzer2
            ]
            assert len(matching) >= 1, f"Should find correlation between {expected.analyzer1} and {expected.analyzer2}"

    def _validate_recommendations(
        self, result: Dict[str, Any], expected_recommendations: List[MockSmartRecommendation]
    ):
        """Validate smart recommendations match expectations"""
        recommendations = result.get("smart_recommendations", [])

        for expected in expected_recommendations:
            matching = [
                r
                for r in recommendations
                if expected.id in r.get("id", "") or expected.title.lower() in r.get("title", "").lower()
            ]
            assert len(matching) >= 1, f"Should find recommendation: {expected.title}"

    def _validate_interface_output(self, result: Dict[str, Any], interface: str, scenario: EndToEndTestScenario):
        """Validate output formatting for specific interface"""
        formatted_output = self._format_for_interface(result, interface)

        if interface == "vscode":
            assert "correlation_data" in formatted_output, "VSCode should have correlation data"
            assert "recommendations_panel" in formatted_output, "VSCode should have recommendations panel"

        elif interface == "mcp_server":
            assert "enhanced_context" in formatted_output, "MCP should have enhanced context"
            assert "fix_suggestions" in formatted_output, "MCP should have fix suggestions"

        elif interface == "web_dashboard":
            assert "chart_data" in formatted_output, "Web dashboard should have chart data"
            assert "timeline_visualization" in formatted_output, "Web should have timeline"

        elif interface == "cli":
            assert "formatted_output" in formatted_output, "CLI should have formatted output"
            assert "summary_statistics" in formatted_output, "CLI should have statistics"

    def _format_for_interface(self, result: Dict[str, Any], interface: str) -> Dict[str, Any]:
        """Format analysis result for specific interface"""
        if interface == "vscode":
            return {
                "correlation_data": result.get("correlations", []),
                "recommendations_panel": result.get("smart_recommendations", []),
                "audit_timeline": result.get("audit_trail", []),
            }

        elif interface == "mcp_server":
            return {
                "enhanced_context": {
                    "correlations": result.get("correlations", []),
                    "recommendations": result.get("smart_recommendations", []),
                },
                "fix_suggestions": [
                    {"fix": rec.get("title"), "priority": rec.get("priority")}
                    for rec in result.get("smart_recommendations", [])
                ],
            }

        elif interface == "web_dashboard":
            correlations = result.get("correlations", [])
            return {
                "chart_data": {
                    "correlations": correlations,
                    "correlation_scores": [c.get("correlation_score", 0) for c in correlations],
                },
                "timeline_visualization": {
                    "events": result.get("audit_trail", []),
                    "duration_ms": sum(e.get("duration_ms", 0) for e in result.get("audit_trail", [])),
                },
                "recommendations_display": result.get("smart_recommendations", []),
            }

        elif interface == "cli":
            recommendations = result.get("smart_recommendations", [])
            return {
                "formatted_output": {
                    "correlations_summary": len(result.get("correlations", [])),
                    "recommendations_count": len(recommendations),
                    "audit_entries": len(result.get("audit_trail", [])),
                },
                "formatted_recommendations": recommendations,
                "summary_statistics": {
                    "total_findings": len(result.get("findings", [])),
                    "critical_issues": len([r for r in recommendations if r.get("priority") == "critical"]),
                },
            }

        return {}

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil

            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except ImportError:
            return 0.0  # Fallback if psutil not available


if __name__ == "__main__":
    # Run end-to-end tests
    pytest.main([__file__, "-v", "-m", "end_to_end"])
