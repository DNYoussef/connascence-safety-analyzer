"""
Magic literal fixer for Connascence of Meaning (CoM) violations.

Automatically detects magic literals and generates patches to extract
them into named constants, improving code maintainability.
"""

import ast
import re
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass

from .patch_api import PatchSuggestion
from analyzer.core import ConnascenceViolation


@dataclass
class MagicLiteralContext:
    """Context information for a magic literal."""
    value: Any
    type_name: str
    usage_context: str  # 'condition', 'assignment', 'return', etc.
    surrounding_code: str
    variable_names: List[str]  # Nearby variables for context


class MagicLiteralFixer:
    """Fixes Connascence of Meaning violations by extracting magic literals."""
    
    def __init__(self):
        self.constants_module_name = "constants"
        self.ignored_values = {0, 1, -1, 2, True, False, None, ""}
        self.ignored_containers = [[], (), {}]  # Keep unhashable types separately
        self.common_patterns = {
            'http_status': r'[45]\d{2}',  # HTTP status codes
            'port': r'^(80|443|8080|3000|5000)$',
            'percentage': r'^(100|50|25|75)$',
            'time': r'^(60|3600|86400)$'  # seconds, minute, hour, day
        }
    
    def generate_patch(self, violation: ConnascenceViolation, 
                      tree: ast.AST, source_code: str) -> Optional[PatchSuggestion]:
        """Generate patch for a magic literal violation."""
        context = self._extract_context(violation, tree, source_code)
        if not context or context.value in self.ignored_values:
            return None
        
        constant_name = self._generate_constant_name(context)
        confidence = self._calculate_confidence(context)
        
        if confidence < 0.5:
            return None
        
        old_code = self._get_old_code(violation, source_code)
        new_code = self._generate_new_code(old_code, context, constant_name)
        
        return PatchSuggestion(
            violation_id=violation.id,
            confidence=confidence,
            description=f"Extract magic literal '{context.value}' to constant {constant_name}",
            old_code=old_code,
            new_code=new_code,
            file_path=violation.file_path,
            line_range=(violation.line_number, violation.line_number),
            safety_level=self._assess_safety(context),
            rollback_info={}
        )
    
    def _extract_context(self, violation: ConnascenceViolation,
                        tree: ast.AST, source_code: str) -> Optional[MagicLiteralContext]:
        """Extract context information about the magic literal."""
        lines = source_code.splitlines()
        if violation.line_number > len(lines):
            return None
        
        target_line = lines[violation.line_number - 1]
        
        # Find the literal in the AST
        literal_finder = MagicLiteralVisitor(violation.line_number)
        literal_finder.visit(tree)
        
        if not literal_finder.found_literal:
            return None
        
        node = literal_finder.found_literal
        context_analyzer = ContextAnalyzer()
        context_analyzer.visit(tree)
        
        usage_context = context_analyzer.get_usage_context(node)
        surrounding_vars = context_analyzer.get_nearby_variables(violation.line_number)
        
        return MagicLiteralContext(
            value=node.value if hasattr(node, 'value') else node.s,
            type_name=type(node.value).__name__ if hasattr(node, 'value') else 'str',
            usage_context=usage_context,
            surrounding_code=target_line.strip(),
            variable_names=surrounding_vars
        )
    
    def _generate_constant_name(self, context: MagicLiteralContext) -> str:
        """Generate appropriate constant name based on context."""
        value_str = str(context.value)
        
        # Check common patterns
        for pattern_name, pattern in self.common_patterns.items():
            if re.match(pattern, value_str):
                return f"{pattern_name.upper()}_{value_str}".replace('.', '_')
        
        # Use context clues
        if context.usage_context == 'condition':
            if isinstance(context.value, (int, float)):
                return f"MAX_{self._extract_concept(context)}" if context.value > 0 else f"MIN_{self._extract_concept(context)}"
        
        # Use surrounding variable names
        if context.variable_names:
            base_name = context.variable_names[0].upper()
            if isinstance(context.value, str):
                return f"{base_name}_DEFAULT"
            elif isinstance(context.value, (int, float)):
                return f"{base_name}_LIMIT"
        
        # Fallback based on value type and content
        if isinstance(context.value, str):
            clean_value = re.sub(r'[^\w]', '_', context.value).upper()[:20]
            return f"DEFAULT_{clean_value}" if clean_value else "DEFAULT_STRING"
        elif isinstance(context.value, (int, float)):
            return f"DEFAULT_VALUE_{abs(context.value)}"
        else:
            return f"DEFAULT_{type(context.value).__name__.upper()}"
    
    def _extract_concept(self, context: MagicLiteralContext) -> str:
        """Extract conceptual meaning from context."""
        code = context.surrounding_code.lower()
        
        concepts = {
            'size': ['len', 'size', 'count', 'length'],
            'age': ['age', 'year', 'old'],
            'price': ['price', 'cost', 'amount', 'fee'],
            'time': ['time', 'hour', 'minute', 'second', 'day'],
            'score': ['score', 'rating', 'points'],
            'id': ['id', 'identifier', 'key']
        }
        
        for concept, keywords in concepts.items():
            if any(keyword in code for keyword in keywords):
                return concept.upper()
        
        return "VALUE"
    
    def _calculate_confidence(self, context: MagicLiteralContext) -> float:
        """Calculate confidence score for the fix."""
        confidence = 0.7  # Base confidence
        
        # Increase confidence for common magic numbers
        if isinstance(context.value, (int, float)):
            if abs(context.value) > 10:  # Larger numbers more likely to be magic
                confidence += 0.2
            if context.value in [100, 200, 300, 400, 500]:  # HTTP-like codes
                confidence += 0.1
        
        # String literals are usually good candidates
        if isinstance(context.value, str) and len(context.value) > 3:
            confidence += 0.1
        
        # Context-based confidence
        if context.usage_context in ['condition', 'assignment']:
            confidence += 0.1
        
        # Reduce confidence for simple cases
        if context.value in self.ignored_values:
            confidence -= 0.5
        
        return min(confidence, 0.95)  # Cap at 95%
    
    def _assess_safety(self, context: MagicLiteralContext) -> str:
        """Assess safety level of the transformation."""
        # String literals are generally safe to extract
        if isinstance(context.value, str):
            return 'safe'
        
        # Small integers might be algorithmic
        if isinstance(context.value, int) and abs(context.value) <= 5:
            return 'risky'
        
        # Large numbers are usually configuration
        if isinstance(context.value, (int, float)) and abs(context.value) > 100:
            return 'safe'
        
        return 'moderate'
    
    def _get_old_code(self, violation: ConnascenceViolation, source: str) -> str:
        """Extract the old code line."""
        lines = source.splitlines()
        if violation.line_number <= len(lines):
            return lines[violation.line_number - 1]
        return ""
    
    def _generate_new_code(self, old_code: str, context: MagicLiteralContext, 
                          constant_name: str) -> str:
        """Generate new code with constant reference."""
        value_str = repr(context.value)
        
        # Add import if needed (simple heuristic)
        new_code = old_code
        if f"from {self.constants_module_name} import" not in old_code:
            import_line = f"from {self.constants_module_name} import {constant_name}\n"
            new_code = import_line + new_code
        
        # Replace the literal
        new_code = new_code.replace(value_str, constant_name, 1)
        
        return new_code


