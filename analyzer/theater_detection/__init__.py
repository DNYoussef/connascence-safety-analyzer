"""Theater Detection for Connascence Analyzer

Prevents performance theater and validates genuine quality improvements.
"""

from .detector import TheaterDetector, TheaterPattern, ValidationResult
from .patterns import TheaterPatternLibrary
from .validator import EvidenceValidator

__all__ = ["EvidenceValidator", "TheaterDetector", "TheaterPattern", "TheaterPatternLibrary", "ValidationResult"]
