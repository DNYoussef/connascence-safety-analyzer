"""
Unified Quality Gate
Integrates Connascence Analysis, NASA Standards, and Clarity Linter

This module provides a unified interface for running all quality checks
and producing consolidated reports with actionable insights.
"""

from dataclasses import dataclass, field
from datetime import datetime
import json
import logging
from pathlib import Path
import sys
from typing import Dict, List, Optional

import yaml

# Import ClarityLinter for integration
from analyzer.clarity_linter import ClarityLinter
from analyzer.connascence_analyzer import ConnascenceAnalyzer
from analyzer.nasa_engine.nasa_analyzer import NASAAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class Violation:
    """Represents a quality violation"""

    rule_id: str
    message: str
    file: str
    line: int
    column: Optional[int] = None
    severity: str = "medium"
    category: str = "quality"
    code_snippet: Optional[str] = None
    fix_suggestion: Optional[str] = None
    nasa_mapping: Optional[str] = None
    connascence_type: Optional[str] = None
    source_analyzer: str = "unknown"

    def to_dict(self) -> Dict:
        """Convert violation to dictionary"""
        return {
            "rule_id": self.rule_id,
            "message": self.message,
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "severity": self.severity,
            "category": self.category,
            "code_snippet": self.code_snippet,
            "fix_suggestion": self.fix_suggestion,
            "nasa_mapping": self.nasa_mapping,
            "connascence_type": self.connascence_type,
            "source_analyzer": self.source_analyzer,
        }


@dataclass
class AnalysisResult:
    """Results from quality analysis"""

    violations: List[Violation] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    metrics: Dict = field(default_factory=dict)
    nasa_compliance_score: float = 0.0
    clarity_score: float = 0.0
    connascence_score: float = 0.0
    overall_score: float = 0.0

    def to_dict(self) -> Dict:
        """Convert result to dictionary"""
        return {
            "violations": [v.to_dict() for v in self.violations],
            "metadata": self.metadata,
            "metrics": self.metrics,
            "scores": {
                "nasa_compliance": self.nasa_compliance_score,
                "clarity": self.clarity_score,
                "connascence": self.connascence_score,
                "overall": self.overall_score,
            },
        }


