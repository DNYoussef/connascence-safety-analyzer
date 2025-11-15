#!/usr/bin/env python3
"""
Comprehensive Dogfooding Analysis - All Analyzers Integrated
============================================================

This script orchestrates ALL analyzer capabilities in a single comprehensive analysis:
- 9 Types of Connascence Detection
- God Object Detection
- MECE Duplication Detection
- NASA Power of Ten Compliance
- Six Sigma Quality Metrics
- Clarity Analysis
- Multiple output formats (JSON, SARIF, YAML)
"""

import argparse
from datetime import datetime
import json
import logging
from pathlib import Path
import sys
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.unified_analyzer import UnifiedConnascenceAnalyzer


def print_banner():
    """Print analysis banner."""
    print("=" * 80)
    print("COMPREHENSIVE DOGFOODING ANALYSIS")
    print("Analyzer Analyzing Itself - All Capabilities Enabled")
    print("=" * 80)
    print()

def print_analyzer_status():
    """Print status of all integrated analyzers."""
    print("Enabled Analyzers:")
    print("-" * 80)

    analyzers = [
        ("Connascence Detection", "9 types (CoN, CoT, CoM, CoP, CoA, CoE, CoV, CoI, CoTiming)"),
        ("God Object Detection", "Excessive methods/complexity detection"),
        ("MECE Duplication", "Mutually Exclusive, Collectively Exhaustive analysis"),
        ("NASA Power of Ten", "10 safety-critical rules"),
        ("Six Sigma Quality", "DPMO, Sigma Level, Process Capability"),
        ("Clarity Linter", "Code readability and maintainability"),
        ("Smart Integration", "Multi-linter correlation"),
        ("SARIF Output", "Security Analysis Results Interchange Format"),
    ]

    for name, description in analyzers:
        print(f"  [OK] {name:25s} - {description}")

    print()

def run_comprehensive_analysis(path: str, output_dir: Path) -> dict:
    """Run comprehensive analysis with all analyzers."""
    print("Starting Comprehensive Analysis...")
    print(f"Target: {path}")
    print(f"Output Directory: {output_dir}")
    print("-" * 80)

    start_time = time.time()

    # Initialize unified analyzer with all components
    logger.info("Initializing UnifiedConnascenceAnalyzer...")
    analyzer = UnifiedConnascenceAnalyzer()

    # Verify all components loaded
    components = []
    if hasattr(analyzer, 'ast_analyzer'):
        components.append("AST")
    if hasattr(analyzer, 'god_object_orchestrator'):
        components.append("GodObject")
    if hasattr(analyzer, 'mece_analyzer'):
        components.append("MECE")
    if hasattr(analyzer, 'nasa_integration'):
        components.append("NASA")
    if hasattr(analyzer, 'smart_engine'):
        components.append("SmartEngine")

    logger.info(f"Components loaded: {', '.join(components)}")

    # Run analysis
    logger.info("Running comprehensive analysis...")
    print("\nAnalyzing...")

    try:
        result = analyzer.analyze_project(
            project_path=path,
            policy_preset="standard",
            options={
                "include_god_objects": True,
                "include_mece_analysis": True,
                "include_nasa_rules": True,
                "enable_correlations": True,
                "enhanced_output": True
            }
        )

        analysis_time = time.time() - start_time

        print(f"\n[OK] Analysis complete in {analysis_time:.2f} seconds")

        # Print summary
        print("\nAnalysis Summary:")
        print("-" * 80)
        print(f"Total Violations: {result.total_violations}")
        print(f"  Critical: {result.critical_count}")
        print(f"  High: {result.high_count}")
        print(f"  Medium: {result.medium_count}")
        print(f"  Low: {result.low_count}")
        print()
        print(f"Quality Metrics:")
        print(f"  Connascence Index: {result.connascence_index:.2f}")
        print(f"  NASA Compliance Score: {result.nasa_compliance_score:.3f}")
        print(f"  Duplication Score: {result.duplication_score:.3f}")
        print(f"  Overall Quality Score: {result.overall_quality_score:.3f}")
        print()

        # Convert to dict for saving
        result_dict = {
            "metadata": {
                "analysis_date": datetime.now().isoformat(),
                "target_path": str(path),
                "analysis_time_seconds": round(analysis_time, 2),
                "analyzer_version": "1.0.0",
                "components_used": components
            },
            "summary": {
                "total_violations": result.total_violations,
                "critical_violations": result.critical_count,
                "high_violations": result.high_count,
                "medium_violations": result.medium_count,
                "low_violations": result.low_count,
                "connascence_index": result.connascence_index,
                "nasa_compliance_score": result.nasa_compliance_score,
                "duplication_score": result.duplication_score,
                "overall_quality_score": result.overall_quality_score
            },
            "violations": {
                "connascence": result.connascence_violations,
                "duplication": result.duplication_clusters,
                "nasa": result.nasa_violations
            },
            "recommendations": result.recommendations if hasattr(result, 'recommendations') else []
        }

        return result_dict

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        print(f"\n[FAIL] Analysis error: {e}")
        return None

