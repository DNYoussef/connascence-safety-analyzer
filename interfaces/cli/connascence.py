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
import asyncio
import json
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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
    from analyzer.ast_engine.core_analyzer import AnalysisResult, ConnascenceASTAnalyzer
    from analyzer.thresholds import ThresholdConfig
    ANALYZER_AVAILABLE = True
except ImportError:
    ANALYZER_AVAILABLE = False
    ConnascenceASTAnalyzer = None
    ThresholdConfig = None

from autofix.core import AutofixConfig, AutofixEngine
from policy.baselines import BaselineManager
from utils.types import ConnascenceViolation

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


class AnalyzerCommandBase:
    """Base utilities shared by analyzer-backed CLI handlers."""

    def __init__(self, analyzer_cls, threshold_cls, progress_callback=None):
        self.analyzer_cls = analyzer_cls
        self.threshold_cls = threshold_cls
        self.progress_callback = progress_callback or (lambda msg: None)

    def _create_analyzer(self):
        if not ANALYZER_AVAILABLE or self.analyzer_cls is None or self.threshold_cls is None:
            raise RuntimeError("ConnascenceASTAnalyzer is not available in this environment")
        return self.analyzer_cls(thresholds=self.threshold_cls())

    def _progress(self, message: str):
        if self.progress_callback:
            self.progress_callback(message)

    def _is_excluded(self, path_obj: Path, patterns: Optional[List[str]] = None) -> bool:
        if not patterns:
            return False
        normalized = str(path_obj)
        return any(pattern and pattern in normalized for pattern in patterns)

    def _analyze_paths(
        self,
        analyzer,
        paths: List[str],
        exclude_patterns: Optional[List[str]] = None,
    ) -> Tuple[List[ConnascenceViolation], int, List[str], List[str]]:
        """Run analyzer across paths and return violations and metadata."""

        violations: List[ConnascenceViolation] = []
        files_scanned = 0
        visited_paths: List[str] = []
        errors: List[str] = []

        for raw_path in dict.fromkeys(paths):
            path_obj = Path(raw_path).expanduser()
            if not path_obj.exists() and str(path_obj) != ".":
                raise FileNotFoundError(f"Path does not exist: {raw_path}")

            path_obj = path_obj if path_obj.exists() else Path.cwd()

            if self._is_excluded(path_obj, exclude_patterns):
                continue

            visited_paths.append(str(path_obj))

            if path_obj.is_file():
                self._progress(f"Analyzing file {path_obj}")
                try:
                    file_violations = analyzer.analyze_file(path_obj)
                    violations.extend(file_violations)
                    files_scanned += 1
                except Exception as exc:  # pragma: no cover - defensive
                    errors.append(f"{path_obj}: {exc}")
            else:
                self._progress(f"Analyzing directory {path_obj}")
                try:
                    result = analyzer.analyze_directory(path_obj)
                    if isinstance(result, AnalysisResult):
                        violations.extend(result.violations)
                        files_scanned += getattr(result, "total_files", 0) or 0
                    else:
                        violations.extend(result)
                except Exception as exc:  # pragma: no cover - defensive
                    errors.append(f"{path_obj}: {exc}")

        return violations, files_scanned, visited_paths, errors

    def _serialize_violation(self, violation: ConnascenceViolation) -> Dict[str, Any]:
        if hasattr(violation, "to_dict"):
            return violation.to_dict()

        return {
            "id": getattr(violation, "id", ""),
            "rule_id": getattr(violation, "rule_id", ""),
            "type": getattr(violation, "type", ""),
            "connascence_type": getattr(violation, "connascence_type", ""),
            "severity": getattr(violation, "severity", "medium"),
            "weight": getattr(violation, "weight", 1.0),
            "file_path": getattr(violation, "file_path", ""),
            "line_number": getattr(violation, "line_number", 0),
            "column": getattr(violation, "column", 0),
            "description": getattr(violation, "description", ""),
            "recommendation": getattr(violation, "recommendation", ""),
            "code_snippet": getattr(violation, "code_snippet", ""),
            "context": getattr(violation, "context", {}),
        }


