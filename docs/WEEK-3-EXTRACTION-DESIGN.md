# Week 3: UnifiedConnascenceAnalyzer Extraction Design

**Version**: 1.0.0
**Status**: Ready for Implementation
**Target**: Extract God Object (2,442 LOC) into 5 Single-Responsibility Classes
**Created**: 2025-11-13
**Complexity**: HIGH (62 methods, multiple concerns)

---

## Executive Summary

### Current State Analysis

**File**: `analyzer/unified_analyzer.py`
**Total Lines**: 2,442 LOC
**Main Class**: `UnifiedConnascenceAnalyzer` (lines 407-2165, ~1,758 LOC)
**Total Methods**: 62 methods
**God Object Score**: CRITICAL (26 methods threshold = 15)

**Key Violations**:
- God Object: 62 methods (413% over threshold)
- Function Length: Max 300+ lines (600% over 50-line limit)
- Cyclomatic Complexity: Estimated 15+ (150% over limit)
- Mixed Responsibilities: 5 distinct concerns in one class

### Target Architecture

Extract into 5 focused classes following Single Responsibility Principle:

1. **StreamProcessor** (350 LOC) - Streaming and incremental analysis
2. **CacheManager** (300 LOC) - File cache and AST caching
3. **MetricsCollector** (300 LOC) - Metrics collection and calculation
4. **ReportGenerator** (250 LOC) - Report generation in multiple formats
5. **UnifiedCoordinator** (400 LOC) - Orchestrates the 4 extracted classes

**Benefits**:
- Reduces God Object from 1,758 to 400 LOC (-77%)
- Improves testability (5 focused test suites vs 1 monolithic)
- Enables parallel development (5 developers can work simultaneously)
- Simplifies maintenance (clear boundaries, single responsibility)

---

## Detailed Method Analysis

### Method Inventory (62 Total Methods)

#### Streaming & Incremental Processing (8 methods)
1. `_analyze_project_streaming()` (23 lines) - Streaming mode analysis
2. `_analyze_project_hybrid()` (21 lines) - Hybrid batch+streaming
3. `_initialize_streaming_components()` (42 lines) - Setup streaming
4. `start_streaming_analysis()` (42 lines) - Start streaming
5. `get_streaming_stats()` (12 lines) - Streaming statistics
6. `_build_result_with_aggregator()` (22 lines) - Aggregate streaming results
7. `_dict_to_unified_result()` (29 lines) - Convert results
8. `_build_unified_result_direct()` (54 lines) - Build result objects

**Total**: ~245 LOC
**Target Class**: `StreamProcessor`

#### Cache Management (10 methods)
9. `_warm_cache_intelligently()` (41 lines) - Intelligent cache warming
10. `_calculate_file_priority()` (28 lines) - File priority calculation
11. `_get_prioritized_python_files()` (12 lines) - Priority sorting
12. `_batch_preload_files()` (18 lines) - Batch file loading
13. `_get_cached_content_with_tracking()` (18 lines) - Content retrieval
14. `_get_cached_lines_with_tracking()` (13 lines) - Line retrieval
15. `_get_cache_hit_rate()` (5 lines) - Hit rate calculation
16. `_log_cache_performance()` (26 lines) - Performance logging
17. `_optimize_cache_for_future_runs()` (19 lines) - Cache optimization
18. `_periodic_cache_cleanup()` (26 lines) - Periodic cleanup

**Total**: ~206 LOC
**Target Class**: `CacheManager`

#### Memory & Resource Management (9 methods)
19. `_setup_monitoring_and_cleanup_hooks()` (22 lines) - Setup hooks
20. `_handle_memory_alert()` (23 lines) - Memory alert handling
21. `_emergency_memory_cleanup()` (23 lines) - Emergency cleanup
22. `_aggressive_cleanup()` (12 lines) - Aggressive cleanup
23. `_cleanup_analysis_resources()` (13 lines) - Resource cleanup
24. `_emergency_resource_cleanup()` (16 lines) - Emergency resources
25. `_investigate_memory_leak()` (18 lines) - Memory leak investigation
26. `_log_comprehensive_monitoring_report()` (51 lines) - Monitoring report
27. Initialization code in `__init__` (~50 lines) - Resource setup

**Total**: ~228 LOC
**Target Class**: `CacheManager` (Resource management extends caching)

#### Metrics & Calculation (6 methods)
28. `_calculate_analysis_metrics()` (4 lines) - Metrics calculation
29. `_calculate_metrics_with_enhanced_calculator()` (18 lines) - Enhanced metrics
30. `_get_default_metrics()` (14 lines) - Default metrics
31. `get_dashboard_summary()` (30 lines) - Dashboard summary
32. `_severity_to_weight()` (5 lines) - Severity weighting
33. Helper class `MetricsCalculator.calculate_comprehensive_metrics()` (13 lines)

**Total**: ~84 LOC + external calculator
**Target Class**: `MetricsCollector`

