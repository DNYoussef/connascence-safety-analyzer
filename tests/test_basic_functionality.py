#!/usr/bin/env python3
"""
Basic functionality tests that should pass with current implementation.

This test suite validates core functionality that is known to work:
1. Import and instantiation of analyzer classes
2. Basic argument parsing
3. File structure validation
4. Core algorithm functionality
"""

import ast
from pathlib import Path
import tempfile

import pytest


# Test basic imports work
def test_core_imports():
    """Test that core modules can be imported."""
    from analyzer.check_connascence import ConnascenceAnalyzer as LegacyAnalyzer
    from analyzer.constants import MAGIC_NUMBERS, resolve_policy_name
    from analyzer.core import ConnascenceAnalyzer, create_parser

    # Should be able to instantiate
    core_analyzer = ConnascenceAnalyzer()
    legacy_analyzer = LegacyAnalyzer()
    parser = create_parser()

    assert core_analyzer is not None
    assert legacy_analyzer is not None
    assert parser is not None

    # Test policy resolution
    assert resolve_policy_name('default') == 'standard'
    assert resolve_policy_name('nasa_jpl_pot10') == 'nasa-compliance'

    # Test constants access
    assert 'timeout_seconds' in MAGIC_NUMBERS
    assert MAGIC_NUMBERS['timeout_seconds'] == 30


def test_parser_basic_functionality():
    """Test basic parser functionality that should work."""
    from analyzer.core import create_parser

    parser = create_parser()

    # Test help can be generated
    help_text = parser.format_help()
    assert 'Connascence Safety Analyzer' in help_text

    # Test basic argument parsing
    args = parser.parse_args(['--path', '.', '--policy', 'default'])
    assert args.path == '.'
    assert args.policy == 'default'


def test_file_structure_validation():
    """Test that expected files and directories exist."""
    project_root = Path(__file__).parent.parent

    # Key files should exist
    expected_files = [
        'analyzer/core.py',
        'analyzer/constants.py',
        'analyzer/check_connascence.py',
        'analyzer/thresholds.py',
    ]

    for file_path in expected_files:
        full_path = project_root / file_path
        assert full_path.exists(), f"Expected file not found: {file_path}"


def test_constants_module():
    """Test constants module functionality."""
    from analyzer.constants import (
        GOD_OBJECT_METHOD_THRESHOLD,
        MAGIC_NUMBERS,
        NASA_PARAMETER_THRESHOLD,
        UNIFIED_POLICY_NAMES,
        resolve_policy_name,
    )

    # Test constants have expected values
    assert NASA_PARAMETER_THRESHOLD == 6
    assert GOD_OBJECT_METHOD_THRESHOLD == 20

    # Test magic numbers dictionary
    assert isinstance(MAGIC_NUMBERS, dict)
    assert 'zero' in MAGIC_NUMBERS
    assert MAGIC_NUMBERS['zero'] == 0

    # Test policy names
    assert isinstance(UNIFIED_POLICY_NAMES, list)
    assert 'nasa-compliance' in UNIFIED_POLICY_NAMES
    assert 'strict' in UNIFIED_POLICY_NAMES

    # Test policy resolution function
    assert resolve_policy_name('nasa_jpl_pot10') == 'nasa-compliance'
    assert resolve_policy_name('unknown') == 'standard'


def test_basic_ast_functionality():
    """Test basic AST analysis functionality."""
    test_code = '''
def simple_function():
    return 42
'''

    # Should be able to parse AST
    tree = ast.parse(test_code)
    assert isinstance(tree, ast.Module)

    # Should find function definition
    function_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    assert len(function_nodes) == 1
    assert function_nodes[0].name == 'simple_function'


def test_violation_dataclass():
    """Test ConnascenceViolation dataclass."""
    from utils.types import ConnascenceViolation

    violation = ConnascenceViolation(
        type="test",
        severity="medium",
        file_path="test.py",
        line_number=1,
        column=0,
        description="Test violation",
        recommendation="Fix it",
        code_snippet="test code",
        context={"test": True}
    )

    assert violation.type == "test"
    assert violation.severity == "medium"
    assert violation.file_path == "test.py"
    assert violation.context["test"] is True


def test_core_analyzer_instantiation():
    """Test that core analyzer can be instantiated and has expected methods."""
    from analyzer.core import ConnascenceAnalyzer

    analyzer = ConnascenceAnalyzer()
    assert hasattr(analyzer, 'analyze_path')
    assert hasattr(analyzer, 'version')
    assert analyzer.version == "2.0.0"


def test_legacy_analyzer_instantiation():
    """Test that legacy analyzer can be instantiated and has expected methods."""
    from analyzer.check_connascence import ConnascenceAnalyzer

    analyzer = ConnascenceAnalyzer()
    assert hasattr(analyzer, 'analyze_file')
    assert hasattr(analyzer, 'analyze_directory')
    assert hasattr(analyzer, 'should_analyze_file')


def test_language_strategies_import():
    """Test that language strategies can be imported."""
    try:
        from analyzer.language_strategies import CStrategy, JavaScriptStrategy, PythonStrategy

        # Should be able to instantiate
        js_strategy = JavaScriptStrategy()
        c_strategy = CStrategy()
        python_strategy = PythonStrategy()

        # Should have expected methods
        assert hasattr(js_strategy, 'detect_magic_literals')
        assert hasattr(c_strategy, 'detect_magic_literals')
        assert hasattr(python_strategy, 'detect_magic_literals')

    except ImportError:
        pytest.skip("Language strategies not available")


def test_thresholds_module():
    """Test thresholds module functionality."""
    try:
        from analyzer.thresholds import ConnascenceType, SeverityLevel, get_connascence_severity, get_severity_weight

        # Test enum values
        assert ConnascenceType.MEANING.value == "CoM"
        assert SeverityLevel.CRITICAL.value == "critical"

        # Test helper functions
        severity = get_connascence_severity(ConnascenceType.MEANING)
        assert severity == SeverityLevel.HIGH

        weight = get_severity_weight(SeverityLevel.CRITICAL)
        assert weight == 10.0

    except ImportError:
        pytest.skip("Thresholds module not available")


def test_error_handling_basic():
    """Test basic error handling doesn't crash."""
    from analyzer.core import ConnascenceAnalyzer

    analyzer = ConnascenceAnalyzer()

    # Should handle non-existent path gracefully
    result = analyzer.analyze_path('/non/existent/path')
    assert 'success' in result
    assert result['success'] is False
    assert 'error' in result


def test_temp_file_analysis():
    """Test analyzing a temporary file."""
    from analyzer.core import ConnascenceAnalyzer

    # Create temporary file with simple content
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('''
def test():
    return 1
''')
        temp_path = f.name

    try:
        analyzer = ConnascenceAnalyzer()
        result = analyzer.analyze_path(temp_path)

        # Should have result structure
        assert 'success' in result
        assert 'violations' in result

    finally:
        # Clean up
        Path(temp_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
