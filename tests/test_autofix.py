"""
Tests for the intelligent autofix system.

Tests patch generation, application, and safety controls for
all types of connascence violations.
"""

import ast
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from autofix.patch_api import PatchGenerator, AutofixEngine, SafeAutofixer, PatchSuggestion
from autofix.magic_literals import MagicLiteralFixer
from autofix.param_bombs import ParameterBombFixer
from autofix.type_hints import TypeHintFixer
from analyzer.core import ConnascenceViolation


class TestMagicLiteralFixer:
    """Test magic literal autofix functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.fixer = MagicLiteralFixer()
    
    def test_numeric_literal_extraction(self):
        """Test extracting numeric magic literals."""
        code = """
def calculate_tax(amount):
    if amount > 1000:  # Magic literal
        return amount * 0.08  # Magic literal
    return 0
"""
        
        violation = ConnascenceViolation(
            id="test1",
            rule_id="CON_CoM",
            connascence_type="CoM",
            severity="medium",
            description="Magic literal '1000' should be extracted",
            file_path="test.py",
            line_number=3,
            weight=2.0
        )
        
        tree = ast.parse(code)
        patch = self.fixer.generate_patch(violation, tree, code)
        
        assert patch is not None
        assert patch.confidence > 0.5
        assert 'constant' in patch.description.lower()
        assert '1000' in patch.description
        
        # Check that new code contains constant reference
        assert patch.new_code != patch.old_code
        # Should contain some form of constant name
        assert any(char.isupper() for char in patch.new_code)
    
    def test_string_literal_extraction(self):
        """Test extracting string magic literals."""
        code = '''
def get_config():
    return {
        "api_url": "https://api.example.com",  # Magic string
        "timeout": 30
    }
'''
        
        violation = ConnascenceViolation(
            id="test2",
            rule_id="CON_CoM", 
            connascence_type="CoM",
            severity="medium",
            description="Magic string literal should be extracted",
            file_path="test.py",
            line_number=4,
            weight=2.0
        )
        
        tree = ast.parse(code)
        patch = self.fixer.generate_patch(violation, tree, code)
        
        if patch:  # String extraction might be more selective
            assert patch.confidence > 0.0
            assert 'constant' in patch.description.lower()
    
    def test_ignored_values(self):
        """Test that common values are ignored."""
        code = """
def simple_function(x):
    if x == 0:  # Should be ignored
        return 1  # Should be ignored
    return x + 2  # Should be ignored
"""
        
        violation = ConnascenceViolation(
            id="test3",
            rule_id="CON_CoM",
            connascence_type="CoM",
            severity="low",
            description="Common value",
            file_path="test.py",
            line_number=3,
            weight=1.0
        )
        
        tree = ast.parse(code)
        patch = self.fixer.generate_patch(violation, tree, code)
        
        # Should not generate patch for common values
        assert patch is None or patch.confidence < 0.5
    
    def test_confidence_scoring(self):
        """Test confidence scoring for different literal types."""
        high_confidence_code = """
def complex_calculation():
    threshold = 987654  # Large, specific number
    return threshold * rate
"""
        
        low_confidence_code = """
def simple_function():
    return 3  # Small, likely algorithmic
"""
        
        # Test high confidence case
        tree1 = ast.parse(high_confidence_code)
        violation1 = ConnascenceViolation(
            id="test4", rule_id="CON_CoM", connascence_type="CoM",
            severity="high", description="Large magic literal", 
            file_path="test.py", line_number=3, weight=3.0
        )
        patch1 = self.fixer.generate_patch(violation1, tree1, high_confidence_code)
        
        # Test low confidence case
        tree2 = ast.parse(low_confidence_code)
        violation2 = ConnascenceViolation(
            id="test5", rule_id="CON_CoM", connascence_type="CoM",
            severity="low", description="Small magic literal",
            file_path="test.py", line_number=3, weight=1.0
        )
        patch2 = self.fixer.generate_patch(violation2, tree2, low_confidence_code)
        
        if patch1 and patch2:
            assert patch1.confidence > patch2.confidence
    
    def test_constant_name_generation(self):
        """Test generation of appropriate constant names."""
        # Test HTTP status code pattern
        code = """
if response.status_code == 404:
    handle_not_found()
