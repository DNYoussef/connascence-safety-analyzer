# SPDX-License-Identifier: MIT
"""
JSON export functionality for connascence analysis results.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class JSONReporter:
    """JSON export reporter for analysis results."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
    
    def export_results(self, results: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """Export analysis results to JSON format."""
        
        # Prepare formatted results
        formatted_results = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "version": "2.0.0",
                "analyzer": "connascence-safety-analyzer"
            },
            "summary": results.get('summary', {}),
            "violations": results.get('violations', []),
            "nasa_compliance": results.get('nasa_compliance', {}),
            "policy": results.get('policy', 'default'),
            "path": results.get('path', '.'),
        }
        
        # Export to file if path provided
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(formatted_results, f, indent=2, ensure_ascii=False)
            
            return str(output_file)
        
        # Return JSON string
        return json.dumps(formatted_results, indent=2, ensure_ascii=False)
    
    def format_violations(self, violations: List[Dict]) -> List[Dict]:
        """Format violations for JSON export."""
        formatted = []
        
        for violation in violations:
            formatted_violation = {
                "id": violation.get("id"),
                "rule_id": violation.get("rule_id"),
                "type": violation.get("connascence_type") or violation.get("type"),
                "severity": violation.get("severity"),
                "description": violation.get("description"),
                "location": {
                    "file": violation.get("file_path"),
                    "line": violation.get("line_number"),
                },
                "weight": violation.get("weight", 1.0)
            }
            formatted.append(formatted_violation)
        
        return formatted
    
    def create_summary(self, violations: List[Dict]) -> Dict[str, Any]:
        """Create summary from violations."""
        severity_counts = {}
        type_counts = {}
        
        for violation in violations:
            severity = violation.get("severity", "unknown")
            violation_type = violation.get("connascence_type") or violation.get("type", "unknown")
            
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            type_counts[violation_type] = type_counts.get(violation_type, 0) + 1
        
        return {
            "total_violations": len(violations),
            "severity_breakdown": severity_counts,
            "type_breakdown": type_counts,
            "quality_score": self._calculate_quality_score(violations)
        }
    
    def _calculate_quality_score(self, violations: List[Dict]) -> float:
        """Calculate overall quality score."""
        if not violations:
            return 1.0
        
        # Simple scoring based on severity weights
        total_weight = 0
        max_weight = len(violations) * 5  # Assume max weight of 5 per violation
        
        for violation in violations:
            severity = violation.get("severity", "low")
            weight_map = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
            total_weight += weight_map.get(severity, 2)
        
        # Invert the score (lower violations = higher score)
        score = max(0.0, 1.0 - (total_weight / max_weight))
        return round(score, 3)