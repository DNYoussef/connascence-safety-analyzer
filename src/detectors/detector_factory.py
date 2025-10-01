"""
Detector Factory - Coordinates specialized detector classes.

Replaces the monolithic ConnascenceDetector with a factory pattern that
coordinates specialized detectors following Single Responsibility Principle.
"""
import ast
from typing import Any, Dict, List

from utils.types import ConnascenceViolation

from .algorithm_detector import AlgorithmDetector
from .god_object_detector import GodObjectDetector

# Import specialized detectors
from .position_detector import PositionDetector


class DetectorFactory:
    """
    Factory class that coordinates specialized connascence detectors.

    This replaces the monolithic 680-line ConnascenceDetector with a
    composable architecture where each detector handles one responsibility.
    """

    def __init__(self, file_path: str, source_lines: List[str]):
        """
        Initialize the detector factory.

        Args:
            file_path: Path to the file being analyzed
            source_lines: List of source code lines for context extraction
        """
        self.file_path = file_path
        self.source_lines = source_lines
        self.violations: List[ConnascenceViolation] = []

        # Initialize all specialized detectors
        self.detectors = [
            PositionDetector(file_path, source_lines),
            AlgorithmDetector(file_path, source_lines),
            GodObjectDetector(file_path, source_lines),
        ]

    def detect_all(self, tree: ast.AST) -> List[ConnascenceViolation]:
        """
        Run all specialized detectors and collect violations.

        Args:
            tree: The AST to analyze

        Returns:
            List of all detected ConnascenceViolation objects from all detectors
        """
        all_violations = []

        for detector in self.detectors:
            try:
                violations = detector.detect(tree)
                all_violations.extend(violations)
            except Exception as e:
                # Log error but continue with other detectors
                print(f"Warning: Detector {detector.__class__.__name__} failed: {e}")

        self.violations = all_violations
        return all_violations.copy()

    def detect_by_type(self, tree: ast.AST, violation_types: List[str]) -> List[ConnascenceViolation]:
        """
        Run only specific detector types.

        Args:
            tree: The AST to analyze
            violation_types: List of violation types to detect

        Returns:
            List of violations from requested detector types
        """
        type_mapping = {
            "connascence_of_position": PositionDetector,
            "connascence_of_algorithm": AlgorithmDetector,
            "god_object": GodObjectDetector,
        }

        selected_violations = []

        for violation_type in violation_types:
            if violation_type in type_mapping:
                detector_class = type_mapping[violation_type]
                detector = detector_class(self.file_path, self.source_lines)
                try:
                    violations = detector.detect(tree)
                    selected_violations.extend(violations)
                except Exception as e:
                    print(f"Warning: {detector_class.__name__} failed: {e}")

        return selected_violations

    def get_detector_statistics(self) -> Dict[str, Any]:
        """
        Get statistics from all detectors.

        Returns:
            Dictionary containing statistics from each detector
        """
        stats = {"total_violations": len(self.violations), "detector_stats": {}}

        for detector in self.detectors:
            detector_name = detector.__class__.__name__
            if hasattr(detector, "get_statistics"):
                stats["detector_stats"][detector_name] = detector.get_statistics()
            else:
                stats["detector_stats"][detector_name] = {"violations": len(getattr(detector, "violations", []))}

        return stats

    # Backward compatibility methods to match original ConnascenceDetector API

    def visit(self, node: ast.AST):
        """Backward compatibility - use detect_all instead."""
        if hasattr(node, "body"):  # It's a module/tree
            return self.detect_all(node)
        else:
            # Create a temporary module wrapper
            module = ast.Module(body=[node], type_ignores=[])
            return self.detect_all(module)

    @property
    def function_definitions(self) -> Dict[str, ast.FunctionDef]:
        """Backward compatibility - aggregate function definitions."""
        functions = {}
        for detector in self.detectors:
            if hasattr(detector, "function_definitions"):
                functions.update(detector.function_definitions)
        return functions

    @property
    def class_definitions(self) -> Dict[str, ast.ClassDef]:
        """Backward compatibility - aggregate class definitions."""
        classes = {}
        for detector in self.detectors:
            if hasattr(detector, "class_definitions"):
                classes.update(detector.class_definitions)
        return classes