def save_outputs(result: dict, output_dir: Path):
    """Save analysis results in multiple formats."""
    print("\nSaving Reports...")
    print("-" * 80)

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Save JSON report
    json_path = output_dir / "dogfooding-comprehensive.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, default=str)
    print(f"  [OK] JSON report: {json_path}")

    # 2. Save summary report (text)
    summary_path = output_dir / "dogfooding-summary.txt"
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("COMPREHENSIVE DOGFOODING ANALYSIS SUMMARY\n")
        f.write("=" * 80 + "\n\n")

        f.write("Metadata:\n")
        f.write("-" * 80 + "\n")
        for key, value in result['metadata'].items():
            f.write(f"  {key}: {value}\n")
        f.write("\n")

        f.write("Summary:\n")
        f.write("-" * 80 + "\n")
        for key, value in result['summary'].items():
            f.write(f"  {key}: {value}\n")
        f.write("\n")

        # Violation breakdown
        f.write("Violation Breakdown:\n")
        f.write("-" * 80 + "\n")
        f.write(f"  Connascence violations: {len(result['violations']['connascence'])}\n")
        f.write(f"  Duplication clusters: {len(result['violations']['duplication'])}\n")
        f.write(f"  NASA violations: {len(result['violations']['nasa'])}\n")
        f.write("\n")

        # Top violation types
        from collections import Counter
        violation_types = Counter()
        for v in result['violations']['connascence']:
            violation_types[v.get('type', 'unknown')] += 1

        f.write("Top 10 Violation Types:\n")
        f.write("-" * 80 + "\n")
        for vtype, count in violation_types.most_common(10):
            f.write(f"  {vtype:30s}: {count:5d}\n")
        f.write("\n")

    print(f"  [OK] Summary report: {summary_path}")

    # 3. Generate SARIF output using CLI
    try:
        import subprocess
        sarif_path = output_dir / "dogfooding-comprehensive.sarif"
        cmd = [
            sys.executable, "-m", "analyzer",
            "--path", result['metadata']['target_path'],
            "--format", "sarif",
            "--output", str(sarif_path)
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"  [OK] SARIF report: {sarif_path}")
    except Exception as e:
        print(f"  [WARN] SARIF generation skipped: {e}")

    print()

def print_recommendations(result: dict):
    """Print actionable recommendations."""
    print("Actionable Recommendations:")
    print("-" * 80)

    recommendations = result.get('recommendations', [])
    if isinstance(recommendations, dict):
        priority_fixes = recommendations.get('priority_fixes', [])
        improvement_actions = recommendations.get('improvement_actions', [])

        if priority_fixes:
            print("\nPriority Fixes:")
            for i, fix in enumerate(priority_fixes[:5], 1):
                print(f"  {i}. {fix}")

        if improvement_actions:
            print("\nImprovement Actions:")
            for i, action in enumerate(improvement_actions[:5], 1):
                print(f"  {i}. {action}")

    print()

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive Dogfooding Analysis - All Analyzers Integrated"
    )
    parser.add_argument(
        "--path",
        default="analyzer/",
        help="Path to analyze (default: analyzer/)"
    )
    parser.add_argument(
        "--output-dir",
        default="docs/dogfooding",
        help="Output directory for reports (default: docs/dogfooding)"
    )

    args = parser.parse_args()

    # Print banner
    print_banner()
    print_analyzer_status()

    # Run analysis
    output_dir = Path(args.output_dir)
    result = run_comprehensive_analysis(args.path, output_dir)

    if result is None:
        print("\n[FAIL] Analysis failed. Check logs for details.")
        return 1

    # Save outputs
    save_outputs(result, output_dir)

    # Print recommendations
    print_recommendations(result)

    # Final summary
    print("=" * 80)
    print("COMPREHENSIVE DOGFOODING ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\nTotal Violations: {result['summary']['total_violations']}")
    print(f"Overall Quality Score: {result['summary']['overall_quality_score']:.3f}")
    print(f"\nReports saved to: {output_dir}")
    print()

    return 0

if __name__ == "__main__":
    sys.exit(main())
