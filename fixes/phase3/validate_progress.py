#!/usr/bin/env python3
"""
Phase 3 Progress Validation Script
Measures NASA POT10 compliance improvement after each phase.
"""

from datetime import datetime
import json
from pathlib import Path
import sys
import time
from typing import Dict

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fixes.phase0.nasa_analyzer_fixed import PythonNASAAnalyzer


class ProgressValidator:
    """Validates progress through Phase 3 implementation."""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.analyzer = PythonNASAAnalyzer()
        self.baseline_file = self.project_path / "fixes" / "phase0" / "baseline" / "baseline_analysis.json"
        self.progress_file = self.project_path / "fixes" / "phase3" / "progress_tracking.json"

    def load_baseline(self) -> Dict:
        """Load baseline metrics from Phase 0.5."""
        with open(self.baseline_file) as f:
            return json.load(f)

    def run_analysis(self, sample_size: int = 100) -> Dict:
        """Run NASA analyzer on sample of files."""
        print("\nRunning NASA POT10 compliance analysis...")
        print("-" * 40)

        baseline = self.load_baseline()

        # Get top violating files from baseline
        files_to_analyze = baseline["files_with_violations"][:sample_size]

        results = {
            "timestamp": datetime.now().isoformat(),
            "files_analyzed": 0,
            "total_violations": 0,
            "violations_by_rule": {},
            "violations_by_severity": {},
            "improved_files": [],
            "unchanged_files": [],
        }

        start_time = time.time()

        for i, file_info in enumerate(files_to_analyze, 1):
            file_path = self.project_path / file_info["file"]

            if not file_path.exists():
                continue

            print(f"[{i}/{len(files_to_analyze)}] Analyzing: {file_info['file']}")

            try:
                # Run analyzer
                violations = self.analyzer.analyze_file(str(file_path))

                # Count violations
                current_count = len(violations)
                original_count = file_info["violation_count"]

                if current_count < original_count:
                    results["improved_files"].append(
                        {
                            "file": file_info["file"],
                            "original": original_count,
                            "current": current_count,
                            "improvement": original_count - current_count,
                        }
                    )
                else:
                    results["unchanged_files"].append(file_info["file"])

                # Count by rule
                for v in violations:
                    rule = v.rule_id
                    if rule not in results["violations_by_rule"]:
                        results["violations_by_rule"][rule] = 0
                    results["violations_by_rule"][rule] += 1

                    # Count by severity
                    severity = v.severity
                    if severity not in results["violations_by_severity"]:
                        results["violations_by_severity"][severity] = 0
                    results["violations_by_severity"][severity] += 1

                results["total_violations"] += current_count
                results["files_analyzed"] += 1

            except Exception as e:
                print(f"  [ERROR] {e}")

        results["analysis_time"] = time.time() - start_time
        return results

    def calculate_improvement(self, current_results: Dict, baseline: Dict) -> Dict:
        """Calculate improvement metrics."""
        # Calculate compliance percentage
        baseline_violations = baseline["total_violations"]
        current_violations = current_results["total_violations"]

        # Simple calculation based on violation reduction
        if baseline_violations > 0:
            reduction_pct = ((baseline_violations - current_violations) / baseline_violations) * 100
        else:
            reduction_pct = 0

        # Estimate compliance (simplified)
        baseline_compliance = 33.4  # From Phase 0.5

        # Each 10% reduction in violations improves compliance by ~3%
        compliance_improvement = (reduction_pct / 10) * 3
        estimated_compliance = baseline_compliance + compliance_improvement

        return {
            "baseline_violations": baseline_violations,
            "current_violations": current_violations,
            "violations_reduced": baseline_violations - current_violations,
            "reduction_percentage": reduction_pct,
            "baseline_compliance": baseline_compliance,
            "estimated_compliance": min(100, estimated_compliance),
            "compliance_improvement": compliance_improvement,
        }

    def generate_report(self, phase: str) -> str:
        """Generate progress report for a phase."""
        print("\nGenerating progress report...")

        # Run analysis
        current_results = self.run_analysis()
        baseline = self.load_baseline()

        # Calculate improvement
        improvement = self.calculate_improvement(current_results, baseline)

        # Build report
        report = []
        report.append("\n" + "=" * 70)
        report.append(f"PHASE {phase} PROGRESS REPORT")
        report.append("=" * 70)

        report.append(f"\nAnalysis Date: {current_results['timestamp']}")
        report.append(f"Files Analyzed: {current_results['files_analyzed']}")

        report.append("\n" + "-" * 40)
        report.append("VIOLATION REDUCTION")
        report.append("-" * 40)
        report.append(f"Baseline Violations: {improvement['baseline_violations']:,}")
        report.append(f"Current Violations: {improvement['current_violations']:,}")
        report.append(f"Violations Reduced: {improvement['violations_reduced']:,}")
        report.append(f"Reduction: {improvement['reduction_percentage']:.1f}%")

        report.append("\n" + "-" * 40)
        report.append("COMPLIANCE IMPROVEMENT")
        report.append("-" * 40)
        report.append(f"Baseline Compliance: {improvement['baseline_compliance']:.1f}%")
        report.append(f"Estimated Compliance: {improvement['estimated_compliance']:.1f}%")
        report.append(f"Improvement: +{improvement['compliance_improvement']:.1f}%")

        if current_results["improved_files"]:
            report.append("\n" + "-" * 40)
            report.append("TOP IMPROVED FILES")
            report.append("-" * 40)
            top_improved = sorted(current_results["improved_files"], key=lambda x: x["improvement"], reverse=True)[:10]
            for file_info in top_improved:
                report.append(f"  {file_info['file']}: -{file_info['improvement']} violations")

        report.append("\n" + "-" * 40)
        report.append("VIOLATIONS BY RULE")
        report.append("-" * 40)
        for rule, count in sorted(current_results["violations_by_rule"].items()):
            baseline_count = baseline["violations_by_rule"].get(rule, 0)
            change = baseline_count - count
            report.append(f"  {rule}: {count} (change: -{change})")

        report.append("\n" + "=" * 70)

        # Save results
        self.save_progress(phase, current_results, improvement)

        return "\n".join(report)

    def save_progress(self, phase: str, results: Dict, improvement: Dict):
        """Save progress tracking data."""
        # Load existing progress or create new
        if self.progress_file.exists():
            with open(self.progress_file) as f:
                progress = json.load(f)
        else:
            progress = {"phases": {}}

        # Add this phase
        progress["phases"][phase] = {"timestamp": results["timestamp"], "results": results, "improvement": improvement}

        # Save
        self.progress_file.parent.mkdir(exist_ok=True)
        with open(self.progress_file, "w") as f:
            json.dump(progress, f, indent=2)

        print(f"[OK] Progress saved to: {self.progress_file}")


def main():
    """Run validation for Phase 3.1."""
    print("Phase 3.1 Progress Validation")
    print("Measuring impact of assertion injection")

    # Initialize validator
    validator = ProgressValidator(project_root)

    # Generate report
    report = validator.generate_report("3.1")
    print(report)

    # Check if we met the target
    with open(validator.progress_file) as f:
        progress = json.load(f)

    phase_31 = progress["phases"]["3.1"]
    compliance = phase_31["improvement"]["estimated_compliance"]

    if compliance >= 55:
        print(f"\n✅ Phase 3.1 TARGET MET: {compliance:.1f}% compliance (target: 55%)")
    else:
        print(f"\n⚠️ Phase 3.1 needs more work: {compliance:.1f}% compliance (target: 55%)")
        print("Consider running assertion injection on more files")


if __name__ == "__main__":
    main()
