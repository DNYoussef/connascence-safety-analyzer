"""
Analyzer Orchestrator - Coordinates all specialized analyzers
Replaces the original monolithic ConnascenceASTAnalyzer class.
"""

import ast
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..thresholds import (
    ThresholdConfig, WeightConfig, PolicyPreset, ConnascenceType, Severity,
    DEFAULT_THRESHOLDS, DEFAULT_WEIGHTS,
    calculate_violation_weight
)
from .base_analyzer import BaseConnascenceAnalyzer
from .violations import Violation, AnalysisResult
from .position_analyzer import PositionAnalyzer
from .meaning_analyzer import MeaningAnalyzer
from .algorithm_analyzer import AlgorithmAnalyzer
from .god_object_analyzer import GodObjectAnalyzer
from .multi_language_analyzer import MultiLanguageAnalyzer

logger = logging.getLogger(__name__)


class AnalyzerOrchestrator(BaseConnascenceAnalyzer):
    """Orchestrates multiple specialized analyzers to perform comprehensive connascence analysis."""
    
    def __init__(
        self, 
        thresholds: Optional[ThresholdConfig] = None,
        weights: Optional[WeightConfig] = None,
        policy_preset: Optional[PolicyPreset] = None,
        exclusions: Optional[List[str]] = None
    ):
        super().__init__(thresholds, weights, policy_preset, exclusions)
        
        # Initialize specialized analyzers
        self.position_analyzer = PositionAnalyzer(thresholds, weights, policy_preset, exclusions)
        self.meaning_analyzer = MeaningAnalyzer(thresholds, weights, policy_preset, exclusions)
        self.algorithm_analyzer = AlgorithmAnalyzer(thresholds, weights, policy_preset, exclusions)
        self.god_object_analyzer = GodObjectAnalyzer(thresholds, weights, policy_preset, exclusions)
        self.multi_language_analyzer = MultiLanguageAnalyzer(thresholds, weights, policy_preset, exclusions)
    
    def analyze_string(self, source_code: str, filename: str = "string_input.py") -> List[Violation]:
        """Analyze source code string for connascence violations."""
        self.current_file_path = filename
        violations = []
        
        try:
            if not source_code.strip():  # Skip empty code
                return []
            
            self.current_source_lines = source_code.splitlines()
            tree = ast.parse(source_code, filename=filename)
            
            # Run all analysis passes using specialized analyzers
            violations.extend(self._run_all_analyzers(tree))
            
            # Calculate weights and finalize violations
            for violation in violations:
                violation.weight = calculate_violation_weight(
                    violation.type, violation.severity, violation.locality,
                    self.current_file_path, self.weights
                )
            
            # Collect file statistics
            self.file_stats[self.current_file_path] = self.calculate_file_stats(
                tree, violations
            )
            
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
            # Determine if this is a Python file or needs multi-language analysis
            file_extension = file_path.suffix.lower()
            
            if file_extension == '.py':
                # Use Python AST analysis
                with open(file_path, encoding="utf-8", errors="ignore") as f:
                    source = f.read()
                    self.current_source_lines = source.splitlines()
                
                if not source.strip():  # Skip empty files
                    return []
                
                tree = ast.parse(source, filename=str(file_path))
                
                # Run all analysis passes using specialized analyzers
                violations.extend(self._run_all_analyzers(tree))
                
                # Collect file statistics for Python files
                self.file_stats[self.current_file_path] = self.calculate_file_stats(
                    tree, violations
                )
                
            else:
                # Use multi-language analyzer for non-Python files
                violations.extend(self.multi_language_analyzer.analyze_file(file_path))
                # Sync state from multi-language analyzer
                self.current_source_lines = self.multi_language_analyzer.current_source_lines
                
                # Collect basic file statistics for non-Python files
                self.file_stats[self.current_file_path] = {
                    "total_lines": len(self.current_source_lines),
                    "language": self.multi_language_analyzer.detect_language(file_path),
                    "violations_count": len(violations)
                }
            
            # Calculate weights and finalize violations for all file types
            for violation in violations:
                violation.weight = calculate_violation_weight(
                    violation.type, violation.severity, violation.locality,
                    self.current_file_path, self.weights
                )
            
        except (SyntaxError, UnicodeDecodeError) as e:
            # Create violation for unparseable files
            violation = Violation(
                id="",
                type=ConnascenceType.NAME,
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
        """Analyze all supported files in a directory tree."""
        self.analysis_start_time = time.time()
        all_violations = []
        files_analyzed = 0
        
        # Supported file extensions
        supported_extensions = ['.py', '.c', '.cpp', '.cxx', '.cc', '.h', '.hpp', '.hxx', '.js', '.mjs', '.ts']
        
        # Find all supported files
        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                if self.should_analyze_file(file_path):
                    file_violations = self.analyze_file(file_path)
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
            summary_metrics=self.calculate_summary_metrics(all_violations),
            policy_preset=self.policy_preset.name if self.policy_preset else None,
        )
    
    def _run_all_analyzers(self, tree: ast.AST) -> List[Violation]:
        """Run all specialized analyzers and collect violations."""
        violations = []
        
        # Sync current file state to all analyzers
        self._sync_analyzers_state()
        
        # Position analysis
        violations.extend(self.position_analyzer.analyze_position_connascence(tree))
        
        # Meaning/Name/Type analysis
        violations.extend(self.meaning_analyzer.analyze_meaning_connascence(tree))
        violations.extend(self.meaning_analyzer.analyze_name_connascence(tree))
        violations.extend(self.meaning_analyzer.analyze_type_connascence(tree))
        
        # Algorithm analysis (includes execution, value, timing, identity)
        violations.extend(self.algorithm_analyzer.analyze_algorithm_connascence(tree))
        violations.extend(self.algorithm_analyzer.analyze_execution_connascence(tree))
        violations.extend(self.algorithm_analyzer.analyze_value_connascence(tree))
        violations.extend(self.algorithm_analyzer.analyze_timing_connascence(tree))
        violations.extend(self.algorithm_analyzer.analyze_identity_connascence(tree))
        
        # God Object analysis
        violations.extend(self.god_object_analyzer.analyze_god_objects(tree))
        violations.extend(self.god_object_analyzer.analyze_large_functions(tree))
        violations.extend(self.god_object_analyzer.analyze_module_size(tree, len(self.current_source_lines)))
        
        return violations
    
    def _sync_analyzers_state(self):
        """Synchronize current file state to all specialized analyzers."""
        analyzers = [
            self.position_analyzer,
            self.meaning_analyzer, 
            self.algorithm_analyzer,
            self.god_object_analyzer
        ]
        
        for analyzer in analyzers:
            analyzer.current_file_path = self.current_file_path
            analyzer.current_source_lines = self.current_source_lines