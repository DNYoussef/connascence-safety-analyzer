"""
Position Connascence Analyzer - CoP detection
Extracted from ConnascenceASTAnalyzer to reduce God Object violation.
"""

import ast
from typing import List

from ..thresholds import ConnascenceType, Severity
from .base_analyzer import BaseConnascenceAnalyzer
from .violations import Violation


class PositionAnalyzer(BaseConnascenceAnalyzer):
    """Specialized analyzer for Connascence of Position (CoP)."""
    
    def analyze_position_connascence(self, tree: ast.AST) -> List[Violation]:
        """Analyze connascence of position (CoP)."""
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Count positional parameters (excluding self/cls)
                args = node.args.args
                if args and args[0].arg in ["self", "cls"]:
                    args = args[1:]
                
                positional_count = len(args)
                
                if positional_count > self.thresholds.max_positional_params:
                    violations.append(Violation(
                        id="",
                        type=ConnascenceType.POSITION,
                        severity=Severity.HIGH,
                        file_path=self.current_file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        description=f"Function '{node.name}' has {positional_count} positional parameters (>{self.thresholds.max_positional_params})",
                        recommendation="Use keyword arguments, data classes, or parameter objects",
                        code_snippet=self.get_code_snippet(node),
                        function_name=node.name,
                        locality="same_function",
                        context={"parameter_count": positional_count}
                    ))
            
            elif isinstance(node, ast.Call):
                # Check function calls with many positional arguments
                if len(node.args) > self.thresholds.max_positional_params:
                    violations.append(Violation(
                        id="",
                        type=ConnascenceType.POSITION,
                        severity=Severity.MEDIUM,
                        file_path=self.current_file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        description=f"Function call with {len(node.args)} positional arguments",
                        recommendation="Use keyword arguments for better readability",
                        code_snippet=self.get_code_snippet(node),
                        locality="same_module",
                        context={"argument_count": len(node.args)}
                    ))
        
        # NASA Power of Ten Rules 6 & 9: Variable scope and pointer restrictions
        violations.extend(self._check_variable_scope_violations(tree))
        violations.extend(self._check_pointer_like_violations(tree))
        
        return violations
    
    def _check_variable_scope_violations(self, tree: ast.AST) -> List[Violation]:
        """Check for NASA Rule 6: Variable scope violations."""
        violations = []
        
        # Count module-level variables
        module_vars = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                # Check if this is at module level (not inside class/function)
                if not self._is_inside_class_or_function(node, tree):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            module_vars.append(target.id)
        
        # NASA Rule 6: Too many module-level variables
        if len(module_vars) > 10:
            violations.append(Violation(
                id="",
                type=ConnascenceType.POSITION,
                severity=Severity.HIGH,
                file_path=self.current_file_path,
                line_number=1,
                column=0,
                description=f"NASA Rule 6 violation: Too many module-level variables ({len(module_vars)})",
                recommendation="REFACTOR: Move variables to smallest possible scope or encapsulate in classes. NASA Rule 6 requires minimal scope",
                locality="same_module",
                context={
                    "nasa_rule": "Rule_6_Smallest_Scope",
                    "module_var_count": len(module_vars),
                    "safety_critical": True
                }
            ))
        
        return violations
    
    def _check_pointer_like_violations(self, tree: ast.AST) -> List[Violation]:
        """Check for NASA Rule 9: Pointer-like operations."""
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                # Count depth of attribute access (obj.attr.attr.attr)
                depth = self._count_attribute_depth(node)
                if depth > 2:  # More than obj.attr.attr
                    violations.append(Violation(
                        id="",
                        type=ConnascenceType.POSITION,
                        severity=Severity.MEDIUM,
                        file_path=self.current_file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        description=f"NASA Rule 9 violation: Deep attribute access chain (depth: {depth})",
                        recommendation="REFACTOR: Use intermediate variables or flatten structure. NASA Rule 9 restricts indirection depth",
                        locality="same_function",
                        context={
                            "nasa_rule": "Rule_9_Pointer_Restrictions",
                            "access_depth": depth,
                            "safety_critical": True
                        }
                    ))
        
        return violations
    
    def _is_inside_class_or_function(self, target_node: ast.AST, tree: ast.AST) -> bool:
        """Check if a node is inside a class or function."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                for child in ast.walk(node):
                    if child is target_node:
                        return True
        return False
    
    def _count_attribute_depth(self, node: ast.Attribute) -> int:
        """Count the depth of attribute access."""
        depth = 1
        current = node.value
        while isinstance(current, ast.Attribute):
            depth += 1
            current = current.value
        return depth