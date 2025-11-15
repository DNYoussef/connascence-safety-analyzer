#!/usr/bin/env python3
"""Wrapper for Connascence Analyzer - delegates to check_connascence.py"""

import sys
import subprocess
from pathlib import Path

if __name__ == "__main__":
    # Delegate to actual connascence checker
    script_path = Path(__file__).parent / "check_connascence.py"

    # Pass through all arguments
    result = subprocess.run([sys.executable, str(script_path)] + sys.argv[1:])
    sys.exit(result.returncode)
