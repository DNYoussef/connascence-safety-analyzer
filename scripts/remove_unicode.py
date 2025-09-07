#!/usr/bin/env python3
"""
Unicode Removal Script for Code Safety
======================================

Removes Unicode characters from Python code while preserving them in:
- Comments for user/admin display
- Docstrings for documentation
- String literals for user messages
- Print statements for console output

This ensures code compatibility across all systems and terminals.
"""

from pathlib import Path
import re
import sys
from datetime import datetime
from typing import Tuple


class UnicodeRemover:
    """Removes Unicode characters from Python code safely."""

    def __init__(self):
        self.stats = {
            'files_processed': 0,
            'unicode_removed': 0,
            'unicode_found': 0,
            'files_modified': 0,
            'files_with_unicode': 0,
            'violations': []  # Detailed violation info for JSON reporting
        }
        
        # Enhanced mode support
        self.quiet_mode = False
        self.verbose_mode = False
        self.check_mode = False
        self.dry_run_mode = False
        self.fix_mode = True
        self.include_types = ['py', 'js', 'ts', 'tsx', 'jsx', 'md', 'yaml', 'yml', 'json']
        self.exclude_dirs = ['.git', '__pycache__', '.pytest_cache', 'node_modules', '.venv', 'venv']

        # Unicode patterns that are safe in user-facing text
        self.safe_contexts = [
            r'#.*',  # Comments
            r'""".*?"""',  # Triple-quoted docstrings
            r"'''.*?'''",  # Single-quote docstrings
            r'print\s*\([^)]*\)',  # Print statements
            r'f"[^"]*"',  # F-strings for user output
            r"f'[^']*'",  # F-strings single quotes
        ]

        # Common Unicode characters to replace with ASCII equivalents
        self.unicode_replacements = {
            # Arrows and symbols
            '→': '->',
            '←': '<-',
            '↑': '^',
            '↓': 'v',
            '⇒': '=>',
            '⇐': '<=',
            '∞': 'inf',

            # Math symbols
            '≤': '<=',
            '≥': '>=',
            '≠': '!=',
            '±': '+/-',
            'x': '*',
            '÷': '/',
            '√': 'sqrt',

            # Bullets and markers
            '•': '*',
            '◦': '-',
            '▪': '*',
            '▫': '-',
            '★': '*',
            '☆': '*',
            '✓': 'OK',
            '✗': 'X',
            '✅': 'YES',
            '❌': 'NO',
            '⚠': 'WARNING',
            '🚨': 'ALERT',
            '💡': 'TIP',
            '🔧': 'TOOL',
            '📊': 'DATA',
            '🎯': 'TARGET',
            '🚀': 'LAUNCH',
            '⭐': 'STAR',
            '🏗': 'BUILD',
            '🛡': 'SECURITY',
            '🏛': 'ARCH',

            # Quotes and dashes
            '"': '"',
            ''': "'",
            ''': "'",
            '-': '-',  # En dash
            '—': '--', # Em dash
            '…': '...',

            # Currency and misc
            '©': '(c)',
            '®': '(R)',
            '™': '(TM)',
            '§': 'section',
            '¶': 'para',
        }

    def is_safe_context(self, line: str, position: int) -> bool:
        """Check if Unicode character is in a safe context (comments, strings, etc.)."""
        # Check if in comment
        comment_pos = line.find('#')
        if comment_pos != -1 and position >= comment_pos:
            return True

        # Check if in string literal (simplified check)
        before_pos = line[:position]
        quote_count_double = before_pos.count('"') - before_pos.count('\\"')
        quote_count_single = before_pos.count("'") - before_pos.count("\\'")

        # If odd number of quotes, we're inside a string
        if quote_count_double % 2 == 1 or quote_count_single % 2 == 1:
            return True

        # Check for print statements and f-strings
        return any(re.search(pattern, line) for pattern in self.safe_contexts)

    def remove_unicode_from_line(self, line: str, line_num: int, file_path: str) -> Tuple[str, int]:
        """Remove Unicode characters from a single line of code."""
        removed_count = 0
        found_count = 0
        result = []

        for i, char in enumerate(line):
            if ord(char) > 127:  # Non-ASCII character
                found_count += 1
                
                if self.is_safe_context(line, i):
                    # Keep Unicode in safe contexts
                    result.append(char)
                else:
                    # Record violation for ALL Unicode outside safe contexts
                    if char in self.unicode_replacements:
                        replacement = self.unicode_replacements[char]
                    else:
                        replacement = ''  # No replacement available
                    
                    violation = {
                        'file': str(file_path),
                        'line': line_num,
                        'column': i,
                        'char': char,
                        'unicode_code': f"U+{ord(char):04X}",
                        'replacement': replacement,
                        'context': line.strip()[:50] + '...' if len(line.strip()) > 50 else line.strip()
                    }
                    self.stats['violations'].append(violation)
                    
                    if char in self.unicode_replacements:
                        if self.fix_mode and not self.check_mode and not self.dry_run_mode:
                            # Replace with ASCII equivalent
                            replacement = self.unicode_replacements[char]
                            result.append(replacement)
                            removed_count += 1
                            if not self.quiet_mode:
                                try:
                                    print(f"  Replaced Unicode char with '{replacement}' at {file_path}:{line_num}:{i}")
                                except UnicodeEncodeError:
                                    print(f"  Replaced Unicode char (U+{ord(char):04X}) with '{replacement}' at {file_path}:{line_num}:{i}")
                        elif self.dry_run_mode:
                            # Show what would be replaced
                            replacement = self.unicode_replacements[char]
                            result.append(char)  # Keep original in dry run
                            if not self.quiet_mode:
                                print(f"  Would replace Unicode char with '{replacement}' at {file_path}:{line_num}:{i}")
                        elif self.check_mode:
                            # Just report the violation
                            result.append(char)  # Keep original in check mode
                            if not self.quiet_mode:
                                print(f"  Found Unicode char (U+{ord(char):04X}) at {file_path}:{line_num}:{i}")
                        else:
                            result.append(char)
                    else:
                        # Handle unknown Unicode character
                        if self.fix_mode and not self.check_mode and not self.dry_run_mode:
                            # Remove unknown Unicode character
                            removed_count += 1
                            if not self.quiet_mode:
                                try:
                                    print(f"  Removed unknown Unicode char (U+{ord(char):04X}) at {file_path}:{line_num}:{i}")
                                except UnicodeEncodeError:
                                    print(f"  Removed unknown Unicode (U+{ord(char):04X}) at {file_path}:{line_num}:{i}")
                            # Don't append anything (remove the character)
                        elif self.dry_run_mode:
                            # Show what would be removed
                            result.append(char)  # Keep original in dry run
                            if not self.quiet_mode:
                                print(f"  Would remove unknown Unicode char (U+{ord(char):04X}) at {file_path}:{line_num}:{i}")
                        elif self.check_mode:
                            # Just report the violation
                            result.append(char)  # Keep original in check mode
                            if not self.quiet_mode:
                                print(f"  Found unknown Unicode char (U+{ord(char):04X}) at {file_path}:{line_num}:{i}")
                        else:
                            result.append(char)
            else:
                result.append(char)
        
        # Update found count
        self.stats['unicode_found'] += found_count
        return ''.join(result), removed_count

    def process_file(self, file_path: Path) -> bool:
        """Process a single Python file to remove Unicode."""
        try:
            with open(file_path, encoding='utf-8') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            print(f"Warning: Could not decode {file_path} as UTF-8")
            return False
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return False

        modified = False
        new_lines = []
        file_unicode_count = 0

        for line_num, line in enumerate(lines, 1):
            new_line, removed = self.remove_unicode_from_line(line, line_num, str(file_path))
            new_lines.append(new_line)

            if removed > 0:
                modified = True
                file_unicode_count += removed

        # Only write back if modified
        if modified:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                print(f"Modified: {file_path} ({file_unicode_count} Unicode chars removed)")
                self.stats['files_modified'] += 1
            except Exception as e:
                print(f"Error writing {file_path}: {e}")
                return False

        self.stats['files_processed'] += 1
        self.stats['unicode_removed'] += file_unicode_count
        return True

    def should_process_file(self, file_path: Path) -> bool:
        """Check if file should be processed."""
        # Check if file extension is supported
        valid_extensions = {f'.{ext}' for ext in self.include_types}
        if file_path.suffix not in valid_extensions:
            return False

        # Skip excluded directories
        if any(skip_dir in str(file_path) for skip_dir in self.exclude_dirs):
            return False

        # Skip if file is too large (>1MB)
        try:
            if file_path.stat().st_size > 1024 * 1024:
                print(f"Skipping large file: {file_path}")
                return False
        except:
            return False

        return True

    def process_directory(self, directory: Path) -> None:
        """Process all supported files in directory recursively."""
        print(f"Processing directory: {directory}")

        # Build glob patterns for all supported file types
        files_to_process = []
        for ext in self.include_types:
            for file_path in directory.rglob(f'*.{ext}'):
                if self.should_process_file(file_path):
                    files_to_process.append(file_path)

        print(f"Found {len(files_to_process)} files to process ({', '.join(self.include_types)} extensions)")

        for file_path in files_to_process:
            self.process_file(file_path)
            # Track files with unicode for reporting
            if any(ord(char) > 127 for line in open(file_path, encoding='utf-8', errors='ignore') for char in line):
                self.stats['files_with_unicode'] += 1

    def generate_json_report(self, output_file: str) -> None:
        """Generate detailed JSON report for CI integration."""
        import json
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'files_processed': self.stats['files_processed'],
                'files_modified': self.stats['files_modified'],
                'files_with_unicode': self.stats['files_with_unicode'],
                'unicode_characters_found': self.stats['unicode_found'],
                'unicode_characters_removed': self.stats['unicode_removed']
            },
            'violations': self.stats['violations'],
            'configuration': {
                'include_types': self.include_types,
                'exclude_dirs': self.exclude_dirs,
                'check_mode': self.check_mode,
                'dry_run_mode': self.dry_run_mode,
                'fix_mode': self.fix_mode
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=True)
        
        print(f"JSON report saved to: {output_file}")
    
    def print_stats(self) -> None:
        """Print processing statistics."""
        print("\n" + "="*50)
        print("UNICODE REMOVAL STATISTICS")
        print("="*50)
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Files with Unicode: {self.stats['files_with_unicode']}")
        print(f"Files modified: {self.stats['files_modified']}")
        print(f"Unicode characters found: {self.stats['unicode_found']}")
        print(f"Unicode characters removed: {self.stats['unicode_removed']}")
        print(f"Violations detected: {len(self.stats['violations'])}")
        print("="*50)


