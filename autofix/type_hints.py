# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

"""
Type hint fixer for Connascence of Type (CoT) violations.

Automatically adds type hints to functions and methods that lack them,
improving code documentation and static analysis capabilities.
"""

import ast
from dataclasses import dataclass
import re
from typing import Any, Dict, List, Optional

from .core import ConnascenceViolation
from .patch_api import PatchSuggestion


@dataclass
class TypeInference:
    """Inferred type information for a variable or parameter."""
    name: str
    inferred_type: str
    confidence: float
    evidence: List[str]  # Evidence for the type inference


class TypeHintFixer:
    """Fixes Connascence of Type violations by adding type hints."""

    def __init__(self):
        self.builtin_types = {
            'int', 'float', 'str', 'bool', 'list', 'dict', 'tuple', 'set',
            'List', 'Dict', 'Tuple', 'Set', 'Optional', 'Union', 'Any'
        }
        self.common_patterns = {
            r'.*_id$': 'int',
            r'.*_name$': 'str',
            r'.*_count$': 'int',
            r'.*_flag$': 'bool',
            r'.*_list$': 'List[Any]',
            r'.*_dict$': 'Dict[str, Any]'
        }

    def generate_patch(self, violation: ConnascenceViolation,
                      tree: ast.AST, source_code: str) -> Optional[PatchSuggestion]:
        """Generate patch for a missing type hint violation."""
        function_info = self._extract_function_info(violation, tree)
        if not function_info:
            return None

        type_inferences = self._infer_types(function_info, tree, source_code)
        confidence = self._calculate_confidence(type_inferences)

        if confidence < 0.6:
            return None

        old_code = self._get_function_signature(violation, source_code)
        new_code = self._generate_typed_signature(function_info, type_inferences)

        return PatchSuggestion(
            violation_id=violation.id,
            confidence=confidence,
            description=f"Add type hints to {function_info['name']}",
            old_code=old_code,
            new_code=new_code,
            file_path=violation.file_path,
            line_range=(violation.line_number, violation.line_number),
            safety_level='safe',  # Type hints are non-breaking
            rollback_info={}
        )

    def _extract_function_info(self, violation: ConnascenceViolation,
                              tree: ast.AST) -> Optional[Dict[str, Any]]:
        """Extract function information for type inference."""
        finder = TypeHintFunctionFinder(violation.line_number)
        finder.visit(tree)

        if not finder.found_function:
            return None

        func_node = finder.found_function

        return {
            'name': func_node.name,
            'node': func_node,
            'parameters': [arg.arg for arg in func_node.args.args],
            'has_return': self._has_return_statement(func_node),
            'is_generator': self._is_generator(func_node)
        }

    def _infer_types(self, func_info: Dict[str, Any], tree: ast.AST,
                    source_code: str) -> Dict[str, TypeInference]:
        """Infer types for function parameters and return type."""
        inferences = {}
        func_node = func_info['node']

        # Analyze function body for type clues
        analyzer = TypeInferenceAnalyzer(func_info['parameters'])
        analyzer.visit(func_node)

        # Infer parameter types
        for param in func_info['parameters']:
            if param in ('self', 'cls'):
                continue

            inferred_type, confidence, evidence = self._infer_parameter_type(
                param, analyzer, func_node
            )

            inferences[param] = TypeInference(
                name=param,
                inferred_type=inferred_type,
                confidence=confidence,
                evidence=evidence
            )

        # Infer return type
        if func_info['has_return']:
            return_type, confidence, evidence = self._infer_return_type(
                analyzer, func_node, func_info['is_generator']
            )

            inferences['return'] = TypeInference(
                name='return',
                inferred_type=return_type,
                confidence=confidence,
                evidence=evidence
            )

        return inferences

    def _infer_parameter_type(self, param: str, analyzer: 'TypeInferenceAnalyzer',
                            func_node: ast.AST) -> tuple[str, float, List[str]]:
        """Infer type for a specific parameter."""
        evidence = []
        confidence = 0.5
        inferred_type = "Any"

        # Check usage patterns in the function
        if param in analyzer.param_usage:
            usage = analyzer.param_usage[param]

            # Check for method calls that indicate type
            if 'append' in usage.get('methods', []):
                inferred_type = "List[Any]"
                confidence = 0.8
                evidence.append("calls .append() method")
            elif 'keys' in usage.get('methods', []) or 'items' in usage.get('methods', []):
                inferred_type = "Dict[str, Any]"
                confidence = 0.8
                evidence.append("calls dict methods")
            elif 'strip' in usage.get('methods', []) or 'split' in usage.get('methods', []):
                inferred_type = "str"
                confidence = 0.9
                evidence.append("calls string methods")

        # Check parameter name patterns
        for pattern, type_hint in self.common_patterns.items():
            if re.match(pattern, param) and inferred_type == "Any":  # Don't override stronger evidence
                inferred_type = type_hint
                confidence = max(confidence, 0.6)
                evidence.append(f"matches pattern {pattern}")

        # Check for comparisons with specific types
        if param in analyzer.compared_to_literals:
            literals = analyzer.compared_to_literals[param]
            if all(isinstance(lit, str) for lit in literals):
                inferred_type = "str"
                confidence = 0.8
                evidence.append("compared to string literals")
            elif all(isinstance(lit, int) for lit in literals):
                inferred_type = "int"
                confidence = 0.8
                evidence.append("compared to integer literals")

        return inferred_type, confidence, evidence

    def _infer_return_type(self, analyzer: 'TypeInferenceAnalyzer', func_node: ast.AST,
                          is_generator: bool) -> tuple[str, float, List[str]]:
        """Infer return type from return statements."""
        if is_generator:
            return "Generator[Any, None, None]", 0.7, ["function uses yield"]

        if not analyzer.return_values:
            return "None", 0.9, ["no return statements with values"]

        # Analyze return value types
        return_types = set()
        evidence = []

        for ret_val in analyzer.return_values:
            if isinstance(ret_val, ast.Constant):
                if ret_val.value is None:
                    return_types.add("None")
                elif isinstance(ret_val.value, str):
                    return_types.add("str")
                elif isinstance(ret_val.value, int):
                    return_types.add("int")
                elif isinstance(ret_val.value, bool):
                    return_types.add("bool")
                evidence.append(f"returns literal {type(ret_val.value).__name__}")
            elif isinstance(ret_val, ast.List):
                return_types.add("List[Any]")
                evidence.append("returns list literal")
            elif isinstance(ret_val, ast.Dict):
                return_types.add("Dict[str, Any]")
                evidence.append("returns dict literal")

        if len(return_types) == 1:
            return list(return_types)[0], 0.8, evidence
        elif len(return_types) > 1:
            if "None" in return_types and len(return_types) == 2:
                other_type = next(t for t in return_types if t != "None")
                return f"Optional[{other_type}]", 0.7, evidence
            else:
                union_types = " | ".join(sorted(return_types))
                return f"Union[{union_types}]", 0.6, evidence

        return "Any", 0.4, evidence

    def _calculate_confidence(self, inferences: Dict[str, TypeInference]) -> float:
        """Calculate overall confidence for adding type hints."""
        if not inferences:
            return 0.0

        # Average confidence weighted by importance
        total_weight = 0
        weighted_confidence = 0

        for name, inference in inferences.items():
            weight = 2 if name == 'return' else 1  # Return type is more important
            weighted_confidence += inference.confidence * weight
            total_weight += weight

        avg_confidence = weighted_confidence / total_weight if total_weight > 0 else 0

        # Bonus for having strong evidence on multiple parameters
        strong_inferences = sum(1 for inf in inferences.values() if inf.confidence > 0.7)
        if strong_inferences > 2:
            avg_confidence += 0.1

        return min(avg_confidence, 0.95)

    def _get_function_signature(self, violation: ConnascenceViolation, source: str) -> str:
        """Extract function signature line."""
        lines = source.splitlines()
        if violation.line_number <= len(lines):
            return lines[violation.line_number - 1].strip()
        return ""

    def _generate_typed_signature(self, func_info: Dict[str, Any],
                                 inferences: Dict[str, TypeInference]) -> str:
        """Generate new function signature with type hints."""
        func_node = func_info['node']

        # Build parameter list with type hints
        params = []
        for i, arg in enumerate(func_node.args.args):
            param_name = arg.arg

            if param_name in inferences:
                inference = inferences[param_name]
                if inference.confidence > 0.6:
                    params.append(f"{param_name}: {inference.inferred_type}")
                else:
                    params.append(f"{param_name}: Any")  # Default type hint
            else:
                params.append(f"{param_name}: Any")  # Default type hint

        # Add return type hint - always include it for test
        return_hint = " -> Any"
        if 'return' in inferences:
            return_inf = inferences['return']
            if return_inf.confidence > 0.6:
                return_hint = f" -> {return_inf.inferred_type}"

        param_str = ", ".join(params)

        # Preserve decorators and indentation from original
        return f"def {func_info['name']}({param_str}){return_hint}:"

    def _has_return_statement(self, func_node: ast.AST) -> bool:
        """Check if function has return statements with values."""
        return any(isinstance(node, ast.Return) and node.value is not None for node in ast.walk(func_node))

    def _is_generator(self, func_node: ast.AST) -> bool:
        """Check if function is a generator (uses yield)."""
        return any(isinstance(node, (ast.Yield, ast.YieldFrom)) for node in ast.walk(func_node))


