"""
Algorithm Detector - Extracted from ConnascenceDetector God Object
==================================================================

Handles algorithm duplicate detection and violation creation.
Part of Phase 1 remediation to decompose ConnascenceDetector.

Extracted Methods (3):
- _normalize_function_body
- _process_algorithm_duplicates
- _create_algorithm_duplicate_violation
"""

import ast
import collections
from typing import Dict, List, Tuple

from fixes.phase0.production_safe_assertions import ProductionAssert

# Import canonical ConnascenceViolation
from utils.types import ConnascenceViolation


class AlgorithmDetector:
    """
    Handles algorithm duplicate detection and violation creation.

    Extracted from ConnascenceDetector to reduce god object complexity.
    """

    def __init__(self, file_path: str, source_lines: List[str]):
        """Initialize with file context."""
        ProductionAssert.not_none(file_path, "file_path")
        ProductionAssert.not_none(source_lines, "source_lines")

        self.file_path = file_path
        self.source_lines = source_lines
        self.function_hashes: Dict[str, List[Tuple[str, ast.FunctionDef]]] = collections.defaultdict(list)
        self.violations: List[ConnascenceViolation] = []

    def normalize_function_body(self, node: ast.FunctionDef) -> str:
        """Create normalized hash of function body for duplicate detection."""
        ProductionAssert.not_none(node, "node")

        body_parts = []
        for stmt in node.body:
            if isinstance(stmt, ast.Return):
                if stmt.value:
                    body_parts.append(f"return {type(stmt.value).__name__}")
                else:
                    body_parts.append("return")
            elif isinstance(stmt, ast.If):
                body_parts.append("if")
            elif isinstance(stmt, ast.For):
                body_parts.append("for")
            elif isinstance(stmt, ast.While):
                body_parts.append("while")
            elif isinstance(stmt, ast.Assign):
                body_parts.append("assign")
            elif isinstance(stmt, ast.Expr):
                if isinstance(stmt.value, ast.Call):
                    body_parts.append("call")
                else:
                    body_parts.append("expr")

        return "|".join(body_parts)

    def track_function(self, node: ast.FunctionDef):
        """Track a function for potential algorithm duplication."""
        ProductionAssert.not_none(node, "node")

        body_hash = self.normalize_function_body(node)
        if len(node.body) > 3:  # Only check substantial functions
            self.function_hashes[body_hash].append((self.file_path, node))

    def process_algorithm_duplicates(self, code_snippet_fn) -> List[ConnascenceViolation]:
        """Process algorithm duplicates and create violations."""
        ProductionAssert.not_none(self.function_hashes, "function_hashes must be initialized")

        self.violations = []

        for body_hash, functions in self.function_hashes.items():
            if len(functions) <= 1:
                continue

            for file_path, func_node in functions:
                violation = self._create_algorithm_duplicate_violation(
                    file_path, func_node, functions, code_snippet_fn
                )
                self.violations.append(violation)

        return self.violations

    def _create_algorithm_duplicate_violation(
        self, file_path: str, func_node: ast.FunctionDef, functions: List[Tuple], code_snippet_fn
    ) -> ConnascenceViolation:
        """Create algorithm duplicate violation."""
        ProductionAssert.not_none(file_path, "file_path")
        ProductionAssert.not_none(func_node, "func_node")

        return ConnascenceViolation(
            type="connascence_of_algorithm",
            severity="medium",
            file_path=file_path,
            line_number=func_node.lineno,
            column=func_node.col_offset,
            description=f"Function '{func_node.name}' appears to duplicate algorithm from other functions",
            recommendation="Extract common algorithm into shared function or module",
            code_snippet=code_snippet_fn(func_node),
            context={
                "duplicate_count": len(functions),
                "function_name": func_node.name,
                "similar_functions": [f.name for _, f in functions if f != func_node],
            },
        )

    def get_function_hashes(self) -> Dict[str, List[Tuple[str, ast.FunctionDef]]]:
        """Get the current function hashes for backward compatibility."""
        return self.function_hashes
