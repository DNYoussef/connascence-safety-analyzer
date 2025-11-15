#!/usr/bin/env python3
"""
Apply Constants Import Rewrite Script
=====================================

Automatically updates source files to import and use extracted constants
from the analyzer.constants modules, replacing magic literals.

Features:
- Smart import addition (avoids duplicates)
- AST-based literal replacement
- Dry-run mode for safety
- Context-aware constant selection
- Preserves code formatting where possible

Usage:
    # Dry-run on single file
    python scripts/apply_constants.py --file analyzer/unified_analyzer.py

    # Apply to single file
    python scripts/apply_constants.py --file analyzer/unified_analyzer.py --apply

    # Batch processing top files
    python scripts/apply_constants.py --dir analyzer --top 5 --apply
"""

import ast
from collections import defaultdict
from pathlib import Path
import re
import sys
from typing import Dict, List, Optional, Tuple


class ConstantImporter:
    """Manages importing and using extracted constants."""

    def __init__(self, constants_dir: Path):
        self.constants_dir = constants_dir
        self.available_constants = self._load_all_constants()

    def _load_all_constants(self) -> Dict[str, Dict]:
        """Load all available constants from constants modules."""
        constants = {}

        # Load from all *_constants.py files
        for constants_file in self.constants_dir.rglob("*_constants.py"):
            if constants_file.stem == "__init__":
                continue

            module_name = constants_file.stem
            module_constants = {}

            try:
                with open(constants_file, encoding='utf-8') as f:
                    content = f.read()

                # Parse constant assignments
                pattern = r'^([A-Z_][A-Z0-9_]*)\s*=\s*(.+)$'
                for match in re.finditer(pattern, content, re.MULTILINE):
                    const_name = match.group(1)
                    const_value = match.group(2).strip()

                    # Evaluate the value to get the actual literal
                    try:
                        # Handle string literals
                        if const_value.startswith(("'", '"')):
                            value = ast.literal_eval(const_value)
                        # Handle numeric literals
                        elif const_value.replace('.', '').replace('-', '').isdigit():
                            value = ast.literal_eval(const_value)
                        else:
                            continue

                        module_constants[repr(value)] = const_name
                    except:
                        continue

                constants[module_name] = module_constants
            except Exception as e:
                print(f"[WARN] Failed to load {constants_file}: {e}")

        return constants

    def find_constant_for_literal(self, literal_value, source_file: Path) -> Optional[Tuple[str, str]]:
        """Find the best constant name for a literal value."""
        literal_repr = repr(literal_value)

        # Priority 1: Same-named constants module (e.g., unified_analyzer.py -> unified_analyzer_constants)
        source_name = source_file.stem
        preferred_module = f"{source_name}_constants"

        if preferred_module in self.available_constants:
            if literal_repr in self.available_constants[preferred_module]:
                return (preferred_module, self.available_constants[preferred_module][literal_repr])

        # Priority 2: Master constants (common values)
        if "master_constants" in self.available_constants:
            if literal_repr in self.available_constants["master_constants"]:
                return ("master_constants", self.available_constants["master_constants"][literal_repr])

        # Priority 3: Any other constants module
        for module_name, constants in self.available_constants.items():
            if literal_repr in constants:
                return (module_name, constants[literal_repr])

        return None

