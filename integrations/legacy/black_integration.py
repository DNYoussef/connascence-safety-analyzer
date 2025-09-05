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
Black integration for connascence analysis.

Integrates with Black code formatter to correlate formatting consistency
with connascence violations and overall code quality.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import tempfile
import difflib

from .base_integration import BaseIntegration


class BlackIntegration(BaseIntegration):
    """Integration with Black Python code formatter."""
    
    @property
    def tool_name(self) -> str:
        return "black"
    
    @property
    def description(self) -> str:
        return "Python code formatter"
    
    @property
    def version_command(self) -> List[str]:
        return ['black', '--version']
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.description = "Python code formatter"
        self._version_cache: Optional[str] = None
    
    def is_available(self) -> bool:
        """Check if Black is available in the environment."""
        try:
            result = subprocess.run(['black', '--version'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def get_version(self) -> str:
        """Get Black version."""
        if self._version_cache:
            return self._version_cache
        
        try:
            result = subprocess.run(['black', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                # Parse version from "black, 23.7.0"
                version_parts = result.stdout.strip().split(',')
                if len(version_parts) >= 2:
                    self._version_cache = version_parts[1].strip()
                else:
                    self._version_cache = result.stdout.strip()
                return self._version_cache
        except FileNotFoundError:
            pass
        
        return "Not available"
    
    def analyze(self, project_path: Path) -> Dict[str, Any]:
        """Analyze project for Black formatting compliance."""
        if not self.is_available():
            raise RuntimeError("Black is not available")
        
        # Check if project would be reformatted by Black
        check_result = self._check_formatting(project_path)
        
        # Get diff information
        diff_info = self._get_formatting_diff(project_path)
        
        # Calculate formatting statistics
        stats = self._calculate_formatting_stats(check_result, diff_info)
        
        return {
            'formatting_compliant': check_result['compliant'],
            'unformatted_files': check_result['unformatted_files'],
            'diff_info': diff_info,
            'statistics': stats,
            'execution_successful': True
        }
    
    def _check_formatting(self, project_path: Path) -> Dict[str, Any]:
        """Check if files comply with Black formatting."""
        cmd = [
            'black',
            '--check',
            '--diff',
            str(project_path)
        ]
        
        # Add configuration options
        if self.config.get('line_length'):
            cmd.extend(['--line-length', str(self.config['line_length'])])
        
        if self.config.get('skip_string_normalization'):
            cmd.append('--skip-string-normalization')
        
        if self.config.get('target_versions'):
            for version in self.config['target_versions']:
                cmd.extend(['--target-version', version])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            # Parse Black output
            unformatted_files = []
            if result.returncode != 0:  # Files would be reformatted
                unformatted_files = self._parse_black_check_output(result.stdout)
            
            return {
                'compliant': result.returncode == 0,
                'unformatted_files': unformatted_files,
                'output': result.stdout,
                'exit_code': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Black formatting check timed out")
        except Exception as e:
            raise RuntimeError(f"Black formatting check failed: {str(e)}")
    
    def _get_formatting_diff(self, project_path: Path) -> Dict[str, Any]:
        """Get detailed diff information for formatting changes."""
        cmd = [
            'black',
            '--diff',
            '--color',
            str(project_path)
        ]
        
        # Add configuration options
        if self.config.get('line_length'):
            cmd.extend(['--line-length', str(self.config['line_length'])])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            # Parse diff output
            diff_info = self._parse_black_diff_output(result.stdout)
            
            return {
                'has_changes': result.returncode != 0,
                'diff_output': result.stdout,
                'file_diffs': diff_info,
                'total_changes': sum(len(changes.get('changes', [])) for changes in diff_info.values())
            }
            
        except subprocess.TimeoutExpired:
            return {'error': 'Black diff generation timed out'}
        except Exception as e:
            return {'error': f'Black diff generation failed: {str(e)}'}
    
    def _parse_black_check_output(self, output: str) -> List[str]:
        """Parse Black check output to extract unformatted files."""
        unformatted_files = []
        
        for line in output.split('\\n'):
            line = line.strip()
            if line.startswith('would reformat'):
                # Extract filename from "would reformat path/to/file.py"
                parts = line.split()
                if len(parts) >= 3:
                    filename = parts[2]
                    unformatted_files.append(filename)
        
        return unformatted_files
    
    def _parse_black_diff_output(self, diff_output: str) -> Dict[str, Any]:
        """Parse Black diff output to extract change information."""
        file_diffs = {}
        current_file = None
        current_changes = []
        
        for line in diff_output.split('\\n'):
            # Check for file headers
            if line.startswith('--- '):
                if current_file and current_changes:
                    file_diffs[current_file] = {'changes': current_changes}
                
                # Extract filename
                current_file = line[4:].split('\\t')[0].strip()
                current_changes = []
            
            elif line.startswith('+++ '):
                continue  # Skip +++ lines
            
            elif line.startswith('@@'):
                # Parse hunk header for line numbers
                current_changes.append({
                    'type': 'hunk_header',
                    'content': line,
                    'line_info': self._parse_hunk_header(line)
                })
            
            elif line.startswith('-') and not line.startswith('---'):
                # Removed line
                current_changes.append({
                    'type': 'removal',
                    'content': line[1:],  # Remove - prefix
                    'line': line
                })
            
            elif line.startswith('+') and not line.startswith('+++'):
                # Added line
                current_changes.append({
                    'type': 'addition',
                    'content': line[1:],  # Remove + prefix
                    'line': line
                })
            
            elif line.startswith(' '):
                # Context line (unchanged)
                current_changes.append({
                    'type': 'context',
                    'content': line[1:],  # Remove space prefix
                    'line': line
                })
        
        # Don't forget the last file
        if current_file and current_changes:
            file_diffs[current_file] = {'changes': current_changes}
        
        return file_diffs
    
    def _parse_hunk_header(self, hunk_header: str) -> Dict[str, Any]:
        """Parse hunk header to extract line number information."""
        # Format: @@ -start,count +start,count @@ optional_context
        import re
        match = re.match(r'@@ -(\\d+)(?:,(\\d+))? \\+(\\d+)(?:,(\\d+))? @@', hunk_header)
        
        if match:
            old_start, old_count, new_start, new_count = match.groups()
            return {
                'old_start': int(old_start),
                'old_count': int(old_count) if old_count else 1,
                'new_start': int(new_start),
                'new_count': int(new_count) if new_count else 1
            }
        
        return {}
    
    def _calculate_formatting_stats(self, check_result: Dict, diff_info: Dict) -> Dict[str, Any]:
        """Calculate formatting statistics."""
        unformatted_files = check_result.get('unformatted_files', [])
        file_diffs = diff_info.get('file_diffs', {})
        
        # Count different types of changes
        total_additions = 0
        total_removals = 0
        total_hunks = 0
        
        for file_diff in file_diffs.values():
            changes = file_diff.get('changes', [])
            
            for change in changes:
                change_type = change.get('type')
                if change_type == 'addition':
                    total_additions += 1
                elif change_type == 'removal':
                    total_removals += 1
                elif change_type == 'hunk_header':
                    total_hunks += 1
        
        # Calculate formatting compliance percentage
        # This is an approximation since we don't know total files
        if not unformatted_files:
            compliance_percentage = 100.0
        else:
            # Estimate based on number of unformatted files
            # Assume reasonable project size for percentage calculation
            estimated_total_files = max(len(unformatted_files) * 2, 10)
            formatted_files = estimated_total_files - len(unformatted_files)
            compliance_percentage = (formatted_files / estimated_total_files) * 100
        
        return {
            'total_unformatted_files': len(unformatted_files),
            'total_formatting_changes': total_additions + total_removals,
            'additions': total_additions,
            'removals': total_removals,
            'hunks': total_hunks,
            'compliance_percentage': compliance_percentage,
            'compliance_grade': self._get_compliance_grade(compliance_percentage)
        }
    
    def _get_compliance_grade(self, percentage: float) -> str:
        """Get letter grade for formatting compliance."""
        if percentage >= 98:
            return 'A+'
        elif percentage >= 95:
            return 'A'
        elif percentage >= 90:
            return 'B+'
        elif percentage >= 85:
            return 'B'
        elif percentage >= 80:
            return 'B-'
        elif percentage >= 70:
            return 'C'
        elif percentage >= 60:
            return 'D'
        else:
            return 'F'
    
    def correlate_with_connascence(self, black_results: Dict[str, Any], 
                                 connascence_violations: List[Dict]) -> Dict[str, Any]:
        """Correlate Black formatting with connascence violations."""
        correlations = {
            'formatting_quality_relationship': 0.0,
            'unformatted_violation_overlap': 0.0,
            'style_consistency_score': 0.0,
            'shared_problem_files': []
        }
        
        unformatted_files = set(black_results.get('unformatted_files', []))
        violation_files = set(v.get('file_path', '') for v in connascence_violations)
        
        if not unformatted_files and not violation_files:
            correlations['style_consistency_score'] = 1.0
            return correlations
        
        # File overlap analysis
        shared_files = unformatted_files.intersection(violation_files)
        all_problem_files = unformatted_files.union(violation_files)
        
        if all_problem_files:
            correlations['unformatted_violation_overlap'] = len(shared_files) / len(all_problem_files)
            correlations['shared_problem_files'] = list(shared_files)
        
        # Style consistency relationship
        # Theory: Well-formatted code tends to have fewer connascence violations
        stats = black_results.get('statistics', {})
        compliance_percentage = stats.get('compliance_percentage', 100)
        
        # Filter for style-related connascence violations (CoM, CoP)
        style_violations = [v for v in connascence_violations 
                           if v.get('connascence_type') in ['CoM', 'CoP']]
        
        # Calculate relationship strength
        if len(style_violations) == 0 and compliance_percentage >= 95:
            correlations['style_consistency_score'] = 1.0
        elif len(style_violations) > 0 and compliance_percentage < 80:
            # Both poor formatting and style violations = strong relationship
            correlations['style_consistency_score'] = 0.8
        else:
            # Moderate relationship
            correlations['style_consistency_score'] = 0.5
        
        # Formatting quality relationship
        # Inverse relationship: more formatting issues = more connascence violations
        total_changes = stats.get('total_formatting_changes', 0)
        violation_count = len(connascence_violations)
        
        if total_changes == 0 and violation_count == 0:
            correlations['formatting_quality_relationship'] = 1.0
        else:
            # Normalize and calculate inverse relationship
            normalized_changes = min(total_changes / 100, 1.0)  # Cap at 1.0
            normalized_violations = min(violation_count / 50, 1.0)  # Cap at 1.0
            
            # Higher correlation when both are high or both are low
            correlations['formatting_quality_relationship'] = 1.0 - abs(normalized_changes - normalized_violations)
        
        return correlations
    
    def suggest_formatting_fixes(self, black_results: Dict[str, Any]) -> List[str]:
        """Suggest formatting fixes based on Black analysis."""
        suggestions = []
        
        stats = black_results.get('statistics', {})
        unformatted_files = black_results.get('unformatted_files', [])
        
        # Main formatting suggestion
        if unformatted_files:
            suggestions.append(f"Run 'black .' to automatically format {len(unformatted_files)} files")
        
        # Compliance-based suggestions
        compliance = stats.get('compliance_percentage', 100)
        if compliance < 90:
            suggestions.append(f"Improve code formatting consistency (current: {compliance:.1f}%)")
        
        # Change-based suggestions
        total_changes = stats.get('total_formatting_changes', 0)
        if total_changes > 100:
            suggestions.append(f"Consider running Black incrementally to handle {total_changes} formatting changes")
        
        # Configuration suggestions
        if not self.config:
            suggestions.append("Create a pyproject.toml or .black configuration file for consistent formatting")
        
        # Integration suggestions
        if unformatted_files:
            suggestions.append("Set up Black as a pre-commit hook to maintain formatting automatically")
        
        return suggestions[:5]  # Limit to top 5 suggestions
    
    def format_project(self, project_path: Path, check_only: bool = False) -> Dict[str, Any]:
        """Format project with Black or check formatting compliance."""
        cmd = ['black']
        
        if check_only:
            cmd.append('--check')
        
        cmd.append(str(project_path))
        
        # Add configuration options
        if self.config.get('line_length'):
            cmd.extend(['--line-length', str(self.config['line_length'])])
        
        if self.config.get('skip_string_normalization'):
            cmd.append('--skip-string-normalization')
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            return {
                'success': result.returncode == 0 or not check_only,
                'output': result.stdout,
                'error': result.stderr,
                'files_formatted': self._count_formatted_files(result.stdout) if not check_only else 0,
                'exit_code': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Black formatting timed out'}
        except Exception as e:
            return {'success': False, 'error': f'Black formatting failed: {str(e)}'}
    
    def _count_formatted_files(self, output: str) -> int:
        """Count number of files formatted from Black output."""
        count = 0
        for line in output.split('\\n'):
            if 'reformatted' in line:
                count += 1
        return count
    
    def generate_black_config(self, project_path: Path, style: str = 'default') -> str:
        """Generate Black configuration for pyproject.toml."""
        configs = {
            'default': {
                'line-length': 88,
                'target-version': ['py38', 'py39', 'py310', 'py311'],
                'include': '\\\\.pyi?$'
            },
            'strict': {
                'line-length': 79,  # PEP 8 compliant
                'target-version': ['py38', 'py39', 'py310', 'py311'],
                'include': '\\\\.pyi?$',
                'extend-exclude': 'migrations/'
            },
            'relaxed': {
                'line-length': 100,
                'target-version': ['py38', 'py39', 'py310', 'py311'],
                'skip-string-normalization': True,
                'include': '\\\\.pyi?$'
            }
        }
        
        config = configs.get(style, configs['default'])
        
        lines = ['[tool.black]']
        for key, value in config.items():
            if isinstance(value, bool):
                lines.append(f'{key} = {str(value).lower()}')
            elif isinstance(value, list):
                formatted_list = '[' + ', '.join(f'"{v}"' for v in value) + ']'
                lines.append(f'{key} = {formatted_list}')
            elif isinstance(value, str):
                lines.append(f'{key} = "{value}"')
            else:
                lines.append(f'{key} = {value}')
        
        return '\\n'.join(lines)