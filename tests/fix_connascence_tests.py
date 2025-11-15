#!/usr/bin/env python3
"""
Fix connascence preservation test issues.
1. Fix CoV syntax error (colon instead of assignment)
2. Ensure detectors are properly configured
"""

file_path = "tests/integration/test_connascence_preservation.py"

# Read the file
with open(file_path) as f:
    content = f.read()

# Fix 1: CoV syntax error - remove colon from line 151
content = content.replace(
    '        fallback = "ACTIVE":  # 4',
    '        fallback = "ACTIVE"  # 4'
)

# Write back
with open(file_path, 'w') as f:
    f.write(content)

print("SUCCESS: Fixed CoV syntax error in test_connascence_preservation.py")
