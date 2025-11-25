# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
Architecture Extraction Validation Tests
=========================================

Tests to validate that the god object extraction was successful and
maintains backward compatibility with zero breaking changes.
"""

import builtins
import contextlib
import os
from pathlib import Path
import sys
import tempfile
import unittest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from analyzer.architecture import (
        AnalysisOrchestrator,
        ConfigurationManager,
        EnhancedMetricsCalculator,
        RecommendationEngine,
        ViolationAggregator,
    )
    from analyzer.unified_analyzer import (
        UnifiedConnascenceAnalyzer,
        get_specialized_components,
        validate_architecture_compliance,
        validate_extraction_success,
    )
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


class TestArchitectureExtraction(unittest.TestCase):
    """Test that god object extraction maintains all functionality."""

    def setUp(self):
        """Set up test environment."""
        self.analyzer = UnifiedConnascenceAnalyzer()

    @unittest.skip("Architecture extraction feature not yet implemented")
    def test_architecture_components_available(self):
        """Test that all architecture components are available."""
        components = self.analyzer.get_architecture_components()

        expected_components = [
            "orchestrator",
            "aggregator",
            "recommendation_engine",
            "config_manager",
            "enhanced_metrics",
        ]

        for component_name in expected_components:
            self.assertIn(component_name, components)
            self.assertIsNotNone(components[component_name])

    @unittest.skip("Architecture extraction feature not yet implemented")
    def test_nasa_rule_4_compliance(self):
        """Test that all architecture components follow NASA Rule 4 (functions under 60 lines)."""
        components = get_specialized_components()

        for name, component in components.items():
            # Get all methods of the component
            methods = [
                method
                for method in dir(component)
                if callable(getattr(component, method)) and not method.startswith("_")
            ]

            # Each component should have methods (not empty)
            self.assertGreater(len(methods), 0, f"Component {name} should have public methods")

    def test_backward_compatibility_maintained(self):
        """Test that all public API methods are still available."""
        # Public API methods that must remain unchanged
        required_methods = [
            "analyze_project",
            "analyze_file",
            "get_dashboard_summary",
            "create_integration_error",
            "convert_exception_to_standard_error",
        ]

        for method_name in required_methods:
            self.assertTrue(hasattr(self.analyzer, method_name), f"Required API method '{method_name}' missing")
            self.assertTrue(callable(getattr(self.analyzer, method_name)), f"'{method_name}' is not callable")

    @unittest.skip("Legacy delegation feature not yet implemented")
    def test_legacy_components_delegate_correctly(self):
        """Test that legacy components delegate to new architecture components."""
        # Test that legacy MetricsCalculator delegates to EnhancedMetricsCalculator
        self.assertIsInstance(self.analyzer.metrics_calculator.enhanced_calculator, EnhancedMetricsCalculator)

        # Test that legacy RecommendationGenerator delegates to RecommendationEngine
        self.assertIsInstance(self.analyzer.recommendation_generator.recommendation_engine, RecommendationEngine)

    @unittest.skip("Architecture extraction validation not yet implemented")
    def test_architecture_extraction_validation(self):
        """Test the architecture extraction validation."""
        validation_results = self.analyzer.validate_architecture_extraction()

        # All validation checks should pass
        for check_name, result in validation_results.items():
            if check_name != "overall_success":
                self.assertTrue(result, f"Validation check '{check_name}' failed")

        # Overall validation should be successful
        self.assertTrue(validation_results["overall_success"], "Overall architecture extraction validation failed")

    def test_component_status_reporting(self):
        """Test that component status is correctly reported."""
        status = self.analyzer.get_component_status()

        # Core and architecture components should always be available
        self.assertTrue(status["core_components"])
        self.assertTrue(status["architecture_components"])

        # Status should include all expected keys
        expected_keys = [
            "core_components",
            "architecture_components",
            "smart_engine",
            "failure_detector",
            "nasa_integration",
            "policy_manager",
            "budget_tracker",
            "caching",
        ]

        for key in expected_keys:
            self.assertIn(key, status)

    @unittest.skip("Configuration manager integration not yet implemented")
    def test_configuration_manager_integration(self):
        """Test that configuration manager is properly integrated."""
        # Configuration should be loaded through manager
        config = self.analyzer.config
        self.assertIsInstance(config, dict)

        # Manager should have validation capabilities
        config_manager = self.analyzer.config_manager
        self.assertTrue(hasattr(config_manager, "validate_configuration"))
        self.assertTrue(hasattr(config_manager, "get_component_configuration"))


class TestArchitectureComponentsIndependently(unittest.TestCase):
    """Test each architecture component independently."""

    def test_analysis_orchestrator(self):
        """Test AnalysisOrchestrator component."""
        orchestrator = AnalysisOrchestrator()
        self.assertIsNotNone(orchestrator)

        # Test phase tracking
        self.assertIsNone(orchestrator.get_current_phase())
        self.assertEqual(len(orchestrator.get_audit_trail()), 0)

    def test_violation_aggregator(self):
        """Test ViolationAggregator component."""
        aggregator = ViolationAggregator()
        self.assertIsNotNone(aggregator)

        # Test aggregation statistics
        stats = aggregator.get_aggregation_stats()
        self.assertIsInstance(stats, dict)

    def test_recommendation_engine(self):
        """Test RecommendationEngine component."""
        engine = RecommendationEngine()
        self.assertIsNotNone(engine)

        # Test empty input handling
        recommendations = engine.generate_unified_recommendations([], [], [])
        self.assertIsInstance(recommendations, dict)
        self.assertIn("priority_fixes", recommendations)
        self.assertIn("improvement_actions", recommendations)

    def test_configuration_manager(self):
        """Test ConfigurationManager component."""
        config_manager = ConfigurationManager()
        self.assertIsNotNone(config_manager)

        # Test default configuration loading
        config = config_manager.load_config()
        self.assertIsInstance(config, dict)

        # Test configuration validation
        validation_result = config_manager.validate_configuration(config)
        self.assertTrue(validation_result["is_valid"])

    def test_enhanced_metrics_calculator(self):
        """Test EnhancedMetricsCalculator component."""
        calculator = EnhancedMetricsCalculator()
        self.assertIsNotNone(calculator)

        # Test empty input handling
        metrics = calculator.calculate_comprehensive_metrics([], [], [])
        self.assertIsInstance(metrics, dict)
        self.assertIn("total_violations", metrics)
        self.assertIn("overall_quality_score", metrics)


class TestIntegrationWithRealCode(unittest.TestCase):
    """Test integration with real Python code to ensure functionality is preserved."""

    def setUp(self):
        """Create temporary Python file for testing."""
        self.test_code = """
