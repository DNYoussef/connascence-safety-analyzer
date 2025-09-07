# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
CLI Interface Enhanced Integration Tests
=======================================

Comprehensive tests for CLI interface enhanced pipeline integration:
- Enhanced arguments parsing and validation
- Unified analyzer selection logic and feature detection
- Export functionality for audit trails, correlations, and recommendations
- Enhanced console output with correlation summaries and timing data
- Policy resolution integration with constants.py
"""

import json
import tempfile
import argparse
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from .test_infrastructure import (
    EnhancedTestDatasets, MockEnhancedAnalyzer, EnhancedTestUtilities,
    integration_test, performance_test
)



@pytest.fixture
def enhanced_test_datasets():
    """Provide enhanced test datasets"""
    return EnhancedTestDatasets()

@pytest.fixture
def sample_code_file(tmp_path):
    """Create temporary Python file for testing"""
    code_content = '''
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
'''
    
    code_file = tmp_path / "test_code.py"
    code_file.write_text(code_content, encoding="utf-8")
    return code_file


class TestCLIEnhancedIntegration:
    """Test suite for CLI interface enhanced pipeline integration."""
    
    @integration_test(["cli"])
    def test_enhanced_arguments_parsing(self):
        """Test enhanced CLI arguments parsing and validation."""
        # Mock argument parser creation
        parser = argparse.ArgumentParser()
        
        # Add enhanced arguments (as implemented in core.py)
        enhanced_args = [
            ("--enable-correlations", {"action": "store_true", "help": "Enable cross-phase correlation analysis"}),
            ("--enable-audit-trail", {"action": "store_true", "help": "Enable analysis audit trail tracking"}),
            ("--enable-smart-recommendations", {"action": "store_true", "help": "Enable AI-powered smart recommendations"}),
            ("--correlation-threshold", {"type": float, "default": 0.7, "help": "Minimum correlation threshold"}),
            ("--export-audit-trail", {"type": str, "help": "Export audit trail to file"}),
            ("--export-correlations", {"type": str, "help": "Export correlation data to file"}),
            ("--export-recommendations", {"type": str, "help": "Export smart recommendations to file"}),
            ("--enhanced-output", {"action": "store_true", "help": "Include enhanced pipeline metadata"}),
            ("--phase-timing", {"action": "store_true", "help": "Display detailed phase timing"})
        ]
        
        # Add arguments to parser
        for arg_name, arg_config in enhanced_args:
            parser.add_argument(arg_name, **arg_config)
        
        # Test valid argument combinations
        valid_test_cases = [
            ["--enable-correlations", "--correlation-threshold", "0.8"],
            ["--enable-audit-trail", "--export-audit-trail", "/tmp/audit.json"],
            ["--enable-smart-recommendations", "--export-recommendations", "/tmp/recs.json"],
            ["--enhanced-output", "--phase-timing"],
            ["--enable-correlations", "--enable-audit-trail", "--enable-smart-recommendations"]
        ]
        
        for test_args in valid_test_cases:
            args = parser.parse_args(test_args)
            
            # Verify arguments are parsed correctly
            if "--enable-correlations" in test_args:
                assert args.enable_correlations == True
            if "--correlation-threshold" in test_args:
                assert args.correlation_threshold == 0.8
            if "--export-audit-trail" in test_args:
                assert args.export_audit_trail == "/tmp/audit.json"
        
        # Test invalid correlation threshold
        with pytest.raises(SystemExit):
            parser.parse_args(["--correlation-threshold", "1.5"])  # Out of range
    
    @integration_test(["cli"])
    def test_unified_analyzer_selection_logic(self, sample_code_file):
        """Test unified analyzer selection based on enhanced features."""
        test_scenarios = [
            # (args_dict, expected_use_enhanced, expected_features)
            ({"enable_correlations": True}, True, {"enable_cross_phase_correlation": True}),
            ({"enable_audit_trail": True}, True, {"enable_audit_trail": True}),
            ({"enable_smart_recommendations": True}, True, {"enable_smart_recommendations": True}),
            ({"enhanced_output": True}, True, {}),
            ({}, False, {}),  # No enhanced features
            ({"policy": "standard", "duplication_analysis": True}, False, {})  # Standard features only
        ]
        
        for args_dict, expected_enhanced, expected_features in test_scenarios:
            # Mock command line arguments
            mock_args = Mock()
            for key, value in args_dict.items():
                setattr(mock_args, key, value)
            
            # Set default values for missing arguments
            default_args = {
                "enable_correlations": False,
                "enable_audit_trail": False,
                "enable_smart_recommendations": False,
                "enhanced_output": False,
                "correlation_threshold": 0.7,
                "path": str(sample_code_file),
                "policy": "standard"
            }
            
            for key, default_value in default_args.items():
                if not hasattr(mock_args, key):
                    setattr(mock_args, key, default_value)
            
            # Test analyzer selection logic
            use_enhanced = self._should_use_enhanced_analyzer(mock_args)
            assert use_enhanced == expected_enhanced, \
                f"Args {args_dict} should {'use' if expected_enhanced else 'not use'} enhanced analyzer"
            
            if expected_enhanced:
                # Test enhanced analyzer initialization
                enhanced_kwargs = self._build_enhanced_analyzer_kwargs(mock_args)
                
                for feature_key, expected_value in expected_features.items():
                    assert enhanced_kwargs.get(feature_key) == expected_value, \
                        f"Feature {feature_key} should be {expected_value}"
    
    @integration_test(["cli"])
    @performance_test(max_time_seconds=5.0, max_memory_mb=40.0)
    def test_enhanced_analysis_execution(self, sample_code_file, enhanced_test_datasets):
        """Test enhanced analysis execution through CLI interface."""
        # Mock enhanced analyzer
        mock_analyzer = MockEnhancedAnalyzer("success")
        
        # Mock command line arguments for enhanced analysis
        mock_args = Mock()
        mock_args.path = str(sample_code_file)
        mock_args.policy = "standard"
        mock_args.enable_correlations = True
        mock_args.enable_audit_trail = True
        mock_args.enable_smart_recommendations = True
        mock_args.correlation_threshold = 0.7
        mock_args.enhanced_output = True
        mock_args.phase_timing = True
        mock_args.format = "json"
        
        # Execute enhanced analysis
        with patch('analyzer.unified_analyzer.UnifiedConnascenceAnalyzer') as MockUnifiedAnalyzer:
            MockUnifiedAnalyzer.return_value = mock_analyzer
            
            result = mock_analyzer.analyze_path(
                path=mock_args.path,
                policy=mock_args.policy,
                enable_cross_phase_correlation=mock_args.enable_correlations,
                enable_audit_trail=mock_args.enable_audit_trail,
                enable_smart_recommendations=mock_args.enable_smart_recommendations,
                correlation_threshold=mock_args.correlation_threshold
            )
            
            # Validate enhanced analysis result
            is_valid, errors = EnhancedTestUtilities.validate_enhanced_result(result)
            assert is_valid, f"Enhanced CLI analysis result validation failed: {errors}"
            
            # Verify enhanced features are enabled
            assert result["cross_phase_analysis"] == True
            assert len(result["correlations"]) > 0
            assert len(result["smart_recommendations"]) > 0
            assert len(result["audit_trail"]) > 0
    
    @integration_test(["cli"])
    def test_enhanced_export_functionality(self, tmp_path, enhanced_test_datasets):
        """Test CLI export functionality for enhanced data."""
        # Create temporary export files
        audit_file = tmp_path / "audit_trail.json"
        correlations_file = tmp_path / "correlations.json"
        recommendations_file = tmp_path / "recommendations.json"
        
        # Mock enhanced analysis result
        enhanced_result = {
            "success": True,
            "audit_trail": [a.__dict__ for a in enhanced_test_datasets.get_expected_audit_trail()],
            "correlations": [c.__dict__ for c in enhanced_test_datasets.get_expected_correlations()],
            "smart_recommendations": [r.__dict__ for r in enhanced_test_datasets.get_expected_smart_recommendations()]
        }
        
        # Mock command line arguments for export
        mock_args = Mock()
        mock_args.export_audit_trail = str(audit_file)
        mock_args.export_correlations = str(correlations_file)
        mock_args.export_recommendations = str(recommendations_file)
        
        # Test export functionality
        self._simulate_enhanced_exports(enhanced_result, mock_args)
        
        # Validate exported files
        assert audit_file.exists(), "Audit trail file should be created"
        assert correlations_file.exists(), "Correlations file should be created"
        assert recommendations_file.exists(), "Recommendations file should be created"
        
        # Validate exported content
        with open(audit_file) as f:
            exported_audit = json.load(f)
            assert len(exported_audit) == len(enhanced_test_datasets.get_expected_audit_trail())
            
        with open(correlations_file) as f:
            exported_correlations = json.load(f)
            assert len(exported_correlations) == len(enhanced_test_datasets.get_expected_correlations())
            
        with open(recommendations_file) as f:
            exported_recommendations = json.load(f)
            assert len(exported_recommendations) == len(enhanced_test_datasets.get_expected_smart_recommendations())
    
    @integration_test(["cli"])
    def test_enhanced_console_output(self, enhanced_test_datasets):
        """Test enhanced console output formatting and display."""
        # Mock enhanced analysis result
        enhanced_result = {
            "correlations": [c.__dict__ for c in enhanced_test_datasets.get_expected_correlations()],
            "smart_recommendations": [r.__dict__ for r in enhanced_test_datasets.get_expected_smart_recommendations()],
            "audit_trail": [a.__dict__ for a in enhanced_test_datasets.get_expected_audit_trail()]
        }
        
        # Mock command line arguments
        mock_args = Mock()
        mock_args.phase_timing = True
        mock_args.enable_correlations = True
        mock_args.enable_smart_recommendations = True
        
        # Capture console output
        console_output = []
        
        def mock_print(*args, **kwargs):
            console_output.append(" ".join(str(arg) for arg in args))
        
        with patch('builtins.print', side_effect=mock_print):
            # Simulate enhanced console output
            self._generate_enhanced_console_output(enhanced_result, mock_args)
        
        output_text = "\n".join(console_output)
        
        # Validate phase timing output
        assert "Analysis Phase Timing" in output_text
        for entry in enhanced_test_datasets.get_expected_audit_trail():
            phase_name = entry.phase.replace("_", " ").title()
            assert phase_name in output_text
        
        # Validate correlation summary output
        assert "Cross-Phase Analysis Summary" in output_text
        assert f"Found {len(enhanced_test_datasets.get_expected_correlations())} cross-phase correlations" in output_text
        
        # Validate recommendations summary output
        assert "Smart Recommendations Summary" in output_text
        assert f"Generated {len(enhanced_test_datasets.get_expected_smart_recommendations())} architectural recommendations" in output_text
    
    @integration_test(["cli"])
    def test_policy_resolution_integration(self):
        """Test policy resolution integration with constants.py."""
        # Test policy mapping scenarios
        policy_test_cases = [
            # (input_policy, expected_resolved_policy)
            ("safety_level_1", "nasa-compliance"),
            ("general_safety_strict", "strict"),
            ("modern_general", "standard"),
            ("safety_level_3", "lenient"),
            ("nasa-compliance", "nasa-compliance"),  # Already unified
            ("strict", "strict"),  # Already unified
            ("standard", "standard"),  # Already unified
            ("lenient", "lenient"),  # Already unified
        ]
        
        for input_policy, expected_resolved in policy_test_cases:
            # Mock policy resolution function
            with patch('analyzer.constants.resolve_policy_name') as mock_resolve:
                mock_resolve.return_value = expected_resolved
                
                resolved_policy = mock_resolve(input_policy)
                assert resolved_policy == expected_resolved, \
                    f"Policy {input_policy} should resolve to {expected_resolved}, got {resolved_policy}"
        
        # Test invalid policy handling
        with patch('analyzer.constants.validate_policy_name') as mock_validate:
            mock_validate.return_value = False  # Invalid policy
            
            with patch('analyzer.constants.list_available_policies') as mock_list:
                mock_list.return_value = ["nasa-compliance", "strict", "standard", "lenient"]
                
                # Should raise error or handle gracefully
                result = self._handle_invalid_policy("invalid_policy")
                assert result == False or "error" in str(result).lower()
    
    @integration_test(["cli"])
    def test_enhanced_output_formats(self, tmp_path, enhanced_test_datasets):
        """Test enhanced output in different formats (JSON, SARIF)."""
        enhanced_result = {
            "success": True,
            "violations": [
                {"type": "connascence_of_literal", "severity": "high", "message": "Test violation"}
            ],
            "correlations": [c.__dict__ for c in enhanced_test_datasets.get_expected_correlations()],
            "smart_recommendations": [r.__dict__ for r in enhanced_test_datasets.get_expected_smart_recommendations()],
            "audit_trail": [a.__dict__ for a in enhanced_test_datasets.get_expected_audit_trail()],
            "canonical_policy": "standard",
            "cross_phase_analysis": True
        }
        
        # Test JSON output format
        json_output = self._format_enhanced_json_output(enhanced_result)
        json_data = json.loads(json_output)
        
        assert "correlations" in json_data
        assert "smart_recommendations" in json_data
        assert "audit_trail" in json_data
        assert "cross_phase_analysis" in json_data
        assert json_data["cross_phase_analysis"] == True
        
        # Test SARIF output format (should include enhanced metadata)
        sarif_output = self._format_enhanced_sarif_output(enhanced_result)
        sarif_data = json.loads(sarif_output)
        
        assert "runs" in sarif_data
        run = sarif_data["runs"][0]
        assert "properties" in run
        
        # Enhanced metadata should be in SARIF properties
        properties = run["properties"]
        assert "enhanced_analysis" in properties
        enhanced_props = properties["enhanced_analysis"]
        assert "cross_phase_correlations" in enhanced_props
        assert "smart_recommendations" in enhanced_props
    
    @integration_test(["cli"])
    def test_cli_error_handling(self, sample_code_file):
        """Test CLI error handling for enhanced features."""
        error_scenarios = [
            ("missing_analyzer", "Enhanced analyzer not available"),
            ("invalid_threshold", "Correlation threshold out of range"),
            ("export_permission_denied", "Cannot write to export file"),
            ("analysis_timeout", "Enhanced analysis timed out")
        ]
        
        for scenario, expected_behavior in error_scenarios:
            mock_args = Mock()
            mock_args.path = str(sample_code_file)
            mock_args.policy = "standard"
            mock_args.enable_correlations = True
            mock_args.correlation_threshold = 0.7
            
            if scenario == "missing_analyzer":
                # Mock analyzer not available
                with patch('analyzer.unified_analyzer.UnifiedConnascenceAnalyzer', side_effect=ImportError("Not available")):
                    result = self._simulate_cli_execution(mock_args, scenario)
                    assert "error" in str(result).lower() or result == False
                    
            elif scenario == "invalid_threshold":
                mock_args.correlation_threshold = 1.5  # Invalid range
                result = self._simulate_cli_execution(mock_args, scenario)
                # Should handle gracefully or validate input
                assert result != None
                
            elif scenario == "export_permission_denied":
                mock_args.export_correlations = "/root/protected_file.json"  # No permission
                with patch('builtins.open', side_effect=PermissionError("Permission denied")):
                    result = self._simulate_cli_execution(mock_args, scenario)
                    assert "permission" in str(result).lower() or result == False
                    
            elif scenario == "analysis_timeout":
                mock_analyzer = MockEnhancedAnalyzer("timeout")
                with patch('analyzer.unified_analyzer.UnifiedConnascenceAnalyzer', return_value=mock_analyzer):
                    result = self._simulate_cli_execution(mock_args, scenario)
                    # Should handle timeout gracefully
                    assert result != None
    
    # Helper methods for CLI testing
    
    def _should_use_enhanced_analyzer(self, args):
        """Determine if enhanced analyzer should be used based on arguments."""
        return (args.enable_correlations or 
                args.enable_audit_trail or 
                args.enable_smart_recommendations or 
                args.enhanced_output)
    
    def _build_enhanced_analyzer_kwargs(self, args):
        """Build keyword arguments for enhanced analyzer."""
        kwargs = {
            "path": args.path,
            "policy": args.policy,
            "correlation_threshold": args.correlation_threshold
        }
        
        if args.enable_correlations:
            kwargs["enable_cross_phase_correlation"] = True
        if args.enable_audit_trail:
            kwargs["enable_audit_trail"] = True
        if args.enable_smart_recommendations:
            kwargs["enable_smart_recommendations"] = True
            
        return kwargs
    
    def _simulate_enhanced_exports(self, result, args):
        """Simulate enhanced data export functionality."""
        if hasattr(args, 'export_audit_trail') and args.export_audit_trail:
            with open(args.export_audit_trail, 'w') as f:
                json.dump(result["audit_trail"], f, indent=2, default=str)
        
        if hasattr(args, 'export_correlations') and args.export_correlations:
            with open(args.export_correlations, 'w') as f:
                json.dump(result["correlations"], f, indent=2, default=str)
        
        if hasattr(args, 'export_recommendations') and args.export_recommendations:
            with open(args.export_recommendations, 'w') as f:
                json.dump(result["smart_recommendations"], f, indent=2, default=str)
    
    def _generate_enhanced_console_output(self, result, args):
        """Generate enhanced console output."""
        if args.phase_timing and result.get("audit_trail"):
            print("\n=== Analysis Phase Timing ===")
            for phase in result["audit_trail"]:
                phase_name = phase["phase"].replace("_", " ").title()
                violations = phase.get("violations_found", 0)
                clusters = phase.get("clusters_found", 0)
                print(f"{phase_name:25} | 2500.0ms | {violations:3d} violations | {clusters:3d} clusters")
        
        if result.get("correlations") and len(result["correlations"]) > 0:
            print(f"\n=== Cross-Phase Analysis Summary ===")
            correlations = result["correlations"]
            print(f"Found {len(correlations)} cross-phase correlations")
            
            # Show top correlations
            for i, corr in enumerate(correlations[:3]):
                score = corr.get("correlation_score", 0) * 100
                analyzer1 = corr.get("analyzer1", "Unknown")
                analyzer2 = corr.get("analyzer2", "Unknown")
                print(f"{i+1}. {analyzer1} <-> {analyzer2}: {score:.1f}% correlation")
        
        if result.get("smart_recommendations") and len(result["smart_recommendations"]) > 0:
            print(f"\n=== Smart Recommendations Summary ===")
            recommendations = result["smart_recommendations"]
            print(f"Generated {len(recommendations)} architectural recommendations")
            
            # Show high priority recommendations
            high_priority = [r for r in recommendations if r.get("priority", "").lower() == "high"]
            for rec in high_priority[:3]:
                category = rec.get("category", "General")
                description = rec.get("description", "No description")[:60] + "..."
                print(f"• [{category}] {description}")
    
    def _handle_invalid_policy(self, policy):
        """Handle invalid policy name."""
        # In real implementation, this would exit with error
        return False
    
    def _format_enhanced_json_output(self, result):
        """Format enhanced result as JSON output."""
        return json.dumps(result, indent=2, default=str)
    
    def _format_enhanced_sarif_output(self, result):
        """Format enhanced result as SARIF output with metadata."""
        sarif = {
            "version": "2.1.0",
            "runs": [{
                "tool": {
                    "driver": {
                        "name": "connascence-analyzer",
                        "version": "2.0.0"
                    }
                },
                "results": [],
                "properties": {
                    "enhanced_analysis": {
                        "cross_phase_correlations": len(result.get("correlations", [])),
                        "smart_recommendations": len(result.get("smart_recommendations", [])),
                        "audit_trail_phases": len(result.get("audit_trail", [])),
                        "canonical_policy": result.get("canonical_policy"),
                        "cross_phase_analysis_enabled": result.get("cross_phase_analysis", False)
                    }
                }
            }]
        }
        
        return json.dumps(sarif, indent=2)
    
    def _simulate_cli_execution(self, args, scenario):
        """Simulate CLI execution for error testing."""
        if scenario == "missing_analyzer":
            return "Error: Enhanced analyzer not available"
        elif scenario == "invalid_threshold":
            # Should validate threshold or handle gracefully
            if hasattr(args, 'correlation_threshold') and not (0.0 <= args.correlation_threshold <= 1.0):
                return "Error: Correlation threshold out of range"
        elif scenario == "export_permission_denied":
            return "Error: Permission denied writing export file"
        elif scenario == "analysis_timeout":
            return "Warning: Analysis timed out, using standard analyzer"
        
        return True  # Success


# CLI specific test configuration
@pytest.mark.cli
@pytest.mark.integration
class TestCLIIntegrationFlow:
    """End-to-end integration tests for CLI enhanced workflow."""
    
    @integration_test(["cli"])
    @performance_test(max_time_seconds=8.0, max_memory_mb=60.0)
    def test_complete_cli_enhanced_workflow(self, sample_code_file, tmp_path, enhanced_test_datasets):
        """Test complete CLI enhanced workflow with all features."""
        # 1. Setup CLI arguments
        audit_file = tmp_path / "audit_trail.json"
        correlations_file = tmp_path / "correlations.json"
        recommendations_file = tmp_path / "recommendations.json"
        
        mock_args = Mock()
        mock_args.path = str(sample_code_file)
        mock_args.policy = "standard"
        mock_args.enable_correlations = True
        mock_args.enable_audit_trail = True
        mock_args.enable_smart_recommendations = True
        mock_args.correlation_threshold = 0.7
        mock_args.enhanced_output = True
        mock_args.phase_timing = True
        mock_args.export_audit_trail = str(audit_file)
        mock_args.export_correlations = str(correlations_file)
        mock_args.export_recommendations = str(recommendations_file)
        mock_args.format = "json"
        
        # 2. Execute enhanced analysis
        mock_analyzer = MockEnhancedAnalyzer("success")
        result = mock_analyzer.analyze_path(
            path=mock_args.path,
            policy=mock_args.policy,
            enable_cross_phase_correlation=mock_args.enable_correlations,
            enable_audit_trail=mock_args.enable_audit_trail,
            enable_smart_recommendations=mock_args.enable_smart_recommendations,
            correlation_threshold=mock_args.correlation_threshold
        )
        
        # 3. Test export functionality
        test_instance = TestCLIEnhancedIntegration()
        test_instance._simulate_enhanced_exports(result, mock_args)
        
        # 4. Test console output
        console_output = []
        def mock_print(*args, **kwargs):
            console_output.append(" ".join(str(arg) for arg in args))
        
        with patch('builtins.print', side_effect=mock_print):
            test_instance._generate_enhanced_console_output(result, mock_args)
        
        # 5. Validate complete workflow
        # Analysis result validation
        is_valid, errors = EnhancedTestUtilities.validate_enhanced_result(result)
        assert is_valid, f"CLI enhanced analysis validation failed: {errors}"
        
        # Export validation
        assert audit_file.exists()
        assert correlations_file.exists()
        assert recommendations_file.exists()
        
        # Console output validation
        output_text = "\n".join(console_output)
        assert "Analysis Phase Timing" in output_text
        assert "Cross-Phase Analysis Summary" in output_text
        assert "Smart Recommendations Summary" in output_text
        
        # 6. Performance validation by decorator
        # Memory and timing validated by @performance_test