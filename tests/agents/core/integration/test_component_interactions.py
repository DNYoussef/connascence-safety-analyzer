"""Integration-style checks for the mock agent implementation."""

from __future__ import annotations

from tests.agents.core.fixtures.conftest import MockTestAgent


class TestComponentInteractions:
    """Ensure messaging and telemetry helpers behave consistently."""

    def setup_method(self) -> None:
        self.agent = MockTestAgent()

    def test_broadcast_updates_status(self) -> None:
        receipts = self.agent.broadcast_message(["alpha", "beta"], "ping")
        assert len(receipts) == 2
        assert self.agent.get_status()["last_broadcast"] == 2

    def test_communicate_tracks_channel(self) -> None:
        response = self.agent.communicate("slack", {"message": "hello"})
        assert response["acknowledged"]
        assert self.agent.get_status()["last_channel"] == "slack"

    def test_health_check_exposes_default_structure(self) -> None:
        health = self.agent.health_check()
        assert "status" in health
        assert isinstance(self.agent.get_performance_metrics(), dict)
