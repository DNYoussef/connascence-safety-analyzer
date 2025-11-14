"""
Clarity Linter Usage Examples

Demonstrates various usage patterns for the ClarityLinter orchestrator.

NASA Rule 4 Compliant: All functions under 60 lines
"""

from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.clarity_linter import ClarityLinter, ClaritySummary


def example_basic_analysis():
    """
    Example 1: Basic project analysis with default configuration.

    NASA Rule 4: Function under 60 lines
    """
    print("=" * 60)
    print("Example 1: Basic Project Analysis")
    print("=" * 60)

    # Initialize linter with default config
    linter = ClarityLinter()

    # Analyze project
    project_path = Path(__file__).parent.parent
    violations = linter.analyze_project(project_path)

    # Print summary
    summary = linter.get_summary()
    print(f"\nFiles analyzed: {summary['total_files_analyzed']}")
    print(f"Violations found: {summary['total_violations_found']}")
    print(f"Detectors enabled: {summary['detectors_enabled']}")

    # Print first 5 violations
    print("\nFirst 5 violations:")
    for i, violation in enumerate(violations[:5], 1):
        print(f"\n{i}. {violation.rule_name} ({violation.severity})")
        print(f"   {violation.file_path}:{violation.line_number}")
        print(f"   {violation.description}")


def example_single_file_analysis():
    """
    Example 2: Analyze single file and group by severity.

    NASA Rule 4: Function under 60 lines
    """
    print("\n" + "=" * 60)
    print("Example 2: Single File Analysis")
    print("=" * 60)

    linter = ClarityLinter()

    # Analyze this file
    file_path = Path(__file__)
    violations = linter.analyze_file(file_path)

    # Group by severity
    by_severity = {}
    for violation in violations:
        severity = violation.severity
        if severity not in by_severity:
            by_severity[severity] = []
        by_severity[severity].append(violation)

    # Print counts
    print(f"\nAnalyzed: {file_path.name}")
    print(f"Total violations: {len(violations)}")
    for severity, violations_list in sorted(by_severity.items()):
        print(f"  {severity}: {len(violations_list)}")


def example_sarif_export():
    """
    Example 3: Export violations to SARIF 2.1.0 format.

    NASA Rule 4: Function under 60 lines
    """
    print("\n" + "=" * 60)
    print("Example 3: SARIF Export")
    print("=" * 60)

    linter = ClarityLinter()

    # Analyze small subset
    project_path = Path(__file__).parent.parent / "analyzer" / "clarity_linter"
    violations = linter.analyze_project(project_path)

    # Export to SARIF
    output_path = Path(__file__).parent / "clarity_results.sarif"
    sarif_doc = linter.export_sarif(violations, output_path)

    print(f"\nSARIF document exported to: {output_path}")
    print(f"Schema version: {sarif_doc['version']}")
    print(f"Results: {len(sarif_doc['runs'][0]['results'])}")
    print(f"Rules defined: {len(sarif_doc['runs'][0]['tool']['driver']['rules'])}")


def example_custom_config():
    """
    Example 4: Use custom configuration file.

    NASA Rule 4: Function under 60 lines
    """
    print("\n" + "=" * 60)
    print("Example 4: Custom Configuration")
    print("=" * 60)

    # Find config file
    config_path = Path(__file__).parent.parent / "clarity_linter.yaml"

    if config_path.exists():
        linter = ClarityLinter(config_path=config_path)
        print(f"Loaded config from: {config_path}")

        # Show enabled rules
        print("\nEnabled rules:")
        for detector in linter.detectors:
            print(f"  - {detector.rule_id}: {detector.rule_name}")
            print(f"    Severity: {detector.severity}")
            print(f"    Enabled: {detector.enabled}")
    else:
        print(f"Config file not found: {config_path}")
        print("Using default configuration")


def example_violation_filtering():
    """
    Example 5: Filter violations by severity and rule.

    NASA Rule 4: Function under 60 lines
    """
    print("\n" + "=" * 60)
    print("Example 5: Violation Filtering")
    print("=" * 60)

    linter = ClarityLinter()
    project_path = Path(__file__).parent.parent / "analyzer" / "clarity_linter"
    violations = linter.analyze_project(project_path)

    # Filter critical and high severity
    high_priority = [
        v for v in violations
        if v.severity in ('critical', 'high')
    ]

    print(f"\nTotal violations: {len(violations)}")
    print(f"High priority (critical/high): {len(high_priority)}")

    # Filter by rule
    thin_helpers = [
        v for v in violations
        if v.rule_id == 'CLARITY_THIN_HELPER'
    ]

    print(f"Thin helper violations: {len(thin_helpers)}")

    # Show examples
    if thin_helpers:
        print("\nExample thin helper violation:")
        v = thin_helpers[0]
        print(f"  File: {v.file_path}")
        print(f"  Line: {v.line_number}")
        print(f"  Description: {v.description}")
        print(f"  Recommendation: {v.recommendation}")


def example_summary_statistics():
    """
    Example 6: Generate comprehensive summary statistics.

    NASA Rule 4: Function under 60 lines
    """
    print("\n" + "=" * 60)
    print("Example 6: Summary Statistics")
    print("=" * 60)

    linter = ClarityLinter()
    project_path = Path(__file__).parent.parent / "analyzer"
    violations = linter.analyze_project(project_path)

    # Create summary
    summary = ClaritySummary.from_violations(
        violations,
        total_files=linter.get_summary()['total_files_analyzed']
    )

    # Print statistics
    print(f"\nAnalysis Summary:")
    print(f"  Files analyzed: {summary.total_files}")
    print(f"  Total violations: {summary.total_violations}")

    print("\nViolations by severity:")
    for severity, count in sorted(summary.violations_by_severity.items()):
        print(f"  {severity}: {count}")

    print("\nViolations by rule:")
    for rule_id, count in sorted(
        summary.violations_by_rule.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]:
        print(f"  {rule_id}: {count}")

    print("\nTop 5 files with most violations:")
    for file_path, count in sorted(
        summary.violations_by_file.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]:
        print(f"  {Path(file_path).name}: {count}")


def example_connascence_integration():
    """
    Example 7: Integration with connascence analyzer.

    NASA Rule 4: Function under 60 lines
    """
    print("\n" + "=" * 60)
    print("Example 7: Connascence Integration")
    print("=" * 60)

    linter = ClarityLinter()
    project_path = Path(__file__).parent.parent / "analyzer" / "clarity_linter"
    clarity_violations = linter.analyze_project(project_path)

    # Convert to connascence format
    connascence_violations = [
        v.to_connascence_violation() for v in clarity_violations
    ]

    print(f"\nClarity violations: {len(clarity_violations)}")
    print(f"Converted to connascence format: {len(connascence_violations)}")

    # Show example conversion
    if connascence_violations:
        print("\nExample converted violation:")
        cv = connascence_violations[0]
        print(f"  Type: {cv['type']}")
        print(f"  Severity: {cv['severity']}")
        print(f"  File: {cv['file_path']}:{cv['line_number']}")
        print(f"  Description: {cv['description']}")
        print(f"  Context: {cv['context']}")


def main():
    """
    Run all examples.

    NASA Rule 4: Function under 60 lines
    """
    try:
        example_basic_analysis()
        example_single_file_analysis()
        example_sarif_export()
        example_custom_config()
        example_violation_filtering()
        example_summary_statistics()
        example_connascence_integration()

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
