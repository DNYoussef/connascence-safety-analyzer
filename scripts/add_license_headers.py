#!/usr/bin/env python3
"""
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

Script to add consistent MIT license headers to all source files.
"""

from pathlib import Path
import sys

# MIT License header template
LICENSE_HEADER = """# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
"""

# Files that should be excluded from license header addition
EXCLUDE_PATTERNS = {
    'test_packages',
    '__pycache__',
    '.git',
    'node_modules',
    'build',
    'dist',
    '.pytest_cache',
    'htmlcov',
    'enterprise-package',
    'startup-package',
    'professional-package'
}

# Extensions to process
PYTHON_EXTENSIONS = {'.py'}


def should_process_file(file_path: Path) -> bool:
    """Check if file should have license header added."""
    # Skip if in excluded directory
    for exclude in EXCLUDE_PATTERNS:
        if exclude in str(file_path):
            return False

    # Only process Python files
    return file_path.suffix in PYTHON_EXTENSIONS


def has_license_header(content: str) -> bool:
    """Check if file already has SPDX license header."""
    return 'SPDX-License-Identifier' in content[:1000]  # Check first 1000 chars


def add_license_header(file_path: Path) -> bool:
    """Add license header to file if it doesn't have one."""
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        # Skip if already has license header
        if has_license_header(content):
            return False

        # Handle shebang lines
        lines = content.split('\n')
        shebang_lines = []
        content_start = 0

        # Preserve shebang and encoding declarations
        for i, line in enumerate(lines):
            if line.startswith('#!') or 'coding:' in line or 'encoding:' in line:
                shebang_lines.append(line)
                content_start = i + 1
            else:
                break

        # Skip empty lines after shebang
        while content_start < len(lines) and not lines[content_start].strip():
            content_start += 1

        # Construct new content
        new_lines = []

        # Add shebang lines first
        new_lines.extend(shebang_lines)
        if shebang_lines:
            new_lines.append('')  # Blank line after shebang

        # Add license header
        new_lines.extend(LICENSE_HEADER.strip().split('\n'))
        new_lines.append('')  # Blank line after license

        # Add original content (skip docstring if it's just after license)
        remaining_content = '\n'.join(lines[content_start:])
        if remaining_content.strip():
            new_lines.append(remaining_content)

        # Write updated content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))

        return True

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Add license headers to all Python source files."""
    project_root = Path(__file__).parent.parent
    print(f"Adding license headers to Python files in: {project_root}")

    # Find all Python files
    python_files = []
    for pattern in ['**/*.py']:
        python_files.extend(project_root.glob(pattern))

    # Filter files
    files_to_process = [f for f in python_files if should_process_file(f)]

    print(f"Found {len(files_to_process)} Python files to process")

    # Process each file
    updated_count = 0
    for file_path in files_to_process:
        if add_license_header(file_path):
            print(f"Updated: {file_path.relative_to(project_root)}")
            updated_count += 1
        else:
            print(f"Skipped: {file_path.relative_to(project_root)} (already has header)")

    print(f"\nCompleted: {updated_count} files updated with license headers")
    return 0


if __name__ == '__main__':
    sys.exit(main())
