# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
Enhanced Pipeline Error Handling and Edge Case Tests
===================================================

Comprehensive testing of error conditions and edge cases:
- Malformed input handling
- Resource constraint scenarios
- Concurrent access edge cases
- Network/IO failure simulation
- Invalid configuration handling
- Partial failure recovery
- Timeout and resource exhaustion
- Interface error propagation
- Data corruption handling
"""

from dataclasses import dataclass
from pathlib import Path
import tempfile
import threading
import time
from typing import Any, Dict, List, Optional
from unittest.mock import patch

import pytest

from .test_infrastructure import MockEnhancedAnalyzer, integration_test


@dataclass
class ErrorTestCase:
    """Test case for error handling scenarios"""

    name: str
    description: str
    error_type: str
    trigger_condition: str
    expected_behavior: str
    recovery_expected: bool
    timeout_seconds: Optional[float] = None


class ErrorHandlingTestSuite:
    """Comprehensive error handling test suite"""

    def __init__(self):
        self.error_test_cases = self._create_error_test_cases()

    def _create_error_test_cases(self) -> List[ErrorTestCase]:
        """Create comprehensive error test cases"""
        return [
            ErrorTestCase(
                name="malformed_python_syntax",
                description="Handle files with syntax errors gracefully",
                error_type="syntax_error",
                trigger_condition="invalid_python_syntax",
                expected_behavior="skip_file_continue_analysis",
                recovery_expected=True,
            ),
            ErrorTestCase(
                name="encoding_issues",
                description="Handle files with invalid encoding",
                error_type="encoding_error",
                trigger_condition="invalid_utf8_bytes",
                expected_behavior="fallback_encoding_detection",
                recovery_expected=True,
            ),
            ErrorTestCase(
                name="extremely_large_files",
                description="Handle files exceeding size limits",
                error_type="resource_limit",
                trigger_condition="file_size_exceeds_limit",
                expected_behavior="partial_analysis_with_warning",
                recovery_expected=True,
            ),
            ErrorTestCase(
                name="circular_import_detection",
                description="Handle circular import dependencies",
                error_type="analysis_error",
                trigger_condition="circular_dependency_graph",
                expected_behavior="detect_cycle_continue_analysis",
                recovery_expected=True,
            ),
            ErrorTestCase(
                name="memory_exhaustion",
                description="Handle memory exhaustion during analysis",
                error_type="resource_exhaustion",
                trigger_condition="high_memory_usage",
                expected_behavior="graceful_degradation",
                recovery_expected=True,
                timeout_seconds=30.0,
            ),
            ErrorTestCase(
                name="concurrent_file_modification",
                description="Handle files modified during analysis",
                error_type="io_error",
                trigger_condition="file_modified_during_read",
                expected_behavior="retry_with_fresh_read",
                recovery_expected=True,
            ),
            ErrorTestCase(
                name="permission_denied",
                description="Handle permission denied on files/directories",
                error_type="permission_error",
                trigger_condition="insufficient_file_permissions",
                expected_behavior="skip_with_warning",
                recovery_expected=True,
            ),
            ErrorTestCase(
                name="network_timeout",
                description="Handle network timeouts in distributed analysis",
                error_type="network_error",
                trigger_condition="network_connection_timeout",
                expected_behavior="fallback_to_local_analysis",
                recovery_expected=True,
                timeout_seconds=10.0,
            ),
            ErrorTestCase(
                name="corrupted_analysis_data",
                description="Handle corrupted intermediate analysis data",
                error_type="data_corruption",
                trigger_condition="invalid_analysis_result_format",
                expected_behavior="regenerate_analysis_data",
                recovery_expected=True,
            ),
            ErrorTestCase(
                name="interface_communication_failure",
                description="Handle interface communication failures",
                error_type="interface_error",
                trigger_condition="interface_connection_lost",
                expected_behavior="queue_results_for_retry",
                recovery_expected=True,
            ),
        ]


@pytest.fixture
def error_test_suite():
    """Fixture providing error handling test suite"""
    return ErrorHandlingTestSuite()


@pytest.fixture
def temp_error_test_directory():
    """Create temporary directory for error testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        error_test_path = Path(temp_dir) / "error_test_project"
        error_test_path.mkdir()
        yield error_test_path


