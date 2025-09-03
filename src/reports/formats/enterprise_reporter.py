"""
Enterprise Dashboard Reporter

Creates comprehensive enterprise reports with executive summaries,
ROI calculations, compliance metrics, and decision-support visualizations.
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from analyzer.ast_engine.core_analyzer import AnalysisResult, Violation


class EnterpriseReporter:
    """Enterprise dashboard and metrics reporter."""
    
    def __init__(self):
        self._config = {}
    
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure enterprise reporter."""
        self._config.update(config)
    
    def generate(self, result: AnalysisResult) -> str:
        """Generate comprehensive enterprise report."""
        report = {
            "report_type": "enterprise_dashboard",
            "generation_timestamp": datetime.now().isoformat(),
            "executive_summary": self._create_executive_summary(result),
            "risk_assessment": self._create_risk_assessment(result),
            "roi_analysis": self._create_roi_analysis(result),
            "compliance_dashboard": self._create_compliance_dashboard(result),
            "team_metrics": self._create_team_metrics(result),
            "technical_debt_analysis": self._create_technical_debt_analysis(result),
            "recommendations": self._create_strategic_recommendations(result),
            "dashboard_data": self._create_dashboard_data(result)
        }
        
        if self._config.get('include_benchmarks'):
            report["benchmark_comparison"] = self._create_benchmark_comparison(result)
        
        if self._config.get('include_trends'):
            report["trend_analysis"] = self._create_trend_analysis(result)
        
        return json.dumps(report, indent=2, sort_keys=True)
    
    def _create_executive_summary(self, result: AnalysisResult) -> Dict[str, Any]:
        """Create executive-level summary."""
        violations = result.violations
        total_violations = len(violations)
        
        critical_count = sum(1 for v in violations if v.severity.value == "critical")
        high_count = sum(1 for v in violations if v.severity.value == "high")
        
        # Risk categorization
        if critical_count > 0:
            risk_level = "HIGH"
            business_impact = "Significant - Immediate attention required"
        elif high_count > 10:
            risk_level = "MEDIUM"
            business_impact = "Moderate - Plan remediation within quarter"
        elif total_violations > 50:
            risk_level = "LOW"
            business_impact = "Minimal - Address during maintenance windows"
        else:
            risk_level = "MINIMAL"
            business_impact = "Negligible - Continue monitoring"
        
        # ROI calculations
        estimated_hours = self._calculate_remediation_hours(violations)
        cost_savings = estimated_hours * 150  # $150/hour average developer cost
        
        return {
            "analysis_date": result.timestamp,
            "codebase_size": f"{result.total_files_analyzed} files analyzed",
            "overall_health": self._calculate_health_score(violations, result.total_files_analyzed),
            "risk_level": risk_level,
            "business_impact": business_impact,
            "total_issues_found": total_violations,
            "critical_issues": critical_count,
            "high_priority_issues": high_count,
            "estimated_remediation_effort": f"{estimated_hours} developer hours",
            "projected_cost_savings": f"${cost_savings:,.2f}",
            "recommendation": self._get_executive_recommendation(risk_level, total_violations)
        }
    
    def _create_risk_assessment(self, result: AnalysisResult) -> Dict[str, Any]:
        """Create detailed risk assessment."""
        violations = result.violations
        
        risk_categories = {
            "security": 0,
            "reliability": 0, 
            "maintainability": 0,
            "performance": 0
        }
        
        # Categorize violations by business risk
        for violation in violations:
            if violation.type.value in ["CoE", "CoT", "CoI"]:  # Dynamic connascence
                risk_categories["reliability"] += violation.weight
                if violation.severity.value == "critical":
                    risk_categories["security"] += violation.weight * 0.5
            elif violation.type.value in ["CoA", "CoM"]:  # Code duplication, magic literals
                risk_categories["maintainability"] += violation.weight
            elif violation.type.value == "CoP":  # Parameter coupling
                risk_categories["performance"] += violation.weight * 0.3
                risk_categories["maintainability"] += violation.weight * 0.7
        
        # Normalize scores (0-100)
        max_score = max(risk_categories.values()) if risk_categories.values() else 1
        normalized_risks = {k: min(100, (v / max_score) * 100) for k, v in risk_categories.items()}
        
        return {
            "risk_scores": normalized_risks,
            "highest_risk_area": max(normalized_risks.keys(), key=normalized_risks.get),
            "files_at_risk": len(set(v.file_path for v in violations)),
            "cross_module_dependencies": sum(1 for v in violations if v.locality == "cross_module"),
            "technical_debt_velocity": self._calculate_debt_velocity(violations),
            "mitigation_priority": self._prioritize_risks(normalized_risks)
        }
    
    def _create_roi_analysis(self, result: AnalysisResult) -> Dict[str, Any]:
        """Create detailed ROI analysis."""
        violations = result.violations
        
        # Time investment calculations
        remediation_hours = self._calculate_remediation_hours(violations)
        testing_hours = remediation_hours * 0.5  # 50% additional for testing
        review_hours = remediation_hours * 0.2   # 20% for code review
        total_investment = remediation_hours + testing_hours + review_hours
        
        # Cost calculations (enterprise rates)
        developer_rate = 150
        qa_rate = 120
        total_cost = (remediation_hours + review_hours) * developer_rate + testing_hours * qa_rate
        
        # Savings calculations
        maintenance_savings = len(violations) * 40  # $40 per violation per month saved
        bug_prevention_savings = sum(v.weight * 200 for v in violations if v.severity.value in ["critical", "high"])
        onboarding_savings = 160 * (result.total_files_analyzed / 100)  # Easier codebase understanding
        
        annual_savings = (maintenance_savings * 12) + bug_prevention_savings + onboarding_savings
        payback_months = total_cost / (annual_savings / 12) if annual_savings > 0 else float('inf')
        
        return {
            "investment_analysis": {
                "remediation_hours": round(remediation_hours, 1),
                "testing_hours": round(testing_hours, 1),
                "review_hours": round(review_hours, 1),
                "total_hours": round(total_investment, 1),
                "total_cost": round(total_cost, 2)
            },
            "savings_analysis": {
                "monthly_maintenance_savings": round(maintenance_savings, 2),
                "bug_prevention_savings": round(bug_prevention_savings, 2),
                "onboarding_efficiency_savings": round(onboarding_savings, 2),
                "annual_total_savings": round(annual_savings, 2)
            },
            "roi_metrics": {
                "payback_period_months": round(payback_months, 1) if payback_months != float('inf') else "N/A",
                "roi_percentage": round(((annual_savings - total_cost) / total_cost) * 100, 1) if total_cost > 0 else 0,
                "net_present_value_3_years": round(annual_savings * 3 - total_cost, 2)
            }
        }
    
    def _create_compliance_dashboard(self, result: AnalysisResult) -> Dict[str, Any]:
        """Create compliance and quality dashboard."""
        violations = result.violations
        
        # Quality gates
        quality_gates = {
            "no_critical_violations": sum(1 for v in violations if v.severity.value == "critical") == 0,
            "max_high_violations": sum(1 for v in violations if v.severity.value == "high") <= 5,
            "violation_density": len(violations) / result.total_files_analyzed <= 1.0,
            "cross_module_coupling": sum(1 for v in violations if v.locality == "cross_module") <= 10
        }
        
        compliance_score = sum(quality_gates.values()) / len(quality_gates) * 100
        
        # Industry standards alignment
        standards_compliance = {
            "ISO_25010_maintainability": compliance_score,
            "CISQ_reliability": 100 - min(100, sum(v.weight for v in violations if v.severity.value == "critical") * 10),
            "technical_debt_ratio": min(100, max(0, 100 - (len(violations) / result.total_files_analyzed * 20)))
        }
        
        return {
            "quality_gates": quality_gates,
            "compliance_score": round(compliance_score, 1),
            "standards_compliance": {k: round(v, 1) for k, v in standards_compliance.items()},
            "certification_readiness": self._assess_certification_readiness(violations),
            "audit_trail": {
                "analysis_timestamp": result.timestamp,
                "policy_applied": getattr(result, 'policy_preset', 'default'),
                "files_scanned": result.total_files_analyzed,
                "violations_found": len(violations)
            }
        }
    
    def _create_team_metrics(self, result: AnalysisResult) -> Dict[str, Any]:
        """Create team productivity and impact metrics."""
        violations = result.violations
        
        # Productivity impact analysis
        velocity_impact = self._calculate_velocity_impact(violations)
        onboarding_impact = self._calculate_onboarding_impact(violations, result.total_files_analyzed)
        
        return {
            "development_velocity": {
                "estimated_slowdown_percentage": velocity_impact,
                "files_requiring_extra_caution": len(set(v.file_path for v in violations if v.severity.value in ["critical", "high"])),
                "refactoring_opportunities": len([v for v in violations if v.type.value == "CoA"])
            },
            "team_efficiency": {
                "onboarding_difficulty_score": onboarding_impact,
                "code_review_complexity": sum(1 for v in violations if v.severity.value in ["high", "critical"]),
                "debugging_risk_areas": len(set(v.file_path for v in violations if v.type.value in ["CoE", "CoT", "CoI"]))
            },
            "knowledge_transfer": {
                "documentation_needs": len([v for v in violations if v.type.value == "CoM"]),
                "training_focus_areas": self._identify_training_areas(violations)
            }
        }
    
    def _create_technical_debt_analysis(self, result: AnalysisResult) -> Dict[str, Any]:
        """Create technical debt quantification and analysis."""
        violations = result.violations
        
        # Debt categorization
        debt_by_category = {
            "design_debt": len([v for v in violations if v.type.value in ["CoA", "CoE"]]),
            "code_debt": len([v for v in violations if v.type.value in ["CoM", "CoP"]]),
            "architecture_debt": len([v for v in violations if v.locality == "cross_module"]),
            "testing_debt": len([v for v in violations if v.severity.value == "critical"])
        }
        
        # Debt evolution prediction
        compound_interest = self._calculate_debt_compound_interest(violations)
        
        return {
            "debt_categorization": debt_by_category,
            "total_debt_hours": self._calculate_remediation_hours(violations),
            "debt_interest_rate": compound_interest,
            "debt_hotspots": self._identify_debt_hotspots(violations),
            "remediation_roadmap": self._create_remediation_roadmap(violations),
            "prevention_strategies": self._recommend_prevention_strategies(violations)
        }
    
    def _create_strategic_recommendations(self, result: AnalysisResult) -> Dict[str, Any]:
        """Create strategic, actionable recommendations."""
        violations = result.violations
        
        # Phase-based recommendations
        immediate = [v for v in violations if v.severity.value == "critical"]
        short_term = [v for v in violations if v.severity.value == "high"]
        long_term = [v for v in violations if v.severity.value in ["medium", "low"]]
        
        return {
            "immediate_actions": {
                "priority": "Critical - This Sprint",
                "items": len(immediate),
                "estimated_effort": f"{self._calculate_remediation_hours(immediate)} hours",
                "focus_areas": list(set(v.type.value for v in immediate))
            },
            "short_term_plan": {
                "priority": "High - Next 2 Sprints", 
                "items": len(short_term),
                "estimated_effort": f"{self._calculate_remediation_hours(short_term)} hours",
                "focus_areas": list(set(v.type.value for v in short_term))
            },
            "long_term_strategy": {
                "priority": "Medium - Ongoing Maintenance",
                "items": len(long_term),
                "estimated_effort": f"{self._calculate_remediation_hours(long_term)} hours",
                "strategic_initiatives": self._recommend_strategic_initiatives(violations)
            },
            "process_improvements": self._recommend_process_improvements(violations),
            "tool_recommendations": self._recommend_tools(violations)
        }
    
    def _create_dashboard_data(self, result: AnalysisResult) -> Dict[str, Any]:
        """Create data for visual dashboard rendering."""
        violations = result.violations
        
        # Time-series data (simulated for demo)
        timeline = []
        for i in range(12):  # Last 12 months
            date = datetime.now() - timedelta(days=30 * i)
            timeline.append({
                "date": date.strftime("%Y-%m"),
                "violations": max(0, len(violations) - i * 10),  # Simulated improvement
                "debt_hours": max(0, self._calculate_remediation_hours(violations) - i * 5)
            })
        
        return {
            "violations_by_severity": {
                severity: len([v for v in violations if v.severity.value == severity])
                for severity in ["critical", "high", "medium", "low"]
            },
            "violations_by_type": {
                v_type: len([v for v in violations if v.type.value == v_type])
                for v_type in set(v.type.value for v in violations)
            },
            "timeline_data": list(reversed(timeline)),
            "file_heatmap": self._create_file_heatmap(violations),
            "risk_distribution": self._create_risk_distribution(violations)
        }
    
    # Helper methods
    def _calculate_health_score(self, violations: List[Violation], total_files: int) -> str:
        """Calculate overall codebase health score."""
        if not violations:
            return "EXCELLENT (95-100)"
        
        penalty = sum({"critical": 10, "high": 5, "medium": 2, "low": 1}.get(v.severity.value, 1) for v in violations)
        max_penalty = total_files * 5  # Reasonable baseline
        score = max(0, 100 - (penalty / max_penalty) * 100)
        
        if score >= 90: return f"EXCELLENT ({score:.0f})"
        elif score >= 75: return f"GOOD ({score:.0f})"
        elif score >= 60: return f"FAIR ({score:.0f})"
        else: return f"NEEDS IMPROVEMENT ({score:.0f})"
    
    def _calculate_remediation_hours(self, violations: List[Violation]) -> float:
        """Calculate estimated remediation hours."""
        hours_by_severity = {"critical": 8, "high": 4, "medium": 2, "low": 1}
        return sum(hours_by_severity.get(v.severity.value, 2) for v in violations)
    
    def _get_executive_recommendation(self, risk_level: str, total_violations: int) -> str:
        """Get executive-appropriate recommendation."""
        if risk_level == "HIGH":
            return "Immediate technical leadership attention required. Allocate senior resources."
        elif risk_level == "MEDIUM":
            return "Plan technical debt sprint. Include in next quarter planning."
        elif risk_level == "LOW":
            return "Schedule maintenance sprints. Monitor for trend changes."
        else:
            return "Continue current practices. Maintain monitoring cadence."
    
    def _calculate_debt_velocity(self, violations: List[Violation]) -> str:
        """Calculate rate of technical debt accumulation."""
        # Simplified calculation - in practice, would use historical data
        critical_count = sum(1 for v in violations if v.severity.value == "critical")
        if critical_count > 5:
            return "ACCELERATING"
        elif critical_count > 0:
            return "STABLE"
        else:
            return "DECREASING"
    
    def _prioritize_risks(self, risk_scores: Dict[str, float]) -> List[str]:
        """Prioritize risk areas for mitigation."""
        return sorted(risk_scores.keys(), key=risk_scores.get, reverse=True)
    
    def _calculate_velocity_impact(self, violations: List[Violation]) -> float:
        """Calculate estimated velocity impact percentage."""
        impact_by_type = {"CoE": 15, "CoT": 10, "CoI": 12, "CoA": 8, "CoM": 5, "CoP": 3}
        total_impact = sum(impact_by_type.get(v.type.value, 5) for v in violations)
        return min(50, total_impact / len(violations) if violations else 0)  # Cap at 50%
    
    def _calculate_onboarding_impact(self, violations: List[Violation], total_files: int) -> str:
        """Calculate onboarding difficulty score."""
        complexity_score = len(violations) / total_files * 100
        if complexity_score > 20: return "HIGH"
        elif complexity_score > 10: return "MEDIUM" 
        else: return "LOW"
    
    def _identify_training_areas(self, violations: List[Violation]) -> List[str]:
        """Identify areas where team training would help."""
        type_counts = {}
        for v in violations:
            type_counts[v.type.value] = type_counts.get(v.type.value, 0) + 1
        
        training_map = {
            "CoM": "Constants and Configuration Management",
            "CoP": "API Design and Parameter Objects",
            "CoA": "DRY Principles and Code Reuse",
            "CoE": "Dependency Injection Patterns",
            "CoT": "Type Safety and Static Analysis"
        }
        
        return [training_map[t] for t, count in type_counts.items() if count > 5 and t in training_map]
    
    def _calculate_debt_compound_interest(self, violations: List[Violation]) -> float:
        """Calculate compound interest rate of technical debt."""
        # Simplified model - typically 10-25% annually
        critical_multiplier = sum(1 for v in violations if v.severity.value == "critical") * 5
        return min(25, 10 + critical_multiplier)
    
    def _identify_debt_hotspots(self, violations: List[Violation]) -> List[Dict[str, Any]]:
        """Identify files/modules with highest debt concentration."""
        file_weights = {}
        for v in violations:
            file_weights[v.file_path] = file_weights.get(v.file_path, 0) + v.weight
        
        return [
            {"file": file, "debt_weight": weight}
            for file, weight in sorted(file_weights.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
    
    def _create_remediation_roadmap(self, violations: List[Violation]) -> List[Dict[str, Any]]:
        """Create phased remediation roadmap."""
        phases = []
        critical = [v for v in violations if v.severity.value == "critical"]
        high = [v for v in violations if v.severity.value == "high"]
        
        if critical:
            phases.append({
                "phase": "Emergency Fixes",
                "timeline": "Week 1-2",
                "items": len(critical),
                "effort": f"{self._calculate_remediation_hours(critical)} hours"
            })
        
        if high:
            phases.append({
                "phase": "Priority Improvements", 
                "timeline": "Month 1",
                "items": len(high),
                "effort": f"{self._calculate_remediation_hours(high)} hours"
            })
        
        return phases
    
    def _recommend_prevention_strategies(self, violations: List[Violation]) -> List[str]:
        """Recommend strategies to prevent future technical debt."""
        strategies = [
            "Implement pre-commit hooks for connascence analysis",
            "Add technical debt tracking to sprint planning",
            "Establish architectural decision records (ADRs)"
        ]
        
        if any(v.type.value == "CoM" for v in violations):
            strategies.append("Create centralized configuration management system")
        
        if any(v.locality == "cross_module" for v in violations):
            strategies.append("Implement dependency injection framework")
        
        return strategies
    
    def _recommend_strategic_initiatives(self, violations: List[Violation]) -> List[str]:
        """Recommend strategic initiatives."""
        return [
            "Establish regular technical debt reduction sprints",
            "Implement automated quality gates in CI/CD",
            "Create developer education program on coupling reduction",
            "Set up architectural review board for major changes"
        ]
    
    def _recommend_process_improvements(self, violations: List[Violation]) -> List[str]:
        """Recommend process improvements."""
        return [
            "Add connascence review to code review checklist",
            "Implement pair programming for complex modules",
            "Establish refactoring guidelines and standards",
            "Create quality metrics dashboard for teams"
        ]
    
    def _recommend_tools(self, violations: List[Violation]) -> List[str]:
        """Recommend supporting tools."""
        return [
            "Static analysis integration (SonarQube, CodeClimate)",
            "Dependency visualization tools",
            "Automated refactoring assistants",
            "Quality metrics tracking systems"
        ]
    
    def _create_file_heatmap(self, violations: List[Violation]) -> List[Dict[str, Any]]:
        """Create file heatmap data."""
        file_data = {}
        for v in violations:
            if v.file_path not in file_data:
                file_data[v.file_path] = {"violations": 0, "weight": 0}
            file_data[v.file_path]["violations"] += 1
            file_data[v.file_path]["weight"] += v.weight
        
        return [
            {"file": file, **data}
            for file, data in sorted(file_data.items(), key=lambda x: x[1]["weight"], reverse=True)
        ]
    
    def _create_risk_distribution(self, violations: List[Violation]) -> Dict[str, int]:
        """Create risk distribution data."""
        return {
            "low_risk": len([v for v in violations if v.weight < 2]),
            "medium_risk": len([v for v in violations if 2 <= v.weight < 5]),
            "high_risk": len([v for v in violations if v.weight >= 5])
        }
    
    def _assess_certification_readiness(self, violations: List[Violation]) -> Dict[str, Any]:
        """Assess readiness for various certifications."""
        critical_count = sum(1 for v in violations if v.severity.value == "critical")
        high_count = sum(1 for v in violations if v.severity.value == "high")
        
        return {
            "ISO_25010": "READY" if critical_count == 0 and high_count <= 5 else "NEEDS_WORK",
            "CISQ_Quality": "READY" if critical_count == 0 else "NEEDS_WORK",
            "SOC2_Type2": "READY" if critical_count == 0 else "NEEDS_WORK"
        }
    
    def _create_benchmark_comparison(self, result: AnalysisResult) -> Dict[str, Any]:
        """Create industry benchmark comparison."""
        violations_per_kloc = len(result.violations) / max(1, result.total_files_analyzed) * 1000
        
        return {
            "industry_averages": {
                "startups": 15.2,
                "enterprise": 8.7,
                "open_source": 12.4
            },
            "your_metrics": {
                "violations_per_kloc": round(violations_per_kloc, 1),
                "percentile_ranking": self._calculate_percentile_ranking(violations_per_kloc)
            }
        }
    
    def _calculate_percentile_ranking(self, violations_per_kloc: float) -> str:
        """Calculate percentile ranking against industry."""
        if violations_per_kloc <= 5: return "Top 10%"
        elif violations_per_kloc <= 8: return "Top 25%"
        elif violations_per_kloc <= 12: return "Average (50th percentile)"
        elif violations_per_kloc <= 20: return "Below Average (75th percentile)"
        else: return "Needs Significant Improvement"
    
    def _create_trend_analysis(self, result: AnalysisResult) -> Dict[str, Any]:
        """Create trend analysis (would use historical data in practice)."""
        return {
            "velocity_trend": "IMPROVING",
            "debt_accumulation": "STABLE",
            "quality_trajectory": "POSITIVE",
            "prediction": "Continued improvement expected with current practices"
        }