#!/usr/bin/env python3
"""
Comprehensive Connascence Analysis Tool
Processes the 35MB FULL_CODEBASE_ANALYSIS.json with 95,395 violations
"""

from collections import Counter, defaultdict
import json
from pathlib import Path


class ConnascenceAnalyzer:
    def __init__(self, analysis_file):
        """Initialize analyzer with the massive dataset"""
        self.analysis_file = analysis_file
        self.data = None
        self.violations = []
        self.critical_violations = []
        self.violation_stats = defaultdict(int)

    def load_analysis(self):
        """Load and parse the 35MB analysis file"""
        print(f"Loading massive dataset: {self.analysis_file}")
        try:
            with open(self.analysis_file, encoding="utf-8") as f:
                self.data = json.load(f)

            self.violations = self.data.get("violations", [])
            print(f"Loaded {len(self.violations)} violations")

            # Extract critical violations
            self.critical_violations = [v for v in self.violations if v.get("severity") == "critical"]
            print(f"Found {len(self.critical_violations)} critical violations")

        except Exception as e:
            print(f"Error loading analysis: {e}")
            return False
        return True

    def analyze_violation_breakdown(self):
        """Comprehensive breakdown of all 95,395 violations"""
        print("\n=== VIOLATION BREAKDOWN ANALYSIS ===")

        # By severity
        severity_counts = Counter()
        # By type
        type_counts = Counter()
        # By folder
        folder_counts = defaultdict(int)
        # By file
        file_counts = defaultdict(int)

        for violation in self.violations:
            severity_counts[violation.get("severity", "unknown")] += 1
            type_counts[violation.get("type", "unknown")] += 1

            file_path = violation.get("file_path", "")
            if file_path:
                # Extract folder
                path_parts = file_path.replace("..\\", "").split("\\")
                if path_parts:
                    folder = path_parts[0]
                    folder_counts[folder] += 1
                    file_counts[file_path] += 1

        results = {
            "severity_breakdown": dict(severity_counts),
            "type_breakdown": dict(type_counts.most_common()),
            "folder_breakdown": dict(sorted(folder_counts.items(), key=lambda x: x[1], reverse=True)),
            "top_problematic_files": dict(Counter(file_counts).most_common(20)),
        }

        return results

    def analyze_mece_duplication(self):
        """MECE Analysis of Code Duplication Across ALL Folders"""
        print("\n=== MECE DUPLICATION ANALYSIS ===")

        # Focus on Connascence of Algorithm (CoA) violations
        coa_violations = [v for v in self.violations if v.get("type") == "connascence_of_algorithm"]

        print(f"Found {len(coa_violations)} Connascence of Algorithm violations")

        # Group by description to find duplicated patterns
        duplication_patterns = defaultdict(list)
        for violation in coa_violations:
            desc = violation.get("description", "")
            duplication_patterns[desc].append(violation)

        # Find most duplicated patterns
        most_duplicated = sorted(duplication_patterns.items(), key=lambda x: len(x[1]), reverse=True)[:10]

        # Analyze cross-folder duplication
        cross_folder_duplication = {}
        for pattern, violations in duplication_patterns.items():
            folders = set()
            for v in violations:
                file_path = v.get("file_path", "")
                if file_path:
                    folder = file_path.replace("..\\", "").split("\\")[0]
                    folders.add(folder)
            if len(folders) > 1:
                cross_folder_duplication[pattern] = list(folders)  # Convert set to list for JSON

        return {
            "total_coa_violations": len(coa_violations),
            "unique_duplication_patterns": len(duplication_patterns),
            "most_duplicated_patterns": [(pattern, len(violations)) for pattern, violations in most_duplicated],
            "cross_folder_duplications": cross_folder_duplication,
            "mece_score": self._calculate_mece_score(duplication_patterns),
        }

    def analyze_architectural_issues(self):
        """Cross-Codebase Architectural Analysis"""
        print("\n=== ARCHITECTURAL ANALYSIS ===")

        # God objects analysis
        god_object_violations = [v for v in self.violations if "god" in v.get("description", "").lower()]

        # NASA Power of Ten violations
        nasa_violations = [
            v
            for v in self.violations
            if "nasa" in v.get("rule_id", "").lower() or "power_of_ten" in v.get("rule_id", "")
        ]

        # Coupling analysis
        coupling_violations = [
            v
            for v in self.violations
            if "coupling" in v.get("type", "") or "coupling" in v.get("description", "").lower()
        ]

        # Hotspot analysis - files with multiple violation types
        file_violation_types = defaultdict(set)
        for violation in self.violations:
            file_path = violation.get("file_path", "")
            violation_type = violation.get("type", "")
            if file_path and violation_type:
                file_violation_types[file_path].add(violation_type)

        # Find hotspots (files with 3+ violation types)
        hotspots = {
            file_path: list(types)  # Convert set to list for JSON
            for file_path, types in file_violation_types.items()
            if len(types) >= 3
        }

        return {
            "god_objects": len(god_object_violations),
            "nasa_violations": len(nasa_violations),
            "coupling_violations": len(coupling_violations),
            "architectural_hotspots": len(hotspots),
            "top_hotspots": dict(sorted(hotspots.items(), key=lambda x: len(x[1]), reverse=True)[:10]),
        }

    def calculate_component_quality_scores(self):
        """Quality Score Breakdown by Components"""
        print("\n=== COMPONENT QUALITY ANALYSIS ===")

        # Group violations by folder
        folder_violations = defaultdict(list)
        folder_file_counts = defaultdict(set)

        for violation in self.violations:
            file_path = violation.get("file_path", "")
            if file_path:
                folder = file_path.replace("..\\", "").split("\\")[0]
                folder_violations[folder].append(violation)
                folder_file_counts[folder].add(file_path)

        # Calculate quality scores for each component
        component_scores = {}
        for folder, violations in folder_violations.items():
            file_count = len(folder_file_counts[folder])
            violation_count = len(violations)
            critical_count = len([v for v in violations if v.get("severity") == "critical"])

            # Quality score calculation (0-1 scale)
            # Factors: violations per file, critical violations ratio, total violations
            violations_per_file = violation_count / max(file_count, 1)
            critical_ratio = critical_count / max(violation_count, 1)

            # Lower score = worse quality
            quality_score = max(0, 1 - (violations_per_file / 100) - (critical_ratio * 0.5))

            component_scores[folder] = {
                "quality_score": round(quality_score, 3),
                "total_violations": violation_count,
                "critical_violations": critical_count,
                "file_count": file_count,
                "violations_per_file": round(violations_per_file, 2),
            }

        # Sort by quality score
        sorted_components = sorted(component_scores.items(), key=lambda x: x[1]["quality_score"])

        return {
            "component_scores": component_scores,
            "worst_components": sorted_components[:5],
            "best_components": sorted_components[-5:],
            "average_quality": round(
                sum(s["quality_score"] for s in component_scores.values()) / len(component_scores), 3
            ),
        }

    def analyze_critical_violations(self):
        """Deep Dive into Critical Violations"""
        print("\n=== CRITICAL VIOLATIONS ANALYSIS ===")

        if not self.critical_violations:
            return {"message": "No critical violations found"}

        # Group by type
        critical_by_type = defaultdict(list)
        critical_by_folder = defaultdict(list)

        for violation in self.critical_violations:
            violation_type = violation.get("type", "unknown")
            critical_by_type[violation_type].append(violation)

            file_path = violation.get("file_path", "")
            if file_path:
                folder = file_path.replace("..\\", "").split("\\")[0]
                critical_by_folder[folder].append(violation)

        # Risk assessment
        risk_assessment = {}
        for violation_type, violations in critical_by_type.items():
            risk_assessment[violation_type] = {
                "count": len(violations),
                "business_risk": self._assess_business_risk(violation_type),
                "technical_debt_hours": len(violations) * self._estimate_fix_time(violation_type),
            }

        return {
            "total_critical": len(self.critical_violations),
            "critical_by_type": {k: len(v) for k, v in critical_by_type.items()},
            "critical_by_folder": {k: len(v) for k, v in critical_by_folder.items()},
            "risk_assessment": risk_assessment,
            "estimated_total_debt_hours": sum(r["technical_debt_hours"] for r in risk_assessment.values()),
        }

    def _calculate_mece_score(self, duplication_patterns):
        """Calculate MECE (Mutually Exclusive, Collectively Exhaustive) score"""
        if not duplication_patterns:
            return 1.0

        total_duplications = sum(len(violations) for violations in duplication_patterns.values())
        unique_patterns = len(duplication_patterns)

        # MECE score: lower duplications relative to patterns = better score
        mece_score = max(0, 1 - (total_duplications / (unique_patterns * 10)))
        return round(mece_score, 3)

    def _assess_business_risk(self, violation_type):
        """Assess business risk level for violation types"""
        high_risk = ["security", "data", "auth", "validation"]
        medium_risk = ["performance", "coupling", "complexity"]

        violation_lower = violation_type.lower()
        if any(risk in violation_lower for risk in high_risk):
            return "HIGH"
        elif any(risk in violation_lower for risk in medium_risk):
            return "MEDIUM"
        return "LOW"

    def _estimate_fix_time(self, violation_type):
        """Estimate fix time in hours for different violation types"""
        time_map = {"security": 8, "coupling": 4, "algorithm": 2, "naming": 1, "complexity": 6}

        violation_lower = violation_type.lower()
        for key, hours in time_map.items():
            if key in violation_lower:
                return hours
        return 3  # default

    def generate_comprehensive_report(self):
        """Generate the complete analysis report"""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE CONNASCENCE CODEBASE ANALYSIS")
        print("=" * 80)

        if not self.load_analysis():
            return None

        # Run all analyses
        violation_breakdown = self.analyze_violation_breakdown()
        mece_analysis = self.analyze_mece_duplication()
        architectural_analysis = self.analyze_architectural_issues()
        quality_scores = self.calculate_component_quality_scores()
        critical_analysis = self.analyze_critical_violations()

        report = {
            "metadata": {
                "total_violations": len(self.violations),
                "critical_violations": len(self.critical_violations),
                "overall_quality_score": self.data.get("summary", {}).get("overall_quality_score", 0),
                "analysis_timestamp": self.data.get("metadata", {}).get("timestamp"),
                "dataset_size_mb": round(Path(self.analysis_file).stat().st_size / (1024 * 1024), 1),
            },
            "violation_breakdown": violation_breakdown,
            "mece_duplication_analysis": mece_analysis,
            "architectural_analysis": architectural_analysis,
            "component_quality_scores": quality_scores,
            "critical_violations_analysis": critical_analysis,
        }

        return report


def main():
    analyzer = ConnascenceAnalyzer("FULL_CODEBASE_ANALYSIS.json")
    report = analyzer.generate_comprehensive_report()

    if report:
        # Save detailed report
        output_file = "docs/COMPREHENSIVE_ANALYSIS_REPORT.json"
        Path("docs").mkdir(exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print("\n=== ANALYSIS COMPLETE ===")
        print(f"Detailed report saved to: {output_file}")
        print(f"Dataset processed: {report['metadata']['dataset_size_mb']} MB")
        print(f"Total violations analyzed: {report['metadata']['total_violations']:,}")

        return output_file

    return None


if __name__ == "__main__":
    main()
