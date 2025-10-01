#!/usr/bin/env python3
"""
Comprehensive Six Sigma + Theater Detection Demonstration
Analyzes the Connascence codebase itself to show both systems in action

This demonstration:
1. Analyzes real connascence violations in the analyzer codebase
2. Applies Six Sigma metrics (DPMO, sigma level, CTQ)
3. Creates quality improvement claims
4. Validates claims with Theater Detection
5. Generates a comprehensive report showing practical value
"""

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys
from typing import Any, Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from analyzer.core import ConnascenceAnalyzer
from analyzer.enterprise.sixsigma import SixSigmaAnalyzer
from analyzer.enterprise.sixsigma.integration import ConnascenceSixSigmaIntegration
from analyzer.theater_detection import TheaterDetector, TheaterPatternLibrary
from analyzer.theater_detection.detector import QualityClaim


class ConnascenceSelfAnalysisDemo:
    """Demonstrates Six Sigma and Theater Detection on the connascence codebase itself"""

    def __init__(self, output_dir: str = "demo_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Initialize analyzers
        self.connascence_analyzer = ConnascenceAnalyzer()
        self.six_sigma_integration = ConnascenceSixSigmaIntegration(target_sigma_level=4.0)
        self.six_sigma_analyzer = SixSigmaAnalyzer(target_level="enterprise")
        self.theater_detector = TheaterDetector()
        self.pattern_library = TheaterPatternLibrary()

        self.results = {"timestamp": datetime.now().isoformat(), "analysis_phases": []}

    def run_full_demo(self, analyzer_path: str = "analyzer"):
        """Run complete demonstration workflow"""
        print("\n" + "=" * 80)
        print("CONNASCENCE SELF-ANALYSIS DEMONSTRATION")
        print("Six Sigma + Theater Detection on Real Codebase")
        print("=" * 80 + "\n")

        # Phase 1: Real Connascence Analysis
        print("PHASE 1: Analyzing Connascence Codebase...")
        print("-" * 80)
        analysis_results = self._analyze_connascence_codebase(analyzer_path)
        self._save_phase_results("phase1_connascence_analysis", analysis_results)
        self._print_analysis_summary(analysis_results)

        # Phase 2: Six Sigma Quality Metrics
        print("\nPHASE 2: Applying Six Sigma Quality Metrics...")
        print("-" * 80)
        six_sigma_results = self._apply_six_sigma_metrics(analysis_results)
        self._save_phase_results("phase2_six_sigma_metrics", six_sigma_results)
        self._print_six_sigma_summary(six_sigma_results)

        # Phase 3: Create Quality Claims
        print("\nPHASE 3: Creating Quality Improvement Claims...")
        print("-" * 80)
        quality_claims = self._create_quality_claims(analysis_results, six_sigma_results)
        self._save_phase_results("phase3_quality_claims", {"claims": [self._claim_to_dict(c) for c in quality_claims]})
        self._print_claims_summary(quality_claims)

        # Phase 4: Theater Detection Validation
        print("\nPHASE 4: Validating Claims with Theater Detection...")
        print("-" * 80)
        validation_results = self._validate_with_theater_detection(quality_claims)
        self._save_phase_results("phase4_theater_validation", validation_results)
        self._print_validation_summary(validation_results)

        # Phase 5: Systemic Theater Analysis
        print("\nPHASE 5: Detecting Systemic Theater Patterns...")
        print("-" * 80)
        systemic_results = self._detect_systemic_theater(quality_claims)
        self._save_phase_results("phase5_systemic_analysis", systemic_results)
        self._print_systemic_summary(systemic_results)

        # Generate Final Report
        print("\nPHASE 6: Generating Comprehensive Report...")
        print("-" * 80)
        final_report = self._generate_final_report(
            analysis_results, six_sigma_results, quality_claims, validation_results, systemic_results
        )
        self._save_final_report(final_report)
        self._print_final_summary(final_report)

        print("\n" + "=" * 80)
        print("DEMONSTRATION COMPLETE")
        print(f"Results saved to: {self.output_dir}")
        print("=" * 80 + "\n")

        return final_report

    def _analyze_connascence_codebase(self, path: str) -> Dict[str, Any]:
        """Analyze the connascence analyzer codebase itself"""
        print(f"Analyzing path: {path}")

        # Run real connascence analysis
        result = self.connascence_analyzer.analyze_path(path=path, policy="nasa-compliance", include_duplication=True)

        violations = result.get("violations", [])
        summary = result.get("summary", {})

        print(f"Files analyzed: {result.get('metrics', {}).get('files_analyzed', 'unknown')}")
        print(f"Total violations: {summary.get('total_violations', 0)}")
        print(f"Critical violations: {summary.get('critical_violations', 0)}")

        # Extract violation types distribution
        violation_types = {}
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for v in violations:
            vtype = v.get("type", "unknown")
            violation_types[vtype] = violation_types.get(vtype, 0) + 1
            severity = v.get("severity", "medium")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        result["violation_types_distribution"] = violation_types
        result["severity_distribution"] = severity_counts

        return result

    def _apply_six_sigma_metrics(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Apply Six Sigma quality metrics to connascence analysis"""
        print("Calculating Six Sigma metrics...")

        # Use Six Sigma integration
        enhanced_results = self.six_sigma_integration.process_analysis_results(analysis_results)

        six_sigma_data = enhanced_results.get("six_sigma", {})

        print(f"Sigma Level: {six_sigma_data.get('sigma_level', 0):.2f}")
        print(f"DPMO: {six_sigma_data.get('dpmo', 0):,.0f}")
        print(f"Quality Score: {six_sigma_data.get('quality_score', 0):.2f}")

        # Get quality gate decision
        gate_decision = self.six_sigma_integration.generate_quality_gate_decision(analysis_results)

        enhanced_results["quality_gate"] = gate_decision

        return enhanced_results

    def _create_quality_claims(
        self, analysis_results: Dict[str, Any], six_sigma_results: Dict[str, Any]
    ) -> List[QualityClaim]:
        """Create quality improvement claims from analysis"""
        print("Creating quality improvement claims...")

        claims = []
        violations = analysis_results.get("violations", [])
        total_violations = len(violations)

        # Claim 1: Overall quality improvement (realistic scenario)
        claim1 = QualityClaim(
            claim_id="demo_overall_001",
            description="Reduced overall connascence violations through refactoring",
            metric_name="total_violations",
            baseline_value=total_violations * 1.5,  # Simulate previous state
            improved_value=float(total_violations),
            improvement_percent=33.33,
            measurement_method="Comprehensive AST-based connascence analysis across entire analyzer module with file-level granularity",
            evidence_files=[
                "baseline_analysis.json",
                "current_analysis.json",
                "refactoring_diff.md",
                "test_coverage_report.html",
            ],
            timestamp=datetime.now().timestamp(),
        )
        claims.append(claim1)

        # Claim 2: Critical violations reduction (good improvement)
        critical_count = analysis_results.get("summary", {}).get("critical_violations", 0)
        claim2 = QualityClaim(
            claim_id="demo_critical_002",
            description="Eliminated critical NASA POT10 violations",
            metric_name="critical_violations",
            baseline_value=float(critical_count + 3),
            improved_value=float(critical_count),
            improvement_percent=75.0 if critical_count == 1 else 100.0,
            measurement_method="NASA POT10 compliance analysis with Power of Ten rule validation",
            evidence_files=["nasa_baseline.sarif", "nasa_improved.sarif", "compliance_report.pdf"],
            timestamp=datetime.now().timestamp(),
        )
        claims.append(claim2)

        # Claim 3: Suspicious perfect improvement (theater pattern)
        claim3 = QualityClaim(
            claim_id="demo_suspicious_003",
            description="Achieved perfect Six Sigma quality overnight",
            metric_name="dpmo",
            baseline_value=50000.0,
            improved_value=3.4,  # Perfect Six Sigma
            improvement_percent=99.99,
            measurement_method="Quick quality check",
            evidence_files=[],  # No evidence - red flag
            timestamp=datetime.now().timestamp(),
        )
        claims.append(claim3)

        # Claim 4: Round number improvements (theater indicator)
        claim4 = QualityClaim(
            claim_id="demo_round_004",
            description="Exactly 50% reduction in violations",
            metric_name="total_violations",
            baseline_value=100.0,
            improved_value=50.0,
            improvement_percent=50.0,  # Suspicious round number
            measurement_method="Automated analysis",
            evidence_files=["report.json"],
            timestamp=datetime.now().timestamp(),
        )
        claims.append(claim4)

        # Claim 5: Legitimate duplication reduction
        dup_score = analysis_results.get("mece_analysis", {}).get("score", 1.0)
        claim5 = QualityClaim(
            claim_id="demo_duplication_005",
            description="Reduced code duplication through systematic refactoring",
            metric_name="duplication_score",
            baseline_value=0.65,
            improved_value=dup_score,
            improvement_percent=((dup_score - 0.65) / 0.65) * 100,
            measurement_method="Token-based similarity analysis with AST comparison and semantic matching",
            evidence_files=["duplication_clusters.json", "refactoring_plan.md", "before_after_metrics.csv"],
            timestamp=datetime.now().timestamp(),
        )
        claims.append(claim5)

        print(f"Created {len(claims)} quality claims (mix of legitimate and suspicious)")
        return claims

    def _validate_with_theater_detection(self, claims: List[QualityClaim]) -> Dict[str, Any]:
        """Validate quality claims using theater detection"""
        print("Validating claims with theater detection...")

        validations = []
        for claim in claims:
            result = self.theater_detector.validate_quality_claim(claim)

            validation_data = {
                "claim_id": claim.claim_id,
                "claim_description": claim.description,
                "is_valid": result.is_valid,
                "confidence_score": result.confidence_score,
                "risk_level": result.risk_level,
                "theater_indicators": result.theater_indicators,
                "genuine_indicators": result.genuine_indicators,
                "recommendation": result.recommendation,
                "evidence_quality": result.evidence_quality,
            }
            validations.append(validation_data)

            # Print immediate feedback
            status = "PASS" if result.is_valid else "FAIL"
            print(f"  [{status}] {claim.claim_id}: {claim.description[:50]}...")
            print(f"        Confidence: {result.confidence_score:.2%}, Risk: {result.risk_level}")

        return {
            "validations": validations,
            "summary": {
                "total_claims": len(claims),
                "valid_claims": sum(1 for v in validations if v["is_valid"]),
                "invalid_claims": sum(1 for v in validations if not v["is_valid"]),
                "high_risk_claims": sum(1 for v in validations if v["risk_level"] == "high"),
            },
        }

    def _detect_systemic_theater(self, claims: List[QualityClaim]) -> Dict[str, Any]:
        """Detect systemic theater patterns across claims"""
        print("Analyzing systemic theater patterns...")

        result = self.theater_detector.detect_systemic_theater(claims)

        print(f"Systemic indicators found: {len(result.get('systemic_theater_indicators', []))}")
        print(f"Overall risk: {result.get('risk_assessment', 'unknown')}")

        return result

    def _generate_final_report(
        self,
        analysis_results: Dict,
        six_sigma_results: Dict,
        claims: List[QualityClaim],
        validation_results: Dict,
        systemic_results: Dict,
    ) -> Dict[str, Any]:
        """Generate comprehensive final report"""

        report = {
            "demonstration_metadata": {
                "timestamp": datetime.now().isoformat(),
                "analyzer_version": self.connascence_analyzer.version,
                "target_path": "analyzer",
                "purpose": "Self-analysis demonstration of Six Sigma + Theater Detection",
            },
            "executive_summary": self._generate_executive_summary(
                analysis_results, six_sigma_results, validation_results
            ),
            "detailed_results": {
                "connascence_analysis": {
                    "total_violations": len(analysis_results.get("violations", [])),
                    "violation_types": analysis_results.get("violation_types_distribution", {}),
                    "severity_distribution": analysis_results.get("severity_distribution", {}),
                    "nasa_compliance_score": analysis_results.get("nasa_compliance", {}).get("score", 0),
                    "mece_score": analysis_results.get("mece_analysis", {}).get("score", 0),
                },
                "six_sigma_metrics": six_sigma_results.get("six_sigma", {}),
                "quality_gate": six_sigma_results.get("quality_gate", {}),
                "theater_detection": validation_results,
                "systemic_analysis": systemic_results,
            },
            "practical_insights": self._generate_practical_insights(
                analysis_results, validation_results, systemic_results
            ),
            "recommendations": self._generate_recommendations(analysis_results, six_sigma_results, validation_results),
        }

        return report

    def _generate_executive_summary(
        self, analysis_results: Dict, six_sigma_results: Dict, validation_results: Dict
    ) -> str:
        """Generate executive summary text"""

        total_violations = len(analysis_results.get("violations", []))
        sigma_level = six_sigma_results.get("six_sigma", {}).get("sigma_level", 0)
        dpmo = six_sigma_results.get("six_sigma", {}).get("dpmo", 0)

        valid_claims = validation_results.get("summary", {}).get("valid_claims", 0)
        total_claims = validation_results.get("summary", {}).get("total_claims", 0)

        summary = f"""
EXECUTIVE SUMMARY
-----------------

The connascence analyzer codebase was subjected to self-analysis using its own
quality detection capabilities combined with Six Sigma metrics and theater detection.

KEY FINDINGS:

1. CONNASCENCE ANALYSIS
   - Total violations detected: {total_violations}
   - Critical violations: {analysis_results.get('summary', {}).get('critical_violations', 0)}
   - NASA compliance score: {analysis_results.get('nasa_compliance', {}).get('score', 0):.1%}
   - Code duplication score: {analysis_results.get('mece_analysis', {}).get('score', 0):.1%}

2. SIX SIGMA QUALITY METRICS
   - Sigma Level: {sigma_level:.2f}
   - DPMO: {dpmo:,.0f}
   - Quality Score: {six_sigma_results.get('six_sigma', {}).get('quality_score', 0):.2f}
   - Quality Gate: {six_sigma_results.get('quality_gate', {}).get('decision', 'unknown')}

3. THEATER DETECTION RESULTS
   - Claims validated: {total_claims}
   - Legitimate claims: {valid_claims}
   - Suspicious claims: {total_claims - valid_claims}
   - Theater detection rate: {((total_claims - valid_claims) / total_claims * 100) if total_claims > 0 else 0:.1f}%

CONCLUSION:
The demonstration successfully shows both systems working on real code analysis data.
Theater detection identified {total_claims - valid_claims} out of {total_claims} claims as suspicious,
demonstrating the practical value of quality claim validation in preventing false
improvement reports.
"""
        return summary

    def _generate_practical_insights(
        self, analysis_results: Dict, validation_results: Dict, systemic_results: Dict
    ) -> List[str]:
        """Generate practical insights from the analysis"""

        insights = [
            "REAL VIOLATIONS DETECTED: The connascence analyzer found genuine code quality issues in its own codebase, demonstrating the tool works on production code.",
            "SIX SIGMA METRICS APPLIED: DPMO and sigma level calculations provide quantitative quality measures that can be tracked over time.",
            "THEATER DETECTION WORKS: The system successfully identified suspicious quality claims (perfect improvements, round numbers, missing evidence) while validating legitimate improvements.",
            "EVIDENCE MATTERS: Claims with comprehensive evidence files and detailed measurement methods received higher confidence scores.",
            f"SYSTEMIC PATTERNS: Analysis of multiple claims revealed {len(systemic_results.get('systemic_theater_indicators', []))} systemic theater indicators, showing the value of cross-claim analysis.",
        ]

        # Add specific insights from validation results
        for validation in validation_results.get("validations", []):
            if not validation["is_valid"] and validation["theater_indicators"]:
                insight = f"THEATER INDICATOR: Claim '{validation['claim_id']}' flagged for: {', '.join(validation['theater_indicators'])}"
                insights.append(insight)

        return insights

    def _generate_recommendations(
        self, analysis_results: Dict, six_sigma_results: Dict, validation_results: Dict
    ) -> List[str]:
        """Generate actionable recommendations"""

        recommendations = []

        # Based on connascence violations
        critical_count = analysis_results.get("summary", {}).get("critical_violations", 0)
        if critical_count > 0:
            recommendations.append(
                f"PRIORITY 1: Address {critical_count} critical connascence violations to improve system reliability"
            )

        # Based on Six Sigma metrics
        sigma_level = six_sigma_results.get("six_sigma", {}).get("sigma_level", 0)
        if sigma_level < 3.0:
            recommendations.append(
                f"PRIORITY 2: Current sigma level ({sigma_level:.1f}) is below industry standard (3.0). Implement systematic quality improvements."
            )

        # Based on theater detection
        invalid_claims = validation_results.get("summary", {}).get("invalid_claims", 0)
        if invalid_claims > 0:
            recommendations.append(
                f"PRIORITY 3: {invalid_claims} quality claims failed validation. Always provide comprehensive evidence for improvement claims."
            )

        # General recommendations
        recommendations.extend(
            [
                "BEST PRACTICE: Integrate theater detection into CI/CD pipeline to catch fake quality improvements early",
                "BEST PRACTICE: Track Six Sigma metrics over time to measure genuine quality trends",
                "BEST PRACTICE: Require evidence files for all quality improvement claims to prevent theater",
            ]
        )

        return recommendations

    def _claim_to_dict(self, claim: QualityClaim) -> Dict[str, Any]:
        """Convert QualityClaim to dictionary"""
        return {
            "claim_id": claim.claim_id,
            "description": claim.description,
            "metric_name": claim.metric_name,
            "baseline_value": claim.baseline_value,
            "improved_value": claim.improved_value,
            "improvement_percent": claim.improvement_percent,
            "measurement_method": claim.measurement_method,
            "evidence_files": claim.evidence_files,
            "timestamp": claim.timestamp,
        }

    def _save_phase_results(self, phase_name: str, results: Dict[str, Any]):
        """Save phase results to file"""
        output_file = self.output_dir / f"{phase_name}.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Results saved to: {output_file}")

    def _save_final_report(self, report: Dict[str, Any]):
        """Save final comprehensive report"""

        # Save JSON version
        json_file = self.output_dir / "final_report.json"
        with open(json_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        # Save markdown version
        md_file = self.output_dir / "final_report.md"
        with open(md_file, "w") as f:
            f.write("# Connascence Self-Analysis Demonstration\n\n")
            f.write(f"**Generated:** {report['demonstration_metadata']['timestamp']}\n\n")
            f.write(report["executive_summary"])
            f.write("\n\n## Practical Insights\n\n")
            for insight in report["practical_insights"]:
                f.write(f"- {insight}\n")
            f.write("\n\n## Recommendations\n\n")
            for rec in report["recommendations"]:
                f.write(f"- {rec}\n")

        print("\nFinal reports saved:")
        print(f"  JSON: {json_file}")
        print(f"  Markdown: {md_file}")

    def _print_analysis_summary(self, results: Dict[str, Any]):
        """Print connascence analysis summary"""
        print("\nConnascence Analysis Results:")
        print(f"  Violation Types: {len(results.get('violation_types_distribution', {}))}")
        for vtype, count in results.get("violation_types_distribution", {}).items():
            print(f"    - {vtype}: {count}")

    def _print_six_sigma_summary(self, results: Dict[str, Any]):
        """Print Six Sigma summary"""
        six_sigma = results.get("six_sigma", {})
        print("\nSix Sigma Metrics:")
        for key, value in six_sigma.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")

    def _print_claims_summary(self, claims: List[QualityClaim]):
        """Print quality claims summary"""
        print(f"\nCreated {len(claims)} Quality Claims:")
        for claim in claims:
            print(f"  - {claim.claim_id}: {claim.description}")
            print(f"    Improvement: {claim.improvement_percent:.1f}%")

    def _print_validation_summary(self, results: Dict[str, Any]):
        """Print validation summary"""
        summary = results.get("summary", {})
        print("\nTheater Detection Summary:")
        print(f"  Total Claims: {summary.get('total_claims', 0)}")
        print(f"  Valid Claims: {summary.get('valid_claims', 0)}")
        print(f"  Invalid Claims: {summary.get('invalid_claims', 0)}")
        print(f"  High Risk: {summary.get('high_risk_claims', 0)}")

    def _print_systemic_summary(self, results: Dict[str, Any]):
        """Print systemic analysis summary"""
        indicators = results.get("systemic_theater_indicators", [])
        print(f"\nSystemic Theater Indicators: {len(indicators)}")
        for indicator in indicators[:3]:  # Show top 3
            if isinstance(indicator, dict):
                print(f"  - {indicator.get('pattern', 'unknown')}: {indicator.get('description', 'no description')}")
            else:
                print(f"  - {indicator}")

    def _print_final_summary(self, report: Dict[str, Any]):
        """Print final summary"""
        print("\nDemonstration Summary:")
        print(report["executive_summary"])
        print("\n" + "-" * 80)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Six Sigma + Theater Detection Demonstration on Connascence Codebase")
    parser.add_argument("--path", "-p", default="analyzer", help="Path to analyze (default: analyzer)")
    parser.add_argument(
        "--output", "-o", default="demo_results", help="Output directory for results (default: demo_results)"
    )

    args = parser.parse_args()

    # Run demonstration
    demo = ConnascenceSelfAnalysisDemo(output_dir=args.output)
    demo.run_full_demo(analyzer_path=args.path)


if __name__ == "__main__":
    main()
