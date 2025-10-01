#!/usr/bin/env python3
"""
Enhanced Linter Integration for Connascence Analysis

This module provides comprehensive integration between standard linters (Ruff, Pylint)
and connascence detection, addressing the 35% linter integration completeness gap.

Key Features:
- Advanced rule mapping between linter rules and connascence types
- Cross-tool correlation analysis
- NASA Power of Ten compliance alignment
- Unified diagnostic reporting
- Enhanced magic literal detection beyond basic PLR2004
"""

import asyncio
from dataclasses import dataclass
import json
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class LinterRule:
    """Represents a linter rule with connascence mapping."""

    rule_code: str
    linter: str
    connascence_type: str
    description: str
    severity: str
    nasa_rule: Optional[str] = None
    autofix_available: bool = False


@dataclass
class CorrelationResult:
    """Results from correlating linter and connascence findings."""

    correlation_score: float
    overlapping_files: Set[str]
    unique_linter_findings: List[Dict]
    unique_connascence_findings: List[Dict]
    aligned_findings: List[Tuple[Dict, Dict]]
    recommendation: str


class EnhancedLinterIntegration:
    """Enhanced linter integration with deep connascence correlation."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.rule_mappings = self._initialize_rule_mappings()
        self.nasa_rule_alignment = self._initialize_nasa_alignment()
        self.magic_literal_patterns = self._initialize_magic_literal_patterns()

    def _initialize_rule_mappings(self) -> Dict[str, LinterRule]:
        """Initialize comprehensive rule mappings."""
        return {
            # Ruff -> Connascence Mappings
            "PLR2004": LinterRule(
                rule_code="PLR2004",
                linter="ruff",
                connascence_type="CoM",
                description="Magic value used in comparison",
                severity="medium",
                nasa_rule="Rule 5: No magic numbers",
                autofix_available=False,
            ),
            "PLR0913": LinterRule(
                rule_code="PLR0913",
                linter="ruff",
                connascence_type="CoP",
                description="Too many arguments",
                severity="medium",
                nasa_rule="Rule 6: Restrict function size",
                autofix_available=False,
            ),
            "PLR0915": LinterRule(
                rule_code="PLR0915",
                linter="ruff",
                connascence_type="CoA",
                description="Too many statements",
                severity="medium",
                nasa_rule="Rule 6: Restrict function size",
                autofix_available=False,
            ),
            "PLR0912": LinterRule(
                rule_code="PLR0912",
                linter="ruff",
                connascence_type="CoA",
                description="Too many branches",
                severity="medium",
                nasa_rule="Rule 6: Restrict function size",
                autofix_available=False,
            ),
            "C901": LinterRule(
                rule_code="C901",
                linter="ruff",
                connascence_type="CoA",
                description="Function too complex",
                severity="high",
                nasa_rule="Rule 6: Restrict function size",
                autofix_available=False,
            ),
            "N801": LinterRule(
                rule_code="N801",
                linter="ruff",
                connascence_type="CoN",
                description="Class name should use CapWords",
                severity="low",
                nasa_rule="Rule 9: Use preprocessor judiciously",
                autofix_available=True,
            ),
            "N802": LinterRule(
                rule_code="N802",
                linter="ruff",
                connascence_type="CoN",
                description="Function name should be lowercase",
                severity="low",
                nasa_rule="Rule 9: Use preprocessor judiciously",
                autofix_available=True,
            ),
            "F821": LinterRule(
                rule_code="F821",
                linter="ruff",
                connascence_type="CoT",
                description="Undefined name",
                severity="high",
                nasa_rule="Rule 10: Compiler warnings",
                autofix_available=False,
            ),
            "F401": LinterRule(
                rule_code="F401",
                linter="ruff",
                connascence_type="CoT",
                description="Module imported but unused",
                severity="medium",
                nasa_rule="Rule 10: Compiler warnings",
                autofix_available=True,
            ),
            # Pylint -> Connascence Mappings
            "R0913": LinterRule(
                rule_code="R0913",
                linter="pylint",
                connascence_type="CoP",
                description="Too many arguments",
                severity="medium",
                nasa_rule="Rule 6: Restrict function size",
                autofix_available=False,
            ),
            "R0915": LinterRule(
                rule_code="R0915",
                linter="pylint",
                connascence_type="CoA",
                description="Too many statements",
                severity="medium",
                nasa_rule="Rule 6: Restrict function size",
                autofix_available=False,
            ),
            "R0912": LinterRule(
                rule_code="R0912",
                linter="pylint",
                connascence_type="CoA",
                description="Too many branches",
                severity="medium",
                nasa_rule="Rule 6: Restrict function size",
                autofix_available=False,
            ),
            "C0103": LinterRule(
                rule_code="C0103",
                linter="pylint",
                connascence_type="CoN",
                description="Invalid name",
                severity="low",
                nasa_rule="Rule 9: Use preprocessor judiciously",
                autofix_available=False,
            ),
            "R0903": LinterRule(
                rule_code="R0903",
                linter="pylint",
                connascence_type="CoA",
                description="Too few public methods",
                severity="low",
                nasa_rule="Rule 6: Restrict function size",
                autofix_available=False,
            ),
        }

    def _initialize_nasa_alignment(self) -> Dict[str, List[str]]:
        """Initialize NASA Power of Ten rule alignment."""
        return {
            "Rule 1: No goto": ["C901", "PLR0912"],
            "Rule 2: No loops with unknown bounds": ["PLR0912", "C901"],
            "Rule 3: No heap allocation": ["F821", "W0621"],
            "Rule 4: No function longer than screen": ["PLR0915", "R0915"],
            "Rule 5: No magic numbers": ["PLR2004"],
            "Rule 6: Restrict function size": ["PLR0913", "PLR0915", "PLR0912", "C901"],
            "Rule 7: Use strong typing": ["F821", "F401"],
            "Rule 8: Restrict heap use": ["F821", "W0621"],
            "Rule 9: Use preprocessor judiciously": ["N801", "N802", "C0103"],
            "Rule 10: Compiler warnings": ["F821", "F401", "W0613"],
        }

    def _initialize_magic_literal_patterns(self) -> Dict[str, re.Pattern]:
        """Initialize enhanced magic literal detection patterns."""
        return {
            "numeric_constants": re.compile(r"\b\d+\b"),
            "string_literals": re.compile(r'["\'][^"\']*["\']'),
            "comparison_operators": re.compile(r"[=!<>]=?"),
            "array_indices": re.compile(r"\[\d+\]"),
            "timeout_values": re.compile(r"\b\d+\s*\*\s*\d+\b"),  # Common timeout patterns
        }

    async def correlate_tools(
        self, project_path: Path, connascence_violations: List[Dict], linter_results: Dict[str, Dict]
    ) -> Dict[str, CorrelationResult]:
        """Correlate findings between different linting tools and connascence analysis."""
        correlations = {}

        for linter_name, results in linter_results.items():
            if not results.get("success", False):
                continue

            issues = results.get("issues", [])
            correlation = await self._correlate_single_linter(linter_name, issues, connascence_violations)
            correlations[linter_name] = correlation

        return correlations

    async def _correlate_single_linter(
        self, linter_name: str, linter_issues: List[Dict], connascence_violations: List[Dict]
    ) -> CorrelationResult:
        """Correlate a single linter's findings with connascence violations."""

        # Group linter issues by connascence type
        grouped_issues = self._group_issues_by_connascence_type(linter_issues)

        # Group connascence violations by type
        grouped_violations = {}
        for violation in connascence_violations:
            conn_type = violation.get("connascence_type", "Unknown")
            if conn_type not in grouped_violations:
                grouped_violations[conn_type] = []
            grouped_violations[conn_type].append(violation)

        # Calculate correlations
        overlapping_files = set()
        aligned_findings = []
        unique_linter = []
        unique_connascence = []
        total_correlation_score = 0.0
        correlation_count = 0

        # Process each connascence type
        for conn_type in set(grouped_issues.keys()).union(set(grouped_violations.keys())):
            linter_items = grouped_issues.get(conn_type, [])
            violation_items = grouped_violations.get(conn_type, [])

            if linter_items and violation_items:
                # Calculate file overlap
                linter_files = {item.get("filename", "") for item in linter_items}
                violation_files = {v.get("file_path", "") for v in violation_items}

                overlap = linter_files.intersection(violation_files)
                overlapping_files.update(overlap)

                # Calculate correlation score for this type
                if linter_files or violation_files:
                    type_score = len(overlap) / len(linter_files.union(violation_files))
                    total_correlation_score += type_score
                    correlation_count += 1

                # Find aligned findings (same file and similar line numbers)
                for linter_item in linter_items:
                    for violation in violation_items:
                        if self._are_findings_aligned(linter_item, violation):
                            aligned_findings.append((linter_item, violation))
                            break
                    else:
                        unique_linter.append(linter_item)

                # Find unique connascence violations
                for violation in violation_items:
                    if not any(self._are_findings_aligned(li, violation) for li in linter_items):
                        unique_connascence.append(violation)

            elif linter_items:
                unique_linter.extend(linter_items)
            elif violation_items:
                unique_connascence.extend(violation_items)

        # Calculate overall correlation score
        correlation_score = total_correlation_score / correlation_count if correlation_count > 0 else 0.0

        # Generate recommendation
        recommendation = self._generate_correlation_recommendation(
            correlation_score, len(aligned_findings), len(unique_linter), len(unique_connascence)
        )

        return CorrelationResult(
            correlation_score=correlation_score,
            overlapping_files=overlapping_files,
            unique_linter_findings=unique_linter,
            unique_connascence_findings=unique_connascence,
            aligned_findings=aligned_findings,
            recommendation=recommendation,
        )

    def _group_issues_by_connascence_type(self, issues: List[Dict]) -> Dict[str, List[Dict]]:
        """Group linter issues by their corresponding connascence type."""
        grouped = {}

        for issue in issues:
            rule_code = issue.get("code", "")
            rule_mapping = self.rule_mappings.get(rule_code)

            if rule_mapping:
                conn_type = rule_mapping.connascence_type
                if conn_type not in grouped:
                    grouped[conn_type] = []
                grouped[conn_type].append(issue)

        return grouped

    def _are_findings_aligned(self, linter_item: Dict, violation: Dict) -> bool:
        """Check if a linter finding and connascence violation are aligned."""
        linter_file = linter_item.get("filename", "")
        violation_file = violation.get("file_path", "")

        if linter_file != violation_file:
            return False

        # Check line number alignment (within 5 lines)
        linter_line = linter_item.get("location", {}).get("row", 0)
        violation_line = violation.get("line_number", 0)

        return abs(linter_line - violation_line) <= 5

    def _generate_correlation_recommendation(
        self, correlation_score: float, aligned_count: int, unique_linter_count: int, unique_connascence_count: int
    ) -> str:
        """Generate correlation-based recommendations."""
        if correlation_score >= 0.8:
            return f"Excellent correlation ({correlation_score:.1%}) - {aligned_count} aligned findings. Both tools are working well together."
        elif correlation_score >= 0.6:
            return f"Good correlation ({correlation_score:.1%}) - Consider reviewing {unique_linter_count} unique linter findings and {unique_connascence_count} unique connascence violations."
        elif correlation_score >= 0.4:
            return f"Moderate correlation ({correlation_score:.1%}) - Significant differences detected. Review tool configurations and thresholds."
        else:
            return f"Low correlation ({correlation_score:.1%}) - Tools may be detecting different issue types. Consider enabling additional linter rules or adjusting connascence thresholds."

    def generate_unified_diagnostics(
        self, project_path: Path, connascence_violations: List[Dict], linter_results: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """Generate unified diagnostic report combining all tools."""
        unified_diagnostics = {
            "summary": {
                "total_issues": len(connascence_violations),
                "linter_issues": sum(len(r.get("issues", [])) for r in linter_results.values()),
                "tools_analyzed": len([r for r in linter_results.values() if r.get("success", False)]),
            },
            "issues_by_type": {},
            "nasa_compliance": self._analyze_nasa_compliance(connascence_violations, linter_results),
            "recommendations": [],
            "autofix_available": [],
        }

        # Categorize all issues by connascence type
        for violation in connascence_violations:
            conn_type = violation.get("connascence_type", "Unknown")
            if conn_type not in unified_diagnostics["issues_by_type"]:
                unified_diagnostics["issues_by_type"][conn_type] = {
                    "connascence_violations": [],
                    "linter_issues": [],
                    "severity_breakdown": {},
                }

            unified_diagnostics["issues_by_type"][conn_type]["connascence_violations"].append(violation)

            # Update severity breakdown
            severity = violation.get("severity", "medium")
            severity_breakdown = unified_diagnostics["issues_by_type"][conn_type]["severity_breakdown"]
            severity_breakdown[severity] = severity_breakdown.get(severity, 0) + 1

        # Add linter issues
        for linter_name, results in linter_results.items():
            if not results.get("success", False):
                continue

            for issue in results.get("issues", []):
                rule_code = issue.get("code", "")
                rule_mapping = self.rule_mappings.get(rule_code)

                if rule_mapping:
                    conn_type = rule_mapping.connascence_type
                    if conn_type not in unified_diagnostics["issues_by_type"]:
                        unified_diagnostics["issues_by_type"][conn_type] = {
                            "connascence_violations": [],
                            "linter_issues": [],
                            "severity_breakdown": {},
                        }

                    unified_diagnostics["issues_by_type"][conn_type]["linter_issues"].append(
                        {"issue": issue, "rule_mapping": rule_mapping}
                    )

                    # Track autofix availability
                    if rule_mapping.autofix_available:
                        unified_diagnostics["autofix_available"].append(
                            {"rule_code": rule_code, "linter": linter_name, "description": rule_mapping.description}
                        )

        # Generate recommendations
        unified_diagnostics["recommendations"] = self._generate_unified_recommendations(unified_diagnostics)

        return unified_diagnostics

    def _analyze_nasa_compliance(
        self, connascence_violations: List[Dict], linter_results: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """Analyze NASA Power of Ten compliance across tools."""
        nasa_analysis = {
            "compliance_score": 0.0,
            "violations_by_rule": {},
            "linter_coverage": {},
            "recommendations": [],
        }

        # Count violations for each NASA rule
        for nasa_rule, linter_codes in self.nasa_rule_alignment.items():
            violations_count = 0

            # Count from linter results
            for linter_name, results in linter_results.items():
                if not results.get("success", False):
                    continue

                linter_violations = [
                    issue for issue in results.get("issues", []) if issue.get("code", "") in linter_codes
                ]
                violations_count += len(linter_violations)

                if linter_violations:
                    nasa_analysis["linter_coverage"][nasa_rule] = nasa_analysis["linter_coverage"].get(nasa_rule, [])
                    nasa_analysis["linter_coverage"][nasa_rule].append(
                        {"linter": linter_name, "violations": len(linter_violations)}
                    )

            # Count from connascence violations (approximate mapping)
            connascence_violations_for_rule = self._map_connascence_to_nasa_rule(nasa_rule, connascence_violations)
            violations_count += len(connascence_violations_for_rule)

            nasa_analysis["violations_by_rule"][nasa_rule] = violations_count

        # Calculate compliance score
        total_violations = sum(nasa_analysis["violations_by_rule"].values())
        nasa_analysis["compliance_score"] = max(0.0, 1.0 - (total_violations / 100.0))  # Normalize

        # Generate NASA-specific recommendations
        if nasa_analysis["compliance_score"] < 0.7:
            nasa_analysis["recommendations"].append(
                "Enable additional Ruff PLR* rules to improve NASA Power of Ten compliance"
            )

        if nasa_analysis["violations_by_rule"].get("Rule 5: No magic numbers", 0) > 10:
            nasa_analysis["recommendations"].append(
                "High number of magic literals detected - consider extracting constants"
            )

        return nasa_analysis

    def _map_connascence_to_nasa_rule(self, nasa_rule: str, connascence_violations: List[Dict]) -> List[Dict]:
        """Map connascence violations to NASA rules."""
        if nasa_rule == "Rule 5: No magic numbers":
            return [v for v in connascence_violations if v.get("connascence_type") == "CoM"]
        elif nasa_rule == "Rule 6: Restrict function size":
            return [v for v in connascence_violations if v.get("connascence_type") in ["CoA", "CoP"]]
        elif nasa_rule == "Rule 9: Use preprocessor judiciously":
            return [v for v in connascence_violations if v.get("connascence_type") == "CoN"]
        elif nasa_rule in ["Rule 7: Use strong typing", "Rule 10: Compiler warnings"]:
            return [v for v in connascence_violations if v.get("connascence_type") == "CoT"]
        else:
            return []

    def _generate_unified_recommendations(self, unified_diagnostics: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on unified analysis."""
        recommendations = []

        issues_by_type = unified_diagnostics["issues_by_type"]
        autofix_count = len(unified_diagnostics["autofix_available"])

        # Priority recommendations
        com_issues = len(issues_by_type.get("CoM", {}).get("connascence_violations", []))
        if com_issues > 20:
            recommendations.append(
                f"HIGH PRIORITY: {com_issues} magic literal violations (CoM) detected. "
                f"Extract constants and use configuration files."
            )

        cop_issues = len(issues_by_type.get("CoP", {}).get("connascence_violations", []))
        if cop_issues > 10:
            recommendations.append(
                f"MEDIUM PRIORITY: {cop_issues} parameter position violations (CoP) detected. "
                f"Use keyword arguments, data classes, or builder patterns."
            )

        coa_issues = len(issues_by_type.get("CoA", {}).get("connascence_violations", []))
        if coa_issues > 5:
            recommendations.append(
                f"MEDIUM PRIORITY: {coa_issues} algorithm complexity violations (CoA) detected. "
                f"Refactor complex functions and extract helper methods."
            )

        # Autofix recommendations
        if autofix_count > 0:
            recommendations.append(
                f"QUICK WIN: {autofix_count} issues can be automatically fixed by linters. "
                f"Run 'ruff check --fix' to resolve formatting and import issues."
            )

        # NASA compliance recommendation
        nasa_score = unified_diagnostics["nasa_compliance"]["compliance_score"]
        if nasa_score < 0.7:
            recommendations.append(
                f"NASA COMPLIANCE: Score {nasa_score:.1%} - Enable additional linter rules "
                f"and address connascence violations to improve safety standards compliance."
            )

        return recommendations

    def export_enhanced_config(self, output_path: Path) -> Dict[str, Path]:
        """Export enhanced linter configurations optimized for connascence detection."""
        configs = {}

        # Enhanced Ruff configuration
        ruff_config = {
            "target-version": "py38",
            "line-length": 120,
            "select": ["E", "W", "F", "I", "UP", "SIM", "RUF", "PLR", "PLW", "PLE", "C90", "ARG", "N", "B", "C4"],
            "ignore": [
                "E501",
                "B008",
                "PLR0911",
                "PLR0912",
                "PLR0913",
                "PLR0915",
                "C901",  # Let connascence handle these
            ],
            "fix": True,
            "show-fixes": True,
            "pylint": {"max-args": 4, "max-branches": 8, "max-returns": 6, "max-statements": 25},
            "mccabe": {"max-complexity": 8},
        }

        ruff_path = output_path / "ruff-enhanced.toml"
        with open(ruff_path, "w") as f:
            import toml

            toml.dump({"tool": {"ruff": ruff_config}}, f)
        configs["ruff"] = ruff_path

        # Enhanced Pylint configuration
        pylint_config = {
            "max-args": 4,
            "max-locals": 15,
            "max-returns": 6,
            "max-branches": 8,
            "max-statements": 25,
            "max-parents": 7,
            "max-attributes": 7,
            "min-public-methods": 1,
            "max-public-methods": 15,
            "max-bool-expr": 5,
            "disable": [
                "C0114",
                "C0115",
                "C0116",  # Missing docstrings
                "R0903",  # Too few public methods
            ],
        }

        pylint_path = output_path / "pylintrc-enhanced"
        with open(pylint_path, "w") as f:
            f.write("[DESIGN]\n")
            for key, value in pylint_config.items():
                if key != "disable":
                    f.write(f"{key}={value}\n")
            f.write("\n[MESSAGES CONTROL]\n")
            f.write(f"disable={','.join(pylint_config['disable'])}\n")
        configs["pylint"] = pylint_path

        return configs


def main():
    """CLI interface for enhanced linter integration."""
    import argparse

    parser = argparse.ArgumentParser(description="Enhanced Linter Integration for Connascence")
    parser.add_argument("project_path", type=Path, help="Project path to analyze")
    parser.add_argument(
        "--connascence-results", type=Path, required=True, help="Path to connascence analysis results JSON"
    )
    parser.add_argument(
        "--linter-results",
        type=Path,
        action="append",
        help="Path to linter results JSON (can be specified multiple times)",
    )
    parser.add_argument(
        "--output", type=Path, default="enhanced-integration-report.json", help="Output file for correlation report"
    )
    parser.add_argument("--export-configs", type=Path, help="Directory to export enhanced linter configurations")

    args = parser.parse_args()

    # Initialize integration
    integration = EnhancedLinterIntegration()

    # Load connascence results
    with open(args.connascence_results) as f:
        connascence_data = json.load(f)

    connascence_violations = connascence_data.get("violations", [])

    # Load linter results
    linter_results = {}
    if args.linter_results:
        for linter_file in args.linter_results:
            linter_name = linter_file.stem.replace("_results", "")
            with open(linter_file) as f:
                linter_results[linter_name] = json.load(f)

    # Run correlation analysis
    async def run_analysis():
        correlations = await integration.correlate_tools(args.project_path, connascence_violations, linter_results)

        unified_diagnostics = integration.generate_unified_diagnostics(
            args.project_path, connascence_violations, linter_results
        )

        # Generate comprehensive report
        report = {
            "project_path": str(args.project_path),
            "analysis_timestamp": str(asyncio.get_event_loop().time()),
            "correlations": {
                name: {
                    "correlation_score": corr.correlation_score,
                    "overlapping_files": list(corr.overlapping_files),
                    "aligned_findings_count": len(corr.aligned_findings),
                    "unique_linter_count": len(corr.unique_linter_findings),
                    "unique_connascence_count": len(corr.unique_connascence_findings),
                    "recommendation": corr.recommendation,
                }
                for name, corr in correlations.items()
            },
            "unified_diagnostics": unified_diagnostics,
            "rule_mappings": {
                code: {
                    "connascence_type": rule.connascence_type,
                    "description": rule.description,
                    "severity": rule.severity,
                    "nasa_rule": rule.nasa_rule,
                    "autofix_available": rule.autofix_available,
                }
                for code, rule in integration.rule_mappings.items()
            },
        }

        # Write report
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)

        print(f"Enhanced integration report written to: {args.output}")

        # Export configurations if requested
        if args.export_configs:
            args.export_configs.mkdir(exist_ok=True)
            configs = integration.export_enhanced_config(args.export_configs)
            print(f"Enhanced configurations exported to: {args.export_configs}")
            for tool, config_path in configs.items():
                print(f"  {tool}: {config_path}")

    # Run analysis
    asyncio.run(run_analysis())


if __name__ == "__main__":
    main()
