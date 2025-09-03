"""
Unit Tests for Refactored Architecture

Tests for the extracted classes and refactored God Objects.
Validates that refactoring maintains functionality while reducing complexity.
"""

import ast
import pytest
from pathlib import Path
from typing import List

# Import refactored components
from src.analyzer.helpers.violation_reporter import ViolationReporter, ConnascenceViolation
from src.analyzer.helpers.ast_analysis_helper import ASTAnalysisHelper
from src.analyzer.helpers.context_analyzer import ContextAnalyzer
from src.analyzer.detectors.refactored_connascence_detector import ConnascenceDetector, ConnascenceAnalyzer
from src.analyzer.analyzers.magic_literal_analyzer import MagicLiteralAnalyzer, MagicLiteralConfig
from src.analyzer.analyzers.parameter_analyzer import ParameterAnalyzer, ParameterConfig
from src.analyzer.analyzers.complexity_analyzer import ComplexityAnalyzer, ComplexityConfig
from src.analyzer.analyzers.refactored_ast_analyzer import RefactoredConnascenceASTAnalyzer, AnalyzerConfig


class TestViolationReporter:
    """Test the extracted ViolationReporter class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.file_path = "test.py"
        self.source_lines = [
            "def test_function(a, b, c, d, e):",
            "    if a > 100:",
            "        return b * 0.2",
            "    return c + d + e"
        ]
        self.reporter = ViolationReporter(self.file_path, self.source_lines)
    
    def test_create_position_violation(self):
        """Test creation of position violations."""
        # Create a mock function node
        code = "def test_function(a, b, c, d, e): pass"
        tree = ast.parse(code)
        func_node = tree.body[0]
        
        violation = self.reporter.create_position_violation(func_node, 5)
        
        assert violation.type == "connascence_of_position"
        assert violation.severity == "high"
        assert violation.file_path == self.file_path
        assert "5 positional parameters" in violation.description
        assert violation.context["parameter_count"] == 5
        assert violation.context["function_name"] == "test_function"
    
    def test_create_meaning_violation(self):
        """Test creation of meaning violations."""
        code = "x = 42"
        tree = ast.parse(code)
        const_node = tree.body[0].value
        
        violation = self.reporter.create_meaning_violation(const_node, 42, False)
        
        assert violation.type == "connascence_of_meaning"
        assert violation.severity == "medium"  # Not in conditional
        assert "Magic literal '42'" in violation.description
        assert violation.context["literal_value"] == 42
    
    def test_create_god_object_violation(self):
        """Test creation of god object violations."""
        code = "class TestClass: pass"
        tree = ast.parse(code)
        class_node = tree.body[0]
        
        violation = self.reporter.create_god_object_violation(class_node, 25, 600)
        
        assert violation.type == "god_object"
        assert violation.severity == "critical"
        assert "25 methods" in violation.description
        assert "600 lines" in violation.description
        assert violation.context["method_count"] == 25
        assert violation.context["estimated_loc"] == 600


class TestASTAnalysisHelper:
    """Test the extracted ASTAnalysisHelper class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.source_lines = [
            "def func1():",
            "    return 1",
            "def func2():",
            "    return 1",
            "x = 42",
            "global y"
        ]
        self.helper = ASTAnalysisHelper(self.source_lines)
    
    def test_normalize_function_body(self):
        """Test function body normalization."""
        code = """
def test_func():
    if True:
        return 42
    else:
        x = 1
        return x
"""
        tree = ast.parse(code)
        func_node = tree.body[0]
        
        normalized = self.helper.normalize_function_body(func_node)
        
        # Should contain normalized elements
        assert "if" in normalized
        assert "return" in normalized
        assert "assign" in normalized
    
    def test_collect_function_definitions(self):
        """Test function definition collection."""
        code = """
def func1():
    pass

def func2():
    pass

class TestClass:
    def method1(self):
        pass
"""
        tree = ast.parse(code)
        functions = self.helper.collect_function_definitions(tree)
        
        # Should find all functions including methods
        assert len(functions) == 3
        assert "func1" in functions
        assert "func2" in functions
        assert "method1" in functions
    
    def test_collect_magic_literals(self):
        """Test magic literal collection."""
        code = """
x = 42
y = "hello world"
z = [1, 2, 3, 999]
valid = 0  # Should be excluded
"""
        tree = ast.parse(code)
        literals = self.helper.collect_magic_literals(tree)
        
        # Should find magic literals but exclude common values
        literal_values = [value for _, value in literals]
        assert 42 in literal_values
        assert "hello world" in literal_values
        assert 999 in literal_values
        assert 0 not in literal_values  # Common value, should be excluded


class TestContextAnalyzer:
    """Test the extracted ContextAnalyzer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.file_path = "test.py"
        self.source_lines = [
            "def complex_function(x, y, z):",
            "    if x > 100:",
            "        return y * 0.2",
            "    return z"
        ]
        self.analyzer = ContextAnalyzer(self.file_path, self.source_lines)
    
    def test_get_function_context(self):
        """Test function context analysis."""
        code = """
