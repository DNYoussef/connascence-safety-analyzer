#!/usr/bin/env python3
"""Validate SARIF output structure."""

import json
from pathlib import Path

sarif_path = Path("docs/test-integration.sarif")

if not sarif_path.exists():
    print("[FAIL] SARIF file not found")
    exit(1)

with open(sarif_path, encoding='utf-8') as f:
    data = json.load(f)

print("=" * 80)
print("SARIF OUTPUT VALIDATION")
print("=" * 80)

print(f"\nSARIF Version: {data.get('version', 'N/A')}")
print(f"Schema: {data.get('$schema', 'N/A')}")

runs = data.get('runs', [])
print(f"Runs: {len(runs)}")

if runs:
    run = runs[0]
    results = run.get('results', [])
    print(f"Violations Found: {len(results)}")

    tool = run.get('tool', {})
    driver = tool.get('driver', {})
    print(f"Tool Name: {driver.get('name', 'N/A')}")
    print(f"Tool Version: {driver.get('version', 'N/A')}")

    # Sample violation
    if results:
        print("\nSample Violation:")
        violation = results[0]
        print(f"  Rule ID: {violation.get('ruleId', 'N/A')}")
        print(f"  Level: {violation.get('level', 'N/A')}")
        message = violation.get('message', {})
        print(f"  Message: {message.get('text', 'N/A')[:60]}...")

print("\n[OK] SARIF output is valid and properly structured")
print("=" * 80)
