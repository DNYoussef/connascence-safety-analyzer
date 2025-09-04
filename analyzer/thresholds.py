"""Threshold configurations for connascence analysis."""

from typing import Dict, Any, Set
from enum import Enum
from .constants import (
    DEFAULT_MAX_POSITIONAL_PARAMS, DEFAULT_GOD_CLASS_METHODS, 
    DEFAULT_MAX_CYCLOMATIC_COMPLEXITY, DEFAULT_MAX_METHOD_LINES,
    DEFAULT_MAX_CLASS_LINES, DEFAULT_GOD_CLASS_LINES, MAGIC_LITERAL_EXCEPTIONS
)

class ThresholdConfig:
    """Configuration for analysis thresholds."""
    def __init__(self, max_positional_params: int = DEFAULT_MAX_POSITIONAL_PARAMS, 
                 god_class_methods: int = DEFAULT_GOD_CLASS_METHODS, 
                 max_cyclomatic_complexity: int = DEFAULT_MAX_CYCLOMATIC_COMPLEXITY, 
                 max_method_lines: int = DEFAULT_MAX_METHOD_LINES,
                 max_class_lines: int = DEFAULT_MAX_CLASS_LINES, 
                 god_class_lines: int = DEFAULT_GOD_CLASS_LINES,
                 magic_literal_exceptions: Set = None,
                 max_function_length: int = 100,
                 max_module_length: int = 2000,
                 max_classes_per_module: int = 15,
                 max_functions_per_module: int = 30):
        self.max_positional_params: int = max_positional_params
        self.god_class_methods: int = god_class_methods
        self.max_cyclomatic_complexity: int = max_cyclomatic_complexity
        self.max_method_lines: int = max_method_lines
        self.max_class_lines: int = max_class_lines
        self.god_class_lines: int = god_class_lines
        self.magic_literal_exceptions: Set = magic_literal_exceptions or MAGIC_LITERAL_EXCEPTIONS
        self.max_function_length: int = max_function_length
        self.max_module_length: int = max_module_length
        self.max_classes_per_module: int = max_classes_per_module
        self.max_functions_per_module: int = max_functions_per_module
    
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
        from .constants import (
            DEFAULT_CRITICAL_WEIGHT, DEFAULT_HIGH_WEIGHT,
            DEFAULT_MEDIUM_WEIGHT, DEFAULT_LOW_WEIGHT
        )
        self.critical: float = DEFAULT_CRITICAL_WEIGHT
        self.high: float = DEFAULT_HIGH_WEIGHT
        self.medium: float = DEFAULT_MEDIUM_WEIGHT
        self.low: float = DEFAULT_LOW_WEIGHT
    
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
    from .constants import MAX_COMPLEXITY_CRITICAL, MAX_COMPLEXITY_HIGH, MAX_PARAMETERS_CRITICAL, MAX_PARAMETERS_HIGH
    
    # High complexity or security-related violations
    if context.get('security_related', False):
        return Severity.CRITICAL
    
    # Critical patterns
    if conn_type == ConnascenceType.ALGORITHM and context.get('complexity', 0) > MAX_COMPLEXITY_CRITICAL:
        return Severity.CRITICAL
    if conn_type == ConnascenceType.POSITION and context.get('parameter_count', 0) > MAX_PARAMETERS_CRITICAL:
        return Severity.CRITICAL
    
    # High severity patterns  
    if conn_type == ConnascenceType.ALGORITHM and context.get('complexity', 0) > MAX_COMPLEXITY_HIGH:
        return Severity.HIGH
    if conn_type == ConnascenceType.POSITION and context.get('parameter_count', 0) > MAX_PARAMETERS_HIGH:
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
    from .constants import (
        LOCALITY_SAME_FUNCTION, LOCALITY_SAME_CLASS, 
        LOCALITY_SAME_MODULE, LOCALITY_CROSS_MODULE,
        TYPE_MULTIPLIER_NAME, TYPE_MULTIPLIER_TYPE, TYPE_MULTIPLIER_MEANING,
        TYPE_MULTIPLIER_POSITION, TYPE_MULTIPLIER_ALGORITHM, TYPE_MULTIPLIER_IDENTITY
    )
    
    locality_multiplier = {
        'same_function': LOCALITY_SAME_FUNCTION,
        'same_class': LOCALITY_SAME_CLASS, 
        'same_module': LOCALITY_SAME_MODULE,
        'cross_module': LOCALITY_CROSS_MODULE
    }.get(locality, LOCALITY_SAME_FUNCTION)
    
    # Type-specific adjustments
    type_multipliers = {
        ConnascenceType.NAME: TYPE_MULTIPLIER_NAME,
        ConnascenceType.TYPE: TYPE_MULTIPLIER_TYPE,
        ConnascenceType.MEANING: TYPE_MULTIPLIER_MEANING,
        ConnascenceType.POSITION: TYPE_MULTIPLIER_POSITION,
        ConnascenceType.ALGORITHM: TYPE_MULTIPLIER_ALGORITHM,
        ConnascenceType.IDENTITY: TYPE_MULTIPLIER_IDENTITY,
    }
    
    type_multiplier = type_multipliers.get(conn_type, 1.0)
    
    return base_weight * locality_multiplier * type_multiplier