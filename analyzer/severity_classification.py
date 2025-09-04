#!/usr/bin/env python3
"""
Enhanced Severity Classification System - Phase 3 Implementation
===============================================================

PHASE 3: Consolidation and enhancement of existing severity classification systems
found throughout the codebase:

EXISTING COMPONENTS DISCOVERED AND INTEGRATED:
1. analyzer/thresholds.py - get_severity_for_violation() function (MOVED)
2. mcp/server.py - calculate_enhanced_severity() function (MOVED)  
3. analyzer/smart_integration_engine.py - _get_violation_severity() + _calculate_cluster_severity() (MOVED)
4. policy/manager.py - PolicyViolation severity handling (INTEGRATED)
5. integrations/enhanced_tool_coordinator.py - _enhanced_severity_classification() (EXTENDED)

This consolidates all severity logic into a single, comprehensive system
connected to the core analyzer pipeline.
"""

import logging
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
import statistics

logger = logging.getLogger(__name__)


class SeverityLevel(Enum):
    """Standardized severity levels across the entire system."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConnascenceType(Enum):
    """Connascence types for severity calculation."""
    NAME = "CoN"
    TYPE = "CoT" 
    MEANING = "CoM"
    POSITION = "CoP"
    ALGORITHM = "CoA"
    TIMING = "CoTm"
    VALUE = "CoV"
    IDENTITY = "CoI"


@dataclass
class SeverityContext:
    """Context information for severity determination."""
    violation_type: str
    file_path: str = ""
    line_number: int = 0
    complexity: int = 0
    parameter_count: int = 0
    security_related: bool = False
    in_conditional: bool = False
    nasa_rules_violated: List[str] = None
    cross_tool_confidence: float = 0.0
    supporting_tools: List[str] = None
    business_impact: str = "medium"
    technical_debt_score: float = 0.0
    
    def __post_init__(self):
        if self.nasa_rules_violated is None:
            self.nasa_rules_violated = []
        if self.supporting_tools is None:
            self.supporting_tools = []


@dataclass
class SeverityResult:
    """Result of severity classification."""
    original_severity: SeverityLevel
    calculated_severity: SeverityLevel
    confidence: float
    reasoning: List[str]
    upgrade_applied: bool
    downgrade_applied: bool
    factors_considered: List[str]
    nasa_impact: bool = False
    tool_consensus: float = 0.0


class SeverityCalculator:
    """Core severity calculation engine - consolidated from existing components."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Thresholds from analyzer/thresholds.py (moved here)
        self.complexity_critical = self.config.get('complexity_critical', 15)
        self.complexity_high = self.config.get('complexity_high', 10)
        self.parameters_critical = self.config.get('parameters_critical', 8)
        self.parameters_high = self.config.get('parameters_high', 5)
        
        # Cross-tool confidence thresholds
        self.multi_tool_upgrade_threshold = self.config.get('multi_tool_threshold', 0.75)
        self.nasa_violation_boost = self.config.get('nasa_boost', 1.5)
        
        # Initialize severity calculation rules
        self._initialize_severity_rules()
    
    def _initialize_severity_rules(self):
        """Initialize severity calculation rules consolidated from existing systems."""
        
        # From analyzer/thresholds.py get_severity_for_violation
        self.base_severity_rules = {
            ConnascenceType.ALGORITHM: {
                'base': SeverityLevel.MEDIUM,
                'critical_threshold': {'complexity': self.complexity_critical},
                'high_threshold': {'complexity': self.complexity_high}
            },
            ConnascenceType.POSITION: {
                'base': SeverityLevel.MEDIUM,
                'critical_threshold': {'parameter_count': self.parameters_critical},
                'high_threshold': {'parameter_count': self.parameters_high}
            },
            ConnascenceType.MEANING: {
                'base': SeverityLevel.MEDIUM,
                'high_conditions': ['in_conditional'],
                'critical_conditions': ['security_related']
            },
            ConnascenceType.TYPE: {
                'base': SeverityLevel.HIGH,  # Type issues are inherently serious
                'critical_conditions': ['security_related']
            },
            ConnascenceType.TIMING: {
                'base': SeverityLevel.HIGH,  # Timing issues can cause race conditions
                'critical_conditions': ['security_related', 'in_critical_path']
            }
        }
        
        # NASA rule severity mappings (from mcp/nasa_power_of_ten_integration.py)
        self.nasa_rule_severity_map = {
            'nasa_rule_1': SeverityLevel.CRITICAL,  # Control flow complexity
            'nasa_rule_2': SeverityLevel.CRITICAL,  # Loop bounds
            'nasa_rule_3': SeverityLevel.CRITICAL,  # Dynamic memory
            'nasa_rule_4': SeverityLevel.HIGH,      # Function size
            'nasa_rule_5': SeverityLevel.HIGH,      # Assertions
            'nasa_rule_6': SeverityLevel.MEDIUM,    # Variable scope
            'nasa_rule_7': SeverityLevel.HIGH,      # Return values
            'nasa_rule_8': SeverityLevel.MEDIUM,    # Preprocessor
            'nasa_rule_9': SeverityLevel.HIGH,      # Pointers
            'nasa_rule_10': SeverityLevel.CRITICAL  # Compiler warnings
        }
    
    def calculate_severity(self, context: SeverityContext, 
                          original_severity: Optional[str] = None) -> SeverityResult:
        """
        Enhanced severity calculation integrating all existing systems.
        
        Consolidates logic from:
        - analyzer/thresholds.py get_severity_for_violation()
        - mcp/server.py calculate_enhanced_severity()
        - analyzer/smart_integration_engine.py _calculate_cluster_severity()
        """
        
        original = self._parse_severity(original_severity) if original_severity else SeverityLevel.MEDIUM
        reasoning = []
        factors_considered = []
        
        # Step 1: Base severity from violation type (from analyzer/thresholds.py)
        base_severity = self._calculate_base_severity(context, reasoning, factors_considered)
        
        # Step 2: NASA rules impact (from mcp/nasa_power_of_ten_integration.py)
        nasa_adjusted_severity = self._apply_nasa_rules_adjustment(
            base_severity, context, reasoning, factors_considered
        )
        
        # Step 3: Cross-tool consensus adjustment (from mcp/server.py)
        tool_adjusted_severity = self._apply_cross_tool_adjustment(
            nasa_adjusted_severity, context, reasoning, factors_considered
        )
        
        # Step 4: Business impact and technical debt (new enhancement)
        final_severity = self._apply_business_impact_adjustment(
            tool_adjusted_severity, context, reasoning, factors_considered
        )
        
        # Calculate confidence based on available information
        confidence = self._calculate_confidence(context, reasoning)
        
        # Determine if upgrade or downgrade was applied
        upgrade_applied = final_severity.value != original.value and self._severity_level(final_severity) > self._severity_level(original)
        downgrade_applied = final_severity.value != original.value and self._severity_level(final_severity) < self._severity_level(original)
        
        return SeverityResult(
            original_severity=original,
            calculated_severity=final_severity,
            confidence=confidence,
            reasoning=reasoning,
            upgrade_applied=upgrade_applied,
            downgrade_applied=downgrade_applied,
            factors_considered=factors_considered,
            nasa_impact=len(context.nasa_rules_violated) > 0,
            tool_consensus=context.cross_tool_confidence
        )
    
    def _calculate_base_severity(self, context: SeverityContext, 
                               reasoning: List[str], factors_considered: List[str]) -> SeverityLevel:
        """Calculate base severity from violation type (from analyzer/thresholds.py)."""
        
        violation_type = context.violation_type
        
        # Handle string-based violation types
        if isinstance(violation_type, str):
            if 'algorithm' in violation_type.lower() or 'coa' in violation_type.upper():
                conn_type = ConnascenceType.ALGORITHM
            elif 'position' in violation_type.lower() or 'cop' in violation_type.upper():
                conn_type = ConnascenceType.POSITION
            elif 'meaning' in violation_type.lower() or 'com' in violation_type.upper():
                conn_type = ConnascenceType.MEANING
            elif 'type' in violation_type.lower() or 'cot' in violation_type.upper():
                conn_type = ConnascenceType.TYPE
            elif 'timing' in violation_type.lower() or 'cotm' in violation_type.upper():
                conn_type = ConnascenceType.TIMING
            else:
                # Default to MEANING for unknown types
                conn_type = ConnascenceType.MEANING
        else:
            conn_type = ConnascenceType.MEANING
        
        # Get base rule
        rule = self.base_severity_rules.get(conn_type, {'base': SeverityLevel.MEDIUM})
        base_severity = rule['base']
        factors_considered.append(f'base_type_{conn_type.value}')
        
        # Check for critical conditions
        if 'critical_threshold' in rule:
            for metric, threshold in rule['critical_threshold'].items():
                if getattr(context, metric, 0) > threshold:
                    reasoning.append(f"Critical threshold exceeded: {metric} = {getattr(context, metric, 0)} > {threshold}")
                    factors_considered.append(f'critical_{metric}')
                    return SeverityLevel.CRITICAL
        
        if 'critical_conditions' in rule:
            for condition in rule['critical_conditions']:
                if getattr(context, condition, False):
                    reasoning.append(f"Critical condition met: {condition}")
                    factors_considered.append(f'critical_condition_{condition}')
                    return SeverityLevel.CRITICAL
        
        # Check for high conditions  
        if 'high_threshold' in rule:
            for metric, threshold in rule['high_threshold'].items():
                if getattr(context, metric, 0) > threshold:
                    reasoning.append(f"High threshold exceeded: {metric} = {getattr(context, metric, 0)} > {threshold}")
                    factors_considered.append(f'high_{metric}')
                    return SeverityLevel.HIGH
        
        if 'high_conditions' in rule:
            for condition in rule['high_conditions']:
                if getattr(context, condition, False):
                    reasoning.append(f"High condition met: {condition}")
                    factors_considered.append(f'high_condition_{condition}')
                    return SeverityLevel.HIGH
        
        reasoning.append(f"Base severity for {conn_type.value}: {base_severity.value}")
        return base_severity
    
    def _apply_nasa_rules_adjustment(self, base_severity: SeverityLevel, context: SeverityContext,
                                   reasoning: List[str], factors_considered: List[str]) -> SeverityLevel:
        """Apply NASA Power of Ten rules severity adjustment."""
        
        if not context.nasa_rules_violated:
            return base_severity
        
        highest_nasa_severity = base_severity
        
        for nasa_rule in context.nasa_rules_violated:
            rule_severity = self.nasa_rule_severity_map.get(nasa_rule, SeverityLevel.MEDIUM)
            
            if self._severity_level(rule_severity) > self._severity_level(highest_nasa_severity):
                highest_nasa_severity = rule_severity
                reasoning.append(f"NASA rule {nasa_rule} requires {rule_severity.value} severity")
                factors_considered.append(f'nasa_{nasa_rule}')
        
        # Apply NASA boost multiplier
        if len(context.nasa_rules_violated) > 1:
            if highest_nasa_severity == SeverityLevel.HIGH:
                highest_nasa_severity = SeverityLevel.CRITICAL
                reasoning.append(f"Multiple NASA rules violated ({len(context.nasa_rules_violated)}) - upgraded to critical")
                factors_considered.append('multiple_nasa_rules')
        
        return highest_nasa_severity
    
    def _apply_cross_tool_adjustment(self, base_severity: SeverityLevel, context: SeverityContext,
                                   reasoning: List[str], factors_considered: List[str]) -> SeverityLevel:
        """Apply cross-tool consensus adjustment (from mcp/server.py)."""
        
        if context.cross_tool_confidence < self.multi_tool_upgrade_threshold:
            return base_severity
        
        # Upgrade logic from mcp/server.py calculate_enhanced_severity
        if context.cross_tool_confidence >= 0.75:  # 3+ tools agree
            severity_upgrade = {
                SeverityLevel.LOW: SeverityLevel.MEDIUM,
                SeverityLevel.MEDIUM: SeverityLevel.HIGH,
                SeverityLevel.HIGH: SeverityLevel.CRITICAL
            }
            
            upgraded = severity_upgrade.get(base_severity, base_severity)
            if upgraded != base_severity:
                reasoning.append(f"Cross-tool consensus ({context.cross_tool_confidence:.2%}) upgraded severity")
                factors_considered.append('cross_tool_consensus')
                factors_considered.extend([f'tool_{tool}' for tool in context.supporting_tools])
            
            return upgraded
        
        return base_severity
    
    def _apply_business_impact_adjustment(self, base_severity: SeverityLevel, context: SeverityContext,
                                        reasoning: List[str], factors_considered: List[str]) -> SeverityLevel:
        """Apply business impact and technical debt adjustments (new enhancement)."""
        
        adjusted_severity = base_severity
        
        # Business impact adjustment
        if context.business_impact == "high":
            if adjusted_severity == SeverityLevel.MEDIUM:
                adjusted_severity = SeverityLevel.HIGH
                reasoning.append("High business impact upgraded severity to high")
                factors_considered.append('business_impact_high')
        elif context.business_impact == "critical":
            if adjusted_severity in [SeverityLevel.MEDIUM, SeverityLevel.HIGH]:
                adjusted_severity = SeverityLevel.CRITICAL
                reasoning.append("Critical business impact upgraded severity to critical")
                factors_considered.append('business_impact_critical')
        
        # Technical debt score adjustment
        if context.technical_debt_score > 0.8:  # High technical debt
            if adjusted_severity == SeverityLevel.LOW:
                adjusted_severity = SeverityLevel.MEDIUM
                reasoning.append(f"High technical debt score ({context.technical_debt_score:.2f}) upgraded severity")
                factors_considered.append('technical_debt_high')
        
        return adjusted_severity
    
    def _calculate_confidence(self, context: SeverityContext, reasoning: List[str]) -> float:
        """Calculate confidence in severity assessment."""
        confidence_factors = []
        
        # Base confidence from available context
        base_confidence = 0.5
        
        # Increase confidence for each available context piece
        if context.complexity > 0:
            confidence_factors.append(0.15)
        if context.parameter_count > 0:
            confidence_factors.append(0.1)
        if context.nasa_rules_violated:
            confidence_factors.append(0.2)
        if context.supporting_tools:
            confidence_factors.append(0.1 * len(context.supporting_tools))
        if context.cross_tool_confidence > 0:
            confidence_factors.append(context.cross_tool_confidence * 0.2)
        
        total_confidence = min(1.0, base_confidence + sum(confidence_factors))
        return total_confidence
    
    def _severity_level(self, severity: SeverityLevel) -> int:
        """Convert severity to numeric level for comparison."""
        levels = {
            SeverityLevel.LOW: 1,
            SeverityLevel.MEDIUM: 2,
            SeverityLevel.HIGH: 3,
            SeverityLevel.CRITICAL: 4
        }
        return levels.get(severity, 2)
    
    def _parse_severity(self, severity_str: str) -> SeverityLevel:
        """Parse string severity to SeverityLevel enum."""
        severity_map = {
            'low': SeverityLevel.LOW,
            'medium': SeverityLevel.MEDIUM,
            'high': SeverityLevel.HIGH,
            'critical': SeverityLevel.CRITICAL
        }
        return severity_map.get(severity_str.lower(), SeverityLevel.MEDIUM)


