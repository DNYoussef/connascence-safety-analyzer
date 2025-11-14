"""
SARIF 2.1.0 Exporter for Clarity Linter

Exports clarity violations in SARIF format for GitHub Code Scanning integration.

NASA Rule 4 Compliant: All functions under 60 lines
NASA Rule 5 Compliant: Input assertions
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from analyzer.clarity_linter.models import ClarityViolation


class SARIFExporter:
    """
    Exports clarity violations in SARIF 2.1.0 format.

    Compatible with GitHub Code Scanning and other SARIF consumers.

    NASA Rule 4 Compliant: All methods under 60 lines
    NASA Rule 5 Compliant: Input assertions
    """

    SARIF_VERSION = "2.1.0"
    SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"

    @staticmethod
    def export(
        violations: List[ClarityViolation],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Export violations as SARIF 2.1.0 document.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation assertions

        Args:
            violations: List of clarity violations
            config: Optional configuration for metadata

        Returns:
            SARIF document as dictionary
        """
        # NASA Rule 5: Input validation
        assert violations is not None, "violations cannot be None"
        assert isinstance(violations, list), "violations must be list"

        config = config or {}

        return {
            "$schema": SARIFExporter.SARIF_SCHEMA,
            "version": SARIFExporter.SARIF_VERSION,
            "runs": [
                SARIFExporter._create_run(violations, config)
            ]
        }

    @staticmethod
    def _create_run(
        violations: List[ClarityViolation],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create SARIF run object.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation

        Args:
            violations: List of violations
            config: Configuration dictionary

        Returns:
            SARIF run dictionary
        """
        # NASA Rule 5: Input validation
        assert isinstance(violations, list), "violations must be list"
        assert isinstance(config, dict), "config must be dictionary"

        return {
            "tool": SARIFExporter._create_tool(config),
            "results": [
                SARIFExporter._create_result(v) for v in violations
            ],
            "columnKind": "utf16CodeUnits"
        }

    @staticmethod
    def _create_tool(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create SARIF tool object.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation

        Args:
            config: Configuration dictionary

        Returns:
            SARIF tool dictionary
        """
        # NASA Rule 5: Input validation
        assert isinstance(config, dict), "config must be dictionary"

        metadata = config.get('metadata', {})

        return {
            "driver": {
                "name": metadata.get('name', 'Clarity Linter'),
                "version": metadata.get('version', '1.0.0'),
                "informationUri": "https://github.com/connascence/clarity-linter",
                "rules": SARIFExporter._create_rules(config)
            }
        }

    @staticmethod
    def _create_rules(config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create SARIF rules from configuration.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation

        Args:
            config: Configuration dictionary

        Returns:
            List of SARIF rule dictionaries
        """
        # NASA Rule 5: Input validation
        assert isinstance(config, dict), "config must be dictionary"

        rules_config = config.get('rules', {})
        sarif_rules = []

        for rule_id, rule_config in rules_config.items():
            sarif_rule = {
                "id": rule_id,
                "shortDescription": {
                    "text": rule_config.get('name', rule_id)
                },
                "fullDescription": {
                    "text": rule_config.get('description', '')
                },
                "defaultConfiguration": {
                    "level": SARIFExporter._map_severity(
                        rule_config.get('severity', 'medium')
                    )
                },
                "properties": {
                    "category": rule_config.get('category', 'clarity'),
                    "nasa_mapping": rule_config.get('nasa_mapping', ''),
                    "connascence_type": rule_config.get('connascence_type', '')
                }
            }
            sarif_rules.append(sarif_rule)

        return sarif_rules

    @staticmethod
    def _create_result(violation: ClarityViolation) -> Dict[str, Any]:
        """
        Create SARIF result from violation.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation

        Args:
            violation: Clarity violation to convert

        Returns:
            SARIF result dictionary
        """
        # NASA Rule 5: Input validation
        assert isinstance(violation, ClarityViolation), \
            "violation must be ClarityViolation"

        return {
            "ruleId": violation.rule_id,
            "level": SARIFExporter._map_severity(violation.severity),
            "message": {
                "text": violation.description
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": violation.file_path
                        },
                        "region": {
                            "startLine": violation.line_number,
                            "startColumn": violation.column or 1,
                            "endLine": violation.end_line or violation.line_number,
                            "snippet": {
                                "text": violation.code_snippet or ""
                            }
                        }
                    }
                }
            ],
            "fixes": [
                {
                    "description": {
                        "text": violation.recommendation
                    }
                }
            ] if violation.recommendation else [],
            "properties": violation.context
        }

    @staticmethod
    def _map_severity(severity: str) -> str:
        """
        Map clarity severity to SARIF level.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation

        Args:
            severity: Clarity severity level

        Returns:
            SARIF level string
        """
        # NASA Rule 5: Input validation
        assert isinstance(severity, str), "severity must be string"

        severity_map = {
            'critical': 'error',
            'high': 'error',
            'medium': 'warning',
            'low': 'note',
            'info': 'note'
        }

        return severity_map.get(severity.lower(), 'warning')

    @staticmethod
    def write_to_file(
        sarif_doc: Dict[str, Any],
        output_path: Path
    ) -> None:
        """
        Write SARIF document to file.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation assertions

        Args:
            sarif_doc: SARIF document dictionary
            output_path: Path to write SARIF file
        """
        # NASA Rule 5: Input validation
        assert sarif_doc is not None, "sarif_doc cannot be None"
        assert isinstance(sarif_doc, dict), "sarif_doc must be dictionary"
        assert output_path is not None, "output_path cannot be None"

        output_path = Path(output_path)

        # Create parent directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sarif_doc, f, indent=2)


__all__ = ['SARIFExporter']