def test_function(a, b, c=None):
    '''Test docstring'''
    if a:
        return b
    return c
"""
        tree = ast.parse(code)
        func_node = tree.body[0]
        
        context = self.analyzer.get_function_context(func_node)
        
        assert context["name"] == "test_function"
        assert context["parameter_count"] == 3
        assert context["docstring"] == "Test docstring"
        assert context["body_length"] == 3
        assert len(context["parameters"]["parameter_names"]) == 3
    
    def test_analyze_complexity_context(self):
        """Test complexity context analysis."""
        code = """
def complex_function(x):
    if x > 0:
        if x > 10:
            for i in range(x):
                if i % 2 == 0:
                    try:
                        return i
                    except:
                        continue
    return 0
"""
        tree = ast.parse(code)
        func_node = tree.body[0]
        
        context = self.analyzer.analyze_complexity_context(func_node)
        
        assert context["cyclomatic_complexity"] > 5
        assert context["nesting_depth"] > 2
        assert context["branch_count"] >= 2
        assert context["loop_count"] >= 1
        assert context["try_except_count"] >= 1


class TestMagicLiteralAnalyzer:
    """Test the specialized MagicLiteralAnalyzer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.file_path = "test.py"
        self.source_lines = [
            "def calculate(x):",
            "    if x > 100:",
            "        return x * 0.2",
            "    return x"
        ]
        self.analyzer = MagicLiteralAnalyzer(self.file_path, self.source_lines)
    
    def test_magic_number_detection(self):
        """Test magic number detection."""
        code = """
def calculate_price(base):
    if base > 100:  # Magic number
        discount = 0.2  # Magic number
        return base * discount
    return base
"""
        tree = ast.parse(code)
        violations = self.analyzer.analyze(tree)
        
        # Should detect magic numbers 100 and 0.2
        magic_violations = [v for v in violations if "100" in v.description or "0.2" in v.description]
        assert len(magic_violations) >= 2
        
        # Check severity assignment
        conditional_violations = [v for v in violations if v.severity == "high"]
        assert len(conditional_violations) >= 1  # 100 is in conditional
    
    def test_security_related_detection(self):
        """Test security-related magic literal detection."""
        self.source_lines = [
            "password = 'secret123'",
            "api_key = 'abc-def-ghi'"
        ]
        self.analyzer = MagicLiteralAnalyzer(self.file_path, self.source_lines)
        
        code = """
password = 'secret123'
api_key = 'abc-def-ghi'
"""
        tree = ast.parse(code)
        violations = self.analyzer.analyze(tree)
        
        # Should detect security-related strings with critical severity
        critical_violations = [v for v in violations if v.severity == "critical"]
        assert len(critical_violations) >= 1


class TestParameterAnalyzer:
    """Test the specialized ParameterAnalyzer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.file_path = "test.py"
        self.source_lines = ["def test_func(a, b, c, d, e): pass"]
        self.analyzer = ParameterAnalyzer(self.file_path, self.source_lines)
    
    def test_parameter_count_violation(self):
        """Test parameter count violation detection."""
        code = "def excessive_params(a, b, c, d, e, f, g): pass"
        tree = ast.parse(code)
        violations = self.analyzer.analyze(tree)
        
        # Should detect parameter count violation
        param_violations = [v for v in violations if "positional parameters" in v.description]
        assert len(param_violations) >= 1
        assert param_violations[0].severity in ["high", "critical"]
    
    def test_boolean_parameter_detection(self):
        """Test boolean parameter detection."""
        code = "def func_with_flag(data, process_immediately=True): pass"
        tree = ast.parse(code)
        violations = self.analyzer.analyze(tree)
        
        # Should detect boolean flag parameter
        flag_violations = [v for v in violations if "Boolean parameter" in v.description]
        assert len(flag_violations) >= 1
    
    def test_function_call_analysis(self):
        """Test function call analysis."""
        code = "result = some_function(1, 2, 3, 4, 5, 6, 7)"
        tree = ast.parse(code)
        violations = self.analyzer.analyze(tree)
        
        # Should detect excessive positional arguments in call
        call_violations = [v for v in violations if "Function call with" in v.description]
        assert len(call_violations) >= 1


class TestComplexityAnalyzer:
    """Test the specialized ComplexityAnalyzer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.file_path = "test.py"
        self.source_lines = []
        self.analyzer = ComplexityAnalyzer(self.file_path, self.source_lines)
    
    def test_cyclomatic_complexity_detection(self):
        """Test cyclomatic complexity detection."""
        code = """
def complex_function(x):
    if x > 0:
        if x > 10:
            if x > 100:
                for i in range(x):
                    if i % 2 == 0:
                        if i % 4 == 0:
                            while i < x:
                                if i > 50:
                                    break
                                i += 1
                return i
            return x * 2
        return x + 1
    return 0
"""
        tree = ast.parse(code)
        violations = self.analyzer.analyze(tree)
        
        # Should detect high complexity
        complexity_violations = [v for v in violations if "cyclomatic complexity" in v.description]
        assert len(complexity_violations) >= 1
        assert complexity_violations[0].severity in ["high", "critical"]
    
    def test_god_class_detection(self):
        """Test God Object detection."""
        # Create a class with many methods
        methods = "\n".join([f"    def method_{i}(self): pass" for i in range(25)])
        code = f"""
class GodClass:
    def __init__(self):
        self.data = 0
{methods}
"""
        tree = ast.parse(code)
        violations = self.analyzer.analyze(tree)
        
        # Should detect God Object
        god_violations = [v for v in violations if "God Object" in v.description]
        assert len(god_violations) >= 1
        assert god_violations[0].severity == "critical"