class ScanCommandHandler(AnalyzerCommandBase):
    """Handler for `scan` command."""

    def run(self, args: argparse.Namespace) -> Tuple[Dict[str, Any], ExitCode]:
        if not ANALYZER_AVAILABLE or self.analyzer_cls is None:
            return {"success": False, "errors": ["Analyzer not available"]}, ExitCode.RUNTIME_ERROR

        paths = self._collect_paths(args)
        exclude_patterns = self._parse_excludes(getattr(args, "exclude", None))

        try:
            analyzer = self._create_analyzer()
        except RuntimeError as exc:
            return {"success": False, "errors": [str(exc)]}, ExitCode.RUNTIME_ERROR

        start_time = time.monotonic()

        try:
            violations, files_scanned, visited_paths, errors = self._analyze_paths(
                analyzer, paths, exclude_patterns
            )
        except FileNotFoundError as exc:
            return {"success": False, "errors": [str(exc)]}, ExitCode.CONFIGURATION_ERROR

        duration = time.monotonic() - start_time
        violation_dicts = [self._serialize_violation(v) for v in violations]

        severity_breakdown = Counter(v.get("severity", "medium") for v in violation_dicts)
        type_breakdown = Counter((v.get("connascence_type") or v.get("type") or "unknown") for v in violation_dicts)

        summary = {
            "total_violations": len(violation_dicts),
            "files_scanned": files_scanned,
            "paths_analyzed": visited_paths,
            "analysis_time_seconds": round(duration, 4),
            "severity_breakdown": dict(severity_breakdown),
            "violations_by_type": dict(type_breakdown),
        }

        metadata = {
            "policy": getattr(args, "policy", "standard"),
            "incremental": getattr(args, "incremental", False),
            "budget_check_requested": getattr(args, "budget_check", False),
            "command": "scan",
        }

        result = {
            "success": True,
            "violations": violation_dicts,
            "summary": summary,
            "metadata": metadata,
            "errors": errors,
        }

        return result, ExitCode.SUCCESS

    def _collect_paths(self, args: argparse.Namespace) -> List[str]:
        paths: List[str] = []
        if getattr(args, "path", None):
            paths.append(args.path)
        if getattr(args, "paths", None):
            paths.extend(args.paths)
        if not paths:
            paths = ["."]
        return paths

    def _parse_excludes(self, raw: Optional[str]) -> List[str]:
        if not raw:
            return []
        return [part.strip() for part in raw.split(",") if part.strip()]


