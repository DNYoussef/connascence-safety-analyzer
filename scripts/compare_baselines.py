#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Compare baseline reports for trend analysis.
Used in self-dogfooding CI workflow.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def load_baseline(filepath: str) -> Dict[str, Any]:
    """Load baseline report and extract metrics."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        baseline = {
            'total_violations': 0,
            'critical_violations': 0,
            'nasa_score': 0.85,
            'mece_score': 0.8,
            'god_objects': 0,
            'timestamp': None
        }
        
        # Parse metrics from markdown
        lines = content.split('\n')
        for line in lines:
            if 'Total Violations:' in line:
                try:
                    baseline['total_violations'] = int(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass
            elif 'Critical Violations:' in line:
                try:
                    baseline['critical_violations'] = int(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass
            elif 'NASA Score:' in line:
                try:
                    baseline['nasa_score'] = float(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass
            elif 'MECE Score:' in line:
                try:
                    baseline['mece_score'] = float(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass
            elif 'God Objects:' in line:
                try:
                    baseline['god_objects'] = int(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass
            elif 'Timestamp:' in line:
                try:
                    baseline['timestamp'] = line.split(':', 1)[1].strip()
                except IndexError:
                    pass
        
        return baseline
    except FileNotFoundError:
        print(f"Warning: Baseline file not found: {filepath}")
        return {
            'total_violations': 0,
            'critical_violations': 0,
            'nasa_score': 0.85,
            'mece_score': 0.8,
            'god_objects': 0,
            'timestamp': None
        }


def compare_baselines(current: Dict[str, Any], previous: Dict[str, Any]) -> Dict[str, Any]:
    """Compare two baseline reports."""
    trends = {
        'analysis_date': datetime.utcnow().isoformat(),
        'trend_analysis': {},
        'significant_changes': [],
        'overall_direction': 'stable'
    }
    
    # Calculate trends for each metric
    metrics = ['total_violations', 'critical_violations', 'nasa_score', 'mece_score', 'god_objects']
    
    for metric in metrics:
        current_val = current.get(metric, 0)
        previous_val = previous.get(metric, 0)
        change = current_val - previous_val
        
        if previous_val > 0:
            change_percent = (change / previous_val) * 100
        else:
            change_percent = 0
        
        trends['trend_analysis'][metric] = {
            'current': current_val,
            'previous': previous_val,
            'absolute_change': change,
            'percent_change': change_percent,
            'direction': 'improving' if (metric in ['nasa_score', 'mece_score'] and change > 0) or 
                        (metric in ['total_violations', 'critical_violations', 'god_objects'] and change < 0) else
                        'declining' if change != 0 else 'stable'
        }
        
        # Mark significant changes (>10% change)
        if abs(change_percent) > 10:
            trends['significant_changes'].append({
                'metric': metric,
                'change_percent': change_percent,
                'description': f"{metric} changed by {change_percent:.1f}%"
            })
    
    # Determine overall direction
    improving_count = sum(1 for m in trends['trend_analysis'].values() if m['direction'] == 'improving')
    declining_count = sum(1 for m in trends['trend_analysis'].values() if m['direction'] == 'declining')
    
    if improving_count > declining_count:
        trends['overall_direction'] = 'improving'
    elif declining_count > improving_count:
        trends['overall_direction'] = 'declining'
    else:
        trends['overall_direction'] = 'stable'
    
    return trends


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Compare baseline reports for trend analysis")
    parser.add_argument('--current', required=True, help='Current baseline report')
    parser.add_argument('--previous', required=True, help='Previous baseline report')
    parser.add_argument('--output', required=True, help='Output trends JSON file')
    
    args = parser.parse_args()
    
    # Load baselines
    current_baseline = load_baseline(args.current)
    previous_baseline = load_baseline(args.previous)
    
    # Compare and analyze trends
    trends = compare_baselines(current_baseline, previous_baseline)
    
    # Save trends
    with open(args.output, 'w') as f:
        json.dump(trends, f, indent=2)
    
    # Print summary
    print(f"Baseline Comparison Complete")
    print(f"Overall Direction: {trends['overall_direction']}")
    print(f"Significant Changes: {len(trends['significant_changes'])}")
    
    for change in trends['significant_changes']:
        print(f"  - {change['description']}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())