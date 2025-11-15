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
Unified Reporting Coordinator
============================

Central coordinator for all reporting formats that leverages existing infrastructure:
- JSON export (existing: reporting/json_export.py)
- SARIF export (existing: reporting/sarif_export.py)
- Markdown summaries (existing: reporting/md_summary.py)
- HTML dashboard (existing: dashboard/)
- CLI outputs (existing: cli/)
- MCP integration (existing: mcp/)

This provides a single entry point for generating reports in any format
while maintaining compatibility with all existing components.
"""

from __future__ import annotations

import logging
from pathlib import Path
import sys
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import existing reporting modules
from analyzer.reporting.json import JSONReporter
from analyzer.reporting.markdown import MarkdownReporter
from analyzer.reporting.sarif import SARIFReporter

# Import unified analyzer (TYPE_CHECKING only to avoid circular import)
if TYPE_CHECKING:
    from analyzer.unified_analyzer import UnifiedAnalysisResult

logger = logging.getLogger(__name__)


class UnifiedReportingCoordinator:
    """
    Central coordinator for all reporting formats.

    Leverages existing reporting infrastructure while providing a unified
    interface for generating reports in any supported format.
    """

    SUPPORTED_FORMATS = [
        "json",  # Machine-readable structured data
        "sarif",  # GitHub Code Scanning compatible
        "markdown",  # PR summaries and documentation
        "html",  # Interactive dashboard
        "text",  # CLI-friendly output
        "csv",  # Spreadsheet-compatible
        "xml",  # Enterprise integration
        "summary",  # Executive summary
    ]

    def __init__(self):
        """Initialize the reporting coordinator with all format handlers."""

        # Initialize existing reporters
        self.json_reporter = JSONReporter()
        self.sarif_reporter = SARIFReporter()
        self.markdown_reporter = MarkdownReporter()

        logger.info("Unified Reporting Coordinator initialized with all format handlers")

    def generate_report(
        self,
        analysis_result: UnifiedAnalysisResult,
        format_type: str,
        output_path: Optional[Union[str, Path]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate a report in the specified format.

        Args:
            analysis_result: Results from unified analysis
            format_type: Target format ('json', 'sarif', 'markdown', etc.)
            output_path: Optional file path to save report
            options: Additional formatting options

        Returns:
            Report content as string
        """

        if format_type not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {format_type}. Supported: {self.SUPPORTED_FORMATS}")

        options = options or {}
        logger.info(f"Generating {format_type} report for {analysis_result.project_path}")

        # Route to appropriate reporter
        if format_type == "json":
            content = self._generate_json_report(analysis_result, options)
        elif format_type == "sarif":
            content = self._generate_sarif_report(analysis_result, options)
        elif format_type == "markdown":
            content = self._generate_markdown_report(analysis_result, options)
        elif format_type == "html":
            content = self._generate_html_report(analysis_result, options)
        elif format_type == "text":
            content = self._generate_text_report(analysis_result, options)
        elif format_type == "csv":
            content = self._generate_csv_report(analysis_result, options)
        elif format_type == "xml":
            content = self._generate_xml_report(analysis_result, options)
        elif format_type == "summary":
            content = self._generate_summary_report(analysis_result, options)
        else:
            raise ValueError(f"Format handler not implemented: {format_type}")

        # Save to file if path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"Report saved to {output_path}")

        return content

    def generate_multi_format_report(
        self,
        analysis_result: UnifiedAnalysisResult,
        formats: List[str],
        output_dir: Union[str, Path],
        base_filename: str = "connascence_report",
    ) -> Dict[str, str]:
        """
        Generate reports in multiple formats simultaneously.

        Args:
            analysis_result: Results from unified analysis
            formats: List of format types to generate
            output_dir: Directory to save all reports
            base_filename: Base name for output files

        Returns:
            Dictionary mapping format to output file path
        """

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_files = {}

        for format_type in formats:
            if format_type not in self.SUPPORTED_FORMATS:
                logger.warning(f"Skipping unsupported format: {format_type}")
                continue

            # Determine file extension
            extension_map = {
                "json": "json",
                "sarif": "sarif",
                "markdown": "md",
                "html": "html",
                "text": "txt",
                "csv": "csv",
                "xml": "xml",
                "summary": "txt",
            }

            extension = extension_map.get(format_type, format_type)
            output_file = output_dir / f"{base_filename}.{extension}"

            try:
                self.generate_report(analysis_result, format_type, output_file)
                generated_files[format_type] = str(output_file)
                logger.info(f"Generated {format_type} report: {output_file}")
            except Exception as e:
                logger.error(f"Failed to generate {format_type} report: {e}")

        return generated_files

    def get_dashboard_report_data(self, analysis_result: UnifiedAnalysisResult) -> Dict[str, Any]:
        """Generate data optimized for dashboard display with enhanced cross-phase integration."""

        # Extract enhanced metadata if available
        audit_trail = getattr(analysis_result, "audit_trail", [])
        correlations = getattr(analysis_result, "correlations", [])
        smart_recommendations = getattr(analysis_result, "smart_recommendations", [])
        cross_phase_analysis = getattr(analysis_result, "cross_phase_analysis", False)

        dashboard_data = {
            "project_info": {
                "name": Path(analysis_result.project_path).name,
                "path": analysis_result.project_path,
                "policy": analysis_result.policy_preset,
                "analyzed_files": analysis_result.files_analyzed,
                "analysis_time": analysis_result.analysis_duration_ms,
                "timestamp": analysis_result.timestamp,
                "cross_phase_analysis_enabled": cross_phase_analysis,
            },
            "quality_metrics": {
                "overall_score": analysis_result.overall_quality_score,
                "connascence_index": analysis_result.connascence_index,
                "nasa_compliance": analysis_result.nasa_compliance_score,
                "duplication_score": analysis_result.duplication_score,
            },
            "violation_summary": {
                "total": analysis_result.total_violations,
                "by_severity": {
                    "critical": analysis_result.critical_count,
                    "high": analysis_result.high_count,
                    "medium": analysis_result.medium_count,
                    "low": analysis_result.low_count,
                },
            },
            "detailed_violations": {
                "connascence": analysis_result.connascence_violations,
                "duplications": analysis_result.duplication_clusters,
                "nasa_compliance": analysis_result.nasa_violations,
            },
            "recommendations": {
                "priority_fixes": analysis_result.priority_fixes,
                "improvement_actions": analysis_result.improvement_actions,
                "smart_recommendations": smart_recommendations,
            },
            "charts": {
                "severity_distribution": self._create_severity_chart_data(analysis_result),
                "file_distribution": self._create_file_chart_data(analysis_result),
                "type_distribution": self._create_type_chart_data(analysis_result),
                "trend_data": self._create_trend_chart_data(analysis_result),
                "correlation_network": self._create_correlation_chart_data(correlations),
            },
            # Enhanced cross-phase analysis data
            "cross_phase_data": {
                "correlations": correlations,
                "audit_trail": audit_trail,
                "phase_timings": self._extract_phase_timings(audit_trail),
                "correlation_summary": self._create_correlation_summary(correlations),
                "hotspot_analysis": self._create_hotspot_analysis(correlations),
            },
        }

        return dashboard_data

    def get_cli_summary(self, analysis_result: UnifiedAnalysisResult, verbose: bool = False) -> str:
        """Generate CLI-friendly summary output."""

        lines = []
        lines.append("=" * 60)
        lines.append("CONNASCENCE ANALYSIS SUMMARY")
        lines.append("=" * 60)
        lines.append("")

        # Project info
        lines.append(f"Project: {Path(analysis_result.project_path).name}")
        lines.append(f"Policy: {analysis_result.policy_preset}")
        lines.append(f"Files analyzed: {analysis_result.files_analyzed}")
        lines.append(f"Analysis time: {analysis_result.analysis_duration_ms}ms")
        lines.append("")

        # Quality scores
        lines.append("QUALITY METRICS:")
        lines.append(f"  Overall Quality Score: {analysis_result.overall_quality_score:.3f}")
        lines.append(f"  Connascence Index: {analysis_result.connascence_index}")
        lines.append(f"  NASA Compliance: {analysis_result.nasa_compliance_score:.3f}")
        lines.append(f"  Duplication Score: {analysis_result.duplication_score:.3f}")
        lines.append("")

        # Violation summary
        lines.append("VIOLATIONS FOUND:")
        lines.append(f"  Total: {analysis_result.total_violations}")
        lines.append(f"  Critical: {analysis_result.critical_count}")
        lines.append(f"  High: {analysis_result.high_count}")
        lines.append(f"  Medium: {analysis_result.medium_count}")
        lines.append(f"  Low: {analysis_result.low_count}")
        lines.append("")

        # Recommendations
        if analysis_result.priority_fixes:
            lines.append("PRIORITY FIXES:")
            for fix in analysis_result.priority_fixes[:5]:
                lines.append(f"  - {fix}")
            lines.append("")

        if verbose and analysis_result.improvement_actions:
            lines.append("IMPROVEMENT ACTIONS:")
            for action in analysis_result.improvement_actions[:5]:
                lines.append(f"  - {action}")
            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)

    # Format-specific generators

    def _generate_json_report(self, analysis_result: UnifiedAnalysisResult, options: Dict) -> str:
        """Generate JSON report using existing JSONReporter."""
        # Convert UnifiedAnalysisResult to format expected by JSONReporter
        legacy_result = self._convert_to_legacy_format(analysis_result)
        return self.json_reporter.generate(legacy_result)

    def _generate_sarif_report(self, analysis_result: UnifiedAnalysisResult, options: Dict) -> str:
        """Generate SARIF report using existing SARIFReporter."""
        legacy_result = self._convert_to_legacy_format(analysis_result)
        return self.sarif_reporter.generate(legacy_result)

    def _generate_markdown_report(self, analysis_result: UnifiedAnalysisResult, options: Dict) -> str:
        """Generate Markdown report using existing MarkdownReporter."""
        legacy_result = self._convert_to_legacy_format(analysis_result)
        return self.markdown_reporter.generate(legacy_result)

    def _generate_html_report(self, analysis_result: UnifiedAnalysisResult, options: Dict) -> str:
        """Generate HTML report for dashboard."""
        self.get_dashboard_report_data(analysis_result)

        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Connascence Analysis Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background: #f5f5f5; padding: 20px; border-radius: 5px; }
        .metrics { display: flex; gap: 20px; margin: 20px 0; }
        .metric { flex: 1; padding: 15px; background: #e9f4ff; border-radius: 5px; text-align: center; }
        .violations { margin: 20px 0; }
        .violation-item { padding: 10px; margin: 5px 0; border-left: 4px solid #ccc; }
        .critical { border-color: #d73a49; }
        .high { border-color: #fb8500; }
        .medium { border-color: #ffd60a; }
        .low { border-color: #28a745; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Connascence Analysis Report</h1>
        <p><strong>Project:</strong> {project_name}</p>
        <p><strong>Analysis Time:</strong> {timestamp}</p>
    </div>

    <div class="metrics">
        <div class="metric">
            <h3>Overall Quality</h3>
            <div style="font-size: 24px; font-weight: bold;">{overall_score:.3f}</div>
        </div>
        <div class="metric">
            <h3>NASA Compliance</h3>
            <div style="font-size: 24px; font-weight: bold;">{nasa_score:.3f}</div>
        </div>
        <div class="metric">
            <h3>Total Violations</h3>
            <div style="font-size: 24px; font-weight: bold;">{total_violations}</div>
        </div>
    </div>

    <div class="violations">
        <h2>Priority Fixes</h2>
        {priority_fixes_html}
    </div>
</body>
</html>
"""

        priority_fixes_html = ""
        for fix in analysis_result.priority_fixes[:10]:
            priority_fixes_html += f'<div class="violation-item critical">• {fix}</div>\n'

        return html_template.format(
            project_name=Path(analysis_result.project_path).name,
            timestamp=analysis_result.timestamp,
            overall_score=analysis_result.overall_quality_score,
            nasa_score=analysis_result.nasa_compliance_score,
            total_violations=analysis_result.total_violations,
            priority_fixes_html=priority_fixes_html,
        )

    def _generate_text_report(self, analysis_result: UnifiedAnalysisResult, options: Dict) -> str:
        """Generate plain text report."""
        return self.get_cli_summary(analysis_result, verbose=options.get("verbose", False))

    def _generate_csv_report(self, analysis_result: UnifiedAnalysisResult, options: Dict) -> str:
        """Generate CSV report."""
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(["File Path", "Line Number", "Type", "Severity", "Description", "Weight", "Category"])

        # Connascence violations
        for violation in analysis_result.connascence_violations:
            writer.writerow(
                [
                    violation.get("file_path", ""),
                    violation.get("line_number", 0),
                    violation.get("type", ""),
                    violation.get("severity", ""),
                    violation.get("description", ""),
                    violation.get("weight", 1),
                    "Connascence",
                ]
            )

        # NASA violations
        for violation in analysis_result.nasa_violations:
            writer.writerow(
                [
                    "",  # file_path
                    "",  # line_number
                    violation.get("rule_id", ""),
                    violation.get("severity", ""),
                    violation.get("rule_title", ""),
                    1,  # weight
                    "NASA",
                ]
            )

        return output.getvalue()

    def _generate_xml_report(self, analysis_result: UnifiedAnalysisResult, options: Dict) -> str:
        """Generate XML report for enterprise integration."""
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<connascence-report>
    <metadata>
        <project>{Path(analysis_result.project_path).name}</project>
        <timestamp>{analysis_result.timestamp}</timestamp>
        <policy>{analysis_result.policy_preset}</policy>
        <files-analyzed>{analysis_result.files_analyzed}</files-analyzed>
        <analysis-duration-ms>{analysis_result.analysis_duration_ms}</analysis-duration-ms>
    </metadata>

    <quality-metrics>
        <overall-score>{analysis_result.overall_quality_score}</overall-score>
        <connascence-index>{analysis_result.connascence_index}</connascence-index>
        <nasa-compliance>{analysis_result.nasa_compliance_score}</nasa-compliance>
        <duplication-score>{analysis_result.duplication_score}</duplication-score>
    </quality-metrics>

    <violation-summary>
        <total>{analysis_result.total_violations}</total>
        <critical>{analysis_result.critical_count}</critical>
        <high>{analysis_result.high_count}</high>
        <medium>{analysis_result.medium_count}</medium>
        <low>{analysis_result.low_count}</low>
    </violation-summary>

    <violations>
"""

        for violation in analysis_result.connascence_violations[:10]:  # Limit for brevity
            xml_content += f"""        <violation>
            <type>{violation.get('type', '')}</type>
            <severity>{violation.get('severity', '')}</severity>
            <file>{violation.get('file_path', '')}</file>
            <line>{violation.get('line_number', 0)}</line>
            <description>{violation.get('description', '')}</description>
        </violation>
"""

        xml_content += """    </violations>
</connascence-report>"""

        return xml_content

    def _generate_summary_report(self, analysis_result: UnifiedAnalysisResult, options: Dict) -> str:
        """Generate executive summary report."""

        # Calculate quality rating
        score = analysis_result.overall_quality_score
        if score >= 0.9:
            quality_rating = "EXCELLENT"
        elif score >= 0.8:
            quality_rating = "GOOD"
        elif score >= 0.7:
            quality_rating = "FAIR"
        else:
            quality_rating = "NEEDS IMPROVEMENT"

        summary = f"""EXECUTIVE SUMMARY - CONNASCENCE ANALYSIS
=============================================

Project: {Path(analysis_result.project_path).name}
Analysis Date: {analysis_result.timestamp}

OVERALL ASSESSMENT: {quality_rating} ({score:.3f}/1.000)

KEY METRICS:
- Files Analyzed: {analysis_result.files_analyzed}
- Total Violations: {analysis_result.total_violations}
- Critical Issues: {analysis_result.critical_count}
- NASA Compliance: {analysis_result.nasa_compliance_score:.3f}

PRIORITY ACTIONS:
"""

        for i, fix in enumerate(analysis_result.priority_fixes[:3], 1):
            summary += f"{i}. {fix}\n"

        summary += "\nRECOMMENDATION: "
        if analysis_result.critical_count > 0:
            summary += "Address critical violations immediately before deployment."
        elif analysis_result.high_count > 5:
            summary += "Focus on reducing high-severity connascence violations."
        else:
            summary += "Continue maintaining good code quality practices."

        return summary

    # Helper methods for chart data and legacy conversion

    def _create_severity_chart_data(self, analysis_result: UnifiedAnalysisResult) -> Dict:
        """Create chart data for severity distribution."""
        return {
            "labels": ["Critical", "High", "Medium", "Low"],
            "data": [
                analysis_result.critical_count,
                analysis_result.high_count,
                analysis_result.medium_count,
                analysis_result.low_count,
            ],
        }

    def _create_file_chart_data(self, analysis_result: UnifiedAnalysisResult) -> Dict:
        """Create chart data for file distribution."""
        file_counts = {}
        for violation in analysis_result.connascence_violations:
            file_path = Path(violation.get("file_path", "")).name
            file_counts[file_path] = file_counts.get(file_path, 0) + 1

        # Get top 10 files
        sorted_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {"labels": [item[0] for item in sorted_files], "data": [item[1] for item in sorted_files]}

    def _create_type_chart_data(self, analysis_result: UnifiedAnalysisResult) -> Dict:
        """Create chart data for violation type distribution."""
        type_counts = {}
        for violation in analysis_result.connascence_violations:
            viol_type = violation.get("type", "unknown")
            type_counts[viol_type] = type_counts.get(viol_type, 0) + 1

        return {"labels": list(type_counts.keys()), "data": list(type_counts.values())}

    def _create_trend_chart_data(self, analysis_result: UnifiedAnalysisResult) -> Dict:
        """Create placeholder trend data (would be populated by historical tracking)."""
        return {
            "labels": ["1 week ago", "5 days ago", "3 days ago", "1 day ago", "Today"],
            "data": [
                analysis_result.total_violations + 5,
                analysis_result.total_violations + 3,
                analysis_result.total_violations + 2,
                analysis_result.total_violations + 1,
                analysis_result.total_violations,
            ],
        }

    def _create_correlation_chart_data(self, correlations: List) -> Dict:
        """Create chart data for correlation network visualization."""
        if not correlations:
            return {"nodes": [], "edges": []}

        # Create nodes for each analyzer type
        analyzer_types = set()
        for correlation in correlations:
            analyzer_types.add(correlation.get("analyzer1", "unknown"))
            analyzer_types.add(correlation.get("analyzer2", "unknown"))

        nodes = [{"id": analyzer, "label": analyzer.replace("_", " ").title()} for analyzer in analyzer_types]

        # Create edges for correlations
        edges = []
        for i, correlation in enumerate(correlations):
            edges.append(
                {
                    "id": f"correlation_{i}",
                    "source": correlation.get("analyzer1", "unknown"),
                    "target": correlation.get("analyzer2", "unknown"),
                    "weight": correlation.get("correlation_score", 0.5),
                    "label": f"{correlation.get('correlation_score', 0):.2f}",
                    "description": correlation.get("description", ""),
                }
            )

        return {"nodes": nodes, "edges": edges}

    def _extract_phase_timings(self, audit_trail: List) -> Dict:
        """Extract phase timing information from audit trail."""
        phase_timings = {}

        for entry in audit_trail:
            phase = entry.get("phase", "unknown")
            if "started" in entry:
                phase_timings[phase] = {"started": entry["started"]}
            elif "completed" in entry and phase in phase_timings:
                phase_timings[phase]["completed"] = entry["completed"]
                phase_timings[phase]["duration_info"] = entry

        return phase_timings

    def _create_correlation_summary(self, correlations: List) -> Dict:
        """Create summary statistics for correlations."""
        if not correlations:
            return {"total": 0, "high_impact": 0, "categories": {}}

        high_impact_correlations = [c for c in correlations if c.get("correlation_score", 0) > 0.7]
        categories = {}

        for correlation in correlations:
            correlation_type = correlation.get("correlation_type", "general")
            categories[correlation_type] = categories.get(correlation_type, 0) + 1

        return {
            "total": len(correlations),
            "high_impact": len(high_impact_correlations),
            "categories": categories,
            "average_score": sum(c.get("correlation_score", 0) for c in correlations) / len(correlations),
        }

    def _create_hotspot_analysis(self, correlations: List) -> Dict:
        """Analyze hotspot files from correlation data."""
        hotspots = {}

        for correlation in correlations:
            if correlation.get("correlation_type") == "violation_hotspots":
                hotspot_files = correlation.get("hotspot_files", [])
                hotspot_details = correlation.get("hotspot_details", {})

                for file_path in hotspot_files:
                    if file_path in hotspot_details:
                        hotspots[file_path] = {
                            "violations": hotspot_details[file_path],
                            "priority": correlation.get("priority", "medium"),
                            "remediation_impact": correlation.get("remediation_impact", "unknown"),
                        }

        # Sort by total violation count
        sorted_hotspots = dict(sorted(hotspots.items(), key=lambda x: sum(x[1]["violations"].values()), reverse=True))

        return {
            "count": len(sorted_hotspots),
            "files": sorted_hotspots,
            "top_hotspot": next(iter(sorted_hotspots.keys())) if sorted_hotspots else None,
        }

    def _convert_to_legacy_format(self, analysis_result: UnifiedAnalysisResult) -> Any:
        """Convert UnifiedAnalysisResult to legacy format for existing reporters."""

        # This would create a mock AnalysisResult object that existing reporters expect
        # For now, return a simple dict that should work with most reporters

        class MockAnalysisResult:
            def __init__(self, unified_result):
                self.violations = []

                # Convert violations to legacy format
                for violation in unified_result.connascence_violations:
                    mock_violation = MockViolation(violation)
                    self.violations.append(mock_violation)

                self.project_root = unified_result.project_path
                self.timestamp = unified_result.timestamp
                self.total_files_analyzed = unified_result.files_analyzed
                self.analysis_duration_ms = unified_result.analysis_duration_ms
                self.policy_preset = unified_result.policy_preset
                self.summary_metrics = {
                    "total_violations": unified_result.total_violations,
                    "critical_count": unified_result.critical_count,
                    "high_count": unified_result.high_count,
                    "medium_count": unified_result.medium_count,
                    "low_count": unified_result.low_count,
                }

        class MockViolation:
            def __init__(self, violation_dict):
                self.id = violation_dict.get("id", "")
                self.type_value = violation_dict.get("type", "unknown")
                self.severity_value = violation_dict.get("severity", "medium")
                self.description = violation_dict.get("description", "")
                self.file_path = violation_dict.get("file_path", "")
                self.line_number = violation_dict.get("line_number", 0)
                self.column = 0  # Default
                self.end_line = None
                self.end_column = None
                self.weight = violation_dict.get("weight", 1)
                self.locality = "local"  # Default
                self.function_name = None
                self.class_name = None
                self.recommendation = ""
                self.context = {}
                self.code_snippet = None

                # Create mock type and severity objects
                self.type = MockType(self.type_value)
                self.severity = MockSeverity(self.severity_value)

        class MockType:
            def __init__(self, value):
                self.value = value

        class MockSeverity:
            def __init__(self, value):
                self.value = value

        return MockAnalysisResult(analysis_result)


# Singleton instance for global access
reporting_coordinator = UnifiedReportingCoordinator()
