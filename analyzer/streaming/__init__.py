"""
Streaming Analysis Components
============================

Real-time incremental analysis system with event-driven architecture.
Provides stream processing, file watching, and incremental caching capabilities
for continuous integration workflows.

Components:
- StreamProcessor: Core streaming engine with event processing
- FileWatcher: File system monitoring with debouncing
- IncrementalCache: Delta-based caching for efficient updates
"""

from .dashboard_reporter import (
    DashboardMetrics,
    DashboardReporter,
    SystemHealthMetrics,
    ViolationTrend,
    add_dashboard_metrics_sample,
    generate_dashboard_report,
    get_global_dashboard_reporter,
)
from .incremental_cache import (
    CACHE_INTEGRATION_AVAILABLE,
    FileDelta,
    IncrementalCache,
    PartialResult,
    clear_incremental_cache,
    get_global_incremental_cache,
)
from .result_aggregator import (
    AggregatedResult,
    StreamAnalysisResult,
    StreamResultAggregator,
    add_streaming_result,
    get_global_stream_aggregator,
    get_streaming_aggregated_result,
    get_streaming_dashboard_data,
)
from .stream_processor import (
    WATCHDOG_AVAILABLE,
    AnalysisRequest,
    AnalysisResult,
    FileChange,
    FileWatcher,
    StreamProcessor,
    create_stream_processor,
    process_file_changes_stream,
)

__all__ = [
    "CACHE_INTEGRATION_AVAILABLE",
    "WATCHDOG_AVAILABLE",
    "AggregatedResult",
    "AnalysisRequest",
    "AnalysisResult",
    "DashboardMetrics",
    "DashboardReporter",
    "FileChange",
    "FileDelta",
    "FileWatcher",
    "IncrementalCache",
    "PartialResult",
    "StreamAnalysisResult",
    "StreamProcessor",
    "StreamResultAggregator",
    "SystemHealthMetrics",
    "ViolationTrend",
    "add_dashboard_metrics_sample",
    "add_streaming_result",
    "clear_incremental_cache",
    "create_stream_processor",
    "generate_dashboard_report",
    "get_global_dashboard_reporter",
    "get_global_incremental_cache",
    "get_global_stream_aggregator",
    "get_streaming_aggregated_result",
    "get_streaming_dashboard_data",
    "process_file_changes_stream",
]
