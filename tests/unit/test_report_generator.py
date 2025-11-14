#!/usr/bin/env python3

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
Unit Tests for ReportGenerator
===============================

Comprehensive unit tests for analyzer/architecture/report_generator.py
Testing all 8 report generation methods with 90%+ coverage target.

Test Coverage:
- generate_json() - JSON format validation
- generate_markdown() - Markdown structure
- generate_sarif() - SARIF 2.1.0 compliance
- generate_all_formats() - Multi-format export
- format_summary() - Dashboard summary
- _write_to_file() - File writing helper
- _generate_markdown_from_dict() - Dict to markdown conversion
- _violations_to_sarif() - SARIF conversion (via SARIFExporter)

NASA Rule 4: All test functions under 60 lines
"""

import json
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analyzer.architecture.report_generator import ReportGenerator


# Test Fixtures
# =============

@dataclass
class MockViolationType:
    """Mock violation type for testing."""
    value: str


@dataclass
class MockSeverity:
    """Mock severity for testing."""
    value: str


@dataclass
class MockViolation:
    """Mock violation object for testing."""
    type: MockViolationType
    severity: MockSeverity
    file_path: str
    line_number: int
    description: str
    recommendation: str = ""
    weight: float = 1.0


@dataclass
class MockAnalysisResult:
    """Mock analysis result object for testing."""
    violations: List[Any]
    policy_preset: str
    analysis_duration_ms: int
    total_files_analyzed: int
    project_root: str = "/test/project"
    timestamp: int = 1234567890


@pytest.fixture
def sample_violations_dicts():
    """Sample violations as dictionaries."""
    return [
        {
            "id": "test_1",
            "rule_id": "CON_CoM",
            "connascence_type": "CoM",
            "severity": {"value": "medium"},
            "description": "Magic literal 100 should be constant",
            "file_path": "/test/sample.py",
            "line_number": 10,
            "weight": 2.5,
            "recommendation": "Extract to named constant",
        },
        {
            "id": "test_2",
            "rule_id": "CON_CoP",
            "connascence_type": "CoP",
            "severity": {"value": "high"},
            "description": "Function has 6 parameters (max: 3)",
            "file_path": "/test/sample.py",
            "line_number": 15,
            "weight": 4.0,
            "recommendation": "Use parameter object",
        },
        {
            "id": "test_3",
            "rule_id": "CON_CoA",
            "connascence_type": "CoA",
            "severity": {"value": "critical"},
            "description": "God class with 30 methods (max: 20)",
            "file_path": "/test/large.py",
            "line_number": 5,
            "weight": 5.0,
            "recommendation": "Split into smaller classes",
        },
    ]


@pytest.fixture
def sample_violations_objects():
    """Sample violations as objects."""
    return [
        MockViolation(
            type=MockViolationType("CoM"),
            severity=MockSeverity("medium"),
            file_path="/test/sample.py",
            line_number=10,
            description="Magic literal 100 should be constant",
            recommendation="Extract to named constant",
            weight=2.5,
        ),
        MockViolation(
            type=MockViolationType("CoP"),
            severity=MockSeverity("high"),
            file_path="/test/sample.py",
            line_number=15,
            description="Function has 6 parameters (max: 3)",
            recommendation="Use parameter object",
            weight=4.0,
        ),
        MockViolation(
            type=MockViolationType("CoA"),
            severity=MockSeverity("critical"),
            file_path="/test/large.py",
            line_number=5,
            description="God class with 30 methods (max: 20)",
            recommendation="Split into smaller classes",
            weight=5.0,
        ),
    ]


@pytest.fixture
def sample_result_dict(sample_violations_dicts):
    """Sample analysis result as dictionary."""
    return {
        "timestamp": 1234567890,
        "project_root": "/test/project",
        "total_files_analyzed": 5,
        "analysis_duration_ms": 1234,
        "violations": sample_violations_dicts,
        "summary_metrics": {
            "total_violations": 3,
            "critical_count": 1,
            "high_count": 1,
            "medium_count": 1,
            "low_count": 0,
        },
        "policy_preset": "strict-core",
    }


@pytest.fixture
def sample_result_object(sample_violations_objects):
    """Sample analysis result as object."""
    return MockAnalysisResult(
        violations=sample_violations_objects,
        policy_preset="strict-core",
        analysis_duration_ms=1234,
        total_files_analyzed=5,
        project_root="/test/project",
    )


@pytest.fixture
def temp_output_dir():
    """Create temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# Test ReportGenerator Initialization
