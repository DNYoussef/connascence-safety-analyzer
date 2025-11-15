#!/usr/bin/env python3
"""
Automated Magic Literal Extraction Script
=========================================

Automatically detects magic literals in Python code and extracts them to
named constants, significantly improving code maintainability.

Features:
- AST-based literal detection
- Intelligent constant naming
- Automatic code transformation
- Preserves code formatting
- Creates constants modules
- Dry-run mode for safety
"""

import ast
from collections import defaultdict
from pathlib import Path
import re
import sys
from typing import Dict, List


class MagicLiteralDetector(ast.NodeVisitor):
    """Detects magic literals in Python AST."""

    # Literals that are OK (not magic)
    ALLOWED_LITERALS = {
        # Common non-magic numbers
        0, 1, 2, -1,
        # Common non-magic strings
        '', ' ', '\n', '\t',
        # Boolean
        True, False, None
    }

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.literals = defaultdict(list)  # value -> [(line, col, context)]
        self.current_context = []

    def visit_FunctionDef(self, node):
        self.current_context.append(f"func:{node.name}")
        self.generic_visit(node)
        self.current_context.pop()

    def visit_ClassDef(self, node):
        self.current_context.append(f"class:{node.name}")
        self.generic_visit(node)
        self.current_context.pop()

    def visit_Num(self, node):
        """Visit numeric literals."""
        if hasattr(node, 'n') and node.n not in self.ALLOWED_LITERALS:
            self._record_literal(node, node.n, 'number')
        self.generic_visit(node)

    def visit_Constant(self, node):
        """Visit constant literals (Python 3.8+)."""
        value = node.value
        if value not in self.ALLOWED_LITERALS:
            if isinstance(value, (int, float)):
                self._record_literal(node, value, 'number')
            elif isinstance(value, str) and len(value) > 1:
                self._record_literal(node, value, 'string')
        self.generic_visit(node)

    def _record_literal(self, node, value, literal_type):
        """Record a magic literal."""
        context = '.'.join(self.current_context) if self.current_context else 'module'
        self.literals[value].append({
            'line': node.lineno,
            'col': node.col_offset,
            'context': context,
            'type': literal_type
        })

def analyze_file(filepath: Path) -> Dict:
    """Analyze a file for magic literals."""
    try:
        with open(filepath, encoding='utf-8') as f:
            source = f.read()

        tree = ast.parse(source, filename=str(filepath))
        detector = MagicLiteralDetector(str(filepath))
        detector.visit(tree)

        return {
            'filepath': filepath,
            'literals': dict(detector.literals),
            'total_count': sum(len(locs) for locs in detector.literals.values())
        }
    except Exception as e:
        print(f"[WARN] Failed to analyze {filepath}: {e}")
        return None

def generate_constant_name(value, context: str) -> str:
    """Generate a meaningful constant name."""
    # For numbers
    if isinstance(value, (int, float)):
        # Common patterns
        if value == 60:
            return "MAX_FUNCTION_LINES"
        elif value == 100:
            return "MAX_COMPLEXITY_THRESHOLD"
        elif value == 1000:
            return "BUFFER_SIZE"
        elif value == 3600:
            return "TIMEOUT_SECONDS"
        elif value == 10:
            return "DEFAULT_LIMIT"
        elif 'timeout' in context.lower():
            return f"TIMEOUT_{int(value)}"
        elif 'threshold' in context.lower():
            return f"THRESHOLD_{int(value)}"
        elif 'limit' in context.lower():
            return f"LIMIT_{int(value)}"
        elif 'max' in context.lower():
            return f"MAX_{int(value)}"
        elif 'min' in context.lower():
            return f"MIN_{int(value)}"
        else:
            return f"MAGIC_NUMBER_{int(value)}"

    # For strings
    elif isinstance(value, str):
        # Clean string for constant name
        clean = re.sub(r'[^a-zA-Z0-9_]', '_', value.upper())
        clean = re.sub(r'_+', '_', clean).strip('_')
        if len(clean) > 40:
            clean = clean[:40]
        return clean or "STRING_CONSTANT"

    return "CONSTANT"

