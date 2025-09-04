"""
Algorithm Connascence Analyzer - CoA detection and complexity analysis
Extracted from ConnascenceASTAnalyzer to reduce God Object violation.
"""

import ast
from typing import Dict, List

from ..thresholds import ConnascenceType, Severity
from .base_analyzer import BaseConnascenceAnalyzer
from .violations import Violation


class AlgorithmAnalyzer(BaseConnascenceAnalyzer):
    """Specialized analyzer for Connascence of Algorithm (CoA) and complexity."""
    
    def analyze_algorithm_connascence(self, tree: ast.AST) -> List[Violation]:
        """Analyze connascence of algorithm (CoA)."""
        violations = []
        function_signatures = {}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Calculate function signature/hash for duplication detection
                signature = self._calculate_function_signature(node)
                
                if signature in function_signatures:
                    # Potential duplicate algorithm
                    original_func = function_signatures[signature]
                    violations.append(Violation(
                        id="",
                        type=ConnascenceType.ALGORITHM,
                        severity=Severity.MEDIUM,
                        file_path=self.current_file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        description=f"Function '{node.name}' may duplicate algorithm from '{original_func.name}'",
                        recommendation="Extract common algorithm into shared function",
                        function_name=node.name,
                        locality="same_module",
                        context={
                            "similar_function": original_func.name,
                            "signature": signature
                        }
                    ))
                else:
                    function_signatures[signature] = node
                
                # Check for high complexity
                complexity = self._calculate_cyclomatic_complexity(node)
                if complexity > self.thresholds.max_cyclomatic_complexity:
                    violations.append(Violation(
                        id="",
                        type=ConnascenceType.ALGORITHM,
                        severity=Severity.HIGH,
                        file_path=self.current_file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        description=f"Function '{node.name}' has high cyclomatic complexity ({complexity})",
                        recommendation="Break down function into smaller, focused functions",
                        function_name=node.name,
                        locality="same_function",
                        context={"complexity": complexity}
                    ))
        
        # NASA Power of Ten Rule 1: Avoid recursive functions
        violations.extend(self._detect_recursion_violations(tree))
        
        return violations
    
    def analyze_execution_connascence(self, tree: ast.AST) -> List[Violation]:
        """Analyze connascence of execution (CoE) - order-dependent operations."""
        violations = []
        
        # Track initialization and method call patterns
        class_methods = {}
        init_patterns = []
        
        for node in ast.walk(tree):
            # Track class methods to detect setup/teardown dependencies
            if isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                class_methods[node.name] = methods
                
                # Look for setup/init methods that suggest order dependency
                init_methods = [m for m in methods if m.name in ['__init__', 'setup', 'initialize', 'connect', 'start']]
                teardown_methods = [m for m in methods if m.name in ['cleanup', 'teardown', 'disconnect', 'stop', 'close']]
                
                if init_methods and teardown_methods:
                    # Check if there are regular methods that might depend on init
                    regular_methods = [m for m in methods if m not in init_methods and m not in teardown_methods and not m.name.startswith('_')]
                    
                    if len(regular_methods) > 0:
                        violations.append(Violation(
                            id="",
                            type=ConnascenceType.EXECUTION,
                            severity=Severity.HIGH,
                            file_path=self.current_file_path,
                            line_number=node.lineno,
                            column=node.col_offset,
                            description=f"Class '{node.name}' has setup/teardown methods suggesting execution order dependency",
                            recommendation="Document required method call order or use context managers",
                            class_name=node.name,
                            locality="same_class",
                            context={
                                "init_methods": [m.name for m in init_methods],
                                "teardown_methods": [m.name for m in teardown_methods],
                                "dependent_methods": [m.name for m in regular_methods]
                            }
                        ))
        
        return violations
    
    def analyze_value_connascence(self, tree: ast.AST) -> List[Violation]:
        """Analyze connascence of value (CoV) - shared mutable state dependencies."""
        violations = []
        
        # Track class attributes that might be shared mutable state
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                mutable_attrs = []
                for child in node.body:
                    if isinstance(child, ast.Assign):
                        for target in child.targets:
                            if isinstance(target, ast.Name):
                                # Check if the assigned value is mutable
                                if isinstance(child.value, (ast.List, ast.Dict, ast.Set)):
                                    mutable_attrs.append(target.id)
                
                if mutable_attrs:
                    # Check if class has methods that modify these attributes
                    methods_modifying_attrs = []
                    for method in [n for n in node.body if isinstance(n, ast.FunctionDef)]:
                        for stmt in ast.walk(method):
                            if isinstance(stmt, ast.Assign):
                                for target in stmt.targets:
                                    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                                        if target.attr in mutable_attrs:
                                            methods_modifying_attrs.append(method.name)
                    
                    if len(methods_modifying_attrs) > 1:
                        violations.append(Violation(
                            id="",
                            type=ConnascenceType.VALUES,
                            severity=Severity.MEDIUM,
                            file_path=self.current_file_path,
                            line_number=node.lineno,
                            column=node.col_offset,
                            description=f"Class '{node.name}' has shared mutable attributes modified by multiple methods",
                            recommendation="Consider immutable data structures or encapsulation patterns",
                            class_name=node.name,
                            locality="same_class",
                            context={
                                "mutable_attributes": mutable_attrs,
                                "modifying_methods": list(set(methods_modifying_attrs))
                            }
                        ))
        
        return violations
    
    def analyze_timing_connascence(self, tree: ast.AST) -> List[Violation]:
        """Analyze connascence of timing (CoTi) - temporal coupling and race conditions."""
        violations = []
        
        # Look for threading and timing-related imports
        threading_imports = set()
        time_imports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in ['threading', 'concurrent.futures', 'asyncio', 'multiprocessing']:
                        threading_imports.add(alias.name)
                    elif alias.name in ['time', 'datetime']:
                        time_imports.add(alias.name)
        
        # Look for timing-dependent patterns
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Sleep calls - direct function call or method call
                if ((isinstance(node.func, ast.Name) and node.func.id == "sleep") or 
                    (isinstance(node.func, ast.Attribute) and node.func.attr == "sleep")):
                    violations.append(Violation(
                        id="",
                        type=ConnascenceType.TIMING,
                        severity=Severity.MEDIUM,
                        file_path=self.current_file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        description="Sleep-based timing dependency detected",
                        recommendation="REFACTOR: Use proper synchronization primitives, events, or async patterns. Pattern: asyncio.Event() or threading.Condition() instead of time.sleep()",
                        code_snippet=self.get_code_snippet(node),
                        locality="same_function",
                        context={
                            "call_type": "sleep",
                            "suggested_refactoring": "synchronization_primitives"
                        }
                    ))
                
                # Thread/async related calls that suggest timing coupling
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr in ['join', 'wait', 'acquire', 'release']:
                        violations.append(Violation(
                            id="",
                            type=ConnascenceType.TIMING,
                            severity=Severity.HIGH,
                            file_path=self.current_file_path,
                            line_number=node.lineno,
                            column=node.col_offset,
                            description=f"Potential timing coupling through {node.func.attr}() call",
                            recommendation="REFACTOR: Use higher-level concurrency patterns or async/await. Pattern: async with context managers or asyncio.gather()",
                            code_snippet=self.get_code_snippet(node),
                            locality="cross_module",
                            context={
                                "call_type": node.func.attr,
                                "suggested_refactoring": "async_context_manager"
                            }
                        ))
        
        # NASA Power of Ten Rule 3: No heap usage after initialization
        violations.extend(self._detect_heap_usage_after_init(tree))
        
        return violations
    
    def _detect_heap_usage_after_init(self, tree: ast.AST) -> List[Violation]:
        """Detect heap usage after initialization for NASA Rule 3."""
        violations = []
        
        # Track initialization functions vs regular runtime functions
        init_functions = {'__init__', 'initialize', 'setup', 'init', 'main', 'configure'}
        runtime_functions = set()
        
        # Collect all function definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name not in init_functions:
                    runtime_functions.add(node.name)
        
        # Check for dynamic allocation in runtime functions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in runtime_functions:
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            # Direct heap allocation calls
                            if child.func.id in ['list', 'dict', 'set', 'bytearray']:
                                violations.append(Violation(
                                    id="",
                                    type=ConnascenceType.TIMING,
                                    severity=Severity.CRITICAL,
                                    file_path=self.current_file_path,
                                    line_number=child.lineno,
                                    column=child.col_offset,
                                    description=f"NASA Rule 3 violation: Heap allocation in runtime function '{node.name}'",
                                    recommendation="REFACTOR: Move all dynamic allocation to initialization phase. NASA Rule 3 prohibits heap usage after initialization",
                                    function_name=node.name,
                                    locality="same_function",
                                    context={
                                        "nasa_rule": "Rule_3_No_Heap_After_Init",
                                        "allocation_type": child.func.id,
                                        "runtime_function": node.name,
                                        "safety_critical": True
                                    }
                                ))
        
        return violations
    
    def _calculate_function_signature(self, node: ast.FunctionDef) -> str:
        """Calculate a signature for function similarity detection."""
        # Normalize function body structure
        elements = []
        for stmt in node.body:
            elements.append(self._normalize_statement(stmt))
        return "|".join(elements)
    
    def _normalize_statement(self, stmt: ast.AST) -> str:
        """Normalize a statement for similarity comparison."""
        if isinstance(stmt, ast.Return):
            return "return" + ("_value" if stmt.value else "")
        elif isinstance(stmt, ast.If):
            return "if"
        elif isinstance(stmt, ast.For):
            return "for"
        elif isinstance(stmt, ast.While):
            return "while"
        elif isinstance(stmt, ast.Assign):
            return f"assign_{len(stmt.targets)}"
        elif isinstance(stmt, ast.Expr):
            if isinstance(stmt.value, ast.Call):
                return "call"
            return "expr"
        else:
            return type(stmt).__name__.lower()
    
    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity for a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def analyze_identity_connascence(self, tree: ast.AST) -> List[Violation]:
        """Analyze connascence of identity (CoI) - object identity and mutable defaults."""
        violations = []
        
        # Track global variables
        global_vars = set()
        mutable_defaults = []
        identity_comparisons = []
        
        for node in ast.walk(tree):
            # Track global variable declarations
            if isinstance(node, ast.Global):
                global_vars.update(node.names)
            
            # Check for mutable default arguments
            elif isinstance(node, ast.FunctionDef):
                for default in node.args.defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        mutable_defaults.append((node, default))
            
            # Check for identity comparisons (is/is not vs ==/!=)
            elif isinstance(node, ast.Compare):
                for op in node.ops:
                    if isinstance(op, (ast.Is, ast.IsNot)):
                        # Check if comparing non-singleton values
                        if not self._is_singleton_comparison(node):
                            identity_comparisons.append(node)
        
        # Report excessive global usage
        if len(global_vars) > 5:
            violations.append(Violation(
                id="",
                type=ConnascenceType.IDENTITY,
                severity=Severity.HIGH,
                file_path=self.current_file_path,
                line_number=1,
                column=0,
                description=f"Excessive global variable usage: {len(global_vars)} globals",
                recommendation="REFACTOR: Replace globals with dependency injection, configuration objects, or class attributes. Create a Config class or use dependency injection framework.",
                locality="cross_module",
                context={
                    "global_count": len(global_vars),
                    "global_vars": list(global_vars),
                    "suggested_refactoring": "dependency_injection_pattern"
                }
            ))
        
        # Report mutable default arguments
        for func_node, default_node in mutable_defaults:
            violations.append(Violation(
                id="",
                type=ConnascenceType.IDENTITY,
                severity=Severity.CRITICAL,
                file_path=self.current_file_path,
                line_number=func_node.lineno,
                column=func_node.col_offset,
                description=f"Mutable default argument in function '{func_node.name}'",
                recommendation="REFACTOR: Use None as default and create mutable object inside function. Pattern: def func(items=None): items = items or []",
                function_name=func_node.name,
                locality="same_function",
                context={
                    "function_name": func_node.name,
                    "mutable_type": type(default_node).__name__,
                    "suggested_refactoring": "none_default_pattern"
                }
            ))
        
        # Report problematic identity comparisons
        for node in identity_comparisons:
            violations.append(Violation(
                id="",
                type=ConnascenceType.IDENTITY,
                severity=Severity.MEDIUM,
                file_path=self.current_file_path,
                line_number=node.lineno,
                column=node.col_offset,
                description="Using identity comparison (is/is not) instead of equality",
                recommendation="REFACTOR: Use equality comparison (==/!=) unless comparing with None, True, False. Pattern: if obj == other instead of if obj is other",
                locality="same_function",
                context={
                    "suggested_refactoring": "equality_comparison"
                }
            ))
        
        return violations
    
    def _is_singleton_comparison(self, node: ast.Compare) -> bool:
        """Check if comparison involves singleton values (None, True, False)."""
        # This is a simplified check - would need more sophisticated AST analysis
        return any(
            isinstance(comparator, ast.Constant) and comparator.value in (None, True, False)
            for comparator in node.comparators
        )
    
    def _detect_recursion_violations(self, tree: ast.AST) -> List[Violation]:
        """Detect recursive function calls for NASA Rule 1."""
        violations = []
        function_calls = {}  # Track function calls within each function
        
        # First pass: collect all function definitions
        functions = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions[node.name] = node
        
        # Second pass: analyze calls within each function
        for func_name, func_node in functions.items():
            calls_in_function = []
            for node in ast.walk(func_node):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id in functions:
                        calls_in_function.append((node.func.id, node))
            
            function_calls[func_name] = calls_in_function
        
        # Detect direct recursion
        for func_name, calls in function_calls.items():
            for called_func, call_node in calls:
                if called_func == func_name:  # Direct recursion
                    violations.append(Violation(
                        id="",
                        type=ConnascenceType.ALGORITHM,
                        severity=Severity.CRITICAL,
                        file_path=self.current_file_path,
                        line_number=call_node.lineno,
                        column=call_node.col_offset,
                        description=f"NASA Rule 1 violation: Direct recursion detected in function '{func_name}'",
                        recommendation="REFACTOR: Replace recursion with iterative approach or bounded recursion with explicit stack limits. NASA Rule 1 prohibits recursion in safety-critical code",
                        function_name=func_name,
                        locality="same_function",
                        context={
                            "nasa_rule": "Rule_1_No_Recursion",
                            "recursion_type": "direct",
                            "function_name": func_name,
                            "safety_critical": True
                        }
                    ))
        
        # Detect indirect recursion (simple cycle detection)
        violations.extend(self._detect_indirect_recursion(function_calls, functions))
        
        return violations
    
    def _detect_indirect_recursion(self, function_calls: dict, functions: dict) -> List[Violation]:
        """Detect indirect recursion cycles."""
        violations = []
        
        def find_cycles(start_func, visited, path):
            if start_func in visited:
                if start_func in path:
                    # Found a cycle
                    cycle_start = path.index(start_func)
                    cycle = path[cycle_start:] + [start_func]
                    return [cycle]
                return []
            
            visited.add(start_func)
            path.append(start_func)
            
            cycles = []
            if start_func in function_calls:
                for called_func, _ in function_calls[start_func]:
                    cycles.extend(find_cycles(called_func, visited.copy(), path.copy()))
            
            return cycles
        
        # Check each function for indirect recursion cycles
        for func_name in functions.keys():
            cycles = find_cycles(func_name, set(), [])
            for cycle in cycles:
                if len(cycle) > 2:  # Indirect recursion (cycle length > 2)
                    func_node = functions[func_name]
                    violations.append(Violation(
                        id="",
                        type=ConnascenceType.ALGORITHM,
                        severity=Severity.HIGH,
                        file_path=self.current_file_path,
                        line_number=func_node.lineno,
                        column=func_node.col_offset,
                        description=f"NASA Rule 1 violation: Indirect recursion cycle detected: {' → '.join(cycle)}",
                        recommendation="REFACTOR: Break recursion cycle by redesigning call hierarchy. NASA Rule 1 prohibits all forms of recursion",
                        function_name=func_name,
                        locality="cross_function",
                        context={
                            "nasa_rule": "Rule_1_No_Recursion",
                            "recursion_type": "indirect",
                            "cycle_path": cycle,
                            "cycle_length": len(cycle) - 1,
                            "safety_critical": True
                        }
                    ))
        
        return violations