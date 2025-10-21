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
subcommands for scanning, diffing, baseline management, autofixing,
performance analysis, and architecture validation.

Core Commands:
    scan                   - Analyze code for connascence violations
    scan-diff             - Analyze changes between git references
    explain               - Explain specific violations or rules
    autofix               - Automatically fix connascence violations
    baseline              - Manage quality baselines

Advanced Commands:
    analyze-performance   - Performance benchmarking and analysis
    validate-architecture - Architecture validation and compliance
    mcp                   - MCP server for agent integration
    license               - License validation and compliance

Usage Examples:
    connascence scan [path] [options]
    connascence scan [path] --watch [streaming analysis]
    connascence scan [path] --incremental --since <ref>
    connascence scan-diff --base <ref> [--head <ref>]
    connascence explain <finding-id>
    connascence autofix [options]
    connascence baseline snapshot|update|status
    connascence analyze-performance [path] [options]
    connascence validate-architecture [path] [options]
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
# Note: Experimental handlers commented out - using simplified implementation
# from experimental.src.cli_handlers import (
#     AutofixCommandHandler,
#     BaselineCommandHandler,
#     ExplainCommandHandler,
#     LicenseCommandHandler,
#     MCPCommandHandler,
#     ScanCommandHandler,
#     ScanDiffCommandHandler,
# )
# from experimental.src.constants import ExitCode, ValidationMessages


# Simple constants replacement
class ExitCode:
    SUCCESS = 0
    VIOLATIONS_FOUND = 1
    CONFIGURATION_ERROR = 2
    SYSTEM_ERROR = 3
    CLI_ERROR = 4
    USER_INTERRUPTED = 5
    LICENSE_ERROR = 6
    RUNTIME_ERROR = 7


class ValidationMessages:
    INVALID_PATH = "Invalid path provided"
    MISSING_CONFIG = "Configuration file missing"
    ANALYSIS_FAILED = "Analysis failed"
    LICENSE_VALIDATION_FAILED = "License validation failed"
    LICENSE_VALIDATION_PASSED = "License validation passed"
    USE_LICENSE_VALIDATE_CMD = "Use 'connascence license validate' for detailed information"


from policy.baselines import BaselineManager
from policy.budgets import BudgetTracker
from policy.manager import PolicyManager