class MagicLiteralVisitor(ast.NodeVisitor):
    """AST visitor to find magic literals on specific lines."""
    
    def __init__(self, target_line: int):
        self.target_line = target_line
        self.found_literal = None
    
    def visit_Constant(self, node):
        if hasattr(node, 'lineno') and node.lineno == self.target_line:
            self.found_literal = node
        self.generic_visit(node)
    
    def visit_Str(self, node):  # Python < 3.8 compatibility
        if hasattr(node, 'lineno') and node.lineno == self.target_line:
            self.found_literal = node
        self.generic_visit(node)
    
    def visit_Num(self, node):  # Python < 3.8 compatibility
        if hasattr(node, 'lineno') and node.lineno == self.target_line:
            self.found_literal = node
        self.generic_visit(node)


class ContextAnalyzer(ast.NodeVisitor):
    """Analyzes code context around magic literals."""
    
    def __init__(self):
        self.contexts = {}
        self.variables_by_line = {}
    
    def visit_Compare(self, node):
        """Track comparison contexts."""
        if hasattr(node, 'lineno'):
            self.contexts[id(node)] = 'condition'
        self.generic_visit(node)
    
    def visit_Assign(self, node):
        """Track assignment contexts."""
        if hasattr(node, 'lineno'):
            self.contexts[id(node.value)] = 'assignment'
            # Track variable names
            for target in node.targets:
                if isinstance(target, ast.Name):
                    line = getattr(node, 'lineno', 0)
                    if line not in self.variables_by_line:
                        self.variables_by_line[line] = []
                    self.variables_by_line[line].append(target.id)
        self.generic_visit(node)
    
    def visit_Return(self, node):
        """Track return contexts."""
        if hasattr(node, 'lineno') and node.value:
            self.contexts[id(node.value)] = 'return'
        self.generic_visit(node)
    
    def get_usage_context(self, node) -> str:
        """Get usage context for a node."""
        return self.contexts.get(id(node), 'unknown')
    
    def get_nearby_variables(self, line_number: int) -> List[str]:
        """Get variable names near the given line."""
        variables = []
        for line in range(max(1, line_number - 2), line_number + 3):
            variables.extend(self.variables_by_line.get(line, []))
        return variables