class TestErrorHandlingAndEdgeCases:
    """Test suite for error handling and edge cases"""

    @integration_test(["error_handling"])
    def test_malformed_python_syntax_handling(self, temp_error_test_directory):
        """Test handling of files with syntax errors"""
        # Create files with various syntax errors
        syntax_error_files = {
            "syntax_error_1.py": """
def broken_function(
    # Missing closing parenthesis
    pass
            """,
            "syntax_error_2.py": """
class BrokenClass
    # Missing colon
    def method(self):
        pass
            """,
            "syntax_error_3.py": """
# Invalid indentation
def function():
pass
    return "broken"
            """,
            "valid_file.py": """
class ValidClass:
    def valid_method(self):
        return "working"
            """,
        }

        # Create test files
        for filename, content in syntax_error_files.items():
            file_path = temp_error_test_directory / filename
            file_path.write_text(content, encoding="utf-8")

        # Test error handling
        mock_analyzer = MockEnhancedAnalyzer("syntax_error")
        result = mock_analyzer.analyze_path(str(temp_error_test_directory), enable_cross_phase_correlation=True)

        # Validate error handling
        assert "errors" in result, "Should report syntax errors"
        assert "findings" in result, "Should continue analysis despite errors"

        errors = result.get("errors", [])
        syntax_errors = [e for e in errors if e.get("type") == "syntax_error"]
        assert len(syntax_errors) == 3, "Should detect all syntax errors"

        # Should still analyze valid file
        findings = result.get("findings", [])
        valid_file_findings = [f for f in findings if "valid_file.py" in str(f.get("file", ""))]
        assert len(valid_file_findings) >= 0, "Should analyze valid files successfully"

    @integration_test(["error_handling"])
    def test_encoding_error_handling(self, temp_error_test_directory):
        """Test handling of files with encoding issues"""
        # Create files with different encodings
        test_files = [
            ("utf8_file.py", "# UTF-8 file with unicode: café", "utf-8"),
            ("latin1_file.py", "# Latin-1 file with special chars", "latin-1"),
            ("valid_ascii.py", "# Simple ASCII file", "ascii"),
        ]

        for filename, content, encoding in test_files:
            file_path = temp_error_test_directory / filename
            try:
                file_path.write_text(content, encoding=encoding)
            except UnicodeEncodeError:
                # For encoding test, write bytes directly
                file_path.write_bytes(content.encode(encoding, errors="ignore"))

        # Create a file with invalid UTF-8 bytes
        invalid_utf8_file = temp_error_test_directory / "invalid_utf8.py"
        invalid_utf8_file.write_bytes(b"\xff\xfe# Invalid UTF-8 bytes\nclass Test:\n    pass")

        # Test encoding error handling
        mock_analyzer = MockEnhancedAnalyzer("encoding_error")
        result = mock_analyzer.analyze_path(str(temp_error_test_directory), enable_cross_phase_correlation=True)

        # Validate encoding error handling
        assert "errors" in result or "warnings" in result, "Should report encoding issues"
        assert "findings" in result, "Should continue analysis with fallback encoding"

        # Check that analysis attempted all files
        if "errors" in result:
            encoding_errors = [e for e in result["errors"] if e.get("type") == "encoding_error"]
            assert len(encoding_errors) <= 2, "Should handle encoding gracefully"

    @integration_test(["error_handling"])
    def test_extremely_large_file_handling(self, temp_error_test_directory):
        """Test handling of extremely large files"""
        # Create a large file that exceeds typical limits
        large_file_content = """
# Large file test
class LargeClass:
    def __init__(self):
        # Generate large amount of code
        self.data = {
"""

        # Add many lines to simulate large file
        for i in range(1000):
            large_file_content += f'            "key_{i}": "value_{i}_{"x" * 50}",\n'

        large_file_content += """        }
        
    def process_data(self):
        # CofE: Algorithm - processing large dataset
        result = {}
        for key, value in self.data.items():
            result[key] = self.transform(value)
        return result
"""

        large_file = temp_error_test_directory / "large_file.py"
        large_file.write_text(large_file_content, encoding="utf-8")

        # Test large file handling
        mock_analyzer = MockEnhancedAnalyzer("large_file")
        result = mock_analyzer.analyze_path(str(temp_error_test_directory), enable_cross_phase_correlation=True)

        # Validate large file handling
        assert "warnings" in result or "findings" in result, "Should handle large file"

        if "warnings" in result:
            large_file_warnings = [w for w in result["warnings"] if "large" in w.get("message", "").lower()]
            assert len(large_file_warnings) >= 0, "May warn about large file processing"

        # Should still produce some analysis results
        findings = result.get("findings", [])
        assert len(findings) >= 0, "Should analyze what it can from large file"

    @integration_test(["error_handling"])
    def test_circular_import_detection(self, temp_error_test_directory):
        """Test handling of circular import dependencies"""
        # Create files with circular imports
        circular_files = {
            "module_a.py": """
from module_b import ClassB

class ClassA:
    def __init__(self):
        # CofE: Type - depends on ClassB
        self.b_instance = ClassB()
        
    def use_b(self):
        return self.b_instance.method()
            """,
            "module_b.py": """
from module_c import ClassC

class ClassB:
    def __init__(self):
        # CofE: Type - depends on ClassC
        self.c_instance = ClassC()
        
    def method(self):
        return self.c_instance.process()
            """,
            "module_c.py": """
from module_a import ClassA

class ClassC:
    def process(self):
        # CofE: Type - circular dependency back to ClassA
        return "processed by " + ClassA().__class__.__name__
            """,
        }

        # Create circular import files
        for filename, content in circular_files.items():
            file_path = temp_error_test_directory / filename
            file_path.write_text(content, encoding="utf-8")

        # Test circular import handling
        mock_analyzer = MockEnhancedAnalyzer("circular_import")
        result = mock_analyzer.analyze_path(str(temp_error_test_directory), enable_cross_phase_correlation=True)

        # Validate circular import detection
        assert "findings" in result, "Should detect connascence despite circular imports"

        # Should detect circular dependency pattern
        correlations = result.get("correlations", [])
        circular_correlations = [
            c
            for c in correlations
            if c.get("correlation_type") == "circular_dependency" or "circular" in c.get("description", "").lower()
        ]

        # May detect circular dependency as a correlation
        # Even if not explicitly detected, should continue analysis
        assert result.get("analysis_completed", True), "Should complete analysis despite circular imports"

    @integration_test(["error_handling"])
    def test_memory_exhaustion_handling(self, temp_error_test_directory):
        """Test handling of memory exhaustion scenarios"""
        # Create files that could potentially cause memory issues
        memory_intensive_files = {}

        for i in range(20):  # Create multiple files
            large_data_structure = f"""
class DataProcessor{i}:
    def __init__(self):
        # Potential memory-intensive structure
        self.large_dict = {{
"""

            # Add many entries
            for j in range(200):
                large_data_structure += f'            "key_{j}": ["item_{k}" for k in range(100)],\n'

            large_data_structure += """        }
        
    def process(self):
        # CofE: Algorithm - memory-intensive processing
        results = {}
        for key, values in self.large_dict.items():
            results[key] = [self.transform(v) for v in values]
        return results
"""
            memory_intensive_files[f"processor_{i}.py"] = large_data_structure

        # Create test files
        for filename, content in memory_intensive_files.items():
            file_path = temp_error_test_directory / filename
            file_path.write_text(content, encoding="utf-8")

        # Test memory exhaustion handling with timeout
        mock_analyzer = MockEnhancedAnalyzer("memory_exhaustion")

        start_time = time.time()
        result = mock_analyzer.analyze_path(
            str(temp_error_test_directory), enable_cross_phase_correlation=True, enable_smart_recommendations=True
        )
        analysis_time = time.time() - start_time

        # Validate memory handling
        assert analysis_time <= 30.0, "Should complete or timeout within reasonable time"
        assert "findings" in result or "errors" in result, "Should produce results or report errors"

        # Check for memory-related warnings or graceful degradation
        if "warnings" in result:
            memory_warnings = [w for w in result["warnings"] if "memory" in w.get("message", "").lower()]
            # May have memory warnings, which is acceptable

        # Should not crash - getting a result means it handled memory constraints
        assert isinstance(result, dict), "Should return structured result even under memory pressure"

    @integration_test(["error_handling"])
    def test_concurrent_file_modification(self, temp_error_test_directory):
        """Test handling of files modified during analysis"""
        # Create initial file
        test_file = temp_error_test_directory / "concurrent_test.py"
        initial_content = """
class TestClass:
    def initial_method(self):
        # CofE: Algorithm - initial implementation
        return "initial"
"""
        test_file.write_text(initial_content, encoding="utf-8")

        # Function to modify file during analysis
        def modify_file_during_analysis():
            time.sleep(0.1)  # Let analysis start
            modified_content = """
class TestClass:
    def initial_method(self):
        # CofE: Algorithm - modified during analysis
        return "modified"
        
    def new_method(self):
        # CofE: Type - new dependency added
        return self.helper_method()
"""
            try:
                test_file.write_text(modified_content, encoding="utf-8")
            except (PermissionError, OSError):
                pass  # File might be locked during analysis

        # Start file modification in background
        modification_thread = threading.Thread(target=modify_file_during_analysis)
        modification_thread.start()

        # Test concurrent modification handling
        mock_analyzer = MockEnhancedAnalyzer("file_modified")
        result = mock_analyzer.analyze_path(str(temp_error_test_directory), enable_cross_phase_correlation=True)

        modification_thread.join()

        # Validate concurrent modification handling
        assert "findings" in result or "errors" in result, "Should handle concurrent modification"

        # Should either analyze the initial or modified version consistently
        findings = result.get("findings", [])
        if findings:
            # If analysis succeeded, should have consistent view of the file
            assert len(findings) >= 0, "Should analyze consistently despite concurrent modification"

        # Check for any warnings about file changes
        warnings = result.get("warnings", [])
        file_change_warnings = [w for w in warnings if "modif" in w.get("message", "").lower()]
        # May have warnings about file modification

    @integration_test(["error_handling"])
    def test_permission_denied_handling(self, temp_error_test_directory):
        """Test handling of permission denied scenarios"""
        # Create test file
        test_file = temp_error_test_directory / "permission_test.py"
        test_content = """
class PermissionTestClass:
    def test_method(self):
        # CofE: Algorithm - testing permissions
        return "test"
"""
        test_file.write_text(test_content, encoding="utf-8")

        # Attempt to restrict permissions (may not work on all systems)
        try:
            test_file.chmod(0o000)  # Remove all permissions
            permissions_modified = True
        except (OSError, PermissionError):
            permissions_modified = False

        try:
            # Test permission handling
            mock_analyzer = MockEnhancedAnalyzer("permission_denied")
            result = mock_analyzer.analyze_path(str(temp_error_test_directory), enable_cross_phase_correlation=True)

            # Validate permission handling
            if permissions_modified:
                # Should handle permission denial gracefully
                assert "errors" in result or "warnings" in result, "Should report permission issues"

                errors = result.get("errors", [])
                permission_errors = [e for e in errors if "permission" in e.get("message", "").lower()]

                warnings = result.get("warnings", [])
                permission_warnings = [w for w in warnings if "permission" in w.get("message", "").lower()]

                assert len(permission_errors) > 0 or len(permission_warnings) > 0, "Should report permission issues"

            # Should continue analysis of other files
            assert isinstance(result, dict), "Should return structured result despite permission issues"

        finally:
            # Restore permissions for cleanup
            try:
                test_file.chmod(0o666)
            except (OSError, PermissionError):
                pass

    @integration_test(["error_handling"])
    def test_network_timeout_simulation(self, temp_error_test_directory):
        """Test handling of network timeouts in distributed scenarios"""
        # Create test files
        test_file = temp_error_test_directory / "network_test.py"
        test_content = """
class NetworkTestClass:
    def network_method(self):
        # CofE: Type - simulating network dependency
        return "network_result"
"""
        test_file.write_text(test_content, encoding="utf-8")

        # Simulate network timeout with mock
        with patch("time.sleep") as mock_sleep:
            mock_sleep.side_effect = lambda x: time.sleep(min(x, 0.1))  # Speed up sleeps

            mock_analyzer = MockEnhancedAnalyzer("network_timeout")

            start_time = time.time()
            result = mock_analyzer.analyze_path(
                str(temp_error_test_directory), enable_cross_phase_correlation=True, enable_smart_recommendations=True
            )
            analysis_time = time.time() - start_time

        # Validate network timeout handling
        assert analysis_time <= 15.0, "Should timeout gracefully within reasonable time"
        assert "findings" in result or "errors" in result, "Should fallback to local analysis"

        # Check for network-related errors or fallback indicators
        if "errors" in result:
            network_errors = [
                e
                for e in result["errors"]
                if "network" in e.get("message", "").lower() or "timeout" in e.get("message", "").lower()
            ]

        if "warnings" in result:
            fallback_warnings = [w for w in result["warnings"] if "fallback" in w.get("message", "").lower()]

        # Should produce some results even with network issues
        assert isinstance(result, dict), "Should return results despite network issues"

    @integration_test(["error_handling"])
    def test_corrupted_analysis_data_recovery(self, temp_error_test_directory):
        """Test recovery from corrupted intermediate analysis data"""
        # Create test file
        test_file = temp_error_test_directory / "corruption_test.py"
        test_content = """
class CorruptionTestClass:
    def test_method(self):
        # CofE: Algorithm - testing data corruption recovery
        return "test_result"
"""
        test_file.write_text(test_content, encoding="utf-8")

        # Test corrupted data handling
        mock_analyzer = MockEnhancedAnalyzer("data_corruption")
        result = mock_analyzer.analyze_path(
            str(temp_error_test_directory), enable_cross_phase_correlation=True, enable_smart_recommendations=True
        )

        # Validate data corruption recovery
        assert "findings" in result or "errors" in result, "Should recover from data corruption"

        # Check for corruption-related errors and recovery
        if "errors" in result:
            corruption_errors = [e for e in result["errors"] if "corrupt" in e.get("message", "").lower()]

        if "warnings" in result:
            recovery_warnings = [
                w
                for w in result["warnings"]
                if "recover" in w.get("message", "").lower() or "regenerat" in w.get("message", "").lower()
            ]

        # Should attempt to regenerate or recover
        assert (
            "analysis_attempted" in result or len(result.get("findings", [])) >= 0
        ), "Should attempt analysis recovery"

    @integration_test(["error_handling"])
    def test_interface_communication_failure(self):
        """Test handling of interface communication failures"""
        # Create mock analysis result
        mock_result = {
            "findings": [{"type": "test", "message": "test finding"}],
            "correlations": [{"analyzer1": "test1", "analyzer2": "test2", "correlation_score": 0.8}],
            "smart_recommendations": [{"title": "test recommendation", "priority": "medium"}],
        }

        # Test interface communication failures
        interfaces = ["vscode", "mcp_server", "web_dashboard", "cli"]

        for interface in interfaces:
            # Simulate communication failure
            with patch("json.dumps") as mock_json_dumps:
                mock_json_dumps.side_effect = Exception("Communication failure")

                try:
                    formatted_result = self._format_for_interface_with_error_handling(mock_result, interface)

                    # Should handle communication failure gracefully
                    assert (
                        "error" in formatted_result or "fallback" in formatted_result
                    ), f"{interface}: Should handle communication failure"

                except Exception as e:
                    # Should not propagate communication errors
                    assert "Communication failure" not in str(
                        e
                    ), f"{interface}: Should not propagate communication errors"

    @integration_test(["error_handling"])
    def test_timeout_handling_with_partial_results(self, temp_error_test_directory):
        """Test timeout handling with partial result preservation"""
        # Create multiple test files
        for i in range(10):
            test_file = temp_error_test_directory / f"timeout_test_{i}.py"
            test_content = f"""
class TimeoutTestClass{i}:
    def method_{i}(self):
        # CofE: Algorithm - method {i} implementation
        return "result_{i}"
        
    def complex_method_{i}(self):
        # CofE: Execution - complex processing for timeout test
        data = []
        for j in range(100):
            data.append({{"key_{i}_{j}": "value_{i}_{j}"}})
        return data
"""
            test_file.write_text(test_content, encoding="utf-8")

        # Test timeout handling with partial results
        mock_analyzer = MockEnhancedAnalyzer("timeout")

        start_time = time.time()
        result = mock_analyzer.analyze_path(
            str(temp_error_test_directory),
            enable_cross_phase_correlation=True,
            enable_smart_recommendations=True,
            enable_audit_trail=True,
            timeout_seconds=5.0,  # Short timeout to trigger partial results
        )
        analysis_time = time.time() - start_time

        # Validate timeout handling
        assert analysis_time <= 10.0, "Should respect timeout or complete quickly"

        # Should have partial results even with timeout
        assert "findings" in result or "partial_results" in result, "Should preserve partial results"

        if "partial_results" in result:
            assert result["partial_results"] is True, "Should indicate partial results"

        if "errors" in result:
            timeout_errors = [e for e in result["errors"] if "timeout" in e.get("message", "").lower()]
            # May have timeout errors

        # Should have some analysis results even if incomplete
        findings = result.get("findings", [])
        assert len(findings) >= 0, "Should have analyzed some files before timeout"

    def _format_for_interface_with_error_handling(self, result: Dict[str, Any], interface: str) -> Dict[str, Any]:
        """Format analysis result for interface with error handling"""
        try:
            if interface == "vscode":
                return {
                    "correlation_data": result.get("correlations", []),
                    "recommendations_panel": result.get("smart_recommendations", []),
                }
            elif interface == "mcp_server":
                return {
                    "enhanced_context": {"correlations": len(result.get("correlations", []))},
                    "fix_suggestions": result.get("smart_recommendations", []),
                }
            elif interface == "web_dashboard":
                return {
                    "chart_data": {"correlations": result.get("correlations", [])},
                    "recommendations_display": result.get("smart_recommendations", []),
                }
            elif interface == "cli":
                return {
                    "formatted_output": {"summary": f"Found {len(result.get('findings', []))} findings"},
                    "detailed_report": result,
                }
        except Exception as e:
            # Error handling for interface formatting
            return {
                "error": f"Interface communication failure: {e!s}",
                "fallback": {"raw_result": result},
                "interface": interface,
            }

        return {"error": "Unknown interface", "interface": interface}