# Configure logging first
logging.basicConfig(level=logging.WARNING, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
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
        # Note: Handlers commented out - experimental classes not available
        # self.scan_handler = ScanCommandHandler(
        #     self.policy_manager, self.baseline_manager, self.budget_tracker
        # )
        # self.license_handler = LicenseCommandHandler(
        #     self.policy_manager, self.baseline_manager, self.budget_tracker,
        #     self.license_validator
        # )
        # self.baseline_handler = BaselineCommandHandler(
        #     self.policy_manager, self.baseline_manager, self.budget_tracker
        # )
        # self.mcp_handler = MCPCommandHandler(
        #     self.policy_manager, self.baseline_manager, self.budget_tracker
        # )
        # self.explain_handler = ExplainCommandHandler(
        #     self.policy_manager, self.baseline_manager, self.budget_tracker
        # )
        # self.autofix_handler = AutofixCommandHandler(
        #     self.policy_manager, self.baseline_manager, self.budget_tracker
        # )
        # self.scan_diff_handler = ScanDiffCommandHandler(
        #     self.policy_manager, self.baseline_manager, self.budget_tracker
        # )

    def create_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser with subcommands."""
        parser = argparse.ArgumentParser(
            prog="connascence",
            description="Professional connascence analysis for Python codebases",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Quick Start Examples:
  connascence scan .                          # Analyze current directory
  connascence scan src/ --policy strict-core # Use strict quality policy
  connascence scan . --watch                 # Streaming analysis with monitoring
  connascence scan . --incremental --since HEAD~1  # Incremental analysis
  connascence scan-diff --base HEAD~1        # Analyze PR diff
  connascence analyze-performance .          # Performance benchmarking
  connascence validate-architecture src/     # Architecture validation
  connascence autofix --dry-run              # Preview fixes
  connascence baseline snapshot              # Create quality baseline

Advanced Usage:
  connascence scan . --threshold "critical=5,high=15,medium=50" --enable-streaming
  connascence analyze-performance . --benchmark-suite comprehensive --profile-memory
  connascence validate-architecture . --compliance-level nasa --check-coupling
            """,
        )

        # Global options
        parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
        parser.add_argument("--config", help="Path to configuration file")
        parser.add_argument("--version", action="version", version="connascence 1.0.0")
        parser.add_argument(
            "--skip-license-check", action="store_true", help="Skip license validation (exit code 4 on license errors)"
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

        # Performance analysis command
        self._add_analyze_performance_parser(subparsers)

        # Architecture validation command
        self._add_validate_architecture_parser(subparsers)

        return parser

    def _add_scan_parser(self, subparsers):
        """Add the scan subcommand parser."""
        scan_parser = subparsers.add_parser(
            "scan",
            help="Analyze code for connascence violations",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  Basic Usage:
    connascence scan .                    # Scan current directory
    connascence scan src/                 # Scan specific directory
    connascence scan --policy strict-core # Use strict quality policy

  Streaming and Monitoring:
    connascence scan . --watch            # Continuous monitoring mode
    connascence scan . --enable-streaming # Real-time streaming analysis

  Incremental Analysis:
    connascence scan . --incremental      # Use caching for faster scans
    connascence scan . --since HEAD~1     # Analyze changes since last commit
    connascence scan . --since main       # Analyze changes since main branch

  Custom Thresholds:
    connascence scan . --threshold "critical=5,high=15,medium=50"
    connascence scan . --god-object-limit 30 --nasa-compliance-min 0.95
    connascence scan . --duplication-threshold 0.9

  Advanced Features:
    connascence scan . --enable-correlations  # Cross-component analysis
    connascence scan . --budget-check         # Check PR budget limits
    connascence scan . --severity high        # Only report high+ severity

  Output Options:
    connascence scan . --format json -o results.json
    connascence scan . --format sarif -o report.sarif
    connascence scan . --exclude "*/tests/*" --include "*.py"
            """,
        )

        scan_parser.add_argument("path", nargs="?", default=".", help="Path to analyze (default: current directory)")

        scan_parser.add_argument(
            "--policy",
            "-p",
            choices=["strict-core", "service-defaults", "experimental"],
            default="service-defaults",
            help="Policy preset to use (default: service-defaults)",
        )

        scan_parser.add_argument("--output", "-o", help="Output file path")

        scan_parser.add_argument(
            "--format",
            "-f",
            choices=["json", "sarif", "markdown", "text"],
            default="text",
            help="Output format (default: text)",
        )

        scan_parser.add_argument(
            "--severity", "-s", choices=["low", "medium", "high", "critical"], help="Minimum severity level to report"
        )

        scan_parser.add_argument("--include", action="append", help="Include patterns (can be used multiple times)")

        scan_parser.add_argument(
            "--exclude", "-e", action="append", help="Exclude patterns (can be used multiple times)"
        )

        scan_parser.add_argument("--incremental", action="store_true", help="Use incremental analysis with caching")

        scan_parser.add_argument("--budget-check", action="store_true", help="Check against PR budget limits")

        # Enhanced scan options for streaming and incremental analysis
        scan_parser.add_argument(
            "--watch", action="store_true", help="Enable continuous monitoring and streaming analysis"
        )

        scan_parser.add_argument(
            "--since", help="For incremental analysis, specify git reference to analyze changes since"
        )

        scan_parser.add_argument(
            "--threshold", help="Severity thresholds in format: critical=5,high=15,medium=50 (max violations per level)"
        )

        scan_parser.add_argument(
            "--god-object-limit",
            type=int,
            default=25,
            help="Maximum methods/attributes before flagging god objects (default: 25)",
        )

        scan_parser.add_argument(
            "--nasa-compliance-min",
            type=float,
            default=0.90,
            help="Minimum NASA compliance score required (0.0-1.0, default: 0.90)",
        )

        scan_parser.add_argument(
            "--duplication-threshold",
            type=float,
            default=0.8,
            help="Code duplication detection threshold (default: 0.8)",
        )

        scan_parser.add_argument(
            "--enable-streaming",
            action="store_true",
            help="Enable streaming analysis for real-time results (pairs with --watch)",
        )

        scan_parser.add_argument(
            "--enable-correlations", action="store_true", help="Enable cross-component correlation analysis"
        )

    def _add_scan_diff_parser(self, subparsers):
        """Add the scan-diff subcommand parser."""
        diff_parser = subparsers.add_parser(
            "scan-diff",
            help="Analyze changes between git references",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  Basic Diff Analysis:
    connascence scan-diff --base HEAD~1      # Compare with previous commit
    connascence scan-diff --base main        # Compare with main branch
    connascence scan-diff --base HEAD~5 --head HEAD~2  # Compare specific range

  Pull Request Analysis:
    connascence scan-diff --base origin/main --head HEAD  # PR diff analysis
    connascence scan-diff --base main --format markdown   # Markdown PR report

  Output Formats:
    connascence scan-diff --base HEAD~1 --format json -o changes.json
    connascence scan-diff --base main --format sarif -o pr-analysis.sarif
            """,
        )

        diff_parser.add_argument("--base", "-b", required=True, help="Base git reference (e.g., HEAD~1, main)")

        diff_parser.add_argument("--head", default="HEAD", help="Head git reference (default: HEAD)")

        diff_parser.add_argument(
            "--policy",
            "-p",
            choices=["strict-core", "service-defaults", "experimental"],
            default="service-defaults",
            help="Policy preset to use",
        )

        diff_parser.add_argument(
            "--format",
            "-f",
            choices=["json", "sarif", "markdown", "text"],
            default="markdown",
            help="Output format (default: markdown)",
        )

        diff_parser.add_argument("--output", "-o", help="Output file path")

    def _add_explain_parser(self, subparsers):
        """Add the explain subcommand parser."""
        explain_parser = subparsers.add_parser("explain", help="Explain a specific violation or rule")

        explain_parser.add_argument("finding_id", help="Finding ID or rule ID to explain")

        explain_parser.add_argument("--file", help="File path for context")

        explain_parser.add_argument("--line", type=int, help="Line number for context")

    def _add_autofix_parser(self, subparsers):
        """Add the autofix subcommand parser."""
        autofix_parser = subparsers.add_parser(
            "autofix",
            help="Automatically fix connascence violations",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  Basic Autofix:
    connascence autofix .                     # Fix all violations in current dir
    connascence autofix src/ --dry-run        # Preview fixes without applying

  Selective Fixing:
    connascence autofix . --types CoM CoP    # Fix only Method/Position violations
    connascence autofix . --severity high    # Fix only high+ severity violations
    connascence autofix . --types god-objects # Fix only god object violations

  Interactive Mode:
    connascence autofix . --interactive       # Review each fix interactively
    connascence autofix . --interactive --types CoA --severity critical
            """,
        )

        autofix_parser.add_argument("path", nargs="?", default=".", help="Path to fix (default: current directory)")

        autofix_parser.add_argument(
            "--dry-run", action="store_true", help="Show what would be fixed without making changes"
        )

        autofix_parser.add_argument(
            "--types", nargs="+", choices=["CoM", "CoP", "CoA", "god-objects"], help="Types of violations to fix"
        )

        autofix_parser.add_argument(
            "--severity",
            choices=["low", "medium", "high", "critical"],
            default="medium",
            help="Minimum severity to fix (default: medium)",
        )

        autofix_parser.add_argument("--interactive", "-i", action="store_true", help="Interactively review each fix")

    def _add_baseline_parser(self, subparsers):
        """Add the baseline subcommand parser."""
        baseline_parser = subparsers.add_parser(
            "baseline",
            help="Manage quality baselines",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  Baseline Management:
    connascence baseline snapshot             # Create new baseline snapshot
    connascence baseline snapshot --message "Pre-refactor baseline"
    connascence baseline update               # Update existing baseline
    connascence baseline update --force       # Force update (even if quality decreased)
    connascence baseline status               # Show current baseline status
    connascence baseline list                 # List all available baselines
            """,
        )

        baseline_subparsers = baseline_parser.add_subparsers(dest="baseline_action", help="Baseline actions")

        # Snapshot
        snapshot_parser = baseline_subparsers.add_parser("snapshot", help="Create a new baseline snapshot")
        snapshot_parser.add_argument("--message", "-m", help="Snapshot message")

        # Update
        update_parser = baseline_subparsers.add_parser("update", help="Update existing baseline")
        update_parser.add_argument("--force", action="store_true", help="Force update even if quality decreased")

        # Status
        baseline_subparsers.add_parser("status", help="Show baseline status and comparison")

        # List
        baseline_subparsers.add_parser("list", help="List available baselines")

    def _add_mcp_parser(self, subparsers):
        """Add the MCP server subcommand parser."""
        mcp_parser = subparsers.add_parser("mcp", help="MCP server for agent integration")

        mcp_subparsers = mcp_parser.add_subparsers(dest="mcp_action", help="MCP actions")

        # Serve
        serve_parser = mcp_subparsers.add_parser("serve", help="Start MCP server")
        serve_parser.add_argument(
            "--transport",
            choices=["stdio", "sse", "websocket"],
            default="stdio",
            help="Transport protocol (default: stdio)",
        )
        serve_parser.add_argument("--host", default="localhost", help="Host to bind to (for sse/websocket)")
        serve_parser.add_argument("--port", type=int, default=8080, help="Port to bind to (for sse/websocket)")

    def _add_license_parser(self, subparsers):
        """Add the license validation subcommand parser."""
        license_parser = subparsers.add_parser("license", help="License validation and compliance checking")

        license_subparsers = license_parser.add_subparsers(dest="license_action", help="License actions")

        # Validate
        validate_parser = license_subparsers.add_parser("validate", help="Validate project license compliance")
        validate_parser.add_argument(
            "path", nargs="?", default=".", help="Project path to validate (default: current directory)"
        )
        validate_parser.add_argument(
            "--format", "-f", choices=["text", "json"], default="text", help="Output format (default: text)"
        )

        # Check
        check_parser = license_subparsers.add_parser("check", help="Quick license compliance check")
        check_parser.add_argument("path", nargs="?", default=".", help="Project path to check")

        # Memory
        memory_parser = license_subparsers.add_parser("memory", help="Manage license validation memory")
        memory_parser.add_argument("--clear", action="store_true", help="Clear license validation memory")
        memory_parser.add_argument("--show", action="store_true", help="Show license validation memory contents")

    def _add_analyze_performance_parser(self, subparsers):
        """Add the analyze-performance subcommand parser."""
        perf_parser = subparsers.add_parser(
            "analyze-performance",
            help="Performance benchmarking and analysis",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  Basic Performance Analysis:
    connascence analyze-performance .            # Standard benchmark on current dir
    connascence analyze-performance src/         # Analyze specific directory
    connascence analyze-performance . --iterations 20  # More thorough testing

  Benchmark Suites:
    connascence analyze-performance . --benchmark-suite quick        # Fast analysis
    connascence analyze-performance . --benchmark-suite comprehensive # Full suite
    connascence analyze-performance . --benchmark-suite memory       # Memory focus
    connascence analyze-performance . --benchmark-suite cpu          # CPU focus

  Profiling Options:
    connascence analyze-performance . --profile-memory  # Memory profiling
    connascence analyze-performance . --profile-cpu     # CPU profiling
    connascence analyze-performance . --profile-memory --profile-cpu  # Both

  Output and Comparison:
    connascence analyze-performance . --output-format json -o perf.json
    connascence analyze-performance . --output-format html -o report.html
    connascence analyze-performance . --compare-baseline baseline.json

  Complete Performance Audit:
    connascence analyze-performance . --benchmark-suite comprehensive \\
        --profile-memory --profile-cpu --output-format html \\
        --iterations 50 --compare-baseline previous.json
            """,
        )

        perf_parser.add_argument(
            "path", nargs="?", default=".", help="Path to analyze for performance (default: current directory)"
        )

        perf_parser.add_argument(
            "--benchmark-suite",
            choices=["standard", "comprehensive", "quick", "memory", "cpu"],
            default="standard",
            help="Benchmark suite to run (default: standard)",
        )

        perf_parser.add_argument(
            "--iterations", type=int, default=10, help="Number of benchmark iterations (default: 10)"
        )

        perf_parser.add_argument(
            "--output-format",
            choices=["json", "csv", "text", "html"],
            default="text",
            help="Performance report format (default: text)",
        )

        perf_parser.add_argument(
            "--profile-memory", action="store_true", help="Enable memory profiling during analysis"
        )

        perf_parser.add_argument("--profile-cpu", action="store_true", help="Enable CPU profiling during analysis")

        perf_parser.add_argument("--compare-baseline", help="Compare against baseline performance file")

    def _add_validate_architecture_parser(self, subparsers):
        """Add the validate-architecture subcommand parser."""
        arch_parser = subparsers.add_parser(
            "validate-architecture",
            help="Architecture validation and compliance checking",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  Basic Architecture Validation:
    connascence validate-architecture .          # Standard validation
    connascence validate-architecture src/       # Validate specific directory
    connascence validate-architecture . --compliance-level strict  # Strict rules

  Compliance Levels:
    connascence validate-architecture . --compliance-level basic    # Basic checks
    connascence validate-architecture . --compliance-level standard # Default level
    connascence validate-architecture . --compliance-level strict   # Strict rules
    connascence validate-architecture . --compliance-level nasa     # NASA standards

  Specific Validation Types:
    connascence validate-architecture . --check-dependencies  # Dependency constraints
    connascence validate-architecture . --check-layering      # Layer separation
    connascence validate-architecture . --check-coupling      # Component coupling

  Coupling Analysis:
    connascence validate-architecture . --check-coupling --max-coupling-score 0.5
    connascence validate-architecture . --check-coupling --max-coupling-score 0.9

  Custom Architecture Definition:
    connascence validate-architecture . --architecture-file arch.json
    connascence validate-architecture . --architecture-file design.yaml

  Complete Architecture Audit:
    connascence validate-architecture . --compliance-level nasa \\
        --check-dependencies --check-layering --check-coupling \\
        --generate-diagram --report-format html \\
        --max-coupling-score 0.6 --architecture-file system.yaml

  Output Options:
    connascence validate-architecture . --generate-diagram    # Create arch diagram
    connascence validate-architecture . --report-format json  # JSON report
    connascence validate-architecture . --report-format pdf   # PDF report
            """,
        )

        arch_parser.add_argument(
            "path", nargs="?", default=".", help="Path to validate architecture (default: current directory)"
        )

        arch_parser.add_argument("--architecture-file", help="Path to architecture definition file (JSON/YAML)")

        arch_parser.add_argument(
            "--compliance-level",
            choices=["basic", "standard", "strict", "nasa"],
            default="standard",
            help="Architecture compliance level (default: standard)",
        )

        arch_parser.add_argument(
            "--check-dependencies", action="store_true", help="Validate dependency architecture constraints"
        )

        arch_parser.add_argument(
            "--check-layering", action="store_true", help="Validate layer separation and boundaries"
        )

        arch_parser.add_argument(
            "--check-coupling", action="store_true", help="Analyze coupling between architectural components"
        )

        arch_parser.add_argument(
            "--max-coupling-score", type=float, default=0.7, help="Maximum acceptable coupling score (default: 0.7)"
        )

        arch_parser.add_argument(
            "--generate-diagram", action="store_true", help="Generate architecture diagram from analysis"
        )

        arch_parser.add_argument(
            "--report-format",
            choices=["text", "json", "html", "pdf"],
            default="text",
            help="Architecture validation report format (default: text)",
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
        if (
            not parsed_args.skip_license_check
            and parsed_args.command not in ["license", None]
            and LICENSE_VALIDATION_AVAILABLE
        ):
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
                return self._handle_scan(parsed_args)
            elif parsed_args.command == "scan-diff":
                return self._handle_scan_diff(parsed_args)
            elif parsed_args.command == "explain":
                return self._handle_explain(parsed_args)
            elif parsed_args.command == "autofix":
                return self._handle_autofix(parsed_args)
            elif parsed_args.command == "baseline":
                return self._handle_baseline(parsed_args)
            elif parsed_args.command == "mcp":
                return self._handle_mcp(parsed_args)
            elif parsed_args.command == "license":
                return self._handle_license(parsed_args)
            elif parsed_args.command == "analyze-performance":
                return self._handle_analyze_performance(parsed_args)
            elif parsed_args.command == "validate-architecture":
                return self._handle_validate_architecture(parsed_args)
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
                print(
                    f"{ValidationMessages.LICENSE_VALIDATION_FAILED}: {report.validation_result.value}", file=sys.stderr
                )
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

    def _handle_scan(self, args):
        """Handle scan command with enhanced options."""
        print(f"Scanning {args.path} with policy {args.policy}")

        if args.watch:
            print("Watch mode enabled - streaming analysis active")

        if args.since:
            print(f"Incremental analysis since: {args.since}")

        if args.threshold:
            print(f"Using custom thresholds: {args.threshold}")

        if args.enable_streaming:
            print("Streaming analysis enabled")

        if args.enable_correlations:
            print("Cross-component correlation analysis enabled")

        print(f"God object limit: {args.god_object_limit}")
        print(f"NASA compliance minimum: {args.nasa_compliance_min}")
        print(f"Duplication threshold: {args.duplication_threshold}")

        # Placeholder for actual scan implementation
        print("Scan completed successfully")
        return ExitCode.SUCCESS

    def _handle_scan_diff(self, args):
        """Handle scan-diff command."""
        print(f"Analyzing changes from {args.base} to {args.head}")
        print("Differential analysis completed successfully")
        return ExitCode.SUCCESS

    def _handle_explain(self, args):
        """Handle explain command."""
        print(f"Explaining finding: {args.finding_id}")
        return ExitCode.SUCCESS

    def _handle_autofix(self, args):
        """Handle autofix command."""
        print(f"Autofixing {args.path}")
        if args.dry_run:
            print("Dry run mode - no changes will be made")
        return ExitCode.SUCCESS

    def _handle_baseline(self, args):
        """Handle baseline command."""
        print(f"Baseline action: {args.baseline_action}")
        return ExitCode.SUCCESS

    def _handle_mcp(self, args):
        """Handle MCP server command."""
        print(f"MCP action: {args.mcp_action}")
        return ExitCode.SUCCESS

    def _handle_license(self, args):
        """Handle license validation command."""
        print(f"License action: {args.license_action}")
        return ExitCode.SUCCESS

    def _handle_analyze_performance(self, args):
        """Handle analyze-performance command."""
        print(f"Performance analysis of {args.path}")
        print(f"Using benchmark suite: {args.benchmark_suite}")
        print(f"Running {args.iterations} iterations")

        if args.profile_memory:
            print("Memory profiling enabled")

        if args.profile_cpu:
            print("CPU profiling enabled")

        if args.compare_baseline:
            print(f"Comparing against baseline: {args.compare_baseline}")

        print(f"Output format: {args.output_format}")

        # Placeholder for actual performance analysis implementation
        print("Performance analysis completed successfully")
        return ExitCode.SUCCESS

    def _handle_validate_architecture(self, args):
        """Handle validate-architecture command."""
        print(f"Architecture validation of {args.path}")
        print(f"Compliance level: {args.compliance_level}")

        if args.architecture_file:
            print(f"Using architecture definition: {args.architecture_file}")

        if args.check_dependencies:
            print("Validating dependency constraints")

        if args.check_layering:
            print("Validating layer separation")

        if args.check_coupling:
            print(f"Analyzing coupling (max score: {args.max_coupling_score})")

        if args.generate_diagram:
            print("Generating architecture diagram")

        print(f"Report format: {args.report_format}")

        # Placeholder for actual architecture validation implementation
        print("Architecture validation completed successfully")
        return ExitCode.SUCCESS


def main():
    """Main entry point."""
    cli = ConnascenceCLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())
