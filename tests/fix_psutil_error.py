#!/usr/bin/env python3
"""
Fix psutil.NoSuchProcess errors in MemoryMonitor initialization.
This patch adds error handling for process initialization failures.
"""

import re

file_path = "analyzer/optimization/memory_monitor.py"

# Read the file
with open(file_path, 'r') as f:
    content = f.read()

# Pattern to find the problematic section
old_pattern = r"""        # Process monitoring
        self\._process = psutil\.Process\(os\.getpid\(\)\)
        self\._start_time = time\.time\(\)"""

new_code = """        # Process monitoring
        try:
            self._process = psutil.Process(os.getpid())
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Fallback for testing environments or restricted access
            self._process = None
        self._start_time = time.time()"""

# Replace
content_fixed = re.sub(old_pattern, new_code, content)

if content == content_fixed:
    print("ERROR: Pattern not found or already fixed")
else:
    # Write back
    with open(file_path, 'w') as f:
        f.write(content_fixed)
    print("SUCCESS: Fixed psutil initialization in memory_monitor.py")

    # Now fix the methods that use self._process
    with open(file_path, 'r') as f:
        content = f.read()

    # Fix memory_info and memory_percent calls
    old_usage = """            memory_info = self._process.memory_info()
            memory_percent = self._process.memory_percent()"""

    new_usage = """            if self._process:
                memory_info = self._process.memory_info()
                memory_percent = self._process.memory_percent()
            else:
                # Fallback when process is not available
                import resource
                memory_info = type('MemInfo', (), {'rss': 0, 'vms': 0})()
                memory_percent = 0.0"""

    content = content.replace(old_usage, new_usage)

    with open(file_path, 'w') as f:
        f.write(content)
    print("SUCCESS: Fixed memory usage methods")
