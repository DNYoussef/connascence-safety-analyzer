"""
Complexity Analyzer - Extracted from ConnascenceASTAnalyzer

Specialized analyzer for detecting Connascence of Algorithm (CoA) violations.
Focuses on complexity metrics, code duplication, and architectural issues.
"""

import ast
import hashlib
from typing import List, Dict, Any, Set, Tuple
from dataclasses import dataclass

from ..helpers.violation_reporter import ConnascenceViolation


@dataclass
class ComplexityConfig:
    """Configuration for complexity analysis."""
    max_cyclomatic_complexity: int = 10
    max_nesting_depth: int = 4
    god_class_methods: int = 20
    god_class_lines: int = 500
    duplicate_threshold: int = 3  # Minimum lines for duplicate detection
    

class ComplexityAnalyzer:
    """Specialized analyzer for complexity and algorithm violations."""
    
    def __init__(
        self,
        file_path: str,
        source_lines: List[str],
        config: ComplexityConfig = None
    ):
        self.file_path = file_path
        self.source_lines = source_lines
        self.config = config or ComplexityConfig()
    
    def analyze(self, tree: ast.AST) -> List[ConnascenceViolation]:
        """Analyze tree for complexity-related violations."""
        violations = []
        
        # Analyze function complexity
        violations.extend(self._analyze_function_complexity(tree))
        
        # Analyze class complexity (God Objects)
        violations.extend(self._analyze_class_complexity(tree))
        
        # Analyze code duplication
        violations.extend(self._analyze_code_duplication(tree))
        
        return violations
    
    def _analyze_function_complexity(self, tree: ast.AST) -> List[ConnascenceViolation]:
        """Analyze functions for complexity violations."""
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Cyclomatic complexity
                complexity = self._calculate_cyclomatic_complexity(node)
                if complexity > self.config.max_cyclomatic_complexity:
                    violations.append(self._create_complexity_violation(node, complexity))
                
                # Nesting depth
                nesting = self._calculate_nesting_depth(node)
                if nesting > self.config.max_nesting_depth:
                    violations.append(self._create_nesting_violation(node, nesting))
        
        return violations
    
    def _analyze_class_complexity(self, tree: ast.AST) -> List[ConnascenceViolation]:
        """Analyze classes for God Object violations."""
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                method_count, loc = self._analyze_class_metrics(node)
                
                if method_count > self.config.god_class_methods or loc > self.config.god_class_lines:
                    violations.append(self._create_god_class_violation(node, method_count, loc))
        
        return violations
    
    def _analyze_code_duplication(self, tree: ast.AST) -> List[ConnascenceViolation]:
        """Analyze for code duplication violations."""
        violations = []
        function_signatures = self._build_function_signatures(tree)
        
        # Find duplicates
        for signature, functions in function_signatures.items():
            if len(functions) > 1:
                for func_node in functions:
                    similar_functions = [f.name for f in functions if f != func_node]
                    violations.append(self._create_duplication_violation(func_node, similar_functions))
        
        return violations
    
    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity for a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            # Decision points
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # Each additional condition in boolean operations
                complexity += len(child.values) - 1
            elif isinstance(child, ast.ListComp):
                # List comprehensions with conditions
                complexity += len(child.ifs)
            elif isinstance(child, ast.DictComp):
                # Dict comprehensions with conditions  
                complexity += len(child.ifs)
            elif isinstance(child, ast.SetComp):
                # Set comprehensions with conditions
                complexity += len(child.ifs)
            elif isinstance(child, ast.GeneratorExp):
                # Generator expressions with conditions
                complexity += len(child.ifs)
        
        return complexity
    
    def _calculate_nesting_depth(self, node: ast.FunctionDef) -> int:
        """Calculate maximum nesting depth."""
        def get_depth(node, current_depth=0):
            max_depth = current_depth
            
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.AsyncFor, ast.AsyncWith)):
                    child_depth = get_depth(child, current_depth + 1)
                    max_depth = max(max_depth, child_depth)
                else:
                    child_depth = get_depth(child, current_depth)
                    max_depth = max(max_depth, child_depth)
            
            return max_depth
        
        return get_depth(node)
    
    def _analyze_class_metrics(self, node: ast.ClassDef) -> Tuple[int, int]:
        """Analyze class metrics: method count and lines of code."""
        method_count = len([n for n in node.body if isinstance(n, ast.FunctionDef)])
        
        # Calculate lines of code
        if hasattr(node, "end_lineno") and node.end_lineno:
            loc = node.end_lineno - node.lineno
        else:
            # Estimate based on body length
            loc = sum(self._estimate_node_lines(n) for n in node.body)
        
        return method_count, loc
    
    def _estimate_node_lines(self, node: ast.AST) -> int:
        """Estimate lines of code for an AST node."""
        if hasattr(node, "end_lineno") and hasattr(node, "lineno"):
            return (node.end_lineno or node.lineno) - node.lineno + 1
        else:
            # Rough estimates for different node types
            if isinstance(node, ast.FunctionDef):
                return 5 + len(node.body)  # Function header + body estimate
            elif isinstance(node, ast.ClassDef):
                return 2 + len(node.body)  # Class header + body estimate  
            else:
                return 1  # Single line estimate
    
    def _build_function_signatures(self, tree: ast.AST) -> Dict[str, List[ast.FunctionDef]]:
        """Build function signatures for duplicate detection."""
        signatures = {}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Only analyze substantial functions
                if len(node.body) >= self.config.duplicate_threshold:
                    signature = self._calculate_function_signature(node)
                    if signature not in signatures:
                        signatures[signature] = []
                    signatures[signature].append(node)
        
        return signatures
    
    def _calculate_function_signature(self, node: ast.FunctionDef) -> str:
        """Calculate a signature for function similarity detection."""
        elements = []
        
        # Include function structure
        elements.append(f"params:{len(node.args.args)}")
        
        # Analyze body structure
        for stmt in node.body:
            elements.append(self._normalize_statement(stmt))
        
        signature = "|".join(elements)
        
        # Create hash for consistent comparison
        return hashlib.md5(signature.encode()).hexdigest()[:12]
    
    def _normalize_statement(self, stmt: ast.AST) -> str:
        """Normalize a statement for similarity comparison."""
        if isinstance(stmt, ast.Return):
            return "return" + ("_value" if stmt.value else "")
        elif isinstance(stmt, ast.If):
            return f"if_{len(stmt.orelse) > 0}"
        elif isinstance(stmt, ast.For):
            return "for"
        elif isinstance(stmt, ast.While):
            return "while"
        elif isinstance(stmt, ast.Assign):
            return f"assign_{len(stmt.targets)}"
        elif isinstance(stmt, ast.AugAssign):
            return "augassign"
        elif isinstance(stmt, ast.Expr):
            if isinstance(stmt.value, ast.Call):
                return "call"
            return "expr"
        elif isinstance(stmt, ast.Try):
            return f"try_{len(stmt.handlers)}"
        elif isinstance(stmt, ast.Raise):
            return "raise"
        elif isinstance(stmt, ast.With):
            return f"with_{len(stmt.items)}"
        else:
            return type(stmt).__name__.lower()
    
    def _create_complexity_violation(self, node: ast.FunctionDef, complexity: int) -> ConnascenceViolation:
        """Create a cyclomatic complexity violation."""
        severity = self._determine_complexity_severity(complexity)
        
        return ConnascenceViolation(
            type="connascence_of_algorithm",
            severity=severity,
            file_path=self.file_path,
            line_number=node.lineno,
            column=node.col_offset,
            description=f"Function '{node.name}' has high cyclomatic complexity ({complexity})",
            recommendation=self._generate_complexity_recommendation(complexity),
            code_snippet=self._get_code_snippet(node),
            context={
                "function_name": node.name,
                "complexity": complexity,
                "threshold": self.config.max_cyclomatic_complexity,
                "issue_type": "cyclomatic_complexity"
            }
        )
    
    def _create_nesting_violation(self, node: ast.FunctionDef, nesting: int) -> ConnascenceViolation:
        """Create a nesting depth violation."""
        return ConnascenceViolation(
            type="connascence_of_algorithm",
            severity="high",
            file_path=self.file_path,
            line_number=node.lineno,
            column=node.col_offset,
            description=f"Function '{node.name}' has excessive nesting depth ({nesting})",
            recommendation="Break down nested logic into smaller functions or use early returns",
            code_snippet=self._get_code_snippet(node),
            context={
                "function_name": node.name,
                "nesting_depth": nesting,
                "threshold": self.config.max_nesting_depth,
                "issue_type": "nesting_depth"
            }
        )
    
    def _create_god_class_violation(self, node: ast.ClassDef, method_count: int, loc: int) -> ConnascenceViolation:
        """Create a God Object violation."""
        return ConnascenceViolation(
            type="connascence_of_algorithm",
            severity="critical",
            file_path=self.file_path,
            line_number=node.lineno,
            column=node.col_offset,
            description=f"God Object: class '{node.name}' has {method_count} methods and ~{loc} lines",
            recommendation="Split into smaller, focused classes following Single Responsibility Principle",
            code_snippet=self._get_code_snippet(node),
            context={
                "class_name": node.name,
                "method_count": method_count,
                "lines_of_code": loc,
                "method_threshold": self.config.god_class_methods,
                "loc_threshold": self.config.god_class_lines,
                "issue_type": "god_class"
            }
        )
    
    def _create_duplication_violation(self, node: ast.FunctionDef, similar_functions: List[str]) -> ConnascenceViolation:
        """Create a code duplication violation."""
        return ConnascenceViolation(
            type="connascence_of_algorithm",
            severity="medium",
            file_path=self.file_path,
            line_number=node.lineno,
            column=node.col_offset,
            description=f"Function '{node.name}' appears to duplicate algorithm from other functions",
            recommendation="Extract common algorithm into shared function or module",
            code_snippet=self._get_code_snippet(node),
            context={
                "function_name": node.name,
                "similar_functions": similar_functions,
                "duplicate_count": len(similar_functions) + 1,
                "issue_type": "code_duplication"
            }
        )
    
    def _determine_complexity_severity(self, complexity: int) -> str:
        """Determine severity based on complexity level."""
        if complexity > 20:
            return "critical"
        elif complexity > 15:
            return "high"
        else:
            return "medium"
    
    def _generate_complexity_recommendation(self, complexity: int) -> str:
        """Generate context-specific recommendation for complexity."""
        if complexity > 20:
            return "This function is extremely complex. Consider major refactoring into multiple smaller functions"
        elif complexity > 15:
            return "Break down function into smaller, focused functions with clear responsibilities"
        else:
            return "Simplify conditional logic and reduce branching complexity"
    
    def _get_code_snippet(self, node: ast.AST, context_lines: int = 2) -> str:
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