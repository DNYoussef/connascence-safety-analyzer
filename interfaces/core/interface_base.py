# SPDX-License-Identifier: MIT
"""
Base Interface Class

Common functionality and patterns shared across all interface types.
Provides consistent API for CLI, Web, and VSCode interfaces.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any, Dict, Iterable, List, Sequence

# Import analyzer components
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from analyzer.core import ConnascenceAnalyzer


@dataclass
class InterfaceConfig:
    """Configuration for interface implementations."""

    interface_type: str
    theme: str = "default"
    verbose: bool = False
    output_format: str = "json"
    policy_preset: str = "service-defaults"
    enable_autofix: bool = True
    enable_ci_integration: bool = False


class InterfaceBase(ABC):
    """Base class for all interface implementations."""

    def __init__(self, config: InterfaceConfig):
        self.config = config
        self.analyzer = ConnascenceAnalyzer()
        self._setup_interface()

    def _setup_interface(self):
        """Initialize interface-specific setup."""
        pass

    @abstractmethod
    def display_results(self, analysis_result: Dict[str, Any]) -> None:
        """Display analysis results in interface-appropriate format."""
        pass

    @abstractmethod
    def handle_error(self, error: Exception) -> None:
        """Handle errors in interface-appropriate way."""
        pass

    def analyze_path(self, path: str, **kwargs) -> Dict[str, Any]:
        """Common analysis entry point for all interfaces."""
        try:
            return self.analyzer.analyze_path(path=path, policy=self.config.policy_preset, **kwargs)
        except Exception as e:
            self.handle_error(e)
            return {"success": False, "error": str(e), "violations": [], "summary": {"total_violations": 0}}

    def get_supported_formats(self) -> List[str]:
        """Get supported output formats for this interface."""
        return ["json", "sarif", "markdown", "text"]

    def format_summary(self, analysis_result: Dict[str, Any]) -> str:
        """Create a formatted summary appropriate for this interface."""
        if not analysis_result.get("success", True):
            return f"Analysis failed: {analysis_result.get('error', 'Unknown error')}"

        summary = analysis_result.get("summary", {})
        total = summary.get("total_violations", 0)
        critical = summary.get("critical_violations", 0)

        if total == 0:
            return "✅ No connascence violations found"
        elif critical > 0:
            return f"❌ {total} violations found ({critical} critical)"
        else:
            return f"⚠️  {total} violations found"

    # ------------------------------------------------------------------
    # Agent-style interaction helpers expected by compliance suites
    # ------------------------------------------------------------------
    def process_task(self, task: Any, *, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Process a unit of work and return a structured response."""

        return {
            "task": task,
            "context": context or {},
            "status": "not-implemented",
        }

    def can_handle_task(self, task_type: str, **metadata: Any) -> bool:
        """Report whether the interface can service a particular task type."""

        return False

    def estimate_task_duration(self, task: Any, *, complexity: str = "medium") -> float:
        """Provide a coarse estimate for how long a task might take."""

        complexity_map = {"low": 0.5, "medium": 1.0, "high": 2.0}
        return float(complexity_map.get(complexity, 1.0))

    def send_message(self, recipient: str, message: str, *, metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Send a message to a single recipient."""

        return {
            "recipient": recipient,
            "delivered": False,
            "metadata": metadata or {},
            "message": message,
        }

    def receive_message(self, *, timeout: float | None = None) -> List[Dict[str, Any]]:
        """Return a collection of pending messages."""

        return []

    def broadcast_message(
        self,
        recipients: Iterable[str],
        message: str,
        *,
        metadata: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        """Send a message to multiple recipients and collect delivery receipts."""

        return [
            {
                "recipient": recipient,
                "delivered": False,
                "metadata": metadata or {},
                "message": message,
            }
            for recipient in recipients
        ]

    def generate(self, prompt: str, *, parameters: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Synthesize content from a prompt using optional generation parameters."""

        return {
            "prompt": prompt,
            "parameters": parameters or {},
            "output": "",
            "metadata": {"status": "not-implemented"},
        }

    def get_embedding(self, text: str, *, model: str | None = None) -> List[float]:
        """Return a deterministic placeholder embedding vector."""

        return [0.0, 0.0, 0.0]

    def rerank(
        self,
        items: Sequence[Dict[str, Any]],
        query: str,
        *,
        model: str | None = None,
    ) -> Sequence[Dict[str, Any]]:
        """Return items unchanged to satisfy the reranking contract."""

        return items

    def introspect(self, *, detail_level: str = "basic") -> Dict[str, Any]:
        """Expose internal diagnostics for observability tooling."""

        return {
            "detail_level": detail_level,
            "status": "not-implemented",
        }

    def communicate(self, channel: str, payload: Dict[str, Any], *, expect_response: bool = True) -> Dict[str, Any]:
        """Simulate communication over an arbitrary channel."""

        return {
            "channel": channel,
            "payload": payload,
            "acknowledged": False,
            "expect_response": expect_response,
        }

    def activate_latent_space(self, *, seed: int | None = None) -> Dict[str, Any]:
        """Placeholder for latent-space activation hooks used in experiments."""

        return {
            "seed": seed,
            "activated": False,
        }

    def health_check(self) -> Dict[str, Any]:
        """Report interface health suitable for readiness probes."""

        return {
            "status": "unknown",
            "components": {},
        }

    def get_capabilities(self) -> Dict[str, Any]:
        """Return advertised capabilities for discovery tooling."""

        return {
            "interfaces": [self.config.interface_type],
            "formats": self.get_supported_formats(),
        }

    def get_status(self) -> Dict[str, Any]:
        """Provide the latest operational status."""

        return {
            "last_broadcast": 0,
            "last_channel": None,
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Return cached performance metrics for observability."""

        return {
            "latency_ms": 0.0,
            "throughput_per_min": 0,
        }

    def _load_theme(self, theme_name: str) -> Dict[str, Any]:
        """Load theme configuration."""
        themes = {
            "default": {
                "colors": {
                    "critical": "#d73a49",
                    "high": "#f66a0a",
                    "medium": "#dbab09",
                    "low": "#28a745",
                    "success": "#28a745",
                    "warning": "#f66a0a",
                    "error": "#d73a49",
                }
            },
            "dark": {
                "colors": {
                    "critical": "#ff6b6b",
                    "high": "#ffa500",
                    "medium": "#ffeb3b",
                    "low": "#4caf50",
                    "success": "#4caf50",
                    "warning": "#ffa500",
                    "error": "#ff6b6b",
                }
            },
        }
        return themes.get(theme_name, themes["default"])


class OutputFormatter:
    """Unified output formatting across interfaces."""

    @staticmethod
    def format_violation(violation: Dict[str, Any], interface_type: str) -> str:
        """Format a single violation for display."""
        severity = violation.get("severity", "medium")
        description = violation.get("description", "Unknown violation")
        file_path = violation.get("file_path", "")
        line_number = violation.get("line_number", 0)

        if interface_type == "cli":
            return f"[{severity.upper()}] {file_path}:{line_number} - {description}"
        elif interface_type == "web":
            return f'<div class="violation {severity}">{description}<br><small>{file_path}:{line_number}</small></div>'
        else:  # vscode or other
            return f"{severity}: {description} ({file_path}:{line_number})"

    @staticmethod
    def format_summary_table(summary: Dict[str, Any], interface_type: str) -> str:
        """Format summary statistics as table."""
        total = summary.get("total_violations", 0)
        critical = summary.get("critical_violations", 0)
        high = summary.get("high_violations", 0)
        medium = summary.get("medium_violations", 0)
        low = summary.get("low_violations", 0)

        if interface_type == "cli":
            return f"""
Summary:
  Total: {total}
  Critical: {critical}
  High: {high}
  Medium: {medium}
  Low: {low}
"""
        elif interface_type == "web":
            return f"""
<table class="summary-table">
  <tr><td>Total</td><td>{total}</td></tr>
  <tr><td>Critical</td><td class="critical">{critical}</td></tr>
  <tr><td>High</td><td class="high">{high}</td></tr>
  <tr><td>Medium</td><td class="medium">{medium}</td></tr>
  <tr><td>Low</td><td class="low">{low}</td></tr>
</table>
"""
        else:
            return f"Total: {total}, Critical: {critical}, High: {high}, Medium: {medium}, Low: {low}"
