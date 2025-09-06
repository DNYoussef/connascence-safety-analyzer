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
JSON Export for Machine-Readable Connascence Analysis

Generates stable, agent-friendly JSON reports with deterministic ordering
and comprehensive metadata for tool integration.
"""

import json
from typing import Any, Dict, List

from analyzer.ast_engine.core_analyzer import AnalysisResult, Violation


class JSONReporter:
    """JSON report generator with stable schema."""

    def __init__(self):
        self.schema_version = "1.0.0"

    def generate(self, result: AnalysisResult) -> str:
        """Generate JSON report from analysis result."""
        report = {
            "schema_version": self.schema_version,
            "metadata": self._create_metadata(result),
            "summary": self._create_summary(result),
            "violations": [self._serialize_violation(v) for v in result.violations],
            "file_stats": result.file_stats,
            "policy_compliance": self._create_policy_compliance(result)
        }

        # Ensure deterministic ordering
        return json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False)

    def _create_metadata(self, result: AnalysisResult) -> Dict[str, Any]:
        """Create report metadata."""
        return {
            "tool": {
                "name": "connascence",
                "version": "1.0.0",
                "url": "https://github.com/connascence/connascence-analyzer"
            },
            "analysis": {
                "timestamp": result.timestamp,
                "project_root": result.project_root,
                "total_files_analyzed": result.total_files_analyzed,
                "analysis_duration_ms": result.analysis_duration_ms,
                "policy_preset": result.policy_preset
            },
            "environment": {
                "python_version": "3.11+",
                "platform": "multi-platform"
            }
        }

    def _create_summary(self, result: AnalysisResult) -> Dict[str, Any]:
        """Create summary statistics."""
        violations = result.violations

        # Count by type
        by_type = {}
        for violation in violations:
            type_key = violation.type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1

        # Count by severity
        by_severity = {}
        for violation in violations:
            severity_key = violation.severity.value
            by_severity[severity_key] = by_severity.get(severity_key, 0) + 1

        # Count by locality
        by_locality = {}
        for violation in violations:
            locality_key = violation.locality
            by_locality[locality_key] = by_locality.get(locality_key, 0) + 1

        # Calculate weights
        total_weight = sum(v.weight for v in violations)
        avg_weight = total_weight / len(violations) if violations else 0

        # File distribution
        files_with_violations = len({v.file_path for v in violations})

        return {
            "total_violations": len(violations),
            "total_weight": round(total_weight, 2),
            "average_weight": round(avg_weight, 2),
            "files_with_violations": files_with_violations,
            "violations_by_type": dict(sorted(by_type.items())),
            "violations_by_severity": dict(sorted(by_severity.items())),
            "violations_by_locality": dict(sorted(by_locality.items())),
            "top_files": self._get_top_problematic_files(violations)[:10],
            "quality_metrics": {
                "connascence_index": round(total_weight, 2),
                "violations_per_file": round(len(violations) / max(1, result.total_files_analyzed), 2),
                "critical_violations": by_severity.get("critical", 0),
                "high_violations": by_severity.get("high", 0)
            }
        }

    def _serialize_violation(self, violation: Violation) -> Dict[str, Any]:
        """Serialize a violation to JSON-friendly format."""
        return {
            "id": violation.id,
            "rule_id": f"CON_{violation.type.value}",
            "type": violation.type.value,
            "severity": violation.severity.value,
            "weight": round(violation.weight, 2),
            "locality": violation.locality,

            # Location information
            "file_path": violation.file_path,
            "line_number": violation.line_number,
            "column": violation.column,
            "end_line": violation.end_line,
            "end_column": violation.end_column,

            # Description and recommendations
            "description": violation.description,
            "recommendation": violation.recommendation,

            # Context information (optional)
            "function_name": violation.function_name,
            "class_name": violation.class_name,
            "code_snippet": violation.code_snippet,

            # Additional context
            "context": violation.context or {}
        }

    def _create_policy_compliance(self, result: AnalysisResult) -> Dict[str, Any]:
        """Create policy compliance information."""
        compliance = {
            "policy_preset": result.policy_preset,
            "budget_status": result.budget_status,
            "baseline_comparison": result.baseline_comparison,
            "quality_gates": {}
        }

        # Calculate quality gate status
        violations = result.violations
        critical_violations = sum(1 for v in violations if v.severity.value == "critical")
        high_violations = sum(1 for v in violations if v.severity.value == "high")

        # Basic quality gates
        compliance["quality_gates"] = {
            "no_critical_violations": critical_violations == 0,
            "max_high_violations": high_violations <= 10,  # Configurable
            "total_violations_acceptable": len(violations) <= 100  # Configurable
        }

        return compliance

    def export_results(self, result, output_file=None):
        """Export results to JSON format.

        Args:
            result: Analysis result (dict or AnalysisResult object)
            output_file: Optional file path to write to. If None, returns JSON string.

        Returns:
            JSON string if output_file is None, otherwise writes to file.
        """
        # Handle both dict and AnalysisResult objects
        if isinstance(result, dict):
            # Convert dict result to JSON-friendly format
            json_output = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False)
        else:
            # Use the generate method for AnalysisResult objects
            json_output = self.generate(result)

        if output_file:
            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_output)
        else:
            # Return JSON string
            return json_output

    def _get_top_problematic_files(self, violations: List[Violation]) -> List[Dict[str, Any]]:
        """Get files with the most violations, sorted by weight."""
        file_stats = {}

        for violation in violations:
            file_path = violation.file_path
            if file_path not in file_stats:
                file_stats[file_path] = {
                    "file_path": file_path,
                    "violation_count": 0,
                    "total_weight": 0.0,
                    "severity_breakdown": {}
                }

            stats = file_stats[file_path]
            stats["violation_count"] += 1
            stats["total_weight"] += violation.weight

            severity = violation.severity.value
            stats["severity_breakdown"][severity] = stats["severity_breakdown"].get(severity, 0) + 1

        # Sort by total weight, then by violation count
        sorted_files = sorted(
            file_stats.values(),
            key=lambda x: (x["total_weight"], x["violation_count"]),
            reverse=True
        )

        # Round weights for cleaner output
        for file_stat in sorted_files:
            file_stat["total_weight"] = round(file_stat["total_weight"], 2)

        return sorted_files
