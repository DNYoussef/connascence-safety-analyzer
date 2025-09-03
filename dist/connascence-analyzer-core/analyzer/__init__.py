"""
Connascence Analyzer Package

This package provides comprehensive connascence detection for Python codebases,
implementing Meilir Page-Jones' connascence theory to identify coupling issues.

Main Components:
- ast_engine: Static analysis using AST traversal
- dup_detection: Algorithm duplication detection  
- runtime_probe: Dynamic analysis via pytest plugin
- frameworks: Framework-specific analysis profiles
"""

from .thresholds import (
    ThresholdConfig, WeightConfig, PolicyPreset,
    ConnascenceType, Severity,
    DEFAULT_THRESHOLDS, DEFAULT_WEIGHTS, DEFAULT_PRESETS,
    get_severity_for_violation, calculate_violation_weight, explain_threshold
)

__version__ = "1.0.0"
__author__ = "Connascence Analytics"

# Public API
__all__ = [
    # Core classes
    "ConnascenceAnalyzer",
    "Violation",
    "AnalysisResult",
    
    # Configuration
    "ThresholdConfig", 
    "WeightConfig",
    "PolicyPreset",
    "ConnascenceType",
    "Severity",
    
    # Defaults
    "DEFAULT_THRESHOLDS",
    "DEFAULT_WEIGHTS", 
    "DEFAULT_PRESETS",
    
    # Utilities
    "get_severity_for_violation",
    "calculate_violation_weight",
    "explain_threshold",
]