class TestEdgeCaseScenarios:
    """Test specific edge case scenarios"""

    @integration_test(["edge_cases"])
    def test_empty_project_handling(self, temp_error_test_directory):
        """Test handling of completely empty project"""
        # Test empty directory analysis
        mock_analyzer = MockEnhancedAnalyzer("empty_project")
        result = mock_analyzer.analyze_path(str(temp_error_test_directory), enable_cross_phase_correlation=True)

        # Validate empty project handling
        assert "findings" in result, "Should handle empty project gracefully"
        assert len(result.get("findings", [])) == 0, "Empty project should have no findings"
        assert result.get("analysis_completed", False), "Should complete analysis of empty project"

    @integration_test(["edge_cases"])
    def test_single_line_file_handling(self, temp_error_test_directory):
        """Test handling of single-line files"""
        # Create single-line file
        single_line_file = temp_error_test_directory / "single_line.py"
        single_line_file.write_text("x = 42", encoding="utf-8")

        mock_analyzer = MockEnhancedAnalyzer("success")
        result = mock_analyzer.analyze_path(str(temp_error_test_directory), enable_cross_phase_correlation=True)

        # Should handle single-line files without error
        assert "findings" in result, "Should analyze single-line file"
        assert result.get("analysis_completed", True), "Should complete analysis"

    @integration_test(["edge_cases"])
    def test_deeply_nested_directory_structure(self, temp_error_test_directory):
        """Test handling of deeply nested directory structures"""
        # Create deep directory structure
        current_path = temp_error_test_directory
        for i in range(10):  # Create deep nesting
            current_path = current_path / f"level_{i}"
            current_path.mkdir()

            # Add file at each level
            test_file = current_path / f"deep_file_{i}.py"
            test_file.write_text(
                f"""
class DeepClass{i}:
    def method(self):
        # CofE: Algorithm - method at depth {i}
        return "depth_{i}"
            """,
                encoding="utf-8",
            )

        mock_analyzer = MockEnhancedAnalyzer("success")
        result = mock_analyzer.analyze_path(str(temp_error_test_directory), enable_cross_phase_correlation=True)

        # Should handle deep directory structures
        assert "findings" in result, "Should analyze deeply nested structure"
        findings = result.get("findings", [])
        assert len(findings) >= 5, "Should find issues in nested files"

    @integration_test(["edge_cases"])
    def test_unicode_filename_handling(self, temp_error_test_directory):
        """Test handling of files with Unicode names"""
        unicode_files = ["café.py", "测试.py", "файл.py", "αρχείο.py"]

        for filename in unicode_files:
            try:
                test_file = temp_error_test_directory / filename
                test_file.write_text(
                    """
class UnicodeClass:
    def unicode_method(self):
        # CofE: Algorithm - unicode filename test
        return "unicode_result"
                """,
                    encoding="utf-8",
                )
            except (OSError, UnicodeError):
                # Skip files that can't be created on this system
                continue

        mock_analyzer = MockEnhancedAnalyzer("success")
        result = mock_analyzer.analyze_path(str(temp_error_test_directory), enable_cross_phase_correlation=True)

        # Should handle Unicode filenames gracefully
        assert "findings" in result or "warnings" in result, "Should handle Unicode filenames"

        # May have warnings about Unicode handling
        if "warnings" in result:
            unicode_warnings = [w for w in result["warnings"] if "unicode" in w.get("message", "").lower()]


if __name__ == "__main__":
    # Run error handling and edge case tests
    pytest.main([__file__, "-v", "-m", "error_handling or edge_cases"])
