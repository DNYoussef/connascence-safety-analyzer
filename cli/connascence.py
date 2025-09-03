#!/usr/bin/env python3
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
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.ast_engine.core_analyzer import ConnascenceASTAnalyzer, AnalysisResult
from analyzer.thresholds import DEFAULT_PRESETS
from reporting.json_export import JSONReporter
from reporting.sarif_export import SARIFReporter  
from reporting.md_summary import MarkdownReporter
from policy.manager import PolicyManager
from policy.budgets import BudgetTracker
from policy.baselines import BaselineManager


# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ConnascenceCLI:
    """Main CLI application class."""
    
    def __init__(self):
        self.policy_manager = PolicyManager()
        self.baseline_manager = BaselineManager()
        self.budget_tracker = BudgetTracker()
        
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
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """Run the CLI application."""
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)
        
        # Configure logging
        if parsed_args.verbose:
            logging.getLogger().setLevel(logging.INFO)
            logger.info("Verbose logging enabled")
        
        # Handle missing command
        if not parsed_args.command:
            parser.print_help()
            return 0
        
        try:
            # Route to appropriate handler
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
            else:
                parser.error(f"Unknown command: {parsed_args.command}")
                
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return 130
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            if parsed_args.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    def _handle_scan(self, args) -> int:
        """Handle the scan command."""
        print(f"Scanning {args.path} with policy '{args.policy}'...")
        start_time = time.time()
        
        # Load policy
        policy = self.policy_manager.load_preset(args.policy)
        
        # Create analyzer with policy configuration
        analyzer = ConnascenceASTAnalyzer(
            thresholds=policy.thresholds,
            weights=policy.weights,
            exclusions=args.exclude
        )
        
        # Perform analysis
        target_path = Path(args.path)
        if target_path.is_file():
            violations = analyzer.analyze_file(target_path)
            # Create minimal result for single file
            result = AnalysisResult(
                timestamp=time.time(),
                project_root=str(target_path.parent),
                total_files_analyzed=1,
                analysis_duration_ms=int((time.time() - start_time) * 1000),
                violations=violations,
                file_stats={str(target_path): {"violations_count": len(violations)}},
                summary_metrics=analyzer._calculate_summary_metrics(violations)
            )
        else:
            result = analyzer.analyze_directory(target_path)
        
        # Filter by severity if specified
        if args.severity:
            result.violations = self._filter_by_severity(result.violations, args.severity)
        
        # Check budgets if requested
        if args.budget_check:
            budget_status = self.budget_tracker.check_budget(result.violations, policy)
            if not budget_status.passed:
                print(f"❌ Budget exceeded! {budget_status.violations_summary}")
                return 1
        
        # Generate output
        output = self._generate_output(result, args.format, policy)
        
        # Write output
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"Results written to {args.output}")
        else:
            print(output)
        
        # Return exit code based on findings
        critical_count = sum(1 for v in result.violations if v.severity.value == "critical")
        return min(critical_count, 1)  # Return 1 if any critical violations
    
    def _handle_scan_diff(self, args) -> int:
        """Handle the scan-diff command."""
        print(f"Analyzing changes between {args.base} and {args.head}...")
        
        # This would implement git diff analysis
        # For now, return a placeholder
        print("scan-diff implementation pending")
        return 0
    
    def _handle_explain(self, args) -> int:
        """Handle the explain command.""" 
        print(f"Explaining finding: {args.finding_id}")
        
        # This would provide detailed explanations
        print("explain implementation pending")
        return 0
    
    def _handle_autofix(self, args) -> int:
        """Handle the autofix command."""
        if args.dry_run:
            print(f"Dry run: showing fixes for {args.path}")
        else:
            print(f"Applying fixes to {args.path}")
        
        print("autofix implementation pending")
        return 0
    
    def _handle_baseline(self, args) -> int:
        """Handle baseline commands."""
        if args.baseline_action == "snapshot":
            print("Creating baseline snapshot...")
        elif args.baseline_action == "update":
            print("Updating baseline...")
        elif args.baseline_action == "status":
            print("Checking baseline status...")
        elif args.baseline_action == "list":
            print("Listing baselines...")
        
        print("baseline implementation pending")
        return 0
    
    def _handle_mcp(self, args) -> int:
        """Handle MCP server commands.""" 
        if args.mcp_action == "serve":
            print(f"Starting MCP server on {args.transport}://{args.host}:{args.port}")
            # This would start the actual MCP server
            print("MCP server implementation pending")
        
        return 0
    
    def _filter_by_severity(self, violations: List, min_severity: str) -> List:
        """Filter violations by minimum severity."""
        severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        min_level = severity_order[min_severity]
        
        return [
            v for v in violations 
            if severity_order.get(v.severity.value, 0) >= min_level
        ]
    
    def _generate_output(self, result: AnalysisResult, format_type: str, policy) -> str:
        """Generate output in the specified format."""
        if format_type == "json":
            return JSONReporter().generate(result)
        elif format_type == "sarif":
            return SARIFReporter().generate(result)
        elif format_type == "markdown":
            return MarkdownReporter().generate(result)
        else:  # text
            return self._generate_text_output(result)
    
    def _generate_text_output(self, result: AnalysisResult) -> str:
        """Generate human-readable text output."""
        lines = []
        lines.append("=" * 80)
        lines.append("CONNASCENCE ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Summary
        lines.append(f"Analysis completed in {result.analysis_duration_ms}ms")
        lines.append(f"Files analyzed: {result.total_files_analyzed}")
        lines.append(f"Total violations: {len(result.violations)}")
        lines.append("")
        
        # Violations by severity
        severity_counts = {}
        for violation in result.violations:
            severity = violation.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        lines.append("Violations by severity:")
        for severity in ["critical", "high", "medium", "low"]:
            count = severity_counts.get(severity, 0)
            lines.append(f"  {severity.capitalize():8s}: {count:3d}")
        lines.append("")
        
        # Top violations
        if result.violations:
            lines.append("Top violations:")
            for violation in sorted(result.violations, key=lambda v: v.weight, reverse=True)[:10]:
                lines.append(
                    f"  {violation.severity.value.upper():4s} - {violation.type.value} - "
                    f"{Path(violation.file_path).name}:{violation.line_number} - "
                    f"{violation.description[:60]}..."
                )
        
        return "\n".join(lines)


def main():
    """Main entry point."""
    cli = ConnascenceCLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())