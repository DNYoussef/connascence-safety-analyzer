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
from typing import Any, Dict, Iterable, List, Optional, Tuple

# License validation availability flag
LICENSE_VALIDATION_AVAILABLE = False

# Import unified policy system
sys.path.append(str(Path(__file__).parent.parent.parent))
from analyzer.cli_entry import get_shared_cli_analyzer
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
    from policy.baselines import BaselineManager
except ImportError:
    BaselineManager = None

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

try:
    from autofix.core import AutofixConfig, AutofixEngine
    AUTOFIX_AVAILABLE = True
except ImportError:
    AutofixConfig = None
    AutofixEngine = None
    AUTOFIX_AVAILABLE = False


SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]
SEVERITY_RANK = {level: idx for idx, level in enumerate(SEVERITY_ORDER)}
SEVERITY_ALIASES = {
    "catastrophic": "critical",
    "critical": "critical",
    "major": "high",
    "significant": "high",
    "high": "high",
    "error": "high",
    "moderate": "medium",
    "medium": "medium",
    "warning": "medium",
    "minor": "low",
    "trivial": "low",
    "low": "low",
    "info": "info",
    "informational": "info",
    "advisory": "info",
    "notice": "info",
    "note": "info",
}


class BaseCommandHandler:
    """Base class for CLI command handlers."""

    def __init__(self, cli: "ConnascenceCLI"):
        self.cli = cli


class ScanCommandHandler(BaseCommandHandler):
    """Handler for the legacy scan command."""

    def handle(self, args: argparse.Namespace) -> int:
        if not self.cli._require_analyzer():
            return ExitCode.RUNTIME_ERROR

        paths = self._collect_paths(args)
        if not self.cli._validate_paths(paths):
            return ExitCode.CONFIGURATION_ERROR

        try:
            min_severity = self.cli._resolve_min_severity(getattr(args, "severity", None))
        except ValueError:
            return ExitCode.CONFIGURATION_ERROR

        violation_map, files_analyzed, analysis_time = self.cli._run_analysis_for_paths(
            paths,
            getattr(args, "policy", "service-defaults"),
            getattr(args, "exclude", None),
        )

        findings = self.cli._flatten_violation_map(violation_map, min_severity)
        payload = self.cli._format_analysis_result(
            findings,
            files_analyzed=files_analyzed,
            profile=getattr(args, "policy", "service-defaults"),
            target=", ".join(paths),
            analysis_time=analysis_time,
        )
        payload["metadata"] = {
            "paths": [str(Path(p)) for p in paths],
            "severity_filter": min_severity,
            "incremental": getattr(args, "incremental", False),
            "budget_check": getattr(args, "budget_check", False),
        }

        self.cli._emit_result(payload, getattr(args, "format", "text"), getattr(args, "output", None))
        return ExitCode.SUCCESS if not findings else ExitCode.GENERAL_ERROR

    def _collect_paths(self, args: argparse.Namespace) -> List[str]:
        paths: List[str] = []
        if getattr(args, "path", None):
            paths.append(args.path)
        extra_paths = getattr(args, "paths", None)
        if extra_paths:
            paths.extend(extra_paths)
        if not paths:
            paths = ["."]
        return paths


