#!/usr/bin/env python3
"""
Test script for enterprise demo reproduction validation
Quick validation of the reproduction script functionality
"""

import json
import sys
from pathlib import Path

def test_reproduction_script():
    """Test that the reproduction script is properly configured"""
    
    # Check that the script exists
    script_path = Path(__file__).parent / "reproduce_enterprise_demo.py"
    if not script_path.exists():
        print("[FAIL] reproduce_enterprise_demo.py not found")
        return False
        
    # Import and validate configuration
    sys.path.insert(0, str(script_path.parent))
    
    try:
        from reproduce_enterprise_demo import ENTERPRISE_CONFIG, EnterpriseReproducer
        
        # Validate configuration
        expected_repos = ["celery", "curl", "express"]
        expected_total = 5743
        expected_counts = {
            "celery": 4630,
            "curl": 1061,
            "express": 52
        }
        
        print("[INFO] Validating configuration...")
        
        # Check repositories
        if set(ENTERPRISE_CONFIG["repositories"].keys()) != set(expected_repos):
            print(f"[FAIL] Repository configuration mismatch")
            return False
            
        # Check expected total
        if ENTERPRISE_CONFIG["expected_total"] != expected_total:
            print(f"[FAIL] Expected total mismatch: {ENTERPRISE_CONFIG['expected_total']} != {expected_total}")
            return False
            
        # Check individual counts
        for repo, expected_count in expected_counts.items():
            actual_count = ENTERPRISE_CONFIG["repositories"][repo]["expected_violations"]
            if actual_count != expected_count:
                print(f"[FAIL] {repo} count mismatch: {actual_count} != {expected_count}")
                return False
                
        # Check SHAs are present
        for repo, config in ENTERPRISE_CONFIG["repositories"].items():
            if not config.get("sha") or len(config["sha"]) != 40:
                print(f"[FAIL] {repo} SHA missing or invalid")
                return False
                
        print("[PASS] Configuration validation passed")
        
        # Test reproducer initialization
        reproducer = EnterpriseReproducer(Path.cwd())
        print(f"[PASS] EnterpriseReproducer initialized successfully")
        print(f"   Session ID: {reproducer.session_id}")
        print(f"   Output Dir: {reproducer.output_dir}")
        
        return True
        
    except ImportError as e:
        print(f"[FAIL] Import error: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Validation error: {e}")
        return False

def main():
    """Main test runner"""
    print("[TEST] Testing Enterprise Demo Reproduction Script")
    print("=" * 50)
    
    success = test_reproduction_script()
    
    print("=" * 50)
    if success:
        print("[PASS] All tests passed! Reproduction script ready for use.")
        print("\n[INFO] Next steps:")
        print("   python scripts/reproduce_enterprise_demo.py --help")
        print("   python scripts/reproduce_enterprise_demo.py --validate-all")
        sys.exit(0)
    else:
        print("[FAIL] Tests failed! Check configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main()