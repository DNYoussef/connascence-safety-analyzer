"""
Integration module for Six Sigma with Connascence Analyzer

Provides seamless integration between connascence detection and
Six Sigma quality metrics.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import logging
from datetime import datetime

from .analyzer import SixSigmaAnalyzer
from .telemetry import SixSigmaTelemetry

logger = logging.getLogger(__name__)


class ConnascenceSixSigmaIntegration:
    """
    Integrates Six Sigma quality metrics with connascence analysis

    This class provides the bridge between the connascence analyzer's
    violation detection and Six Sigma's quality measurement framework.
    """

    def __init__(self, target_sigma_level: float = 5.0):
        """
        Initialize integration

        Args:
            target_sigma_level: Target sigma level (default 5.0 for enterprise)
        """
        self.analyzer = SixSigmaAnalyzer(self._get_target_level(target_sigma_level))
        self.telemetry = SixSigmaTelemetry()
        self.violation_history = []

    def _get_target_level(self, sigma_level: float) -> str:
        """Map sigma level to target level name"""
        if sigma_level >= 6.0:
            return "world_class"
        elif sigma_level >= 5.0:
            return "enterprise"
        elif sigma_level >= 4.0:
            return "standard"
        else:
            return "baseline"

    def process_analysis_results(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process connascence analysis results with Six Sigma metrics

        Args:
            analysis_results: Results from connascence analyzer

        Returns:
            Enhanced results with Six Sigma metrics
        """
        # Extract violations from results
        violations = self._extract_violations(analysis_results)

        # Analyze with Six Sigma
        six_sigma_result = self.analyzer.analyze_violations(violations)

        # Enhance original results
        enhanced_results = analysis_results.copy()
        enhanced_results['six_sigma'] = {
            'dpmo': six_sigma_result.dpmo,
            'sigma_level': six_sigma_result.sigma_level,
            'rty': six_sigma_result.rty,
            'quality_level': six_sigma_result.quality_level,
            'process_capability': {
                'cp': six_sigma_result.process_capability[0],
                'cpk': six_sigma_result.process_capability[1]
            },
            'ctq_metrics': six_sigma_result.ctq_metrics,
            'improvement_suggestions': six_sigma_result.improvement_suggestions
        }

        # Add trend if we have history
        if len(self.violation_history) > 0:
            enhanced_results['six_sigma']['trend'] = self._calculate_trend()

        # Store for trending
        self.violation_history.append({
            'violations': violations,
            'metrics': enhanced_results['six_sigma']
        })

        return enhanced_results

    def _extract_violations(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract violations from analysis results"""
        violations = []

        # Handle different result formats
        if 'violations' in analysis_results:
            violations = analysis_results['violations']
        elif 'results' in analysis_results:
            for file_result in analysis_results['results']:
                if 'violations' in file_result:
                    violations.extend(file_result['violations'])

        return violations

    def _calculate_trend(self) -> Dict[str, Any]:
        """Calculate quality trend from history"""
        if len(self.violation_history) < 2:
            return {"status": "insufficient_data"}

        recent = self.violation_history[-5:]  # Last 5 analyses
        dpmo_values = [h['metrics']['dpmo'] for h in recent]
        sigma_values = [h['metrics']['sigma_level'] for h in recent]

        # Calculate trend direction
        dpmo_trend = "improving" if dpmo_values[-1] < dpmo_values[0] else "declining"
        sigma_trend = "improving" if sigma_values[-1] > sigma_values[0] else "declining"

        return {
            "dpmo_trend": dpmo_trend,
            "sigma_trend": sigma_trend,
            "analyses_compared": len(recent)
        }

    def generate_quality_gate_decision(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate quality gate pass/fail decision based on Six Sigma metrics

        Args:
            analysis_results: Connascence analysis results

        Returns:
            Quality gate decision with details
        """
        # Process results to get Six Sigma metrics
        enhanced = self.process_analysis_results(analysis_results)
        six_sigma = enhanced['six_sigma']

        # Define quality gate criteria
        gate_criteria = {
            'sigma_level': {'threshold': 4.0, 'actual': six_sigma['sigma_level']},
            'dpmo': {'threshold': 6210, 'actual': six_sigma['dpmo']},
            'rty': {'threshold': 80.0, 'actual': six_sigma['rty']},
            'critical_violations': {'threshold': 0, 'actual': self._count_critical_violations(analysis_results)}
        }

        # Evaluate each criterion
        gate_results = {}
        all_passed = True
        for criterion, values in gate_criteria.items():
            if criterion in ['sigma_level', 'rty']:
                passed = values['actual'] >= values['threshold']
            else:  # dpmo, critical_violations - lower is better
                passed = values['actual'] <= values['threshold']

            gate_results[criterion] = {
                'passed': passed,
                'threshold': values['threshold'],
                'actual': values['actual']
            }
            all_passed = all_passed and passed

        return {
            'decision': 'PASS' if all_passed else 'FAIL',
            'criteria': gate_results,
            'recommendations': six_sigma['improvement_suggestions'][:3] if not all_passed else [],
            'quality_level': six_sigma['quality_level']
        }

    def _count_critical_violations(self, analysis_results: Dict[str, Any]) -> int:
        """Count critical violations in results"""
        violations = self._extract_violations(analysis_results)
        return sum(1 for v in violations if v.get('severity', '').lower() == 'critical')

    def generate_executive_report(self, analysis_results: Dict[str, Any]) -> str:
        """
        Generate executive-level Six Sigma quality report

        Args:
            analysis_results: Connascence analysis results

        Returns:
            Formatted executive report
        """
        enhanced = self.process_analysis_results(analysis_results)
        six_sigma = enhanced['six_sigma']

        report = []
        report.append("=" * 60)
        report.append("CONNASCENCE ANALYSIS - SIX SIGMA QUALITY REPORT")
        report.append("=" * 60)
        report.append("")

        # Executive Summary
        report.append("EXECUTIVE SUMMARY")
        report.append("-" * 40)
        report.append(f"Quality Level: {six_sigma['quality_level']}")
        report.append(f"Sigma Level: {six_sigma['sigma_level']:.1f}σ")
        report.append(f"DPMO: {six_sigma['dpmo']:.0f}")
        report.append(f"RTY: {six_sigma['rty']:.1f}%")
        report.append("")

        # Quality Gate
        gate = self.generate_quality_gate_decision(analysis_results)
        report.append("QUALITY GATE STATUS")
        report.append("-" * 40)
        report.append(f"Decision: {gate['decision']}")
        for criterion, result in gate['criteria'].items():
            status = "✓" if result['passed'] else "✗"
            report.append(f"  {status} {criterion}: {result['actual']:.1f} (target: {result['threshold']:.1f})")
        report.append("")

        # Top Issues
        if six_sigma.get('ctq_metrics'):
            report.append("CRITICAL TO QUALITY METRICS")
            report.append("-" * 40)
            top_issues = sorted(
                [(k, v) for k, v in six_sigma['ctq_metrics'].items() if k != 'composite'],
                key=lambda x: x[1],
                reverse=True
            )[:3]
            for issue, score in top_issues:
                report.append(f"  • {issue}: {score:.1f}")
            report.append(f"  Composite Score: {six_sigma['ctq_metrics'].get('composite', 0):.1f}")
            report.append("")

        # Recommendations
        report.append("TOP RECOMMENDATIONS")
        report.append("-" * 40)
        for i, suggestion in enumerate(six_sigma['improvement_suggestions'][:3], 1):
            report.append(f"{i}. {suggestion}")
        report.append("")

        # Trend
        if 'trend' in six_sigma:
            trend = six_sigma['trend']
            if trend.get('status') != 'insufficient_data':
                report.append("QUALITY TREND")
                report.append("-" * 40)
                report.append(f"DPMO Trend: {trend['dpmo_trend'].upper()}")
                report.append(f"Sigma Trend: {trend['sigma_trend'].upper()}")
                report.append(f"Based on last {trend['analyses_compared']} analyses")
                report.append("")

        report.append("=" * 60)

        return "\n".join(report)

    def export_dashboard_data(self, analysis_results: Dict[str, Any],
                            output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Export data formatted for Six Sigma dashboard

        Args:
            analysis_results: Connascence analysis results
            output_path: Optional path to save dashboard data

        Returns:
            Dashboard-formatted data
        """
        enhanced = self.process_analysis_results(analysis_results)
        six_sigma = enhanced['six_sigma']

        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'sigma_level': six_sigma['sigma_level'],
                'dpmo': six_sigma['dpmo'],
                'rty': six_sigma['rty'],
                'quality_level': six_sigma['quality_level']
            },
            'gauges': {
                'sigma': {
                    'value': six_sigma['sigma_level'],
                    'min': 1,
                    'max': 6,
                    'target': 5,
                    'zones': [
                        {'from': 1, 'to': 3, 'color': 'red'},
                        {'from': 3, 'to': 4, 'color': 'yellow'},
                        {'from': 4, 'to': 5, 'color': 'green'},
                        {'from': 5, 'to': 6, 'color': 'blue'}
                    ]
                },
                'dpmo': {
                    'value': six_sigma['dpmo'],
                    'min': 0,
                    'max': 100000,
                    'target': 6210,
                    'zones': [
                        {'from': 0, 'to': 233, 'color': 'blue'},
                        {'from': 233, 'to': 6210, 'color': 'green'},
                        {'from': 6210, 'to': 66807, 'color': 'yellow'},
                        {'from': 66807, 'to': 100000, 'color': 'red'}
                    ]
                }
            },
            'charts': {
                'violations_by_type': self._format_for_chart(
                    six_sigma.get('violations_by_type', {}),
                    'Violations by Type'
                ),
                'ctq_metrics': self._format_for_chart(
                    {k: v for k, v in six_sigma.get('ctq_metrics', {}).items() if k != 'composite'},
                    'CTQ Metrics'
                )
            },
            'quality_gate': self.generate_quality_gate_decision(analysis_results),
            'trends': self._generate_trend_data()
        }

        if output_path:
            with open(output_path, 'w') as f:
                json.dump(dashboard_data, f, indent=2, default=str)

        return dashboard_data

    def _format_for_chart(self, data: Dict[str, Any], title: str) -> Dict[str, Any]:
        """Format data for chart display"""
        return {
            'title': title,
            'type': 'bar',
            'data': {
                'labels': list(data.keys()),
                'values': list(data.values())
            }
        }

    def _generate_trend_data(self) -> List[Dict[str, Any]]:
        """Generate trend data from history"""
        if len(self.violation_history) < 2:
            return []

        trend_data = []
        for i, record in enumerate(self.violation_history[-10:]):  # Last 10 records
            trend_data.append({
                'index': i,
                'dpmo': record['metrics']['dpmo'],
                'sigma_level': record['metrics']['sigma_level'],
                'rty': record['metrics']['rty']
            })

        return trend_data

    def integrate_with_ci_cd(self, analysis_results: Dict[str, Any],
                            fail_on_quality_gate: bool = True) -> int:
        """
        Integration point for CI/CD pipelines

        Args:
            analysis_results: Connascence analysis results
            fail_on_quality_gate: Whether to return non-zero exit code on gate failure

        Returns:
            Exit code (0 for pass, 1 for fail)
        """
        # Generate quality gate decision
        gate = self.generate_quality_gate_decision(analysis_results)

        # Print report to console
        print(self.generate_executive_report(analysis_results))

        # Export metrics for CI/CD artifacts
        self.export_dashboard_data(
            analysis_results,
            Path('./.connascence-six-sigma-metrics.json')
        )

        # Return appropriate exit code
        if fail_on_quality_gate and gate['decision'] == 'FAIL':
            logger.error("Quality gate FAILED - Six Sigma metrics below threshold")
            return 1

        logger.info("Quality gate PASSED - Six Sigma metrics acceptable")
        return 0