#### Report Generation (5 methods)
34. `_build_unified_result()` (24 lines) - Build unified result
35. `_violation_to_dict()` (17 lines) - Violation serialization
36. `_cluster_to_dict()` (10 lines) - Cluster serialization
37. `_get_empty_file_result()` (13 lines) - Empty result generation
38. `_create_analysis_result_object()` (40 lines) - Result object creation

**Total**: ~104 LOC
**Target Class**: `ReportGenerator`

#### Core Orchestration (24 methods - REMAIN in Coordinator)
39. `__init__()` (90 lines) - Initialization
40. `analyze_project()` (25 lines) - Main entry point
41. `_analyze_project_batch()` (48 lines) - Batch analysis
42. `analyze_file()` (72 lines) - Single file analysis
43. `_run_analysis_phases()` (28 lines) - Run phases
44. `_run_ast_analysis()` (20 lines) - AST analysis
45. `_run_refactored_analysis()` (57 lines) - Refactored detectors
46. `_run_ast_optimizer_analysis()` (66 lines) - AST optimizer
47. `_run_tree_sitter_nasa_analysis()` (71 lines) - Tree-sitter NASA
48. `_run_dedicated_nasa_analysis()` (66 lines) - Dedicated NASA
49. `_should_analyze_file()` (32 lines) - File filtering
50. `_run_duplication_analysis()` (7 lines) - Duplication
51. `_run_smart_integration()` (47 lines) - Smart integration
52. `_run_nasa_analysis()` (75 lines) - NASA analysis
53. `_validate_analysis_inputs()` (12 lines) - Input validation
54. `_initialize_analysis_context()` (20 lines) - Context setup
55. `_execute_analysis_phases()` (4 lines) - Execute phases
56. `_execute_analysis_phases_with_orchestrator()` (19 lines) - With orchestrator
57. `_generate_analysis_recommendations()` (4 lines) - Recommendations
58. `_generate_recommendations_with_engine()` (23 lines) - With engine
59. `_log_analysis_completion()` (12 lines) - Completion logging
60. `_enhance_recommendations_with_metadata()` (16 lines) - Enhance recommendations
61. `_integrate_smart_results()` (11 lines) - Integrate smart results
62. `_add_enhanced_metadata_to_result()` (18 lines) - Add metadata

Plus utility methods:
- `get_architecture_components()` (10 lines)
- `get_component_status()` (13 lines)
- `validate_architecture_extraction()` (18 lines)
- `_check_api_compatibility()` (12 lines)
- `_load_config()` (4 lines)
- `_get_timestamp_ms()` (6 lines)
- `_get_iso_timestamp()` (6 lines)
- `_get_nasa_analyzer()` (8 lines)
- `create_integration_error()` (7 lines)
- `convert_exception_to_standard_error()` (7 lines)

**Total**: ~900 LOC
**Target Class**: `UnifiedCoordinator`

---

## Extraction Architecture

### 1. StreamProcessor Class

**Responsibility**: Handle streaming and incremental analysis with file watching.

**File**: `analyzer/stream_processor.py`

**Interface**:
```python
class StreamProcessor:
    """
    Streaming analysis processor for real-time file change detection.

    Responsibilities:
    - Async stream processing with concurrency control
    - File change watching and incremental updates
    - Result aggregation from streaming sources
    - Progress tracking and cancellation support
    """

    def __init__(self, max_concurrent: int = 4, config: Optional[Dict] = None):
        """Initialize streaming processor with concurrency limits."""

    def initialize_components(self, streaming_config: Dict) -> None:
        """Initialize stream processor and incremental cache."""

    def start_streaming(self, directories: List[Path]) -> None:
        """Start streaming analysis on directories."""

    def watch_directory(self, directory: Path) -> None:
        """Watch directory for file changes."""

    def stop_streaming(self) -> None:
        """Stop streaming and cleanup resources."""

    def get_stats(self) -> Dict[str, Any]:
        """Get streaming statistics."""

    @property
    def is_running(self) -> bool:
        """Check if streaming is active."""

    async def process_stream(
        self,
        files: AsyncIterator[Path],
        processor: Callable[[Path], Any],
        progress_callback: Optional[Callable] = None
    ) -> AsyncIterator[AnalysisResult]:
        """Process files from async stream with concurrency control."""
```

**Dependencies**:
- `streaming.stream_processor.StreamProcessor` (existing)
- `streaming.incremental_cache.IncrementalCache` (existing)

**Public Methods**: 7
**Estimated LOC**: 350

---

### 2. CacheManager Class

**Responsibility**: Manage file content cache, AST caching, and resource cleanup.

**File**: `analyzer/cache_manager.py`