class TestRefactoredConnascenceDetector:
    """Test the refactored ConnascenceDetector."""
    
    def test_composition_works(self):
        """Test that the refactored detector works with composition."""
        source_lines = [
            "def bad_function(a, b, c, d, e):",
            "    if a > 100:",
            "        return b * 0.2",
            "    return c"
        ]
        
        detector = ConnascenceDetector("test.py", source_lines)
        tree = ast.parse("\n".join(source_lines))
        detector.visit(tree)
        detector.finalize_analysis()
        
        # Should detect violations using helper classes
        assert len(detector.violations) > 0
        
        # Should maintain the same interface
        violation_types = [v.type for v in detector.violations]
        assert "connascence_of_position" in violation_types or "connascence_of_meaning" in violation_types


class TestRefactoredASTAnalyzer:
    """Test the refactored AST analyzer."""
    
    def test_specialized_analyzers_integration(self):
        """Test that specialized analyzers work together."""
        config = AnalyzerConfig()
        analyzer = RefactoredConnascenceASTAnalyzer(config)
        
        # Test with a sample Python file content
        code = """
def complex_function(a, b, c, d, e, f):
    secret_key = "abc123"
    if a > 100:
        if b > 200:
            for i in range(10):
                if i % 2 == 0:
                    return c * 0.15
    return d + e + f

class GodClass:
    def __init__(self): pass
""" + "\n".join([f"    def method_{i}(self): pass" for i in range(25)])
        
        # Create temporary file for testing
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = Path(f.name)
        
        try:
            violations = analyzer.analyze_file(temp_path)
            
            # Should find multiple types of violations
            violation_types = set(v.type for v in violations)
            assert len(violation_types) > 1  # Multiple analyzers should contribute
            assert len(violations) > 3  # Should find several issues
            
        finally:
            temp_path.unlink()  # Clean up


@pytest.fixture
def sample_code_with_issues():
    """Fixture providing sample code with various issues."""
    return '''
def problematic_function(a, b, c, d, e, f, g, h):
    """Function with multiple connascence issues."""
    secret = "hardcoded_password"
    magic_number = 42
    threshold = 100
    
    if a > threshold:
        if b > magic_number:
            for i in range(1000):
                if i % 2 == 0:
                    try:
                        if c > 500:
                            while d < 50:
                                d += 1
                                if d > 25:
                                    break
                    except Exception:
                        continue
                    return e * 0.25
        return f + g
    return h

class MassiveClass:
    def __init__(self):
        self.data = []
    
    def method_1(self): pass
    def method_2(self): pass
    def method_3(self): pass
    def method_4(self): pass
    def method_5(self): pass
    def method_6(self): pass
    def method_7(self): pass
    def method_8(self): pass
    def method_9(self): pass
    def method_10(self): pass
    def method_11(self): pass
    def method_12(self): pass
    def method_13(self): pass
    def method_14(self): pass
    def method_15(self): pass
    def method_16(self): pass
    def method_17(self): pass
    def method_18(self): pass
    def method_19(self): pass
    def method_20(self): pass
    def method_21(self): pass
    def method_22(self): pass
'''


class TestIntegrationRefactoredVsOriginal:
    """Integration tests comparing refactored vs original behavior."""
    
    def test_violation_count_consistency(self, sample_code_with_issues):
        """Test that refactored version finds similar violations to original."""
        # This would compare against the original analyzer if imported
        # For now, we test that the refactored version finds expected violations
        
        config = AnalyzerConfig()
        analyzer = RefactoredConnascenceASTAnalyzer(config)
        
        # Create temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(sample_code_with_issues)
            temp_path = Path(f.name)
        
        try:
            violations = analyzer.analyze_file(temp_path)
            
            # Should find various types of issues
            assert len(violations) >= 5  # Multiple issues should be detected
            
            # Should find parameter issues
            param_issues = [v for v in violations if "parameter" in v.description.lower()]
            assert len(param_issues) >= 1
            
            # Should find complexity issues
            complexity_issues = [v for v in violations if "complexity" in v.description.lower() or "god" in v.description.lower()]
            assert len(complexity_issues) >= 1
            
            # Should find magic literal issues
            magic_issues = [v for v in violations if "magic" in v.description.lower() or "literal" in v.description.lower()]
            assert len(magic_issues) >= 1
            
        finally:
            temp_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])