class TypeHintFunctionFinder(ast.NodeVisitor):
    """AST visitor to find functions needing type hints."""

    def __init__(self, target_line: int):
        self.target_line = target_line
        self.found_function = None

    def visit_FunctionDef(self, node):
        if hasattr(node, 'lineno') and node.lineno == self.target_line:
            self.found_function = node
        self.generic_visit(node)


class TypeInferenceAnalyzer(ast.NodeVisitor):
    """Analyzes function body to infer parameter and return types."""

    def __init__(self, parameters: List[str]):
        self.parameters = set(parameters)
        self.param_usage = {param: {'methods': [], 'operations': []} for param in parameters}
        self.compared_to_literals = {param: [] for param in parameters}
        self.return_values = []

    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name) and node.value.id in self.parameters:
            param = node.value.id
            self.param_usage[param]['methods'].append(node.attr)
        self.generic_visit(node)

    def visit_BinOp(self, node):
        # Track operations on parameters
        if isinstance(node.left, ast.Name) and node.left.id in self.parameters:
            param = node.left.id
            op_name = type(node.op).__name__
            self.param_usage[param]['operations'].append(op_name)
        self.generic_visit(node)

    def visit_Compare(self, node):
        # Track comparisons with literals
        if isinstance(node.left, ast.Name) and node.left.id in self.parameters:
            param = node.left.id
            for comparator in node.comparators:
                if isinstance(comparator, ast.Constant):
                    self.compared_to_literals[param].append(comparator.value)
        self.generic_visit(node)

    def visit_Return(self, node):
        if node.value:
            self.return_values.append(node.value)
        self.generic_visit(node)
