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
CLI Command Handlers

Extracts command handling logic from ConnascenceCLI to reduce the God Object
and improve cohesion. Each handler focuses on a specific command responsibility.
"""

import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import constants to reduce magic literals
from .constants import (
    ExitCode, SeverityLevel, OutputFormats, PolicyPresets,
    SafetyProfiles, MCPTransports, AnalysisMessages,
    ConfigurationDefaults, ValidationMessages, ReportHeaders,
    NetworkDefaults, DefaultPorts
)

logger = logging.getLogger(__name__)


class BaseCommandHandler:
    """Base class for command handlers with common functionality."""
    
    def __init__(self, policy_manager, baseline_manager, budget_tracker):
        self.policy_manager = policy_manager
        self.baseline_manager = baseline_manager  
        self.budget_tracker = budget_tracker
    
    def handle_runtime_error(self, error: Exception, operation: str) -> int:
        """Handle runtime errors consistently across handlers."""
        print(f"Runtime error during {operation}: {error}", file=sys.stderr)
        logger.exception(f"{operation} runtime error")
        return ExitCode.GENERAL_ERROR
    
    def _filter_by_severity(self, violations: List, min_severity: str) -> List:
        """Filter violations by minimum severity."""
        severity_order = {
            SeverityLevel.LOW.value: 0,
            SeverityLevel.MEDIUM.value: 1, 
            SeverityLevel.HIGH.value: 2,
            SeverityLevel.CRITICAL.value: 3
        }
        min_level = severity_order[min_severity]
        
        return [
            v for v in violations 
            if severity_order.get(v.severity.value, 0) >= min_level
        ]


class ScanCommandHandler(BaseCommandHandler):
    """Handles the 'scan' command for code analysis."""
    
    def handle(self, args) -> int:
        """Execute scan command."""
        print(f"Scanning {args.path} with policy '{args.policy}'...")
        start_time = time.time()
        
        try:
            # Load policy using constant
            if args.policy not in [PolicyPresets.STRICT_CORE, PolicyPresets.SERVICE_DEFAULTS, PolicyPresets.EXPERIMENTAL]:
                print(f"Invalid policy: {args.policy}")
                return ExitCode.CONFIGURATION_ERROR
            
            policy = self.policy_manager.get_preset(args.policy)
            
            # Import analyzer here to avoid circular imports
            from analyzer.ast_engine.core_analyzer import ConnascenceASTAnalyzer, AnalysisResult
            from analyzer.thresholds import ThresholdConfig, DEFAULT_WEIGHTS
            
            # Create analyzer with policy configuration
            thresholds = ThresholdConfig(**policy['thresholds'])
            weights = DEFAULT_WEIGHTS
            analyzer = ConnascenceASTAnalyzer(
                thresholds=thresholds,
                weights=weights,
                exclusions=args.exclude
            )
            
            # Perform analysis
            target_path = Path(args.path)
            if not target_path.exists():
                print(f"Error: Path '{target_path}' does not exist", file=sys.stderr)
                return ExitCode.CONFIGURATION_ERROR
            
            if target_path.is_file():
                violations = analyzer.analyze_file(target_path)
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
                    print(f" Budget exceeded! {budget_status.violations_summary}")
                    return ExitCode.GENERAL_ERROR
            
            # Generate output
            output = self._generate_output(result, args.format, policy)
            
            # Write output
            if args.output:
                try:
                    with open(args.output, 'w') as f:
                        f.write(output)
                    print(f"Results written to {args.output}")
                except IOError as e:
                    print(f"Error writing output file: {e}", file=sys.stderr)
                    return ExitCode.RUNTIME_ERROR
            else:
                print(output)
            
            # Return exit code based on findings
            if result.violations:
                # Policy violations found - return exit code 1
                return ExitCode.GENERAL_ERROR
            else:
                # No violations found - return exit code 0
                return ExitCode.SUCCESS
                
        except Exception as e:
            print(f"Runtime error during scan: {e}", file=sys.stderr)
            logger.exception("Scan runtime error")
            return ExitCode.RUNTIME_ERROR
    
    def _generate_output(self, result, format_type: str, policy) -> str:
        """Generate output in the specified format."""
        if format_type == OutputFormats.JSON:
            from reporting.json_export import JSONReporter
            return JSONReporter().generate(result)
        elif format_type == OutputFormats.SARIF:
            from reporting.sarif_export import SARIFReporter
            return SARIFReporter().generate(result)
        elif format_type == OutputFormats.MARKDOWN:
            from reporting.md_summary import MarkdownReporter
            return MarkdownReporter().generate(result)
        else:  # text
            return self._generate_text_output(result)
    
    def _generate_text_output(self, result) -> str:
        """Generate human-readable text output."""
        from .constants import ReportHeaders
        
        lines = []
        lines.append(ReportHeaders.SEPARATOR)
        lines.append(ReportHeaders.ANALYSIS_HEADER)
        lines.append(ReportHeaders.SEPARATOR)
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
        for severity in [SeverityLevel.CRITICAL.value, SeverityLevel.HIGH.value, 
                        SeverityLevel.MEDIUM.value, SeverityLevel.LOW.value]:
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


class LicenseCommandHandler(BaseCommandHandler):
    """Handles license validation commands."""
    
    def __init__(self, policy_manager, baseline_manager, budget_tracker, license_validator=None):
        super().__init__(policy_manager, baseline_manager, budget_tracker)
        self.license_validator = license_validator
    
    def handle(self, args) -> int:
        """Handle license validation commands."""
        if not self.license_validator:
            print(ValidationMessages.LICENSE_UNAVAILABLE, file=sys.stderr)
            return ExitCode.CONFIGURATION_ERROR
        
        if args.license_action == "validate":
            return self._handle_validate(args)
        elif args.license_action == "check":
            return self._handle_check(args)
        elif args.license_action == "memory":
            return self._handle_memory(args)
        else:
            print("License action required", file=sys.stderr)
            return ExitCode.CONFIGURATION_ERROR
    
    def _handle_validate(self, args) -> int:
        """Handle license validate command."""
        project_path = Path(args.path)
        if not project_path.exists():
            print(f"Error: Path '{project_path}' does not exist", file=sys.stderr)
            return ExitCode.CONFIGURATION_ERROR
        
        print(f"Validating license compliance for {project_path}...")
        
        try:
            from licensing import LicenseValidationResult
            report = self.license_validator.validate_license(project_path)
            
            if args.format == OutputFormats.JSON:
                # Convert to JSON-serializable format
                report_dict = {
                    "timestamp": report.timestamp.isoformat(),
                    "validation_result": report.validation_result.value,
                    "exit_code": report.exit_code,
                    "errors": [
                        {
                            "code": e.error_code,
                            "type": e.error_type,
                            "description": e.description,
                            "severity": e.severity,
                            "recommendation": e.recommendation
                        }
                        for e in report.errors
                    ],
                    "sequential_steps": report.sequential_steps[-5:],  # Last 5 steps
                    "memory_key": report.memory_storage_key
                }
                print(json.dumps(report_dict, indent=2))
            else:
                print(self.license_validator.generate_license_report(report))
            
            return report.exit_code
            
        except Exception as e:
            print(f"License validation failed: {e}", file=sys.stderr)
            return ExitCode.LICENSE_ERROR
    
    def _handle_check(self, args) -> int:
        """Handle quick license check command."""
        project_path = Path(args.path)
        
        try:
            from licensing import LicenseValidationResult
            report = self.license_validator.validate_license(project_path)
            
            if report.validation_result == LicenseValidationResult.VALID:
                print("✓ License validation passed")
                return ExitCode.SUCCESS
            else:
                print(f"✗ License validation failed: {report.validation_result.value}")
                if report.errors:
                    for error in report.errors[:3]:  # Show first 3 errors
                        print(f"  - {error.description}")
                return report.exit_code
                
        except Exception as e:
            print(f"License check failed: {e}", file=sys.stderr)
            return ExitCode.LICENSE_ERROR
    
    def _handle_memory(self, args) -> int:
        """Handle license memory management commands."""
        if args.clear:
            memory_file = Path.home() / ".connascence" / "license_memory.json"
            if memory_file.exists():
                memory_file.unlink()
                print("License validation memory cleared")
            else:
                print("No license memory to clear")
            return ExitCode.SUCCESS
        
        if args.show:
            memory_file = Path.home() / ".connascence" / "license_memory.json"
            if memory_file.exists():
                try:
                    with open(memory_file, 'r') as f:
                        memory_data = json.load(f)
                    print(json.dumps(memory_data, indent=2))
                except Exception as e:
                    print(f"Failed to read license memory: {e}", file=sys.stderr)
                    return ExitCode.CONFIGURATION_ERROR
            else:
                print("No license memory file found")
            return ExitCode.SUCCESS
        
        print("License memory action required (--clear or --show)", file=sys.stderr)
        return ExitCode.CONFIGURATION_ERROR


class BaselineCommandHandler(BaseCommandHandler):
    """Handles baseline management commands."""
    
    def handle(self, args) -> int:
        """Handle baseline commands."""
        try:
            if args.baseline_action == "snapshot":
                print("Creating baseline snapshot...")
                # TODO: Implement actual baseline snapshot logic
            elif args.baseline_action == "update":
                print("Updating baseline...")
                # TODO: Implement baseline update logic
            elif args.baseline_action == "status":
                print("Checking baseline status...")
                # TODO: Implement baseline status logic
            elif args.baseline_action == "list":
                print("Listing baselines...")
                # TODO: Implement baseline list logic
            else:
                print("Invalid baseline action", file=sys.stderr)
                return ExitCode.CONFIGURATION_ERROR
            
            print("baseline implementation pending")
            return ExitCode.SUCCESS
        except Exception as e:
            return self.handle_runtime_error(e, "baseline management")


class MCPCommandHandler(BaseCommandHandler):
    """Handles MCP server commands."""
    
    def handle(self, args) -> int:
        """Handle MCP server commands."""
        try:
            if args.mcp_action == "serve":
                transport = args.transport or MCPTransports.STDIO
                host = args.host or NetworkDefaults.LOCALHOST
                port = args.port or DefaultPorts.MCP_SERVER
                
                print(f"Starting MCP server on {transport}://{host}:{port}")
                # TODO: Implement actual MCP server startup logic
                print("MCP server implementation pending")
            else:
                print("Invalid MCP action", file=sys.stderr)
                return ExitCode.CONFIGURATION_ERROR
            
            return ExitCode.SUCCESS
        except Exception as e:
            return self.handle_runtime_error(e, "MCP server management")


class ExplainCommandHandler(BaseCommandHandler):
    """Handles the explain command for violation details."""
    
    def handle(self, args) -> int:
        """Handle the explain command."""
        try:
            if not args.finding_id:
                print("Finding ID is required", file=sys.stderr)
                return ExitCode.CONFIGURATION_ERROR
            
            print(f"Explaining finding: {args.finding_id}")
            
            # TODO: Implement explain logic with knowledge base lookup
            print("explain implementation pending")
            return ExitCode.SUCCESS
        except Exception as e:
            return self.handle_runtime_error(e, "explain operation")


class AutofixCommandHandler(BaseCommandHandler):
    """Handles the autofix command for automatic code fixes."""
    
    def handle(self, args) -> int:
        """Handle the autofix command."""
        try:
            target_path = Path(args.path)
            if not target_path.exists():
                print(f"Error: Path '{target_path}' does not exist", file=sys.stderr)
                return ExitCode.CONFIGURATION_ERROR
            
            if args.dry_run:
                print(f"Dry run: showing fixes for {args.path}")
            else:
                print(f"Applying fixes to {args.path}")
            
            # TODO: Implement autofix logic
            print("autofix implementation pending")
            return ExitCode.SUCCESS
        except Exception as e:
            return self.handle_runtime_error(e, "autofix operation")


class ScanDiffCommandHandler(BaseCommandHandler):
    """Handles the scan-diff command for git difference analysis."""
    
    def handle(self, args) -> int:
        """Handle the scan-diff command."""
        try:
            if not args.base:
                print("Base reference is required", file=sys.stderr)
                return ExitCode.CONFIGURATION_ERROR
            
            print(f"Analyzing changes between {args.base} and {args.head}...")
            
            # TODO: Implement git diff analysis
            print("scan-diff implementation pending")
            return ExitCode.SUCCESS
        except Exception as e:
            return self.handle_runtime_error(e, "scan-diff operation")