class ConstantReplacer:
    """Replaces magic literals with constant references."""

    def __init__(self, importer: ConstantImporter):
        self.importer = importer
        self.replacements = []
        self.imports_needed = set()

    def process_file(self, filepath: Path, dry_run: bool = True) -> Dict:
        """Process a file to replace literals with constants."""
        print(f"\nProcessing: {filepath}")
        print("-" * 80)

        try:
            with open(filepath, encoding='utf-8') as f:
                original_content = f.read()

            # Parse AST
            tree = ast.parse(original_content, filename=str(filepath))

            # Find all magic literals
            literals = self._find_literals(tree)

            print(f"Found {len(literals)} magic literal occurrences")

            # Map literals to constants
            replacements = []
            imports_needed = defaultdict(set)

            for literal_value, positions in literals.items():
                constant_info = self.importer.find_constant_for_literal(literal_value, filepath)

                if constant_info:
                    module_name, const_name = constant_info
                    replacements.append({
                        'literal': literal_value,
                        'constant': const_name,
                        'module': module_name,
                        'count': len(positions)
                    })
                    imports_needed[module_name].add(const_name)

            print(f"\nReplacements found: {len(replacements)}")
            for repl in replacements[:10]:  # Show first 10
                print(f"  {repr(repl['literal'])} -> {repl['constant']} ({repl['count']} occurrences)")

            if len(replacements) > 10:
                print(f"  ... and {len(replacements) - 10} more")

            # Generate new content
            if not dry_run and replacements:
                new_content = self._apply_replacements(
                    original_content,
                    replacements,
                    imports_needed
                )

                # Write back
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                print(f"\n[OK] Applied {len(replacements)} replacements")
            elif dry_run:
                print("\n[DRY RUN] No changes made")

            return {
                'filepath': filepath,
                'literals_found': len(literals),
                'replacements': len(replacements),
                'imports_needed': dict(imports_needed)
            }

        except Exception as e:
            print(f"[FAIL] Error processing {filepath}: {e}")
            return None

    def _find_literals(self, tree: ast.AST) -> Dict:
        """Find all magic literals in AST."""
        literals = defaultdict(list)

        class LiteralVisitor(ast.NodeVisitor):
            ALLOWED_LITERALS = {0, 1, 2, -1, '', ' ', '\n', '\t', True, False, None}

            def visit_Constant(self, node):
                value = node.value
                if value not in self.ALLOWED_LITERALS:
                    if isinstance(value, (int, float, str)):
                        if not (isinstance(value, str) and len(value) <= 1):
                            literals[value].append((node.lineno, node.col_offset))
                self.generic_visit(node)

        visitor = LiteralVisitor()
        visitor.visit(tree)

        return dict(literals)

    def _apply_replacements(self, content: str, replacements: List[Dict], imports_needed: Dict) -> str:
        """Apply replacements to content."""
        lines = content.split('\n')

        # Step 1: Add imports at top (after docstring and existing imports)
        import_section = self._generate_imports(imports_needed)

        # Find where to insert imports
        insert_line = 0
        in_docstring = False
        for i, line in enumerate(lines):
            stripped = line.strip()

            # Skip docstring
            if i == 0 and stripped.startswith(('"""', "'''")):
                in_docstring = True
            if in_docstring:
                if stripped.endswith(('"""', "'''")):
                    in_docstring = False
                    insert_line = i + 1
                continue

            # Skip existing imports
            if stripped.startswith(('import ', 'from ')):
                insert_line = i + 1
            elif stripped and not stripped.startswith('#'):
                break

        # Insert imports
        if import_section:
            lines.insert(insert_line, import_section)
            lines.insert(insert_line + 1, '')  # Blank line

        # Step 2: Replace literals with constants (regex-based for precision)
        new_content = '\n'.join(lines)

        for repl in replacements:
            literal_value = repl['literal']
            const_name = repl['constant']

            # Use regex with word boundaries to avoid partial replacements
            if isinstance(literal_value, (int, float)):
                # For numbers, match whole number (handle floats correctly)
                pattern = r'\b' + re.escape(str(literal_value)) + r'\b'
            elif isinstance(literal_value, str):
                # For strings, match exact quoted string
                pattern = re.escape(repr(literal_value))
            else:
                continue

            new_content = re.sub(pattern, const_name, new_content)

        return new_content

    def _generate_imports(self, imports_needed: Dict) -> str:
        """Generate import statements."""
        if not imports_needed:
            return ""

        import_lines = []
        for module_name, constants in sorted(imports_needed.items()):
            constants_sorted = sorted(constants)

            # Group imports nicely
            if len(constants_sorted) <= 5:
                import_lines.append(
                    f"from analyzer.constants.{module_name} import {', '.join(constants_sorted)}"
                )
            else:
                # Multi-line import
                import_lines.append(f"from analyzer.constants.{module_name} import (")
                for const in constants_sorted[:-1]:
                    import_lines.append(f"    {const},")
                import_lines.append(f"    {constants_sorted[-1]}")
                import_lines.append(")")

        return '\n'.join(import_lines)

