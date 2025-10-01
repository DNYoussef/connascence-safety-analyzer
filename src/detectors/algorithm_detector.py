"""
Algorithm Detector - Detects Connascence of Algorithm violations.

Extracted from ConnascenceDetector to follow Single Responsibility Principle.
"""
import ast
import collections
from typing import Dict, List

from utils.types import ConnascenceViolation


class AlgorithmDetector(ast.NodeVisitor):
    """Detects duplicate algorithms across functions."""

    def __init__(self, file_path: str, source_lines: List[str]):
        self.file_path = file_path
        self.source_lines = source_lines
        self.violations: List[ConnascenceViolation] = []
        self.function_hashes: Dict[str, List[tuple[str, ast.FunctionDef]]] = collections.defaultdict(list)

    def get_code_snippet(self, node: ast.AST, context_lines: int = 2) -> str:
        """Extract code snippet around the given node. Consolidated implementation."""
        from analyzer.utils.code_utils import get_code_snippet_for_node

        return get_code_snippet_for_node(node, self.source_lines, context_lines)

    def _normalize_function_body(self, node: ast.FunctionDef) -> str:
        """Create normalized hash of function body for duplicate detection."""
        # Extract just the structure, not variable names
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

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Check for algorithm duplication."""
        # Check for algorithm duplication
        body_hash = self._normalize_function_body(node)
        if len(node.body) > 3:  # Only check substantial functions
            self.function_hashes[body_hash].append((self.file_path, node))

        self.generic_visit(node)

    def detect(self, tree: ast.AST) -> List[ConnascenceViolation]:
        """Run algorithm detection and return violations."""
        self.visit(tree)

        # Create violations for duplicates
        for body_hash, functions in self.function_hashes.items():
            if len(functions) > 1:
                # Multiple functions with same algorithm structure
                for file_path, func_node in functions:
                    if file_path == self.file_path:  # Only report for current file
                        duplicate_names = [f.name for _, f in functions if f != func_node]
                        self.violations.append(
                            ConnascenceViolation(
                                type="connascence_of_algorithm",
                                severity="medium",
                                file_path=file_path,
                                line_number=func_node.lineno,
                                column=func_node.col_offset,
                                description=f"Function '{func_node.name}' has duplicate algorithm structure",
                                recommendation=f"Consider extracting common algorithm. Duplicates: {', '.join(duplicate_names)}",
                                code_snippet=self.get_code_snippet(func_node),
                                context={"function_name": func_node.name, "duplicates": duplicate_names},
                            )
                        )

        return self.violations