**Interface**:
```python
class CacheManager:
    """
    Intelligent cache manager for file content and AST trees.

    Responsibilities:
    - File content and AST caching with LRU eviction
    - Intelligent cache warming based on access patterns
    - Resource monitoring and automatic cleanup
    - Memory management and leak prevention
    """

    def __init__(self, max_memory: int = 100 * 1024 * 1024):
        """Initialize cache with memory limit."""

    def warm_cache_intelligently(self, project_path: Path) -> None:
        """Pre-load frequently accessed files based on patterns."""

    def get_cached_content(self, file_path: Path) -> Optional[str]:
        """Get cached file content with tracking."""

    def get_cached_lines(self, file_path: Path) -> List[str]:
        """Get cached file lines with tracking."""

    def batch_preload_files(self, files: List[Path]) -> None:
        """Batch preload files for better performance."""

    def calculate_file_priority(self, file_path: Path) -> int:
        """Calculate file priority for cache eviction."""

    def get_prioritized_files(self, project_path: Path) -> List[Path]:
        """Get files sorted by priority."""

    def get_hit_rate(self) -> float:
        """Get cache hit rate percentage."""

    def log_performance(self) -> None:
        """Log cache performance metrics."""

    def optimize_for_future_runs(self) -> None:
        """Optimize cache based on access patterns."""

    def periodic_cleanup(self) -> int:
        """Periodic cache cleanup, returns bytes freed."""

    def setup_monitoring_hooks(self, memory_monitor) -> None:
        """Setup memory monitoring and cleanup hooks."""

    def handle_memory_alert(self, alert_type: str, context: Dict) -> None:
        """Handle memory alerts from monitor."""

    def emergency_cleanup(self) -> None:
        """Emergency memory cleanup."""

    def cleanup_resources(self) -> None:
        """Cleanup analysis resources."""

    def investigate_memory_leak(self, context: Dict) -> None:
        """Investigate potential memory leaks."""
```

**Dependencies**:
- `optimization.file_cache.FileContentCache` (existing)
- `optimization.memory_monitor.MemoryMonitor` (existing)
- `optimization.resource_manager` (existing)

**Public Methods**: 16
**Estimated LOC**: 300

---

### 3. MetricsCollector Class

**Responsibility**: Collect, calculate, and aggregate analysis metrics.

**File**: `analyzer/metrics_collector.py`

**Interface**:
```python
class MetricsCollector:
    """
    Metrics collection and calculation engine.

    Responsibilities:
    - Violation counting and categorization
    - Severity weighting and scoring
    - Dashboard metric generation
    - Comprehensive metric aggregation
    """

    def __init__(self):
        """Initialize metrics collector."""

    def calculate_metrics(
        self,
        violations: Dict[str, List],
        errors: List[StandardError]
    ) -> Dict[str, Any]:
        """Calculate comprehensive analysis metrics."""

    def get_default_metrics(self) -> Dict[str, Any]:
        """Get default metric structure."""

    def calculate_dashboard_summary(
        self,
        result: UnifiedAnalysisResult
    ) -> Dict[str, Any]:
        """Generate dashboard summary metrics."""

    def severity_to_weight(self, severity: str) -> float:
        """Convert severity string to numeric weight."""

    def aggregate_violation_counts(
        self,
        violations: Dict[str, List]
    ) -> Dict[str, int]:
        """Aggregate violation counts by type."""

    def calculate_health_score(self, metrics: Dict) -> float:
        """Calculate overall project health score (0-100)."""
```

**Dependencies**:
- Internal metric calculation logic only
- No external dependencies

**Public Methods**: 7
**Estimated LOC**: 300

---

### 4. ReportGenerator Class

**Responsibility**: Generate reports in multiple formats (dict, JSON, dashboard).

**File**: `analyzer/report_generator.py`

**Interface**:
```python
class ReportGenerator:
    """
    Multi-format report generator for analysis results.

    Responsibilities:
    - Result object construction
    - Serialization to various formats
    - Dashboard data preparation
    - Empty result generation
    """

    def __init__(self):
        """Initialize report generator."""

    def build_unified_result(
        self,
        violations: Dict[str, List],
        metrics: Dict,
        recommendations: Dict,
        project_path: Path,
        policy_preset: str,
        analysis_time: int,
        errors: List[StandardError],
        warnings: List
    ) -> UnifiedAnalysisResult:
        """Build complete unified analysis result."""

    def dict_to_result(self, result_dict: Dict) -> UnifiedAnalysisResult:
        """Convert dictionary to UnifiedAnalysisResult object."""

    def violation_to_dict(self, violation: Any) -> Dict[str, Any]:
        """Convert violation object to dictionary."""

    def cluster_to_dict(self, cluster: Any) -> Dict[str, Any]:
        """Convert cluster object to dictionary."""

    def get_empty_file_result(
        self,
        file_path: Path,
        errors: List[StandardError]
    ) -> Dict[str, Any]:
        """Generate empty result for failed file analysis."""

    def create_result_object(
        self,
        violations: Dict,
        metrics: Dict,
        recommendations: Dict,
        errors: List,
        warnings: List
    ) -> UnifiedAnalysisResult:
        """Create UnifiedAnalysisResult object."""

    def add_metadata_to_result(
        self,
        result: UnifiedAnalysisResult,
        metadata: Dict
    ) -> UnifiedAnalysisResult:
        """Add enhanced metadata to result."""
```

