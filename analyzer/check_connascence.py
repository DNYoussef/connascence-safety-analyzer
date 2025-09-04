#!/usr/bin/env python3
"""
Enhanced Connascence Detection Engine
=====================================

This is the unified entry point for comprehensive connascence analysis that coordinates:
1. Core connascence detection (all 9 types)
2. NASA Power of Ten rules compliance
3. MECE duplication analysis
4. Multi-linter integration (Ruff, MyPy, Radon, Bandit, Black, BuildFlags)
5. Enterprise reporting and quality gates

Based on Meilir Page-Jones' connascence theory for reducing coupling.
Enhanced with NASA safety standards for mission-critical software.

ARCHITECTURE INTEGRATION:
- Leverages existing AST engine components
- Integrates with tool coordinator for multi-linter analysis  
- Uses policy system for configurable thresholds
- Includes failure detection system for comprehensive validation

EXIT CODES:
- 0: Success (no violations or only low severity)
- 1: Policy violations found
- 2: Configuration error
- 3: Runtime error  
- 4: License validation error
"""

import argparse
import ast
import collections
import json
import os
import sys
import time
import traceback
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# Import existing core analyzer components
try:
    from .ast_engine.core_analyzer import ConnascenceASTAnalyzer
    from .thresholds import ThresholdConfig, ConnascenceType, Severity
    from .smart_integration_engine import SmartIntegrationEngine
    from .failure_detection_system import FailureDetectionSystem
    from .severity_classification import SeverityCalculator, BatchSeverityClassifier, SeverityContext
    ENHANCED_ANALYZER_AVAILABLE = True
except ImportError as e:
    try:
        # Try absolute imports for direct execution
        import sys
        from pathlib import Path
        analyzer_path = Path(__file__).parent
        if str(analyzer_path) not in sys.path:
            sys.path.insert(0, str(analyzer_path))
        
        from ast_engine.core_analyzer import ConnascenceASTAnalyzer
        from thresholds import ThresholdConfig, ConnascenceType, Severity
        from smart_integration_engine import SmartIntegrationEngine
        from failure_detection_system import FailureDetectionSystem
        from severity_classification import SeverityCalculator, BatchSeverityClassifier, SeverityContext
        ENHANCED_ANALYZER_AVAILABLE = True
    except ImportError:
        if "--verbose" in sys.argv:
            print(f"Warning: Core analyzer components not found: {e}", file=sys.stderr)
        ConnascenceASTAnalyzer = None
        ThresholdConfig = None
        SmartIntegrationEngine = None
        FailureDetectionSystem = None
        SeverityCalculator = None
        BatchSeverityClassifier = None
        SeverityContext = None
        ENHANCED_ANALYZER_AVAILABLE = False

# Import tool integration (optional)
try:
    # Try relative import first
    import sys
    from pathlib import Path
    base_path = Path(__file__).parent.parent
    if str(base_path) not in sys.path:
        sys.path.insert(0, str(base_path))
    
    from integrations.tool_coordinator import ToolCoordinator
except ImportError:
    ToolCoordinator = None

# Import policy system (optional)
try:
    from policy.manager import PolicyManager
except ImportError:
    PolicyManager = None

# Import MCP integration (optional)
try:
    from mcp.nasa_power_of_ten_integration import NASAPowerOfTenIntegration
except ImportError:
    NASAPowerOfTenIntegration = None

# Import MECE analyzer (enhanced in Phase 6B)
try:
    from dup_detection.mece_analyzer import MECEAnalyzer
    MECE_ANALYZER_AVAILABLE = True
except ImportError:
    try:
        # Try absolute import for direct execution
        import sys
        from pathlib import Path
        base_path = Path(__file__).parent
        if str(base_path) not in sys.path:
            sys.path.insert(0, str(base_path))
        
        from dup_detection.mece_analyzer import MECEAnalyzer
        MECE_ANALYZER_AVAILABLE = True
    except ImportError:
        MECEAnalyzer = None
        MECE_ANALYZER_AVAILABLE = False


@dataclass
class EnhancedViolation:
    """Enhanced violation with NASA rules and MECE integration."""
    # Core violation data (backward compatible)
    type: str
    severity: str  # 'critical', 'high', 'medium', 'low' 
    file_path: str
    line_number: int
    column: int
    description: str
    recommendation: str
    code_snippet: str
    context: Dict[str, Any]
    
    # Enhanced metadata
    weight: float = 0.0
    nasa_rules_violated: List[str] = None
    related_duplications: List[str] = None
    correlation_id: Optional[str] = None
    confidence_score: float = 1.0
    
    def __post_init__(self):
        if self.nasa_rules_violated is None:
            self.nasa_rules_violated = []
        if self.related_duplications is None:
            self.related_duplications = []


