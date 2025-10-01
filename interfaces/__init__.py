# SPDX-License-Identifier: MIT
"""
Unified Interface Architecture for Connascence Safety Analyzer

This module consolidates all user interface implementations:
- CLI (Command Line Interface)
- Web Dashboard (Flask-based)
- VSCode Extension (TypeScript/JavaScript)
- Core shared components

Eliminates duplication across cli/, dashboard/, and vscode-extension/ directories.
"""

__version__ = "2.0.0"
__all__ = ["InterfaceManager", "SharedComponents"]


class InterfaceManager:
    """Central manager for all interface types."""

    def __init__(self):
        self.available_interfaces = {"cli": "interfaces.cli", "web": "interfaces.web", "vscode": "interfaces.vscode"}

    def get_interface(self, interface_type: str):
        """Get specific interface implementation."""
        if interface_type not in self.available_interfaces:
            raise ValueError(f"Unknown interface type: {interface_type}")

        module_path = self.available_interfaces[interface_type]
        # Dynamic import will be implemented in each interface module
        return module_path


class SharedComponents:
    """Registry of shared components across all interfaces."""

    DASHBOARD_ENGINE = "interfaces.core.dashboard_engine"
    CI_INTEGRATION = "interfaces.core.ci_integration"
    CHARTS = "interfaces.core.components.charts"
    METRICS = "interfaces.core.components.metrics"
    THEMING = "interfaces.core.components.theming"