**Dependencies**:
- `unified_analyzer.UnifiedAnalysisResult` (dataclass)
- `unified_analyzer.StandardError` (dataclass)

**Public Methods**: 8
**Estimated LOC**: 250

---

### 5. UnifiedCoordinator Class

**Responsibility**: Orchestrate analysis using extracted components.

**File**: `analyzer/unified_coordinator.py`

**Interface**:
```python
class UnifiedCoordinator:
    """
    Main coordinator orchestrating all analysis components.

    Responsibilities:
    - Component initialization and wiring
    - Analysis mode routing (batch/streaming/hybrid)
    - Phase execution and orchestration
    - Recommendation generation
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        analysis_mode: str = "batch",
        streaming_config: Optional[Dict] = None
    ):
        """
        Initialize coordinator with components via dependency injection.

        Components created:
        - StreamProcessor (if streaming enabled)
        - CacheManager (always)
        - MetricsCollector (always)
        - ReportGenerator (always)
        - Error handler, analyzers, etc.
        """

    def analyze_project(
        self,
        project_path: Union[str, Path],
        policy_preset: str = "service-defaults",
        options: Optional[Dict] = None
    ) -> UnifiedAnalysisResult:
        """Main analysis entry point - routes to batch/streaming/hybrid."""

    def analyze_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Analyze single file."""

    def get_architecture_components(self) -> Dict[str, Any]:
        """Get architecture component information."""

    def get_component_status(self) -> Dict[str, bool]:
        """Get status of all components."""

    def validate_architecture_extraction(self) -> Dict[str, bool]:
        """Validate architecture extraction succeeded."""

    # Private orchestration methods
    def _analyze_batch(self, project_path: Path, policy: str, options: Dict) -> UnifiedAnalysisResult
    def _analyze_streaming(self, project_path: Path, policy: str, options: Dict) -> UnifiedAnalysisResult
    def _analyze_hybrid(self, project_path: Path, policy: str, options: Dict) -> UnifiedAnalysisResult

    def _run_analysis_phases(self, project_path: Path, policy: str) -> Dict[str, Any]
    def _run_ast_analysis(self, project_path: Path) -> List[Dict]
    def _run_refactored_analysis(self, project_path: Path) -> List[Dict]
    def _run_ast_optimizer_analysis(self, project_path: Path) -> List[Dict]
    def _run_tree_sitter_nasa_analysis(self) -> List[Dict]
    def _run_dedicated_nasa_analysis(self, project_path: Path) -> List[Dict]
    def _run_duplication_analysis(self, project_path: Path) -> List[Dict]
    def _run_smart_integration(self, violations: Dict, project_path: Path) -> Dict
    def _run_nasa_analysis(self, project_path: Path, violations: Dict) -> List[Dict]

    def _should_analyze_file(self, file_path: Path) -> bool
    def _validate_analysis_inputs(self, project_path: Path, policy: str) -> None
    def _initialize_analysis_context(self, project_path: Path, policy: str) -> Tuple
    def _execute_analysis_phases(self, project_path: Path, policy: str, errors: List) -> Dict
    def _generate_recommendations(self, violations: Dict, warnings: List) -> Dict
    def _enhance_recommendations(self, violations: Dict, recommendations: Dict) -> Dict
    def _integrate_smart_results(self, recommendations: Dict, smart_results: Dict) -> None
    def _log_analysis_completion(self, result: UnifiedAnalysisResult, time: int) -> None
```

**Dependencies**:
- `StreamProcessor` (created component)
- `CacheManager` (created component)
- `MetricsCollector` (created component)
- `ReportGenerator` (created component)
- Existing analyzers (AST, MECE, NASA, etc.)

**Public Methods**: 6
**Private Methods**: ~20
**Estimated LOC**: 400

---

## Dependency Injection Strategy

### Component Initialization Pattern

