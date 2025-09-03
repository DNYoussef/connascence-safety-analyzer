"""
AST Analysis Helper - Extracted from ConnascenceDetector

Provides utility functions for AST traversal and analysis.
Implements helper functions for code analysis and pattern matching.
"""

import ast
import collections
from typing import Dict, List, Any, Tuple


class ASTAnalysisHelper:
    """Helper class for AST analysis operations."""
    
    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        
    def normalize_function_body(self, node: ast.FunctionDef) -> str:
        """Create normalized hash of function body for duplicate detection."""
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
    
    def is_in_conditional(self, node: ast.AST) -> bool:
        """Check if node is within a conditional statement."""
        if not hasattr(node, "lineno") or node.lineno > len(self.source_lines):
            return False
            
        line_content = self.source_lines[node.lineno - 1]
        return any(keyword in line_content for keyword in ["if ", "elif ", "while ", "assert "])
    
    def collect_function_definitions(self, tree: ast.AST) -> Dict[str, ast.FunctionDef]:
        """Collect all function definitions from AST."""
        functions = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions[node.name] = node
        return functions
    
    def collect_class_definitions(self, tree: ast.AST) -> Dict[str, ast.ClassDef]:
        """Collect all class definitions from AST."""
        classes = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes[node.name] = node
        return classes
    
    def collect_imports(self, tree: ast.AST) -> set[str]:
        """Collect all import statements."""
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        imports.add(f"{node.module}.{alias.name}")
        return imports
    
    def collect_global_vars(self, tree: ast.AST) -> set[str]:
        """Collect all global variable declarations."""
        global_vars = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Global):
                for name in node.names:
                    global_vars.add(name)
        return global_vars
    
    def collect_magic_literals(self, tree: ast.AST) -> List[Tuple[ast.AST, Any]]:
        """Collect magic literals from AST."""
        magic_literals = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Num):
                # Skip common "safe" numbers
                if hasattr(node, "n") and node.n not in [0, 1, -1, 2, 10, 100, 1000]:
                    magic_literals.append((node, node.n))
            elif isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)):
                    if node.value not in [0, 1, -1, 2, 10, 100, 1000]:
                        magic_literals.append((node, node.value))
                elif isinstance(node.value, str):
                    # Skip very short strings and common patterns
                    import re
                    if len(node.value) > 3 and not re.match(r"^[a-zA-Z0-9_-]+$", node.value):
                        magic_literals.append((node, node.value))
        
        return magic_literals
    
    def collect_sleep_calls(self, tree: ast.AST) -> List[ast.Call]:
        """Collect all sleep() function calls."""
        sleep_calls = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for sleep() calls
                if (isinstance(node.func, ast.Name) and node.func.id == "sleep") or (
                    isinstance(node.func, ast.Attribute) and node.func.attr == "sleep"
                ):
                    sleep_calls.append(node)
        
        return sleep_calls
    
    def collect_positional_parameters(self, tree: ast.AST) -> List[Tuple[ast.FunctionDef, int]]:
        """Collect functions with excessive positional parameters."""
        positional_params = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                positional_count = sum(1 for arg in node.args.args if not arg.arg.startswith("_"))
                if positional_count > 3:
                    positional_params.append((node, positional_count))
        
        return positional_params
    
    def build_function_hashes(self, tree: ast.AST) -> Dict[str, List[Tuple[str, ast.FunctionDef]]]:
        """Build function signature hashes for duplicate detection."""
        function_hashes = collections.defaultdict(list)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                body_hash = self.normalize_function_body(node)
                if len(node.body) > 3:  # Only check substantial functions
                    function_hashes[body_hash].append(("current_file", node))
        
        return function_hashes
    
    def count_class_complexity(self, node: ast.ClassDef) -> Tuple[int, int]:
        """Count method count and estimate lines of code for a class."""
        method_count = sum(1 for n in node.body if isinstance(n, ast.FunctionDef))
        
        # Estimate lines of code
        if hasattr(node, "end_lineno") and node.end_lineno:
            loc = node.end_lineno - node.lineno
        else:
            loc = len(node.body) * 5  # Rough estimate
            
        return method_count, loc
    
    def find_first_global_node(self, tree: ast.AST) -> ast.Global:
        """Find the first global declaration node."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Global):
                return node
        return None