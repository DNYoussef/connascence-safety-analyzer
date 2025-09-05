# SPDX-License-Identifier: MIT
"""
SARIF (Static Analysis Results Interchange Format) export functionality.
"""

import json
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class SARIFReporter:
    """SARIF format reporter for analysis results."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.tool_name = "connascence-safety-analyzer"
        self.tool_version = "2.0.0"
    
    def export_results(self, results: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """Export analysis results to SARIF format."""
        
        sarif_report = self._create_sarif_report(results)
        
        # Export to file if path provided
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(sarif_report, f, indent=2, ensure_ascii=False)
            
            return str(output_file)
        
        # Return SARIF JSON string
        return json.dumps(sarif_report, indent=2, ensure_ascii=False)
    
    def _create_sarif_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Create SARIF v2.1.0 compliant report."""
        
        violations = results.get('violations', [])
        
        # Create SARIF structure
        sarif_report = {
            "version": "2.1.0",
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": self.tool_name,
                            "version": self.tool_version,
                            "informationUri": "https://github.com/DNYoussef/connascence-safety-analyzer",
                            "rules": self._create_rules(violations)
                        }
                    },
                    "results": self._create_results(violations),
                    "invocations": [
                        {
                            "executionSuccessful": True,
                            "startTimeUtc": datetime.now().isoformat() + "Z"
                        }
                    ]
                }
            ]
        }
        
        return sarif_report
    
    def _create_rules(self, violations: List[Dict]) -> List[Dict]:
        """Create SARIF rules from violations."""
        rules_dict = {}
        
        for violation in violations:
            rule_id = violation.get("rule_id", "unknown")
            if rule_id not in rules_dict:
                rules_dict[rule_id] = {
                    "id": rule_id,
                    "name": rule_id.replace("_", " ").title(),
                    "shortDescription": {
                        "text": f"{rule_id} violation"
                    },
                    "fullDescription": {
                        "text": violation.get("description", "Connascence violation detected")
                    },
                    "help": {
                        "text": f"This rule detects {rule_id} connascence violations."
                    },
                    "properties": {
                        "category": violation.get("connascence_type", "CoA"),
                        "severity": violation.get("severity", "medium")
                    }
                }
        
        return list(rules_dict.values())
    
    def _create_results(self, violations: List[Dict]) -> List[Dict]:
        """Create SARIF results from violations."""
        results = []
        
        for violation in violations:
            result = {
                "ruleId": violation.get("rule_id", "unknown"),
                "level": self._map_severity_to_level(violation.get("severity", "medium")),
                "message": {
                    "text": violation.get("description", "Connascence violation detected")
                },
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": violation.get("file_path", "unknown")
                            },
                            "region": {
                                "startLine": violation.get("line_number", 1),
                                "startColumn": 1
                            }
                        }
                    }
                ],
                "properties": {
                    "weight": violation.get("weight", 1.0),
                    "connascence_type": violation.get("connascence_type", "CoA"),
                    "violation_id": violation.get("id", str(uuid.uuid4()))
                }
            }
            
            results.append(result)
        
        return results
    
    def _map_severity_to_level(self, severity: str) -> str:
        """Map internal severity to SARIF level."""
        severity_map = {
            "critical": "error",
            "high": "error", 
            "medium": "warning",
            "low": "note",
            "info": "note"
        }
        return severity_map.get(severity.lower(), "warning")