class UnifiedQualityGate:
    """
    Unified Quality Gate that orchestrates multiple analyzers:
    - Connascence Analyzer
    - NASA Standards Checker
    - Clarity Linter

    Produces consolidated reports with unified scoring.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the unified quality gate.

        Args:
            config_path: Path to quality_gate.config.yaml
        """
        self.config_path = Path(config_path) if config_path else None
        self.config = self._load_config()
        self.results = AnalysisResult()

        # Initialize ClarityLinter (finds its own config automatically)
        try:
            self.clarity_linter = ClarityLinter()
            logger.info("[UnifiedQualityGate] ClarityLinter initialized successfully")
        except Exception as e:
            logger.warning("[UnifiedQualityGate] Failed to initialize ClarityLinter: %s", e)
            self.clarity_linter = None

    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        if self.config_path and self.config_path.exists():
            with open(self.config_path) as f:
                return yaml.safe_load(f)
        return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            "analyzers": {
                "clarity_linter": {"enabled": True},
                "connascence_analyzer": {"enabled": True},
                "nasa_standards": {"enabled": True},
            },
            "thresholds": {
                "max_critical": 0,
                "max_high": 5,
                "max_medium": 10,
                "max_low": 20,
            },
        }

    def analyze_project(
        self,
        project_path: str,
        fail_on: str = "high",
        output_format: str = "json",
    ) -> AnalysisResult:
        """
        Analyze entire project with all enabled analyzers.

        Args:
            project_path: Path to project root
            fail_on: Severity level to fail on (critical, high, medium, low, any)
            output_format: Output format (json, sarif, markdown, html)

        Returns:
            AnalysisResult with all violations and metrics
        """
        project_path = Path(project_path)
        if not project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")

        self.results.metadata = {
            "project_path": str(project_path),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "config": self.config.get("metadata", {}),
        }

        # Run analyzers
        if self.config["analyzers"]["clarity_linter"]["enabled"]:
            self._run_clarity_linter(project_path)

        if self.config["analyzers"]["connascence_analyzer"]["enabled"]:
            self._run_connascence_analyzer(project_path)

        if self.config["analyzers"]["nasa_standards"]["enabled"]:
            self._run_nasa_standards(project_path)

        # Calculate metrics and scores
        self._calculate_metrics()
        self._calculate_scores()

        # Check if quality gate passes
        gate_passed = self._check_quality_gate(fail_on)
        self.results.metadata["quality_gate_passed"] = gate_passed

        return self.results

    def _run_clarity_linter(self, project_path: Path) -> None:
        """
        Run Clarity Linter analysis with real implementation.

        Integrates the ClarityLinter orchestrator which coordinates:
        - ThinHelperDetector
        - UselessIndirectionDetector
        - CallChainDepthDetector
        - PoorNamingDetector
        - CommentIssuesDetector
        """
        logger.info("[Clarity Linter] Starting analysis...")

        if not self.clarity_linter:
            logger.warning("[Clarity Linter] Skipped - not initialized")
            return

        try:
            # Run actual clarity linter analysis
            clarity_violations_raw = self.clarity_linter.analyze_project(project_path)

            # Convert ClarityViolation objects to Violation objects
            for cv in clarity_violations_raw:
                violation = Violation(
                    rule_id=cv.rule_id,
                    message=cv.message,
                    file=str(cv.file_path),
                    line=cv.line_number,
                    column=cv.column_number,
                    severity=cv.severity,
                    category=cv.category,
                    code_snippet=cv.code_snippet,
                    fix_suggestion=cv.fix_suggestion,
                    source_analyzer="clarity_linter",
                )
                self.results.violations.append(violation)

            # Get summary metrics
            summary = self.clarity_linter.get_summary()
            logger.info("[Clarity Linter] Analyzed %s files", summary["total_files_analyzed"])
            logger.info("[Clarity Linter] Found %s violations", summary["total_violations_found"])

        except Exception as e:
            logger.error("[Clarity Linter] Error during analysis: %s", e)
            import traceback
            traceback.print_exc()

    def _run_connascence_analyzer(self, project_path: Path) -> None:
        """
        Run Connascence Analyzer.
        """
        logger.info("[Connascence Analyzer] Starting analysis...")

        try:
            analyzer = ConnascenceAnalyzer()
            violations = analyzer.analyze_directory(project_path)
            for violation in violations:
                self.results.violations.append(
                    Violation(
                        rule_id=getattr(violation, "rule_id", None) or getattr(violation, "type", "connascence"),
                        message=getattr(violation, "description", ""),
                        file=getattr(violation, "file_path", ""),
                        line=getattr(violation, "line_number", 0),
                        column=getattr(violation, "column", None),
                        severity=getattr(violation, "severity", "medium"),
                        category="design",
                        connascence_type=getattr(violation, "connascence_type", None)
                        or getattr(violation, "type", None),
                        fix_suggestion=getattr(violation, "recommendation", None),
                        source_analyzer="connascence_analyzer",
                    )
                )
            logger.info("[Connascence Analyzer] Found %s violations", len(violations))
        except Exception as e:
            logger.error("[Connascence Analyzer] Analysis failed: %s", e)

    def _run_nasa_standards(self, project_path: Path) -> None:
        """
        Run NASA Standards compliance check.
        """
        logger.info("[NASA Standards] Starting compliance check...")

        try:
            analyzer = NASAAnalyzer()
            nasa_violations = []
            for file_path in project_path.rglob("*.py"):
                nasa_violations.extend(analyzer.analyze_file(str(file_path)))

            for violation in nasa_violations:
                self.results.violations.append(
                    Violation(
                        rule_id=getattr(violation, "rule_id", None) or getattr(violation, "type", "nasa_rule"),
                        message=getattr(violation, "description", ""),
                        file=getattr(violation, "file_path", ""),
                        line=getattr(violation, "line_number", 0),
                        column=getattr(violation, "column", None),
                        severity=getattr(violation, "severity", "medium"),
                        category="reliability",
                        nasa_mapping=getattr(violation, "rule_id", None),
                        fix_suggestion=getattr(violation, "recommendation", None),
                        source_analyzer="nasa_standards",
                    )
                )
            logger.info("[NASA Standards] Found %s violations", len(nasa_violations))
        except Exception as e:
            logger.error("[NASA Standards] Analysis failed: %s", e)

    def _calculate_metrics(self) -> None:
        """Calculate quality metrics from violations"""
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
        }

        category_counts = {}
        analyzer_counts = {}
        files_affected = set()

        for violation in self.results.violations:
            severity_counts[violation.severity] = (
                severity_counts.get(violation.severity, 0) + 1
            )
            category_counts[violation.category] = (
                category_counts.get(violation.category, 0) + 1
            )
            analyzer_counts[violation.source_analyzer] = (
                analyzer_counts.get(violation.source_analyzer, 0) + 1
            )
            files_affected.add(violation.file)

        self.results.metrics = {
            "total_violations": len(self.results.violations),
            "severity_counts": severity_counts,
            "category_counts": category_counts,
            "analyzer_counts": analyzer_counts,
            "files_affected": len(files_affected),
        }

    def _calculate_scores(self) -> None:
        """
        Calculate normalized quality scores (0-100 scale).

        Scoring algorithm:
        - Start with 100 points
        - Deduct points based on violation severity
        - Critical: -10 points each
        - High: -5 points each
        - Medium: -2 points each
        - Low: -1 point each
        """
        base_score = 100.0
        penalties = {"critical": 10, "high": 5, "medium": 2, "low": 1, "info": 0}

        clarity_violations = [
            v for v in self.results.violations if v.source_analyzer == "clarity_linter"
        ]
        connascence_violations = [
            v
            for v in self.results.violations
            if v.source_analyzer == "connascence_analyzer"
        ]
        nasa_violations = [
            v for v in self.results.violations if v.source_analyzer == "nasa_standards"
        ]

        # Calculate individual scores
        self.results.clarity_score = max(
            0,
            base_score - sum(penalties[v.severity] for v in clarity_violations),
        )

        self.results.connascence_score = max(
            0,
            base_score - sum(penalties[v.severity] for v in connascence_violations),
        )

        self.results.nasa_compliance_score = max(
            0,
            base_score - sum(penalties[v.severity] for v in nasa_violations),
        )

        # Overall score is weighted average
        weights = {"clarity": 0.4, "connascence": 0.3, "nasa": 0.3}

        self.results.overall_score = (
            self.results.clarity_score * weights["clarity"]
            + self.results.connascence_score * weights["connascence"]
            + self.results.nasa_compliance_score * weights["nasa"]
        )

    def _check_quality_gate(self, fail_on: str) -> bool:
        """
        Check if quality gate passes based on fail_on threshold.

        Args:
            fail_on: Severity threshold (critical, high, medium, low, any)

        Returns:
            True if quality gate passes, False otherwise
        """
        severity_order = ["critical", "high", "medium", "low", "info"]
        fail_index = severity_order.index(fail_on)

        counts = self.results.metrics["severity_counts"]
        thresholds = self.config.get("thresholds", {})

        # Check if any severity at or above threshold is exceeded
        for i in range(fail_index + 1):
            severity = severity_order[i]
            count = counts.get(severity, 0)
            threshold = thresholds.get(f"max_{severity}", 0)

            if count > threshold:
                return False

        return True

    def export_sarif(self, output_path: str) -> None:
        """
        Export results in SARIF format for GitHub Code Scanning.

        Merges results from all three analyzers:
        - Clarity Linter
        - Connascence Analyzer
        - NASA Standards

        Args:
            output_path: Path to output SARIF file
        """
        # Group violations by source analyzer
        clarity_violations = [v for v in self.results.violations if v.source_analyzer == "clarity_linter"]
        connascence_violations = [v for v in self.results.violations if v.source_analyzer == "connascence_analyzer"]
        nasa_violations = [v for v in self.results.violations if v.source_analyzer == "nasa_standards"]

        # Create unified SARIF with separate runs for each analyzer
        sarif = {
            "version": "2.1.0",
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "runs": []
        }

        # Add Clarity Linter run if violations exist
        if clarity_violations:
            sarif["runs"].append(self._create_sarif_run(
                "Clarity Linter",
                "1.0.0",
                clarity_violations
            ))

        # Add Connascence Analyzer run if violations exist
        if connascence_violations:
            sarif["runs"].append(self._create_sarif_run(
                "Connascence Analyzer",
                "1.0.0",
                connascence_violations
            ))

        # Add NASA Standards run if violations exist
        if nasa_violations:
            sarif["runs"].append(self._create_sarif_run(
                "NASA Standards Checker",
                "1.0.0",
                nasa_violations
            ))

        # If no violations from any analyzer, create empty unified run
        if not sarif["runs"]:
            sarif["runs"].append(self._create_sarif_run(
                "Unified Quality Gate",
                "1.0.0",
                []
            ))

        Path(output_path).write_text(json.dumps(sarif, indent=2))

    def _create_sarif_run(self, tool_name: str, version: str, violations: List[Violation]) -> Dict:
        """
        Create a SARIF run for a specific analyzer.

        Args:
            tool_name: Name of the analyzer tool
            version: Version of the analyzer
            violations: List of violations from this analyzer

        Returns:
            SARIF run dictionary
        """
        return {
            "tool": {
                "driver": {
                    "name": tool_name,
                    "version": version,
                    "informationUri": "https://github.com/connascence/analyzer",
                }
            },
            "results": [
                {
                    "ruleId": v.rule_id,
                    "message": {"text": v.message},
                    "level": self._sarif_level(v.severity),
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {"uri": v.file},
                                "region": {
                                    "startLine": v.line,
                                    "startColumn": v.column or 1,
                                },
                            }
                        }
                    ],
                    "properties": {
                        "category": v.category,
                        "fix_suggestion": v.fix_suggestion,
                    } if v.fix_suggestion else {"category": v.category}
                }
                for v in violations
            ],
        }

    def _sarif_level(self, severity: str) -> str:
        """Map severity to SARIF level"""
        mapping = {
            "critical": "error",
            "high": "error",
            "medium": "warning",
            "low": "note",
            "info": "note",
        }
        return mapping.get(severity, "warning")

    def export_json(self, output_path: str) -> None:
        """
        Export results in JSON format.

        Args:
            output_path: Path to output JSON file
        """
        Path(output_path).write_text(json.dumps(self.results.to_dict(), indent=2))

    def export_markdown(self, output_path: str) -> None:
        """
        Export results in Markdown format for human readability.

        Args:
            output_path: Path to output Markdown file
        """
        lines = [
            "# Quality Gate Report",
            "",
            f"**Generated:** {self.results.metadata['timestamp']}",
            f"**Project:** {self.results.metadata['project_path']}",
            "",
            "## Summary",
            "",
            f"- **Overall Score:** {self.results.overall_score:.2f}/100",
            f"- **Clarity Score:** {self.results.clarity_score:.2f}/100",
            f"- **Connascence Score:** {self.results.connascence_score:.2f}/100",
            f"- **NASA Compliance:** {self.results.nasa_compliance_score:.2f}/100",
            "",
            f"- **Total Violations:** {self.results.metrics['total_violations']}",
            f"- **Files Affected:** {self.results.metrics['files_affected']}",
            "",
            "### Violations by Severity",
            "",
        ]

        for severity, count in self.results.metrics["severity_counts"].items():
            lines.append(f"- **{severity.title()}:** {count}")

        lines.extend(["", "### Violations by Analyzer", ""])

        for analyzer, count in self.results.metrics["analyzer_counts"].items():
            lines.append(f"- **{analyzer}:** {count}")

        lines.extend(["", "## Violations", ""])

        for i, v in enumerate(self.results.violations[:20], 1):
            lines.extend(
                [
                    f"### {i}. {v.rule_id}: {v.message}",
                    f"- **File:** `{v.file}:{v.line}`",
                    f"- **Severity:** {v.severity}",
                    f"- **Category:** {v.category}",
                    f"- **Analyzer:** {v.source_analyzer}",
                ]
            )

            if v.fix_suggestion:
                lines.append(f"- **Fix:** {v.fix_suggestion}")

            lines.append("")

        if len(self.results.violations) > 20:
            lines.append(
                f"_... and {len(self.results.violations) - 20} more violations_"
            )

        Path(output_path).write_text("\n".join(lines))


