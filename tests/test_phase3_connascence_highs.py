import ast
from datetime import datetime, timedelta

from analyzer.detectors.detector_factory import DetectorFactory
from analyzer.detectors.identity_detector import IdentityDetector
from analyzer.optimization.incremental_analyzer import IncrementalAnalyzer
from integrations.consolidated_integrations import (
    BlackIntegration,
    BlackIntegrationLegacy,
    MyPyIntegration,
    MyPyIntegrationLegacy,
    RuffIntegration,
    RuffIntegrationLegacy,
)
from policy.drift import DriftMetric, EnhancedDriftTracker


def test_legacy_integration_wrappers_accept_default_config():
    wrappers = [
        (BlackIntegrationLegacy, BlackIntegration),
        (MyPyIntegrationLegacy, MyPyIntegration),
        (RuffIntegrationLegacy, RuffIntegration),
    ]

    for wrapper, integration_class in wrappers:
        integration = wrapper()

        assert isinstance(integration, integration_class)
        assert integration.config == {}


def test_incremental_dependency_cache_records_import_edges(tmp_path):
    (tmp_path / "a.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("import a\n", encoding="utf-8")
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "helper.py").write_text("HELPER = True\n", encoding="utf-8")
    (package / "c.py").write_text("from . import helper\nfrom .. import a\n", encoding="utf-8")

    analyzer = IncrementalAnalyzer.__new__(IncrementalAnalyzer)
    analyzer.project_root = tmp_path
    analyzer.dependency_cache_file = tmp_path / ".connascence_deps.json"
    analyzer.dependency_graph = {}

    analyzer._update_dependency_cache()

    assert analyzer.dependency_graph["b.py"]["dependencies"] == ["a.py"]
    assert "b.py" in analyzer.dependency_graph["a.py"]["dependents"]
    assert "pkg/helper.py" in analyzer.dependency_graph["pkg/c.py"]["dependencies"]
    assert "pkg/c.py" in analyzer.dependency_graph["pkg/helper.py"]["dependents"]


def test_drift_forecast_projects_from_last_observed_measurement():
    now = datetime.now()
    tracker = EnhancedDriftTracker.__new__(EnhancedDriftTracker)
    tracker.drift_history = [
        DriftMetric(
            timestamp=(now - timedelta(days=2)).isoformat(),
            total_violations=10,
            violations_by_type={},
            violations_by_severity={},
            files_analyzed=1,
            analysis_duration_ms=1.0,
        ),
        DriftMetric(
            timestamp=(now - timedelta(days=1)).isoformat(),
            total_violations=20,
            violations_by_type={},
            violations_by_severity={},
            files_analyzed=1,
            analysis_duration_ms=1.0,
        ),
        DriftMetric(
            timestamp=now.isoformat(),
            total_violations=30,
            violations_by_type={},
            violations_by_severity={},
            files_analyzed=1,
            analysis_duration_ms=1.0,
        ),
    ]

    trend = tracker.analyze_trend(days=30)

    assert trend.rate_of_change == 10
    assert trend.forecast_7d == 100
    assert trend.forecast_30d == 330


def test_identity_detector_emits_canonical_violation_fields():
    source = "def configure():\n    global a, b, c, d, e, f\n    return a\n"
    tree = ast.parse(source)
    detector = IdentityDetector("sample.py", source.splitlines())

    violations = detector.detect(tree)

    assert len(violations) == 1
    violation = violations[0]
    assert violation.id == "CoI-sample.py:1"
    assert violation.type == "connascence_of_identity"
    assert "6 globals" in violation.description
    assert violation.context["global_vars"] == ["a", "b", "c", "d", "e", "f"]


def test_detector_factory_does_not_drop_identity_violations():
    source = "def configure():\n    global a, b, c, d, e, f\n    return a\n"
    tree = ast.parse(source)
    factory = DetectorFactory("sample.py", source.splitlines())

    violations = factory.detect_by_type(tree, ["connascence_of_identity"])

    assert [violation.type for violation in violations] == ["connascence_of_identity"]