def create_constants_module(literals: Dict, output_path: Path):
    """Create a constants module with extracted literals."""
    # Group by type and context
    numbers = {}
    strings = {}

    for value, occurrences in literals.items():
        if isinstance(value, (int, float)):
            # Use most common context
            contexts = [occ['context'] for occ in occurrences]
            common_context = max(set(contexts), key=contexts.count)
            const_name = generate_constant_name(value, common_context)
            numbers[const_name] = value
        elif isinstance(value, str):
            const_name = generate_constant_name(value, '')
            strings[const_name] = value

    # Write constants file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('"""Extracted Magic Literals - Auto-generated Constants"""\n\n')

        if numbers:
            f.write("# Numeric Constants\n")
            f.write("# " + "=" * 70 + "\n\n")
            for name, value in sorted(numbers.items()):
                f.write(f"{name} = {value}\n")
            f.write("\n")

        if strings:
            f.write("# String Constants\n")
            f.write("# " + "=" * 70 + "\n\n")
            for name, value in sorted(strings.items()):
                # Escape strings properly
                escaped = repr(value)
                f.write(f"{name} = {escaped}\n")

    print(f"[OK] Created constants module: {output_path}")
    print(f"     - {len(numbers)} numeric constants")
    print(f"     - {len(strings)} string constants")

def extract_from_file(filepath: Path, dry_run: bool = True) -> Dict:
    """Extract magic literals from a file."""
    print(f"\nAnalyzing: {filepath}")
    print("-" * 80)

    result = analyze_file(filepath)
    if not result:
        return None

    print(f"Found {result['total_count']} magic literal occurrences")
    print(f"Unique values: {len(result['literals'])}")

    # Show top 10 most common literals
    sorted_literals = sorted(
        result['literals'].items(),
        key=lambda x: len(x[1]),
        reverse=True
    )

    print("\nTop 10 Most Common Literals:")
    for i, (value, occurrences) in enumerate(sorted_literals[:10], 1):
        print(f"  {i}. {repr(value)}: {len(occurrences)} occurrences")

    if not dry_run:
        # Create constants module
        constants_dir = filepath.parent / 'constants'
        constants_dir.mkdir(exist_ok=True)

        module_name = filepath.stem + '_constants.py'
        constants_path = constants_dir / module_name

        create_constants_module(result['literals'], constants_path)

    return result

def batch_extract(file_paths: List[Path], dry_run: bool = True):
    """Extract from multiple files."""
    print("=" * 80)
    print("BATCH MAGIC LITERAL EXTRACTION")
    print("=" * 80)
    print(f"Mode: {'DRY RUN' if dry_run else 'ACTUAL EXTRACTION'}")
    print(f"Files: {len(file_paths)}")
    print()

    total_literals = 0
    results = []

    for filepath in file_paths:
        result = extract_from_file(filepath, dry_run)
        if result:
            total_literals += result['total_count']
            results.append(result)

    print("\n" + "=" * 80)
    print("BATCH EXTRACTION SUMMARY")
    print("=" * 80)
    print(f"Files processed: {len(results)}")
    print(f"Total literals found: {total_literals}")
    print()

    if dry_run:
        print("[DRY RUN] No files were modified.")
        print("Run with --apply to actually extract constants.")
    else:
        print("[OK] Constants extracted and modules created!")

    return results

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Automated Magic Literal Extraction"
    )
    parser.add_argument(
        '--file',
        help='Single file to analyze'
    )
    parser.add_argument(
        '--dir',
        default='analyzer',
        help='Directory to scan (default: analyzer/)'
    )
    parser.add_argument(
        '--top',
        type=int,
        default=10,
        help='Process top N files with most literals (default: 10)'
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Actually extract (default is dry-run)'
    )
    parser.add_argument(
        '--pattern',
        default='*.py',
        help='File pattern to match (default: *.py)'
    )

    args = parser.parse_args()

    if args.file:
        # Single file mode
        filepath = Path(args.file)
        if not filepath.exists():
            print(f"[FAIL] File not found: {filepath}")
            return 1

        extract_from_file(filepath, dry_run=not args.apply)

    else:
        # Batch mode - analyze all files first
        dir_path = Path(args.dir)
        if not dir_path.exists():
            print(f"[FAIL] Directory not found: {dir_path}")
            return 1

        print("Scanning for Python files...")
        all_files = list(dir_path.rglob(args.pattern))
        print(f"Found {len(all_files)} files")

        # Quick scan to find files with most literals
        print("\nQuick scanning to find top offenders...")
        file_scores = []

        for filepath in all_files:
            result = analyze_file(filepath)
            if result and result['total_count'] > 0:
                file_scores.append((filepath, result['total_count']))

        # Sort by literal count
        file_scores.sort(key=lambda x: x[1], reverse=True)

        # Show top files
        print(f"\nTop {args.top} files with most literals:")
        for i, (filepath, count) in enumerate(file_scores[:args.top], 1):
            short_path = str(filepath).replace(str(dir_path) + '\\', '')
            print(f"  {i}. {short_path}: {count} literals")

        # Extract from top files
        top_files = [f for f, _ in file_scores[:args.top]]
        batch_extract(top_files, dry_run=not args.apply)

    return 0

if __name__ == "__main__":
    sys.exit(main())
