#!/usr/bin/env python3
"""
CI Integration Dashboard Generator for Connascence Safety Analyzer
================================================================

Generates comprehensive HTML dashboards for CI/CD pipeline integration.
Compatible with GitHub Actions and other CI systems.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class CIDashboardGenerator:
    """Generates CI-compatible dashboards from analysis results."""
    
    def __init__(self, output_dir: str = "."):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'analysis_results': {},
            'policy_compliance': {},
            'summary': {}
        }
        
    def load_analysis_results(self) -> None:
        """Load available analysis results from current directory."""
        result_files = {
            'nasa': 'nasa_analysis.json',
            'connascence': 'connascence_full.json', 
            'mece': 'mece_analysis.json',
            'god_objects': 'god_objects.json',
            'correlated': 'correlated_results.json'
        }
        
        for analysis_type, filename in result_files.items():
            file_path = Path(filename)
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    self.dashboard_data['analysis_results'][analysis_type] = data
                    print(f"✅ Loaded {analysis_type} results from {filename}")
                except Exception as e:
                    print(f"⚠️ Could not load {filename}: {e}")
                    self.dashboard_data['analysis_results'][analysis_type] = {'error': str(e)}
            else:
                print(f"ℹ️ {filename} not found, skipping {analysis_type} analysis")
                
    def generate_summary_metrics(self) -> None:
        """Generate summary metrics from loaded analysis data."""
        summary = {
            'total_violations': 0,
            'critical_violations': 0,
            'nasa_score': 0.0,
            'mece_score': 0.0,
            'god_objects_count': 0,
            'overall_quality_score': 0.0
        }
        
        # Extract NASA compliance
        if 'nasa' in self.dashboard_data['analysis_results']:
            nasa_data = self.dashboard_data['analysis_results']['nasa']
            if 'nasa_compliance' in nasa_data:
                summary['nasa_score'] = nasa_data['nasa_compliance'].get('score', 0.0)
            
        # Extract connascence metrics
        if 'connascence' in self.dashboard_data['analysis_results']:
            conn_data = self.dashboard_data['analysis_results']['connascence']
            violations = conn_data.get('violations', [])
            summary['total_violations'] = len(violations)
            summary['critical_violations'] = len([v for v in violations if v.get('severity') == 'critical'])
            if 'summary' in conn_data:
                summary['overall_quality_score'] = conn_data['summary'].get('overall_quality_score', 0.0)
                
        # Extract MECE score
        if 'mece' in self.dashboard_data['analysis_results']:
            mece_data = self.dashboard_data['analysis_results']['mece']
            summary['mece_score'] = mece_data.get('mece_score', 0.0)
            
        # Extract god objects
        if 'god_objects' in self.dashboard_data['analysis_results']:
            god_data = self.dashboard_data['analysis_results']['god_objects']
            violations = god_data.get('violations', [])
            summary['god_objects_count'] = len([v for v in violations if v.get('type') == 'CoA' and 'God Object' in v.get('description', '')])
            
        self.dashboard_data['summary'] = summary
        
    def generate_html_dashboard(self, policy: str = "nasa_jpl_pot10") -> str:
        """Generate comprehensive HTML dashboard."""
        summary = self.dashboard_data['summary']
        timestamp = self.dashboard_data['timestamp']
        
        # Determine overall status
        nasa_pass = summary['nasa_score'] >= 0.90
        violations_acceptable = summary['critical_violations'] <= 50
        overall_pass = nasa_pass and violations_acceptable
        
        status_color = "#28a745" if overall_pass else "#dc3545"
        status_text = "PASSED" if overall_pass else "FAILED"
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connascence Analysis Dashboard - {policy.upper()}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .status-badge {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            margin-top: 10px;
            background-color: {status_color};
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 30px;
        }}
        .metric-card {{
            background: #f8f9fa;
            border-left: 4px solid #007bff;
            padding: 20px;
            border-radius: 8px;
        }}
        .metric-card.critical {{
            border-left-color: #dc3545;
        }}
        .metric-card.warning {{
            border-left-color: #ffc107;
        }}
        .metric-card.success {{
            border-left-color: #28a745;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }}
        .metric-label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .details-section {{
            padding: 30px;
            border-top: 1px solid #eee;
        }}
        .section-title {{
            font-size: 1.5em;
            margin-bottom: 20px;
            color: #333;
        }}
        .analysis-item {{
            background: #f8f9fa;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 5px;
            border-left: 3px solid #007bff;
        }}
        .footer {{
            background: #333;
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 0.9em;
        }}
        .progress-bar {{
            width: 100%;
            height: 20px;
            background-color: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 10px;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #dc3545 0%, #ffc107 50%, #28a745 100%);
            transition: width 0.3s ease;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ Connascence Safety Analysis</h1>
            <div class="status-badge">{status_text}</div>
            <p>Policy: {policy.upper()} | Generated: {datetime.fromisoformat(timestamp).strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card {'success' if nasa_pass else 'critical'}">
                <div class="metric-value">{summary['nasa_score']:.1%}</div>
                <div class="metric-label">NASA Compliance Score</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {summary['nasa_score'] * 100}%"></div>
                </div>
            </div>
            
            <div class="metric-card {'success' if summary['critical_violations'] <= 10 else 'warning' if summary['critical_violations'] <= 50 else 'critical'}">
                <div class="metric-value">{summary['critical_violations']}</div>
                <div class="metric-label">Critical Violations</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-value">{summary['total_violations']}</div>
                <div class="metric-label">Total Violations</div>
            </div>
            
            <div class="metric-card {'success' if summary['mece_score'] >= 0.8 else 'warning'}">
                <div class="metric-value">{summary['mece_score']:.2f}</div>
                <div class="metric-label">MECE Score</div>
            </div>
            
            <div class="metric-card {'success' if summary['god_objects_count'] <= 5 else 'warning' if summary['god_objects_count'] <= 25 else 'critical'}">
                <div class="metric-value">{summary['god_objects_count']}</div>
                <div class="metric-label">God Objects</div>
            </div>
            
            <div class="metric-card {'success' if summary['overall_quality_score'] >= 0.7 else 'warning'}">
                <div class="metric-value">{summary['overall_quality_score']:.1%}</div>
                <div class="metric-label">Overall Quality Score</div>
            </div>
        </div>
        
        <div class="details-section">
            <h2 class="section-title">📊 Analysis Details</h2>
            
            {'<div class="analysis-item">✅ NASA Power of Ten compliance analysis completed</div>' if 'nasa' in self.dashboard_data['analysis_results'] else '<div class="analysis-item">⚠️ NASA analysis not available</div>'}
            
            {'<div class="analysis-item">✅ God Object detection completed</div>' if 'god_objects' in self.dashboard_data['analysis_results'] else '<div class="analysis-item">ℹ️ God Object analysis not available</div>'}
            
            {'<div class="analysis-item">✅ MECE duplication analysis completed</div>' if 'mece' in self.dashboard_data['analysis_results'] else '<div class="analysis-item">ℹ️ MECE analysis not available</div>'}
            
            {'<div class="analysis-item">✅ Full connascence analysis completed</div>' if 'connascence' in self.dashboard_data['analysis_results'] else '<div class="analysis-item">⚠️ Connascence analysis not available</div>'}
            
            {'<div class="analysis-item">✅ Tool correlation analysis completed</div>' if 'correlated' in self.dashboard_data['analysis_results'] else '<div class="analysis-item">ℹ️ Tool correlation not available</div>'}
        </div>
        
        <div class="details-section">
            <h2 class="section-title">🎯 Quality Gates</h2>
            
            <div class="analysis-item">
                {'✅ NASA Compliance: PASSED' if nasa_pass else '❌ NASA Compliance: FAILED'} 
                ({summary['nasa_score']:.1%} {'≥' if nasa_pass else '<'} 90%)
            </div>
            
            <div class="analysis-item">
                {'✅ Critical Violations: ACCEPTABLE' if violations_acceptable else '❌ Critical Violations: TOO HIGH'} 
                ({summary['critical_violations']} {'≤' if violations_acceptable else '>'} 50)
            </div>
            
            <div class="analysis-item">
                {'✅ God Objects: ACCEPTABLE' if summary['god_objects_count'] <= 25 else '❌ God Objects: TOO MANY'} 
                ({summary['god_objects_count']} {'≤' if summary['god_objects_count'] <= 25 else '>'} 25)
            </div>
            
            <div class="analysis-item">
                {'✅ MECE Score: GOOD' if summary['mece_score'] >= 0.75 else '⚠️ MECE Score: NEEDS IMPROVEMENT'} 
                ({summary['mece_score']:.2f} {'≥' if summary['mece_score'] >= 0.75 else '<'} 0.75)
            </div>
        </div>
        
        <div class="footer">
            <p>🛡️ Generated by Connascence Safety Analyzer | 
            Defense Industry Compliance: {'✅ APPROVED' if nasa_pass else '❌ NOT APPROVED'}</p>
        </div>
    </div>
</body>
</html>"""
        
        return html_content
        
    def save_dashboard(self, html_content: str) -> str:
        """Save the HTML dashboard to file."""
        dashboard_path = self.output_dir / "comprehensive_dashboard.html"
        
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"✅ Dashboard saved to: {dashboard_path}")
        return str(dashboard_path)
        
    def generate_dashboard(self, policy: str = "nasa_jpl_pot10") -> str:
        """Main method to generate complete dashboard."""
        print("Loading analysis results...")
        self.load_analysis_results()
        
        print("Generating summary metrics...")
        self.generate_summary_metrics()
        
        print("Creating HTML dashboard...")
        html_content = self.generate_html_dashboard(policy)
        
        print("Saving dashboard...")
        dashboard_path = self.save_dashboard(html_content)
        
        # Also create a simple JSON summary for CI systems
        json_summary_path = self.output_dir / "dashboard_summary.json"
        with open(json_summary_path, 'w') as f:
            json.dump({
                'timestamp': self.dashboard_data['timestamp'],
                'summary': self.dashboard_data['summary'],
                'overall_status': 'PASSED' if (self.dashboard_data['summary']['nasa_score'] >= 0.90 and 
                                             self.dashboard_data['summary']['critical_violations'] <= 50) else 'FAILED',
                'policy': policy
            }, f, indent=2)
        
        print(f"✅ Dashboard generation completed successfully!")
        return dashboard_path


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate CI/CD dashboard from Connascence analysis results"
    )
    parser.add_argument(
        '--output-dir', 
        default=".",
        help="Output directory for dashboard files (default: current directory)"
    )
    parser.add_argument(
        '--policy',
        default="nasa_jpl_pot10", 
        help="Policy compliance to highlight (default: nasa_jpl_pot10)"
    )
    
    args = parser.parse_args()
    
    try:
        generator = CIDashboardGenerator(args.output_dir)
        dashboard_path = generator.generate_dashboard(args.policy)
        
        print(f"\n🎉 Success! Dashboard available at: {dashboard_path}")
        return 0
        
    except Exception as e:
        print(f"❌ Dashboard generation failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())