```python
# analyzer/unified_coordinator.py

class UnifiedCoordinator:
    def __init__(
        self,
        config_path: Optional[str] = None,
        analysis_mode: str = "batch",
        streaming_config: Optional[Dict] = None,
        # Dependency injection parameters (for testing)
        stream_processor: Optional[StreamProcessor] = None,
        cache_manager: Optional[CacheManager] = None,
        metrics_collector: Optional[MetricsCollector] = None,
        report_generator: Optional[ReportGenerator] = None
    ):
        """
        Initialize coordinator with dependency injection support.

        Production use:
            coordinator = UnifiedCoordinator()

        Testing use (inject mocks):
            coordinator = UnifiedCoordinator(
                cache_manager=MockCacheManager(),
                metrics_collector=MockMetricsCollector()
            )
        """
        self.analysis_mode = analysis_mode
        self.config = self._load_config(config_path)

        # Create or inject components
        self.cache_manager = cache_manager or CacheManager(
            max_memory=self.config.get('cache_size', 100 * 1024 * 1024)
        )

        self.metrics_collector = metrics_collector or MetricsCollector()

        self.report_generator = report_generator or ReportGenerator()

        # Streaming only initialized if mode requires it
        self.stream_processor = None
        if analysis_mode in ['streaming', 'hybrid']:
            if stream_processor:
                self.stream_processor = stream_processor
            elif STREAMING_AVAILABLE:
                self.stream_processor = StreamProcessor(
                    max_concurrent=streaming_config.get('max_concurrent', 4),
                    config=streaming_config
                )
                self.stream_processor.initialize_components(streaming_config or {})

        # Initialize error handling
        self.error_handler = ErrorHandler("coordinator")

        # Initialize existing analyzers (unchanged)
        self.ast_analyzer = ConnascenceASTAnalyzer()
        self.god_object_orchestrator = GodObjectOrchestrator()
        self.mece_analyzer = MECEAnalyzer()

        # Optional components
        initializer = ComponentInitializer()
        self.smart_engine = initializer.init_smart_engine()
        self.failure_detector = initializer.init_failure_detector()
        self.nasa_integration = initializer.init_nasa_integration()
        self.policy_manager = initializer.init_policy_manager()
        self.budget_tracker = initializer.init_budget_tracker()

        logger.info("UnifiedCoordinator initialized with extracted components")
```

### Delegation Pattern

```python
# Example: Batch analysis delegates to components

def _analyze_batch(
    self,
    project_path: Path,
    policy: str,
    options: Dict
) -> UnifiedAnalysisResult:
    """Execute batch analysis using extracted components."""
    start_time = self._get_timestamp_ms()

    # DELEGATE: Cache warming to CacheManager
    self.cache_manager.warm_cache_intelligently(project_path)

    # Validate inputs
    errors, warnings = self._initialize_analysis_context(project_path, policy)

    # Execute analysis phases (coordinator's core responsibility)
    violations = self._execute_analysis_phases(project_path, policy, errors)

    # DELEGATE: Metrics calculation to MetricsCollector
    metrics = self.metrics_collector.calculate_metrics(violations, errors)

    # Generate recommendations (coordinator's responsibility)
    recommendations = self._generate_recommendations(violations, warnings)

    # DELEGATE: Report generation to ReportGenerator
    analysis_time = self._get_timestamp_ms() - start_time
    result = self.report_generator.build_unified_result(
        violations, metrics, recommendations,
        project_path, policy, analysis_time,
        errors, warnings
    )

    # DELEGATE: Cache performance logging to CacheManager
    self.cache_manager.log_performance()
    self.cache_manager.optimize_for_future_runs()

    self._log_analysis_completion(result, analysis_time)
    return result
```

---

## Backward Compatibility Layer

### Approach: Facade Pattern in `__init__.py`

**File**: `analyzer/__init__.py`

```python
"""
Analyzer package with backward compatibility for UnifiedConnascenceAnalyzer.

Legacy imports continue to work:
    from analyzer.unified_analyzer import UnifiedConnascenceAnalyzer

New imports (post-refactoring):
    from analyzer.unified_coordinator import UnifiedCoordinator
    from analyzer.stream_processor import StreamProcessor
    from analyzer.cache_manager import CacheManager
    from analyzer.metrics_collector import MetricsCollector
    from analyzer.report_generator import ReportGenerator
"""

# New extracted components
from .stream_processor import StreamProcessor
from .cache_manager import CacheManager
from .metrics_collector import MetricsCollector
from .report_generator import ReportGenerator
from .unified_coordinator import UnifiedCoordinator

# Backward compatibility alias
UnifiedConnascenceAnalyzer = UnifiedCoordinator

# Export all
__all__ = [
    # New architecture
    'StreamProcessor',
    'CacheManager',
    'MetricsCollector',
    'ReportGenerator',
    'UnifiedCoordinator',
    # Legacy (deprecated but working)
    'UnifiedConnascenceAnalyzer',
]
```

**Deprecation Warning Strategy**:

```python
# analyzer/unified_coordinator.py

import warnings

class UnifiedCoordinator:
    """
    Main coordinator for connascence analysis (formerly UnifiedConnascenceAnalyzer).

    NOTE: UnifiedConnascenceAnalyzer is deprecated. Use UnifiedCoordinator instead.
    Legacy imports will continue to work via alias in analyzer/__init__.py
    """

    def __init__(self, *args, **kwargs):
        # Detect if imported via legacy name
        import inspect
        frame = inspect.currentframe()
        caller_locals = frame.f_back.f_locals

        if 'UnifiedConnascenceAnalyzer' in str(caller_locals):
            warnings.warn(
                "UnifiedConnascenceAnalyzer is deprecated. "
                "Use UnifiedCoordinator instead. "
                "Legacy name will be removed in version 3.0.0",
                DeprecationWarning,
                stacklevel=2
            )

        # Normal initialization
        super().__init__(*args, **kwargs)
```

