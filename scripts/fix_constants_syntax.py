#!/usr/bin/env python3
"""
Fix Constants Syntax Errors
===========================

Automatically fixes Python syntax errors in extracted constants files:
1. Replaces dots in variable names with underscores
2. Removes assignments to reserved keywords (True, False, None)
3. Validates fixed files with py_compile

Usage:
    python scripts/fix_constants_syntax.py --file path/to/constants.py
    python scripts/fix_constants_syntax.py --all  # Fix all affected files
"""

import keyword
from pathlib import Path
import py_compile
import re
import shutil
import sys
from typing import List, Tuple

# List of files with known syntax errors
AFFECTED_FILES = [
    "analyzer/literal_constants/check_connascence_constants.py",
    "analyzer/literal_constants/context_analyzer_constants.py",
    "analyzer/literal_constants/core_constants.py",
    "analyzer/literal_constants/constants_constants.py",
    "analyzer/enterprise/constants/nasa_pot10_enhanced_constants.py",
    "analyzer/enterprise/sixsigma/constants/analyzer_constants.py",
    "analyzer/quality_gates/constants/unified_quality_gate_constants.py",
    "analyzer/reporting/constants/coordinator_constants.py",
    "analyzer/reporting/constants/sarif_constants.py",
    "analyzer/streaming/constants/dashboard_reporter_constants.py",
    "analyzer/theater_detection/constants/detector_constants.py",
    "analyzer/theater_detection/constants/validator_constants.py",
]

def is_valid_identifier(name: str) -> bool:
    """Check if name is a valid Python identifier."""
    if not name:
        return False

    # Check for reserved keywords
    if keyword.iskeyword(name) or name in ['True', 'False', 'None']:
        return False

    # Check starts with letter or underscore
    if not (name[0].isalpha() or name[0] == '_'):
        return False

    # Check contains only alphanumeric and underscores (no dots!)
    if not all(c.isalnum() or c == '_' for c in name):
        return False

    return True

def sanitize_identifier(name: str) -> str:
    """Sanitize a name to be a valid Python identifier."""
    # Replace dots with underscores
    name = name.replace('.', '_')

    # Replace other invalid characters with underscores
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name)

    # Ensure starts with letter or underscore
    if name and name[0].isdigit():
        name = f'CONST_{name}'

    # Handle reserved keywords by prefixing
    if keyword.iskeyword(name) or name in ['True', 'False', 'None']:
        name = f'CONST_{name}'

    return name

def backup_file(filepath: Path) -> Path:
    """Create backup of file."""
    backup_path = filepath.with_suffix(filepath.suffix + '.backup')
    shutil.copy2(filepath, backup_path)
    return backup_path

