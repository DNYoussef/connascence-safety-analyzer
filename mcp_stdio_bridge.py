# SPDX-License-Identifier: MIT
"""Minimal MCP stdio bridge for the connascence analyzer.

The repo's mcp/cli.py run_stdio_server speaks a homemade JSON protocol
(prints a server_ready banner, expects {"tool": ...} lines). Claude Code
speaks real MCP JSON-RPC 2.0 over stdio, so it never connects.

This bridge implements just enough of the MCP protocol (initialize,
tools/list, tools/call, ping) as newline-delimited JSON-RPC, and forwards
calls to the existing EnhancedConnascenceMCPServer. No external SDK, so no
collision with the repo's own top-level package named `mcp`.

ponytail: hand-rolled JSON-RPC, ~80 lines. Swap to the official `mcp` SDK
only if/when the repo package is renamed off `mcp`.
"""

import asyncio
from contextlib import redirect_stdout, suppress
from dataclasses import asdict, is_dataclass
import json
import sys

# enhanced_server emits warnings on import; keep them off stdout (stdout is
# reserved for JSON-RPC only).
_real_stdout = sys.stdout
with redirect_stdout(sys.stderr):
    from mcp.enhanced_server import create_enhanced_mcp_server, get_server_info

PROTOCOL_VERSION = "2024-11-05"


def _to_input_schema(params):
    """Convert the repo's {name: {type, description, default?}} into JSON Schema."""
    props = dict(params or {})
    required = [k for k, v in props.items() if "default" not in v and not v.get("optional")]
    return {"type": "object", "properties": props, "required": required}


def _send(msg):
    _real_stdout.write(json.dumps(msg) + "\n")
    _real_stdout.flush()


def _result(req_id, result):
    _send({"jsonrpc": "2.0", "id": req_id, "result": result})


def _error(req_id, code, message):
    _send({"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}})


def _jsonable(value):
    """Normalize server result objects before serializing an MCP response."""
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return to_dict()
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    return value


async def handle(server, msg):
    method = msg.get("method")
    req_id = msg.get("id")
    is_notification = "id" not in msg

    # JSON-RPC notifications never receive a response. tools/call still runs
    # for its side effect, then discards the result below.
    if is_notification and method != "tools/call":
        return

    if method == "initialize":
        info = get_server_info()
        _result(req_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": info.get("name", "connascence-analyzer"),
                           "version": info.get("version", "2.0.0")},
        })
    elif method == "notifications/initialized":
        pass  # notification, no response
    elif method == "ping":
        _result(req_id, {})
    elif method == "tools/list":
        tools = [{
            "name": t["name"],
            "description": t.get("description", ""),
            "inputSchema": _to_input_schema(t.get("parameters")),
        } for t in server.list_tools()]
        _result(req_id, {"tools": tools})
    elif method == "tools/call":
        params = msg.get("params") or {}
        name = params.get("name")
        arguments = params.get("arguments") or {}
        try:
            with redirect_stdout(sys.stderr):
                out = await server.call_tool(name, dict(arguments))
            out = _jsonable(out)
            is_error = isinstance(out, dict) and out.get("success") is False
            if not is_notification:
                _result(req_id, {
                    "content": [{"type": "text", "text": json.dumps(out, indent=2, default=str)}],
                    "isError": bool(is_error),
                })
        except Exception as e:  # every error path is a code path
            if not is_notification:
                _error(req_id, -32603, f"tool execution failed: {e}")
    else:
        _error(req_id, -32601, f"method not found: {method}")


async def main():
    server = create_enhanced_mcp_server(None)
    loop = asyncio.get_event_loop()
    while True:
        line = await loop.run_in_executor(None, sys.stdin.readline)
        if not line:
            break  # EOF -> client closed stdin
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            _error(None, -32700, "parse error")
            continue
        await handle(server, msg)


if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        asyncio.run(main())
