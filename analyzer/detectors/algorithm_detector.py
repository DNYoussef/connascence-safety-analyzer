"""
Algorithm Detector

Detects Connascence of Algorithm violations - duplicate algorithms across functions.
"""

import ast
import collections
from typing import List, Dict, Tuple

from utils.types import ConnascenceViolation
from .base import DetectorBase


class AlgorithmDetector(DetectorBase):
    """Detects duplicate algorithms across functions."""
    
    def __init__(self, file_path: str, source_lines: List[str]):
        super().__init__(file_path, source_lines)
        self.function_hashes: Dict[str, List[Tuple[str, ast.FunctionDef]]] = collections.defaultdict(list)
    
    def detect_violations(self, tree: ast.AST) -> List[ConnascenceViolation]:
        """
        Detect duplicate algorithms in the AST tree.
        NASA Rule 5 compliant: Added input validation assertions.
        
        Args:
            tree: AST tree to analyze
            
        Returns:
            List of algorithm duplication violations
        """
        # NASA Rule 5: Input validation assertions
        assert tree is not None, "AST tree cannot be None"
        assert isinstance(tree, ast.AST), "Input must be valid AST object"
        
        self.violations.clear()
        self.function_hashes.clear()
        
        # Collect function hashes
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self._analyze_function(node)
        
        # Find duplicates
        self._find_duplicate_algorithms()
        
        # NASA Rule 7: Validate return value
        assert isinstance(self.violations, list), "violations must be a list"
        return self.violations
    
    def _analyze_function(self, node: ast.FunctionDef) -> None:
        """Analyze a function and create a normalized hash."""
        # NASA Rule 5: Input validation assertions
        assert node is not None, "Function node cannot be None"
        assert isinstance(node, ast.FunctionDef), "Node must be a function definition"
        
        body_hash = self._normalize_function_body(node)
        
        # Only check substantial functions (NASA Rule 1: Avoid trivial complexity)
        if len(node.body) > 3:
            self.function_hashes[body_hash].append((self.file_path, node))
    
    def _normalize_function_body(self, node: ast.FunctionDef) -> str:
        """Create normalized hash of function body for duplicate detection."""
        # NASA Rule 5: Input validation assertions
        assert node is not None, "Function node cannot be None"
        assert hasattr(node, 'body'), "Function node must have body attribute"
        
        # Extract just the structure, not variable names
        body_parts = []
        for stmt in node.body:
            stmt_type = self._get_statement_type(stmt)
            body_parts.append(stmt_type)
        
        result = "|".join(body_parts)
        # NASA Rule 7: Validate return value
        assert isinstance(result, str), "Normalized body must be string"
        return result
    
    def _get_statement_type(self, stmt: ast.stmt) -> str:
        """Get normalized statement type. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation assertion
        assert stmt is not None, "Statement cannot be None"
        
        if isinstance(stmt, ast.Return):
            return f"return {type(stmt.value).__name__}" if stmt.value else "return"
        elif isinstance(stmt, ast.If):
            return "if"
        elif isinstance(stmt, ast.For):
            return "for"
        elif isinstance(stmt, ast.While):
            return "while"
        elif isinstance(stmt, ast.Assign):
            return "assign"
        elif isinstance(stmt, ast.Expr):
            return "call" if isinstance(stmt.value, ast.Call) else "expr"
        elif isinstance(stmt, ast.Try):
            return "try"
        elif isinstance(stmt, ast.With):
            return "with"
        elif isinstance(stmt, ast.FunctionDef):
            return "function"
        elif isinstance(stmt, ast.ClassDef):
            return "class"
        else:
            return type(stmt).__name__.lower()
    
    def _find_duplicate_algorithms(self) -> None:
        """Find and report duplicate algorithms. NASA Rule 4 compliant - reduced nesting."""
        # NASA Rule 5: Input validation assertions
        assert self.function_hashes is not None, "function_hashes must be initialized"
        
        for body_hash, functions in self.function_hashes.items():
            # NASA Rule 1: Use guard clause to avoid deep nesting
            if len(functions) <= 1:
                continue
                
            self._create_violations_for_duplicate_group(body_hash, functions)
    
    def _create_violations_for_duplicate_group(self, body_hash: str, functions: List) -> None:
        """Create violations for a group of duplicate functions. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation assertions
        assert body_hash is not None, "body_hash cannot be None"
        assert functions is not None and len(functions) > 0, "functions list cannot be empty"
        
        filtered_functions = self._filter_duplicate_groups(functions)
        
        for file_path, func_node in filtered_functions:
            violation = self._create_algorithm_violation(body_hash, functions, file_path, func_node)
            self.violations.append(violation)
    
    def _filter_duplicate_groups(self, functions: List) -> List:
        """Filter duplicate function groups for processing. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation assertions
        assert functions is not None, "functions list cannot be None"
        
        # For now, return all functions but this method allows for future filtering logic
        return functions
    
    def _create_algorithm_violation(
        self, body_hash: str, functions: List, file_path: str, func_node
    ) -> ConnascenceViolation:
        """Create a single algorithm violation. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation assertions
        assert body_hash is not None, "body_hash cannot be None"
        assert func_node is not None, "func_node cannot be None"
        
        similar_functions = [f.name for _, f in functions if f != func_node]
        
        return ConnascenceViolation(
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
                "similar_functions": similar_functions,
                "algorithm_hash": body_hash
            },
        )
    
    def analyze_from_data(self, collected_data) -> List[ConnascenceViolation]:
        """
        Optimized two-phase method: Analyze from pre-collected data.
        
        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input assertions
        
        Args:
            collected_data: Pre-collected AST data from unified visitor
            
        Returns:
            List of algorithm duplication violations
        """
        assert collected_data is not None, "collected_data cannot be None"
        
        violations = []
        
        # Use pre-collected algorithm hashes instead of computing them
        for body_hash, functions in collected_data.algorithm_hashes.items():
            if len(functions) > 1:
                # Report each duplicate
                for file_path, func_node in functions:
                    violations.append(
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
        
        return violations