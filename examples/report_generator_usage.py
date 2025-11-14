#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
ReportGenerator Usage Examples
===============================

Demonstrates how to use the centralized ReportGenerator class for
generating analysis reports in multiple formats.
"""

from pathlib import Path
from analyzer.architecture.report_generator import ReportGenerator


def example_basic_usage():
    """Example 1: Basic report generation."""
    print("=" * 60)
    print("EXAMPLE 1: Basic Report Generation")
    print("=" * 60)

    # Initialize generator
    generator = ReportGenerator({"version": "1.0.0"})

    # Sample analysis result (would normally come from UnifiedConnascenceAnalyzer)
    sample_result = {
        "total_violations": 10,
        "critical_count": 2,
        "high_count": 3,
        "medium_count": 3,
        "low_count": 2,
        "overall_quality_score": 0.85,
        "connascence_index": 12.5,
        "policy_preset": "service-defaults",
        "analysis_duration_ms": 1234,
        "total_files_analyzed": 42,
        "violations": [
            {
                "type": "CoM",
                "severity": "high",
                "file_path": "src/example.py",
                "line_number": 42,
                "description": "Magic literal '5432' detected",
                "recommendation": "Extract to named constant"
            }
        ]
    }

    # Generate JSON report
    json_report = generator.generate_json(sample_result)
    print("\nJSON Report (first 200 chars):")
    print(json_report[:200] + "...")

    print("\n" + "=" * 60 + "\n")


def example_summary_generation():
    """Example 2: Generate text summary."""
    print("=" * 60)
    print("EXAMPLE 2: Summary Generation")
    print("=" * 60)

    generator = ReportGenerator()

    metrics = {
        "total_violations": 42,
        "critical_count": 3,
        "high_count": 12,
        "medium_count": 20,
        "low_count": 7,
        "overall_quality_score": 0.85,
        "connascence_index": 12.5
    }

    summary = generator.format_summary(metrics)
    print("\n" + summary)

    print("\n" + "=" * 60 + "\n")


def example_multi_format_generation(output_dir: Path):
    """Example 3: Generate all formats at once."""
    print("=" * 60)
    print("EXAMPLE 3: Multi-Format Generation")
    print("=" * 60)

    generator = ReportGenerator({
        "version": "2.0.0",
        "max_violations_to_show": 20,
        "max_files_to_show": 10
    })

    # Sample data
    sample_result = {
        "total_violations": 5,
        "policy_preset": "service-defaults",
        "analysis_duration_ms": 500,
        "total_files_analyzed": 10,
        "violations": []
    }

    violations = [
        {
            "type": "CoM",
            "severity": "high",
            "file_path": "src/config.py",
            "line_number": 15,
            "description": "Magic literal '8080' detected",
            "recommendation": "Use PORT constant"
        }
    ]

    # Generate all formats
    output_paths = generator.generate_all_formats(
        result=sample_result,
        violations=violations,
        output_dir=output_dir,
        base_name="example_analysis"
    )

    print(f"\nReports generated in: {output_dir}")
    for format_name, file_path in output_paths.items():
        print(f"  - {format_name}: {file_path}")

    print("\n" + "=" * 60 + "\n")


def example_advanced_configuration():
    """Example 4: Advanced configuration options."""
    print("=" * 60)
    print("EXAMPLE 4: Advanced Configuration")
    print("=" * 60)

    # Custom configuration
    config = {
        "version": "2.0.0",
        "max_violations_to_show": 25,  # Show more violations in markdown
        "max_files_to_show": 15,       # Show more files in markdown
        "indent": 4,                   # Larger JSON indentation
        "sort_keys": True              # Sorted JSON keys for readability
    }

    generator = ReportGenerator(config)

    print("\nGenerator configured with:")
    print(f"  - Version: {generator.version}")
    print(f"  - Max violations in markdown: {generator.markdown_reporter.max_violations_to_show}")
    print(f"  - Max files in markdown: {generator.markdown_reporter.max_files_to_show}")

    print("\n" + "=" * 60 + "\n")


def example_error_handling():
    """Example 5: Error handling in report generation."""
    print("=" * 60)
    print("EXAMPLE 5: Error Handling")
    print("=" * 60)

    generator = ReportGenerator()

    # Test with invalid data
    try:
        invalid_result = None
        generator.generate_json(invalid_result)
    except Exception as e:
        print(f"\nExpected error caught: {type(e).__name__}")
        print(f"Error message: {e}")

    print("\nError handling working correctly!")

    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("ReportGenerator Usage Examples")
    print("=" * 60 + "\n")

    # Run examples
    example_basic_usage()
    example_summary_generation()

    # Create temporary output directory for examples
    output_dir = Path(__file__).parent / "example_output"
    output_dir.mkdir(exist_ok=True)

    example_multi_format_generation(output_dir)
    example_advanced_configuration()
    example_error_handling()

    print("=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)
