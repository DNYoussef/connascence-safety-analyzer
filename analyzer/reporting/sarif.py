# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

"""
SARIF 2.1.0 Export for Connascence Analysis

Generates SARIF (Static Analysis Results Interchange Format) reports
compatible with GitHub Code Scanning, Azure DevOps, and other platforms.

SARIF 2.1.0 Specification: https://docs.oasis-open.org/sarif/sarif/v2.1.0/
"""

from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, List
import uuid

from analyzer.ast_engine.core_analyzer import AnalysisResult, Violation
from analyzer.thresholds import ConnascenceType


class SARIFReporter:
    """SARIF 2.1.0 report generator."""

    def __init__(self):
        self.tool_name = "connascence"
        self.tool_version = "1.0.0"
        self.tool_uri = "https://github.com/connascence/connascence-analyzer"
        self.organization = "Connascence Analytics"

    def generate(self, result: AnalysisResult) -> str:
        """Generate SARIF report from analysis result."""
        sarif_report = {
            "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0.json",
            "version": "2.1.0",
            "runs": [self._create_run(result)]
        }

        return json.dumps(sarif_report, indent=2, ensure_ascii=False)

    def _create_run(self, result: AnalysisResult) -> Dict[str, Any]:
        """Create the main SARIF run object."""
        return {
            "tool": self._create_tool(),
            "automationDetails": {
                "id": f"connascence/{uuid.uuid4()}",
                "correlationGuid": str(uuid.uuid4()),
                "description": {
                    "text": "Connascence analysis for Python codebases"
                }
            },
            "conversion": {
                "tool": {
                    "driver": {
                        "name": "connascence-cli",
                        "version": self.tool_version
                    }
                },
                "invocation": {
                    "executionSuccessful": True,
                    "startTimeUtc": result.timestamp,
                    "endTimeUtc": datetime.now().isoformat()
                }
            },
            "invocations": [
                {
                    "executionSuccessful": True,
                    "startTimeUtc": result.timestamp,
                    "workingDirectory": {
                        "uri": f"file://{result.project_root}"
                    }
                }
            ],
            "results": [self._create_result(violation) for violation in result.violations],
            "properties": {
                "analysisType": "connascence",
                "totalFilesAnalyzed": result.total_files_analyzed,
                "analysisDurationMs": result.analysis_duration_ms,
                "summaryMetrics": result.summary_metrics,
                "policyPreset": result.policy_preset
            }
        }

    def _create_tool(self) -> Dict[str, Any]:
        """Create the tool descriptor."""
        return {
            "driver": {
                "name": self.tool_name,
                "version": self.tool_version,
                "informationUri": self.tool_uri,
                "organization": self.organization,
                "shortDescription": {
                    "text": "Connascence analysis for reducing coupling in codebases"
                },
                "fullDescription": {
                    "text": (
                        "Professional connascence analyzer that detects various forms "
                        "of coupling in Python code based on Meilir Page-Jones' theory. "
                        "Identifies static forms (Name, Type, Meaning, Position, Algorithm) "
                        "and dynamic forms (Execution, Timing, Value, Identity) of connascence."
                    )
                },
                "rules": self._create_rules(),
                "notifications": [
                    {
                        "id": "CFG001",
                        "shortDescription": {
                            "text": "Configuration issue"
                        },
                        "messageStrings": {
                            "default": {
                                "text": "Configuration issue: {0}"
                            }
                        }
                    }
                ]
            }
        }

    def _create_rules(self) -> List[Dict[str, Any]]:
        """Create SARIF rule definitions for all connascence types."""
        rules = []

        # Define rules for each connascence type
        rule_definitions = {
            ConnascenceType.NAME: {
                "name": "Connascence of Name",
                "shortDescription": "Dependencies on specific names or identifiers",
                "fullDescription": (
                    "Connascence of Name occurs when multiple components must agree "
                    "on the name of an entity. This is the weakest form of connascence "
                    "but can still cause maintenance issues when names change."
                ),
                "defaultSeverity": "note",
                "tags": ["coupling", "maintenance", "static"]
            },
            ConnascenceType.TYPE: {
                "name": "Connascence of Type",
                "shortDescription": "Dependencies on data types",
                "fullDescription": (
                    "Connascence of Type occurs when multiple components must agree "
                    "on the type of an entity. Use type hints and proper abstractions "
                    "to minimize type coupling."
                ),
                "defaultSeverity": "note",
                "tags": ["coupling", "types", "static"]
            },
            ConnascenceType.MEANING: {
                "name": "Connascence of Meaning",
                "shortDescription": "Dependencies on magic literals or values",
                "fullDescription": (
                    "Connascence of Meaning occurs when multiple components must agree "
                    "on the meaning of particular values. Magic numbers and strings "
                    "create this coupling. Use named constants instead."
                ),
                "defaultSeverity": "warning",
                "tags": ["coupling", "magic-literals", "static", "maintenance"]
            },
            ConnascenceType.POSITION: {
                "name": "Connascence of Position",
                "shortDescription": "Dependencies on parameter or argument order",
                "fullDescription": (
                    "Connascence of Position occurs when multiple components must agree "
                    "on the order of values. Function parameters create this coupling. "
                    "Use keyword arguments or data structures to reduce it."
                ),
                "defaultSeverity": "warning",
                "tags": ["coupling", "parameters", "static", "api-design"]
            },
            ConnascenceType.ALGORITHM: {
                "name": "Connascence of Algorithm",
                "shortDescription": "Dependencies on specific algorithms or implementations",
                "fullDescription": (
                    "Connascence of Algorithm occurs when multiple components must agree "
                    "on a particular algorithm. This includes duplicate code and "
                    "complex interdependent logic. Extract shared algorithms."
                ),
                "defaultSeverity": "warning",
                "tags": ["coupling", "duplication", "static", "complexity"]
            },
            ConnascenceType.EXECUTION: {
                "name": "Connascence of Execution",
                "shortDescription": "Dependencies on execution order",
                "fullDescription": (
                    "Connascence of Execution occurs when the order of execution matters. "
                    "This dynamic coupling makes code fragile and hard to test. "
                    "Use dependency injection and proper initialization patterns."
                ),
                "defaultSeverity": "error",
                "tags": ["coupling", "execution-order", "dynamic", "reliability"]
            },
            ConnascenceType.TIMING: {
                "name": "Connascence of Timing",
                "shortDescription": "Dependencies on timing or delays",
                "fullDescription": (
                    "Connascence of Timing occurs when components depend on timing. "
                    "This is a strong form of dynamic coupling that makes systems "
                    "unreliable. Use proper synchronization mechanisms."
                ),
                "defaultSeverity": "error",
                "tags": ["coupling", "timing", "dynamic", "reliability"]
            },
            ConnascenceType.VALUE: {
                "name": "Connascence of Value",
                "shortDescription": "Dependencies on shared mutable values",
                "fullDescription": (
                    "Connascence of Value occurs when multiple components depend on "
                    "the same shared value. This dynamic coupling can lead to "
                    "unexpected side effects and race conditions."
                ),
                "defaultSeverity": "warning",
                "tags": ["coupling", "shared-state", "dynamic", "concurrency"]
            },
            ConnascenceType.IDENTITY: {
                "name": "Connascence of Identity",
                "shortDescription": "Dependencies on object identity",
                "fullDescription": (
                    "Connascence of Identity occurs when multiple components must "
                    "reference the same object. This is the strongest and most "
                    "dangerous form of coupling. Use immutable objects and values."
                ),
                "defaultSeverity": "error",
                "tags": ["coupling", "identity", "dynamic", "reliability"]
            }
        }

        for connascence_type, definition in rule_definitions.items():
            rule_id = f"CON_{connascence_type.value}"

            rule = {
                "id": rule_id,
                "name": definition["name"],
                "shortDescription": {
                    "text": definition["shortDescription"]
                },
                "fullDescription": {
                    "text": definition["fullDescription"]
                },
                "defaultConfiguration": {
                    "level": definition["defaultSeverity"]
                },
                "properties": {
                    "tags": definition["tags"],
                    "precision": "high",
                    "problem.severity": definition["defaultSeverity"]
                },
                "messageStrings": {
                    "default": {
                        "text": "{0}"
                    }
                },
                "helpUri": f"{self.tool_uri}/docs/rules/{rule_id.lower()}"
            }

            rules.append(rule)

        return rules

    def _create_result(self, violation: Violation) -> Dict[str, Any]:
        """Create SARIF result from violation."""
        rule_id = f"CON_{violation.type.value}"

        # Convert severity to SARIF level
        sarif_level = self._severity_to_sarif_level(violation.severity.value)

        result = {
            "ruleId": rule_id,
            "ruleIndex": self._get_rule_index(violation.type),
            "level": sarif_level,
            "message": {
                "text": violation.description,
                "arguments": [violation.description]
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": self._normalize_path(violation.file_path),
                            "uriBaseId": "%SRCROOT%"
                        },
                        "region": {
                            "startLine": violation.line_number,
                            "startColumn": violation.column + 1,  # SARIF is 1-based
                            "endLine": violation.end_line or violation.line_number,
                            "endColumn": (violation.end_column + 1) if violation.end_column else violation.column + 1
                        }
                    }
                }
            ],
            "partialFingerprints": {
                "primaryLocationLineHash": violation.id,
                "connascenceFingerprint": violation.id
            },
            "properties": {
                "connascenceType": violation.type.value,
                "severity": violation.severity.value,
                "weight": violation.weight,
                "locality": violation.locality,
                "functionName": violation.function_name,
                "className": violation.class_name,
                "recommendation": violation.recommendation,
                "context": violation.context
            }
        }

        # Add code snippet if available
        if violation.code_snippet:
            result["locations"][0]["physicalLocation"]["contextRegion"] = {
                "snippet": {
                    "text": violation.code_snippet
                }
            }

        # Add related locations for cross-module violations
        if violation.locality == "cross_module" and violation.context:
            related_locations = self._extract_related_locations(violation)
            if related_locations:
                result["relatedLocations"] = related_locations

        return result

    def _severity_to_sarif_level(self, severity: str) -> str:
        """Convert connascence severity to SARIF level."""
        mapping = {
            "low": "note",
            "medium": "warning",
            "high": "error",
            "critical": "error"
        }
        return mapping.get(severity, "warning")

    def _get_rule_index(self, connascence_type: ConnascenceType) -> int:
        """Get the index of a rule in the rules array."""
        # This would map to actual rule positions
        type_order = [
            ConnascenceType.NAME,
            ConnascenceType.TYPE,
            ConnascenceType.MEANING,
            ConnascenceType.POSITION,
            ConnascenceType.ALGORITHM,
            ConnascenceType.EXECUTION,
            ConnascenceType.TIMING,
            ConnascenceType.VALUE,
            ConnascenceType.IDENTITY
        ]
        return type_order.index(connascence_type)

    def _normalize_path(self, file_path: str) -> str:
        """Normalize file path for SARIF."""
        # Convert Windows paths to URI format
        path = Path(file_path)
        return path.as_posix()

    def _extract_related_locations(self, violation: Violation) -> List[Dict[str, Any]]:
        """Extract related locations from violation context."""
        related_locations = []

        # Example: if violation has related function or duplicate
        if "similar_function" in violation.context:
            related_locations.append({
                "id": 1,
                "physicalLocation": {
                    "artifactLocation": {
                        "uri": self._normalize_path(violation.file_path),
                        "uriBaseId": "%SRCROOT%"
                    },
                    "region": {
                        "startLine": violation.line_number,
                        "startColumn": violation.column + 1
                    }
                },
                "message": {
                    "text": f"Related to {violation.context['similar_function']}"
                }
            })

        return related_locations

    def export_results(self, result, output_file=None):
        """Export results to SARIF format.

        Args:
            result: Analysis result (dict or AnalysisResult object)
            output_file: Optional file path to write to. If None, returns SARIF string.

        Returns:
            SARIF JSON string if output_file is None, otherwise writes to file.
        """
        # Handle both dict and AnalysisResult objects
        if isinstance(result, dict):
            # Convert dict result to SARIF-compatible format
            sarif_output = self._convert_dict_to_sarif(result)
        else:
            # Use the generate method for AnalysisResult objects
            sarif_output = self.generate(result)

        if output_file:
            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(sarif_output)
        else:
            # Return SARIF string
            return sarif_output

    def _convert_dict_to_sarif(self, result_dict):
        """Convert dict-based analysis result to SARIF format."""
        # Create a minimal SARIF report from dict results
        violations = result_dict.get('violations', [])

        sarif_report = {
            "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0.json",
            "version": "2.1.0",
            "runs": [{
                "tool": self._create_tool(),
                "automationDetails": {
                    "id": f"connascence/{uuid.uuid4()}",
                    "description": {
                        "text": "Connascence analysis for Python codebases"
                    }
                },
                "invocations": [{
                    "executionSuccessful": result_dict.get('success', True),
                    "startTimeUtc": datetime.now().isoformat(),
                    "workingDirectory": {
                        "uri": f"file://{result_dict.get('path', '.')}"
                    }
                }],
                "results": [self._create_result_from_dict(violation) for violation in violations],
                "properties": {
                    "analysisType": "connascence",
                    "policyPreset": result_dict.get('policy', 'default'),
                    "summaryMetrics": result_dict.get('summary', {})
                }
            }]
        }

        return json.dumps(sarif_report, indent=2, ensure_ascii=False)

    def _create_result_from_dict(self, violation_dict):
        """Create SARIF result from violation dictionary."""
        rule_id = violation_dict.get('rule_id', 'CON_UNKNOWN')
        severity = violation_dict.get('severity', 'medium')
        sarif_level = self._severity_to_sarif_level(severity)

        result = {
            "ruleId": rule_id,
            "level": sarif_level,
            "message": {
                "text": violation_dict.get('description', 'Connascence violation detected'),
                "arguments": [violation_dict.get('description', 'Connascence violation detected')]
            },
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {
                        "uri": self._normalize_path(violation_dict.get('file_path', 'unknown.py')),
                        "uriBaseId": "%SRCROOT%"
                    },
                    "region": {
                        "startLine": violation_dict.get('line_number', 1),
                        "startColumn": 1
                    }
                }
            }],
            "partialFingerprints": {
                "primaryLocationLineHash": violation_dict.get('id', str(uuid.uuid4())),
                "connascenceFingerprint": violation_dict.get('id', str(uuid.uuid4()))
            },
            "properties": {
                "connascenceType": violation_dict.get('type', 'unknown'),
                "severity": severity,
                "weight": violation_dict.get('weight', 1.0)
            }
        }

        return result
