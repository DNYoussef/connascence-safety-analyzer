"""
Context Analyzer - Extracted from ConnascenceDetector

Handles code context analysis and snippet extraction.
Provides contextual information for better violation reporting.
"""

import ast
from typing import List, Optional, Dict, Any


class ContextAnalyzer:
    """Analyzes code context for enhanced violation reporting."""
    
    def __init__(self, file_path: str, source_lines: List[str]):
        self.file_path = file_path
        self.source_lines = source_lines
    
    def get_code_snippet(self, node: ast.AST, context_lines: int = 2) -> str:
        """Extract code snippet around the given node with context."""
        if not hasattr(node, "lineno"):
            return ""
        
        start_line = max(0, node.lineno - context_lines - 1)
        end_line = min(len(self.source_lines), node.lineno + context_lines)
        
        lines = []
        for i in range(start_line, end_line):
            marker = ">>>" if i == node.lineno - 1 else "   "
            lines.append(f"{marker} {i+1:3d}: {self.source_lines[i].rstrip()}")
        
        return "\n".join(lines)
    
    def get_function_context(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Get contextual information about a function."""
        context = {
            "name": node.name,
            "line_number": node.lineno,
            "parameter_count": len(node.args.args),
            "has_decorators": len(node.decorator_list) > 0,
            "is_method": self._is_method(node),
            "is_private": node.name.startswith("_"),
            "docstring": ast.get_docstring(node),
            "body_length": len(node.body)
        }
        
        # Analyze parameters
        context["parameters"] = self._analyze_parameters(node)
        
        # Analyze return statements
        context["return_statements"] = self._analyze_returns(node)
        
        return context
    
    def get_class_context(self, node: ast.ClassDef) -> Dict[str, Any]:
        """Get contextual information about a class."""
        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
        properties = [n for n in node.body if isinstance(n, ast.Assign)]
        
        context = {
            "name": node.name,
            "line_number": node.lineno,
            "method_count": len(methods),
            "property_count": len(properties),
            "base_classes": [self._get_base_name(base) for base in node.bases],
            "has_decorators": len(node.decorator_list) > 0,
            "docstring": ast.get_docstring(node),
            "methods": [method.name for method in methods],
            "estimated_loc": self._estimate_class_loc(node)
        }
        
        return context
    
    def get_call_context(self, node: ast.Call) -> Dict[str, Any]:
        """Get contextual information about a function call."""
        context = {
            "line_number": node.lineno,
            "function_name": self._get_call_name(node),
            "argument_count": len(node.args),
            "keyword_argument_count": len(node.keywords),
            "has_star_args": any(isinstance(arg, ast.Starred) for arg in node.args),
            "has_kwargs": any(kw.arg is None for kw in node.keywords)
        }
        
        return context
    
    def get_literal_context(self, node: ast.AST, literal_value: Any) -> Dict[str, Any]:
        """Get contextual information about a literal value."""
        context = {
            "value": literal_value,
            "type": type(literal_value).__name__,
            "line_number": node.lineno,
            "in_conditional": self._is_in_conditional(node),
            "in_assignment": self._is_in_assignment(node),
            "in_comparison": self._is_in_comparison(node),
            "surrounding_context": self._get_surrounding_context(node)
        }
        
        return context
    
    def analyze_complexity_context(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Analyze complexity-related context for a function."""
        context = {
            "cyclomatic_complexity": self._calculate_cyclomatic_complexity(node),
            "nesting_depth": self._calculate_nesting_depth(node),
            "branch_count": self._count_branches(node),
            "loop_count": self._count_loops(node),
            "try_except_count": self._count_try_except(node)
        }
        
        return context
    
    def _is_method(self, node: ast.FunctionDef) -> bool:
        """Check if function is a method (has self as first parameter)."""
        if not node.args.args:
            return False
        return node.args.args[0].arg in ["self", "cls"]
    
    def _analyze_parameters(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Analyze function parameters."""
        args = node.args
        return {
            "positional_count": len(args.args),
            "defaults_count": len(args.defaults),
            "keyword_only_count": len(args.kwonlyargs),
            "has_varargs": args.vararg is not None,
            "has_kwargs": args.kwarg is not None,
            "parameter_names": [arg.arg for arg in args.args]
        }
    
    def _analyze_returns(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Analyze return statements in function."""
        returns = []
        for child in ast.walk(node):
            if isinstance(child, ast.Return):
                returns.append({
                    "line": child.lineno,
                    "has_value": child.value is not None,
                    "value_type": type(child.value).__name__ if child.value else None
                })
        
        return {
            "count": len(returns),
            "statements": returns,
            "has_early_returns": len(returns) > 1
        }
    
    def _get_base_name(self, base: ast.expr) -> str:
        """Get name of base class."""
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return base.attr
        else:
            return str(base)
    
    def _estimate_class_loc(self, node: ast.ClassDef) -> int:
        """Estimate lines of code for a class."""
        if hasattr(node, "end_lineno") and node.end_lineno:
            return node.end_lineno - node.lineno
        else:
            return len(node.body) * 5  # Rough estimate
    
    def _get_call_name(self, node: ast.Call) -> str:
        """Get the name of the function being called."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        else:
            return "unknown"
    
    def _is_in_conditional(self, node: ast.AST) -> bool:
        """Check if node is within a conditional statement."""
        if not hasattr(node, "lineno") or node.lineno > len(self.source_lines):
            return False
            
        line_content = self.source_lines[node.lineno - 1]
        return any(keyword in line_content for keyword in ["if ", "elif ", "while ", "assert "])
    
    def _is_in_assignment(self, node: ast.AST) -> bool:
        """Check if node is part of an assignment."""
        if not hasattr(node, "lineno") or node.lineno > len(self.source_lines):
            return False
            
        line_content = self.source_lines[node.lineno - 1]
        return "=" in line_content and not any(op in line_content for op in ["==", "!=", "<=", ">="])
    
    def _is_in_comparison(self, node: ast.AST) -> bool:
        """Check if node is part of a comparison."""
        if not hasattr(node, "lineno") or node.lineno > len(self.source_lines):
            return False
            
        line_content = self.source_lines[node.lineno - 1]
        return any(op in line_content for op in ["==", "!=", "<", ">", "<=", ">="])
    
    def _get_surrounding_context(self, node: ast.AST, lines: int = 1) -> str:
        """Get surrounding code context."""
        if not hasattr(node, "lineno") or node.lineno > len(self.source_lines):
            return ""
        
        start = max(0, node.lineno - lines - 1)
        end = min(len(self.source_lines), node.lineno + lines)
        
        return "\n".join(self.source_lines[start:end])
    
    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _calculate_nesting_depth(self, node: ast.FunctionDef) -> int:
        """Calculate maximum nesting depth."""
        def get_depth(node, current_depth=0):
            max_depth = current_depth
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                    child_depth = get_depth(child, current_depth + 1)
                    max_depth = max(max_depth, child_depth)
                else:
                    child_depth = get_depth(child, current_depth)
                    max_depth = max(max_depth, child_depth)
            return max_depth
        
        return get_depth(node)
    
    def _count_branches(self, node: ast.FunctionDef) -> int:
        """Count conditional branches."""
        count = 0
        for child in ast.walk(node):
            if isinstance(child, ast.If):
                count += 1
                count += len(child.orelse) if child.orelse else 0
        return count
    
    def _count_loops(self, node: ast.FunctionDef) -> int:
        """Count loop statements."""
        count = 0
        for child in ast.walk(node):
            if isinstance(child, (ast.For, ast.While, ast.AsyncFor)):
                count += 1
        return count
    
    def _count_try_except(self, node: ast.FunctionDef) -> int:
        """Count try-except blocks."""
        count = 0
        for child in ast.walk(node):
            if isinstance(child, ast.Try):
                count += 1
        return count