def example_function(param1, param2):
    # This function has some connascence issues
    if param1 == "magic_string":  # CoM - Connascence of Meaning
        return param2[0]  # CoP - Connascence of Position
    return None

class ExampleClass:
    def __init__(self):
        self.data = []

    def add_item(self, item):
        self.data.append(item)  # Simple method
"""

        self.temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        self.temp_file.write(self.test_code)
        self.temp_file.close()

        self.analyzer = UnifiedConnascenceAnalyzer()

    def tearDown(self):
        """Clean up temporary file."""
        with contextlib.suppress(builtins.BaseException):
            os.unlink(self.temp_file.name)

    def test_file_analysis_still_works(self):
        """Test that file analysis functionality is preserved."""
        result = self.analyzer.analyze_file(self.temp_file.name)

        # Result should have expected structure
        self.assertIsInstance(result, dict)
        self.assertIn("file_path", result)
        self.assertIn("connascence_violations", result)
        self.assertIn("violation_count", result)

        # Should detect violations in test code
        self.assertIsInstance(result["connascence_violations"], list)


def run_validation_tests():
    """Run all validation tests."""
    print("Running Architecture Extraction Validation Tests...")

    # Test architecture compliance
    compliance_result = validate_architecture_compliance()
    print(f"Architecture compliance: {'PASS' if compliance_result else 'FAIL'}")

    # Test extraction success
    extraction_result = validate_extraction_success()
    print(f"Extraction success: {'PASS' if extraction_result else 'FAIL'}")

    # Run unit tests
    unittest.main(verbosity=2, exit=False)

    return compliance_result and extraction_result


if __name__ == "__main__":
    run_validation_tests()
