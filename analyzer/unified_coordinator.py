# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors
"""
Unified Coordinator - Clean Orchestrator for Architecture Components
====================================================================

Refactored from UnifiedConnascenceAnalyzer to follow NASA Rule 4 (<400 LOC).
Delegates to specialized architecture components instead of implementing
all functionality directly.

Components:
- CacheManager: File content and AST caching
- MetricsCollector: Violation metrics and quality scoring
- ReportGenerator: Multi-format report generation
- StreamProcessor: Streaming and incremental analysis

NASA Compliance:
- Rule 4: Class under 400 LOC, functions under 60 lines
- Rule 5: Input validation assertions
- Rule 7: Bounded resource management via components
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from fixes.phase0.production_safe_assertions import ProductionAssert

# Import architecture components
from .architecture.cache_manager import CacheManager
from .architecture.metrics_collector import MetricsCollector
from .architecture.report_generator import ReportGenerator
from .architecture.stream_processor import StreamProcessor

# Import core analyzers
from .check_connascence import ConnascenceAnalyzer as ConnascenceASTAnalyzer
from .ast_engine.analyzer_orchestrator import AnalyzerOrchestrator as GodObjectOrchestrator
from .dup_detection.mece_analyzer import MECEAnalyzer
from .refactored_detector import RefactoredConnascenceDetector
from .optimization.ast_optimizer import ConnascencePatternOptimizer

# Import result dataclass from unified_analyzer
from .unified_analyzer import UnifiedAnalysisResult, ErrorHandler, ComponentInitializer

logger = logging.getLogger(__name__)


class UnifiedCoordinator:
    """
    Lightweight orchestrator coordinating specialized architecture components.

    Responsibilities (NASA Rule 1: Single Responsibility):
    1. Component initialization and lifecycle management
    2. Workflow orchestration across components
    3. Backward compatibility via aliasing
    4. High-level API surface maintenance

    NASA Rule 4: Class under 400 LOC total
    NASA Rule 7: Bounded resource management via components
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        analysis_mode: str = "batch",
        streaming_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize coordinator with architecture components.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation
        """
        assert analysis_mode in ["batch", "streaming", "hybrid"], \
            f"Invalid analysis_mode: {analysis_mode}"

        self.analysis_mode = analysis_mode
        self.config = self._load_config(config_path)

        # Initialize architecture components (dependency injection)
        self.cache_manager = CacheManager(config=self._get_cache_config())
        self.metrics_collector = MetricsCollector(config=self._get_metrics_config())
        self.report_generator = ReportGenerator(config=self._get_report_config())
        self.stream_processor = StreamProcessor(config=streaming_config or {})

        # Initialize core analyzers
        self.ast_analyzer = ConnascenceASTAnalyzer()
        self.god_object_orchestrator = GodObjectOrchestrator()
        self.mece_analyzer = MECEAnalyzer()

        # Initialize optional components via initializer
        initializer = ComponentInitializer()
        self.smart_engine = initializer.init_smart_engine()
        self.nasa_integration = initializer.init_nasa_integration()

        # Error handling
        self.error_handler = ErrorHandler("coordinator")

        logger.info(f"UnifiedCoordinator initialized (mode={analysis_mode})")

    # === PRIMARY API (4 methods) ===

    def analyze_project(
        self,
        project_path: Union[str, Path],
        policy_preset: str = "service-defaults",
        options: Optional[Dict[str, Any]] = None,
    ) -> UnifiedAnalysisResult:
        """
        Primary analysis entry point with mode routing.

        NASA Rule 4: Function under 60 lines
        """
        assert project_path is not None, "project_path cannot be None"
        project_path = Path(project_path)

        if self.analysis_mode == "streaming":
            return self._analyze_streaming(project_path, policy_preset, options)
        elif self.analysis_mode == "hybrid":
            return self._analyze_hybrid(project_path, policy_preset, options)
        else:
            return self._analyze_batch(project_path, policy_preset, options)

    def analyze_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Single file analysis. NASA Rule 4 compliant."""
        file_path = Path(file_path)
        if not file_path.exists():
            return {"file_path": str(file_path), "violations": [], "error": "File not found"}

        violations = self.ast_analyzer.analyze_file(file_path)
        metrics = self.metrics_collector.collect_violation_metrics({
            "connascence": [self._violation_to_dict(v) for v in violations],
            "duplication": [],
            "nasa": []
        })
        return {"file_path": str(file_path), "violations": violations, "metrics": metrics}

    def get_dashboard_summary(self, analysis_result: Union[Dict, UnifiedAnalysisResult]) -> str:
        """Generate dashboard summary via ReportGenerator. NASA Rule 4 compliant."""
        if hasattr(analysis_result, "to_dict"):
            metrics = analysis_result.to_dict()
        else:
            metrics = analysis_result
        return self.report_generator.format_summary(metrics)

    def export_reports(
        self,
        result: Union[Dict, UnifiedAnalysisResult],
        output_dir: Union[str, Path],
        base_name: str = "analysis"
    ) -> Dict[str, Path]:
        """Export all report formats via ReportGenerator. NASA Rule 4 compliant."""
        violations = self._extract_violations_list(result)
        return self.report_generator.generate_all_formats(
            result=result,
            violations=violations,
            output_dir=Path(output_dir),
            base_name=base_name
        )

    # === BATCH ANALYSIS PIPELINE ===

    def _analyze_batch(
        self,
        project_path: Path,
        policy_preset: str,
        options: Optional[Dict[str, Any]]
    ) -> UnifiedAnalysisResult:
        """Traditional batch analysis with cache optimization. NASA Rule 4 compliant."""
        start_time = time.time()
        logger.info(f"Starting batch analysis of {project_path}")

        # Phase 1: Cache warming via CacheManager
        self.cache_manager.warm_cache(project_path, file_limit=15)

        # Phase 2: Execute analysis phases
        violations = self._execute_analysis_phases(project_path, policy_preset)

        # Phase 3: Collect metrics via MetricsCollector
        metrics = self.metrics_collector.collect_violation_metrics(violations)
        self.metrics_collector.create_snapshot(metrics)

        # Phase 4: Generate recommendations
        recommendations = self._generate_recommendations(violations, metrics)

        # Phase 5: Build result
        analysis_time = int((time.time() - start_time) * 1000)
        result = self._build_result(
            violations, metrics, recommendations,
            project_path, policy_preset, analysis_time
        )

        # Phase 6: Log performance
        self.cache_manager.log_performance()
        logger.info(f"Batch analysis complete in {analysis_time}ms")

        return result

    def _execute_analysis_phases(self, project_path: Path, policy_preset: str) -> Dict[str, List]:
        """Execute all analysis phases. NASA Rule 4 compliant."""
        violations = {"connascence": [], "duplication": [], "nasa": []}

        # Phase 1: AST Analysis
        violations["connascence"] = self._run_ast_analysis(project_path)

        # Phase 2: Duplication Analysis
        if self.mece_analyzer:
            try:
                mece_results = self.mece_analyzer.analyze_directory(project_path)
                violations["duplication"] = [self._violation_to_dict(v) for v in mece_results]
            except Exception as e:
                logger.warning(f"MECE analysis failed: {e}")

        # Phase 3: NASA Analysis
        if self.nasa_integration:
            try:
                nasa_results = self.nasa_integration.validate_project(str(project_path))
                if isinstance(nasa_results, dict) and "violations" in nasa_results:
                    violations["nasa"] = nasa_results["violations"]
            except Exception as e:
                logger.warning(f"NASA analysis failed: {e}")

        return violations

    def _run_ast_analysis(self, project_path: Path) -> List[Dict[str, Any]]:
        """Run core AST analysis. NASA Rule 4 compliant."""
        violations = []

        # Core AST analysis
        ast_results = self.ast_analyzer.analyze_directory(project_path)
        violations.extend([self._violation_to_dict(v) for v in ast_results])

        # God object analysis
        god_results = self.god_object_orchestrator.analyze_directory(project_path)
        violations.extend([self._violation_to_dict(v) for v in god_results])

        # Refactored detector analysis
        for py_file in project_path.glob("**/*.py"):
            if self._should_analyze_file(py_file):
                try:
                    content = self.cache_manager.get_cached_content(py_file)
                    if content is None:
                        content = py_file.read_text(encoding="utf-8")
                    lines = content.splitlines()
                    detector = RefactoredConnascenceDetector(str(py_file), lines)
                    file_violations = detector.analyze(content)
                    violations.extend([self._violation_to_dict(v) for v in file_violations])
                except Exception as e:
                    logger.debug(f"Refactored analysis failed for {py_file}: {e}")

        return violations

    def _build_result(
        self,
        violations: Dict[str, List],
        metrics: Dict[str, Any],
        recommendations: Dict[str, Any],
        project_path: Path,
        policy_preset: str,
        analysis_time: int
    ) -> UnifiedAnalysisResult:
        """Build UnifiedAnalysisResult. NASA Rule 4 compliant."""
        return UnifiedAnalysisResult(
            connascence_violations=violations["connascence"],
            duplication_clusters=violations["duplication"],
            nasa_violations=violations["nasa"],
            total_violations=metrics.get("total_violations", 0),
            critical_count=metrics.get("critical_count", 0),
            high_count=metrics.get("high_count", 0),
            medium_count=metrics.get("medium_count", 0),
            low_count=metrics.get("low_count", 0),
            connascence_index=metrics.get("connascence_index", 0.0),
            nasa_compliance_score=metrics.get("nasa_compliance_score", 1.0),
            duplication_score=metrics.get("duplication_score", 1.0),
            overall_quality_score=metrics.get("overall_quality_score", 0.0),
            project_path=str(project_path),
            policy_preset=policy_preset,
            analysis_duration_ms=analysis_time,
            files_analyzed=metrics.get("files_analyzed", 0),
            timestamp=metrics.get("timestamp", ""),
            priority_fixes=recommendations.get("priority_fixes", []),
            improvement_actions=recommendations.get("improvement_actions", []),
            errors=[],
            warnings=[]
        )

    # === STREAMING ANALYSIS PIPELINE ===

    def _analyze_streaming(
        self,
        project_path: Path,
        policy_preset: str,
        options: Optional[Dict[str, Any]]
    ) -> UnifiedAnalysisResult:
        """Streaming analysis via StreamProcessor. NASA Rule 4 compliant."""
        if not self.stream_processor.is_running:
            self.stream_processor.initialize(self._create_analyzer_factory())
            asyncio.run(self.stream_processor.start_streaming([project_path]))

        result = self._analyze_batch(project_path, policy_preset, options)
        self.stream_processor.watch_directory(project_path)
        return result

    def _analyze_hybrid(
        self,
        project_path: Path,
        policy_preset: str,
        options: Optional[Dict[str, Any]]
    ) -> UnifiedAnalysisResult:
        """Hybrid analysis combining batch and streaming. NASA Rule 4 compliant."""
        batch_result = self._analyze_batch(project_path, policy_preset, options)

        if not self.stream_processor.is_running:
            self.stream_processor.initialize(self._create_analyzer_factory())
            asyncio.run(self.stream_processor.start_streaming([project_path]))
        self.stream_processor.watch_directory(project_path)

        return batch_result

    # === BACKWARD COMPATIBILITY ALIASES ===

    def _warm_cache_intelligently(self, project_path: Path) -> None:
        """Backward compatibility: delegate to CacheManager."""
        self.cache_manager.warm_cache(project_path)

    def _get_cache_hit_rate(self) -> float:
        """Backward compatibility: delegate to CacheManager."""
        return self.cache_manager.get_hit_rate()

    def _log_cache_performance(self) -> None:
        """Backward compatibility: delegate to CacheManager."""
        self.cache_manager.log_performance()

    def _calculate_metrics_with_enhanced_calculator(self, violations, errors) -> Dict:
        """Backward compatibility: delegate to MetricsCollector."""
        return self.metrics_collector.collect_violation_metrics(violations)

    def _severity_to_weight(self, severity: str) -> float:
        """Backward compatibility: use MetricsCollector normalization."""
        weights = {"critical": 10, "high": 5, "medium": 2, "low": 1, "info": 0.5}
        return weights.get(severity.lower(), 2)

    def start_streaming_analysis(self, directories: Optional[List[Path]] = None) -> bool:
        """Backward compatibility: delegate to StreamProcessor."""
        if directories:
            return asyncio.run(self.stream_processor.start_streaming(directories))
        return False

    def stop_streaming_analysis(self) -> bool:
        """Backward compatibility: delegate to StreamProcessor."""
        return asyncio.run(self.stream_processor.stop_streaming())

    def get_streaming_stats(self) -> Dict[str, Any]:
        """Backward compatibility: delegate to StreamProcessor."""
        return self.stream_processor.get_stats()

    # === HELPER METHODS ===

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration. NASA Rule 4 compliant."""
        return {}  # Uses component defaults

    def _get_cache_config(self) -> Dict[str, Any]:
        """Get cache configuration. NASA Rule 4 compliant."""
        return {"max_memory": 100 * 1024 * 1024}  # 100MB

    def _get_metrics_config(self) -> Dict[str, Any]:
        """Get metrics configuration. NASA Rule 4 compliant."""
        return {}

    def _get_report_config(self) -> Dict[str, Any]:
        """Get report configuration. NASA Rule 4 compliant."""
        return {"version": "1.0.0"}

    def _should_analyze_file(self, file_path: Path) -> bool:
        """Check if file should be analyzed. NASA Rule 4 compliant."""
        excludes = ["__pycache__", "venv", ".git", "node_modules", ".tox", "dist", "build"]
        return not any(excl in str(file_path) for excl in excludes)

    def _violation_to_dict(self, violation: Any) -> Dict[str, Any]:
        """Convert violation to dictionary. NASA Rule 4 compliant."""
        if isinstance(violation, dict):
            return violation
        if hasattr(violation, "__dict__"):
            return vars(violation)
        if hasattr(violation, "_asdict"):
            return violation._asdict()
        return {"value": str(violation)}

    def _extract_violations_list(self, result: Any) -> List[Dict[str, Any]]:
        """Extract violations list from result. NASA Rule 4 compliant."""
        if isinstance(result, dict):
            violations = result.get("violations", [])
            violations.extend(result.get("connascence_violations", []))
            return violations
        if hasattr(result, "connascence_violations"):
            return result.connascence_violations
        return []

    def _generate_recommendations(self, violations: Dict, metrics: Dict) -> Dict[str, Any]:
        """Generate recommendations. NASA Rule 4 compliant."""
        priority_fixes = []
        for v in violations.get("connascence", [])[:5]:
            if v.get("severity") in ["critical", "high"]:
                priority_fixes.append({
                    "type": v.get("type"),
                    "file": v.get("file_path"),
                    "line": v.get("line_number"),
                    "recommendation": v.get("recommendation", "Review and refactor")
                })
        return {"priority_fixes": priority_fixes, "improvement_actions": []}

    def _create_analyzer_factory(self) -> Callable:
        """Create analyzer factory for streaming. NASA Rule 4 compliant."""
        def factory():
            return self.ast_analyzer
        return factory
