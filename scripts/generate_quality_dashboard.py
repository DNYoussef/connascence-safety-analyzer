#!/usr/bin/env python3
"""
Generate Quality Dashboard from CI/CD reports.

This script aggregates various quality reports (security, coverage, linting)
into a single HTML dashboard for easy visualization.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


class QualityDashboardGenerator:
    """Generates an HTML quality dashboard from various report files."""

    def __init__(self, reports_dir: str = "."):
        self.reports_dir = Path(reports_dir)
        self.metrics: Dict[str, Any] = {}

    def load_coverage_report(self) -> Dict[str, Any]:
        """Load Python test coverage report."""
        coverage_file = self.reports_dir / "coverage-reports" / "coverage.json"
        if coverage_file.exists():
            with open(coverage_file) as f:
                data = json.load(f)
                return {
                    "coverage": data["totals"]["percent_covered"],
                    "lines_covered": data["totals"]["covered_lines"],
                    "lines_total": data["totals"]["num_statements"],
                    "status": "pass" if data["totals"]["percent_covered"] >= 60 else "warn"
                }
        return {"coverage": 0, "lines_covered": 0, "lines_total": 0, "status": "fail"}

    def load_security_report(self) -> Dict[str, Any]:
        """Load Bandit security scan report."""
        bandit_file = self.reports_dir / "security-scan-reports" / "bandit-report.json"
        if bandit_file.exists():
            with open(bandit_file) as f:
                data = json.load(f)
                issues = data.get("results", [])
                critical = sum(1 for i in issues if i.get("issue_severity") == "HIGH")
                medium = sum(1 for i in issues if i.get("issue_severity") == "MEDIUM")
                low = sum(1 for i in issues if i.get("issue_severity") == "LOW")

                return {
                    "total_issues": len(issues),
                    "critical": critical,
                    "medium": medium,
                    "low": low,
                    "status": "fail" if critical > 0 else ("warn" if medium > 5 else "pass")
                }
        return {"total_issues": 0, "critical": 0, "medium": 0, "low": 0, "status": "unknown"}

    def load_dependency_audit(self) -> Dict[str, Any]:
        """Load dependency audit reports."""
        npm_audit = self.reports_dir / "dependency-audit-reports" / "npm-audit-report.json"
        vulnerabilities = {"critical": 0, "high": 0, "moderate": 0, "low": 0}

        if npm_audit.exists():
            try:
                with open(npm_audit) as f:
                    data = json.load(f)
                    metadata = data.get("metadata", {}).get("vulnerabilities", {})
                    vulnerabilities = {
                        "critical": metadata.get("critical", 0),
                        "high": metadata.get("high", 0),
                        "moderate": metadata.get("moderate", 0),
                        "low": metadata.get("low", 0)
                    }
            except (json.JSONDecodeError, KeyError):
                pass

        total = sum(vulnerabilities.values())
        status = "fail" if vulnerabilities["critical"] > 0 else ("warn" if vulnerabilities["high"] > 0 else "pass")

        return {
            **vulnerabilities,
            "total": total,
            "status": status
        }

    def load_code_quality(self) -> Dict[str, Any]:
        """Load code quality metrics."""
        ruff_file = self.reports_dir / "code-quality-reports" / "ruff-report.json"

        if ruff_file.exists():
            try:
                with open(ruff_file) as f:
                    issues = json.load(f)
                    error_count = sum(1 for i in issues if i.get("level") == "error")
                    warning_count = sum(1 for i in issues if i.get("level") == "warning")

                    return {
                        "errors": error_count,
                        "warnings": warning_count,
                        "total": len(issues),
                        "status": "fail" if error_count > 10 else ("warn" if warning_count > 50 else "pass")
                    }
            except (json.JSONDecodeError, KeyError):
                pass

        return {"errors": 0, "warnings": 0, "total": 0, "status": "unknown"}

    def generate_html(self) -> str:
        """Generate HTML dashboard."""
        # Load all metrics
        coverage = self.load_coverage_report()
        security = self.load_security_report()
        dependencies = self.load_dependency_audit()
        quality = self.load_code_quality()

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connascence Analyzer - Quality Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #c9d1d9; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #58a6ff; margin-bottom: 10px; }}
        .timestamp {{ color: #8b949e; margin-bottom: 30px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 20px; }}
        .card h2 {{ color: #58a6ff; margin-bottom: 15px; font-size: 18px; }}
        .metric {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #21262d; }}
        .metric:last-child {{ border-bottom: none; }}
        .metric-label {{ color: #8b949e; }}
        .metric-value {{ font-weight: bold; }}
        .status-pass {{ color: #3fb950; }}
        .status-warn {{ color: #d29922; }}
        .status-fail {{ color: #f85149; }}
        .status-unknown {{ color: #8b949e; }}
        .badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 600; }}
        .badge-pass {{ background: #1a4027; color: #3fb950; }}
        .badge-warn {{ background: #3e3014; color: #d29922; }}
        .badge-fail {{ background: #4d1e21; color: #f85149; }}
        .badge-unknown {{ background: #21262d; color: #8b949e; }}
        .progress {{ width: 100%; height: 8px; background: #21262d; border-radius: 4px; overflow: hidden; margin-top: 5px; }}
        .progress-bar {{ height: 100%; transition: width 0.3s; }}
        .progress-pass {{ background: #3fb950; }}
        .progress-warn {{ background: #d29922; }}
        .progress-fail {{ background: #f85149; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Quality Dashboard</h1>
        <p class="timestamp">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>

        <div class="grid">
            <!-- Test Coverage -->
            <div class="card">
                <h2>📊 Test Coverage</h2>
                <div class="metric">
                    <span class="metric-label">Coverage</span>
                    <span class="metric-value status-{coverage['status']}">{coverage['coverage']:.1f}%</span>
                </div>
                <div class="progress">
                    <div class="progress-bar progress-{coverage['status']}" style="width: {coverage['coverage']:.1f}%"></div>
                </div>
                <div class="metric">
                    <span class="metric-label">Lines Covered</span>
                    <span class="metric-value">{coverage['lines_covered']:,} / {coverage['lines_total']:,}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Status</span>
                    <span class="badge badge-{coverage['status']}">{coverage['status'].upper()}</span>
                </div>
            </div>

            <!-- Security Scan -->
            <div class="card">
                <h2>🛡️ Security Scan</h2>
                <div class="metric">
                    <span class="metric-label">Total Issues</span>
                    <span class="metric-value">{security['total_issues']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Critical</span>
                    <span class="metric-value status-fail">{security['critical']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Medium</span>
                    <span class="metric-value status-warn">{security['medium']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Low</span>
                    <span class="metric-value">{security['low']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Status</span>
                    <span class="badge badge-{security['status']}">{security['status'].upper()}</span>
                </div>
            </div>

            <!-- Dependency Audit -->
            <div class="card">
                <h2>📦 Dependency Audit</h2>
                <div class="metric">
                    <span class="metric-label">Total Vulnerabilities</span>
                    <span class="metric-value">{dependencies['total']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Critical</span>
                    <span class="metric-value status-fail">{dependencies['critical']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">High</span>
                    <span class="metric-value status-warn">{dependencies['high']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Moderate</span>
                    <span class="metric-value">{dependencies['moderate']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Status</span>
                    <span class="badge badge-{dependencies['status']}">{dependencies['status'].upper()}</span>
                </div>
            </div>

            <!-- Code Quality -->
            <div class="card">
                <h2>✨ Code Quality</h2>
                <div class="metric">
                    <span class="metric-label">Total Issues</span>
                    <span class="metric-value">{quality['total']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Errors</span>
                    <span class="metric-value status-fail">{quality['errors']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Warnings</span>
                    <span class="metric-value status-warn">{quality['warnings']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Status</span>
                    <span class="badge badge-{quality['status']}">{quality['status'].upper()}</span>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>📋 Overall Status</h2>
            <div class="metric">
                <span class="metric-label">Coverage Gate (≥60%)</span>
                <span class="badge badge-{coverage['status']}">{coverage['status'].upper()}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Security Gate (0 critical)</span>
                <span class="badge badge-{security['status']}">{security['status'].upper()}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Dependency Gate (0 critical)</span>
                <span class="badge badge-{dependencies['status']}">{dependencies['status'].upper()}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Quality Gate (≤10 errors)</span>
                <span class="badge badge-{quality['status']}">{quality['status'].upper()}</span>
            </div>
        </div>
    </div>
</body>
</html>"""
        return html

    def save_dashboard(self, output_file: str = "quality-dashboard.html"):
        """Save the dashboard to an HTML file."""
        html = self.generate_html()
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Quality dashboard generated: {output_file}")


if __name__ == "__main__":
    generator = QualityDashboardGenerator()
    generator.save_dashboard()