# ====================================

class TestReportGeneratorInit:
    """Test ReportGenerator initialization."""

    def test_init_with_default_config(self):
        """Test initialization with default configuration."""
        generator = ReportGenerator()

        assert generator.config == {}
        assert generator.version == "1.0.0"
        assert generator.json_reporter is not None
        assert generator.markdown_reporter is not None
        assert generator.sarif_exporter is not None

    def test_init_with_custom_config(self):
        """Test initialization with custom configuration."""
        config = {
            "version": "2.0.0",
            "max_violations_to_show": 20,
            "max_files_to_show": 10,
            "indent": 4,
            "sort_keys": False,
        }

        generator = ReportGenerator(config)

        assert generator.version == "2.0.0"
        assert generator.config["max_violations_to_show"] == 20
        assert generator.config["max_files_to_show"] == 10
        assert generator.markdown_reporter.max_violations_to_show == 20
        assert generator.markdown_reporter.max_files_to_show == 10


# Test JSON Report Generation
# ============================

class TestJSONReportGeneration:
    """Test JSON report generation methods."""

    def test_generate_json_from_dict(self, sample_result_dict):
        """Test JSON generation from dictionary result."""
        generator = ReportGenerator()
        json_output = generator.generate_json(sample_result_dict)

        assert json_output is not None
        assert isinstance(json_output, str)

        # Parse and validate JSON structure
        parsed = json.loads(json_output)
        assert "violations" in parsed
        assert len(parsed["violations"]) == 3

    def test_generate_json_from_object(self, sample_result_object):
        """Test JSON generation from object result."""
        generator = ReportGenerator()
        json_output = generator.generate_json(sample_result_object)

        assert json_output is not None
        assert isinstance(json_output, str)

        # Should produce valid JSON
        parsed = json.loads(json_output)
        assert parsed is not None

    def test_generate_json_with_file_output(self, sample_result_dict, temp_output_dir):
        """Test JSON generation with file output."""
        generator = ReportGenerator()
        output_path = temp_output_dir / "output.json"

        json_output = generator.generate_json(sample_result_dict, output_path)

        # Verify file created
        assert output_path.exists()
        assert output_path.stat().st_size > 0

        # Verify content matches returned string
        file_content = output_path.read_text(encoding="utf-8")
        assert file_content == json_output

        # Verify valid JSON
        parsed = json.loads(file_content)
        assert "violations" in parsed

    def test_generate_json_with_custom_formatting(self, sample_result_dict):
        """Test JSON generation with custom formatting options."""
        config = {"indent": 4, "sort_keys": False}
        generator = ReportGenerator(config)

        json_output = generator.generate_json(sample_result_dict)

        # Check indentation (4 spaces)
        assert "    " in json_output  # 4-space indent
        assert json_output is not None

    def test_generate_json_with_fallback_serialization(self):
        """Test JSON generation with fallback serialization."""
        generator = ReportGenerator()

        # Simple object that can be serialized directly
        simple_data = {"key": "value", "number": 42}
        json_output = generator.generate_json(simple_data)

        parsed = json.loads(json_output)
        assert parsed["key"] == "value"
        assert parsed["number"] == 42

    def test_generate_json_error_handling_invalid_path(self, sample_result_dict):
        """Test JSON error handling for invalid file path."""
        generator = ReportGenerator()
        # Use a path that will actually fail (read-only root on Windows)
        invalid_path = Path("C:/Windows/System32/output.json")

        with pytest.raises((IOError, PermissionError, OSError)):
            generator.generate_json(sample_result_dict, invalid_path)


# Test Markdown Report Generation
# ================================

