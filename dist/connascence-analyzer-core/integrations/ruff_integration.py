"""
Ruff integration for connascence analysis.

Integrates with Ruff linter to correlate style and lint issues
with connascence violations for comprehensive code quality analysis.
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, List, Any, Optional


class RuffIntegration:
    """Integration with Ruff Python linter."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.description = "Fast Python linter and code formatter"
        self._version_cache: Optional[str] = None
    
    def is_available(self) -> bool:
        """Check if Ruff is available in the environment."""
        try:
            result = subprocess.run(['ruff', '--version'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def get_version(self) -> str:
        """Get Ruff version."""
        if self._version_cache:
            return self._version_cache
        
        try:
            result = subprocess.run(['ruff', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self._version_cache = result.stdout.strip()
                return self._version_cache
        except FileNotFoundError:
            pass
        
        return "Not available"
    
    def analyze(self, project_path: Path) -> Dict[str, Any]:
        """Run Ruff analysis on project."""
        if not self.is_available():
            raise RuntimeError("Ruff is not available")
        
        # Run ruff check with JSON output
        cmd = [
            'ruff', 'check', 
            str(project_path),
            '--format', 'json',
            '--output-format', 'json'
        ]
        
        # Add configuration options
        if self.config.get('config_file'):
            cmd.extend(['--config', str(self.config['config_file'])])
        
        if self.config.get('ignore'):
            for ignore in self.config['ignore']:
                cmd.extend(['--ignore', ignore])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            # Parse JSON output
            issues = []
            if result.stdout:
                try:
                    ruff_output = json.loads(result.stdout)
                    issues = ruff_output if isinstance(ruff_output, list) else []
                except json.JSONDecodeError:
                    # Fallback to text parsing
                    issues = self._parse_text_output(result.stdout)
            
            # Categorize issues
            categorized = self._categorize_issues(issues)
            
            # Get statistics
            stats = self._calculate_statistics(issues)
            
            return {
                'issues': issues,
                'categories': categorized,
                'statistics': stats,
                'total_issues': len(issues),
                'execution_successful': result.returncode == 0 or len(issues) > 0
            }
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Ruff analysis timed out")
        except Exception as e:
            raise RuntimeError(f"Ruff analysis failed: {str(e)}")
    
    def _parse_text_output(self, text_output: str) -> List[Dict[str, Any]]:
        """Parse Ruff text output as fallback."""
        issues = []
        
        for line in text_output.strip().split('\n'):
            if not line.strip():
                continue
            
            # Parse format: path:line:col: code message
            parts = line.split(':', 3)
            if len(parts) >= 4:
                try:
                    file_path = parts[0]
                    line_num = int(parts[1])
                    col_num = int(parts[2])
                    
                    # Extract code and message
                    message_part = parts[3].strip()
                    code_end = message_part.find(' ')
                    if code_end > 0:
                        code = message_part[:code_end]
                        message = message_part[code_end:].strip()
                    else:
                        code = "UNKNOWN"
                        message = message_part
                    
                    issues.append({
                        'filename': file_path,
                        'location': {'row': line_num, 'column': col_num},
                        'code': code,
                        'message': message,
                        'severity': self._get_severity_for_code(code)
                    })
                except (ValueError, IndexError):
                    continue
        
        return issues
    
    def _categorize_issues(self, issues: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize Ruff issues by type."""
        categories = {
            'style': [],
            'complexity': [],
            'imports': [],
            'naming': [],
            'errors': [],
            'warnings': [],
            'other': []
        }
        
        for issue in issues:
            code = issue.get('code', '')
            
            # Categorize based on Ruff rule codes
            if code.startswith('E') or code.startswith('W'):
                # pycodestyle errors and warnings
                if code.startswith('E'):
                    categories['errors'].append(issue)
                else:
                    categories['warnings'].append(issue)
            elif code.startswith('F'):
                # Pyflakes
                categories['errors'].append(issue)
            elif code.startswith('C9'):
                # McCabe complexity
                categories['complexity'].append(issue)
            elif code.startswith('I'):
                # isort imports
                categories['imports'].append(issue)
            elif code.startswith('N'):
                # pep8-naming
                categories['naming'].append(issue)
            elif any(code.startswith(prefix) for prefix in ['B', 'A', 'COM', 'T']):
                # Various style-related rules
                categories['style'].append(issue)
            else:
                categories['other'].append(issue)
        
        return categories
    
    def _calculate_statistics(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics from Ruff issues."""
        if not issues:
            return {
                'total_issues': 0,
                'files_with_issues': 0,
                'avg_issues_per_file': 0.0,
                'severity_breakdown': {}
            }
        
        # Count issues by file
        files_with_issues = set()
        severity_counts = {}
        
        for issue in issues:
            file_path = issue.get('filename', '')
            if file_path:
                files_with_issues.add(file_path)
            
            severity = issue.get('severity', 'unknown')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            'total_issues': len(issues),
            'files_with_issues': len(files_with_issues),
            'avg_issues_per_file': len(issues) / len(files_with_issues) if files_with_issues else 0.0,
            'severity_breakdown': severity_counts
        }
    
    def _get_severity_for_code(self, code: str) -> str:
        """Get severity level for Ruff rule code."""
        # Simplified severity mapping
        if code.startswith('E9') or code.startswith('F'):
            return 'error'
        elif code.startswith('E') or code.startswith('W'):
            return 'warning'
        elif code.startswith('C9'):
            return 'warning'  # Complexity warnings
        else:
            return 'info'
    
    def correlate_with_connascence(self, ruff_results: Dict[str, Any], 
                                 connascence_violations: List[Dict]) -> Dict[str, Any]:
        """Correlate Ruff issues with connascence violations."""
        correlations = {
            'style_connascence_overlap': 0,
            'complexity_alignment': 0,
            'import_organization': 0,
            'naming_consistency': 0
        }
        
        ruff_issues = ruff_results.get('issues', [])
        categories = ruff_results.get('categories', {})
        
        # Style issues vs CoM/CoP violations
        style_issues = categories.get('style', []) + categories.get('warnings', [])
        style_violations = [v for v in connascence_violations 
                           if v.get('connascence_type') in ['CoM', 'CoP']]
        
        if style_issues and style_violations:
            # Calculate file overlap
            style_files = set(issue.get('filename', '') for issue in style_issues)
            violation_files = set(v.get('file_path', '') for v in style_violations)
            overlap = len(style_files.intersection(violation_files))
            correlations['style_connascence_overlap'] = overlap / len(style_files.union(violation_files))
        
        # Complexity issues vs CoA violations
        complexity_issues = categories.get('complexity', [])
        complexity_violations = [v for v in connascence_violations 
                               if v.get('connascence_type') == 'CoA']
        
        if complexity_issues and complexity_violations:
            complexity_files = set(issue.get('filename', '') for issue in complexity_issues)
            violation_files = set(v.get('file_path', '') for v in complexity_violations)
            overlap = len(complexity_files.intersection(violation_files))
            correlations['complexity_alignment'] = overlap / len(complexity_files.union(violation_files))
        
        # Import organization (general code organization metric)
        import_issues = categories.get('imports', [])
        correlations['import_organization'] = 1.0 - (len(import_issues) / 100.0)  # Normalize
        
        # Naming consistency vs overall connascence
        naming_issues = categories.get('naming', [])
        correlations['naming_consistency'] = 1.0 - (len(naming_issues) / 50.0)  # Normalize
        
        return correlations
    
    def suggest_fixes(self, ruff_results: Dict[str, Any]) -> List[str]:
        """Suggest fixes based on Ruff results."""
        suggestions = []
        
        issues = ruff_results.get('issues', [])
        categories = ruff_results.get('categories', {})
        
        # General fix suggestions
        if len(issues) > 50:
            suggestions.append("Run 'ruff check --fix' to automatically fix many style issues")
        
        # Category-specific suggestions
        if len(categories.get('imports', [])) > 5:
            suggestions.append("Run 'ruff check --select I --fix' to fix import organization")
        
        if len(categories.get('style', [])) > 10:
            suggestions.append("Run 'ruff format' to automatically format code style")
        
        complexity_issues = categories.get('complexity', [])
        if complexity_issues:
            suggestions.append(f"Consider refactoring {len(complexity_issues)} functions with high complexity")
        
        # Specific rule suggestions
        error_codes = set()
        for issue in issues[:10]:  # Top 10 issues
            error_codes.add(issue.get('code', ''))
        
        common_fixes = {
            'E501': "Consider breaking long lines or increasing line length limit",
            'F401': "Remove unused imports",
            'E203': "Fix whitespace around operators",
            'W503': "Consider consistent line breaking around operators"
        }
        
        for code in error_codes:
            if code in common_fixes:
                suggestions.append(common_fixes[code])
        
        return suggestions[:5]  # Limit to top 5 suggestions
    
    def get_autofix_commands(self, project_path: Path) -> List[str]:
        """Get commands to automatically fix Ruff issues."""
        commands = []
        
        if self.is_available():
            # Basic autofix command
            commands.append(f"ruff check {project_path} --fix")
            
            # Format command
            commands.append(f"ruff format {project_path}")
            
            # Specific category fixes
            if self.config.get('fix_imports', True):
                commands.append(f"ruff check {project_path} --select I --fix")
            
            if self.config.get('fix_style', True):
                commands.append(f"ruff check {project_path} --select E,W --fix")
        
        return commands