class ScanDiffCommandHandler(BaseCommandHandler):
    """Handler for scan-diff command leveraging git history."""

    def handle(self, args: argparse.Namespace) -> int:
        if not self.cli._require_analyzer():
            return ExitCode.RUNTIME_ERROR

        base_ref = getattr(args, "base", "HEAD~1")
        head_ref = getattr(args, "head", "HEAD")

        try:
            min_severity = self.cli._resolve_min_severity(getattr(args, "severity", None))
        except ValueError:
            return ExitCode.CONFIGURATION_ERROR

        changed_files, exit_code = self._collect_changed_files(base_ref, head_ref)
        if exit_code is not None:
            return exit_code

        if not changed_files:
            print("No Python files changed in diff", file=sys.stderr)
            return ExitCode.SUCCESS

        violation_map, files_analyzed, analysis_time = self.cli._run_analysis_for_files(
            changed_files,
            getattr(args, "policy", "service-defaults"),
        )

        findings = self.cli._flatten_violation_map(violation_map, min_severity)
        payload = self.cli._format_analysis_result(
            findings,
            files_analyzed=files_analyzed,
            profile=getattr(args, "policy", "service-defaults"),
            target=f"diff {base_ref}..{head_ref}",
            analysis_time=analysis_time,
        )
        payload["metadata"] = {
            "base": base_ref,
            "head": head_ref,
            "changed_files": len(changed_files),
            "severity_filter": min_severity,
        }

        self.cli._emit_result(payload, getattr(args, "format", "text"), getattr(args, "output", None))
        return ExitCode.SUCCESS if not findings else ExitCode.GENERAL_ERROR

    def _collect_changed_files(self, base_ref: str, head_ref: str) -> Tuple[List[str], Optional[int]]:
        cmd = ["git", "diff", "--name-only", base_ref, head_ref]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            print(f"git diff failed: {result.stderr.strip()}", file=sys.stderr)
            return [], ExitCode.RUNTIME_ERROR

        files = [line.strip() for line in result.stdout.splitlines() if line.strip().endswith(".py")]
        existing = [f for f in files if Path(f).exists()]
        return existing, None


class BaselineCommandHandler(BaseCommandHandler):
    """Handler for baseline subcommands."""

    def __init__(self, cli: "ConnascenceCLI"):
        super().__init__(cli)
        self.manager = BaselineManager() if BaselineManager else None

    def handle(self, args: argparse.Namespace) -> int:
        if self.manager is None:
            print("Baseline manager is not available in this environment", file=sys.stderr)
            return ExitCode.RUNTIME_ERROR

        command = getattr(args, "baseline_command", None)
        if command in {"snapshot", "create", "update"}:
            set_active = command in {"create", "update"}
            return self._create_snapshot(args, set_active=set_active)
        if command == "status":
            return self._status()

        print("Unknown or missing baseline subcommand", file=sys.stderr)
        return ExitCode.INVALID_ARGUMENTS

    def _create_snapshot(self, args: argparse.Namespace, set_active: bool = False) -> int:
        if not self.cli._require_analyzer():
            return ExitCode.RUNTIME_ERROR
        profile = "service-defaults"
        violation_map, _, analysis_time = self.cli._run_analysis_for_paths(["."], profile)
        violations = [v for file_list in violation_map.values() for v in file_list]
        message = getattr(args, "message", "Baseline snapshot")
        baseline_id = self.manager.create_baseline(violations, description=message)
        if set_active:
            self.manager.active_baseline = baseline_id

        print(
            f"Baseline {baseline_id} created with {len(violations)} violations in {analysis_time:.2f}s"
        )
        return ExitCode.SUCCESS

    def _status(self) -> int:
        baselines = self.manager.list_baselines()
        if not baselines:
            print("No baselines recorded yet")
            return ExitCode.SUCCESS

        print("Baseline history:")
        for baseline in baselines:
            created = baseline.get("created_at", "unknown time")
            description = baseline.get("description", "(no description)")
            count = baseline.get("violation_count", 0)
            print(f"- {baseline['id']}: {description} ({count} violations, created {created})")
        return ExitCode.SUCCESS


