"""
Core AST-based Connascence Analyzer

Enhanced version of the original analyzer with better accuracy,
performance, and integration capabilities.
"""

import ast
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
import json
import logging
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from ..thresholds import (
    ThresholdConfig, WeightConfig, PolicyPreset, ConnascenceType, Severity,
    DEFAULT_THRESHOLDS, DEFAULT_WEIGHTS,
    get_severity_for_violation, calculate_violation_weight
)

logger = logging.getLogger(__name__)


@dataclass
class Violation:
    """Represents a detected connascence violation."""
    
    id: str                          # Unique fingerprint
    type: ConnascenceType           
    severity: Severity
    file_path: str
    line_number: int
    column: int
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    
    # Context information
    description: str = ""
    recommendation: str = ""
    code_snippet: str = ""
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    
    # Metrics
    weight: float = 1.0
    locality: str = "same_module"  # same_function, same_class, same_module, cross_module
    
    # Additional context
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}
        
        # Generate stable fingerprint
        if not self.id:
            self.id = self._generate_fingerprint()
    
    def _generate_fingerprint(self) -> str:
        """Generate stable fingerprint for violation deduplication."""
        components = [
            self.type.value,
            self.file_path,
            str(self.line_number),
            str(self.column),
            self.description[:50],  # First 50 chars of description
        ]
        content = "|".join(components)
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    @property
    def connascence_type(self) -> str:
        """Backward compatibility property for tests."""
        return self.type.value
    
    @property
    def rule_id(self) -> str:
        """Generate rule ID for compatibility."""
        return f"CON_{self.type.value}"
    


@dataclass
class AnalysisResult:
    """Results of connascence analysis."""
    
    violations: List[Violation]
    total_files: int = 0
    analysis_time: float = 0.0
    connascence_index: float = 0.0
    
    # Advanced fields
    timestamp: str = ""
    project_root: str = ""
    total_files_analyzed: int = 0
    analysis_duration_ms: int = 0
    file_stats: Dict[str, Dict[str, Any]] = None
    summary_metrics: Dict[str, Any] = None
    policy_preset: Optional[str] = None
    budget_status: Optional[Dict[str, Any]] = None
    baseline_comparison: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.file_stats is None:
            self.file_stats = {}
        if self.summary_metrics is None:
            self.summary_metrics = {}
        # Backward compatibility
        if self.total_files == 0:
            self.total_files = self.total_files_analyzed
        if self.analysis_time == 0.0:
            self.analysis_time = self.analysis_duration_ms / 1000.0
    
    @property
    def total_violations(self) -> int:
        """Total number of violations."""
        return len(self.violations)
    
    @property
    def critical_count(self) -> int:
        """Number of critical violations."""
        return len([v for v in self.violations if v.severity == Severity.CRITICAL])
    
    @property
    def high_count(self) -> int:
        """Number of high severity violations."""
        return len([v for v in self.violations if v.severity == Severity.HIGH])
    
    @property
    def medium_count(self) -> int:
        """Number of medium severity violations."""
        return len([v for v in self.violations if v.severity == Severity.MEDIUM])
    
    @property
    def low_count(self) -> int:
        """Number of low severity violations."""
        return len([v for v in self.violations if v.severity == Severity.LOW])
    
    @property
    def violations_by_type(self) -> Dict[str, int]:
        """Count violations by type."""
        counts = {}
        for violation in self.violations:
            type_key = violation.type.value
            counts[type_key] = counts.get(type_key, 0) + 1
        return counts


