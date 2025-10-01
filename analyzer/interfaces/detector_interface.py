"""
Detector Interface - Eliminates Connascence of Name and Position
===============================================================

Standardized interfaces that reduce coupling between detector components
and ensure consistent method signatures across all detectors.
"""

from fixes.phase0.production_safe_assertions import ProductionAssert
import ast
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Protocol
from dataclasses import dataclass

from utils.types import ConnascenceViolation


@dataclass  
class AnalysisContext:
    """
    Context object that reduces Connascence of Position by bundling
    related parameters into a single, well-structured object.
    """
    file_path: str
    source_lines: List[str]
    policy: str = "standard" 
    options: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.options is None:
            self.options = {}
        if self.metadata is None:
            self.metadata = {}


@dataclass
class DetectorResult:
    """
    Standardized result object that eliminates result format variations
    and reduces Connascence of Type across detector implementations.
    """
    violations: List[ConnascenceViolation]
    metadata: Dict[str, Any]
    processing_time_ms: Optional[int] = None
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
            
    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)
    
    def has_errors(self) -> bool:
        """Check if result has any errors."""
        return bool(self.errors)
    
    def get_violation_count(self) -> int:
        """Get total violation count."""
        return len(self.violations)


class DetectorProtocol(Protocol):
    """
    Protocol that defines the standard detector interface.
    This eliminates Connascence of Name by establishing consistent
    method signatures across all detector implementations.
    """
    
    def detect_violations(self, tree: ast.AST, context: AnalysisContext) -> DetectorResult:
        """Detect violations in AST with context."""
        ...
    
    def get_supported_violation_types(self) -> List[str]:
        """Get list of violation types this detector can find."""
        ...


class StandardDetectorInterface(ABC):
    """
    Abstract base class that standardizes detector interfaces and reduces
    Connascence of Position through consistent parameter ordering.
    """
    
    def __init__(self, context: AnalysisContext):
        """
        Initialize detector with analysis context.
        Eliminates Connascence of Position in constructor parameters.
        """
        self.context = context
        self.violations: List[ConnascenceViolation] = []
    
    @abstractmethod
    def detect_violations(self, tree: ast.AST) -> DetectorResult:
        """
        Main detection method with standardized signature.
        
        Args:
            tree: AST tree to analyze
            
        Returns:
            DetectorResult with violations and metadata
        """
        pass
    
    @abstractmethod
    def get_supported_violation_types(self) -> List[str]:
        """
        Get list of connascence types this detector handles.
        
        Returns:
            List of violation type strings
        """
        pass
    
    def get_code_snippet(self, node: ast.AST, context_lines: int = 2) -> str:
        """
        Get code snippet around a node for violation reporting.
        Standardized method reduces algorithm duplication.
        """
        if not hasattr(node, 'lineno') or node.lineno <= 0:
            return ""
        
        try:
            start_line = max(0, node.lineno - context_lines - 1)
            end_line = min(len(self.context.source_lines), node.lineno + context_lines)
            
            lines = self.context.source_lines[start_line:end_line]
            return '\n'.join(lines)
        except (IndexError, AttributeError):
            return ""
    
    def get_line_content(self, node: ast.AST) -> str:
        """
        Get the content of the line containing a node.
        Standardized method reduces code duplication.
        """
        if not hasattr(node, 'lineno') or node.lineno <= 0:
            return ""
        
        try:
            line_index = node.lineno - 1
            if 0 <= line_index < len(self.context.source_lines):
                return self.context.source_lines[line_index]
        except (IndexError, AttributeError):
            pass
        
        return ""
    
    def create_violation(
        self,
        violation_type: str,
        severity: str,
        node: ast.AST,
        description: str,
        recommendation: str,
        context_data: Optional[Dict[str, Any]] = None
    ) -> ConnascenceViolation:
        """
        Create a standardized violation object.
        Eliminates variation in violation creation across detectors.
        """
        return ConnascenceViolation(
            type=violation_type,
            severity=severity,
            file_path=self.context.file_path,
            line_number=getattr(node, 'lineno', 0),
            column=getattr(node, 'col_offset', 0),
            description=description,
            recommendation=recommendation,
            code_snippet=self.get_code_snippet(node),
            context=context_data or {}
        )


