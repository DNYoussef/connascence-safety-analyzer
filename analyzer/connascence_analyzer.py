#!/usr/bin/env python3
"""Wrapper for Connascence Analyzer - delegates to check_connascence.py

This module provides backward-compatible imports for ConnascenceAnalyzer.
"""

import sys
import subprocess
from pathlib import Path

# Re-export core classes for backward compatibility
# ConnascenceDetector is the AST visitor from check_connascence
from .check_connascence import ConnascenceDetector

# ConnascenceAnalyzer is the service layer from src/services
try:
    from src.services.connascence_analyzer import ConnascenceAnalyzer
except ImportError:
    # Fallback: create an alias to ConnascenceDetector if service layer unavailable
    ConnascenceAnalyzer = ConnascenceDetector

__all__ = ['ConnascenceAnalyzer', 'ConnascenceDetector']

if __name__ == "__main__":
    # Delegate to actual connascence checker
    script_path = Path(__file__).parent / "check_connascence.py"

    # Pass through all arguments
    result = subprocess.run([sys.executable, str(script_path)] + sys.argv[1:])
    sys.exit(result.returncode)
