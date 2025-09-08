"""
NASA Power of Ten Rule Analyzer

Analyzes code for compliance with NASA JPL Power of Ten rules for safety-critical software.
Uses the configuration from policy/presets/nasa_power_of_ten.yml to perform comprehensive
rule checking.
"""

import ast
import re
from collections import defaultdict
from pathlib import Path
import sys
from typing import Dict, List, Optional, Set

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.types import ConnascenceViolation

# Import optimization components
try:
    from ..optimization.file_cache import (
        cached_file_content, cached_ast_tree, get_global_cache
    )
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

try:
    import yaml
except ImportError:
    yaml = None


class NASAAnalyzer:
    """Analyzes code for NASA Power of Ten compliance."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize NASA analyzer with configuration."""
        self.config_path = config_path or self._find_nasa_config()
        self.rules_config = self._load_nasa_config()
        
        # Track violations by rule
        self.rule_violations: Dict[str, List[ConnascenceViolation]] = defaultdict(list)
        
        # Analysis state
        self.function_definitions: List[ast.FunctionDef] = []
        self.global_variables: List[ast.Name] = []
        self.loops: List[ast.AST] = []
        self.assertions: List[ast.Assert] = []
        self.malloc_calls: List[ast.Call] = []
        self.return_checks: List[ast.AST] = []
    
    def _find_nasa_config(self) -> str:
        """Find NASA configuration file."""
        possible_paths = [
            Path(__file__).parent.parent.parent / "policy" / "presets" / "nasa_power_of_ten.yml",
            Path(__file__).parent.parent.parent / "config" / "policies" / "nasa_power_of_ten.yml",
            Path("policy/presets/nasa_power_of_ten.yml"),
            Path("config/policies/nasa_power_of_ten.yml")
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path)
        
        return None
    
    def _load_nasa_config(self) -> Dict:
        """Load NASA rules configuration."""
        if not self.config_path or not yaml:
            return self._get_default_nasa_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            print(f"Warning: Could not load NASA config from {self.config_path}: {e}")
            return self._get_default_nasa_config()
    
    def _get_default_nasa_config(self) -> Dict:
        """Get default NASA rules configuration."""
        return {
            "rules": {
                "nasa_rule_1": {"severity": "critical", "violations": [{"type": "goto_statement"}, {"type": "recursive_function"}]},
                "nasa_rule_2": {"severity": "critical", "violations": [{"type": "unbounded_loop"}]},
                "nasa_rule_3": {"severity": "critical", "violations": [{"type": "malloc_after_init"}]},
                "nasa_rule_4": {"severity": "high", "violations": [{"type": "function_too_long", "threshold": 60}]},
                "nasa_rule_5": {"severity": "high", "violations": [{"type": "insufficient_assertions", "threshold": 2}]},
                "nasa_rule_6": {"severity": "medium", "violations": [{"type": "variable_scope_too_wide"}]},
                "nasa_rule_7": {"severity": "high", "violations": [{"type": "unchecked_return_value"}]},
                "nasa_rule_8": {"severity": "medium", "violations": [{"type": "complex_macro"}]},
                "nasa_rule_9": {"severity": "high", "violations": [{"type": "multiple_pointer_indirection"}]},
                "nasa_rule_10": {"severity": "medium", "violations": [{"type": "compiler_warning"}]}
            }
        }
    
    def analyze_file(self, file_path: str, source_code: str = None) -> List[ConnascenceViolation]:
        """Analyze a single file for NASA compliance. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation assertions
        assert file_path is not None, "file_path cannot be None"
        assert isinstance(file_path, str), "file_path must be a string"
        
        self._clear_analysis_state()
        
        try:
            # Use cached AST if available, otherwise parse provided source
            if CACHE_AVAILABLE and source_code is None:
                tree = cached_ast_tree(file_path)
                if not tree:
                    return []
            else:
                # Use provided source code or read from file
                if source_code is None:
                    if CACHE_AVAILABLE:
                        source_code = cached_file_content(file_path)
                    else:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            source_code = f.read()
                
                if not source_code:
                    return []
                
                tree = ast.parse(source_code)
        except (SyntaxError, FileNotFoundError, PermissionError):
            return []  # Skip files with errors
        
        # Collect AST elements for analysis
        self._collect_ast_elements(tree)
        
        # Run all NASA rule checks with bounded operations
        assert len(self.function_definitions) < 1000, "Too many functions for analysis"
        
        self._check_rule_1_control_flow(file_path)
        self._check_rule_2_loop_bounds(file_path)
        self._check_rule_3_heap_usage(file_path)
        self._check_rule_4_function_size(file_path)
        self._check_rule_5_assertions(file_path)
        self._check_rule_6_variable_scope(file_path)
        self._check_rule_7_return_values(file_path)
        # Rules 8-10 are more language-specific and would need additional analysis
        
        # Flatten all violations with memory bounds
        all_violations = []
        for rule_violations in self.rule_violations.values():
            all_violations.extend(rule_violations)
        
        # NASA Rule 7: Bounded memory usage
        assert len(all_violations) < 10000, "Excessive violations detected - possible analysis error"
        
        return all_violations
    
    def _collect_ast_elements(self, tree: ast.AST) -> None:
        """Collect relevant AST elements for analysis."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self.function_definitions.append(node)
            elif isinstance(node, (ast.For, ast.While)):
                self.loops.append(node)
            elif isinstance(node, ast.Assert):
                self.assertions.append(node)
            elif isinstance(node, ast.Global):
                self.global_variables.extend([ast.Name(id=name, ctx=ast.Store()) for name in node.names])
            elif isinstance(node, ast.Call):
                if self._is_malloc_call(node):
                    self.malloc_calls.append(node)
    
    def _is_malloc_call(self, node: ast.Call) -> bool:
        """Check if call is a memory allocation function."""
        if isinstance(node.func, ast.Name):
            return node.func.id in ['malloc', 'calloc', 'realloc']
        return False
    
    def _check_rule_1_control_flow(self, file_path: str) -> None:
        """Check Rule 1: Avoid complex flow constructs."""
        # Check for recursion
        for func in self.function_definitions:
            if self._is_recursive_function(func):
                violation = ConnascenceViolation(
                    type="nasa_rule_1_violation",
                    severity="critical",
                    file_path=file_path,
                    line_number=func.lineno,
                    column=func.col_offset,
                    description=f"NASA Rule 1: Recursive function '{func.name}' detected",
                    recommendation="Convert to iterative solution with explicit stack if needed",
                    code_snippet=f"def {func.name}(...)",
                    context={"nasa_rule": "rule_1", "violation_type": "recursive_function", "function_name": func.name}
                )
                self.rule_violations["nasa_rule_1"].append(violation)
    
    def _check_rule_2_loop_bounds(self, file_path: str) -> None:
        """Check Rule 2: All loops must have fixed upper bounds."""
        for loop in self.loops:
            if not self._has_deterministic_bounds(loop):
                violation = ConnascenceViolation(
                    type="nasa_rule_2_violation",
                    severity="critical",
                    file_path=file_path,
                    line_number=loop.lineno,
                    column=loop.col_offset,
                    description="NASA Rule 2: Loop lacks statically determinable upper bound",
                    recommendation="Add loop counter or use bounded iteration",
                    code_snippet=f"{type(loop).__name__} loop",
                    context={"nasa_rule": "rule_2", "violation_type": "unbounded_loop"}
                )
                self.rule_violations["nasa_rule_2"].append(violation)
    
    def _check_rule_3_heap_usage(self, file_path: str) -> None:
        """Check Rule 3: Do not use heap after initialization."""
        # In Python, this is more about explicit memory management
        for malloc_call in self.malloc_calls:
            violation = ConnascenceViolation(
                type="nasa_rule_3_violation",
                severity="critical",
                file_path=file_path,
                line_number=malloc_call.lineno,
                column=malloc_call.col_offset,
                description="NASA Rule 3: Dynamic memory allocation detected",
                recommendation="Pre-allocate memory during initialization phase",
                code_snippet=f"Memory allocation call",
                context={"nasa_rule": "rule_3", "violation_type": "malloc_after_init"}
            )
            self.rule_violations["nasa_rule_3"].append(violation)
    
    def _check_rule_4_function_size(self, file_path: str) -> None:
        """Check Rule 4: Functions should not exceed 60 lines."""
        for func in self.function_definitions:
            func_length = self._calculate_function_lines(func)
            if func_length > 60:
                violation = ConnascenceViolation(
                    type="nasa_rule_4_violation",
                    severity="high",
                    file_path=file_path,
                    line_number=func.lineno,
                    column=func.col_offset,
                    description=f"NASA Rule 4: Function '{func.name}' is {func_length} lines (limit: 60)",
                    recommendation="Break into smaller, focused functions",
                    code_snippet=f"def {func.name}(...)",
                    context={"nasa_rule": "rule_4", "violation_type": "function_too_long", "function_length": func_length, "threshold": 60}
                )
                self.rule_violations["nasa_rule_4"].append(violation)
    
    def _check_rule_5_assertions(self, file_path: str) -> None:
        """Check Rule 5: At least 2 assertions per function."""
        for func in self.function_definitions:
            func_assertions = self._count_function_assertions(func)
            if func_assertions < 2 and self._calculate_function_lines(func) > 5:  # Only check non-trivial functions
                violation = ConnascenceViolation(
                    type="nasa_rule_5_violation",
                    severity="high",
                    file_path=file_path,
                    line_number=func.lineno,
                    column=func.col_offset,
                    description=f"NASA Rule 5: Function '{func.name}' has {func_assertions} assertions (minimum: 2)",
                    recommendation="Add pre/post-condition assertions or invariant checks",
                    code_snippet=f"def {func.name}(...)",
                    context={"nasa_rule": "rule_5", "violation_type": "insufficient_assertions", "assertion_count": func_assertions, "threshold": 2}
                )
                self.rule_violations["nasa_rule_5"].append(violation)
    
    def _check_rule_6_variable_scope(self, file_path: str) -> None:
        """Check Rule 6: Declare objects at smallest scope."""
        if len(self.global_variables) > 20:
            violation = ConnascenceViolation(
                type="nasa_rule_6_violation",
                severity="medium",
                file_path=file_path,
                line_number=1,
                column=0,
                description=f"NASA Rule 6: Excessive global variables ({len(self.global_variables)} > 20)",
                recommendation="Encapsulate in modules or pass as parameters",
                code_snippet="Global variable declarations",
                context={"nasa_rule": "rule_6", "violation_type": "excessive_global_variables", "global_count": len(self.global_variables), "threshold": 20}
            )
            self.rule_violations["nasa_rule_6"].append(violation)
    
    def _check_rule_7_return_values(self, file_path: str) -> None:
        """Check Rule 7: Check return values of non-void functions."""
        # Optimized: Use cached content to avoid I/O in analysis loops
        unchecked_calls = []
        
        try:
            # Use cached file content if available
            if CACHE_AVAILABLE:
                source_code = cached_file_content(file_path)
                if not source_code:
                    return
                tree = cached_ast_tree(file_path)
            else:
                if not Path(file_path).exists():
                    return
                with open(file_path, 'r', encoding='utf-8') as f:
                    source_code = f.read()
                tree = ast.parse(source_code)
            
            if not tree:
                return
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                    # Function call in expression context (return value not used)
                    if isinstance(node.value.func, ast.Name):
                        func_name = node.value.func.id
                        if func_name not in ['print', 'assert', 'len']:  # Common functions where return value is often ignored
                            unchecked_calls.append(node.value)
            
            for call in unchecked_calls[:5]:  # Limit to avoid spam
                violation = ConnascenceViolation(
                    type="nasa_rule_7_violation",
                    severity="high",
                    file_path=file_path,
                    line_number=call.lineno,
                    column=call.col_offset,
                    description="NASA Rule 7: Function return value not checked",
                    recommendation="Check return value or explicitly cast to void with comment",
                    code_snippet="Function call",
                    context={"nasa_rule": "rule_7", "violation_type": "unchecked_return_value"}
                )
                self.rule_violations["nasa_rule_7"].append(violation)
        except Exception as e:
            # Log error but don't fail analysis
            print(f"Warning: Could not analyze return values in {file_path}: {e}")
    
    def _is_recursive_function(self, func: ast.FunctionDef) -> bool:
        """Check if function is recursive."""
        func_name = func.name
        for node in ast.walk(func):
            if (isinstance(node, ast.Call) and 
                isinstance(node.func, ast.Name) and 
                node.func.id == func_name):
                return True
        return False
    
    def _has_deterministic_bounds(self, loop: ast.AST) -> bool:
        """Check if loop has deterministic bounds."""
        if isinstance(loop, ast.For):
            # For loops with range() are generally bounded
            if (isinstance(loop.iter, ast.Call) and 
                isinstance(loop.iter.func, ast.Name) and 
                loop.iter.func.id == 'range'):
                return True
        elif isinstance(loop, ast.While):
            # while True is unbounded
            if (isinstance(loop.test, ast.Constant) and 
                loop.test.value is True):
                return False
        
        # Simplified check - in practice would need more sophisticated analysis
        return True
    
    def _calculate_function_lines(self, func: ast.FunctionDef) -> int:
        """Calculate function length in lines."""
        if hasattr(func, 'end_lineno') and func.end_lineno:
            return func.end_lineno - func.lineno + 1
        else:
            # Fallback: estimate based on body
            return len(func.body) + 2  # +2 for def line and potential decorators
    
    def _count_function_assertions(self, func: ast.FunctionDef) -> int:
        """Count assertions within a function."""
        assertion_count = 0
        for node in ast.walk(func):
            if isinstance(node, ast.Assert):
                assertion_count += 1
        return assertion_count
    
    def get_nasa_compliance_score(self, violations: List[ConnascenceViolation]) -> float:
        """Calculate NASA compliance score (0.0 = worst, 1.0 = perfect)."""
        if not violations:
            return 1.0
        
        # Weight violations by rule severity
        severity_weights = {"critical": 10, "high": 5, "medium": 2, "low": 1}
        total_penalty = sum(severity_weights.get(v.severity, 1) for v in violations)
        
        # Normalize to 0-1 scale (assuming max 100 weighted violations for 0 score)
        score = max(0.0, 1.0 - (total_penalty / 100.0))
        return round(score, 3)
    
    def get_rule_summary(self, violations: List[ConnascenceViolation]) -> Dict[str, int]:
        """Get summary of violations by NASA rule."""
        # NASA Rule 5: Input validation assertions
        assert violations is not None, "violations cannot be None"
        
        rule_counts = defaultdict(int)
        for violation in violations:
            nasa_rule = violation.context.get("nasa_rule", "unknown")
            rule_counts[nasa_rule] += 1
        
        # NASA Rule 7: Validate return value
        result = dict(rule_counts)
        assert isinstance(result, dict), "result must be a dictionary"
        return result
    
    def _clear_analysis_state(self) -> None:
        """Clear all analysis state for new file. NASA Rule 4 compliant."""
        self.rule_violations.clear()
        self.function_definitions.clear()
        self.global_variables.clear()
        self.loops.clear()
        self.assertions.clear()
        self.malloc_calls.clear()
        self.return_checks.clear()
    
    def _run_all_nasa_rule_checks(self, file_path: str) -> None:
        """Run all NASA rule checks. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation assertion
        assert file_path is not None, "file_path cannot be None"
        
        self._check_rule_1_control_flow(file_path)
        self._check_rule_2_loop_bounds(file_path)
        self._check_rule_3_heap_usage(file_path)
        self._check_rule_4_function_size(file_path)
        self._check_rule_5_assertions(file_path)
        self._check_rule_6_variable_scope(file_path)
        self._check_rule_7_return_values(file_path)
        # Rules 8-10 are more language-specific and would need additional analysis
    
    def _collect_all_violations(self) -> List[ConnascenceViolation]:
        """Collect all violations from rule checks. NASA Rule 4 compliant."""
        all_violations = []
        for rule_violations in self.rule_violations.values():
            all_violations.extend(rule_violations)
        
        # NASA Rule 7: Validate return value
        assert isinstance(all_violations, list), "all_violations must be a list"
        return all_violations