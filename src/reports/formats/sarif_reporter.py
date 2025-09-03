"""
SARIF 2.1.0 Export for Connascence Analysis

Consolidated from demo_scans/reports/sarif_export.py with improvements.
Generates SARIF (Static Analysis Results Interchange Format) reports
compatible with GitHub Code Scanning, Azure DevOps, and other platforms.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from analyzer.ast_engine.core_analyzer import AnalysisResult, Violation
from analyzer.thresholds import ConnascenceType


class SARIFReporter:
    """SARIF 2.1.0 report generator with enhanced enterprise features."""
    
    def __init__(self):
        self.tool_name = "connascence"
        self.tool_version = "1.0.0"
        self.tool_uri = "https://github.com/connascence/connascence-analyzer"
        self.organization = "Connascence Analytics"
        self._config = {}
    
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure SARIF reporter with template options."""
        self._config.update(config)
    
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
        run = {
            "tool": self._create_tool(),
            "automationDetails": {
                "id": f"connascence/{uuid.uuid4()}",
                "correlationGuid": str(uuid.uuid4()),
                "description": {
                    "text": "Connascence analysis for reducing coupling in codebases"
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
                "summaryMetrics": getattr(result, 'summary_metrics', {}),
                "policyPreset": getattr(result, 'policy_preset', 'default')
            }
        }
        
        # Add enterprise metadata if configured
        if self._config.get('enterprise_mode'):
            run["properties"]["enterpriseMetadata"] = self._create_enterprise_metadata(result)
        
        return run
    
    def _create_tool(self) -> Dict[str, Any]:
        """Create the tool descriptor with enhanced rules."""
        return {
            "driver": {
                "name": self.tool_name,
                "version": self.tool_version,
                "informationUri": self.tool_uri,
                "organization": self.organization,
                "shortDescription": {
                    "text": "Enterprise connascence analyzer for reducing coupling"
                },
                "fullDescription": {
                    "text": (
                        "Professional connascence analyzer that detects various forms "
                        "of coupling in codebases based on Meilir Page-Jones' theory. "
                        "Identifies static forms (Name, Type, Meaning, Position, Algorithm) "
                        "and dynamic forms (Execution, Timing, Value, Identity) of connascence."
                    )
                },
                "rules": self._create_rules(),
                "notifications": [
                    {
                        "id": "CFG001",
                        "shortDescription": {"text": "Configuration issue"},
                        "messageStrings": {
                            "default": {"text": "Configuration issue: {0}"}
                        }
                    }
                ]
            }
        }
    
    def _create_rules(self) -> List[Dict[str, Any]]:
        """Create SARIF rule definitions for all connascence types."""
        rules = []
        
        # Enhanced rule definitions with enterprise context
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
                "tags": ["coupling", "maintenance", "static", "refactoring"]
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
                "tags": ["coupling", "types", "static", "type-safety"]
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
                "tags": ["coupling", "magic-literals", "static", "maintenance", "constants"]
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
                "tags": ["coupling", "parameters", "static", "api-design", "usability"]
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
                "tags": ["coupling", "duplication", "static", "complexity", "dry"]
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
                "tags": ["coupling", "execution-order", "dynamic", "reliability", "testing"]
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
                "tags": ["coupling", "timing", "dynamic", "reliability", "concurrency"]
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
                "tags": ["coupling", "shared-state", "dynamic", "concurrency", "immutability"]
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
                "tags": ["coupling", "identity", "dynamic", "reliability", "immutability"]
            }
        }
        
        for connascence_type, definition in rule_definitions.items():
            rule_id = f"CON_{connascence_type.value}"
            
            rule = {
                "id": rule_id,
                "name": definition["name"],
                "shortDescription": {"text": definition["shortDescription"]},
                "fullDescription": {"text": definition["fullDescription"]},
                "defaultConfiguration": {"level": definition["defaultSeverity"]},
                "properties": {
                    "tags": definition["tags"],
                    "precision": "high",
                    "problem.severity": definition["defaultSeverity"],
                    "security-severity": self._get_security_severity(connascence_type)
                },
                "messageStrings": {
                    "default": {"text": "{0}"},
                    "withRecommendation": {"text": "{0}\n\nRecommendation: {1}"}
                },
                "helpUri": f"{self.tool_uri}/docs/rules/{rule_id.lower()}"
            }
            
            rules.append(rule)
        
        return rules
    
    def _get_security_severity(self, connascence_type: ConnascenceType) -> str:
        """Map connascence types to security severity levels."""
        security_mapping = {
            ConnascenceType.EXECUTION: "8.0",
            ConnascenceType.TIMING: "7.5",
            ConnascenceType.IDENTITY: "7.0",
            ConnascenceType.VALUE: "5.0",
            ConnascenceType.ALGORITHM: "4.0",
            ConnascenceType.POSITION: "3.0",
            ConnascenceType.MEANING: "2.5",
            ConnascenceType.TYPE: "2.0",
            ConnascenceType.NAME: "1.0"
        }
        return security_mapping.get(connascence_type, "2.0")
    
    def _create_result(self, violation: Violation) -> Dict[str, Any]:
        """Create SARIF result from violation with enhanced metadata."""
        rule_id = f"CON_{violation.type.value}"
        sarif_level = self._severity_to_sarif_level(violation.severity.value)
        
        result = {
            "ruleId": rule_id,
            "ruleIndex": self._get_rule_index(violation.type),
            "level": sarif_level,
            "message": {
                "text": violation.description,
                "arguments": [violation.description]
            },
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {
                        "uri": self._normalize_path(violation.file_path),
                        "uriBaseId": "%SRCROOT%"
                    },
                    "region": {
                        "startLine": violation.line_number,
                        "startColumn": violation.column + 1,
                        "endLine": violation.end_line or violation.line_number,
                        "endColumn": (violation.end_column + 1) if violation.end_column else violation.column + 1
                    }
                }
            }],
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
                "context": violation.context or {}
            }
        }
        
        # Add code snippet if available
        if violation.code_snippet:
            result["locations"][0]["physicalLocation"]["contextRegion"] = {
                "snippet": {"text": violation.code_snippet}
            }
        
        # Add recommendation to message if configured
        if violation.recommendation and self._config.get('include_recommendations', True):
            result["message"] = {
                "text": f"{violation.description}\n\nRecommendation: {violation.recommendation}",
                "messageId": "withRecommendation",
                "arguments": [violation.description, violation.recommendation]
            }
        
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
        type_order = [
            ConnascenceType.NAME, ConnascenceType.TYPE, ConnascenceType.MEANING,
            ConnascenceType.POSITION, ConnascenceType.ALGORITHM, ConnascenceType.EXECUTION,
            ConnascenceType.TIMING, ConnascenceType.VALUE, ConnascenceType.IDENTITY
        ]
        return type_order.index(connascence_type)
    
    def _normalize_path(self, file_path: str) -> str:
        """Normalize file path for SARIF."""
        return Path(file_path).as_posix()
    
    def _create_enterprise_metadata(self, result: AnalysisResult) -> Dict[str, Any]:
        """Create enterprise-specific metadata for SARIF."""
        return {
            "complianceStatus": getattr(result, 'compliance_status', 'unknown'),
            "budgetAnalysis": getattr(result, 'budget_analysis', {}),
            "trendData": getattr(result, 'trend_data', {}),
            "benchmarkComparison": getattr(result, 'benchmark_comparison', {})
        }