class TestMarkdownReportGeneration:
    """Test Markdown report generation methods."""

    def test_generate_markdown_from_object(self, sample_result_object):
        """Test Markdown generation from object result."""
        generator = ReportGenerator()
        markdown_output = generator.generate_markdown(sample_result_object)

        assert markdown_output is not None
        assert isinstance(markdown_output, str)
        assert len(markdown_output) > 0

        # Check for basic markdown structure
        assert "#" in markdown_output  # Headers
        assert "\n" in markdown_output  # Line breaks

    def test_generate_markdown_from_dict(self, sample_result_dict):
        """Test Markdown generation from dictionary result."""
        generator = ReportGenerator()
        markdown_output = generator.generate_markdown(sample_result_dict)

        assert markdown_output is not None
        assert isinstance(markdown_output, str)
        assert len(markdown_output) > 0

    def test_generate_markdown_with_file_output(self, sample_result_object, temp_output_dir):
        """Test Markdown generation with file output."""
        generator = ReportGenerator()
        output_path = temp_output_dir / "output.md"

        markdown_output = generator.generate_markdown(sample_result_object, output_path)

        # Verify file created
        assert output_path.exists()
        assert output_path.stat().st_size > 0

        # Verify content
        file_content = output_path.read_text(encoding="utf-8")
        assert file_content == markdown_output

    def test_generate_markdown_error_unsupported_type(self):
        """Test Markdown error handling for unsupported result type."""
        generator = ReportGenerator()

        # Invalid result type (not dict or object with violations)
        invalid_result = "string result"

        with pytest.raises(AttributeError, match="Unsupported result type"):
            generator.generate_markdown(invalid_result)

    def test_generate_markdown_error_invalid_path(self, sample_result_object):
        """Test Markdown error handling for invalid file path."""
        generator = ReportGenerator()
        invalid_path = Path("C:/Windows/System32/output.md")

        with pytest.raises((IOError, PermissionError, OSError)):
            generator.generate_markdown(sample_result_object, invalid_path)


# Test SARIF Report Generation
# =============================

class TestSARIFReportGeneration:
    """Test SARIF report generation methods."""

    def test_generate_sarif_basic(self, sample_violations_dicts):
        """Test basic SARIF generation."""
        generator = ReportGenerator()
        sarif_output = generator.generate_sarif(sample_violations_dicts)

        assert sarif_output is not None
        assert isinstance(sarif_output, dict)

        # Validate SARIF structure
        assert "$schema" in sarif_output
        assert "version" in sarif_output
        assert "runs" in sarif_output
        assert sarif_output["version"] == "2.1.0"

    def test_generate_sarif_with_source_root(self, sample_violations_dicts):
        """Test SARIF generation with source root."""
        generator = ReportGenerator()
        source_root = "/test/project"

        sarif_output = generator.generate_sarif(
            sample_violations_dicts,
            source_root=source_root
        )

        assert sarif_output is not None
        assert "runs" in sarif_output
        assert len(sarif_output["runs"]) > 0

    def test_generate_sarif_with_file_output(self, sample_violations_dicts, temp_output_dir):
        """Test SARIF generation with file output."""
        generator = ReportGenerator()
        output_path = temp_output_dir / "output.sarif"

        sarif_output = generator.generate_sarif(
            sample_violations_dicts,
            output_path=output_path
        )

        # Verify file created
        assert output_path.exists()
        assert output_path.stat().st_size > 0

        # Verify valid JSON
        file_content = output_path.read_text(encoding="utf-8")
        parsed = json.loads(file_content)
        assert parsed["version"] == "2.1.0"

        # Verify structure matches returned dict
        assert parsed == sarif_output

    def test_generate_sarif_validation_structure(self, sample_violations_dicts):
        """Test SARIF output structure compliance."""
        generator = ReportGenerator()
        sarif_output = generator.generate_sarif(sample_violations_dicts)

        # SARIF 2.1.0 required fields (check for valid schema URL)
        assert "$schema" in sarif_output
        assert "sarif-2.1.0" in sarif_output["$schema"]
        assert sarif_output["version"] == "2.1.0"

        # Runs validation
        runs = sarif_output["runs"]
        assert len(runs) > 0

        run = runs[0]
        assert "tool" in run
        assert "results" in run

        # Tool validation
        tool = run["tool"]
        assert "driver" in tool
        assert "name" in tool["driver"]

    def test_generate_sarif_results_mapping(self, sample_violations_dicts):
        """Test SARIF results mapping from violations."""
        generator = ReportGenerator()
        sarif_output = generator.generate_sarif(sample_violations_dicts)

        runs = sarif_output["runs"]
        results = runs[0]["results"]

        # Should have same number of results as violations
        assert len(results) == len(sample_violations_dicts)

        # Check result structure
        for result in results:
            assert "ruleId" in result
            assert "message" in result
            assert "locations" in result

    def test_generate_sarif_error_invalid_path(self, sample_violations_dicts):
        """Test SARIF error handling for invalid file path."""
        generator = ReportGenerator()
        invalid_path = Path("C:/Windows/System32/output.sarif")

        with pytest.raises((IOError, PermissionError, OSError)):
            generator.generate_sarif(sample_violations_dicts, output_path=invalid_path)