class ScanDiffCommandHandler(AnalyzerCommandBase):
    """Handler for `scan-diff` command."""

    def run(self, args: argparse.Namespace) -> Tuple[Dict[str, Any], ExitCode]:
        if not ANALYZER_AVAILABLE or self.analyzer_cls is None:
            return {"success": False, "errors": ["Analyzer not available"]}, ExitCode.RUNTIME_ERROR

        base_ref = getattr(args, "base", "HEAD~1")
        head_ref = getattr(args, "head", "HEAD")

        try:
            files = self._collect_changed_files(base_ref, head_ref)
        except RuntimeError as exc:
            return {"success": False, "errors": [str(exc)]}, ExitCode.RUNTIME_ERROR

        if not files:
            summary = {
                "total_violations": 0,
                "changed_files": [],
                "analysis_time_seconds": 0.0,
                "base_commit": base_ref,
                "head_commit": head_ref,
            }
            return {
                "success": True,
                "violations": [],
                "summary": summary,
                "metadata": {"command": "scan-diff"},
                "errors": [],
            }, ExitCode.SUCCESS

        try:
            analyzer = self._create_analyzer()
        except RuntimeError as exc:
            return {"success": False, "errors": [str(exc)]}, ExitCode.RUNTIME_ERROR

        start_time = time.monotonic()
        violations: List[ConnascenceViolation] = []
        errors: List[str] = []

        for file_path in files:
            self._progress(f"Analyzing changed file {file_path}")
            try:
                violations.extend(analyzer.analyze_file(file_path))
            except Exception as exc:  # pragma: no cover - defensive
                errors.append(f"{file_path}: {exc}")

        duration = time.monotonic() - start_time
        violation_dicts = [self._serialize_violation(v) for v in violations]

        summary = {
            "total_violations": len(violation_dicts),
            "changed_files": [str(p) for p in files],
            "analysis_time_seconds": round(duration, 4),
            "base_commit": base_ref,
            "head_commit": head_ref,
        }

        result = {
            "success": True,
            "violations": violation_dicts,
            "summary": summary,
            "metadata": {"command": "scan-diff"},
            "errors": errors,
        }

        return result, ExitCode.SUCCESS

    def _collect_changed_files(self, base_ref: str, head_ref: str) -> List[Path]:
        diff_cmd = ["git", "diff", "--name-only", f"{base_ref}...{head_ref}"]
        result = subprocess.run(diff_cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "git diff command failed")

        files: List[Path] = []
        for line in result.stdout.splitlines():
            candidate = Path(line.strip())
            if candidate.suffix == ".py" and candidate.exists():
                files.append(candidate)
        return files


class BaselineCommandHandler(AnalyzerCommandBase):
    """Handler for baseline subcommands."""

    def __init__(self, baseline_manager: BaselineManager, **kwargs):
        super().__init__(**kwargs)
        self.baseline_manager = baseline_manager

    def run(self, args: argparse.Namespace) -> ExitCode:
        command = getattr(args, "baseline_command", None)
        if command in {"snapshot", "create", "update"}:
            return self._create_snapshot(args, command)
        if command == "status":
            return self._show_status()

        print("Baseline command requires a subcommand (snapshot/status/create/update)", file=sys.stderr)
        return ExitCode.INVALID_ARGUMENTS

    def _create_snapshot(self, args: argparse.Namespace, label: str) -> ExitCode:
        try:
            analyzer = self._create_analyzer()
        except RuntimeError as exc:
            print(f"Baseline {label} failed: {exc}", file=sys.stderr)
            return ExitCode.RUNTIME_ERROR

        description = getattr(args, "message", None) or f"Baseline {label}"
        try:
            violations, files_scanned, _, errors = self._analyze_paths(analyzer, ["."])
        except FileNotFoundError as exc:
            print(f"Baseline {label} failed: {exc}", file=sys.stderr)
            return ExitCode.CONFIGURATION_ERROR

        baseline_id = self.baseline_manager.create_baseline(violations, description=description)
        print(
            f"Baseline '{baseline_id}' created from {files_scanned or 'unknown'} file(s) "
            f"with {len(violations)} violation(s)."
        )

        if errors:
            print("Warnings during baseline creation:")
            for error in errors:
                print(f"  - {error}")

        return ExitCode.SUCCESS

    def _show_status(self) -> ExitCode:
        baselines = self.baseline_manager.list_baselines()
        if not baselines:
            print("No baselines recorded yet. Run 'connascence baseline snapshot' to create one.")
            return ExitCode.SUCCESS

        print("Available baselines:")
        for baseline in baselines:
            print(
                f"- {baseline['id']} ({baseline.get('created_at', 'unknown time')}): "
                f"{baseline.get('violation_count', 0)} violations"
            )
        return ExitCode.SUCCESS


