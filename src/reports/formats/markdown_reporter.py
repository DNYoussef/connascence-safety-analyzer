"""
Markdown Summary Reporter for PR Comments

Consolidated from demo_scans/reports/md_summary.py with improvements.
Generates concise, actionable markdown summaries suitable for 
GitHub/GitLab pull request comments and documentation.
"""

from typing import List
from pathlib import Path

from analyzer.ast_engine.core_analyzer import AnalysisResult, Violation


class MarkdownReporter:
    """Markdown report generator for PR comments and documentation."""
    
    def __init__(self):
        self.max_violations_to_show = 10
        self.max_files_to_show = 5
        self._config = {}
    
    def configure(self, config: dict) -> None:
        """Configure markdown reporter with template options."""
        self._config.update(config)
        
        # Apply configuration overrides
        self.max_violations_to_show = config.get('max_violations_shown', self.max_violations_to_show)
        self.max_files_to_show = config.get('max_files_shown', self.max_files_to_show)
    
    def generate(self, result: AnalysisResult) -> str:
        """Generate markdown summary from analysis result."""
        sections = []
        
        # Header with appropriate mode
        sections.append(self._create_header(result))
        
        # Summary with mode-specific formatting
        sections.append(self._create_summary(result))
        
        # Top violations
        if result.violations:
            sections.append(self._create_top_violations(result.violations))
        
        # File breakdown
        sections.append(self._create_file_breakdown(result.violations))
        
        # Recommendations with mode-specific content
        sections.append(self._create_recommendations(result))
        
        # Footer with appropriate links
        sections.append(self._create_footer(result))
        
        return "\n\n".join(sections)
    
    def _create_header(self, result: AnalysisResult) -> str:
        """Create report header with mode-specific formatting."""
        total_violations = len(result.violations)
        critical_count = sum(1 for v in result.violations if v.severity.value == "critical")
        
        # Determine status and emoji based on mode
        if self._config.get('sales_mode'):
            return self._create_sales_header(total_violations, critical_count, result)
        elif self._config.get('executive_mode'):
            return self._create_executive_header(total_violations, critical_count, result)
        else:
            return self._create_standard_header(total_violations, critical_count, result)
    
    def _create_standard_header(self, total: int, critical: int, result: AnalysisResult) -> str:
        """Standard PR comment header."""
        if critical > 0:
            status_emoji, status = "🚨", f"{critical} critical issues found"
        elif total > 20:
            status_emoji, status = "⚠️", f"{total} issues found"
        elif total > 0:
            status_emoji, status = "💡", f"{total} minor issues"
        else:
            status_emoji, status = "✅", "No issues found"
        
        policy = getattr(result, 'policy_preset', 'default')
        duration = getattr(result, 'analysis_duration_ms', 0)
        
        return f"""# {status_emoji} Connascence Analysis Report

**Status:** {status} | **Policy:** `{policy}` | **Duration:** {duration}ms"""
    
    def _create_sales_header(self, total: int, critical: int, result: AnalysisResult) -> str:
        """Sales-focused header emphasizing value."""
        if total == 0:
            return """# 🎯 Connascence Analysis: Clean Codebase Validated

**Excellent Code Quality Confirmed** - Your codebase demonstrates mature development practices."""
        
        roi_value = self._estimate_roi_hours(total)
        
        return f"""# 🚀 Connascence Analysis: {total} Optimization Opportunities

**Potential Value:** {roi_value} hours of development time savings  
**Technical Debt Identified:** {total} improvement opportunities  
**Investment Protection:** Proactive quality assurance validated"""
    
    def _create_executive_header(self, total: int, critical: int, result: AnalysisResult) -> str:
        """Executive summary header."""
        if critical > 0:
            risk_level = "High Risk"
            priority = "Immediate Action Required"
        elif total > 10:
            risk_level = "Medium Risk"  
            priority = "Planned Remediation Recommended"
        elif total > 0:
            risk_level = "Low Risk"
            priority = "Maintenance Window Opportunity"
        else:
            risk_level = "Minimal Risk"
            priority = "Code Quality Validated"
        
        return f"""# 📊 Executive Code Quality Report

**Risk Assessment:** {risk_level} | **Priority:** {priority}  
**Issues Identified:** {total} | **Files Analyzed:** {result.total_files_analyzed}"""
    
    def _create_summary(self, result: AnalysisResult) -> str:
        """Create summary with mode-specific metrics."""
        violations = result.violations
        
        if not violations:
            if self._config.get('sales_mode'):
                return "**🎉 Investment Protection Validated!** Your development practices are paying off with clean, maintainable code."
            return "**✅ Excellent!** No connascence violations detected."
        
        # Count by severity and type
        by_severity = {}
        by_type = {}
        for violation in violations:
            severity = violation.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1
            type_key = violation.type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1
        
        if self._config.get('sales_mode'):
            return self._create_sales_summary(by_severity, by_type, result)
        elif self._config.get('executive_mode'):
            return self._create_executive_summary(by_severity, by_type, result)
        else:
            return self._create_standard_summary(by_severity, by_type, result)
    
    def _create_standard_summary(self, by_severity: dict, by_type: dict, result: AnalysisResult) -> str:
        """Standard technical summary."""
        summary_lines = ["## 📊 Summary"]
        
        # Severity breakdown with emojis
        severity_emojis = {"critical": "🚨", "high": "⚠️", "medium": "💡", "low": "ℹ️"}
        
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
        files_affected = len(set(v.file_path for v in result.violations))
        summary_lines.append(f"**Files Affected:** {files_affected}/{result.total_files_analyzed}")
        
        return "\n".join(summary_lines)
    
    def _create_sales_summary(self, by_severity: dict, by_type: dict, result: AnalysisResult) -> str:
        """Sales-focused summary emphasizing business value."""
        total_violations = sum(by_severity.values())
        roi_hours = self._estimate_roi_hours(total_violations)
        
        summary_lines = ["## 💰 Business Impact Analysis"]
        
        # ROI calculation
        summary_lines.append(f"**Time Savings Opportunity:** {roi_hours} developer hours")
        summary_lines.append(f"**Maintenance Cost Reduction:** {total_violations} potential future bugs prevented")
        
        # Risk assessment
        critical_count = by_severity.get("critical", 0)
        if critical_count > 0:
            summary_lines.append(f"**🚨 High-Risk Issues:** {critical_count} critical problems requiring immediate attention")
        
        # Value proposition
        high_count = by_severity.get("high", 0) + critical_count
        if high_count > 0:
            summary_lines.append(f"**📈 Improvement Potential:** {high_count} high-impact optimizations identified")
        
        return "\n".join(summary_lines)
    
    def _create_executive_summary(self, by_severity: dict, by_type: dict, result: AnalysisResult) -> str:
        """Executive-level summary."""
        summary_lines = ["## 🎯 Key Metrics"]
        
        critical_count = by_severity.get("critical", 0)
        high_count = by_severity.get("high", 0)
        
        if critical_count > 0:
            summary_lines.append(f"**🚨 Critical Issues:** {critical_count} - Require immediate development resources")
        if high_count > 0:
            summary_lines.append(f"**⚠️ High Priority:** {high_count} - Plan for next development cycle")
        
        # Quality assessment
        total_violations = sum(by_severity.values())
        files_affected = len(set(v.file_path for v in result.violations))
        quality_ratio = files_affected / result.total_files_analyzed * 100
        
        summary_lines.append(f"**📊 Code Quality:** {quality_ratio:.1f}% of files need attention")
        summary_lines.append(f"**🎯 Focus Areas:** Top issues are {', '.join([t for t, _ in sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:2]])}")
        
        return "\n".join(summary_lines)
    
    def _create_top_violations(self, violations: List[Violation]) -> str:
        """Create top violations section with mode-specific formatting."""
        if not violations:
            return ""
        
        # Sort by weight and severity
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        sorted_violations = sorted(
            violations,
            key=lambda v: (severity_order.get(v.severity.value, 0), v.weight),
            reverse=True
        )
        
        if self._config.get('sales_mode'):
            return self._create_sales_violations(sorted_violations)
        else:
            return self._create_standard_violations(sorted_violations)
    
    def _create_standard_violations(self, violations: List[Violation]) -> str:
        """Standard violations list."""
        lines = ["## 🔍 Top Issues"]
        
        shown_count = 0
        for violation in violations:
            if shown_count >= self.max_violations_to_show:
                break
            
            severity_emoji = {"critical": "🚨", "high": "⚠️", "medium": "💡", "low": "ℹ️"}.get(
                violation.severity.value, "❓"
            )
            
            file_name = Path(violation.file_path).name
            line_ref = f"{file_name}:{violation.line_number}"
            
            lines.append(
                f"- {severity_emoji} **{violation.type.value}** in `{line_ref}` - {violation.description}"
            )
            
            if violation.recommendation and self._config.get('include_recommendations', True):
                lines.append(f"  > 💡 {violation.recommendation}")
            
            shown_count += 1
        
        remaining = len(violations) - shown_count
        if remaining > 0:
            lines.append(f"\n_...and {remaining} more issues_")
        
        return "\n".join(lines)
    
    def _create_sales_violations(self, violations: List[Violation]) -> str:
        """Sales-focused violations emphasizing business impact."""
        lines = ["## 🎯 High-Value Improvement Opportunities"]
        
        shown_count = 0
        for violation in violations:
            if shown_count >= self.max_violations_to_show:
                break
            
            file_name = Path(violation.file_path).name
            impact_hours = self._estimate_violation_impact(violation)
            
            lines.append(
                f"- **{violation.type.value}** in `{file_name}` - {impact_hours}h savings potential"
            )
            lines.append(f"  📋 {violation.description}")
            
            if violation.recommendation:
                lines.append(f"  💡 **Solution:** {violation.recommendation}")
            
            shown_count += 1
        
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
        
        lines = ["## 📁 Files Needing Attention"]
        
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
            
            if self._config.get('sales_mode'):
                impact_hours = sum(self._estimate_violation_impact(v) for v in file_violations)
                lines.append(f"- **`{file_name}`** - {violation_count} issues, {impact_hours}h impact ({breakdown})")
            else:
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
            if self._config.get('sales_mode'):
                return """## 🚀 Competitive Advantage Maintained

Your development team's excellent practices are protecting your technology investment and maintaining competitive advantage through superior code quality."""
            return "## 🎉 Keep up the great work!\n\nYour code shows excellent connascence practices."
        
        if self._config.get('sales_mode'):
            return self._create_sales_recommendations(violations)
        elif self._config.get('executive_mode'): 
            return self._create_executive_recommendations(violations)
        else:
            return self._create_standard_recommendations(violations)
    
    def _create_standard_recommendations(self, violations: List[Violation]) -> str:
        """Standard technical recommendations."""
        lines = ["## 💡 Recommendations"]
        
        by_type = {}
        for violation in violations:
            type_key = violation.type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1
        
        recommendations = []
        
        if by_type.get("CoM", 0) > 5:
            recommendations.append(
                "🔧 **Extract Magic Literals**: Consider creating a constants module for numerous magic numbers and strings."
            )
        
        if by_type.get("CoP", 0) > 3:
            recommendations.append(
                "📝 **Use Keyword Arguments**: Functions with many positional parameters are hard to maintain."
            )
        
        if by_type.get("CoA", 0) > 2:
            recommendations.append(
                "♻️ **Eliminate Duplication**: Similar algorithms detected. Extract common logic."
            )
        
        critical_count = sum(1 for v in violations if v.severity.value == "critical")
        if critical_count > 0:
            recommendations.append(
                "🚨 **Address Critical Issues First**: Focus on critical violations as they represent significant design problems."
            )
        
        if not recommendations:
            recommendations.append(
                "🎯 **Review High-Weight Issues**: Focus on violations with the highest weight scores for maximum impact."
            )
        
        for rec in recommendations[:3]:
            lines.append(f"- {rec}")
        
        return "\n".join(lines)
    
    def _create_sales_recommendations(self, violations: List[Violation]) -> str:
        """Sales-focused recommendations emphasizing ROI."""
        total_hours = self._estimate_roi_hours(len(violations))
        
        return f"""## 📈 Investment Recommendations

**Immediate ROI Opportunity:** {total_hours} hours of developer productivity gains available

**Phase 1 (Week 1-2):** Address {sum(1 for v in violations if v.severity.value in ['critical', 'high'])} high-impact issues
- Eliminates technical debt compound interest
- Prevents future maintenance costs
- Improves team velocity

**Phase 2 (Month 2):** Systematic refactoring of remaining {len([v for v in violations if v.severity.value in ['medium', 'low']])} opportunities
- Establishes sustainable code quality practices  
- Reduces onboarding time for new developers
- Minimizes regression risk

**Ongoing Value:** Implementing these improvements creates a measurable competitive advantage through reduced development cycle times."""
    
    def _create_executive_recommendations(self, violations: List[Violation]) -> str:
        """Executive-level strategic recommendations."""
        critical_count = sum(1 for v in violations if v.severity.value == "critical")
        high_count = sum(1 for v in violations if v.severity.value == "high")
        
        return f"""## 🎯 Strategic Action Plan

**Immediate Actions Required ({critical_count + high_count} issues):**
- Allocate senior developer resources to critical issues
- Implement code review process improvements
- Establish quality gates for future deployments

**Medium-term Initiatives:**
- Developer training on coupling reduction techniques
- Automated quality monitoring integration
- Technical debt reduction sprint planning

**Risk Management:**
- Current technical debt represents manageable risk level
- Proactive remediation prevents compound maintenance costs
- Quality improvements support long-term scalability goals"""
    
    def _create_footer(self, result: AnalysisResult) -> str:
        """Create report footer with mode-appropriate content."""
        duration = getattr(result, 'analysis_duration_ms', 0)
        
        if self._config.get('sales_mode'):
            return f"""---
_Analysis completed in {duration}ms analyzing {result.total_files_analyzed} files_

**ROI Analysis**: These metrics demonstrate quantifiable technical debt reduction opportunities. 
🚀 **Next Step**: Schedule a technical debt remediation planning session to realize these productivity gains.

📞 [Contact Sales](mailto:sales@connascence.com) | 📚 [Enterprise Demo](https://connascence.com/demo)"""
        
        return f"""---
_Analysis completed in {duration}ms analyzing {result.total_files_analyzed} files_

**What is Connascence?** Connascence is a software engineering metric that measures the strength of coupling between components. Lower connascence leads to more maintainable code.

🔗 [Learn More](https://connascence.io) | 🛠️ [Connascence Analyzer](https://github.com/connascence/connascence-analyzer)"""
    
    def _estimate_roi_hours(self, violation_count: int) -> int:
        """Estimate ROI in developer hours."""
        # Conservative estimates based on typical refactoring time
        if violation_count == 0:
            return 0
        elif violation_count <= 10:
            return violation_count * 2  # 2 hours per issue
        elif violation_count <= 50:
            return 20 + (violation_count - 10) * 1.5  # Diminishing returns
        else:
            return 80 + (violation_count - 50) * 1  # Bulk improvements
    
    def _estimate_violation_impact(self, violation: Violation) -> float:
        """Estimate individual violation impact in hours."""
        base_impact = {"critical": 8, "high": 4, "medium": 2, "low": 1}
        return base_impact.get(violation.severity.value, 2)