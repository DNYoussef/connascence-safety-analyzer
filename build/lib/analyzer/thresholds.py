"""Threshold configurations for connascence analysis."""

from typing import Dict, Any, Set
from enum import Enum

class ThresholdConfig:
    """Configuration for analysis thresholds."""
    def __init__(self):
        self.max_positional_params: int = 4
        self.god_class_methods: int = 20
        self.max_cyclomatic_complexity: int = 10
        self.max_method_lines: int = 50
        self.max_class_lines: int = 300
        self.god_class_lines: int = 300
        self.magic_literal_exceptions: Set = {0, 1, -1, 2, '', None, True, False}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'max_positional_params': self.max_positional_params,
            'god_class_methods': self.god_class_methods,
            'max_cyclomatic_complexity': self.max_cyclomatic_complexity,
            'max_method_lines': self.max_method_lines,
            'max_class_lines': self.max_class_lines
        }

class WeightConfig:
    """Weight configuration for violation scoring."""
    def __init__(self):
        self.critical: float = 5.0
        self.high: float = 3.0
        self.medium: float = 2.0
        self.low: float = 1.0
    
class BudgetConfig:
    """Budget configuration for violation limits."""
    def __init__(self, **kwargs):
        self.limits = kwargs
        
class QualityGates:
    """Quality gate configuration."""
    def __init__(self, **kwargs):
        self.gates = kwargs

class PolicyPreset:
    """Policy preset configuration."""
    def __init__(self, name, **kwargs):
        self.name = name
        self.config = kwargs

class AnalysisResult:
    """Basic analysis result container."""
    def __init__(self, violations=None, metrics=None):
        self.violations = violations or []
        self.metrics = metrics or {}

class Violation:
    """Basic violation container."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

class ConnascenceType(Enum):
    """Connascence type enumeration."""
    NAME = 'CoN'
    TYPE = 'CoT'  
    MEANING = 'CoM'
    POSITION = 'CoP'
    ALGORITHM = 'CoA'
    IDENTITY = 'CoI'
    EXECUTION = 'CoE'
    TIMING = 'CoTi'
    VALUES = 'CoV'

class Severity(Enum):
    """Severity level enumeration."""
    CRITICAL = 'critical'
    HIGH = 'high'
    MEDIUM = 'medium'  
    LOW = 'low'

# Default configurations
DEFAULT_THRESHOLDS = ThresholdConfig()
DEFAULT_WEIGHTS = WeightConfig()

def get_severity_for_violation(conn_type: ConnascenceType, context: Dict[str, Any]) -> Severity:
    """Determine severity based on connascence type and context."""
    # High complexity or security-related violations
    if context.get('security_related', False):
        return Severity.CRITICAL
    
    # Critical patterns
    if conn_type == ConnascenceType.ALGORITHM and context.get('complexity', 0) > 15:
        return Severity.CRITICAL
    if conn_type == ConnascenceType.POSITION and context.get('parameter_count', 0) > 8:
        return Severity.CRITICAL
    
    # High severity patterns  
    if conn_type == ConnascenceType.ALGORITHM and context.get('complexity', 0) > 10:
        return Severity.HIGH
    if conn_type == ConnascenceType.POSITION and context.get('parameter_count', 0) > 5:
        return Severity.HIGH
    if conn_type == ConnascenceType.MEANING and context.get('in_conditional', False):
        return Severity.HIGH
    
    # Medium severity (default for most)
    if conn_type in [ConnascenceType.MEANING, ConnascenceType.NAME]:
        return Severity.MEDIUM
    
    # Low severity
    return Severity.LOW

def calculate_violation_weight(
    conn_type: ConnascenceType, 
    severity: Severity, 
    locality: str,
    file_path: str,
    weights: WeightConfig = None
) -> float:
    """Calculate numeric weight for a violation.
    
    Args:
        violation_type: Type of connascence violation
        severity: Severity level of the violation
        locality: Scope locality (same_function, same_class, etc.)
        file_path: Path to the file containing the violation
        weights_config: Weight configuration to use
        
    Returns:
        Calculated weight value
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS
    
    # Base weight from severity
    severity_weights = {
        Severity.CRITICAL: weights.critical,
        Severity.HIGH: weights.high,
        Severity.MEDIUM: weights.medium,
        Severity.LOW: weights.low,
    }
    
    base_weight = severity_weights.get(severity, weights.medium)
    
    # Locality multiplier
    locality_multiplier = {
        'same_function': 1.0,
        'same_class': 1.2, 
        'same_module': 1.5,
        'cross_module': 2.0
    }.get(locality, 1.0)
    
    # Type-specific adjustments
    type_multipliers = {
        ConnascenceType.NAME: 0.9,
        ConnascenceType.TYPE: 0.8,
        ConnascenceType.MEANING: 1.1,
        ConnascenceType.POSITION: 1.3,
        ConnascenceType.ALGORITHM: 1.4,
        ConnascenceType.IDENTITY: 1.5,
    }
    
    type_multiplier = type_multipliers.get(conn_type, 1.0)
    
    return base_weight * locality_multiplier * type_multiplier