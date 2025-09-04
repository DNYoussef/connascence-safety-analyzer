"""
Meaning Connascence Analyzer - CoM detection (magic literals)
Extracted from ConnascenceASTAnalyzer to reduce God Object violation.
"""

import ast
from typing import Any, List, Tuple

from ..thresholds import ConnascenceType, Severity
from .base_analyzer import BaseConnascenceAnalyzer
from .violations import Violation


class MeaningAnalyzer(BaseConnascenceAnalyzer):
    """Specialized analyzer for Connascence of Meaning (CoM) - magic literals."""
    
    def analyze_meaning_connascence(self, tree: ast.AST) -> List[Violation]:
        """Analyze connascence of meaning (CoM) - magic literals."""
        violations = []
        magic_literals = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant):
                if self._is_magic_literal(node.value):
                    magic_literals.append((node, node.value))
            # Handle deprecated AST nodes
            elif isinstance(node, (ast.Num, ast.Str)):
                value = node.n if isinstance(node, ast.Num) else node.s
                if self._is_magic_literal(value):
                    magic_literals.append((node, value))
        
        for node, value in magic_literals:
            # Determine severity based on context
            in_conditional = self._is_in_conditional(node)
            context_lines = self.get_context_lines(node.lineno)
            is_security_related = any(
                keyword in context_lines.lower() 
                for keyword in ["password", "secret", "key", "token", "auth", "crypto"]
            )
            
            if is_security_related:
                severity = Severity.CRITICAL
            elif in_conditional:
                severity = Severity.HIGH
            else:
                severity = Severity.MEDIUM
            
            # Enhanced refactor suggestion based on literal type and context
            refactor_pattern = self._get_refactor_pattern(value, in_conditional, is_security_related)
            
            violations.append(Violation(
                id="",
                type=ConnascenceType.MEANING,
                severity=severity,
                file_path=self.current_file_path,
                line_number=node.lineno,
                column=node.col_offset,
                description=f"Magic literal '{value}' should be a named constant",
                recommendation=f"REFACTOR: {refactor_pattern['description']}. Pattern: {refactor_pattern['example']}",
                code_snippet=self.get_code_snippet(node),
                locality="same_module",
                context={
                    "literal_value": value,
                    "in_conditional": in_conditional,
                    "security_related": is_security_related,
                    "literal_type": type(value).__name__,
                    "suggested_refactoring": refactor_pattern['type']
                }
            ))
        
        return violations
    
    def _is_magic_literal(self, value: Any) -> bool:
        """Check if a value is a magic literal."""
        return value not in self.thresholds.magic_literal_exceptions
    
    def _is_in_conditional(self, node: ast.AST) -> bool:
        """Check if node is within a conditional statement."""
        if not hasattr(node, "lineno"):
            return False
        
        line_content = self.current_source_lines[node.lineno - 1] if node.lineno <= len(self.current_source_lines) else ""
        return any(keyword in line_content for keyword in ["if ", "elif ", "while ", "assert "])
    
    def analyze_name_connascence(self, tree: ast.AST) -> List[Violation]:
        """Analyze connascence of name (CoN) - also related to meaning."""
        violations = []
        
        # Track name usage patterns
        name_usage = {}
        import_conflicts = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                name = node.id
                name_usage[name] = name_usage.get(name, 0) + 1
            
            # Check for import conflicts
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.asname and alias.name != alias.asname:
                        import_conflicts.add((alias.name, alias.asname))
        
        # Detect excessive name coupling
        for name, count in name_usage.items():
            if count > 15 and not name.startswith("_") and name not in ["self", "cls"]:
                violations.append(Violation(
                    id="",
                    type=ConnascenceType.NAME,
                    severity=Severity.MEDIUM,
                    file_path=self.current_file_path,
                    line_number=1,  # Would need more sophisticated tracking
                    column=0,
                    description=f"Name '{name}' used {count} times (high coupling)",
                    recommendation="REFACTOR: Extract class or use dependency injection to reduce name coupling. Pattern: Create a dedicated class or pass as parameter instead of global access",
                    locality="same_module",
                    context={"name": name, "usage_count": count}
                ))
        
        return violations
    
    def analyze_type_connascence(self, tree: ast.AST) -> List[Violation]:
        """Analyze connascence of type (CoT) - also related to meaning."""
        violations = []
        
        # Check for missing type annotations
        functions_without_types = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Skip if it has type annotations
                has_return_annotation = node.returns is not None
                has_arg_annotations = any(arg.annotation for arg in node.args.args)
                
                if not has_return_annotation and not has_arg_annotations:
                    functions_without_types.append(node)
        
        for func_node in functions_without_types:
            if not func_node.name.startswith("_") and func_node.name != "__init__":
                violations.append(Violation(
                    id="",
                    type=ConnascenceType.TYPE,
                    severity=Severity.LOW,
                    file_path=self.current_file_path,
                    line_number=func_node.lineno,
                    column=func_node.col_offset,
                    description=f"Function '{func_node.name}' lacks type annotations",
                    recommendation="REFACTOR: Add type hints for better IDE support and documentation. Pattern: def function_name(param: ParamType) -> ReturnType:",
                    function_name=func_node.name,
                    locality="same_function"
                ))
        
        return violations
    
    def _get_refactor_pattern(self, value: Any, in_conditional: bool, is_security: bool) -> dict:
        """Get specific refactor pattern based on literal type and context."""
        if is_security:
            return {
                'type': 'environment_variable',
                'description': 'Move security-related literal to environment variable or config',
                'example': f'SECRET_KEY = os.environ.get("SECRET_KEY"); if key == SECRET_KEY:'
            }
        elif isinstance(value, (int, float)):
            if in_conditional:
                return {
                    'type': 'status_constant',
                    'description': 'Extract numeric literal to status constant or enum',
                    'example': f'STATUS_ACTIVE = {value}; if status == STATUS_ACTIVE:'
                }
            else:
                return {
                    'type': 'configuration_constant',
                    'description': 'Move numeric literal to configuration constants',
                    'example': f'MAX_RETRIES = {value}; for _ in range(MAX_RETRIES):'
                }
        elif isinstance(value, str):
            if len(str(value)) < 10:
                return {
                    'type': 'string_constant',
                    'description': 'Extract string literal to named constant',
                    'example': f'DEFAULT_FORMAT = "{value}"; format_type = DEFAULT_FORMAT'
                }
            else:
                return {
                    'type': 'message_template',
                    'description': 'Move long string to message template or i18n',
                    'example': f'ERROR_TEMPLATE = "{str(value)[:30]}..."; raise ValueError(ERROR_TEMPLATE)'
                }
        else:
            return {
                'type': 'typed_constant', 
                'description': f'Extract {type(value).__name__} literal to named constant',
                'example': f'DEFAULT_VALUE = {repr(value)}; value = value or DEFAULT_VALUE'
            }