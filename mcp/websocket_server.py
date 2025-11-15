# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""WebSocket server wrapper for the enhanced MCP backend."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, Optional, Set

try:
    import websockets
    from websockets.server import Serve, WebSocketServerProtocol
except ImportError as exc:  # pragma: no cover - surfaced during CLI invocation
    raise RuntimeError(
        "The 'websockets' package is required to start the MCP WebSocket server. "
        "Install it via 'pip install websockets' or run 'pip install -r requirements.txt'."
    ) from exc

from mcp.enhanced_server import create_enhanced_mcp_server, get_server_info

logger = logging.getLogger(__name__)


class MCPWebSocketServer:
    """Thin WebSocket layer that exposes the enhanced MCP server."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8765, config: Optional[Dict[str, Any]] = None):
        self.host = host
        self.port = port
        self.config = config or {}
        self._ws_server: Optional[Serve] = None
        self._clients: Set[WebSocketServerProtocol] = set()
        self._backend = create_enhanced_mcp_server(self.config)
        self._server_info = get_server_info()

    async def start(self) -> None:
        """Start accepting WebSocket connections."""

        async def handler(websocket: WebSocketServerProtocol):
            await self._handle_client(websocket)

        self._ws_server = await websockets.serve(handler, self.host, self.port, ping_interval=30, ping_timeout=30)
        logger.info("MCP WebSocket server listening on %s:%s", self.host, self.port)

    async def stop(self) -> None:
        """Stop the WebSocket server and disconnect clients."""
        if self._ws_server is not None:
            self._ws_server.close()
            await self._ws_server.wait_closed()
            self._ws_server = None

        await asyncio.gather(*(self._close_client(client) for client in list(self._clients)), return_exceptions=True)

    async def _close_client(self, websocket: WebSocketServerProtocol) -> None:
        try:
            await websocket.close()
        except Exception:  # pragma: no cover - best effort close
            pass

    async def _handle_client(self, websocket: WebSocketServerProtocol) -> None:
        self._clients.add(websocket)
        logger.debug("New MCP client connected (%s active)", len(self._clients))
        try:
            await websocket.send(
                json.dumps(
                    {
                        "type": "welcome",
                        "server": self._server_info,
                    }
                )
            )

            async for raw_message in websocket:
                await self._dispatch_message(websocket, raw_message)
        except websockets.ConnectionClosedOK:
            logger.debug("MCP client disconnected cleanly")
        except websockets.ConnectionClosedError as error:
            logger.warning("MCP client disconnected with error: %s", error)
        finally:
            self._clients.discard(websocket)
            logger.debug("MCP client disconnected (%s active)", len(self._clients))

    async def _dispatch_message(self, websocket: WebSocketServerProtocol, raw_message: str) -> None:
        try:
            message = json.loads(raw_message)
        except json.JSONDecodeError:
            await websocket.send(
                json.dumps({"type": "error", "error": "Invalid JSON payload", "requestId": None})
            )
            return

        message_type = message.get("type")
        request_id = message.get("requestId")

        if message_type == "register":
            await websocket.send(
                json.dumps(
                    {
                        "type": "registered",
                        "status": "ok",
                        "requestId": request_id,
                        "server": self._server_info,
                    }
                )
            )
            return

        if message_type in {"health", "health_check"}:
            health = await self._backend.health_check()
            status = "ok" if health.get("success") else "error"
            await websocket.send(
                json.dumps(
                    {
                        "type": "health",
                        "status": status,
                        "requestId": request_id,
                        "details": health,
                    }
                )
            )
            return

        if message_type == "analyze":
            file_path = message.get("filePath")
            if not file_path:
                await websocket.send(
                    json.dumps(
                        {
                            "type": "analysis_result",
                            "requestId": request_id,
                            "error": "Missing filePath for analysis",
                        }
                    )
                )
                return

            options = message.get("options") or {}
            result = await self._backend.analyze_file(file_path=file_path, **options)
            await websocket.send(
                json.dumps(
                    {
                        "type": "analysis_result",
                        "requestId": request_id,
                        "data": result,
                        "error": None if result.get("success") else result.get("error"),
                    }
                )
            )
            return

        if message_type == "ping":
            await websocket.send(json.dumps({"type": "pong", "requestId": request_id}))
            return

        await websocket.send(
            json.dumps(
                {
                    "type": "error",
                    "requestId": request_id,
                    "error": f"Unknown MCP message type: {message_type}",
                }
            )
        )


__all__ = ["MCPWebSocketServer"]

