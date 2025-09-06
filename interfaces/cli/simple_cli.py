# SPDX-License-Identifier: MIT
"""
Flake8-style simple CLI interface for connascence analysis.

Usage:
    connascence .                    # Analyze current directory
    connascence src/                 # Analyze src directory
    connascence file.py              # Analyze single file
    connascence --help               # Show help

This provides a simple interface similar to flake8, while preserving
all advanced features through command-line options.
"""

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

# Import configuration discovery utilities
from .config_discovery import ConfigDiscovery
from .policy_detection import PolicyDetection

# Import the full analyzer for actual analysis
try:
    from analyzer.core import ConnascenceAnalyzer
    ANALYZER_AVAILABLE = True
except ImportError:
    ANALYZER_AVAILABLE = False


class SimpleConnascenceCLI:
    """Simple flake8-style interface for connascence analysis."""

    def __init__(self):
        self.config_discovery = ConfigDiscovery()
        self.policy_detection = PolicyDetection()
        self.exit_code = 0

    def create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser with simple flake8-like interface."""
        parser = argparse.ArgumentParser(
            prog="connascence",
            description="Connascence analyzer - Find coupling issues in your Python code",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  connascence .                     # Analyze current directory
  connascence src/                  # Analyze src directory
  connascence file.py               # Analyze single file
  connascence --config=setup.cfg .  # Use specific config file
  connascence --format=sarif .      # Output SARIF format
  connascence --policy=strict .     # Use strict policy
            """.strip()
        )

        # Main positional argument - paths to analyze (like flake8)
        parser.add_argument(
            "paths",
            nargs="*",
            default=["."],
            help="Files or directories to analyze (default: current directory)"
        )

        # Simple configuration options
        parser.add_argument(
            "--config",
            metavar="FILE",
            help="Configuration file path (auto-discovered by default)"
        )

        parser.add_argument(
            "--format",
            choices=["json", "text", "sarif"],
            default="json",
            help="Output format (default: json)"
        )

        parser.add_argument(
            "--output", "-o",
            metavar="FILE",
            help="Write output to file instead of stdout"
        )

        # Policy selection with smart defaults
        parser.add_argument(
            "--policy",
            help="Analysis policy (auto-detected by default: default, strict-core, nasa_jpl_pot10, lenient)"
        )

        # Simple quality controls
        parser.add_argument(
            "--exit-zero",
            action="store_true",
            help="Exit with code 0 even if violations found (like flake8 --exit-zero)"
        )

        parser.add_argument(
            "--show-source",
            action="store_true",
            help="Show source code excerpts for violations"
        )

        # Filtering options
        parser.add_argument(
            "--exclude",
            metavar="PATTERNS",
            help="Comma-separated list of patterns to exclude"
        )

        parser.add_argument(
            "--include",
            metavar="PATTERNS",
            help="Comma-separated list of patterns to include"
        )

        # Severity filtering
        parser.add_argument(
            "--severity",
            choices=["low", "medium", "high", "critical"],
            help="Only show violations of this severity or higher"
        )

        # Advanced options (preserve full functionality)
        parser.add_argument(
            "--nasa-validation",
            action="store_true",
            help="Enable NASA Power of Ten validation"
        )

        parser.add_argument(
            "--strict-mode",
            action="store_true",
            help="Enable strict analysis mode"
        )

        # Compatibility with old interface
        parser.add_argument(
            "--legacy-cli",
            action="store_true",
            help="Use the full legacy CLI interface"
        )

        # Informational
        parser.add_argument(
            "--version",
            action="version",
            version="connascence-analyzer 2.0.0"
        )

        parser.add_argument(
            "--list-policies",
            action="store_true",
            help="List available analysis policies"
        )

        return parser

    def discover_configuration(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Discover and load configuration from various sources."""
        if config_path:
            return self.config_discovery.load_config_file(config_path)

        # Auto-discovery order: pyproject.toml, setup.cfg, .connascence.cfg
        config = self.config_discovery.discover_config()
        return config

    def detect_policy(self, paths: List[str], explicit_policy: Optional[str] = None) -> str:
        """Auto-detect the best policy based on project structure."""
        if explicit_policy:
            return explicit_policy

        # Auto-detect based on project characteristics
        detected_policy = self.policy_detection.detect_policy(paths)
        return detected_policy

    def format_output(self, result: Dict[str, Any], format_type: str, show_source: bool = False) -> str:
        """Format analysis results for output."""
        if format_type == "json":
            return json.dumps(result, indent=2, ensure_ascii=False)

        elif format_type == "sarif":
            # Use SARIF reporter if available
            try:
                from analyzer.reporting.sarif import SARIFReporter
                reporter = SARIFReporter()
                return reporter.export_results(result)
            except ImportError:
                # Fallback to JSON
                return json.dumps(result, indent=2)

        elif format_type == "text":
            return self._format_text_output(result, show_source)

        return str(result)

    def _format_text_output(self, result: Dict[str, Any], show_source: bool = False) -> str:
        """Format results as human-readable text (flake8-style)."""
        lines = []

        violations = result.get("violations", [])
        if not violations:
            return "No connascence violations found."

        for violation in violations:
            file_path = violation.get("file_path", "unknown")
            line_number = violation.get("line_number", 0)
            rule_id = violation.get("rule_id", "UNKNOWN")
            description = violation.get("description", "No description")

            # Clean up description to avoid unicode issues
            description = description.encode('ascii', errors='replace').decode('ascii')

            # Format like flake8: file:line:col: code message
            line = f"{file_path}:{line_number}:1: {rule_id} {description}"
            lines.append(line)

            if show_source and violation.get("source_code"):
                source = violation['source_code'].strip()
                source = source.encode('ascii', errors='replace').decode('ascii')
                lines.append(f"    {source}")

        # Add summary
        total = len(violations)
        critical = len([v for v in violations if v.get("severity") == "critical"])

        if total > 0:
            lines.append("")
            lines.append(f"Found {total} connascence violations ({critical} critical)")

        return "\n".join(lines)

    def filter_violations(self, violations: List[Dict[str, Any]],
                         severity_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Filter violations by severity level."""
        if not severity_filter:
            return violations

        severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        min_severity = severity_order.get(severity_filter, 0)

        filtered = []
        for violation in violations:
            violation_severity = violation.get("severity", "medium")
            if severity_order.get(violation_severity, 1) >= min_severity:
                filtered.append(violation)

        return filtered

    def run_legacy_cli(self, args: argparse.Namespace) -> int:
        """Delegate to the full legacy CLI interface."""
        try:
            # Import and run the full CLI
            from analyzer.core import main as legacy_main

            # Convert simple args back to legacy format
            legacy_args = [
                "--path", " ".join(args.paths),
                "--format", args.format
            ]

            if args.policy:
                legacy_args.extend(["--policy", args.policy])
            if args.output:
                legacy_args.extend(["--output", args.output])
            if args.nasa_validation:
                legacy_args.append("--nasa-validation")
            if args.strict_mode:
                legacy_args.append("--strict-mode")

            # Run legacy CLI
            sys.argv = ["connascence", *legacy_args]
            legacy_main()
            return 0

        except Exception as e:
            print(f"Error running legacy CLI: {e}", file=sys.stderr)
            return 1

    def run(self, argv: Optional[List[str]] = None) -> int:
        """Main entry point - run the simple CLI."""
        parser = self.create_parser()
        args = parser.parse_args(argv)

        # Handle special cases
        if args.list_policies:
            policies = ["default", "strict-core", "nasa_jpl_pot10", "lenient"]
            print("Available policies:")
            for policy in policies:
                print(f"  {policy}")
            return 0

        if args.legacy_cli:
            return self.run_legacy_cli(args)

        # Load configuration
        self.discover_configuration(args.config)

        # Detect best policy
        policy = self.detect_policy(args.paths, args.policy)

        # Run analysis
        if not ANALYZER_AVAILABLE:
            print("Error: Analyzer not available. Run with --legacy-cli", file=sys.stderr)
            return 1

        try:
            analyzer = ConnascenceAnalyzer()

            results = []
            for path in args.paths:
                result = analyzer.analyze_path(
                    path=path,
                    policy=policy,
                    strict_mode=args.strict_mode,
                    exclude=args.exclude.split(",") if args.exclude else [],
                    nasa_validation=args.nasa_validation
                )
                results.append(result)

            # Combine results
            combined_result = self._combine_results(results)

            # Apply filtering
            if args.severity:
                combined_result["violations"] = self.filter_violations(
                    combined_result.get("violations", []),
                    args.severity
                )

            # Format output
            output = self.format_output(combined_result, args.format, args.show_source)

            # Write output
            if args.output:
                Path(args.output).write_text(output, encoding="utf-8")
                print(f"Results written to {args.output}")
            else:
                print(output)

            # Determine exit code
            violations = combined_result.get("violations", [])
            critical_violations = [v for v in violations if v.get("severity") == "critical"]

            if args.exit_zero:
                return 0
            elif critical_violations:
                return 1
            else:
                return 0

        except Exception as e:
            print(f"Analysis failed: {e}", file=sys.stderr)
            return 1

    def _combine_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine multiple analysis results into one."""
        if not results:
            return {"violations": [], "summary": {"total_violations": 0}}

        if len(results) == 1:
            return results[0]

        # Combine multiple results
        combined = {
            "success": all(r.get("success", False) for r in results),
            "violations": [],
            "summary": {"total_violations": 0}
        }

        for result in results:
            combined["violations"].extend(result.get("violations", []))

        combined["summary"]["total_violations"] = len(combined["violations"])

        return combined


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for simple CLI."""
    cli = SimpleConnascenceCLI()
    return cli.run(argv)


if __name__ == "__main__":
    sys.exit(main())
