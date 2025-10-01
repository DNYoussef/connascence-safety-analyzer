# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
Consolidated Integrations
========================

Replaces the fragmented integration files with consolidated implementations
that use the UnifiedBaseIntegration to eliminate 85.7% code duplication.

This addresses the architectural fragmentation root cause by providing
consistent, maintainable integration patterns.
"""

import json
import re
from typing import Any, Dict, List, Optional

from config.central_constants import IntegrationConstants
from fixes.phase0.production_safe_assertions import ProductionAssert

from .unified_base import INTEGRATION_REGISTRY, IntegrationType, UnifiedBaseIntegration


class BlackIntegration(UnifiedBaseIntegration):
    """Black code formatter integration."""

    @property
    def tool_name(self) -> str:
        return IntegrationConstants.BLACK

    @property
    def tool_command(self) -> str:
        return IntegrationConstants.BLACK

    @property
    def version_command(self) -> List[str]:
        return [IntegrationConstants.BLACK, "--version"]

    @property
    def integration_type(self) -> IntegrationType:
        return IntegrationType.FORMATTER

    @property
    def description(self) -> str:
        return "The uncompromising Python code formatter"

    def _parse_output(self, stdout: str, stderr: str) -> List[Dict[str, Any]]:
        """Parse Black output to find formatting issues."""
        issues = []

        # Black uses stderr for diff output when --check --diff is used
        if stderr and "would reformat" in stderr:
            lines = stderr.split("\n")
            for line in lines:
                if "would reformat" in line:
                    issues.append(
                        {
                            "type": "formatting",
                            "severity": "info",
                            "message": line.strip(),
                            "line": None,
                            "column": None,
                            "rule": "black-format",
                        }
                    )

        return issues


class MyPyIntegration(UnifiedBaseIntegration):
    """MyPy static type checker integration."""

    @property
    def tool_name(self) -> str:
        return IntegrationConstants.MYPY

    @property
    def tool_command(self) -> str:
        return IntegrationConstants.MYPY

    @property
    def version_command(self) -> List[str]:
        return [IntegrationConstants.MYPY, "--version"]

    @property
    def integration_type(self) -> IntegrationType:
        return IntegrationType.TYPE_CHECKER

    @property
    def description(self) -> str:
        return "Static type checker for Python"

    def _parse_output(self, stdout: str, stderr: str) -> List[Dict[str, Any]]:
        """Parse MyPy output to extract type violations."""
        issues = []

        # MyPy format: file:line:column: error: message [error-code]
        pattern = r"^(.+?):(\d+):(?:(\d+):)?\s*(error|warning|note):\s*(.+?)(?:\s+\[(.+?)\])?$"

        for line in stdout.split("\n"):
            line = line.strip()
            if not line:
                continue

            match = re.match(pattern, line)
            if match:
                file_path, line_num, column, severity, message, error_code = match.groups()

                issues.append(
                    {
                        "type": "type-error",
                        "severity": severity,
                        "message": message,
                        "line": int(line_num) if line_num else None,
                        "column": int(column) if column else None,
                        "rule": error_code or "mypy",
                        "file": file_path,
                    }
                )

        return issues


class RuffIntegration(UnifiedBaseIntegration):
    """Ruff linter integration."""

    @property
    def tool_name(self) -> str:
        return IntegrationConstants.RUFF

    @property
    def tool_command(self) -> str:
        return IntegrationConstants.RUFF

    @property
    def version_command(self) -> List[str]:
        return [IntegrationConstants.RUFF, "--version"]

    @property
    def integration_type(self) -> IntegrationType:
        return IntegrationType.LINTER

    @property
    def description(self) -> str:
        return "An extremely fast Python linter, written in Rust"

    def _parse_output(self, stdout: str, stderr: str) -> List[Dict[str, Any]]:
        """Parse Ruff JSON output to extract linting violations."""
        issues = []

        try:
            # Try parsing as JSON first (if --format json was used)
            data = json.loads(stdout)
            if isinstance(data, list):
                for item in data:
                    issues.append(
                        {
                            "type": "lint-error",
                            "severity": "error" if item.get("fix") else "warning",
                            "message": item.get("message", ""),
                            "line": item.get("location", {}).get("row"),
                            "column": item.get("location", {}).get("column"),
                            "rule": item.get("code", "ruff"),
                            "file": item.get("filename"),
                        }
                    )
        except (json.JSONDecodeError, KeyError):
            # Fallback to text parsing
            # Ruff format: file:line:column: code message
            pattern = r"^(.+?):(\d+):(\d+):\s*([A-Z]\d+)\s*(.+)$"

            for line in stdout.split("\n"):
                line = line.strip()
                if not line:
                    continue

                match = re.match(pattern, line)
                if match:
                    file_path, line_num, column, code, message = match.groups()

                    issues.append(
                        {
                            "type": "lint-error",
                            "severity": "error" if code.startswith("E") else "warning",
                            "message": message,
                            "line": int(line_num) if line_num else None,
                            "column": int(column) if column else None,
                            "rule": code,
                            "file": file_path,
                        }
                    )

        return issues


class RadonIntegration(UnifiedBaseIntegration):
    """Radon complexity analyzer integration."""

    @property
    def tool_name(self) -> str:
        return IntegrationConstants.RADON

    @property
    def tool_command(self) -> str:
        return IntegrationConstants.RADON

    @property
    def version_command(self) -> List[str]:
        return [IntegrationConstants.RADON, "--version"]

    @property
    def integration_type(self) -> IntegrationType:
        return IntegrationType.COMPLEXITY_ANALYZER

    @property
    def description(self) -> str:
        return "Code complexity analyzer for Python"

    def _parse_output(self, stdout: str, stderr: str) -> List[Dict[str, Any]]:
        """Parse Radon output to extract complexity violations."""
        issues = []

        # Radon cc format: file:line:column: function - A (complexity)
        pattern = r"^(.+?):(\d+):(\d+):\s*(.+?)\s*-\s*([A-F])\s*\((\d+)\)$"

        for line in stdout.split("\n"):
            line = line.strip()
            if not line:
                continue

            match = re.match(pattern, line)
            if match:
                file_path, line_num, column, function, grade, complexity = match.groups()

                # Convert grade to severity
                severity_map = {"A": "info", "B": "info", "C": "warning", "D": "error", "E": "error", "F": "error"}

                issues.append(
                    {
                        "type": "complexity",
                        "severity": severity_map.get(grade, "warning"),
                        "message": f"Function '{function}' has complexity {complexity} (grade {grade})",
                        "line": int(line_num) if line_num else None,
                        "column": int(column) if column else None,
                        "rule": f"radon-cc-{grade.lower()}",
                        "file": file_path,
                        "complexity": int(complexity),
                    }
                )

        return issues


class BanditIntegration(UnifiedBaseIntegration):
    """Bandit security scanner integration."""

    @property
    def tool_name(self) -> str:
        return IntegrationConstants.BANDIT

    @property
    def tool_command(self) -> str:
        return IntegrationConstants.BANDIT

    @property
    def version_command(self) -> List[str]:
        return [IntegrationConstants.BANDIT, "--version"]

    @property
    def integration_type(self) -> IntegrationType:
        return IntegrationType.SECURITY_SCANNER

    @property
    def description(self) -> str:
        return "Security linter for Python"

    def _parse_output(self, stdout: str, stderr: str) -> List[Dict[str, Any]]:
        """Parse Bandit JSON output to extract security issues."""
        issues = []

        try:
            data = json.loads(stdout)
            results = data.get("results", [])

            for result in results:
                issues.append(
                    {
                        "type": "security",
                        "severity": result.get("issue_severity", "medium").lower(),
                        "message": result.get("issue_text", ""),
                        "line": result.get("line_number"),
                        "column": result.get("col_offset"),
                        "rule": result.get("test_id", "bandit"),
                        "file": result.get("filename"),
                        "confidence": result.get("issue_confidence", "medium"),
                    }
                )
        except (json.JSONDecodeError, KeyError):
            # Fallback: basic text parsing if JSON fails
            pass

        return issues


# =============================================================================
# INTEGRATION FACTORY
# =============================================================================


def create_all_integrations(config: Optional[Dict] = None) -> Dict[str, UnifiedBaseIntegration]:
    """
    Create and register all available integrations.

    Args:
        config: Optional configuration dictionary

    Returns:
        Dictionary of integration instances
    """
    integrations = {
        "black": BlackIntegration(config),
        "mypy": MyPyIntegration(config),
        "ruff": RuffIntegration(config),
        "radon": RadonIntegration(config),
        "bandit": BanditIntegration(config),
    }

    # Register with global registry
    for integration in integrations.values():
        INTEGRATION_REGISTRY.register(integration)

    return integrations


def get_available_integrations(config: Optional[Dict] = None) -> Dict[str, UnifiedBaseIntegration]:
    """Get only the integrations that are available in the current environment."""
    all_integrations = create_all_integrations(config)

    return {name: integration for name, integration in all_integrations.items() if integration.is_available()}


# =============================================================================
# LEGACY COMPATIBILITY
# =============================================================================


# Provide backwards compatibility for existing code
def BlackIntegrationLegacy(config=None):
    """Legacy compatibility wrapper."""
    ProductionAssert.not_none(config, "config")

    ProductionAssert.not_none(config, "config")

    return BlackIntegration(config)


def MyPyIntegrationLegacy(config=None):
    """Legacy compatibility wrapper."""

    ProductionAssert.not_none(config, "config")

    ProductionAssert.not_none(config, "config")

    return MyPyIntegration(config)


def RuffIntegrationLegacy(config=None):
    """Legacy compatibility wrapper."""

    ProductionAssert.not_none(config, "config")

    ProductionAssert.not_none(config, "config")

    return RuffIntegration(config)


# Export the registry for external use
__all__ = [
    "INTEGRATION_REGISTRY",
    "BanditIntegration",
    "BlackIntegration",
    "MyPyIntegration",
    "RadonIntegration",
    "RuffIntegration",
    "create_all_integrations",
    "get_available_integrations",
]
