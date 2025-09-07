"""Unit tests for DetectorFactory."""
import ast
import unittest
from src.detectors.detector_factory import DetectorFactory


class TestDetectorFactory(unittest.TestCase):
    
    def setUp(self):
        self.source_lines = [
            "class GodObject:",
            "    def method1(self): pass",
            "    def method2(self): pass",
            # Add many more lines to simulate a god object
        ] + [f"    def method{i}(self): pass" for i in range(3, 25)]
        
        self.factory = DetectorFactory("/test/file.py", self.source_lines)
    
    def test_detect_all_integrates_detectors(self):
        """Test that detect_all runs all detectors and aggregates results."""
        code = """
class LargeClass:
    def __init__(self): pass
    def method1(self): pass
    def method2(self): pass
    def method3(self): pass
    def method4(self): pass
    def method5(self): pass

def bad_position_function(a, b, c, d, e):
    return a + b + c + d + e
"""
        tree = ast.parse(code)
        violations = self.factory.detect_all(tree)
        
        # Should have both god object and position violations
        self.assertGreater(len(violations), 0)
        
        violation_types = [v.type for v in violations]
        self.assertIn("connascence_of_position", violation_types)
    
    def test_detect_by_type(self):
        """Test selective detection by violation type."""
        code = "def bad_function(a, b, c, d, e):\n    return a + b + c + d + e"
        tree = ast.parse(code)
        
        violations = self.factory.detect_by_type(tree, ["connascence_of_position"])
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].type, "connascence_of_position")


if __name__ == '__main__':
    unittest.main()