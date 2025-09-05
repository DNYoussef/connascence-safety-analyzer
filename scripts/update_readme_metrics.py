#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Update README metrics if significantly changed.
Used in self-dogfooding CI workflow.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Optional


def read_readme() -> str:
    """Read README.md content."""
    readme_path = Path('README.md')
    if readme_path.exists():
        return readme_path.read_text()
    return ""


def update_metric_in_readme(content: str, metric_name: str, new_value: str) -> str:
    """Update a specific metric in README content."""
    # Pattern to match metrics like "1,234+ violations detected"
    patterns = [
        rf'(\d+,?\d*\+?\s*{metric_name})',
        rf'({metric_name}:\s*\d+,?\d*)',
        rf'(\d+,?\d*\s*{metric_name})',
        rf'({metric_name}\s*\d+,?\d*)',
    ]
    
    updated = content
    for pattern in patterns:
        if re.search(pattern, updated, re.IGNORECASE):
            updated = re.sub(pattern, f"{new_value} {metric_name}", updated, flags=re.IGNORECASE)
            break
    
    return updated


def update_nasa_score_in_readme(content: str, nasa_score: float) -> str:
    """Update NASA compliance score in README."""
    # Pattern to match NASA score like "85.4% NASA compliant"
    patterns = [
        r'(\d+\.?\d*%?\s*NASA\s*complia\w*)',
        r'(NASA\s*complia\w*:\s*\d+\.?\d*%?)',
        r'(\d+\.?\d*%?\s*Power\s*of\s*Ten)',
    ]
    
    nasa_percent = f"{nasa_score * 100:.1f}%"
    updated = content
    
    for pattern in patterns:
        if re.search(pattern, updated, re.IGNORECASE):
            updated = re.sub(pattern, f"{nasa_percent} NASA compliant", updated, flags=re.IGNORECASE)
            break
    
    return updated


def should_update_readme(current_violations: int, current_nasa: float) -> bool:
    """Check if README should be updated based on significant changes."""
    readme_content = read_readme()
    
    if not readme_content:
        return False
    
    # Extract current metrics from README
    violation_match = re.search(r'(\d+,?\d*)\+?\s*violations?', readme_content, re.IGNORECASE)
    nasa_match = re.search(r'(\d+\.?\d*)%?\s*NASA\s*complia', readme_content, re.IGNORECASE)
    
    current_readme_violations = 0
    current_readme_nasa = 85.0
    
    if violation_match:
        try:
            current_readme_violations = int(violation_match.group(1).replace(',', ''))
        except ValueError:
            pass
    
    if nasa_match:
        try:
            current_readme_nasa = float(nasa_match.group(1))
        except ValueError:
            pass
    
    # Check for significant changes (>20% for violations, >5% for NASA score)
    violation_change = abs(current_violations - current_readme_violations)
    violation_threshold = max(10, current_readme_violations * 0.2)  # 20% or at least 10
    
    nasa_change = abs(current_nasa * 100 - current_readme_nasa)
    nasa_threshold = 5.0  # 5%
    
    return violation_change > violation_threshold or nasa_change > nasa_threshold


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Update README metrics if significantly changed")
    parser.add_argument('--current-violations', type=int, required=True, help='Current violation count')
    parser.add_argument('--nasa-score', type=float, required=True, help='Current NASA score (0-1)')
    parser.add_argument('--update-if-changed', action='store_true', help='Only update if significantly changed')
    
    args = parser.parse_args()
    
    # Check if update is needed
    if args.update_if_changed and not should_update_readme(args.current_violations, args.nasa_score):
        print("No significant changes detected - README not updated")
        return 0
    
    # Read current README
    readme_content = read_readme()
    if not readme_content:
        print("No README.md found - skipping update")
        return 0
    
    # Update metrics
    updated_content = update_metric_in_readme(readme_content, "violations", f"{args.current_violations:,}+")
    updated_content = update_nasa_score_in_readme(updated_content, args.nasa_score)
    
    # Write updated README
    if updated_content != readme_content:
        Path('README.md').write_text(updated_content)
        print(f"Updated README.md with {args.current_violations} violations and {args.nasa_score:.1%} NASA score")
        return 0
    else:
        print("No changes made to README.md")
        return 0


if __name__ == '__main__':
    sys.exit(main())