"""
Refactored ConnascenceASTAnalyzer

Enhanced version using composition with specialized analyzers.
Reduced from 597 lines to focused orchestration logic with delegated responsibilities.
"""

import ast
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from .magic_literal_analyzer import MagicLiteralAnalyzer, MagicLiteralConfig
from .parameter_analyzer import ParameterAnalyzer, ParameterConfig
from .complexity_analyzer import ComplexityAnalyzer, ComplexityConfig
from ..helpers.violation_reporter import ConnascenceViolation

logger = logging.getLogger(__name__)


@dataclass
class Violation:
    """Enhanced violation data structure."""
    
    id: str
    type: str           
    severity: str
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
    locality: str = "same_module"
    
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
        import hashlib
        components = [
            self.type,
            self.file_path,
            str(self.line_number),
            str(self.column),
            self.description[:50],
        ]
        content = "|".join(components)
        return hashlib.md5(content.encode()).hexdigest()[:12]


@dataclass
class AnalysisResult:
    """Results of connascence analysis."""
    
    timestamp: str
    project_root: str
    total_files_analyzed: int
    analysis_duration_ms: int
    
    violations: List[Violation]
    file_stats: Dict[str, Dict[str, Any]]
    summary_metrics: Dict[str, Any]
    
    # Policy compliance
    policy_preset: Optional[str] = None
    budget_status: Optional[Dict[str, Any]] = None
    baseline_comparison: Optional[Dict[str, Any]] = None


@dataclass
class AnalyzerConfig:
    """Configuration for the refactored analyzer."""
    magic_literal_config: MagicLiteralConfig = None
    parameter_config: ParameterConfig = None
    complexity_config: ComplexityConfig = None
    exclusions: List[str] = None
    
    def __post_init__(self):
        if self.magic_literal_config is None:
            self.magic_literal_config = MagicLiteralConfig()
        if self.parameter_config is None:
            self.parameter_config = ParameterConfig()
        if self.complexity_config is None:
            self.complexity_config = ComplexityConfig()
        if self.exclusions is None:
            self.exclusions = self._default_exclusions()
    
    def _default_exclusions(self) -> List[str]:
        """Default exclusion patterns."""
        return [
            "test_*", "tests/", "*_test.py", "conftest.py",
            "deprecated/", "archive/", "experimental/",
            "__pycache__/", ".git/", "build/", "dist/",
            "*.egg-info/", "venv*/", "*env*/", "node_modules/",
        ]


