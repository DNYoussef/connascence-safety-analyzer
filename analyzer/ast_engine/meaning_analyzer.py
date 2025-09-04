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
        
        # NASA Power of Ten Rules 7 & 8: Preprocessor use and pointer restrictions
        violations.extend(self._check_preprocessor_and_pointers(tree))
        
        return violations
    
    def _check_preprocessor_and_pointers(self, tree: ast.AST) -> List[Violation]:
        """Check for preprocessor-like patterns and pointer-like operations (NASA Rules 7 & 8)."""
        violations = []
        
        # NASA Rule 8: Restrict function pointer use (Python equivalent: dynamic function calls)
        dynamic_calls = []
        exec_eval_usage = []
        
        for node in ast.walk(tree):
            # Check for dynamic function calls (getattr with call)
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Call):
                    if (isinstance(node.func.func, ast.Name) and 
                        node.func.func.id == 'getattr'):
                        dynamic_calls.append(node)
                
                # Check for eval/exec usage (closest Python equivalent to preprocessor)
                elif isinstance(node.func, ast.Name):
                    if node.func.id in ['eval', 'exec', 'compile']:
                        exec_eval_usage.append(node)
            
            # Check for __import__ usage (dynamic imports)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == '__import__':
                    dynamic_calls.append(node)
        
        # Report dynamic function calls (NASA Rule 8 equivalent)
        for node in dynamic_calls:
            violations.append(Violation(
                id="",
                type=ConnascenceType.NAME,
                severity=Severity.HIGH,
                file_path=self.current_file_path,
                line_number=node.lineno,
                column=node.col_offset,
                description="NASA Rule 8 violation: Dynamic function call detected (equivalent to function pointers)",
                recommendation="REFACTOR: Use explicit function references or polymorphism instead of dynamic calls. NASA Rule 8 restricts dynamic function calls in safety-critical code",
                locality="same_function",
                context={
                    "nasa_rule": "Rule_8_Function_Pointers",
                    "call_type": "dynamic_function_call",
                    "safety_critical": True
                }
            ))
        
        # Report eval/exec usage (NASA Rule 7 equivalent - preprocessor restrictions)
        for node in exec_eval_usage:
            violations.append(Violation(
                id="",
                type=ConnascenceType.NAME,
                severity=Severity.CRITICAL,
                file_path=self.current_file_path,
                line_number=node.lineno,
                column=node.col_offset,
                description="NASA Rule 7 violation: Dynamic code execution detected (eval/exec equivalent to preprocessor)",
                recommendation="REFACTOR: Remove eval/exec calls and use static code structures. NASA Rule 7 limits preprocessor use in safety-critical code",
                locality="same_function",
                context={
                    "nasa_rule": "Rule_7_Preprocessor",
                    "execution_type": node.func.id if isinstance(node.func, ast.Name) else "dynamic",
                    "safety_critical": True
                }
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
        
        # NASA Power of Ten Rule 5: Assertion density should be at least 2%
        violations.extend(self._check_assertion_density(tree))
        
        return violations
    
    def _check_assertion_density(self, tree: ast.AST) -> List[Violation]:
        """Check assertion density for NASA Rule 5."""
        violations = []
        
        # Count total statements and assertions
        total_statements = 0
        assertion_count = 0
        functions_with_low_assertions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Count statements in this function
                func_statements = len([n for n in ast.walk(node) if isinstance(n, ast.stmt)])
                func_assertions = len([n for n in ast.walk(node) if isinstance(n, ast.Assert)])
                
                total_statements += func_statements
                assertion_count += func_assertions
                
                # Check individual function assertion density
                if func_statements > 10:  # Only check functions with substantial code
                    assertion_density = (func_assertions / func_statements) * 100
                    if assertion_density < 2.0:  # NASA Rule 5: 2% minimum
                        functions_with_low_assertions.append({
                            'node': node,
                            'statements': func_statements,
                            'assertions': func_assertions,
                            'density': assertion_density
                        })
        
        # Report functions with low assertion density
        for func_data in functions_with_low_assertions:
            node = func_data['node']
            density = func_data['density']
            violations.append(Violation(
                id="",
                type=ConnascenceType.TYPE,
                severity=Severity.HIGH,
                file_path=self.current_file_path,
                line_number=node.lineno,
                column=node.col_offset,
                description=f"NASA Rule 5 violation: Function '{node.name}' has {density:.1f}% assertion density (minimum: 2%)",
                recommendation="REFACTOR: Add assertions to validate preconditions, postconditions, and invariants. NASA Rule 5 requires ≥2% assertion density for safety-critical code",
                function_name=node.name,
                locality="same_function",
                context={
                    "nasa_rule": "Rule_5_Assertion_Density",
                    "assertion_density": density,
                    "assertions": func_data['assertions'],
                    "statements": func_data['statements'],
                    "required_density": 2.0,
                    "safety_critical": True
                }
            ))
        
        # Report overall module assertion density if too low
        if total_statements > 50:  # Only check substantial modules
            overall_density = (assertion_count / total_statements) * 100
            if overall_density < 1.5:  # Slightly lower threshold for modules
                violations.append(Violation(
                    id="",
                    type=ConnascenceType.TYPE,
                    severity=Severity.MEDIUM,
                    file_path=self.current_file_path,
                    line_number=1,
                    column=0,
                    description=f"NASA Rule 5 violation: Module has {overall_density:.1f}% assertion density (recommended: ≥2%)",
                    recommendation="REFACTOR: Add more assertions throughout the module to validate assumptions and catch errors early. Focus on input validation, boundary conditions, and invariant checks",
                    locality="same_module",
                    context={
                        "nasa_rule": "Rule_5_Assertion_Density",
                        "module_assertion_density": overall_density,
                        "total_assertions": assertion_count,
                        "total_statements": total_statements,
                        "safety_critical": True
                    }
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