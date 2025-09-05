#!/usr/bin/env python3
"""
Integration test for the VSCode extension with Python analyzer
"""
import os
import sys
import json
import subprocess
from pathlib import Path

def test_analyzer_accessibility():
    """Test if the analyzer can be imported and executed"""
    try:
        # Test direct import
        sys.path.insert(0, str(Path(__file__).parent.parent / "analyzer"))
        import check_connascence
        print("✅ Analyzer module import: SUCCESS")
        return True
    except Exception as e:
        print(f"❌ Analyzer module import: FAILED - {e}")
        return False

def test_analyzer_execution():
    """Test if the analyzer can be executed via subprocess (as extension would do)"""
    try:
        analyzer_path = Path(__file__).parent.parent / "analyzer" / "check_connascence.py"
        test_file = Path(__file__).parent.parent / "tests" / "fixtures" / "sample.py"
        
        # Create a simple test file if it doesn't exist
        test_file.parent.mkdir(parents=True, exist_ok=True)
        if not test_file.exists():
            test_file.write_text("""
def function_with_connascence():
    x = 1
    y = 1  # Position connascence
    return x + y
""")
        
        # Execute analyzer subprocess
        result = subprocess.run([
            sys.executable, str(analyzer_path),
            str(test_file), "--format", "json"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Analyzer subprocess execution: SUCCESS")
            print(f"   Output length: {len(result.stdout)} chars")
            return True
        else:
            print(f"❌ Analyzer subprocess execution: FAILED - {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Analyzer subprocess execution: FAILED - {e}")
        return False

def test_extension_structure():
    """Test if extension files are properly updated"""
    extension_path = Path("C:/Users/17175/.vscode/extensions/connascence-systems.connascence-safety-analyzer-2.0.0/out")
    
    required_files = [
        "extension.js",
        "services/connascenceApiClient.js",
        "utils/cache.js",
        "utils/errorHandler.js",
        "core/ConnascenceExtension.js"
    ]
    
    all_found = True
    for file_path in required_files:
        full_path = extension_path / file_path
        if full_path.exists():
            print(f"✅ Extension file {file_path}: EXISTS")
        else:
            print(f"❌ Extension file {file_path}: MISSING")
            all_found = False
    
    return all_found

def main():
    """Run all integration tests"""
    print("🧪 VSCode Extension Integration Tests")
    print("=" * 50)
    
    tests = [
        ("Analyzer Accessibility", test_analyzer_accessibility),
        ("Analyzer Execution", test_analyzer_execution),
        ("Extension Structure", test_extension_structure)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔄 Running: {test_name}")
        if test_func():
            passed += 1
            print(f"✅ {test_name}: PASSED")
        else:
            print(f"❌ {test_name}: FAILED")
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Extension integration is working!")
        return 0
    else:
        print("⚠️ Some tests failed - Check the output above")
        return 1

if __name__ == "__main__":
    sys.exit(main())