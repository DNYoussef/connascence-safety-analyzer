"""Base template implementing shared agent behaviours."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence

from .agent_interface import AgentInterface


class BaseAgentTemplate(AgentInterface):
    """Convenience mixin that provides pragmatic default behaviours."""

    def __init__(self) -> None:
        super().__init__()
        self._inbox: List[Dict[str, Any]] = []

    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Return a simple echo-style task response."""
        result = {
            "task": task,
            "status": "completed",
            "output": task.get("payload", ""),
        }
        self._performance["tasks_completed"] += 1
        return result

    def send_message(self, recipient: str, message: str) -> Dict[str, Any]:
        payload = super().send_message(recipient, message)
        self._performance["avg_latency_ms"] = 1.0
        return payload

    def receive_message(self) -> Dict[str, Any]:
        if self._inbox:
            return self._inbox.pop(0)
        return super().receive_message()

    def broadcast_message(self, recipients: Iterable[str], message: str) -> List[Dict[str, Any]]:
        deliveries = super().broadcast_message(recipients, message)
        self._performance["tasks_completed"] += len(deliveries)
        return deliveries

    def rerank(self, query: str, documents: Sequence[str]) -> List[int]:
        # Reverse sort by length to demonstrate deterministic behaviour.
        return sorted(range(len(documents)), key=lambda idx: len(documents[idx]))

    def communicate(self, channel: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = super().communicate(channel, payload)
        if response["acknowledged"]:
            self._status["last_channel"] = channel
        return response
