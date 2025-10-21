"""Quick test script to verify file discovery and analysis."""

from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.unified_analyzer import UnifiedConnascenceAnalyzer


def test_file_discovery():
    """Test file discovery for celery package."""
    analyzer = UnifiedConnascenceAnalyzer()

    # Test 1: Direct glob
    project_path = Path("test_packages/celery")
    python_files = list(project_path.glob("**/*.py"))
    print(f"Direct glob found: {len(python_files)} Python files")

    # Test 2: Using analyzer's method
    prioritized = analyzer._get_prioritized_python_files(project_path)
    print(f"Analyzer _get_prioritized_python_files: {len(prioritized)} files")

    # Test 3: Check filtering
    total_files = len(python_files)
    filtered_files = [f for f in python_files if analyzer._should_analyze_file(f)]
    skipped_files = total_files - len(filtered_files)
    print(f"After _should_analyze_file filter: {len(filtered_files)} files (skipped {skipped_files})")

    # Test 4: Show which files are skipped
    if skipped_files > 0:
        print("\nFirst 10 skipped files:")
        for f in python_files:
            if not analyzer._should_analyze_file(f):
                print(f"  SKIPPED: {f}")
                if skipped_files <= 0:
                    break
                skipped_files -= 1


if __name__ == "__main__":
    test_file_discovery()