class BatchSeverityClassifier:
    """Batch processor for severity classification with cluster analysis."""
    
    def __init__(self, calculator: SeverityCalculator):
        self.calculator = calculator
        self.violation_clusters: Dict[str, List[SeverityContext]] = {}
    
    def classify_violations_batch(self, violations: List[Dict], 
                                cross_tool_results: Optional[Dict] = None) -> List[SeverityResult]:
        """
        Classify multiple violations with cluster analysis.
        
        Integrates logic from analyzer/smart_integration_engine.py _calculate_cluster_severity().
        """
        
        # Convert violations to SeverityContext objects
        contexts = self._create_contexts_from_violations(violations, cross_tool_results)
        
        # Group violations into clusters by file and type
        clusters = self._cluster_violations(contexts)
        
        # Apply cluster-based adjustments
        adjusted_contexts = self._apply_cluster_adjustments(clusters, contexts)
        
        # Calculate severity for each violation
        results = []
        for context in adjusted_contexts:
            result = self.calculator.calculate_severity(context)
            results.append(result)
        
        return results
    
    def _create_contexts_from_violations(self, violations: List[Dict], 
                                       cross_tool_results: Optional[Dict] = None) -> List[SeverityContext]:
        """Create SeverityContext objects from violation dictionaries."""
        
        contexts = []
        
        for violation in violations:
            # Extract cross-tool data if available
            cross_tool_confidence = 0.0
            supporting_tools = []
            
            if cross_tool_results:
                violation_id = violation.get('id', '')
                tool_data = cross_tool_results.get(violation_id, {})
                cross_tool_confidence = tool_data.get('confidence', 0.0)
                supporting_tools = tool_data.get('supporting_tools', [])
            
            # Extract NASA rules from violation context
            nasa_rules_violated = []
            violation_context = violation.get('context', {})
            if isinstance(violation_context, dict):
                nasa_rules_violated = violation_context.get('nasa_rules_violated', [])
                if not isinstance(nasa_rules_violated, list):
                    nasa_rules_violated = []
            
            context = SeverityContext(
                violation_type=violation.get('type', 'unknown'),
                file_path=violation.get('file_path', ''),
                line_number=violation.get('line_number', 0),
                complexity=violation_context.get('complexity', 0) if isinstance(violation_context, dict) else 0,
                parameter_count=violation_context.get('parameter_count', 0) if isinstance(violation_context, dict) else 0,
                security_related=violation_context.get('security_related', False) if isinstance(violation_context, dict) else False,
                in_conditional=violation_context.get('in_conditional', False) if isinstance(violation_context, dict) else False,
                nasa_rules_violated=nasa_rules_violated,
                cross_tool_confidence=cross_tool_confidence,
                supporting_tools=supporting_tools,
                business_impact=violation.get('business_impact', 'medium'),
                technical_debt_score=violation.get('technical_debt_score', 0.0)
            )
            
            contexts.append(context)
        
        return contexts
    
    def _cluster_violations(self, contexts: List[SeverityContext]) -> Dict[str, List[SeverityContext]]:
        """Group violations into clusters for analysis (from smart_integration_engine.py)."""
        
        clusters = {}
        
        for context in contexts:
            # Create cluster key based on file and violation type
            cluster_key = f"{context.file_path}:{context.violation_type}"
            
            if cluster_key not in clusters:
                clusters[cluster_key] = []
            
            clusters[cluster_key].append(context)
        
        return clusters
    
    def _apply_cluster_adjustments(self, clusters: Dict[str, List[SeverityContext]], 
                                 contexts: List[SeverityContext]) -> List[SeverityContext]:
        """Apply cluster-based severity adjustments."""
        
        adjusted_contexts = []
        
        for context in contexts:
            cluster_key = f"{context.file_path}:{context.violation_type}"
            cluster = clusters.get(cluster_key, [context])
            
            # Apply cluster size boost
            if len(cluster) > 3:  # Multiple violations of same type in same file
                # Increase technical debt score to boost severity
                context.technical_debt_score = max(context.technical_debt_score, 0.7)
            
            # Apply cross-cluster correlation
            related_clusters = [c for c in clusters.values() if self._clusters_related(cluster, c)]
            if len(related_clusters) > 2:  # Multiple related violation types
                context.business_impact = "high"
            
            adjusted_contexts.append(context)
        
        return adjusted_contexts
    
    def _clusters_related(self, cluster1: List[SeverityContext], cluster2: List[SeverityContext]) -> bool:
        """Check if two clusters are related (same file or related types)."""
        
        if cluster1 == cluster2:
            return False
        
        # Same file
        files1 = set(c.file_path for c in cluster1)
        files2 = set(c.file_path for c in cluster2)
        if files1.intersection(files2):
            return True
        
        # Related violation types
        related_types = [
            ('position', 'algorithm'),  # Parameter and complexity issues often related
            ('meaning', 'type'),        # Magic values and type issues often related
            ('timing', 'algorithm'),    # Timing and algorithm complexity related
        ]
        
        types1 = set(c.violation_type.lower() for c in cluster1)
        types2 = set(c.violation_type.lower() for c in cluster2)
        
        for type1, type2 in related_types:
            if (any(type1 in t for t in types1) and any(type2 in t for t in types2)) or \
               (any(type2 in t for t in types1) and any(type1 in t for t in types2)):
                return True
        
        return False


