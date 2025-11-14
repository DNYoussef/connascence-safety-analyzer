#!/usr/bin/env python3
"""Fix CoI sample to use non-excluded sentinel values"""

file_path = "tests/integration/test_connascence_preservation.py"

with open(file_path, 'r') as f:
    content = f.read()

# Exact match for current CoI code
old_coi = '''            # CoI - Identity: Identity connascence (via duplicate sentinel values)
            "CoI": \'\'\'
# Identity connascence via duplicate sentinel values (3+ occurrences required)
SENTINEL = None  # 1

def get_default_value():
    """Return default sentinel"""
    return None  # 2

def process_with_default(value):
    """Check against sentinel"""
    if value is None:  # 3
        default_value = None  # 4
        return default_value
    return value
\'\'\','''

new_coi = '''            # CoI - Identity: Identity connascence (via duplicate sentinel values)
            "CoI": \'\'\'
# Identity connascence via duplicate sentinel values (3+ occurrences required)
SENTINEL_VALUE = "UNDEFINED"  # 1

def get_default_value():
    """Return default sentinel"""
    return "UNDEFINED"  # 2

def process_with_default(value):
    """Check against sentinel"""
    if value == "UNDEFINED":  # 3
        default_value = "UNDEFINED"  # 4
        return default_value
    return value

def validate_input(data):
    """Validate input data"""
    if data == "UNDEFINED":  # 5
        return False
    return True
\'\'\','''

content = content.replace(old_coi, new_coi)

with open(file_path, 'w') as f:
    f.write(content)

print("SUCCESS: Fixed CoI sample code")
print("  - Changed None to 'UNDEFINED' (5 occurrences)")