@dataclass 
class ComprehensiveReport:
    """Comprehensive analysis report including all analysis types."""
    timestamp: float
    analysis_duration_ms: int
    project_root: str
    files_analyzed: int
    
    # Core metrics
    violations: List[EnhancedViolation]
    severity_counts: Dict[str, int]
    type_counts: Dict[str, int]
    
    # Enhanced metrics
    nasa_compliance_score: float
    mece_duplication_score: float
    overall_quality_score: float
    
    # Tool integration results
    tool_results: Dict[str, Any] = None
    correlations: Dict[str, Any] = None
    
    # MECE analysis results (enhanced in Phase 6B)
    mece_analysis_results: Dict[str, Any] = None
    
    # Failure predictions
    failure_predictions: List[Dict[str, Any]] = None
    
    # Recommendations
    priority_recommendations: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.tool_results is None:
            self.tool_results = {}
        if self.correlations is None:
            self.correlations = {}
        if self.mece_analysis_results is None:
            self.mece_analysis_results = {}
        if self.failure_predictions is None:
            self.failure_predictions = []
        if self.priority_recommendations is None:
            self.priority_recommendations = []


class LegacyConnascenceDetector(ast.NodeVisitor):
    """
    Legacy AST visitor for backward compatibility.
    
    This maintains the existing simple detection logic while we transition
    to the enhanced modular analyzer architecture.
    """
    
    def __init__(self, file_path: str, source_lines: List[str]):
        self.file_path = file_path
        self.source_lines = source_lines
        self.violations: List[EnhancedViolation] = []
        
        # Tracking structures (legacy compatibility)
        self.function_definitions: Dict[str, ast.FunctionDef] = {}
        self.class_definitions: Dict[str, ast.ClassDef] = {}
        self.imports: Set[str] = set()
        self.magic_literals: List[tuple] = []
        self.global_vars: Set[str] = set()
        self.sleep_calls: List[ast.Call] = []
        self.positional_params: List[tuple] = []
        self.function_hashes: Dict[str, List[tuple]] = collections.defaultdict(list)
    
    def get_code_snippet(self, node: ast.AST, context_lines: int = 2) -> str:
        """Extract code snippet around the given node."""
        if not hasattr(node, "lineno"):
            return ""
        
        start_line = max(0, node.lineno - context_lines - 1)
        end_line = min(len(self.source_lines), node.lineno + context_lines)
        
        lines = []
        for i in range(start_line, end_line):
            marker = ">>>" if i == node.lineno - 1 else "   "
            lines.append(f"{marker} {i+1:3d}: {self.source_lines[i].rstrip()}")
        
        return "\\n".join(lines)
    
    def _normalize_function_body(self, node: ast.FunctionDef) -> str:
        """Create normalized hash of function body for duplicate detection."""
        body_parts = []
        for stmt in node.body:
            if isinstance(stmt, ast.Return):
                body_parts.append(f"return {type(stmt.value).__name__}" if stmt.value else "return")
            elif isinstance(stmt, ast.If):
                body_parts.append("if")
            elif isinstance(stmt, ast.For):
                body_parts.append("for")
            elif isinstance(stmt, ast.While):
                body_parts.append("while")
            elif isinstance(stmt, ast.Assign):
                body_parts.append("assign")
            elif isinstance(stmt, ast.Expr):
                body_parts.append("call" if isinstance(stmt.value, ast.Call) else "expr")
        return "|".join(body_parts)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Detect function-level violations."""
        self.function_definitions[node.name] = node
        
        # Connascence of Position (NASA Rule integration)
        positional_count = sum(1 for arg in node.args.args if not arg.arg.startswith("_"))
        if positional_count > 3:
            self.positional_params.append((node, positional_count))
            
            # Enhanced violation with NASA context
            nasa_rules = ["Rule_9_Pointer_Restrictions"] if positional_count > 5 else []
            
            self.violations.append(EnhancedViolation(
                type="connascence_of_position",
                severity="high", 
                file_path=self.file_path,
                line_number=node.lineno,
                column=node.col_offset,
                description=f"Function '{node.name}' has {positional_count} positional parameters (>3)",
                recommendation="Consider using keyword arguments, data classes, or parameter objects",
                code_snippet=self.get_code_snippet(node),
                context={"parameter_count": positional_count, "function_name": node.name},
                nasa_rules_violated=nasa_rules,
                weight=positional_count * 0.2  # Weight based on parameter count
            ))
        
        # NASA Rule 4: Function size check
        func_length = (node.end_lineno or node.lineno + 10) - node.lineno
        if func_length > 60:  # NASA Rule 4 limit
            severity = "critical" if func_length > 100 else "high"
            self.violations.append(EnhancedViolation(
                type="nasa_function_size_violation",
                severity=severity,
                file_path=self.file_path,
                line_number=node.lineno,
                column=node.col_offset, 
                description=f"NASA Rule 4 violation: Function '{node.name}' has {func_length} lines (limit: 60)",
                recommendation="REFACTOR: Split function into smaller units. NASA Rule 4 requires functions ≤60 lines",
                code_snippet=self.get_code_snippet(node),
                context={
                    "function_length": func_length,
                    "nasa_rule": "Rule_4_Function_Size",
                    "safety_critical": True
                },
                nasa_rules_violated=["Rule_4_Function_Size"],
                weight=func_length * 0.1
            ))
        
        # Algorithm duplication check
        body_hash = self._normalize_function_body(node) 
        if len(node.body) > 3:
            self.function_hashes[body_hash].append((self.file_path, node))
        
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Detect God Objects and class-level violations."""
        self.class_definitions[node.name] = node
        
        method_count = sum(1 for n in node.body if isinstance(n, ast.FunctionDef))
        
        # Estimate lines of code  
        if hasattr(node, "end_lineno") and node.end_lineno:
            loc = node.end_lineno - node.lineno
        else:
            loc = len(node.body) * 5
        
        # God Object detection (NASA Rule 4 related)
        if method_count > 20 or loc > 500:
            nasa_rules = ["Rule_4_Function_Size"] if loc > 500 else []
            
            self.violations.append(EnhancedViolation(
                type="god_object",
                severity="critical",
                file_path=self.file_path,
                line_number=node.lineno,
                column=node.col_offset,
                description=f"Class '{node.name}' is a God Object: {method_count} methods, ~{loc} lines",
                recommendation="Split into smaller, focused classes following Single Responsibility Principle",
                code_snippet=self.get_code_snippet(node),
                context={
                    "method_count": method_count, 
                    "estimated_loc": loc, 
                    "class_name": node.name
                },
                nasa_rules_violated=nasa_rules,
                weight=method_count * 0.3 + loc * 0.01
            ))
        
        self.generic_visit(node)
    
    def visit_Import(self, node: ast.Import):
        """Track imports for dependency analysis."""
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Track imports for dependency analysis.""" 
        if node.module:
            for alias in node.names:
                self.imports.add(f"{node.module}.{alias.name}")
        self.generic_visit(node)
    
    def visit_Global(self, node: ast.Global):
        """Track global variable usage (NASA Rule 6 related)."""
        for name in node.names:
            self.global_vars.add(name)
        self.generic_visit(node)
    
    def visit_Constant(self, node: ast.Constant):
        """Detect magic literals (Connascence of Meaning + NASA Rule 8)."""
        if isinstance(node.value, (int, float)):
            if node.value not in [0, 1, -1, 2, 10, 100, 1000]:
                self.magic_literals.append((node, node.value))
        elif isinstance(node.value, str) and len(node.value) > 1:
            if node.value not in ['', ' ', '\\n', '\\t', 'utf-8', 'ascii']:
                self.magic_literals.append((node, node.value))
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """Detect timing-related calls and other patterns."""
        # Connascence of Timing - sleep() calls
        if ((isinstance(node.func, ast.Name) and node.func.id == "sleep") or
           (isinstance(node.func, ast.Attribute) and node.func.attr == "sleep")):
            self.sleep_calls.append(node)
            self.violations.append(EnhancedViolation(
                type="connascence_of_timing",
                severity="medium",
                file_path=self.file_path,
                line_number=node.lineno,
                column=node.col_offset,
                description="Sleep-based timing dependency detected",
                recommendation="Use proper synchronization primitives, events, or async patterns",
                code_snippet=self.get_code_snippet(node),
                context={"call_type": "sleep"},
                weight=1.0
            ))
        
        # NASA Rule 3: Dynamic memory allocation detection
        if isinstance(node.func, ast.Name) and node.func.id in ['list', 'dict', 'set', 'bytearray']:
            if len(node.args) == 0:  # No size specified = dynamic
                self.violations.append(EnhancedViolation(
                    type="nasa_dynamic_memory_violation",
                    severity="high",
                    file_path=self.file_path,
                    line_number=node.lineno,
                    column=node.col_offset,
                    description=f"NASA Rule 3 violation: Dynamic memory allocation {node.func.id}()",
                    recommendation="REFACTOR: Use pre-allocated containers with fixed sizes",
                    code_snippet=self.get_code_snippet(node),
                    context={
                        "nasa_rule": "Rule_3_No_Heap_After_Init",
                        "allocation_type": node.func.id,
                        "safety_critical": True
                    },
                    nasa_rules_violated=["Rule_3_No_Heap_After_Init"],
                    weight=1.5
                ))
        
        self.generic_visit(node)
    
    def finalize_analysis(self):
        """Perform final analysis requiring complete traversal."""
        # Algorithm duplicates (MECE related)
        for body_hash, functions in self.function_hashes.items():
            if len(functions) > 1:
                for file_path, func_node in functions:
                    self.violations.append(EnhancedViolation(
                        type="connascence_of_algorithm", 
                        severity="medium",
                        file_path=file_path,
                        line_number=func_node.lineno,
                        column=func_node.col_offset,
                        description=f"Function '{func_node.name}' duplicates algorithm from other functions",
                        recommendation="Extract common algorithm into shared function or module",
                        code_snippet=self.get_code_snippet(func_node),
                        context={
                            "duplicate_count": len(functions),
                            "function_name": func_node.name,
                            "similar_functions": [f.name for _, f in functions if f != func_node]
                        },
                        related_duplications=[f.name for _, f in functions if f != func_node],
                        weight=len(functions) * 0.5
                    ))
        
        # Magic literals analysis (NASA Rule 8 related)
        for node, value in self.magic_literals:
            in_conditional = self._is_in_conditional(node)
            nasa_rules = ["Rule_8_Preprocessor"] if in_conditional else []
            
            self.violations.append(EnhancedViolation(
                type="connascence_of_meaning",
                severity="high" if in_conditional else "medium", 
                file_path=self.file_path,
                line_number=node.lineno,
                column=node.col_offset,
                description=f"Magic literal '{value}' should be a named constant",
                recommendation="Replace with a well-named constant or configuration value",
                code_snippet=self.get_code_snippet(node),
                context={
                    "literal_value": value,
                    "in_conditional": in_conditional
                },
                nasa_rules_violated=nasa_rules,
                weight=1.2 if in_conditional else 0.8
            ))
        
        # NASA Rule 6: Excessive global usage  
        if len(self.global_vars) > 5:
            for node in ast.walk(ast.parse("".join(self.source_lines))):
                if isinstance(node, ast.Global):
                    self.violations.append(EnhancedViolation(
                        type="nasa_scope_violation",
                        severity="high",
                        file_path=self.file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        description=f"NASA Rule 6 violation: Excessive global variables ({len(self.global_vars)})",
                        recommendation="Use dependency injection, configuration objects, or class attributes",
                        code_snippet=self.get_code_snippet(node),
                        context={
                            "global_count": len(self.global_vars),
                            "global_vars": list(self.global_vars),
                            "nasa_rule": "Rule_6_Smallest_Scope"
                        },
                        nasa_rules_violated=["Rule_6_Smallest_Scope"],
                        weight=len(self.global_vars) * 0.3
                    ))
                    break
    
    def _is_in_conditional(self, node: ast.AST) -> bool:
        """Check if node is within a conditional statement.""" 
        line_content = self.source_lines[node.lineno - 1] if node.lineno <= len(self.source_lines) else ""
        return any(keyword in line_content for keyword in ["if ", "elif ", "while ", "assert "])


class EnhancedConnascenceAnalyzer:
    """
    Enhanced analyzer that coordinates multiple analysis approaches.
    
    Combines legacy detection with new modular architecture and 
    integrates NASA rules, MECE analysis, and tool coordination.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.exclusions = self.config.get('exclusions', [
            "test_*", "tests/", "*_test.py", "conftest.py",
            "deprecated/", "archive/", "experimental/",
            "__pycache__/", ".git/", "build/", "dist/",
            "*.egg-info/", "venv*/", "*env*/"
        ])
        
        # Initialize components if available
        self.policy_manager = None  # Will be initialized if needed
        self.tool_coordinator = None  # Will be initialized if needed
        self.smart_integration = None  # Will be initialized if needed
        self.failure_detector = None  # Will be initialized if needed
        
        # Initialize enhanced severity classification system
        if SeverityCalculator:
            self.severity_calculator = SeverityCalculator(config.get('severity', {}))
            self.batch_classifier = BatchSeverityClassifier(self.severity_calculator)
        else:
            self.severity_calculator = None
            self.batch_classifier = None
        
        # Results storage
        self.violations: List[EnhancedViolation] = []
        self.file_stats: Dict[str, Dict] = {}
        self.tool_results: Dict[str, Any] = {}
    
    def should_analyze_file(self, file_path: Path) -> bool:
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
    
    def analyze_file(self, file_path: Path) -> List[EnhancedViolation]:
        """Enhanced file analysis combining legacy and new approaches."""
        violations = []
        
        try:
            with open(file_path, encoding="utf-8") as f:
                source = f.read()
                source_lines = source.splitlines()
            
            # Legacy analysis (always available)
            tree = ast.parse(source, filename=str(file_path))
            detector = LegacyConnascenceDetector(str(file_path), source_lines)
            detector.visit(tree) 
            detector.finalize_analysis()
            violations.extend(detector.violations)
            
            # Enhanced analysis if components available
            if ENHANCED_ANALYZER_AVAILABLE and ConnascenceASTAnalyzer:
                try:
                    analyzer = ConnascenceASTAnalyzer()
                    enhanced_violations = analyzer.analyze_file(file_path)
                    # Convert to enhanced format and merge
                    for v in enhanced_violations:
                        enhanced_v = self._convert_to_enhanced_violation(v)
                        violations.append(enhanced_v)
                except Exception as e:
                    if "verbose" in sys.argv:
                        print(f"Enhanced analysis failed for {file_path}: {e}", file=sys.stderr)
            
            # Collect file statistics
            self.file_stats[str(file_path)] = {
                "functions": len(detector.function_definitions),
                "classes": len(detector.class_definitions), 
                "imports": len(detector.imports),
                "globals": len(detector.global_vars),
                "magic_literals": len(detector.magic_literals),
                "violations": len(violations)
            }
            
        except (SyntaxError, UnicodeDecodeError) as e:
            # Syntax error violation
            violations.append(EnhancedViolation(
                type="syntax_error",
                severity="critical",
                file_path=str(file_path), 
                line_number=getattr(e, "lineno", 1),
                column=getattr(e, "offset", 0) or 0,
                description=f"File cannot be parsed: {e}",
                recommendation="Fix syntax errors before analyzing connascence",
                code_snippet="",
                context={"error": str(e)},
                weight=10.0  # High weight for syntax errors
            ))
        
        return violations
    
    def analyze_directory(self, directory: Path) -> ComprehensiveReport:
        """Enhanced directory analysis with comprehensive reporting."""
        start_time = time.time()
        all_violations = []
        files_analyzed = 0
        
        # Core connascence analysis
        for py_file in directory.rglob("*.py"):
            if self.should_analyze_file(py_file):
                file_violations = self.analyze_file(py_file)
                all_violations.extend(file_violations)
                files_analyzed += 1
        
        # Tool integration analysis (optional)
        tool_results = {}
        correlations = {}
        if ToolCoordinator:
            try:
                self.tool_coordinator = ToolCoordinator()
                import asyncio
                integrated_results = asyncio.run(
                    self.tool_coordinator.analyze_project(directory)
                )
                tool_results = {
                    tool: result.results 
                    for tool, result in integrated_results.tool_results.items()
                }
                correlations = integrated_results.correlations
            except Exception as e:
                if "verbose" in sys.argv:
                    print(f"Tool integration failed: {e}", file=sys.stderr)
        
        # Calculate metrics
        severity_counts = collections.Counter(v.severity for v in all_violations)
        type_counts = collections.Counter(v.type for v in all_violations)
        
        # NASA compliance score
        nasa_violations = [v for v in all_violations if v.nasa_rules_violated]
        nasa_compliance = 1.0 - min(1.0, len(nasa_violations) / max(files_analyzed, 1))
        
        # MECE duplication analysis (enhanced in Phase 6B)
        mece_results = {}
        mece_score = 1.0
        if MECE_ANALYZER_AVAILABLE and "--mece-analysis" in sys.argv:
            try:
                mece_analyzer = MECEAnalyzer()
                mece_results = mece_analyzer.analyze_codebase(str(directory))
                
                # Update existing violations with MECE data
                self._enhance_violations_with_mece_data(all_violations, mece_results)
                
                # Calculate MECE score from detailed analysis
                if mece_results.get('metrics', {}).get('total_functions_analyzed', 0) > 0:
                    duplication_percentage = mece_results['metrics'].get('duplication_percentage', 0)
                    mece_score = 1.0 - (duplication_percentage / 100.0)
                else:
                    # Fallback to basic calculation
                    mece_violations = [v for v in all_violations if v.related_duplications]
                    mece_score = 1.0 - min(1.0, len(mece_violations) / max(files_analyzed, 1))
                    
            except Exception as e:
                if "--verbose" in sys.argv:
                    print(f"MECE analysis failed: {e}", file=sys.stderr)
                # Fallback to basic MECE score
                mece_violations = [v for v in all_violations if v.related_duplications]
                mece_score = 1.0 - min(1.0, len(mece_violations) / max(files_analyzed, 1))
        else:
            # Basic MECE score calculation (legacy)
            mece_violations = [v for v in all_violations if v.related_duplications]
            mece_score = 1.0 - min(1.0, len(mece_violations) / max(files_analyzed, 1))
        
        # Overall quality score
        weight_sum = sum(v.weight for v in all_violations)
        quality_score = max(0.0, 1.0 - (weight_sum / max(files_analyzed * 10, 1)))
        
        # Failure predictions
        failure_predictions = []
        if severity_counts['critical'] > 0:
            failure_predictions.append({
                'type': 'critical_failure_risk',
                'probability': min(1.0, severity_counts['critical'] / 5),
                'description': f'{severity_counts["critical"]} critical violations detected',
                'timeframe': 'immediate'
            })
        
        # Priority recommendations
        recommendations = self._generate_priority_recommendations(
            severity_counts, nasa_compliance, mece_score
        )
        
        analysis_duration = int((time.time() - start_time) * 1000)
        
        return ComprehensiveReport(
            timestamp=time.time(),
            analysis_duration_ms=analysis_duration,
            project_root=str(directory),
            files_analyzed=files_analyzed,
            violations=all_violations,
            severity_counts=dict(severity_counts),
            type_counts=dict(type_counts),
            nasa_compliance_score=nasa_compliance,
            mece_duplication_score=mece_score,
            overall_quality_score=quality_score,
            tool_results=tool_results,
            correlations=correlations,
            mece_analysis_results=mece_results,  # Enhanced in Phase 6B
            failure_predictions=failure_predictions,
            priority_recommendations=recommendations
        )
    
    def _enhance_violations_with_mece_data(self, violations: List[EnhancedViolation], 
                                          mece_results: Dict[str, Any]):
        """Enhance existing violations with MECE duplication data."""
        if not mece_results.get('duplication_clusters'):
            return
            
        # Create mapping from file paths to duplication clusters
        file_to_clusters = {}
        for cluster in mece_results['duplication_clusters']:
            for file_path in cluster.get('files_involved', []):
                if file_path not in file_to_clusters:
                    file_to_clusters[file_path] = []
                file_to_clusters[file_path].append(cluster)
        
        # Enhance violations with MECE data
        for violation in violations:
            file_path = violation.file_path
            if file_path in file_to_clusters:
                clusters = file_to_clusters[file_path]
                
                # Add related duplications
                if violation.related_duplications is None:
                    violation.related_duplications = []
                
                for cluster in clusters:
                    cluster_info = f"{cluster['cluster_id']}:{cluster['duplication_type']}"
                    if cluster_info not in violation.related_duplications:
                        violation.related_duplications.append(cluster_info)
                
                # Enhance context with MECE information
                if 'mece_clusters' not in violation.context:
                    violation.context['mece_clusters'] = []
                
                for cluster in clusters:
                    violation.context['mece_clusters'].append({
                        'cluster_id': cluster['cluster_id'],
                        'type': cluster['duplication_type'],
                        'confidence': cluster.get('confidence', 0.0),
                        'similarity_score': cluster.get('similarity_score', 0.0),
                        'recommendation': cluster.get('consolidation_recommendation', '')
                    })

    def _convert_to_enhanced_violation(self, violation) -> EnhancedViolation:
        """Convert standard violation to enhanced format."""
        return EnhancedViolation(
            type=getattr(violation, 'type', 'unknown'),
            severity=getattr(violation, 'severity', 'medium'), 
            file_path=getattr(violation, 'file_path', ''),
            line_number=getattr(violation, 'line_number', 0),
            column=getattr(violation, 'column', 0),
            description=getattr(violation, 'description', ''),
            recommendation=getattr(violation, 'recommendation', ''),
            code_snippet=getattr(violation, 'code_snippet', ''),
            context=getattr(violation, 'context', {}),
            weight=getattr(violation, 'weight', 1.0)
        )
    
    def _generate_priority_recommendations(self, severity_counts: Dict, 
                                         nasa_compliance: float,
                                         mece_score: float) -> List[Dict[str, Any]]:
        """Generate prioritized recommendations based on analysis results.""" 
        recommendations = []
        
        if severity_counts['critical'] > 0:
            recommendations.append({
                'priority': 'CRITICAL',
                'category': 'System Stability',
                'action': f'Address {severity_counts["critical"]} critical violations immediately',
                'impact': 'System may fail in production',
                'effort': 'High'
            })
        
        if nasa_compliance < 0.8:
            recommendations.append({
                'priority': 'HIGH', 
                'category': 'Safety Compliance',
                'action': 'Implement NASA Power of Ten rules systematically',
                'impact': 'Safety certification requirements',
                'effort': 'High'
            })
        
        if mece_score < 0.7:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Code Duplication',
                'action': 'Consolidate duplicate code to improve maintainability', 
                'impact': 'Reduced maintenance burden',
                'effort': 'Medium'
            })
        
        return recommendations
    
    def generate_report(self, report: ComprehensiveReport, output_format: str = "text") -> str:
        """Generate comprehensive report with enhanced metrics."""
        if output_format == "json":
            # Convert to JSON-serializable format
            report_dict = asdict(report)
            return json.dumps(report_dict, indent=2, default=str)
        
        # Enhanced text report
        lines = ["=" * 80, "CONNASCENCE SAFETY ANALYZER - COMPREHENSIVE REPORT", "=" * 80, ""]
        
        # Executive Summary
        lines.extend([
            "EXECUTIVE SUMMARY",
            "-" * 40,
            f"Analysis completed in {report.analysis_duration_ms}ms",
            f"Files analyzed: {report.files_analyzed}",
            f"Total violations: {len(report.violations)}",
            f"Overall quality score: {report.overall_quality_score:.2%}",
            f"NASA compliance score: {report.nasa_compliance_score:.2%}",
            f"MECE duplication score: {report.mece_duplication_score:.2%}",
            ""
        ])
        
        # Severity breakdown
        lines.extend([
            "SEVERITY BREAKDOWN",
            "-" * 40,
            f"  Critical: {report.severity_counts.get('critical', 0):3d}",
            f"  High:     {report.severity_counts.get('high', 0):3d}", 
            f"  Medium:   {report.severity_counts.get('medium', 0):3d}",
            f"  Low:      {report.severity_counts.get('low', 0):3d}",
            ""
        ])
        
        # Priority recommendations
        if report.priority_recommendations:
            lines.extend(["PRIORITY RECOMMENDATIONS", "-" * 40])
            for rec in report.priority_recommendations:
                lines.extend([
                    f"[{rec['priority']}] {rec['category']}",
                    f"  Action: {rec['action']}", 
                    f"  Impact: {rec['impact']}",
                    f"  Effort: {rec['effort']}",
                    ""
                ])
        
        # Failure predictions
        if report.failure_predictions:
            lines.extend(["FAILURE PREDICTIONS", "-" * 40])
            for pred in report.failure_predictions:
                lines.extend([
                    f"Risk: {pred['type']} (probability: {pred.get('probability', 0):.1%})",
                    f"  Description: {pred['description']}",
                    f"  Timeframe: {pred.get('timeframe', 'unknown')}",
                    ""
                ])
        
        # MECE consolidation recommendations (enhanced in Phase 6B)
        if report.mece_analysis_results and "--consolidation-recommendations" in sys.argv:
            consolidation_opps = report.mece_analysis_results.get('consolidation_opportunities', [])
            if consolidation_opps:
                lines.extend(["MECE CONSOLIDATION RECOMMENDATIONS", "-" * 40])
                for i, opp in enumerate(consolidation_opps[:5], 1):  # Show top 5
                    lines.extend([
                        f"{i}. Priority: {opp.get('priority', 'Unknown')} - {opp.get('consolidation_strategy', 'Review required')}",
                        f"   Effort: {opp.get('estimated_effort', 'Unknown')} | Benefits: {len(opp.get('benefits', []))} items",
                        f"   Files: {len(opp.get('cluster_id', '').split('_'))} affected",
                        ""
                    ])
            
            # Show duplication metrics
            metrics = report.mece_analysis_results.get('metrics', {})
            if metrics:
                lines.extend([
                    "DUPLICATION METRICS",
                    "-" * 40,
                    f"  Functions analyzed: {metrics.get('total_functions_analyzed', 0)}",
                    f"  Duplication clusters: {metrics.get('total_duplication_clusters', 0)}",
                    f"  Exact duplicates: {metrics.get('exact_duplicates', 0)}",
                    f"  Similar functions: {metrics.get('similar_functions', 0)}",
                    ""
                ])

        # Tool integration results
        if report.tool_results:
            lines.extend(["TOOL INTEGRATION RESULTS", "-" * 40])
            for tool, results in report.tool_results.items():
                issue_count = len(results) if isinstance(results, list) else results.get('issue_count', 0)
                lines.append(f"  {tool:15s}: {issue_count:3d} issues")
            lines.append("")
        
        # Top violations
        if report.violations:
            lines.extend(["TOP VIOLATIONS", "-" * 40])
            sorted_violations = sorted(report.violations, key=lambda v: v.weight, reverse=True)
            for i, v in enumerate(sorted_violations[:10], 1):
                lines.extend([
                    f"{i:2d}. [{v.severity.upper()}] {v.type}",
                    f"    {Path(v.file_path).name}:{v.line_number} - {v.description[:60]}...",
                    f"    Weight: {v.weight:.1f} | NASA: {len(v.nasa_rules_violated)} | MECE: {len(v.related_duplications)}",
                    ""
                ])
        
        return "\\n".join(lines)


