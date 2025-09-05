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
Self-Analysis with NASA Power of Ten Compliance
==============================================

This script applies the complete connascence analysis suite, NASA Power of Ten
compliance checking, and MECE duplication analysis to our own codebase.

This demonstrates the tool's capability by analyzing itself and providing
comprehensive quality metrics and improvement recommendations.

Usage:
    python scripts/self_analysis_with_nasa_compliance.py

Output:
    - Comprehensive analysis report
    - NASA compliance assessment
    - MECE duplication findings
    - Actionable improvement recommendations
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from analyzer.ast_engine.core_analyzer import ConnascenceASTAnalyzer
    from analyzer.dup_detection import MECEAnalyzer
    from integrations.tool_coordinator import ToolCoordinator
    from mcp.nasa_power_of_ten_integration import NASAPowerOfTenIntegration
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


class ComprehensiveSelfAnalysis:
    """Comprehensive self-analysis of the connascence codebase."""
    
    def __init__(self):
        self.project_root = project_root
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'analysis_type': 'comprehensive_self_analysis',
            'connascence_analysis': {},
            'nasa_compliance': {},
            'mece_duplication': {},
            'tool_integration': {},
            'recommendations': [],
            'metrics': {}
        }
        
        # Initialize analyzers
        self.connascence_analyzer = ConnascenceASTAnalyzer()
        self.mece_analyzer = MECEAnalyzer()
        self.nasa_integration = NASAPowerOfTenIntegration()
        self.tool_coordinator = ToolCoordinator()
    
    async def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """Run complete analysis suite on the codebase."""
        
        print("🚀 Starting Comprehensive Self-Analysis...")
        print(f"📁 Analyzing project: {self.project_root}")
        print("=" * 60)
        
        # Phase 1: Connascence Analysis
        print("\n🔍 Phase 1: Connascence Analysis")
        await self._analyze_connascence()
        
        # Phase 2: NASA Power of Ten Compliance
        print("\n🛡️ Phase 2: NASA Power of Ten Compliance Check")
        await self._check_nasa_compliance()
        
        # Phase 3: MECE Duplication Analysis  
        print("\n🔍 Phase 3: MECE Duplication Analysis")
        await self._analyze_duplications()
        
        # Phase 4: Tool Integration Analysis
        print("\n🔧 Phase 4: Multi-Tool Integration Analysis")
        await self._analyze_tool_integration()
        
        # Phase 5: Generate Recommendations
        print("\n💡 Phase 5: Generate Improvement Recommendations")
        self._generate_recommendations()
        
        # Phase 6: Calculate Quality Metrics
        print("\n📊 Phase 6: Calculate Quality Metrics")
        self._calculate_metrics()
        
        print("\n✅ Comprehensive analysis complete!")
        return self.results
    
    async def _analyze_connascence(self):
        """Analyze connascence violations in the codebase."""
        print("  🔍 Scanning for connascence violations...")
        
        violations = []
        files_analyzed = 0
        
        # Analyze Python files
        for py_file in self.project_root.rglob("*.py"):
            if self._should_analyze_file(py_file):
                try:
                    file_violations = self.connascence_analyzer.analyze_file(py_file)
                    violations.extend(file_violations)
                    files_analyzed += 1
                except Exception as e:
                    print(f"    ⚠️ Error analyzing {py_file}: {e}")
        
        # Categorize violations
        violation_counts = {}
        severity_counts = {}
        
        for violation in violations:
            v_type = violation.type.value if hasattr(violation, 'type') else str(violation.get('type', 'unknown'))
            severity = violation.severity.value if hasattr(violation, 'severity') else str(violation.get('severity', 'unknown'))
            
            violation_counts[v_type] = violation_counts.get(v_type, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        self.results['connascence_analysis'] = {
            'files_analyzed': files_analyzed,
            'total_violations': len(violations),
            'violations_by_type': violation_counts,
            'violations_by_severity': severity_counts,
            'violations': [self._serialize_violation(v) for v in violations[:50]]  # First 50 for report
        }
        
        print(f"    📊 Found {len(violations)} violations across {files_analyzed} files")
        for v_type, count in violation_counts.items():
            print(f"    - {v_type}: {count}")
    
    async def _check_nasa_compliance(self):
        """Check NASA Power of Ten compliance."""
        print("  🛡️ Checking NASA Power of Ten compliance...")
        
        all_nasa_violations = []
        compliance_scores = []
        
        # Get connascence violations to check against NASA rules
        connascence_violations = self.results['connascence_analysis'].get('violations', [])
        
        for violation in connascence_violations[:20]:  # Check subset for performance
            nasa_violations = self.nasa_integration.check_nasa_violations(violation)
            all_nasa_violations.extend(nasa_violations)
            
            compliance_score = self.nasa_integration.calculate_nasa_compliance_score(nasa_violations)
            compliance_scores.append(compliance_score)
        
        # Calculate overall compliance
        overall_compliance = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 1.0
        
        # Count violations by NASA rule
        rule_violations = {}
        for nasa_violation in all_nasa_violations:
            rule_id = nasa_violation.get('rule_id', 'unknown')
            rule_violations[rule_id] = rule_violations.get(rule_id, 0) + 1
        
        self.results['nasa_compliance'] = {
            'overall_compliance_score': overall_compliance,
            'is_nasa_compliant': overall_compliance >= 0.9,
            'total_nasa_violations': len(all_nasa_violations),
            'violations_by_rule': rule_violations,
            'nasa_violations': all_nasa_violations[:20]  # First 20 for report
        }
        
        print(f"    📊 NASA Compliance Score: {overall_compliance:.2%}")
        print(f"    🛡️ NASA Violations: {len(all_nasa_violations)}")
        for rule, count in rule_violations.items():
            print(f"    - {rule}: {count}")
    
    async def _analyze_duplications(self):
        """Analyze code duplications using MECE analyzer."""  
        print("  🔍 Analyzing code duplications...")
        
        try:
            results = self.mece_analyzer.analyze_codebase(str(self.project_root), ['*.py'])
            
            clusters = results.get('duplication_clusters', [])
            opportunities = results.get('consolidation_opportunities', [])
            
            # Categorize clusters by type
            cluster_types = {}
            for cluster in clusters:
                cluster_type = cluster.duplication_type
                cluster_types[cluster_type] = cluster_types.get(cluster_type, 0) + 1
            
            self.results['mece_duplication'] = {
                'files_analyzed': results.get('files_analyzed', 0),
                'duplication_clusters_found': len(clusters),
                'consolidation_opportunities': len(opportunities),
                'clusters_by_type': cluster_types,
                'duplication_percentage': results.get('metrics', {}).get('duplication_percentage', 0),
                'high_confidence_clusters': len([c for c in clusters if c.confidence > 0.8]),
                'top_clusters': self._serialize_clusters(clusters[:10])
            }
            
            print(f"    📊 Duplication Clusters: {len(clusters)}")
            print(f"    🎯 Consolidation Opportunities: {len(opportunities)}")
            for cluster_type, count in cluster_types.items():
                print(f"    - {cluster_type}: {count}")
                
        except Exception as e:
            print(f"    ⚠️ MECE analysis failed: {e}")
            self.results['mece_duplication'] = {'error': str(e)}
    
    async def _analyze_tool_integration(self):
        """Analyze multi-tool integration effectiveness."""
        print("  🔧 Analyzing tool integration...")
        
        try:
            # Run integrated analysis on a subset of files
            test_dir = self.project_root / "analyzer"
            if test_dir.exists():
                enabled_tools = {'ruff', 'mypy', 'radon', 'bandit', 'black'}
                
                integration_results = await self.tool_coordinator.analyze_project(
                    test_dir,
                    enabled_tools=enabled_tools,
                    include_connascence=True
                )
                
                # Analyze correlation effectiveness
                correlations = integration_results.correlations
                tool_results = integration_results.tool_results
                
                correlation_scores = {}
                for tool_pair, correlation in correlations.items():
                    score = correlation.get('correlation_score', 0)
                    correlation_scores[tool_pair] = score
                
                self.results['tool_integration'] = {
                    'tools_analyzed': list(enabled_tools),
                    'correlation_scores': correlation_scores,
                    'average_correlation': sum(correlation_scores.values()) / len(correlation_scores) if correlation_scores else 0,
                    'tool_coverage': {tool: len(results) for tool, results in tool_results.items()},
                    'integration_effectiveness': 'high' if sum(correlation_scores.values()) / len(correlation_scores) > 0.7 else 'medium'
                }
                
                print(f"    📊 Tools Integrated: {len(enabled_tools)}")
                print(f"    🎯 Average Correlation: {self.results['tool_integration']['average_correlation']:.2f}")
                
        except Exception as e:
            print(f"    ⚠️ Tool integration analysis failed: {e}")
            self.results['tool_integration'] = {'error': str(e)}
    
    def _generate_recommendations(self):
        """Generate actionable improvement recommendations."""
        recommendations = []
        
        # Connascence recommendations
        connascence_violations = self.results['connascence_analysis'].get('total_violations', 0)
        if connascence_violations > 100:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Code Quality',
                'issue': f'{connascence_violations} connascence violations found',
                'recommendation': 'Focus on reducing connascence of meaning (magic literals) and algorithm (god objects)',
                'estimated_effort': 'Medium',
                'impact': 'High - Improved maintainability'
            })
        
        # NASA compliance recommendations  
        nasa_compliance = self.results['nasa_compliance'].get('overall_compliance_score', 1.0)
        if nasa_compliance < 0.9:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Safety Compliance',
                'issue': f'NASA compliance score: {nasa_compliance:.2%}',
                'recommendation': 'Address NASA Power of Ten violations, especially Rules 1, 4, and 5',
                'estimated_effort': 'High',
                'impact': 'Critical - Safety compliance required'
            })
        
        # Duplication recommendations
        duplication_clusters = self.results['mece_duplication'].get('duplication_clusters_found', 0)
        if duplication_clusters > 10:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Code Duplication',
                'issue': f'{duplication_clusters} duplication clusters found',
                'recommendation': 'Consolidate exact duplicates first, then similar functions',
                'estimated_effort': 'Medium',
                'impact': 'Medium - Reduced maintenance burden'
            })
        
        # Tool integration recommendations
        integration_score = self.results['tool_integration'].get('average_correlation', 0)
        if integration_score < 0.5:
            recommendations.append({
                'priority': 'LOW',
                'category': 'Tool Integration',
                'issue': f'Low tool correlation score: {integration_score:.2f}',
                'recommendation': 'Improve correlation algorithms and tool result normalization',
                'estimated_effort': 'Low',
                'impact': 'Low - Better tool synergy'
            })
        
        self.results['recommendations'] = recommendations
        
        print(f"    💡 Generated {len(recommendations)} recommendations")
        for rec in recommendations:
            print(f"    - {rec['priority']}: {rec['issue']}")
    
    def _calculate_metrics(self):
        """Calculate overall quality metrics."""
        connascence_total = self.results['connascence_analysis'].get('total_violations', 0)
        files_analyzed = self.results['connascence_analysis'].get('files_analyzed', 1)
        nasa_compliance = self.results['nasa_compliance'].get('overall_compliance_score', 1.0)
        duplication_percentage = self.results['mece_duplication'].get('duplication_percentage', 0)
        
        # Calculate composite quality score
        quality_score = (
            min(1.0, max(0.0, 1.0 - connascence_total / (files_analyzed * 10))) * 0.4 +  # 40% connascence
            nasa_compliance * 0.4 +  # 40% NASA compliance
            max(0.0, 1.0 - duplication_percentage / 100) * 0.2  # 20% duplication
        )
        
        self.results['metrics'] = {
            'overall_quality_score': quality_score,
            'quality_grade': self._get_quality_grade(quality_score),
            'connascence_density': connascence_total / files_analyzed if files_analyzed > 0 else 0,
            'nasa_compliance_score': nasa_compliance,
            'duplication_percentage': duplication_percentage,
            'tool_integration_score': self.results['tool_integration'].get('average_correlation', 0)
        }
        
        print(f"    📊 Overall Quality Score: {quality_score:.2%}")
        print(f"    🎖️ Quality Grade: {self._get_quality_grade(quality_score)}")
    
    def _should_analyze_file(self, file_path: Path) -> bool:
        """Check if file should be analyzed."""
        if file_path.name.startswith('.'):
            return False
        if 'test' in str(file_path).lower():
            return False
        if '__pycache__' in str(file_path):
            return False
        if 'node_modules' in str(file_path):
            return False
        return True
    
    def _serialize_violation(self, violation) -> Dict[str, Any]:
        """Serialize violation for JSON output."""
        if hasattr(violation, '__dict__'):
            return {
                'type': violation.type.value if hasattr(violation.type, 'value') else str(violation.type),
                'severity': violation.severity.value if hasattr(violation.severity, 'value') else str(violation.severity),
                'message': getattr(violation, 'message', ''),
                'file': getattr(violation, 'file_path', ''),
                'line': getattr(violation, 'line_number', 0)
            }
        return violation if isinstance(violation, dict) else str(violation)
    
    def _serialize_clusters(self, clusters) -> List[Dict[str, Any]]:
        """Serialize duplication clusters for JSON output."""
        serialized = []
        for cluster in clusters:
            try:
                serialized.append({
                    'cluster_id': cluster.cluster_id,
                    'type': cluster.duplication_type,
                    'confidence': cluster.confidence,
                    'files_involved': cluster.files_involved,
                    'similarity_score': cluster.similarity_score,
                    'recommendation': cluster.consolidation_recommendation
                })
            except AttributeError:
                serialized.append(str(cluster))
        return serialized
    
    def _get_quality_grade(self, score: float) -> str:
        """Get letter grade for quality score."""
        if score >= 0.9: return 'A'
        elif score >= 0.8: return 'B'
        elif score >= 0.7: return 'C'
        elif score >= 0.6: return 'D'
        else: return 'F'


