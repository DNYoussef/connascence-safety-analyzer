"""
Automated testing for regex SyntaxWarning detection.
Ensures all regex patterns in the analyzer follow best practices.
"""

import ast
import importlib
from pathlib import Path
import re
import warnings

import pytest


def test_no_syntax_warnings_on_import():
    """Test that importing analyzer modules doesn't generate SyntaxWarnings."""

    # Modules to test for regex warnings
    modules_to_test = [
        "analyzer.language_strategies",
        "analyzer.smart_integration_engine",
        "analyzer.check_connascence",
        "analyzer.ast_engine.connascence_detector",
        "analyzer.ast_engine.god_object_detector",
        "analyzer.ast_engine.parameter_analyzer",
    ]

    for module_name in modules_to_test:
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter("always", SyntaxWarning)

            try:
                importlib.import_module(module_name)
            except ImportError:
                # Module might not exist, skip
                continue

            # Check for SyntaxWarnings
            syntax_warnings = [w for w in warning_list if issubclass(w.category, SyntaxWarning)]

            if syntax_warnings:
                warning_messages = [str(w.message) for w in syntax_warnings]
                pytest.fail(f"SyntaxWarnings in {module_name}: {warning_messages}")


def test_regex_patterns_use_raw_strings():
    """Test that regex patterns in source code use raw strings."""

    analyzer_dir = Path(__file__).parent.parent / "analyzer"
    python_files = list(analyzer_dir.rglob("*.py"))

    issues = []

    for py_file in python_files:
        try:
            with open(py_file, encoding="utf-8") as f:
                content = f.read()

            # Parse AST to find re.compile calls
            tree = ast.parse(content, filename=str(py_file))

            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and hasattr(node.func, "attr")
                    and node.func.attr == "compile"
                    and hasattr(node.func.value, "id")
                    and node.func.value.id == "re"
                ):
                    # Check if the first argument is a raw string
                    if node.args and isinstance(node.args[0], ast.Constant):
                        pattern_str = node.args[0].value
                        if isinstance(pattern_str, str):
                            # Check if it contains escape sequences that should be raw
                            if "\\" in pattern_str and not _is_likely_raw_string(content, node.lineno):
                                issues.append(f"{py_file}:{node.lineno} - Regex pattern should use raw string")

        except (SyntaxError, UnicodeDecodeError):
            # Skip files with syntax errors
            continue

    if issues:
        pytest.fail("Non-raw string regex patterns found:\n" + "\n".join(issues))


def _is_likely_raw_string(content: str, line_no: int) -> bool:
    """Check if a string on given line is likely a raw string."""
    lines = content.split("\n")
    if line_no > len(lines):
        return False

    line = lines[line_no - 1]  # Convert to 0-based indexing

    # Look for r" or r' patterns
    return bool(re.search(r'r["\']', line))


def test_specific_patterns_compile_without_warnings():
    """Test that our specific regex patterns don't generate warnings."""

    # Test patterns that were problematic before
    test_patterns = [
        r"\\w+\\s*\\([^)]*\\)",  # Function detection
        r"""["'][^"']{3,}["']""",  # String literals with mixed quotes
        r"\\b(?!0\\b|1\\b|-1\\b)\\d+\\.?\\d*\\b",  # Magic numbers
        r"^\\s*(?:function\\s+\\w+|(?:const|let|var)\\s+\\w+\\s*=)",  # JS functions
        r"interface\\s*\\{",  # Interface detection
    ]

    for pattern_str in test_patterns:
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter("always", SyntaxWarning)

            # Test compilation
            pattern = re.compile(pattern_str)

            # Test usage
            test_text = "function test() { return 42; }"
            pattern.search(test_text)

            # Check for warnings
            syntax_warnings = [w for w in warning_list if issubclass(w.category, SyntaxWarning)]

            if syntax_warnings:
                warning_messages = [str(w.message) for w in syntax_warnings]
                pytest.fail(f"Pattern '{pattern_str}' caused SyntaxWarnings: {warning_messages}")


def test_language_strategies_patterns():
    """Test that LanguageStrategy patterns compile without warnings."""

    try:
        from analyzer.language_strategies import CStrategy, JavaScriptStrategy, PythonStrategy

        strategies = [JavaScriptStrategy(), CStrategy(), PythonStrategy()]

        for strategy in strategies:
            with warnings.catch_warnings(record=True) as warning_list:
                warnings.simplefilter("always", SyntaxWarning)

                # Test pattern compilation
                patterns = strategy.get_magic_literal_patterns()
                function_detector = strategy.get_function_detector()
                param_detector = strategy.get_parameter_detector()

                # Test pattern usage
                test_code = "function test(a, b, c) { return 42; }"
                for pattern_name, pattern in patterns.items():
                    pattern.search(test_code)

                function_detector.search(test_code)
                param_detector.search(test_code)

                # Check for warnings
                syntax_warnings = [w for w in warning_list if issubclass(w.category, SyntaxWarning)]

                if syntax_warnings:
                    warning_messages = [str(w.message) for w in syntax_warnings]
                    pytest.fail(f"{strategy.__class__.__name__} patterns caused SyntaxWarnings: {warning_messages}")

    except ImportError:
        pytest.skip("Language strategies not available")


def test_ruff_catches_invalid_escape_sequences():
    """Test that our ruff configuration catches invalid escape sequences."""

    # Create a temporary file with bad regex patterns
    bad_pattern_code = """
import re

# This should be caught by ruff W605
bad_pattern = re.compile('["\'][^"\']{3,}["\']')

# This should be flagged for non-raw string
another_bad = re.compile('\\\\w+\\\\s*\\\\(')
"""

    test_file = Path(__file__).parent / "temp_bad_regex.py"

    try:
        test_file.write_text(bad_pattern_code)

        # Run ruff on the bad file (this is informational)
        import subprocess

        result = subprocess.run(
            ["ruff", "check", str(test_file), "--select=W605"],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        # If ruff found issues, that's good (it means our config is working)
        # If ruff is not available, skip this test
        if result.returncode != 0 and "W605" in result.stdout:
            # Good - ruff caught the issue
            pass
        elif result.returncode == 127:  # Command not found
            pytest.skip("ruff not available for testing")
        else:
            # Ruff didn't catch the issue - configuration might be wrong
            pytest.fail(f"ruff didn't catch invalid escape sequences. Output: {result.stdout}")

    finally:
        if test_file.exists():
            test_file.unlink()


if __name__ == "__main__":
    # Run tests manually
    test_no_syntax_warnings_on_import()
    test_specific_patterns_compile_without_warnings()
    print("All regex warning tests passed!")
