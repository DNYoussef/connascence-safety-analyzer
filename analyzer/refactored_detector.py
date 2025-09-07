"""
Refactored ConnascenceDetector

This is the refactored version that uses specialized detector classes.
This will replace the massive ConnascenceDetector class once testing is complete.
"""

import ast
import collections
from typing import Any, List

from utils.types import ConnascenceViolation
from detectors import (
    PositionDetector,
    MagicLiteralDetector, 
    AlgorithmDetector,
    GodObjectDetector,
    TimingDetector
)


class RefactoredConnascenceDetector(ast.NodeVisitor):
    """Refactored AST visitor that orchestrates specialized detectors."""

    def __init__(self, file_path: str, source_lines: list[str]):
        self.file_path = file_path
        self.source_lines = source_lines
        self.violations: list[ConnascenceViolation] = []

        # Tracking structures for remaining functionality
        self.function_definitions: dict[str, ast.FunctionDef] = {}
        self.class_definitions: dict[str, ast.ClassDef] = {}
        self.imports: set[str] = set()
        self.global_vars: set[str] = set()

        # Initialize specialized detectors
        self.position_detector = PositionDetector(file_path, source_lines)
        self.magic_literal_detector = MagicLiteralDetector(file_path, source_lines)
        self.algorithm_detector = AlgorithmDetector(file_path, source_lines)
        self.god_object_detector = GodObjectDetector(file_path, source_lines)
        self.timing_detector = TimingDetector(file_path, source_lines)

    def get_code_snippet(self, node: ast.AST, context_lines: int = 2) -> str:
        """Extract code snippet around the given node."""
        if not hasattr(node, "lineno"):
            return ""

        start_line = max(0, node.lineno - context_lines - 1)
        end_line = min(len(self.source_lines), node.lineno + context_lines)

        lines = []
        for i in range(start_line, end_line):
            marker = ">>>" if i == node.lineno - 1 else "   "
            lines.append(f"{marker} {i+1:3d}: {self.source_lines[i].rstrip()}")

        return "\n".join(lines)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Track function definitions for analysis."""
        self.function_definitions[node.name] = node
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        """Track class definitions for analysis."""
        self.class_definitions[node.name] = node
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        """Track imports for dependency analysis."""
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Track imports for dependency analysis."""
        if node.module:
            for alias in node.names:
                self.imports.add(f"{node.module}.{alias.name}")
        self.generic_visit(node)

    def visit_Global(self, node: ast.Global):
        """Track global variable usage (Connascence of Identity)."""
        for name in node.names:
            self.global_vars.add(name)
        self.generic_visit(node)

    def detect_all_violations(self, tree: ast.AST) -> List[ConnascenceViolation]:
        """
        Run all specialized detectors and collect violations.
        
        Args:
            tree: AST tree to analyze
            
        Returns:
            Combined list of all violations
        """
        all_violations = []
        
        # Run specialized detectors
        all_violations.extend(self.position_detector.detect_violations(tree))
        all_violations.extend(self.magic_literal_detector.detect_violations(tree))
        all_violations.extend(self.algorithm_detector.detect_violations(tree))
        all_violations.extend(self.god_object_detector.detect_violations(tree))
        all_violations.extend(self.timing_detector.detect_violations(tree))
        
        # Handle remaining violations (global usage, etc.)
        self.visit(tree)  # Collect tracking info
        all_violations.extend(self._detect_global_violations(tree))
        
        self.violations = all_violations
        return all_violations

    def _detect_global_violations(self, tree: ast.AST) -> List[ConnascenceViolation]:
        """Detect excessive global variable usage."""
        violations = []
        
        if len(self.global_vars) > 5:
            # Find a representative location (first global usage)
            for node in ast.walk(tree):
                if isinstance(node, ast.Global):
                    violations.append(
                        ConnascenceViolation(
                            type="connascence_of_identity",
                            severity="high",
                            file_path=self.file_path,
                            line_number=node.lineno,
                            column=node.col_offset,
                            description=f"Excessive global variable usage: {len(self.global_vars)} globals",
                            recommendation="Use dependency injection, configuration objects, or class attributes",
                            code_snippet=self.get_code_snippet(node),
                            context={
                                "global_count": len(self.global_vars), 
                                "global_vars": list(self.global_vars)
                            },
                        )
                    )
                    break
        
        return violations

    def finalize_analysis(self):
        """Legacy method for compatibility - now handled by detect_all_violations."""
        pass