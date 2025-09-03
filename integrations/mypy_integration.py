"""
MyPy integration for connascence analysis.

Integrates with MyPy static type checker to correlate type issues
with Connascence of Type (CoT) violations.
"""

import subprocess
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional


class MyPyIntegration:
    """Integration with MyPy static type checker."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.description = "Static type checker for Python"
        self._version_cache: Optional[str] = None
    
    def is_available(self) -> bool:
        """Check if MyPy is available in the environment."""
        try:
            result = subprocess.run(['mypy', '--version'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def get_version(self) -> str:
        """Get MyPy version."""
        if self._version_cache:
            return self._version_cache
        
        try:
            result = subprocess.run(['mypy', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                # Parse version from "mypy 1.5.1 (compiled: yes)"
                version_match = re.search(r'mypy (\\d+\\.\\d+\\.\\d+)', result.stdout)
                if version_match:
                    self._version_cache = version_match.group(1)
                else:
                    self._version_cache = result.stdout.strip()
                return self._version_cache
        except FileNotFoundError:
            pass
        
        return "Not available"
    
    def analyze(self, project_path: Path) -> Dict[str, Any]:
        """Run MyPy analysis on project."""
        if not self.is_available():
            raise RuntimeError("MyPy is not available")
        
        # Build MyPy command
        cmd = [
            'mypy',
            str(project_path),
            '--show-error-codes',
            '--show-column-numbers',
            '--no-error-summary'
        ]
        
        # Add configuration options
        if self.config.get('config_file'):
            cmd.extend(['--config-file', str(self.config['config_file'])])
        else:
            # Default strict-ish settings
            cmd.extend([
                '--ignore-missing-imports',
                '--follow-imports=silent',
                '--show-error-context'
            ])
        
        # Add strictness options
        if self.config.get('strict', False):
            cmd.append('--strict')
        elif self.config.get('strict_optional', True):
            cmd.append('--strict-optional')
        
        # Disable incremental mode for consistent results
        cmd.extend(['--no-incremental', '--cache-dir=/tmp/mypy_cache'])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            # Parse MyPy output
            errors = self._parse_mypy_output(result.stdout)
            
            # Categorize errors
            categorized = self._categorize_errors(errors)
            
            # Calculate statistics
            stats = self._calculate_statistics(errors)
            
            return {
                'errors': errors,
                'categories': categorized,
                'statistics': stats,
                'error_count': len(errors),
                'execution_successful': True,  # MyPy always succeeds, errors are in output
                'exit_code': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("MyPy analysis timed out")
        except Exception as e:
            raise RuntimeError(f"MyPy analysis failed: {str(e)}")
    
    def _parse_mypy_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse MyPy text output into structured errors."""
        errors = []
        
        for line in output.strip().split('\\n'):
            if not line.strip():
                continue
            
            # Parse MyPy output format: file:line:column: error: message [error-code]
            # Example: src/main.py:15:23: error: Argument 1 to "foo" has incompatible type "str"; expected "int"  [arg-type]
            match = re.match(
                r'^([^:]+):(\\d+):(\\d+): (error|warning|note): (.+?)(?:\\s+\\[([^\\]]+)\\])?$',
                line
            )
            
            if match:
                file_path, line_num, col_num, severity, message, error_code = match.groups()
                
                errors.append({
                    'file': file_path,
                    'line': int(line_num),
                    'column': int(col_num),
                    'severity': severity,
                    'message': message.strip(),
                    'error_code': error_code or 'unknown',
                    'raw_line': line
                })
        
        return errors
    
    def _categorize_errors(self, errors: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize MyPy errors by type."""
        categories = {
            'missing_type_hints': [],
            'incompatible_types': [],
            'undefined_variables': [],
            'attribute_errors': [],
            'import_errors': [],
            'call_errors': [],
            'return_type_errors': [],
            'other': []
        }
        
        for error in errors:
            error_code = error.get('error_code', '')
            message = error.get('message', '').lower()
            
            # Categorize by error code
            if error_code in ['var-annotated', 'no-untyped-def', 'no-untyped-call']:
                categories['missing_type_hints'].append(error)
            elif error_code in ['arg-type', 'assignment', 'return-value']:
                categories['incompatible_types'].append(error)
            elif error_code in ['name-defined', 'attr-defined']:
                if 'attribute' in message:
                    categories['attribute_errors'].append(error)
                else:
                    categories['undefined_variables'].append(error)
            elif error_code in ['import', 'import-untyped']:
                categories['import_errors'].append(error)
            elif error_code in ['call-arg', 'call-overload', 'operator']:
                categories['call_errors'].append(error)
            elif error_code in ['return-value', 'return']:
                categories['return_type_errors'].append(error)
            else:
                # Categorize by message content
                if any(keyword in message for keyword in ['type hint', 'annotation', 'untyped']):
                    categories['missing_type_hints'].append(error)
                elif any(keyword in message for keyword in ['incompatible', 'expected']):
                    categories['incompatible_types'].append(error)
                elif 'import' in message:
                    categories['import_errors'].append(error)
                else:
                    categories['other'].append(error)
        
        return categories
    
    def _calculate_statistics(self, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics from MyPy errors."""
        if not errors:
            return {
                'total_errors': 0,
                'files_with_errors': 0,
                'avg_errors_per_file': 0.0,
                'severity_breakdown': {},
                'error_code_frequency': {}
            }
        
        # Count errors by file
        files_with_errors = set()
        severity_counts = {}
        error_code_counts = {}
        
        for error in errors:
            file_path = error.get('file', '')
            if file_path:
                files_with_errors.add(file_path)
            
            severity = error.get('severity', 'unknown')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            error_code = error.get('error_code', 'unknown')
            error_code_counts[error_code] = error_code_counts.get(error_code, 0) + 1
        
        return {
            'total_errors': len(errors),
            'files_with_errors': len(files_with_errors),
            'avg_errors_per_file': len(errors) / len(files_with_errors) if files_with_errors else 0.0,
            'severity_breakdown': severity_counts,
            'error_code_frequency': dict(sorted(error_code_counts.items(), 
                                               key=lambda x: x[1], reverse=True))
        }
    
    def correlate_with_connascence(self, mypy_results: Dict[str, Any], 
                                 connascence_violations: List[Dict]) -> Dict[str, Any]:
        """Correlate MyPy errors with connascence violations."""
        correlations = {
            'type_safety_coverage': 0.0,
            'annotation_completeness': 0.0,
            'type_connascence_overlap': 0.0,
            'shared_problem_files': []
        }
        
        mypy_errors = mypy_results.get('errors', [])
        categories = mypy_results.get('categories', {})
        
        # Filter for CoT (Connascence of Type) violations
        type_violations = [v for v in connascence_violations 
                          if v.get('connascence_type') == 'CoT']
        
        if not mypy_errors and not type_violations:
            correlations['type_safety_coverage'] = 1.0
            correlations['annotation_completeness'] = 1.0
            return correlations
        
        # Calculate file overlap
        mypy_files = set(error.get('file', '') for error in mypy_errors)
        violation_files = set(v.get('file_path', '') for v in type_violations)
        
        shared_files = mypy_files.intersection(violation_files)
        all_files = mypy_files.union(violation_files)
        
        if all_files:
            correlations['type_connascence_overlap'] = len(shared_files) / len(all_files)
        
        # List shared problem files
        correlations['shared_problem_files'] = list(shared_files)
        
        # Type safety coverage (inverse of missing type annotations)
        missing_annotations = len(categories.get('missing_type_hints', []))
        total_type_issues = len(type_violations) + missing_annotations
        
        if total_type_issues > 0:
            # Higher overlap means better detection coverage
            correlations['type_safety_coverage'] = len(shared_files) / len(all_files) if all_files else 0.0
        else:
            correlations['type_safety_coverage'] = 1.0
        
        # Annotation completeness
        if mypy_errors:
            annotation_errors = missing_annotations
            correlations['annotation_completeness'] = 1.0 - min(1.0, annotation_errors / 100.0)
        else:
            correlations['annotation_completeness'] = 1.0
        
        return correlations
    
    def suggest_fixes(self, mypy_results: Dict[str, Any]) -> List[str]:
        """Suggest fixes based on MyPy results."""
        suggestions = []
        
        categories = mypy_results.get('categories', {})
        stats = mypy_results.get('statistics', {})
        
        # Missing type hints
        missing_hints = len(categories.get('missing_type_hints', []))
        if missing_hints > 0:
            suggestions.append(f"Add type hints to {missing_hints} functions/variables lacking annotations")
        
        # Incompatible types
        type_errors = len(categories.get('incompatible_types', []))
        if type_errors > 0:
            suggestions.append(f"Fix {type_errors} type compatibility issues")
        
        # Import errors
        import_errors = len(categories.get('import_errors', []))
        if import_errors > 0:
            suggestions.append(f"Resolve {import_errors} import-related type issues")
        
        # Undefined variables/attributes
        undefined_errors = len(categories.get('undefined_variables', []) + 
                             categories.get('attribute_errors', []))
        if undefined_errors > 0:
            suggestions.append(f"Fix {undefined_errors} undefined variable/attribute errors")
        
        # Return type errors
        return_errors = len(categories.get('return_type_errors', []))
        if return_errors > 0:
            suggestions.append(f"Fix {return_errors} return type mismatches")
        
        # General suggestions based on error frequency
        error_codes = stats.get('error_code_frequency', {})
        top_error = max(error_codes.items(), key=lambda x: x[1]) if error_codes else None
        
        if top_error and top_error[1] > 5:
            code, count = top_error
            code_suggestions = {
                'arg-type': "Review function call arguments for type compatibility",
                'assignment': "Check variable assignment type compatibility",
                'attr-defined': "Verify object attributes exist and are properly typed",
                'import-untyped': "Add type stubs for untyped imports",
                'no-untyped-def': "Add type annotations to function definitions"
            }
            
            if code in code_suggestions:
                suggestions.append(f"{code_suggestions[code]} ({count} occurrences)")
        
        return suggestions[:5]  # Limit to top 5 suggestions
    
    def get_type_coverage_report(self, mypy_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a type coverage report."""
        categories = mypy_results.get('categories', {})
        stats = mypy_results.get('statistics', {})
        
        missing_annotations = len(categories.get('missing_type_hints', []))
        total_errors = stats.get('total_errors', 0)
        files_with_errors = stats.get('files_with_errors', 0)
        
        # Estimate type coverage (this is approximate)
        if total_errors == 0:
            coverage_estimate = 100.0
        else:
            # Assume each missing annotation represents uncovered code
            coverage_estimate = max(0.0, 100.0 - (missing_annotations * 2))  # 2% per missing annotation
        
        return {
            'estimated_coverage': coverage_estimate,
            'missing_annotations': missing_annotations,
            'type_errors': len(categories.get('incompatible_types', [])),
            'files_needing_attention': files_with_errors,
            'coverage_grade': self._get_coverage_grade(coverage_estimate)
        }
    
    def _get_coverage_grade(self, coverage: float) -> str:
        """Get letter grade for type coverage."""
        if coverage >= 95:
            return 'A+'
        elif coverage >= 90:
            return 'A'
        elif coverage >= 85:
            return 'B+'
        elif coverage >= 80:
            return 'B'
        elif coverage >= 75:
            return 'B-'
        elif coverage >= 70:
            return 'C+'
        elif coverage >= 65:
            return 'C'
        elif coverage >= 60:
            return 'C-'
        elif coverage >= 50:
            return 'D'
        else:
            return 'F'
    
    def generate_mypy_config(self, project_path: Path, strict_level: str = 'medium') -> str:
        """Generate a mypy.ini configuration file."""
        strict_configs = {
            'lenient': {
                'ignore_missing_imports': True,
                'follow_imports': 'silent',
                'strict_optional': False,
                'warn_redundant_casts': False,
                'warn_unused_ignores': False
            },
            'medium': {
                'ignore_missing_imports': True,
                'follow_imports': 'silent', 
                'strict_optional': True,
                'warn_redundant_casts': True,
                'warn_unused_ignores': True,
                'disallow_untyped_calls': False,
                'disallow_untyped_defs': False
            },
            'strict': {
                'ignore_missing_imports': False,
                'follow_imports': 'normal',
                'strict_optional': True,
                'warn_redundant_casts': True,
                'warn_unused_ignores': True,
                'disallow_untyped_calls': True,
                'disallow_untyped_defs': True,
                'disallow_incomplete_defs': True,
                'check_untyped_defs': True,
                'warn_return_any': True
            }
        }
        
        config = strict_configs.get(strict_level, strict_configs['medium'])
        
        lines = ['[mypy]']
        for key, value in config.items():
            if isinstance(value, bool):
                lines.append(f'{key} = {str(value).lower()}')
            else:
                lines.append(f'{key} = {value}')
        
        return '\\n'.join(lines)