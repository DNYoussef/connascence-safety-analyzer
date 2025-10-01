# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
Architecture Components Module
==============================

Specialized components extracted from UnifiedConnascenceAnalyzer god object.
All components follow NASA Rule 4 compliance (functions under 60 lines).

Includes performance optimization components like DetectorPool.
"""

# Import detector pool for performance optimization
from .aggregator import ViolationAggregator
from .configuration_manager import ConfigurationManager
from .detector_pool import DetectorPool, get_detector_pool
from .enhanced_metrics import EnhancedMetricsCalculator

# Import existing architecture components
from .orchestrator import AnalysisOrchestrator
from .recommendation_engine import RecommendationEngine

__all__ = [
    "AnalysisOrchestrator",
    "ConfigurationManager",
    "DetectorPool",
    "EnhancedMetricsCalculator",
    "RecommendationEngine",
    "ViolationAggregator",
    "get_detector_pool",
]
