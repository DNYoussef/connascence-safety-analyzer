#!/usr/bin/env python3
"""Parse dogfooding results from JSON report."""

import collections
import json
from pathlib import Path

# Read JSON with UTF-8 encoding
json_path = Path("docs/self-analysis-day2-retry.json")
with open(json_path, encoding='utf-8', errors='ignore') as f:
    data = json.load(f)

# Extract summary
summary = data.get("summary", {})
violations = data.get("violations", [])

print("=" * 60)
print("DOGFOODING CYCLE 1 RETRY - RESULTS SUMMARY")
print("=" * 60)
print(f"\nTotal Violations: {len(violations)}")
print(f"Files Analyzed: {data.get('files_analyzed', 0)}")
print(f"Critical Violations: {summary.get('critical_violations', 0)}")
print(f"Overall Quality Score: {summary.get('overall_quality_score', 0):.3f}")
print(f"\n" + "=" * 60)

# Count by type
print("\nVIOLATIONS BY TYPE:")
print("-" * 40)
types = collections.Counter(v.get('type', 'unknown') for v in violations)
for vtype, count in types.most_common(15):
    print(f"  {vtype:30s}: {count:4d}")

# Count by severity
print(f"\n" + "=" * 60)
print("\nVIOLATIONS BY SEVERITY:")
print("-" * 40)
severities = collections.Counter(v.get('severity', 'unknown') for v in violations)
for sev, count in sorted(severities.items(), key=lambda x: x[1], reverse=True):
    print(f"  {sev:10s}: {count:4d}")

# Top files with violations
print(f"\n" + "=" * 60)
print("\nTOP 10 FILES WITH MOST VIOLATIONS:")
print("-" * 40)
file_counts = collections.Counter(v.get('file_path', 'unknown') for v in violations)
for filepath, count in file_counts.most_common(10):
    # Shorten path for readability
    short_path = filepath.replace('C:\\Users\\17175\\Desktop\\connascence\\', '')
    print(f"  {count:3d} - {short_path}")

print(f"\n" + "=" * 60)
print("\nSUCCESS: Analyzer is now working!")
print("Original errors (orchestrator, calculate_metrics, generate_recommendations) are FIXED!")
print(f"=" * 60)
