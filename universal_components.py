"""Universal component wiring for connascence."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from library.components.cognitive_architecture.integration.connascence_bridge import ConnascenceBridge
from library.components.cognitive_architecture.integration.telemetry_bridge import TelemetryBridge
from library.components.memory.memory_mcp_client import create_memory_mcp_client
from library.components.observability.tagging_protocol import TaggingProtocol, create_simple_tagger


def init_tagger() -> TaggingProtocol:
    return create_simple_tagger(agent_id="connascence", project_id="connascence")


def init_memory_client():
    endpoint = os.getenv("MEMORY_MCP_URL", "http://localhost:3000")
    return create_memory_mcp_client(
        project_id="connascence",
        project_name="connascence",
        agent_id="connascence",
        agent_category="analysis",
        capabilities=["analysis", "connascence", "quality"],
        mcp_endpoint=endpoint,
    )


def init_telemetry_bridge(loop_dir: Optional[str] = None) -> TelemetryBridge:
    resolved = Path(loop_dir) if loop_dir else Path(".loop")
    return TelemetryBridge(loop_dir=resolved)


def init_connascence_bridge() -> ConnascenceBridge:
    return ConnascenceBridge()
