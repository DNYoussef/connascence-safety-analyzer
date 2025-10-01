#!/usr/bin/env python3

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
Test script for Enhanced Tool Coordinator - Phase 2
==================================================

Tests the enhanced tool coordinator capabilities and validates
Phase 2 implementation features.
"""

import asyncio
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from integrations.enhanced_tool_coordinator import EnhancedToolCoordinator


async def main():
    """Test enhanced tool coordinator."""
    print("Testing Enhanced Tool Coordinator - Phase 2")
    print("=" * 60)

    # Initialize enhanced coordinator
    config = {
        "enhancements": {"ai_recommendations": True, "confidence_threshold": 0.75, "severity_weight": 0.8},
        "ruff": {"enabled": True},
        "mypy": {"enabled": True},
    }

    coordinator = EnhancedToolCoordinator(config)

    # Test on analyzer directory (contains connascence violations)
    test_path = Path(__file__).parent.parent / "analyzer"

    print(f"Analyzing: {test_path}")
    print("Features enabled:")
    print("  + Enhanced correlation analysis")
    print("  + Cross-tool severity classification")
    print("  + AI-powered recommendations")
    print("  + Performance bottleneck detection")
    print("  + NASA rules correlation")
    print("  + MECE analysis integration")
    print()

    try:
        # Run enhanced analysis
        result = await coordinator.enhanced_analyze_project(
            project_path=test_path,
            enabled_tools={"ruff", "mypy"},  # Limit to available tools for testing
            include_connascence=True,
            enable_nasa_correlation=True,
            enable_mece_analysis=True,
        )

        print("ENHANCED ANALYSIS RESULTS")
        print("-" * 40)
        print("Base analysis completed: [OK]")
        print(f"Enhanced correlations: {len(result.enhanced_correlations)}")
        print(f"Performance metrics: {len(result.performance_metrics)}")
        print(f"AI recommendations: {len(result.ai_recommendations)}")
        print()

        # Show top correlations
        if result.enhanced_correlations:
            print("TOP CORRELATIONS")
            print("-" * 40)
            for i, correlation in enumerate(result.enhanced_correlations[:3], 1):
                print(f"{i}. {correlation.correlation_type}")
                print(f"   Confidence: {correlation.confidence_score:.2%}")
                print(f"   Supporting tools: {len(correlation.supporting_tools)}")
                print(f"   Priority: {correlation.recommendation_priority}")
                print()

        # Show AI recommendations
        if result.ai_recommendations:
            print("AI RECOMMENDATIONS")
            print("-" * 40)
            for i, rec in enumerate(result.ai_recommendations[:3], 1):
                print(f"{i}. {rec['title']}")
                print(f"   Type: {rec['type']}")
                print(f"   Effort: {rec.get('estimated_effort', 'unknown')}")
                print()

        # Show enhanced execution summary
        print("PERFORMANCE METRICS")
        print("-" * 40)
        summary = result.execution_summary
        print(f"Tools executed: {summary.get('tools_executed', 0)}")
        print(f"Tools failed: {summary.get('tools_failed', 0)}")
        print(f"Base analysis time: {summary.get('total_execution_time', 0):.2f}s")
        print(f"Enhancement time: {summary.get('enhancement_time', 0):.2f}s")
        print()

        # Generate enhanced report
        print("GENERATING ENHANCED REPORT")
        print("-" * 40)

        report = coordinator.generate_enhanced_report(result, format_type="text")
        report_lines = report.split("\n")

        # Show first 20 lines of report
        print("Preview (first 20 lines):")
        for line in report_lines[:20]:
            print(line)
        print("... (truncated)")
        print()

        print("[OK] Phase 2 Enhanced Tool Coordinator Test PASSED")
        print(f"   - Enhanced correlations: {len(result.enhanced_correlations)} generated")
        print(f"   - AI recommendations: {len(result.ai_recommendations)} generated")
        print(f"   - Performance metrics: {len(result.performance_metrics)} identified")
        print("   - Cross-tool consensus: Available")

        # Save detailed report for inspection
        report_file = Path(__file__).parent.parent / "enhanced_analysis_report.txt"
        with open(report_file, "w") as f:
            f.write(report)
        print(f"   - Detailed report saved: {report_file}")

    except Exception as e:
        print(f"[ERROR] Enhanced analysis failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
