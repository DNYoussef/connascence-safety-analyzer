"""Debug script to trace directory analysis execution."""
import logging
from pathlib import Path
import sys

# Setup logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s - %(name)s - %(message)s")

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.unified_analyzer import UnifiedConnascenceAnalyzer


def debug_analysis():
    """Debug directory analysis."""
    print("=" * 60)
    print("DIRECTORY ANALYSIS DEBUG")
    print("=" * 60)

    analyzer = UnifiedConnascenceAnalyzer()
    project_path = Path("test_packages/celery")

    print("\n1. Testing file discovery...")
    python_files = analyzer._get_prioritized_python_files(project_path)
    print(f"   Found {len(python_files)} Python files")

    if len(python_files) > 0:
        print("\n2. First 10 files:")
        for f in python_files[:10]:
            print(f"   - {f}")

        print("\n3. Testing analyze_project...")
        try:
            result = analyzer.analyze_project(project_path=project_path, policy_preset="default", options={})
            print(f"   Result type: {type(result)}")
            print(f"   Total violations: {result.total_violations}")
            print(f"   Connascence violations: {len(result.connascence_violations)}")
            print(f"   Duplication violations: {len(result.duplication_violations)}")
            print(f"   NASA violations: {len(result.nasa_violations)}")
        except Exception as e:
            print(f"   ERROR: {e}")
            import traceback

            traceback.print_exc()
    else:
        print("\n   ERROR: No files found!")


if __name__ == "__main__":
    debug_analysis()