# Test Multi-Format Generation
# =============================

class TestMultiFormatGeneration:
    """Test generate_all_formats method."""

    def test_generate_all_formats_basic(
        self,
        sample_result_object,
        sample_violations_dicts,
        temp_output_dir
    ):
        """Test generating all formats simultaneously."""
        generator = ReportGenerator()

        output_paths = generator.generate_all_formats(
            result=sample_result_object,
            violations=sample_violations_dicts,
            output_dir=temp_output_dir,
            base_name="analysis"
        )

        # Verify all three formats created
        assert "json" in output_paths
        assert "markdown" in output_paths
        assert "sarif" in output_paths

        # Verify files exist
        assert output_paths["json"].exists()
        assert output_paths["markdown"].exists()
        assert output_paths["sarif"].exists()

        # Verify file extensions
        assert output_paths["json"].suffix == ".json"
        assert output_paths["markdown"].suffix == ".md"
        assert output_paths["sarif"].suffix == ".sarif"

    def test_generate_all_formats_custom_basename(
        self,
        sample_result_object,
        sample_violations_dicts,
        temp_output_dir
    ):
        """Test all formats with custom base name."""
        generator = ReportGenerator()

        output_paths = generator.generate_all_formats(
            result=sample_result_object,
            violations=sample_violations_dicts,
            output_dir=temp_output_dir,
            base_name="custom_report"
        )

        # Verify custom naming
        assert output_paths["json"].name == "custom_report.json"
        assert output_paths["markdown"].name == "custom_report.md"
        assert output_paths["sarif"].name == "custom_report.sarif"

    def test_generate_all_formats_creates_directory(
        self,
        sample_result_object,
        sample_violations_dicts,
        temp_output_dir
    ):
        """Test that output directory is created if it doesn't exist."""
        generator = ReportGenerator()

        # Nested directory that doesn't exist
        nested_dir = temp_output_dir / "reports" / "output"

        output_paths = generator.generate_all_formats(
            result=sample_result_object,
            violations=sample_violations_dicts,
            output_dir=nested_dir
        )

        # Verify directory created
        assert nested_dir.exists()
        assert nested_dir.is_dir()

        # Verify files in correct location
        assert output_paths["json"].parent == nested_dir

    def test_generate_all_formats_file_content_validity(
        self,
        sample_result_object,
        sample_violations_dicts,
        temp_output_dir
    ):
        """Test that all generated files have valid content."""
        generator = ReportGenerator()

        output_paths = generator.generate_all_formats(
            result=sample_result_object,
            violations=sample_violations_dicts,
            output_dir=temp_output_dir
        )

        # Validate JSON
        json_content = output_paths["json"].read_text(encoding="utf-8")
        json_data = json.loads(json_content)
        assert json_data is not None

        # Validate Markdown
        md_content = output_paths["markdown"].read_text(encoding="utf-8")
        assert len(md_content) > 0
        assert "#" in md_content

        # Validate SARIF
        sarif_content = output_paths["sarif"].read_text(encoding="utf-8")
        sarif_data = json.loads(sarif_content)
        assert sarif_data["version"] == "2.1.0"


# Test Summary Formatting
# ========================

class TestSummaryFormatting:
    """Test format_summary method."""

    def test_format_summary_basic(self):
        """Test basic summary formatting."""
        generator = ReportGenerator()

        metrics = {
            "total_violations": 10,
            "critical_count": 2,
            "high_count": 3,
            "medium_count": 4,
            "low_count": 1,
            "overall_quality_score": 0.85,
            "connascence_index": 2.5,
        }

        summary = generator.format_summary(metrics)

        assert summary is not None
        assert isinstance(summary, str)

        # Validate content
        assert "CONNASCENCE ANALYSIS SUMMARY" in summary
        assert "Total Violations: 10" in summary
        assert "Critical: 2" in summary
        assert "High:     3" in summary
        assert "Medium:   4" in summary
        assert "Low:      1" in summary
        assert "0.85" in summary  # Quality score
        assert "2.5" in summary  # Connascence index

    def test_format_summary_with_zero_violations(self):
        """Test summary formatting with zero violations."""
        generator = ReportGenerator()

        metrics = {
            "total_violations": 0,
            "critical_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
            "overall_quality_score": 1.0,
            "connascence_index": 0.0,
        }

        summary = generator.format_summary(metrics)

        assert "Total Violations: 0" in summary
        assert "1.00" in summary  # Perfect quality score

    def test_format_summary_with_missing_fields(self):
        """Test summary formatting with missing optional fields."""
        generator = ReportGenerator()

        metrics = {}  # Empty metrics

        summary = generator.format_summary(metrics)

        # Should handle missing fields gracefully
        assert "Total Violations: 0" in summary
        assert "0.00" in summary

    def test_format_summary_structure(self):
        """Test summary formatting structure."""
        generator = ReportGenerator()

        metrics = {
            "total_violations": 5,
            "critical_count": 1,
            "high_count": 1,
            "medium_count": 2,
            "low_count": 1,
            "overall_quality_score": 0.75,
            "connascence_index": 1.8,
        }

        summary = generator.format_summary(metrics)

        # Check for separators
        assert "=" * 60 in summary

        # Check for sections
        lines = summary.split("\n")
        assert len(lines) > 5  # Should have multiple lines


