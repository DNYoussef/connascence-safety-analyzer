"""
Formatters package for connascence analyzer output.

This package provides various output formatters for connascence violations,
including SARIF (Static Analysis Results Interchange Format) for CI/CD integration.
"""

from .sarif import SARIFExporter

__all__ = ["SARIFExporter"]
