"""
Specialized Connascence Detectors

This package contains focused detector classes that implement the Single Responsibility Principle.
Each detector handles one specific type of connascence violation.
"""

from .algorithm_detector import AlgorithmDetector
from .base import DetectorBase
from .convention_detector import ConventionDetector
from .execution_detector import ExecutionDetector
from .god_object_detector import GodObjectDetector
from .magic_literal_detector import MagicLiteralDetector
from .position_detector import PositionDetector
from .timing_detector import TimingDetector
from .values_detector import ValuesDetector

__all__ = [
    "AlgorithmDetector",
    "ConventionDetector",
    "DetectorBase",
    "ExecutionDetector",
    "GodObjectDetector",
    "MagicLiteralDetector",
    "PositionDetector",
    "TimingDetector",
    "ValuesDetector",
]
