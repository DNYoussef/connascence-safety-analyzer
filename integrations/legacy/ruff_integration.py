# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

"""
Ruff integration for connascence analysis.

Integrates with Ruff linter to correlate style and lint issues
with connascence violations for comprehensive code quality analysis.
"""

import subprocess
import json
import logging
import shlex
from pathlib import Path
from typing import Dict, List, Any, Optional
import re

logger = logging.getLogger(__name__)


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
        """Run Ruff analysis on project with enhanced security."""
        if not self.is_available():
            raise RuntimeError("Ruff is not available")
        
        # Validate and sanitize project path
        validated_path = self._validate_and_sanitize_path(project_path)
        if not validated_path:
            raise ValueError(f"Invalid or unsafe project path: {project_path}")
        
        # Run ruff check with JSON output
        cmd = [
            'ruff', 'check', 
            str(validated_path),
            '--format', 'json',
            '--output-format', 'json'
        ]
        
        # Add configuration options with validation
        if self.config.get('config_file'):
            config_file_path = self._validate_and_sanitize_path(Path(self.config['config_file']))
            if config_file_path:
                cmd.extend(['--config', str(config_file_path)])
        
        if self.config.get('ignore'):
            for ignore in self.config['ignore']:
                # Sanitize ignore patterns to prevent injection
                sanitized_ignore = self._sanitize_ignore_pattern(ignore)
                if sanitized_ignore:
                    cmd.extend(['--ignore', sanitized_ignore])
        
        try:
            # Log command for audit (without sensitive data)
            logger.debug(f"Executing ruff command: {' '.join(cmd[:3])} [path]")
            
            # Execute with enhanced security
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=60,
                shell=False,  # Prevent shell injection
                cwd=None,     # Don't inherit current directory
                env={'PATH': '/usr/bin:/bin'}  # Restrict environment
            )
            
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
            logger.warning(f"Ruff analysis timed out for path: {validated_path}")
            raise RuntimeError("Ruff analysis timed out")
        except subprocess.CalledProcessError as e:
            logger.error(f"Ruff analysis failed with return code {e.returncode}")
            raise RuntimeError(f"Ruff analysis failed: return code {e.returncode}")
        except Exception as e:
            logger.error(f"Unexpected error during ruff analysis: {str(e)}")
            raise RuntimeError(f"Ruff analysis failed: {str(e)}")
    
    def _validate_and_sanitize_path(self, path: Path) -> Optional[Path]:
        """Validate and sanitize file path to prevent path traversal attacks."""
        try:
            # Resolve path to absolute path
            resolved_path = path.resolve()
            
            # Convert to string for validation
            path_str = str(resolved_path)
            
            # Check for path traversal attempts
            if '..' in path_str or path_str.startswith('/'):
                # Additional validation for legitimate parent directory access
                if not self._is_safe_path(resolved_path):
                    return None
            
            # Check against restricted paths
            restricted_paths = [
                '/etc', '/var/log', '/usr/bin', '/bin', '/sbin',
                '/proc', '/sys', '/dev', '/root',
                'C:\\Windows', 'C:\\Program Files', 'C:\\Users\\Administrator'
            ]
            
            path_lower = path_str.lower()
            for restricted in restricted_paths:
                if path_lower.startswith(restricted.lower()):
                    return None
            
            # Verify path exists and is readable
            if not resolved_path.exists():
                return None
                
            return resolved_path
            
        except (OSError, ValueError) as e:
            logger.warning(f"Path validation failed: {e}")
            return None
    
    def _is_safe_path(self, path: Path) -> bool:
        """Check if path is within safe boundaries."""
        try:
            # Get current working directory
            cwd = Path.cwd()
            
            # Check if path is within current working directory or subdirectories
            try:
                path.relative_to(cwd)
                return True
            except ValueError:
                # Path is outside current directory - additional checks needed
                pass
            
            # Allow specific safe parent directories
            safe_parents = ['/tmp', '/var/tmp', Path.home()]
            for safe_parent in safe_parents:
                try:
                    if isinstance(safe_parent, str):
                        safe_parent = Path(safe_parent)
                    path.relative_to(safe_parent)
                    return True
                except ValueError:
                    continue
                    
            return False
            
        except Exception:
            return False
    
    def _sanitize_ignore_pattern(self, pattern: str) -> Optional[str]:
        """Sanitize ignore pattern to prevent command injection."""
        if not pattern or len(pattern) > 100:  # Reasonable limit
            return None
            
        # Only allow alphanumeric, dash, underscore, dot, slash, and asterisk
        if not re.match(r'^[a-zA-Z0-9_\-\.*/]+$', pattern):
            return None
            
        # Remove any shell metacharacters
        pattern = re.sub(r'[;&|`$(){}\\[\\]<>]', '', pattern)
        
        return pattern if pattern else None
    
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
            'naming_consistency': 0,
            'magic_literal_correlation': 0,
            'parameter_position_correlation': 0,
            'nasa_compliance_alignment': 0,
            'rule_mappings': self._get_connascence_rule_mappings()
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
        
        # Enhanced magic literal correlation (CoM)
        magic_literal_correlation = self._correlate_magic_literals(ruff_issues, connascence_violations)
        correlations['magic_literal_correlation'] = magic_literal_correlation
        
        # Parameter position correlation (CoP)
        param_correlation = self._correlate_parameter_issues(ruff_issues, connascence_violations)
        correlations['parameter_position_correlation'] = param_correlation
        
        # NASA Power of Ten alignment
        nasa_alignment = self._correlate_nasa_compliance(ruff_issues, connascence_violations)
        correlations['nasa_compliance_alignment'] = nasa_alignment
        
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
    
    def _get_connascence_rule_mappings(self) -> Dict[str, Dict[str, str]]:
        """Get mappings between Ruff rules and connascence types."""
        return {
            # Connascence of Meaning (CoM) - Magic Literals
            'PLR2004': {
                'connascence_type': 'CoM',
                'description': 'Magic value used in comparison',
                'severity': 'medium',
                'nasa_rule': 'Rule 5: No magic numbers'
            },
            # Connascence of Position (CoP) - Parameter Order
            'PLR0913': {
                'connascence_type': 'CoP',
                'description': 'Too many arguments in function',
                'severity': 'medium',
                'nasa_rule': 'Rule 4: No goto, Rule 6: Restrict function size'
            },
            # Connascence of Algorithm (CoA) - Complexity
            'PLR0915': {
                'connascence_type': 'CoA',
                'description': 'Too many statements',
                'severity': 'medium',
                'nasa_rule': 'Rule 6: Restrict function size'
            },
            'PLR0912': {
                'connascence_type': 'CoA',
                'description': 'Too many branches',
                'severity': 'medium',
                'nasa_rule': 'Rule 6: Restrict function size'
            },
            'C901': {
                'connascence_type': 'CoA',
                'description': 'Function is too complex',
                'severity': 'high',
                'nasa_rule': 'Rule 6: Restrict function size'
            },
            # Connascence of Name (CoN) - Naming Issues
            'N801': {
                'connascence_type': 'CoN',
                'description': 'Class name should use CapWords convention',
                'severity': 'low',
                'nasa_rule': 'Rule 9: Use preprocessor judiciously'
            },
            'N802': {
                'connascence_type': 'CoN',
                'description': 'Function name should be lowercase',
                'severity': 'low',
                'nasa_rule': 'Rule 9: Use preprocessor judiciously'
            },
            # Connascence of Type (CoT) - Type Issues
            'F821': {
                'connascence_type': 'CoT',
                'description': 'Undefined name',
                'severity': 'high',
                'nasa_rule': 'Rule 8: Restrict heap use'
            },
            'F401': {
                'connascence_type': 'CoT',
                'description': 'Module imported but unused',
                'severity': 'medium',
                'nasa_rule': 'Rule 10: Compiler warnings'
            }
        }
    
    def _correlate_magic_literals(self, ruff_issues: List[Dict], 
                                connascence_violations: List[Dict]) -> float:
        """Correlate PLR2004 (magic literals) with CoM violations."""
        plr2004_issues = [issue for issue in ruff_issues if issue.get('code') == 'PLR2004']
        com_violations = [v for v in connascence_violations if v.get('connascence_type') == 'CoM']
        
        if not plr2004_issues and not com_violations:
            return 1.0  # Perfect correlation when both are empty
        
        if not plr2004_issues or not com_violations:
            return 0.0  # No correlation when one is empty
        
        # Calculate file-based correlation
        ruff_files = set(issue.get('filename', '') for issue in plr2004_issues)
        conn_files = set(v.get('file_path', '') for v in com_violations)
        
        overlap = len(ruff_files.intersection(conn_files))
        total_files = len(ruff_files.union(conn_files))
        
        return overlap / total_files if total_files > 0 else 0.0
    
    def _correlate_parameter_issues(self, ruff_issues: List[Dict], 
                                  connascence_violations: List[Dict]) -> float:
        """Correlate PLR0913 (too many arguments) with CoP violations."""
        param_issues = [issue for issue in ruff_issues if issue.get('code') == 'PLR0913']
        cop_violations = [v for v in connascence_violations if v.get('connascence_type') == 'CoP']
        
        if not param_issues and not cop_violations:
            return 1.0
        
        if not param_issues or not cop_violations:
            return 0.0
        
        # Calculate correlation based on function-level detection
        ruff_functions = set()
        for issue in param_issues:
            filename = issue.get('filename', '')
            line = issue.get('location', {}).get('row', 0)
            ruff_functions.add(f"{filename}:{line}")
        
        conn_functions = set()
        for violation in cop_violations:
            filename = violation.get('file_path', '')
            line = violation.get('line_number', 0)
            conn_functions.add(f"{filename}:{line}")
        
        overlap = len(ruff_functions.intersection(conn_functions))
        total_functions = len(ruff_functions.union(conn_functions))
        
        return overlap / total_functions if total_functions > 0 else 0.0
    
    def _correlate_nasa_compliance(self, ruff_issues: List[Dict], 
                                 connascence_violations: List[Dict]) -> float:
        """Correlate Ruff findings with NASA Power of Ten compliance."""
        nasa_relevant_codes = {'PLR2004', 'PLR0913', 'PLR0915', 'C901', 'PLR0912'}
        nasa_issues = [issue for issue in ruff_issues if issue.get('code') in nasa_relevant_codes]
        
        # Count high-severity connascence violations (likely NASA-relevant)
        high_severity_violations = [
            v for v in connascence_violations 
            if v.get('severity') in ['high', 'critical']
        ]
        
        if not nasa_issues and not high_severity_violations:
            return 1.0  # Perfect compliance when no issues
        
        # Calculate alignment score
        nasa_issue_count = len(nasa_issues)
        high_severity_count = len(high_severity_violations)
        
        # Good alignment when both tools detect similar numbers of serious issues
        if nasa_issue_count == 0 and high_severity_count == 0:
            return 1.0
        elif nasa_issue_count == 0 or high_severity_count == 0:
            return 0.3  # Some alignment but one tool missed issues
        else:
            # Score based on ratio similarity
            ratio = min(nasa_issue_count, high_severity_count) / max(nasa_issue_count, high_severity_count)
            return ratio
    
    def get_rule_recommendations(self, ruff_results: Dict[str, Any], 
                               connascence_violations: List[Dict]) -> List[str]:
        """Generate rule-specific recommendations based on correlation analysis."""
        recommendations = []
        
        issues = ruff_results.get('issues', [])
        rule_mappings = self._get_connascence_rule_mappings()
        
        # Count issues by rule
        rule_counts = {}
        for issue in issues:
            code = issue.get('code', '')
            rule_counts[code] = rule_counts.get(code, 0) + 1
        
        # Generate recommendations for top issues
        for rule_code, count in sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            if rule_code in rule_mappings:
                mapping = rule_mappings[rule_code]
                conn_type = mapping['connascence_type']
                nasa_rule = mapping.get('nasa_rule', 'General best practice')
                
                recommendations.append(
                    f"Address {count} {rule_code} violations ({conn_type}): {mapping['description']} "
                    f"- Aligns with {nasa_rule}"
                )
        
        return recommendations