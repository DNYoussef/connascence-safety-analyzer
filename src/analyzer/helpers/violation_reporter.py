"""
Violation Reporter - Extracted from ConnascenceDetector

Handles creation, formatting and reporting of connascence violations.
Implements Single Responsibility Principle for violation management.
"""

import ast
from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class ConnascenceViolation:
    """Represents a detected connascence violation."""
    
    type: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    file_path: str
    line_number: int
    column: int
    description: str
    recommendation: str
    code_snippet: str
    context: dict[str, Any]


class ViolationReporter:
    """Handles creation and management of connascence violations."""
    
    def __init__(self, file_path: str, source_lines: List[str]):
        self.file_path = file_path
        self.source_lines = source_lines
    
    def create_violation(
        self,
        violation_type: str,
        severity: str,
        node: ast.AST,
        description: str,
        recommendation: str,
        context: Optional[dict[str, Any]] = None
    ) -> ConnascenceViolation:
        """Create a standardized connascence violation."""
        return ConnascenceViolation(
            type=violation_type,
            severity=severity,
            file_path=self.file_path,
            line_number=node.lineno,
            column=node.col_offset,
            description=description,
            recommendation=recommendation,
            code_snippet=self._get_code_snippet(node),
            context=context or {}
        )
    
    def create_position_violation(
        self,
        node: ast.FunctionDef,
        parameter_count: int
    ) -> ConnascenceViolation:
        """Create a connascence of position violation."""
        return self.create_violation(
            violation_type="connascence_of_position",
            severity="high",
            node=node,
            description=f"Function '{node.name}' has {parameter_count} positional parameters (>3)",
            recommendation="Consider using keyword arguments, data classes, or parameter objects",
            context={
                "parameter_count": parameter_count,
                "function_name": node.name
            }
        )
    
    def create_algorithm_violation(
        self,
        node: ast.FunctionDef,
        similar_functions: List[str]
    ) -> ConnascenceViolation:
        """Create a connascence of algorithm violation."""
        return self.create_violation(
            violation_type="connascence_of_algorithm",
            severity="medium",
            node=node,
            description=f"Function '{node.name}' appears to duplicate algorithm from other functions",
            recommendation="Extract common algorithm into shared function or module",
            context={
                "duplicate_count": len(similar_functions) + 1,
                "function_name": node.name,
                "similar_functions": similar_functions
            }
        )
    
    def create_timing_violation(
        self,
        node: ast.Call
    ) -> ConnascenceViolation:
        """Create a connascence of timing violation."""
        return self.create_violation(
            violation_type="connascence_of_timing",
            severity="medium",
            node=node,
            description="Sleep-based timing dependency detected",
            recommendation="Use proper synchronization primitives, events, or async patterns",
            context={"call_type": "sleep"}
        )
    
    def create_meaning_violation(
        self,
        node: ast.AST,
        literal_value: Any,
        in_conditional: bool
    ) -> ConnascenceViolation:
        """Create a connascence of meaning violation."""
        severity = "high" if in_conditional else "medium"
        
        return self.create_violation(
            violation_type="connascence_of_meaning",
            severity=severity,
            node=node,
            description=f"Magic literal '{literal_value}' should be a named constant",
            recommendation="Replace with a well-named constant or configuration value",
            context={
                "literal_value": literal_value,
                "in_conditional": in_conditional
            }
        )
    
    def create_god_object_violation(
        self,
        node: ast.ClassDef,
        method_count: int,
        estimated_loc: int
    ) -> ConnascenceViolation:
        """Create a god object violation."""
        return self.create_violation(
            violation_type="god_object",
            severity="critical",
            node=node,
            description=f"Class '{node.name}' is a God Object: {method_count} methods, ~{estimated_loc} lines",
            recommendation="Split into smaller, focused classes following Single Responsibility Principle",
            context={
                "method_count": method_count,
                "estimated_loc": estimated_loc,
                "class_name": node.name
            }
        )
    
    def create_identity_violation(
        self,
        node: ast.Global,
        global_count: int,
        global_vars: List[str]
    ) -> ConnascenceViolation:
        """Create a connascence of identity violation."""
        return self.create_violation(
            violation_type="connascence_of_identity",
            severity="high",
            node=node,
            description=f"Excessive global variable usage: {global_count} globals",
            recommendation="Use dependency injection, configuration objects, or class attributes",
            context={
                "global_count": global_count,
                "global_vars": global_vars
            }
        )
    
    def create_syntax_error_violation(
        self,
        error: Exception,
        line_number: int = 1,
        column: int = 0
    ) -> ConnascenceViolation:
        """Create a violation for syntax errors."""
        return ConnascenceViolation(
            type="syntax_error",
            severity="critical",
            file_path=self.file_path,
            line_number=line_number,
            column=column,
            description=f"File cannot be parsed: {error}",
            recommendation="Fix syntax errors before analyzing connascence",
            code_snippet="",
            context={"error": str(error)}
        )
    
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