class AutofixCommandHandler(BaseCommandHandler):
    """Handler for autofix operations."""

    def handle(self, args: argparse.Namespace) -> int:
        if not AUTOFIX_AVAILABLE or AutofixEngine is None:
            print("Autofix engine is not available in this build", file=sys.stderr)
            return ExitCode.RUNTIME_ERROR

        if not self.cli._require_analyzer():
            return ExitCode.RUNTIME_ERROR

        if not getattr(args, "force", False) and not getattr(args, "preview", False):
            print(
                "Error: Autofix requires --apply to apply changes or --preview to preview fixes",
                file=sys.stderr,
            )
            return ExitCode.INVALID_ARGUMENTS

        target_path = getattr(args, "path", None) or "."
        if not Path(target_path).exists():
            print(f"Path does not exist: {target_path}", file=sys.stderr)
            return ExitCode.CONFIGURATION_ERROR

        violation_map, _, _ = self.cli._run_analysis_for_paths([target_path], "service-defaults")
        filtered_map = self._filter_violations(violation_map, args)

        engine = AutofixEngine(AutofixConfig(), dry_run=getattr(args, "dry_run", False))
        patches = self._generate_patches(engine, filtered_map)
        patches = self.cli._filter_patches(patches, args)
        if getattr(args, "safe_only", False):
            patches = [p for p in patches if getattr(p, "safety_level", "safe") == "safe"]

        if getattr(args, "preview", False):
            print("Preview mode: showing fixes without applying")
            for patch in patches:
                print(f"- {patch.file_path}:{patch.line_range} -> {patch.description} ({patch.confidence:.2f})")
            print(f"Total patches available: {len(patches)}")
            return ExitCode.SUCCESS

        result = engine.apply_patches(patches, confidence_threshold=getattr(args, "min_confidence", 0.7))
        print(
            f"Applied {getattr(result, 'patches_applied', 0)} patches, "
            f"skipped {getattr(result, 'patches_skipped', 0)}"
        )
        for warning in getattr(result, "warnings", []) or []:
            print(f"warning: {warning}", file=sys.stderr)

        return ExitCode.SUCCESS

    def _filter_violations(
        self, violation_map: Dict[str, List[Any]], args: argparse.Namespace
    ) -> Dict[str, List[Any]]:
        if not getattr(args, "types", None):
            return violation_map

        allowed_types: set = set()
        for violation_type in args.types:
            lowered = violation_type.lower()
            allowed_types.add(lowered)
            allowed_types.add(lowered.replace("connascence_of_", ""))
        filtered: Dict[str, List[Any]] = {}
        for file_path, violations in violation_map.items():
            kept = [
                v
                for v in violations
                if self._match_violation_type(v, allowed_types)
            ]
            if kept:
                filtered[file_path] = kept
        return filtered

    def _generate_patches(
        self, engine: AutofixEngine, violation_map: Dict[str, List[Any]]
    ) -> List[Any]:
        patches: List[Any] = []
        for file_path, violations in violation_map.items():
            self.cli._stream_progress(f"[autofix] analyzing {file_path}")
            patches.extend(engine.analyze_file(file_path, violations))
        return patches

    def _match_violation_type(self, violation: Any, allowed_types: set) -> bool:
        violation_type = getattr(violation, "connascence_type", getattr(violation, "type", ""))
        normalized = str(violation_type).lower()
        simplified = normalized.replace("connascence_of_", "")
        return normalized in allowed_types or simplified in allowed_types


