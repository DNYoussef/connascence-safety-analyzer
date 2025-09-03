"""
Connascence Detection Thresholds and Configuration

This module defines all thresholds and weights used in connascence analysis,
with clear rationale and configurability for different environments.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum


class Severity(Enum):
    """Severity levels for connascence violations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConnascenceType(Enum):
    """Types of connascence from weakest to strongest."""
    # Static forms (compile-time)
    NAME = "CoN"           # Connascence of Name
    TYPE = "CoT"           # Connascence of Type  
    MEANING = "CoM"        # Connascence of Meaning
    POSITION = "CoP"       # Connascence of Position
    ALGORITHM = "CoA"      # Connascence of Algorithm
    
    # Dynamic forms (runtime)
    EXECUTION = "CoE"      # Connascence of Execution
    TIMING = "CoTi"        # Connascence of Timing
    VALUE = "CoV"          # Connascence of Value
    IDENTITY = "CoI"       # Connascence of Identity


@dataclass
class ThresholdConfig:
    """Configuration for connascence detection thresholds."""
    
    # Position thresholds
    max_positional_params: int = 3
    max_function_params: int = 7
    
    # Size thresholds  
    god_class_methods: int = 20
    god_class_lines: int = 500
    god_function_lines: int = 50
    
    # Complexity thresholds
    max_cyclomatic_complexity: int = 10
    max_nesting_depth: int = 4
    max_return_statements: int = 5
    
    # Magic literal thresholds
    max_magic_literals_per_function: int = 5
    max_magic_literals_per_file: int = 20
    magic_literal_density_threshold: float = 0.25  # 25%
    
    # Global variable thresholds
    max_global_variables: int = 5
    max_global_mutations: int = 3
    
    # Duplication thresholds
    min_duplicate_lines: int = 6
    similarity_threshold: float = 0.85
    
    # Time-based thresholds (for runtime detection)
    max_sleep_duration_ms: int = 100
    timing_dependency_threshold_ms: int = 50
    
    # Allowed exceptions
    magic_literal_exceptions: List = None
    
    def __post_init__(self):
        if self.magic_literal_exceptions is None:
            self.magic_literal_exceptions = [
                # Common non-magic numbers
                0, 1, -1, 2, 10, 24, 60, 100, 1000,
                # Common percentages  
                0.0, 0.5, 1.0,
                # HTTP status codes
                200, 201, 204, 400, 401, 403, 404, 500,
                # Port numbers
                80, 443, 8080, 3000,
                # Boolean-like
                True, False, None
            ]


@dataclass  
class WeightConfig:
    """Weights for different connascence types and contexts."""
    
    # Base weights by connascence type (higher = worse)
    type_weights: Dict[ConnascenceType, int] = None
    
    # Locality multipliers (closer = worse)
    same_function_multiplier: float = 1.0
    same_class_multiplier: float = 2.0  
    same_module_multiplier: float = 3.0
    cross_module_multiplier: float = 5.0
    
    # Directory-based multipliers
    core_code_multiplier: float = 2.0      # /core, /src paths
    test_code_multiplier: float = 0.5      # /test paths
    config_code_multiplier: float = 0.7    # /config paths
    experimental_multiplier: float = 0.3   # /experimental paths
    
    # Severity weights
    severity_weights: Dict[Severity, int] = None
    
    def __post_init__(self):
        if self.type_weights is None:
            self.type_weights = {
                # Static forms (weakest to strongest)
                ConnascenceType.NAME: 1,
                ConnascenceType.TYPE: 2,
                ConnascenceType.MEANING: 3,
                ConnascenceType.POSITION: 4,
                ConnascenceType.ALGORITHM: 5,
                
                # Dynamic forms (stronger)
                ConnascenceType.EXECUTION: 6,
                ConnascenceType.TIMING: 8,
                ConnascenceType.VALUE: 7,
                ConnascenceType.IDENTITY: 9,
            }
            
        if self.severity_weights is None:
            self.severity_weights = {
                Severity.LOW: 1,
                Severity.MEDIUM: 3,
                Severity.HIGH: 9,
                Severity.CRITICAL: 27,
            }