def fix_constants_file(filepath: Path, dry_run: bool = False) -> Tuple[int, List[str]]:
    """
    Fix syntax errors in constants file.

    Returns:
        (fixes_applied, errors_found)
    """
    print(f"\nProcessing: {filepath}")
    print("-" * 80)

    if not filepath.exists():
        print(f"[SKIP] File not found: {filepath}")
        return 0, [f"File not found: {filepath}"]

    # Read original content
    try:
        with open(filepath, encoding='utf-8') as f:
            original_lines = f.readlines()
    except Exception as e:
        print(f"[FAIL] Cannot read file: {e}")
        return 0, [f"Read error: {e}"]

    # Try to compile original to see if it actually has errors
    try:
        py_compile.compile(filepath, doraise=True)
        print("[OK] File already valid, no fixes needed")
        return 0, []
    except py_compile.PyCompileError as e:
        print(f"[DETECTED] Syntax error: {e.msg}")

    # Create backup
    if not dry_run:
        backup_path = backup_file(filepath)
        print(f"[BACKUP] Created: {backup_path}")

    # Process line by line
    fixed_lines = []
    fixes_applied = 0
    errors_found = []

    for line_num, line in enumerate(original_lines, 1):
        # Skip comments and blank lines
        if line.strip().startswith('#') or not line.strip():
            fixed_lines.append(line)
            continue

        # Check for constant assignment pattern
        if '=' in line and not line.strip().startswith('import'):
            parts = line.split('=', 1)
            if len(parts) == 2:
                const_name = parts[0].strip()
                const_value = parts[1].strip()

                # Check if it's a constant definition (all caps or starts with uppercase)
                if const_name and (const_name.isupper() or const_name[0].isupper()):
                    original_name = const_name

                    # Check if name is valid
                    if not is_valid_identifier(const_name):
                        # Sanitize the name
                        const_name = sanitize_identifier(const_name)
                        fixes_applied += 1

                        print(f"  Line {line_num}: {original_name} -> {const_name}")

                    # Check if assigning to reserved keyword
                    if original_name in ['True', 'False', 'None']:
                        print(f"  Line {line_num}: SKIP assignment to {original_name}")
                        # Skip this line entirely
                        continue

                    # Reconstruct line
                    indent = len(line) - len(line.lstrip())
                    fixed_line = ' ' * indent + f"{const_name} = {const_value}"
                    fixed_lines.append(fixed_line)
                    continue

        # Keep line as-is
        fixed_lines.append(line)

    # Write fixed version
    if not dry_run:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(fixed_lines)
            print(f"[WRITE] Fixed version written")
        except Exception as e:
            print(f"[FAIL] Cannot write file: {e}")
            # Restore backup
            shutil.copy2(backup_path, filepath)
            return 0, [f"Write error: {e}"]

        # Validate fixed version
        try:
            py_compile.compile(filepath, doraise=True)
            print(f"[OK] Validation passed - file compiles successfully")
        except py_compile.PyCompileError as e:
            print(f"[FAIL] Validation failed: {e.msg}")
            errors_found.append(f"Line {e.exc_value.lineno}: {e.msg}")

            # Restore backup on validation failure
            print(f"[RESTORE] Restoring backup due to validation failure")
            shutil.copy2(backup_path, filepath)
            return 0, errors_found

        print(f"[SUCCESS] {fixes_applied} fixes applied and validated")
    else:
        print(f"[DRY RUN] Would apply {fixes_applied} fixes")

    return fixes_applied, errors_found

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Fix constants syntax errors")
    parser.add_argument(
        '--file',
        help='Single file to fix'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Fix all known affected files'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be fixed without applying changes'
    )

    args = parser.parse_args()

    if not args.file and not args.all:
        parser.error("Must specify either --file or --all")

    print("=" * 80)
    print("CONSTANTS SYNTAX ERROR FIX SCRIPT")
    print("=" * 80)
    print(f"Mode: {'DRY RUN' if args.dry_run else 'ACTUAL FIX'}")
    print()

    # Determine files to process
    if args.file:
        files_to_process = [Path(args.file)]
    else:
        files_to_process = [Path(f) for f in AFFECTED_FILES]

    # Process each file
    total_fixes = 0
    total_errors = 0
    results = []

    for filepath in files_to_process:
        fixes, errors = fix_constants_file(filepath, dry_run=args.dry_run)
        total_fixes += fixes
        total_errors += len(errors)

        results.append({
            'file': filepath,
            'fixes': fixes,
            'errors': errors,
            'status': 'OK' if not errors else 'FAIL'
        })

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    for result in results:
        status_icon = '[OK]' if result['status'] == 'OK' else '[FAIL]'
        print(f"{status_icon} {result['file']}")
        if result['fixes'] > 0:
            print(f"       Fixes applied: {result['fixes']}")
        if result['errors']:
            for error in result['errors']:
                print(f"       Error: {error}")

    print()
    print(f"Total files processed: {len(results)}")
    print(f"Total fixes applied: {total_fixes}")
    print(f"Total errors remaining: {total_errors}")
    print()

    if args.dry_run:
        print("[DRY RUN] No changes were made.")
        print("Run without --dry-run to apply fixes.")
    elif total_errors == 0:
        print("[SUCCESS] All files fixed and validated!")
    else:
        print("[WARNING] Some files still have errors.")
        print("Manual intervention may be required.")

    return 0 if total_errors == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
