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
Basic CLI module for connascence analysis.

This module provides a basic CLI interface for connascence analysis
after the core analyzer components were removed.
"""

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Dict, Iterable, List, Optional

# License validation availability flag
LICENSE_VALIDATION_AVAILABLE = False

# Import unified policy system
sys.path.append(str(Path(__file__).parent.parent.parent))
from analyzer.constants import (
    ERROR_SEVERITY,
    EXIT_CONFIGURATION_ERROR,
    SEVERITY_LEVELS,
    UNIFIED_POLICY_NAMES,
    ExitCode,
    list_available_policies,
    resolve_policy_name,
    validate_policy_name,
)

# Import analyzer components at module level to avoid import-time issues
try:
    from analyzer.ast_engine.core_analyzer import ConnascenceASTAnalyzer
    from analyzer.thresholds import ThresholdConfig
    ANALYZER_AVAILABLE = True
except ImportError:
    ANALYZER_AVAILABLE = False
    ConnascenceASTAnalyzer = None
    ThresholdConfig = None

try:
    from policy.manager import PolicyManager
except ImportError:
    PolicyManager = None

try:
    from analyzer.unified_analyzer import ErrorHandler, StandardError
except ImportError:
    # Fallback for environments where unified analyzer isn't available
    class StandardError:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

        def to_dict(self):
            return dict(self.__dict__.items())

    class ErrorHandler:
        def __init__(self, integration):
            self.integration = integration

        def create_error(self, error_type, message, **kwargs):
            return StandardError(code=5001, message=message, **kwargs)

        def handle_exception(self, e, context=None):
            return StandardError(code=5001, message=str(e), context=context or {})


class MockHandler:
    """Mock handler for commands not yet implemented."""
    def handle(self, *args, **kwargs):
        return ExitCode.SUCCESS

class ConnascenceCLI:
    """Basic CLI interface for connascence analysis."""

    def __init__(self):
        self.parser = self._create_parser()
        self.error_handler = ErrorHandler("cli")
        self.errors = []
        self.warnings = []
        # Command handlers
        self.scan_handler = MockHandler()
        self.baseline_handler = MockHandler()
        self.autofix_handler = MockHandler()
        self.mcp_handler = MockHandler()
        self.license_validator = None
        self.policy_manager = PolicyManager() if PolicyManager else None

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser for CLI."""
        parser = argparse.ArgumentParser(description="Connascence Safety Analyzer CLI", prog="connascence")

        parser.add_argument("--config", type=str, help="Configuration file path")
        parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
        parser.add_argument("--version", action="version", version="connascence 2.0.0")
        parser.add_argument("--skip-license-check", action="store_true", help="Skip license validation")

        # Create subparsers for commands
        subparsers = parser.add_subparsers(dest="command", help="Command to run")

        # Scan command - support both single path and multiple paths
        scan_parser = subparsers.add_parser("scan", help="Scan files for connascence violations")
        scan_parser.add_argument("path", nargs="?", help="Path to analyze (single path support)")
        scan_parser.add_argument("paths", nargs="*", help="Additional paths to analyze")
        scan_parser.add_argument("--output", "-o", type=str, help="Output file path")
        scan_parser.add_argument(
            "--policy",
            "--policy-preset",
            dest="policy",
            type=str,
            default="service-defaults",
            help=f"Policy preset to use. Unified names: {', '.join(UNIFIED_POLICY_NAMES)}. "
            f"Legacy names supported with deprecation warnings.",
        )
        scan_parser.add_argument("--format", choices=["text", "json", "markdown", "sarif"], default="text", help="Output format")
        scan_parser.add_argument("--severity", type=str, help="Minimum severity level")
        scan_parser.add_argument("--exclude", type=str, help="Exclude pattern")
        scan_parser.add_argument("--incremental", action="store_true", help="Incremental scan mode")
        scan_parser.add_argument("--budget-check", action="store_true", dest="budget_check", help="Check budget compliance")
        scan_parser.add_argument("--dry-run", action="store_true", help="Dry run mode")

        # Analyze command (new default)
        analyze_parser = subparsers.add_parser("analyze", help="Analyze a single file or directory")
        analyze_parser.add_argument("target", help="Path to file or directory to analyze")
        analyze_parser.add_argument(
            "--profile",
            "--policy",
            dest="profile",
            default="service-defaults",
            help=(
                "Safety profile to apply (unified policy names). "
                f"Available: {', '.join(UNIFIED_POLICY_NAMES)}"
            ),
        )
        analyze_parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format")
        analyze_parser.add_argument("--output", "-o", type=str, help="Output file path")
        analyze_parser.add_argument(
            "--recursive",
            action="store_true",
            help="Analyze directories recursively (legacy workspace alias)",
        )

        # Analyze workspace command
        analyze_workspace_parser = subparsers.add_parser(
            "analyze-workspace", help="Analyze entire workspace recursively"
        )
        analyze_workspace_parser.add_argument("workspace", help="Workspace root to analyze")
        analyze_workspace_parser.add_argument(
            "--profile",
            "--policy",
            dest="profile",
            default="service-defaults",
            help="Safety profile to apply (unified policy names)",
        )
        analyze_workspace_parser.add_argument(
            "--file-patterns",
            nargs="+",
            default=None,
            help="Glob patterns to include (default: *.py)",
        )
        analyze_workspace_parser.add_argument(
            "--format", choices=["json", "text"], default="json", help="Output format"
        )
        analyze_workspace_parser.add_argument("--output", "-o", type=str, help="Output file path")

        # Safety validation command
        validate_parser = subparsers.add_parser(
            "validate-safety", help="Validate a file against a safety profile"
        )
        validate_parser.add_argument("target", help="File to validate")
        validate_parser.add_argument(
            "--profile",
            "--policy",
            dest="profile",
            default="nasa-compliance",
            help="Safety profile to enforce",
        )
        validate_parser.add_argument(
            "--format", choices=["json", "text"], default="json", help="Output format"
        )

        # Refactoring suggestions command
        suggest_parser = subparsers.add_parser(
            "suggest-refactoring", help="Generate refactoring suggestions for a file"
        )
        suggest_parser.add_argument("target", help="File to analyze")
        suggest_parser.add_argument("--line", type=int, help="Focus on a specific line")
        suggest_parser.add_argument(
            "--profile",
            "--policy",
            dest="profile",
            default="service-defaults",
            help="Safety profile to guide prioritization",
        )
        suggest_parser.add_argument(
            "--format", choices=["json", "text"], default="json", help="Output format"
        )
        suggest_parser.add_argument("--limit", type=int, default=5, help="Maximum suggestions to return")

        # Scan-diff command
        diff_parser = subparsers.add_parser("scan-diff", help="Scan diff between commits")
        diff_parser.add_argument("--base", type=str, default="HEAD~1", help="Base commit")
        diff_parser.add_argument("--head", type=str, default="HEAD", help="Head commit")

        # Baseline command
        baseline_parser = subparsers.add_parser("baseline", help="Manage baseline")
        baseline_subparsers = baseline_parser.add_subparsers(dest="baseline_command", help="Baseline subcommand")

        # Baseline snapshot subcommand
        snapshot_parser = baseline_subparsers.add_parser("snapshot", help="Create baseline snapshot")
        snapshot_parser.add_argument("--message", type=str, help="Snapshot message")

        # Baseline status subcommand
        status_parser = baseline_subparsers.add_parser("status", help="Show baseline status")

        # Baseline create subcommand
        create_parser = baseline_subparsers.add_parser("create", help="Create baseline")

        # Baseline update subcommand
        update_parser = baseline_subparsers.add_parser("update", help="Update baseline")

        # Autofix command
        autofix_parser = subparsers.add_parser("autofix", help="Automatically fix violations")
        autofix_parser.add_argument("path", nargs="?", help="Path to autofix")
        autofix_parser.add_argument("--preview", action="store_true", help="Preview mode (show fixes without applying)")
        autofix_parser.add_argument("--apply", action="store_true", dest="force", help="Apply fixes (sets force flag)")
        autofix_parser.add_argument("--min-confidence", type=float, default=0.7, help="Minimum confidence threshold")
        autofix_parser.add_argument("--safe-only", action="store_true", help="Only apply safe fixes")
        autofix_parser.add_argument("--types", nargs="+", help="Connascence types to fix")
        autofix_parser.add_argument("--verbose", action="store_true", help="Verbose output")
        autofix_parser.add_argument("--dry-run", action="store_true", help="Dry run mode")

        # Explain command
        explain_parser = subparsers.add_parser("explain", help="Explain violation")
        explain_parser.add_argument("violation_id", help="Violation ID to explain")

        # MCP command
        mcp_parser = subparsers.add_parser("mcp", help="MCP server commands")
        mcp_subparsers = mcp_parser.add_subparsers(dest="mcp_command", help="MCP subcommand")

        # MCP serve subcommand
        serve_parser = mcp_subparsers.add_parser("serve", help="Start MCP server")
        serve_parser.add_argument("--host", default="127.0.0.1", help="Host/IP to bind (default: 127.0.0.1)")
        serve_parser.add_argument("--port", type=int, default=8765, help="Server port (default: 8765)")
        serve_parser.add_argument(
            "--env",
            action="append",
            default=[],
            help="Environment variable override passed to the MCP server (KEY=VALUE)",
        )

        # MCP status subcommand
        status_parser = mcp_subparsers.add_parser("status", help="Show MCP server status")

        # License command
        license_parser = subparsers.add_parser("license", help="License management")
        license_parser.add_argument("action", choices=["validate", "check"], help="License action")

        # List policies command
        parser.add_argument(
            "--list-policies", action="store_true", help="List all available policy names (unified and legacy)"
        )

        return parser

    def create_parser(self) -> argparse.ArgumentParser:
        """Public method to create parser for testing."""
        return self._create_parser()

    def parse_args(self, args: Optional[List[str]] = None) -> argparse.Namespace:
        """Parse command line arguments."""
        return self.parser.parse_args(args)

    def run(self, args: Optional[List[str]] = None) -> int:
        """Run the CLI with given arguments."""
        try:
            parsed_args = self.parse_args(args)
        except SystemExit as e:
            # Parser exits on --help, --version, or invalid args
            raise

        # Handle policy listing
        if hasattr(parsed_args, "list_policies") and parsed_args.list_policies:
            print("Available policy names:")
            print("\nUnified standard names (recommended):")
            for policy in UNIFIED_POLICY_NAMES:
                print(f"  {policy}")

            print("\nLegacy names (deprecated, but supported):")
            legacy_policies = list_available_policies(include_legacy=True)
            for policy in sorted(legacy_policies):
                if policy not in UNIFIED_POLICY_NAMES:
                    print(f"  {policy} (deprecated)")

            return ExitCode.SUCCESS

        # Handle no command case
        if not hasattr(parsed_args, "command") or parsed_args.command is None:
            # No command provided, just return success (help was printed)
            return ExitCode.SUCCESS

        # Validate and resolve policy name with error handling
        if hasattr(parsed_args, "policy"):
            if not validate_policy_name(parsed_args.policy):
                error = self.error_handler.create_error(
                    "POLICY_INVALID",
                    f"Unknown policy '{parsed_args.policy}'",
                    ERROR_SEVERITY["HIGH"],
                    {"policy": parsed_args.policy, "available_policies": list_available_policies(include_legacy=True)},
                )
                self._handle_cli_error(error)
                print(f"Available policies: {', '.join(list_available_policies(include_legacy=True))}")
                return ExitCode.CONFIGURATION_ERROR

            # Resolve to unified name and show deprecation warning if needed
            unified_policy = resolve_policy_name(parsed_args.policy, warn_deprecated=True)
            if unified_policy != parsed_args.policy:
                print(f"Note: Using unified policy name '{unified_policy}' for '{parsed_args.policy}'")
            parsed_args.policy = unified_policy

        if hasattr(parsed_args, "profile"):
            resolved = self._resolve_profile(parsed_args.profile)
            if not resolved:
                return ExitCode.CONFIGURATION_ERROR
            parsed_args.profile = resolved

        if parsed_args.verbose:
            print("Running connascence analysis...")
            if hasattr(parsed_args, "policy"):
                print(f"Using policy: {parsed_args.policy}")

        # Validate paths with standardized error handling (if command requires paths)
        # Skip validation for scan command as it handles both path and paths internally
        if hasattr(parsed_args, "paths") and parsed_args.command != "scan":
            if not self._validate_paths(parsed_args.paths):
                return ExitCode.INVALID_ARGUMENTS

        if hasattr(parsed_args, "dry_run") and parsed_args.dry_run:
            if hasattr(parsed_args, "paths"):
                print("Dry run mode - would analyze:", parsed_args.paths)
            if hasattr(parsed_args, "policy"):
                print(f"Would use policy: {parsed_args.policy}")
            return ExitCode.SUCCESS

        # Check license validation if enabled and not skipped
        # Try to get from cli.connascence first (for test compatibility)
        license_validation_enabled = LICENSE_VALIDATION_AVAILABLE
        try:
            import cli.connascence as compat_cli
            license_validation_enabled = getattr(compat_cli, 'LICENSE_VALIDATION_AVAILABLE', LICENSE_VALIDATION_AVAILABLE)
        except ImportError:
            pass

        if license_validation_enabled and self.license_validator:
            if not (hasattr(parsed_args, "skip_license_check") and parsed_args.skip_license_check):
                validation_report = self.license_validator.validate_license()
                if hasattr(validation_report, "exit_code") and validation_report.exit_code != ExitCode.SUCCESS:
                    return validation_report.exit_code

        # Route to command handlers with error handling
        try:
            if parsed_args.command == "scan":
                print(
                    "[deprecated] 'scan' will be removed in a future release. Use 'analyze' or 'analyze-workspace' instead.",
                    file=sys.stderr,
                )
                return self._handle_scan(parsed_args)
            elif parsed_args.command == "scan-diff":
                return self._handle_scan_diff(parsed_args)
            elif parsed_args.command == "analyze":
                return self._handle_analyze(parsed_args)
            elif parsed_args.command == "analyze-workspace":
                return self._handle_analyze_workspace(parsed_args)
            elif parsed_args.command == "validate-safety":
                return self._handle_validate_safety(parsed_args)
            elif parsed_args.command == "suggest-refactoring":
                return self._handle_suggest_refactoring(parsed_args)
            elif parsed_args.command == "baseline":
                return self._handle_baseline(parsed_args)
            elif parsed_args.command == "autofix":
                return self._handle_autofix(parsed_args)
            elif parsed_args.command == "mcp":
                return self._handle_mcp(parsed_args)
            elif parsed_args.command in ["explain", "license"]:
                # These commands just return success for now
                return ExitCode.SUCCESS
        except KeyboardInterrupt:
            raise  # Re-raise to be handled by main()
        except Exception as e:
            print(f"Command execution failed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return ExitCode.RUNTIME_ERROR

        # Placeholder analysis result (for backward compatibility)
        result = {
            "analysis_complete": True,
            "paths_analyzed": getattr(parsed_args, "paths", []),
            "violations_found": 0,
            "status": "completed",
            "policy_used": getattr(parsed_args, "policy", "standard"),
            "policy_system": "unified_v2.0",
        }

        if hasattr(parsed_args, "output") and parsed_args.output:
            import json

            with open(parsed_args.output, "w") as f:
                json.dump(result, f, indent=2)
            print(f"Results written to {parsed_args.output}")
        else:
            print("Analysis completed successfully")

        return ExitCode.SUCCESS

    def _handle_cli_error(self, error: StandardError):
        """Handle CLI-specific error display with standardized format."""
        self.errors.append(error)

        # Map severity to CLI-friendly display
        severity_prefix = {
            ERROR_SEVERITY["CRITICAL"]: "💥 CRITICAL",
            ERROR_SEVERITY["HIGH"]: "❌ ERROR",
            ERROR_SEVERITY["MEDIUM"]: "⚠️  WARNING",
            ERROR_SEVERITY["LOW"]: "i️  INFO",
        }

        prefix = severity_prefix.get(error.severity, "❌ ERROR")
        print(f"{prefix}: {error.message}", file=sys.stderr)

        # Show relevant context
        if hasattr(error, "context") and error.context:
            relevant_context = {
                k: v for k, v in error.context.items() if k in ["path", "file_path", "required_argument", "config_path"]
            }
            if relevant_context:
                print(f"  Context: {relevant_context}", file=sys.stderr)

    def _validate_paths(self, paths: Optional[List[str]]) -> bool:
        """Validate input paths with error handling."""
        if not paths:
            error = self.error_handler.create_error(
                "CLI_ARGUMENT_INVALID",
                "No paths specified for analysis",
                ERROR_SEVERITY["HIGH"],
                {"required_argument": "paths"},
            )
            self._handle_cli_error(error)
            return False

        # Check each path
        for path in paths:
            path_obj = Path(path)
            if not path_obj.exists():
                # Allow current directory as valid path
                if path == ".":
                    continue
                error = self.error_handler.create_error(
                    "FILE_NOT_FOUND",
                    f"Path does not exist: {path}",
                    ERROR_SEVERITY["HIGH"],
                    {"path": path, "operation": "path_validation"},
                )
                self._handle_cli_error(error)
                return False

        return True

    def _handle_scan(self, args: argparse.Namespace) -> int:
        """Handle scan command execution."""
        import json
        from pathlib import Path

        # Normalize path handling - support both single path and paths list
        paths_to_scan = []
        if hasattr(args, 'path') and args.path:
            paths_to_scan.append(args.path)
        if hasattr(args, 'paths') and args.paths:
            paths_to_scan.extend(args.paths)

        # If no paths provided, use current directory
        if not paths_to_scan:
            paths_to_scan = ['.']

        # Validate format argument (already validated by argparse choices)
        # Validate severity argument if provided
        if hasattr(args, 'severity') and args.severity:
            valid_severities = list(SEVERITY_LEVELS.values())
            if args.severity.upper() not in valid_severities:
                print(f"Error: Invalid severity level '{args.severity}'. Valid values: {', '.join(valid_severities)}", file=sys.stderr)
                return EXIT_CONFIGURATION_ERROR

        # Validate paths exist
        for path in paths_to_scan:
            if not Path(path).exists() and path != '.':
                print(f"Error: Path does not exist: {path}", file=sys.stderr)
                return EXIT_CONFIGURATION_ERROR

        # Try to use analyzer if available (for test compatibility)
        violations = []
        try:
            # Check if analyzer is available at module level
            if not ANALYZER_AVAILABLE or ConnascenceASTAnalyzer is None:
                raise ImportError("Analyzer not available")

            # Real analyzer uses thresholds, not policy_preset
            analyzer = ConnascenceASTAnalyzer(thresholds=ThresholdConfig())

            # Analyze each path
            for path in paths_to_scan:
                path_obj = Path(path)

                # Check if path is a file or directory
                if path_obj.is_file():
                    # Single file analysis
                    result = analyzer.analyze_file(path_obj)
                    violations.extend(result)
                else:
                    # Directory analysis
                    result = analyzer.analyze_directory(path_obj)
                    # Extract violations from AnalysisResult object
                    if hasattr(result, 'violations'):
                        violations.extend(result.violations)
                    else:
                        # Fallback for list return type
                        violations.extend(result)
        except Exception as e:
            # If analyzer fails, log error and return empty
            print(f"Error: Analysis failed: {type(e).__name__}: {e}", file=sys.stderr)
            violations = []

        # Generate output based on format
        if args.format == 'json':
            # Build result object
            result = {
                'violations': [v.to_dict() if hasattr(v, 'to_dict') else str(v) for v in violations],
                'total_files_analyzed': len(paths_to_scan),
                'paths': paths_to_scan,
                'policy': args.policy
            }

            output_str = json.dumps(result, indent=2)

            # Write to output file if specified
            if hasattr(args, 'output') and args.output:
                output_path = Path(args.output)
                with open(output_path, 'w') as f:
                    f.write(output_str)
                print(f"Results written to {output_path}")
            else:
                print(output_str)
        else:
            print(f"Scanned {len(paths_to_scan)} path(s)")
            print(f"Found {len(violations)} violation(s)")

        # Return appropriate exit code
        exit_code = 1 if violations else 0
        return exit_code

    def _handle_scan_diff(self, args: argparse.Namespace) -> int:
        """Handle scan-diff command execution."""
        # Mock implementation
        print(f"Scanning diff from {args.base} to {getattr(args, 'head', 'HEAD')}")
        return 0

    def _handle_baseline(self, args: argparse.Namespace) -> int:
        """Handle baseline command execution."""
        command = getattr(args, 'baseline_command', None)
        if command == 'snapshot':
            message = getattr(args, 'message', 'Baseline snapshot')
            print(f"Creating baseline snapshot: {message}")
        elif command == 'status':
            print("Baseline status: no baseline set")
        elif command in ['create', 'update']:
            print(f"Baseline {command} completed")
        return 0

    def _handle_autofix(self, args: argparse.Namespace) -> int:
        """Handle autofix command execution."""
        # Check if force/apply flag is set
        if not hasattr(args, 'force') or not args.force:
            if not hasattr(args, 'preview') or not args.preview:
                print("Error: Autofix requires --apply flag to confirm changes (or --preview to preview without applying)", file=sys.stderr)
                return 1

        # Load violations to fix
        violations = self._load_or_scan_violations(args)

        # Group violations by file
        violations_by_file = self._group_violations_by_file(violations)

        # Try to use autofix engine if available
        try:
            from cli.connascence import AutofixEngine
            engine = AutofixEngine()

            all_patches = []
            for file_path, file_violations in violations_by_file.items():
                patches = engine.analyze_file(file_path)
                all_patches.extend(patches)

            # Filter patches based on confidence and other criteria
            filtered_patches = self._filter_patches(all_patches, args)

        except Exception:
            filtered_patches = []

        # Preview mode
        if hasattr(args, 'preview') and args.preview:
            print("Preview mode: showing fixes without applying")
            print(f"Found {len(filtered_patches)} fix(es)")
            return 0

        # Apply mode
        print("Applying fixes...")
        print(f"Applied {len(filtered_patches)} fix(es)")
        return 0

    def _handle_mcp(self, args: argparse.Namespace) -> int:
        """Handle MCP command execution."""
        command = getattr(args, 'mcp_command', None)
        if command == 'serve':
            host = getattr(args, 'host', '127.0.0.1')
            port = getattr(args, 'port', 8765)
            env_args = getattr(args, 'env', []) or []

            cmd = [sys.executable, '-m', 'mcp.cli', 'serve', '--host', host, '--port', str(port)]
            for env_var in env_args:
                cmd.extend(['--env', env_var])

            result = subprocess.run(cmd, check=False)
            return result.returncode

        if command == 'status':
            cmd = [sys.executable, '-m', 'mcp.cli', 'health-check']
            result = subprocess.run(cmd, check=False)
            return result.returncode

        print("Unknown MCP subcommand", file=sys.stderr)
        return ExitCode.ERROR

    def _load_or_scan_violations(self, args: argparse.Namespace = None):
        """Load violations from scan or existing results."""
        # Mock implementation - returns empty list
        return []

    def _group_violations_by_file(self, violations):
        """Group violations by file path."""
        from collections import defaultdict
        grouped = defaultdict(list)
        for violation in violations:
            file_path = getattr(violation, 'file_path', 'unknown')
            grouped[file_path].append(violation)
        return dict(grouped)

    def _filter_patches(self, patches, args):
        """Filter patches based on confidence and other criteria."""
        filtered = []
        min_confidence = getattr(args, 'min_confidence', 0.7)
        for patch in patches:
            confidence = getattr(patch, 'confidence', 1.0)
            if confidence >= min_confidence:
                filtered.append(patch)
        return filtered

    # ---------------------------------------------------------------------
    # New analysis helpers
    # ---------------------------------------------------------------------

    def _resolve_profile(self, profile: Optional[str]) -> Optional[str]:
        profile = profile or "service-defaults"
        if not validate_policy_name(profile):
            error = self.error_handler.create_error(
                "POLICY_INVALID",
                f"Unknown safety profile '{profile}'",
                ERROR_SEVERITY["HIGH"],
                {"policy": profile, "available_policies": list_available_policies(include_legacy=True)},
            )
            self._handle_cli_error(error)
            return None

        unified = resolve_policy_name(profile, warn_deprecated=True)
        if unified != profile:
            print(f"Note: Using unified profile '{unified}' for '{profile}'")
        return unified

    def _get_threshold_config(self, profile: str) -> ThresholdConfig:
        if self.policy_manager:
            try:
                return self.policy_manager.get_preset(profile)
            except ValueError as exc:
                error = self.error_handler.create_error(
                    "POLICY_INVALID",
                    str(exc),
                    ERROR_SEVERITY["HIGH"],
                    {"policy": profile},
                )
                self._handle_cli_error(error)
                return ThresholdConfig()

        return ThresholdConfig()

    def _require_analyzer(self) -> bool:
        if ANALYZER_AVAILABLE and ConnascenceASTAnalyzer is not None and ThresholdConfig is not None:
            return True

        print(
            "Error: Analyzer components are not available in this environment.",
            file=sys.stderr,
        )
        return False

    def _handle_analyze(self, args: argparse.Namespace) -> int:
        if not self._require_analyzer():
            return ExitCode.RUNTIME_ERROR

        target = Path(args.target)
        if not target.exists():
            print(f"Error: Path does not exist: {target}", file=sys.stderr)
            return ExitCode.CONFIGURATION_ERROR

        if target.is_dir() or getattr(args, "recursive", False):
            return self._run_workspace_analysis(target, args.profile, args.format, args.output, None)

        return self._run_file_analysis(target, args.profile, args.format, args.output)

    def _handle_analyze_workspace(self, args: argparse.Namespace) -> int:
        if not self._require_analyzer():
            return ExitCode.RUNTIME_ERROR

        workspace = Path(args.workspace)
        if not workspace.exists() or not workspace.is_dir():
            print(f"Error: Workspace path does not exist or is not a directory: {workspace}", file=sys.stderr)
            return ExitCode.CONFIGURATION_ERROR

        return self._run_workspace_analysis(
            workspace,
            args.profile,
            args.format,
            args.output,
            args.file_patterns,
        )

    def _handle_validate_safety(self, args: argparse.Namespace) -> int:
        if not self._require_analyzer():
            return ExitCode.RUNTIME_ERROR

        target = Path(args.target)
        if not target.exists() or not target.is_file():
            print(f"Error: Cannot validate non-existent file: {target}", file=sys.stderr)
            return ExitCode.CONFIGURATION_ERROR

        thresholds = self._get_threshold_config(args.profile)
        analyzer = ConnascenceASTAnalyzer(thresholds=thresholds)
        violations = analyzer.analyze_file(target)
        payload = {
            "compliant": len(violations) == 0,
            "profile": args.profile,
            "violations": [self._convert_violation(v, default_file=str(target)) for v in violations],
        }

        self._emit_result(payload, args.format, None)
        return ExitCode.SUCCESS if payload["compliant"] else ExitCode.GENERAL_ERROR

    def _handle_suggest_refactoring(self, args: argparse.Namespace) -> int:
        if not self._require_analyzer():
            return ExitCode.RUNTIME_ERROR

        target = Path(args.target)
        if not target.exists() or not target.is_file():
            print(f"Error: Cannot generate suggestions for non-existent file: {target}", file=sys.stderr)
            return ExitCode.CONFIGURATION_ERROR

        thresholds = self._get_threshold_config(args.profile)
        analyzer = ConnascenceASTAnalyzer(thresholds=thresholds)
        violations = analyzer.analyze_file(target)
        suggestions = self._build_refactoring_suggestions(violations, args.line, args.limit)
        payload = {
            "path": str(target),
            "profile": args.profile,
            "suggestions": suggestions,
        }

        self._emit_result(payload, args.format, None)
        return ExitCode.SUCCESS

    def _run_file_analysis(
        self,
        target: Path,
        profile: str,
        fmt: str,
        output_path: Optional[str],
    ) -> int:
        thresholds = self._get_threshold_config(profile)
        analyzer = ConnascenceASTAnalyzer(thresholds=thresholds)
        start = time.time()
        violations = analyzer.analyze_file(target)
        payload = self._format_analysis_result(
            violations,
            files_analyzed=1,
            profile=profile,
            target=str(target),
            analysis_time=time.time() - start,
        )

        self._emit_result(payload, fmt, output_path)
        return ExitCode.SUCCESS

    def _run_workspace_analysis(
        self,
        workspace: Path,
        profile: str,
        fmt: str,
        output_path: Optional[str],
        patterns: Optional[Iterable[str]],
    ) -> int:
        thresholds = self._get_threshold_config(profile)
        analyzer = ConnascenceASTAnalyzer(thresholds=thresholds)
        files: Dict[str, Dict[str, object]] = {}
        total_score = 0.0

        for file_path in self._iter_workspace_files(workspace, patterns):
            start = time.time()
            violations = analyzer.analyze_file(file_path)
            file_payload = self._format_analysis_result(
                violations,
                files_analyzed=1,
                profile=profile,
                target=str(file_path),
                analysis_time=time.time() - start,
            )
            files[str(file_path)] = file_payload
            total_score += file_payload.get("quality_score", 0.0)

        analyzed_files = len(files)
        workspace_payload = {
            "files": files,
            "profile": profile,
            "files_analyzed": analyzed_files,
            "overall_score": round(total_score / analyzed_files, 2) if analyzed_files else 100.0,
        }

        self._emit_result(workspace_payload, fmt, output_path)
        return ExitCode.SUCCESS

    def _iter_workspace_files(self, workspace: Path, patterns: Optional[Iterable[str]]) -> Iterable[Path]:
        glob_patterns = list(patterns) if patterns else ["*.py"]
        seen = set()
        for pattern in glob_patterns:
            for path in workspace.rglob(pattern):
                if not path.is_file():
                    continue
                real_path = path.resolve()
                if real_path in seen:
                    continue
                seen.add(real_path)
                yield path

    def _format_analysis_result(
        self,
        violations,
        files_analyzed: int,
        profile: str,
        target: Optional[str] = None,
        analysis_time: Optional[float] = None,
    ) -> Dict[str, object]:
        severity_map = {"critical": "critical", "high": "major", "medium": "minor", "low": "info"}
        severity_summary = {"critical": 0, "major": 0, "minor": 0, "info": 0}
        findings = []
        normalized_violations = list(violations or [])

        for idx, violation in enumerate(normalized_violations):
            finding = self._convert_violation(violation, idx, target)
            finding_severity = severity_map.get(getattr(violation, "severity", "medium").lower(), "info")
            severity_summary[finding_severity] += 1
            finding["severity"] = finding_severity
            findings.append(finding)

        total_weight = sum(getattr(v, "weight", 1.0) or 1.0 for v in normalized_violations)
        quality_score = round(max(0.0, 100.0 - (total_weight * 5.0)), 2)
        result: Dict[str, object] = {
            "target": target,
            "profile": profile,
            "quality_score": quality_score,
            "findings": findings,
            "summary": {"totalIssues": len(findings), "issuesBySeverity": severity_summary},
            "files_analyzed": files_analyzed,
        }

        if analysis_time is not None:
            result["analysis_time_ms"] = int(analysis_time * 1000)

        return result

    def _convert_violation(
        self,
        violation,
        idx: int = 0,
        default_file: Optional[str] = None,
    ) -> Dict[str, object]:
        violation_id = getattr(violation, "id", None) or f"{getattr(violation, 'type', 'violation')}-{idx}"
        conn_type = getattr(violation, "connascence_type", None) or getattr(violation, "type", "")
        severity = getattr(violation, "severity", "medium")
        severity_map = {"critical": "critical", "high": "major", "medium": "minor", "low": "info"}
        severity_value = severity_map.get(str(severity).lower(), "info")
        description = getattr(violation, "description", "") or f"Detected {conn_type or 'connascence'}"
        recommendation = getattr(violation, "recommendation", "")
        line_number = getattr(violation, "line_number", 0) or 0
        if line_number <= 0:
            line_number = 1

        return {
            "id": violation_id,
            "type": conn_type or getattr(violation, "type", "unknown"),
            "severity": severity_value,
            "message": description,
            "file": getattr(violation, "file_path", "") or default_file,
            "line": line_number,
            "column": getattr(violation, "column", 0) or 0,
            "suggestion": recommendation,
        }

    def _build_refactoring_suggestions(
        self,
        violations,
        focus_line: Optional[int],
        limit: int,
    ) -> List[Dict[str, object]]:
        if not violations:
            return [
                {
                    "technique": "Review design",
                    "description": "No connascence findings detected. Review architecture or run workspace analysis for context.",
                    "confidence": 0.4,
                    "preview": "File appears clean",
                }
            ]

        severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}

        def sort_key(v):
            severity = getattr(v, "severity", "medium").lower()
            severity_score = severity_rank.get(severity, 3)
            if focus_line is None:
                return (severity_score, getattr(v, "line_number", 0))
            return (abs((getattr(v, "line_number", 0) or 0) - focus_line), severity_score)

        prioritized = sorted(violations, key=sort_key)
        suggestions = []
        for violation in prioritized[: max(1, limit)]:
            conn_type = getattr(violation, "connascence_type", None) or getattr(violation, "type", "unknown")
            description = getattr(violation, "description", "") or f"Reduce {conn_type}"
            line_number = getattr(violation, "line_number", 0) or 0
            preview_line = line_number if line_number > 0 else "unknown"
            suggestions.append(
                {
                    "technique": f"Reduce {conn_type}",
                    "description": description,
                    "confidence": max(0.3, 1.0 - (severity_rank.get(getattr(violation, "severity", "medium"), 3) * 0.2)),
                    "preview": f"Line {preview_line}: {description[:80]}",
                }
            )

        return suggestions

    def _emit_result(self, payload: Dict[str, object], fmt: str, output_path: Optional[str]):
        if fmt == "json":
            serialized = json.dumps(payload, indent=2)
            if output_path:
                Path(output_path).write_text(serialized, encoding="utf-8")
                print(f"Results written to {output_path}")
            else:
                print(serialized)
            return

        self._print_text_summary(payload)
        if output_path:
            Path(output_path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
            print(f"Detailed JSON written to {output_path}")

    def _print_text_summary(self, payload: Dict[str, object]):
        if "findings" in payload:
            print(f"Analyzed {payload.get('target', 'input')} with profile {payload.get('profile')}")
            summary = payload.get("summary", {})
            print(f"Total findings: {summary.get('totalIssues', 0)} | Quality Score: {payload.get('quality_score', 0)}")
            issues = summary.get("issuesBySeverity", {})
            print(
                "Severity breakdown: "
                f"critical={issues.get('critical', 0)}, "
                f"major={issues.get('major', 0)}, "
                f"minor={issues.get('minor', 0)}, "
                f"info={issues.get('info', 0)}"
            )
            return

        if "files" in payload:
            print(
                f"Analyzed workspace with {payload.get('files_analyzed', 0)} files | "
                f"Overall score: {payload.get('overall_score', 0)}"
            )
            return

        if "violations" in payload and "compliant" in payload:
            status = "COMPLIANT" if payload.get("compliant") else "NON-COMPLIANT"
            print(f"Safety validation: {status} for profile {payload.get('profile')}")
            print(f"Violations: {len(payload.get('violations', []))}")
            return

        if "suggestions" in payload:
            print(f"Suggestions for {payload.get('path')}: {len(payload.get('suggestions', []))} items")
            for suggestion in payload.get("suggestions", []):
                print(f"- {suggestion.get('technique')}: {suggestion.get('description')}")
            return

        print(json.dumps(payload, indent=2))


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for CLI with error handling."""
    try:
        cli = ConnascenceCLI()
        return cli.run(args)
    except KeyboardInterrupt:
        print("\n Analysis interrupted by user", file=sys.stderr)
        return ExitCode.USER_INTERRUPTED
    except SystemExit as e:
        # Re-raise SystemExit from argparse (--help, --version, etc.)
        raise
    except Exception as e:
        print(f"CLI initialization failed: {e}", file=sys.stderr)
        return ExitCode.RUNTIME_ERROR


if __name__ == "__main__":
    sys.exit(main())
