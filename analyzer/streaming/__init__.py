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

from .stream_processor import (
    StreamProcessor,
    FileChange,
    AnalysisRequest,
    AnalysisResult,
    FileWatcher,
    create_stream_processor,
    process_file_changes_stream,
    WATCHDOG_AVAILABLE
)

from .incremental_cache import (
    IncrementalCache,
    FileDelta,
    PartialResult,
    get_global_incremental_cache,
    clear_incremental_cache,
    CACHE_INTEGRATION_AVAILABLE
)

from .result_aggregator import (
    StreamResultAggregator,
    StreamAnalysisResult,
    AggregatedResult,
    get_global_stream_aggregator,
    add_streaming_result,
    get_streaming_dashboard_data,
    get_streaming_aggregated_result
)

from .dashboard_reporter import (
    DashboardReporter,
    DashboardMetrics,
    ViolationTrend,
    SystemHealthMetrics,
    get_global_dashboard_reporter,
    generate_dashboard_report,
    add_dashboard_metrics_sample
)

__all__ = [
    "StreamProcessor",
    "FileChange", 
    "AnalysisRequest",
    "AnalysisResult",
    "FileWatcher",
    "create_stream_processor",
    "process_file_changes_stream",
    "WATCHDOG_AVAILABLE",
    "IncrementalCache",
    "FileDelta",
    "PartialResult",
    "get_global_incremental_cache",
    "clear_incremental_cache",
    "CACHE_INTEGRATION_AVAILABLE",
    "StreamResultAggregator",
    "StreamAnalysisResult",
    "AggregatedResult", 
    "get_global_stream_aggregator",
    "add_streaming_result",
    "get_streaming_dashboard_data",
    "get_streaming_aggregated_result",
    "DashboardReporter",
    "DashboardMetrics",
    "ViolationTrend",
    "SystemHealthMetrics", 
    "get_global_dashboard_reporter",
    "generate_dashboard_report",
    "add_dashboard_metrics_sample"
]