# Integration with existing system
def integrate_with_core_analyzer():
    """Integration point for connecting to core analyzer pipeline."""
    
    # This function will be called from analyzer/check_connascence.py
    # to replace the distributed severity calculation logic
    
    calculator = SeverityCalculator()
    classifier = BatchSeverityClassifier(calculator)
    
    return calculator, classifier


# Backward compatibility functions (maintain existing API)
def get_severity_for_violation(conn_type, context: Dict[str, Any]) -> str:
    """Backward compatibility with analyzer/thresholds.py."""
    calculator = SeverityCalculator()
    
    severity_context = SeverityContext(
        violation_type=conn_type,
        complexity=context.get('complexity', 0),
        parameter_count=context.get('parameter_count', 0),
        security_related=context.get('security_related', False),
        in_conditional=context.get('in_conditional', False)
    )
    
    result = calculator.calculate_severity(severity_context)
    return result.calculated_severity.value


def calculate_enhanced_severity(violation: Dict, linter_correlations: Dict) -> str:
    """Backward compatibility with mcp/server.py."""
    calculator = SeverityCalculator()
    
    severity_context = SeverityContext(
        violation_type=violation.get('type', 'unknown'),
        file_path=violation.get('file_path', ''),
        line_number=violation.get('line_number', 0),
        cross_tool_confidence=linter_correlations.get('cross_tool_confidence', 0.0),
        supporting_tools=linter_correlations.get('supporting_tools', [])
    )
    
    original_severity = violation.get('severity', 'medium')
    result = calculator.calculate_severity(severity_context, original_severity)
    return result.calculated_severity.value


