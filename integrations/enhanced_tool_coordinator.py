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
Enhanced Tool Coordinator - Phase 2 Implementation
=================================================

PHASE 2 ENHANCEMENTS to existing tool_coordinator.py:
1. Enhanced correlation analysis with confidence scoring
2. Cross-tool severity classification
3. AI-powered recommendation system
4. Performance bottleneck detection
5. NASA rules correlation with linter findings
6. MECE analysis integration with tool results
7. Advanced reporting with multi-tool insights

This extends the existing 607-line tool_coordinator.py with enhanced capabilities
while maintaining backward compatibility.
"""

import asyncio
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
import statistics

# Import the existing tool coordinator as base
from .tool_coordinator import (
    ToolCoordinator as BaseToolCoordinator,
    ToolResult, IntegratedAnalysis
)

logger = logging.getLogger(__name__)


@dataclass
class EnhancedCorrelation:
    """Enhanced correlation analysis between tools and connascence."""
    correlation_type: str
    confidence_score: float
    supporting_tools: List[str]
    violation_impact: str
    recommendation_priority: str
    cross_tool_agreement: float
    severity_consensus: str
    actionable_steps: List[str]


@dataclass
class PerformanceMetrics:
    """Performance analysis metrics."""
    bottleneck_type: str
    affected_files: List[str]
    performance_impact: str
    optimization_opportunity: str
    estimated_improvement: float
    complexity_reduction: float


@dataclass
class EnhancedAnalysisResult(IntegratedAnalysis):
    """Enhanced analysis result with advanced metrics."""
    enhanced_correlations: List[EnhancedCorrelation]
    performance_metrics: List[PerformanceMetrics]
    severity_classification: Dict[str, Any]
    nasa_compliance_detail: Dict[str, Any]
    mece_integration_results: Dict[str, Any]
    ai_recommendations: List[Dict[str, Any]]
    cross_tool_consensus: Dict[str, float]
    quality_trends: Dict[str, Any]


class EnhancedToolCoordinator(BaseToolCoordinator):
    """Enhanced tool coordinator with Phase 2 capabilities."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.enhancement_config = config.get('enhancements', {}) if config else {}
        
        # Enhanced analysis settings
        self.enable_ai_recommendations = self.enhancement_config.get('ai_recommendations', True)
        self.cross_tool_confidence_threshold = self.enhancement_config.get('confidence_threshold', 0.75)
        self.severity_consensus_weight = self.enhancement_config.get('severity_weight', 0.8)
        
        # Performance tracking
        self.analysis_history: List[Dict] = []
        
    async def enhanced_analyze_project(self, project_path: Path,
                                     enabled_tools: Optional[Set[str]] = None,
                                     include_connascence: bool = True,
                                     enable_nasa_correlation: bool = True,
                                     enable_mece_analysis: bool = True) -> EnhancedAnalysisResult:
        """Enhanced project analysis with Phase 2 capabilities."""
        
        # Start with base analysis
        base_analysis = await super().analyze_project(
            project_path, enabled_tools, include_connascence
        )
        
        # Phase 2 Enhancements
        start_time = time.time()
        
        # Enhanced correlation analysis
        enhanced_correlations = await self._perform_enhanced_correlation_analysis(
            base_analysis.connascence_results,
            base_analysis.tool_results
        )
        
        # Cross-tool severity classification
        severity_classification = await self._enhanced_severity_classification(
            base_analysis.connascence_results,
            base_analysis.tool_results,
            enhanced_correlations
        )
        
        # Performance bottleneck detection
        performance_metrics = await self._detect_performance_bottlenecks(
            base_analysis.tool_results,
            base_analysis.connascence_results
        )
        
        # NASA rules correlation (if enabled)
        nasa_compliance_detail = {}
        if enable_nasa_correlation:
            nasa_compliance_detail = await self._correlate_nasa_rules(
                base_analysis.connascence_results,
                base_analysis.tool_results
            )
        
        # MECE integration (if enabled)
        mece_integration_results = {}
        if enable_mece_analysis:
            mece_integration_results = await self._integrate_mece_analysis(
                project_path,
                base_analysis.tool_results,
                enhanced_correlations
            )
        
        # AI-powered recommendations
        ai_recommendations = []
        if self.enable_ai_recommendations:
            ai_recommendations = await self._generate_ai_recommendations(
                base_analysis.connascence_results,
                base_analysis.tool_results,
                enhanced_correlations,
                performance_metrics
            )
        
        # Cross-tool consensus analysis
        cross_tool_consensus = self._calculate_cross_tool_consensus(
            base_analysis.tool_results,
            enhanced_correlations
        )
        
        # Quality trends (if historical data available)
        quality_trends = self._analyze_quality_trends(base_analysis, enhanced_correlations)
        
        enhancement_time = time.time() - start_time
        
        # Update execution summary
        enhanced_execution_summary = {
            **base_analysis.execution_summary,
            'enhancement_time': enhancement_time,
            'enhanced_features_enabled': {
                'correlation_analysis': True,
                'severity_classification': True,
                'performance_metrics': len(performance_metrics) > 0,
                'nasa_correlation': enable_nasa_correlation,
                'mece_analysis': enable_mece_analysis,
                'ai_recommendations': self.enable_ai_recommendations,
            }
        }
        
        return EnhancedAnalysisResult(
            # Base analysis fields
            connascence_results=base_analysis.connascence_results,
            tool_results=base_analysis.tool_results,
            correlations=base_analysis.correlations,
            recommendations=base_analysis.recommendations,
            overall_score=base_analysis.overall_score,
            execution_summary=enhanced_execution_summary,
            
            # Enhanced fields
            enhanced_correlations=enhanced_correlations,
            performance_metrics=performance_metrics,
            severity_classification=severity_classification,
            nasa_compliance_detail=nasa_compliance_detail,
            mece_integration_results=mece_integration_results,
            ai_recommendations=ai_recommendations,
            cross_tool_consensus=cross_tool_consensus,
            quality_trends=quality_trends
        )
    
    async def _perform_enhanced_correlation_analysis(self, 
                                                   connascence_results: Dict,
                                                   tool_results: Dict[str, ToolResult]) -> List[EnhancedCorrelation]:
        """Phase 2: Enhanced correlation analysis with confidence scoring."""
        correlations = []
        
        violations = connascence_results.get('violations', [])
        
        for violation in violations:
            # Analyze each violation against all tool results
            correlation = await self._analyze_violation_correlations(violation, tool_results)
            if correlation.confidence_score >= self.cross_tool_confidence_threshold:
                correlations.append(correlation)
        
        # Sort by confidence score and impact
        correlations.sort(key=lambda c: (c.confidence_score, c.cross_tool_agreement), reverse=True)
        
        return correlations
    
    async def _analyze_violation_correlations(self, violation: Dict, 
                                            tool_results: Dict[str, ToolResult]) -> EnhancedCorrelation:
        """Analyze correlation between a single violation and all tools."""
        
        violation_type = violation.get('type', '')
        file_path = violation.get('file_path', '')
        line_number = violation.get('line_number', 0)
        
        supporting_tools = []
        tool_agreements = []
        actionable_steps = []
        
        # Check each tool for related findings
        for tool_name, tool_result in tool_results.items():
            if not tool_result.success:
                continue
                
            correlation_strength = await self._calculate_tool_correlation_strength(
                violation, tool_name, tool_result
            )
            
            if correlation_strength > 0.5:
                supporting_tools.append(tool_name)
                tool_agreements.append(correlation_strength)
                
                # Get tool-specific actionable steps
                steps = self._get_tool_specific_actions(violation_type, tool_name, tool_result)
                actionable_steps.extend(steps)
        
        # Calculate confidence metrics
        confidence_score = statistics.mean(tool_agreements) if tool_agreements else 0.0
        cross_tool_agreement = len(supporting_tools) / len(tool_results) if tool_results else 0.0
        
        # Determine violation impact and priority
        violation_impact = self._assess_violation_impact(violation, supporting_tools)
        recommendation_priority = self._determine_recommendation_priority(
            confidence_score, cross_tool_agreement, violation_impact
        )
        
        # Consensus on severity
        severity_consensus = self._determine_severity_consensus(violation, supporting_tools, tool_results)
        
        return EnhancedCorrelation(
            correlation_type=violation_type,
            confidence_score=confidence_score,
            supporting_tools=supporting_tools,
            violation_impact=violation_impact,
            recommendation_priority=recommendation_priority,
            cross_tool_agreement=cross_tool_agreement,
            severity_consensus=severity_consensus,
            actionable_steps=list(set(actionable_steps))  # Remove duplicates
        )
    
    async def _calculate_tool_correlation_strength(self, violation: Dict, 
                                                 tool_name: str, 
                                                 tool_result: ToolResult) -> float:
        """Calculate correlation strength between violation and tool findings."""
        
        file_path = violation.get('file_path', '')
        line_number = violation.get('line_number', 0)
        violation_type = violation.get('type', '')
        
        correlation_strength = 0.0
        
        if tool_name == 'ruff':
            correlation_strength = self._correlate_with_ruff(violation, tool_result)
        elif tool_name == 'mypy':
            correlation_strength = self._correlate_with_mypy(violation, tool_result)
        elif tool_name == 'radon':
            correlation_strength = self._correlate_with_radon(violation, tool_result)
        elif tool_name == 'bandit':
            correlation_strength = self._correlate_with_bandit(violation, tool_result)
        elif tool_name == 'black':
            correlation_strength = self._correlate_with_black(violation, tool_result)
        elif tool_name == 'build_flags':
            correlation_strength = self._correlate_with_build_flags(violation, tool_result)
        
        return min(1.0, max(0.0, correlation_strength))  # Clamp to [0, 1]
    
    def _correlate_with_ruff(self, violation: Dict, tool_result: ToolResult) -> float:
        """Correlate connascence violation with Ruff findings."""
        violation_type = violation.get('type', '')
        file_path = violation.get('file_path', '')
        line_number = violation.get('line_number', 0)
        
        # Strong correlations
        strong_correlations = {
            'connascence_of_meaning': 0.9,  # Magic literals -> Ruff F541, E731
            'connascence_of_position': 0.8,  # Parameter issues -> Ruff B006, E999
            'god_object': 0.85,  # Complexity -> Ruff C901, PLR0912
            'nasa_dynamic_memory_violation': 0.7,  # Memory -> Various Ruff rules
        }
        
        base_strength = strong_correlations.get(violation_type, 0.3)
        
        # Check if Ruff found issues in same file
        ruff_issues = tool_result.results.get('issues', [])
        file_match_bonus = 0.0
        line_proximity_bonus = 0.0
        
        for issue in ruff_issues:
            if issue.get('file', '') == file_path:
                file_match_bonus = 0.2
                issue_line = issue.get('line', 0)
                if abs(issue_line - line_number) <= 5:  # Within 5 lines
                    line_proximity_bonus = 0.3
                    break
        
        return base_strength + file_match_bonus + line_proximity_bonus
    
    def _correlate_with_mypy(self, violation: Dict, tool_result: ToolResult) -> float:
        """Correlate connascence violation with MyPy findings."""
        violation_type = violation.get('type', '')
        
        # MyPy correlations
        type_correlations = {
            'connascence_of_type': 0.95,  # Direct type issues
            'connascence_of_name': 0.8,   # Name resolution issues
            'connascence_of_identity': 0.7,  # Object identity issues
        }
        
        return type_correlations.get(violation_type, 0.2)
    
    def _correlate_with_radon(self, violation: Dict, tool_result: ToolResult) -> float:
        """Correlate connascence violation with Radon complexity findings."""
        violation_type = violation.get('type', '')
        
        complexity_correlations = {
            'connascence_of_algorithm': 0.9,  # Algorithm complexity
            'god_object': 0.85,  # Large class complexity
            'nasa_function_size_violation': 0.8,  # Function size vs complexity
        }
        
        return complexity_correlations.get(violation_type, 0.1)
    
    def _correlate_with_bandit(self, violation: Dict, tool_result: ToolResult) -> float:
        """Correlate connascence violation with Bandit security findings."""
        violation_type = violation.get('type', '')
        severity = violation.get('severity', '')
        
        # Security correlations
        security_correlations = {
            'nasa_dynamic_memory_violation': 0.8,  # Memory safety
            'connascence_of_meaning': 0.6,  # Hardcoded secrets/values
        }
        
        base_strength = security_correlations.get(violation_type, 0.1)
        
        # High/critical violations more likely to have security implications
        if severity in ['high', 'critical']:
            base_strength += 0.2
        
        return base_strength
    
    def _correlate_with_black(self, violation: Dict, tool_result: ToolResult) -> float:
        """Correlate connascence violation with Black formatting findings."""
        violation_type = violation.get('type', '')
        
        # Formatting can help with readability of coupled code
        formatting_correlations = {
            'connascence_of_position': 0.6,  # Parameter formatting
            'connascence_of_meaning': 0.4,   # Literal formatting
        }
        
        return formatting_correlations.get(violation_type, 0.1)
    
    def _correlate_with_build_flags(self, violation: Dict, tool_result: ToolResult) -> float:
        """Correlate connascence violation with build flag findings."""
        violation_type = violation.get('type', '')
        severity = violation.get('severity', '')
        
        # Compiler flag correlations
        compiler_correlations = {
            'nasa_scope_violation': 0.7,  # Variable scope warnings
            'nasa_function_size_violation': 0.6,  # Function complexity warnings
        }
        
        base_strength = compiler_correlations.get(violation_type, 0.1)
        
        # NASA violations should be caught by strict compiler flags
        if violation_type.startswith('nasa_'):
            base_strength += 0.3
        
        return base_strength
    
    def _get_tool_specific_actions(self, violation_type: str, tool_name: str, 
                                 tool_result: ToolResult) -> List[str]:
        """Get actionable steps specific to each tool."""
        actions = []
        
        if tool_name == 'ruff':
            actions.extend([
                "Run 'ruff check --fix' to auto-fix style issues",
                "Run 'ruff format' to improve code formatting",
                "Review ruff configuration for project-specific rules"
            ])
        elif tool_name == 'mypy':
            actions.extend([
                "Add type annotations to resolve type issues",
                "Run 'mypy --strict' for comprehensive type checking",
                "Consider using generic types for better type safety"
            ])
        elif tool_name == 'radon':
            actions.extend([
                "Refactor complex functions identified by radon",
                "Extract helper methods to reduce cyclomatic complexity",
                "Consider using strategy pattern for complex conditionals"
            ])
        elif tool_name == 'bandit':
            actions.extend([
                "Address security vulnerabilities identified by bandit",
                "Review hardcoded values for potential secrets",
                "Implement proper input validation and sanitization"
            ])
        
        return actions
    
    def _assess_violation_impact(self, violation: Dict, supporting_tools: List[str]) -> str:
        """Assess the impact of a violation based on tool consensus."""
        severity = violation.get('severity', 'medium')
        tool_count = len(supporting_tools)
        
        if severity == 'critical' or tool_count >= 4:
            return "high_impact"
        elif severity == 'high' or tool_count >= 2:
            return "medium_impact"
        else:
            return "low_impact"
    
    def _determine_recommendation_priority(self, confidence_score: float, 
                                         cross_tool_agreement: float, 
                                         violation_impact: str) -> str:
        """Determine priority for recommendations."""
        
        if violation_impact == "high_impact" and confidence_score > 0.8:
            return "critical"
        elif violation_impact == "medium_impact" and confidence_score > 0.6:
            return "high"
        elif confidence_score > 0.5:
            return "medium"
        else:
            return "low"
    
    def _determine_severity_consensus(self, violation: Dict, supporting_tools: List[str], 
                                    tool_results: Dict[str, ToolResult]) -> str:
        """Determine consensus severity based on multiple tools."""
        original_severity = violation.get('severity', 'medium')
        tool_count = len(supporting_tools)
        
        # Upgrade severity if multiple tools agree
        if tool_count >= 3:
            severity_upgrade = {
                'low': 'medium',
                'medium': 'high',
                'high': 'critical'
            }
            return severity_upgrade.get(original_severity, original_severity)
        elif tool_count >= 2:
            if original_severity == 'low':
                return 'medium'
        
        return original_severity
    
    async def _enhanced_severity_classification(self, connascence_results: Dict,
                                              tool_results: Dict[str, ToolResult],
                                              enhanced_correlations: List[EnhancedCorrelation]) -> Dict[str, Any]:
        """Enhanced severity classification based on multi-tool analysis."""
        
        classification = {
            'methodology': 'multi_tool_consensus',
            'confidence_threshold': self.cross_tool_confidence_threshold,
            'severity_adjustments': [],
            'consensus_metrics': {},
            'upgrade_statistics': {
                'total_violations': 0,
                'severity_upgrades': 0,
                'high_confidence_correlations': 0
            }
        }
        
        violations = connascence_results.get('violations', [])
        total_violations = len(violations)
        severity_upgrades = 0
        high_confidence_correlations = 0
        
        for correlation in enhanced_correlations:
            if correlation.confidence_score >= self.cross_tool_confidence_threshold:
                high_confidence_correlations += 1
                
                if correlation.recommendation_priority in ['critical', 'high']:
                    severity_upgrades += 1
                    
                    classification['severity_adjustments'].append({
                        'violation_type': correlation.correlation_type,
                        'original_severity': 'medium',  # Would need to track this
                        'adjusted_severity': correlation.severity_consensus,
                        'confidence_score': correlation.confidence_score,
                        'supporting_tools': correlation.supporting_tools,
                        'justification': f"Consensus from {len(correlation.supporting_tools)} tools"
                    })
        
        # Consensus metrics
        classification['consensus_metrics'] = {
            'average_confidence': statistics.mean([c.confidence_score for c in enhanced_correlations]) 
                                if enhanced_correlations else 0.0,
            'cross_tool_agreement': statistics.mean([c.cross_tool_agreement for c in enhanced_correlations])
                                  if enhanced_correlations else 0.0,
            'critical_priority_count': len([c for c in enhanced_correlations if c.recommendation_priority == 'critical']),
            'high_priority_count': len([c for c in enhanced_correlations if c.recommendation_priority == 'high'])
        }
        
        # Update statistics
        classification['upgrade_statistics'].update({
            'total_violations': total_violations,
            'severity_upgrades': severity_upgrades,
            'high_confidence_correlations': high_confidence_correlations,
            'upgrade_percentage': (severity_upgrades / total_violations * 100) if total_violations > 0 else 0
        })
        
        return classification
    
    async def _detect_performance_bottlenecks(self, tool_results: Dict[str, ToolResult],
                                            connascence_results: Dict) -> List[PerformanceMetrics]:
        """Detect performance bottlenecks from tool analysis."""
        
        bottlenecks = []
        
        # Radon complexity bottlenecks
        if 'radon' in tool_results and tool_results['radon'].success:
            radon_bottlenecks = self._analyze_radon_bottlenecks(tool_results['radon'])
            bottlenecks.extend(radon_bottlenecks)
        
        # Connascence algorithm bottlenecks
        violations = connascence_results.get('violations', [])
        algorithm_violations = [v for v in violations if v.get('type') == 'connascence_of_algorithm']
        
        for violation in algorithm_violations:
            bottlenecks.append(PerformanceMetrics(
                bottleneck_type='algorithm_duplication',
                affected_files=[violation.get('file_path', '')],
                performance_impact='medium',
                optimization_opportunity='Extract common algorithm to shared function',
                estimated_improvement=0.2,  # 20% improvement estimate
                complexity_reduction=0.3
            ))
        
        # God object bottlenecks
        god_objects = [v for v in violations if v.get('type') == 'god_object']
        for violation in god_objects:
            bottlenecks.append(PerformanceMetrics(
                bottleneck_type='god_object',
                affected_files=[violation.get('file_path', '')],
                performance_impact='high',
                optimization_opportunity='Split class using Single Responsibility Principle',
                estimated_improvement=0.4,  # 40% improvement estimate
                complexity_reduction=0.6
            ))
        
        return bottlenecks
    
    def _analyze_radon_bottlenecks(self, radon_result: ToolResult) -> List[PerformanceMetrics]:
        """Analyze Radon results for performance bottlenecks."""
        bottlenecks = []
        
        # Extract high complexity functions
        complex_functions = radon_result.results.get('complex_functions', [])
        
        for func in complex_functions:
            if func.get('complexity', 0) > 10:  # High complexity threshold
                bottlenecks.append(PerformanceMetrics(
                    bottleneck_type='cyclomatic_complexity',
                    affected_files=[func.get('file', '')],
                    performance_impact='medium',
                    optimization_opportunity=f"Refactor function '{func.get('function', '')}' to reduce complexity",
                    estimated_improvement=0.25,
                    complexity_reduction=0.5
                ))
        
        return bottlenecks
    
    async def _correlate_nasa_rules(self, connascence_results: Dict, 
                                   tool_results: Dict[str, ToolResult]) -> Dict[str, Any]:
        """Correlate NASA Power of Ten rules with tool findings."""
        
        nasa_correlation = {
            'rules_analyzed': 10,
            'violations_found': 0,
            'tool_correlations': {},
            'compliance_score': 0.0,
            'rule_breakdown': {}
        }
        
        violations = connascence_results.get('violations', [])
        nasa_violations = [v for v in violations if 'nasa_' in v.get('type', '')]
        
        nasa_correlation['violations_found'] = len(nasa_violations)
        nasa_correlation['compliance_score'] = max(0.0, 1.0 - (len(nasa_violations) / 50.0))  # Normalize
        
        # Analyze each NASA rule
        for i in range(1, 11):
            rule_violations = [v for v in nasa_violations if f'rule_{i}' in v.get('context', {}).get('nasa_rule', '')]
            
            nasa_correlation['rule_breakdown'][f'rule_{i}'] = {
                'violation_count': len(rule_violations),
                'severity_distribution': self._get_severity_distribution(rule_violations),
                'tool_correlations': self._find_nasa_tool_correlations(rule_violations, tool_results)
            }
        
        return nasa_correlation
    
    def _get_severity_distribution(self, violations: List[Dict]) -> Dict[str, int]:
        """Get severity distribution for violations."""
        distribution = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for violation in violations:
            severity = violation.get('severity', 'medium')
            if severity in distribution:
                distribution[severity] += 1
        
        return distribution
    
    def _find_nasa_tool_correlations(self, nasa_violations: List[Dict], 
                                   tool_results: Dict[str, ToolResult]) -> Dict[str, int]:
        """Find correlations between NASA violations and tool findings."""
        correlations = {}
        
        for tool_name, tool_result in tool_results.items():
            if not tool_result.success:
                continue
                
            correlation_count = 0
            # This would need specific logic for each tool type
            # For now, return placeholder data
            correlations[tool_name] = correlation_count
        
        return correlations
    
    async def _integrate_mece_analysis(self, project_path: Path, 
                                     tool_results: Dict[str, ToolResult],
                                     enhanced_correlations: List[EnhancedCorrelation]) -> Dict[str, Any]:
        """Integrate MECE (Mutually Exclusive, Collectively Exhaustive) analysis."""
        
        mece_results = {
            'duplication_clusters': [],
            'consolidation_opportunities': [],
            'exclusivity_analysis': {},
            'completeness_analysis': {},
            'mece_score': 0.0
        }
        
        # Analyze duplication clusters from tool results
        duplication_violations = [c for c in enhanced_correlations 
                                if 'algorithm' in c.correlation_type or 'duplication' in c.correlation_type]
        
        mece_results['duplication_clusters'] = len(duplication_violations)
        
        # Calculate MECE score
        total_functions = self._estimate_total_functions(tool_results)
        duplicate_functions = len(duplication_violations)
        
        mece_results['mece_score'] = max(0.0, 1.0 - (duplicate_functions / max(total_functions, 1)))
        
        return mece_results
    
    def _estimate_total_functions(self, tool_results: Dict[str, ToolResult]) -> int:
        """Estimate total number of functions from tool results."""
        # This is a simplified estimation
        if 'radon' in tool_results and tool_results['radon'].success:
            return len(tool_results['radon'].results.get('functions', [])) or 50
        return 50  # Default estimate
    
    async def _generate_ai_recommendations(self, connascence_results: Dict,
                                         tool_results: Dict[str, ToolResult],
                                         enhanced_correlations: List[EnhancedCorrelation],
                                         performance_metrics: List[PerformanceMetrics]) -> List[Dict[str, Any]]:
        """Generate AI-powered recommendations."""
        
        recommendations = []
        
        # High-priority recommendations from correlations
        critical_correlations = [c for c in enhanced_correlations 
                               if c.recommendation_priority == 'critical']
        
        for correlation in critical_correlations:
            recommendations.append({
                'type': 'critical_action',
                'title': f'Address {correlation.correlation_type}',
                'description': f'High confidence ({correlation.confidence_score:.2%}) issue supported by {len(correlation.supporting_tools)} tools',
                'actionable_steps': correlation.actionable_steps,
                'estimated_effort': 'high',
                'business_impact': correlation.violation_impact,
                'tools_supporting': correlation.supporting_tools
            })
        
        # Performance improvement recommendations
        for metric in performance_metrics:
            if metric.performance_impact == 'high':
                recommendations.append({
                    'type': 'performance_optimization',
                    'title': f'Optimize {metric.bottleneck_type}',
                    'description': metric.optimization_opportunity,
                    'estimated_improvement': f'{metric.estimated_improvement:.1%}',
                    'complexity_reduction': f'{metric.complexity_reduction:.1%}',
                    'affected_files': metric.affected_files,
                    'estimated_effort': 'medium'
                })
        
        # Tool integration recommendations
        successful_tools = [name for name, result in tool_results.items() if result.success]
        failed_tools = [name for name, result in tool_results.items() if not result.success]
        
        if failed_tools:
            recommendations.append({
                'type': 'tool_integration',
                'title': 'Fix tool integration issues',
                'description': f'Tools not running: {", ".join(failed_tools)}',
                'actionable_steps': [
                    f'Install and configure {tool}' for tool in failed_tools
                ],
                'estimated_effort': 'low',
                'business_impact': 'medium_impact'
            })
        
        # Sort by priority
        priority_order = {'critical_action': 0, 'performance_optimization': 1, 'tool_integration': 2}
        recommendations.sort(key=lambda r: priority_order.get(r['type'], 3))
        
        return recommendations
    
    def _calculate_cross_tool_consensus(self, tool_results: Dict[str, ToolResult],
                                      enhanced_correlations: List[EnhancedCorrelation]) -> Dict[str, float]:
        """Calculate consensus metrics across tools."""
        
        consensus = {}
        
        if enhanced_correlations:
            consensus['average_confidence'] = statistics.mean([c.confidence_score for c in enhanced_correlations])
            consensus['average_agreement'] = statistics.mean([c.cross_tool_agreement for c in enhanced_correlations])
            
            # Tool participation rates
            all_tools = set(tool_results.keys())
            tool_participation = {}
            
            for tool in all_tools:
                participated_in = len([c for c in enhanced_correlations if tool in c.supporting_tools])
                tool_participation[tool] = participated_in / len(enhanced_correlations) if enhanced_correlations else 0.0
            
            consensus['tool_participation_rates'] = tool_participation
        
        return consensus
    
    def _analyze_quality_trends(self, base_analysis: IntegratedAnalysis, 
                              enhanced_correlations: List[EnhancedCorrelation]) -> Dict[str, Any]:
        """Analyze quality trends (placeholder for historical analysis)."""
        
        # This would need historical data to be meaningful
        # For now, return current snapshot analysis
        
        return {
            'current_snapshot': {
                'total_violations': len(base_analysis.connascence_results.get('violations', [])),
                'tool_success_rate': len([r for r in base_analysis.tool_results.values() if r.success]) / 
                                   len(base_analysis.tool_results) if base_analysis.tool_results else 0.0,
                'high_confidence_issues': len([c for c in enhanced_correlations 
                                             if c.confidence_score > 0.8]),
                'overall_score': base_analysis.overall_score
            },
            'trend_analysis': {
                'note': 'Historical trend analysis requires multiple analysis runs',
                'recommendation': 'Run analysis regularly to build trend data'
            }
        }
    
    def generate_enhanced_report(self, analysis: EnhancedAnalysisResult, 
                               format_type: str = "text") -> str:
        """Generate enhanced report with Phase 2 capabilities."""
        
        if format_type == "json":
            return json.dumps(asdict(analysis), indent=2, default=str)
        
        # Generate comprehensive text report
        lines = [
            "=" * 100,
            "ENHANCED CONNASCENCE ANALYSIS REPORT - PHASE 2",
            "=" * 100,
            "",
            "EXECUTIVE SUMMARY",
            "-" * 50,
            f"Analysis completed in {analysis.execution_summary.get('total_execution_time', 0):.2f}s",
            f"Enhancement processing: {analysis.execution_summary.get('enhancement_time', 0):.2f}s",
            f"Tools executed: {analysis.execution_summary.get('tools_executed', 0)}",
            f"Tools failed: {analysis.execution_summary.get('tools_failed', 0)}",
            f"Overall score: {analysis.overall_score:.2%}",
            "",
            "ENHANCED CORRELATIONS",
            "-" * 50,
            f"High-confidence correlations: {len([c for c in analysis.enhanced_correlations if c.confidence_score > 0.8])}",
            f"Critical priority issues: {len([c for c in analysis.enhanced_correlations if c.recommendation_priority == 'critical'])}",
            f"Average confidence score: {statistics.mean([c.confidence_score for c in analysis.enhanced_correlations]) if analysis.enhanced_correlations else 0:.2%}",
            "",
        ]
        
        # Top correlations
        if analysis.enhanced_correlations:
            lines.extend([
                "TOP PRIORITY CORRELATIONS",
                "-" * 50
            ])
            
            for i, correlation in enumerate(analysis.enhanced_correlations[:5], 1):
                lines.extend([
                    f"{i}. [{correlation.recommendation_priority.upper()}] {correlation.correlation_type}",
                    f"   Confidence: {correlation.confidence_score:.2%} | Tools: {len(correlation.supporting_tools)}",
                    f"   Supporting: {', '.join(correlation.supporting_tools)}",
                    f"   Impact: {correlation.violation_impact} | Agreement: {correlation.cross_tool_agreement:.2%}",
                    ""
                ])
        
        # Performance metrics
        if analysis.performance_metrics:
            lines.extend([
                "PERFORMANCE BOTTLENECKS",
                "-" * 50
            ])
            
            for metric in analysis.performance_metrics:
                lines.extend([
                    f"• {metric.bottleneck_type} ({metric.performance_impact} impact)",
                    f"  Opportunity: {metric.optimization_opportunity}",
                    f"  Estimated improvement: {metric.estimated_improvement:.1%}",
                    f"  Complexity reduction: {metric.complexity_reduction:.1%}",
                    ""
                ])
        
        # AI Recommendations
        if analysis.ai_recommendations:
            lines.extend([
                "AI-POWERED RECOMMENDATIONS",
                "-" * 50
            ])
            
            for i, rec in enumerate(analysis.ai_recommendations[:3], 1):
                lines.extend([
                    f"{i}. {rec['title']} ({rec.get('estimated_effort', 'unknown')} effort)",
                    f"   {rec['description']}",
                    ""
                ])
        
        # NASA Compliance (if available)
        if analysis.nasa_compliance_detail:
            nasa_score = analysis.nasa_compliance_detail.get('compliance_score', 0)
            lines.extend([
                "NASA POWER OF TEN COMPLIANCE",
                "-" * 50,
                f"Compliance score: {nasa_score:.2%}",
                f"Rules violated: {analysis.nasa_compliance_detail.get('violations_found', 0)}",
                ""
            ])
        
        # Cross-tool consensus
        if analysis.cross_tool_consensus:
            lines.extend([
                "CROSS-TOOL CONSENSUS",
                "-" * 50,
                f"Average confidence: {analysis.cross_tool_consensus.get('average_confidence', 0):.2%}",
                f"Average agreement: {analysis.cross_tool_consensus.get('average_agreement', 0):.2%}",
                ""
            ])
        
        lines.extend([
            "=" * 100,
            "END ENHANCED ANALYSIS REPORT",
            "=" * 100
        ])
        
        return "\n".join(lines)