class AutofixCommandHandler(AnalyzerCommandBase):
    """Handler for `autofix` command."""

    def run(self, args: argparse.Namespace) -> ExitCode:
        if not getattr(args, "force", False) and not getattr(args, "preview", False):
            print(
                "Autofix requires --apply to make changes or --preview to inspect suggestions", file=sys.stderr
            )
            return ExitCode.INVALID_ARGUMENTS

        try:
            analyzer = self._create_analyzer()
        except RuntimeError as exc:
            print(f"Autofix unavailable: {exc}", file=sys.stderr)
            return ExitCode.RUNTIME_ERROR

        target_path = getattr(args, "path", None) or "."
        try:
            violations, _, _, errors = self._analyze_paths(analyzer, [target_path])
        except FileNotFoundError as exc:
            print(f"Autofix failed: {exc}", file=sys.stderr)
            return ExitCode.CONFIGURATION_ERROR

        if errors:
            print("Autofix warnings:")
            for error in errors:
                print(f"  - {error}")

        if args.types:
            allowed = {t.lower() for t in args.types}
            violations = [
                v
                for v in violations
                if (getattr(v, "connascence_type", "") or getattr(v, "type", "")).lower() in allowed
            ]

        if not violations:
            print("Autofix: no matching violations detected.")
            return ExitCode.SUCCESS

        grouped: Dict[str, List[ConnascenceViolation]] = defaultdict(list)
        for violation in violations:
            file_path = getattr(violation, "file_path", "")
            if file_path:
                grouped[file_path].append(violation)

        engine = AutofixEngine(config=AutofixConfig(), dry_run=getattr(args, "dry_run", False))
        patches = []
        for file_path, vio_list in grouped.items():
            self._progress(f"Generating fixes for {file_path}")
            patches.extend(engine.analyze_file(file_path, vio_list))

        if not patches:
            print("Autofix: analysis completed but no fixes were generated.")
            return ExitCode.SUCCESS

        candidate_patches = [p for p in patches if p.confidence >= getattr(args, "min_confidence", 0.7)]
        if getattr(args, "safe_only", False):
            candidate_patches = [p for p in candidate_patches if getattr(p, "safety_level", "safe") == "safe"]

        if getattr(args, "preview", False) and not getattr(args, "force", False):
            print("Autofix preview (no changes applied):")
            for patch in candidate_patches:
                print(
                    f"- {patch.file_path}:{patch.line_range[0]} [{patch.safety_level}] "
                    f"{patch.description} (confidence {patch.confidence:.2f})"
                )
            print(
                f"{len(candidate_patches)} patch(es) available above confidence threshold "
                f"{getattr(args, 'min_confidence', 0.7):.2f}."
            )
            return ExitCode.SUCCESS

        apply_result = engine.apply_patches(
            candidate_patches, confidence_threshold=getattr(args, "min_confidence", 0.7)
        )

        print(
            f"Autofix applied {apply_result.patches_applied} patch(es); "
            f"skipped {apply_result.patches_skipped}."
        )
        for warning in getattr(apply_result, "warnings", []):
            print(f"Warning: {warning}")

        return ExitCode.SUCCESS