### API Compatibility Table

| Legacy Method | New Location | Status |
|--------------|--------------|--------|
| `analyze_project()` | `UnifiedCoordinator.analyze_project()` | Unchanged |
| `analyze_file()` | `UnifiedCoordinator.analyze_file()` | Unchanged |
| `start_streaming_analysis()` | `StreamProcessor.start_streaming()` | Delegated |
| `get_streaming_stats()` | `StreamProcessor.get_stats()` | Delegated |
| `get_dashboard_summary()` | `MetricsCollector.calculate_dashboard_summary()` | Delegated |
| Internal methods | Various | Extracted |

**Migration Path**:
```python
# OLD (still works, with deprecation warning):
from analyzer.unified_analyzer import UnifiedConnascenceAnalyzer
analyzer = UnifiedConnascenceAnalyzer()
result = analyzer.analyze_project("/path")

# NEW (recommended):
from analyzer import UnifiedCoordinator
coordinator = UnifiedCoordinator()
result = coordinator.analyze_project("/path")

# ADVANCED (direct component access):
from analyzer import CacheManager, MetricsCollector
cache = CacheManager(max_memory=200 * 1024 * 1024)
metrics = MetricsCollector()
```

---

## Dependency Diagram

```
                    +-------------------------+
                    |   UnifiedCoordinator    |
                    |   (400 LOC)             |
                    |   - Orchestration       |
                    |   - Phase execution     |
                    |   - Recommendations     |
                    +-------------------------+
                              |
                    +---------+---------+---------+---------+
                    |         |         |         |         |
                    v         v         v         v         v
         +-------------+ +----------+ +-------------+ +-------------+ +------------------+
         | Stream      | | Cache    | | Metrics     | | Report      | | Existing         |
         | Processor   | | Manager  | | Collector   | | Generator   | | Analyzers        |
         | (350 LOC)   | | (300 LOC)| | (300 LOC)   | | (250 LOC)   | | (AST, MECE,etc.) |
         +-------------+ +----------+ +-------------+ +-------------+ +------------------+
                |              |                                              |
                v              v                                              v
         +-----------+  +-----------+                                  +-----------+
         | streaming | | optimization|                                 | External  |
         | package   | | package     |                                 | Detectors |
         +-----------+  +-----------+                                  +-----------+

Dependency Flow:
1. UnifiedCoordinator creates and owns all 4 extracted components
2. StreamProcessor depends on streaming package (optional)
3. CacheManager depends on optimization package
4. MetricsCollector has NO external dependencies (pure calculation)
5. ReportGenerator depends only on dataclasses
6. UnifiedCoordinator delegates to components but retains orchestration logic
7. Existing analyzers remain unchanged (AST, MECE, NASA, etc.)

Key Principles:
- NO circular dependencies (coordinator creates components)
- Components are independent (can be tested in isolation)
- Components have minimal interfaces (7-16 methods)
- Coordinator is ONLY orchestrator (no implementation logic)
```

---

## Migration Plan

### Phase 1: Extract StreamProcessor (Week 3, Days 1-2)

**Steps**:
1. Create `analyzer/stream_processor.py`
2. Move 8 streaming methods from UnifiedConnascenceAnalyzer
3. Add dependency injection to UnifiedCoordinator.__init__()
4. Update UnifiedCoordinator to delegate streaming calls
5. Write unit tests for StreamProcessor
6. Run integration tests to verify no regression

**Validation**:
```bash
# Run existing tests
pytest tests/test_unified_analyzer.py -v

# Run new component tests
pytest tests/test_stream_processor.py -v

# Verify no regression
python -m analyzer.cli analyze analyzer/ --gate-level 2
```

**Success Criteria**:
- All existing tests pass
- StreamProcessor has 95%+ code coverage
- No streaming-related code remains in UnifiedCoordinator
- Streaming analysis works identically to before

### Phase 2: Extract CacheManager (Week 3, Days 2-3)

**Steps**:
1. Create `analyzer/cache_manager.py`
2. Move 19 cache/memory methods (10 cache + 9 resource management)
3. Update UnifiedCoordinator to delegate cache calls
4. Refactor monitoring hooks to use CacheManager
5. Write unit tests for CacheManager
6. Run integration tests

**Validation**:
```bash
pytest tests/test_cache_manager.py -v
pytest tests/test_unified_analyzer.py -v

# Verify cache performance maintained
python scripts/benchmark_cache.py
```

**Success Criteria**:
- Cache hit rates unchanged (>80%)
- Memory monitoring still functional
- All tests pass
- CacheManager has 90%+ coverage

