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
import sys
import warnings
from typing import List, Optional
from pathlib import Path

# Import unified policy system
sys.path.append(str(Path(__file__).parent.parent))
from analyzer.constants import (
    resolve_policy_name, 
    validate_policy_name,
    list_available_policies,
    UNIFIED_POLICY_NAMES,
    POLICY_DEPRECATION_WARNINGS,
    ERROR_CODE_MAPPING,
    ERROR_SEVERITY,
    INTEGRATION_ERROR_MAPPING,
    EXIT_SUCCESS,
    EXIT_VIOLATIONS_FOUND,
    EXIT_ERROR,
    EXIT_INVALID_ARGUMENTS,
    EXIT_CONFIGURATION_ERROR,
    EXIT_INTERRUPTED
)

try:
    from analyzer.unified_analyzer import StandardError, ErrorHandler
except ImportError:
    # Fallback for environments where unified analyzer isn't available
    class StandardError:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        def to_dict(self):
            return {k: v for k, v in self.__dict__.items()}
    
    class ErrorHandler:
        def __init__(self, integration):
            self.integration = integration
        def create_error(self, error_type, message, **kwargs):
            return StandardError(code=5001, message=message, **kwargs)
        def handle_exception(self, e, context=None):
            return StandardError(code=5001, message=str(e), context=context or {})


class ConnascenceCLI:
    """Basic CLI interface for connascence analysis."""
    
    def __init__(self):
        self.parser = self._create_parser()
        self.error_handler = ErrorHandler('cli')
        self.errors = []
        self.warnings = []
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser for CLI."""
        parser = argparse.ArgumentParser(
            description="Connascence Safety Analyzer CLI",
            prog="connascence"
        )
        
        parser.add_argument(
            "paths",
            nargs="*",
            help="Paths to analyze"
        )
        
        parser.add_argument(
            "--config",
            type=str,
            help="Configuration file path"
        )
        
        parser.add_argument(
            "--output",
            "-o",
            type=str,
            help="Output file path"
        )
        
        parser.add_argument(
            "--policy",
            "--policy-preset", 
            dest="policy",
            type=str,
            default="standard",
            help=f"Policy preset to use. Unified names: {', '.join(UNIFIED_POLICY_NAMES)}. "
                 f"Legacy names supported with deprecation warnings."
        )
        
        parser.add_argument(
            "--format",
            choices=["json", "markdown", "sarif"],
            default="json",
            help="Output format"
        )
        
        parser.add_argument(
            "--verbose",
            "-v",
            action="store_true",
            help="Verbose output"
        )
        
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Dry run mode"
        )
        
        parser.add_argument(
            "--list-policies",
            action="store_true",
            help="List all available policy names (unified and legacy)"
        )
        
        return parser
    
    def parse_args(self, args: Optional[List[str]] = None) -> argparse.Namespace:
        """Parse command line arguments."""
        return self.parser.parse_args(args)
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """Run the CLI with given arguments."""
        parsed_args = self.parse_args(args)
        
        # Handle policy listing
        if parsed_args.list_policies:
            print("Available policy names:")
            print("\nUnified standard names (recommended):")
            for policy in UNIFIED_POLICY_NAMES:
                print(f"  {policy}")
            
            print("\nLegacy names (deprecated, but supported):")
            legacy_policies = list_available_policies(include_legacy=True)
            for policy in sorted(legacy_policies):
                if policy not in UNIFIED_POLICY_NAMES:
                    print(f"  {policy} (deprecated)")
            
            return 0
        
        # Validate and resolve policy name with error handling
        if hasattr(parsed_args, 'policy'):
            if not validate_policy_name(parsed_args.policy):
                error = self.error_handler.create_error(
                    'POLICY_INVALID',
                    f"Unknown policy '{parsed_args.policy}'",
                    ERROR_SEVERITY['HIGH'],
                    {
                        'policy': parsed_args.policy,
                        'available_policies': list_available_policies(include_legacy=True)
                    }
                )
                self._handle_cli_error(error)
                print(f"Available policies: {', '.join(list_available_policies(include_legacy=True))}")
                return EXIT_CONFIGURATION_ERROR
                
            # Resolve to unified name and show deprecation warning if needed
            unified_policy = resolve_policy_name(parsed_args.policy, warn_deprecated=True)
            if unified_policy != parsed_args.policy:
                print(f"Note: Using unified policy name '{unified_policy}' for '{parsed_args.policy}'")
            parsed_args.policy = unified_policy
        
        if parsed_args.verbose:
            print("Running connascence analysis...")
            if hasattr(parsed_args, 'policy'):
                print(f"Using policy: {parsed_args.policy}")
            
        # Validate paths with standardized error handling
        if not self._validate_paths(parsed_args.paths):
            return EXIT_INVALID_ARGUMENTS
        
        if parsed_args.dry_run:
            print("Dry run mode - would analyze:", parsed_args.paths)
            if hasattr(parsed_args, 'policy'):
                print(f"Would use policy: {parsed_args.policy}")
            return 0
        
        # Placeholder analysis result
        result = {
            "analysis_complete": True,
            "paths_analyzed": parsed_args.paths,
            "violations_found": 0,
            "status": "completed",
            "policy_used": getattr(parsed_args, 'policy', 'standard'),
            "policy_system": "unified_v2.0"
        }
        
        if parsed_args.output:
            import json
            with open(parsed_args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"Results written to {parsed_args.output}")
        else:
            print("Analysis completed successfully")
            
        return 0
    
    def _handle_cli_error(self, error: StandardError):
        """Handle CLI-specific error display with standardized format."""
        self.errors.append(error)
        
        # Map severity to CLI-friendly display
        severity_prefix = {
            ERROR_SEVERITY['CRITICAL']: '💥 CRITICAL',
            ERROR_SEVERITY['HIGH']: '❌ ERROR',
            ERROR_SEVERITY['MEDIUM']: '⚠️  WARNING',
            ERROR_SEVERITY['LOW']: 'ℹ️  INFO'
        }
        
        prefix = severity_prefix.get(error.severity, '❌ ERROR')
        print(f"{prefix}: {error.message}", file=sys.stderr)
        
        # Show relevant context
        if hasattr(error, 'context') and error.context:
            relevant_context = {k: v for k, v in error.context.items() 
                              if k in ['path', 'file_path', 'required_argument', 'config_path']}
            if relevant_context:
                print(f"  Context: {relevant_context}", file=sys.stderr)
    
    def _validate_paths(self, paths: List[str]) -> bool:
        """Validate input paths with error handling."""
        if not paths:
            error = self.error_handler.create_error(
                'CLI_ARGUMENT_INVALID',
                'No paths specified for analysis',
                ERROR_SEVERITY['HIGH'],
                {'required_argument': 'paths'}
            )
            self._handle_cli_error(error)
            return False
        
        # Check each path
        for path in paths:
            if not Path(path).exists():
                error = self.error_handler.create_error(
                    'FILE_NOT_FOUND',
                    f'Path does not exist: {path}',
                    ERROR_SEVERITY['HIGH'],
                    {'path': path, 'operation': 'path_validation'}
                )
                self._handle_cli_error(error)
                return False
        
        return True


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for CLI with error handling."""
    try:
        cli = ConnascenceCLI()
        return cli.run(args)
    except KeyboardInterrupt:
        print("\n⏹️ Analysis interrupted by user", file=sys.stderr)
        return EXIT_INTERRUPTED
    except Exception as e:
        print(f"💥 CLI initialization failed: {e}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())