class MCPCommandHandler:
    """Handler for `mcp` command."""

    def __init__(self, progress_callback=None):
        self.progress_callback = progress_callback or (lambda msg: None)

    def _progress(self, message: str):
        if self.progress_callback:
            self.progress_callback(message)

    def run(self, args: argparse.Namespace) -> ExitCode:
        command = getattr(args, "mcp_command", None)
        if command == "serve":
            return self._serve(args)
        if command == "status":
            return self._status()

        print("MCP command requires a subcommand (serve/status)", file=sys.stderr)
        return ExitCode.INVALID_ARGUMENTS

    def _serve(self, args: argparse.Namespace) -> ExitCode:
        port = getattr(args, "port", 8080)
        try:
            server, info = self._create_server()
        except Exception as exc:  # pragma: no cover - defensive
            print(f"Failed to initialize MCP server: {exc}", file=sys.stderr)
            return ExitCode.RUNTIME_ERROR

        self._progress(f"Starting MCP server '{info.get('name')}:{port}'")

        async def _serve_loop():
            readiness = {"status": "ready", "name": info.get("name"), "version": info.get("version"), "port": port}
            print(json.dumps(readiness))
            try:
                health_result = await self._maybe_await(getattr(server, "health_check", None))
                if isinstance(health_result, dict):
                    self._progress(f"Health check: {health_result.get('status', 'ok')}")
            except Exception:  # pragma: no cover - defensive
                pass
            while True:
                await asyncio.sleep(1)

        try:
            asyncio.run(_serve_loop())
        except KeyboardInterrupt:
            self._progress("MCP server stopped")
            return ExitCode.USER_INTERRUPTED
        except Exception as exc:  # pragma: no cover - defensive
            print(f"MCP server failed: {exc}", file=sys.stderr)
            return ExitCode.RUNTIME_ERROR

        return ExitCode.SUCCESS

    def _status(self) -> ExitCode:
        try:
            server, info = self._create_server()
            health = asyncio.run(self._maybe_await(getattr(server, "health_check", None)))
            payload = {"status": "ready", "info": info, "health": health}
            if isinstance(health, dict) and not health.get("success", True):
                payload["status"] = "error"
            print(json.dumps(payload, indent=2))
            return ExitCode.SUCCESS if payload["status"] == "ready" else ExitCode.RUNTIME_ERROR
        except Exception as exc:  # pragma: no cover - defensive
            print(f"Failed to query MCP server: {exc}", file=sys.stderr)
            return ExitCode.RUNTIME_ERROR

    async def _maybe_await(self, candidate):
        if candidate is None:
            return None
        if asyncio.iscoroutinefunction(candidate):
            return await candidate()
        result = candidate()
        if asyncio.iscoroutine(result):
            return await result
        return result

    def _create_server(self):
        try:
            from mcp.enhanced_server import create_enhanced_mcp_server, get_server_info

            server = create_enhanced_mcp_server()
            info = get_server_info()
            return server, info
        except Exception:
            from mcp.server import ConnascenceMCPServer

            server = ConnascenceMCPServer()
            info = {"name": server.name, "version": server.version}
            return server, info


