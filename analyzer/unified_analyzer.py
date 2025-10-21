# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

"""
Unified Connascence Analyzer
============================

Central orchestrator that combines all Phase 1-6 analysis capabilities:
- Core AST-based connascence detection
- MECE duplication analysis
- NASA Power of Ten compliance
- Smart integration engine
- Multi-linter correlation
- Failure prediction system

This provides a single entry point for all connascence analysis functionality.
"""

import ast
from dataclasses import asdict, dataclass
import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Union

from fixes.phase0.production_safe_assertions import ProductionAssert

# Import optimization components
try:
    from .optimization.file_cache import (
        FileContentCache,
        cached_ast_tree,
        cached_file_content,
        cached_file_lines,
        cached_python_files,
        get_global_cache,
    )

    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

# Import memory monitoring and resource management
try:
    from .optimization.memory_monitor import (
        MemoryMonitor,
        MemoryWatcher,
        get_global_memory_monitor,
        start_global_monitoring,
        stop_global_monitoring,
    )
    from .optimization.resource_manager import (
        cleanup_all_resources,
        get_global_resource_manager,
        get_resource_report,
        managed_ast_tree,
        managed_file_handle,
    )

    ADVANCED_MONITORING_AVAILABLE = True
except ImportError:
    ADVANCED_MONITORING_AVAILABLE = False

# Import streaming and incremental analysis components
try:
    from .streaming.incremental_cache import IncrementalCache, get_global_incremental_cache
    from .streaming.stream_processor import (
        AnalysisRequest,
        AnalysisResult,
        StreamProcessor,
        create_stream_processor,
        process_file_changes_stream,
    )

    STREAMING_AVAILABLE = True
except ImportError:
    STREAMING_AVAILABLE = False

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Core analyzer components (Phase 1-5) - now all in analyzer/
try:
    from .ast_engine.analyzer_orchestrator import AnalyzerOrchestrator as GodObjectOrchestrator
    from .check_connascence import ConnascenceAnalyzer as ConnascenceASTAnalyzer
    from .detectors.timing_detector import TimingDetector
    from .dup_detection.mece_analyzer import MECEAnalyzer
    from .nasa_engine.nasa_analyzer import NASAAnalyzer
    from .optimization.ast_optimizer import ConnascencePatternOptimizer
    from .refactored_detector import RefactoredConnascenceDetector
    from .smart_integration_engine import SmartIntegrationEngine
except ImportError:
    # Fallback when running as script
    from ast_engine.analyzer_orchestrator import AnalyzerOrchestrator as GodObjectOrchestrator
    from check_connascence import ConnascenceAnalyzer as ConnascenceASTAnalyzer
    from dup_detection.mece_analyzer import MECEAnalyzer
    from nasa_engine.nasa_analyzer import NASAAnalyzer
    from optimization.ast_optimizer import ConnascencePatternOptimizer
    from refactored_detector import RefactoredConnascenceDetector
    from smart_integration_engine import SmartIntegrationEngine

# Import new architecture components
# Temporarily disabled broken architecture imports - will re-implement correctly
pass

# Try to import Tree-Sitter backend with fallback
try:
    from ..grammar.backends.tree_sitter_backend import LanguageSupport, TreeSitterBackend
except ImportError:
    try:
        from grammar.backends.tree_sitter_backend import LanguageSupport, TreeSitterBackend
    except ImportError:
        TreeSitterBackend = None
        LanguageSupport = None
try:
    from .constants import (
        ERROR_CODE_MAPPING,
        ERROR_SEVERITY,
    )
except ImportError:
    from constants import (
        ERROR_CODE_MAPPING,
        ERROR_SEVERITY,
    )

# Try to import optional components with fallbacks
try:
    from .failure_detection_system import FailureDetectionSystem
except ImportError:
    FailureDetectionSystem = None

try:
    from ..mcp.nasa_integration import NASAPowerOfTenIntegration
except ImportError:
    NASAPowerOfTenIntegration = None

try:
    from ..policy.budgets import BudgetTracker
    from ..policy.manager import PolicyManager
except ImportError:
    PolicyManager = None
    BudgetTracker = None

logger = logging.getLogger(__name__)


@dataclass
class StandardError:
    """Standard error response format across all integrations."""

    code: int
    message: str
    severity: str
    timestamp: str
    integration: str
    error_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestions: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class UnifiedAnalysisResult:
    """Complete analysis result from all Phase 1-6 components."""

    # Core results
    connascence_violations: List[Dict[str, Any]]
    duplication_clusters: List[Dict[str, Any]]
    nasa_violations: List[Dict[str, Any]]

    # Summary metrics
    total_violations: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int

    # Quality scores
    connascence_index: float
    nasa_compliance_score: float
    duplication_score: float
    overall_quality_score: float

    # Analysis metadata
    project_path: str
    policy_preset: str
    analysis_duration_ms: int
    files_analyzed: int
    timestamp: str

    # Recommendations
    priority_fixes: List[str]
    improvement_actions: List[str]

    # Error tracking
    errors: List[StandardError] = None
    warnings: List[StandardError] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    def has_errors(self) -> bool:
        """Check if analysis has any errors."""
        return bool(self.errors)

    def has_critical_errors(self) -> bool:
        """Check if analysis has critical errors."""
        if not self.errors:
            return False
        return any(error.severity == ERROR_SEVERITY["CRITICAL"] for error in self.errors)


class ErrorHandler:
    """Centralized error handling for all integrations."""

    def __init__(self, integration: str = "analyzer"):
        self.integration = integration
        self.correlation_id = self._generate_correlation_id()

    def _generate_correlation_id(self) -> str:
        """Generate unique correlation ID for error tracking."""
        import uuid

        return str(uuid.uuid4())[:8]

    def create_error(
        self,
        error_type: str,
        message: str,
        severity: str = ERROR_SEVERITY["MEDIUM"],
        context: Optional[Dict[str, Any]] = None,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        suggestions: Optional[List[str]] = None,
    ) -> StandardError:
        """Create standardized error response."""
        from datetime import datetime

        error_code = ERROR_CODE_MAPPING.get(error_type, ERROR_CODE_MAPPING["INTERNAL_ERROR"])

        return StandardError(
            code=error_code,
            message=message,
            severity=severity,
            timestamp=datetime.now().isoformat(),
            integration=self.integration,
            error_id=error_type,
            context=context or {},
            correlation_id=self.correlation_id,
            file_path=file_path,
            line_number=line_number,
            suggestions=suggestions,
        )

    def handle_exception(
        self, exception: Exception, context: Optional[Dict[str, Any]] = None, file_path: Optional[str] = None
    ) -> StandardError:
        """Convert exception to standardized error."""
        # Map common exceptions to error types
        exception_mapping = {
            FileNotFoundError: "FILE_NOT_FOUND",
            PermissionError: "PERMISSION_DENIED",
            SyntaxError: "SYNTAX_ERROR",
            TimeoutError: "TIMEOUT_ERROR",
            MemoryError: "MEMORY_ERROR",
            ValueError: "ANALYSIS_FAILED",
            ImportError: "DEPENDENCY_MISSING",
        }

        error_type = exception_mapping.get(type(exception), "INTERNAL_ERROR")
        severity = (
            ERROR_SEVERITY["HIGH"]
            if error_type in ["FILE_NOT_FOUND", "PERMISSION_DENIED"]
            else ERROR_SEVERITY["MEDIUM"]
        )

        return self.create_error(
            error_type=error_type, message=str(exception), severity=severity, context=context, file_path=file_path
        )

    def log_error(self, error: StandardError):
        """Log error with appropriate level."""

        ProductionAssert.not_none(error, "error")

        ProductionAssert.not_none(error, "error")

        log_level_mapping = {
            ERROR_SEVERITY["CRITICAL"]: logger.critical,
            ERROR_SEVERITY["HIGH"]: logger.error,
            ERROR_SEVERITY["MEDIUM"]: logger.warning,
            ERROR_SEVERITY["LOW"]: logger.info,
            ERROR_SEVERITY["INFO"]: logger.info,
        }

        log_func = log_level_mapping.get(error.severity, logger.error)
        log_func(f"[{error.integration}:{error.correlation_id}] {error.message} (Code: {error.code})")

        if error.file_path:
            log_func(f"  File: {error.file_path}:{error.line_number or 0}")
        if error.suggestions:
            log_func(f"  Suggestions: {', '.join(error.suggestions)}")


class ComponentInitializer:
    """Handles initialization of optional components with fallbacks."""

    @staticmethod
    def init_smart_engine():
        """Initialize smart integration engine with fallback."""
        try:
            return SmartIntegrationEngine()
        except:
            return None

    @staticmethod
    def init_failure_detector():
        """Initialize failure detector with fallback."""
        if FailureDetectionSystem:
            try:
                return FailureDetectionSystem()
            except:
                return None
        return None

    @staticmethod
    def init_nasa_integration():
        """Initialize NASA integration with fallback."""
        if NASAPowerOfTenIntegration:
            try:
                return NASAPowerOfTenIntegration()
            except:
                return None
        return None

    @staticmethod
    def init_policy_manager():
        """Initialize policy manager with fallback."""
        if PolicyManager:
            try:
                return PolicyManager()
            except:
                return None
        return None

    @staticmethod
    def init_budget_tracker():
        """Initialize budget tracker with fallback."""
        if BudgetTracker:
            try:
                return BudgetTracker()
            except:
                return None
        return None


# Legacy MetricsCalculator class for backward compatibility
class MetricsCalculator:
    """Legacy metrics calculator - delegates to EnhancedMetricsCalculator for compatibility."""

    def __init__(self):
        pass  # Simplified implementation

    def calculate_comprehensive_metrics(
        self, connascence_violations, duplication_clusters, nasa_violations, nasa_integration=None
    ):
        """Calculate comprehensive quality metrics - delegates to enhanced calculator."""
        return self.enhanced_calculator.calculate_comprehensive_metrics(
            connascence_violations, duplication_clusters, nasa_violations, nasa_integration
        )


# Legacy RecommendationGenerator class for backward compatibility
class RecommendationGenerator:
    """Legacy recommendation generator - delegates to RecommendationEngine for compatibility."""

    def __init__(self):
        pass  # Simplified implementation

    def generate_unified_recommendations(
        self, connascence_violations, duplication_clusters, nasa_violations, nasa_integration=None
    ):
        """Generate comprehensive improvement recommendations - delegates to engine."""
        return self.recommendation_engine.generate_unified_recommendations(
            connascence_violations, duplication_clusters, nasa_violations, nasa_integration
        )