class ConnascenceASTAnalyzer:
    """Enhanced AST-based connascence analyzer."""
    
    def __init__(
        self, 
        thresholds: Optional[ThresholdConfig] = None,
        weights: Optional[WeightConfig] = None,
        policy_preset: Optional[PolicyPreset] = None,
        exclusions: Optional[List[str]] = None
    ):
        self.thresholds = thresholds or DEFAULT_THRESHOLDS
        self.weights = weights or DEFAULT_WEIGHTS
        self.policy_preset = policy_preset
        self.exclusions = exclusions or self._default_exclusions()
        
        # Analysis state
        self.violations: List[Violation] = []
        self.file_stats: Dict[str, Dict[str, Any]] = {}
        self.current_file_path: str = ""
        self.current_source_lines: List[str] = []
        
        # Performance tracking
        self.analysis_start_time = 0.0
        
    def _default_exclusions(self) -> List[str]:
        """Default exclusion patterns."""
        return [
            "test_*", "tests/", "*_test.py", "conftest.py",
            "deprecated/", "archive/", "experimental/",
            "__pycache__/", ".git/", "build/", "dist/",
            "*.egg-info/", "venv*/", "*env*/", "node_modules/",
        ]
    
    def should_analyze_file(self, file_path: Path) -> bool:
        """Check if file should be analyzed based on exclusions."""
        path_str = str(file_path).replace("\\", "/")  # Normalize path separators
        
        for exclusion in self.exclusions:
            if exclusion.endswith("/"):
                if exclusion[:-1] in path_str:
                    return False
            elif "*" in exclusion:
                import fnmatch
                if fnmatch.fnmatch(path_str, exclusion):
                    return False
            elif exclusion in path_str:
                return False
        return True
    
    def analyze_string(self, source_code: str, filename: str = "string_input.py") -> List[Violation]:
        """Analyze source code string for connascence violations."""
        self.current_file_path = filename
        violations = []
        
        try:
            if not source_code.strip():  # Skip empty code
                return []
            
            self.current_source_lines = source_code.splitlines()
            tree = ast.parse(source_code, filename=filename)
            
            # Run all static analysis passes
            file_violations = []
            file_violations.extend(self._analyze_name_connascence(tree))
            file_violations.extend(self._analyze_type_connascence(tree))
            file_violations.extend(self._analyze_meaning_connascence(tree))
            file_violations.extend(self._analyze_position_connascence(tree))
            file_violations.extend(self._analyze_algorithm_connascence(tree))
            
            # Calculate weights and finalize violations
            for violation in file_violations:
                violation.weight = calculate_violation_weight(
                    violation.type, violation.severity, violation.locality,
                    self.current_file_path, self.weights
                )
            
            # Collect file statistics
            self.file_stats[self.current_file_path] = self._calculate_file_stats(
                tree, file_violations
            )
            
            violations.extend(file_violations)
            
        except (SyntaxError, UnicodeDecodeError) as e:
            # Create violation for unparseable code
            violation = Violation(
                id="",
                type=ConnascenceType.NAME,  # Closest match
                severity=Severity.CRITICAL,
                file_path=self.current_file_path,
                line_number=getattr(e, "lineno", 1),
                column=getattr(e, "offset", 0) or 0,
                description=f"Code cannot be parsed: {e}",
                recommendation="Fix syntax errors before analyzing connascence",
                context={"error_type": type(e).__name__, "error_message": str(e)}
            )
            violations.append(violation)
            
        except Exception as e:
            logger.warning(f"Error analyzing {filename}: {e}")
        
        return violations

    def analyze_file(self, file_path: Path) -> List[Violation]:
        """Analyze a single file for connascence violations."""
        if not self.should_analyze_file(file_path):
            return []
        
        self.current_file_path = str(file_path)
        violations = []
        
        try:
            # Read and parse file
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                source = f.read()
                self.current_source_lines = source.splitlines()
            
            if not source.strip():  # Skip empty files
                return []
            
            tree = ast.parse(source, filename=str(file_path))
            
            # Run all static analysis passes
            file_violations = []
            file_violations.extend(self._analyze_name_connascence(tree))
            file_violations.extend(self._analyze_type_connascence(tree))
            file_violations.extend(self._analyze_meaning_connascence(tree))
            file_violations.extend(self._analyze_position_connascence(tree))
            file_violations.extend(self._analyze_algorithm_connascence(tree))
            file_violations.extend(self._analyze_execution_connascence(tree))
            file_violations.extend(self._analyze_value_connascence(tree))
            file_violations.extend(self._analyze_timing_connascence(tree))
            
            # Calculate weights and finalize violations
            for violation in file_violations:
                violation.weight = calculate_violation_weight(
                    violation.type, violation.severity, violation.locality,
                    self.current_file_path, self.weights
                )
            
            # Collect file statistics
            self.file_stats[self.current_file_path] = self._calculate_file_stats(
                tree, file_violations
            )
            
            violations.extend(file_violations)
            
        except (SyntaxError, UnicodeDecodeError) as e:
            # Create violation for unparseable files
            violation = Violation(
                id="",
                type=ConnascenceType.NAME,  # Closest match
                severity=Severity.CRITICAL,
                file_path=self.current_file_path,
                line_number=getattr(e, "lineno", 1),
                column=getattr(e, "offset", 0) or 0,
                description=f"File cannot be parsed: {e}",
                recommendation="Fix syntax errors before analyzing connascence",
                context={"error_type": type(e).__name__, "error_message": str(e)}
            )
            violations.append(violation)
            
        except Exception as e:
            logger.warning(f"Error analyzing {file_path}: {e}")
        
        return violations
    
    def analyze_directory(self, directory: Path) -> AnalysisResult:
        """Analyze all Python files in a directory tree."""
        self.analysis_start_time = time.time()
        all_violations = []
        files_analyzed = 0
        
        for py_file in directory.rglob("*.py"):
            if self.should_analyze_file(py_file):
                file_violations = self.analyze_file(py_file)
                all_violations.extend(file_violations)
                files_analyzed += 1
        
        analysis_duration = int((time.time() - self.analysis_start_time) * 1000)
        
        return AnalysisResult(
            timestamp=datetime.now().isoformat(),
            project_root=str(directory),
            total_files_analyzed=files_analyzed,
            analysis_duration_ms=analysis_duration,
            violations=all_violations,
            file_stats=self.file_stats,
            summary_metrics=self._calculate_summary_metrics(all_violations),
            policy_preset=self.policy_preset.name if self.policy_preset else None,
        )
    
    def _analyze_name_connascence(self, tree: ast.AST) -> List[Violation]:
        """Analyze connascence of name (CoN)."""
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
                    recommendation="Consider refactoring to reduce name dependencies",
                    locality="same_module",
                    context={"name": name, "usage_count": count}
                ))
        
        return violations
    
    def _analyze_type_connascence(self, tree: ast.AST) -> List[Violation]:
        """Analyze connascence of type (CoT)."""
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
                    recommendation="Add type hints to improve type safety and documentation",
                    function_name=func_node.name,
                    locality="same_function"
                ))
        
        return violations
    
    def _analyze_meaning_connascence(self, tree: ast.AST) -> List[Violation]:
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
            context_lines = self._get_context_lines(node.lineno)
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
            
            violations.append(Violation(
                id="",
                type=ConnascenceType.MEANING,
                severity=severity,
                file_path=self.current_file_path,
                line_number=node.lineno,
                column=node.col_offset,
                description=f"Magic literal '{value}' should be a named constant",
                recommendation="Replace with a well-named constant or configuration value",
                code_snippet=self._get_code_snippet(node),
                locality="same_module",
                context={
                    "literal_value": value,
                    "in_conditional": in_conditional,
                    "security_related": is_security_related,
                    "literal_type": type(value).__name__
                }
            ))
        
        return violations
    
    def _analyze_position_connascence(self, tree: ast.AST) -> List[Violation]:
        """Analyze connascence of position (CoP)."""
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Count positional parameters (excluding self/cls)
                args = node.args.args
                if args and args[0].arg in ["self", "cls"]:
                    args = args[1:]
                
                positional_count = len(args)
                
                if positional_count > self.thresholds.max_positional_params:
                    violations.append(Violation(
                        id="",
                        type=ConnascenceType.POSITION,
                        severity=Severity.HIGH,
                        file_path=self.current_file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        description=f"Function '{node.name}' has {positional_count} positional parameters (>{self.thresholds.max_positional_params})",
                        recommendation="Use keyword arguments, data classes, or parameter objects",
                        code_snippet=self._get_code_snippet(node),
                        function_name=node.name,
                        locality="same_function",
                        context={"parameter_count": positional_count}
                    ))
            
            elif isinstance(node, ast.Call):
                # Check function calls with many positional arguments
                if len(node.args) > self.thresholds.max_positional_params:
                    violations.append(Violation(
                        id="",
                        type=ConnascenceType.POSITION,
                        severity=Severity.MEDIUM,
                        file_path=self.current_file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        description=f"Function call with {len(node.args)} positional arguments",
                        recommendation="Use keyword arguments for better readability",
                        code_snippet=self._get_code_snippet(node),
                        locality="same_module",
                        context={"argument_count": len(node.args)}
                    ))
        
        return violations
    
    def _analyze_algorithm_connascence(self, tree: ast.AST) -> List[Violation]:
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
        
        # Check for God Objects
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                method_count = len([n for n in node.body if isinstance(n, ast.FunctionDef)])
                loc = (node.end_lineno or node.lineno + 10) - node.lineno
                
                if method_count > self.thresholds.god_class_methods or loc > self.thresholds.god_class_lines:
                    violations.append(Violation(
                        id="",
                        type=ConnascenceType.ALGORITHM,
                        severity=Severity.CRITICAL,
                        file_path=self.current_file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        description=f"God Object: class '{node.name}' has {method_count} methods and ~{loc} lines",
                        recommendation="Split into smaller, focused classes following Single Responsibility Principle",
                        class_name=node.name,
                        locality="same_class",
                        context={"method_count": method_count, "lines_of_code": loc}
                    ))
        
        return violations
    
    def _analyze_execution_connascence(self, tree: ast.AST) -> List[Violation]:
        """Analyze connascence of execution (CoE) - order-dependent operations."""
        violations = []
        
        # Track initialization and method call patterns
        class_methods = {}
        function_calls = []
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
            
            # Look for explicit order dependencies in function calls
            elif isinstance(node, ast.Call):
                function_calls.append(node)
                
                # Check for common order-dependent patterns
                if isinstance(node.func, ast.Attribute):
                    method_name = node.func.attr
                    
                    # Database transaction patterns
                    if method_name in ['begin', 'commit', 'rollback']:
                        init_patterns.append((node, 'transaction'))
                    
                    # File operation patterns
                    elif method_name in ['open', 'close', 'write', 'read']:
                        init_patterns.append((node, 'file_ops'))
                    
                    # Network connection patterns
                    elif method_name in ['connect', 'disconnect', 'send', 'receive']:
                        init_patterns.append((node, 'network'))
        
        # Check for missing error handling around order-dependent operations
        for node, pattern_type in init_patterns:
            # Check if the call is within try-except block
            parent_nodes = []
            current = node
            
            # Walk up the AST to find if we're in a try block
            in_try_block = False
            for ancestor in ast.walk(tree):
                if isinstance(ancestor, ast.Try):
                    for child in ast.walk(ancestor):
                        if child is node:
                            in_try_block = True
                            break
            
            if not in_try_block:
                severity = Severity.HIGH if pattern_type in ['transaction', 'network'] else Severity.MEDIUM
                violations.append(Violation(
                    id="",
                    type=ConnascenceType.EXECUTION,
                    severity=severity,
                    file_path=self.current_file_path,
                    line_number=node.lineno,
                    column=node.col_offset,
                    description=f"Order-dependent {pattern_type} operation without error handling",
                    recommendation="Wrap order-dependent operations in try-except blocks",
                    code_snippet=self._get_code_snippet(node),
                    locality="same_function",
                    context={"operation_type": pattern_type}
                ))
        
        return violations
    
    def _analyze_value_connascence(self, tree: ast.AST) -> List[Violation]:
        """Analyze connascence of value (CoV) - shared mutable state dependencies."""
        violations = []
        
        # Track global variables and their usage
        global_vars = set()
        global_assignments = []
        global_reads = []
        class_attributes = {}
        
        for node in ast.walk(tree):
            # Track global variable assignments
            if isinstance(node, ast.Global):
                global_vars.update(node.names)
            
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        # Check if it's a module-level assignment (potential global)
                        if isinstance(node.parent, ast.Module) if hasattr(node, 'parent') else True:
                            global_assignments.append((node, target.id))
            
            # Track class attributes that might be shared mutable state
            elif isinstance(node, ast.ClassDef):
                mutable_attrs = []
                for child in node.body:
                    if isinstance(child, ast.Assign):
                        for target in child.targets:
                            if isinstance(target, ast.Name):
                                # Check if the assigned value is mutable
                                if isinstance(child.value, (ast.List, ast.Dict, ast.Set)):
                                    mutable_attrs.append(target.id)
                
                if mutable_attrs:
                    class_attributes[node.name] = mutable_attrs
                    
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
            
            # Look for singleton patterns with mutable state
            elif isinstance(node, ast.FunctionDef) and node.name.lower() in ['singleton', 'get_instance']:
                # Check if function modifies global state
                modifies_global = False
                for stmt in ast.walk(node):
                    if isinstance(stmt, ast.Global):
                        modifies_global = True
                        break
                
                if modifies_global:
                    violations.append(Violation(
                        id="",
                        type=ConnascenceType.VALUES,
                        severity=Severity.HIGH,
                        file_path=self.current_file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        description=f"Singleton pattern in '{node.name}' creates shared mutable state dependency",
                        recommendation="Consider dependency injection or immutable singleton state",
                        function_name=node.name,
                        locality="same_module",
                        context={"pattern_type": "singleton"}
                    ))
        
        # Check for module-level mutable collections
        module_level_mutables = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and hasattr(node, 'lineno'):
                # Check if this is at module level by examining line context
                line_content = self.current_source_lines[node.lineno - 1] if node.lineno <= len(self.current_source_lines) else ""
                if not line_content.startswith(' ') and not line_content.startswith('\t'):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and isinstance(node.value, (ast.List, ast.Dict, ast.Set)):
                            module_level_mutables.append((node, target.id))
        
        for node, var_name in module_level_mutables:
            violations.append(Violation(
                id="",
                type=ConnascenceType.VALUES,
                severity=Severity.MEDIUM,
                file_path=self.current_file_path,
                line_number=node.lineno,
                column=node.col_offset,
                description=f"Module-level mutable collection '{var_name}' creates shared state dependency",
                recommendation="Consider using immutable collections or factory functions",
                locality="same_module",
                context={"variable_name": var_name, "collection_type": type(node.value).__name__}
            ))
        
        return violations
    
    def _analyze_timing_connascence(self, tree: ast.AST) -> List[Violation]:
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
                # Sleep calls (basic timing dependency)
                if isinstance(node.func, ast.Attribute) and node.func.attr == 'sleep':
                    violations.append(Violation(
                        id="",
                        type=ConnascenceType.TIMING,
                        severity=Severity.MEDIUM,
                        file_path=self.current_file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        description="Sleep call creates timing dependency",
                        recommendation="Consider using proper synchronization primitives or async patterns",
                        code_snippet=self._get_code_snippet(node),
                        locality="same_function"
                    ))
                
                # Threading operations without proper synchronization
                elif isinstance(node.func, ast.Attribute):
                    method_name = node.func.attr
                    
                    # Thread creation without locks
                    if method_name in ['Thread', 'start'] and 'threading' in threading_imports:
                        violations.append(Violation(
                            id="",
                            type=ConnascenceType.TIMING,
                            severity=Severity.HIGH,
                            file_path=self.current_file_path,
                            line_number=node.lineno,
                            column=node.col_offset,
                            description="Threading operation may create race conditions",
                            recommendation="Use proper synchronization mechanisms (locks, queues, etc.)",
                            code_snippet=self._get_code_snippet(node),
                            locality="same_module",
                            context={"operation": method_name}
                        ))
                    
                    # Time-based polling patterns
                    elif method_name in ['now', 'time'] and any(imp in time_imports for imp in ['time', 'datetime']):
                        # Check if this is in a loop (polling pattern)
                        in_loop = False
                        for ancestor in ast.walk(tree):
                            if isinstance(ancestor, (ast.While, ast.For)):
                                for child in ast.walk(ancestor):
                                    if child is node:
                                        in_loop = True
                                        break
                        
                        if in_loop:
                            violations.append(Violation(
                                id="",
                                type=ConnascenceType.TIMING,
                                severity=Severity.MEDIUM,
                                file_path=self.current_file_path,
                                line_number=node.lineno,
                                column=node.col_offset,
                                description="Time-based polling loop creates timing dependency",
                                recommendation="Use event-driven patterns or proper async mechanisms",
                                code_snippet=self._get_code_snippet(node),
                                locality="same_function",
                                context={"pattern_type": "polling"}
                            ))
        
        # Look for async/await without proper error handling
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                has_await = False
                has_timeout = False
                
                for child in ast.walk(node):
                    if isinstance(child, ast.Await):
                        has_await = True
                    elif isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                        if child.func.attr in ['wait_for', 'timeout']:
                            has_timeout = True
                
                if has_await and not has_timeout:
                    violations.append(Violation(
                        id="",
                        type=ConnascenceType.TIMING,
                        severity=Severity.MEDIUM,
                        file_path=self.current_file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        description=f"Async function '{node.name}' has await without timeout handling",
                        recommendation="Add timeout handling to prevent indefinite blocking",
                        function_name=node.name,
                        locality="same_function",
                        context={"async_pattern": "await_without_timeout"}
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
    
    def _get_context_lines(self, line_number: int, context: int = 2) -> str:
        """Get context lines around the given line number."""
        start = max(0, line_number - context - 1)
        end = min(len(self.current_source_lines), line_number + context)
        return "\n".join(self.current_source_lines[start:end])
    
    def _get_code_snippet(self, node: ast.AST, context_lines: int = 2) -> str:
        """Extract code snippet around the given node."""
        if not hasattr(node, "lineno"):
            return ""
        
        start_line = max(0, node.lineno - context_lines - 1)
        end_line = min(len(self.current_source_lines), node.lineno + context_lines)
        
        lines = []
        for i in range(start_line, end_line):
            marker = ">>>" if i == node.lineno - 1 else "   "
            lines.append(f"{marker} {i+1:3d}: {self.current_source_lines[i]}")
        
        return "\n".join(lines)
    
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
    
    def _calculate_file_stats(self, tree: ast.AST, violations: List[Violation]) -> Dict[str, Any]:
        """Calculate statistics for the analyzed file."""
        stats = {
            "violations_count": len(violations),
            "violations_by_type": {},
            "violations_by_severity": {},
            "functions_count": 0,
            "classes_count": 0,
            "lines_of_code": len(self.current_source_lines),
        }
        
        # Count violations by type and severity
        for violation in violations:
            type_key = violation.type.value
            severity_key = violation.severity.value
            
            stats["violations_by_type"][type_key] = stats["violations_by_type"].get(type_key, 0) + 1
            stats["violations_by_severity"][severity_key] = stats["violations_by_severity"].get(severity_key, 0) + 1
        
        # Count AST elements
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                stats["functions_count"] += 1
            elif isinstance(node, ast.ClassDef):
                stats["classes_count"] += 1
        
        return stats
    
    def _calculate_summary_metrics(self, violations: List[Violation]) -> Dict[str, Any]:
        """Calculate overall summary metrics."""
        total_violations = len(violations)
        total_weight = sum(v.weight for v in violations)
        
        metrics = {
            "total_violations": total_violations,
            "total_weight": total_weight,
            "average_weight": total_weight / max(1, total_violations),
            "violations_by_type": {},
            "violations_by_severity": {},
            "violations_by_locality": {},
        }
        
        for violation in violations:
            # By type
            type_key = violation.type.value
            metrics["violations_by_type"][type_key] = metrics["violations_by_type"].get(type_key, 0) + 1
            
            # By severity
            severity_key = violation.severity.value
            metrics["violations_by_severity"][severity_key] = metrics["violations_by_severity"].get(severity_key, 0) + 1
            
            # By locality
            locality_key = violation.locality
            metrics["violations_by_locality"][locality_key] = metrics["violations_by_locality"].get(locality_key, 0) + 1
        
        return metrics