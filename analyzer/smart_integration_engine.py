# SPDX-License-Identifier: MIT
# Smart integration engine for real connascence analysis

import ast
from pathlib import Path
from typing import List, Dict, Any, Optional

class SmartIntegrationEngine:
    """Smart integration engine for real connascence analysis."""
    
    def __init__(self):
        self.violations = []
        self.correlations = []
        self.recommendations = []
    
    def integrate(self, *args, **kwargs):
        """Legacy integration method for backward compatibility."""
        return []
    
    def analyze_correlations(self, findings, duplication_clusters, nasa_violations):
        """Analyze correlations between different analyzer findings."""
        correlations = []
        
        try:
            # Find correlations between connascence violations and duplications
            for cluster in duplication_clusters:
                related_violations = []
                for violation in findings:
                    if violation.get('file_path') in cluster.get('files_involved', []):
                        related_violations.append(violation)
                
                if related_violations:
                    correlations.append({
                        'analyzer1': 'connascence',
                        'analyzer2': 'duplication',
                        'correlation_score': 0.8,
                        'common_findings': related_violations,
                        'description': f"Duplication cluster correlates with {len(related_violations)} connascence violations"
                    })
            
            # Find correlations between NASA violations and connascence violations
            nasa_files = set(v.get('file_path', '') for v in nasa_violations)
            connascence_files = set(v.get('file_path', '') for v in findings)
            common_files = nasa_files.intersection(connascence_files)
            
            if common_files:
                correlations.append({
                    'analyzer1': 'nasa_compliance',
                    'analyzer2': 'connascence',
                    'correlation_score': len(common_files) / max(len(nasa_files), 1),
                    'common_findings': list(common_files),
                    'description': f"NASA violations and connascence violations overlap in {len(common_files)} files"
                })
                
        except Exception as e:
            print(f"Warning: Correlation analysis failed: {e}")
        
        return correlations
    
    def generate_intelligent_recommendations(self, findings, duplication_clusters, nasa_violations):
        """Generate intelligent recommendations based on analysis results."""
        recommendations = []
        
        try:
            # High-priority recommendations for critical violations
            critical_violations = [f for f in findings if f.get('severity') == 'critical']
            if critical_violations:
                recommendations.append({
                    'priority': 'high',
                    'category': 'critical_violations',
                    'description': f'Address {len(critical_violations)} critical connascence violations immediately',
                    'impact': 'High - critical violations can lead to system instability and maintenance issues',
                    'effort': 'high',
                    'suggested_actions': [
                        f"Review and refactor {v.get('file_path', 'unknown')} line {v.get('line_number', 0)}" 
                        for v in critical_violations[:3]
                    ]
                })
            
            # Duplication cluster recommendations
            high_similarity_clusters = [c for c in duplication_clusters if c.get('similarity_score', 0) >= 0.9]
            if high_similarity_clusters:
                recommendations.append({
                    'priority': 'high',
                    'category': 'code_duplication',
                    'description': f'Eliminate {len(high_similarity_clusters)} high-similarity duplication clusters',
                    'impact': 'High - code duplication increases maintenance burden and bug risk',
                    'effort': 'medium',
                    'suggested_actions': [
                        'Extract common functionality into shared modules',
                        'Use inheritance or composition patterns',
                        'Create utility functions for repeated code blocks'
                    ]
                })
            
            # NASA compliance recommendations
            if nasa_violations:
                recommendations.append({
                    'priority': 'medium',
                    'category': 'nasa_compliance',
                    'description': f'Improve NASA Power of Ten compliance ({len(nasa_violations)} violations)',
                    'impact': 'Medium - improves code safety and reliability',
                    'effort': 'medium',
                    'suggested_actions': [
                        'Limit function parameters to 6 or fewer',
                        'Reduce cyclomatic complexity',
                        'Limit nesting depth to 4 levels maximum',
                        'Replace goto statements with structured control flow'
                    ]
                })
            
            # General quality improvement
            if len(findings) > 10:
                recommendations.append({
                    'priority': 'medium',
                    'category': 'general_quality',
                    'description': 'Implement systematic code quality improvements',
                    'impact': 'Medium - gradual improvement in overall codebase quality',
                    'effort': 'low',
                    'suggested_actions': [
                        'Establish coding standards and review processes',
                        'Integrate automated quality checks in CI/CD',
                        'Schedule regular refactoring sessions',
                        'Set up code quality metrics tracking'
                    ]
                })
                
        except Exception as e:
            print(f"Warning: Recommendation generation failed: {e}")
        
        return recommendations
    
    def comprehensive_analysis(self, path: str, policy: str = "default") -> Dict[str, Any]:
        """Perform comprehensive analysis on real files."""
        path_obj = Path(path)
        violations = []
        
        if not path_obj.exists():
            return {
                'violations': [],
                'summary': {'total_violations': 0, 'critical_violations': 0},
                'nasa_compliance': {'score': 1.0, 'violations': [], 'passing': True}
            }
        
        # Analyze real files
        if path_obj.is_file() and path_obj.suffix == '.py':
            violations.extend(self._analyze_python_file(path_obj))
        elif path_obj.is_dir():
            # Recursively analyze Python files in directory
            for py_file in path_obj.rglob('*.py'):
                try:
                    violations.extend(self._analyze_python_file(py_file))
                except Exception as e:
                    print(f"Warning: Failed to analyze {py_file}: {e}")
        
        # Calculate summary
        critical_violations = len([v for v in violations if v.get('severity') == 'critical'])
        
        # Generate intelligent analysis
        duplication_clusters = []  # Placeholder for duplication detection
        nasa_violations = [v for v in violations if 'nasa' in v.get('rule_id', '').lower()]
        
        correlations = self.analyze_correlations(violations, duplication_clusters, nasa_violations)
        recommendations = self.generate_intelligent_recommendations(violations, duplication_clusters, nasa_violations)
        
        return {
            'violations': violations,
            'summary': {
                'total_violations': len(violations),
                'critical_violations': critical_violations
            },
            'nasa_compliance': {
                'score': 1.0 if critical_violations == 0 else 0.5,
                'violations': nasa_violations,
                'passing': critical_violations == 0
            },
            'correlations': correlations,
            'recommendations': recommendations,
            'quality_trends': [{
                'metric': 'overall_quality',
                'current': 0.8 if critical_violations == 0 else 0.5,
                'trend': 'stable',
                'projection': 0.8 if critical_violations == 0 else 0.5
            }],
            'risk_assessment': {
                'overall_risk': 'high' if critical_violations > 5 else 'medium' if critical_violations > 0 else 'low',
                'risk_factors': [
                    {
                        'factor': f'critical_violations',
                        'impact': critical_violations * 2,
                        'likelihood': 8 if critical_violations > 0 else 2,
                        'description': f'{critical_violations} critical violations found'
                    }
                ] if critical_violations > 0 else [],
                'mitigation': ['Address critical violations immediately', 'Implement code review process'] if critical_violations > 0 else []
            }
        }
    
    def _analyze_python_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Analyze a single Python file for real violations."""
        violations = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            # Parse AST
            tree = ast.parse(source)
            
            # Analyze for real violations
            for node in ast.walk(tree):
                # Check for God Objects (classes with too many methods)
                if isinstance(node, ast.ClassDef):
                    methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                    if len(methods) > 15:  # Threshold for God Object
                        violations.append({
                            'id': f'god_object_{node.name}',
                            'rule_id': 'god_object',
                            'type': 'god_object',
                            'severity': 'high',
                            'description': f'God Object detected: Class "{node.name}" has {len(methods)} methods (threshold: 15)',
                            'file_path': str(file_path),
                            'line_number': node.lineno,
                            'weight': 4.0
                        })
                    
                    # Check for classes with too many instance variables (Data Class smell)
                    instance_vars = []
                    for method in methods:
                        if method.name == '__init__':
                            for stmt in ast.walk(method):
                                if isinstance(stmt, ast.Assign):
                                    for target in stmt.targets:
                                        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                                            instance_vars.append(target.attr)
                    
                    unique_vars = list(set(instance_vars))
                    if len(unique_vars) > 10:  # Too many instance variables
                        violations.append({
                            'id': f'data_class_{node.name}',
                            'rule_id': 'data_class',
                            'type': 'data_class',
                            'severity': 'medium',
                            'description': f'Data Class smell: Class "{node.name}" has {len(unique_vars)} instance variables (threshold: 10)',
                            'file_path': str(file_path),
                            'line_number': node.lineno,
                            'weight': 2.5
                        })
                
                # Check for long parameter lists (Connascence of Position)
                if isinstance(node, ast.FunctionDef):
                    param_count = len(node.args.args)
                    if param_count > 6:  # NASA Rule: max 6 parameters
                        violations.append({
                            'id': f'parameter_bomb_{node.name}',
                            'rule_id': 'connascence_of_position',
                            'type': 'CoP',
                            'severity': 'medium',
                            'description': f'Function "{node.name}" has {param_count} parameters (NASA limit: 6)',
                            'file_path': str(file_path),
                            'line_number': node.lineno,
                            'weight': 2.0
                        })
                    
                    # Check for long functions (lines of code)
                    func_length = getattr(node, 'end_lineno', node.lineno + 10) - node.lineno
                    if func_length > 50:  # Function too long
                        violations.append({
                            'id': f'long_function_{node.name}',
                            'rule_id': 'long_function',
                            'type': 'long_function',
                            'severity': 'medium',
                            'description': f'Function "{node.name}" is {func_length} lines long (threshold: 50)',
                            'file_path': str(file_path),
                            'line_number': node.lineno,
                            'weight': 2.0
                        })
                    
                    # Check for cyclomatic complexity (nested if/for/while statements)
                    complexity = self._calculate_complexity(node)
                    if complexity > 10:  # McCabe complexity threshold
                        violations.append({
                            'id': f'high_complexity_{node.name}',
                            'rule_id': 'cyclomatic_complexity',
                            'type': 'complexity',
                            'severity': 'high',
                            'description': f'Function "{node.name}" has cyclomatic complexity {complexity} (threshold: 10)',
                            'file_path': str(file_path),
                            'line_number': node.lineno,
                            'weight': 3.0
                        })
                    
                    # Check for deep nesting
                    max_depth = self._calculate_nesting_depth(node)
                    if max_depth > 4:  # NASA Rule: max 4 levels of nesting
                        violations.append({
                            'id': f'deep_nesting_{node.name}',
                            'rule_id': 'deep_nesting',
                            'type': 'nesting',
                            'severity': 'high',
                            'description': f'Function "{node.name}" has {max_depth} levels of nesting (NASA limit: 4)',
                            'file_path': str(file_path),
                            'line_number': node.lineno,
                            'weight': 3.0
                        })
                
                # Check for magic literals (Connascence of Meaning) - ONLY meaningful ones
                if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                    # Skip common/acceptable numbers that aren't magic literals
                    acceptable_numbers = {0, 1, -1, 2, 10, 100, 1000}  # Common patterns
                    # Skip small integers (often array indices, basic math)
                    if node.value in acceptable_numbers or (isinstance(node.value, int) and abs(node.value) <= 10):
                        continue
                    # Skip obvious configuration values that should be constants (ports, timeouts, etc.)
                    if isinstance(node.value, int) and (node.value > 1000 or node.value in {80, 443, 8080, 3000, 5432, 6379, 27017}):
                        violations.append({
                            'id': f'config_magic_literal_{node.lineno}',
                            'rule_id': 'connascence_of_meaning',
                            'type': 'CoM',
                            'severity': 'medium',
                            'description': f'Configuration value "{node.value}" should be a named constant (likely port/timeout/limit)',
                            'file_path': str(file_path),
                            'line_number': node.lineno,
                            'weight': 2.0
                        })
                
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
        
        return violations
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate McCabe cyclomatic complexity."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.With, ast.AsyncWith)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # Add complexity for each boolean operator (and/or)
                complexity += len(child.values) - 1
        
        return complexity
    
    def _calculate_nesting_depth(self, node: ast.FunctionDef) -> int:
        """Calculate maximum nesting depth in a function."""
        def depth_visitor(node, current_depth=0):
            max_depth = current_depth
            
            for child in ast.iter_child_nodes(node):
                child_depth = current_depth
                if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.With, ast.AsyncWith, ast.Try)):
                    child_depth += 1
                
                nested_depth = depth_visitor(child, child_depth)
                max_depth = max(max_depth, nested_depth)
            
            return max_depth
        
        return depth_visitor(node)

__all__ = ["SmartIntegrationEngine"]
