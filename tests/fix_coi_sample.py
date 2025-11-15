#!/usr/bin/env python3
"""
Fix CoI sample code to use values that ValuesDetector will detect.
ValuesDetector excludes: "None", "", " ", "\n", "\t", "True", "False" and numbers 0, 1, -1, 2, 10, 100, 1000

We need to use duplicate non-excluded values (3+ occurrences) for ValuesDetector to flag them.
"""

file_path = "tests/integration/test_connascence_preservation.py"

with open(file_path) as f:
    content = f.read()

# Replace CoI sample with code that uses duplicate non-excluded sentinel values
old_coi = '''            # CoI - Identity: Identity connascence (via duplicate sentinel values)
            "CoI": \'\'\'
# Identity connascence via duplicate sentinel values (3+ occurrences required)
SENTINEL = None  # 1

def get_default_value():
    """Return default sentinel"""
    return None  # 2

def check_value(val):
    """Check against sentinel"""
    if val is None:  # 3
        return SENTINEL
    return val

def process(item):
    """Process with sentinel check"""
    if item == None:  # 4
        return "empty"
    return item
\'\'\','''

new_coi = '''            # CoI - Identity: Identity connascence (via duplicate sentinel values)
            "CoI": \'\'\'
# Identity connascence via duplicate sentinel values (3+ occurrences required)
SENTINEL_VALUE = "UNDEFINED"  # 1

def get_default_value():
    """Return default sentinel"""
    return "UNDEFINED"  # 2

def check_value(val):
    """Check against sentinel"""
    if val == "UNDEFINED":  # 3
        return SENTINEL_VALUE
    return val

def process(item):
    """Process with sentinel check"""
    if item == "UNDEFINED":  # 4
        return "empty"
    return item

def validate_input(data):
    """Validate input data"""
    if data == "UNDEFINED":  # 5
        return False
    return True
\'\'\','''

content = content.replace(old_coi, new_coi)

with open(file_path, 'w') as f:
    f.write(content)

print("SUCCESS: Updated CoI sample code to use non-excluded sentinel values")
print("  - Changed from None to 'UNDEFINED' (5 occurrences)")
print("  - ValuesDetector should now detect duplicate string literal violations")
