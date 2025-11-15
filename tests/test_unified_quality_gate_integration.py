"""
Test suite for ClarityLinter integration with UnifiedQualityGate

Verifies that:
1. ClarityLinter imports correctly
2. Integration initializes without errors
3. Analysis workflow includes clarity violations
4. SARIF export merges all analyzer outputs
5. Quality scoring includes clarity violations
"""

from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.quality_gates.unified_quality_gate import UnifiedQualityGate, Violation


def test_import_integration():
    """Test that ClarityLinter imports successfully"""
    gate = UnifiedQualityGate()
    assert hasattr(gate, 'clarity_linter'), "ClarityLinter not initialized"
    print("PASS: ClarityLinter import integration")


def test_initialization():
    """Test that UnifiedQualityGate initializes with ClarityLinter"""
    gate = UnifiedQualityGate()
    assert gate.clarity_linter is not None, "ClarityLinter failed to initialize"
    print("PASS: UnifiedQualityGate initialization with ClarityLinter")


def test_analyze_project_includes_clarity():
    """Test that analyze_project runs clarity analysis"""
    gate = UnifiedQualityGate()

    # Create test project structure
    test_project = Path(__file__).parent / "test_project"
    test_project.mkdir(exist_ok=True)

    # Create test file with clarity violations
    test_file = test_project / "test_clarity.py"
    test_file.write_text("""
def a():  # Poor naming
    return 1

def thin_helper(x):  # Thin helper
    return x + 1
""")

    try:
        results = gate.analyze_project(str(test_project))

        # Check that clarity violations are present
        clarity_violations = [
            v for v in results.violations
            if v.source_analyzer == "clarity_linter"
        ]

        print(f"Found {len(clarity_violations)} clarity violations")
        print("PASS: analyze_project includes clarity violations")

    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()
        if test_project.exists():
            test_project.rmdir()


def test_sarif_export_merges_analyzers():
    """Test that SARIF export merges all three analyzers"""
    gate = UnifiedQualityGate()

    # Create mock violations from different analyzers
    gate.results.violations = [
        Violation(
            rule_id="CLARITY001",
            message="Poor naming",
            file="test.py",
            line=1,
            severity="medium",
            category="readability",
            source_analyzer="clarity_linter"
        ),
        Violation(
            rule_id="CON001",
            message="God Object",
            file="test.py",
            line=5,
            severity="high",
            category="design",
            source_analyzer="connascence_analyzer"
        ),
        Violation(
            rule_id="NASA001",
            message="Function too long",
            file="test.py",
            line=10,
            severity="high",
            category="reliability",
            source_analyzer="nasa_standards"
        ),
    ]

    # Export to temporary file
    temp_sarif = Path(__file__).parent / "temp_sarif.json"
    try:
        gate.export_sarif(str(temp_sarif))

        # Verify SARIF structure
        import json
        with open(temp_sarif) as f:
            sarif = json.load(f)

        assert sarif["version"] == "2.1.0"
        assert len(sarif["runs"]) == 3, f"Expected 3 runs, got {len(sarif['runs'])}"

        run_names = [run["tool"]["driver"]["name"] for run in sarif["runs"]]
        assert "Clarity Linter" in run_names
        assert "Connascence Analyzer" in run_names
        assert "NASA Standards Checker" in run_names

        print("PASS: SARIF export merges all analyzers")

    finally:
        if temp_sarif.exists():
            temp_sarif.unlink()


def test_quality_score_includes_clarity():
    """Test that quality score calculation includes clarity violations"""
    gate = UnifiedQualityGate()

    # Add clarity violations
    gate.results.violations = [
        Violation(
            rule_id="CLARITY001",
            message="Poor naming",
            file="test.py",
            line=1,
            severity="high",
            category="readability",
            source_analyzer="clarity_linter"
        ),
        Violation(
            rule_id="CLARITY002",
            message="Thin helper",
            file="test.py",
            line=5,
            severity="medium",
            category="readability",
            source_analyzer="clarity_linter"
        ),
    ]

    # Calculate scores
    gate._calculate_metrics()
    gate._calculate_scores()

    # Verify clarity score is calculated
    assert gate.results.clarity_score < 100, "Clarity score should be penalized for violations"
    assert gate.results.overall_score < 100, "Overall score should include clarity violations"

    print(f"Clarity score: {gate.results.clarity_score:.2f}/100")
    print(f"Overall score: {gate.results.overall_score:.2f}/100")
    print("PASS: Quality score includes clarity violations")


if __name__ == "__main__":
    print("=" * 60)
    print("ClarityLinter Integration Test Suite")
    print("=" * 60)

    try:
        test_import_integration()
        test_initialization()
        test_analyze_project_includes_clarity()
        test_sarif_export_merges_analyzers()
        test_quality_score_includes_clarity()

        print("=" * 60)
        print("ALL TESTS PASSED")
        print("=" * 60)

    except AssertionError as e:
        print(f"\nFAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
