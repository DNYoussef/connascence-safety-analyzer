"""
Unified Connascence Analyzer
============================

Central orchestrator that combines all Phase 1-6 analysis capabilities:
- Core AST-based connascence detection
- MECE duplication analysis
- NASA Power of Ten compliance
- Smart integration engine
- Multi-linter correlation
- Failure prediction system

This provides a single entry point for all connascence analysis functionality.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
import logging
import json

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Core analyzer components (Phase 1-5)
from analyzer.ast_engine.core_analyzer import ConnascenceASTAnalyzer
from analyzer.ast_engine.analyzer_orchestrator import AnalyzerOrchestrator
from analyzer.dup_detection.mece_analyzer import MECEAnalyzer
from analyzer.smart_integration_engine import SmartIntegrationEngine
from analyzer.failure_detection_system import FailureDetectionSystem

# Phase 6: Integrations
from src.mcp.nasa_integration import NASAPowerOfTenIntegration
from policy.manager import PolicyManager
from policy.budgets import BudgetTracker

logger = logging.getLogger(__name__)


@dataclass
class UnifiedAnalysisResult:
    """Complete analysis result from all Phase 1-6 components."""
    
    # Core results
    connascence_violations: List[Dict[str, Any]]
    duplication_clusters: List[Dict[str, Any]]
    nasa_violations: List[Dict[str, Any]]
    
    # Summary metrics
    total_violations: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    
    # Quality scores
    connascence_index: float
    nasa_compliance_score: float
    duplication_score: float
    overall_quality_score: float
    
    # Analysis metadata
    project_path: str
    policy_preset: str
    analysis_duration_ms: int
    files_analyzed: int
    timestamp: str
    
    # Recommendations
    priority_fixes: List[str]
    improvement_actions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


class UnifiedConnascenceAnalyzer:
    """
    Unified analyzer that orchestrates all Phase 1-6 analysis capabilities.
    
    This class provides a single, consistent interface to all connascence
    analysis features while maintaining the modularity of individual components.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the unified analyzer with all components."""
        
        # Initialize core analyzers
        self.ast_analyzer = ConnascenceASTAnalyzer()
        self.orchestrator = AnalyzerOrchestrator()
        self.mece_analyzer = MECEAnalyzer()
        self.smart_engine = SmartIntegrationEngine()
        self.failure_detector = FailureDetectionSystem()
        
        # Initialize integrations
        self.nasa_integration = NASAPowerOfTenIntegration()
        self.policy_manager = PolicyManager()
        self.budget_tracker = BudgetTracker()
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        logger.info("Unified Connascence Analyzer initialized with all Phase 1-6 components")
    
    def analyze_project(self, 
                       project_path: Union[str, Path], 
                       policy_preset: str = "service-defaults",
                       options: Optional[Dict[str, Any]] = None) -> UnifiedAnalysisResult:
        """
        Perform comprehensive connascence analysis on a project.
        
        Args:
            project_path: Path to the project directory
            policy_preset: Policy configuration to use
            options: Additional analysis options
            
        Returns:
            Complete analysis result with all findings and recommendations
        """
        
        project_path = Path(project_path)
        options = options or {}
        start_time = self._get_timestamp_ms()
        
        logger.info(f"Starting unified analysis of {project_path}")
        
        # Phase 1-2: Core AST Analysis
        logger.info("Phase 1-2: Running core AST analysis")
        ast_results = self.orchestrator.analyze_directory(project_path)
        connascence_violations = [self._violation_to_dict(v) for v in ast_results.violations]
        
        # Phase 3-4: MECE Duplication Detection
        logger.info("Phase 3-4: Running MECE duplication analysis")
        dup_results = self.mece_analyzer.analyze_duplications(project_path)
        duplication_clusters = [self._cluster_to_dict(c) for c in dup_results.clusters]
        
        # Phase 5: Smart Integration
        logger.info("Phase 5: Running smart integration engine")
        smart_results = self.smart_engine.comprehensive_analysis(
            str(project_path), policy_preset
        )
        
        # Phase 6: NASA Compliance Check
        logger.info("Phase 6: Checking NASA Power of Ten compliance")
        nasa_violations = []
        for violation in connascence_violations:
            nasa_checks = self.nasa_integration.check_nasa_violations(violation)
            nasa_violations.extend(nasa_checks)
        
        # Calculate metrics and scores
        metrics = self._calculate_comprehensive_metrics(
            connascence_violations, duplication_clusters, nasa_violations
        )
        
        # Generate recommendations
        recommendations = self._generate_unified_recommendations(
            connascence_violations, duplication_clusters, nasa_violations
        )
        
        # Build unified result
        analysis_time = self._get_timestamp_ms() - start_time
        
        result = UnifiedAnalysisResult(
            connascence_violations=connascence_violations,
            duplication_clusters=duplication_clusters,
            nasa_violations=nasa_violations,
            
            total_violations=metrics['total_violations'],
            critical_count=metrics['critical_count'],
            high_count=metrics['high_count'],
            medium_count=metrics['medium_count'],
            low_count=metrics['low_count'],
            
            connascence_index=metrics['connascence_index'],
            nasa_compliance_score=metrics['nasa_compliance_score'],
            duplication_score=metrics['duplication_score'],
            overall_quality_score=metrics['overall_quality_score'],
            
            project_path=str(project_path),
            policy_preset=policy_preset,
            analysis_duration_ms=analysis_time,
            files_analyzed=len(ast_results.analyzed_files),
            timestamp=self._get_iso_timestamp(),
            
            priority_fixes=recommendations['priority_fixes'],
            improvement_actions=recommendations['improvement_actions']
        )
        
        logger.info(f"Unified analysis complete in {analysis_time}ms")
        logger.info(f"Found {result.total_violations} total violations across all analyzers")
        
        return result
    
    def analyze_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Analyze a single file with all available analyzers."""
        file_path = Path(file_path)
        
        # Run individual file analysis through each component
        ast_violations = self.ast_analyzer.analyze_file(file_path)
        
        # Convert to unified format
        violations = [self._violation_to_dict(v) for v in ast_violations]
        
        # Check NASA compliance for each violation
        nasa_violations = []
        for violation in violations:
            nasa_checks = self.nasa_integration.check_nasa_violations(violation)
            nasa_violations.extend(nasa_checks)
        
        return {
            'file_path': str(file_path),
            'connascence_violations': violations,
            'nasa_violations': nasa_violations,
            'violation_count': len(violations),
            'nasa_compliance_score': self.nasa_integration.calculate_nasa_compliance_score(nasa_violations)
        }
    
    def get_dashboard_summary(self, analysis_result: UnifiedAnalysisResult) -> Dict[str, Any]:
        """Generate dashboard-compatible summary from analysis result."""
        return {
            'project_info': {
                'path': analysis_result.project_path,
                'policy': analysis_result.policy_preset,
                'files_analyzed': analysis_result.files_analyzed,
                'analysis_time': analysis_result.analysis_duration_ms
            },
            'violation_summary': {
                'total': analysis_result.total_violations,
                'by_severity': {
                    'critical': analysis_result.critical_count,
                    'high': analysis_result.high_count,
                    'medium': analysis_result.medium_count,
                    'low': analysis_result.low_count
                }
            },
            'quality_metrics': {
                'connascence_index': analysis_result.connascence_index,
                'nasa_compliance': analysis_result.nasa_compliance_score,
                'duplication_score': analysis_result.duplication_score,
                'overall_quality': analysis_result.overall_quality_score
            },
            'recommendations': {
                'priority_fixes': analysis_result.priority_fixes[:5],  # Top 5
                'improvement_actions': analysis_result.improvement_actions[:5]
            }
        }
    
    def _violation_to_dict(self, violation) -> Dict[str, Any]:
        """Convert violation object to dictionary."""
        return {
            'id': getattr(violation, 'id', str(hash(str(violation)))),
            'type': getattr(violation, 'type', 'unknown'),
            'severity': getattr(violation, 'severity', 'medium'),
            'description': getattr(violation, 'description', str(violation)),
            'file_path': getattr(violation, 'file_path', ''),
            'line_number': getattr(violation, 'line_number', 0),
            'weight': getattr(violation, 'weight', 1)
        }
    
    def _cluster_to_dict(self, cluster) -> Dict[str, Any]:
        """Convert duplication cluster to dictionary."""
        return {
            'id': getattr(cluster, 'id', str(hash(str(cluster)))),
            'type': 'duplication',
            'severity': getattr(cluster, 'severity', 'medium'),
            'functions': getattr(cluster, 'functions', []),
            'similarity_score': getattr(cluster, 'similarity_score', 0.0)
        }
    
    def _calculate_comprehensive_metrics(self, 
                                       connascence_violations: List[Dict], 
                                       duplication_clusters: List[Dict], 
                                       nasa_violations: List[Dict]) -> Dict[str, Any]:
        """Calculate comprehensive quality metrics."""
        
        all_violations = connascence_violations + duplication_clusters
        
        # Count by severity
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for violation in all_violations:
            severity = violation.get('severity', 'medium')
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        # Calculate connascence index
        weight_map = {'critical': 10, 'high': 5, 'medium': 2, 'low': 1}
        connascence_index = sum(
            weight_map.get(v.get('severity', 'medium'), 1) * v.get('weight', 1)
            for v in connascence_violations
        )
        
        # NASA compliance score
        nasa_compliance_score = self.nasa_integration.calculate_nasa_compliance_score(nasa_violations)
        
        # Duplication score
        duplication_score = max(0.0, 1.0 - (len(duplication_clusters) * 0.1))
        
        # Overall quality score (weighted average)
        connascence_weight = 0.4
        nasa_weight = 0.3
        duplication_weight = 0.3
        
        connascence_score = max(0.0, 1.0 - (connascence_index * 0.01))
        overall_quality_score = (
            connascence_score * connascence_weight +
            nasa_compliance_score * nasa_weight +
            duplication_score * duplication_weight
        )
        
        return {
            'total_violations': len(all_violations),
            'critical_count': severity_counts['critical'],
            'high_count': severity_counts['high'],
            'medium_count': severity_counts['medium'],
            'low_count': severity_counts['low'],
            'connascence_index': round(connascence_index, 2),
            'nasa_compliance_score': round(nasa_compliance_score, 3),
            'duplication_score': round(duplication_score, 3),
            'overall_quality_score': round(overall_quality_score, 3)
        }
    
    def _generate_unified_recommendations(self,
                                        connascence_violations: List[Dict],
                                        duplication_clusters: List[Dict],
                                        nasa_violations: List[Dict]) -> Dict[str, List[str]]:
        """Generate comprehensive improvement recommendations."""
        
        priority_fixes = []
        improvement_actions = []
        
        # Priority fixes from critical violations
        critical_violations = [v for v in connascence_violations if v.get('severity') == 'critical']
        for violation in critical_violations[:3]:  # Top 3 critical
            priority_fixes.append(f"Fix critical {violation.get('type', 'violation')} in {violation.get('file_path', 'unknown file')}")
        
        # NASA compliance actions
        nasa_actions = self.nasa_integration.get_nasa_compliance_actions(nasa_violations)
        improvement_actions.extend(nasa_actions[:3])
        
        # Duplication reduction
        if duplication_clusters:
            improvement_actions.append(f"Refactor {len(duplication_clusters)} duplication clusters to reduce code repetition")
        
        # General improvement suggestions
        if len(connascence_violations) > 10:
            improvement_actions.append("Consider breaking down large modules to reduce connascence violations")
        
        return {
            'priority_fixes': priority_fixes,
            'improvement_actions': improvement_actions
        }
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load analyzer configuration."""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        
        # Default configuration
        return {
            'enable_nasa_checks': True,
            'enable_mece_analysis': True,
            'enable_smart_integration': True,
            'default_policy_preset': 'service-defaults'
        }
    
    def _get_timestamp_ms(self) -> int:
        """Get current timestamp in milliseconds."""
        import time
        return int(time.time() * 1000)
    
    def _get_iso_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()


# Singleton instance for global access
unified_analyzer = UnifiedConnascenceAnalyzer()