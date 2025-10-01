"""
Centralized Error Handling - Eliminates Connascence of Algorithm
================================================================

Standardized error handling patterns that eliminate duplicate error handling
algorithms across the analyzer system and provide consistent error responses.
"""

from fixes.phase0.production_safe_assertions import ProductionAssert
import logging
import traceback
from typing import Any, Dict, List, Optional, Callable, Type
from dataclasses import dataclass
from enum import Enum
import time
from functools import wraps

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Standardized error severity levels."""
    CRITICAL = "critical"
    HIGH = "high" 
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ErrorCategory(Enum):
    """Error categories for classification."""
    ANALYSIS = "analysis"
    CONFIGURATION = "configuration"
    FILE_IO = "file_io"
    PARSING = "parsing"
    VALIDATION = "validation"
    DEPENDENCY = "dependency"
    INTERNAL = "internal"


@dataclass
class AnalysisError:
    """Standardized error object for analysis failures."""
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    component: Optional[str] = None
    exception_type: Optional[str] = None
    traceback_info: Optional[str] = None
    timestamp: Optional[float] = None
    context: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.context is None:
            self.context = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for serialization."""
        return {
            'category': self.category.value,
            'severity': self.severity.value,
            'message': self.message,
            'file_path': self.file_path,
            'line_number': self.line_number,
            'component': self.component,
            'exception_type': self.exception_type,
            'traceback': self.traceback_info,
            'timestamp': self.timestamp,
            'context': self.context
        }


