"""
Refactored Connascence Detector

Refactored version of the original ConnascenceDetector using composition
and the Single Responsibility Principle. This version uses extracted
helper classes to reduce complexity and improve maintainability.
"""

import ast
from typing import List, Dict, Any, Tuple

from ..helpers.violation_reporter import ViolationReporter, ConnascenceViolation
from ..helpers.ast_analysis_helper import ASTAnalysisHelper
from ..helpers.context_analyzer import ContextAnalyzer


class ConnascenceDetector(ast.NodeVisitor):
    """
    Refactored AST visitor that detects connascence violations.
    
    Uses composition with specialized helper classes to maintain
    single responsibility and reduce complexity.
    """
    
    def __init__(self, file_path: str, source_lines: List[str]):
        self.file_path = file_path
        self.source_lines = source_lines
        
        # Initialize helper classes
        self.violation_reporter = ViolationReporter(file_path, source_lines)
        self.ast_helper = ASTAnalysisHelper(source_lines)
        self.context_analyzer = ContextAnalyzer(file_path, source_lines)
        
        # Violations list
        self.violations: List[ConnascenceViolation] = []
        
        # Core tracking structures (reduced from original)
        self.function_definitions: Dict[str, ast.FunctionDef] = {}
        self.class_definitions: Dict[str, ast.ClassDef] = {}
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Detect connascence violations in function definitions."""
        self.function_definitions[node.name] = node
        
        # Check for Connascence of Position using helper
        positional_count = sum(1 for arg in node.args.args if not arg.arg.startswith("_"))
        if positional_count > 3:
            violation = self.violation_reporter.create_position_violation(node, positional_count)
            self.violations.append(violation)
        
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Detect God Objects and other class-level violations."""
        self.class_definitions[node.name] = node
        
        # Use helper to count complexity
        method_count, loc = self.ast_helper.count_class_complexity(node)
        
        # God Object detection
        if method_count > 20 or loc > 500:
            violation = self.violation_reporter.create_god_object_violation(node, method_count, loc)
            self.violations.append(violation)
        
        self.generic_visit(node)
    
    def visit_Import(self, node: ast.Import):
        """Track imports for dependency analysis."""
        # Simplified - major analysis moved to helpers
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Track imports for dependency analysis."""
        # Simplified - major analysis moved to helpers
        self.generic_visit(node)
    
    def visit_Global(self, node: ast.Global):
        """Track global variable usage (Connascence of Identity)."""
        # Simplified - will be handled in finalize_analysis
        self.generic_visit(node)
    
    def visit_Num(self, node: ast.Num):
        """Detect magic numbers - deprecated but kept for compatibility."""
        # Simplified - moved to finalize_analysis for batch processing
        self.generic_visit(node)
    
    def visit_Constant(self, node: ast.Constant):
        """Detect magic constants."""
        # Simplified - moved to finalize_analysis for batch processing
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """Detect timing-related calls and other patterns."""
        # Check for timing violations using helper
        if self._is_sleep_call(node):
            violation = self.violation_reporter.create_timing_violation(node)
            self.violations.append(violation)
        
        self.generic_visit(node)
    
    def finalize_analysis(self):
        """
        Perform final analysis that requires complete traversal.
        Uses helper classes to reduce complexity of main detector.
        """
        # Use helpers to collect data
        tree = ast.parse("".join(self.source_lines))
        
        # Algorithm duplicate detection
        self._analyze_algorithm_duplicates(tree)
        
        # Magic literal analysis
        self._analyze_magic_literals(tree)
        
        # Global variable analysis
        self._analyze_global_variables(tree)
    
    def _is_sleep_call(self, node: ast.Call) -> bool:
        """Check if call is a sleep function."""
        return (isinstance(node.func, ast.Name) and node.func.id == "sleep") or (
            isinstance(node.func, ast.Attribute) and node.func.attr == "sleep"
        )
    
    def _analyze_algorithm_duplicates(self, tree: ast.AST):
        """Analyze for algorithm duplicates using helper."""
        function_hashes = self.ast_helper.build_function_hashes(tree)
        
        for body_hash, functions in function_hashes.items():
            if len(functions) > 1:
                for file_path, func_node in functions:
                    similar_functions = [f.name for _, f in functions if f != func_node]
                    violation = self.violation_reporter.create_algorithm_violation(
                        func_node, similar_functions
                    )
                    self.violations.append(violation)
    
    def _analyze_magic_literals(self, tree: ast.AST):
        """Analyze magic literals using helper."""
        magic_literals = self.ast_helper.collect_magic_literals(tree)
        
        for node, value in magic_literals:
            in_conditional = self.context_analyzer._is_in_conditional(node)
            violation = self.violation_reporter.create_meaning_violation(
                node, value, in_conditional
            )
            self.violations.append(violation)
    
    def _analyze_global_variables(self, tree: ast.AST):
        """Analyze global variable usage using helper."""
        global_vars = self.ast_helper.collect_global_vars(tree)
        
        if len(global_vars) > 5:
            # Find first global node for violation reporting
            first_global_node = self.ast_helper.find_first_global_node(tree)
            if first_global_node:
                violation = self.violation_reporter.create_identity_violation(
                    first_global_node, len(global_vars), list(global_vars)
                )
                self.violations.append(violation)


class ConnascenceAnalyzer:
    """
    Main analyzer that orchestrates connascence detection.
    Reduced complexity version of the original.
    """
    
    def __init__(self, exclusions: List[str] = None):
        self.exclusions = exclusions or self._default_exclusions()
        self.violations: List[ConnascenceViolation] = []
        self.file_stats: Dict[str, Dict] = {}
    
    def _default_exclusions(self) -> List[str]:
        """Default exclusion patterns."""
        return [
            "test_*", "tests/", "*_test.py", "conftest.py",
            "deprecated/", "archive/", "experimental/",
            "__pycache__/", ".git/", "build/", "dist/",
            "*.egg-info/", "venv*/", "*env*/",
        ]
    
    def should_analyze_file(self, file_path) -> bool:
        """Check if file should be analyzed based on exclusions."""
        path_str = str(file_path)
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
    
    def analyze_file(self, file_path) -> List[ConnascenceViolation]:
        """Analyze a single Python file for connascence violations."""
        try:
            with open(file_path, encoding="utf-8") as f:
                source = f.read()
                source_lines = source.splitlines()
            
            tree = ast.parse(source, filename=str(file_path))
            detector = ConnascenceDetector(str(file_path), source_lines)
            detector.visit(tree)
            detector.finalize_analysis()
            
            # Collect file statistics
            self.file_stats[str(file_path)] = {
                "functions": len(detector.function_definitions),
                "classes": len(detector.class_definitions),
                "violations": len(detector.violations),
            }
            
            return detector.violations
        
        except (SyntaxError, UnicodeDecodeError) as e:
            # Use violation reporter for error handling
            violation_reporter = ViolationReporter(str(file_path), [])
            return [violation_reporter.create_syntax_error_violation(
                e, getattr(e, "lineno", 1), getattr(e, "offset", 0) or 0
            )]
    
    def analyze_directory(self, directory) -> List[ConnascenceViolation]:
        """Analyze all Python files in a directory tree."""
        from pathlib import Path
        
        all_violations = []
        for py_file in Path(directory).rglob("*.py"):
            if self.should_analyze_file(py_file):
                file_violations = self.analyze_file(py_file)
                all_violations.extend(file_violations)
                self.violations.extend(file_violations)
        
        return all_violations
    
    def generate_report(self, violations: List[ConnascenceViolation], output_format: str = "text") -> str:
        """Generate a report of connascence violations."""
        if output_format == "json":
            import json
            from dataclasses import asdict
            return json.dumps([asdict(v) for v in violations], indent=2)
        
        # Text report generation (simplified)
        report_lines = [
            "=" * 80,
            "CONNASCENCE ANALYSIS REPORT (Refactored Detector)",
            "=" * 80,
            f"Total violations: {len(violations)}",
            f"Files analyzed: {len(self.file_stats)}",
            ""
        ]
        
        # Group violations by severity
        for severity in ["critical", "high", "medium", "low"]:
            severity_violations = [v for v in violations if v.severity == severity]
            if not severity_violations:
                continue
            
            report_lines.extend([
                f"\n{severity.upper()} SEVERITY ({len(severity_violations)} violations)",
                "-" * 40
            ])
            
            for v in severity_violations:
                report_lines.extend([
                    f"\n{v.type}: {v.description}",
                    f"File: {v.file_path}:{v.line_number}:{v.column}",
                    f"Recommendation: {v.recommendation}",
                ])
                
                if v.code_snippet:
                    report_lines.extend(["Code context:", v.code_snippet, ""])
        
        return "\n".join(report_lines)