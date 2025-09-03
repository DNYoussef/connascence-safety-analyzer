"""
Unified Reporting System

Consolidates all report generation capabilities:
- SARIF 2.1.0 exports for CI/CD integration
- JSON analysis formats for machine consumption
- Markdown summaries for PR comments
- Enterprise dashboards for executive reporting
- Sales presentations for prospect demonstrations

Single entry point with template-based generation system.
"""

from .core.unified_reporter import (
    UnifiedReporter,
    unified_reporter,
    generate_report,
    generate_enterprise_package,
    generate_sales_package
)
from .core.report_registry import ReportRegistry, get_registry
from .formats.sarif_reporter import SARIFReporter
from .formats.json_reporter import JSONReporter
from .formats.markdown_reporter import MarkdownReporter
from .formats.enterprise_reporter import EnterpriseReporter
from .formats.sales_reporter import SalesReporter

__version__ = "1.0.0"

__all__ = [
    # Core classes
    "UnifiedReporter",
    "ReportRegistry",
    
    # Global instances
    "unified_reporter",
    "get_registry",
    
    # Format reporters
    "SARIFReporter",
    "JSONReporter", 
    "MarkdownReporter",
    "EnterpriseReporter",
    "SalesReporter",
    
    # Convenience functions
    "generate_report",
    "generate_enterprise_package",
    "generate_sales_package"
]

# Register available formats on import
def _initialize_formats():
    """Initialize all available report formats."""
    registry = get_registry()
    
    # Core analysis formats
    registry.register("sarif", SARIFReporter(), 
                     "SARIF 2.1.0 for GitHub Code Scanning", "analysis")
    registry.register("json", JSONReporter(),
                     "Machine-readable JSON analysis", "analysis") 
    registry.register("markdown", MarkdownReporter(),
                     "PR comment markdown summaries", "analysis")
    
    # Business formats
    registry.register("enterprise", EnterpriseReporter(),
                     "Executive dashboard reports", "enterprise")
    registry.register("sales", SalesReporter(),
                     "Sales presentation materials", "sales")

# Initialize on module import
_initialize_formats()