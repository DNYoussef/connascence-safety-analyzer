#!/usr/bin/env python3
"""Wrapper for Clarity Linter - delegates to run_week3_clarity_scan.py"""

import sys
import subprocess
from pathlib import Path

if __name__ == "__main__":
    # Delegate to actual clarity scanner
    script_path = Path(__file__).parent / "run_week3_clarity_scan.py"

    # Pass through all arguments
    result = subprocess.run([sys.executable, str(script_path)] + sys.argv[1:])
    sys.exit(result.returncode)