def main():
    """Enhanced main entry point with comprehensive options."""
    parser = argparse.ArgumentParser(
        description="Enhanced Connascence Safety Analyzer with NASA Rules & MECE Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
  # Basic analysis
  python check_connascence.py .
  python check_connascence.py src/ --format json
  
  # NASA compliance focus
  python check_connascence.py . --nasa-compliance --severity high
  
  # Enterprise analysis with tools
  python check_connascence.py . --enable-tools --comprehensive
  
  # CI/CD integration
  python check_connascence.py . --fail-on critical,high --format json --output report.json
  
  # MECE duplication analysis
  python check_connascence.py . --mece-analysis --consolidation-recommendations
        """
    )
    
    # Core arguments
    parser.add_argument("path", help="Path to analyze (file or directory)")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument("--format", "-f", choices=["text", "json", "sarif"], 
                       default="text", help="Output format")
    parser.add_argument("--severity", "-s", 
                       choices=["low", "medium", "high", "critical"],
                       help="Minimum severity level to report")
    parser.add_argument("--exclude", "-e", action="append", 
                       help="Additional exclusion patterns")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Verbose output")
    
    # Enhanced analysis options
    parser.add_argument("--nasa-compliance", action="store_true",
                       help="Focus on NASA Power of Ten rules compliance")
    parser.add_argument("--mece-analysis", action="store_true", 
                       help="Include MECE duplication analysis")
    parser.add_argument("--enable-tools", action="store_true",
                       help="Enable multi-tool integration (Ruff, MyPy, etc.)")
    parser.add_argument("--comprehensive", action="store_true",
                       help="Run comprehensive analysis with all features")
    
    # CI/CD integration
    parser.add_argument("--fail-on", help="Comma-separated severities to fail on (e.g., critical,high)")
    parser.add_argument("--budget-file", help="Path to violation budget file")
    parser.add_argument("--baseline-file", help="Path to baseline file for comparison")
    
    # Output options
    parser.add_argument("--consolidation-recommendations", action="store_true",
                       help="Include MECE consolidation recommendations")
    parser.add_argument("--failure-predictions", action="store_true",
                       help="Include failure prediction analysis")
    
    args = parser.parse_args()
    
    # Configure analysis
    config = {}
    if args.exclude:
        config['exclusions'] = args.exclude
    
    if args.comprehensive:
        args.nasa_compliance = True
        args.mece_analysis = True
        args.enable_tools = True
        args.failure_predictions = True
    
    # Initialize analyzer
    analyzer = EnhancedConnascenceAnalyzer(config)
    
    # Validate path
    target_path = Path(args.path)
    if not target_path.exists():
        print(f"Error: Path '{target_path}' does not exist", file=sys.stderr)
        return 2  # Configuration error
    
    if args.verbose:
        print(f"Enhanced Connascence Analysis of {target_path}...")
        if args.nasa_compliance:
            print("  + NASA Power of Ten rules enabled")
        if args.mece_analysis:
            print("  + MECE duplication analysis enabled") 
        if args.enable_tools:
            print("  + Multi-tool integration enabled")
    
    start_time = time.time()
    
    try:
        # Perform analysis
        if target_path.is_file():
            violations = analyzer.analyze_file(target_path)
            # Create report from single file
            report = ComprehensiveReport(
                timestamp=time.time(),
                analysis_duration_ms=int((time.time() - start_time) * 1000),
                project_root=str(target_path.parent),
                files_analyzed=1,
                violations=violations,
                severity_counts=collections.Counter(v.severity for v in violations),
                type_counts=collections.Counter(v.type for v in violations),
                nasa_compliance_score=1.0 - len([v for v in violations if v.nasa_rules_violated]) / max(len(violations), 1),
                mece_duplication_score=1.0 - len([v for v in violations if v.related_duplications]) / max(len(violations), 1),
                overall_quality_score=max(0.0, 1.0 - sum(v.weight for v in violations) / 10)
            )
        else:
            report = analyzer.analyze_directory(target_path)
        
        # Filter by severity
        if args.severity:
            severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
            min_level = severity_order[args.severity]
            report.violations = [
                v for v in report.violations 
                if severity_order.get(v.severity, 0) >= min_level
            ]
        
        # Generate report
        output_text = analyzer.generate_report(report, args.format)
        
        # Output results
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output_text)
            if args.verbose:
                print(f"Report saved to {args.output}")
        else:
            print(output_text)
        
        # Performance summary
        if args.verbose:
            elapsed = time.time() - start_time
            print(f"\\nAnalysis completed in {elapsed:.2f} seconds")
            print(f"Quality Score: {report.overall_quality_score:.2%}")
            print(f"NASA Compliance: {report.nasa_compliance_score:.2%}")
            print(f"MECE Score: {report.mece_duplication_score:.2%}")
        
        # Determine exit code
        if args.fail_on:
            fail_severities = set(s.strip() for s in args.fail_on.split(','))
            failing_violations = [
                v for v in report.violations 
                if v.severity in fail_severities
            ]
            if failing_violations:
                if args.verbose:
                    print(f"\\nFAILING: {len(failing_violations)} violations match --fail-on criteria")
                return 1  # Policy violation
        
        # Default success/warning based on critical violations
        critical_count = report.severity_counts.get('critical', 0)
        if critical_count > 0:
            return 1  # Policy violation
        else:
            return 0  # Success
            
    except KeyboardInterrupt:
        print("\\nAnalysis interrupted by user", file=sys.stderr)
        return 3  # Runtime error
    except Exception as e:
        print(f"Runtime error: {e}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        return 3  # Runtime error


if __name__ == "__main__":
    sys.exit(main())