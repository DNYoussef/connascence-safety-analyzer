"""
Parameter bomb fixer for Connascence of Position (CoP) violations.

Automatically refactors functions with too many positional parameters
into dataclass-based or keyword-only parameter patterns.
"""

import ast
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from .patch_api import PatchSuggestion
from analyzer.core import ConnascenceViolation


@dataclass
class ParameterInfo:
    """Information about a function parameter."""
    name: str
    type_hint: Optional[str]
    default_value: Optional[str]
    position: int


@dataclass
class FunctionSignature:
    """Information about a function signature."""
    name: str
    parameters: List[ParameterInfo]
    return_type: Optional[str]
    docstring: Optional[str]
    is_method: bool
    class_name: Optional[str]


class ParameterBombFixer:
    """Fixes Connascence of Position violations by refactoring parameter lists."""
    
    def __init__(self):
        self.max_positional_params = 3
        self.dataclass_threshold = 5  # Use dataclass if more than this many params
    
    def generate_patch(self, violation: ConnascenceViolation,
                      tree: ast.AST, source_code: str) -> Optional[PatchSuggestion]:
        """Generate patch for a parameter bomb violation."""
        function_info = self._extract_function_info(violation, tree)
        if not function_info:
            return None
        
        strategy = self._choose_refactoring_strategy(function_info)
        confidence = self._calculate_confidence(function_info, strategy)
        
        if confidence < 0.6:
            return None
        
        old_code = self._get_function_code(violation, source_code)
        new_code = self._generate_refactored_code(function_info, strategy, source_code)
        
        return PatchSuggestion(
            violation_id=violation.id,
            confidence=confidence,
            description=f"Refactor {function_info.name} using {strategy} pattern",
            old_code=old_code,
            new_code=new_code,
            file_path=violation.file_path,
            line_range=self._get_function_line_range(violation, tree),
            safety_level=self._assess_safety(function_info, strategy),
            rollback_info={}
        )
    
    def _extract_function_info(self, violation: ConnascenceViolation,
                              tree: ast.AST) -> Optional[FunctionSignature]:
        """Extract function signature information."""
        finder = FunctionFinder(violation.line_number)
        finder.visit(tree)
        
        if not finder.found_function:
            return None
        
        func_node = finder.found_function
        
        # Extract parameters
        parameters = []
        for i, arg in enumerate(func_node.args.args):
            param_info = ParameterInfo(
                name=arg.arg,
                type_hint=self._get_type_annotation(arg),
                default_value=None,  # TODO: Extract defaults
                position=i
            )
            parameters.append(param_info)
        
        # Check if it's a method
        is_method = len(parameters) > 0 and parameters[0].name in ('self', 'cls')
        
        return FunctionSignature(
            name=func_node.name,
            parameters=parameters,
            return_type=self._get_type_annotation(func_node, is_return=True),
            docstring=ast.get_docstring(func_node),
            is_method=is_method,
            class_name=finder.class_context
        )
    
    def _choose_refactoring_strategy(self, func_info: FunctionSignature) -> str:
        """Choose the best refactoring strategy."""
        param_count = len(func_info.parameters)
        
        # Subtract self/cls for methods
        if func_info.is_method:
            param_count -= 1
        
        if param_count >= self.dataclass_threshold:
            return 'dataclass'
        elif param_count >= 4:
            return 'keyword_only'
        else:
            return 'typed_params'
    
    def _calculate_confidence(self, func_info: FunctionSignature, strategy: str) -> float:
        """Calculate confidence score for the refactoring."""
        confidence = 0.7  # Base confidence
        
        param_count = len(func_info.parameters)
        if func_info.is_method:
            param_count -= 1
        
        # Higher confidence for more parameters
        if param_count > 6:
            confidence += 0.2
        elif param_count > 4:
            confidence += 0.1
        
        # Boost confidence if types are already present
        typed_params = sum(1 for p in func_info.parameters if p.type_hint)
        if typed_params > param_count * 0.5:
            confidence += 0.1
        
        # Strategy-specific confidence adjustments
        if strategy == 'dataclass' and param_count >= self.dataclass_threshold:
            confidence += 0.1
        elif strategy == 'keyword_only' and 4 <= param_count < self.dataclass_threshold:
            confidence += 0.1
        
        return min(confidence, 0.9)
    
    def _assess_safety(self, func_info: FunctionSignature, strategy: str) -> str:
        """Assess safety level of the refactoring."""
        # Dataclass refactoring is more invasive
        if strategy == 'dataclass':
            return 'moderate'
        
        # Keyword-only is generally safe
        if strategy == 'keyword_only':
            return 'safe'
        
        # Adding type hints is very safe
        if strategy == 'typed_params':
            return 'safe'
        
        return 'moderate'
    
    def _get_function_code(self, violation: ConnascenceViolation, source: str) -> str:
        """Extract the function code."""
        lines = source.splitlines()
        start_line = violation.line_number - 1
        
        # Find function end (simple heuristic)
        indent_level = len(lines[start_line]) - len(lines[start_line].lstrip())
        end_line = start_line + 1
        
        while end_line < len(lines):
            line = lines[end_line]
            if line.strip() and len(line) - len(line.lstrip()) <= indent_level:
                break
            end_line += 1
        
        return '\n'.join(lines[start_line:end_line])
    
    def _get_function_line_range(self, violation: ConnascenceViolation, 
                                tree: ast.AST) -> Tuple[int, int]:
        """Get the line range of the function."""
        finder = FunctionFinder(violation.line_number)
        finder.visit(tree)
        
        if finder.found_function:
            func = finder.found_function
            start = func.lineno
            end = getattr(func, 'end_lineno', start + 10)  # Fallback
            return (start, end)
        
        return (violation.line_number, violation.line_number + 5)
    
    def _generate_refactored_code(self, func_info: FunctionSignature, 
                                 strategy: str, source_code: str) -> str:
        """Generate refactored function code."""
        if strategy == 'dataclass':
            return self._generate_dataclass_refactor(func_info)
        elif strategy == 'keyword_only':
            return self._generate_keyword_only_refactor(func_info)
        elif strategy == 'typed_params':
            return self._generate_typed_params_refactor(func_info)
        else:
            return source_code
    
    def _generate_dataclass_refactor(self, func_info: FunctionSignature) -> str:
        """Generate dataclass-based refactor."""
        # Generate dataclass
        class_name = f"{func_info.name.title()}Request"
        
        dataclass_code = f"@dataclass\nclass {class_name}:\n"
        
        # Add fields (skip self/cls)
        start_idx = 1 if func_info.is_method else 0
        for param in func_info.parameters[start_idx:]:
            type_hint = param.type_hint or "Any"
            default = " = None" if param.default_value else ""
            dataclass_code += f"    {param.name}: {type_hint}{default}\n"
        
        # Generate refactored function
        self_param = func_info.parameters[0].name if func_info.is_method else ""
        params = f"{self_param}, request: {class_name}" if func_info.is_method else f"request: {class_name}"
        
        return_hint = f" -> {func_info.return_type}" if func_info.return_type else ""
        
        func_code = f"\n\ndef {func_info.name}({params}){return_hint}:\n"
        if func_info.docstring:
            func_code += f'    """{func_info.docstring}"""\n'
        func_code += "    # TODO: Update function body to use request.field_name\n"
        func_code += "    pass\n"
        
        return dataclass_code + func_code
    
    def _generate_keyword_only_refactor(self, func_info: FunctionSignature) -> str:
        """Generate keyword-only parameter refactor."""
        # Keep first few params as positional, rest as keyword-only
        positional_limit = 2 if func_info.is_method else 1
        
        params = []
        for i, param in enumerate(func_info.parameters):
            type_hint = f": {param.type_hint}" if param.type_hint else ""
            default = f" = {param.default_value}" if param.default_value else ""
            
            if i < positional_limit:
                params.append(f"{param.name}{type_hint}{default}")
            elif i == positional_limit and i < len(func_info.parameters) - 1:
                params.append("*")  # Add keyword-only marker
                params.append(f"{param.name}{type_hint}{default}")
            else:
                params.append(f"{param.name}{type_hint}{default}")
        
        param_str = ", ".join(params)
        return_hint = f" -> {func_info.return_type}" if func_info.return_type else ""
        
        func_code = f"def {func_info.name}({param_str}){return_hint}:\n"
        if func_info.docstring:
            func_code += f'    """{func_info.docstring}"""\n'
        func_code += "    # Function body unchanged\n"
        func_code += "    pass\n"
        
        return func_code
    
    def _generate_typed_params_refactor(self, func_info: FunctionSignature) -> str:
        """Generate refactor with added type hints."""
        params = []
        for param in func_info.parameters:
            type_hint = param.type_hint or "Any"
            default = f" = {param.default_value}" if param.default_value else ""
            params.append(f"{param.name}: {type_hint}{default}")
        
        param_str = ", ".join(params)
        return_hint = f" -> {func_info.return_type}" if func_info.return_type else " -> Any"
        
        func_code = f"def {func_info.name}({param_str}){return_hint}:\n"
        if func_info.docstring:
            func_code += f'    """{func_info.docstring}"""\n'
        func_code += "    # Function body unchanged\n"
        func_code += "    pass\n"
        
        return func_code
    
    def _get_type_annotation(self, node, is_return: bool = False) -> Optional[str]:
        """Extract type annotation from AST node."""
        if is_return:
            if hasattr(node, 'returns') and node.returns:
                return ast.unparse(node.returns) if hasattr(ast, 'unparse') else 'Any'
            return None
        
        if hasattr(node, 'annotation') and node.annotation:
            return ast.unparse(node.annotation) if hasattr(ast, 'unparse') else 'Any'
        return None


class FunctionFinder(ast.NodeVisitor):
    """AST visitor to find functions on specific lines."""
    
    def __init__(self, target_line: int):
        self.target_line = target_line
        self.found_function = None
        self.class_context = None
        self._class_stack = []
    
    def visit_ClassDef(self, node):
        self._class_stack.append(node.name)
        self.generic_visit(node)
        self._class_stack.pop()
    
    def visit_FunctionDef(self, node):
        if hasattr(node, 'lineno') and node.lineno <= self.target_line:
            # Check if target line is within function
            end_line = getattr(node, 'end_lineno', node.lineno + 10)
            if self.target_line <= end_line:
                self.found_function = node
                self.class_context = self._class_stack[-1] if self._class_stack else None
        self.generic_visit(node)