"""
Six Sigma Analyzer for Connascence Detection

Integrates Six Sigma quality metrics with connascence analysis
to provide enterprise-grade quality measurement and improvement.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import json
import logging
from datetime import datetime

from .telemetry import SixSigmaTelemetry, QualityLevel
from .calculator import CTQCalculator, ProcessCapability

logger = logging.getLogger(__name__)


@dataclass
class SixSigmaAnalysisResult:
    """Result of Six Sigma analysis on connascence violations"""
    file_path: Path
    dpmo: float
    sigma_level: float
    rty: float
    quality_level: str
    violations_by_type: Dict[str, int]
    violations_by_severity: Dict[str, int]
    process_capability: Tuple[float, float]
    improvement_suggestions: List[str]
    ctq_metrics: Dict[str, float]


class SixSigmaAnalyzer:
    """
    Six Sigma analyzer for connascence violations

    Provides enterprise-grade quality analysis by applying Six Sigma
    methodology to connascence detection results.
    """

    # Target thresholds for different quality levels
    QUALITY_TARGETS = {
        "world_class": {"sigma": 6.0, "dpmo": 3.4},
        "enterprise": {"sigma": 5.0, "dpmo": 233},
        "standard": {"sigma": 4.0, "dpmo": 6210},
        "baseline": {"sigma": 3.0, "dpmo": 66807}
    }

    # CTQ (Critical To Quality) weights for connascence types
    CTQ_WEIGHTS = {
        'identity': 0.15,    # High impact on maintainability
        'meaning': 0.12,     # High impact on clarity
        'algorithm': 0.18,   # Very high impact on correctness
        'position': 0.08,    # Medium impact
        'execution': 0.20,   # Very high impact on runtime
        'timing': 0.22,      # Highest impact on reliability
        'values': 0.10,      # Medium impact
        'type': 0.12,        # High impact on safety
        'convention': 0.05   # Lower impact
    }

    def __init__(self, target_level: str = "enterprise"):
        """
        Initialize Six Sigma analyzer

        Args:
            target_level: Target quality level (world_class, enterprise, standard, baseline)
        """
        self.telemetry = SixSigmaTelemetry()
        self.ctq_calculator = CTQCalculator()
        self.process_capability = ProcessCapability()
        self.target_level = self.QUALITY_TARGETS.get(target_level, self.QUALITY_TARGETS["enterprise"])
        self.analysis_results = []

    def analyze_violations(self, violations: List[Dict[str, Any]],
                          file_path: Optional[Path] = None) -> SixSigmaAnalysisResult:
        """
        Analyze connascence violations using Six Sigma methodology

        Args:
            violations: List of violation dictionaries
            file_path: Optional file path being analyzed

        Returns:
            SixSigmaAnalysisResult with comprehensive metrics
        """
        # Reset session for new analysis
        self.telemetry.reset_session()

        # Process violations
        violations_by_type = {}
        violations_by_severity = {}

        for violation in violations:
            vtype = violation.get('type', 'unknown')
            severity = violation.get('severity', 'low')

            # Record in telemetry
            self.telemetry.record_connascence_violation(vtype, severity)

            # Count by type
            violations_by_type[vtype] = violations_by_type.get(vtype, 0) + 1

            # Count by severity
            violations_by_severity[severity] = violations_by_severity.get(severity, 0) + 1

        # Record file analysis
        total_violations = len(violations)
        total_checks = 100  # Assume 100 potential violation points per file
        self.telemetry.record_file_analyzed(total_violations, total_checks)

        # Generate metrics
        metrics = self.telemetry.generate_metrics_snapshot()

        # Calculate CTQ metrics
        ctq_metrics = self._calculate_ctq_metrics(violations_by_type, total_violations)

        # Calculate process capability
        if total_violations > 0:
            violation_rates = [violations_by_type.get(vtype, 0) / total_violations
                             for vtype in self.CTQ_WEIGHTS.keys()]
            cp, cpk = self.telemetry.calculate_process_capability(
                violation_rates, 0.0, 0.1  # Target: 0%, USL: 10% violation rate
            )
        else:
            cp, cpk = float('inf'), float('inf')

        # Generate improvement suggestions
        suggestions = self._generate_improvement_suggestions(
            metrics.dpmo,
            metrics.sigma_level,
            violations_by_type,
            violations_by_severity
        )

        # Create result
        result = SixSigmaAnalysisResult(
            file_path=file_path or Path("."),
            dpmo=metrics.dpmo,
            sigma_level=metrics.sigma_level,
            rty=metrics.rty,
            quality_level=metrics.quality_level.name if metrics.quality_level else "UNKNOWN",
            violations_by_type=violations_by_type,
            violations_by_severity=violations_by_severity,
            process_capability=(cp, cpk),
            improvement_suggestions=suggestions,
            ctq_metrics=ctq_metrics
        )

        self.analysis_results.append(result)
        return result

    def _calculate_ctq_metrics(self, violations_by_type: Dict[str, int],
                               total_violations: int) -> Dict[str, float]:
        """Calculate Critical To Quality metrics"""
        if total_violations == 0:
            return {vtype: 0.0 for vtype in self.CTQ_WEIGHTS.keys()}

        ctq_metrics = {}
        for vtype, weight in self.CTQ_WEIGHTS.items():
            count = violations_by_type.get(vtype, 0)
            # CTQ score = (violation_count / total) * weight * 100
            ctq_metrics[vtype] = round((count / total_violations) * weight * 100, 2)

        # Add composite CTQ score
        ctq_metrics['composite'] = round(sum(ctq_metrics.values()), 2)

        return ctq_metrics

    def _generate_improvement_suggestions(self, dpmo: float, sigma_level: float,
                                         violations_by_type: Dict[str, int],
                                         violations_by_severity: Dict[str, int]) -> List[str]:
        """Generate actionable improvement suggestions"""
        suggestions = []

        # Sigma level suggestions
        if sigma_level < self.target_level["sigma"]:
            gap = self.target_level["sigma"] - sigma_level
            suggestions.append(
                f"Improve sigma level by {gap:.1f} to reach {self.target_level['sigma']:.1f} target"
            )

        # DPMO suggestions
        if dpmo > self.target_level["dpmo"]:
            reduction_needed = dpmo - self.target_level["dpmo"]
            suggestions.append(
                f"Reduce DPMO by {reduction_needed:.0f} to reach target of {self.target_level['dpmo']:.1f}"
            )

        # Critical violations focus
        if violations_by_severity.get('critical', 0) > 0:
            suggestions.append(
                f"Priority: Eliminate {violations_by_severity['critical']} critical violations immediately"
            )

        # High-impact connascence types
        high_impact_types = sorted(
            [(vtype, count) for vtype, count in violations_by_type.items()],
            key=lambda x: x[1] * self.CTQ_WEIGHTS.get(x[0], 0.1),
            reverse=True
        )[:3]

        for vtype, count in high_impact_types:
            if count > 0:
                suggestions.append(
                    f"Focus on {vtype} violations ({count} found) - CTQ weight: {self.CTQ_WEIGHTS.get(vtype, 0):.0%}"
                )

        # Process improvement suggestions
        if sigma_level < 4.0:
            suggestions.append("Implement automated detection and fixing for common violations")
        if sigma_level < 5.0:
            suggestions.append("Establish code review gates with Six Sigma metrics")
        if dpmo > 1000:
            suggestions.append("Create violation prevention guidelines and training")

        return suggestions

    def analyze_codebase(self, violations_by_file: Dict[Path, List[Dict]]) -> Dict[str, Any]:
        """
        Analyze entire codebase using Six Sigma methodology

        Args:
            violations_by_file: Dictionary mapping file paths to violation lists

        Returns:
            Comprehensive Six Sigma analysis report
        """
        all_results = []
        for file_path, violations in violations_by_file.items():
            result = self.analyze_violations(violations, file_path)
            all_results.append(result)

        # Aggregate metrics
        total_dpmo = sum(r.dpmo for r in all_results) / len(all_results) if all_results else 0
        avg_sigma = sum(r.sigma_level for r in all_results) / len(all_results) if all_results else 6.0
        avg_rty = sum(r.rty for r in all_results) / len(all_results) if all_results else 100.0

        # Aggregate violations
        total_by_type = {}
        total_by_severity = {}
        for result in all_results:
            for vtype, count in result.violations_by_type.items():
                total_by_type[vtype] = total_by_type.get(vtype, 0) + count
            for severity, count in result.violations_by_severity.items():
                total_by_severity[severity] = total_by_severity.get(severity, 0) + count

        # Determine overall quality level
        overall_quality = self.telemetry.get_quality_level(total_dpmo)

        # Generate DMAIC improvement plan
        dmaic_plan = self._generate_dmaic_plan(
            total_dpmo, avg_sigma, total_by_type, total_by_severity
        )

        return {
            "summary": {
                "files_analyzed": len(all_results),
                "average_dpmo": round(total_dpmo, 2),
                "average_sigma_level": round(avg_sigma, 2),
                "average_rty": round(avg_rty, 2),
                "overall_quality": overall_quality.name,
                "target_achieved": avg_sigma >= self.target_level["sigma"]
            },
            "violations": {
                "by_type": total_by_type,
                "by_severity": total_by_severity,
                "total": sum(total_by_type.values())
            },
            "file_results": [
                {
                    "file": str(r.file_path),
                    "dpmo": r.dpmo,
                    "sigma_level": r.sigma_level,
                    "quality": r.quality_level
                }
                for r in all_results
            ],
            "dmaic_improvement_plan": dmaic_plan,
            "trend_analysis": self.telemetry.get_trend_analysis(30),
            "timestamp": datetime.now().isoformat()
        }

    def _generate_dmaic_plan(self, dpmo: float, sigma_level: float,
                            violations_by_type: Dict[str, int],
                            violations_by_severity: Dict[str, int]) -> Dict[str, Any]:
        """Generate DMAIC (Define, Measure, Analyze, Improve, Control) plan"""
        return {
            "define": {
                "problem": f"Code quality at {sigma_level:.1f} sigma, below target {self.target_level['sigma']:.1f}",
                "goal": f"Achieve {self.target_level['sigma']:.1f} sigma level",
                "scope": "All connascence violations in codebase",
                "timeline": "30-60 days"
            },
            "measure": {
                "current_dpmo": dpmo,
                "current_sigma": sigma_level,
                "baseline_violations": sum(violations_by_type.values()),
                "critical_violations": violations_by_severity.get('critical', 0)
            },
            "analyze": {
                "root_causes": self._identify_root_causes(violations_by_type),
                "pareto_analysis": self._perform_pareto_analysis(violations_by_type),
                "impact_matrix": self._create_impact_matrix(violations_by_type)
            },
            "improve": {
                "quick_wins": self._identify_quick_wins(violations_by_severity),
                "systematic_improvements": self._plan_systematic_improvements(violations_by_type),
                "automation_opportunities": self._identify_automation_opportunities(violations_by_type)
            },
            "control": {
                "monitoring_plan": "Weekly Six Sigma metrics review",
                "control_limits": {
                    "upper": self.target_level["dpmo"],
                    "lower": 0
                },
                "sustainability_measures": [
                    "Automated quality gates in CI/CD",
                    "Regular Six Sigma training",
                    "Continuous improvement cycles"
                ]
            }
        }

    def _identify_root_causes(self, violations_by_type: Dict[str, int]) -> List[str]:
        """Identify root causes of violations"""
        root_causes = []

        total = sum(violations_by_type.values())
        if total == 0:
            return ["No violations detected"]

        # Analyze violation patterns
        for vtype, count in sorted(violations_by_type.items(), key=lambda x: x[1], reverse=True)[:3]:
            percentage = (count / total) * 100
            if vtype == 'algorithm':
                root_causes.append(f"Algorithm duplication ({percentage:.0f}%): Lack of shared utilities")
            elif vtype == 'timing':
                root_causes.append(f"Timing issues ({percentage:.0f}%): Missing synchronization patterns")
            elif vtype == 'execution':
                root_causes.append(f"Execution order ({percentage:.0f}%): Unclear dependencies")
            elif vtype == 'identity':
                root_causes.append(f"Identity coupling ({percentage:.0f}%): Poor encapsulation")
            else:
                root_causes.append(f"{vtype.title()} violations ({percentage:.0f}%)")

        return root_causes

    def _perform_pareto_analysis(self, violations_by_type: Dict[str, int]) -> Dict[str, Any]:
        """Perform Pareto analysis (80/20 rule)"""
        if not violations_by_type:
            return {"vital_few": [], "trivial_many": []}

        sorted_violations = sorted(violations_by_type.items(), key=lambda x: x[1], reverse=True)
        total = sum(violations_by_type.values())
        cumulative = 0
        vital_few = []
        trivial_many = []

        for vtype, count in sorted_violations:
            cumulative += count
            percentage = (cumulative / total) * 100
            if percentage <= 80:
                vital_few.append({"type": vtype, "count": count, "percentage": round((count/total)*100, 1)})
            else:
                trivial_many.append({"type": vtype, "count": count})

        return {
            "vital_few": vital_few,
            "trivial_many": trivial_many,
            "recommendation": f"Focus on {len(vital_few)} violation types for 80% impact"
        }

    def _create_impact_matrix(self, violations_by_type: Dict[str, int]) -> List[Dict[str, Any]]:
        """Create impact-effort matrix for prioritization"""
        matrix = []
        for vtype, count in violations_by_type.items():
            impact = self.CTQ_WEIGHTS.get(vtype, 0.1) * count
            # Estimate effort based on violation type
            effort_map = {
                'convention': 1,  # Easy to fix
                'identity': 3,
                'meaning': 2,
                'values': 2,
                'position': 4,
                'type': 3,
                'algorithm': 5,
                'execution': 6,
                'timing': 7  # Hardest to fix
            }
            effort = effort_map.get(vtype, 5)

            quadrant = "quick_win" if impact > 5 and effort < 4 else \
                      "major_project" if impact > 5 and effort >= 4 else \
                      "fill_in" if impact <= 5 and effort < 4 else "low_priority"

            matrix.append({
                "type": vtype,
                "count": count,
                "impact": round(impact, 2),
                "effort": effort,
                "quadrant": quadrant
            })

        return sorted(matrix, key=lambda x: x['impact'] / x['effort'], reverse=True)

    def _identify_quick_wins(self, violations_by_severity: Dict[str, int]) -> List[str]:
        """Identify quick win improvements"""
        quick_wins = []

        if violations_by_severity.get('critical', 0) > 0:
            quick_wins.append(f"Fix {violations_by_severity['critical']} critical violations (immediate impact)")

        if violations_by_severity.get('high', 0) > 5:
            quick_wins.append(f"Address {violations_by_severity['high']} high-severity violations")

        quick_wins.extend([
            "Enable auto-fix for convention violations",
            "Add pre-commit hooks for basic violations",
            "Create shared utilities to reduce algorithm duplication"
        ])

        return quick_wins[:5]  # Top 5 quick wins

    def _plan_systematic_improvements(self, violations_by_type: Dict[str, int]) -> List[Dict[str, str]]:
        """Plan systematic improvements"""
        improvements = []

        for vtype in ['timing', 'execution', 'algorithm']:
            if violations_by_type.get(vtype, 0) > 0:
                improvements.append({
                    "violation_type": vtype,
                    "action": f"Refactor {vtype} connascence patterns",
                    "expected_impact": f"Reduce {vtype} violations by 50%",
                    "timeline": "2-4 weeks"
                })

        return improvements

    def _identify_automation_opportunities(self, violations_by_type: Dict[str, int]) -> List[str]:
        """Identify opportunities for automation"""
        opportunities = []

        if sum(violations_by_type.values()) > 50:
            opportunities.append("Implement automated violation detection in CI/CD")

        if violations_by_type.get('convention', 0) > 10:
            opportunities.append("Configure automatic code formatting")

        if violations_by_type.get('algorithm', 0) > 5:
            opportunities.append("Create code generation templates for common patterns")

        opportunities.append("Set up Six Sigma metrics dashboard")
        opportunities.append("Automate violation trend reporting")

        return opportunities

    def export_report(self, output_path: Path):
        """Export comprehensive Six Sigma report"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "target_level": self.target_level,
            "telemetry": self.telemetry.export_metrics(),
            "analysis_results": [
                {
                    "file": str(r.file_path),
                    "dpmo": r.dpmo,
                    "sigma_level": r.sigma_level,
                    "rty": r.rty,
                    "quality_level": r.quality_level,
                    "violations": {
                        "by_type": r.violations_by_type,
                        "by_severity": r.violations_by_severity
                    },
                    "ctq_metrics": r.ctq_metrics,
                    "suggestions": r.improvement_suggestions
                }
                for r in self.analysis_results
            ]
        }

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Six Sigma report exported to {output_path}")