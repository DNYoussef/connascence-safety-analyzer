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
from .detector_pool import DetectorPool, get_detector_pool

# Import existing architecture components
from .orchestrator import AnalysisOrchestrator
from .aggregator import ViolationAggregator  
from .recommendation_engine import RecommendationEngine
from .configuration_manager import ConfigurationManager
from .enhanced_metrics import EnhancedMetricsCalculator

__all__ = [
    "DetectorPool", 
    "get_detector_pool",
    "AnalysisOrchestrator",
    "ViolationAggregator", 
    "RecommendationEngine",
    "ConfigurationManager",
    "EnhancedMetricsCalculator",
]