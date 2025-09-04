"""
God Object Analyzer - Large class detection
Extracted from ConnascenceASTAnalyzer to reduce God Object violation.
"""

import ast
from typing import List

from ..thresholds import ConnascenceType, Severity
from .base_analyzer import BaseConnascenceAnalyzer
from .violations import Violation


class GodObjectAnalyzer(BaseConnascenceAnalyzer):
    """Specialized analyzer for God Object antipattern detection."""
    
    def analyze_god_objects(self, tree: ast.AST) -> List[Violation]:
        """Detect God Objects - classes that violate Single Responsibility Principle."""
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                method_count = len([n for n in node.body if isinstance(n, ast.FunctionDef)])
                loc = (node.end_lineno or node.lineno + 10) - node.lineno
                
                if method_count > self.thresholds.god_class_methods or loc > self.thresholds.god_class_lines:
                    violations.append(Violation(
                        id="",
                        type=ConnascenceType.ALGORITHM,
                        severity=Severity.CRITICAL,
                        file_path=self.current_file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        description=f"God Object: class '{node.name}' has {method_count} methods and ~{loc} lines",
                        recommendation="Split into smaller, focused classes following Single Responsibility Principle",
                        class_name=node.name,
                        locality="same_class",
                        context={"method_count": method_count, "lines_of_code": loc}
                    ))
        
        return violations
    
    def analyze_large_functions(self, tree: ast.AST) -> List[Violation]:
        """Detect large functions that may indicate procedural god objects."""
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Calculate function length
                func_length = (node.end_lineno or node.lineno + 10) - node.lineno
                
                # Count statements in function
                statement_count = len([n for n in ast.walk(node) if isinstance(n, ast.stmt)])
                
                # Check for excessive function size
                if func_length > self.thresholds.max_function_length:
                    violations.append(Violation(
                        id="",
                        type=ConnascenceType.ALGORITHM,
                        severity=Severity.HIGH,
                        file_path=self.current_file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        description=f"Large function: '{node.name}' has {func_length} lines ({statement_count} statements)",
                        recommendation="Break down function into smaller, focused functions",
                        function_name=node.name,
                        locality="same_function",
                        context={
                            "function_length": func_length,
                            "statement_count": statement_count
                        }
                    ))
        
        return violations
    
    def analyze_module_size(self, tree: ast.AST, file_lines: int) -> List[Violation]:
        """Detect overly large modules that may indicate god modules."""
        violations = []
        
        # Count classes and functions at module level
        module_classes = len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
        module_functions = len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])
        
        # Check for god modules
        if (file_lines > self.thresholds.max_module_length or 
            module_classes > self.thresholds.max_classes_per_module or
            module_functions > self.thresholds.max_functions_per_module):
            
            violations.append(Violation(
                id="",
                type=ConnascenceType.ALGORITHM,
                severity=Severity.MEDIUM,
                file_path=self.current_file_path,
                line_number=1,
                column=0,
                description=f"Large module: {file_lines} lines, {module_classes} classes, {module_functions} functions",
                recommendation="Split module into smaller, focused modules",
                locality="same_module",
                context={
                    "module_lines": file_lines,
                    "class_count": module_classes,
                    "function_count": module_functions
                }
            ))
        
        return violations