def batch_process(file_paths: List[Path], importer: ConstantImporter, dry_run: bool = True):
    """Process multiple files."""
    print("=" * 80)
    print("BATCH CONSTANT APPLICATION")
    print("=" * 80)
    print(f"Mode: {'DRY RUN' if dry_run else 'ACTUAL APPLICATION'}")
    print(f"Files: {len(file_paths)}")
    print()

    replacer = ConstantReplacer(importer)
    results = []

    for filepath in file_paths:
        result = replacer.process_file(filepath, dry_run=dry_run)
        if result:
            results.append(result)

    # Summary
    print("\n" + "=" * 80)
    print("BATCH PROCESSING SUMMARY")
    print("=" * 80)

    total_literals = sum(r['literals_found'] for r in results)
    total_replacements = sum(r['replacements'] for r in results)

    print(f"Files processed: {len(results)}")
    print(f"Total literals found: {total_literals}")
    print(f"Total replacements: {total_replacements}")
    print(f"Replacement rate: {(total_replacements / total_literals * 100) if total_literals > 0 else 0:.1f}%")
    print()

    if dry_run:
        print("[DRY RUN] No files were modified.")
        print("Run with --apply to actually replace literals.")
    else:
        print("[OK] Constants imported and literals replaced!")

    return results

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Apply Constants Import Rewrite"
    )
    parser.add_argument(
        '--file',
        help='Single file to process'
    )
    parser.add_argument(
        '--dir',
        default='analyzer',
        help='Directory to scan (default: analyzer/)'
    )
    parser.add_argument(
        '--top',
        type=int,
        default=5,
        help='Process top N files (default: 5)'
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Actually apply changes (default is dry-run)'
    )
    parser.add_argument(
        '--constants-dir',
        default='analyzer/constants',
        help='Constants directory (default: analyzer/constants/)'
    )

    args = parser.parse_args()

    # Initialize importer
    constants_dir = Path(args.constants_dir)
    if not constants_dir.exists():
        print(f"[FAIL] Constants directory not found: {constants_dir}")
        return 1

    importer = ConstantImporter(constants_dir)
    print(f"Loaded constants from {len(importer.available_constants)} modules")

    if args.file:
        # Single file mode
        filepath = Path(args.file)
        if not filepath.exists():
            print(f"[FAIL] File not found: {filepath}")
            return 1

        replacer = ConstantReplacer(importer)
        replacer.process_file(filepath, dry_run=not args.apply)

    else:
        # Batch mode - find files with most literals
        dir_path = Path(args.dir)
        if not dir_path.exists():
            print(f"[FAIL] Directory not found: {dir_path}")
            return 1

        # Get top files (re-use analysis from extract script)
        from extract_magic_literals import analyze_file

        print("Scanning for files with most literals...")
        all_files = list(dir_path.rglob("*.py"))
        file_scores = []

        for filepath in all_files:
            # Skip constants files themselves
            if "constants" in str(filepath):
                continue

            result = analyze_file(filepath)
            if result and result['total_count'] > 0:
                file_scores.append((filepath, result['total_count']))

        file_scores.sort(key=lambda x: x[1], reverse=True)

        print(f"\nTop {args.top} files with most literals:")
        for i, (filepath, count) in enumerate(file_scores[:args.top], 1):
            short_path = str(filepath).replace(str(dir_path) + '\\', '')
            print(f"  {i}. {short_path}: {count} literals")

        # Process top files
        top_files = [f for f, _ in file_scores[:args.top]]
        batch_process(top_files, importer, dry_run=not args.apply)

    return 0

if __name__ == "__main__":
    sys.exit(main())
