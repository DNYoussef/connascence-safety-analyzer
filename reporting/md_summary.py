# SPDX-License-Identifier: MIT
"""
Markdown summary reporter for connascence analysis results.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class MarkdownReporter:
    """Markdown format reporter for analysis results."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
    
    def export_results(self, results: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """Export analysis results to Markdown format."""
        
        violations = results.get('violations', [])
        summary = results.get('summary', {})
        nasa_compliance = results.get('nasa_compliance', {})
        
        # Generate markdown report
        md_content = self._generate_markdown_report(violations, summary, nasa_compliance, results)
        
        # Export to file if path provided
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            return str(output_file)
        
        return md_content
    
    def _generate_markdown_report(self, violations: List[Dict], summary: Dict, nasa_compliance: Dict, results: Dict) -> str:
        """Generate markdown report content."""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        md_lines = [
            "# Connascence Analysis Report",
            "",
            f"**Generated:** {timestamp}  ",
            f"**Analyzer:** connascence-safety-analyzer v2.0.0  ",
            f"**Path:** {results.get('path', '.')}  ",
            f"**Policy:** {results.get('policy', 'default')}  ",
            "",
            "## Executive Summary",
            "",
        ]
        
        # Summary statistics
        total_violations = summary.get('total_violations', 0)
        critical_violations = summary.get('critical_violations', 0)
        overall_score = summary.get('overall_quality_score', 0.0)
        
        md_lines.extend([
            f"- **Total Violations:** {total_violations}",
            f"- **Critical Violations:** {critical_violations}",
            f"- **Overall Quality Score:** {overall_score:.2%}",
            "",
        ])
        
        # NASA Compliance if available
        if nasa_compliance:
            nasa_score = nasa_compliance.get('score', 0.0)
            nasa_violations = nasa_compliance.get('violations', [])
            
            md_lines.extend([
                "## NASA Power of Ten Compliance",
                "",
                f"- **NASA Compliance Score:** {nasa_score:.2%}",
                f"- **NASA Rule Violations:** {len(nasa_violations)}",
                "",
            ])
        
        # Violation breakdown by severity
        if violations:
            severity_counts = {}
            for violation in violations:
                severity = violation.get('severity', 'unknown')
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            md_lines.extend([
                "## Severity Breakdown",
                "",
            ])
            
            for severity in ['critical', 'high', 'medium', 'low', 'info']:
                count = severity_counts.get(severity, 0)
                if count > 0:
                    emoji = self._get_severity_emoji(severity)
                    md_lines.append(f"- {emoji} **{severity.title()}:** {count}")
            
            md_lines.extend(["", "## Detailed Violations", ""])
            
            # Group violations by file
            violations_by_file = {}
            for violation in violations:
                file_path = violation.get('file_path', 'unknown')
                if file_path not in violations_by_file:
                    violations_by_file[file_path] = []
                violations_by_file[file_path].append(violation)
            
            for file_path, file_violations in violations_by_file.items():
                md_lines.extend([
                    f"### {file_path}",
                    "",
                ])
                
                for violation in file_violations:
                    severity = violation.get('severity', 'medium')
                    emoji = self._get_severity_emoji(severity)
                    line_num = violation.get('line_number', 1)
                    rule_id = violation.get('rule_id', 'unknown')
                    description = violation.get('description', 'No description')
                    
                    md_lines.extend([
                        f"**Line {line_num}** {emoji} `{rule_id}` - {severity.title()}",
                        f"> {description}",
                        "",
                    ])
        else:
            md_lines.extend([
                "## No Violations Found",
                "",
                "✅ Congratulations! No connascence violations were detected in the analyzed code.",
                "",
            ])
        
        return '\n'.join(md_lines)
    
    def _get_severity_emoji(self, severity: str) -> str:
        """Get emoji for severity level."""
        emoji_map = {
            'critical': '🔴',
            'high': '🟠', 
            'medium': '🟡',
            'low': '🔵',
            'info': 'ℹ️'
        }
        return emoji_map.get(severity, '⚪')