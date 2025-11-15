#!/usr/bin/env python3
"""
Dogfooding Cycle Comparison Script
Compares two large JSON files from connascence analysis cycles
"""

import json
import sys
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Any, Tuple


def load_json_safely(filepath: Path) -> Dict:
    """Load large JSON file safely with error handling"""
    try:
        print(f"Loading {filepath.name} ({filepath.stat().st_size / (1024*1024):.1f} MB)...")
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Successfully loaded {filepath.name}")
        return data
    except FileNotFoundError:
        print(f"ERROR: File not found: {filepath}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {filepath}: {e}")
        sys.exit(1)
    except MemoryError:
        print(f"ERROR: File too large to load into memory: {filepath}")
        sys.exit(1)


def extract_violations(data: Dict) -> List[Dict]:
    """Extract violations from various possible JSON structures"""
    violations = []

    # Handle different possible structures
    if isinstance(data, dict):
        # Check for direct violations array
        if 'violations' in data:
            violations.extend(data['violations'])

        # Check for results -> violations
        if 'results' in data and isinstance(data['results'], dict):
            if 'violations' in data['results']:
                violations.extend(data['results']['violations'])

        # Check for runs[0].results (SARIF format)
        if 'runs' in data and isinstance(data['runs'], list):
            for run in data['runs']:
                if 'results' in run:
                    violations.extend(run['results'])

        # Check for files with violations
        if 'files' in data:
            for file_data in data.get('files', []):
                if isinstance(file_data, dict) and 'violations' in file_data:
                    violations.extend(file_data['violations'])

    elif isinstance(data, list):
        # Data is already a list of violations
        violations = data

    return violations


def categorize_violations(violations: List[Dict]) -> Dict[str, Any]:
    """Categorize violations by type, severity, and other metrics"""
    metrics = {
        'total': len(violations),
        'by_severity': Counter(),
        'by_type': Counter(),
        'by_category': Counter(),
        'files_affected': set(),
        'violations_list': violations
    }

    for violation in violations:
        # Extract severity (handle different formats)
        severity = 'unknown'
        if 'level' in violation:
            severity = violation['level']
        elif 'severity' in violation:
            severity = violation['severity']
        elif 'properties' in violation and 'severity' in violation['properties']:
            severity = violation['properties']['severity']

        metrics['by_severity'][severity] += 1

        # Extract violation type/rule
        rule_id = 'unknown'
        if 'ruleId' in violation:
            rule_id = violation['ruleId']
        elif 'rule' in violation:
            rule_id = violation['rule']
        elif 'type' in violation:
            rule_id = violation['type']

        metrics['by_type'][rule_id] += 1

        # Extract category (CoP, CoM, etc.)
        category = 'other'
        if 'CoP' in rule_id or 'parameter' in rule_id.lower():
            category = 'CoP (Position)'
        elif 'CoM' in rule_id or 'meaning' in rule_id.lower() or 'magic' in rule_id.lower():
            category = 'CoM (Meaning)'
        elif 'CoN' in rule_id or 'name' in rule_id.lower():
            category = 'CoN (Name)'
        elif 'CoT' in rule_id or 'type' in rule_id.lower():
            category = 'CoT (Type)'
        elif 'complexity' in rule_id.lower():
            category = 'Complexity'
        elif 'god' in rule_id.lower() or 'method-count' in rule_id.lower():
            category = 'God Objects'
        elif 'nesting' in rule_id.lower():
            category = 'Deep Nesting'
        elif 'function-length' in rule_id.lower() or 'long-function' in rule_id.lower():
            category = 'Long Functions'

        metrics['by_category'][category] += 1

        # Extract file path
        file_path = None
        if 'locations' in violation and violation['locations']:
            loc = violation['locations'][0]
            if 'physicalLocation' in loc:
                file_path = loc['physicalLocation'].get('artifactLocation', {}).get('uri')
        elif 'file' in violation:
            file_path = violation['file']
        elif 'path' in violation:
            file_path = violation['path']

        if file_path:
            metrics['files_affected'].add(file_path)

    # Convert set to list for JSON serialization
    metrics['files_affected'] = sorted(list(metrics['files_affected']))

    return metrics


