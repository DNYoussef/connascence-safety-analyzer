import json

from analyzer.check_connascence import FallbackConnascenceAnalyzer
from analyzer.core import ConnascenceAnalyzer
from utils.types import ConnascenceViolation


def test_core_analyzer_scans_external_directory(tmp_path):
    external_project = tmp_path / "external_project"
    external_project.mkdir()
    (external_project / "sample.py").write_text(
        """
def build_order(user_id, account_id, region, currency):
    total = 42
    return user_id, account_id, region, currency, total
""".strip(),
        encoding="utf-8",
    )

    result = ConnascenceAnalyzer().analyze_path(
        str(external_project),
        policy="service-defaults",
        include_duplication=False,
    )

    assert result["success"] is True
    assert result["metrics"]["files_analyzed"] >= 1
    assert result["violations"]
    assert result["violations"][0]["file_path"].endswith("sample.py")
    assert "code_snippet" not in result["violations"][0]
    json.dumps(result)


def test_fallback_directory_stats_accept_dict_and_object_violations(tmp_path, monkeypatch):
    project = tmp_path / "mixed_violations"
    project.mkdir()
    source_file = project / "sample.py"
    source_file.write_text("def sample(value):\n    return value\n", encoding="utf-8")

    analyzer = FallbackConnascenceAnalyzer()
    object_violation = ConnascenceViolation(
        type="CoT",
        severity="medium",
        file_path=str(source_file),
        line_number=1,
        description="Object violation",
    )
    dict_violation = {
        "type": "CoP",
        "severity": "high",
        "file_path": str(source_file),
        "line_number": 1,
        "description": "Dict violation",
    }

    monkeypatch.setattr(analyzer, "analyze_file", lambda _path: [dict_violation, object_violation])

    violations = analyzer.analyze_directory(project)

    assert len(violations) == 2
    assert set(analyzer.file_stats[str(source_file)]["types"]) == {"CoP", "CoT"}


def test_external_scan_artifacts_are_deterministic_and_source_free(tmp_path):
    """Emitted violations must be JSON-safe, free of source excerpts, and free of
    non-deterministic object reprs (e.g. ``<ast.arg object at 0x...>``)."""
    external_project = tmp_path / "deterministic_project"
    external_project.mkdir()
    # 4 positional params -> CoP, whose context embeds raw ast.arg nodes.
    (external_project / "sample.py").write_text(
        "def build_order(user_id, account_id, region, currency):\n"
        "    return user_id, account_id, region, currency\n",
        encoding="utf-8",
    )

    result = ConnascenceAnalyzer().analyze_path(
        str(external_project),
        policy="service-defaults",
        include_duplication=False,
    )

    assert result["success"] is True
    assert result["violations"]

    serialized = json.dumps(result)  # must not raise on embedded ast nodes
    assert "object at 0x" not in serialized, "non-deterministic memory address leaked into artifact"
    for violation in result["violations"]:
        for source_key in ("code_snippet", "source_code", "source", "snippet"):
            assert source_key not in violation