class MCPCommandHandler(BaseCommandHandler):
    """Handler for MCP server lifecycle commands."""

    def handle(self, args: argparse.Namespace) -> int:
        command = getattr(args, "mcp_command", None)
        if command == "serve":
            return self._serve(args)
        if command == "status":
            return self._status(args)

        print("Unknown MCP subcommand", file=sys.stderr)
        return ExitCode.INVALID_ARGUMENTS

    def _serve(self, args: argparse.Namespace) -> int:
        host = getattr(args, "host", "127.0.0.1")
        port = getattr(args, "port", 8765)
        env_args = getattr(args, "env", []) or []

        cmd = [sys.executable, "-m", "mcp.cli", "serve", "--host", host, "--port", str(port)]
        for env_var in env_args:
            cmd.extend(["--env", env_var])

        self.cli._stream_progress(f"[mcp] starting server on {host}:{port}")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        try:
            assert process.stdout is not None
            for line in process.stdout:
                if not line:
                    break
                sys.stdout.write(line)
                sys.stdout.flush()
        except KeyboardInterrupt:
            process.terminate()
            process.wait(timeout=5)
            return ExitCode.USER_INTERRUPTED

        return self._coerce_exit_code(process.returncode)

    def _status(self, args: argparse.Namespace) -> int:
        cmd = [sys.executable, "-m", "mcp.cli", "health-check"]
        result = subprocess.run(cmd, check=False)
        return self._coerce_exit_code(result.returncode)

    def _coerce_exit_code(self, value: Optional[int]) -> int:
        if value is None:
            return ExitCode.RUNTIME_ERROR
        try:
            return ExitCode(value)
        except ValueError:
            return ExitCode.RUNTIME_ERROR


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
        self.analysis_helper = get_shared_cli_analyzer()
        # Command handlers
        self.scan_handler = ScanCommandHandler(self)
        self.scan_diff_handler = ScanDiffCommandHandler(self)
        self.baseline_handler = BaselineCommandHandler(self)
        self.autofix_handler = AutofixCommandHandler(self)
        self.mcp_handler = MCPCommandHandler(self)
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
        diff_parser.add_argument(
            "--policy",
            dest="policy",
            default="service-defaults",
            help=(
                "Policy preset to use when analyzing the diff "
                f"(available: {', '.join(UNIFIED_POLICY_NAMES)})"
            ),
        )
        diff_parser.add_argument(
            "--format",
            choices=["text", "json", "markdown", "sarif"],
            default="text",
            help="Output format for diff analysis",
        )
        diff_parser.add_argument("--output", "-o", type=str, help="Output file path")
        diff_parser.add_argument("--severity", type=str, help="Minimum severity level to report")

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
                return self.scan_handler.handle(parsed_args)
            elif parsed_args.command == "scan-diff":
                return self.scan_diff_handler.handle(parsed_args)
            elif parsed_args.command == "analyze":
                return self._handle_analyze(parsed_args)
            elif parsed_args.command == "analyze-workspace":
                return self._handle_analyze_workspace(parsed_args)
            elif parsed_args.command == "validate-safety":
                return self._handle_validate_safety(parsed_args)
            elif parsed_args.command == "suggest-refactoring":
                return self._handle_suggest_refactoring(parsed_args)
            elif parsed_args.command == "baseline":
                return self.baseline_handler.handle(parsed_args)
            elif parsed_args.command == "autofix":
                return self.autofix_handler.handle(parsed_args)
            elif parsed_args.command == "mcp":
                return self.mcp_handler.handle(parsed_args)
            elif parsed_args.command in ["explain", "license"]:
                # These commands just return success for now
                return ExitCode.SUCCESS
        except KeyboardInterrupt:
            print("\nAnalysis interrupted by user", file=sys.stderr)
            return ExitCode.USER_INTERRUPTED
        except Exception as e:
            print(f"Command execution failed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return ExitCode.RUNTIME_ERROR
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

    def _stream_progress(self, message: str) -> None:
        """Emit progress information for streaming integrations."""
        print(message, file=sys.stderr)

    def _resolve_min_severity(self, severity: Optional[str]) -> Optional[str]:
        """Validate and normalize severity filters."""
        if not severity:
            return None

        normalized = severity.strip().lower()
        mapped = SEVERITY_ALIASES.get(normalized, normalized)
        if mapped in SEVERITY_RANK:
            return mapped

        error = self.error_handler.create_error(
            "CLI_ARGUMENT_INVALID",
            f"Unknown severity level '{severity}'",
            ERROR_SEVERITY["HIGH"],
            {"severity": severity, "allowed": list(SEVERITY_RANK.keys())},
        )
        self._handle_cli_error(error)
        raise ValueError(severity)

    def _run_analysis_for_paths(
        self,
        paths: Iterable[str],
        profile: str,
        exclude: Optional[str] = None,
    ) -> Tuple[Dict[str, List[Any]], int, float]:
        files = list(self._iter_source_files(paths, exclude))
        return self._run_analysis_for_files(files, profile)

    def _run_analysis_for_files(
        self,
        files: Iterable[Path],
        profile: str,
    ) -> Tuple[Dict[str, List[Any]], int, float]:
        thresholds = self._get_threshold_config(profile)
        analyzer = ConnascenceASTAnalyzer(thresholds=thresholds)
        violation_map: Dict[str, List[Any]] = {}
        start = time.time()
        files_analyzed = 0

        for file_path in files:
            path_obj = Path(file_path)
            if not path_obj.exists():
                continue
            self._stream_progress(f"[scan] Analyzing {path_obj}")
            try:
                violations = analyzer.analyze_file(path_obj)
            except Exception as exc:  # pragma: no cover - analyzer failures are rare
                error = self.error_handler.create_error(
                    "ANALYSIS_FAILED",
                    f"Failed to analyze {path_obj}: {exc}",
                    ERROR_SEVERITY["MEDIUM"],
                    {"path": str(path_obj)},
                )
                self._handle_cli_error(error)
                continue

            violation_map[str(path_obj)] = violations
            files_analyzed += 1

        analysis_time = time.time() - start
        return violation_map, files_analyzed, analysis_time

    def _iter_source_files(self, paths: Iterable[str], exclude: Optional[str] = None) -> Iterable[Path]:
        seen = set()
        for raw_path in paths:
            path_obj = Path(raw_path)
            if not path_obj.exists():
                continue

            if path_obj.is_file():
                if self._is_file_excluded(path_obj, exclude):
                    continue
                real = path_obj.resolve()
                if real not in seen:
                    seen.add(real)
                    yield path_obj
                continue

            for file_path in path_obj.rglob("*.py"):
                if self._is_file_excluded(file_path, exclude):
                    continue
                real = file_path.resolve()
                if real in seen:
                    continue
                seen.add(real)
                yield file_path

    def _is_file_excluded(self, file_path: Path, exclude: Optional[str]) -> bool:
        if not exclude:
            return False
        return exclude in str(file_path)

    def _flatten_violation_map(
        self, violation_map: Dict[str, List[Any]], min_severity: Optional[str]
    ) -> List[Any]:
        findings: List[Any] = []
        for violations in violation_map.values():
            for violation in violations:
                if self._should_include_violation(violation, min_severity):
                    findings.append(violation)
        return findings

    def _should_include_violation(self, violation: Any, min_severity: Optional[str]) -> bool:
        if min_severity is None:
            return True

        severity = str(getattr(violation, "severity", "info")).lower()
        violation_rank = SEVERITY_RANK.get(severity, len(SEVERITY_RANK))
        threshold = SEVERITY_RANK[min_severity]
        return violation_rank <= threshold


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
        try:
            return self.analysis_helper.get_threshold_config(profile)
        except RuntimeError as exc:
            error = self.error_handler.create_error(
                "POLICY_INVALID",
                str(exc),
                ERROR_SEVERITY["HIGH"],
                {"policy": profile},
            )
            self._handle_cli_error(error)
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
        payload = self.analysis_helper.analyze_file(target, profile)
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
        workspace_payload = self.analysis_helper.analyze_workspace(
            workspace,
            profile,
            patterns=patterns,
        )

        self._emit_result(workspace_payload, fmt, output_path)
        return ExitCode.SUCCESS

    def _format_analysis_result(
        self,
        violations,
        files_analyzed: int,
        profile: str,
        target: Optional[str] = None,
        analysis_time: Optional[float] = None,
    ) -> Dict[str, object]:
        """(Deprecated) kept for compatibility with validation commands."""
        return self.analysis_helper.format_analysis_result(
            violations,
            profile=profile,
            files_analyzed=files_analyzed,
            target=target,
            analysis_time=analysis_time,
        )

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

        if fmt == "markdown":
            content = self._render_markdown(payload)
            self._write_output(content, output_path)
            return

        if fmt == "sarif":
            sarif_payload = self._build_sarif(payload)
            content = json.dumps(sarif_payload, indent=2)
            self._write_output(content, output_path)
            return

        text_summary = self._render_text_summary(payload)
        print(text_summary)
        if output_path:
            Path(output_path).write_text(text_summary, encoding="utf-8")
            print(f"Text report written to {output_path}")

    def _render_text_summary(self, payload: Dict[str, object]) -> str:
        if "findings" not in payload:
            return "No findings available."

        lines = ["CONNASCENCE ANALYSIS REPORT"]
        lines.append(f"Analyzed {payload.get('target', 'input')} with profile {payload.get('profile')}")
        summary = payload.get("summary", {})
        total = summary.get("totalIssues", 0)
        lines.append(f"Violations found: {total} | Quality Score: {payload.get('quality_score', 0)}")
        issues = summary.get("issuesBySeverity", {})
        lines.append(
            "Severity breakdown: "
            f"critical={issues.get('critical', 0)}, "
            f"major={issues.get('major', 0)}, "
            f"minor={issues.get('minor', 0)}, "
            f"info={issues.get('info', 0)}"
        )
        return "\n".join(lines)

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

    def _write_output(self, content: str, output_path: Optional[str]) -> None:
        if output_path:
            Path(output_path).write_text(content, encoding="utf-8")
            print(f"Results written to {output_path}")
        else:
            print(content)

    def _render_markdown(self, payload: Dict[str, object]) -> str:
        lines = ["# Connascence Analysis Report", ""]
        target = payload.get("target", "input")
        profile = payload.get("profile", "service-defaults")
        lines.append(f"- **Target**: `{target}`")
        lines.append(f"- **Profile**: `{profile}`")
        lines.append(f"- **Quality Score**: {payload.get('quality_score', 'n/a')}")
        summary = payload.get("summary", {})
        lines.append(
            f"- **Findings**: {summary.get('totalIssues', 0)} (critical={summary.get('issuesBySeverity', {}).get('critical', 0)}, "
            f"major={summary.get('issuesBySeverity', {}).get('major', 0)}, "
            f"minor={summary.get('issuesBySeverity', {}).get('minor', 0)}, "
            f"info={summary.get('issuesBySeverity', {}).get('info', 0)})"
        )
        lines.append("")

        findings = payload.get("findings", [])
        if not findings:
            lines.append("_No findings were reported for the selected severity threshold._")
            return "\n".join(lines)

        lines.append("## Violations")
        lines.append("| Severity | Rule | Message | Location |")
        lines.append("| --- | --- | --- | --- |")
        for finding in findings:
            severity = finding.get("severity", "info")
            rule = finding.get("type", finding.get("id", "connascence"))
            message = str(finding.get("message", "")).replace("|", "\\|")
            location = f"{finding.get('file', '')}:{finding.get('line', 0)}"
            lines.append(f"| {severity} | {rule} | {message} | {location} |")

        return "\n".join(lines)

    def _build_sarif(self, payload: Dict[str, object]) -> Dict[str, Any]:
        findings = payload.get("findings", [])
        results = []
        for finding in findings:
            level = self._sarif_level(finding.get("severity"))
            message = finding.get("message", "Connascence issue detected")
            location = {
                "physicalLocation": {
                    "artifactLocation": {"uri": finding.get("file", "")},
                    "region": {
                        "startLine": finding.get("line", 1) or 1,
                        "startColumn": max(1, finding.get("column", 1) or 1),
                    },
                }
            }
            results.append(
                {
                    "ruleId": finding.get("type") or finding.get("id") or "connascence",
                    "level": level,
                    "message": {"text": message},
                    "locations": [location],
                    "properties": {"suggestion": finding.get("suggestion")},
                }
            )

        run = {
            "tool": {
                "driver": {
                    "name": "connascence-cli",
                    "version": "2.0.0",
                    "informationUri": "https://github.com/connascence/connascence-safety-analyzer",
                }
            },
            "results": results,
            "properties": {
                "profile": payload.get("profile"),
                "target": payload.get("target"),
                "summary": payload.get("summary"),
            },
        }
        return {
            "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0.json",
            "version": "2.1.0",
            "runs": [run],
        }

    def _sarif_level(self, severity: Optional[str]) -> str:
        normalized = str(severity or "warning").lower()
        if normalized in {"critical", "high", "major"}:
            return "error"
        if normalized in {"medium", "minor"}:
            return "warning"
        return "note"


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
