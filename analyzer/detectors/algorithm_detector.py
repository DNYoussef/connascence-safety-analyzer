"""
Algorithm Detector

Detects Connascence of Algorithm violations - duplicate algorithms across functions.
"""

import ast
import collections
from typing import List, Dict, Tuple

from utils.types import ConnascenceViolation
from base import DetectorBase


class AlgorithmDetector(DetectorBase):
    """Detects duplicate algorithms across functions."""
    
    def __init__(self, file_path: str, source_lines: List[str]):
        super().__init__(file_path, source_lines)
        self.function_hashes: Dict[str, List[Tuple[str, ast.FunctionDef]]] = collections.defaultdict(list)
    
    def detect_violations(self, tree: ast.AST) -> List[ConnascenceViolation]:
        """
        Detect duplicate algorithms in the AST tree.
        
        Args:
            tree: AST tree to analyze
            
        Returns:
            List of algorithm duplication violations
        """
        self.violations.clear()
        self.function_hashes.clear()
        
        # Collect function hashes
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self._analyze_function(node)
        
        # Find duplicates
        self._find_duplicate_algorithms()
        
        return self.violations
    
    def _analyze_function(self, node: ast.FunctionDef) -> None:
        """Analyze a function and create a normalized hash."""
        body_hash = self._normalize_function_body(node)
        
        # Only check substantial functions
        if len(node.body) > 3:
            self.function_hashes[body_hash].append((self.file_path, node))
    
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
            elif isinstance(stmt, ast.Try):
                body_parts.append("try")
            elif isinstance(stmt, ast.With):
                body_parts.append("with")
            elif isinstance(stmt, ast.FunctionDef):
                body_parts.append("function")
            elif isinstance(stmt, ast.ClassDef):
                body_parts.append("class")
            else:
                body_parts.append(type(stmt).__name__.lower())
        
        return "|".join(body_parts)
    
    def _find_duplicate_algorithms(self) -> None:
        """Find and report duplicate algorithms."""
        for body_hash, functions in self.function_hashes.items():
            if len(functions) > 1:
                # Report each duplicate
                for file_path, func_node in functions:
                    self.violations.append(
                        ConnascenceViolation(
                            type="connascence_of_algorithm",
                            severity="medium",
                            file_path=file_path,
                            line_number=func_node.lineno,
                            column=func_node.col_offset,
                            description=f"Function '{func_node.name}' appears to duplicate algorithm from other functions",
                            recommendation="Extract common algorithm into shared function or module",
                            code_snippet=self.get_code_snippet(func_node),
                            context={
                                "duplicate_count": len(functions),
                                "function_name": func_node.name,
                                "similar_functions": [f.name for _, f in functions if f != func_node],
                                "algorithm_hash": body_hash
                            },
                        )
                    )