def main():
    """CLI entry point for unified quality gate"""
    import argparse

    parser = argparse.ArgumentParser(description="Unified Quality Gate")
    parser.add_argument("project_path", help="Path to project to analyze")
    parser.add_argument(
        "--config",
        default="quality_gate.config.yaml",
        help="Path to config file",
    )
    parser.add_argument(
        "--fail-on",
        choices=["critical", "high", "medium", "low", "any"],
        default="high",
        help="Fail if violations at or above this severity",
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "sarif", "markdown"],
        default="json",
        help="Output format",
    )
    parser.add_argument(
        "--output-file",
        help="Output file path",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    # Run analysis
    gate = UnifiedQualityGate(config_path=args.config)
    results = gate.analyze_project(
        args.project_path,
        fail_on=args.fail_on,
        output_format=args.output_format,
    )

    # Export results
    if args.output_file:
        if args.output_format == "sarif":
            gate.export_sarif(args.output_file)
        elif args.output_format == "markdown":
            gate.export_markdown(args.output_file)
        else:
            gate.export_json(args.output_file)

        logger.info("Results written to: %s", args.output_file)

    # Print summary
    logger.info("\n%s", "=" * 50)
    logger.info("Quality Gate Results")
    logger.info("%s", "=" * 50)
    logger.info("Overall Score: %.2f/100", results.overall_score)
    logger.info("Total Violations: %s", results.metrics["total_violations"])
    logger.info("Quality Gate: %s", "PASSED" if results.metadata["quality_gate_passed"] else "FAILED")
    logger.info("%s", "=" * 50)

    # Exit with appropriate code
    sys.exit(0 if results.metadata["quality_gate_passed"] else 1)


if __name__ == "__main__":
    main()
