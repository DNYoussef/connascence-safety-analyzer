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
Unified Connascence Analyzer Entry Point
========================================

This is the main entry script that coordinates all analysis components:
1. Enhanced connascence detection (check_connascence.py)
2. NASA Power of Ten rules compliance
3. MECE duplication analysis  
4. Multi-linter integration (Ruff, MyPy, Radon, Bandit, Black, BuildFlags)
5. Enterprise reporting and CI/CD integration

PHASE 1B IMPLEMENTATION:
- Creates unified entry point that orchestrates all existing components
- Integrates with existing tool coordinator and policy systems
- Provides comprehensive CLI with all enterprise options
- Enables NASA rules, MECE analysis, and tool integration

Usage:
  python scripts/unified_connascence_analyzer.py <path> [options]
  
Examples:
  # Basic analysis
  python scripts/unified_connascence_analyzer.py src/
  
  # NASA compliance focus
  python scripts/unified_connascence_analyzer.py . --nasa-compliance --severity high
  
  # Enterprise analysis with all tools
  python scripts/unified_connascence_analyzer.py . --enable-tools --comprehensive
  
  # CI/CD integration
  python scripts/unified_connascence_analyzer.py . --fail-on critical,high --format json --output report.json
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def main():
    """Main unified entry point."""
    parser = argparse.ArgumentParser(
        description="Unified Connascence Safety Analyzer with NASA Rules & MECE Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMPREHENSIVE ANALYSIS OPTIONS:
  --nasa-compliance     Enable NASA Power of Ten rules checking
  --mece-analysis      Enable MECE duplication detection
  --enable-tools       Enable multi-tool integration (Ruff, MyPy, etc.)
  --comprehensive      Enable all analysis features
  
ENTERPRISE FEATURES:
  --fail-on SEVERITIES    Comma-separated severities to fail on
  --budget-file FILE       Path to violation budget file
  --baseline-file FILE     Path to baseline comparison file
  --consolidation-recommendations  Include MECE consolidation advice
  --failure-predictions    Include failure prediction analysis

EXAMPLES:
  # Basic connascence analysis
  python scripts/unified_connascence_analyzer.py src/ --format json
  
  # NASA compliance focus
  python scripts/unified_connascence_analyzer.py . --nasa-compliance --severity high
  
  # Enterprise analysis with all tools
  python scripts/unified_connascence_analyzer.py . --enable-tools --comprehensive
  
  # CI/CD integration
  python scripts/unified_connascence_analyzer.py . --fail-on critical,high --output report.json
  
  # MECE duplication analysis
  python scripts/unified_connascence_analyzer.py . --mece-analysis --consolidation-recommendations
        """
    )
    
    # Core arguments
    parser.add_argument("path", help="Path to analyze (file or directory)")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument("--format", "-f", choices=["text", "json", "sarif"], 
                       default="text", help="Output format")
    parser.add_argument("--severity", "-s", 
                       choices=["low", "medium", "high", "critical"],
                       help="Minimum severity level to report")
    parser.add_argument("--exclude", "-e", action="append", 
                       help="Additional exclusion patterns")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Verbose output")
    
    # Enhanced analysis options
    parser.add_argument("--nasa-compliance", action="store_true",
                       help="Focus on NASA Power of Ten rules compliance")
    parser.add_argument("--mece-analysis", action="store_true", 
                       help="Include MECE duplication analysis")
    parser.add_argument("--enable-tools", action="store_true",
                       help="Enable multi-tool integration (Ruff, MyPy, etc.)")
    parser.add_argument("--comprehensive", action="store_true",
                       help="Run comprehensive analysis with all features")
    
    # CI/CD integration
    parser.add_argument("--fail-on", help="Comma-separated severities to fail on (e.g., critical,high)")
    parser.add_argument("--budget-file", help="Path to violation budget file")
    parser.add_argument("--baseline-file", help="Path to baseline file for comparison")
    
    # Output options
    parser.add_argument("--consolidation-recommendations", action="store_true",
                       help="Include MECE consolidation recommendations")
    parser.add_argument("--failure-predictions", action="store_true",
                       help="Include failure prediction analysis")
    
    args = parser.parse_args()
    
    # Configure comprehensive mode
    if args.comprehensive:
        args.nasa_compliance = True
        args.mece_analysis = True
        args.enable_tools = True
        args.failure_predictions = True
        args.consolidation_recommendations = True
    
    # Validate path
    target_path = Path(args.path)
    if not target_path.exists():
        print(f"Error: Path '{target_path}' does not exist", file=sys.stderr)
        return 2  # Configuration error
    
    if args.verbose:
        print("Unified Connascence Safety Analyzer")
        print(f"Analyzing: {target_path}")
        if args.nasa_compliance:
            print("  + NASA Power of Ten rules enabled")
        if args.mece_analysis:
            print("  + MECE duplication analysis enabled") 
        if args.enable_tools:
            print("  + Multi-tool integration enabled")
        print()
    
    start_time = time.time()
    
    try:
        # Build command to execute enhanced check_connascence.py
        analyzer_path = Path(__file__).parent.parent / "analyzer" / "check_connascence.py"
        cmd = [sys.executable, str(analyzer_path), str(target_path)]
        
        # Add format option
        cmd.extend(["--format", args.format])
        
        # Add severity filtering
        if args.severity:
            cmd.extend(["--severity", args.severity])
        
        # Add exclusion patterns
        if args.exclude:
            for pattern in args.exclude:
                cmd.extend(["--exclude", pattern])
        
        # Add verbose flag
        if args.verbose:
            cmd.append("--verbose")
        
        # Add enhanced analysis options
        if args.nasa_compliance:
            cmd.append("--nasa-compliance")
        
        if args.mece_analysis:
            cmd.append("--mece-analysis")
        
        if args.enable_tools:
            cmd.append("--enable-tools")
        
        if args.comprehensive:
            cmd.append("--comprehensive")
        
        # Add CI/CD options
        if args.fail_on:
            cmd.extend(["--fail-on", args.fail_on])
        
        if args.budget_file:
            cmd.extend(["--budget-file", args.budget_file])
        
        if args.baseline_file:
            cmd.extend(["--baseline-file", args.baseline_file])
        
        # Add output options
        if args.consolidation_recommendations:
            cmd.append("--consolidation-recommendations")
        
        if args.failure_predictions:
            cmd.append("--failure-predictions")
        
        # Add output file
        if args.output:
            cmd.extend(["--output", args.output])
        
        if args.verbose:
            print(f"Executing: {' '.join(cmd[:3])} [path] [options]")
            print()
        
        # Execute the enhanced analyzer
        result = subprocess.run(
            cmd,
            capture_output=not args.output,  # Capture only if not writing to file
            text=True,
            cwd=str(Path(__file__).parent.parent),
            env={**os.environ, 'PYTHONPATH': str(Path(__file__).parent.parent)}
        )
        
        # Handle output
        if not args.output and result.stdout:
            print(result.stdout)
        
        if result.stderr and args.verbose:
            print("Warnings/Errors:", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
        
        # Performance summary
        if args.verbose:
            elapsed = time.time() - start_time
            print(f"\nAnalysis completed in {elapsed:.2f} seconds")
            if result.returncode == 0:
                print("[OK] Analysis successful")
            else:
                print(f"[WARN] Analysis completed with exit code {result.returncode}")
        
        # Forward the exit code from the analyzer
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n[STOP] Analysis interrupted by user", file=sys.stderr)
        return 130  # User interrupted
    except FileNotFoundError as e:
        print(f"[ERROR] Analyzer not found: {e}", file=sys.stderr)
        print(f"Expected at: {analyzer_path}", file=sys.stderr)
        return 2  # Configuration error
    except Exception as e:
        print(f"[ERROR] Runtime error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 3  # Runtime error


def check_dependencies():
    """Check if required dependencies are available.""" 
    missing_deps = []
    
    # Check Python version
    if sys.version_info < (3, 8):
        missing_deps.append("Python 3.8+ required")
    
    # Check for optional tools
    tools_status = {}
    
    # Check Ruff
    try:
        result = subprocess.run(['ruff', '--version'], capture_output=True, text=True)
        tools_status['ruff'] = 'available' if result.returncode == 0 else 'not available'
    except FileNotFoundError:
        tools_status['ruff'] = 'not available'
    
    # Check MyPy
    try:
        result = subprocess.run(['mypy', '--version'], capture_output=True, text=True)
        tools_status['mypy'] = 'available' if result.returncode == 0 else 'not available'
    except FileNotFoundError:
        tools_status['mypy'] = 'not available'
    
    # Check if enhanced analyzer exists
    analyzer_path = Path(__file__).parent.parent / "analyzer" / "check_connascence.py"
    if not analyzer_path.exists():
        missing_deps.append(f"Enhanced analyzer not found at: {analyzer_path}")
    
    return missing_deps, tools_status


def show_system_info():
    """Show system information and available tools."""
    missing_deps, tools_status = check_dependencies()
    
    print("Unified Connascence Safety Analyzer - System Info")
    print("=" * 60)
    
    print(f"Python Version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Working Directory: {os.getcwd()}")
    print()
    
    print("Tool Integration Status:")
    for tool, status in tools_status.items():
        icon = "[OK]" if status == "available" else "[X]"
        print(f"  {icon} {tool}: {status}")
    print()
    
    if missing_deps:
        print("Missing Dependencies:")
        for dep in missing_deps:
            print(f"  [X] {dep}")
        print()
    
    # Show analyzer path
    analyzer_path = Path(__file__).parent.parent / "analyzer" / "check_connascence.py"
    analyzer_status = "[OK] available" if analyzer_path.exists() else "[X] missing"
    print(f"Enhanced Analyzer: {analyzer_status}")
    print(f"  Path: {analyzer_path}")
    print()
    
    print("Available Analysis Features:")
    print("  + Core connascence detection (9 types)")
    print("  + NASA Power of Ten rules compliance")
    print("  + MECE duplication analysis")
    print("  + Multi-linter integration")
    print("  + Enterprise reporting (JSON, SARIF, text)")
    print("  + CI/CD integration and quality gates")
    print("  + Failure prediction and recommendations")


if __name__ == "__main__":
    # Handle special commands
    if len(sys.argv) > 1 and sys.argv[1] in ["--info", "--system-info"]:
        show_system_info()
        sys.exit(0)
    
    # Run main analyzer
    sys.exit(main())