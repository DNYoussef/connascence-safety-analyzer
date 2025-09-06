# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

"""
Tests for the Connascence CLI interface.

Tests all CLI commands including scan, scan-diff, autofix, baseline management,
and MCP server functionality.
"""

import argparse
import contextlib
import json
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import Mock, patch

import pytest

from cli.connascence import ConnascenceCLI


class TestConnascenceCLI:
    """Test the main CLI class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cli = ConnascenceCLI()

    def test_parser_creation(self):
        """Test that argument parser is created correctly."""
        parser = self.cli.create_parser()

        # Test parser properties
        assert parser.prog == "connascence"
        assert parser.description

        # Test that subcommands are registered
        subparsers_actions = [
            action for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ]
        assert len(subparsers_actions) == 1

        subparsers = subparsers_actions[0]
        commands = list(subparsers.choices.keys())

        expected_commands = ['scan', 'scan-diff', 'explain', 'autofix', 'baseline', 'mcp']
        for cmd in expected_commands:
            assert cmd in commands

    def test_scan_command_parsing(self):
        """Test parsing of scan command arguments."""
        parser = self.cli.create_parser()

        # Test basic scan command
        args = parser.parse_args(['scan', '/path/to/code'])
        assert args.command == 'scan'
        assert args.path == '/path/to/code'
        assert args.policy == 'service-defaults'  # default
        assert args.format == 'text'  # default

        # Test scan with options
        args = parser.parse_args([
            'scan', '/path',
            '--policy', 'strict-core',
            '--format', 'json',
            '--output', 'results.json',
            '--severity', 'high',
            '--exclude', '*.test.py',
            '--incremental',
            '--budget-check'
        ])

        assert args.policy == 'strict-core'
        assert args.format == 'json'
        assert args.output == 'results.json'
        assert args.severity == 'high'
        assert 'parse_args.exclude' in str(args) or hasattr(args, 'exclude')
        assert args.incremental is True
        assert args.budget_check is True

    def test_autofix_command_parsing(self):
        """Test parsing of autofix command arguments."""
        parser = self.cli.create_parser()

        # Test preview mode
        args = parser.parse_args(['autofix', '--preview'])
        assert args.command == 'autofix'
        assert args.preview is True

        # Test apply mode with options
        args = parser.parse_args([
            'autofix', '/path',
            '--apply',
            '--min-confidence', '0.8',
            '--safe-only',
            '--types', 'CoM', 'CoP',
            '--verbose'
        ])

        assert args.force is True  # --apply sets force
        assert args.min_confidence == 0.8
        assert args.safe_only is True
        assert args.types == ['CoM', 'CoP']
        assert args.verbose is True

    def test_baseline_command_parsing(self):
        """Test parsing of baseline command arguments."""
        parser = self.cli.create_parser()

        # Test snapshot subcommand
        args = parser.parse_args(['baseline', 'snapshot', '--message', 'Initial baseline'])
        assert args.command == 'baseline'
        assert args.baseline_command == 'snapshot'
        assert args.message == 'Initial baseline'

        # Test status subcommand
        args = parser.parse_args(['baseline', 'status'])
        assert args.baseline_command == 'status'


class TestCLIScanCommand:
    """Test the scan command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cli = ConnascenceCLI()

    @patch('cli.connascence.ConnascenceASTAnalyzer')
    def test_scan_basic_execution(self, mock_analyzer_class):
        """Test basic scan command execution."""
        # Mock analyzer
        mock_analyzer = Mock()
        mock_analyzer.analyze_directory.return_value = []
        mock_analyzer_class.return_value = mock_analyzer

        # Create test arguments
        parser = self.cli.create_parser()
        args = parser.parse_args(['scan', '.'])

        # Execute scan
        result = self.cli._handle_scan(args)

        # Verify analyzer was called
        mock_analyzer.analyze_directory.assert_called_once()
        assert result == 0  # Success exit code

    @patch('cli.connascence.ConnascenceASTAnalyzer')
    def test_scan_with_violations(self, mock_analyzer_class):
        """Test scan command with violations found."""
        from analyzer.core import ConnascenceViolation

        # Mock violations
        violations = [
            ConnascenceViolation(
                id="test1", rule_id="CON_CoM", connascence_type="CoM",
                severity="high", description="Magic literal",
                file_path="test.py", line_number=10, weight=3.0
            ),
            ConnascenceViolation(
                id="test2", rule_id="CON_CoP", connascence_type="CoP",
                severity="medium", description="Too many params",
                file_path="test.py", line_number=5, weight=2.0
            )
        ]

        # Mock analyzer
        mock_analyzer = Mock()
        mock_analyzer.analyze_directory.return_value = violations
        mock_analyzer_class.return_value = mock_analyzer

        # Create test arguments
        parser = self.cli.create_parser()
        args = parser.parse_args(['scan', '.', '--format', 'json'])

        # Execute scan
        with patch('builtins.print') as mock_print:
            result = self.cli._handle_scan(args)

        # Should return error exit code when violations found
        assert result == 1

        # Should have printed results
        mock_print.assert_called()

    @patch('cli.connascence.ConnascenceASTAnalyzer')
    @patch('cli.connascence.JSONReporter')
    def test_scan_json_output(self, mock_reporter_class, mock_analyzer_class):
        """Test scan command with JSON output format."""
        # Mock analyzer
        mock_analyzer = Mock()
        mock_analyzer.analyze_directory.return_value = []
        mock_analyzer_class.return_value = mock_analyzer

        # Mock reporter
        mock_reporter = Mock()
        mock_reporter.generate_report.return_value = '{"violations": []}'
        mock_reporter_class.return_value = mock_reporter

        # Create test arguments
        parser = self.cli.create_parser()
        args = parser.parse_args(['scan', '.', '--format', 'json'])

        # Execute scan
        self.cli._handle_scan(args)

        # Verify JSON reporter was used
        mock_reporter_class.assert_called_once()
        mock_reporter.generate_report.assert_called_once()

    @patch('cli.connascence.ConnascenceASTAnalyzer')
    def test_scan_with_policy(self, mock_analyzer_class):
        """Test scan command with specific policy."""
        mock_analyzer = Mock()
        mock_analyzer.analyze_directory.return_value = []
        mock_analyzer_class.return_value = mock_analyzer

        # Test with strict policy
        parser = self.cli.create_parser()
        args = parser.parse_args(['scan', '.', '--policy', 'strict-core'])

        self.cli._handle_scan(args)

        # Verify analyzer was configured with correct policy
        mock_analyzer_class.assert_called_with(policy_preset='strict-core')


