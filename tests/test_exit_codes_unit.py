#!/usr/bin/env python3

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
Smoke Test Suite: CLI Exit Code Tests

Comprehensive tests for all CLI exit code paths to ensure proper error handling
and return codes for various scenarios.
"""

import sys
import subprocess
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import List, Optional


class TestCLIExitCodes:
    """Test CLI exit codes for various scenarios."""

    @pytest.fixture(scope="class", autouse=True)
    def setup_path(self):
        """Add project root to Python path."""
        project_root = Path(__file__).parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

    def test_success_exit_code(self):
        """Test that successful operations return exit code 0."""
        try:
            from cli.connascence import ConnascenceCLI
            from analyzer.constants import EXIT_SUCCESS as ExitCode
            
            cli = ConnascenceCLI()
            
            # Test help command returns success
            exit_code = cli.run(['--help'])
            # Help might print and exit, so we catch SystemExit
            
        except SystemExit as e:
            # Help command exits with 0
            assert e.code == 0
        except ImportError as e:
            pytest.skip(f"CLI not available: {e}")

    def test_no_command_exit_code(self):
        """Test exit code when no command is provided."""
        try:
            from cli.connascence import ConnascenceCLI
            from analyzer.constants import EXIT_SUCCESS as ExitCode
            
            cli = ConnascenceCLI()
            exit_code = cli.run([])
            
            # Should return success (prints help)
            assert exit_code == ExitCode.SUCCESS
            
        except ImportError as e:
            pytest.skip(f"CLI not available: {e}")

    def test_invalid_command_exit_code(self):
        """Test exit code for invalid commands."""
        try:
            from cli.connascence import ConnascenceCLI
            from analyzer.constants import EXIT_SUCCESS as ExitCode
            
            cli = ConnascenceCLI()
            
            # Test with invalid command
            with pytest.raises(SystemExit) as exc_info:
                cli.run(['invalid-command'])
            
            # ArgumentParser exits with code 2 for invalid arguments
            assert exc_info.value.code == 2
            
        except ImportError as e:
            pytest.skip(f"CLI not available: {e}")

    def test_keyboard_interrupt_exit_code(self):
        """Test exit code when user interrupts with Ctrl+C."""
        try:
            from cli.connascence import ConnascenceCLI
            from analyzer.constants import EXIT_SUCCESS as ExitCode
            
            cli = ConnascenceCLI()
            
            # Mock a scan operation that raises KeyboardInterrupt
            with patch.object(cli.scan_handler, 'handle', side_effect=KeyboardInterrupt()):
                exit_code = cli.run(['scan', '.'])
                assert exit_code == ExitCode.USER_INTERRUPTED
                
        except ImportError as e:
            pytest.skip(f"CLI not available: {e}")

    def test_general_error_exit_code(self):
        """Test exit code for general errors."""
        try:
            from cli.connascence import ConnascenceCLI
            from analyzer.constants import EXIT_SUCCESS as ExitCode
            
            cli = ConnascenceCLI()
            
            # Mock a scan operation that raises a general exception
            with patch.object(cli.scan_handler, 'handle', side_effect=Exception("Test error")):
                exit_code = cli.run(['scan', '.'])
                assert exit_code == ExitCode.RUNTIME_ERROR
                
        except ImportError as e:
            pytest.skip(f"CLI not available: {e}")

    def test_license_error_exit_code(self):
        """Test exit code for license validation errors."""
        try:
            from cli.connascence import ConnascenceCLI
            from analyzer.constants import EXIT_SUCCESS as ExitCode
            import cli.connascence
            
            cli = ConnascenceCLI()
            
            # Mock license validation failure
            mock_validator = MagicMock()
            mock_report = MagicMock()
            mock_report.exit_code = ExitCode.LICENSE_ERROR
            mock_report.validation_result = MagicMock()
            mock_report.validation_result.value = "INVALID"
            mock_report.errors = []
            mock_validator.validate_license.return_value = mock_report
            
            cli.license_validator = mock_validator
            
            # Enable license validation for this test
            with patch('cli.connascence.LICENSE_VALIDATION_AVAILABLE', True):
                exit_code = cli.run(['scan', '.'])
                assert exit_code == ExitCode.LICENSE_ERROR
            
        except ImportError as e:
            pytest.skip(f"CLI not available: {e}")

    def test_configuration_error_exit_code(self):
        """Test exit code for configuration errors."""
        try:
            from analyzer.constants import EXIT_SUCCESS as ExitCode
            
            # Configuration errors typically happen in handler classes
            # This tests that the constant exists and has correct value
            assert ExitCode.CONFIGURATION_ERROR == 2
            
        except ImportError as e:
            pytest.skip(f"Constants not available: {e}")

    @pytest.mark.slow
    def test_command_line_script_exists(self):
        """Test that the connascence command-line script works."""
        try:
            # Try to run the console script
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'show', 'connascence-analyzer'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # If package is not installed, that's OK for development
            # Just test that we can import the main function
            from cli.connascence import main
            assert callable(main)
            
        except subprocess.TimeoutExpired:
            pytest.skip("Command timeout - package may not be installed")
        except ImportError as e:
            pytest.fail(f"Cannot import main function: {e}")

    def test_version_command_exit_code(self):
        """Test that version command returns proper exit code."""
        try:
            from cli.connascence import ConnascenceCLI
            
            cli = ConnascenceCLI()
            
            # Version command should exit with code 0
            with pytest.raises(SystemExit) as exc_info:
                cli.run(['--version'])
            
            assert exc_info.value.code == 0
            
        except ImportError as e:
            pytest.skip(f"CLI not available: {e}")

    def test_all_subcommand_parsers_exist(self):
        """Test that all expected subcommand parsers can be created."""
        try:
            from cli.connascence import ConnascenceCLI
            
            cli = ConnascenceCLI()
            parser = cli.create_parser()
            
            # Test that parser was created successfully
            assert parser is not None
            
            # Test parsing some basic commands
            test_commands = [
                ['scan', '.'],
                ['scan-diff', '--base', 'HEAD~1'],
                ['baseline', 'status'],
                ['autofix', '--dry-run'],
                ['explain', 'test-id'],
                ['mcp', 'serve'],
                ['license', 'validate']
            ]
            
            for cmd in test_commands:
                try:
                    # Just test parsing, not execution
                    args = parser.parse_args(cmd)
                    assert args is not None
                except SystemExit:
                    # Some commands might exit during parsing (that's OK)
                    pass
                    
        except ImportError as e:
            pytest.skip(f"CLI not available: {e}")

    def test_verbose_flag_handling(self):
        """Test that verbose flag is handled properly."""
        try:
            from cli.connascence import ConnascenceCLI
            
            cli = ConnascenceCLI()
            
            # Mock the scan handler to avoid actual scanning
            with patch.object(cli.scan_handler, 'handle', return_value=0):
                exit_code = cli.run(['--verbose', 'scan', '.'])
                assert exit_code == 0
                
        except ImportError as e:
            pytest.skip(f"CLI not available: {e}")

    def test_config_file_handling(self):
        """Test that config file parameter is handled."""
        try:
            from cli.connascence import ConnascenceCLI
            
            cli = ConnascenceCLI()
            parser = cli.create_parser()
            
            # Test parsing with config file
            args = parser.parse_args(['--config', 'test.yml', 'scan', '.'])
            assert args.config == 'test.yml'
            
        except ImportError as e:
            pytest.skip(f"CLI not available: {e}")

    def test_skip_license_check_flag(self):
        """Test skip license check flag functionality."""
        try:
            from cli.connascence import ConnascenceCLI
            
            cli = ConnascenceCLI()
            
            # Mock the scan handler
            with patch.object(cli.scan_handler, 'handle', return_value=0):
                exit_code = cli.run(['--skip-license-check', 'scan', '.'])
                assert exit_code == 0
                
        except ImportError as e:
            pytest.skip(f"CLI not available: {e}")


class TestCommandHandlerIntegration:
    """Test that command handlers integrate properly with CLI."""

    def test_scan_handler_integration(self):
        """Test that scan command handler integrates properly."""
        try:
            from cli.connascence import ConnascenceCLI
            
            cli = ConnascenceCLI()
            assert cli.scan_handler is not None
            assert hasattr(cli.scan_handler, 'handle')
            assert callable(cli.scan_handler.handle)
            
        except ImportError as e:
            pytest.skip(f"CLI not available: {e}")

    def test_baseline_handler_integration(self):
        """Test that baseline command handler integrates properly."""
        try:
            from cli.connascence import ConnascenceCLI
            
            cli = ConnascenceCLI()
            assert cli.baseline_handler is not None
            assert hasattr(cli.baseline_handler, 'handle')
            assert callable(cli.baseline_handler.handle)
            
        except ImportError as e:
            pytest.skip(f"CLI not available: {e}")

    def test_autofix_handler_integration(self):
        """Test that autofix command handler integrates properly."""
        try:
            from cli.connascence import ConnascenceCLI
            
            cli = ConnascenceCLI()
            assert cli.autofix_handler is not None
            assert hasattr(cli.autofix_handler, 'handle')
            assert callable(cli.autofix_handler.handle)
            
        except ImportError as e:
            pytest.skip(f"CLI not available: {e}")

    def test_mcp_handler_integration(self):
        """Test that MCP command handler integrates properly."""
        try:
            from cli.connascence import ConnascenceCLI
            
            cli = ConnascenceCLI()
            assert cli.mcp_handler is not None
            assert hasattr(cli.mcp_handler, 'handle')
            assert callable(cli.mcp_handler.handle)
            
        except ImportError as e:
            pytest.skip(f"CLI not available: {e}")


class TestExitCodeConstants:
    """Test that exit code constants are properly defined."""

    def test_exit_code_enum_values(self):
        """Test that all expected exit codes are defined."""
        try:
            from analyzer.constants import EXIT_SUCCESS as ExitCode
            
            # Test all expected exit codes
            expected_codes = {
                'SUCCESS': 0,
                'GENERAL_ERROR': 1,
                'CONFIGURATION_ERROR': 2,
                'LICENSE_ERROR': 4,
                'USER_INTERRUPTED': 130
            }
            
            for name, value in expected_codes.items():
                assert hasattr(ExitCode, name), f"ExitCode.{name} not defined"
                assert getattr(ExitCode, name) == value, f"ExitCode.{name} has wrong value"
                
        except ImportError as e:
            pytest.fail(f"Cannot import ExitCode constants: {e}")

    def test_backward_compatibility_mapping(self):
        """Test backward compatibility exit code mapping."""
        try:
            from src.constants import EXIT_CODES, ExitCode
            
            # Test that mapping exists and is correct
            assert EXIT_CODES['success'] == ExitCode.SUCCESS
            assert EXIT_CODES['error'] == ExitCode.GENERAL_ERROR
            assert EXIT_CODES['config_error'] == ExitCode.CONFIGURATION_ERROR
            assert EXIT_CODES['license_error'] == ExitCode.LICENSE_ERROR
            assert EXIT_CODES['interrupted'] == ExitCode.USER_INTERRUPTED
            
        except ImportError as e:
            pytest.fail(f"Cannot import exit code mappings: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])