class CLIOutputFormatter:
    """Shared formatter for scan outputs across commands."""

    SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    NASA_SEVERITY_RANK = {
        "catastrophic": 4,
        "critical": 4,
        "major": 3,
        "significant": 3,
        "moderate": 2,
        "minor": 2,
        "trivial": 1,
        "informational": 1,
        "advisory": 1,
        "notice": 1,
    }

    def __init__(self, format_name: str = "text", severity: Optional[str] = None):
        self.format_name = (format_name or "text").lower()
        self.min_rank = self._resolve_severity(severity)

    def _resolve_severity(self, severity: Optional[str]) -> int:
        if not severity:
            return 0

        normalized = severity.strip().lower()
        if normalized in self.SEVERITY_RANK:
            return self.SEVERITY_RANK[normalized]
        if normalized in self.NASA_SEVERITY_RANK:
            return self.NASA_SEVERITY_RANK[normalized]
        if normalized.isdigit():
            numeric = int(normalized)
            if numeric in SEVERITY_LEVELS:
                mapped = SEVERITY_LEVELS[numeric].lower()
                return self.NASA_SEVERITY_RANK.get(mapped, self.SEVERITY_RANK.get(mapped, 0))
        raise ValueError(
            f"Unknown severity level '{severity}'. Expected one of "
            f"{list(self.SEVERITY_RANK.keys())} or NASA severity names."
        )

    def render(self, result: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        filtered_result = self._apply_filters(result)

        if self.format_name == "json":
            return json.dumps(filtered_result, indent=2, ensure_ascii=False), filtered_result
        if self.format_name == "markdown":
            return self._render_markdown(filtered_result), filtered_result
        if self.format_name == "sarif":
            sarif_payload = self._render_sarif(filtered_result)
            return json.dumps(sarif_payload, indent=2, ensure_ascii=False), filtered_result

        return self._render_text(filtered_result), filtered_result

    def _apply_filters(self, result: Dict[str, Any]) -> Dict[str, Any]:
        violations = result.get("violations", [])
        filtered = [v for v in violations if self._rank_for_violation(v) >= self.min_rank]
        summary = dict(result.get("summary", {}))
        summary["total_violations"] = len(filtered)
        filtered_result = dict(result)
        filtered_result["violations"] = filtered
        filtered_result["summary"] = summary
        return filtered_result

    def _rank_for_violation(self, violation: Dict[str, Any]) -> int:
        severity = str(violation.get("severity", "medium")).lower()
        return self.SEVERITY_RANK.get(severity, self.NASA_SEVERITY_RANK.get(severity, 0))

    def _render_text(self, result: Dict[str, Any]) -> str:
        summary = result.get("summary", {})
        violations = result.get("violations", [])
        lines: List[str] = []
        if not violations:
            lines.append("✅ No connascence violations found.")
        else:
            for violation in violations:
                severity = violation.get("severity", "medium").upper()
                path = violation.get("file_path", "<unknown>")
                line = violation.get("line_number", 0) or 0
                conn_type = violation.get("connascence_type") or violation.get("type", "")
                description = violation.get("description", "")
                lines.append(f"{severity:>8} {path}:{line} {conn_type} - {description}")
            lines.append("")
            lines.append(
                f"Total violations: {summary.get('total_violations', len(violations))} across "
                f"{summary.get('files_scanned', 'unknown')} files"
            )
        return "\n".join(lines)

    def _render_markdown(self, result: Dict[str, Any]) -> str:
        summary = result.get("summary", {})
        violations = result.get("violations", [])
        lines = ["# Connascence Scan Report", ""]
        lines.append("## Summary")
        lines.append(f"- Total violations: {summary.get('total_violations', len(violations))}")
        lines.append(f"- Files scanned: {summary.get('files_scanned', 'unknown')}")
        lines.append(f"- Paths: {', '.join(summary.get('paths_analyzed', []))}")
        lines.append("")
        lines.append("## Findings")
        if not violations:
            lines.append("No violations were detected.")
            return "\n".join(lines)

        lines.append("| Severity | File | Line | Type | Description |")
        lines.append("| --- | --- | --- | --- | --- |")
        for violation in violations:
            severity = violation.get("severity", "medium")
            path = violation.get("file_path", "<unknown>")
            line = violation.get("line_number", 0) or 0
            conn_type = violation.get("connascence_type") or violation.get("type", "")
            description = violation.get("description", "").replace("|", "\\|")
            lines.append(f"| {severity} | {path} | {line} | {conn_type} | {description} |")

        return "\n".join(lines)

    def _render_sarif(self, result: Dict[str, Any]) -> Dict[str, Any]:
        severity_map = {
            "critical": "error",
            "high": "error",
            "medium": "warning",
            "low": "note",
        }

        sarif_results = []
        for violation in result.get("violations", []):
            severity = violation.get("severity", "medium").lower()
            sarif_results.append(
                {
                    "ruleId": violation.get("rule_id") or violation.get("type") or "connascence",
                    "level": severity_map.get(severity, "warning"),
                    "message": {"text": violation.get("description", "")},
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {"uri": violation.get("file_path", "")},
                                "region": {"startLine": max(int(violation.get("line_number", 1)) or 1, 1)},
                            }
                        }
                    ],
                    "properties": {
                        "connascenceType": violation.get("connascence_type"),
                        "recommendation": violation.get("recommendation"),
                    },
                }
            )

        sarif = {
            "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {"driver": {"name": "connascence-cli", "version": "2.0.0"}},
                    "results": sarif_results,
                    "properties": {
                        "summary": result.get("summary", {}),
                        "metadata": result.get("metadata", {}),
                    },
                }
            ],
        }
        return sarif


