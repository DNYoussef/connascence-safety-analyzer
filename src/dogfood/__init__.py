"""
Dogfood System - Self-Improvement Controller

This package implements the complete dogfood self-improvement system
for the Connascence Safety Analyzer.
"""

from .controller import DogfoodController
from .safety_validator import SafetyValidator
from .branch_manager import BranchManager
from .metrics_tracker import MetricsTracker

__all__ = [
    'DogfoodController',
    'SafetyValidator', 
    'BranchManager',
    'MetricsTracker'
]