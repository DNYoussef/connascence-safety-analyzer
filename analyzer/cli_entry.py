"""Shared CLI entry point for the unified analyzer.

This module centralizes the logic used by the standalone CLI, VS Code
extension, and MCP server so they all emit the exact same JSON schema.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
import sys
import time
from typing import Any, Dict, Iterable, List, Optional

from analyzer.unified_analyzer import UnifiedConnascenceAnalyzer

CLI_SCHEMA_VERSION = "2024-08-01"


@dataclass
class CLIAnalysisRequest:
    """Normalized request used by every entry point."""

    input_path: str
    mode: str = "file"  # "file" or "workspace"
    policy: str = "service-defaults"
    include_tests: bool = False
    exclude: List[str] = field(default_factory=list)
    threshold: Optional[float] = None
    parallel: bool = False
    max_workers: Optional[int] = None
    format: str = "json"


@dataclass
class CLIAnalysisResponse:
    """Standard JSON payload shared by CLI, MCP, and VSCode."""

    schema_version: str
    success: bool
    request: CLIAnalysisRequest
    result: Dict[str, Any]
    summary: Dict[str, Any]
    metadata: Dict[str, Any]
    duration_ms: int
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["request"] = asdict(self.request)
        return data

    def to_json(self, indent: Optional[int] = None) -> str:
        return json.dumps(self.to_dict(), indent=indent)


_SHARED_ANALYZER: Optional[UnifiedConnascenceAnalyzer] = None


def _get_analyzer() -> UnifiedConnascenceAnalyzer:
    global _SHARED_ANALYZER
    if _SHARED_ANALYZER is None:
        _SHARED_ANALYZER = UnifiedConnascenceAnalyzer()
    return _SHARED_ANALYZER


def _build_summary(result: Dict[str, Any]) -> Dict[str, Any]:
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for violation in result.get("connascence_violations", []):
        severity = str(violation.get("severity", "low")).lower()
        if severity in severity_counts:
            severity_counts[severity] += 1
    total = result.get("total_violations")
    if total is None:
        total = len(result.get("connascence_violations", []))
    return {
        "total_violations": total,
        "severity_breakdown": severity_counts,
    }


def _build_metadata(request: CLIAnalysisRequest, duration_ms: int) -> Dict[str, Any]:
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "schema_version": CLI_SCHEMA_VERSION,
        "mode": request.mode,
        "policy": request.policy,
        "duration_ms": duration_ms,
    }


def run_cli_analysis(request: CLIAnalysisRequest) -> CLIAnalysisResponse:
    """Execute analysis with shared configuration."""

    analyzer = _get_analyzer()
    start = time.time()
    path = Path(request.input_path)

    options = {
        "parallel": request.parallel,
        "max_workers": request.max_workers,
        "include_tests": request.include_tests,
        "exclude": request.exclude,
    }
    if request.threshold is not None:
        options["threshold"] = request.threshold

    try:
        if request.mode == "file" and path.is_file():
            raw_result = analyzer.analyze_file(str(path))
        else:
            raw_result = analyzer.analyze_project(str(path), request.policy, options)

        result_dict = raw_result.to_dict() if hasattr(raw_result, "to_dict") else raw_result
        duration_ms = int((time.time() - start) * 1000)
        summary = _build_summary(result_dict)
        metadata = _build_metadata(request, duration_ms)
        return CLIAnalysisResponse(
            schema_version=CLI_SCHEMA_VERSION,
            success=True,
            request=request,
            result=result_dict,
            summary=summary,
            metadata=metadata,
            duration_ms=duration_ms,
        )
    except Exception as exc:  # pragma: no cover - surfaced through response
        duration_ms = int((time.time() - start) * 1000)
        metadata = _build_metadata(request, duration_ms)
        metadata["exception_type"] = type(exc).__name__
        return CLIAnalysisResponse(
            schema_version=CLI_SCHEMA_VERSION,
            success=False,
            request=request,
            result={},
            summary={},
            metadata=metadata,
            duration_ms=duration_ms,
            errors=[str(exc)],
        )


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path", nargs="?", default=".", help="Path to analyze")
    parser.add_argument("--policy", dest="policy", default="service-defaults", help="Policy preset")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format")
    parser.add_argument("--include-tests", action="store_true", help="Include test files")
    parser.add_argument("--exclude", nargs="*", default=[], help="Exclude glob patterns")
    parser.add_argument("--threshold", type=float, help="Quality threshold override")
    parser.add_argument("--parallel", action="store_true", help="Enable parallel analysis")
    parser.add_argument("--max-workers", type=int, help="Maximum worker processes")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Shared analyzer CLI entry")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze", help="Analyze a single file or directory")
    _add_common_arguments(analyze_parser)

    workspace_parser = subparsers.add_parser("analyze-workspace", help="Analyze entire workspace")
    _add_common_arguments(workspace_parser)

    return parser


def _request_from_args(args: argparse.Namespace) -> CLIAnalysisRequest:
    return CLIAnalysisRequest(
        input_path=args.path,
        mode="file" if args.command == "analyze" else "workspace",
        policy=args.policy,
        include_tests=args.include_tests,
        exclude=list(args.exclude) if isinstance(args.exclude, list) else [],
        threshold=args.threshold,
        parallel=args.parallel,
        max_workers=args.max_workers,
        format=args.format,
    )


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    request = _request_from_args(args)
    response = run_cli_analysis(request)

    if request.format == "json":
        print(response.to_json(indent=2))
    else:
        print(f"Analysis success: {response.success}")
        print(json.dumps(response.summary, indent=2))

    return 0 if response.success else 1


if __name__ == "__main__":  # pragma: no cover - manual execution
    sys.exit(main())
