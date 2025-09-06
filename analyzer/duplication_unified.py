#!/usr/bin/env python3
"""
Unified Duplication Analyzer
============================

Combines both MECE similarity clustering and standard CoA detection for comprehensive
duplication analysis. Provides enterprise-grade duplicate code detection with:

- Function-level similarity analysis (MECE approach)
- Algorithm pattern duplication (CoA approach) 
- Cross-file and intra-file duplicate detection
- Unified scoring system (0.0-1.0 scale)
- Actionable remediation recommendations
"""

import ast
import hashlib
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Optional

# Import both existing analyzers
try:
    from .dup_detection.mece_analyzer import MECEAnalyzer, CodeBlock, DuplicationCluster
    from .check_connascence import ConnascenceDetector
    from .constants import MECE_SIMILARITY_THRESHOLD, MECE_CLUSTER_MIN_SIZE
except ImportError:
    # Fallback for script execution
    sys.path.append(str(Path(__file__).parent))
    from dup_detection.mece_analyzer import MECEAnalyzer, CodeBlock, DuplicationCluster
    from check_connascence import ConnascenceDetector
    from constants import MECE_SIMILARITY_THRESHOLD, MECE_CLUSTER_MIN_SIZE


@dataclass
class DuplicationViolation:
    """Unified duplication violation combining both analysis approaches."""
    violation_id: str
    type: str  # 'function_similarity', 'algorithm_duplication', 'structural_clone'
    severity: str  # 'critical', 'high', 'medium', 'low'
    description: str
    files_involved: List[str]
    similarity_score: float  # 0.0-1.0
    line_ranges: List[Dict[str, Any]]  # [{"file": "path", "start": 10, "end": 20}]
    recommendation: str
    context: Dict[str, Any]


@dataclass 
class UnifiedDuplicationResult:
    """Complete duplication analysis result."""
    success: bool
    path: str
    analysis_type: str = "unified_duplication"
    total_violations: int = 0
    similarity_violations: List[DuplicationViolation] = None
    algorithm_violations: List[DuplicationViolation] = None
    overall_duplication_score: float = 1.0  # Higher is better (less duplication)
    summary: Dict[str, Any] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.similarity_violations is None:
            self.similarity_violations = []
        if self.algorithm_violations is None:
            self.algorithm_violations = []
        if self.summary is None:
            self.summary = {}