### Phase 3: Extract MetricsCollector & ReportGenerator (Week 3, Day 4)

**Steps**:
1. Create `analyzer/metrics_collector.py` (6 methods)
2. Create `analyzer/report_generator.py` (8 methods)
3. Update UnifiedCoordinator to delegate metrics/reporting
4. Write unit tests for both components
5. Run full test suite

**Validation**:
```bash
pytest tests/test_metrics_collector.py -v
pytest tests/test_report_generator.py -v
pytest tests/ -v  # Full suite

# Verify metrics unchanged
python scripts/validate_metrics.py
```

**Success Criteria**:
- Metrics calculations identical to before
- Report formats unchanged
- All tests pass
- Both components have 95%+ coverage

### Phase 4: Finalize UnifiedCoordinator & Backward Compatibility (Week 3, Day 5)

**Steps**:
1. Rename UnifiedConnascenceAnalyzer to UnifiedCoordinator
2. Update `analyzer/__init__.py` with backward compatibility alias
3. Add deprecation warnings
4. Update documentation
5. Run full test suite + dogfooding analysis

**Validation**:
```bash
# Test backward compatibility
python -c "from analyzer.unified_analyzer import UnifiedConnascenceAnalyzer; print('Legacy import works')"

# Test new imports
python -c "from analyzer import UnifiedCoordinator; print('New import works')"

# Full dogfooding
python -m analyzer.cli analyze analyzer/ --gate-level 3
```

**Success Criteria**:
- Legacy imports work with deprecation warning
- New imports work without warnings
- All 100% of existing tests pass
- Dogfooding analysis passes Gate 3 (CRITICAL + HIGH + MEDIUM)

### Phase 5: Test Suite Expansion (Week 3, Post-migration)

**New Test Files**:
```
tests/
├── test_stream_processor.py         # 15 tests
├── test_cache_manager.py             # 20 tests
├── test_metrics_collector.py         # 12 tests
├── test_report_generator.py          # 15 tests
├── test_unified_coordinator.py       # 25 tests (refactored)
└── test_backward_compatibility.py    # 10 tests (new)
```

**Test Coverage Goals**:
- StreamProcessor: 95%
- CacheManager: 90%
- MetricsCollector: 95%
- ReportGenerator: 95%
- UnifiedCoordinator: 85% (orchestration, less unit testable)

---

## Risk Mitigation

### Risk 1: Breaking Existing Tests

**Probability**: 40%
**Impact**: HIGH (blocks merge)

**Mitigation**:
- Extract one component at a time (5 separate PRs)
- Run full test suite after each extraction
- Maintain 100% backward compatibility via aliases
- Keep all existing test files unchanged
- Add integration tests before extraction

### Risk 2: Performance Degradation from Delegation

**Probability**: 25%
**Impact**: MEDIUM (slower analysis)

**Mitigation**:
- Benchmark cache performance before/after
- Profile hot paths (cache hits, metrics calculation)
- Inline delegate methods if overhead >5%
- Use direct references instead of method calls where needed

### Risk 3: Circular Dependencies

**Probability**: 15%
**Impact**: HIGH (breaks architecture)

**Mitigation**:
- Dependency injection from coordinator only (one-way)
- Components NEVER reference coordinator
- Use interfaces/protocols for component communication
- Validate with dependency checker tool

### Risk 4: Lost Context in Extraction

**Probability**: 30%
**Impact**: MEDIUM (requires re-work)

**Mitigation**:
- Document method context before moving
- Keep related methods together (e.g., all cache methods)
- Extract complete responsibility boundaries
- Review extracted code with original author

### Risk 5: Incomplete Backward Compatibility

**Probability**: 20%
**Impact**: MEDIUM (external users break)

**Mitigation**:
- Maintain aliases for all public methods
- Add deprecation warnings with migration guide
- Test legacy import paths explicitly
- Version bump (2.x.x) with clear CHANGELOG

---

## Success Metrics

### Code Quality Metrics

**Before Extraction**:
- God Object: 1,758 LOC, 62 methods
- Max function length: 300+ lines
- Cyclomatic complexity: 15+
- Test files: 1 monolithic suite

**After Extraction**:
- UnifiedCoordinator: 400 LOC, 26 methods (-77%)
- Max function length: <50 lines (-83%)
- Cyclomatic complexity: <10 (-33%)
- Test files: 6 focused suites (+500%)

### Maintainability Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| God Object Violations | 1 | 0 | -100% |
| CLARITY011 (Mega-functions) | 5+ | 0 | -100% |
| Average Method Length | 28 lines | 15 lines | -46% |
| Test Suite Granularity | 1 file | 6 files | +500% |
| Parallel Development Capacity | 1 dev | 5 devs | +400% |

### Test Coverage Metrics