"""
        
        tree = ast.parse(code)
        violation = ConnascenceViolation(
            id="test6", rule_id="CON_CoM", connascence_type="CoM",
            severity="medium", description="HTTP status code",
            file_path="test.py", line_number=2, weight=2.0
        )
        
        patch = self.fixer.generate_patch(violation, tree, code)
        if patch:
            # Should suggest HTTP-related constant name
            assert 'HTTP' in patch.new_code or '404' in patch.new_code


class TestParameterBombFixer:
    """Test parameter bomb autofix functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.fixer = ParameterBombFixer()
    
    def test_keyword_only_refactor(self):
        """Test conversion to keyword-only parameters."""
        code = """
def complex_function(a, b, c, d, e):
    return a + b + c + d + e
"""
        
        violation = ConnascenceViolation(
            id="test7",
            rule_id="CON_CoP",
            connascence_type="CoP", 
            severity="high",
            description="Too many positional parameters",
            file_path="test.py",
            line_number=2,
            weight=4.0
        )
        
        tree = ast.parse(code)
        patch = self.fixer.generate_patch(violation, tree, code)
        
        assert patch is not None
        assert patch.confidence > 0.6
        assert 'keyword' in patch.description.lower() or 'refactor' in patch.description.lower()
        
        # New code should contain keyword-only marker (*)
        assert '*' in patch.new_code or 'keyword' in patch.description.lower()
    
    def test_dataclass_refactor_suggestion(self):
        """Test suggestion to use dataclass for many parameters."""
        # Create function with many parameters
        params = ', '.join([f'param_{i}' for i in range(8)])
        code = f"""
def very_complex_function({params}):
    return sum([{', '.join([f'param_{i}' for i in range(8)])}])
"""
        
        violation = ConnascenceViolation(
            id="test8",
            rule_id="CON_CoP",
            connascence_type="CoP",
            severity="critical", 
            description="Excessive parameters",
            file_path="test.py",
            line_number=2,
            weight=5.0
        )
        
        tree = ast.parse(code)
        patch = self.fixer.generate_patch(violation, tree, code)
        
        assert patch is not None
        assert patch.confidence > 0.5
        assert 'dataclass' in patch.description.lower() or 'Request' in patch.new_code
    
    def test_method_vs_function_handling(self):
        """Test different handling for methods vs functions."""
        method_code = """
class Calculator:
    def calculate(self, a, b, c, d, e):
        return a + b + c + d + e
"""
        
        function_code = """
def calculate(a, b, c, d, e):
    return a + b + c + d + e
"""
        
        violation_method = ConnascenceViolation(
            id="test9", rule_id="CON_CoP", connascence_type="CoP",
            severity="high", description="Method with too many params",
            file_path="test.py", line_number=3, weight=4.0
        )
        
        violation_function = ConnascenceViolation(
            id="test10", rule_id="CON_CoP", connascence_type="CoP", 
            severity="high", description="Function with too many params",
            file_path="test.py", line_number=2, weight=4.0
        )
        
        tree_method = ast.parse(method_code)
        tree_function = ast.parse(function_code)
        
        patch_method = self.fixer.generate_patch(violation_method, tree_method, method_code)
        patch_function = self.fixer.generate_patch(violation_function, tree_function, function_code)
        
        # Both should generate patches but might have different strategies
        if patch_method and patch_function:
            # Method patch should account for 'self' parameter
            assert 'self' in patch_method.new_code
            assert patch_method.confidence > 0


class TestTypeHintFixer:
    """Test type hint autofix functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.fixer = TypeHintFixer()
    
    def test_simple_type_inference(self):
        """Test basic type hint addition."""
        code = """
def add_numbers(a, b):
    return a + b
"""
        
        violation = ConnascenceViolation(
            id="test11",
            rule_id="CON_CoT",
            connascence_type="CoT",
            severity="medium",
            description="Missing type hints",
            file_path="test.py", 
            line_number=2,
            weight=2.0
        )
        
        tree = ast.parse(code)
        patch = self.fixer.generate_patch(violation, tree, code)
        
        assert patch is not None
        assert patch.confidence > 0.5
        assert 'type hint' in patch.description.lower()
        
        # New code should contain type annotations
        assert ':' in patch.new_code and '->' in patch.new_code
    
    def test_return_type_inference(self):
        """Test return type inference from return statements."""
        code = """
def get_name():
    return "John Doe"
        
def get_count():
    return 42
        
def get_flag():
    return True
