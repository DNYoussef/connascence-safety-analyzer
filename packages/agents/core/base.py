"""Concrete base agent providing ready-to-use defaults."""

from __future__ import annotations

from typing import Any, Dict

from .base_agent_template import BaseAgentTemplate


class BaseAgent(BaseAgentTemplate):
    """Simple agent implementation suited for unit tests."""

    def __init__(self) -> None:
        super().__init__()
        self._metadata: Dict[str, Any] = {"name": "BaseAgent", "version": "1.0"}

    def get_metadata(self) -> Dict[str, Any]:
        """Expose metadata describing the agent implementation."""
        return self._metadata.copy()
