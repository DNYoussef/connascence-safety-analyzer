"""
SARIF (Static Analysis Results Interchange Format) exporter.

Converts connascence violations to SARIF v2.1.0 format for CI/CD integration,
including GitHub Code Scanning, VS Code, Azure DevOps, and GitLab.

NASA Rule 4: All functions under 60 lines
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from .sarif_rules import get_connascence_rules, get_severity_mapping


class SARIFExporter:
    """
    Export connascence violations to SARIF format.

    SARIF enables integration with GitHub Code Scanning, VS Code,
    and other modern code quality tools.
    """

    def __init__(self, version: str = "1.0.0"):
        """
        Initialize SARIF exporter.

        Args:
            version: Analyzer version string
        """
        self.version = version
        self.severity_map = get_severity_mapping()

    def generate_sarif(
        self, violations: List[Dict], source_root: Optional[str] = None
    ) -> Dict:
        """
        Generate SARIF report from connascence violations.

        Args:
            violations: List of violation dicts from analyzer
            source_root: Optional source root path for relative URIs

        Returns:
            SARIF v2.1.0 compliant dict

        NASA Rule 4: Function under 60 lines (30 LOC)
        """
        return {
            "version": "2.1.0",
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "runs": [
                {
                    "tool": self._create_tool_metadata(),
                    "results": self._create_results(violations, source_root),
                }
            ],
        }

    def _create_tool_metadata(self) -> Dict:
        """
        Create SARIF tool metadata section.

        Returns:
            Tool metadata dict with driver and rules

        NASA Rule 4: Function under 60 lines (18 LOC)
        """
        return {
            "driver": {
                "name": "Connascence Analyzer",
                "version": self.version,
                "informationUri": "https://github.com/connascence/connascence.io",
                "shortDescription": {
                    "text": "Static analysis tool for detecting connascence violations"
                },
                "rules": get_connascence_rules(),
            }
        }

    def _create_results(
        self, violations: List[Dict], source_root: Optional[str]
    ) -> List[Dict]:
        """
        Convert violations to SARIF results.

        Args:
            violations: List of violation dicts
            source_root: Optional source root for relative paths

        Returns:
            List of SARIF result objects

        NASA Rule 4: Function under 60 lines (20 LOC)
        """
        results = []
        for violation in violations:
            result = self._create_result(violation, source_root)
            if result:
                results.append(result)
        return results

    def _create_result(
        self, violation: Dict, source_root: Optional[str]
    ) -> Optional[Dict]:
        """
        Create single SARIF result from violation.

        Args:
            violation: Violation dict from analyzer
            source_root: Optional source root for relative paths

        Returns:
            SARIF result object or None if invalid

        NASA Rule 4: Function under 60 lines (40 LOC)
        """
        # Extract violation metadata
        conn_type = violation.get("type", "Unknown")
        file_path = violation.get("file", "")
        line = violation.get("line", 1)
        message = violation.get("message", f"Connascence violation: {conn_type}")

        # Map to SARIF severity
        level = self.severity_map.get(conn_type, "warning")

        # Create relative URI if source root provided
        uri = self._create_relative_uri(file_path, source_root)

        return {
            "ruleId": conn_type,
            "level": level,
            "message": {"text": message},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": uri},
                        "region": {"startLine": line},
                    }
                }
            ],
        }

    def _create_relative_uri(
        self, file_path: str, source_root: Optional[str]
    ) -> str:
        """
        Create relative URI for SARIF artifact location.

        Args:
            file_path: Absolute or relative file path
            source_root: Optional source root directory

        Returns:
            Relative URI string

        NASA Rule 4: Function under 60 lines (20 LOC)
        """
        if not file_path:
            return "unknown"

        if source_root:
            try:
                path_obj = Path(file_path)
                root_obj = Path(source_root)
                return str(path_obj.relative_to(root_obj))
            except (ValueError, Exception):
                # Fall back to original path if relative fails
                pass

        return str(file_path)
