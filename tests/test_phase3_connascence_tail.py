import ast
import os
import subprocess
import sys
import tomllib
from pathlib import Path

from flask import Flask
from flask_socketio import SocketIO

from analyzer.reporting.json import JSONReporter
from analyzer.reporting.sarif import SARIFReporter
from interfaces.web.server_flask import LocalDashboard


def test_ast_cache_import_is_lazy_and_has_no_cwd_side_effect(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    code = (
        "from pathlib import Path\n"
        "import analyzer.caching.ast_cache as cache_module\n"
        "print(Path('.connascence_cache').exists())\n"
        "print(cache_module._default_ast_cache is None)\n"
    )

    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(repo_root)},
        text=True,
        capture_output=True,
        check=True,
    )

    assert result.stdout.splitlines() == ["False", "True"]


def test_ast_cache_lazy_proxy_creates_cache_only_on_use(tmp_path, monkeypatch):
    import analyzer.caching.ast_cache as cache_module

    cache_module._default_ast_cache = None
    monkeypatch.chdir(tmp_path)

    assert not (tmp_path / ".connascence_cache").exists()

    stats = cache_module.ast_cache.get_cache_statistics()

    assert stats["entries_count"] == 0
    assert (tmp_path / ".connascence_cache").is_dir()


def test_dashboard_static_route_uses_configured_module_static_dir(tmp_path, monkeypatch):
    module_static = tmp_path / "module_static"
    module_static.mkdir()
    (module_static / "probe.txt").write_text("from module static", encoding="utf-8")

    cwd_static = tmp_path / "cwd" / "static"
    cwd_static.mkdir(parents=True)
    (cwd_static / "probe.txt").write_text("from cwd static", encoding="utf-8")
    monkeypatch.chdir(cwd_static.parent)

    dashboard = object.__new__(LocalDashboard)
    dashboard.port = 8080
    dashboard.app = Flask(__name__, static_folder=str(module_static))
    dashboard.bind_host = "127.0.0.1"
    dashboard.auth_token = None
    dashboard.scan_results = {}
    dashboard.current_project = None
    dashboard.static_dir = module_static
    dashboard.socketio = SocketIO(dashboard.app, cors_allowed_origins=[])
    dashboard._setup_routes()

    response = dashboard.app.test_client().get("/static/probe.txt")

    assert response.status_code == 200
    assert response.get_data(as_text=True) == "from module static"


def test_reporter_and_package_versions_match_runtime():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["project"]["version"] == "2.0.0"
    assert JSONReporter().tool_version == "2.0.0"
    assert SARIFReporter().tool_version == "2.0.0"


def test_run_unified_analysis_has_no_dead_time_expression():
    source = Path("analyzer/core.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name != "_run_unified_analysis":
            continue
        expression_calls = [
            expr.value
            for expr in ast.walk(node)
            if isinstance(expr, ast.Expr) and isinstance(expr.value, ast.Call)
        ]
        assert not any(
            isinstance(call.func, ast.Attribute)
            and call.func.attr == "time"
            and isinstance(call.func.value, ast.Name)
            and call.func.value.id == "time"
            for call in expression_calls
        )
        return

    raise AssertionError("_run_unified_analysis not found")