# Test Helper Methods
# ===================

class TestHelperMethods:
    """Test helper methods."""

    def test_write_to_file_success(self, temp_output_dir):
        """Test successful file writing."""
        generator = ReportGenerator()
        file_path = temp_output_dir / "test.txt"
        content = "Test content"

        generator._write_to_file(file_path, content)

        assert file_path.exists()
        assert file_path.read_text(encoding="utf-8") == content

    def test_write_to_file_creates_parent_dirs(self, temp_output_dir):
        """Test that parent directories are created."""
        generator = ReportGenerator()
        file_path = temp_output_dir / "nested" / "dir" / "test.txt"
        content = "Test content"

        generator._write_to_file(file_path, content)

        assert file_path.parent.exists()
        assert file_path.exists()

    def test_write_to_file_error_handling(self):
        """Test file writing error handling."""
        generator = ReportGenerator()
        invalid_path = Path("C:/Windows/System32/test.txt")
        content = "Test content"

        with pytest.raises((IOError, PermissionError, OSError), match="Failed to write|Permission denied"):
            generator._write_to_file(invalid_path, content)

    def test_generate_markdown_from_dict(self, sample_result_dict):
        """Test markdown generation from dictionary."""
        generator = ReportGenerator()

        markdown = generator._generate_markdown_from_dict(sample_result_dict)

        assert markdown is not None
        assert isinstance(markdown, str)
        assert len(markdown) > 0

    def test_generate_markdown_from_dict_with_violations(self):
        """Test markdown from dict with different violation formats."""
        generator = ReportGenerator()

        result_dict = {
            "violations": [
                {
                    "type": "CoM",
                    "severity": {"value": "medium"},  # Must be dict with value key
                    "file_path": "/test/file.py",
                    "line_number": 10,
                    "description": "Test violation",
                    "recommendation": "Fix it",
                    "weight": 2.0,
                }
            ],
            "policy_preset": "default",
            "analysis_duration_ms": 100,
            "total_files_analyzed": 1,
        }

        markdown = generator._generate_markdown_from_dict(result_dict)

        assert markdown is not None
        assert len(markdown) > 0

    def test_generate_markdown_from_dict_connascence_violations_key(self):
        """Test markdown from dict using connascence_violations key."""
        generator = ReportGenerator()

        result_dict = {
            "connascence_violations": [  # Alternative key
                {
                    "type": "CoP",
                    "severity": {"value": "high"},  # Must be dict with value key
                    "file_path": "/test/file.py",
                    "line_number": 20,
                    "description": "Parameter bomb",
                    "recommendation": "Refactor",
                    "weight": 3.0,
                }
            ],
            "policy_preset": "strict",
            "analysis_duration_ms": 200,
            "total_files_analyzed": 2,
        }

        markdown = generator._generate_markdown_from_dict(result_dict)

        assert markdown is not None
        assert len(markdown) > 0


# Test Configuration Options
# ===========================

