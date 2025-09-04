#!/usr/bin/env python3
"""
Pre-commit integration example for connascence detection.

This script demonstrates how to integrate connascence detection into your
development workflow using pre-commit hooks.
"""

import subprocess
import sys
from pathlib import Path


def run_connascence_checks():
    """Run connascence checks as part of pre-commit."""
    print("Running connascence analysis...")
    
    # Run analysis on staged Python files using unified CLI
    try:
        result = subprocess.run([
            "connascence", "analyze",
            ".",
            "--severity", "high",
            "--format", "json"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("[DONE] No high-severity connascence violations found!")
            return True
        else:
            print(" Connascence violations detected:")
            print(result.stdout)
            return False
            
    except subprocess.TimeoutExpired:
        print(" Connascence analysis timed out")
        return False
    except Exception as e:
        print(f" Error running connascence analysis: {e}")
        return False


def run_magic_literal_checks():
    """Run magic literal detection."""
    print("Running magic literal detection...")
    
    try:
        result = subprocess.run([
            "connascence", "detect-literals",
            ".", 
            "--threshold", "25.0",  # Allow up to 25% magic literals
            "--severity", "medium"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("[DONE] Magic literal usage within acceptable limits!")
            return True
        else:
            print(" Excessive magic literals detected:")
            print(result.stdout)
            return False
            
    except Exception as e:
        print(f" Error running magic literal detection: {e}")
        return False


if __name__ == "__main__":
    """Main pre-commit check."""
    print("[SEARCH] Running connascence pre-commit checks...")
    
    checks_passed = 0
    total_checks = 2
    
    # Run connascence checks
    if run_connascence_checks():
        checks_passed += 1
    
    # Run magic literal checks  
    if run_magic_literal_checks():
        checks_passed += 1
    
    # Final result
    if checks_passed == total_checks:
        print(f"[DONE] All {total_checks} connascence checks passed!")
        sys.exit(0)
    else:
        print(f" {total_checks - checks_passed}/{total_checks} connascence checks failed!")
        print("\n[TIP] Fix the connascence violations above and try again.")
        sys.exit(1)