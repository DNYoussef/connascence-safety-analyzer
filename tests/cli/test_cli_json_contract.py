import contextlib
import json
from io import StringIO

import pytest

from interfaces.cli.connascence import ConnascenceCLI


@pytest.mark.parametrize("content", ["def demo(x):\n    return x + 42\n", "class Demo:\n    pass\n"])
def test_cli_analyze_outputs_json(tmp_path, monkeypatch, content):
    cli = ConnascenceCLI()
    target = tmp_path / "example.py"
    target.write_text(content, encoding="utf-8")

    captured = {}

    def capture(payload, fmt, output_path):
        captured["payload"] = payload

    monkeypatch.setattr(cli, "_emit_result", capture)

    exit_code = cli.run(["analyze", str(target), "--format", "json"])

    assert exit_code == 0
    payload = captured["payload"]
    assert payload["target"].endswith("example.py")
    assert "findings" in payload
    assert "summary" in payload