if __name__ == "__main__":
    # Test the enhanced severity classification system
    
    # Test case 1: NASA rule violation with high complexity
    test_context = SeverityContext(
        violation_type="connascence_of_algorithm",
        complexity=12,
        nasa_rules_violated=["nasa_rule_4"],
        cross_tool_confidence=0.8,
        supporting_tools=["ruff", "radon", "mypy"]
    )
    
    calculator = SeverityCalculator()
    result = calculator.calculate_severity(test_context, "medium")
    
    print(f"Test Case 1 - High Complexity + NASA Rule:")
    print(f"  Original: {result.original_severity.value}")
    print(f"  Calculated: {result.calculated_severity.value}")
    print(f"  Confidence: {result.confidence:.2%}")
    print(f"  Upgrade applied: {result.upgrade_applied}")
    print(f"  Reasoning: {', '.join(result.reasoning)}")
    print()
    
    # Test case 2: Multiple tool consensus
    test_context2 = SeverityContext(
        violation_type="connascence_of_meaning",
        cross_tool_confidence=0.9,
        supporting_tools=["ruff", "mypy", "bandit", "black"],
        security_related=True
    )
    
    result2 = calculator.calculate_severity(test_context2, "low")
    
    print(f"Test Case 2 - Multi-tool Security Issue:")
    print(f"  Original: {result2.original_severity.value}")
    print(f"  Calculated: {result2.calculated_severity.value}")
    print(f"  Confidence: {result2.confidence:.2%}")
    print(f"  Factors: {', '.join(result2.factors_considered)}")