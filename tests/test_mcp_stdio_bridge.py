"""Focused protocol tests for the standalone MCP stdio bridge."""

import asyncio
from dataclasses import dataclass
import json

import mcp_stdio_bridge as bridge


@dataclass
class Response:
    success: bool
    payload: dict

    def to_dict(self):
        return {"success": self.success, **self.payload}


class Server:
    def __init__(self, response=None):
        self.response = response
        self.calls = []

    async def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        print("server diagnostic")
        return self.response


def test_tool_failure_is_structured_and_marked_error(monkeypatch, capsys):
    sent = []
    monkeypatch.setattr(bridge, "_send", sent.append)
    server = Server(Response(False, {"error": "missing file"}))

    asyncio.run(bridge.handle(server, {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "analyze_file", "arguments": {"file_path": "missing.py"}},
    }))

    assert sent[0]["result"]["isError"] is True
    assert json.loads(sent[0]["result"]["content"][0]["text"])["error"] == "missing file"
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "server diagnostic" in captured.err


def test_notifications_never_receive_responses(monkeypatch):
    sent = []
    monkeypatch.setattr(bridge, "_send", sent.append)
    server = Server({"success": True})

    asyncio.run(bridge.handle(server, {"jsonrpc": "2.0", "method": "ping"}))
    asyncio.run(bridge.handle(server, {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": "health_check", "arguments": {}},
    }))

    assert server.calls == [("health_check", {})]
    assert sent == []
