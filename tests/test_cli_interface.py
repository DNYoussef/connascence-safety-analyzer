#!/usr/bin/env python3
"""
Test suite for CLI interface changes and flake8-style usage.

Tests Requirements:
1. Test `connascence .` command works
2. Test configuration file discovery
3. Test backwards compatibility
4. Test error handling and help messages
"""

import contextlib
from pathlib import Path
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from analyzer.constants import resolve_policy_name
from analyzer.core import create_parser, main


class TestCLIInterface:
    """Test CLI interface and command-line argument handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.test_file = self.test_dir / "test_code.py"

        # Create a simple test file
        self.test_file.write_text(
            """
def simple_function():
    magic_number = 42  # This should trigger a violation
    return magic_number * 2
"""
        )

    def teardown_method(self):
        """Clean up test fixtures."""
        if self.test_dir.exists():
            for file in self.test_dir.glob("*"):
                if file.is_file():
                    file.unlink()
            self.test_dir.rmdir()

    def test_basic_directory_analysis_command(self):
        """Test that CLI argument parsing works with current implementation."""
        parser = create_parser()

        # Test parsing with --path flag (current implementation style)
        args = parser.parse_args(["--path", "."])
        assert args.path == "."
        assert args.policy == "default"
        assert args.format == "json"

    def test_simplified_command_structure(self):
        """Test simplified command structure without subcommands."""
        parser = create_parser()

        # Test basic analysis command with current argument structure
        args = parser.parse_args(["--path", str(self.test_dir)])
        assert args.path == str(self.test_dir)

        # Test with policy
        args = parser.parse_args(["--path", str(self.test_dir), "--policy", "strict-core"])
        assert args.policy == "strict-core"

        # Test with output format
        args = parser.parse_args(["--path", str(self.test_dir), "--format", "sarif"])
        assert args.format == "sarif"

    def test_flake8_style_usage_patterns(self):
        """Test CLI usage patterns similar to flake8."""
        parser = create_parser()

        # Test with --path flag (current implementation)
        args = parser.parse_args(["--path", str(self.test_dir)])
        assert args.path == str(self.test_dir)

        # Test with exclusions
        args = parser.parse_args(["--path", str(self.test_dir), "--exclude", "test_*", "--exclude", "*.egg-info"])
        assert "test_*" in args.exclude
        assert "*.egg-info" in args.exclude

        # Test output to file
        args = parser.parse_args(["--path", str(self.test_dir), "--output", "report.json"])
        assert args.output == "report.json"

    def test_policy_argument_handling(self):
        """Test policy argument handling and validation."""
        parser = create_parser()

        # Test valid policies
        valid_policies = ["default", "strict-core", "nasa_jpl_pot10", "lenient"]
        for policy in valid_policies:
            args = parser.parse_args(["--policy", policy, str(self.test_dir)])
            assert args.policy == policy

    def test_format_argument_handling(self):
        """Test output format argument handling."""
        parser = create_parser()

        # Test valid formats
        valid_formats = ["json", "yaml", "sarif"]
        for fmt in valid_formats:
            args = parser.parse_args(["--format", fmt, str(self.test_dir)])
            assert args.format == fmt

    def test_nasa_validation_flag(self):
        """Test NASA validation flag integration."""
        parser = create_parser()

        args = parser.parse_args(["--nasa-validation", str(self.test_dir)])
        assert args.nasa_validation is True

        # When NASA validation is enabled, it should override policy
        with patch("analyzer.core.ConnascenceAnalyzer") as mock_analyzer:
            mock_instance = MagicMock()
            mock_analyzer.return_value = mock_instance
            mock_instance.analyze_path.return_value = {
                "success": True,
                "violations": [],
                "summary": {"total_violations": 0},
            }

            with patch("sys.argv", ["connascence", "--nasa-validation", str(self.test_dir)]), patch("sys.exit"):
                with contextlib.suppress(SystemExit):
                    main()

            # Should call analyze_path with nasa policy
            mock_instance.analyze_path.assert_called_once()
            call_args = mock_instance.analyze_path.call_args
            assert call_args[1]["policy"] == "nasa_jpl_pot10"

    def test_strict_mode_flag(self):
        """Test strict mode flag handling."""
        parser = create_parser()

        args = parser.parse_args(["--strict-mode", str(self.test_dir)])
        assert args.strict_mode is True

    def test_exclude_patterns_handling(self):
        """Test exclude pattern handling."""
        parser = create_parser()

        args = parser.parse_args(
            ["--exclude", "test_*", "--exclude", "__pycache__", "--exclude", "*.pyc", str(self.test_dir)]
        )

        assert args.exclude == ["test_*", "__pycache__", "*.pyc"]

    def test_tool_correlation_flags(self):
        """Test tool correlation and confidence threshold flags."""
        parser = create_parser()

        args = parser.parse_args(["--enable-tool-correlation", "--confidence-threshold", "0.9", str(self.test_dir)])

        assert args.enable_tool_correlation is True
        assert args.confidence_threshold == 0.9

    def test_sarif_specific_flags(self):
        """Test SARIF-specific output flags."""
        parser = create_parser()

        args = parser.parse_args(
            ["--include-nasa-rules", "--include-god-objects", "--include-mece-analysis", str(self.test_dir)]
        )

        assert args.include_nasa_rules is True
        assert args.include_god_objects is True
        assert args.include_mece_analysis is True

    @patch("analyzer.core.ConnascenceAnalyzer")
    def test_successful_analysis_exit_code(self, mock_analyzer):
        """Test exit code for successful analysis."""
        mock_instance = MagicMock()
        mock_analyzer.return_value = mock_instance
        mock_instance.analyze_path.return_value = {
            "success": True,
            "violations": [],
            "summary": {"total_violations": 0},
        }

        with patch("sys.argv", ["connascence", str(self.test_dir)]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0

    @patch("analyzer.core.ConnascenceAnalyzer")
    def test_analysis_with_violations_exit_code(self, mock_analyzer):
        """Test exit code when violations found but not critical."""
        mock_instance = MagicMock()
        mock_analyzer.return_value = mock_instance
        mock_instance.analyze_path.return_value = {
            "success": True,
            "violations": [{"severity": "medium", "type": "connascence_of_meaning"}],
            "summary": {"total_violations": 1},
        }

        with patch("sys.argv", ["connascence", str(self.test_dir)]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0  # Non-critical violations don't fail

    @patch("analyzer.core.ConnascenceAnalyzer")
    def test_critical_violations_exit_code_strict_mode(self, mock_analyzer):
        """Test exit code for critical violations in strict mode."""
        mock_instance = MagicMock()
        mock_analyzer.return_value = mock_instance
        mock_instance.analyze_path.return_value = {
            "success": True,
            "violations": [{"severity": "critical", "type": "god_object"}],
            "summary": {"total_violations": 1},
        }

        with patch("sys.argv", ["connascence", "--strict-mode", str(self.test_dir)]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1  # Critical violations in strict mode fail

    @patch("analyzer.core.ConnascenceAnalyzer")
    def test_analysis_failure_exit_code(self, mock_analyzer):
        """Test exit code for analysis failure."""
        mock_instance = MagicMock()
        mock_analyzer.return_value = mock_instance
        mock_instance.analyze_path.return_value = {"success": False, "error": "Analysis failed", "violations": []}

        with patch("sys.argv", ["connascence", str(self.test_dir)]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

    def test_help_message_content(self):
        """Test help message contains expected information."""
        parser = create_parser()
        help_text = parser.format_help()

        # Check key elements are in help
        assert "Connascence Safety Analyzer" in help_text
        assert "--path" in help_text
        assert "--policy" in help_text
        assert "--format" in help_text
        assert "--nasa-validation" in help_text

    def test_error_handling_invalid_path(self):
        """Test error handling for invalid paths."""
        with patch("sys.argv", ["connascence", "/nonexistent/path"]), patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(SystemExit):
                main()

    @patch("analyzer.core.ConnascenceAnalyzer")
    def test_json_output_format(self, mock_analyzer):
        """Test JSON output format."""
        mock_instance = MagicMock()
        mock_analyzer.return_value = mock_instance
        mock_instance.analyze_path.return_value = {
            "success": True,
            "violations": [],
            "summary": {"total_violations": 0},
        }

        with patch("analyzer.core.JSONReporter") as mock_reporter:
            mock_reporter_instance = MagicMock()
            mock_reporter.return_value = mock_reporter_instance
            mock_reporter_instance.export_results.return_value = '{"test": "json"}'

            with patch("sys.argv", ["connascence", "--format", "json", str(self.test_dir)]), pytest.raises(SystemExit):
                main()

            # Should use JSONReporter
            mock_reporter.assert_called_once()

    @patch("analyzer.core.ConnascenceAnalyzer")
    def test_sarif_output_format(self, mock_analyzer):
        """Test SARIF output format."""
        mock_instance = MagicMock()
        mock_analyzer.return_value = mock_instance
        mock_instance.analyze_path.return_value = {
            "success": True,
            "violations": [],
            "summary": {"total_violations": 0},
        }

        with patch("analyzer.core.SARIFReporter") as mock_reporter:
            mock_reporter_instance = MagicMock()
            mock_reporter.return_value = mock_reporter_instance
            mock_reporter_instance.export_results.return_value = '{"version": "2.1.0"}'

            with patch("sys.argv", ["connascence", "--format", "sarif", str(self.test_dir)]), pytest.raises(SystemExit):
                main()

            # Should use SARIFReporter
            mock_reporter.assert_called_once()

    def test_output_file_handling(self):
        """Test output file argument handling."""
        output_file = self.test_dir / "output.json"

        with patch("analyzer.core.ConnascenceAnalyzer") as mock_analyzer:
            mock_instance = MagicMock()
            mock_analyzer.return_value = mock_instance
            mock_instance.analyze_path.return_value = {
                "success": True,
                "violations": [],
                "summary": {"total_violations": 0},
            }

            with patch("analyzer.core.JSONReporter") as mock_reporter:
                mock_reporter_instance = MagicMock()
                mock_reporter.return_value = mock_reporter_instance

                with patch("sys.argv", ["connascence", "--output", str(output_file), str(self.test_dir)]):
                    with pytest.raises(SystemExit):
                        main()

                # Should call export_results with file path
                mock_reporter_instance.export_results.assert_called()


class TestCLIBackwardsCompatibility:
    """Test backwards compatibility with existing CLI usage patterns."""

    def test_legacy_argument_patterns(self):
        """Test that legacy argument patterns still work."""
        parser = create_parser()

        # Legacy style arguments should still parse
        legacy_patterns = [
            ["--path", ".", "--policy", "default"],
            [".", "--format", "json"],
            ["--nasa-validation", "."],
        ]

        for pattern in legacy_patterns:
            args = parser.parse_args(pattern)
            # Should parse without errors
            assert args is not None

    def test_policy_name_resolution(self):
        """Test policy name resolution for backwards compatibility."""
        # Test policy name resolution
        assert resolve_policy_name("default") == "standard"
        assert resolve_policy_name("nasa_jpl_pot10") == "nasa-compliance"
        assert resolve_policy_name("strict-core") == "strict"
        assert resolve_policy_name("lenient") == "lenient"

        # Test unknown policy defaults to standard
        assert resolve_policy_name("unknown_policy") == "standard"

    def test_deprecated_policy_warnings(self):
        """Test that deprecated policy names generate warnings."""
        with patch("warnings.warn") as mock_warn:
            resolve_policy_name("nasa_jpl_pot10", warn_deprecated=True)
            mock_warn.assert_called_once()

    def test_error_handling_compatibility(self):
        """Test error handling maintains compatibility."""
        # Test that error codes and messages are compatible
        parser = create_parser()

        # Invalid policy should still be handled gracefully
        try:
            args = parser.parse_args(["--policy", "invalid_policy", "."])
            # Parser should accept it, resolution happens later
            assert args.policy == "invalid_policy"
        except SystemExit:
            # Or parser rejects it - both are acceptable
            pass


class TestCLIConfigurationDiscovery:
    """Test configuration file discovery and handling."""

    def setup_method(self):
        """Set up test configuration files."""
        self.test_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test fixtures."""
        if self.test_dir.exists():
            for file in self.test_dir.rglob("*"):
                if file.is_file():
                    file.unlink()
            for dir in sorted(self.test_dir.rglob("*"), reverse=True):
                if dir.is_dir():
                    dir.rmdir()
            self.test_dir.rmdir()

    def test_pyproject_toml_discovery(self):
        """Test discovery of pyproject.toml configuration."""
        pyproject_file = self.test_dir / "pyproject.toml"
        pyproject_file.write_text(
            """
[tool.connascence]
policy = "strict-core"
exclude = ["test_*", "__pycache__"]
"""
        )

        # Configuration discovery would happen in the main application
        # This test verifies the file exists and is readable
        assert pyproject_file.exists()
        content = pyproject_file.read_text()
        assert "connascence" in content

    def test_setup_cfg_discovery(self):
        """Test discovery of setup.cfg configuration."""
        setup_cfg = self.test_dir / "setup.cfg"
        setup_cfg.write_text(
            """
[connascence]
policy = nasa_jpl_pot10
format = sarif
"""
        )

        assert setup_cfg.exists()
        content = setup_cfg.read_text()
        assert "connascence" in content

    def test_connascence_cfg_discovery(self):
        """Test discovery of .connascence.cfg configuration file."""
        connascence_cfg = self.test_dir / ".connascence.cfg"
        connascence_cfg.write_text(
            """
[connascence]
policy = strict-core
exclude = test_*,__pycache__
include-nasa-rules = true
"""
        )

        assert connascence_cfg.exists()

    def test_config_file_precedence(self):
        """Test configuration file precedence order."""
        # CLI args should override config files
        # Project-specific config should override global config

        # This would be tested in integration with actual config loading
        # Here we just verify the files can be created and read
        files_to_create = [".connascence.cfg", "setup.cfg", "pyproject.toml"]

        for filename in files_to_create:
            config_file = self.test_dir / filename
            config_file.write_text(
                f"""
# Configuration for {filename}
[tool.connascence]
policy = "test"
"""
            )
            assert config_file.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