def compare_metrics(cycle1: Dict[str, Any], cycle2: Dict[str, Any]) -> Dict[str, Any]:
    """Compare metrics between two cycles"""
    comparison = {
        'total_change': cycle2['total'] - cycle1['total'],
        'total_pct_change': ((cycle2['total'] - cycle1['total']) / cycle1['total'] * 100) if cycle1['total'] > 0 else 0,
        'severity_changes': {},
        'type_changes': {},
        'category_changes': {},
        'files_added': len(set(cycle2['files_affected']) - set(cycle1['files_affected'])),
        'files_removed': len(set(cycle1['files_affected']) - set(cycle2['files_affected'])),
        'files_still_affected': len(set(cycle1['files_affected']) & set(cycle2['files_affected']))
    }

    # Compare severities
    all_severities = set(cycle1['by_severity'].keys()) | set(cycle2['by_severity'].keys())
    for severity in all_severities:
        c1_count = cycle1['by_severity'].get(severity, 0)
        c2_count = cycle2['by_severity'].get(severity, 0)
        comparison['severity_changes'][severity] = {
            'cycle1': c1_count,
            'cycle2': c2_count,
            'change': c2_count - c1_count,
            'pct_change': ((c2_count - c1_count) / c1_count * 100) if c1_count > 0 else (100 if c2_count > 0 else 0)
        }

    # Compare types (top 10 most common)
    all_types = set(cycle1['by_type'].keys()) | set(cycle2['by_type'].keys())
    top_types = sorted(all_types, key=lambda x: cycle1['by_type'].get(x, 0) + cycle2['by_type'].get(x, 0), reverse=True)[:10]
    for rule_type in top_types:
        c1_count = cycle1['by_type'].get(rule_type, 0)
        c2_count = cycle2['by_type'].get(rule_type, 0)
        comparison['type_changes'][rule_type] = {
            'cycle1': c1_count,
            'cycle2': c2_count,
            'change': c2_count - c1_count,
            'pct_change': ((c2_count - c1_count) / c1_count * 100) if c1_count > 0 else (100 if c2_count > 0 else 0)
        }

    # Compare categories
    all_categories = set(cycle1['by_category'].keys()) | set(cycle2['by_category'].keys())
    for category in all_categories:
        c1_count = cycle1['by_category'].get(category, 0)
        c2_count = cycle2['by_category'].get(category, 0)
        comparison['category_changes'][category] = {
            'cycle1': c1_count,
            'cycle2': c2_count,
            'change': c2_count - c1_count,
            'pct_change': ((c2_count - c1_count) / c1_count * 100) if c1_count > 0 else (100 if c2_count > 0 else 0)
        }

    return comparison


def generate_markdown_report(cycle1_metrics: Dict, cycle2_metrics: Dict, comparison: Dict, output_path: Path):
    """Generate human-readable markdown comparison report"""

    report = f"""# Dogfooding Cycle Metrics Comparison

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Executive Summary

| Metric | Cycle 1 | Cycle 2 | Change | % Change |
|--------|---------|---------|--------|----------|
| **Total Violations** | {cycle1_metrics['total']:,} | {cycle2_metrics['total']:,} | {comparison['total_change']:+,} | {comparison['total_pct_change']:+.2f}% |
| **Files Affected** | {len(cycle1_metrics['files_affected']):,} | {len(cycle2_metrics['files_affected']):,} | {len(cycle2_metrics['files_affected']) - len(cycle1_metrics['files_affected']):+,} | - |
| **Files Added** | - | - | {comparison['files_added']:,} | - |
| **Files Removed** | - | - | {comparison['files_removed']:,} | - |
| **Files Still Affected** | - | - | {comparison['files_still_affected']:,} | - |

"""

    # Severity breakdown
    report += "\n## Violations by Severity\n\n"
    report += "| Severity | Cycle 1 | Cycle 2 | Change | % Change |\n"
    report += "|----------|---------|---------|--------|----------|\n"

    for severity in sorted(comparison['severity_changes'].keys()):
        data = comparison['severity_changes'][severity]
        emoji = ""
        if data['change'] < 0:
            emoji = "✅"
        elif data['change'] > 0:
            emoji = "⚠️"

        report += f"| {emoji} **{severity}** | {data['cycle1']:,} | {data['cycle2']:,} | {data['change']:+,} | {data['pct_change']:+.2f}% |\n"

    # Category breakdown
    report += "\n## Violations by Category\n\n"
    report += "| Category | Cycle 1 | Cycle 2 | Change | % Change |\n"
    report += "|----------|---------|---------|--------|----------|\n"

    for category in sorted(comparison['category_changes'].keys(), key=lambda x: comparison['category_changes'][x]['cycle1'] + comparison['category_changes'][x]['cycle2'], reverse=True):
        data = comparison['category_changes'][category]
        emoji = ""
        if data['change'] < 0:
            emoji = "✅"
        elif data['change'] > 0:
            emoji = "⚠️"

        report += f"| {emoji} **{category}** | {data['cycle1']:,} | {data['cycle2']:,} | {data['change']:+,} | {data['pct_change']:+.2f}% |\n"

    # Top violation types
    report += "\n## Top 10 Violation Types\n\n"
    report += "| Rule/Type | Cycle 1 | Cycle 2 | Change | % Change |\n"
    report += "|-----------|---------|---------|--------|----------|\n"

    for rule_type in sorted(comparison['type_changes'].keys(), key=lambda x: comparison['type_changes'][x]['cycle1'] + comparison['type_changes'][x]['cycle2'], reverse=True):
        data = comparison['type_changes'][rule_type]
        emoji = ""
        if data['change'] < 0:
            emoji = "✅"
        elif data['change'] > 0:
            emoji = "⚠️"

        report += f"| {emoji} `{rule_type}` | {data['cycle1']:,} | {data['cycle2']:,} | {data['change']:+,} | {data['pct_change']:+.2f}% |\n"

    # Key insights
    report += "\n## Key Insights\n\n"

    if comparison['total_change'] < 0:
        report += f"- ✅ **Overall Improvement**: {abs(comparison['total_change']):,} fewer violations ({abs(comparison['total_pct_change']):.2f}% reduction)\n"
    elif comparison['total_change'] > 0:
        report += f"- ⚠️ **Regression**: {comparison['total_change']:,} more violations ({comparison['total_pct_change']:.2f}% increase)\n"
    else:
        report += "- No overall change in violation count\n"

    # Find biggest improvements
    biggest_improvements = sorted(
        [(cat, data) for cat, data in comparison['category_changes'].items() if data['change'] < 0],
        key=lambda x: x[1]['change']
    )[:3]

    if biggest_improvements:
        report += "\n### Biggest Improvements\n\n"
        for category, data in biggest_improvements:
            report += f"- **{category}**: {abs(data['change']):,} fewer violations ({abs(data['pct_change']):.2f}% reduction)\n"

    # Find biggest regressions
    biggest_regressions = sorted(
        [(cat, data) for cat, data in comparison['category_changes'].items() if data['change'] > 0],
        key=lambda x: x[1]['change'],
        reverse=True
    )[:3]

    if biggest_regressions:
        report += "\n### Biggest Regressions\n\n"
        for category, data in biggest_regressions:
            report += f"- **{category}**: {data['change']:,} more violations ({data['pct_change']:.2f}% increase)\n"

    # File changes
    if comparison['files_added'] > 0:
        report += f"\n- {comparison['files_added']:,} new files with violations added in Cycle 2\n"
    if comparison['files_removed'] > 0:
        report += f"- {comparison['files_removed']:,} files cleaned up (no longer have violations)\n"

    # Raw data summary
    report += "\n## Raw Data Summary\n\n"
    report += "### Cycle 1 Metrics\n\n"
    report += f"- **Total Violations**: {cycle1_metrics['total']:,}\n"
    report += f"- **Files Affected**: {len(cycle1_metrics['files_affected']):,}\n"
    report += f"- **Severity Distribution**: {dict(cycle1_metrics['by_severity'])}\n"
    report += f"- **Category Distribution**: {dict(cycle1_metrics['by_category'])}\n"

    report += "\n### Cycle 2 Metrics\n\n"
    report += f"- **Total Violations**: {cycle2_metrics['total']:,}\n"
    report += f"- **Files Affected**: {len(cycle2_metrics['files_affected']):,}\n"
    report += f"- **Severity Distribution**: {dict(cycle2_metrics['by_severity'])}\n"
    report += f"- **Category Distribution**: {dict(cycle2_metrics['by_category'])}\n"

    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\nReport saved to: {output_path}")


