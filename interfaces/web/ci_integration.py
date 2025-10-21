# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

"""
CI/CD Dashboard Integration

Provides dashboard components specifically designed for CI/CD environments,
including GitHub Actions integration, pull request comments, and build status.
"""

from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List, Optional

from analyzer.ast_engine.core_analyzer import ConnascenceASTAnalyzer
from analyzer.reporting.sarif import SARIFReporter
from policy.baselines import BaselineManager
from policy.budgets import BudgetTracker

from .metrics import DashboardMetrics


class CIDashboard:
    """CI/CD integration dashboard for connascence analysis."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.analyzer = ConnascenceASTAnalyzer()
        self.budget_tracker = BudgetTracker()
        self.baseline_manager = BaselineManager()
        self.metrics = DashboardMetrics()
        self.sarif_reporter = SARIFReporter()

        # CI environment detection
        self.is_github_actions = os.getenv("GITHUB_ACTIONS") == "true"
        self.is_gitlab_ci = os.getenv("GITLAB_CI") == "true"
        self.is_jenkins = os.getenv("JENKINS_URL") is not None
        self.is_ci = any([self.is_github_actions, self.is_gitlab_ci, self.is_jenkins])

    def analyze_pull_request(
        self, base_ref: str, head_ref: str = "HEAD", policy_preset: str = "service-defaults"
    ) -> Dict[str, Any]:
        """Analyze pull request changes for connascence violations."""
        try:
            # Get changed files
            changed_files = self._get_changed_files(base_ref, head_ref)
            if not changed_files:
                return self._create_pr_report([], [], "No Python files changed")

            # Analyze only changed files
            violations = []
            for file_path in changed_files:
                if file_path.suffix == ".py" and file_path.exists():
                    file_violations = self.analyzer.analyze_file(file_path)
                    violations.extend(file_violations)

            # Compare against baseline if available
            baseline_comparison = None
            try:
                baseline_id = self.baseline_manager.get_latest_baseline_id()
                if baseline_id:
                    baseline_comparison = self.baseline_manager.compare_against_baseline(violations, baseline_id)
                    # Focus on new violations for PR review
                    violations = baseline_comparison["new_violations"]
            except Exception:
                pass  # Continue without baseline if not available

            # Check budget compliance
            budget_status = self._check_pr_budget(violations, policy_preset)

            return self._create_pr_report(
                violations, changed_files, baseline_comparison=baseline_comparison, budget_status=budget_status
            )

        except Exception as e:
            return self._create_error_report(str(e))

    def generate_ci_artifacts(self, scan_results: Dict[str, Any], output_dir: Path) -> Dict[str, str]:
        """Generate CI artifacts from scan results."""
        artifacts = {}
        output_dir.mkdir(exist_ok=True)

        # SARIF report for GitHub Code Scanning
        if scan_results.get("violations"):
            sarif_path = output_dir / "connascence.sarif"
            sarif_content = self.sarif_reporter.generate_report(scan_results["violations"])
            sarif_path.write_text(sarif_content)
            artifacts["sarif"] = str(sarif_path)

        # HTML dashboard report
        html_path = output_dir / "dashboard.html"
        html_content = self._generate_html_report(scan_results)
        html_path.write_text(html_content)
        artifacts["html"] = str(html_path)

        # JSON summary
        json_path = output_dir / "summary.json"
        summary = self._create_ci_summary(scan_results)
        json_path.write_text(json.dumps(summary, indent=2))
        artifacts["json"] = str(json_path)

        # Badge data for README
        badge_path = output_dir / "badge.json"
        badge_data = self._generate_badge_data(scan_results)
        badge_path.write_text(json.dumps(badge_data))
        artifacts["badge"] = str(badge_path)

        return artifacts

    def post_github_comment(self, pr_number: int, scan_results: Dict[str, Any]) -> bool:
        """Post scan results as GitHub PR comment."""
        if not self.is_github_actions:
            return False

        try:
            comment_body = self._generate_pr_comment(scan_results)

            # Use GitHub CLI if available
            result = subprocess.run(
                ["gh", "pr", "comment", str(pr_number), "--body", comment_body],
                check=False,
                capture_output=True,
                text=True,
            )

            return result.returncode == 0
        except Exception:
            return False

    def set_build_status(self, scan_results: Dict[str, Any]) -> bool:
        """Set build status based on scan results."""
        violations = scan_results.get("violations", [])
        critical_violations = [v for v in violations if v.get("severity") == "critical"]

        # Fail build if critical violations or budget exceeded
        budget_exceeded = scan_results.get("budget_status", {}).get("budget_exceeded", False)

        if critical_violations or budget_exceeded:
            if self.is_github_actions:
                print("::error::Critical connascence violations detected")
                return False
            return False

        return True

    def _get_changed_files(self, base_ref: str, head_ref: str) -> List[Path]:
        """Get list of changed Python files between refs."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", f"{base_ref}...{head_ref}"], check=False, capture_output=True, text=True
            )

            if result.returncode != 0:
                return []

            files = []
            for line in result.stdout.strip().split("\n"):
                if line and line.endswith(".py"):
                    file_path = Path(line)
                    if file_path.exists():
                        files.append(file_path)

            return files
        except Exception:
            return []

    def _check_pr_budget(self, violations: List, policy_preset: str) -> Dict[str, Any]:
        """Check PR violations against budget limits."""
        try:
            # Load policy preset to get budget limits
            policy_config = self.config.get("policies", {}).get(policy_preset, {})
            budget_limits = policy_config.get(
                "pr_budget_limits",
                {
                    "total_violations": 10,
                    "critical": 0,
                    "high": 3,
                    "CoM": 5,  # Magic literals
                    "CoP": 2,  # Parameter bombs
                },
            )

            self.budget_tracker.set_budget_limits(budget_limits)
            self.budget_tracker.track_violations(violations)

            return self.budget_tracker.check_compliance()
        except Exception as e:
            return {"compliant": True, "error": str(e)}

    def _create_pr_report(
        self,
        violations: List,
        changed_files: List[Path],
        message: Optional[str] = None,
        baseline_comparison: Optional[Dict] = None,
        budget_status: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Create PR analysis report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "changed_files": [str(f) for f in changed_files],
            "violations": [self._violation_to_dict(v) for v in violations],
            "summary": {
                "total_violations": len(violations),
                "files_analyzed": len(changed_files),
                "critical_count": len([v for v in violations if getattr(v, "severity", None) == "critical"]),
                "high_count": len([v for v in violations if getattr(v, "severity", None) == "high"]),
                "violations_by_type": self._group_violations_by_type(violations),
            },
        }

        if message:
            report["message"] = message

        if baseline_comparison:
            report["baseline_comparison"] = baseline_comparison

        if budget_status:
            report["budget_status"] = budget_status

        # Determine PR status
        critical_violations = report["summary"]["critical_count"]
        budget_exceeded = budget_status and budget_status.get("budget_exceeded", False)

        if critical_violations > 0:
            report["status"] = "critical"
            report["status_message"] = f"{critical_violations} critical violations detected"
        elif budget_exceeded:
            report["status"] = "budget_exceeded"
            report["status_message"] = "PR budget limits exceeded"
        elif len(violations) > 0:
            report["status"] = "violations_found"
            report["status_message"] = f"{len(violations)} violations found"
        else:
            report["status"] = "clean"
            report["status_message"] = "No connascence violations detected"

        return report

    def _create_error_report(self, error_message: str) -> Dict[str, Any]:
        """Create error report."""
        return {
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "error_message": error_message,
            "violations": [],
            "summary": {"total_violations": 0},
        }

    def _violation_to_dict(self, violation) -> Dict:
        """Convert violation object to dictionary."""
        if hasattr(violation, "__dict__"):
            return {
                "id": getattr(violation, "id", ""),
                "rule_id": getattr(violation, "rule_id", ""),
                "connascence_type": getattr(violation, "connascence_type", ""),
                "severity": getattr(violation, "severity", "medium"),
                "description": getattr(violation, "description", ""),
                "file_path": getattr(violation, "file_path", ""),
                "line_number": getattr(violation, "line_number", 0),
                "weight": getattr(violation, "weight", 1.0),
            }
        return violation

    def _group_violations_by_type(self, violations: List) -> Dict[str, int]:
        """Group violations by connascence type."""
        groups = {}
        for violation in violations:
            conn_type = getattr(violation, "connascence_type", "Unknown")
            groups[conn_type] = groups.get(conn_type, 0) + 1
        return groups

    def _create_ci_summary(self, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create CI summary report."""
        scan_results.get("violations", [])
        summary = scan_results.get("summary", {})

        return {
            "connascence_analysis": {
                "timestamp": scan_results.get("timestamp", datetime.now().isoformat()),
                "project_path": scan_results.get("project_path", ""),
                "policy_preset": scan_results.get("policy_preset", ""),
                "total_violations": summary.get("total_violations", 0),
                "connascence_index": summary.get("connascence_index", 0.0),
                "severity_breakdown": {
                    "critical": summary.get("critical_count", 0),
                    "high": summary.get("high_count", 0),
                    "medium": summary.get("medium_count", 0),
                    "low": summary.get("low_count", 0),
                },
                "type_breakdown": summary.get("violations_by_type", {}),
                "build_status": "pass" if summary.get("critical_count", 0) == 0 else "fail",
            }
        }

    def _generate_badge_data(self, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate badge data for shields.io."""
        summary = scan_results.get("summary", {})
        total_violations = summary.get("total_violations", 0)
        critical_count = summary.get("critical_count", 0)

        if critical_count > 0:
            color = "red"
            message = f"{total_violations} violations ({critical_count} critical)"
        elif total_violations > 10:
            color = "orange"
            message = f"{total_violations} violations"
        elif total_violations > 0:
            color = "yellow"
            message = f"{total_violations} violations"
        else:
            color = "green"
            message = "clean"

        return {"schemaVersion": 1, "label": "connascence", "message": message, "color": color}

    def _generate_html_report(self, scan_results: Dict[str, Any]) -> str:
        """Generate HTML dashboard report."""
        violations = scan_results.get("violations", [])
        summary = scan_results.get("summary", {})

        # Simple HTML template
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Connascence Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #f5f5f5; padding: 20px; border-radius: 8px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric {{ background: white; padding: 15px; border: 1px solid #ddd; border-radius: 4px; text-align: center; }}
        .metric-value {{ font-size: 2em; font-weight: bold; }}
        .critical {{ color: #d73a49; }}
        .high {{ color: #f66a0a; }}
        .medium {{ color: #dbab09; }}
        .low {{ color: #28a745; }}
        .violations {{ margin-top: 30px; }}
        .violation {{ border-left: 4px solid #ddd; padding: 10px; margin: 10px 0; background: #f9f9f9; }}
        .violation.critical {{ border-left-color: #d73a49; }}
        .violation.high {{ border-left-color: #f66a0a; }}
        .violation.medium {{ border-left-color: #dbab09; }}
        .violation.low {{ border-left-color: #28a745; }}
    </style>
</head>
<body>
    <div class="header">
        <h1> Connascence Analysis Report</h1>
        <p><strong>Project:</strong> {scan_results.get('project_path', 'Unknown')}</p>
        <p><strong>Policy:</strong> {scan_results.get('policy_preset', 'Unknown')}</p>
        <p><strong>Generated:</strong> {scan_results.get('timestamp', 'Unknown')}</p>
    </div>

    <div class="summary">
        <div class="metric">
            <div class="metric-value">{summary.get('total_violations', 0)}</div>
            <div>Total Violations</div>
        </div>
        <div class="metric">
            <div class="metric-value critical">{summary.get('critical_count', 0)}</div>
            <div>Critical</div>
        </div>
        <div class="metric">
            <div class="metric-value high">{summary.get('high_count', 0)}</div>
            <div>High</div>
        </div>
        <div class="metric">
            <div class="metric-value medium">{summary.get('medium_count', 0)}</div>
            <div>Medium</div>
        </div>
        <div class="metric">
            <div class="metric-value low">{summary.get('low_count', 0)}</div>
            <div>Low</div>
        </div>
        <div class="metric">
            <div class="metric-value">{summary.get('connascence_index', 0):.1f}</div>
            <div>Connascence Index</div>
        </div>
    </div>
"""

        if violations:
            html += '<div class="violations"><h2>Violations</h2>'
            for violation in violations[:50]:  # Limit display
                severity = violation.get("severity", "medium")
                html += f"""
                <div class="violation {severity}">
                    <strong>{violation.get('connascence_type', 'Unknown')}</strong> - {violation.get('description', '')}
                    <br>
                    <small>{violation.get('file_path', '')}:{violation.get('line_number', 0)}</small>
                </div>
                """

            if len(violations) > 50:
                html += f"<p><em>... and {len(violations) - 50} more violations</em></p>"

            html += "</div>"

        html += "</body></html>"
        return html

    def _generate_pr_comment(self, scan_results: Dict[str, Any]) -> str:
        """Generate GitHub PR comment."""
        violations = scan_results.get("violations", [])
        summary = scan_results.get("summary", {})
        status = scan_results.get("status", "unknown")

        # Status emoji
        status_emoji = {
            "clean": "[DONE]",
            "violations_found": "[WARNING]",
            "budget_exceeded": "",
            "critical": "",
            "error": "",
        }.get(status, "[METRICS]")

        comment = f"""## {status_emoji} Connascence Analysis Report

**Status:** {scan_results.get('status_message', 'Analysis complete')}

### Summary
- **Total Violations:** {summary.get('total_violations', 0)}
- **Critical:** {summary.get('critical_count', 0)}
- **High:** {summary.get('high_count', 0)}
- **Medium:** {summary.get('medium_count', 0)}
- **Low:** {summary.get('low_count', 0)}

### Violations by Type
"""

        violations_by_type = summary.get("violations_by_type", {})
        for conn_type, count in violations_by_type.items():
            comment += f"- **{conn_type}:** {count}\n"

        # Show critical violations
        critical_violations = [v for v in violations if v.get("severity") == "critical"]
        if critical_violations:
            comment += "\n###  Critical Violations\n"
            for violation in critical_violations[:5]:  # Limit to 5
                file_path = violation.get("file_path", "")
                line_number = violation.get("line_number", 0)
                description = violation.get("description", "")
                comment += f"- `{file_path}:{line_number}` - {description}\n"

        # Budget status
        budget_status = scan_results.get("budget_status")
        if budget_status and budget_status.get("budget_exceeded"):
            comment += "\n###  Budget Exceeded\n"
            for violation_type, details in budget_status.get("violations", {}).items():
                comment += f"- **{violation_type}:** Over budget\n"

        comment += "\n---\n*Analysis powered by [Connascence Analyzer](https://github.com/DNYoussef/connascence)*"

        return comment


def main():
    """CLI entry point for CI dashboard."""
    import argparse

    parser = argparse.ArgumentParser(description="Connascence CI Dashboard")
    parser.add_argument("--pr-analysis", action="store_true", help="Run PR analysis mode")
    parser.add_argument("--base-ref", default="origin/main", help="Base reference for PR analysis")
    parser.add_argument("--head-ref", default="HEAD", help="Head reference for PR analysis")
    parser.add_argument(
        "--output-dir", type=Path, default="connascence-artifacts", help="Output directory for CI artifacts"
    )
    parser.add_argument("--policy", default="service-defaults", help="Policy preset to use")

    args = parser.parse_args()

    dashboard = CIDashboard()

    if args.pr_analysis:
        # Run PR analysis
        results = dashboard.analyze_pull_request(args.base_ref, args.head_ref, args.policy)

        # Generate artifacts
        dashboard.generate_ci_artifacts(results, args.output_dir)

        # Print results
        print(json.dumps(results, indent=2))

        # Exit with appropriate code
        if results["status"] in ["critical", "budget_exceeded"]:
            sys.exit(1)
    else:
        print("CI Dashboard - use --pr-analysis for PR analysis mode")


if __name__ == "__main__":
    main()
