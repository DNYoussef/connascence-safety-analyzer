#!/usr/bin/env python3
"""Consolidate duplicate constants across modules."""

from collections import defaultdict
from pathlib import Path
import re


def scan_constants_modules(base_dir: Path):
    """Scan all constants modules and find duplicates."""
    print("Scanning constants modules...")
    print("=" * 80)

    # Find all constants files
    constants_files = list(base_dir.rglob("*_constants.py"))
    print(f"Found {len(constants_files)} constants modules\n")

    # Parse constants from each file
    all_constants = defaultdict(list)  # value -> [(module, name)]

    for filepath in constants_files:
        module_name = filepath.stem
        try:
            with open(filepath, encoding='utf-8') as f:
                content = f.read()

            # Extract constant assignments
            pattern = r'^([A-Z_][A-Z0-9_]*)\s*=\s*(.+)$'
            for match in re.finditer(pattern, content, re.MULTILINE):
                const_name = match.group(1)
                const_value = match.group(2).strip()
                all_constants[const_value].append((module_name, const_name))
        except Exception as e:
            print(f"[WARN] Failed to parse {filepath}: {e}")

    # Find duplicates
    duplicates = {k: v for k, v in all_constants.items() if len(v) > 1}

    print(f"Total unique constant values: {len(all_constants)}")
    print(f"Duplicate constant values: {len(duplicates)}\n")

    # Show top duplicates
    print("Top 20 Most Duplicated Constants:")
    print("-" * 80)

    sorted_dups = sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)
    for i, (value, occurrences) in enumerate(sorted_dups[:20], 1):
        print(f"{i}. {value[:50]:50s} - {len(occurrences)} modules")
        for module, name in occurrences[:3]:
            print(f"     - {module}.{name}")
        if len(occurrences) > 3:
            print(f"     ... and {len(occurrences) - 3} more")
        print()

    return all_constants, duplicates

def create_master_constants(duplicates, output_path: Path):
    """Create master constants file for common duplicates."""
    print("\nCreating master constants module...")
    print("=" * 80)

    # Extract highly duplicated constants (used in 3+ modules)
    common_constants = {
        k: v for k, v in duplicates.items()
        if len(v) >= 3
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('"""Master Constants - Common Values Across Modules"""\n')
        f.write('# Auto-generated - Consolidates frequently used constants\n\n')

        # Group by type
        numbers = []
        strings = []

        for value, occurrences in sorted(common_constants.items(), key=lambda x: len(x[1]), reverse=True):
            # Use most common name
            names = [name for _, name in occurrences]
            common_name = max(set(names), key=names.count)

            if value.replace('.', '').replace('-', '').isdigit():
                numbers.append((common_name, value, len(occurrences)))
            elif value.startswith(("'", '"')):
                strings.append((common_name, value, len(occurrences)))

        if numbers:
            f.write("# Numeric Constants (used in multiple modules)\n")
            f.write("# " + "=" * 70 + "\n\n")
            for name, value, count in numbers:
                f.write(f"{name} = {value}  # Used in {count} modules\n")
            f.write("\n")

        if strings:
            f.write("# String Constants (used in multiple modules)\n")
            f.write("# " + "=" * 70 + "\n\n")
            for name, value, count in strings:
                f.write(f"{name} = {value}  # Used in {count} modules\n")

    print(f"[OK] Master constants created: {output_path}")
    print(f"     - {len(numbers)} numeric constants")
    print(f"     - {len(strings)} string constants")
    print(f"     - Total: {len(common_constants)} common constants")

def main():
    """Main entry point."""
    base_dir = Path("analyzer")

    # Scan and analyze
    all_constants, duplicates = scan_constants_modules(base_dir)

    # Create master constants
    master_path = base_dir / "constants" / "master_constants.py"
    master_path.parent.mkdir(exist_ok=True)
    create_master_constants(duplicates, master_path)

    print("\n" + "=" * 80)
    print("CONSOLIDATION COMPLETE")
    print("=" * 80)
    print(f"\nNext steps:")
    print("1. Review master_constants.py")
    print("2. Update module imports to use master constants")
    print("3. Remove duplicates from individual modules")

if __name__ == "__main__":
    main()