def main():
    """Main execution function"""
    print("=" * 80)
    print("Dogfooding Cycle Comparison Tool")
    print("=" * 80)

    # Define file paths
    cycle1_path = Path("C:/Users/17175/Desktop/connascence/docs/dogfooding/full-analysis.json")
    cycle2_path = Path("C:/Users/17175/Desktop/connascence/docs/dogfooding/cycle2-fixed.json")
    output_path = Path("C:/Users/17175/Desktop/connascence/docs/dogfooding/METRICS-COMPARISON.md")

    # Load JSON files
    print("\n[1/5] Loading JSON files...")
    cycle1_data = load_json_safely(cycle1_path)
    cycle2_data = load_json_safely(cycle2_path)

    # Extract violations
    print("\n[2/5] Extracting violations...")
    cycle1_violations = extract_violations(cycle1_data)
    cycle2_violations = extract_violations(cycle2_data)
    print(f"Cycle 1: {len(cycle1_violations):,} violations")
    print(f"Cycle 2: {len(cycle2_violations):,} violations")

    # Categorize violations
    print("\n[3/5] Categorizing violations...")
    cycle1_metrics = categorize_violations(cycle1_violations)
    cycle2_metrics = categorize_violations(cycle2_violations)

    # Compare metrics
    print("\n[4/5] Comparing metrics...")
    comparison = compare_metrics(cycle1_metrics, cycle2_metrics)

    # Generate report
    print("\n[5/5] Generating markdown report...")
    generate_markdown_report(cycle1_metrics, cycle2_metrics, comparison, output_path)

    # Print summary
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)
    print(f"Cycle 1: {cycle1_metrics['total']:,} violations across {len(cycle1_metrics['files_affected']):,} files")
    print(f"Cycle 2: {cycle2_metrics['total']:,} violations across {len(cycle2_metrics['files_affected']):,} files")
    print(f"Change: {comparison['total_change']:+,} violations ({comparison['total_pct_change']:+.2f}%)")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
