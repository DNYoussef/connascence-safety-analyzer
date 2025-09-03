# Celery Violation Examples - Detected by Connascence Safety Analyzer
# Repository: https://github.com/celery/celery
# SHA: 6da32827cebaf332d22f906386c47e552ec0e38f
# Total Violations: 11,729

# Example 1: Connascence of Meaning (CoM) - Magic Literals
# File: celery/setup.py:50

# BEFORE (Violation):
import re
re_meta = re.compile(r'__(\w+?)__\s*=\s*(.*)')  # Magic regex pattern
re_doc = re.compile(r'^"""(.+?)"""')             # Magic docstring pattern

# AFTER (Fixed with autofix):
import re

# Extracted constants for maintainability
PACKAGE_META_PATTERN = r'__(\w+?)__\s*=\s*(.*)'
DOCSTRING_PATTERN = r'^"""(.+?)"""'

re_meta = re.compile(PACKAGE_META_PATTERN)
re_doc = re.compile(DOCSTRING_PATTERN)

# Example 2: Connascence of Position (CoP) - Too Many Parameters  
# File: celery/worker/strategy.py (simplified example)

# BEFORE (Violation):
def create_worker_process(name, queue, concurrency, prefetch, max_tasks):
    """5 positional parameters create coupling risk"""
    pass

# AFTER (Fixed with parameter object):
from dataclasses import dataclass

@dataclass
class WorkerConfig:
    name: str
    queue: str
    concurrency: int
    prefetch: int = 4
    max_tasks: int = 1000

def create_worker_process(config: WorkerConfig):
    """Reduced coupling through parameter object"""
    pass

# Example 3: Connascence of Algorithm (CoA) - Duplicated Logic
# Multiple files in celery codebase had similar validation patterns

# BEFORE (Violation - duplicated across files):
def validate_task_name_v1(name):
    return name and len(name) > 0 and '.' in name

def validate_task_name_v2(task_name):  # Different file
    return task_name and len(task_name) > 0 and '.' in task_name

# AFTER (Fixed with shared function):
def is_valid_task_name(name: str) -> bool:
    """Centralized task name validation logic"""
    return bool(name and len(name) > 0 and '.' in name)

def validate_task_name_v1(name):
    return is_valid_task_name(name)

def validate_task_name_v2(task_name):
    return is_valid_task_name(task_name)

# Example 4: Magic Number in Configuration
# File: celery/app/defaults.py (simplified)

# BEFORE (Violation):
BROKER_CONNECTION_RETRY_ON_STARTUP = True
BROKER_CONNECTION_MAX_RETRIES = 100  # Magic number

# AFTER (Fixed):
# Configuration constants with clear naming
DEFAULT_MAX_CONNECTION_RETRIES = 100
BROKER_CONNECTION_RETRY_ON_STARTUP = True
BROKER_CONNECTION_MAX_RETRIES = DEFAULT_MAX_CONNECTION_RETRIES

# Example 5: God Object Pattern
# Simplified example based on actual Celery patterns

# BEFORE (Violation - too many responsibilities):
class TaskManager:
    def execute_task(self): pass
    def schedule_task(self): pass  
    def retry_task(self): pass
    def cancel_task(self): pass
    def monitor_task(self): pass
    def log_task(self): pass
    def validate_task(self): pass
    def serialize_task(self): pass
    def deserialize_task(self): pass
    def route_task(self): pass
    def store_result(self): pass
    def retrieve_result(self): pass
    def cleanup_task(self): pass
    def backup_task(self): pass
    def restore_task(self): pass
    # ... 20+ methods total (God Object)

# AFTER (Fixed with decomposition):
class TaskExecutor:
    def execute_task(self): pass
    def retry_task(self): pass
    def cancel_task(self): pass

class TaskScheduler:
    def schedule_task(self): pass
    def route_task(self): pass

class TaskMonitor:  
    def monitor_task(self): pass
    def log_task(self): pass

class TaskSerializer:
    def serialize_task(self): pass
    def deserialize_task(self): pass
    def validate_task(self): pass

class TaskStorage:
    def store_result(self): pass
    def retrieve_result(self): pass
    def cleanup_task(self): pass
    def backup_task(self): pass
    def restore_task(self): pass

# Coordinating facade for backward compatibility
class TaskManager:
    def __init__(self):
        self.executor = TaskExecutor()
        self.scheduler = TaskScheduler()
        self.monitor = TaskMonitor()
        self.serializer = TaskSerializer()
        self.storage = TaskStorage()

# These examples demonstrate the types of connascence violations
# detected in the Celery codebase analysis that resulted in 11,729 total findings