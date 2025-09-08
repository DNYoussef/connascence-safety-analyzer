"""
Execution Detector

Detects Connascence of Execution violations - control flow dependencies, execution order coupling,
and implicit execution sequence assumptions.
"""

import ast
from collections import defaultdict
from typing import List, Dict, Set

from utils.types import ConnascenceViolation
from .base import DetectorBase


class ExecutionDetector(DetectorBase):
    """Detects execution-based coupling and control flow dependencies."""
    
    def __init__(self, file_path: str, source_lines: List[str]):
        super().__init__(file_path, source_lines)
        
        # Track execution dependencies
        self.global_assignments: List[ast.AST] = []
        self.global_reads: List[ast.AST] = []
        self.exception_handlers: List[ast.AST] = []
        self.function_calls: List[ast.Call] = []
        self.control_flow_nodes: List[ast.AST] = []
        self.import_statements: List[ast.AST] = []
        
        # Track variables that suggest execution order dependencies
        self.stateful_variables: Set[str] = set()
        self.initialization_patterns: Dict[str, ast.AST] = {}
    
    def detect_violations(self, tree: ast.AST) -> List[ConnascenceViolation]:
        """
        Detect execution coupling violations in the AST tree.
        
        Args:
            tree: AST tree to analyze
            
        Returns:
            List of execution-coupling related violations
        """
        self.violations.clear()
        
        # Collect execution-related patterns
        for node in ast.walk(tree):
            if isinstance(node, ast.Global):
                self._track_global_usage(node)
            elif isinstance(node, ast.Name):
                self._track_name_usage(node)
            elif isinstance(node, ast.Call):
                self._track_function_call(node)
            elif isinstance(node, (ast.Try, ast.ExceptHandler)):
                self._track_exception_handling(node)
            elif isinstance(node, (ast.If, ast.For, ast.While)):
                self._track_control_flow(node)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                self._track_imports(node)
            elif isinstance(node, ast.Assign):
                self._track_assignments(node)
        
        # Analyze for execution coupling violations
        self._check_global_state_coupling()
        self._check_initialization_order_coupling()
        self._check_exception_flow_coupling()
        self._check_side_effect_coupling()
        self._check_import_order_dependencies()
        
        return self.violations
    
    def _track_global_usage(self, node: ast.Global) -> None:
        """Track global variable declarations and usage."""
        for name in node.names:
            self.stateful_variables.add(name)
        self.global_assignments.append(node)
    
    def _track_name_usage(self, node: ast.Name) -> None:
        """Track variable name usage patterns."""
        if isinstance(node.ctx, ast.Store):
            # Check for initialization patterns
            var_name = node.id
            if any(keyword in var_name.lower() for keyword in 
                   ['init', 'setup', 'config', 'state', 'cache', 'buffer']):
                self.initialization_patterns[var_name] = node
        elif isinstance(node.ctx, ast.Load):
            # Track reads of potentially stateful variables
            if node.id in self.stateful_variables:
                self.global_reads.append(node)
    
    def _track_function_call(self, node: ast.Call) -> None:
        """Track function calls that might indicate execution dependencies."""
        self.function_calls.append(node)
        
        # Check for calls that suggest order dependencies
        if isinstance(node.func, ast.Name):
            func_name = node.func.id.lower()
            if any(keyword in func_name for keyword in 
                   ['init', 'setup', 'start', 'stop', 'open', 'close', 'connect', 'disconnect']):
                self.initialization_patterns[func_name] = node
    
    def _track_exception_handling(self, node: ast.AST) -> None:
        """Track exception handling patterns."""
        self.exception_handlers.append(node)
    
    def _track_control_flow(self, node: ast.AST) -> None:
        """Track control flow structures."""
        self.control_flow_nodes.append(node)
    
    def _track_imports(self, node: ast.AST) -> None:
        """Track import statements for order dependencies."""
        self.import_statements.append(node)
    
    def _track_assignments(self, node: ast.Assign) -> None:
        """Track assignments for state modification patterns."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id
                # Track assignments to module-level variables
                if var_name.islower() and not var_name.startswith('_'):
                    self.stateful_variables.add(var_name)
    
    def _check_global_state_coupling(self) -> None:
        """Check for excessive global state dependencies."""
        if len(self.global_assignments) > 3 or len(self.stateful_variables) > 5:
            representative_node = self.global_assignments[0] if self.global_assignments else None
            if representative_node:
                self._create_global_state_violation(
                    representative_node, len(self.global_assignments), len(self.stateful_variables)
                )
    
    def _check_initialization_order_coupling(self) -> None:
        """Check for implicit initialization order dependencies."""
        if len(self.initialization_patterns) >= 3:
            # Look for patterns that suggest order matters
            init_functions = [name for name in self.initialization_patterns.keys() 
                             if any(keyword in name.lower() for keyword in ['init', 'setup', 'start'])]
            
            if len(init_functions) >= 2:
                representative_node = list(self.initialization_patterns.values())[0]
                self._create_initialization_order_violation(
                    representative_node, init_functions
                )
    
    def _check_exception_flow_coupling(self) -> None:
        """Check for exception handling that creates execution coupling."""
        if len(self.exception_handlers) > 5:
            # Many exception handlers might indicate complex execution flow coupling
            representative_node = self.exception_handlers[0]
            self._create_exception_flow_violation(
                representative_node, len(self.exception_handlers)
            )
    
    def _check_side_effect_coupling(self) -> None:
        """Check for functions with side effects that create execution coupling."""
        side_effect_calls = []
        
        for call_node in self.function_calls:
            if self._has_side_effects(call_node):
                side_effect_calls.append(call_node)
        
        if len(side_effect_calls) > 8:  # Many side-effect calls
            representative_node = side_effect_calls[0]
            self._create_side_effect_violation(
                representative_node, len(side_effect_calls)
            )
    
    def _check_import_order_dependencies(self) -> None:
        """Check for imports that might create execution order dependencies."""
        # Look for imports mixed with executable code
        if len(self.import_statements) > 0:
            last_import_line = max(node.lineno for node in self.import_statements)
            
            # Check if there are assignments or calls before the last import
            early_code = [node for node in self.function_calls + self.global_assignments 
                         if hasattr(node, 'lineno') and node.lineno < last_import_line]
            
            if len(early_code) > 0:
                representative_node = self.import_statements[-1]
                self._create_import_order_violation(
                    representative_node, len(early_code), last_import_line
                )
    
    def _has_side_effects(self, call_node: ast.Call) -> bool:
        """Check if a function call likely has side effects."""
        if isinstance(call_node.func, ast.Name):
            func_name = call_node.func.id.lower()
            side_effect_keywords = [
                'print', 'write', 'save', 'delete', 'create', 'update', 'insert',
                'connect', 'send', 'post', 'put', 'patch', 'execute', 'run'
            ]
            return any(keyword in func_name for keyword in side_effect_keywords)
        elif isinstance(call_node.func, ast.Attribute):
            attr_name = call_node.func.attr.lower()
            side_effect_methods = [
                'write', 'save', 'delete', 'insert', 'update', 'create',
                'append', 'extend', 'remove', 'clear', 'pop'
            ]
            return any(keyword in attr_name for keyword in side_effect_methods)
        
        return False
    
    def _create_global_state_violation(
        self, node: ast.AST, global_assignments: int, stateful_vars: int
    ) -> None:
        """Create violation for excessive global state coupling."""
        self.violations.append(
            ConnascenceViolation(
                type="connascence_of_execution",
                severity="high",
                file_path=self.file_path,
                line_number=node.lineno,
                column=node.col_offset,
                description=f"Excessive global state coupling: {global_assignments} global assignments, {stateful_vars} stateful variables",
                recommendation="Reduce global state dependencies; use dependency injection or state objects",
                code_snippet=self.get_code_snippet(node),
                context={
                    "violation_type": "global_state_coupling",
                    "global_assignments": global_assignments,
                    "stateful_variables": stateful_vars
                },
            )
        )
    
    def _create_initialization_order_violation(
        self, node: ast.AST, init_functions: List[str]
    ) -> None:
        """Create violation for initialization order dependencies."""
        self.violations.append(
            ConnascenceViolation(
                type="connascence_of_execution",
                severity="medium",
                file_path=self.file_path,
                line_number=node.lineno,
                column=node.col_offset,
                description=f"Initialization order coupling detected: {len(init_functions)} initialization functions",
                recommendation="Make initialization order explicit or eliminate order dependencies",
                code_snippet=self.get_code_snippet(node),
                context={
                    "violation_type": "initialization_order",
                    "init_functions": init_functions,
                    "dependency_count": len(init_functions)
                },
            )
        )
    
    def _create_exception_flow_violation(
        self, node: ast.AST, handler_count: int
    ) -> None:
        """Create violation for complex exception flow coupling."""
        self.violations.append(
            ConnascenceViolation(
                type="connascence_of_execution",
                severity="medium",
                file_path=self.file_path,
                line_number=node.lineno,
                column=node.col_offset,
                description=f"Complex exception flow coupling: {handler_count} exception handlers",
                recommendation="Simplify exception handling; consider using error objects or result types",
                code_snippet=self.get_code_snippet(node),
                context={
                    "violation_type": "exception_flow_coupling",
                    "handler_count": handler_count
                },
            )
        )
    
    def _create_side_effect_violation(
        self, node: ast.AST, side_effect_count: int
    ) -> None:
        """Create violation for excessive side effect coupling."""
        self.violations.append(
            ConnascenceViolation(
                type="connascence_of_execution",
                severity="medium",
                file_path=self.file_path,
                line_number=node.lineno,
                column=node.col_offset,
                description=f"Excessive side effect coupling: {side_effect_count} side-effect operations",
                recommendation="Reduce side effects; separate pure functions from effectful operations",
                code_snippet=self.get_code_snippet(node),
                context={
                    "violation_type": "side_effect_coupling",
                    "side_effect_count": side_effect_count
                },
            )
        )
    
    def _create_import_order_violation(
        self, node: ast.AST, early_code_count: int, last_import_line: int
    ) -> None:
        """Create violation for import order dependencies."""
        self.violations.append(
            ConnascenceViolation(
                type="connascence_of_execution",
                severity="low",
                file_path=self.file_path,
                line_number=node.lineno,
                column=node.col_offset,
                description=f"Import order coupling: {early_code_count} executable statements before imports",
                recommendation="Move all imports to the top of the file to avoid execution order dependencies",
                code_snippet=self.get_code_snippet(node),
                context={
                    "violation_type": "import_order",
                    "early_code_count": early_code_count,
                    "last_import_line": last_import_line
                },
            )
        )