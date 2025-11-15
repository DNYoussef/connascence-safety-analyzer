# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors
"""Regression tests for the MCP CLI entry points."""

import asyncio
import json
from types import SimpleNamespace

from mcp import cli as mcp_cli


def test_cli_analyze_file_payload(tmp_path, capsys):
    sample_file = tmp_path / "sample.py"
    sample_file.write_text(
        """
PORT = 8080


def demo(value):
    if value > PORT:
        return value - PORT
    return value
"""
    )

    args = SimpleNamespace(
        file_path=str(sample_file),
        analysis_type="full",
        include_integrations=False,
        format="json",
        output=None,
        config={},
    )

    exit_code = asyncio.run(mcp_cli.analyze_file_command(args))
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["success"] is True
    assert payload["file_path"].endswith("sample.py")
    assert "summary" in payload
    assert "nasa_compliance" in payload
    assert "metrics" in payload


def test_cli_health_check_payload(capsys):
    args = SimpleNamespace(config={})
    exit_code = asyncio.run(mcp_cli.health_check_command(args))
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["success"] is True
    assert payload["server"]["name"] == "connascence-analyzer-mcp"
    assert payload["analyzer"]["analyzer_available"] is True


def test_cli_mcp_server_once_flag(capsys):
    args = SimpleNamespace(config={}, once=True)
    exit_code = asyncio.run(mcp_cli.mcp_server_command(args))
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["event"] == "server_ready"
    assert payload["info"]["name"] == "connascence-analyzer-mcp"