def save_results(results: Dict[str, Any], output_file: str = "self_analysis_results.json"):
    """Save analysis results to file."""
    output_path = project_root / output_file
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Results saved to: {output_path}")
    return output_path


def print_summary(results: Dict[str, Any]):
    """Print executive summary of results."""
    print("\n" + "="*60)
    print("🏆 COMPREHENSIVE SELF-ANALYSIS SUMMARY")  
    print("="*60)
    
    metrics = results.get('metrics', {})
    
    print(f"📊 Overall Quality Score: {metrics.get('overall_quality_score', 0):.2%}")
    print(f"🎖️ Quality Grade: {metrics.get('quality_grade', 'N/A')}")
    print()
    
    print("📈 Key Metrics:")
    print(f"  • Connascence Violations: {results['connascence_analysis'].get('total_violations', 0)}")
    print(f"  • NASA Compliance: {results['nasa_compliance'].get('overall_compliance_score', 0):.2%}")
    print(f"  • Duplication Clusters: {results['mece_duplication'].get('duplication_clusters_found', 0)}")
    print(f"  • Files Analyzed: {results['connascence_analysis'].get('files_analyzed', 0)}")
    print()
    
    recommendations = results.get('recommendations', [])
    if recommendations:
        print("💡 Top Recommendations:")
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"  {i}. [{rec['priority']}] {rec['issue']}")
            print(f"     → {rec['recommendation']}")
        print()
    
    print("✅ Analysis Complete! See detailed results in JSON file.")
    print("="*60)


async def main():
    """Main function to run comprehensive self-analysis."""
    print("🚀 Connascence Self-Analysis with NASA Compliance")
    print("Analyzing our own codebase for quality and compliance...")
    print()
    
    try:
        analyzer = ComprehensiveSelfAnalysis()
        results = await analyzer.run_comprehensive_analysis()
        
        # Save results
        output_file = save_results(results)
        
        # Print summary  
        print_summary(results)
        
        # Additional output for CI/CD
        if '--ci' in sys.argv:
            quality_score = results.get('metrics', {}).get('overall_quality_score', 0)
            if quality_score < 0.7:
                print("\n❌ Quality score below threshold (70%)")
                sys.exit(1)
            else:
                print("\n✅ Quality threshold met")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))