"""Fixtures and helper classes for agent compliance tests."""

from __future__ import annotations

from typing import Dict, Iterable, List

import pytest

from packages.agents.core import BaseAgent


class MockTestAgent(BaseAgent):
    """Minimal agent implementation used to exercise the shared interface."""

    def __init__(self) -> None:
        super().__init__()
        self._inbox: List[Dict[str, Any]] = []
        self.initialize()

    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Extend the base implementation with echo semantics."""
        result = super().process_task(task)
        result["echo"] = task.get("payload", "")
        return result

    def can_handle_task(self, task: Dict[str, Any]) -> bool:
        task_type = task.get("type", "")
        return task_type in {"echo", "analysis"}

    def receive_message(self) -> Dict[str, Any]:
        if self._inbox:
            return self._inbox.pop(0)
        return super().receive_message()

    def queue_message(self, sender: str, message: str) -> None:
        self._inbox.append({"sender": sender, "message": message})

    def broadcast_message(self, recipients: Iterable[str], message: str) -> List[Dict[str, Any]]:
        deliveries = super().broadcast_message(recipients, message)
        self._status["last_broadcast"] = len(deliveries)
        return deliveries


@pytest.fixture
def mock_agent() -> MockTestAgent:
    """Provide a ready-to-use mock agent for tests."""
    return MockTestAgent()
