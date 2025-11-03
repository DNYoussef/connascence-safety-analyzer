"""Property-oriented checks for agent invariants."""

from __future__ import annotations

from tests.agents.core.fixtures.conftest import MockTestAgent


class TestAgentInvariants:
    """Validate basic invariants such as health and embeddings."""

    def setup_method(self) -> None:
        self.agent = MockTestAgent()

    def test_health_check_reports_ready_state(self) -> None:
        status = self.agent.health_check()
        assert status["status"] in {"ready", "initialized"}

    def test_embeddings_are_length_two(self) -> None:
        embedding = self.agent.get_embedding("example text")
        assert len(embedding) == 2

    def test_latent_space_activation_sets_capability(self) -> None:
        assert self.agent.activate_latent_space("synthetic")
        assert self.agent.get_capabilities()["synthetic"]
