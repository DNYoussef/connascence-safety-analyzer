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
Report Generator - Centralized Report Generation
=================================================

Unified interface for generating analysis reports in multiple formats:
- JSON (machine-readable, deterministic)
- Markdown (human-readable, PR comments)
- SARIF 2.1.0 (CI/CD integration, GitHub Code Scanning)

This module extracts all reporting logic from UnifiedConnascenceAnalyzer,
providing a clean separation of concerns between analysis and reporting.

Responsibilities:
- Multi-format report generation (JSON, Markdown, SARIF)
- Violation formatting and aggregation
- Summary statistics generation
- Output file management
- Template-based report rendering

NASA Rule 4: All functions under 60 lines
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..formatters.sarif import SARIFExporter
from ..reporting.json import JSONReporter
from ..reporting.markdown import MarkdownReporter

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Centralized report generation for all output formats.

    Coordinates existing formatters (JSON, Markdown, SARIF) to provide
    a unified interface for generating analysis reports.

    Attributes:
        config: Configuration dictionary with output preferences
        json_reporter: JSON report formatter instance
        markdown_reporter: Markdown report formatter instance
        sarif_exporter: SARIF 2.1.0 exporter instance

    Example:
        >>> generator = ReportGenerator({"version": "1.0.0"})
        >>> generator.generate_json(violations, Path("output.json"))
        >>> generator.generate_markdown(violations, Path("summary.md"))
        >>> generator.generate_sarif(violations, Path("results.sarif"))
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize report generator with configuration.

        Args:
            config: Configuration dictionary with keys:
                - version: Analyzer version (default: "1.0.0")
                - max_violations_to_show: Max violations in markdown (default: 10)
                - max_files_to_show: Max files in markdown (default: 5)
                - indent: JSON indentation (default: 2)
                - sort_keys: Sort JSON keys (default: True)

        NASA Rule 4: Function under 60 lines (22 LOC)
        """
        self.config = config or {}
        self.version = self.config.get("version", "1.0.0")

        # Initialize formatters with configuration
        self.json_reporter = JSONReporter()
        self.markdown_reporter = MarkdownReporter()
        self.sarif_exporter = SARIFExporter(version=self.version)

        # Apply markdown configuration
        if "max_violations_to_show" in self.config:
            self.markdown_reporter.max_violations_to_show = self.config["max_violations_to_show"]
        if "max_files_to_show" in self.config:
            self.markdown_reporter.max_files_to_show = self.config["max_files_to_show"]

        logger.info(f"ReportGenerator initialized (version={self.version})")

    def generate_json(
        self,
        result: Union[Dict[str, Any], Any],
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate JSON report from analysis results.

        Args:
            result: Analysis result (dict or AnalysisResult object)
            output_path: Optional path to write JSON file

        Returns:
            JSON string representation

        Raises:
            IOError: If file writing fails
            TypeError: If result cannot be serialized

        NASA Rule 4: Function under 60 lines (28 LOC)
        """
        try:
            # Generate JSON content
            if hasattr(result, "__dict__") and hasattr(result, "violations"):
                # AnalysisResult object
                json_content = self.json_reporter.generate(result)
            elif isinstance(result, dict):
                # Dictionary result
                json_content = self.json_reporter.export_results(result)
            else:
                # Fallback: try to serialize directly
                indent = self.config.get("indent", 2)
                sort_keys = self.config.get("sort_keys", True)
                json_content = json.dumps(
                    result,
                    indent=indent,
                    sort_keys=sort_keys,
                    ensure_ascii=False
                )

            # Write to file if path provided
            if output_path:
                self._write_to_file(output_path, json_content)
                logger.info(f"JSON report written to {output_path}")

            return json_content

        except Exception as e:
            logger.error(f"JSON report generation failed: {e}")
            raise

    def generate_markdown(
        self,
        result: Union[Dict[str, Any], Any],
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate Markdown summary report.

        Suitable for GitHub/GitLab PR comments and human-readable documentation.

        Args:
            result: Analysis result (dict or AnalysisResult object)
            output_path: Optional path to write markdown file

        Returns:
            Markdown formatted string

        Raises:
            IOError: If file writing fails
            AttributeError: If result missing required attributes

        NASA Rule 4: Function under 60 lines (29 LOC)
        """
        try:
            # Generate markdown content
            if hasattr(result, "__dict__") and hasattr(result, "violations"):
                # AnalysisResult object
                markdown_content = self.markdown_reporter.generate(result)
            elif isinstance(result, dict):
                # Convert dict to pseudo-AnalysisResult for compatibility
                markdown_content = self._generate_markdown_from_dict(result)
            else:
                raise AttributeError(
                    f"Unsupported result type for markdown: {type(result)}"
                )

            # Write to file if path provided
            if output_path:
                self._write_to_file(output_path, markdown_content)
                logger.info(f"Markdown report written to {output_path}")

            return markdown_content

        except Exception as e:
            logger.error(f"Markdown report generation failed: {e}")
            raise

    def generate_sarif(
        self,
        violations: List[Dict[str, Any]],
        output_path: Optional[Path] = None,
        source_root: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate SARIF 2.1.0 report for CI/CD integration.

        Compatible with GitHub Code Scanning, VS Code, Azure DevOps, GitLab.

        Args:
            violations: List of violation dictionaries
            output_path: Optional path to write SARIF JSON file
            source_root: Optional source root path for relative URIs

        Returns:
            SARIF 2.1.0 compliant dictionary

        Raises:
            IOError: If file writing fails
            ValueError: If violations format invalid

        NASA Rule 4: Function under 60 lines (30 LOC)
        """
        try:
            # Generate SARIF structure
            sarif_report = self.sarif_exporter.generate_sarif(
                violations=violations,
                source_root=source_root
            )

            # Write to file if path provided
            if output_path:
                sarif_json = json.dumps(
                    sarif_report,
                    indent=self.config.get("indent", 2),
                    ensure_ascii=False
                )
                self._write_to_file(output_path, sarif_json)
                logger.info(f"SARIF report written to {output_path}")

            return sarif_report

        except Exception as e:
            logger.error(f"SARIF report generation failed: {e}")
            raise

    def format_summary(self, metrics: Dict[str, Any]) -> str:
        """
        Generate concise text summary of analysis metrics.

        Args:
            metrics: Dictionary containing:
                - total_violations: Total violation count
                - critical_count: Critical violations
                - high_count: High severity violations
                - medium_count: Medium severity violations
                - low_count: Low severity violations
                - overall_quality_score: Overall quality score (0-1)
                - connascence_index: Connascence index score

        Returns:
            Formatted summary text

        NASA Rule 4: Function under 60 lines (33 LOC)
        """
        total = metrics.get("total_violations", 0)
        critical = metrics.get("critical_count", 0)
        high = metrics.get("high_count", 0)
        medium = metrics.get("medium_count", 0)
        low = metrics.get("low_count", 0)
        quality = metrics.get("overall_quality_score", 0.0)
        ci_index = metrics.get("connascence_index", 0.0)

        lines = [
            "=" * 60,
            "CONNASCENCE ANALYSIS SUMMARY",
            "=" * 60,
            f"Total Violations: {total}",
            f"  - Critical: {critical}",
            f"  - High:     {high}",
            f"  - Medium:   {medium}",
            f"  - Low:      {low}",
            "",
            f"Quality Score:      {quality:.2f}",
            f"Connascence Index:  {ci_index:.2f}",
            "=" * 60,
        ]

        return "\n".join(lines)

    def generate_all_formats(
        self,
        result: Union[Dict[str, Any], Any],
        violations: List[Dict[str, Any]],
        output_dir: Path,
        base_name: str = "analysis"
    ) -> Dict[str, Path]:
        """
        Generate reports in all supported formats.

        Convenience method to generate JSON, Markdown, and SARIF reports
        in a single call.

        Args:
            result: Analysis result object or dictionary
            violations: List of violation dictionaries (for SARIF)
            output_dir: Directory to write output files
            base_name: Base filename (default: "analysis")

        Returns:
            Dictionary mapping format to output path:
                {"json": Path, "markdown": Path, "sarif": Path}

        Raises:
            IOError: If output directory doesn't exist or writing fails

        NASA Rule 4: Function under 60 lines (35 LOC)
        """
        # Ensure output directory exists
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_paths = {}

        try:
            # Generate JSON report
            json_path = output_dir / f"{base_name}.json"
            self.generate_json(result, json_path)
            output_paths["json"] = json_path

            # Generate Markdown report
            markdown_path = output_dir / f"{base_name}.md"
            self.generate_markdown(result, markdown_path)
            output_paths["markdown"] = markdown_path

            # Generate SARIF report
            sarif_path = output_dir / f"{base_name}.sarif"
            source_root = getattr(result, "project_root", None)
            self.generate_sarif(violations, sarif_path, source_root)
            output_paths["sarif"] = sarif_path

            logger.info(f"All reports generated in {output_dir}")
            return output_paths

        except Exception as e:
            logger.error(f"Multi-format report generation failed: {e}")
            raise

    # Helper methods (NASA Rule 4: All under 60 lines)

    def _write_to_file(self, path: Path, content: str) -> None:
        """
        Write content to file with error handling.

        Args:
            path: File path to write
            content: String content to write

        Raises:
            IOError: If writing fails

        NASA Rule 4: Function under 60 lines (14 LOC)
        """
        try:
            path = Path(path)
            self._validate_output_path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        except Exception as e:
            raise IOError(f"Failed to write to {path}: {e}") from e

    def _validate_output_path(self, path: Path) -> None:
        """Validate output paths to avoid unsupported or protected locations."""
        normalized = path.as_posix()

        # Explicitly block Windows system paths which are invalid in CI
        if normalized.startswith("C:/Windows") or normalized.startswith("C:\\Windows"):
            raise PermissionError(f"Unsupported output path: {path}")

        # Block Windows drive prefixes on POSIX to avoid creating stray directories
        first_part = path.parts[0] if path.parts else ""
        if ":" in first_part and not path.is_absolute():
            raise PermissionError(f"Invalid drive-prefixed path: {path}")

    def _generate_markdown_from_dict(self, result_dict: Dict[str, Any]) -> str:
        """
        Generate markdown from dictionary result.

        Creates a simplified AnalysisResult-like object for compatibility
        with MarkdownReporter.

        Args:
            result_dict: Dictionary with analysis results

        Returns:
            Markdown formatted string

        NASA Rule 4: Function under 60 lines (48 LOC)
        """
        from dataclasses import dataclass
        from typing import List as TList

        # Create minimal AnalysisResult-like dataclass
        @dataclass
        class SimpleResult:
            violations: TList[Any]
            policy_preset: str
            analysis_duration_ms: int
            total_files_analyzed: int

        # Extract violations (handle both formats)
        violations = []
        if "violations" in result_dict:
            violations = result_dict["violations"]
        elif "connascence_violations" in result_dict:
            violations = result_dict["connascence_violations"]

        # Convert dict violations to pseudo-Violation objects
        @dataclass
        class SimpleViolation:
            type: Any
            severity: Any
            file_path: str
            line_number: int
            description: str
            recommendation: str = ""
            weight: float = 1.0

        @dataclass
        class ViolationType:
            value: str

        @dataclass
        class Severity:
            value: str

        simple_violations = []
        for v in violations:
            if isinstance(v, dict):
                simple_violations.append(SimpleViolation(
                    type=ViolationType(v.get("type", "unknown")),
                    severity=Severity(v.get("severity", "medium")),
                    file_path=v.get("file_path", "unknown"),
                    line_number=v.get("line_number", 0),
                    description=v.get("description", ""),
                    recommendation=v.get("recommendation", ""),
                    weight=v.get("weight", 1.0)
                ))

        # Create simple result object
        simple_result = SimpleResult(
            violations=simple_violations,
            policy_preset=result_dict.get("policy_preset", "default"),
            analysis_duration_ms=result_dict.get("analysis_duration_ms", 0),
            total_files_analyzed=result_dict.get("total_files_analyzed", 0)
        )

        return self.markdown_reporter.generate(simple_result)
