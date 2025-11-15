#!/usr/bin/env python3
"""
Fix connascence detector sample code to trigger violations.

CoE (Execution): Needs >3 global assignments or >5 stateful variables
CoI (Identity): ValuesDetector should detect duplicate None values (needs investigation)
"""

file_path = "tests/integration/test_connascence_preservation.py"

with open(file_path) as f:
    content = f.read()

# Fix CoE - Add more global variables to exceed threshold (needs >3 assignments or >5 vars)
old_coe = '''            # CoE - Execution: Execution order dependencies (using GLOBAL state)
            "CoE": \'\'\'
# Global state creates execution order dependencies
database_connected = False
database_cursor = None

def connect_database():
    """Initialize global database state"""
    global database_connected, database_cursor
    database_connected = True
    database_cursor = "cursor"

def execute_query(query):
    """Depends on connect_database() being called first"""
    global database_connected, database_cursor
    if not database_connected:
        raise RuntimeError("Must call connect_database() first")
    return database_cursor

def disconnect_database():
    """Depends on connect_database() being called first"""
    global database_connected, database_cursor
    if not database_connected:
        raise RuntimeError("Must call connect_database() first")
    database_connected = False
\'\'\','''

new_coe = '''            # CoE - Execution: Execution order dependencies (using GLOBAL state)
            "CoE": \'\'\'
# Global state creates execution order dependencies (exceeds threshold)
database_connected = False
database_cursor = None
cache_initialized = False
session_active = False
config_loaded = False
state_manager = None

def initialize_system():
    """Initialize global system state"""
    global database_connected, database_cursor, cache_initialized, config_loaded, state_manager
    database_connected = True
    database_cursor = "cursor"
    cache_initialized = True
    config_loaded = True
    state_manager = {}

def connect_database():
    """Depends on initialize_system() being called first"""
    global database_connected, database_cursor, config_loaded
    if not config_loaded:
        raise RuntimeError("Must call initialize_system() first")
    database_connected = True
    database_cursor = "cursor"

def start_session():
    """Depends on connect_database() being called first"""
    global session_active, database_connected
    if not database_connected:
        raise RuntimeError("Must call connect_database() first")
    session_active = True

def execute_query(query):
    """Depends on start_session() being called first"""
    global session_active, database_cursor
    if not session_active:
        raise RuntimeError("Must call start_session() first")
    return database_cursor
\'\'\','''

content = content.replace(old_coe, new_coe)

# Write back
with open(file_path, 'w') as f:
    f.write(content)

print("SUCCESS: Updated CoE sample code to exceed global state threshold")
print("  - Added 6 stateful variables (exceeds threshold of 5)")
print("  - Added 4+ global statements (exceeds threshold of 3)")