@dataclass
class PolicyPreset:
    """Predefined policy configurations for different environments."""
    
    name: str
    description: str
    thresholds: ThresholdConfig
    weights: WeightConfig
    enabled_analyzers: List[str]
    budget_limits: Dict[str, int]  # Per-PR limits
    
    @classmethod
    def strict_core(cls) -> 'PolicyPreset':
        """Ultra-strict policy for core business logic."""
        return cls(
            name="strict-core",
            description="Maximum quality for core business logic",
            thresholds=ThresholdConfig(
                max_positional_params=2,
                god_class_methods=15,
                god_class_lines=300,
                max_cyclomatic_complexity=8,
                max_magic_literals_per_function=3,
            ),
            weights=WeightConfig(
                core_code_multiplier=3.0,
                cross_module_multiplier=8.0,
            ),
            enabled_analyzers=["ast", "runtime"],
            budget_limits={
                "CoM": 5,   # Max 5 new magic literals per PR
                "CoP": 3,   # Max 3 new position violations
                "CoA": 2,   # Max 2 new algorithm duplications
            }
        )
    
    @classmethod  
    def service_defaults(cls) -> 'PolicyPreset':
        """Balanced policy for typical services."""
        return cls(
            name="service-defaults", 
            description="Balanced quality for typical microservices",
            thresholds=ThresholdConfig(),  # Use defaults
            weights=WeightConfig(),
            enabled_analyzers=["ast"],
            budget_limits={
                "CoM": 15,
                "CoP": 10, 
                "CoA": 8,
                "total": 50,  # Total new violations
            }
        )
    
    @classmethod
    def experimental(cls) -> 'PolicyPreset':
        """Relaxed policy for experimental/prototype code."""
        return cls(
            name="experimental",
            description="Relaxed policy for prototypes and experiments",
            thresholds=ThresholdConfig(
                max_positional_params=5,
                god_class_methods=30,
                max_cyclomatic_complexity=15,
                magic_literal_density_threshold=0.5,  # 50%
            ),
            weights=WeightConfig(
                experimental_multiplier=0.1,
            ),
            enabled_analyzers=["ast"],
            budget_limits={
                "total": 100,  # Very high limit
            }
        )


# Default configurations
DEFAULT_THRESHOLDS = ThresholdConfig()
DEFAULT_WEIGHTS = WeightConfig() 
DEFAULT_PRESETS = {
    "strict-core": PolicyPreset.strict_core(),
    "service-defaults": PolicyPreset.service_defaults(),
    "experimental": PolicyPreset.experimental(),
}


def get_severity_for_violation(
    connascence_type: ConnascenceType,
    locality: str,
    context: Optional[Dict] = None
) -> Severity:
    """Determine severity based on connascence type, locality, and context."""
    
    # Critical: Identity/timing violations are always serious
    if connascence_type in [ConnascenceType.IDENTITY, ConnascenceType.TIMING]:
        return Severity.CRITICAL
    
    # Critical: Cross-module algorithm duplication
    if connascence_type == ConnascenceType.ALGORITHM and locality == "cross_module":
        return Severity.CRITICAL
    
    # High: Cross-module static violations
    if locality == "cross_module" and connascence_type in [
        ConnascenceType.POSITION, ConnascenceType.MEANING
    ]:
        return Severity.HIGH
    
    # High: Security-related magic literals
    if (connascence_type == ConnascenceType.MEANING and 
        context and any(keyword in str(context).lower() 
                       for keyword in ["password", "secret", "key", "token", "auth"])):
        return Severity.HIGH
    
    # Medium: Most other violations
    if connascence_type in [ConnascenceType.MEANING, ConnascenceType.POSITION, 
                           ConnascenceType.ALGORITHM]:
        return Severity.MEDIUM
    
    # Low: Name/Type violations
    return Severity.LOW


def calculate_violation_weight(
    connascence_type: ConnascenceType,
    severity: Severity, 
    locality: str,
    file_path: str,
    weights: WeightConfig = None
) -> float:
    """Calculate the weighted score for a violation."""
    
    if weights is None:
        weights = DEFAULT_WEIGHTS
    
    # Base weight from type and severity
    base_weight = weights.type_weights[connascence_type] * weights.severity_weights[severity]
    
    # Locality multiplier
    locality_multiplier = {
        "same_function": weights.same_function_multiplier,
        "same_class": weights.same_class_multiplier,
        "same_module": weights.same_module_multiplier,
        "cross_module": weights.cross_module_multiplier,
    }.get(locality, weights.same_module_multiplier)
    
    # Directory-based multiplier  
    path_lower = file_path.lower()
    if any(segment in path_lower for segment in ["/core", "/src"]):
        dir_multiplier = weights.core_code_multiplier
    elif "/test" in path_lower:
        dir_multiplier = weights.test_code_multiplier
    elif "/config" in path_lower:
        dir_multiplier = weights.config_code_multiplier
    elif "/experimental" in path_lower:
        dir_multiplier = weights.experimental_multiplier
    else:
        dir_multiplier = 1.0
    
    return base_weight * locality_multiplier * dir_multiplier


# Rationale documentation
THRESHOLD_RATIONALE = {
    "max_positional_params": (
        "3 positional parameters max. Beyond this, parameter order becomes "
        "a significant source of coupling and errors. Use keyword arguments "
        "or data classes for complex parameter sets."
    ),
    "god_class_methods": (
        "20 methods per class max. Classes with more methods likely violate "
        "Single Responsibility Principle and should be split into focused, "
        "cohesive classes."
    ),
    "max_cyclomatic_complexity": (
        "10 complexity max per function. Higher complexity makes testing "
        "exponentially harder and indicates functions doing too much."
    ),
    "magic_literal_density_threshold": (
        "25% magic literal density max. Files with higher ratios of magic "
        "literals to total literals are harder to maintain and configure."
    ),
}


def explain_threshold(threshold_name: str) -> str:
    """Get explanation for why a threshold is set to its current value."""
    return THRESHOLD_RATIONALE.get(
        threshold_name, 
        f"No rationale documented for threshold: {threshold_name}"
    )