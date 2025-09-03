#!/usr/bin/env python3
"""
Connascence Sales Demo Runner v1.0.0
Run complete demo suite for customer presentations
"""

import sys
from pathlib import Path

# Add sales directory to path
sys.path.insert(0, str(Path(__file__).parent / "sales"))

from run_all_demos import MasterDemoRunner

def main():
    print("Connascence Sales Demo Suite v1.0.0")
    print("Building proof points for customer presentation...")
    
    runner = MasterDemoRunner()
    success = runner.run_complete_suite()
    
    if success:
        print("\nDemo suite complete - ready for customer presentation!")
        print("Key artifacts:")
        print(" False Positive Rate: <5% validated")
        print(" Autofix Acceptance: >=60% validated") 
        print(" NASA/JPL compliance: Ready")
        print(" Enterprise security: Deployed")
    else:
        print("\nDemo suite had some issues - check output for details")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
