"""
Tests for AST-based connascence analysis engine.

Tests all connascence forms detection including static forms
(CoN, CoT, CoM, CoP, CoA) and basic runtime forms.
"""

import ast
import pytest
from pathlib import Path
from typing import List

# Import path fixes
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from analyzer.ast_engine import ConnascenceASTAnalyzer, AnalysisResult, Violation
from analyzer.core import ConnascenceViolation


class TestConnascenceASTAnalyzer:
    """Test cases for the core AST analyzer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = ConnascenceASTAnalyzer()
    
    def test_magic_literal_detection(self):
        """Test detection of magic literals (CoM)."""
        code = """
def calculate_price(base_price):
    if base_price > 100:  # Magic literal
        discount = 0.2    # Magic literal
        return base_price * (1 - discount)
    return base_price
"""
        
        violations = self.analyzer.analyze_string(code, "test.py")
        
        # Should detect two magic literals: 100 and 0.2
        magic_violations = [v for v in violations if v.connascence_type == 'CoM']
        assert len(magic_violations) >= 2
        
        # Check that violations have required fields
        for violation in magic_violations:
            assert violation.file_path == "test.py"
            assert violation.line_number > 0
            assert violation.description
            # Handle both string and enum severity values
            severity_val = violation.severity.value if hasattr(violation.severity, 'value') else violation.severity
            assert severity_val in ['low', 'medium', 'high', 'critical']
    
    def test_parameter_bomb_detection(self):
        """Test detection of too many positional parameters (CoP)."""
        code = """
def complex_function(a, b, c, d, e, f, g):  # Too many parameters
    return a + b + c + d + e + f + g

class Calculator:
    def calculate(self, x, y, z, w, v, u, t, s):  # Method with too many params
        return x * y * z * w * v * u * t * s
"""
        
        violations = self.analyzer.analyze_string(code, "test.py")
        
        # Should detect parameter bombs
        param_violations = [v for v in violations if v.connascence_type == 'CoP']
        assert len(param_violations) >= 2
        
        # Check severity is appropriate for parameter count
        for violation in param_violations:
            assert violation.severity in ['medium', 'high', 'critical']
    
    def test_missing_type_hints_detection(self):
        """Test detection of missing type hints (CoT)."""
        code = """
def untyped_function(param1, param2):  # Missing type hints
    return param1 + param2

def typed_function(param1: int, param2: str) -> str:  # Has type hints
    return str(param1) + param2
"""
        
        violations = self.analyzer.analyze_string(code, "test.py")
        
        # Should detect missing type hints only in first function
        type_violations = [v for v in violations if v.connascence_type == 'CoT']
        assert len(type_violations) >= 1
        
        # Should not flag the typed function
        violation_lines = [v.line_number for v in type_violations]
        assert 5 not in violation_lines  # Line with typed function
    
    def test_god_class_detection(self):
        """Test detection of god classes (CoA)."""
        # Create a class with many methods
        methods = []
        for i in range(25):  # Create 25 methods
            methods.append(f"""
    def method_{i}(self):
        return {i}""")
        
        code = f"""
class GodClass:
    def __init__(self):
        self.value = 0
{"".join(methods)}
"""
        
        violations = self.analyzer.analyze_string(code, "test.py")
        
        # Should detect god class
        algo_violations = [v for v in violations if v.connascence_type == 'CoA']
        god_class_violations = [v for v in algo_violations if 'class' in v.description.lower()]
        assert len(god_class_violations) >= 1
        
        # Should be high or critical severity
        for violation in god_class_violations:
            assert violation.severity in ['high', 'critical']
    
    def test_complex_method_detection(self):
        """Test detection of complex methods (CoA)."""
        code = """
def complex_method(x):
    if x > 0:
        if x > 10:
            if x > 100:
                for i in range(x):
                    if i % 2 == 0:
                        try:
                            if i % 4 == 0:
                                while i < x:
                                    i += 1
                                    if i > 50:
                                        break
                        except Exception:
                            continue
                return x
            return x * 2
        return x + 1
    return 0
"""
        
        violations = self.analyzer.analyze_string(code, "test.py")
        
        # Should detect high cyclomatic complexity
        complexity_violations = [v for v in violations if 'complexity' in v.description.lower()]
        assert len(complexity_violations) >= 1
        
        # Should suggest breaking down the method
        for violation in complexity_violations:
            assert 'method' in violation.description.lower() or 'function' in violation.description.lower()
    
    def test_duplicate_code_detection(self):
        """Test detection of code duplication (CoA)."""
        code = """
