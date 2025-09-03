"""
JSON Export for Machine-Readable Connascence Analysis

Consolidated from demo_scans/reports/json_export.py with enhancements.
Generates stable, agent-friendly JSON reports with deterministic ordering
and comprehensive metadata for tool integration.
"""

import json
from datetime import datetime
from typing import Any, Dict, List

from analyzer.ast_engine.core_analyzer import AnalysisResult, Violation


class JSONReporter:
    """JSON report generator with stable schema and enterprise features."""
    
    def __init__(self):
        self.schema_version = "1.1.0"  # Upgraded from original
        self._config = {}
    
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure JSON reporter with template options."""
        self._config.update(config)
    
    def generate(self, result: AnalysisResult) -> str:
        """Generate JSON report from analysis result."""
        report = {
            "schema_version": self.schema_version,
            "metadata": self._create_metadata(result),
            "summary": self._create_summary(result),
            "violations": [self._serialize_violation(v) for v in result.violations],
            "policy_compliance": self._create_policy_compliance(result)
        }
        
        # Add optional sections based on configuration
        if self._config.get('include_file_stats', True):
            report["file_stats"] = getattr(result, 'file_stats', {})
        
        if self._config.get('include_trend_analysis'):
            report["trend_analysis"] = self._create_trend_analysis(result)
        
        if self._config.get('enterprise_mode'):
            report["enterprise"] = self._create_enterprise_section(result)
        
        # Ensure deterministic ordering
        return json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False)
    
    def _create_metadata(self, result: AnalysisResult) -> Dict[str, Any]:
        """Create enhanced report metadata."""
        metadata = {
            "tool": {
                "name": "connascence",
                "version": "1.0.0",
                "url": "https://github.com/connascence/connascence-analyzer",
                "schema_version": self.schema_version
            },
            "analysis": {
                "timestamp": result.timestamp,
                "project_root": result.project_root,
                "total_files_analyzed": result.total_files_analyzed,
                "analysis_duration_ms": result.analysis_duration_ms,
                "policy_preset": getattr(result, 'policy_preset', 'default')
            },
            "environment": {
                "python_version": "3.11+",
                "platform": "multi-platform"
            }
        }
        
        # Add git information if available
        if hasattr(result, 'git_info'):
            metadata["git"] = result.git_info
        
        return metadata
    
    def _create_summary(self, result: AnalysisResult) -> Dict[str, Any]:
        """Create comprehensive summary statistics."""
        violations = result.violations
        
        # Basic counts
        by_type = {}
        by_severity = {}
        by_locality = {}
        
        for violation in violations:
            # By type
            type_key = violation.type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1
            
            # By severity
            severity_key = violation.severity.value
            by_severity[severity_key] = by_severity.get(severity_key, 0) + 1
            
            # By locality
            locality_key = violation.locality
            by_locality[locality_key] = by_locality.get(locality_key, 0) + 1
        
        # Weight calculations
        total_weight = sum(v.weight for v in violations)
        avg_weight = total_weight / len(violations) if violations else 0
        
        # File distribution
        files_with_violations = len(set(v.file_path for v in violations))
        
        summary = {
            "total_violations": len(violations),
            "total_weight": round(total_weight, 2),
            "average_weight": round(avg_weight, 2),
            "files_with_violations": files_with_violations,
            "violations_by_type": dict(sorted(by_type.items())),
            "violations_by_severity": dict(sorted(by_severity.items())),
            "violations_by_locality": dict(sorted(by_locality.items())),
            "quality_metrics": {
                "connascence_index": round(total_weight, 2),
                "violations_per_file": round(len(violations) / max(1, result.total_files_analyzed), 2),
                "critical_violations": by_severity.get("critical", 0),
                "high_violations": by_severity.get("high", 0),
                "violation_density": round(len(violations) / max(1, result.total_files_analyzed) * 100, 2)
            }
        }
        
        # Add top problematic files
        if self._config.get('include_top_files', True):
            summary["top_files"] = self._get_top_problematic_files(violations)[:10]
        
        # Add pattern analysis
        if self._config.get('detailed_analysis'):
            summary["pattern_analysis"] = self._analyze_patterns(violations)
        
        return summary
    
    def _serialize_violation(self, violation: Violation) -> Dict[str, Any]:
        """Serialize a violation to JSON-friendly format with enhancements."""
        serialized = {
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
            
            # Description and recommendations
            "description": violation.description,
            "recommendation": violation.recommendation,
            
            # Context information (optional)
            "function_name": violation.function_name,
            "class_name": violation.class_name
        }
        
        # Optional fields based on configuration
        if self._config.get('include_code_snippets', False) and violation.code_snippet:
            serialized["code_snippet"] = violation.code_snippet
        
        if self._config.get('detailed_context') and violation.context:
            serialized["context"] = violation.context
        
        if violation.end_line:
            serialized["end_line"] = violation.end_line
        if violation.end_column:
            serialized["end_column"] = violation.end_column
        
        return serialized
    
    def _create_policy_compliance(self, result: AnalysisResult) -> Dict[str, Any]:
        """Create enhanced policy compliance information."""
        violations = result.violations
        critical_count = sum(1 for v in violations if v.severity.value == "critical")
        high_count = sum(1 for v in violations if v.severity.value == "high")
        
        compliance = {
            "policy_preset": getattr(result, 'policy_preset', 'default'),
            "budget_status": getattr(result, 'budget_status', 'unknown'),
            "baseline_comparison": getattr(result, 'baseline_comparison', {}),
            "quality_gates": {
                "no_critical_violations": critical_count == 0,
                "max_high_violations_10": high_count <= 10,
                "max_high_violations_5": high_count <= 5,
                "total_violations_under_100": len(violations) <= 100,
                "total_violations_under_50": len(violations) <= 50,
                "violation_density_acceptable": len(violations) / max(1, result.total_files_analyzed) <= 2.0
            },
            "compliance_score": self._calculate_compliance_score(violations, result.total_files_analyzed)
        }
        
        return compliance
    
    def _calculate_compliance_score(self, violations: List[Violation], total_files: int) -> float:
        """Calculate overall compliance score (0-100)."""
        if not violations:
            return 100.0
        
        # Weight-based scoring
        total_weight = sum(v.weight for v in violations)
        severity_penalties = {
            "critical": 10,
            "high": 5,
            "medium": 2,
            "low": 1
        }
        
        penalty_score = sum(severity_penalties.get(v.severity.value, 1) for v in violations)
        max_penalty = total_files * 10  # Assume worst case
        
        score = max(0, 100 - (penalty_score / max(1, max_penalty)) * 100)
        return round(score, 1)
    
    def _get_top_problematic_files(self, violations: List[Violation]) -> List[Dict[str, Any]]:
        """Get files with the most violations, sorted by weight and count."""
        file_stats = {}
        
        for violation in violations:
            file_path = violation.file_path
            if file_path not in file_stats:
                file_stats[file_path] = {
                    "file_path": file_path,
                    "violation_count": 0,
                    "total_weight": 0.0,
                    "severity_breakdown": {},
                    "type_breakdown": {}
                }
            
            stats = file_stats[file_path]
            stats["violation_count"] += 1
            stats["total_weight"] += violation.weight
            
            # Severity breakdown
            severity = violation.severity.value
            stats["severity_breakdown"][severity] = stats["severity_breakdown"].get(severity, 0) + 1
            
            # Type breakdown
            violation_type = violation.type.value
            stats["type_breakdown"][violation_type] = stats["type_breakdown"].get(violation_type, 0) + 1
        
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
    
    def _analyze_patterns(self, violations: List[Violation]) -> Dict[str, Any]:
        """Analyze violation patterns for insights."""
        patterns = {
            "hotspot_functions": {},
            "hotspot_classes": {},
            "cross_module_violations": 0,
            "file_clusters": {}
        }
        
        for violation in violations:
            # Function hotspots
            if violation.function_name:
                func_key = f"{violation.file_path}::{violation.function_name}"
                patterns["hotspot_functions"][func_key] = patterns["hotspot_functions"].get(func_key, 0) + 1
            
            # Class hotspots
            if violation.class_name:
                class_key = f"{violation.file_path}::{violation.class_name}"
                patterns["hotspot_classes"][class_key] = patterns["hotspot_classes"].get(class_key, 0) + 1
            
            # Cross-module violations
            if violation.locality == "cross_module":
                patterns["cross_module_violations"] += 1
        
        return patterns
    
    def _create_trend_analysis(self, result: AnalysisResult) -> Dict[str, Any]:
        """Create trend analysis section."""
        return getattr(result, 'trend_data', {})
    
    def _create_enterprise_section(self, result: AnalysisResult) -> Dict[str, Any]:
        """Create enterprise-specific reporting section."""
        return {
            "roi_metrics": getattr(result, 'roi_metrics', {}),
            "benchmark_data": getattr(result, 'benchmark_data', {}),
            "technical_debt_estimate": getattr(result, 'technical_debt_estimate', {}),
            "team_productivity_impact": getattr(result, 'team_impact', {})
        }