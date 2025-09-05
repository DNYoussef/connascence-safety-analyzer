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

import os
import re
import sys
import ast
from pathlib import Path
from typing import List, Tuple, Dict


class UnicodeRemover:
    """Removes Unicode characters from Python code safely."""
    
    def __init__(self):
        self.stats = {
            'files_processed': 0,
            'unicode_removed': 0,
            'files_modified': 0
        }
        
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
            '×': '*',
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
            '"': '"',  # Smart quotes
            '"': '"',
            ''': "'",
            ''': "'",
            '–': '-',  # En dash
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
        for pattern in self.safe_contexts:
            if re.search(pattern, line):
                return True
                
        return False

    def remove_unicode_from_line(self, line: str, line_num: int, file_path: str) -> Tuple[str, int]:
        """Remove Unicode characters from a single line of code."""
        original_line = line
        removed_count = 0
        result = []
        
        for i, char in enumerate(line):
            if ord(char) > 127:  # Non-ASCII character
                if self.is_safe_context(line, i):
                    # Keep Unicode in safe contexts
                    result.append(char)
                elif char in self.unicode_replacements:
                    # Replace with ASCII equivalent
                    replacement = self.unicode_replacements[char]
                    result.append(replacement)
                    removed_count += 1
                    try:
                        print(f"  Replaced Unicode char with '{replacement}' at {file_path}:{line_num}:{i}")
                    except UnicodeEncodeError:
                        print(f"  Replaced Unicode char (U+{ord(char):04X}) with '{replacement}' at {file_path}:{line_num}:{i}")
                else:
                    # Remove unknown Unicode character
                    try:
                        print(f"  Removed unknown Unicode char (U+{ord(char):04X}) at {file_path}:{line_num}:{i}")
                    except UnicodeEncodeError:
                        print(f"  Removed unknown Unicode (U+{ord(char):04X}) at {file_path}:{line_num}:{i}")
                    removed_count += 1
                    # Don't append anything (remove the character)
            else:
                result.append(char)
        
        return ''.join(result), removed_count

    def process_file(self, file_path: Path) -> bool:
        """Process a single Python file to remove Unicode."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
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
        # Only process Python files
        if file_path.suffix != '.py':
            return False
            
        # Skip certain directories
        skip_dirs = {'.git', '__pycache__', '.pytest_cache', 'node_modules', '.venv', 'venv'}
        if any(skip_dir in str(file_path) for skip_dir in skip_dirs):
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
        """Process all Python files in directory recursively."""
        print(f"Processing directory: {directory}")
        
        python_files = []
        for file_path in directory.rglob('*.py'):
            if self.should_process_file(file_path):
                python_files.append(file_path)
        
        print(f"Found {len(python_files)} Python files to process")
        
        for file_path in python_files:
            self.process_file(file_path)
    
    def print_stats(self) -> None:
        """Print processing statistics."""
        print("\n" + "="*50)
        print("UNICODE REMOVAL STATISTICS")
        print("="*50)
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Files modified: {self.stats['files_modified']}")
        print(f"Unicode characters removed: {self.stats['unicode_removed']}")
        print("="*50)


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python remove_unicode.py <directory>")
        print("Example: python remove_unicode.py .")
        sys.exit(1)
    
    directory = Path(sys.argv[1])
    if not directory.exists():
        print(f"Error: Directory {directory} does not exist")
        sys.exit(1)
    
    remover = UnicodeRemover()
    remover.process_directory(directory)
    remover.print_stats()


if __name__ == '__main__':
    main()