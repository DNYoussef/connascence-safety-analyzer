
"""Threshold configurations for connascence analysis."""

from dataclasses import dataclass
from typing import Dict, Any
from enum import Enum

@dataclass
class ThresholdConfig:
    """Configuration for analysis thresholds."""
    max_positional_params: int = 4
    god_class_methods: int = 20
    max_cyclomatic_complexity: int = 10
    max_method_lines: int = 50
    max_class_lines: int = 300
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'max_positional_params': self.max_positional_params,
            'god_class_methods': self.god_class_methods,
            'max_cyclomatic_complexity': self.max_cyclomatic_complexity,
            'max_method_lines': self.max_method_lines,
            'max_class_lines': self.max_class_lines
        }

@dataclass
class WeightConfig:
    critical: float = 5.0
    high: float = 3.0
    medium: float = 2.0
    low: float = 1.0
    
class BudgetConfig:
    def __init__(self, **kwargs):
        self.limits = kwargs
        
class QualityGates:
    def __init__(self, **kwargs):
        self.gates = kwargs

class PolicyPreset:
    def __init__(self, name, **kwargs):
        self.name = name
        self.config = kwargs

class AnalysisResult:
    def __init__(self, violations=None, metrics=None):
        self.violations = violations or []
        self.metrics = metrics or {}

class Violation:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

class ConnascenceType(Enum):
    COM = 'CoM'
    COP = 'CoP'  
    COT = 'CoT'
    COA = 'CoA'
    CON = 'CoN'
    COI = 'CoI'

class Severity(Enum):
    CRITICAL = 'critical'
    HIGH = 'high'
    MEDIUM = 'medium'  
    LOW = 'low'

# Default thresholds configuration
DEFAULT_THRESHOLDS = ThresholdConfig()
