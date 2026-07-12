"""Behavioral proof that the NASA critical-violation gate fails closed."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_nasa_critical.py"
WORKFLOW = ROOT / ".github" / "workflows" / "nasa-compliance-check.yml"


def run_checker(report: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), str(report)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def write_report(path: Path, critical: int) -> None:
    violations = [{"severity": "critical"} for _ in range(critical)]
    path.write_text(json.dumps({"success": True, "violations": violations}), encoding="utf-8")


def test_checker_accepts_policy_limit(tmp_path: Path):
    report = tmp_path / "report.json"
    write_report(report, 5)

    result = run_checker(report)

    assert result.returncode == 0
    assert "NASA_CRITICAL_GATE_GREEN critical=5 limit=5" in result.stdout


def test_checker_rejects_excess_critical_violations(tmp_path: Path):
    report = tmp_path / "report.json"
    write_report(report, 6)

    result = run_checker(report)

    assert result.returncode == 1
    assert "NASA_CRITICAL_GATE_RED critical=6 limit=5" in result.stdout


@pytest.mark.parametrize("case", ["missing", "malformed", "invalid_schema", "analyzer_failed"])
def test_checker_rejects_unreadable_reports(tmp_path: Path, case: str):
    report = tmp_path / "report.json"
    if case == "malformed":
        report.write_text("not json", encoding="utf-8")
    elif case == "invalid_schema":
        report.write_text(json.dumps({"success": True, "violations": [{}]}), encoding="utf-8")
    elif case == "analyzer_failed":
        report.write_text(json.dumps({"success": False, "violations": []}), encoding="utf-8")

    result = run_checker(report)

    assert result.returncode == 2
    assert "NASA_CRITICAL_GATE_INVALID" in result.stderr


def test_workflow_invokes_checker_without_soft_fail():
    text = WORKFLOW.read_text(encoding="utf-8")
    step = text.split("- name: Fail on Critical Violations", 1)[1].split("\n    - name:", 1)[0]

    assert "python scripts/check_nasa_critical.py nasa-connascence-report.json" in step
    assert "continue-on-error" not in step
    assert "||" not in step
    assert "if [ -f" not in step
