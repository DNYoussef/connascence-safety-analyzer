"""
Radon integration for connascence analysis.

Integrates with Radon complexity analyzer to correlate complexity metrics
with Connascence of Algorithm (CoA) violations.
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, List, Any, Optional


class RadonIntegration:
    """Integration with Radon complexity analyzer."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.description = "Python code complexity analyzer"
        self._version_cache: Optional[str] = None
    
    def is_available(self) -> bool:
        """Check if Radon is available in the environment."""
        try:
            result = subprocess.run(['radon', '--version'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def get_version(self) -> str:
        """Get Radon version."""
        if self._version_cache:
            return self._version_cache
        
        try:
            result = subprocess.run(['radon', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self._version_cache = result.stdout.strip()
                return self._version_cache
        except FileNotFoundError:
            pass
        
        return "Not available"
    
    def analyze(self, project_path: Path) -> Dict[str, Any]:
        """Run Radon analysis on project."""
        if not self.is_available():
            raise RuntimeError("Radon is not available")
        
        results = {}
        
        # Run cyclomatic complexity analysis
        results['cyclomatic'] = self._analyze_cyclomatic_complexity(project_path)
        
        # Run maintainability index analysis
        results['maintainability'] = self._analyze_maintainability(project_path)
        
        # Run raw metrics analysis
        results['raw_metrics'] = self._analyze_raw_metrics(project_path)
        
        # Calculate summary statistics
        results['summary'] = self._calculate_summary(results)
        
        return results
    
    def _analyze_cyclomatic_complexity(self, project_path: Path) -> Dict[str, Any]:
        """Analyze cyclomatic complexity with Radon."""
        cmd = [
            'radon', 'cc', 
            str(project_path),
            '--json',
            '--average'
        ]
        
        # Add complexity threshold
        min_complexity = self.config.get('min_complexity', 'C')
        cmd.extend(['--min', min_complexity])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and result.stdout:
                try:
                    cc_data = json.loads(result.stdout)
                    return self._process_cyclomatic_data(cc_data)
                except json.JSONDecodeError:
                    return {'error': 'Failed to parse cyclomatic complexity JSON'}
            
            return {'error': f'Radon CC failed: {result.stderr}'}
            
        except subprocess.TimeoutExpired:
            return {'error': 'Radon cyclomatic complexity analysis timed out'}
        except Exception as e:
            return {'error': f'Radon CC analysis failed: {str(e)}'}
    
    def _analyze_maintainability(self, project_path: Path) -> Dict[str, Any]:
        """Analyze maintainability index with Radon."""
        cmd = [
            'radon', 'mi',
            str(project_path),
            '--json'
        ]
        
        # Add maintainability threshold
        min_mi = self.config.get('min_maintainability', 'B')
        cmd.extend(['--min', min_mi])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and result.stdout:
                try:
                    mi_data = json.loads(result.stdout)
                    return self._process_maintainability_data(mi_data)
                except json.JSONDecodeError:
                    return {'error': 'Failed to parse maintainability JSON'}
            
            return {'error': f'Radon MI failed: {result.stderr}'}
            
        except subprocess.TimeoutExpired:
            return {'error': 'Radon maintainability analysis timed out'}
        except Exception as e:
            return {'error': f'Radon MI analysis failed: {str(e)}'}
    
    def _analyze_raw_metrics(self, project_path: Path) -> Dict[str, Any]:
        """Analyze raw metrics with Radon."""
        cmd = [
            'radon', 'raw',
            str(project_path),
            '--json'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and result.stdout:
                try:
                    raw_data = json.loads(result.stdout)
                    return self._process_raw_metrics_data(raw_data)
                except json.JSONDecodeError:
                    return {'error': 'Failed to parse raw metrics JSON'}
            
            return {'error': f'Radon raw metrics failed: {result.stderr}'}
            
        except subprocess.TimeoutExpired:
            return {'error': 'Radon raw metrics analysis timed out'}
        except Exception as e:
            return {'error': f'Radon raw metrics analysis failed: {str(e)}'}
    
    def _process_cyclomatic_data(self, cc_data: Dict) -> Dict[str, Any]:
        """Process cyclomatic complexity data."""
        complex_functions = []
        total_complexity = 0
        function_count = 0
        
        complexity_grades = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0, 'F': 0}
        
        for file_path, file_data in cc_data.items():
            if isinstance(file_data, list):
                for item in file_data:
                    if item['type'] in ['function', 'method']:
                        complexity = item['complexity']
                        total_complexity += complexity
                        function_count += 1
                        
                        # Grade complexity
                        grade = self._get_complexity_grade(complexity)
                        complexity_grades[grade] += 1
                        
                        # Collect complex functions
                        if complexity >= self.config.get('complexity_threshold', 10):
                            complex_functions.append({
                                'file': file_path,
                                'name': item['name'],
                                'complexity': complexity,
                                'line': item['lineno'],
                                'grade': grade
                            })
        
        avg_complexity = total_complexity / function_count if function_count > 0 else 0
        
        return {
            'complex_functions': sorted(complex_functions, key=lambda x: x['complexity'], reverse=True),
            'average_complexity': avg_complexity,
            'total_functions': function_count,
            'complexity_grades': complexity_grades,
            'high_complexity_count': len([f for f in complex_functions if f['complexity'] >= 15])
        }
    
    def _process_maintainability_data(self, mi_data: Dict) -> Dict[str, Any]:
        """Process maintainability index data."""
        maintainability_scores = []
        low_maintainability_files = []
        
        for file_path, score in mi_data.items():
            maintainability_scores.append(score)
            
            # Flag low maintainability files
            if score < 10:  # Extremely low maintainability
                low_maintainability_files.append({
                    'file': file_path,
                    'score': score,
                    'grade': self._get_maintainability_grade(score)
                })
        
        avg_maintainability = sum(maintainability_scores) / len(maintainability_scores) if maintainability_scores else 0
        
        return {
            'average_maintainability': avg_maintainability,
            'low_maintainability_files': sorted(low_maintainability_files, key=lambda x: x['score']),
            'maintainability_distribution': self._calculate_maintainability_distribution(maintainability_scores),
            'files_analyzed': len(maintainability_scores)
        }
    
    def _process_raw_metrics_data(self, raw_data: Dict) -> Dict[str, Any]:
        """Process raw metrics data."""
        total_loc = 0
        total_lloc = 0
        total_sloc = 0
        total_comments = 0
        total_multi = 0
        total_blank = 0
        
        file_metrics = []
        
        for file_path, metrics in raw_data.items():
            loc = metrics.get('loc', 0)
            lloc = metrics.get('lloc', 0)
            sloc = metrics.get('sloc', 0)
            comments = metrics.get('comments', 0)
            multi = metrics.get('multi', 0)
            blank = metrics.get('blank', 0)
            
            total_loc += loc
            total_lloc += lloc
            total_sloc += sloc
            total_comments += comments
            total_multi += multi
            total_blank += blank
            
            # Calculate comment ratio
            comment_ratio = comments / loc if loc > 0 else 0
            
            file_metrics.append({
                'file': file_path,
                'loc': loc,
                'lloc': lloc,
                'sloc': sloc,
                'comments': comments,
                'comment_ratio': comment_ratio
            })
        
        # Calculate overall ratios
        comment_ratio = total_comments / total_loc if total_loc > 0 else 0
        
        return {
            'total_loc': total_loc,
            'total_logical_loc': total_lloc,
            'total_source_loc': total_sloc,
            'total_comments': total_comments,
            'comment_ratio': comment_ratio,
            'file_metrics': file_metrics,
            'large_files': [f for f in file_metrics if f['loc'] > 500],  # Files with > 500 LOC
            'files_analyzed': len(file_metrics)
        }
    
    def _calculate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary statistics across all analyses."""
        summary = {
            'overall_complexity_grade': 'Unknown',
            'maintainability_grade': 'Unknown',
            'code_quality_score': 0.0,
            'recommendations': []
        }
        
        # Complexity summary
        cc_data = results.get('cyclomatic', {})
        if 'average_complexity' in cc_data:
            avg_complexity = cc_data['average_complexity']
            summary['overall_complexity_grade'] = self._get_complexity_grade(avg_complexity)
            
            # Add recommendations based on complexity
            high_complexity = cc_data.get('high_complexity_count', 0)
            if high_complexity > 0:
                summary['recommendations'].append(
                    f"Refactor {high_complexity} functions with high complexity (>= 15)"
                )
        
        # Maintainability summary
        mi_data = results.get('maintainability', {})
        if 'average_maintainability' in mi_data:
            avg_maintainability = mi_data['average_maintainability']
            summary['maintainability_grade'] = self._get_maintainability_grade(avg_maintainability)
            
            # Add recommendations based on maintainability
            low_files = len(mi_data.get('low_maintainability_files', []))
            if low_files > 0:
                summary['recommendations'].append(
                    f"Improve maintainability of {low_files} files with low scores"
                )
        
        # Raw metrics summary
        raw_data = results.get('raw_metrics', {})
        if 'comment_ratio' in raw_data:
            comment_ratio = raw_data['comment_ratio']
            if comment_ratio < 0.1:  # Less than 10% comments
                summary['recommendations'].append(
                    f"Increase code documentation (current: {comment_ratio:.1%} comments)"
                )
        
        # Calculate overall code quality score (0-100)
        score_components = []
        
        if 'average_complexity' in cc_data:
            # Lower complexity = higher score
            complexity_score = max(0, 100 - (cc_data['average_complexity'] - 1) * 15)
            score_components.append(complexity_score * 0.4)  # 40% weight
        
        if 'average_maintainability' in mi_data:
            # Maintainability index is already 0-100
            score_components.append(mi_data['average_maintainability'] * 0.4)  # 40% weight
        
        if 'comment_ratio' in raw_data:
            # Good comment ratio (10-30%) gets full points
            comment_score = min(100, raw_data['comment_ratio'] * 500)  # Scale to 0-100
            score_components.append(comment_score * 0.2)  # 20% weight
        
        if score_components:
            summary['code_quality_score'] = sum(score_components) / (len(score_components))
        
        return summary
    
    def _get_complexity_grade(self, complexity: float) -> str:
        """Get letter grade for complexity."""
        if complexity <= 5:
            return 'A'
        elif complexity <= 10:
            return 'B'
        elif complexity <= 20:
            return 'C'
        elif complexity <= 30:
            return 'D'
        elif complexity <= 40:
            return 'E'
        else:
            return 'F'
    
    def _get_maintainability_grade(self, score: float) -> str:
        """Get letter grade for maintainability."""
        if score >= 85:
            return 'A'
        elif score >= 70:
            return 'B'
        elif score >= 50:
            return 'C'
        elif score >= 25:
            return 'D'
        elif score >= 10:
            return 'E'
        else:
            return 'F'
    
    def _calculate_maintainability_distribution(self, scores: List[float]) -> Dict[str, int]:
        """Calculate distribution of maintainability grades."""
        grades = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0, 'F': 0}
        
        for score in scores:
            grade = self._get_maintainability_grade(score)
            grades[grade] += 1
        
        return grades
    
    def correlate_with_connascence(self, radon_results: Dict[str, Any], 
                                 connascence_violations: List[Dict]) -> Dict[str, Any]:
        """Correlate Radon complexity metrics with connascence violations."""
        correlations = {
            'complexity_alignment': 0.0,
            'maintainability_connascence_relationship': 0.0,
            'shared_complex_files': [],
            'complexity_prediction_accuracy': 0.0
        }
        
        cc_data = radon_results.get('cyclomatic', {})
        mi_data = radon_results.get('maintainability', {})
        
        # Filter for CoA (Connascence of Algorithm) violations
        algorithm_violations = [v for v in connascence_violations 
                              if v.get('connascence_type') == 'CoA']
        
        # Complexity alignment
        complex_functions = cc_data.get('complex_functions', [])
        if complex_functions and algorithm_violations:
            # Check file overlap
            radon_complex_files = set(f['file'] for f in complex_functions)
            connascence_files = set(v.get('file_path', '') for v in algorithm_violations)
            
            shared_files = radon_complex_files.intersection(connascence_files)
            all_files = radon_complex_files.union(connascence_files)
            
            if all_files:
                correlations['complexity_alignment'] = len(shared_files) / len(all_files)
                correlations['shared_complex_files'] = list(shared_files)
        
        # Maintainability relationship
        low_maintainability_files = set(
            f['file'] for f in mi_data.get('low_maintainability_files', [])
        )
        violation_files = set(v.get('file_path', '') for v in connascence_violations)
        
        if low_maintainability_files and violation_files:
            overlap = len(low_maintainability_files.intersection(violation_files))
            correlations['maintainability_connascence_relationship'] = (
                overlap / len(low_maintainability_files.union(violation_files))
            )
        
        # Prediction accuracy (how well Radon predicts connascence issues)
        if complex_functions:
            # Count how many complex functions have connascence violations
            complex_files_with_violations = len([
                f for f in complex_functions 
                if f['file'] in violation_files
            ])
            
            correlations['complexity_prediction_accuracy'] = (
                complex_files_with_violations / len(complex_functions)
            )
        
        return correlations
    
    def suggest_refactoring_targets(self, radon_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest specific refactoring targets based on Radon analysis."""
        targets = []
        
        cc_data = radon_results.get('cyclomatic', {})
        mi_data = radon_results.get('maintainability', {})
        raw_data = radon_results.get('raw_metrics', {})
        
        # High complexity functions
        complex_functions = cc_data.get('complex_functions', [])
        for func in complex_functions[:5]:  # Top 5 most complex
            targets.append({
                'type': 'function_complexity',
                'file': func['file'],
                'function': func['name'],
                'line': func['line'],
                'complexity': func['complexity'],
                'priority': 'high' if func['complexity'] >= 20 else 'medium',
                'suggestion': f"Break down function '{func['name']}' (complexity: {func['complexity']})"
            })
        
        # Low maintainability files
        low_maintainability = mi_data.get('low_maintainability_files', [])
        for file_info in low_maintainability[:3]:  # Top 3 worst files
            targets.append({
                'type': 'file_maintainability',
                'file': file_info['file'],
                'score': file_info['score'],
                'grade': file_info['grade'],
                'priority': 'high' if file_info['score'] < 10 else 'medium',
                'suggestion': f"Refactor file for better maintainability (score: {file_info['score']:.1f})"
            })
        
        # Large files
        large_files = raw_data.get('large_files', [])
        for file_info in large_files[:3]:  # Top 3 largest files
            targets.append({
                'type': 'file_size',
                'file': file_info['file'],
                'loc': file_info['loc'],
                'priority': 'medium',
                'suggestion': f"Consider splitting large file ({file_info['loc']} lines)"
            })
        
        # Sort by priority
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        targets.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
        
        return targets