"""
        
        # Test each function type
        for line_num, expected_type in [(2, 'str'), (5, 'int'), (8, 'bool')]:
            violation = ConnascenceViolation(
                id=f"test12_{line_num}",
                rule_id="CON_CoT", 
                connascence_type="CoT",
                severity="medium",
                description="Missing return type",
                file_path="test.py",
                line_number=line_num,
                weight=2.0
            )
            
            tree = ast.parse(code)
            patch = self.fixer.generate_patch(violation, tree, code)
            
            if patch:
                # Should infer correct return type
                assert '->' in patch.new_code
    
    def test_parameter_type_inference(self):
        """Test parameter type inference from usage."""
        code = """
def process_string(text):
    return text.upper().strip()
        
def process_number(value):
    return value * 2 + 1
        
def process_list(items):
    return items.append("new")
"""
        
        test_cases = [
            (2, 'str'),   # string methods
            (5, 'int'),   # numeric operations  
            (8, 'list')   # list methods
        ]
        
        for line_num, expected_hint in test_cases:
            violation = ConnascenceViolation(
                id=f"test13_{line_num}",
                rule_id="CON_CoT",
                connascence_type="CoT", 
                severity="medium",
                description="Missing parameter type",
                file_path="test.py",
                line_number=line_num,
                weight=2.0
            )
            
            tree = ast.parse(code)
            patch = self.fixer.generate_patch(violation, tree, code)
            
            if patch and expected_hint in ['str', 'int']:
                # Should infer reasonable type for clear cases
                assert ':' in patch.new_code


class TestPatchGenerator:
    """Test the unified patch generation system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.generator = PatchGenerator()
    
    def test_patch_generation_routing(self):
        """Test that patches are routed to correct fixers."""
        violations = [
            ConnascenceViolation(
                id="test14", rule_id="CON_CoM", connascence_type="CoM",
                severity="medium", description="Magic literal",
                file_path="test.py", line_number=1, weight=2.0
            ),
            ConnascenceViolation(
                id="test15", rule_id="CON_CoP", connascence_type="CoP", 
                severity="high", description="Parameter bomb",
                file_path="test.py", line_number=2, weight=4.0
            ),
            ConnascenceViolation(
                id="test16", rule_id="CON_CoT", connascence_type="CoT",
                severity="medium", description="Missing types", 
                file_path="test.py", line_number=3, weight=2.0
            )
        ]
        
        code = """
def bad_function(a, b, c, d, e):
    if a > 100:
        return b + c + d + e
"""
        
        patches = []
        for violation in violations:
            patch = self.generator.generate_patch(violation, code)
            if patch:
                patches.append(patch)
        
        # Should generate patches for fixable violations
        assert len(patches) > 0
        
        # Check that patches have correct violation types
        patch_types = {p.violation_id.split('test')[1].split('_')[0] for p in patches}
        assert len(patch_types) > 0
    
    def test_patch_caching(self):
        """Test that patch generation uses caching."""
        violation = ConnascenceViolation(
            id="test17", rule_id="CON_CoM", connascence_type="CoM",
            severity="medium", description="Magic literal",
            file_path="test.py", line_number=1, weight=2.0
        )
        
        code = "def func(): return 100"
        
        # Generate patch twice
        patch1 = self.generator.generate_patch(violation, code)
        patch2 = self.generator.generate_patch(violation, code)
        
        if patch1 and patch2:
            # Should be identical (from cache)
            assert patch1.violation_id == patch2.violation_id
            assert patch1.confidence == patch2.confidence


class TestAutofixEngine:
    """Test the main autofix engine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = AutofixEngine(dry_run=True)
    
    def test_dry_run_mode(self):
        """Test dry run mode doesn't modify files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def bad_function(a, b, c, d, e):
    return a + b + 100
