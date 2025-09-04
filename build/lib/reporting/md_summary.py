"""
Markdown Summary Reporter for PR Comments

Generates concise, actionable markdown summaries suitable for 
GitHub/GitLab pull request comments and documentation.
"""

from typing import List
from pathlib import Path

from analyzer.ast_engine.core_analyzer import AnalysisResult, Violation


class MarkdownReporter:
    """Markdown report generator for PR comments."""
    
    def __init__(self):
        self.max_violations_to_show = 10
        self.max_files_to_show = 5
    
    def generate(self, result: AnalysisResult) -> str:
        """Generate markdown summary from analysis result."""
        sections = []
        
        # Header
        sections.append(self._create_header(result))
        
        # Summary
        sections.append(self._create_summary(result))
        
        # Top violations
        if result.violations:
            sections.append(self._create_top_violations(result.violations))
        
        # File breakdown
        sections.append(self._create_file_breakdown(result.violations))
        
        # Recommendations
        sections.append(self._create_recommendations(result))
        
        # Footer
        sections.append(self._create_footer(result))
        
        return "\n\n".join(sections)
    
    def _create_header(self, result: AnalysisResult) -> str:
        """Create report header."""
        total_violations = len(result.violations)
        critical_count = sum(1 for v in result.violations if v.severity.value == "critical")
        
        if critical_count > 0:
            status_emoji = ""
            status = f"{critical_count} critical issues found"
        elif total_violations > 20:
            status_emoji = "" 
            status = f"{total_violations} issues found"
        elif total_violations > 0:
            status_emoji = ""
            status = f"{total_violations} minor issues"
        else:
            status_emoji = "[DONE]"
            status = "No issues found"
        
        return f"""# {status_emoji} Connascence Analysis Report

**Status:** {status} | **Policy:** `{result.policy_preset or 'default'}` | **Duration:** {result.analysis_duration_ms}ms"""
    
    def _create_summary(self, result: AnalysisResult) -> str:
        """Create summary statistics."""
        violations = result.violations
        
        if not violations:
            return "**[SUCCESS] Great work!** No connascence violations detected."
        
        # Count by severity
        by_severity = {}
        for violation in violations:
            severity = violation.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        # Count by type
        by_type = {}
        for violation in violations:
            type_key = violation.type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1
        
        summary_lines = ["## [METRICS] Summary"]
        
        # Severity breakdown with emojis
        severity_emojis = {
            "critical": "",
            "high": "", 
            "medium": "",
            "low": ""
        }
        
        severity_items = []
        for severity in ["critical", "high", "medium", "low"]:
            count = by_severity.get(severity, 0)
            if count > 0:
                emoji = severity_emojis[severity]
                severity_items.append(f"{emoji} **{count}** {severity}")
        
        if severity_items:
            summary_lines.append("**By Severity:** " + " | ".join(severity_items))
        
        # Type breakdown  
        top_types = sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:3]
        if top_types:
            type_items = [f"**{count}** {type_name}" for type_name, count in top_types]
            summary_lines.append("**Most Common:** " + " | ".join(type_items))
        
        # Files affected
        files_affected = len(set(v.file_path for v in violations))
        summary_lines.append(f"**Files Affected:** {files_affected}/{result.total_files_analyzed}")
        
        return "\n".join(summary_lines)
    
    def _create_top_violations(self, violations: List[Violation]) -> str:
        """Create top violations section."""
        if not violations:
            return ""
        
        # Sort by weight (importance), then by severity
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        
        sorted_violations = sorted(
            violations,
            key=lambda v: (severity_order.get(v.severity.value, 0), v.weight),
            reverse=True
        )
        
        lines = ["## [SEARCH] Top Issues"]
        
        shown_count = 0
        for violation in sorted_violations:
            if shown_count >= self.max_violations_to_show:
                break
            
            # Format violation
            severity_emoji = {
                "critical": "",
                "high": "",
                "medium": "", 
                "low": ""
            }.get(violation.severity.value, "")
            
            file_name = Path(violation.file_path).name
            line_ref = f"{file_name}:{violation.line_number}"
            
            lines.append(
                f"- {severity_emoji} **{violation.type.value}** in `{line_ref}` - {violation.description}"
            )
            
            # Add recommendation if available
            if violation.recommendation:
                lines.append(f"  > [TIP] {violation.recommendation}")
            
            shown_count += 1
        
        # Show count if truncated
        remaining = len(sorted_violations) - shown_count
        if remaining > 0:
            lines.append(f"\n_...and {remaining} more issues_")
        
        return "\n".join(lines)
    
    def _create_file_breakdown(self, violations: List[Violation]) -> str:
        """Create file-by-file breakdown."""
        if not violations:
            return ""
        
        # Group violations by file
        by_file = {}
        for violation in violations:
            file_path = violation.file_path
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append(violation)
        
        # Sort files by violation count and weight
        sorted_files = sorted(
            by_file.items(),
            key=lambda x: (len(x[1]), sum(v.weight for v in x[1])),
            reverse=True
        )
        
        lines = ["## [FOLDER] Files Needing Attention"]
        
        shown_files = 0
        for file_path, file_violations in sorted_files:
            if shown_files >= self.max_files_to_show:
                break
            
            file_name = Path(file_path).name
            violation_count = len(file_violations)
            
            # Count by severity for this file
            severity_counts = {}
            for v in file_violations:
                severity = v.severity.value
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Format severity breakdown
            severity_parts = []
            for severity in ["critical", "high", "medium", "low"]:
                count = severity_counts.get(severity, 0)
                if count > 0:
                    severity_parts.append(f"{count} {severity}")
            
            breakdown = " | ".join(severity_parts) if severity_parts else "mixed"
            
            lines.append(f"- **`{file_name}`** - {violation_count} issues ({breakdown})")
            
            shown_files += 1
        
        remaining_files = len(sorted_files) - shown_files
        if remaining_files > 0:
            lines.append(f"\n_...and {remaining_files} more files_")
        
        return "\n".join(lines)
    
    def _create_recommendations(self, result: AnalysisResult) -> str:
        """Create actionable recommendations."""
        violations = result.violations
        
        if not violations:
            return "## [FEATURE] Keep up the great work!\n\nYour code shows excellent connascence practices."
        
        lines = ["## [TIP] Recommendations"]
        
        # Analyze violation patterns for targeted advice
        by_type = {}
        for violation in violations:
            type_key = violation.type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1
        
        recommendations = []
        
        # Type-specific recommendations
        if by_type.get("CoM", 0) > 5:  # Many magic literals
            recommendations.append(
                " **Extract Magic Literals**: Consider creating a constants module "
                "for the numerous magic numbers and strings found."
            )
        
        if by_type.get("CoP", 0) > 3:  # Position issues
            recommendations.append(
                "[CHECKLIST] **Use Keyword Arguments**: Functions with many positional parameters "
                "are hard to maintain. Consider using keyword arguments or data classes."
            )
        
        if by_type.get("CoA", 0) > 2:  # Algorithm duplication
            recommendations.append(
                "[PROGRESS] **Eliminate Duplication**: Similar algorithms detected. "
                "Extract common logic into shared functions or modules."
            )
        
        # Critical issues
        critical_count = sum(1 for v in violations if v.severity.value == "critical")
        if critical_count > 0:
            recommendations.append(
                " **Address Critical Issues First**: Focus on critical violations "
                "as they represent significant design problems."
            )
        
        # General advice if no specific patterns
        if not recommendations:
            recommendations.append(
                "[SEARCH] **Review High-Weight Issues**: Focus on violations with the highest "
                "weight scores for maximum impact on code quality."
            )
        
        for rec in recommendations[:3]:  # Show top 3 recommendations
            lines.append(f"- {rec}")
        
        return "\n".join(lines)
    
    def _create_footer(self, result: AnalysisResult) -> str:
        """Create report footer."""
        footer_parts = [
            "---",
            f"_Analysis completed in {result.analysis_duration_ms}ms",
            f"analyzing {result.total_files_analyzed} files_",
            "",
            "**What is Connascence?** Connascence is a software engineering metric that "
            "measures the strength of coupling between components. Lower connascence "
            "leads to more maintainable code.",
            "",
            " [Learn More](https://connascence.io) | "
            "[TECH] [Connascence Analyzer](https://github.com/connascence/connascence-analyzer)"
        ]
        
        return "\n".join(footer_parts)