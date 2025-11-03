"""High-level agent interface contract used in compliance tests."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Sequence


class AgentInterface(ABC):
    """Abstract interface that all test agents are expected to implement."""

    def __init__(self) -> None:
        self._capabilities: Dict[str, Any] = {
            "messaging": True,
            "embeddings": True,
            "reranking": True,
            "generation": True,
        }
        self._status: Dict[str, Any] = {"state": "initialized", "active_sessions": 0}
        self._performance: Dict[str, float] = {"avg_latency_ms": 0.0, "tasks_completed": 0.0}

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------
    def initialize(self, **kwargs: Any) -> None:
        """Prepare the agent for use."""
        self._status.update({"state": "ready", "initialization_args": kwargs})

    def shutdown(self) -> None:
        """Tear down resources used by the agent."""
        self._status["state"] = "stopped"

    def health_check(self) -> Dict[str, Any]:
        """Return a lightweight health indicator."""
        return {"status": self._status.get("state", "unknown"), "details": {}}

    # ------------------------------------------------------------------
    # Task processing contract
    # ------------------------------------------------------------------
    @abstractmethod
    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task and return structured results."""

    def can_handle_task(self, task: Dict[str, Any]) -> bool:
        """Determine whether the agent can handle the supplied task."""
        return bool(task)

    def estimate_task_duration(self, task: Dict[str, Any]) -> float:
        """Return a naive duration estimate in seconds for the task."""
        complexity = task.get("complexity", 1)
        return float(complexity)

    # ------------------------------------------------------------------
    # Messaging helpers
    # ------------------------------------------------------------------
    def send_message(self, recipient: str, message: str) -> Dict[str, Any]:
        """Send a message to a single recipient."""
        return {"recipient": recipient, "message": message, "status": "sent"}

    def receive_message(self) -> Dict[str, Any]:
        """Receive the next available message."""
        return {"sender": "system", "message": "no-op"}

    def broadcast_message(self, recipients: Iterable[str], message: str) -> List[Dict[str, Any]]:
        """Broadcast a message to multiple recipients."""
        return [self.send_message(recipient, message) for recipient in recipients]

    # ------------------------------------------------------------------
    # Generative capabilities
    # ------------------------------------------------------------------
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a synthetic response to the provided prompt."""
        tone = kwargs.get("tone", "neutral")
        return f"[{tone}] {prompt.strip()}"

    def get_embedding(self, text: str) -> List[float]:
        """Return a simple deterministic embedding for the supplied text."""
        return [float(len(text)), float(len(text.split()))]

    def rerank(self, query: str, documents: Sequence[str]) -> List[int]:
        """Return an ascending index ranking for the provided documents."""
        return list(range(len(documents)))

    def introspect(self) -> Dict[str, Any]:
        """Return introspection data useful for debugging."""
        return {"status": self._status.copy(), "capabilities": self._capabilities.copy()}

    def communicate(self, channel: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send structured data to an integration channel."""
        message = payload.get("message", "")
        return {"channel": channel, "acknowledged": bool(message)}

    def activate_latent_space(self, feature: str) -> bool:
        """Toggle a synthetic latent feature for testing purposes."""
        self._capabilities[feature] = True
        return True

    # ------------------------------------------------------------------
    # Observability helpers
    # ------------------------------------------------------------------
    def get_capabilities(self) -> Dict[str, Any]:
        """Expose advertised agent capabilities."""
        return self._capabilities.copy()

    def get_status(self) -> Dict[str, Any]:
        """Return the current agent status payload."""
        return self._status.copy()

    def get_performance_metrics(self) -> Dict[str, float]:
        """Return synthetic performance metrics."""
        return self._performance.copy()
