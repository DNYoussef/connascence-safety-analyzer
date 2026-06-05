"""Phase 5 claim-control tests for MCP and fallback evidence paths."""

import ast
import json
from pathlib import Path
from types import SimpleNamespace
import tomllib

import pytest

from analyzer.detectors.detector_factory import DetectorFactory
from analyzer.core import ConnascenceAnalyzer
from autofix.patch_generator import PatchGenerator
from interfaces.cli import simple_cli
from interfaces.cli.connascence import ConnascenceCLI
from mcp import server as mcp_server


class DummyFallbackAnalyzer:
    def analyze_file(self, _path):
        return [SimpleNamespace(rule_id="CON_CoM", severity="medium", file_path="sample.py")]

    def analyze_directory(self, _path):
        return self.analyze_file(_path)


def _core_analyzer_with_fallback():
    analyzer = ConnascenceAnalyzer.__new__(ConnascenceAnalyzer)
    analyzer.version = "2.0.0"
    analyzer.analysis_mode = "fallback"
    analyzer.fallback_analyzer = DummyFallbackAnalyzer()
    return analyzer


def test_fallback_analysis_labels_nasa_and_mece_scores_unavailable(tmp_path):
    target = tmp_path / "sample.py"
    target.write_text("VALUE = 42\n", encoding="utf-8")

    result = _core_analyzer_with_fallback()._run_fallback_analysis(str(target), "default")

    assert result["success"] is True
    assert result["nasa_compliance"]["score"] is None
    assert result["nasa_compliance"]["evidence_status"] == "unavailable_fallback_analyzer"
    assert result["nasa_compliance"]["independent_evidence"] is False
    assert result["mece_analysis"]["score"] is None
    assert result["mece_analysis"]["evidence_status"] == "unavailable_fallback_analyzer"
    assert result["mece_analysis"]["independent_evidence"] is False
    assert result["nasa_compliance"]["score"] != 0.8
    assert result["mece_analysis"]["score"] != 0.75


def test_mock_analysis_fails_closed_instead_of_returning_fabricated_scores():
    analyzer = ConnascenceAnalyzer.__new__(ConnascenceAnalyzer)
    analyzer.analysis_mode = "mock"

    result = analyzer._run_mock_analysis("missing-project", "default")

    assert result["success"] is False
    assert result["violations"] == []
    assert result["summary"]["overall_quality_score"] is None
    assert result["nasa_compliance"]["score"] is None
    assert result["mece_analysis"]["score"] is None
    assert result["evidence_status"] == "real_analyzer_unavailable"


def test_core_src_and_grammar_packages_are_included_for_distribution():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    packages = set(pyproject["tool"]["setuptools"]["packages"])

    expected = {
        "core",
        "grammar",
        "grammar.backends",
        "grammar.constrained_generator",
        "src",
        "src.detectors",
        "src.library",
        "src.library.validation",
        "src.services",
        "src.utils",
    }
    assert expected.issubset(packages)
    assert Path("core/__init__.py").exists()


def test_registered_mcp_entrypoint_delegates_to_stdio_transport(monkeypatch):
    calls = {}

    async def fake_stdio_entrypoint(args):
        calls["once"] = args.once
        calls["config"] = args.config
        return 0

    monkeypatch.setattr(mcp_server, "_run_stdio_entrypoint", fake_stdio_entrypoint)

    assert mcp_server.main(["--once", "--config", "server.json"]) == 0
    assert calls == {"once": True, "config": "server.json"}


def test_registered_mcp_entrypoint_rejects_mock_serving():
    with pytest.raises(SystemExit) as exc:
        mcp_server.main(["--mock"])

    assert exc.value.code == 2


def test_registered_simple_cli_delegates_documented_commands(monkeypatch):
    calls = []

    def fake_run(self, argv):
        calls.append(argv)
        return 0

    monkeypatch.setattr(ConnascenceCLI, "run", fake_run)

    assert simple_cli.main(["explain", "CON_CoT"]) == 0
    assert calls == [["explain", "CON_CoT"]]


def test_full_cli_explain_and_license_are_not_silent_noops(capsys):
    assert ConnascenceCLI().run(["explain", "CON_CoT"]) == 0
    explain_output = capsys.readouterr().out
    assert "Connascence of Type" in explain_output
    assert "Recommendation:" in explain_output

    assert ConnascenceCLI().run(["license", "check"]) == 0
    license_output = capsys.readouterr().out
    assert "License check:" in license_output
    assert "LICENSE" in license_output


def test_simple_cli_analyzes_every_supplied_path(monkeypatch, tmp_path, capsys):
    first = tmp_path / "first.py"
    second = tmp_path / "second.py"
    first.write_text("A = 1\n", encoding="utf-8")
    second.write_text("B = 2\n", encoding="utf-8")
    analyzed_paths = []

    class FakeAnalyzer:
        def analyze_path(self, path, **_kwargs):
            analyzed_paths.append(path)
            return {
                "success": True,
                "violations": [{"file_path": path, "severity": "medium"}],
                "summary": {"overall_quality_score": 0.9},
                "god_objects": [],
            }

    monkeypatch.setattr(simple_cli, "ANALYZER_AVAILABLE", True)
    monkeypatch.setattr(simple_cli, "ConnascenceAnalyzer", FakeAnalyzer)

    exit_code = simple_cli.main(
        [
            "--format",
            "json",
            "--exit-zero",
            str(first),
            str(second),
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert analyzed_paths == [str(first), str(second)]
    assert output["analyzed_paths"] == [str(first), str(second)]
    assert len(output["violations"]) == 2


def test_detector_factory_uses_dedicated_type_detector_for_cot():
    source = """
def process_order(order, retry_count: int):
    return order
"""
    tree = ast.parse(source)
    factory = DetectorFactory("sample.py", source.splitlines())

    violations = factory.detect_by_type(tree, ["connascence_of_type"])

    assert len(violations) == 1
    assert violations[0].type == "connascence_of_type"
    assert violations[0].rule_id == "CON_CoT"
    assert violations[0].context["missing_parameters"] == ["order"]


def test_architectural_autofixes_do_not_emit_todo_comment_patches(tmp_path):
    target = tmp_path / "sample.py"
    target.write_text("class GodObject:\n    pass\n", encoding="utf-8")
    generator = PatchGenerator()

    god_patch = generator.generate_patch(
        {
            "type": "god_object",
            "file_path": str(target),
            "line_number": 1,
            "severity": "medium",
        },
        {"code_context": target.read_text(encoding="utf-8")},
    )
    param_patch = generator.generate_patch(
        {
            "type": "parameter_position",
            "file_path": str(target),
            "line_number": 1,
            "severity": "medium",
        },
        {"code_context": "def f(a, b, c, d): pass"},
    )

    for patch in (god_patch, param_patch):
        assert patch.operations == []
        assert "manual refactor required" in patch.description.lower()
        assert "TODO" not in patch.description
        result = generator.apply_patch(patch)
        assert result["success"] is False
        assert "manual refactor required" in result["error"]
