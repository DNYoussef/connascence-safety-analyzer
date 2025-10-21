"""Unit tests for PositionDetector."""

import ast
import unittest

from src.detectors.position_detector import PositionDetector


class TestPositionDetector(unittest.TestCase):
    def setUp(self):
        self.source_lines = [
            "def good_function(a, b, c):",
            "    return a + b + c",
            "",
            "def bad_function(a, b, c, d, e):",
            "    return a + b + c + d + e",
        ]
        self.detector = PositionDetector("/test/file.py", self.source_lines)

    def test_no_violations_for_good_function(self):
        """Test that functions with <=3 params don't trigger violations."""
        code = "def good_function(a, b, c):\n    return a + b + c"
        tree = ast.parse(code)
        violations = self.detector.detect(tree)
        self.assertEqual(len(violations), 0)

    def test_violation_for_bad_function(self):
        """Test that functions with >3 params trigger violations."""
        code = "def bad_function(a, b, c, d, e):\n    return a + b + c + d + e"
        tree = ast.parse(code)
        violations = self.detector.detect(tree)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].type, "connascence_of_position")
        self.assertEqual(violations[0].severity, "high")
        self.assertIn("5 positional parameters", violations[0].description)


if __name__ == "__main__":
    unittest.main()