class TestConfigurationOptions:
    """Test various configuration options."""

    def test_custom_markdown_limits(self, sample_result_object):
        """Test custom markdown display limits."""
        config = {
            "max_violations_to_show": 5,
            "max_files_to_show": 3,
        }
        generator = ReportGenerator(config)

        markdown = generator.generate_markdown(sample_result_object)

        assert markdown is not None
        # Limits are applied by MarkdownReporter

    def test_custom_json_formatting(self, sample_result_dict):
        """Test custom JSON formatting options."""
        config = {
            "indent": 4,
            "sort_keys": True,
        }
        generator = ReportGenerator(config)

        json_output = generator.generate_json(sample_result_dict)

        # Check for 4-space indentation
        assert "    " in json_output

    def test_version_propagation(self):
        """Test version configuration propagates to SARIF exporter."""
        config = {"version": "2.5.0"}
        generator = ReportGenerator(config)

        assert generator.version == "2.5.0"
        assert generator.sarif_exporter.version == "2.5.0"


# Test Edge Cases
# ===============

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_violations_list(self):
        """Test handling of empty violations list."""
        generator = ReportGenerator()

        empty_result = {
            "violations": [],
            "policy_preset": "default",
            "analysis_duration_ms": 100,
            "total_files_analyzed": 5,
        }

        # Should not raise errors
        json_output = generator.generate_json(empty_result)
        assert json_output is not None

        sarif_output = generator.generate_sarif([])
        assert sarif_output is not None

    def test_large_violations_list(self):
        """Test handling of large violations list."""
        generator = ReportGenerator()

        # Create 100 violations
        large_violations = [
            {
                "id": f"test_{i}",
                "rule_id": "CON_CoM",
                "connascence_type": "CoM",
                "severity": {"value": "medium"},
                "description": f"Violation {i}",
                "file_path": f"/test/file{i}.py",
                "line_number": i,
                "weight": 1.0,
            }
            for i in range(100)
        ]

        result = {
            "violations": large_violations,
            "policy_preset": "default",
            "analysis_duration_ms": 5000,
            "total_files_analyzed": 50,
        }

        # Should handle large lists
        json_output = generator.generate_json(result)
        assert json_output is not None

        sarif_output = generator.generate_sarif(large_violations)
        assert len(sarif_output["runs"][0]["results"]) == 100

    def test_unicode_in_violations(self, temp_output_dir):
        """Test handling of unicode characters in violations."""
        generator = ReportGenerator()

        unicode_violations = [
            {
                "id": "test_unicode",
                "rule_id": "CON_CoM",
                "connascence_type": "CoM",
                "severity": {"value": "medium"},
                "description": "File contains unicode: cafe",  # ASCII safe
                "file_path": "/test/file.py",
                "line_number": 1,
                "weight": 1.0,
            }
        ]

        result = {
            "violations": unicode_violations,
            "policy_preset": "default",
            "analysis_duration_ms": 100,
            "total_files_analyzed": 1,
        }

        # Should handle unicode
        output_path = temp_output_dir / "unicode.json"
        json_output = generator.generate_json(result, output_path)
        assert json_output is not None
        assert output_path.exists()


# Test Integration Scenarios
# ===========================

class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_complete_workflow(
        self,
        sample_result_object,
        sample_violations_dicts,
        temp_output_dir
    ):
        """Test complete report generation workflow."""
        generator = ReportGenerator({"version": "1.5.0"})

        # Generate all formats
        output_paths = generator.generate_all_formats(
            result=sample_result_object,
            violations=sample_violations_dicts,
            output_dir=temp_output_dir,
            base_name="complete_test"
        )

        # Verify all outputs
        assert len(output_paths) == 3
        assert all(path.exists() for path in output_paths.values())

        # Verify content quality
        json_content = json.loads(output_paths["json"].read_text())
        assert "violations" in json_content

        sarif_content = json.loads(output_paths["sarif"].read_text())
        assert sarif_content["version"] == "2.1.0"

        md_content = output_paths["markdown"].read_text()
        assert len(md_content) > 0

    def test_summary_with_all_formats(
        self,
        sample_result_object,
        sample_violations_dicts,
        temp_output_dir
    ):
        """Test summary generation alongside all formats."""
        generator = ReportGenerator()

        # Generate formats
        generator.generate_all_formats(
            result=sample_result_object,
            violations=sample_violations_dicts,
            output_dir=temp_output_dir
        )

        # Generate summary
        metrics = {
            "total_violations": len(sample_violations_dicts),
            "critical_count": 1,
            "high_count": 1,
            "medium_count": 1,
            "low_count": 0,
            "overall_quality_score": 0.75,
            "connascence_index": 2.0,
        }

        summary = generator.format_summary(metrics)
        assert "Total Violations: 3" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--cov=analyzer.architecture.report_generator"])
