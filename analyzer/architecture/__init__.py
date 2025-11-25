# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
Architecture Components Module
==============================

Specialized components extracted from UnifiedConnascenceAnalyzer god object.
All components follow NASA Rule 4 compliance (functions under 60 lines).

Includes performance optimization components like DetectorPool.

Phase 7 Additions (Loop 2 Three-Loop System):
- MonitoringCoordinator: 9 methods for memory/resource monitoring
- StreamingCoordinator: 5 methods for streaming analysis
- ResultBuilder: 11 methods for result construction
"""

# Import detector pool for performance optimization
from .aggregator import ViolationAggregator
from .configuration_manager import ConfigurationManager
from .detector_pool import DetectorPool, get_detector_pool
from .enhanced_metrics import EnhancedMetricsCalculator

# Import existing architecture components
from .orchestrator import AnalysisOrchestrator
from .recommendation_engine import RecommendationEngine
from .report_generator import ReportGenerator

# Phase 7: New coordinators extracted from UnifiedConnascenceAnalyzer
from .monitoring_coordinator import MonitoringCoordinator
from .streaming_coordinator import StreamingCoordinator
from .result_builder import ResultBuilder

__all__ = [
    "AnalysisOrchestrator",
    "ConfigurationManager",
    "DetectorPool",
    "EnhancedMetricsCalculator",
    "MonitoringCoordinator",
    "RecommendationEngine",
    "ReportGenerator",
    "ResultBuilder",
    "StreamingCoordinator",
    "ViolationAggregator",
    "get_detector_pool",
]