class ConfigurableDetectorMixin:
    """
    Mixin that provides configuration management for detectors.
    Eliminates hardcoded configuration values and provides
    standardized configuration access.
    """
    
    def __init__(self):
        from ..utils.config_manager import get_detector_config
        self._detector_config = None
        self._detector_name = self.__class__.__name__.lower().replace('detector', '_detector')
    
    def get_config(self):
        """Get detector-specific configuration."""
        if self._detector_config is None:
            from ..utils.config_manager import get_detector_config
            self._detector_config = get_detector_config(self._detector_name)
        return self._detector_config
    
    def get_threshold(self, threshold_name: str, default_value: Any = None) -> Any:
        """Get a threshold value from configuration."""
        config = self.get_config()
        return config.thresholds.get(threshold_name, default_value)
    
    def get_exclusions(self, exclusion_type: str) -> List[Any]:
        """Get exclusion list from configuration."""
        config = self.get_config()
        return config.exclusions.get(exclusion_type, [])
    
    def is_excluded_value(self, value: Any, exclusion_type: str) -> bool:
        """Check if a value should be excluded from analysis."""
        exclusions = self.get_exclusions(exclusion_type)
        return value in exclusions


class DetectorFactory:
    """
    Factory class that eliminates direct detector instantiation coupling
    and provides centralized detector creation with consistent configuration.
    """
    
    _detector_registry: Dict[str, type] = {}
    
    @classmethod
    def register_detector(cls, violation_type: str, detector_class: type) -> None:
        """Register a detector class for a specific violation type."""
        cls._detector_registry[violation_type] = detector_class
    
    @classmethod
    def create_detector(cls, violation_type: str, context: AnalysisContext) -> Optional[StandardDetectorInterface]:
        """
        Create a detector instance for a specific violation type.
        
        Args:
            violation_type: Type of connascence to detect
            context: Analysis context
            
        Returns:
            Detector instance or None if not found
        """
        detector_class = cls._detector_registry.get(violation_type)
        if detector_class:
            return detector_class(context)
        return None
    
    @classmethod
    def get_available_detectors(cls) -> List[str]:
        """Get list of available detector types."""
        return list(cls._detector_registry.keys())
    
    @classmethod
    def create_all_detectors(cls, context: AnalysisContext) -> List[StandardDetectorInterface]:
        """Create instances of all registered detectors."""
        detectors = []
        for violation_type in cls._detector_registry:
            detector = cls.create_detector(violation_type, context)
            if detector:
                detectors.append(detector)
        return detectors


class AnalysisOrchestrator:
    """
    Orchestrator that manages detector execution and reduces
    Connascence of Execution by standardizing the analysis workflow.
    """
    
    def __init__(self, context: AnalysisContext):
        self.context = context
        self.detectors = DetectorFactory.create_all_detectors(context)
    
    def run_analysis(self, tree: ast.AST) -> List[DetectorResult]:
        """
        Run all detectors on the provided AST tree.
        
        Args:
            tree: AST tree to analyze
            
        Returns:
            List of detector results
        """
        results = []
        
        for detector in self.detectors:
            try:
                result = detector.detect_violations(tree)
                results.append(result)
            except Exception as e:
                # Create error result for failed detector
                error_result = DetectorResult(
                    violations=[],
                    metadata={'detector_error': str(e)},
                    errors=[f"Detector {detector.__class__.__name__} failed: {e}"]
                )
                results.append(error_result)
        
        return results
    
    def get_aggregated_violations(self, tree: ast.AST) -> List[ConnascenceViolation]:
        """
        Get all violations from all detectors in a single list.
        
        Args:
            tree: AST tree to analyze
            
        Returns:
            Aggregated list of violations
        """
        all_violations = []
        results = self.run_analysis(tree)
        
        for result in results:
            all_violations.extend(result.violations)
        
        return all_violations


# Decorator for automatic detector registration
def register_detector(violation_type: str):
    """
    Decorator that automatically registers detectors with the factory.
    Eliminates manual registration coupling.
    """
    ProductionAssert.not_none(violation_type, 'violation_type')

    ProductionAssert.not_none(violation_type, 'violation_type')

    def decorator(detector_class):

        ProductionAssert.not_none(detector_class, 'detector_class')

        ProductionAssert.not_none(detector_class, 'detector_class')

        DetectorFactory.register_detector(violation_type, detector_class)
        return detector_class
    return decorator


# Common violation severity constants to eliminate magic strings
class ViolationSeverity:
    """Constants for violation severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Common connascence type constants
class ConnascenceType:
    """Constants for connascence types to eliminate magic strings."""
    NAME = "connascence_of_name"
    TYPE = "connascence_of_type"
    MEANING = "connascence_of_meaning"
    POSITION = "connascence_of_position"
    ALGORITHM = "connascence_of_algorithm"
    EXECUTION = "connascence_of_execution"
    TIMING = "connascence_of_timing"
    VALUES = "connascence_of_values"
    IDENTITY = "connascence_of_identity"