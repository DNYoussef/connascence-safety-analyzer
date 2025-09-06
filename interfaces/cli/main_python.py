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
Professional Connascence CLI

A comprehensive command-line interface for connascence analysis with
subcommands for scanning, diffing, baseline management, and autofixing.

Usage:
    connascence scan [path] [options]
    connascence scan-diff --base <ref> [--head <ref>]
    connascence explain <finding-id>
    connascence autofix [options]
    connascence baseline snapshot|update|status
    connascence mcp serve [options]
"""

import argparse
import logging
from pathlib import Path
import sys
from typing import List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import constants and handlers to reduce connascence
from experimental.src.cli_handlers import (
    AutofixCommandHandler,
    BaselineCommandHandler,
    ExplainCommandHandler,
    LicenseCommandHandler,
    MCPCommandHandler,
    ScanCommandHandler,
    ScanDiffCommandHandler,
)
from experimental.src.constants import ExitCode, ValidationMessages

from policy.baselines import BaselineManager
from policy.budgets import BudgetTracker
from policy.manager import PolicyManager

# Configure logging first
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import license validation system
try:
    from licensing import LicenseValidationResult, LicenseValidator
    LICENSE_VALIDATION_AVAILABLE = True
except ImportError:
    LICENSE_VALIDATION_AVAILABLE = False
    logger.warning("License validation system not available")


class ConnascenceCLI:
    """Main CLI application class - Focused orchestrator for command delegation."""

    def __init__(self):
        self.policy_manager = PolicyManager()
        self.baseline_manager = BaselineManager()
        self.budget_tracker = BudgetTracker()

        # Initialize license validator if available
        if LICENSE_VALIDATION_AVAILABLE:
            self.license_validator = LicenseValidator()
        else:
            self.license_validator = None

        # Initialize command handlers (Delegation pattern)
        self.scan_handler = ScanCommandHandler(
            self.policy_manager, self.baseline_manager, self.budget_tracker
        )
        self.license_handler = LicenseCommandHandler(
            self.policy_manager, self.baseline_manager, self.budget_tracker,
            self.license_validator
        )
        self.baseline_handler = BaselineCommandHandler(
            self.policy_manager, self.baseline_manager, self.budget_tracker
        )
        self.mcp_handler = MCPCommandHandler(
            self.policy_manager, self.baseline_manager, self.budget_tracker
        )
        self.explain_handler = ExplainCommandHandler(
            self.policy_manager, self.baseline_manager, self.budget_tracker
        )
        self.autofix_handler = AutofixCommandHandler(
            self.policy_manager, self.baseline_manager, self.budget_tracker
        )
        self.scan_diff_handler = ScanDiffCommandHandler(
            self.policy_manager, self.baseline_manager, self.budget_tracker
        )

    def create_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser with subcommands."""
        parser = argparse.ArgumentParser(
            prog="connascence",
            description="Professional connascence analysis for Python codebases",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  connascence scan .                          # Analyze current directory
  connascence scan src/ --policy strict-core # Use strict policy
  connascence scan-diff --base HEAD~1        # Analyze PR diff
  connascence autofix --dry-run              # Preview fixes
  connascence baseline snapshot              # Create quality baseline
            """
        )

        # Global options
        parser.add_argument(
            "--verbose", "-v",
            action="store_true",
            help="Enable verbose logging"
        )
        parser.add_argument(
            "--config",
            help="Path to configuration file"
        )
        parser.add_argument(
            "--version",
            action="version",
            version="connascence 1.0.0"
        )
        parser.add_argument(
            "--skip-license-check",
            action="store_true",
            help="Skip license validation (exit code 4 on license errors)"
        )

        # Subcommands
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Scan command
        self._add_scan_parser(subparsers)

        # Scan-diff command
        self._add_scan_diff_parser(subparsers)

        # Explain command
        self._add_explain_parser(subparsers)

        # Autofix command
        self._add_autofix_parser(subparsers)

        # Baseline commands
        self._add_baseline_parser(subparsers)

        # MCP server command
        self._add_mcp_parser(subparsers)

        # License validation command
        self._add_license_parser(subparsers)

        return parser

    def _add_scan_parser(self, subparsers):
        """Add the scan subcommand parser."""
        scan_parser = subparsers.add_parser(
            "scan",
            help="Analyze code for connascence violations"
        )

        scan_parser.add_argument(
            "path",
            nargs="?",
            default=".",
            help="Path to analyze (default: current directory)"
        )

        scan_parser.add_argument(
            "--policy", "-p",
            choices=["strict-core", "service-defaults", "experimental"],
            default="service-defaults",
            help="Policy preset to use (default: service-defaults)"
        )

        scan_parser.add_argument(
            "--output", "-o",
            help="Output file path"
        )

        scan_parser.add_argument(
            "--format", "-f",
            choices=["json", "sarif", "markdown", "text"],
            default="text",
            help="Output format (default: text)"
        )

        scan_parser.add_argument(
            "--severity", "-s",
            choices=["low", "medium", "high", "critical"],
            help="Minimum severity level to report"
        )

        scan_parser.add_argument(
            "--include",
            action="append",
            help="Include patterns (can be used multiple times)"
        )

        scan_parser.add_argument(
            "--exclude", "-e",
            action="append",
            help="Exclude patterns (can be used multiple times)"
        )

        scan_parser.add_argument(
            "--incremental",
            action="store_true",
            help="Use incremental analysis with caching"
        )

        scan_parser.add_argument(
            "--budget-check",
            action="store_true",
            help="Check against PR budget limits"
        )

    def _add_scan_diff_parser(self, subparsers):
        """Add the scan-diff subcommand parser."""
        diff_parser = subparsers.add_parser(
            "scan-diff",
            help="Analyze changes between git references"
        )

        diff_parser.add_argument(
            "--base", "-b",
            required=True,
            help="Base git reference (e.g., HEAD~1, main)"
        )

        diff_parser.add_argument(
            "--head",
            default="HEAD",
            help="Head git reference (default: HEAD)"
        )

        diff_parser.add_argument(
            "--policy", "-p",
            choices=["strict-core", "service-defaults", "experimental"],
            default="service-defaults",
            help="Policy preset to use"
        )

        diff_parser.add_argument(
            "--format", "-f",
            choices=["json", "sarif", "markdown", "text"],
            default="markdown",
            help="Output format (default: markdown)"
        )

        diff_parser.add_argument(
            "--output", "-o",
            help="Output file path"
        )

    def _add_explain_parser(self, subparsers):
        """Add the explain subcommand parser."""
        explain_parser = subparsers.add_parser(
            "explain",
            help="Explain a specific violation or rule"
        )

        explain_parser.add_argument(
            "finding_id",
            help="Finding ID or rule ID to explain"
        )

        explain_parser.add_argument(
            "--file",
            help="File path for context"
        )

        explain_parser.add_argument(
            "--line",
            type=int,
            help="Line number for context"
        )

    def _add_autofix_parser(self, subparsers):
        """Add the autofix subcommand parser."""
        autofix_parser = subparsers.add_parser(
            "autofix",
            help="Automatically fix connascence violations"
        )

        autofix_parser.add_argument(
            "path",
            nargs="?",
            default=".",
            help="Path to fix (default: current directory)"
        )

        autofix_parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be fixed without making changes"
        )

        autofix_parser.add_argument(
            "--types",
            nargs="+",
            choices=["CoM", "CoP", "CoA", "god-objects"],
            help="Types of violations to fix"
        )

        autofix_parser.add_argument(
            "--severity",
            choices=["low", "medium", "high", "critical"],
            default="medium",
            help="Minimum severity to fix (default: medium)"
        )

        autofix_parser.add_argument(
            "--interactive", "-i",
            action="store_true",
            help="Interactively review each fix"
        )

    def _add_baseline_parser(self, subparsers):
        """Add the baseline subcommand parser."""
        baseline_parser = subparsers.add_parser(
            "baseline",
            help="Manage quality baselines"
        )

        baseline_subparsers = baseline_parser.add_subparsers(
            dest="baseline_action",
            help="Baseline actions"
        )

        # Snapshot
        snapshot_parser = baseline_subparsers.add_parser(
            "snapshot",
            help="Create a new baseline snapshot"
        )
        snapshot_parser.add_argument(
            "--message", "-m",
            help="Snapshot message"
        )

        # Update
        update_parser = baseline_subparsers.add_parser(
            "update",
            help="Update existing baseline"
        )
        update_parser.add_argument(
            "--force",
            action="store_true",
            help="Force update even if quality decreased"
        )

        # Status
        baseline_subparsers.add_parser(
            "status",
            help="Show baseline status and comparison"
        )

        # List
        baseline_subparsers.add_parser(
            "list",
            help="List available baselines"
        )

    def _add_mcp_parser(self, subparsers):
        """Add the MCP server subcommand parser."""
        mcp_parser = subparsers.add_parser(
            "mcp",
            help="MCP server for agent integration"
        )

        mcp_subparsers = mcp_parser.add_subparsers(
            dest="mcp_action",
            help="MCP actions"
        )

        # Serve
        serve_parser = mcp_subparsers.add_parser(
            "serve",
            help="Start MCP server"
        )
        serve_parser.add_argument(
            "--transport",
            choices=["stdio", "sse", "websocket"],
            default="stdio",
            help="Transport protocol (default: stdio)"
        )
        serve_parser.add_argument(
            "--host",
            default="localhost",
            help="Host to bind to (for sse/websocket)"
        )
        serve_parser.add_argument(
            "--port",
            type=int,
            default=8080,
            help="Port to bind to (for sse/websocket)"
        )

    def _add_license_parser(self, subparsers):
        """Add the license validation subcommand parser."""
        license_parser = subparsers.add_parser(
            "license",
            help="License validation and compliance checking"
        )

        license_subparsers = license_parser.add_subparsers(
            dest="license_action",
            help="License actions"
        )

        # Validate
        validate_parser = license_subparsers.add_parser(
            "validate",
            help="Validate project license compliance"
        )
        validate_parser.add_argument(
            "path",
            nargs="?",
            default=".",
            help="Project path to validate (default: current directory)"
        )
        validate_parser.add_argument(
            "--format", "-f",
            choices=["text", "json"],
            default="text",
            help="Output format (default: text)"
        )

        # Check
        check_parser = license_subparsers.add_parser(
            "check",
            help="Quick license compliance check"
        )
        check_parser.add_argument(
            "path",
            nargs="?",
            default=".",
            help="Project path to check"
        )

        # Memory
        memory_parser = license_subparsers.add_parser(
            "memory",
            help="Manage license validation memory"
        )
        memory_parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear license validation memory"
        )
        memory_parser.add_argument(
            "--show",
            action="store_true",
            help="Show license validation memory contents"
        )

    def run(self, args: Optional[List[str]] = None) -> int:
        """Run the CLI application."""
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)

        # Configure logging
        if parsed_args.verbose:
            logging.getLogger().setLevel(logging.INFO)
            logger.info("Verbose logging enabled")

        # Perform license validation first (unless skipped or for license commands)
        if (not parsed_args.skip_license_check and
            parsed_args.command not in ["license", None] and
            LICENSE_VALIDATION_AVAILABLE):

            license_exit_code = self._perform_license_validation(Path.cwd(), parsed_args.verbose)
            if license_exit_code != 0:
                return license_exit_code

        # Handle missing command
        if not parsed_args.command:
            parser.print_help()
            return 0

        try:
            # Delegate to focused command handlers
            if parsed_args.command == "scan":
                return self.scan_handler.handle(parsed_args)
            elif parsed_args.command == "scan-diff":
                return self.scan_diff_handler.handle(parsed_args)
            elif parsed_args.command == "explain":
                return self.explain_handler.handle(parsed_args)
            elif parsed_args.command == "autofix":
                return self.autofix_handler.handle(parsed_args)
            elif parsed_args.command == "baseline":
                return self.baseline_handler.handle(parsed_args)
            elif parsed_args.command == "mcp":
                return self.mcp_handler.handle(parsed_args)
            elif parsed_args.command == "license":
                return self.license_handler.handle(parsed_args)
            else:
                parser.error(f"Unknown command: {parsed_args.command}")
                return ExitCode.CONFIGURATION_ERROR

        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return ExitCode.USER_INTERRUPTED
        except ImportError as e:
            logger.error(f"Configuration error - missing dependency: {e}")
            if parsed_args.verbose:
                import traceback
                traceback.print_exc()
            return ExitCode.CONFIGURATION_ERROR
        except Exception as e:
            logger.error(f"Runtime error: {e}")
            if parsed_args.verbose:
                import traceback
                traceback.print_exc()
            return ExitCode.RUNTIME_ERROR


    def _perform_license_validation(self, project_path: Path, verbose: bool) -> int:
        """Perform license validation and return exit code."""
        if not self.license_validator:
            return ExitCode.SUCCESS  # Skip if not available

        try:
            if verbose:
                print("Performing license validation...", file=sys.stderr)

            report = self.license_validator.validate_license(project_path)

            if report.validation_result != LicenseValidationResult.VALID:
                print(f"{ValidationMessages.LICENSE_VALIDATION_FAILED}: {report.validation_result.value}", file=sys.stderr)
                if verbose and report.errors:
                    for error in report.errors[:2]:  # Show first 2 errors
                        print(f"  - {error.description}", file=sys.stderr)
                print(ValidationMessages.USE_LICENSE_VALIDATE_CMD, file=sys.stderr)
                return report.exit_code

            if verbose:
                print(ValidationMessages.LICENSE_VALIDATION_PASSED, file=sys.stderr)
            return ExitCode.SUCCESS

        except Exception as e:
            if verbose:
                print(f"License validation error: {e}", file=sys.stderr)
            return ExitCode.LICENSE_ERROR



def main():
    """Main entry point."""
    cli = ConnascenceCLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())