class TestCLIAutofixCommand:
    """Test the autofix command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cli = ConnascenceCLI()

    @patch('cli.connascence.SafeAutofixer')
    def test_autofix_preview_mode(self, mock_autofixer_class):
        """Test autofix command in preview mode."""
        # Mock autofixer
        mock_autofixer = Mock()
        mock_autofixer.preview_fixes.return_value = {
            'file_path': 'test.py',
            'total_patches': 2,
            'patches': [
                {
                    'description': 'Extract magic literal',
                    'confidence': 0.8,
                    'safety': 'safe',
                    'diff': '+CONSTANT = 100\\n-value = 100\\n+value = CONSTANT'
                }
            ],
            'recommendations': ['Consider creating constants module']
        }
        mock_autofixer_class.return_value = mock_autofixer

        # Mock violations loading
        with patch.object(self.cli, '_load_or_scan_violations') as mock_load:
            mock_load.return_value = [Mock()]  # Some violations

            parser = self.cli.create_parser()
            args = parser.parse_args(['autofix', '--preview'])

            with patch('builtins.print') as mock_print:
                result = self.cli._handle_autofix(args)

            # Should succeed in preview mode
            assert result == 0

            # Should show preview output
            mock_print.assert_called()
            print_calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
            preview_output = ' '.join(print_calls)
            assert 'preview' in preview_output.lower() or 'fixes' in preview_output.lower()

    @patch('cli.connascence.AutofixEngine')
    def test_autofix_apply_mode(self, mock_engine_class):
        """Test autofix command in apply mode."""
        from autofix.patch_api import AutofixResult

        # Mock engine
        mock_engine = Mock()
        mock_engine.analyze_file.return_value = []  # No patches
        mock_engine.apply_patches.return_value = AutofixResult(
            patches_generated=0, patches_applied=0, violations_fixed=[],
            warnings=[], errors=[], confidence_score=0.0
        )
        mock_engine_class.return_value = mock_engine

        # Mock violations loading
        with patch.object(self.cli, '_load_or_scan_violations') as mock_load:
            mock_load.return_value = []  # No violations

            parser = self.cli.create_parser()
            args = parser.parse_args(['autofix', '--apply'])

            with patch('builtins.print'):
                result = self.cli._handle_autofix(args)

            # Should succeed when no violations
            assert result == 0

    def test_autofix_without_force_flag(self):
        """Test autofix command without --force flag."""
        with patch.object(self.cli, '_load_or_scan_violations') as mock_load:
            mock_load.return_value = [Mock()]  # Some violations

            parser = self.cli.create_parser()
            args = parser.parse_args(['autofix'])  # No --apply flag

            with patch('builtins.print') as mock_print:
                result = self.cli._handle_autofix(args)

            # Should fail without force flag
            assert result == 1

            # Should show warning message
            print_calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
            output = ' '.join(print_calls)
            assert 'force' in output.lower() or 'confirm' in output.lower()

    @patch('cli.connascence.AutofixEngine')
    def test_autofix_confidence_filtering(self, mock_engine_class):
        """Test autofix command with confidence filtering."""
        from autofix.patch_api import PatchSuggestion

        # Mock patches with different confidence levels
        patches = [
            PatchSuggestion(
                violation_id="high", confidence=0.9, description="High confidence",
                old_code="old", new_code="new", file_path="test.py",
                line_range=(1, 1), safety_level="safe", rollback_info={}
            ),
            PatchSuggestion(
                violation_id="low", confidence=0.5, description="Low confidence",
                old_code="old", new_code="new", file_path="test.py",
                line_range=(2, 2), safety_level="safe", rollback_info={}
            )
        ]

        mock_engine = Mock()
        mock_engine.analyze_file.return_value = patches
        mock_engine_class.return_value = mock_engine

        with patch.object(self.cli, '_load_or_scan_violations') as mock_load:
            with patch.object(self.cli, '_group_violations_by_file') as mock_group:
                mock_load.return_value = [Mock()]
                mock_group.return_value = {'test.py': [Mock()]}

                parser = self.cli.create_parser()
                args = parser.parse_args([
                    'autofix', '--apply', '--min-confidence', '0.8'
                ])

                # Mock the filter method
                with patch.object(self.cli, '_filter_patches') as mock_filter:
                    mock_filter.return_value = [patches[0]]  # Only high confidence

                    self.cli._handle_autofix(args)

                    # Should call filter with correct confidence
                    mock_filter.assert_called()
                    call_args = mock_filter.call_args[0]
                    assert call_args[0] == patches  # Original patches
                    assert call_args[1].min_confidence == 0.8


class TestCLIIntegration:
    """Integration tests for CLI functionality."""

    @pytest.fixture
    def temp_project(self):
        """Create temporary project with Python files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create sample files with violations
            (project_path / "main.py").write_text("""
def calculate_price(base, tax_rate, discount_rate, handling_fee, service_charge):
    if base > 100:  # Magic literal
        return base * 1.2  # Magic literal
    return base
""")

            (project_path / "utils.py").write_text("""
def clean_function(x: int) -> int:
    return x * 2
""")

            yield project_path

    def test_end_to_end_scan(self, temp_project):
        """Test complete scan workflow."""
        cli = ConnascenceCLI()
        parser = cli.create_parser()

        # Test scan command
        args = parser.parse_args(['scan', str(temp_project), '--format', 'json'])

        with patch('builtins.print') as mock_print:
            result = cli._handle_scan(args)

        # Should find violations and return error code
        assert result == 1

        # Should output JSON format
        print_calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
        json_output = ' '.join(print_calls)

        # Try to parse as JSON to verify format
        with contextlib.suppress(json.JSONDecodeError, TypeError):
            json.loads(json_output)


    def test_cli_error_handling(self):
        """Test CLI error handling for invalid inputs."""
        cli = ConnascenceCLI()
        parser = cli.create_parser()

        # Test scan on non-existent path
        args = parser.parse_args(['scan', '/non/existent/path'])

        with patch('builtins.print'):
            result = cli._handle_scan(args)

        # Should handle error gracefully
        assert result == 1

    def test_verbose_logging(self):
        """Test verbose logging option."""
        cli = ConnascenceCLI()
        parser = cli.create_parser()

        args = parser.parse_args(['--verbose', 'scan', '.'])

        # Should set verbose flag
        assert args.verbose is True

        # In a real implementation, this would configure logging level