class ConnascenceCLI:
    """Basic CLI interface for connascence analysis."""

    def __init__(self):
        self.parser = self._create_parser()
        self.error_handler = ErrorHandler("cli")
        self.errors = []
        self.warnings = []
        self.baseline_manager = BaselineManager()
        self._progress_enabled = False
        # Command handlers
        self.scan_handler = ScanCommandHandler(
            analyzer_cls=ConnascenceASTAnalyzer,
            threshold_cls=ThresholdConfig,
            progress_callback=self._progress,
        )
        self.scan_diff_handler = ScanDiffCommandHandler(
            analyzer_cls=ConnascenceASTAnalyzer,
            threshold_cls=ThresholdConfig,
            progress_callback=self._progress,
        )
        self.baseline_handler = BaselineCommandHandler(
            baseline_manager=self.baseline_manager,
            analyzer_cls=ConnascenceASTAnalyzer,
            threshold_cls=ThresholdConfig,
            progress_callback=self._progress,
        )
        self.autofix_handler = AutofixCommandHandler(
            analyzer_cls=ConnascenceASTAnalyzer,
            threshold_cls=ThresholdConfig,
            progress_callback=self._progress,
        )
        self.mcp_handler = MCPCommandHandler(progress_callback=self._progress)
        self.license_validator = None

    def _progress(self, message: str):
        if getattr(self, "_progress_enabled", False):
            print(f"[connascence] {message}", flush=True)

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
        serve_parser.add_argument("--port", type=int, default=8080, help="Server port")

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

        self._progress_enabled = bool(getattr(parsed_args, "verbose", False)) or (
            getattr(parsed_args, "command", None) in {"scan", "scan-diff", "autofix"}
        )

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
                return self._handle_scan(parsed_args)
            elif parsed_args.command == "scan-diff":
                return self._handle_scan_diff(parsed_args)
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
        result, exit_code = self.scan_handler.run(args)
        if exit_code != ExitCode.SUCCESS:
            self._print_handler_errors(result)
            return exit_code
        return self._render_analysis_output(result, args)

    def _handle_scan_diff(self, args: argparse.Namespace) -> int:
        result, exit_code = self.scan_diff_handler.run(args)
        if exit_code != ExitCode.SUCCESS:
            self._print_handler_errors(result)
            return exit_code
        return self._render_analysis_output(result, args)

    def _handle_baseline(self, args: argparse.Namespace) -> int:
        return self.baseline_handler.run(args)

    def _handle_autofix(self, args: argparse.Namespace) -> int:
        return self.autofix_handler.run(args)

    def _handle_mcp(self, args: argparse.Namespace) -> int:
        return self.mcp_handler.run(args)

    def _render_analysis_output(self, result: Dict[str, Any], args: argparse.Namespace) -> int:
        formatter = CLIOutputFormatter(
            format_name=getattr(args, "format", "text"),
            severity=getattr(args, "severity", None),
        )
        try:
            output_text, filtered_result = formatter.render(result)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return ExitCode.CONFIGURATION_ERROR

        self._write_output(output_text, getattr(args, "output", None))
        violation_count = filtered_result.get("summary", {}).get(
            "total_violations", len(filtered_result.get("violations", []))
        )
        return ExitCode.SUCCESS if violation_count == 0 else ExitCode.GENERAL_ERROR

    def _write_output(self, content: str, output_path: Optional[str]) -> None:
        if output_path:
            Path(output_path).write_text(content, encoding="utf-8")
            print(f"Results written to {output_path}")
        else:
            try:
                print(content)
            except UnicodeEncodeError:
                print(content.encode("ascii", errors="replace").decode("ascii"))

    def _print_handler_errors(self, result: Optional[Dict[str, Any]]):
        if not isinstance(result, dict):
            return
        for message in result.get("errors", []):
            print(f"Error: {message}", file=sys.stderr)


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
