"""
Unified Report Generation API

Consolidates all report generation capabilities:
- SARIF 2.1.0 exports
- JSON analysis formats  
- Markdown summaries
- Enterprise dashboards
- Sales presentations

Single entry point for all report types with template-based generation.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from analyzer.ast_engine.core_analyzer import AnalysisResult
from .report_registry import ReportRegistry
from ..formats.sarif_reporter import SARIFReporter
from ..formats.json_reporter import JSONReporter
from ..formats.markdown_reporter import MarkdownReporter
from ..formats.enterprise_reporter import EnterpriseReporter
from ..formats.sales_reporter import SalesReporter


logger = logging.getLogger(__name__)


class UnifiedReporter:
    """
    Unified interface for all report generation.
    
    Provides single entry point with template-based generation system.
    Supports multiple output formats and enterprise/sales presentation modes.
    """
    
    def __init__(self):
        self.registry = ReportRegistry()
        self._initialize_core_reporters()
    
    def _initialize_core_reporters(self):
        """Initialize and register core report formats."""
        # Core analysis formats
        self.registry.register("sarif", SARIFReporter(), 
                             description="SARIF 2.1.0 for GitHub Code Scanning")
        self.registry.register("json", JSONReporter(),
                             description="Machine-readable JSON analysis")
        self.registry.register("markdown", MarkdownReporter(), 
                             description="PR comment markdown summaries")
        
        # Enterprise formats
        self.registry.register("enterprise", EnterpriseReporter(),
                             description="Executive dashboard reports")
        self.registry.register("sales", SalesReporter(),
                             description="Sales presentation materials")
    
    def generate_report(
        self,
        result: AnalysisResult,
        format_type: str,
        output_path: Optional[Union[str, Path]] = None,
        template_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate unified report in specified format.
        
        Args:
            result: Analysis results to report on
            format_type: Output format (sarif, json, markdown, enterprise, sales)
            output_path: Optional path to save report
            template_config: Optional template configuration
            
        Returns:
            Generated report content as string
        """
        try:
            reporter = self.registry.get_reporter(format_type)
            if not reporter:
                raise ValueError(f"Unknown report format: {format_type}")
            
            # Apply template configuration if provided
            if template_config and hasattr(reporter, 'configure'):
                reporter.configure(template_config)
            
            # Generate report content
            content = reporter.generate(result)
            
            # Save to file if path provided
            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                if format_type == "json":
                    # Pretty print JSON with stable ordering
                    if isinstance(content, str):
                        data = json.loads(content)
                        content = json.dumps(data, indent=2, sort_keys=True)
                
                output_path.write_text(content, encoding='utf-8')
                logger.info(f"Report saved to {output_path}")
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to generate {format_type} report: {e}")
            raise
    
    def generate_multiple(
        self,
        result: AnalysisResult,
        formats: List[str],
        output_dir: Union[str, Path],
        template_configs: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, str]:
        """
        Generate multiple report formats simultaneously.
        
        Args:
            result: Analysis results to report on
            formats: List of format types to generate
            output_dir: Directory to save all reports
            template_configs: Per-format template configurations
            
        Returns:
            Dictionary mapping format to generated content
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = {}
        template_configs = template_configs or {}
        
        for format_type in formats:
            try:
                # Determine output filename
                extensions = {
                    "sarif": ".sarif",
                    "json": ".json", 
                    "markdown": ".md",
                    "enterprise": "_enterprise.json",
                    "sales": "_sales.md"
                }
                
                filename = f"connascence_report{extensions.get(format_type, '.txt')}"
                output_path = output_dir / filename
                
                # Generate with format-specific config
                config = template_configs.get(format_type)
                content = self.generate_report(result, format_type, output_path, config)
                
                results[format_type] = content
                logger.info(f"Generated {format_type} report: {output_path}")
                
            except Exception as e:
                logger.error(f"Failed to generate {format_type} report: {e}")
                results[format_type] = None
        
        return results
    
    def get_available_formats(self) -> Dict[str, str]:
        """Get all available report formats with descriptions."""
        return self.registry.list_formats()
    
    def create_enterprise_package(
        self,
        result: AnalysisResult,
        output_dir: Union[str, Path],
        include_dashboard: bool = True,
        include_metrics: bool = True
    ) -> Dict[str, str]:
        """
        Create complete enterprise reporting package.
        
        Generates all enterprise-relevant formats:
        - Executive dashboard (JSON + HTML)
        - SARIF for tools integration
        - Detailed JSON for analysis
        - Markdown summary for sharing
        
        Args:
            result: Analysis results
            output_dir: Output directory for package
            include_dashboard: Generate HTML dashboard
            include_metrics: Include detailed metrics
            
        Returns:
            Dictionary of generated files
        """
        package_formats = ["json", "sarif", "markdown", "enterprise"]
        
        # Enterprise template configurations
        template_configs = {
            "enterprise": {
                "include_dashboard": include_dashboard,
                "include_metrics": include_metrics,
                "executive_summary": True,
                "roi_calculations": True
            },
            "markdown": {
                "executive_mode": True,
                "max_violations_shown": 15,
                "include_recommendations": True
            },
            "json": {
                "include_file_stats": True,
                "include_policy_compliance": True,
                "detailed_context": True
            }
        }
        
        return self.generate_multiple(result, package_formats, output_dir, template_configs)
    
    def create_sales_package(
        self,
        result: AnalysisResult,
        output_dir: Union[str, Path],
        company_name: Optional[str] = None,
        demo_mode: bool = True
    ) -> Dict[str, str]:
        """
        Create sales presentation package.
        
        Optimized for prospect demonstrations:
        - Sales-focused metrics
        - ROI calculations
        - Comparison benchmarks
        - Demo-ready visualizations
        
        Args:
            result: Analysis results
            output_dir: Output directory
            company_name: Optional company name for customization
            demo_mode: Enable demo-specific formatting
            
        Returns:
            Dictionary of generated sales materials
        """
        sales_formats = ["sales", "json", "markdown"]
        
        # Sales-optimized configurations
        template_configs = {
            "sales": {
                "company_name": company_name,
                "demo_mode": demo_mode,
                "roi_emphasis": True,
                "benchmark_comparisons": True,
                "executive_summary": True
            },
            "markdown": {
                "sales_mode": True,
                "roi_focused": True,
                "simplified_technical": True
            }
        }
        
        return self.generate_multiple(result, sales_formats, output_dir, template_configs)


# Global instance for convenience
unified_reporter = UnifiedReporter()


def generate_report(
    result: AnalysisResult,
    format_type: str = "json",
    output_path: Optional[Union[str, Path]] = None,
    **kwargs
) -> str:
    """Convenience function for single report generation."""
    return unified_reporter.generate_report(result, format_type, output_path, kwargs)


def generate_enterprise_package(
    result: AnalysisResult,
    output_dir: Union[str, Path],
    **kwargs
) -> Dict[str, str]:
    """Convenience function for enterprise package generation."""
    return unified_reporter.create_enterprise_package(result, output_dir, **kwargs)


def generate_sales_package(
    result: AnalysisResult,
    output_dir: Union[str, Path],
    **kwargs
) -> Dict[str, str]:
    """Convenience function for sales package generation."""
    return unified_reporter.create_sales_package(result, output_dir, **kwargs)