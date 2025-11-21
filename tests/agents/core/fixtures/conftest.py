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
