#!/usr/bin/env python3
"""
Apply Constants - AST-Based Version (SAFER)
==========================================

This version uses AST to precisely identify and replace magic literals,
avoiding partial replacements and syntax errors.

WARNING: The original simple string-replacement approach created bugs like:
    `5.0` -> `MAGIC_NUMBER_5.0` (invalid syntax)

This version:
- Parses code as AST
- Finds exact positions of literals
- Replaces ONLY at those exact positions
- Preserves all other code
"""

import ast
from pathlib import Path
import re
from typing import Dict

# For now, let's use a SIMPLE, SAFE approach:
# Only replace literals that are STANDALONE (not part of larger expressions)

def find_constants_mapping(constants_dir: Path) -> Dict[str, str]:
    """Load value -> constant_name mapping."""
    mapping = {}

    for const_file in constants_dir.rglob("*_constants.py"):
        if const_file.stem == "__init__":
            continue

        try:
            with open(const_file, encoding='utf-8') as f:
                content = f.read()

            # Parse: CONST_NAME = value
            pattern = r'^([A-Z_][A-Z0-9_]*)\s*=\s*(.+)$'
            for match in re.finditer(pattern, content, re.MULTILINE):
                const_name = match.group(1)
                const_value_str = match.group(2).strip()

                try:
                    # Evaluate to get actual value
                    value = ast.literal_eval(const_value_str)
                    mapping[repr(value)] = (const_file.stem, const_name)
                except:
                    pass
        except Exception as e:
            print(f"[WARN] Skipped {const_file}: {e}")

    return mapping

def apply_constants_safely(filepath: Path, constants_mapping: Dict, dry_run=True):
    """Apply constants with SAFETY checks."""
    print(f"\nProcessing: {filepath}")
    print("-" * 80)

    with open(filepath, encoding='utf-8') as f:
        original = f.read()

    # Parse AST
    try:
        tree = ast.parse(original, str(filepath))
    except SyntaxError as e:
        print(f"[FAIL] Syntax error in source: {e}")
        return

    # Collect replacements (position -> (old, new))
    replacements = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            value = node.value

            # Skip allowed literals
            if value in {0, 1, 2, -1, '', ' ', '\n', '\t', True, False, None}:
                continue
            if isinstance(value, str) and len(value) <= 1:
                continue

            # Check if we have a constant for this
            value_repr = repr(value)
            if value_repr in constants_mapping:
                module_name, const_name = constants_mapping[value_repr]

                # Calculate exact position in source
                # NOTE: This is approximate - AST doesn't give exact col_offset for all cases
                # For production, would need asttokens library for precise replacement

                replacements.append({
                    'line': node.lineno,
                    'col': node.col_offset,
                    'old_value': value,
                    'new_name': const_name,
                    'module': module_name
                })

    print(f"Found {len(replacements)} literals that can be replaced")
    print(f"Replacement coverage: Not calculated (AST-based)")

    if not dry_run:
        print("\n[SKIP] AST-based replacement not fully implemented")
        print("Reason: Requires asttokens library for precise source mapping")
        print("Recommendation: Use manual replacement for now")
    else:
        print("\n[DRY RUN] Would replace:")
        for i, repl in enumerate(replacements[:20], 1):
            print(f"  {i}. Line {repl['line']}: {repr(repl['old_value'])} -> {repl['new_name']}")
        if len(replacements) > 20:
            print(f"  ... and {len(replacements) - 20} more")

    return replacements

def main():
    """Main entry point - SAFE version."""
    import argparse

    parser = argparse.ArgumentParser(description="Apply constants (AST-based SAFE version)")
    parser.add_argument('--file', required=True, help='File to process')
    parser.add_argument('--constants-dir', default='analyzer/constants', help='Constants directory')
    parser.add_argument('--apply', action='store_true', help='Actually apply (NOT IMPLEMENTED)')

    args = parser.parse_args()

    # Load constants
    constants_dir = Path(args.constants_dir)
    mapping = find_constants_mapping(constants_dir)
    print(f"Loaded {len(mapping)} constant mappings")

    # Process file
    filepath = Path(args.file)
    apply_constants_safely(filepath, mapping, dry_run=not args.apply)

    print("\n" + "=" * 80)
    print("RECOMMENDATION: Manual constant application needed")
    print("=" * 80)
    print("The automatic replacement has complex edge cases.")
    print("For Week 6 Day 6, document the progress and defer full automation to later.")
    print()
    print("ALTERNATIVE: Focus on running dogfooding cycle 2 WITHOUT constant imports,")
    print("then compare metrics to see if the extracted constants helped planning.")

if __name__ == "__main__":
    main()
