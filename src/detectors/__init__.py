"""
Specialized Connascence Detectors Package.

This package contains specialized detector classes extracted from the monolithic
ConnascenceDetector to follow Single Responsibility Principle.
"""

from .detector_factory import DetectorFactory
from .position_detector import PositionDetector
from .algorithm_detector import AlgorithmDetector
from .god_object_detector import GodObjectDetector

__all__ = [
    'DetectorFactory',
    'PositionDetector', 
    'AlgorithmDetector',
    'GodObjectDetector'
]