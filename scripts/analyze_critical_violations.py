#!/usr/bin/env python3
"""Analyze critical violations from dogfooding results."""

import collections
import json
from pathlib import Path

# Read JSON with UTF-8 encoding
json_path = Path("docs/self-analysis-day2-retry.json")
with open(json_path, encoding='utf-8', errors='ignore') as f:
    data = json.load(f)

violations = data.get("violations", [])

# Filter by severity
critical = [v for v in violations if v.get("severity") == "critical"]
high = [v for v in violations if v.get("severity") == "high"]

print("=" * 80)
print("CRITICAL VIOLATIONS ANALYSIS (75 total)")
print("=" * 80)

# Group critical by type
critical_by_type = collections.defaultdict(list)
for v in critical:
    vtype = v.get("type", "unknown")
    critical_by_type[vtype].append(v)

print("\nCritical Violations by Type:")
print("-" * 80)
for vtype, vlist in sorted(critical_by_type.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"  {vtype:30s}: {len(vlist):3d} violations")

    # Show first 3 examples
    for i, v in enumerate(vlist[:3]):
        filepath = v.get("file_path", "unknown").replace("C:\\Users\\17175\\Desktop\\connascence\\", "")
        line = v.get("line_number", 0)
        message = v.get("message", "")[:60]
        print(f"    {i+1}. {filepath}:{line} - {message}")

print("\n" + "=" * 80)
print("HIGH PRIORITY VIOLATIONS ANALYSIS (307 total)")
print("=" * 80)

# Group high by type
high_by_type = collections.defaultdict(list)
for v in high:
    vtype = v.get("type", "unknown")
    high_by_type[vtype].append(v)

print("\nHigh Priority Violations by Type:")
print("-" * 80)
for vtype, vlist in sorted(high_by_type.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"  {vtype:30s}: {len(vlist):3d} violations")

# Find god objects
print("\n" + "=" * 80)
print("GOD OBJECT VIOLATIONS (96 total)")
print("=" * 80)

god_objects = [v for v in violations if v.get("type") == "god_object"]
god_by_file = collections.defaultdict(list)
for v in god_objects:
    filepath = v.get("file_path", "unknown")
    god_by_file[filepath].append(v)

print("\nGod Objects by File:")
print("-" * 80)
for filepath, vlist in sorted(god_by_file.items(), key=lambda x: len(x[1]), reverse=True)[:15]:
    short_path = filepath.replace("C:\\Users\\17175\\Desktop\\connascence\\", "")
    print(f"  {len(vlist):2d} - {short_path}")

    # Show details of first god object
    if vlist:
        v = vlist[0]
        context = v.get("context", {})
        methods = context.get("method_count", 0)
        loc = context.get("loc", 0)
        print(f"       Methods: {methods}, LOC: {loc}")

# Magic literals (CoM)
print("\n" + "=" * 80)
print("MAGIC LITERAL VIOLATIONS (22,396 total)")
print("=" * 80)

magic_literals = [v for v in violations if v.get("type") == "connascence_of_meaning"]
magic_by_file = collections.defaultdict(list)
for v in magic_literals:
    filepath = v.get("file_path", "unknown")
    magic_by_file[filepath].append(v)

print("\nTop Files with Magic Literals:")
print("-" * 80)
for filepath, vlist in sorted(magic_by_file.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
    short_path = filepath.replace("C:\\Users\\17175\\Desktop\\connascence\\", "")
    print(f"  {len(vlist):4d} - {short_path}")

print("\n" + "=" * 80)
print("ACTIONABLE PRIORITIES FOR DAY 3")
print("=" * 80)
print("\n1. Fix Critical Violations (75 total)")
print("   - Focus on types with most instances")
print("   - Start with unified_analyzer.py")
print("\n2. Reduce God Objects (96 total)")
print("   - Target files with 2+ god objects")
print("   - Refactor by extracting specialized classes")
print("\n3. Address Magic Literals (22,396 total)")
print("   - Extract constants for critical/high severity files")
print("   - Focus on unified_analyzer.py first")
print("\n4. Fix MECEAnalyzer.analyze_directory method")
print("   - Add missing method to enable duplication detection")
print("\n" + "=" * 80)
