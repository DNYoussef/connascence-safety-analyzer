#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Compare current self-analysis results with baseline report.
Used in self-dogfooding CI workflow.
"""

import argparse
import contextlib
import json
import sys
from typing import Any, Dict


def load_json_results(filepath: str) -> Dict[str, Any]:
    """Load JSON analysis results."""
    try:
        with open(filepath) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Results file not found: {filepath}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file {filepath}: {e}")
        return {}


def load_baseline_report(filepath: str) -> Dict[str, Any]:
    """Load baseline markdown report and extract metrics."""
    try:
        with open(filepath) as f:
            content = f.read()

        # Extract metrics from markdown format
        baseline = {
            'total_violations': 0,
            'critical_violations': 0,
            'nasa_score': 0.85,
            'mece_score': 0.8,
            'god_objects': 0
        }

        # Simple parsing of metrics from markdown
        lines = content.split('\n')
        for line in lines:
            if 'Total Violations:' in line:
                with contextlib.suppress(ValueError, IndexError):
                    baseline['total_violations'] = int(line.split(':')[1].strip())

            elif 'Critical Violations:' in line:
                with contextlib.suppress(ValueError, IndexError):
                    baseline['critical_violations'] = int(line.split(':')[1].strip())

            elif 'NASA Score:' in line:
                with contextlib.suppress(ValueError, IndexError):
                    baseline['nasa_score'] = float(line.split(':')[1].strip())


        return baseline
    except FileNotFoundError:
        print(f"Warning: Baseline report not found: {filepath}")
        return {
            'total_violations': 0,
            'critical_violations': 0,
            'nasa_score': 0.85,
            'mece_score': 0.8,
            'god_objects': 0
        }


def compare_results(current: Dict[str, Any], baseline: Dict[str, Any]) -> Dict[str, Any]:
    """Compare current results with baseline."""
    comparison = {
        'comparison_timestamp': None,
        'improvements': [],
        'regressions': [],
        'metrics_comparison': {}
    }

    # Extract current metrics
    current_violations = len(current.get('violations', []))
    current_critical = len([v for v in current.get('violations', []) if v.get('severity') == 'critical'])
    current_nasa = current.get('nasa_compliance', {}).get('score', 0.0)

    # Extract baseline metrics
    baseline_violations = baseline.get('total_violations', 0)
    baseline_critical = baseline.get('critical_violations', 0)
    baseline_nasa = baseline.get('nasa_score', 0.85)

    # Compare metrics
    comparison['metrics_comparison'] = {
        'total_violations': {
            'current': current_violations,
            'baseline': baseline_violations,
            'change': current_violations - baseline_violations
        },
        'critical_violations': {
            'current': current_critical,
            'baseline': baseline_critical,
            'change': current_critical - baseline_critical
        },
        'nasa_score': {
            'current': current_nasa,
            'baseline': baseline_nasa,
            'change': current_nasa - baseline_nasa
        }
    }

    # Identify improvements and regressions
    if current_violations < baseline_violations:
        comparison['improvements'].append(f"Total violations decreased by {baseline_violations - current_violations}")
    elif current_violations > baseline_violations:
        comparison['regressions'].append(f"Total violations increased by {current_violations - baseline_violations}")

    if current_critical < baseline_critical:
        comparison['improvements'].append(f"Critical violations decreased by {baseline_critical - current_critical}")
    elif current_critical > baseline_critical:
        comparison['regressions'].append(f"Critical violations increased by {current_critical - baseline_critical}")

    if current_nasa > baseline_nasa:
        comparison['improvements'].append(f"NASA score improved by {current_nasa - baseline_nasa:.3f}")
    elif current_nasa < baseline_nasa:
        comparison['regressions'].append(f"NASA score decreased by {baseline_nasa - current_nasa:.3f}")

    return comparison


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Compare self-analysis results with baseline")
    parser.add_argument('--current', required=True, help='Current analysis results JSON file')
    parser.add_argument('--baseline', required=True, help='Baseline report markdown file')
    parser.add_argument('--output', required=True, help='Output comparison JSON file')

    args = parser.parse_args()

    # Load data
    current_results = load_json_results(args.current)
    baseline_results = load_baseline_report(args.baseline)

    # Compare
    comparison = compare_results(current_results, baseline_results)

    # Save comparison results
    with open(args.output, 'w') as f:
        json.dump(comparison, f, indent=2)

    # Print summary
    print("Self-Analysis Comparison Complete")
    print(f"Improvements: {len(comparison['improvements'])}")
    print(f"Regressions: {len(comparison['regressions'])}")

    # Exit with appropriate code based on significant regression thresholds
    significant_regressions = []

    # Extract metrics for threshold evaluation
    metrics = comparison['metrics_comparison']
    violations_change = metrics['total_violations']['change']
    critical_change = metrics['critical_violations']['change']
    nasa_change = metrics['nasa_score']['change']

    # Define thresholds for significant regressions
    VIOLATION_INCREASE_THRESHOLD = 50  # More than 50 additional violations
    CRITICAL_INCREASE_THRESHOLD = 10   # More than 10 additional critical violations
    NASA_DECREASE_THRESHOLD = 0.05     # NASA score drops by more than 5%
    VIOLATION_PERCENTAGE_THRESHOLD = 0.10  # More than 10% increase in violations

    baseline_violations = metrics['total_violations']['baseline']
    violation_percentage_increase = violations_change / max(baseline_violations, 1) if baseline_violations > 0 else 0

    # Check for significant regressions
    if violations_change > VIOLATION_INCREASE_THRESHOLD:
        significant_regressions.append(f"Total violations increased significantly by {violations_change} (threshold: {VIOLATION_INCREASE_THRESHOLD})")

    if violation_percentage_increase > VIOLATION_PERCENTAGE_THRESHOLD:
        significant_regressions.append(f"Total violations increased by {violation_percentage_increase:.1%} (threshold: {VIOLATION_PERCENTAGE_THRESHOLD:.1%})")

    if critical_change > CRITICAL_INCREASE_THRESHOLD:
        significant_regressions.append(f"Critical violations increased significantly by {critical_change} (threshold: {CRITICAL_INCREASE_THRESHOLD})")

    if nasa_change < -NASA_DECREASE_THRESHOLD:
        significant_regressions.append(f"NASA score decreased significantly by {-nasa_change:.3f} (threshold: {NASA_DECREASE_THRESHOLD:.3f})")

    if significant_regressions:
        print("ERROR: Significant regressions detected in self-analysis:")
        for regression in significant_regressions:
            print(f"  - {regression}")
        print(f"\nTotal minor regressions: {len(comparison['regressions'])}")
        print("CI failure triggered due to significant quality degradation")
        return 1
    elif comparison['regressions']:
        print(f"Info: {len(comparison['regressions'])} minor regressions detected but within acceptable thresholds")
        print("CI continues - no significant quality degradation detected")

    return 0


if __name__ == '__main__':
    sys.exit(main())
