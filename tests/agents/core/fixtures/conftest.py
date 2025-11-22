# SPDX-License-Identifier: MIT
"""
Shared fixtures for agent compliance testing.

These fixtures provide mock agent interfaces and test utilities
required by the architectural compliance test suite.
"""

import pytest
from typing import Any, Dict, List


@pytest.fixture
def mock_agent_interface():
    """Provide a mock agent interface for compliance testing."""
    return MockAgentInterface()


@pytest.fixture
def agent_capabilities():
    """Provide standard agent capabilities for testing."""
    return {
        "messaging": True,
        "embeddings": False,
        "reranking": False,
        "health_check": True,
        "task_processing": True,
    }


class MockAgentInterface:
    """Mock implementation of agent interface for testing."""

    def __init__(self):
        self.messages: List[Dict[str, Any]] = []
        self.tasks_processed: List[Any] = []

    def send_message(self, recipient: str, message: str, **kwargs) -> Dict[str, Any]:
        """Mock message sending."""
        msg = {"recipient": recipient, "message": message, "delivered": True, **kwargs}
        self.messages.append(msg)
        return msg

    def receive_message(self, timeout: float = None) -> List[Dict[str, Any]]:
        """Return pending messages."""
        return self.messages

    def process_task(self, task: Any, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Mock task processing."""
        self.tasks_processed.append(task)
        return {"task": task, "status": "completed", "context": context or {}}

    def health_check(self) -> Dict[str, Any]:
        """Return health status."""
        return {"status": "healthy", "components": {"messaging": "ok"}}

    def get_capabilities(self) -> Dict[str, Any]:
        """Return interface capabilities."""
        return {
            "interfaces": ["mock"],
            "formats": ["json"],
            "messaging": True,
            "task_processing": True,
        }


class MockTestAgent:
    """Reference implementation used by the compliance test suite."""

    def __init__(self):
        self.messages: List[Dict[str, Any]] = []
        self.tasks_processed: List[Any] = []
        self.capabilities: Dict[str, Any] = {
            "messaging": True,
            "embeddings": True,
            "reranking": True,
            "health_check": True,
            "task_processing": True,
            "synthetic": False,
        }
        self.status: Dict[str, Any] = {
            "state": "initialized",
            "last_broadcast": 0,
            "last_channel": None,
        }

    # Lifecycle operations
    def initialize(self) -> bool:
        self.status["state"] = "ready"
        return True

    def shutdown(self) -> bool:
        self.status["state"] = "shutdown"
        return True

    # Capability and health interfaces
    def health_check(self) -> Dict[str, Any]:
        return {
            "status": self.status.get("state", "ready"),
            "components": {"messaging": "ok", "tasks": len(self.tasks_processed)},
        }

    def get_capabilities(self) -> Dict[str, Any]:
        return dict(self.capabilities)

    def activate_latent_space(self, mode: str) -> bool:
        self.capabilities["synthetic"] = True
        self.status["latent_mode"] = mode
        return True

    # Task handling
    def can_handle_task(self, task: Dict[str, Any]) -> bool:
        return task.get("type") in {"echo", "synthetic"}

    def process_task(self, task: Dict[str, Any], context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        self.tasks_processed.append(task)
        if task.get("type") == "echo":
            return {
                "status": "completed",
                "task": task,
                "echo": task.get("payload"),
                "context": context or {},
            }
        return {"status": "unsupported", "task": task}

    def estimate_task_duration(self, task: Dict[str, Any]) -> float:
        return 0.1 if self.can_handle_task(task) else 1.0

    # Messaging helpers
    def send_message(self, recipient: str, message: str, **kwargs) -> Dict[str, Any]:
        envelope = {"recipient": recipient, "message": message, "delivered": True, **kwargs}
        self.messages.append(envelope)
        return envelope

    def receive_message(self, timeout: float | None = None) -> List[Dict[str, Any]]:
        return list(self.messages)

    def broadcast_message(self, recipients: List[str], message: str) -> List[Dict[str, Any]]:
        receipts = [self.send_message(r, message) for r in recipients]
        self.status["last_broadcast"] = len(recipients)
        return receipts

    def communicate(self, channel: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.status["last_channel"] = channel
        return {"channel": channel, "acknowledged": True, "payload": payload}

    # Generation, embeddings, and ranking
    def generate(self, prompt: str, tone: str = "neutral") -> str:
        return f"[{tone}] {prompt}"

    def get_embedding(self, text: str) -> List[int]:
        return [len(text), len(text.split())]

    def rerank(self, items: List[Any], query: str) -> List[Any]:
        return sorted(items, key=lambda item: str(item))

    def introspect(self) -> Dict[str, Any]:
        return {"status": self.status, "capabilities": self.capabilities}

    # Telemetry helpers used by integration tests
    def get_status(self) -> Dict[str, Any]:
        return dict(self.status)

    def get_performance_metrics(self) -> Dict[str, Any]:
        return {
            "messages": len(self.messages),
            "tasks_processed": len(self.tasks_processed),
            "latency_seconds": 0.01,
        }
