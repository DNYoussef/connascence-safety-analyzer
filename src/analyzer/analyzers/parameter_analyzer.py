"""
Parameter Analyzer - Extracted from ConnascenceASTAnalyzer

Specialized analyzer for detecting Connascence of Position (CoP) violations.
Focuses on parameter-related coupling and complexity.
"""

import ast
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass

from ..helpers.violation_reporter import ConnascenceViolation


@dataclass
class ParameterConfig:
    """Configuration for parameter analysis."""
    max_positional_params: int = 3
    max_call_args: int = 5
    flag_boolean_params: bool = True
    flag_long_param_names: bool = True
    max_param_name_length: int = 30
    

class ParameterAnalyzer:
    """Specialized analyzer for parameter-related connascence."""
    
    def __init__(
        self,
        file_path: str,
        source_lines: List[str],
        config: ParameterConfig = None
    ):
        self.file_path = file_path
        self.source_lines = source_lines
        self.config = config or ParameterConfig()
    
    def analyze(self, tree: ast.AST) -> List[ConnascenceViolation]:
        """Analyze tree for parameter-related violations."""
        violations = []
        
        # Analyze function definitions
        violations.extend(self._analyze_function_definitions(tree))
        
        # Analyze function calls
        violations.extend(self._analyze_function_calls(tree))
        
        return violations
    
    def _analyze_function_definitions(self, tree: ast.AST) -> List[ConnascenceViolation]:
        """Analyze function definitions for parameter issues."""
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                violations.extend(self._analyze_single_function(node))
        
        return violations
    
    def _analyze_single_function(self, node: ast.FunctionDef) -> List[ConnascenceViolation]:
        """Analyze a single function for parameter issues."""
        violations = []
        
        # Analyze parameter count
        param_analysis = self._analyze_parameter_count(node)
        if param_analysis["violation"]:
            violations.append(param_analysis["violation"])
        
        # Analyze parameter types and patterns
        violations.extend(self._analyze_parameter_patterns(node))
        
        return violations
    
    def _analyze_parameter_count(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Analyze parameter count violations."""
        args = node.args.args
        
        # Exclude self/cls for methods
        if args and args[0].arg in ["self", "cls"]:
            args = args[1:]
        
        positional_count = len(args)
        
        if positional_count > self.config.max_positional_params:
            violation = ConnascenceViolation(
                type="connascence_of_position",
                severity=self._determine_position_severity(positional_count),
                file_path=self.file_path,
                line_number=node.lineno,
                column=node.col_offset,
                description=f"Function '{node.name}' has {positional_count} positional parameters (>{self.config.max_positional_params})",
                recommendation=self._generate_position_recommendation(positional_count, node),
                code_snippet=self._get_code_snippet(node),
                context=self._build_function_context(node, positional_count)
            )
            
            return {"violation": violation, "count": positional_count}
        
        return {"violation": None, "count": positional_count}
    
    def _analyze_parameter_patterns(self, node: ast.FunctionDef) -> List[ConnascenceViolation]:
        """Analyze parameter patterns and anti-patterns."""
        violations = []
        
        # Check for boolean parameters (flag arguments)
        if self.config.flag_boolean_params:
            violations.extend(self._detect_boolean_parameters(node))
        
        # Check for long parameter names
        if self.config.flag_long_param_names:
            violations.extend(self._detect_long_parameter_names(node))
        
        # Check parameter ordering issues
        violations.extend(self._detect_parameter_ordering_issues(node))
        
        return violations
    
    def _detect_boolean_parameters(self, node: ast.FunctionDef) -> List[ConnascenceViolation]:
        """Detect functions with boolean flag parameters."""
        violations = []
        
        # Look for boolean type hints or default values
        args_with_defaults = zip(
            node.args.args[-len(node.args.defaults):] if node.args.defaults else [],
            node.args.defaults if node.args.defaults else []
        )
        
        for arg, default in args_with_defaults:
            if isinstance(default, ast.Constant) and isinstance(default.value, bool):
                violations.append(ConnascenceViolation(
                    type="connascence_of_position",
                    severity="medium",
                    file_path=self.file_path,
                    line_number=arg.lineno,
                    column=arg.col_offset,
                    description=f"Boolean parameter '{arg.arg}' in function '{node.name}' creates positional coupling",
                    recommendation="Consider using keyword-only arguments or enum/string constants",
                    code_snippet=self._get_code_snippet(node),
                    context={
                        "function_name": node.name,
                        "parameter_name": arg.arg,
                        "default_value": default.value,
                        "issue_type": "boolean_flag"
                    }
                ))
        
        return violations
    
    def _detect_long_parameter_names(self, node: ast.FunctionDef) -> List[ConnascenceViolation]:
        """Detect parameters with excessively long names."""
        violations = []
        
        for arg in node.args.args:
            if len(arg.arg) > self.config.max_param_name_length:
                violations.append(ConnascenceViolation(
                    type="connascence_of_position",
                    severity="low",
                    file_path=self.file_path,
                    line_number=arg.lineno if hasattr(arg, 'lineno') else node.lineno,
                    column=arg.col_offset if hasattr(arg, 'col_offset') else node.col_offset,
                    description=f"Parameter '{arg.arg}' has excessive name length ({len(arg.arg)} chars)",
                    recommendation="Use shorter, more concise parameter names",
                    code_snippet=self._get_code_snippet(node),
                    context={
                        "function_name": node.name,
                        "parameter_name": arg.arg,
                        "name_length": len(arg.arg),
                        "issue_type": "long_name"
                    }
                ))
        
        return violations
    
    def _detect_parameter_ordering_issues(self, node: ast.FunctionDef) -> List[ConnascenceViolation]:
        """Detect parameter ordering anti-patterns."""
        violations = []
        
        # Check if optional parameters come before required ones
        args = node.args.args
        defaults = node.args.defaults or []
        
        # Parameters with defaults (optional)
        optional_start_index = len(args) - len(defaults)
        
        # Look for required parameters after optional ones
        for i, arg in enumerate(args):
            if i < optional_start_index:  # This is a required parameter
                # Check if it comes after any optional parameters
                if i > 0 and (i - 1) >= optional_start_index:
                    violations.append(ConnascenceViolation(
                        type="connascence_of_position",
                        severity="medium",
                        file_path=self.file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        description=f"Required parameter '{arg.arg}' follows optional parameters in '{node.name}'",
                        recommendation="Place required parameters before optional ones",
                        code_snippet=self._get_code_snippet(node),
                        context={
                            "function_name": node.name,
                            "parameter_name": arg.arg,
                            "issue_type": "parameter_ordering"
                        }
                    ))
        
        return violations
    
    def _analyze_function_calls(self, tree: ast.AST) -> List[ConnascenceViolation]:
        """Analyze function calls for position-related issues."""
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if len(node.args) > self.config.max_call_args:
                    violations.append(ConnascenceViolation(
                        type="connascence_of_position",
                        severity="medium",
                        file_path=self.file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        description=f"Function call with {len(node.args)} positional arguments (>{self.config.max_call_args})",
                        recommendation="Use keyword arguments for better readability and maintainability",
                        code_snippet=self._get_code_snippet(node),
                        context={
                            "argument_count": len(node.args),
                            "function_name": self._get_call_name(node),
                            "issue_type": "excessive_call_args"
                        }
                    ))
        
        return violations
    
    def _determine_position_severity(self, param_count: int) -> str:
        """Determine severity based on parameter count."""
        if param_count > 7:
            return "critical"
        elif param_count > 5:
            return "high"
        else:
            return "medium"
    
    def _generate_position_recommendation(self, param_count: int, node: ast.FunctionDef) -> str:
        """Generate context-specific recommendation for position violations."""
        if param_count > 6:
            return "Consider using a data class, named tuple, or configuration object to group related parameters"
        elif param_count > 4:
            return "Use keyword arguments or consider parameter objects for better maintainability"
        else:
            return "Consider using keyword arguments or grouping related parameters"
    
    def _build_function_context(self, node: ast.FunctionDef, param_count: int) -> Dict[str, Any]:
        """Build context information for function analysis."""
        return {
            "function_name": node.name,
            "parameter_count": param_count,
            "has_defaults": len(node.args.defaults) > 0 if node.args.defaults else False,
            "has_varargs": node.args.vararg is not None,
            "has_kwargs": node.args.kwarg is not None,
            "parameter_names": [arg.arg for arg in node.args.args],
            "is_method": len(node.args.args) > 0 and node.args.args[0].arg in ["self", "cls"]
        }
    
    def _get_call_name(self, node: ast.Call) -> str:
        """Get the name of the function being called."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        else:
            return "unknown"
    
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