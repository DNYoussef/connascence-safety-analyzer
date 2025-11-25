"""
Connascence Detector Handlers Package
=====================================

This package contains handlers extracted from the ConnascenceDetector god object
as part of Phase 1 remediation (god object decomposition).

Phase 1.5 further decomposed MagicLiteralHandler into:
- SeverityCalculator: Severity determination logic
- DescriptionBuilder: Description/recommendation generation
- ContextHelper: Context analysis utilities

Main Classes:
- MagicLiteralHandler: Orchestrates magic literal detection (uses composition)
- AlgorithmDetector: Handles algorithm duplicate detection
"""

from .magic_literal_handler import MagicLiteralHandler
from .algorithm_detector import AlgorithmDetector
from .severity_calculator import SeverityCalculator
from .description_builder import DescriptionBuilder
from .context_helper import ContextHelper

__all__ = [
    "MagicLiteralHandler",
    "AlgorithmDetector",
    "SeverityCalculator",
    "DescriptionBuilder",
    "ContextHelper",
]
