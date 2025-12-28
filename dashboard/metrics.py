#!/usr/bin/env python3
"""
Historical Metrics and Trend Analysis for Connascence Safety Analyzer
====================================================================

Tracks analysis results over time and generates trend dashboards
for continuous monitoring of code quality metrics.
"""

import argparse
from datetime import datetime, timedelta
import json
from pathlib import Path
import sys
from typing import Any, Dict, List


class MetricsTrendAnalyzer:
    """Analyzes and tracks metrics trends over time."""

    def __init__(self, storage_dir: str = "historical_metrics"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.trends_file = self.storage_dir / "trends.json"
        self.current_metrics = {}

    def load_historical_data(self) -> Dict[str, Any]:
        """Load historical metrics data."""
        if self.trends_file.exists():
            try:
                with open(self.trends_file) as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Could not load historical data: {e}")
                return {"entries": [], "metadata": {"version": "1.0"}}
        else:
            return {"entries": [], "metadata": {"version": "1.0"}}

    def save_historical_data(self, data: Dict[str, Any]) -> None:
        """Save historical metrics data."""
        try:
            with open(self.trends_file, "w") as f:
                json.dump(data, f, indent=2)
            print(f"✅ Historical data saved to {self.trends_file}")
        except Exception as e:
            print(f"❌ Could not save historical data: {e}")

    def extract_metrics_from_results(self, nasa_file: str, connascence_file: str, mece_file: str) -> Dict[str, Any]:
        """Extract key metrics from analysis result files."""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "nasa_score": 0.0,
            "nasa_violations": 0,
            "total_violations": 0,
            "critical_violations": 0,
            "god_objects": 0,
            "mece_score": 0.0,
            "mece_duplications": 0,
            "overall_quality": 0.0,
            "files_analyzed": 0,
        }

        # Extract NASA metrics
        if Path(nasa_file).exists():
            try:
                with open(nasa_file) as f:
                    nasa_data = json.load(f)
                if "nasa_compliance" in nasa_data:
                    metrics["nasa_score"] = nasa_data["nasa_compliance"].get("score", 0.0)
                    metrics["nasa_violations"] = len(nasa_data["nasa_compliance"].get("violations", []))
                print(f"✅ Extracted NASA metrics from {nasa_file}")
            except Exception as e:
                print(f"⚠️ Could not extract NASA metrics: {e}")

        # Extract Connascence metrics
        if Path(connascence_file).exists():
            try:
                with open(connascence_file) as f:
                    conn_data = json.load(f)
                violations = conn_data.get("violations", [])
                metrics["total_violations"] = len(violations)
                metrics["critical_violations"] = len([v for v in violations if v.get("severity") == "critical"])

                if "summary" in conn_data:
                    metrics["overall_quality"] = conn_data["summary"].get("overall_quality_score", 0.0)
                    metrics["files_analyzed"] = conn_data["summary"].get("files_analyzed", 0)

                # Count God Objects
                metrics["god_objects"] = len(
                    [v for v in violations if v.get("type") == "CoA" and "God Object" in v.get("description", "")]
                )
                print(f"✅ Extracted Connascence metrics from {connascence_file}")
            except Exception as e:
                print(f"⚠️ Could not extract Connascence metrics: {e}")

        # Extract MECE metrics
        if Path(mece_file).exists():
            try:
                with open(mece_file) as f:
                    mece_data = json.load(f)
                metrics["mece_score"] = mece_data.get("mece_score", 0.0)
                metrics["mece_duplications"] = len(mece_data.get("duplications", []))
                print(f"✅ Extracted MECE metrics from {mece_file}")
            except Exception as e:
                print(f"⚠️ Could not extract MECE metrics: {e}")

        return metrics

    def update_trends(self, nasa_results: str, connascence_results: str, mece_results: str, commit_sha: str) -> bool:
        """Update historical trends with new analysis results."""
        print("📊 Updating historical trends...")

        # Load existing data
        historical_data = self.load_historical_data()

        # Extract current metrics
        current_metrics = self.extract_metrics_from_results(nasa_results, connascence_results, mece_results)
        current_metrics["commit_sha"] = commit_sha

        # Add to historical data
        historical_data["entries"].append(current_metrics)
        historical_data["metadata"]["last_updated"] = datetime.now().isoformat()

        # Keep only last 100 entries to manage file size
        if len(historical_data["entries"]) > 100:
            historical_data["entries"] = historical_data["entries"][-100:]

        # Save updated data
        self.save_historical_data(historical_data)

        self.current_metrics = current_metrics
        return True

    def calculate_trend_direction(self, values: List[float], window: int = 5) -> str:
        """Calculate trend direction for a list of values."""
        if len(values) < 2:
            return "stable"

        # Use recent values for trend calculation
        recent_values = values[-min(window, len(values)) :]

        if len(recent_values) < 2:
            return "stable"

        # Simple linear trend
        first_half = sum(recent_values[: len(recent_values) // 2]) / len(recent_values[: len(recent_values) // 2])
        second_half = sum(recent_values[len(recent_values) // 2 :]) / len(recent_values[len(recent_values) // 2 :])

        change = (second_half - first_half) / (first_half + 0.001)  # Avoid division by zero

        if change > 0.05:  # 5% improvement
            return "improving"
        elif change < -0.05:  # 5% degradation
            return "declining"
        else:
            return "stable"

    def generate_trends_dashboard(self, days: int = 30, output: str = "trend_dashboard.html") -> str:
        """Generate HTML dashboard showing trends over specified days."""
        print(f"🎨 Generating trend dashboard for last {days} days...")

        # Load historical data
        historical_data = self.load_historical_data()
        entries = historical_data.get("entries", [])

        if not entries:
            print("⚠️ No historical data available, creating basic dashboard...")
            return self._create_basic_dashboard(output)

        # Filter by date range
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered_entries = []

        for entry in entries:
            try:
                entry_date = datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
                if entry_date.replace(tzinfo=None) >= cutoff_date:
                    filtered_entries.append(entry)
            except (ValueError, KeyError, TypeError):
                # Include entries with parsing issues
                filtered_entries.append(entry)

        if not filtered_entries:
            print("⚠️ No data in specified date range, using all available data...")
            filtered_entries = entries[-min(30, len(entries)) :]  # Last 30 entries

        # Calculate trends
        nasa_scores = [e.get("nasa_score", 0) for e in filtered_entries]
        critical_violations = [e.get("critical_violations", 0) for e in filtered_entries]
        total_violations = [e.get("total_violations", 0) for e in filtered_entries]
        mece_scores = [e.get("mece_score", 0) for e in filtered_entries]

        trends = {
            "nasa_score": self.calculate_trend_direction(nasa_scores),
            "critical_violations": self.calculate_trend_direction(critical_violations),
            "total_violations": self.calculate_trend_direction(total_violations),
            "mece_score": self.calculate_trend_direction(mece_scores),
        }

        # Generate HTML
        html_content = self._generate_trend_html(filtered_entries, trends, days)

        # Save dashboard
        output_path = Path(output)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"✅ Trend dashboard saved to: {output_path}")
        return str(output_path)

    def _create_basic_dashboard(self, output: str) -> str:
        """Create basic dashboard when no historical data is available."""
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connascence Analysis Trends</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; color: #333; margin-bottom: 30px; }}
        .info-box {{ background: #e3f2fd; padding: 20px; border-radius: 5px; border-left: 4px solid #2196f3; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1> Connascence Analysis Trends</h1>
            <p>Historical Trend Analysis Dashboard</p>
        </div>

        <div class="info-box">
            <h3> Trend Analysis Initializing</h3>
            <p><strong>Status:</strong> No historical data available yet</p>
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            <p><strong>Note:</strong> Trend analysis will be available after multiple analysis runs</p>
        </div>

        <div style="margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 5px;">
            <h4>DATA What You'll See Next Time:</h4>
            <ul>
                <li>NASA Power of Ten compliance trends</li>
                <li>Critical violation patterns over time</li>
                <li>MECE score improvements</li>
                <li>Code quality progression charts</li>
                <li>Comparative analysis across commits</li>
            </ul>
        </div>
    </div>
</body>
</html>"""

        output_path = Path(output)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return str(output_path)

    def _generate_trend_html(self, entries: List[Dict], trends: Dict[str, str], days: int) -> str:
        """Generate comprehensive trend analysis HTML."""
        if not entries:
            return self._create_basic_dashboard("temp.html")

        latest = entries[-1] if entries else {}
        entry_count = len(entries)

        # Calculate averages
        avg_nasa = sum(e.get("nasa_score", 0) for e in entries) / len(entries) if entries else 0
        avg_critical = sum(e.get("critical_violations", 0) for e in entries) / len(entries) if entries else 0
        avg_mece = sum(e.get("mece_score", 0) for e in entries) / len(entries) if entries else 0

        # Trend indicators
        trend_icons = {"improving": "📈 ↗️", "declining": "📉 ↘️", "stable": "📊 →"}

        trend_colors = {"improving": "#28a745", "declining": "#dc3545", "stable": "#6c757d"}

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connascence Analysis Trends - Last {days} Days</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 2.5em; font-weight: 300; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; padding: 30px; }}
        .trend-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff; }}
        .trend-card.improving {{ border-left-color: #28a745; }}
        .trend-card.declining {{ border-left-color: #dc3545; }}
        .trend-card.stable {{ border-left-color: #6c757d; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #333; margin-bottom: 10px; }}
        .metric-label {{ color: #666; font-size: 1em; margin-bottom: 10px; }}
        .trend-indicator {{ font-size: 1.2em; font-weight: bold; }}
        .summary-section {{ padding: 30px; border-top: 1px solid #eee; }}
        .data-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        .data-table th, .data-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        .data-table th {{ background-color: #f8f9fa; font-weight: bold; }}
        .footer {{ background: #333; color: white; padding: 20px; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1> Connascence Analysis Trends</h1>
            <p>Historical Analysis * Last {days} Days * {entry_count} Data Points</p>
            <p>Period: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        </div>

        <div class="metrics-grid">
            <div class="trend-card {trends.get('nasa_score', 'stable')}">
                <div class="metric-value">{latest.get('nasa_score', 0):.1%}</div>
                <div class="metric-label">Current NASA Compliance</div>
                <div class="trend-indicator" style="color: {trend_colors.get(trends.get('nasa_score', 'stable'))}">
                    {trend_icons.get(trends.get('nasa_score', 'stable'))} {trends.get('nasa_score', 'stable').title()}
                </div>
                <div style="margin-top: 10px; font-size: 0.9em; color: #666;">
                    Average: {avg_nasa:.1%}
                </div>
            </div>

            <div class="trend-card {trends.get('critical_violations', 'stable')}">
                <div class="metric-value">{latest.get('critical_violations', 0)}</div>
                <div class="metric-label">Critical Violations</div>
                <div class="trend-indicator" style="color: {trend_colors.get(trends.get('critical_violations', 'stable'))}">
                    {trend_icons.get(trends.get('critical_violations', 'stable'))} {trends.get('critical_violations', 'stable').title()}
                </div>
                <div style="margin-top: 10px; font-size: 0.9em; color: #666;">
                    Average: {avg_critical:.1f}
                </div>
            </div>

            <div class="trend-card {trends.get('total_violations', 'stable')}">
                <div class="metric-value">{latest.get('total_violations', 0)}</div>
                <div class="metric-label">Total Violations</div>
                <div class="trend-indicator" style="color: {trend_colors.get(trends.get('total_violations', 'stable'))}">
                    {trend_icons.get(trends.get('total_violations', 'stable'))} {trends.get('total_violations', 'stable').title()}
                </div>
            </div>

            <div class="trend-card {trends.get('mece_score', 'stable')}">
                <div class="metric-value">{latest.get('mece_score', 0):.2f}</div>
                <div class="metric-label">MECE Score</div>
                <div class="trend-indicator" style="color: {trend_colors.get(trends.get('mece_score', 'stable'))}">
                    {trend_icons.get(trends.get('mece_score', 'stable'))} {trends.get('mece_score', 'stable').title()}
                </div>
                <div style="margin-top: 10px; font-size: 0.9em; color: #666;">
                    Average: {avg_mece:.2f}
                </div>
            </div>
        </div>

        <div class="summary-section">
            <h2>DATA Recent Analysis History</h2>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>NASA Score</th>
                        <th>Critical Issues</th>
                        <th>Total Issues</th>
                        <th>MECE Score</th>
                        <th>Commit</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join([f'''
                    <tr>
                        <td>{datetime.fromisoformat(entry.get('timestamp', '')).strftime('%Y-%m-%d %H:%M') if entry.get('timestamp') else 'Unknown'}</td>
                        <td>{entry.get('nasa_score', 0):.1%}</td>
                        <td>{entry.get('critical_violations', 0)}</td>
                        <td>{entry.get('total_violations', 0)}</td>
                        <td>{entry.get('mece_score', 0):.2f}</td>
                        <td>{entry.get('commit_sha', 'Unknown')[:8] if entry.get('commit_sha') else 'N/A'}</td>
                    </tr>''' for entry in entries[-10:]])}  <!-- Show last 10 entries -->
                </tbody>
            </table>
        </div>

        <div class="footer">
            <p>SECURITY Generated by Connascence Safety Analyzer Trend Analysis |
            Data Points: {entry_count} | Time Range: {days} days</p>
        </div>
    </div>
</body>
</html>"""

        return html_content


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Connascence Safety Analyzer - Historical Metrics and Trend Analysis")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Update trends command
    update_parser = subparsers.add_parser("--update-trends", help="Update historical trends")
    update_parser.add_argument("--nasa-results", required=True, help="Path to NASA analysis results")
    update_parser.add_argument("--connascence-results", required=True, help="Path to connascence analysis results")
    update_parser.add_argument("--mece-results", required=True, help="Path to MECE analysis results")
    update_parser.add_argument("--commit-sha", required=True, help="Git commit SHA")

    # Generate trends dashboard command
    dashboard_parser = subparsers.add_parser("--generate-trends-dashboard", help="Generate trends dashboard")
    dashboard_parser.add_argument("--days", type=int, default=30, help="Number of days to include (default: 30)")
    dashboard_parser.add_argument("--output", default="trend_dashboard.html", help="Output file name")

    # Handle both old-style and new-style arguments
    if len(sys.argv) > 1:
        if sys.argv[1].startswith("--update-trends"):
            # Handle --update-trends being passed as single argument
            sys.argv[1] = "--update-trends"
        elif sys.argv[1].startswith("--generate-trends-dashboard"):
            sys.argv[1] = "--generate-trends-dashboard"

    args = parser.parse_args()

    try:
        analyzer = MetricsTrendAnalyzer()

        if args.command == "--update-trends":
            success = analyzer.update_trends(
                args.nasa_results, args.connascence_results, args.mece_results, args.commit_sha
            )
            if success:
                print("🎉 Historical trends updated successfully!")
                return 0
            else:
                print("❌ Failed to update historical trends")
                return 1

        elif args.command == "--generate-trends-dashboard":
            dashboard_path = analyzer.generate_trends_dashboard(days=args.days, output=args.output)
            print(f"🎉 Trend dashboard generated: {dashboard_path}")
            return 0

        else:
            parser.print_help()
            return 1

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