class RefactoredConnascenceASTAnalyzer:
    """
    Refactored AST-based connascence analyzer using composition.
    
    Reduced from 597 lines to focused orchestration by delegating
    specific analysis to specialized analyzer classes.
    """
    
    def __init__(self, config: AnalyzerConfig = None):
        self.config = config or AnalyzerConfig()
        
        # Analysis state
        self.violations: List[Violation] = []
        self.file_stats: Dict[str, Dict[str, Any]] = {}
        self.current_file_path: str = ""
        self.current_source_lines: List[str] = []
        
        # Performance tracking
        self.analysis_start_time = 0.0
    
    def should_analyze_file(self, file_path: Path) -> bool:
        """Check if file should be analyzed based on exclusions."""
        path_str = str(file_path).replace("\\", "/")  # Normalize path separators
        
        for exclusion in self.config.exclusions:
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
    
    def analyze_file(self, file_path: Path) -> List[Violation]:
        """Analyze a single file using specialized analyzers."""
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
            
            # Delegate to specialized analyzers
            violations.extend(self._analyze_with_specialists(tree))
            
            # Collect file statistics
            self.file_stats[self.current_file_path] = self._calculate_file_stats(tree, violations)
            
        except (SyntaxError, UnicodeDecodeError) as e:
            # Create violation for unparseable files
            violation = self._create_syntax_error_violation(e)
            violations.append(violation)
            
        except Exception as e:
            logger.warning(f"Error analyzing {file_path}: {e}")
        
        return violations
    
    def _analyze_with_specialists(self, tree: ast.AST) -> List[Violation]:
        """Analyze using specialized analyzer classes."""
        all_violations = []
        
        # Magic Literal Analysis
        magic_analyzer = MagicLiteralAnalyzer(
            self.current_file_path, 
            self.current_source_lines,
            self.config.magic_literal_config
        )
        magic_violations = magic_analyzer.analyze(tree)
        all_violations.extend(self._convert_violations(magic_violations))
        
        # Parameter Analysis
        param_analyzer = ParameterAnalyzer(
            self.current_file_path,
            self.current_source_lines,
            self.config.parameter_config
        )
        param_violations = param_analyzer.analyze(tree)
        all_violations.extend(self._convert_violations(param_violations))
        
        # Complexity Analysis
        complexity_analyzer = ComplexityAnalyzer(
            self.current_file_path,
            self.current_source_lines,
            self.config.complexity_config
        )
        complexity_violations = complexity_analyzer.analyze(tree)
        all_violations.extend(self._convert_violations(complexity_violations))
        
        # Additional analyses (name, type, etc.) can be added here
        # by creating more specialized analyzers
        
        return all_violations
    
    def _convert_violations(self, violations: List[ConnascenceViolation]) -> List[Violation]:
        """Convert from ConnascenceViolation to enhanced Violation format."""
        converted = []
        
        for v in violations:
            converted.append(Violation(
                id="",
                type=v.type,
                severity=v.severity,
                file_path=v.file_path,
                line_number=v.line_number,
                column=v.column,
                description=v.description,
                recommendation=v.recommendation,
                code_snippet=v.code_snippet,
                context=v.context,
                weight=1.0,  # Can be calculated based on severity/type
                locality="same_module"  # Can be determined from context
            ))
        
        return converted
    
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
            summary_metrics=self._calculate_summary_metrics(all_violations)
        )
    
    def _create_syntax_error_violation(self, error: Exception) -> Violation:
        """Create violation for syntax errors."""
        return Violation(
            id="",
            type="syntax_error",
            severity="critical",
            file_path=self.current_file_path,
            line_number=getattr(error, "lineno", 1),
            column=getattr(error, "offset", 0) or 0,
            description=f"File cannot be parsed: {error}",
            recommendation="Fix syntax errors before analyzing connascence",
            context={"error_type": type(error).__name__, "error_message": str(error)}
        )
    
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
            type_key = violation.type
            severity_key = violation.severity
            
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
            type_key = violation.type
            metrics["violations_by_type"][type_key] = metrics["violations_by_type"].get(type_key, 0) + 1
            
            # By severity
            severity_key = violation.severity
            metrics["violations_by_severity"][severity_key] = metrics["violations_by_severity"].get(severity_key, 0) + 1
            
            # By locality
            locality_key = violation.locality
            metrics["violations_by_locality"][locality_key] = metrics["violations_by_locality"].get(locality_key, 0) + 1
        
        return metrics
    
    def generate_report(self, result: AnalysisResult, output_format: str = "text") -> str:
        """Generate analysis report."""
        if output_format == "json":
            return self._generate_json_report(result)
        else:
            return self._generate_text_report(result)
    
    def _generate_json_report(self, result: AnalysisResult) -> str:
        """Generate JSON format report."""
        import json
        return json.dumps(asdict(result), indent=2, default=str)
    
    def _generate_text_report(self, result: AnalysisResult) -> str:
        """Generate text format report."""
        lines = [
            "=" * 80,
            "CONNASCENCE ANALYSIS REPORT (Refactored Analyzer)",
            "=" * 80,
            f"Analysis completed: {result.timestamp}",
            f"Project root: {result.project_root}",
            f"Files analyzed: {result.total_files_analyzed}",
            f"Analysis duration: {result.analysis_duration_ms}ms",
            f"Total violations: {len(result.violations)}",
            "",
            "Summary by severity:"
        ]
        
        severity_counts = result.summary_metrics.get("violations_by_severity", {})
        for severity in ["critical", "high", "medium", "low"]:
            count = severity_counts.get(severity, 0)
            lines.append(f"  {severity.capitalize():10}: {count:3d}")
        
        lines.extend(["", "Summary by type:"])
        type_counts = result.summary_metrics.get("violations_by_type", {})
        for type_name, count in sorted(type_counts.items()):
            lines.append(f"  {type_name:30}: {count:3d}")
        
        # Detailed violations
        lines.extend(["", "=" * 80, "DETAILED VIOLATIONS", "=" * 80])
        
        for severity in ["critical", "high", "medium", "low"]:
            severity_violations = [v for v in result.violations if v.severity == severity]
            if severity_violations:
                lines.append(f"\n{severity.upper()} SEVERITY ({len(severity_violations)} violations)")
                lines.append("-" * 40)
                
                for v in severity_violations:
                    lines.extend([
                        f"\n{v.type}: {v.description}",
                        f"File: {v.file_path}:{v.line_number}:{v.column}",
                        f"Recommendation: {v.recommendation}"
                    ])
                    
                    if v.code_snippet:
                        lines.extend(["Code context:", v.code_snippet, ""])
        
        return "\n".join(lines)