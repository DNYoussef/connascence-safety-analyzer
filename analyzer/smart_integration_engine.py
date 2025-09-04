#!/usr/bin/env python3
"""
Smart Integration Engine
========================

This module creates a smart integration layer that combines:
1. Core connascence analyzer
2. MECE duplication detection  
3. NASA Power of Ten rules
4. Multi-linter correlation

It intelligently detects failures and provides comprehensive assessment
by using the full power of our analysis suite.

Key Features:
- Smart violation correlation across all analyzers
- Failure prediction and early detection
- Comprehensive quality scoring
- Actionable improvement recommendations

Author: Connascence Safety Analyzer Team
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import json
import hashlib
import difflib

# Core analyzer integration
try:
    from .core import ConnascenceViolation, ViolationType, Severity
    from .ast_engine.core_analyzer import ConnascenceASTAnalyzer
    from .dup_detection import MECEAnalyzer, DuplicationCluster, FunctionSignature
except ImportError:
    print("Warning: Core analyzer components not found")

# NASA integration  
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from mcp.nasa_power_of_ten_integration import NASAPowerOfTenIntegration
except ImportError:
    print("Warning: NASA Power of Ten integration not found")

# Tool coordination
try:
    from integrations.tool_coordinator import ToolCoordinator
except ImportError:
    print("Warning: Tool coordinator not found")


@dataclass
class SmartViolationCluster:
    """Enhanced violation cluster with smart correlation."""
    cluster_id: str
    violation_types: List[str]
    severity_level: str
    confidence_score: float
    nasa_rules_violated: List[str]
    connascence_types: List[str]
    duplication_involved: bool
    failure_risk: str  # 'low', 'medium', 'high', 'critical'
    smart_recommendations: List[str]
    affected_files: Set[str] = field(default_factory=set)
    correlation_strength: float = 0.0


@dataclass
class ComprehensiveAssessment:
    """Complete assessment results from smart integration."""
    quality_score: float
    failure_predictions: List[Dict[str, Any]]
    violation_clusters: List[SmartViolationCluster]
    nasa_compliance_score: float
    duplication_risk_score: float
    overall_risk_level: str
    priority_recommendations: List[Dict[str, Any]]
    detailed_metrics: Dict[str, Any]


class SmartIntegrationEngine:
    """
    Smart integration engine that combines all analysis components
    for comprehensive failure detection and quality assessment.
    """
    
    def __init__(self):
        # Initialize all analysis components
        self.connascence_analyzer = self._init_connascence_analyzer()
        self.mece_analyzer = self._init_mece_analyzer()
        self.nasa_integration = self._init_nasa_integration()
        self.tool_coordinator = self._init_tool_coordinator()
        
        # Smart correlation patterns
        self.violation_patterns = self._load_violation_patterns()
        self.failure_indicators = self._load_failure_indicators()
        
    def _init_connascence_analyzer(self):
        """Initialize connascence analyzer with error handling."""
        try:
            return ConnascenceASTAnalyzer()
        except Exception as e:
            print(f"Warning: Could not initialize connascence analyzer: {e}")
            return None
    
    def _init_mece_analyzer(self):
        """Initialize MECE analyzer with error handling."""
        try:
            return MECEAnalyzer()
        except Exception as e:
            print(f"Warning: Could not initialize MECE analyzer: {e}")
            return None
    
    def _init_nasa_integration(self):
        """Initialize NASA integration with error handling."""
        try:
            return NASAPowerOfTenIntegration()
        except Exception as e:
            print(f"Warning: Could not initialize NASA integration: {e}")
            return None
    
    def _init_tool_coordinator(self):
        """Initialize tool coordinator with error handling."""
        try:
            return ToolCoordinator()
        except Exception as e:
            print(f"Warning: Could not initialize tool coordinator: {e}")
            return None
    
    def _load_violation_patterns(self) -> Dict[str, Any]:
        """Load patterns that indicate potential failures."""
        return {
            'high_risk_combinations': [
                {'types': ['algorithm', 'meaning'], 'risk': 'high'},
                {'types': ['position', 'algorithm'], 'risk': 'high'},
                {'types': ['timing', 'execution'], 'risk': 'critical'}
            ],
            'nasa_rule_correlations': {
                'nasa_rule_1': ['algorithm', 'execution'],
                'nasa_rule_4': ['algorithm'],
                'nasa_rule_5': ['meaning'],
                'nasa_rule_7': ['meaning']
            },
            'duplication_indicators': [
                'similar function names',
                'identical parameter patterns',
                'repeated code blocks'
            ]
        }
    
    def _load_failure_indicators(self) -> Dict[str, Any]:
        """Load indicators that predict system failures."""
        return {
            'critical_thresholds': {
                'connascence_density': 0.5,  # violations per file
                'nasa_compliance': 0.8,      # minimum compliance score
                'duplication_percentage': 15, # max acceptable duplication
                'complexity_score': 10        # max cyclomatic complexity
            },
            'failure_patterns': [
                {'pattern': 'god_object + magic_literals', 'risk': 'critical'},
                {'pattern': 'recursion + unbounded_loops', 'risk': 'critical'},
                {'pattern': 'multiple_duplications + poor_naming', 'risk': 'high'},
                {'pattern': 'missing_assertions + unchecked_returns', 'risk': 'high'}
            ]
        }
    
    async def comprehensive_assessment(self, path: str, include_predictions: bool = True) -> ComprehensiveAssessment:
        """
        Perform comprehensive assessment using all analysis components
        with smart failure detection and correlation.
        """
        print("🧠 Starting Smart Integration Analysis...")
        
        # Phase 1: Collect raw data from all analyzers
        print("📊 Phase 1: Collecting data from all analyzers...")
        raw_data = await self._collect_all_analysis_data(path)
        
        # Phase 2: Smart correlation and clustering
        print("🔗 Phase 2: Smart correlation analysis...")
        violation_clusters = self._perform_smart_correlation(raw_data)
        
        # Phase 3: Failure prediction
        print("🔮 Phase 3: Failure prediction analysis...")
        failure_predictions = []
        if include_predictions:
            failure_predictions = self._predict_failures(violation_clusters, raw_data)
        
        # Phase 4: Risk assessment
        print("⚠️ Phase 4: Risk assessment...")
        risk_assessment = self._assess_overall_risk(violation_clusters, failure_predictions)
        
        # Phase 5: Generate smart recommendations
        print("💡 Phase 5: Generating smart recommendations...")
        recommendations = self._generate_smart_recommendations(violation_clusters, risk_assessment)
        
        # Compile final assessment
        assessment = ComprehensiveAssessment(
            quality_score=risk_assessment['quality_score'],
            failure_predictions=failure_predictions,
            violation_clusters=violation_clusters,
            nasa_compliance_score=raw_data['nasa_data']['overall_compliance'],
            duplication_risk_score=raw_data['mece_data']['risk_score'],
            overall_risk_level=risk_assessment['risk_level'],
            priority_recommendations=recommendations,
            detailed_metrics=self._calculate_detailed_metrics(raw_data, violation_clusters)
        )
        
        print("✅ Smart integration analysis complete!")
        return assessment
    
    async def _collect_all_analysis_data(self, path: str) -> Dict[str, Any]:
        """Collect data from all available analyzers."""
        data = {
            'connascence_data': {'violations': [], 'files_analyzed': 0},
            'mece_data': {'clusters': [], 'risk_score': 0.0},
            'nasa_data': {'violations': [], 'overall_compliance': 1.0},
            'tool_data': {'correlations': {}, 'coverage': {}},
            'path': path
        }
        
        # Connascence analysis
        if self.connascence_analyzer:
            print("  🔍 Running connascence analysis...")
            data['connascence_data'] = await self._run_connascence_analysis(path)
        
        # MECE duplication analysis
        if self.mece_analyzer:
            print("  🔍 Running MECE duplication analysis...")
            data['mece_data'] = await self._run_mece_analysis(path)
        
        # NASA compliance check
        if self.nasa_integration:
            print("  🛡️ Running NASA compliance check...")
            data['nasa_data'] = await self._run_nasa_analysis(data['connascence_data']['violations'])
        
        # Multi-tool integration
        if self.tool_coordinator:
            print("  🔧 Running multi-tool analysis...")
            data['tool_data'] = await self._run_tool_integration(path)
        
        return data
    
    async def _run_connascence_analysis(self, path: str) -> Dict[str, Any]:
        """Run smart connascence analysis."""
        violations = []
        files_analyzed = 0
        
        path_obj = Path(path)
        
        if path_obj.is_file() and path_obj.suffix == '.py':
            try:
                file_violations = self.connascence_analyzer.analyze_file(path_obj)
                violations.extend(file_violations)
                files_analyzed = 1
            except Exception as e:
                print(f"    ⚠️ Error analyzing {path_obj}: {e}")
        
        elif path_obj.is_dir():
            for py_file in path_obj.rglob("*.py"):
                if self._should_analyze_file(py_file):
                    try:
                        file_violations = self.connascence_analyzer.analyze_file(py_file)
                        violations.extend(file_violations)
                        files_analyzed += 1
                    except Exception as e:
                        print(f"    ⚠️ Error analyzing {py_file}: {e}")
        
        return {
            'violations': violations,
            'files_analyzed': files_analyzed,
            'violation_density': len(violations) / max(files_analyzed, 1)
        }
    
    async def _run_mece_analysis(self, path: str) -> Dict[str, Any]:
        """Run smart MECE analysis."""
        try:
            results = self.mece_analyzer.analyze_codebase(path, ['*.py'])
            
            clusters = results.get('duplication_clusters', [])
            high_risk_clusters = [c for c in clusters if c.confidence > 0.8]
            
            # Calculate risk score based on duplication severity
            risk_score = min(1.0, len(high_risk_clusters) * 0.1)
            
            return {
                'clusters': clusters,
                'high_risk_clusters': high_risk_clusters,
                'risk_score': risk_score,
                'consolidation_opportunities': results.get('consolidation_opportunities', [])
            }
            
        except Exception as e:
            print(f"    ⚠️ MECE analysis error: {e}")
            return {'clusters': [], 'risk_score': 0.0}
    
    async def _run_nasa_analysis(self, connascence_violations: List) -> Dict[str, Any]:
        """Run smart NASA compliance analysis."""
        try:
            all_nasa_violations = []
            compliance_scores = []
            
            for violation in connascence_violations[:50]:  # Limit for performance
                violation_dict = self._serialize_violation(violation)
                nasa_violations = self.nasa_integration.check_nasa_violations(violation_dict)
                all_nasa_violations.extend(nasa_violations)
                
                compliance_score = self.nasa_integration.calculate_nasa_compliance_score(nasa_violations)
                compliance_scores.append(compliance_score)
            
            overall_compliance = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 1.0
            
            return {
                'violations': all_nasa_violations,
                'overall_compliance': overall_compliance,
                'rule_violations': self._count_rule_violations(all_nasa_violations)
            }
            
        except Exception as e:
            print(f"    ⚠️ NASA analysis error: {e}")
            return {'violations': [], 'overall_compliance': 1.0}
    
    async def _run_tool_integration(self, path: str) -> Dict[str, Any]:
        """Run smart multi-tool integration analysis."""
        try:
            path_obj = Path(path)
            if path_obj.is_dir():
                enabled_tools = {'ruff', 'mypy', 'radon', 'bandit', 'black'}
                
                integration_results = await self.tool_coordinator.analyze_project(
                    path_obj,
                    enabled_tools=enabled_tools,
                    include_connascence=True
                )
                
                return {
                    'correlations': integration_results.correlations,
                    'tool_results': integration_results.tool_results,
                    'coverage': {tool: len(results) for tool, results in integration_results.tool_results.items()}
                }
            
        except Exception as e:
            print(f"    ⚠️ Tool integration error: {e}")
        
        return {'correlations': {}, 'coverage': {}}
    
    def _perform_smart_correlation(self, raw_data: Dict[str, Any]) -> List[SmartViolationCluster]:
        """Perform smart correlation analysis across all data sources."""
        clusters = []
        
        # Group violations by file and type
        violation_groups = self._group_violations_intelligently(raw_data)
        
        for group_id, group_data in violation_groups.items():
            cluster = self._create_smart_cluster(group_id, group_data, raw_data)
            if cluster:
                clusters.append(cluster)
        
        # Sort by risk level and confidence
        clusters.sort(key=lambda c: (c.failure_risk == 'critical', c.confidence_score), reverse=True)
        
        return clusters
    
    def _group_violations_intelligently(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Intelligently group violations by correlation patterns."""
        groups = {}
        
        connascence_violations = raw_data['connascence_data']['violations']
        mece_clusters = raw_data['mece_data']['clusters']
        nasa_violations = raw_data['nasa_data']['violations']
        
        # Group by file first
        file_groups = defaultdict(lambda: {
            'connascence': [], 
            'mece': [], 
            'nasa': [],
            'files': set()
        })
        
        # Add connascence violations
        for violation in connascence_violations:
            file_path = self._get_violation_file(violation)
            if file_path:
                file_groups[file_path]['connascence'].append(violation)
                file_groups[file_path]['files'].add(file_path)
        
        # Add MECE clusters
        for cluster in mece_clusters:
            for file_path in cluster.files_involved:
                file_groups[file_path]['mece'].append(cluster)
                file_groups[file_path]['files'].update(cluster.files_involved)
        
        # Add NASA violations
        for nasa_violation in nasa_violations:
            conn_violation_id = nasa_violation.get('connascence_violation_id')
            if conn_violation_id:
                # Find corresponding connascence violation
                for file_path, group in file_groups.items():
                    for conn_v in group['connascence']:
                        if self._get_violation_id(conn_v) == conn_violation_id:
                            file_groups[file_path]['nasa'].append(nasa_violation)
        
        return dict(file_groups)
    
    def _create_smart_cluster(self, group_id: str, group_data: Dict[str, Any], 
                            raw_data: Dict[str, Any]) -> Optional[SmartViolationCluster]:
        """Create a smart violation cluster from grouped data."""
        
        connascence_violations = group_data.get('connascence', [])
        mece_clusters = group_data.get('mece', [])
        nasa_violations = group_data.get('nasa', [])
        
        if not (connascence_violations or mece_clusters or nasa_violations):
            return None
        
        # Analyze violation types
        violation_types = []
        for violation in connascence_violations:
            v_type = self._get_violation_type(violation)
            if v_type:
                violation_types.append(v_type)
        
        # Analyze NASA rule violations
        nasa_rules_violated = []
        for nasa_violation in nasa_violations:
            rule_id = nasa_violation.get('rule_id')
            if rule_id:
                nasa_rules_violated.append(rule_id)
        
        # Calculate severity and confidence
        severity_level = self._calculate_cluster_severity(connascence_violations, nasa_violations)
        confidence_score = self._calculate_cluster_confidence(group_data)
        failure_risk = self._assess_failure_risk(violation_types, nasa_rules_violated, mece_clusters)
        
        # Generate smart recommendations
        recommendations = self._generate_cluster_recommendations(
            violation_types, nasa_rules_violated, mece_clusters
        )
        
        return SmartViolationCluster(
            cluster_id=f"smart_cluster_{group_id}",
            violation_types=violation_types,
            severity_level=severity_level,
            confidence_score=confidence_score,
            nasa_rules_violated=nasa_rules_violated,
            connascence_types=violation_types,  # Same for now
            duplication_involved=len(mece_clusters) > 0,
            failure_risk=failure_risk,
            smart_recommendations=recommendations,
            affected_files=group_data.get('files', set()),
            correlation_strength=self._calculate_correlation_strength(group_data)
        )
    
    def _predict_failures(self, clusters: List[SmartViolationCluster], 
                         raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Predict potential failures based on violation patterns."""
        predictions = []
        
        # Critical failure patterns
        critical_clusters = [c for c in clusters if c.failure_risk == 'critical']
        if critical_clusters:
            predictions.append({
                'type': 'critical_failure_risk',
                'probability': 0.8,
                'description': f'{len(critical_clusters)} critical violation clusters found',
                'impact': 'System may fail under stress or edge cases',
                'timeframe': 'immediate',
                'recommended_action': 'Address critical clusters immediately'
            })
        
        # NASA compliance failure
        nasa_compliance = raw_data['nasa_data']['overall_compliance']
        if nasa_compliance < 0.7:
            predictions.append({
                'type': 'nasa_compliance_failure',
                'probability': 1.0 - nasa_compliance,
                'description': f'NASA compliance at {nasa_compliance:.2%}',
                'impact': 'Safety requirements not met, potential certification failure',
                'timeframe': 'short-term',
                'recommended_action': 'Implement NASA Power of Ten rules systematically'
            })
        
        # Duplication maintenance burden
        duplication_risk = raw_data['mece_data']['risk_score']
        if duplication_risk > 0.3:
            predictions.append({
                'type': 'maintenance_burden_increase',
                'probability': duplication_risk,
                'description': f'High code duplication detected ({duplication_risk:.2%} risk)',
                'impact': 'Maintenance costs will increase, bug fixing becomes difficult',
                'timeframe': 'medium-term',
                'recommended_action': 'Prioritize code consolidation efforts'
            })
        
        return predictions
    
    def _assess_overall_risk(self, clusters: List[SmartViolationCluster], 
                           predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess overall risk level and calculate quality score."""
        
        # Count risk levels
        risk_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for cluster in clusters:
            risk_counts[cluster.failure_risk] += 1
        
        # Determine overall risk level
        if risk_counts['critical'] > 0:
            overall_risk = 'critical'
        elif risk_counts['high'] > 2:
            overall_risk = 'high'
        elif risk_counts['high'] > 0 or risk_counts['medium'] > 5:
            overall_risk = 'medium'
        else:
            overall_risk = 'low'
        
        # Calculate quality score (0.0 to 1.0)
        penalty = (
            risk_counts['critical'] * 0.3 +
            risk_counts['high'] * 0.1 +
            risk_counts['medium'] * 0.05 +
            risk_counts['low'] * 0.01
        )
        
        quality_score = max(0.0, 1.0 - penalty)
        
        return {
            'risk_level': overall_risk,
            'risk_counts': risk_counts,
            'quality_score': quality_score,
            'total_clusters': len(clusters),
            'prediction_count': len(predictions)
        }
    
    def _generate_smart_recommendations(self, clusters: List[SmartViolationCluster], 
                                      risk_assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate prioritized smart recommendations."""
        recommendations = []
        
        # Critical issues first
        critical_clusters = [c for c in clusters if c.failure_risk == 'critical']
        if critical_clusters:
            recommendations.append({
                'priority': 'CRITICAL',
                'category': 'System Stability',
                'issue': f'{len(critical_clusters)} critical violation clusters',
                'action': 'Address immediately to prevent system failures',
                'estimated_effort': 'High',
                'impact': 'Critical - System stability',
                'affected_files': len(set().union(*[c.affected_files for c in critical_clusters]))
            })
        
        # High-risk issues
        high_risk_clusters = [c for c in clusters if c.failure_risk == 'high']
        if high_risk_clusters:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Code Quality',
                'issue': f'{len(high_risk_clusters)} high-risk violation clusters',
                'action': 'Refactor to reduce complexity and coupling',
                'estimated_effort': 'Medium',
                'impact': 'High - Maintainability improvement',
                'affected_files': len(set().union(*[c.affected_files for c in high_risk_clusters]))
            })
        
        # NASA compliance
        nasa_clusters = [c for c in clusters if c.nasa_rules_violated]
        if nasa_clusters:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Safety Compliance',
                'issue': f'NASA Power of Ten violations in {len(nasa_clusters)} clusters',
                'action': 'Implement safety standards systematically',
                'estimated_effort': 'High',
                'impact': 'Critical - Safety compliance',
                'affected_files': len(set().union(*[c.affected_files for c in nasa_clusters]))
            })
        
        return recommendations
    
    # Helper methods for smart analysis
    def _should_analyze_file(self, file_path: Path) -> bool:
        """Check if file should be analyzed."""
        if file_path.name.startswith('.'):
            return False
        if '__pycache__' in str(file_path):
            return False
        if 'test' in str(file_path).lower():
            return False
        return True
    
    def _serialize_violation(self, violation) -> Dict[str, Any]:
        """Serialize violation for processing."""
        if hasattr(violation, '__dict__'):
            return {
                'id': getattr(violation, 'id', f"v_{hash(str(violation))}"),
                'type': self._get_violation_type(violation),
                'severity': self._get_violation_severity(violation),
                'message': getattr(violation, 'message', ''),
                'file': self._get_violation_file(violation),
                'line': getattr(violation, 'line_number', 0)
            }
        return violation if isinstance(violation, dict) else {'id': str(violation), 'type': 'unknown'}
    
    def _get_violation_type(self, violation) -> str:
        """Get violation type consistently."""
        if hasattr(violation, 'type'):
            return violation.type.value if hasattr(violation.type, 'value') else str(violation.type)
        return violation.get('type', 'unknown') if isinstance(violation, dict) else 'unknown'
    
    def _get_violation_severity(self, violation) -> str:
        """Get violation severity consistently."""
        if hasattr(violation, 'severity'):
            return violation.severity.value if hasattr(violation.severity, 'value') else str(violation.severity)
        return violation.get('severity', 'medium') if isinstance(violation, dict) else 'medium'
    
    def _get_violation_file(self, violation) -> Optional[str]:
        """Get violation file path consistently."""
        if hasattr(violation, 'file_path'):
            return str(violation.file_path)
        if isinstance(violation, dict):
            return violation.get('file') or violation.get('file_path')
        return None
    
    def _get_violation_id(self, violation) -> str:
        """Get violation ID consistently."""
        if hasattr(violation, 'id'):
            return str(violation.id)
        if isinstance(violation, dict):
            return violation.get('id', f"v_{hash(str(violation))}")
        return f"v_{hash(str(violation))}"
    
    def _count_rule_violations(self, nasa_violations: List[Dict]) -> Dict[str, int]:
        """Count violations by NASA rule."""
        counts = {}
        for violation in nasa_violations:
            rule_id = violation.get('rule_id', 'unknown')
            counts[rule_id] = counts.get(rule_id, 0) + 1
        return counts
    
    def _calculate_cluster_severity(self, conn_violations: List, nasa_violations: List) -> str:
        """Calculate cluster severity level."""
        critical_count = sum(1 for v in conn_violations if self._get_violation_severity(v) == 'critical')
        nasa_critical = sum(1 for v in nasa_violations if v.get('severity') == 'critical')
        
        if critical_count > 0 or nasa_critical > 0:
            return 'critical'
        elif len(conn_violations) > 3 or len(nasa_violations) > 1:
            return 'high'
        elif len(conn_violations) > 1 or len(nasa_violations) > 0:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_cluster_confidence(self, group_data: Dict[str, Any]) -> float:
        """Calculate confidence score for cluster."""
        confidence = 0.5  # Base confidence
        
        # More violations = higher confidence
        total_violations = len(group_data.get('connascence', [])) + len(group_data.get('nasa', []))
        confidence += min(0.3, total_violations * 0.05)
        
        # MECE involvement increases confidence
        if group_data.get('mece'):
            confidence += 0.2
        
        return min(1.0, confidence)
    
    def _assess_failure_risk(self, violation_types: List[str], nasa_rules: List[str], 
                           mece_clusters: List) -> str:
        """Assess failure risk based on violation patterns."""
        
        # Check critical patterns from failure indicators
        for pattern in self.failure_indicators['failure_patterns']:
            pattern_str = pattern['pattern']
            if self._matches_failure_pattern(pattern_str, violation_types, nasa_rules, mece_clusters):
                return pattern['risk']
        
        # Check NASA rule criticality
        critical_nasa_rules = ['nasa_rule_1', 'nasa_rule_2', 'nasa_rule_3']
        if any(rule in critical_nasa_rules for rule in nasa_rules):
            return 'high'
        
        # Check violation type combinations
        high_risk_types = ['algorithm', 'timing', 'execution']
        if len([t for t in violation_types if t in high_risk_types]) > 1:
            return 'high'
        
        # Default risk assessment
        if violation_types or nasa_rules or mece_clusters:
            return 'medium'
        else:
            return 'low'
    
    def _matches_failure_pattern(self, pattern: str, violation_types: List[str], 
                               nasa_rules: List[str], mece_clusters: List) -> bool:
        """Check if violations match a failure pattern."""
        pattern_lower = pattern.lower()
        
        # Check for god object + magic literals
        if 'god_object' in pattern_lower and 'magic_literals' in pattern_lower:
            has_god_object = 'algorithm' in violation_types
            has_magic_literals = 'meaning' in violation_types
            return has_god_object and has_magic_literals
        
        # Check for recursion + unbounded loops  
        if 'recursion' in pattern_lower and 'unbounded_loops' in pattern_lower:
            return 'nasa_rule_1' in nasa_rules and 'nasa_rule_2' in nasa_rules
        
        # Check for duplications + poor naming
        if 'duplications' in pattern_lower and 'naming' in pattern_lower:
            return len(mece_clusters) > 0 and 'name' in violation_types
        
        # Check for missing assertions + unchecked returns
        if 'assertions' in pattern_lower and 'returns' in pattern_lower:
            return 'nasa_rule_5' in nasa_rules and 'nasa_rule_7' in nasa_rules
        
        return False
    
    def _calculate_correlation_strength(self, group_data: Dict[str, Any]) -> float:
        """Calculate correlation strength between different violation types."""
        strength = 0.0
        
        # Multiple violation types in same file = higher correlation
        if len(group_data.get('connascence', [])) > 1:
            strength += 0.3
        
        # NASA violations with connascence = strong correlation
        if group_data.get('nasa') and group_data.get('connascence'):
            strength += 0.4
        
        # MECE clusters with other violations = moderate correlation
        if group_data.get('mece') and (group_data.get('connascence') or group_data.get('nasa')):
            strength += 0.3
        
        return min(1.0, strength)
    
    def _generate_cluster_recommendations(self, violation_types: List[str], 
                                        nasa_rules: List[str], mece_clusters: List) -> List[str]:
        """Generate specific recommendations for a cluster."""
        recommendations = []
        
        # Connascence-specific recommendations
        if 'algorithm' in violation_types:
            recommendations.append("Break down large functions using Extract Method pattern")
        if 'meaning' in violation_types:
            recommendations.append("Extract magic literals to named constants")
        if 'position' in violation_types:
            recommendations.append("Use named parameters or parameter objects")
        
        # NASA-specific recommendations
        if 'nasa_rule_1' in nasa_rules:
            recommendations.append("Replace recursive functions with iterative solutions")
        if 'nasa_rule_4' in nasa_rules:
            recommendations.append("Split functions to stay within 60-line limit")
        if 'nasa_rule_5' in nasa_rules:
            recommendations.append("Add precondition and postcondition assertions")
        
        # MECE-specific recommendations
        if mece_clusters:
            recommendations.append("Consolidate duplicate code into shared utilities")
        
        return recommendations
    
    def _calculate_detailed_metrics(self, raw_data: Dict[str, Any], 
                                  clusters: List[SmartViolationCluster]) -> Dict[str, Any]:
        """Calculate detailed quality metrics."""
        return {
            'total_files_analyzed': raw_data['connascence_data']['files_analyzed'],
            'violation_density': raw_data['connascence_data']['violation_density'],
            'nasa_compliance_score': raw_data['nasa_data']['overall_compliance'],
            'duplication_risk_score': raw_data['mece_data']['risk_score'],
            'smart_clusters_found': len(clusters),
            'high_risk_clusters': len([c for c in clusters if c.failure_risk in ['high', 'critical']]),
            'average_cluster_confidence': sum(c.confidence_score for c in clusters) / len(clusters) if clusters else 0,
            'correlation_effectiveness': sum(c.correlation_strength for c in clusters) / len(clusters) if clusters else 0
        }


# Example usage and testing
def demonstrate_smart_integration():
    """Demonstrate the smart integration engine capabilities."""
    print("🚀 Smart Integration Engine Demo")
    print("=" * 50)
    
    engine = SmartIntegrationEngine()
    
    # This would be called with actual path
    # assessment = await engine.comprehensive_assessment("./analyzer")
    # print(f"Quality Score: {assessment.quality_score:.2%}")
    
    print("✅ Smart Integration Engine initialized successfully")


if __name__ == "__main__":
    demonstrate_smart_integration()