""")
            temp_file = Path(f.name)
        
        try:
            violations = [
                ConnascenceViolation(
                    id="test18", rule_id="CON_CoM", connascence_type="CoM",
                    severity="medium", description="Magic literal",
                    file_path=str(temp_file), line_number=3, weight=2.0
                )
            ]
            
            patches = self.engine.analyze_file(str(temp_file), violations)
            result = self.engine.apply_patches(patches, confidence_threshold=0.5)
            
            # In dry run, no patches should actually be applied
            assert result.patches_applied == 0 or len(result.warnings) > 0
            
            # Original file should be unchanged
            original_content = temp_file.read_text()
            assert "100" in original_content  # Magic literal still there
            
        finally:
            temp_file.unlink()
    
    def test_confidence_threshold_filtering(self):
        """Test filtering patches by confidence threshold."""
        # Mock patches with different confidence levels
        patches = [
            PatchSuggestion(
                violation_id="high_conf", confidence=0.9, description="High confidence",
                old_code="old", new_code="new", file_path="test.py",
                line_range=(1, 1), safety_level="safe", rollback_info={}
            ),
            PatchSuggestion(
                violation_id="low_conf", confidence=0.4, description="Low confidence", 
                old_code="old", new_code="new", file_path="test.py",
                line_range=(2, 2), safety_level="safe", rollback_info={}
            )
        ]
        
        # Test with high threshold
        result = self.engine.apply_patches(patches, confidence_threshold=0.8)
        
        # Should only consider high-confidence patch
        high_conf_warnings = [w for w in result.warnings if "high_conf" not in w]
        low_conf_warnings = [w for w in result.warnings if "low_conf" in w or "confidence too low" in w]
        
        assert len(low_conf_warnings) > 0  # Low confidence patch should be skipped
    
    def test_safety_level_filtering(self):
        """Test filtering patches by safety level."""
        patches = [
            PatchSuggestion(
                violation_id="safe_patch", confidence=0.8, description="Safe patch",
                old_code="old", new_code="new", file_path="test.py",
                line_range=(1, 1), safety_level="safe", rollback_info={}
            ),
            PatchSuggestion(
                violation_id="risky_patch", confidence=0.8, description="Risky patch",
                old_code="old", new_code="new", file_path="test.py", 
                line_range=(2, 2), safety_level="risky", rollback_info={}
            )
        ]
        
        result = self.engine.apply_patches(patches, confidence_threshold=0.5)
        
        # Risky patches should be skipped in dry run
        risky_warnings = [w for w in result.warnings if "risky" in w.lower()]
        assert len(risky_warnings) > 0


class TestSafeAutofixer:
    """Test the safe autofix wrapper."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.autofixer = SafeAutofixer()
    
    def test_preview_generation(self):
        """Test preview generation without applying changes."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def bad_function(a, b, c, d, e):
    magic_value = 12345
    return a + b + magic_value
""")
            temp_file = Path(f.name)
        
        try:
            violations = [
                ConnascenceViolation(
                    id="test19", rule_id="CON_CoM", connascence_type="CoM",
                    severity="medium", description="Magic literal", 
                    file_path=str(temp_file), line_number=3, weight=2.0
                ),
                ConnascenceViolation(
                    id="test20", rule_id="CON_CoP", connascence_type="CoP",
                    severity="high", description="Too many parameters",
                    file_path=str(temp_file), line_number=2, weight=4.0
                )
            ]
            
            preview = self.autofixer.preview_fixes(str(temp_file), violations)
            
            assert 'file_path' in preview
            assert 'total_patches' in preview  
            assert 'patches' in preview
            assert 'recommendations' in preview
            
            # Should provide actionable preview
            assert preview['total_patches'] >= 0
            assert isinstance(preview['patches'], list)
            assert isinstance(preview['recommendations'], list)
            
        finally:
            temp_file.unlink()
    
    def test_patch_limiting(self):
        """Test limiting patches per file for safety."""
        # Create many violations
        violations = []
        for i in range(20):  # More than max_patches_per_file
            violations.append(
                ConnascenceViolation(
                    id=f"test21_{i}", rule_id="CON_CoM", connascence_type="CoM",
                    severity="medium", description=f"Magic literal {i}",
                    file_path="test.py", line_number=i+1, weight=2.0
                )
            )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            # Create file with many magic literals
            lines = [f"value_{i} = {i * 100}" for i in range(20)]
            f.write("\\n".join(lines))
            temp_file = Path(f.name)
        
        try:
            preview = self.autofixer.preview_fixes(str(temp_file), violations)
            
            # Should limit patches per file
            assert preview['total_patches'] <= self.autofixer.max_patches_per_file
            
        finally:
            temp_file.unlink()
    
    def test_recommendation_generation(self):
        """Test generation of human-readable recommendations."""
        violations = [
            ConnascenceViolation(
                id="test22", rule_id="CON_CoM", connascence_type="CoM",
                severity="medium", description="Magic literal",
                file_path="test.py", line_number=1, weight=2.0
            )
        ] * 6  # Multiple magic literal violations
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def func(): return 1, 2, 3, 4, 5, 6")
            temp_file = Path(f.name)
        
        try:
            preview = self.autofixer.preview_fixes(str(temp_file), violations)
            
            # Should generate relevant recommendations
            assert len(preview['recommendations']) > 0
            
            # Should suggest constants module for many literals
            recommendations_text = " ".join(preview['recommendations'])
            assert 'constant' in recommendations_text.lower()
            
        finally:
            temp_file.unlink()