class UnifiedDuplicationAnalyzer:
    """Unified analyzer combining MECE and CoA duplication detection."""
    
    def __init__(self, similarity_threshold: float = MECE_SIMILARITY_THRESHOLD):
        self.similarity_threshold = similarity_threshold
        self.min_cluster_size = MECE_CLUSTER_MIN_SIZE
        self.min_function_lines = 3
        
        # Initialize component analyzers
        self.mece_analyzer = MECEAnalyzer(threshold=similarity_threshold)
        
        # Algorithm tracking for CoA detection
        self.function_hashes = defaultdict(list)
        self.processed_files = set()
        
    def analyze_path(self, path: str, comprehensive: bool = True) -> UnifiedDuplicationResult:
        """Run comprehensive unified duplication analysis."""
        path_obj = Path(path)
        
        if not path_obj.exists():
            return UnifiedDuplicationResult(
                success=False,
                path=str(path),
                error=f"Path does not exist: {path}"
            )
        
        try:
            # Phase 1: MECE similarity analysis
            similarity_violations = self._run_similarity_analysis(path_obj)
            
            # Phase 2: Algorithm duplication analysis (CoA)
            algorithm_violations = self._run_algorithm_analysis(path_obj)
            
            # Phase 3: Calculate unified duplication score
            overall_score = self._calculate_unified_score(
                similarity_violations, algorithm_violations, path_obj
            )
            
            # Phase 4: Generate summary
            summary = self._generate_summary(similarity_violations, algorithm_violations)
            
            return UnifiedDuplicationResult(
                success=True,
                path=str(path),
                total_violations=len(similarity_violations) + len(algorithm_violations),
                similarity_violations=similarity_violations,
                algorithm_violations=algorithm_violations,
                overall_duplication_score=overall_score,
                summary=summary
            )
            
        except Exception as e:
            return UnifiedDuplicationResult(
                success=False,
                path=str(path),
                error=f"Analysis error: {str(e)}"
            )
    
    def _run_similarity_analysis(self, path_obj: Path) -> List[DuplicationViolation]:
        """Run MECE similarity-based analysis."""
        violations = []
        
        # Use MECE analyzer for similarity clustering
        mece_result = self.mece_analyzer.analyze_path(str(path_obj), comprehensive=True)
        
        if not mece_result.get('success', False):
            return violations
        
        # Convert MECE clusters to unified violations
        for i, cluster_data in enumerate(mece_result.get('duplications', []), 1):
            violation_id = f"SIM-{i:03d}"
            
            # Determine severity based on similarity score and block count
            similarity = cluster_data.get('similarity_score', 0.0)
            block_count = cluster_data.get('block_count', 0)
            
            if similarity > 0.9 and block_count >= 3:
                severity = 'critical'
            elif similarity > 0.8 and block_count >= 2:
                severity = 'high'
            elif similarity > 0.7:
                severity = 'medium'
            else:
                severity = 'low'
            
            # Extract line ranges
            line_ranges = []
            for block in cluster_data.get('blocks', []):
                line_ranges.append({
                    'file': block['file_path'],
                    'start': block['start_line'],
                    'end': block['end_line'],
                    'lines': block.get('lines', [])
                })
            
            violation = DuplicationViolation(
                violation_id=violation_id,
                type='function_similarity',
                severity=severity,
                description=f"Found {block_count} similar functions with {similarity:.1%} similarity",
                files_involved=cluster_data.get('files_involved', []),
                similarity_score=similarity,
                line_ranges=line_ranges,
                recommendation=self._get_similarity_recommendation(similarity, block_count),
                context={
                    'cluster_id': cluster_data.get('id', ''),
                    'analysis_method': 'mece_similarity',
                    'block_count': block_count
                }
            )
            
            violations.append(violation)
        
        return violations
    
    def _run_algorithm_analysis(self, path_obj: Path) -> List[DuplicationViolation]:
        """Run CoA algorithm duplication analysis.""" 
        violations = []
        self.function_hashes.clear()
        
        # Collect all Python files
        python_files = []
        if path_obj.is_file() and path_obj.suffix == '.py':
            python_files = [path_obj]
        elif path_obj.is_dir():
            python_files = [f for f in path_obj.rglob('*.py') 
                          if self._should_analyze_file(f)]
        
        # Process each file for algorithm patterns
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    source_lines = content.splitlines()
                
                tree = ast.parse(content)
                self._extract_algorithm_patterns(tree, str(file_path), source_lines)
                
            except (SyntaxError, UnicodeDecodeError, OSError) as e:
                print(f"Warning: Could not analyze {file_path}: {e}")
                continue
        
        # Find algorithm duplications
        violation_id = 1
        for pattern_hash, functions in self.function_hashes.items():
            if len(functions) >= 2:  # Found duplicates
                
                # Calculate algorithm similarity
                avg_similarity = self._calculate_algorithm_similarity(functions)
                
                # Determine severity
                if len(functions) >= 4:
                    severity = 'critical'
                elif len(functions) >= 3:
                    severity = 'high'
                else:
                    severity = 'medium'
                
                # Build violation
                files_involved = list(set(f[0] for f in functions))
                line_ranges = []
                
                for file_path, func_node, _ in functions:
                    line_ranges.append({
                        'file': file_path,
                        'start': func_node.lineno,
                        'end': getattr(func_node, 'end_lineno', func_node.lineno + 10),
                        'function_name': func_node.name
                    })
                
                violation = DuplicationViolation(
                    violation_id=f"COA-{violation_id:03d}",
                    type='algorithm_duplication',
                    severity=severity,
                    description=f"Found {len(functions)} functions with identical algorithm patterns",
                    files_involved=files_involved,
                    similarity_score=avg_similarity,
                    line_ranges=line_ranges,
                    recommendation=self._get_algorithm_recommendation(len(functions)),
                    context={
                        'pattern_hash': pattern_hash[:16],
                        'function_count': len(functions),
                        'analysis_method': 'coa_algorithm',
                        'functions': [f[1].name for f in functions]
                    }
                )
                
                violations.append(violation)
                violation_id += 1
        
        return violations
    
    def _extract_algorithm_patterns(self, tree: ast.AST, file_path: str, source_lines: List[str]):
        """Extract algorithm patterns from AST for CoA detection."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if len(node.body) >= self.min_function_lines:
                    # Create normalized algorithm pattern
                    pattern = self._normalize_algorithm_pattern(node)
                    pattern_hash = hashlib.md5(pattern.encode()).hexdigest()
                    
                    self.function_hashes[pattern_hash].append((file_path, node, source_lines))
    
    def _normalize_algorithm_pattern(self, func_node: ast.FunctionDef) -> str:
        """Create normalized algorithm pattern for comparison."""
        patterns = []
        
        for stmt in func_node.body:
            if isinstance(stmt, ast.Return):
                if stmt.value:
                    patterns.append(f"return_{type(stmt.value).__name__}")
                else:
                    patterns.append("return_none")
            elif isinstance(stmt, ast.If):
                patterns.append("conditional")
            elif isinstance(stmt, ast.For):
                patterns.append("loop_for")
            elif isinstance(stmt, ast.While):
                patterns.append("loop_while")
            elif isinstance(stmt, ast.Assign):
                if len(stmt.targets) == 1:
                    patterns.append("assign_single")
                else:
                    patterns.append("assign_multiple")
            elif isinstance(stmt, ast.Expr):
                if isinstance(stmt.value, ast.Call):
                    patterns.append("call")
                else:
                    patterns.append("expression")
            elif isinstance(stmt, ast.Try):
                patterns.append("exception_handling")
            elif isinstance(stmt, ast.With):
                patterns.append("context_manager")
        
        return "|".join(patterns)
    
    def _calculate_algorithm_similarity(self, functions: List[Tuple[str, ast.FunctionDef, List[str]]]) -> float:
        """Calculate average algorithm similarity for functions with same pattern."""
        # Since they have the same normalized pattern hash, similarity is high
        # Adjust based on additional factors like parameter count, complexity
        
        base_similarity = 0.85  # High base similarity for same algorithm pattern
        
        # Check parameter count consistency
        param_counts = [len(f[1].args.args) for f in functions]
        if len(set(param_counts)) == 1:
            base_similarity += 0.1  # Bonus for consistent parameter counts
        
        return min(1.0, base_similarity)
    
    def _calculate_unified_score(self, similarity_violations: List[DuplicationViolation], 
                               algorithm_violations: List[DuplicationViolation], 
                               path_obj: Path) -> float:
        """Calculate unified duplication score (higher is better)."""
        
        # Count total Python files for baseline
        python_files = []
        if path_obj.is_file():
            python_files = [path_obj]
        else:
            python_files = [f for f in path_obj.rglob('*.py') if self._should_analyze_file(f)]
        
        total_files = len(python_files)
        if total_files == 0:
            return 1.0
        
        # Calculate penalty based on violations
        similarity_penalty = sum(v.similarity_score for v in similarity_violations) / total_files
        algorithm_penalty = len(algorithm_violations) * 0.1
        
        # Base score starts at 1.0 (perfect)
        base_score = 1.0
        total_penalty = (similarity_penalty + algorithm_penalty) * 0.5
        
        final_score = max(0.0, base_score - total_penalty)
        return round(final_score, 3)
    
    def _generate_summary(self, similarity_violations: List[DuplicationViolation],
                         algorithm_violations: List[DuplicationViolation]) -> Dict[str, Any]:
        """Generate comprehensive summary of duplication analysis."""
        
        # Count by severity
        all_violations = similarity_violations + algorithm_violations
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for violation in all_violations:
            severity_counts[violation.severity] += 1
        
        # Calculate average similarity scores
        if similarity_violations:
            avg_similarity = sum(v.similarity_score for v in similarity_violations) / len(similarity_violations)
        else:
            avg_similarity = 0.0
        
        return {
            'total_violations': len(all_violations),
            'similarity_duplications': len(similarity_violations),
            'algorithm_duplications': len(algorithm_violations),
            'severity_breakdown': severity_counts,
            'average_similarity_score': round(avg_similarity, 3),
            'files_with_duplications': len(set(
                file for violation in all_violations
                for file in violation.files_involved
            )),
            'recommendation_priority': self._get_priority_recommendation(all_violations)
        }
    
    def _get_similarity_recommendation(self, similarity: float, block_count: int) -> str:
        """Get recommendation for similarity-based duplications."""
        if similarity > 0.9:
            return "Critical: Extract common functionality into shared utility functions or base classes"
        elif similarity > 0.8:
            return "High: Consider creating a common interface or abstract base class"
        elif similarity > 0.7:
            return "Medium: Review for potential refactoring opportunities"
        else:
            return "Low: Monitor for future refactoring opportunities"
    
    def _get_algorithm_recommendation(self, function_count: int) -> str:
        """Get recommendation for algorithm duplications."""
        if function_count >= 4:
            return "Critical: Immediately extract common algorithm into utility function"
        elif function_count >= 3:
            return "High: Extract algorithm pattern into reusable component"
        else:
            return "Medium: Consider creating shared algorithm implementation"
    
    def _get_priority_recommendation(self, violations: List[DuplicationViolation]) -> str:
        """Get overall priority recommendation."""
        critical_count = sum(1 for v in violations if v.severity == 'critical')
        high_count = sum(1 for v in violations if v.severity == 'high')
        
        if critical_count > 0:
            return f"Address {critical_count} critical duplication(s) immediately"
        elif high_count > 0:
            return f"Address {high_count} high-priority duplication(s) in next sprint"
        elif violations:
            return "Schedule refactoring review for medium/low priority duplications"
        else:
            return "No significant duplications detected - maintain current code quality"
    
    def _should_analyze_file(self, file_path: Path) -> bool:
        """Check if file should be analyzed."""
        skip_patterns = ['__pycache__', '.git', '.pytest_cache', 'test_', '_test.py', 
                        'conftest.py', '.pyc', 'migrations', 'node_modules']
        
        path_str = str(file_path)
        return not any(pattern in path_str for pattern in skip_patterns)
    
    def export_results(self, result: UnifiedDuplicationResult, output_file: Optional[str] = None) -> str:
        """Export results to JSON format."""
        # Convert dataclasses to dictionaries
        export_data = {
            'analysis_type': 'unified_duplication',
            'success': result.success,
            'path': result.path,
            'total_violations': result.total_violations,
            'overall_duplication_score': result.overall_duplication_score,
            'summary': result.summary,
            'violations': {
                'similarity_violations': [asdict(v) for v in result.similarity_violations],
                'algorithm_violations': [asdict(v) for v in result.algorithm_violations]
            }
        }
        
        if result.error:
            export_data['error'] = result.error
        
        json_output = json.dumps(export_data, indent=2, ensure_ascii=True)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_output)
            return f"Results exported to {output_file}"
        
        return json_output


def main():
    """Command-line interface for unified duplication analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Unified duplication analyzer")
    parser.add_argument('--path', required=True, help='Path to analyze')
    parser.add_argument('--threshold', type=float, default=MECE_SIMILARITY_THRESHOLD, 
                       help='Similarity threshold (0.0-1.0)')
    parser.add_argument('--output', help='Output JSON file')
    parser.add_argument('--comprehensive', action='store_true', help='Run comprehensive analysis')
    
    args = parser.parse_args()
    
    try:
        analyzer = UnifiedDuplicationAnalyzer(similarity_threshold=args.threshold)
        result = analyzer.analyze_path(args.path, comprehensive=args.comprehensive)
        
        output = analyzer.export_results(result, args.output)
        
        if not args.output:
            print(output)
        
        return 0 if result.success else 1
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())