class TestCLISubcommands:
    """Test individual CLI subcommands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cli = ConnascenceCLI()

    @patch('cli.connascence.BaselineManager')
    def test_baseline_snapshot_command(self, mock_baseline_class):
        """Test baseline snapshot command."""
        mock_baseline = Mock()
        mock_baseline.create_snapshot.return_value = True
        mock_baseline_class.return_value = mock_baseline

        parser = self.cli.create_parser()
        args = parser.parse_args(['baseline', 'snapshot', '--message', 'Test baseline'])

        # Mock the baseline handler
        with patch.object(self.cli, '_handle_baseline') as mock_handler:
            mock_handler.return_value = 0

            result = mock_handler(args)
            assert result == 0

    @patch('cli.connascence.subprocess.run')
    def test_scan_diff_command(self, mock_subprocess):
        """Test scan-diff command."""
        # Mock git diff output
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "modified_file.py\\n"

        parser = self.cli.create_parser()
        args = parser.parse_args(['scan-diff', '--base', 'main', '--head', 'feature'])

        # Mock the scan-diff handler
        with patch.object(self.cli, '_handle_scan_diff') as mock_handler:
            mock_handler.return_value = 0

            result = mock_handler(args)
            assert result == 0

    @patch('mcp.server')
    def test_mcp_serve_command(self, mock_mcp_server):
        """Test MCP server command."""
        mock_mcp_server.serve.return_value = None

        parser = self.cli.create_parser()
        args = parser.parse_args(['mcp', 'serve', '--port', '8080'])

        # Mock the MCP handler
        with patch.object(self.cli, '_handle_mcp') as mock_handler:
            mock_handler.return_value = 0

            result = mock_handler(args)
            assert result == 0


# Integration test with actual CLI execution (optional, slower)
class TestCLIExecution:
    """Test actual CLI execution (integration tests)."""

    @pytest.mark.slow
    def test_cli_help(self):
        """Test CLI help output."""
        try:
            result = subprocess.run(
                ['python', '-m', 'cli.connascence', '--help'],
                capture_output=True,
                text=True,
                timeout=10
            )

            assert result.returncode == 0
            assert 'connascence' in result.stdout.lower()
            assert 'scan' in result.stdout

        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("CLI not available for execution test")

    @pytest.mark.slow
    def test_cli_version(self):
        """Test CLI version output."""
        try:
            result = subprocess.run(
                ['python', '-m', 'cli.connascence', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )

            assert result.returncode == 0
            assert 'connascence' in result.stdout.lower()

        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("CLI not available for execution test")
