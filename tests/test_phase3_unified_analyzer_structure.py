import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYZER_DIR = ROOT / "analyzer"
UNIFIED_ANALYZER = ANALYZER_DIR / "unified_analyzer.py"
UNIFIED_COORDINATOR = ANALYZER_DIR / "unified_coordinator.py"
RESULT_TYPES = ANALYZER_DIR / "result_types.py"
COMPONENT_INIT = ANALYZER_DIR / "component_init.py"
MONITORING_LIFECYCLE = ANALYZER_DIR / "monitoring_lifecycle.py"


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _class_names(path: Path) -> set[str]:
    return {node.name for node in ast.walk(_tree(path)) if isinstance(node, ast.ClassDef)}


def _method_names(path: Path, class_name: str) -> set[str]:
    for node in ast.walk(_tree(path)):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {child.name for child in node.body if isinstance(child, ast.FunctionDef)}
    raise AssertionError(f"{class_name} not found in {path}")


def _class_span(path: Path, class_name: str) -> int:
    for node in ast.walk(_tree(path)):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return node.end_lineno - node.lineno + 1
    raise AssertionError(f"{class_name} not found in {path}")


def test_unified_analyzer_is_a_thin_compatibility_facade():
    unified_source = UNIFIED_ANALYZER.read_text(encoding="utf-8")
    unified_lines = unified_source.splitlines()
    coordinator_source = UNIFIED_COORDINATOR.read_text(encoding="utf-8")

    assert len(unified_lines) < 300
    assert _class_span(UNIFIED_ANALYZER, "UnifiedConnascenceAnalyzer") < 20
    assert _method_names(UNIFIED_ANALYZER, "UnifiedConnascenceAnalyzer") == set()
    assert "from .unified_coordinator import UnifiedCoordinator" in unified_source
    assert "from .unified_analyzer import" not in coordinator_source
    assert "def _run_ast_optimizer_analysis" not in unified_source
    assert "def _run_nasa_analysis" not in unified_source
    assert "def _build_unified_result_direct" not in unified_source

    from analyzer.unified_analyzer import UnifiedConnascenceAnalyzer
    from analyzer.unified_coordinator import UnifiedCoordinator

    assert issubclass(UnifiedConnascenceAnalyzer, UnifiedCoordinator)


def test_unified_analyzer_no_longer_owns_extracted_helper_classes():
    unified_lines = UNIFIED_ANALYZER.read_text(encoding="utf-8").splitlines()
    assert len(unified_lines) < 300

    extracted_class_names = {
        "StandardError",
        "UnifiedAnalysisResult",
        "ErrorHandler",
        "ComponentInitializer",
        "MetricsCalculator",
        "RecommendationGenerator",
    }

    assert extracted_class_names.isdisjoint(_class_names(UNIFIED_ANALYZER))
    assert {"StandardError", "UnifiedAnalysisResult"} <= _class_names(RESULT_TYPES)
    assert {
        "ErrorHandler",
        "ComponentInitializer",
        "MetricsCalculator",
        "RecommendationGenerator",
    } <= _class_names(COMPONENT_INIT)


def test_monitoring_lifecycle_methods_live_in_extracted_mixin():
    monitoring_methods = {
        "_setup_monitoring_and_cleanup_hooks",
        "_handle_memory_alert",
        "_emergency_memory_cleanup",
        "_aggressive_cleanup",
        "_cleanup_analysis_resources",
        "_emergency_resource_cleanup",
        "_periodic_cache_cleanup",
        "_investigate_memory_leak",
        "_log_comprehensive_monitoring_report",
    }

    assert monitoring_methods.isdisjoint(
        _method_names(UNIFIED_ANALYZER, "UnifiedConnascenceAnalyzer")
    )
    assert monitoring_methods <= _method_names(MONITORING_LIFECYCLE, "MonitoringLifecycleMixin")

    from analyzer.monitoring_lifecycle import MonitoringLifecycleMixin
    from analyzer.unified_analyzer import UnifiedConnascenceAnalyzer

    assert issubclass(UnifiedConnascenceAnalyzer, MonitoringLifecycleMixin)
