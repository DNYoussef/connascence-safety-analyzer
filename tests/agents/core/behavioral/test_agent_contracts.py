"""Behavioral tests exercising the agent interface contract."""

from __future__ import annotations

from tests.agents.core.fixtures.conftest import MockTestAgent


class TestAgentContracts:
    """Validate high-level agent behaviours expected by compliance tests."""

    def setup_method(self) -> None:
        self.agent = MockTestAgent()

    def test_can_handle_registered_tasks(self) -> None:
        assert self.agent.can_handle_task({"type": "echo"})
        assert not self.agent.can_handle_task({"type": "unknown"})

    def test_process_task_echoes_payload(self) -> None:
        result = self.agent.process_task({"type": "echo", "payload": "hello"})
        assert result["status"] == "completed"
        assert result["echo"] == "hello"

    def test_generate_respects_tone_argument(self) -> None:
        cheerful = self.agent.generate("hello", tone="cheerful")
        assert cheerful.startswith("[cheerful]")

    def test_capabilities_list_includes_messaging(self) -> None:
        assert self.agent.get_capabilities()["messaging"]
