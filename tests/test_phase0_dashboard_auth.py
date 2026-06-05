from flask import Flask
from flask_socketio import SocketIO
from typing import Optional

from interfaces.web.server_flask import LocalDashboard


class _PolicyManager:
    def list_presets(self):
        return {"service-defaults": {}}


def _dashboard_for_auth(bind_host: str, token: Optional[str]) -> LocalDashboard:
    dashboard = object.__new__(LocalDashboard)
    dashboard.port = 8080
    dashboard.app = Flask(__name__)
    dashboard.bind_host = bind_host
    dashboard.auth_token = token
    dashboard.scan_results = {}
    dashboard.current_project = None
    dashboard.policy_manager = _PolicyManager()
    dashboard.socketio = SocketIO(dashboard.app, cors_allowed_origins=[])
    dashboard._setup_routes()
    return dashboard


def test_dashboard_requires_token_when_bound_outside_loopback():
    dashboard = _dashboard_for_auth("0.0.0.0", None)
    response = dashboard.app.test_client().get("/api/policy/presets")

    assert response.status_code == 503
    assert response.json == {
        "error": "CONNASCENCE_DASHBOARD_TOKEN is required when binding outside loopback"
    }


def test_dashboard_allows_loopback_bind_without_token():
    dashboard = _dashboard_for_auth("127.0.0.1", None)
    response = dashboard.app.test_client().get("/api/policy/presets")

    assert response.status_code == 200
    assert response.json == {"service-defaults": {}}


def test_dashboard_accepts_token_on_non_loopback_bind():
    dashboard = _dashboard_for_auth("0.0.0.0", "secret")
    response = dashboard.app.test_client().get(
        "/api/policy/presets",
        headers={"Authorization": "Bearer secret"},
    )

    assert response.status_code == 200
    assert response.json == {"service-defaults": {}}