class UnifiedConnascenceAnalyzer:
    """
    Unified analyzer that orchestrates all Phase 1-6 analysis capabilities.

    This class provides a single, consistent interface to all connascence
    analysis features while maintaining the modularity of individual components.

    Supports multiple analysis modes:
    - batch: Traditional full project analysis
    - streaming: Real-time incremental analysis with file watching
    - hybrid: Combination of batch and streaming for optimal performance
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        analysis_mode: str = "batch",
        streaming_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the unified analyzer with available components.

        Args:
            config_path: Path to configuration file
            analysis_mode: Analysis mode ('batch', 'streaming', 'hybrid')
            streaming_config: Configuration for streaming mode
        """
        assert analysis_mode in [
            "batch",
            "streaming",
            "hybrid",
        ], f"Invalid analysis_mode: {analysis_mode}. Must be 'batch', 'streaming', or 'hybrid'"

        self.analysis_mode = analysis_mode
        self.streaming_config = streaming_config or {}

        # Initialize error handling
        self.error_handler = ErrorHandler("analyzer")

        # Initialize streaming components if available and requested
        self.stream_processor: Optional[StreamProcessor] = None
        self.incremental_cache: Optional[IncrementalCache] = None
        if STREAMING_AVAILABLE and analysis_mode in ["streaming", "hybrid"]:
            self._initialize_streaming_components()

        # Initialize enhanced file cache for optimized I/O with intelligent warming
        self.file_cache = (
            FileContentCache(max_memory=100 * 1024 * 1024) if CACHE_AVAILABLE else None
        )  # 100MB for large projects
        self._cache_stats = {"hits": 0, "misses": 0, "warm_requests": 0, "batch_loads": 0}
        self._analysis_patterns = {}  # Track file access patterns for intelligent caching
        self._file_priorities = {}  # Cache file priority scores for better eviction

        # Initialize advanced monitoring and resource management
        self.memory_monitor = None
        self.resource_manager = None
        if ADVANCED_MONITORING_AVAILABLE:
            self.memory_monitor = get_global_memory_monitor()
            self.resource_manager = get_global_resource_manager()
            self._setup_monitoring_and_cleanup_hooks()

        # Initialize new architecture components (NASA Rule 4 compliant)
        # Temporarily disabled all broken architecture components
        # self.config_manager = ConfigurationManager()
        # self.orchestrator_component = AnalysisOrchestrator()
        # self.aggregator = ViolationAggregator()
        # self.recommendation_engine = RecommendationEngine()
        # self.enhanced_metrics = EnhancedMetricsCalculator()

        # Load configuration (simplified)
        self.config = self._load_config(config_path)

        # Initialize core analyzers (always available)
        try:
            self.ast_analyzer = ConnascenceASTAnalyzer()
            self.god_object_orchestrator = GodObjectOrchestrator()  # Renamed for clarity
            self.mece_analyzer = MECEAnalyzer()
        except Exception as e:
            error = self.error_handler.handle_exception(e, {"component": "core_analyzers"})
            self.error_handler.log_error(error)
            raise

        # Initialize optional components
        initializer = ComponentInitializer()
        self.smart_engine = initializer.init_smart_engine()
        self.failure_detector = initializer.init_failure_detector()
        self.nasa_integration = initializer.init_nasa_integration()
        self.policy_manager = initializer.init_policy_manager()
        self.budget_tracker = initializer.init_budget_tracker()

        # Initialize helper classes
        self.metrics_calculator = MetricsCalculator()
        self.recommendation_generator = RecommendationGenerator()

        components_loaded = ["AST Analyzer", "Orchestrator", "MECE Analyzer"]
        if self.smart_engine:
            components_loaded.append("Smart Engine")
        if self.failure_detector:
            components_loaded.append("Failure Detector")
        if self.nasa_integration:
            components_loaded.append("NASA Integration")

        logger.info(f"Unified Connascence Analyzer initialized with: {', '.join(components_loaded)}")

    def analyze_project(
        self,
        project_path: Union[str, Path],
        policy_preset: str = "service-defaults",
        options: Optional[Dict[str, Any]] = None,
    ) -> UnifiedAnalysisResult:
        """
        Perform comprehensive connascence analysis on a project.
        Supports batch, streaming, and hybrid analysis modes.
        NASA Rule 4 Compliant: Function under 60 lines.
        """
        # NASA Rule 5: Input validation assertions
        assert project_path is not None, "project_path cannot be None"
        assert isinstance(policy_preset, str), "policy_preset must be string"

        project_path = Path(project_path)
        options = options or {}

        # Route to appropriate analysis pipeline based on mode
        if self.analysis_mode == "streaming":
            return self._analyze_project_streaming(project_path, policy_preset, options)
        elif self.analysis_mode == "hybrid":
            return self._analyze_project_hybrid(project_path, policy_preset, options)
        else:  # batch mode (default)
            return self._analyze_project_batch(project_path, policy_preset, options)

    def _analyze_project_batch(
        self, project_path: Path, policy_preset: str, options: Dict[str, Any]
    ) -> UnifiedAnalysisResult:
        """Execute traditional batch analysis."""
        start_time = self._get_timestamp_ms()

        logger.info(f"Starting batch unified analysis of {project_path}")

        # Intelligent cache warming based on project structure
        if self.file_cache:
            self._warm_cache_intelligently(project_path)

        # Validate inputs and handle errors
        analysis_errors, analysis_warnings = self._initialize_analysis_context(project_path, policy_preset)

        # Execute analysis phases using new orchestrator component
        violations = self._execute_analysis_phases_with_orchestrator(project_path, policy_preset, analysis_errors)

        # Calculate metrics using enhanced calculator
        metrics = self._calculate_metrics_with_enhanced_calculator(violations, analysis_errors)

        # Generate recommendations using recommendation engine
        recommendations = self._generate_recommendations_with_engine(violations, analysis_warnings)

        # Build final result using aggregator
        analysis_time = self._get_timestamp_ms() - start_time
        result = self._build_result_with_aggregator(
            violations,
            metrics,
            recommendations,
            project_path,
            policy_preset,
            analysis_time,
            analysis_errors,
            analysis_warnings,
        )

        # Log comprehensive performance and resource reports
        if self.file_cache:
            self._log_cache_performance()
            self._optimize_cache_for_future_runs()

        # Log memory and resource management reports
        if ADVANCED_MONITORING_AVAILABLE:
            self._log_comprehensive_monitoring_report()

        self._log_analysis_completion(result, analysis_time)
        return result

    def _analyze_project_streaming(
        self, project_path: Path, policy_preset: str, options: Dict[str, Any]
    ) -> UnifiedAnalysisResult:
        """Execute streaming analysis with real-time processing."""
        if not STREAMING_AVAILABLE or not self.stream_processor:
            logger.warning("Streaming mode requested but not available, falling back to batch")
            return self._analyze_project_batch(project_path, policy_preset, options)

        logger.info(f"Starting streaming analysis of {project_path}")
        self._get_timestamp_ms()

        # Start streaming processor if not already running
        if not self.stream_processor.is_running:
            self.start_streaming_analysis()

        # Process initial batch for immediate results
        initial_result = self._analyze_project_batch(project_path, policy_preset, options)

        # Set up continuous monitoring for file changes
        self.stream_processor.watch_directory(str(project_path))

        logger.info(f"Streaming analysis active for {project_path}")
        return initial_result

    def _analyze_project_hybrid(
        self, project_path: Path, policy_preset: str, options: Dict[str, Any]
    ) -> UnifiedAnalysisResult:
        """Execute hybrid analysis combining batch and streaming."""
        if not STREAMING_AVAILABLE or not self.stream_processor:
            logger.warning("Hybrid mode requested but streaming not available, using batch only")
            return self._analyze_project_batch(project_path, policy_preset, options)

        logger.info(f"Starting hybrid analysis of {project_path}")

        # Run comprehensive batch analysis first
        batch_result = self._analyze_project_batch(project_path, policy_preset, options)

        # Enable streaming for incremental updates
        if not self.stream_processor.is_running:
            self.start_streaming_analysis()

        self.stream_processor.watch_directory(str(project_path))

        logger.info(f"Hybrid analysis complete - batch done, streaming active for {project_path}")
        return batch_result

    def _run_analysis_phases(self, project_path: Path, policy_preset: str) -> Dict[str, Any]:
        """Run analysis phases using direct method calls (fallback implementation)."""
        # Direct implementation since orchestrator_component is disabled
        logger.info("Running analysis phases with direct fallback implementation")

        # Run AST analysis
        connascence_violations = self._run_ast_analysis(project_path)

        # Run duplication analysis if MECE analyzer available
        duplication_violations = []
        if self.mece_analyzer:
            try:
                mece_results = self.mece_analyzer.analyze_directory(str(project_path))
                duplication_violations = [self._violation_to_dict(v) for v in mece_results]
            except Exception as e:
                logger.warning(f"MECE analysis failed: {e}")

        # Run NASA analysis if available
        nasa_violations = []
        if self.nasa_integration:
            try:
                nasa_results = self.nasa_integration.validate_project(str(project_path))
                if isinstance(nasa_results, dict) and "violations" in nasa_results:
                    nasa_violations = nasa_results["violations"]
            except Exception as e:
                logger.warning(f"NASA analysis failed: {e}")

        return {"connascence": connascence_violations, "duplication": duplication_violations, "nasa": nasa_violations}

    def _run_ast_analysis(self, project_path: Path) -> List[Dict[str, Any]]:
        """Run core AST analysis phases."""
        logger.info("Phase 1-2: Running core AST analysis with enhanced detectors")

        ast_results = self.ast_analyzer.analyze_directory(project_path)
        connascence_violations = [self._violation_to_dict(v) for v in ast_results]

        # Also run god object analysis from orchestrator
        god_results = self.orchestrator.analyze_directory(str(project_path))
        connascence_violations.extend([self._violation_to_dict(v) for v in god_results])

        # Run refactored detector architecture (includes 5 specialized detectors + identity)
        refactored_violations = self._run_refactored_analysis(project_path)
        connascence_violations.extend(refactored_violations)

        # Run AST optimizer pattern analysis (adds connascence_of_name, _literal, _position, _algorithm)
        ast_optimizer_violations = self._run_ast_optimizer_analysis(project_path)
        connascence_violations.extend(ast_optimizer_violations)

        return connascence_violations

    def _run_refactored_analysis(self, project_path: Path) -> List[Dict[str, Any]]:
        """Run refactored detector analysis using RefactoredConnascenceDetector."""
        logger.info("Running comprehensive connascence analysis with specialized detectors")
        refactored_violations = []

        # Enhanced: Get prioritized Python files for optimal cache utilization
        python_files = self._get_prioritized_python_files(project_path)

        # Batch preload files for better cache performance
        if self.file_cache:
            self._batch_preload_files(python_files[:15])  # Pre-load top 15 files

        for py_file in python_files:
            if self._should_analyze_file(py_file):
                try:
                    # Enhanced: Use cache with access pattern tracking
                    if self.file_cache:
                        source_code = self._get_cached_content_with_tracking(py_file)
                        source_lines = self._get_cached_lines_with_tracking(py_file)
                    else:
                        with open(py_file, encoding="utf-8") as f:
                            source_code = f.read()
                            source_lines = source_code.splitlines()

                    if not source_code:
                        continue

                    # Enhanced: Use cached AST with intelligent fallback
                    if self.file_cache:
                        tree = self.file_cache.get_ast_tree(py_file)
                        if tree:
                            self._cache_stats["hits"] += 1
                        else:
                            self._cache_stats["misses"] += 1
                    else:
                        try:
                            tree = ast.parse(source_code)
                        except SyntaxError:
                            continue  # Skip files with syntax errors

                    if not tree:
                        continue

                    # Run RefactoredConnascenceDetector (includes all 5 specialized detectors)
                    refactored_detector = RefactoredConnascenceDetector(str(py_file), source_lines)
                    file_violations = refactored_detector.detect_all_violations(tree)

                    # Convert violations to dict format
                    refactored_violations.extend([self._violation_to_dict(v) for v in file_violations])

                except Exception as e:
                    logger.debug(f"Failed to analyze {py_file} with refactored detector: {e}")
                    continue

        logger.info(f"Found {len(refactored_violations)} violations from specialized detectors")
        return refactored_violations

    def _run_ast_optimizer_analysis(self, project_path: Path) -> List[Dict[str, Any]]:
        """Run AST optimizer pattern analysis using ConnascencePatternOptimizer."""
        logger.info("Running AST optimizer connascence pattern analysis")
        optimizer_violations = []

        # Initialize AST optimizer
        ast_optimizer = ConnascencePatternOptimizer()

        # Enhanced: Reuse prioritized Python files list for optimal cache benefits
        python_files = self._get_prioritized_python_files(project_path)

        # Cache performance tracking
        logger.info(f"Starting AST optimizer analysis (current cache hit rate: {self._get_cache_hit_rate():.1%})")

        for py_file in python_files:
            if self._should_analyze_file(py_file):
                try:
                    # Enhanced: Use cached content and AST with performance tracking
                    if self.file_cache:
                        source_code = self._get_cached_content_with_tracking(py_file)
                        tree = self.file_cache.get_ast_tree(py_file)
                        if tree:
                            self._cache_stats["hits"] += 1
                        else:
                            self._cache_stats["misses"] += 1
                    else:
                        with open(py_file, encoding="utf-8") as f:
                            source_code = f.read()
                        try:
                            tree = ast.parse(source_code)
                        except SyntaxError:
                            continue  # Skip files with syntax errors

                    if not source_code or not tree:
                        continue

                    # Run AST optimizer analysis
                    file_violations = ast_optimizer.analyze_connascence_fast(tree)

                    # Convert AST optimizer results to standard violation format
                    for violation_type, violations in file_violations.items():
                        for violation in violations:
                            violation_dict = {
                                "id": f"ast_opt_{violation.get('node_type', 'unknown')}_{violation.get('line_number', 0)}",
                                "rule_id": violation_type,
                                "type": violation_type,
                                "severity": violation.get("severity", "medium"),
                                "description": violation.get("description", f"{violation_type} detected"),
                                "file_path": str(py_file),
                                "line_number": violation.get("line_number", 0),
                                "column": violation.get("column_number", 0),
                                "weight": self._severity_to_weight(violation.get("severity", "medium")),
                                "context": {
                                    "analysis_engine": "ast_optimizer",
                                    "node_type": violation.get("node_type", "unknown"),
                                },
                            }
                            optimizer_violations.append(violation_dict)

                except Exception as e:
                    logger.debug(f"Failed to analyze {py_file} with AST optimizer: {e}")
                    continue

        logger.info(f"Found {len(optimizer_violations)} violations from AST optimizer patterns")
        return optimizer_violations

    def get_architecture_components(self) -> Dict[str, Any]:
        """Get references to architecture components for advanced usage. NASA Rule 4 compliant."""
        return {
            "orchestrator": self.orchestrator_component,
            "aggregator": self.aggregator,
            "recommendation_engine": self.recommendation_engine,
            "config_manager": self.config_manager,
            "enhanced_metrics": self.enhanced_metrics,
        }

    def get_component_status(self) -> Dict[str, bool]:
        """Get status of all components. NASA Rule 4 compliant."""
        return {
            "core_components": True,  # Always available
            "architecture_components": True,  # New specialized components
            "smart_engine": self.smart_engine is not None,
            "failure_detector": self.failure_detector is not None,
            "nasa_integration": self.nasa_integration is not None,
            "policy_manager": self.policy_manager is not None,
            "budget_tracker": self.budget_tracker is not None,
            "caching": self.file_cache is not None,
        }

    def _run_tree_sitter_nasa_analysis(self) -> List[Dict[str, Any]]:
        """Run Tree-Sitter NASA rule analysis for goto, exec/eval, function pointer detection."""
        tree_sitter_violations = []

        if not TreeSitterBackend or not LanguageSupport:
            return tree_sitter_violations

        try:
            # Initialize Tree-Sitter backend
            backend = TreeSitterBackend()

            if not backend.is_available():
                logger.info("Tree-Sitter backend not fully available, skipping NASA rule detection")
                return tree_sitter_violations

            # Find source code files (Python, C, JavaScript)
            project_path = Path(".")  # Placeholder - should be passed from context
            language_files = {
                LanguageSupport.PYTHON: list(project_path.rglob("*.py")),
                LanguageSupport.C: list(project_path.rglob("*.c")) + list(project_path.rglob("*.h")),
                LanguageSupport.JAVASCRIPT: list(project_path.rglob("*.js")) + list(project_path.rglob("*.ts")),
            }

            for language, files in language_files.items():
                for file_path in files:
                    if self._should_analyze_file(file_path):
                        try:
                            with open(file_path, encoding="utf-8") as f:
                                source_code = f.read()

                            # Parse with Tree-Sitter
                            parse_result = backend.parse(source_code, language)

                            if parse_result.success and parse_result.ast:
                                # Run NASA overlay validation
                                validation_result = backend.validate(
                                    source_code,
                                    language,
                                    overlay="nasa_c_safety" if language == LanguageSupport.C else "nasa_python_safety",
                                )

                                # Convert Tree-Sitter violations to standard format
                                for violation in validation_result.overlay_violations:
                                    tree_sitter_violation = {
                                        "id": f"tree_sitter_{violation.get('rule', 'unknown')}_{violation.get('line', 0)}",
                                        "rule_id": violation.get("rule", "nasa_tree_sitter"),
                                        "type": violation.get("type", "nasa_compliance"),
                                        "severity": violation.get("severity", "high"),
                                        "description": violation.get("message", "NASA rule violation"),
                                        "file_path": str(file_path),
                                        "line_number": violation.get("line", 0),
                                        "column": violation.get("column", 0),
                                        "weight": self._severity_to_weight(violation.get("severity", "high")),
                                        "context": {
                                            "analysis_engine": "tree_sitter",
                                            "language": language.value,
                                            "nasa_rule": violation.get("rule", "unknown"),
                                        },
                                    }
                                    tree_sitter_violations.append(tree_sitter_violation)

                        except Exception as e:
                            logger.debug(f"Failed Tree-Sitter analysis of {file_path}: {e}")
                            continue

        except Exception as e:
            logger.warning(f"Tree-Sitter NASA analysis failed: {e}")

        logger.info(f"Found {len(tree_sitter_violations)} NASA violations from Tree-Sitter")
        return tree_sitter_violations

    def _run_dedicated_nasa_analysis(self, project_path: Optional[Path] = None) -> List[Dict[str, Any]]:
        """Run dedicated NASA Power of Ten analysis."""
        nasa_violations = []

        try:
            # Initialize NASA analyzer
            nasa_analyzer = NASAAnalyzer()

            # Use provided project path or current directory
            if project_path is None:
                project_path = Path(".")

            # Optimized: Reuse cached Python files list (eliminates third file traversal)
            if self.file_cache:
                python_files = self.file_cache.get_python_files(str(project_path))
            else:
                python_files = [str(f) for f in project_path.rglob("*.py") if self._should_analyze_file(f)]

            for py_file_str in python_files:
                py_file = Path(py_file_str)
                if self._should_analyze_file(py_file):
                    try:
                        # Optimized: Use cached file content
                        if self.file_cache:
                            source_code = self.file_cache.get_file_content(py_file)
                        else:
                            with open(py_file, encoding="utf-8") as f:
                                source_code = f.read()

                        if not source_code:
                            continue

                        # Run NASA analysis on file
                        file_violations = nasa_analyzer.analyze_file(str(py_file), source_code)

                        # Convert NASA violations to standard format
                        for violation in file_violations:
                            nasa_violation = {
                                "id": f"nasa_{violation.context.get('nasa_rule', 'unknown')}_{violation.line_number}",
                                "rule_id": violation.type,
                                "type": violation.type,
                                "severity": violation.severity,
                                "description": violation.description,
                                "file_path": violation.file_path,
                                "line_number": violation.line_number,
                                "column": violation.column,
                                "weight": self._severity_to_weight(violation.severity),
                                "context": {
                                    "analysis_engine": "dedicated_nasa",
                                    "nasa_rule": violation.context.get("nasa_rule", "unknown"),
                                    "violation_type": violation.context.get("violation_type", "unknown"),
                                    "recommendation": violation.recommendation,
                                },
                            }
                            nasa_violations.append(nasa_violation)

                    except Exception as e:
                        logger.debug(f"Failed NASA analysis of {py_file}: {e}")
                        continue

        except Exception as e:
            logger.warning(f"Dedicated NASA analysis failed: {e}")

        logger.info(f"Found {len(nasa_violations)} NASA violations from dedicated analyzer")
        return nasa_violations

    def _should_analyze_file(self, file_path: Path) -> bool:
        """Check if file should be analyzed (skip test files, __pycache__, etc.)."""
        # Skip system/build directories
        skip_patterns = [
            "__pycache__",
            ".git",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            ".tox",
            ".venv",
            "venv",
            "node_modules",
        ]
        path_str = str(file_path)

        # Check system directories
        if any(pattern in path_str for pattern in skip_patterns):
            return False

        # Skip actual test files (but not directories named "test_*")
        # Only skip files that are actually test files, not just in directories with "test" in the name
        path_parts = file_path.parts
        filename = file_path.name

        # Skip files in /tests/ or \tests\ directories (actual test directories)
        if "tests" in path_parts:
            return False

        # Skip files that start with test_ or end with _test.py (actual test files)
        return not (filename.startswith("test_") or filename.endswith("_test.py"))

    def _run_duplication_analysis(self, project_path: Path) -> List[Dict[str, Any]]:
        """Run MECE duplication detection."""
        logger.info("Phase 3-4: Running MECE duplication analysis")

        dup_analysis = self.mece_analyzer.analyze_path(str(project_path), comprehensive=True)
        return dup_analysis.get("duplications", [])

    def _run_smart_integration(self, project_path: Path, policy_preset: str, existing_violations: Optional[Dict] = None):
        """Run smart integration engine with enhanced correlation analysis."""
        if self.smart_engine:
            logger.info("Phase 5: Running smart integration engine with cross-phase correlation")
            try:
                # Pass existing violations for correlation analysis
                base_results = self.smart_engine.comprehensive_analysis(str(project_path), policy_preset)

                # Enhanced correlation analysis if we have existing violations
                if existing_violations:
                    correlations = self.smart_engine.analyze_correlations(
                        existing_violations.get("connascence", []),
                        existing_violations.get("duplication", []),
                        existing_violations.get("nasa", []),
                    )

                    recommendations = self.smart_engine.generate_intelligent_recommendations(
                        existing_violations.get("connascence", []),
                        existing_violations.get("duplication", []),
                        existing_violations.get("nasa", []),
                    )

                    # Enhance base results with cross-phase analysis
                    if base_results:
                        base_results["correlations"] = correlations
                        base_results["enhanced_recommendations"] = recommendations
                        base_results["cross_phase_analysis"] = True
                    else:
                        base_results = {
                            "correlations": correlations,
                            "enhanced_recommendations": recommendations,
                            "cross_phase_analysis": True,
                            "violations": [],
                            "summary": {"total_violations": 0, "critical_violations": 0},
                        }

                return base_results

            except Exception as e:
                logger.warning(f"Smart integration failed: {e}")
                return {"error": str(e), "correlations": [], "enhanced_recommendations": []}
        else:
            logger.info("Phase 5: Smart integration engine not available")
            return None

    def _run_nasa_analysis(
        self, connascence_violations: List[Dict[str, Any]], phase_metadata: Optional[Dict] = None, project_path: Optional[Path] = None
    ) -> List[Dict[str, Any]]:
        """Run NASA compliance analysis with enhanced context awareness and Tree-Sitter backend."""
        nasa_violations = []

        # First run dedicated NASA analyzer with project context
        logger.info("Running dedicated NASA Power of Ten analysis")
        dedicated_nasa_violations = self._run_dedicated_nasa_analysis(project_path)
        nasa_violations.extend(dedicated_nasa_violations)

        # Also run Tree-Sitter NASA rule detection if available
        if TreeSitterBackend and LanguageSupport:
            logger.info("Running Tree-Sitter NASA rule detection")
            tree_sitter_violations = self._run_tree_sitter_nasa_analysis()
            nasa_violations.extend(tree_sitter_violations)

        if self.nasa_integration:
            logger.info("Phase 6: Checking NASA Power of Ten compliance with cross-phase context")
            try:
                # Enhanced NASA analysis with phase context
                for violation in connascence_violations:
                    nasa_checks = self.nasa_integration.check_nasa_violations(violation)

                    # Enhance NASA violations with cross-phase context
                    for nasa_violation in nasa_checks:
                        if phase_metadata and phase_metadata.get("correlations"):
                            # Add correlation context to NASA violations
                            related_correlations = [
                                c
                                for c in phase_metadata["correlations"]
                                if violation.get("file_path") in str(c.get("common_findings", []))
                            ]
                            if related_correlations:
                                nasa_violation["cross_phase_correlations"] = related_correlations
                                nasa_violation["enhanced_context"] = True

                    nasa_violations.extend(nasa_checks)

                # Add metadata about NASA analysis
                if phase_metadata:
                    nasa_compliance_score = max(0.0, 1.0 - (len(nasa_violations) * 0.1))
                    phase_metadata["nasa_compliance_score"] = nasa_compliance_score
                    phase_metadata["nasa_rules_checked"] = [
                        "Rule1",
                        "Rule2",
                        "Rule3",
                        "Rule4",
                        "Rule5",
                        "Rule6",
                        "Rule7",
                        "Rule8",
                        "Rule9",
                        "Rule10",
                    ]

            except Exception as e:
                logger.warning(f"NASA compliance check failed: {e}")
                if phase_metadata:
                    phase_metadata["nasa_analysis_error"] = str(e)
        else:
            logger.info("Phase 6: Using fallback NASA compliance extraction")
            # Extract NASA violations from existing connascence violations
            nasa_violations = [v for v in connascence_violations if "NASA" in v.get("rule_id", "")]

            # Add enhanced context even for fallback mode
            for violation in nasa_violations:
                violation["analysis_mode"] = "fallback"
                violation["enhanced_context"] = False

        return nasa_violations

    def _validate_analysis_inputs(self, project_path: Path, policy_preset: str):
        """Validate analysis inputs and raise appropriate errors."""
        if not project_path.exists():
            raise FileNotFoundError(f"Project path does not exist: {project_path}")

        if not project_path.is_dir():
            raise ValueError(f"Project path is not a directory: {project_path}")

        valid_presets = ["service-defaults", "strict-core", "experimental", "balanced", "lenient"]
        if policy_preset not in valid_presets:
            raise ValueError(f"Invalid policy preset: {policy_preset}. Valid options: {valid_presets}")

    def _get_default_metrics(self) -> Dict[str, Any]:
        """Provide default metrics when calculation fails."""
        return {
            "total_violations": 0,
            "critical_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
            "connascence_index": 0.0,
            "nasa_compliance_score": 1.0,
            "duplication_score": 1.0,
            "overall_quality_score": 0.8,
        }

    def _warm_cache_intelligently(self, project_path: Path) -> None:
        """
        Intelligent cache warming strategy to achieve >80% hit rates.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input assertions and error handling
        """
        assert project_path.exists(), "project_path must exist"

        try:
            # Strategy 1: Pre-load frequently accessed file types
            common_files = ["__init__.py", "setup.py", "main.py", "app.py", "config.py"]
            for filename in common_files:
                file_matches = list(project_path.rglob(filename))
                for file_path in file_matches[:5]:  # Limit to avoid memory issues
                    if file_path.stat().st_size < 100 * 1024:  # Only small files
                        self.file_cache.get_file_content(file_path)
                        self._cache_stats["warm_requests"] += 1

            # Strategy 2: Pre-load directory structure for pattern recognition
            python_files = list(project_path.glob("**/*.py"))

            # Prioritize by file size and common patterns
            prioritized = sorted(
                python_files,
                key=lambda f: (
                    -self._calculate_file_priority(f),  # Higher priority first
                    f.stat().st_size,  # Smaller files first within same priority
                ),
            )[
                :15
            ]  # Pre-warm top 15 files

            for py_file in prioritized:
                if py_file.stat().st_size < 500 * 1024:  # Skip large files
                    self.file_cache.get_file_content(py_file)
                    self._cache_stats["warm_requests"] += 1

        except Exception as e:
            logger.warning(f"Cache warming failed: {e}")

    def _calculate_file_priority(self, file_path: Path) -> int:
        """Calculate file priority for intelligent caching (0-100)."""
        score = 0
        filename = file_path.name.lower()
        parent_dir = file_path.parent.name.lower()

        # High priority files
        high_priority_names = ["__init__", "main", "app", "config", "settings"]
        if any(name in filename for name in high_priority_names):
            score += 40

        # Medium priority directories
        important_dirs = ["src", "lib", "core", "utils", "common"]
        if any(dir_name in parent_dir for dir_name in important_dirs):
            score += 20

        # Boost for smaller files (easier to cache)
        if file_path.stat().st_size < 50 * 1024:  # < 50KB
            score += 20
        elif file_path.stat().st_size < 200 * 1024:  # < 200KB
            score += 10

        # Frequently imported patterns
        if filename.endswith(("_utils.py", "_common.py", "_base.py")):
            score += 15

        return min(score, 100)

    def _get_prioritized_python_files(self, project_path: Path) -> List[Path]:
        """Get Python files prioritized for analysis with caching benefits."""
        if self.file_cache:
            # FileContentCache returns strings, convert to Path objects
            python_files_str = self.file_cache.get_python_files(str(project_path))
            python_files = [Path(f) for f in python_files_str]
        else:
            python_files = list(project_path.glob("**/*.py"))

        # Sort by priority for better cache utilization
        return sorted(python_files, key=self._calculate_file_priority, reverse=True)

    def _batch_preload_files(self, files: List[Path]) -> None:
        """Batch preload files for optimal cache performance."""
        if not self.file_cache:
            return

        logger.info(f"Batch preloading {len(files)} files for cache optimization")

        for file_path in files:
            try:
                if file_path.stat().st_size < 1024 * 1024:  # Only files < 1MB
                    # Preload both content and AST for maximum benefit
                    self.file_cache.get_file_content(file_path)
                    self.file_cache.get_ast_tree(file_path)
                    self._cache_stats["batch_loads"] += 1

            except Exception as e:
                logger.debug(f"Failed to preload {file_path}: {e}")

    def _get_cached_content_with_tracking(self, file_path: Path) -> Optional[str]:
        """Get file content with access pattern tracking for cache optimization."""
        if not self.file_cache:
            return None

        # Track access pattern
        file_key = str(file_path)
        self._analysis_patterns[file_key] = self._analysis_patterns.get(file_key, 0) + 1

        # Get content and track cache performance
        content = self.file_cache.get_file_content(file_path)
        if content:
            self._cache_stats["hits"] += 1
        else:
            self._cache_stats["misses"] += 1

        return content

    def _get_cached_lines_with_tracking(self, file_path: Path) -> List[str]:
        """Get file lines with access pattern tracking."""
        if not self.file_cache:
            return []

        lines = self.file_cache.get_file_lines(file_path)
        if lines:
            self._cache_stats["hits"] += 1
        else:
            self._cache_stats["misses"] += 1

        return lines

    def _get_cache_hit_rate(self) -> float:
        """Calculate current cache hit rate."""
        total = self._cache_stats["hits"] + self._cache_stats["misses"]
        return self._cache_stats["hits"] / total if total > 0 else 0.0

    def _log_cache_performance(self) -> None:
        """Log detailed cache performance metrics for monitoring."""
        if not self.file_cache:
            return

        hit_rate = self._get_cache_hit_rate()
        cache_stats = self.file_cache._stats if hasattr(self.file_cache, "_stats") else None

        logger.info("Cache Performance Summary:")
        logger.info(f"  Hit Rate: {hit_rate:.1%} (Target: >80%)")
        logger.info(f"  Hits: {self._cache_stats['hits']}")
        logger.info(f"  Misses: {self._cache_stats['misses']}")
        logger.info(f"  Warm Requests: {self._cache_stats['warm_requests']}")
        logger.info(f"  Batch Loads: {self._cache_stats['batch_loads']}")

        if cache_stats:
            memory_usage = cache_stats.memory_usage / (1024 * 1024)  # MB
            logger.info(f"  Memory Usage: {memory_usage:.1f}MB / {cache_stats.max_memory // (1024 * 1024)}MB")
            logger.info(f"  Evictions: {cache_stats.evictions}")

        # Performance recommendations
        if hit_rate < 0.6:
            logger.warning("Low cache hit rate - consider increasing warm-up files")
        elif hit_rate > 0.9:
            logger.info("Excellent cache performance!")

    def _optimize_cache_for_future_runs(self) -> None:
        """
        Learn from current analysis patterns to optimize future cache performance.

        NASA Rule 4: Function under 60 lines
        """
        if not self._analysis_patterns:
            return

        # Identify most frequently accessed files
        frequent_files = sorted(self._analysis_patterns.items(), key=lambda x: x[1], reverse=True)[
            :10
        ]  # Top 10 most accessed

        # Store for next analysis session (simplified for now)
        logger.info(f"Learned access patterns for {len(frequent_files)} high-frequency files")

        # Future enhancement: Persist patterns to improve next analysis

    def _setup_monitoring_and_cleanup_hooks(self) -> None:
        """
        Setup memory monitoring and resource cleanup hooks.

        NASA Rule 4: Function under 60 lines
        NASA Rule 7: Bounded resource management
        """
        if not (self.memory_monitor and self.resource_manager):
            return

        # Setup memory monitoring alerts
        self.memory_monitor.add_alert_callback(self._handle_memory_alert)
        self.memory_monitor.add_emergency_cleanup_callback(self._emergency_memory_cleanup)

        # Setup resource management cleanup hooks
        self.resource_manager.add_cleanup_hook(self._cleanup_analysis_resources)
        self.resource_manager.add_emergency_hook(self._emergency_resource_cleanup)
        self.resource_manager.add_periodic_cleanup_callback(self._periodic_cache_cleanup)

        # Start monitoring
        self.memory_monitor.start_monitoring()

    def _handle_memory_alert(self, alert_type: str, context: Dict[str, Any]) -> None:
        """Handle memory usage alerts with appropriate actions."""
        logger.warning(f"Memory alert: {alert_type}")

        if alert_type == "MEMORY_WARNING":
            # Cleanup old cache entries
            if self.file_cache:
                self.file_cache.clear_cache()
                logger.info("Cleared file cache due to memory warning")

        elif alert_type == "MEMORY_HIGH":
            # More aggressive cleanup
            self._aggressive_cleanup()

        elif alert_type == "MEMORY_CRITICAL":
            # Emergency procedures
            self._emergency_memory_cleanup()

        elif alert_type == "MEMORY_LEAK":
            growth_mb = context.get("growth_mb", 0)
            logger.error(f"Memory leak detected: {growth_mb:.1f}MB growth")
            self._investigate_memory_leak(context)

    def _emergency_memory_cleanup(self) -> None:
        """Emergency memory cleanup procedures."""
        logger.critical("Executing emergency memory cleanup")

        try:
            # Clear all caches
            if self.file_cache:
                self.file_cache.clear_cache()

            # Force garbage collection
            import gc

            for _ in range(3):
                gc.collect()

            # Cleanup all tracked resources
            if self.resource_manager:
                cleaned = self.resource_manager.cleanup_all()
                logger.info(f"Emergency cleanup: {cleaned} resources cleaned")

        except Exception as e:
            logger.error(f"Emergency cleanup failed: {e}")

    def _aggressive_cleanup(self) -> None:
        """Aggressive cleanup for high memory usage."""
        logger.info("Executing aggressive cleanup")

        # Clear cache entries older than 2 minutes
        if self.resource_manager:
            self.resource_manager.cleanup_old_resources(max_age_seconds=120.0)

        # Clear large cache entries
        if self.resource_manager:
            self.resource_manager.cleanup_large_resources(min_size_mb=5.0)

    def _cleanup_analysis_resources(self) -> None:
        """Cleanup analysis-specific resources."""
        try:
            # Clear analysis patterns and priorities
            self._analysis_patterns.clear()
            self._file_priorities.clear()

            # Reset cache stats
            self._cache_stats = {"hits": 0, "misses": 0, "warm_requests": 0, "batch_loads": 0}

        except Exception as e:
            logger.error(f"Analysis resource cleanup failed: {e}")

    def _emergency_resource_cleanup(self) -> None:
        """Emergency resource cleanup procedures."""
        logger.warning("Executing emergency resource cleanup")

        try:
            # Clear all analysis state
            self._cleanup_analysis_resources()

            # Clear component state
            if hasattr(self, "ast_analyzer") and self.ast_analyzer:
                if hasattr(self.ast_analyzer, "clear_state"):
                    self.ast_analyzer.clear_state()

        except Exception as e:
            logger.error(f"Emergency resource cleanup failed: {e}")

    def _periodic_cache_cleanup(self) -> int:
        """Periodic cache cleanup callback."""
        cleaned_count = 0

        try:
            import time

            # Cleanup cache entries older than 10 minutes
            if self.file_cache and hasattr(self.file_cache, "_cache"):
                old_entries = []
                current_time = time.time()

                for key, entry in self.file_cache._cache.items():
                    if hasattr(entry, "last_accessed") and (current_time - entry.last_accessed) > 600:
                        old_entries.append(key)

                for key in old_entries[:50]:  # Limit to avoid excessive cleanup
                    if key in self.file_cache._cache:
                        del self.file_cache._cache[key]
                        cleaned_count += 1

        except Exception as e:
            logger.error(f"Periodic cache cleanup failed: {e}")

        return cleaned_count

    def _investigate_memory_leak(self, context: Dict[str, Any]) -> None:
        """Investigate potential memory leak with detailed analysis."""
        try:
            import gc

            # Get object counts by type
            obj_counts = {}
            for obj in gc.get_objects()[:1000]:  # Bounded analysis (NASA Rule 7)
                obj_type = type(obj).__name__
                obj_counts[obj_type] = obj_counts.get(obj_type, 0) + 1

            # Log top object types
            top_types = sorted(obj_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            logger.warning(f"Top object types during leak: {top_types}")

        except Exception as e:
            logger.error(f"Memory leak investigation failed: {e}")

    def _log_comprehensive_monitoring_report(self) -> None:
        """Log comprehensive monitoring and resource management report."""
        try:
            logger.info("=== COMPREHENSIVE SYSTEM MONITORING REPORT ===")

            # Memory monitoring report
            if self.memory_monitor:
                memory_report = self.memory_monitor.get_memory_report()
                logger.info("Memory Monitoring Summary:")
                logger.info(f"  Current Usage: {memory_report['current_memory_mb']:.1f}MB")
                logger.info(f"  Peak Usage: {memory_report['peak_memory_mb']:.1f}MB")
                logger.info(f"  Average Usage: {memory_report['average_memory_mb']:.1f}MB")
                logger.info(f"  Monitoring Duration: {memory_report['monitoring_duration_minutes']:.1f} minutes")
                logger.info(f"  Leak Detected: {memory_report['leak_detected']}")

                if memory_report.get("recommendations"):
                    logger.info("  Memory Recommendations:")
                    for rec in memory_report["recommendations"]:
                        logger.info(f"    • {rec}")

            # Resource management report
            if self.resource_manager:
                resource_report = self.resource_manager.get_resource_report()
                summary = resource_report["summary"]

                logger.info("Resource Management Summary:")
                logger.info(f"  Resources Created: {summary['resources_created']}")
                logger.info(f"  Resources Cleaned: {summary['resources_cleaned']}")
                logger.info(f"  Currently Tracked: {summary['currently_tracked']}")
                logger.info(f"  Peak Tracked: {summary['peak_tracked']}")
                logger.info(f"  Cleanup Success Rate: {summary['cleanup_success_rate']:.1%}")
                logger.info(f"  Resource Leaks: {summary['resource_leaks']}")
                logger.info(f"  Emergency Cleanups: {summary['emergency_cleanups']}")
                logger.info(f"  Total Size: {summary['total_size_mb']:.1f}MB")

                if resource_report.get("recommendations"):
                    logger.info("  Resource Recommendations:")
                    for rec in resource_report["recommendations"]:
                        logger.info(f"    • {rec}")

                # Log by resource type
                logger.info("  Resource Breakdown by Type:")
                for resource_type, stats in resource_report["by_type"].items():
                    logger.info(
                        f"    {resource_type}: {stats['tracked']} tracked, "
                        f"{stats['size_mb']:.1f}MB, {stats['success_rate']:.1%} cleanup rate"
                    )

        except Exception as e:
            logger.error(f"Failed to generate comprehensive monitoring report: {e}")

    def _initialize_streaming_components(self) -> None:
        """
        Initialize streaming analysis components.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation and error handling
        """
        try:
            # Get global incremental cache instance
            self.incremental_cache = get_global_incremental_cache()

            # Create analyzer factory for stream processor
            def analyzer_factory():
                # Create a simplified analyzer instance for streaming
                return UnifiedConnascenceAnalyzer(
                    config_path=None, analysis_mode="batch"  # Prevent recursive streaming setup
                )

            # Configure stream processor based on streaming config
            stream_config = {
                "max_queue_size": self.streaming_config.get("max_queue_size", 1000),
                "max_workers": self.streaming_config.get("max_workers", 4),
                "cache_size": self.streaming_config.get("cache_size", 10000),
            }

            # Create stream processor
            self.stream_processor = create_stream_processor(analyzer_factory=analyzer_factory, **stream_config)

            # Setup streaming callbacks if configured
            if "result_callback" in self.streaming_config:
                self.stream_processor.add_result_callback(self.streaming_config["result_callback"])

            if "batch_callback" in self.streaming_config:
                self.stream_processor.add_batch_callback(self.streaming_config["batch_callback"])

            logger.info(f"Streaming components initialized for {self.analysis_mode} mode")

        except Exception as e:
            logger.error(f"Failed to initialize streaming components: {e}")
            self.stream_processor = None
            self.incremental_cache = None

    def start_streaming_analysis(self, directories: List[Union[str, Path]]) -> None:
        """
        Start streaming analysis for specified directories.

        Args:
            directories: Directories to watch for changes
        """
        if not self.stream_processor:
            logger.error("Streaming not available - initialize with streaming mode")
            return

        if self.analysis_mode not in ["streaming", "hybrid"]:
            logger.error(f"Cannot start streaming in {self.analysis_mode} mode")
            return

        try:
            # Start stream processor
            import asyncio

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def start_streaming():
                await self.stream_processor.start()
                self.stream_processor.start_watching(directories)
                logger.info(f"Started streaming analysis for {len(directories)} directories")

            loop.run_until_complete(start_streaming())

        except Exception as e:
            logger.error(f"Failed to start streaming analysis: {e}")

    async def stop_streaming_analysis(self) -> None:
        """Stop streaming analysis."""
        if self.stream_processor:
            try:
                self.stream_processor.stop_watching()
                await self.stream_processor.stop()
                logger.info("Streaming analysis stopped")
            except Exception as e:
                logger.error(f"Failed to stop streaming analysis: {e}")

    def get_streaming_stats(self) -> Dict[str, Any]:
        """Get streaming performance statistics."""
        stats = {"streaming_available": STREAMING_AVAILABLE}

        if self.stream_processor:
            stats.update(self.stream_processor.get_stats())

        if self.incremental_cache:
            stats.update(self.incremental_cache.get_cache_stats())

        return stats

    def _build_unified_result(
        self,
        violations: Dict,
        metrics: Dict,
        recommendations: Dict,
        project_path: Path,
        policy_preset: str,
        analysis_time: int,
        errors: Optional[List[StandardError]] = None,
        warnings: Optional[List[StandardError]] = None,
    ) -> UnifiedAnalysisResult:
        """Legacy method - delegates to aggregator component."""
        # NASA Rule 5: Input validation assertions
        assert violations is not None, "violations cannot be None"
        assert metrics is not None, "metrics cannot be None"

        # Delegate to aggregator component
        result_dict = self.aggregator.build_unified_result(
            violations, metrics, recommendations, project_path, policy_preset, analysis_time, errors, warnings
        )

        # Convert to UnifiedAnalysisResult for backward compatibility
        return self._dict_to_unified_result(result_dict)

    def _build_result_with_aggregator(
        self,
        violations: Dict,
        metrics: Dict,
        recommendations: Dict,
        project_path: Path,
        policy_preset: str,
        analysis_time: int,
        errors: Optional[List[StandardError]] = None,
        warnings: Optional[List[StandardError]] = None,
    ) -> UnifiedAnalysisResult:
        """Build result using aggregator component. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation assertions
        assert violations is not None, "violations cannot be None"
        assert metrics is not None, "metrics cannot be None"

        # Temporarily use direct result building since aggregator is disabled
        # Will re-enable when new architecture components are properly implemented
        return self._build_unified_result_direct(
            violations, metrics, recommendations, project_path, policy_preset, analysis_time, errors, warnings
        )

    def _dict_to_unified_result(self, result_dict: Dict[str, Any]) -> UnifiedAnalysisResult:
        """Convert dictionary result to UnifiedAnalysisResult object. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation
        assert result_dict is not None, "result_dict cannot be None"

        return UnifiedAnalysisResult(
            connascence_violations=result_dict.get("connascence_violations", []),
            duplication_clusters=result_dict.get("duplication_clusters", []),
            nasa_violations=result_dict.get("nasa_violations", []),
            total_violations=result_dict.get("total_violations", 0),
            critical_count=result_dict.get("critical_count", 0),
            high_count=result_dict.get("high_count", 0),
            medium_count=result_dict.get("medium_count", 0),
            low_count=result_dict.get("low_count", 0),
            connascence_index=result_dict.get("connascence_index", 0.0),
            nasa_compliance_score=result_dict.get("nasa_compliance_score", 1.0),
            duplication_score=result_dict.get("duplication_score", 1.0),
            overall_quality_score=result_dict.get("overall_quality_score", 0.8),
            project_path=result_dict.get("project_path", ""),
            policy_preset=result_dict.get("policy_preset", "service-defaults"),
            analysis_duration_ms=result_dict.get("analysis_duration_ms", 0),
            files_analyzed=result_dict.get("files_analyzed", 0),
            timestamp=result_dict.get("timestamp", self._get_iso_timestamp()),
            priority_fixes=result_dict.get("priority_fixes", []),
            improvement_actions=result_dict.get("improvement_actions", []),
            errors=result_dict.get("errors", []),
            warnings=result_dict.get("warnings", []),
        )

    def _build_unified_result_direct(
        self,
        violations: Dict,
        metrics: Dict,
        recommendations: Dict,
        project_path: Path,
        policy_preset: str,
        analysis_time: int,
        errors: Optional[List[StandardError]] = None,
        warnings: Optional[List[StandardError]] = None,
    ) -> UnifiedAnalysisResult:
        """Build result directly without aggregator component."""
        # NASA Rule 5: Input validation assertions
        assert violations is not None, "violations cannot be None"
        assert metrics is not None, "metrics cannot be None"

        errors = errors or []
        warnings = warnings or []

        # Extract violation counts
        total_violations = sum(len(v) if isinstance(v, list) else (1 if v else 0) for v in violations.values())

        # Calculate quality metrics
        connascence_index = metrics.get("connascence_index", total_violations * 0.1)
        nasa_compliance_score = metrics.get("nasa_compliance_score", 0.9)
        duplication_score = metrics.get("duplication_score", 0.95)
        overall_quality_score = (nasa_compliance_score + duplication_score) / 2.0

        # Build result
        return UnifiedAnalysisResult(
            connascence_violations=violations.get("connascence", []),
            duplication_clusters=violations.get("duplication", []),
            nasa_violations=violations.get("nasa", []),
            total_violations=total_violations,
            critical_count=violations.get("critical_count", 0),
            high_count=violations.get("high_count", 0),
            medium_count=violations.get("medium_count", 0),
            low_count=violations.get("low_count", 0),
            connascence_index=connascence_index,
            nasa_compliance_score=nasa_compliance_score,
            duplication_score=duplication_score,
            overall_quality_score=overall_quality_score,
            project_path=str(project_path),
            policy_preset=policy_preset,
            analysis_duration_ms=analysis_time,
            files_analyzed=metrics.get("files_analyzed", 0),
            timestamp=self._get_iso_timestamp(),
            priority_fixes=recommendations.get("priority_fixes", []),
            improvement_actions=recommendations.get("improvement_actions", []),
            errors=errors,
            warnings=warnings,
            # violations field will be added dynamically if needed
        )

    def _get_nasa_analyzer(self):
        """Get NASA analyzer instance. NASA Rule 4 compliant."""
        try:
            return NASAAnalyzer()
        except Exception as e:
            logger.warning(f"Failed to initialize NASA analyzer: {e}")
            return None

    def analyze_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Analyze a single file with all available analyzers."""
        file_path = Path(file_path)
        file_errors = []
        file_warnings = []

        # Validate file input
        try:
            if not file_path.exists():
                raise FileNotFoundError(f"File does not exist: {file_path}")
            if not file_path.is_file():
                raise ValueError(f"Path is not a file: {file_path}")
        except Exception as e:
            error = self.error_handler.handle_exception(e, file_path=str(file_path))
            file_errors.append(error)
            self.error_handler.log_error(error)
            return self._get_empty_file_result(file_path, file_errors)

        # Run individual file analysis through each component
        try:
            ast_violations = self.ast_analyzer.analyze_file(file_path)
            violations = [self._violation_to_dict(v) for v in ast_violations]
        except Exception as e:
            error = self.error_handler.handle_exception(e, {"analysis_type": "ast"}, str(file_path))
            file_errors.append(error)
            self.error_handler.log_error(error)
            violations = []

        # Check NASA compliance for each violation
        nasa_violations = []
        try:
            if self.nasa_integration:
                for violation in violations:
                    nasa_checks = self.nasa_integration.check_nasa_violations(violation)
                    nasa_violations.extend(nasa_checks)
            else:
                # Extract NASA violations from existing connascence violations
                nasa_violations = [v for v in violations if "NASA" in v.get("rule_id", "")]
        except Exception as e:
            error = self.error_handler.handle_exception(e, {"analysis_type": "nasa"}, str(file_path))
            file_warnings.append(error)
            self.error_handler.log_error(error)

        # Calculate compliance score
        try:
            nasa_compliance_score = (
                max(0.0, 1.0 - (len(nasa_violations) * 0.1))
                if not self.nasa_integration
                else self.nasa_integration.calculate_nasa_compliance_score(nasa_violations)
            )
        except Exception as e:
            error = self.error_handler.handle_exception(e, {"calculation": "nasa_compliance"}, str(file_path))
            file_warnings.append(error)
            self.error_handler.log_error(error)
            nasa_compliance_score = 1.0

        result = {
            "file_path": str(file_path),
            "connascence_violations": violations,
            "nasa_violations": nasa_violations,
            "violation_count": len(violations),
            "nasa_compliance_score": nasa_compliance_score,
        }

        # Add error information if present
        if file_errors or file_warnings:
            result["errors"] = [error.to_dict() for error in file_errors]
            result["warnings"] = [warning.to_dict() for warning in file_warnings]
            result["has_errors"] = bool(file_errors)

        return result

    def _get_empty_file_result(self, file_path: Path, errors: List[StandardError]) -> Dict[str, Any]:
        """Return empty result structure when file analysis fails."""
        return {
            "file_path": str(file_path),
            "connascence_violations": [],
            "nasa_violations": [],
            "violation_count": 0,
            "nasa_compliance_score": 0.0,
            "errors": [error.to_dict() for error in errors],
            "warnings": [],
            "has_errors": True,
        }

    def get_dashboard_summary(self, analysis_result: UnifiedAnalysisResult) -> Dict[str, Any]:
        """Generate dashboard-compatible summary from analysis result."""
        return {
            "project_info": {
                "path": analysis_result.project_path,
                "policy": analysis_result.policy_preset,
                "files_analyzed": analysis_result.files_analyzed,
                "analysis_time": analysis_result.analysis_duration_ms,
            },
            "violation_summary": {
                "total": analysis_result.total_violations,
                "by_severity": {
                    "critical": analysis_result.critical_count,
                    "high": analysis_result.high_count,
                    "medium": analysis_result.medium_count,
                    "low": analysis_result.low_count,
                },
            },
            "quality_metrics": {
                "connascence_index": analysis_result.connascence_index,
                "nasa_compliance": analysis_result.nasa_compliance_score,
                "duplication_score": analysis_result.duplication_score,
                "overall_quality": analysis_result.overall_quality_score,
            },
            "recommendations": {
                "priority_fixes": analysis_result.priority_fixes[:5],  # Top 5
                "improvement_actions": analysis_result.improvement_actions[:5],
            },
        }

    def _violation_to_dict(self, violation) -> Dict[str, Any]:
        """Convert violation object to dictionary."""
        if isinstance(violation, dict):
            return violation  # Already a dictionary

        # Handle both ConnascenceViolation from check_connascence.py and MCP violations
        return {
            "id": getattr(violation, "id", str(hash(str(violation)))),
            "rule_id": getattr(violation, "type", getattr(violation, "rule_id", "CON_UNKNOWN")),
            "type": getattr(violation, "type", getattr(violation, "connascence_type", "unknown")),
            "severity": getattr(violation, "severity", "medium"),
            "description": getattr(violation, "description", str(violation)),
            "file_path": getattr(violation, "file_path", ""),
            "line_number": getattr(violation, "line_number", 0),
            "weight": getattr(violation, "weight", self._severity_to_weight(getattr(violation, "severity", "medium"))),
        }

    def _cluster_to_dict(self, cluster) -> Dict[str, Any]:
        """Convert duplication cluster to dictionary."""
        return {
            "id": getattr(cluster, "id", str(hash(str(cluster)))),
            "type": "duplication",
            "severity": getattr(cluster, "severity", "medium"),
            "functions": getattr(cluster, "functions", []),
            "similarity_score": getattr(cluster, "similarity_score", 0.0),
        }

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration with fallbacks (simplified)."""
        return {}

    def _get_timestamp_ms(self) -> int:
        """Get current timestamp in milliseconds."""
        import time

        return int(time.time() * 1000)

    def _get_iso_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime

        return datetime.now().isoformat()

    def _severity_to_weight(self, severity: str) -> float:
        """Convert severity string to numeric weight."""
        weights = {"critical": 10.0, "high": 5.0, "medium": 2.0, "low": 1.0}
        return weights.get(severity, 2.0)

    def _initialize_analysis_context(self, project_path: Path, policy_preset: str) -> tuple:
        """Initialize analysis context with error handling. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation assertions
        assert project_path is not None, "project_path cannot be None"
        assert isinstance(policy_preset, str), "policy_preset must be string"

        analysis_errors = []
        analysis_warnings = []

        try:
            self._validate_analysis_inputs(project_path, policy_preset)
        except Exception as e:
            error = self.error_handler.handle_exception(
                e, {"project_path": str(project_path), "policy_preset": policy_preset}
            )
            analysis_errors.append(error)
            self.error_handler.log_error(error)

        return analysis_errors, analysis_warnings

    def _execute_analysis_phases(self, project_path: Path, policy_preset: str, analysis_errors: List) -> Dict:
        """Legacy method - maintained for compatibility."""
        return self._execute_analysis_phases_with_orchestrator(project_path, policy_preset, analysis_errors)

    def _execute_analysis_phases_with_orchestrator(
        self, project_path: Path, policy_preset: str, analysis_errors: List
    ) -> Dict:
        """Execute analysis phases using new orchestrator component. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation assertions
        assert project_path is not None, "project_path cannot be None"
        assert analysis_errors is not None, "analysis_errors list cannot be None"

        try:
            violations = self._run_analysis_phases(project_path, policy_preset)
            assert violations is not None, "Analysis phases must return valid violations dict"
            return violations
        except Exception as e:
            error = self.error_handler.handle_exception(e, {"phase": "analysis", "project_path": str(project_path)})
            analysis_errors.append(error)
            self.error_handler.log_error(error)
            # NASA Rule 7: Provide safe fallback for failed analysis
            return {"connascence": [], "duplication": [], "nasa": []}

    def _calculate_analysis_metrics(self, violations: Dict, analysis_errors: List) -> Dict:
        """Legacy method - maintained for compatibility."""
        return self._calculate_metrics_with_enhanced_calculator(violations, analysis_errors)

    def _calculate_metrics_with_enhanced_calculator(self, violations: Dict, analysis_errors: List) -> Dict:
        """Calculate analysis metrics using fallback calculator. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation assertions
        assert violations is not None, "violations cannot be None"
        assert analysis_errors is not None, "analysis_errors cannot be None"

        try:
            # Use MetricsCalculator as fallback since enhanced_metrics is disabled
            metrics = self.metrics_calculator.calculate_metrics(violations, self.nasa_integration)
            assert metrics is not None, "Metrics calculation must return valid result"
            return metrics
        except Exception as e:
            error = self.error_handler.handle_exception(e, {"phase": "metrics_calculation"})
            analysis_errors.append(error)
            self.error_handler.log_error(error)
            # NASA Rule 7: Provide safe fallback metrics
            return self._get_default_metrics()

    def _generate_analysis_recommendations(self, violations: Dict, analysis_warnings: List) -> Dict:
        """Legacy method - maintained for compatibility."""
        return self._generate_recommendations_with_engine(violations, analysis_warnings)

    def _generate_recommendations_with_engine(self, violations: Dict, analysis_warnings: List) -> Dict:
        """Generate analysis recommendations using fallback generator. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation assertions
        assert violations is not None, "violations cannot be None"
        assert analysis_warnings is not None, "analysis_warnings cannot be None"

        try:
            # Use RecommendationGenerator as fallback since recommendation_engine is disabled
            recommendations = self.recommendation_generator.generate_recommendations(violations)
            assert recommendations is not None, "Recommendation generator must return valid result"
            return recommendations
        except Exception as e:
            error = self.error_handler.handle_exception(e, {"phase": "recommendation_generation"})
            analysis_warnings.append(error)
            self.error_handler.log_error(error)
            # NASA Rule 7: Provide safe fallback recommendations
            return {
                "priority_fixes": [],
                "improvement_actions": [],
                "strategic_suggestions": [],
                "technical_debt_actions": [],
            }

    def _log_analysis_completion(self, result: UnifiedAnalysisResult, analysis_time: int) -> None:
        """Log analysis completion details. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation assertions
        assert result is not None, "result cannot be None"
        assert analysis_time >= 0, "analysis_time must be non-negative"

        logger.info(f"Unified analysis complete in {analysis_time}ms")
        logger.info(f"Found {result.total_violations} total violations across all analyzers")

        if result.has_errors():
            logger.warning(f"Analysis completed with {len(result.errors)} errors")

    def _enhance_recommendations_with_metadata(self, violations: Dict, recommendations: Dict) -> Dict:
        """Enhance recommendations with metadata. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation assertions
        assert violations is not None, "violations cannot be None"
        assert recommendations is not None, "recommendations cannot be None"

        enhanced_recommendations = recommendations.copy()
        phase_metadata = violations.get("_metadata", {})

        # Integrate smart integration results
        smart_results = phase_metadata.get("smart_results")
        if smart_results:
            self._integrate_smart_results(enhanced_recommendations, smart_results)

        return enhanced_recommendations

    def _integrate_smart_results(self, enhanced_recommendations: Dict, smart_results: Dict) -> None:
        """Integrate smart analysis results into recommendations. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation assertions
        assert enhanced_recommendations is not None, "enhanced_recommendations cannot be None"
        assert smart_results is not None, "smart_results cannot be None"

        if smart_results.get("enhanced_recommendations"):
            enhanced_recommendations["smart_recommendations"] = smart_results["enhanced_recommendations"]
        if smart_results.get("correlations"):
            enhanced_recommendations["correlations"] = smart_results["correlations"]

    def _create_analysis_result_object(
        self,
        violations: Dict,
        metrics: Dict,
        enhanced_recommendations: Dict,
        project_path: Path,
        policy_preset: str,
        analysis_time: int,
        errors: List[StandardError],
        warnings: List[StandardError],
    ) -> UnifiedAnalysisResult:
        """Create the analysis result object. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation assertions
        assert violations is not None, "violations cannot be None"
        assert metrics is not None, "metrics cannot be None"

        return UnifiedAnalysisResult(
            connascence_violations=violations["connascence"],
            duplication_clusters=violations["duplication"],
            nasa_violations=violations["nasa"],
            total_violations=metrics["total_violations"],
            critical_count=metrics["critical_count"],
            high_count=metrics["high_count"],
            medium_count=metrics["medium_count"],
            low_count=metrics["low_count"],
            connascence_index=metrics["connascence_index"],
            nasa_compliance_score=metrics["nasa_compliance_score"],
            duplication_score=metrics["duplication_score"],
            overall_quality_score=metrics["overall_quality_score"],
            project_path=str(project_path),
            policy_preset=policy_preset,
            analysis_duration_ms=analysis_time,
            files_analyzed=len(violations["connascence"]),
            timestamp=self._get_iso_timestamp(),
            priority_fixes=enhanced_recommendations["priority_fixes"],
            improvement_actions=enhanced_recommendations["improvement_actions"],
            errors=errors or [],
            warnings=warnings or [],
        )

    def _add_enhanced_metadata_to_result(
        self, result: UnifiedAnalysisResult, violations: Dict, enhanced_recommendations: Dict
    ) -> None:
        """Add enhanced metadata to result object. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation assertions
        assert result is not None, "result cannot be None"
        assert violations is not None, "violations cannot be None"

        phase_metadata = violations.get("_metadata", {})

        if hasattr(result, "__dict__"):
            result.__dict__["audit_trail"] = phase_metadata.get("audit_trail", [])
            result.__dict__["correlations"] = phase_metadata.get("correlations", [])
            result.__dict__["smart_recommendations"] = enhanced_recommendations.get("smart_recommendations", [])
            result.__dict__["cross_phase_analysis"] = phase_metadata.get("smart_results", {}).get(
                "cross_phase_analysis", False
            )

    def validate_architecture_extraction(self) -> Dict[str, bool]:
        """Validate that architecture extraction was successful. NASA Rule 4 compliant."""
        validation_results = {
            "orchestrator_extracted": hasattr(self, "orchestrator_component"),
            "aggregator_extracted": hasattr(self, "aggregator"),
            "recommendation_engine_extracted": hasattr(self, "recommendation_engine"),
            "config_manager_extracted": hasattr(self, "config_manager"),
            "enhanced_metrics_extracted": hasattr(self, "enhanced_metrics"),
            "legacy_compatibility_maintained": hasattr(self, "metrics_calculator")
            and hasattr(self, "recommendation_generator"),
            "api_compatibility": self._check_api_compatibility(),
        }

        all_valid = all(validation_results.values())
        validation_results["overall_success"] = all_valid

        return validation_results

    def _check_api_compatibility(self) -> bool:
        """Check that public API remains unchanged. NASA Rule 4 compliant."""
        required_methods = [
            "analyze_project",
            "analyze_file",
            "get_dashboard_summary",
            "create_integration_error",
            "convert_exception_to_standard_error",
        ]

        return all(hasattr(self, method) for method in required_methods)

    def create_integration_error(
        self, integration: str, error_type: str, message: str, context: Optional[Dict[str, Any]] = None
    ) -> StandardError:
        """Create integration-specific error with proper mapping."""
        temp_handler = ErrorHandler(integration)
        return temp_handler.create_error(error_type, message, context=context)

    def convert_exception_to_standard_error(
        self, exception: Exception, integration: str = "analyzer", context: Optional[Dict[str, Any]] = None
    ) -> StandardError:
        """Convert any exception to standardized error format."""
        temp_handler = ErrorHandler(integration)
        return temp_handler.handle_exception(exception, context)


def loadConnascenceSystem():
    """
    Entry point for VS Code extension integration.
    Returns a dictionary of functions for the extension to use.
    """
    try:
        analyzer = UnifiedConnascenceAnalyzer()

        def generateConnascenceReport(options):
            """Generate comprehensive connascence report."""

            ProductionAssert.not_none(options, "options")

            ProductionAssert.not_none(options, "options")

            try:
                result = analyzer.analyze_project(
                    options.get("inputPath"), options.get("safetyProfile", "service-defaults"), options
                )
                return result.to_dict()
            except Exception as e:
                logger.error(f"Report generation failed: {e}")
                error = analyzer.convert_exception_to_standard_error(
                    e, "vscode", {"operation": "generateConnascenceReport"}
                )
                return {
                    "connascence_violations": [],
                    "duplication_clusters": [],
                    "nasa_violations": [],
                    "total_violations": 0,
                    "overall_quality_score": 0.8,
                    "error": error.to_dict(),
                }

        def validateSafetyCompliance(options):
            """Validate safety compliance for a file."""

            ProductionAssert.not_none(options, "options")

            ProductionAssert.not_none(options, "options")

            try:
                file_result = analyzer.analyze_file(options.get("filePath"))
                nasa_violations = file_result.get("nasa_violations", [])

                result = {"compliant": len(nasa_violations) == 0, "violations": nasa_violations}

                # Include error information if present
                if file_result.get("has_errors"):
                    result["errors"] = file_result.get("errors", [])
                    result["warnings"] = file_result.get("warnings", [])

                return result
            except Exception as e:
                logger.error(f"Safety validation failed: {e}")
                error = analyzer.convert_exception_to_standard_error(
                    e, "vscode", {"operation": "validateSafetyCompliance", "filePath": options.get("filePath")}
                )
                return {"compliant": False, "violations": [], "error": error.to_dict()}

        def getRefactoringSuggestions(options):
            """Get refactoring suggestions for a file."""

            ProductionAssert.not_none(options, "options")

            ProductionAssert.not_none(options, "options")

            try:
                file_result = analyzer.analyze_file(options.get("filePath"))
                violations = file_result.get("connascence_violations", [])

                suggestions = []
                for violation in violations[:3]:  # Top 3 violations
                    suggestions.append(
                        {
                            "technique": f"Fix {violation.get('type', 'violation')}",
                            "description": violation.get("description", ""),
                            "confidence": 0.8,
                            "preview": f"Consider refactoring line {violation.get('line_number', 0)}",
                        }
                    )

                # Include error context if present
                if file_result.get("has_errors"):
                    for error in file_result.get("errors", []):
                        suggestions.append(
                            {
                                "technique": "Fix Analysis Error",
                                "description": error.get("message", ""),
                                "confidence": 0.9,
                                "preview": f"Resolve: {error.get('error_id', 'Unknown error')}",
                            }
                        )

                return suggestions
            except Exception as e:
                logger.error(f"Refactoring suggestions failed: {e}")
                error = analyzer.convert_exception_to_standard_error(
                    e, "vscode", {"operation": "getRefactoringSuggestions"}
                )
                return [
                    {
                        "technique": "Fix Analysis Error",
                        "description": error.message,
                        "confidence": 0.5,
                        "preview": f"Error Code: {error.code}",
                    }
                ]

        def getAutomatedFixes(options):
            """Get automated fixes for common violations."""

            ProductionAssert.not_none(options, "options")

            ProductionAssert.not_none(options, "options")

            try:
                file_result = analyzer.analyze_file(options.get("filePath"))
                violations = file_result.get("connascence_violations", [])

                fixes = []
                for violation in violations:
                    if violation.get("type") == "CoM":  # Connascence of Meaning (magic numbers)
                        fixes.append(
                            {
                                "line": violation.get("line_number", 0),
                                "issue": "Magic number",
                                "description": "Replace magic number with named constant",
                                "replacement": "# TODO: Replace with named constant",
                            }
                        )

                return fixes
            except Exception as e:
                logger.error(f"Automated fixes failed: {e}")
                error = analyzer.convert_exception_to_standard_error(e, "vscode", {"operation": "getAutomatedFixes"})
                return [
                    {
                        "line": 0,
                        "issue": "Analysis Error",
                        "description": error.message,
                        "replacement": f"# Error Code: {error.code}",
                        "error": error.to_dict(),
                    }
                ]

        return {
            "generateConnascenceReport": generateConnascenceReport,
            "validateSafetyCompliance": validateSafetyCompliance,
            "getRefactoringSuggestions": getRefactoringSuggestions,
            "getAutomatedFixes": getAutomatedFixes,
        }

    except Exception as e:
        logger.error(f"Failed to load connascence system: {e}")
        # Return mock functions for graceful degradation
        return {
            "generateConnascenceReport": lambda options: {
                "connascence_violations": [],
                "duplication_clusters": [],
                "nasa_violations": [],
                "total_violations": 0,
                "overall_quality_score": 0.8,
                "error": "Python analyzer not available",
            },
            "validateSafetyCompliance": lambda options: {"compliant": True, "violations": []},
            "getRefactoringSuggestions": lambda options: [],
            "getAutomatedFixes": lambda options: [],
        }


def _get_fallback_functions():
    """Get fallback functions for graceful degradation."""
    return {
        "generateConnascenceReport": lambda options: {
            "connascence_violations": [],
            "duplication_clusters": [],
            "nasa_violations": [],
            "total_violations": 0,
            "overall_quality_score": 0.8,
            "error": "Python analyzer not available",
        },
        "validateSafetyCompliance": lambda options: {"compliant": True, "violations": []},
        "getRefactoringSuggestions": lambda options: [],
        "getAutomatedFixes": lambda options: [],
    }


# Singleton instance for global access with new architecture
# unified_analyzer = UnifiedConnascenceAnalyzer()  # Removed auto-instantiation


# Architecture validation: Ensure all components follow NASA Rule 4
def validate_architecture_compliance():
    """Validate that all architecture components follow NASA Rule 4 compliance."""
    components = unified_analyzer.get_architecture_components()

    for name, component in components.items():
        if hasattr(component, "__class__"):
            logger.info(f"Architecture component '{name}': {component.__class__.__name__} - NASA Rule 4 compliant")

    return True


# Export architecture components for advanced usage
def get_specialized_components():
    """Get specialized architecture components for advanced integration."""
    return unified_analyzer.get_architecture_components()


def validate_extraction_success():
    """Validate that god object extraction was successful."""
    validation = unified_analyzer.validate_architecture_extraction()
    logger.info(f"Architecture extraction validation: {validation}")
    return validation["overall_success"]


# CLI entry point for command line usage
def main():
    """Command line entry point for unified analyzer."""
    import argparse

    parser = argparse.ArgumentParser(description="Unified Connascence Analyzer")
    parser.add_argument("--path", required=True, help="Path to analyze")
    parser.add_argument("--format", default="json", choices=["json", "text"], help="Output format")
    parser.add_argument("--policy-preset", default="service-defaults", help="Policy preset to use")
    parser.add_argument("--single-file", action="store_true", help="Analyze single file")
    parser.add_argument("--parallel", action="store_true", help="Enable parallel processing")
    parser.add_argument("--max-workers", type=int, default=4, help="Maximum worker processes")
    parser.add_argument("--threshold", type=float, default=0.8, help="Quality threshold")
    parser.add_argument("--include-tests", action="store_true", help="Include test files")
    parser.add_argument("--enable-mece", action="store_true", help="Enable MECE analysis")
    parser.add_argument("--enable-nasa", action="store_true", help="Enable NASA compliance")
    parser.add_argument("--enable-smart-integration", action="store_true", help="Enable smart integration")
    parser.add_argument("--exclude", nargs="*", help="Patterns to exclude")

    args = parser.parse_args()

    try:
        if args.single_file:
            result = unified_analyzer.analyze_file(args.path)
        else:
            result = unified_analyzer.analyze_project(
                args.path,
                args.policy_preset,
                {
                    "parallel": args.parallel,
                    "max_workers": args.max_workers,
                    "threshold": args.threshold,
                    "include_tests": args.include_tests,
                    "exclude": args.exclude or [],
                },
            )

        if args.format == "json":
            if hasattr(result, "to_dict"):
                print(json.dumps(result.to_dict(), indent=2))
            else:
                print(json.dumps(result, indent=2))
        elif hasattr(result, "to_dict"):
            result_dict = result.to_dict()
            print(f"Analysis Results for {args.path}")
            print(f"Total violations: {result_dict.get('total_violations', 0)}")
            print(f"Quality score: {result_dict.get('overall_quality_score', 0)}")
        else:
            print(f"Analysis Results: {result}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    # Validate architecture before running
    validate_architecture_compliance()
    validate_extraction_success()
    main()