def main():
    """Main entry point with enhanced CLI modes."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Enhanced Unicode Removal Tool for Code Safety",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python remove_unicode.py .                    # Fix Unicode issues (default)
  python remove_unicode.py --check .            # Check for Unicode without fixing
  python remove_unicode.py --dry-run .          # Preview what would be changed
  python remove_unicode.py --report-json . out.json  # Generate JSON report
        """
    )
    
    parser.add_argument('directory', help='Directory to process')
    
    # Operating modes
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--check', action='store_true',
                           help='Check for Unicode violations without modifying files (CI mode)')
    mode_group.add_argument('--fix', action='store_true', default=True,
                           help='Fix Unicode violations by modifying files (default)')
    mode_group.add_argument('--dry-run', action='store_true',
                           help='Show what would be changed without modifying files')
    
    # Reporting options
    parser.add_argument('--report-json', metavar='OUTPUT_FILE',
                       help='Generate detailed JSON report for CI integration')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output with detailed information')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Suppress all output except errors')
    
    # File filtering options
    parser.add_argument('--include-types', nargs='*', 
                       default=['py'],
                       help='File extensions to process (default: py)')
    parser.add_argument('--exclude-dirs', nargs='*',
                       default=['.git', '__pycache__', '.pytest_cache', 'node_modules', '.venv', 'venv'],
                       help='Directories to exclude from processing')
    
    args = parser.parse_args()
    
    # Determine mode
    if args.check:
        args.fix = False
    elif args.dry_run:
        args.fix = False
    
    # Validate directory
    directory = Path(args.directory)
    if not directory.exists():
        print(f"Error: Directory {directory} does not exist")
        sys.exit(1)

    # Create remover with enhanced options
    remover = UnicodeRemover()
    remover.quiet_mode = args.quiet
    remover.verbose_mode = args.verbose
    remover.check_mode = args.check
    remover.dry_run_mode = args.dry_run
    remover.fix_mode = args.fix
    remover.include_types = args.include_types
    remover.exclude_dirs = args.exclude_dirs
    
    # Process directory
    remover.process_directory(directory)
    
    # Generate reports
    if args.report_json:
        remover.generate_json_report(args.report_json)
    
    if not args.quiet:
        remover.print_stats()
    
    # Exit codes for CI integration
    if args.check and len(remover.stats['violations']) > 0:
        sys.exit(1)  # Unicode violations found
    elif args.check:
        sys.exit(0)  # No Unicode violations
    else:
        sys.exit(0)  # Fix or dry-run mode always succeeds


if __name__ == '__main__':
    main()