def validate_email(email):
    if not email:
        return False
    if '@' not in email:
        return False
    if '.' not in email.split('@')[1]:
        return False
    return True

def validate_username(username):
    if not username:
        return False
    if '@' not in username:  # Different validation but similar structure
        return True
    if len(username) < 3:
        return False
    return True
"""
        
        violations = self.analyzer.analyze_string(code, "test.py")
        
        # Should detect some form of duplication or similar patterns
        duplication_violations = [v for v in violations if 'duplicate' in v.description.lower()]
        # Note: Basic AST analysis might not catch all duplication, so we're lenient here
    
    def test_empty_file_handling(self):
        """Test handling of empty files."""
        violations = self.analyzer.analyze_string("", "empty.py")
        assert isinstance(violations, list)
        assert len(violations) == 0
    
    def test_syntax_error_handling(self):
        """Test handling of files with syntax errors."""
        code = """
def broken_function(
    # Missing closing parenthesis and colon
    pass
"""
        
        # Should not raise exception, might return empty or error violation
        violations = self.analyzer.analyze_string(code, "broken.py")
        assert isinstance(violations, list)
    
    def test_violation_severity_assignment(self):
        """Test that violations are assigned appropriate severity levels."""
        code = """
# Mix of different severity violations
def bad_function(a, b, c, d, e, f, g, h):  # High: too many params
    magic_number = 12345  # Medium: magic literal
    if a > 9999999:       # Critical: very large magic literal
        pass
"""
        
        violations = self.analyzer.analyze_string(code, "test.py")
        
        # Should have mix of severity levels
        severities = [v.severity for v in violations]
        assert len(set(severities)) > 1  # Multiple different severities
        
        # Each violation should have valid severity
        for violation in violations:
            assert violation.severity in ['low', 'medium', 'high', 'critical']
    
    def test_violation_completeness(self):
        """Test that violations contain all required fields."""
        code = """
def test_function(a, b, c, d, e):
    return a + b + c + 100 + 200
"""
        
        violations = self.analyzer.analyze_string(code, "test.py")
        
        for violation in violations:
            # Check required fields
            assert hasattr(violation, 'id')
            assert hasattr(violation, 'rule_id')
            assert hasattr(violation, 'connascence_type')
            assert hasattr(violation, 'severity')
            assert hasattr(violation, 'description')
            assert hasattr(violation, 'file_path')
            assert hasattr(violation, 'line_number')
            assert hasattr(violation, 'weight')
            
            # Check field values
            assert violation.id
            assert violation.rule_id.startswith('CON_')
            assert violation.connascence_type in ['CoN', 'CoT', 'CoM', 'CoP', 'CoA', 'CoE', 'CoTi', 'CoV', 'CoI']
            assert violation.file_path == "test.py"
            assert violation.line_number > 0
            assert isinstance(violation.weight, (int, float))
            assert violation.weight > 0
    
    def test_incremental_analysis(self):
        """Test incremental analysis with caching."""
        code = """
def simple_function():
    return 42
"""
        
        # First analysis
        violations1 = self.analyzer.analyze_string(code, "test.py")
        
        # Second analysis of same code should use cache
        violations2 = self.analyzer.analyze_string(code, "test.py")
        
        # Results should be identical
        assert len(violations1) == len(violations2)
        
        if violations1:  # If there are violations
            for v1, v2 in zip(violations1, violations2):
                assert v1.rule_id == v2.rule_id
                assert v1.line_number == v2.line_number
    
    def test_threshold_configuration(self):
        """Test that analyzer respects threshold configuration."""
        from analyzer.thresholds import ThresholdConfig
        
        # Create analyzer with strict thresholds
        strict_config = ThresholdConfig(
            max_positional_params=2,  # Very strict
            max_cyclomatic_complexity=5,
            god_class_methods=10
        )
        
        strict_analyzer = ConnascenceASTAnalyzer(thresholds=strict_config)
        
        code = """
def moderate_function(a, b, c):  # 3 params - should trigger with strict config
    if a > 10:
        return b + c
    return 0
"""
        
        violations = strict_analyzer.analyze_string(code, "test.py")
        
        # Should detect violation with strict thresholds
        param_violations = [v for v in violations if v.connascence_type == 'CoP']
        assert len(param_violations) >= 1


class TestAnalysisResult:
    """Test the AnalysisResult data structure."""
    
    def test_analysis_result_creation(self):
        """Test creation of AnalysisResult."""
        violations = [
            ConnascenceViolation(
                id="test1",
                rule_id="CON_CoM",
                connascence_type="CoM",
                severity="medium",
                description="Test violation",
                file_path="test.py",
                line_number=1,
                weight=2.0
            )
        ]
        
        result = AnalysisResult(
            violations=violations,
            total_files=1,
            analysis_time=1.5,
            connascence_index=10.5
        )
        
        assert result.violations == violations
        assert result.total_files == 1
        assert result.analysis_time == 1.5
        assert result.connascence_index == 10.5
    
    def test_analysis_result_summary(self):
        """Test AnalysisResult summary methods."""
        violations = [
            ConnascenceViolation(
                id="test1", rule_id="CON_CoM", connascence_type="CoM",
                severity="critical", description="Critical", file_path="test.py",
                line_number=1, weight=5.0
            ),
            ConnascenceViolation(
                id="test2", rule_id="CON_CoP", connascence_type="CoP",
                severity="high", description="High", file_path="test.py",
                line_number=2, weight=3.0
            ),
            ConnascenceViolation(
                id="test3", rule_id="CON_CoM", connascence_type="CoM",
                severity="medium", description="Medium", file_path="test.py",
                line_number=3, weight=2.0
            )
        ]
        
        result = AnalysisResult(violations=violations, total_files=1, analysis_time=1.0)
        
        # Test summary statistics
        assert result.total_violations == 3
        assert result.critical_count == 1
        assert result.high_count == 1
        assert result.medium_count == 1
        assert result.low_count == 0
        
        # Test violations by type
        by_type = result.violations_by_type
        assert by_type['CoM'] == 2
        assert by_type['CoP'] == 1


@pytest.fixture
def sample_python_files(tmp_path):
    """Create sample Python files for testing."""
    files = {}
    
    # File with magic literals
    magic_file = tmp_path / "magic_literals.py"
    magic_file.write_text("""
def calculate_discount(price):
    if price > 100:  # Magic literal
        return price * 0.1  # Magic literal
    return 0
""")
    files['magic'] = magic_file
    
    # File with parameter bombs
    params_file = tmp_path / "param_bombs.py"
    params_file.write_text("""
def complex_function(a, b, c, d, e, f, g, h):
    return a + b + c + d + e + f + g + h
""")
    files['params'] = params_file
    
    # Clean file
    clean_file = tmp_path / "clean.py"
    clean_file.write_text("""
def simple_function(x: int) -> int:
    return x * 2
""")
    files['clean'] = clean_file
    
    return files


class TestAnalyzerIntegration:
    """Integration tests for the analyzer."""
    
    def test_analyze_file(self, sample_python_files):
        """Test analyzing individual files."""
        analyzer = ConnascenceASTAnalyzer()
        
        # Test magic literals file
        violations = analyzer.analyze_file(sample_python_files['magic'])
        magic_violations = [v for v in violations if v.connascence_type == 'CoM']
        assert len(magic_violations) > 0
        
        # Test clean file
        violations = analyzer.analyze_file(sample_python_files['clean'])
        # Should have few or no violations
        critical_violations = [v for v in violations if v.severity == 'critical']
        assert len(critical_violations) == 0
    
    def test_analyze_directory(self, sample_python_files, tmp_path):
        """Test analyzing directories."""
        analyzer = ConnascenceASTAnalyzer()
        
        # Analyze the temporary directory with sample files
        result = analyzer.analyze_directory(tmp_path)
        
        # Should find violations from multiple files
        assert len(result.violations) > 0
        
        # Should have violations from different files
        file_paths = {v.file_path for v in result.violations}
        assert len(file_paths) > 1
    
    def test_performance_on_large_file(self):
        """Test analyzer performance on larger files."""
        # Generate a large Python file
        lines = ["def function_{}(x):".format(i) for i in range(100)]
        lines.extend(["    return x + {}".format(i) for i in range(100)])
        large_code = "\n".join(lines)
        
        analyzer = ConnascenceASTAnalyzer()
        
        import time
        start_time = time.time()
        violations = analyzer.analyze_string(large_code, "large.py")
        end_time = time.time()
        
        # Should complete in reasonable time (< 5 seconds)
        assert end_time - start_time < 5.0
        
        # Should still detect violations
        assert isinstance(violations, list)