class ErrorHandler:
    """
    Centralized error handler that eliminates duplicate error handling patterns
    and provides consistent error management across all analyzer components.
    """
    
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.errors: List[AnalysisError] = []
        self.warnings: List[AnalysisError] = []
    
    def handle_exception(
        self,
        exception: Exception,
        category: ErrorCategory,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        include_traceback: bool = True
    ) -> AnalysisError:
        """
        Handle an exception with standardized error creation.
        
        Args:
            exception: The exception that occurred
            category: Category of the error
            severity: Severity level
            file_path: File where error occurred
            line_number: Line number where error occurred
            context: Additional context information
            include_traceback: Whether to include traceback info
            
        Returns:
            Created AnalysisError object
        """
        traceback_info = None
        if include_traceback:
            traceback_info = traceback.format_exc()
        
        error = AnalysisError(
            category=category,
            severity=severity,
            message=str(exception),
            file_path=file_path,
            line_number=line_number,
            component=self.component_name,
            exception_type=type(exception).__name__,
            traceback_info=traceback_info,
            context=context
        )
        
        # Store error based on severity
        if severity in (ErrorSeverity.CRITICAL, ErrorSeverity.HIGH):
            self.errors.append(error)
        else:
            self.warnings.append(error)
        
        # Log error
        self._log_error(error)
        
        return error
    
    def create_error(
        self,
        message: str,
        category: ErrorCategory,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AnalysisError:
        """
        Create a custom error without an exception.
        
        Args:
            message: Error message
            category: Category of the error
            severity: Severity level
            file_path: File where error occurred
            line_number: Line number where error occurred
            context: Additional context information
            
        Returns:
            Created AnalysisError object
        """
        error = AnalysisError(
            category=category,
            severity=severity,
            message=message,
            file_path=file_path,
            line_number=line_number,
            component=self.component_name,
            context=context
        )
        
        # Store error based on severity
        if severity in (ErrorSeverity.CRITICAL, ErrorSeverity.HIGH):
            self.errors.append(error)
        else:
            self.warnings.append(error)
        
        # Log error
        self._log_error(error)
        
        return error
    
    def _log_error(self, error: AnalysisError) -> None:
        """Log error with appropriate level."""
        log_message = f"[{error.component}] {error.message}"
        
        if error.file_path:
            log_message += f" (File: {error.file_path}"
            if error.line_number:
                log_message += f":{error.line_number}"
            log_message += ")"
        
        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif error.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        elif error.severity == ErrorSeverity.LOW:
            logger.info(log_message)
        else:
            logger.debug(log_message)
    
    def has_errors(self) -> bool:
        """Check if any errors were recorded."""
        return len(self.errors) > 0
    
    def has_critical_errors(self) -> bool:
        """Check if any critical errors were recorded."""
        return any(error.severity == ErrorSeverity.CRITICAL for error in self.errors)
    
    def get_all_errors(self) -> List[AnalysisError]:
        """Get all errors and warnings."""
        return self.errors + self.warnings
    
    def get_errors_by_category(self, category: ErrorCategory) -> List[AnalysisError]:
        """Get errors by category."""
        all_errors = self.get_all_errors()
        return [error for error in all_errors if error.category == category]
    
    def get_error_summary(self) -> Dict[str, int]:
        """Get summary of error counts by severity."""
        all_errors = self.get_all_errors()
        summary = {}
        
        for severity in ErrorSeverity:
            count = sum(1 for error in all_errors if error.severity == severity)
            summary[severity.value] = count
        
        return summary
    
    def clear_errors(self) -> None:
        """Clear all recorded errors and warnings."""
        self.errors.clear()
        self.warnings.clear()


class SafeExecutionMixin:
    """
    Mixin that provides safe execution patterns for detector methods.
    Eliminates duplicate try-catch patterns across detector implementations.
    """
    
    def __init__(self):
        if not hasattr(self, '_error_handler'):
            component_name = getattr(self, '__class__', type(self)).__name__
            self._error_handler = ErrorHandler(component_name)
    
    def safe_execute(
        self,
        operation: Callable,
        error_category: ErrorCategory,
        error_severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        default_return=None,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Execute operation safely with standardized error handling.
        
        Args:
            operation: Function to execute safely
            error_category: Category of potential errors
            error_severity: Severity level for errors
            default_return: Value to return on error
            context: Additional context for error reporting
            
        Returns:
            Operation result or default value on error
        """
        try:
            return operation()
        except Exception as e:
            self._error_handler.handle_exception(
                e, error_category, error_severity, context=context
            )
            return default_return
    
    def safe_parse_ast(self, source_code: str, file_path: str):
        """Safely parse source code to AST with standardized error handling."""
    
        ProductionAssert.not_none(source_code, 'source_code')
    
        ProductionAssert.not_none(file_path, 'file_path')

    
        ProductionAssert.not_none(source_code, 'source_code')
    
        ProductionAssert.not_none(file_path, 'file_path')

        import ast
        
        def parse_operation():
            return ast.parse(source_code)
        
        return self.safe_execute(
            parse_operation,
            ErrorCategory.PARSING,
            ErrorSeverity.HIGH,
            default_return=None,
            context={'file_path': file_path}
        )
    
    def safe_file_read(self, file_path: str, encoding: str = 'utf-8'):
        """Safely read file with standardized error handling."""
    
        ProductionAssert.not_none(file_path, 'file_path')
    
        ProductionAssert.not_none(encoding, 'encoding')

    
        ProductionAssert.not_none(file_path, 'file_path')
    
        ProductionAssert.not_none(encoding, 'encoding')

        def read_operation():
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                lines = content.splitlines()
                return content, lines
        
        return self.safe_execute(
            read_operation,
            ErrorCategory.FILE_IO,
            ErrorSeverity.HIGH,
            default_return=(None, []),
            context={'file_path': file_path, 'encoding': encoding}
        )


# Decorator for automatic error handling
def handle_errors(
    category: ErrorCategory,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    default_return=None,
    log_errors: bool = True
):
    """
    Decorator that automatically handles errors in detector methods.
    Eliminates repetitive error handling code.
    
    Args:
        category: Error category
        severity: Error severity
        default_return: Value to return on error
        log_errors: Whether to log errors
    """
    def decorator(func):
        ProductionAssert.not_none(func, 'func')

        ProductionAssert.not_none(func, 'func')

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if args:
                ProductionAssert.not_none(args, 'args')
            if kwargs:
                ProductionAssert.not_none(kwargs, 'kwargs')

            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                # Get or create error handler
                if not hasattr(self, '_error_handler'):
                    component_name = self.__class__.__name__
                    self._error_handler = ErrorHandler(component_name)
                
                # Handle the error
                error = self._error_handler.handle_exception(
                    e, category, severity,
                    context={'method': func.__name__, 'args': str(args)[:100]}
                )
                
                return default_return
        return wrapper
    return decorator


# Context manager for error boundaries
class ErrorBoundary:
    """
    Context manager that creates error boundaries for operations.
    Eliminates duplicate error boundary patterns.
    """
    
    def __init__(
        self,
        component_name: str,
        category: ErrorCategory = ErrorCategory.ANALYSIS,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        reraise_critical: bool = True
    ):
        self.error_handler = ErrorHandler(component_name)
        self.category = category
        self.severity = severity
        self.reraise_critical = reraise_critical
        self.exception_occurred = False
        self.last_error: Optional[AnalysisError] = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.exception_occurred = True
            self.last_error = self.error_handler.handle_exception(
                exc_val, self.category, self.severity
            )
            
            # Reraise critical errors
            if self.reraise_critical and self.severity == ErrorSeverity.CRITICAL:
                return False
            
            # Suppress non-critical errors
            return True
    
    def get_errors(self) -> List[AnalysisError]:
        """Get all errors that occurred in this boundary."""
        return self.error_handler.get_all_errors()
    
    def has_errors(self) -> bool:
        """Check if errors occurred in this boundary.""" 
        return self.exception_occurred or self.error_handler.has_errors()


# Factory for creating error handlers
class ErrorHandlerFactory:
    """Factory for creating standardized error handlers."""
    
    _handlers: Dict[str, ErrorHandler] = {}
    
    @classmethod
    def get_handler(cls, component_name: str) -> ErrorHandler:
        """Get or create error handler for component."""
        if component_name not in cls._handlers:
            cls._handlers[component_name] = ErrorHandler(component_name)
        return cls._handlers[component_name]
    
    @classmethod
    def clear_handlers(cls) -> None:
        """Clear all cached handlers."""
        cls._handlers.clear()
    
    @classmethod
    def get_global_error_summary(cls) -> Dict[str, Dict[str, int]]:
        """Get error summary across all components."""
        summary = {}
        for component_name, handler in cls._handlers.items():
            summary[component_name] = handler.get_error_summary()
        return summary