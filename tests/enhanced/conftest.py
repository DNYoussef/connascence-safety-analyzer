# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
Enhanced Test Infrastructure Configuration
==========================================

Pytest configuration for enhanced integration tests with external service checks.

This conftest provides:
- Skip markers for tests requiring external services
- Helper functions to check service availability
- Fixtures for test environment configuration
- Custom pytest markers for enhanced test categorization
"""

import os
import socket
from typing import List, Optional

import pytest


# Service availability checkers
def is_service_available(host: str, port: int, timeout: float = 1.0) -> bool:
    """
    Check if a service is available at the specified host and port.

    Args:
        host: Service hostname or IP address
        port: Service port number
        timeout: Connection timeout in seconds

    Returns:
        True if service is reachable, False otherwise
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except (socket.error, socket.timeout):
        return False


def is_mcp_server_available() -> bool:
    """
    Check if MCP server is running.

    Default port: 3000
    Override with MCP_SERVER_HOST and MCP_SERVER_PORT environment variables.
    """
    host = os.environ.get("MCP_SERVER_HOST", "localhost")
    port = int(os.environ.get("MCP_SERVER_PORT", "3000"))
    return is_service_available(host, port)


def is_web_dashboard_available() -> bool:
    """
    Check if Web Dashboard is running.

    Default port: 3001
    Override with DASHBOARD_HOST and DASHBOARD_PORT environment variables.
    """
    host = os.environ.get("DASHBOARD_HOST", "localhost")
    port = int(os.environ.get("DASHBOARD_PORT", "3001"))
    return is_service_available(host, port)


def is_vscode_extension_enabled() -> bool:
    """
    Check if VSCode extension testing is enabled.

    Enable by setting VSCODE_EXTENSION_TEST=1 environment variable.
    """
    return os.environ.get("VSCODE_EXTENSION_TEST", "0") == "1"


def get_missing_services() -> List[str]:
    """
    Get list of missing external services.

    Returns:
        List of service names that are not available
    """
    missing = []

    if not is_mcp_server_available():
        missing.append("MCP Server (localhost:3000)")

    if not is_web_dashboard_available():
        missing.append("Web Dashboard (localhost:3001)")

    if not is_vscode_extension_enabled():
        missing.append("VSCode Extension (VSCODE_EXTENSION_TEST not set)")

    return missing


# Skip markers for external dependencies
requires_mcp_server = pytest.mark.skipif(
    not is_mcp_server_available(),
    reason="MCP server not available at localhost:3000 (set MCP_SERVER_HOST/PORT to override)"
)

requires_web_dashboard = pytest.mark.skipif(
    not is_web_dashboard_available(),
    reason="Web dashboard not available at localhost:3001 (set DASHBOARD_HOST/PORT to override)"
)

requires_vscode_extension = pytest.mark.skipif(
    not is_vscode_extension_enabled(),
    reason="VSCode extension testing not enabled (set VSCODE_EXTENSION_TEST=1)"
)


# Pytest configuration hooks
def pytest_configure(config):
    """
    Configure pytest with custom markers for enhanced tests.
    """
    # Register custom markers
    config.addinivalue_line(
        "markers",
        "mcp_server: marks tests requiring MCP server (deselect with '-m \"not mcp_server\"')"
    )
    config.addinivalue_line(
        "markers",
        "web_dashboard: marks tests requiring Web dashboard (deselect with '-m \"not web_dashboard\"')"
    )
    config.addinivalue_line(
        "markers",
        "vscode: marks tests requiring VSCode extension (deselect with '-m \"not vscode\"')"
    )
    config.addinivalue_line(
        "markers",
        "performance: marks performance benchmark tests"
    )
    config.addinivalue_line(
        "markers",
        "integration: marks integration tests with external services"
    )


