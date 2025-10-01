"""
Specialized Connascence Detectors Package.

This package contains specialized detector classes extracted from the monolithic
ConnascenceDetector to follow Single Responsibility Principle.
"""

from .algorithm_detector import AlgorithmDetector
from .detector_factory import DetectorFactory
from .god_object_detector import GodObjectDetector
from .position_detector import PositionDetector

__all__ = ["AlgorithmDetector", "DetectorFactory", "GodObjectDetector", "PositionDetector"]