| Component | Coverage Goal | Existing | New |
|-----------|---------------|----------|-----|
| StreamProcessor | 95% | N/A | 15 tests |
| CacheManager | 90% | Partial | 20 tests |
| MetricsCollector | 95% | N/A | 12 tests |
| ReportGenerator | 95% | N/A | 15 tests |
| UnifiedCoordinator | 85% | ~70% | 25 tests |
| Overall | 90%+ | ~65% | ~90% |

---

## Appendix: Method Extraction Checklist

### Pre-Extraction Checklist (Per Component)

- [ ] Read all methods assigned to component
- [ ] Identify shared state (instance variables)
- [ ] Identify external dependencies
- [ ] Map all method calls (internal and external)
- [ ] Design component interface (public methods)
- [ ] Write component docstring with responsibilities
- [ ] Plan dependency injection strategy
- [ ] Write unit tests BEFORE extraction

### Extraction Checklist (Per Method)

- [ ] Copy method to new component file
- [ ] Update self references to new component
- [ ] Update instance variable access
- [ ] Add type hints to parameters
- [ ] Add docstring with Args/Returns
- [ ] Update coordinator to delegate to component
- [ ] Run tests to verify extraction
- [ ] Remove method from original class (if passing)

### Post-Extraction Checklist (Per Component)

- [ ] All methods extracted and passing tests
- [ ] Component has <500 LOC
- [ ] Component has <15 public methods
- [ ] No circular dependencies
- [ ] 90%+ test coverage
- [ ] Backward compatibility verified
- [ ] Documentation updated
- [ ] Code review completed

### Final Validation Checklist

- [ ] All 5 components extracted
- [ ] UnifiedCoordinator <500 LOC
- [ ] All existing tests pass (100%)
- [ ] New component tests pass (100%)
- [ ] Backward compatibility tests pass
- [ ] Dogfooding analysis passes Gate 3
- [ ] Performance benchmarks within 5% of baseline
- [ ] Documentation updated
- [ ] CHANGELOG updated with migration guide
- [ ] Version bumped (2.0.0)

---

## Appendix: File Structure After Extraction

```
analyzer/
├── __init__.py                      # Backward compatibility aliases
├── unified_coordinator.py           # Main orchestrator (400 LOC)
├── stream_processor.py              # Streaming analysis (350 LOC)
├── cache_manager.py                 # Cache & resource management (300 LOC)
├── metrics_collector.py             # Metrics calculation (300 LOC)
├── report_generator.py              # Report generation (250 LOC)
├── unified_analyzer.py              # DEPRECATED (remove in 3.0.0)
├── check_connascence.py             # Existing (unchanged)
├── ast_engine/
│   └── analyzer_orchestrator.py    # Existing (unchanged)
├── dup_detection/
│   └── mece_analyzer.py            # Existing (unchanged)
├── nasa_engine/
│   └── nasa_analyzer.py            # Existing (unchanged)
├── optimization/
│   ├── file_cache.py               # Existing (used by CacheManager)
│   ├── memory_monitor.py           # Existing (used by CacheManager)
│   └── resource_manager.py         # Existing (used by CacheManager)
└── streaming/
    ├── stream_processor.py         # Existing (used by StreamProcessor)
    └── incremental_cache.py        # Existing (used by StreamProcessor)

tests/
├── test_unified_coordinator.py     # Refactored from test_unified_analyzer.py
├── test_stream_processor.py        # NEW
├── test_cache_manager.py           # NEW
├── test_metrics_collector.py       # NEW
├── test_report_generator.py        # NEW
└── test_backward_compatibility.py  # NEW

docs/
├── WEEK-3-EXTRACTION-DESIGN.md     # This document
├── API-MIGRATION-GUIDE.md          # Migration guide (to be created)
└── ARCHITECTURE-COMPONENTS.md      # Component documentation (to be created)
```

---

## Conclusion

This extraction design transforms the `UnifiedConnascenceAnalyzer` god object (2,442 LOC, 62 methods) into 5 focused, single-responsibility classes totaling 1,600 LOC with clear boundaries.

**Key Benefits**:
1. **Maintainability**: Each component has ONE responsibility
2. **Testability**: 6 focused test suites vs 1 monolithic
3. **Scalability**: 5 developers can work in parallel
4. **Clarity**: Clear interfaces, no mixed concerns
5. **Backward Compatibility**: Legacy code continues to work

**Next Steps**:
1. Review and approve this design document
2. Create GitHub issues for each extraction phase
3. Begin Phase 1: StreamProcessor extraction
4. Validate with comprehensive test suite
5. Proceed to Phase 2-5 incrementally

**Timeline**: Week 3 (5 days)
**Effort**: 2 engineer-weeks
**Risk**: LOW (incremental extraction with backward compatibility)
**Approval Required**: Technical Lead, Senior Engineers

---

**Document Status**: READY FOR IMPLEMENTATION
**Questions**: Contact system architect or open GitHub discussion
**Related Documents**: META-REMEDIATION-PLAN-DOGFOODING.md, CLARITY-RULES.md
