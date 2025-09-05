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
Bandit integration for connascence analysis.

Integrates with Bandit security linter to identify security-related
connascence patterns and correlate security issues with code quality.
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, List, Any, Optional


class BanditIntegration:
    """Integration with Bandit security linter."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.description = "Python security linter"
        self._version_cache: Optional[str] = None
    
    def is_available(self) -> bool:
        """Check if Bandit is available in the environment."""
        try:
            result = subprocess.run(['bandit', '--version'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def get_version(self) -> str:
        """Get Bandit version."""
        if self._version_cache:
            return self._version_cache
        
        try:
            result = subprocess.run(['bandit', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                # Parse version from output
                for line in result.stdout.split('\\n'):
                    if 'bandit' in line.lower() and any(c.isdigit() for c in line):
                        self._version_cache = line.strip()
                        return self._version_cache
                self._version_cache = result.stdout.strip()
                return self._version_cache
        except FileNotFoundError:
            pass
        
        return "Not available"
    
    def analyze(self, project_path: Path) -> Dict[str, Any]:
        """Run Bandit security analysis on project."""
        if not self.is_available():
            raise RuntimeError("Bandit is not available")
        
        # Build Bandit command
        cmd = [
            'bandit',
            '-r', str(project_path),  # Recursive
            '-f', 'json',  # JSON format
            '-ll'  # Low-level and above (include more issues)
        ]
        
        # Add configuration options
        if self.config.get('config_file'):
            cmd.extend(['-c', str(self.config['config_file'])])
        
        if self.config.get('baseline_file'):
            cmd.extend(['-b', str(self.config['baseline_file'])])
        
        # Skip files/directories
        skip_patterns = self.config.get('skip_patterns', ['*/test*', '*/tests/*'])
        for pattern in skip_patterns:
            cmd.extend(['--skip', pattern])
        
        # Confidence and severity levels
        confidence = self.config.get('min_confidence', 'low')
        severity = self.config.get('min_severity', 'low')
        cmd.extend(['-i', confidence, '-iii', severity])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            # Parse Bandit JSON output
            if result.stdout:
                try:
                    bandit_data = json.loads(result.stdout)
                    return self._process_bandit_data(bandit_data)
                except json.JSONDecodeError:
                    return {'error': 'Failed to parse Bandit JSON output'}
            
            # Handle case where no issues found
            if result.returncode == 0:
                return {
                    'issues': [],
                    'categories': {},
                    'statistics': {'total_issues': 0},
                    'execution_successful': True
                }
            
            return {'error': f'Bandit analysis failed: {result.stderr}'}
            
        except subprocess.TimeoutExpired:
            return {'error': 'Bandit analysis timed out'}
        except Exception as e:
            return {'error': f'Bandit analysis failed: {str(e)}'}
    
    def _process_bandit_data(self, bandit_data: Dict) -> Dict[str, Any]:
        """Process Bandit JSON output into structured results."""
        issues = bandit_data.get('results', [])
        metrics = bandit_data.get('metrics', {})
        
        # Process and enhance issues
        processed_issues = []
        for issue in issues:
            processed_issue = {
                'test_id': issue.get('test_id', ''),
                'test_name': issue.get('test_name', ''),
                'filename': issue.get('filename', ''),
                'line_number': issue.get('line_number', 0),
                'line_range': issue.get('line_range', []),
                'code': issue.get('code', ''),
                'severity': issue.get('issue_severity', 'MEDIUM').lower(),
                'confidence': issue.get('issue_confidence', 'MEDIUM').lower(),
                'cwe': issue.get('issue_cwe', {}),
                'text': issue.get('issue_text', ''),
                'more_info': issue.get('more_info', ''),
                'category': self._categorize_security_issue(issue)
            }
            processed_issues.append(processed_issue)
        
        # Categorize issues
        categories = self._categorize_issues(processed_issues)
        
        # Calculate statistics
        stats = self._calculate_statistics(processed_issues, metrics)
        
        return {
            'issues': processed_issues,
            'categories': categories,
            'statistics': stats,
            'total_issues': len(processed_issues),
            'execution_successful': True
        }
    
    def _categorize_security_issue(self, issue: Dict) -> str:
        """Categorize a security issue based on test ID and description."""
        test_id = issue.get('test_id', '')
        test_name = issue.get('test_name', '').lower()
        
        # Map test IDs to categories
        category_mapping = {
            # Injection vulnerabilities
            'B101': 'code_injection',
            'B102': 'shell_injection', 
            'B103': 'shell_injection',
            'B104': 'path_traversal',
            'B105': 'hardcoded_password',
            'B106': 'hardcoded_password',
            'B107': 'hardcoded_password',
            'B108': 'insecure_temp',
            'B110': 'try_except_pass',
            'B112': 'try_except_continue',
            
            # Cryptography issues
            'B301': 'weak_crypto',
            'B302': 'weak_crypto',
            'B303': 'weak_crypto',
            'B304': 'insecure_cipher',
            'B305': 'weak_crypto',
            'B306': 'weak_random',
            'B307': 'eval_usage',
            'B308': 'markup_safe',
            'B309': 'httpsconnection',
            'B310': 'urllib_urlopen',
            'B311': 'weak_random',
            'B312': 'telnetlib',
            'B313': 'xml_parsing',
            'B314': 'xml_parsing',
            'B315': 'xml_parsing',
            'B316': 'xml_parsing',
            'B317': 'xml_parsing',
            'B318': 'xml_parsing',
            'B319': 'xml_parsing',
            'B320': 'xml_parsing',
            'B321': 'ftp',
            'B322': 'input_validation',
            'B323': 'unverified_context',
            
            # Input validation
            'B501': 'ssl_context',
            'B502': 'ssl_context',
            'B503': 'ssl_context',
            'B504': 'ssl_context',
            'B505': 'weak_crypto',
            'B506': 'yaml_load',
            'B507': 'ssh_key',
            'B601': 'shell_injection',
            'B602': 'shell_injection',
            'B603': 'shell_injection',
            'B604': 'shell_injection',
            'B605': 'shell_injection',
            'B606': 'shell_injection',
            'B607': 'shell_injection',
            'B608': 'sql_injection',
            'B609': 'path_traversal',
            'B610': 'shell_injection',
            'B611': 'shell_injection',
            'B701': 'jinja2_autoescape',
            'B702': 'test_use_of_mako_templates',
            'B703': 'django_mark_safe'
        }
        
        category = category_mapping.get(test_id, 'other')
        
        # Fallback categorization based on test name
        if category == 'other':
            if any(keyword in test_name for keyword in ['inject', 'sql', 'command', 'shell']):
                category = 'injection'
            elif any(keyword in test_name for keyword in ['crypto', 'hash', 'cipher', 'random']):
                category = 'crypto'
            elif any(keyword in test_name for keyword in ['password', 'secret', 'key']):
                category = 'secrets'
            elif any(keyword in test_name for keyword in ['xml', 'pickle', 'yaml']):
                category = 'deserialization'
            elif any(keyword in test_name for keyword in ['ssl', 'tls', 'https']):
                category = 'transport_security'
        
        return category
    
    def _categorize_issues(self, issues: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize security issues by type."""
        categories = {
            'injection': [],
            'crypto': [],
            'secrets': [],
            'deserialization': [],
            'transport_security': [],
            'input_validation': [],
            'code_quality': [],
            'other': []
        }
        
        for issue in issues:
            category = issue.get('category', 'other')
            
            # Map specific categories to general ones
            category_mapping = {
                'code_injection': 'injection',
                'shell_injection': 'injection',
                'sql_injection': 'injection',
                'weak_crypto': 'crypto',
                'insecure_cipher': 'crypto',
                'weak_random': 'crypto',
                'hardcoded_password': 'secrets',
                'ssl_context': 'transport_security',
                'xml_parsing': 'deserialization',
                'path_traversal': 'input_validation',
                'try_except_pass': 'code_quality'
            }
            
            general_category = category_mapping.get(category, category)
            if general_category not in categories:
                general_category = 'other'
            
            categories[general_category].append(issue)
        
        return categories
    
    def _calculate_statistics(self, issues: List[Dict[str, Any]], 
                            metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate statistics from Bandit issues."""
        if not issues:
            return {
                'total_issues': 0,
                'files_with_issues': 0,
                'severity_breakdown': {},
                'confidence_breakdown': {},
                'cwe_distribution': {},
                'lines_scanned': metrics.get('_totals', {}).get('loc', 0)
            }
        
        # Count by severity
        severity_counts = {}
        confidence_counts = {}
        files_with_issues = set()
        cwe_counts = {}
        
        for issue in issues:
            # Severity breakdown
            severity = issue.get('severity', 'unknown')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Confidence breakdown
            confidence = issue.get('confidence', 'unknown')
            confidence_counts[confidence] = confidence_counts.get(confidence, 0) + 1
            
            # Files with issues
            filename = issue.get('filename', '')
            if filename:
                files_with_issues.add(filename)
            
            # CWE distribution
            cwe = issue.get('cwe', {})
            if isinstance(cwe, dict) and 'id' in cwe:
                cwe_id = cwe['id']
                cwe_counts[cwe_id] = cwe_counts.get(cwe_id, 0) + 1
        
        return {
            'total_issues': len(issues),
            'files_with_issues': len(files_with_issues),
            'avg_issues_per_file': len(issues) / len(files_with_issues) if files_with_issues else 0.0,
            'severity_breakdown': severity_counts,
            'confidence_breakdown': confidence_counts,
            'cwe_distribution': cwe_counts,
            'lines_scanned': metrics.get('_totals', {}).get('loc', 0),
            'files_scanned': metrics.get('_totals', {}).get('nosec', 0)
        }
    
    def correlate_with_connascence(self, bandit_results: Dict[str, Any], 
                                 connascence_violations: List[Dict]) -> Dict[str, Any]:
        """Correlate Bandit security issues with connascence violations."""
        correlations = {
            'security_connascence_overlap': 0.0,
            'hardcoded_secrets_com_overlap': 0.0,
            'injection_risk_files': [],
            'security_quality_score': 0.0
        }
        
        issues = bandit_results.get('issues', [])
        categories = bandit_results.get('categories', {})
        
        if not issues:
            correlations['security_quality_score'] = 1.0
            return correlations
        
        # General file overlap
        security_files = set(issue.get('filename', '') for issue in issues)
        violation_files = set(v.get('file_path', '') for v in connascence_violations)
        
        shared_files = security_files.intersection(violation_files)
        all_files = security_files.union(violation_files)
        
        if all_files:
            correlations['security_connascence_overlap'] = len(shared_files) / len(all_files)
        
        # Hardcoded secrets vs Connascence of Meaning (CoM)
        secrets_issues = categories.get('secrets', [])
        com_violations = [v for v in connascence_violations 
                         if v.get('connascence_type') == 'CoM']
        
        if secrets_issues and com_violations:
            secrets_files = set(issue.get('filename', '') for issue in secrets_issues)
            com_files = set(v.get('file_path', '') for v in com_violations)
            
            overlap = len(secrets_files.intersection(com_files))
            correlations['hardcoded_secrets_com_overlap'] = (
                overlap / len(secrets_files.union(com_files))
            )
        
        # Injection risk files (files with both injection vulnerabilities and connascence issues)
        injection_issues = categories.get('injection', [])
        if injection_issues:
            injection_files = set(issue.get('filename', '') for issue in injection_issues)
            risky_files = injection_files.intersection(violation_files)
            correlations['injection_risk_files'] = list(risky_files)
        
        # Security quality score (combination of security issues and connascence)
        # Lower scores indicate higher risk
        security_weight = len(issues) * 2  # Weight security issues more heavily
        connascence_weight = len(connascence_violations)
        total_issues = security_weight + connascence_weight
        
        # Normalize to 0-1 scale (assume 50 total weighted issues = 0 score)
        correlations['security_quality_score'] = max(0.0, 1.0 - (total_issues / 50.0))
        
        return correlations
    
    def suggest_security_fixes(self, bandit_results: Dict[str, Any]) -> List[str]:
        """Suggest security fixes based on Bandit results."""
        suggestions = []
        
        categories = bandit_results.get('categories', {})
        stats = bandit_results.get('statistics', {})
        
        # Category-specific suggestions
        if categories.get('secrets'):
            secrets_count = len(categories['secrets'])
            suggestions.append(f"Move {secrets_count} hardcoded secrets to environment variables or config files")
        
        if categories.get('injection'):
            injection_count = len(categories['injection'])
            suggestions.append(f"Fix {injection_count} potential injection vulnerabilities with input sanitization")
        
        if categories.get('crypto'):
            crypto_count = len(categories['crypto'])
            suggestions.append(f"Update {crypto_count} cryptographic implementations to use secure algorithms")
        
        if categories.get('transport_security'):
            tls_count = len(categories['transport_security'])
            suggestions.append(f"Enable proper TLS/SSL verification for {tls_count} network connections")
        
        if categories.get('deserialization'):
            deser_count = len(categories['deserialization'])
            suggestions.append(f"Secure {deser_count} deserialization operations against code execution")
        
        # High-impact suggestions based on severity
        high_severity = [issue for issue in bandit_results.get('issues', []) 
                        if issue.get('severity') == 'high']
        if high_severity:
            suggestions.insert(0, f" URGENT: Address {len(high_severity)} high-severity security issues immediately")
        
        # Confidence-based suggestions
        high_confidence = [issue for issue in bandit_results.get('issues', []) 
                          if issue.get('confidence') == 'high']
        if high_confidence:
            suggestions.append(f"Prioritize {len(high_confidence)} high-confidence security findings")
        
        return suggestions[:5]  # Limit to top 5 suggestions
    
    def generate_security_report(self, bandit_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive security report."""
        stats = bandit_results.get('statistics', {})
        categories = bandit_results.get('categories', {})
        issues = bandit_results.get('issues', [])
        
        # Calculate security score
        total_issues = len(issues)
        high_severity = len([i for i in issues if i.get('severity') == 'high'])
        medium_severity = len([i for i in issues if i.get('severity') == 'medium'])
        
        # Security score (0-100, higher is better)
        if total_issues == 0:
            security_score = 100
        else:
            # Penalty based on severity
            penalty = (high_severity * 15) + (medium_severity * 5) + (total_issues * 2)
            security_score = max(0, 100 - penalty)
        
        return {
            'security_score': security_score,
            'total_issues': total_issues,
            'severity_breakdown': stats.get('severity_breakdown', {}),
            'top_categories': dict(sorted(
                [(cat, len(issues)) for cat, issues in categories.items() if issues],
                key=lambda x: x[1], reverse=True
            )[:5]),
            'files_scanned': stats.get('files_scanned', 0),
            'lines_scanned': stats.get('lines_scanned', 0),
            'security_grade': self._get_security_grade(security_score),
            'risk_level': self._get_risk_level(high_severity, total_issues)
        }
    
    def _get_security_grade(self, score: float) -> str:
        """Get letter grade for security score."""
        if score >= 95:
            return 'A+'
        elif score >= 90:
            return 'A'
        elif score >= 85:
            return 'B+'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C+'
        elif score >= 60:
            return 'C'
        elif score >= 50:
            return 'D'
        else:
            return 'F'
    
    def _get_risk_level(self, high_severity: int, total_issues: int) -> str:
        """Determine overall risk level."""
        if high_severity > 0:
            return 'HIGH'
        elif total_issues > 10:
            return 'MEDIUM'
        elif total_issues > 0:
            return 'LOW'
        else:
            return 'MINIMAL'