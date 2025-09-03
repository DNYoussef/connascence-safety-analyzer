"""
Unified CLI Interface for All Report Types

Provides command-line interface for generating all report formats
with comprehensive options and batch processing capabilities.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from analyzer.ast_engine.core_analyzer import AnalysisResult
from ..core.unified_reporter import unified_reporter


class UnifiedReportCLI:
    """Command-line interface for unified report generation."""
    
    def __init__(self):
        self.reporter = unified_reporter
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser for CLI."""
        parser = argparse.ArgumentParser(
            prog="connascence-reports",
            description="Unified report generation for Connascence analysis",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Generate single JSON report
  connascence-reports --format json --output reports/analysis.json

  # Generate enterprise package
  connascence-reports --enterprise --output-dir reports/enterprise/

  # Generate sales presentation  
  connascence-reports --sales --company "Acme Corp" --output-dir sales/

  # Generate multiple formats
  connascence-reports --formats json,sarif,markdown --output-dir reports/

  # Custom configuration
  connascence-reports --format markdown --config config.json
            """
        )
        
        # Input options
        parser.add_argument(
            "--input", "-i",
            type=Path,
            help="Input analysis result file (JSON format)"
        )
        
        # Output options
        output_group = parser.add_mutually_exclusive_group()
        output_group.add_argument(
            "--output", "-o",
            type=Path,
            help="Output file path for single format"
        )
        output_group.add_argument(
            "--output-dir", "-d", 
            type=Path,
            help="Output directory for multiple formats"
        )
        
        # Format selection
        format_group = parser.add_mutually_exclusive_group()
        format_group.add_argument(
            "--format", "-f",
            choices=["json", "sarif", "markdown", "enterprise", "sales"],
            default="json",
            help="Single report format to generate"
        )
        format_group.add_argument(
            "--formats",
            help="Comma-separated list of formats (json,sarif,markdown,enterprise,sales)"
        )
        format_group.add_argument(
            "--enterprise",
            action="store_true",
            help="Generate complete enterprise reporting package"
        )
        format_group.add_argument(
            "--sales",
            action="store_true", 
            help="Generate sales presentation package"
        )
        
        # Template configuration
        parser.add_argument(
            "--config", "-c",
            type=Path,
            help="JSON configuration file for template options"
        )
        parser.add_argument(
            "--company",
            help="Company name for sales presentations"
        )
        parser.add_argument(
            "--demo-mode",
            action="store_true",
            help="Enable demo mode for sales presentations"
        )
        
        # Markdown options
        parser.add_argument(
            "--max-violations",
            type=int,
            default=10,
            help="Maximum violations to show in markdown reports"
        )
        parser.add_argument(
            "--max-files",
            type=int,
            default=5,
            help="Maximum files to show in markdown reports"
        )
        
        # Enterprise options
        parser.add_argument(
            "--include-dashboard",
            action="store_true",
            default=True,
            help="Include HTML dashboard in enterprise reports"
        )
        parser.add_argument(
            "--include-metrics",
            action="store_true",
            default=True,
            help="Include detailed metrics in enterprise reports"
        )
        
        # Output options
        parser.add_argument(
            "--pretty",
            action="store_true",
            help="Pretty-print JSON output"
        )
        parser.add_argument(
            "--verbose", "-v",
            action="store_true",
            help="Enable verbose output"
        )
        parser.add_argument(
            "--quiet", "-q", 
            action="store_true",
            help="Suppress all output except errors"
        )
        
        return parser
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """Run the CLI with given arguments."""
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)
        
        try:
            # Validate arguments
            self._validate_args(parsed_args)
            
            # Load analysis result
            result = self._load_analysis_result(parsed_args.input)
            
            # Generate reports based on options
            if parsed_args.enterprise:
                self._generate_enterprise_package(result, parsed_args)
            elif parsed_args.sales:
                self._generate_sales_package(result, parsed_args)
            elif parsed_args.formats:
                self._generate_multiple_formats(result, parsed_args)
            else:
                self._generate_single_format(result, parsed_args)
            
            if not parsed_args.quiet:
                print("✅ Report generation completed successfully")
            
            return 0
            
        except Exception as e:
            if not parsed_args.quiet:
                print(f"❌ Error: {e}", file=sys.stderr)
            return 1
    
    def _validate_args(self, args: argparse.Namespace) -> None:
        """Validate command-line arguments."""
        if not args.input:
            raise ValueError("Input analysis result file is required (--input)")
        
        if not args.input.exists():
            raise FileNotFoundError(f"Input file not found: {args.input}")
        
        if not (args.output or args.output_dir):
            raise ValueError("Either --output or --output-dir must be specified")
        
        if args.formats and not args.output_dir:
            raise ValueError("--formats requires --output-dir")
        
        if (args.enterprise or args.sales) and not args.output_dir:
            raise ValueError("Enterprise and sales packages require --output-dir")
    
    def _load_analysis_result(self, input_path: Path) -> AnalysisResult:
        """Load analysis result from file."""
        # This would normally load from a serialized AnalysisResult
        # For now, create a mock result for demonstration
        import json
        
        try:
            with open(input_path, 'r') as f:
                data = json.load(f)
            
            # Convert JSON data back to AnalysisResult
            # This is a simplified implementation - in practice would need
            # proper deserialization logic
            result = AnalysisResult(
                violations=[],  # Would deserialize violations
                total_files_analyzed=data.get('total_files_analyzed', 0),
                analysis_duration_ms=data.get('analysis_duration_ms', 0),
                timestamp=data.get('timestamp', ''),
                project_root=data.get('project_root', '')
            )
            
            return result
            
        except Exception as e:
            raise ValueError(f"Failed to load analysis result: {e}")
    
    def _generate_single_format(self, result: AnalysisResult, args: argparse.Namespace) -> None:
        """Generate single format report."""
        config = self._build_config(args)
        
        content = self.reporter.generate_report(
            result, 
            args.format, 
            args.output,
            config
        )
        
        if not args.quiet:
            print(f"📄 Generated {args.format} report: {args.output}")
    
    def _generate_multiple_formats(self, result: AnalysisResult, args: argparse.Namespace) -> None:
        """Generate multiple format reports."""
        formats = [f.strip() for f in args.formats.split(',')]
        config = self._build_config(args)
        
        # Build format-specific configs
        template_configs = {}
        if 'markdown' in formats:
            template_configs['markdown'] = {
                'max_violations_shown': args.max_violations,
                'max_files_shown': args.max_files
            }
        
        results = self.reporter.generate_multiple(
            result,
            formats,
            args.output_dir,
            template_configs
        )
        
        if not args.quiet:
            for format_name, content in results.items():
                if content:
                    print(f"📄 Generated {format_name} report")
                else:
                    print(f"⚠️  Failed to generate {format_name} report")
    
    def _generate_enterprise_package(self, result: AnalysisResult, args: argparse.Namespace) -> None:
        """Generate enterprise reporting package."""
        results = self.reporter.create_enterprise_package(
            result,
            args.output_dir,
            include_dashboard=args.include_dashboard,
            include_metrics=args.include_metrics
        )
        
        if not args.quiet:
            print(f"📊 Generated enterprise package in {args.output_dir}")
            for format_name in results.keys():
                print(f"  • {format_name} report")
    
    def _generate_sales_package(self, result: AnalysisResult, args: argparse.Namespace) -> None:
        """Generate sales presentation package."""
        results = self.reporter.create_sales_package(
            result,
            args.output_dir,
            company_name=args.company,
            demo_mode=args.demo_mode
        )
        
        if not args.quiet:
            print(f"🚀 Generated sales package in {args.output_dir}")
            for format_name in results.keys():
                print(f"  • {format_name} presentation")
    
    def _build_config(self, args: argparse.Namespace) -> dict:
        """Build configuration from arguments."""
        config = {}
        
        # Load config file if provided
        if args.config and args.config.exists():
            import json
            with open(args.config, 'r') as f:
                config.update(json.load(f))
        
        # Override with command-line options
        if args.company:
            config['company_name'] = args.company
        
        if args.demo_mode:
            config['demo_mode'] = True
        
        if hasattr(args, 'max_violations'):
            config['max_violations_shown'] = args.max_violations
        
        if hasattr(args, 'max_files'):
            config['max_files_shown'] = args.max_files
        
        return config


def main():
    """Main entry point for CLI."""
    cli = UnifiedReportCLI()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()