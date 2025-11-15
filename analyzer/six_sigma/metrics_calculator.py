#!/usr/bin/env python3
"""Wrapper for Six Sigma Metrics - delegates to enterprise/sixsigma/calculator.py"""

import sys
import subprocess
from pathlib import Path

if __name__ == "__main__":
    # Delegate to actual six sigma calculator
    script_path = Path(__file__).parent.parent / "enterprise" / "sixsigma" / "calculator.py"

    # Pass through all arguments
    result = subprocess.run([sys.executable, str(script_path)] + sys.argv[1:])
    sys.exit(result.returncode)
