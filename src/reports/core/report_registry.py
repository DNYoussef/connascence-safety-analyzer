"""
Report Registry and Template Management

Centralized registry for all report formats and templates.
Provides discovery, registration, and factory capabilities.
"""

import logging
from typing import Any, Dict, Optional, Protocol


logger = logging.getLogger(__name__)


class ReportGenerator(Protocol):
    """Protocol for report generators."""
    
    def generate(self, result: Any) -> str:
        """Generate report content from analysis result."""
        ...
    
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure reporter with template options (optional)."""
        ...


class ReportRegistry:
    """
    Central registry for all report generators and templates.
    
    Manages discovery, registration, and instantiation of report formats.
    """
    
    def __init__(self):
        self._reporters: Dict[str, ReportGenerator] = {}
        self._descriptions: Dict[str, str] = {}
        self._categories: Dict[str, str] = {}
    
    def register(
        self,
        format_name: str,
        reporter: ReportGenerator,
        description: str = "",
        category: str = "analysis"
    ) -> None:
        """
        Register a report generator.
        
        Args:
            format_name: Unique format identifier
            reporter: Report generator instance
            description: Human-readable description
            category: Category (analysis, enterprise, sales, etc.)
        """
        self._reporters[format_name] = reporter
        self._descriptions[format_name] = description
        self._categories[format_name] = category
        
        logger.info(f"Registered report format: {format_name} ({category})")
    
    def get_reporter(self, format_name: str) -> Optional[ReportGenerator]:
        """Get report generator by format name."""
        return self._reporters.get(format_name)
    
    def list_formats(self) -> Dict[str, str]:
        """List all available formats with descriptions."""
        return self._descriptions.copy()
    
    def list_by_category(self, category: str) -> Dict[str, str]:
        """List formats in specific category."""
        return {
            name: desc for name, desc in self._descriptions.items()
            if self._categories.get(name) == category
        }
    
    def get_categories(self) -> Dict[str, int]:
        """Get all categories with count of formats."""
        categories = {}
        for category in self._categories.values():
            categories[category] = categories.get(category, 0) + 1
        return categories
    
    def is_registered(self, format_name: str) -> bool:
        """Check if format is registered."""
        return format_name in self._reporters
    
    def unregister(self, format_name: str) -> bool:
        """Remove a format from registry."""
        if format_name in self._reporters:
            del self._reporters[format_name]
            del self._descriptions[format_name]
            del self._categories[format_name]
            logger.info(f"Unregistered report format: {format_name}")
            return True
        return False


# Global registry instance
_registry = ReportRegistry()


def get_registry() -> ReportRegistry:
    """Get the global report registry."""
    return _registry


def register_reporter(format_name: str, reporter: ReportGenerator, **kwargs) -> None:
    """Convenience function to register a reporter."""
    _registry.register(format_name, reporter, **kwargs)


def get_reporter(format_name: str) -> Optional[ReportGenerator]:
    """Convenience function to get a reporter."""
    return _registry.get_reporter(format_name)