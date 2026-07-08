"""Guards that the NASA-compliance workflow can no longer hardcode a pass."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_nasa_workflow_has_no_hardcoded_pass():
    text = (ROOT / ".github" / "workflows" / "nasa-compliance-check.yml").read_text(encoding="utf-8")
    assert "passed_with_warnings" not in text, "workflow still hardcodes an overall pass"


def test_nasa_workflow_can_fail_the_build():
    text = (ROOT / ".github" / "workflows" / "nasa-compliance-check.yml").read_text(encoding="utf-8")
    # the critical-violation gate must be a live sys.exit(1), not a commented one
    assert "sys.exit(1)" in text
    assert "# sys.exit(1)" not in text