def pytest_collection_modifyitems(config, items):
    """
    Automatically apply skip markers to tests based on external service availability.

    This function:
    1. Identifies tests requiring external services
    2. Applies appropriate skip markers if services are unavailable
    3. Marks tests by category (integration, performance, etc.)
    """
    for item in items:
        # Check test file name and apply skip markers
        if "mcp_server_integration" in item.nodeid:
            if not is_mcp_server_available():
                item.add_marker(requires_mcp_server)
            item.add_marker(pytest.mark.mcp_server)
            item.add_marker(pytest.mark.integration)

        if "web_dashboard_integration" in item.nodeid:
            if not is_web_dashboard_available():
                item.add_marker(requires_web_dashboard)
            item.add_marker(pytest.mark.web_dashboard)
            item.add_marker(pytest.mark.integration)

        if "vscode_integration" in item.nodeid:
            if not is_vscode_extension_enabled():
                item.add_marker(requires_vscode_extension)
            item.add_marker(pytest.mark.vscode)
            item.add_marker(pytest.mark.integration)

        if "performance_benchmarks" in item.nodeid:
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)


def pytest_report_header(config):
    """
    Add external service status to pytest report header.
    """
    services_status = []

    if is_mcp_server_available():
        services_status.append("MCP Server: AVAILABLE")
    else:
        services_status.append("MCP Server: NOT AVAILABLE (tests will be skipped)")

    if is_web_dashboard_available():
        services_status.append("Web Dashboard: AVAILABLE")
    else:
        services_status.append("Web Dashboard: NOT AVAILABLE (tests will be skipped)")

    if is_vscode_extension_enabled():
        services_status.append("VSCode Extension: ENABLED")
    else:
        services_status.append("VSCode Extension: NOT ENABLED (tests will be skipped)")

    return [
        "Enhanced Integration Test Configuration",
        "-" * 60,
        *services_status,
        "-" * 60,
        "To run with external services:",
        "  1. MCP Server: Start server on localhost:3000 (or set MCP_SERVER_HOST/PORT)",
        "  2. Web Dashboard: Start dashboard on localhost:3001 (or set DASHBOARD_HOST/PORT)",
        "  3. VSCode Extension: Set VSCODE_EXTENSION_TEST=1 environment variable",
        ""
    ]


# Fixtures for service configuration
@pytest.fixture
def mcp_server_config():
    """
    Fixture providing MCP server configuration.
    """
    return {
        "host": os.environ.get("MCP_SERVER_HOST", "localhost"),
        "port": int(os.environ.get("MCP_SERVER_PORT", "3000")),
        "timeout": 30.0,
        "available": is_mcp_server_available()
    }


@pytest.fixture
def web_dashboard_config():
    """
    Fixture providing Web Dashboard configuration.
    """
    return {
        "host": os.environ.get("DASHBOARD_HOST", "localhost"),
        "port": int(os.environ.get("DASHBOARD_PORT", "3001")),
        "timeout": 10.0,
        "available": is_web_dashboard_available()
    }


@pytest.fixture
def vscode_extension_config():
    """
    Fixture providing VSCode extension configuration.
    """
    return {
        "enabled": is_vscode_extension_enabled(),
        "test_workspace": os.environ.get("VSCODE_TEST_WORKSPACE", None)
    }


@pytest.fixture
def skip_if_services_unavailable():
    """
    Fixture to skip tests if any required external services are unavailable.

    Usage in test:
        def test_something(skip_if_services_unavailable):
            # Test will be skipped if services are down
            pass
    """
    missing = get_missing_services()
    if missing:
        pytest.skip(f"Required services unavailable: {', '.join(missing)}")


@pytest.fixture(scope="session")
def enhanced_test_environment_info():
    """
    Session-scoped fixture providing enhanced test environment information.
    """
    return {
        "mcp_server_available": is_mcp_server_available(),
        "web_dashboard_available": is_web_dashboard_available(),
        "vscode_extension_enabled": is_vscode_extension_enabled(),
        "missing_services": get_missing_services(),
        "environment_variables": {
            "MCP_SERVER_HOST": os.environ.get("MCP_SERVER_HOST", "localhost"),
            "MCP_SERVER_PORT": os.environ.get("MCP_SERVER_PORT", "3000"),
            "DASHBOARD_HOST": os.environ.get("DASHBOARD_HOST", "localhost"),
            "DASHBOARD_PORT": os.environ.get("DASHBOARD_PORT", "3001"),
            "VSCODE_EXTENSION_TEST": os.environ.get("VSCODE_EXTENSION_TEST", "0"),
            "VSCODE_TEST_WORKSPACE": os.environ.get("VSCODE_TEST_WORKSPACE", None),
        }
    }
