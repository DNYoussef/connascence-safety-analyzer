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
Error Sanitization Module

Prevents information leakage through error messages by sanitizing
sensitive information before exposing errors to users.
"""

import re
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ErrorSanitizer:
    """Sanitizes error messages to prevent information disclosure."""
    
    # Sensitive patterns that should be redacted
    SENSITIVE_PATTERNS = [
        # File paths
        (r'[A-Z]:\\[^\\]+(?:\\[^\\]+)*', '[REDACTED_PATH]'),
        (r'/[^/\s]+(?:/[^/\s]+)*', '[REDACTED_PATH]'),
        
        # Database connections
        (r'postgresql://[^@]+@[^/]+/\w+', 'postgresql://[REDACTED]'),
        (r'mysql://[^@]+@[^/]+/\w+', 'mysql://[REDACTED]'),
        (r'sqlite:///[^\s]+', 'sqlite:///[REDACTED]'),
        
        # API keys and tokens
        (r'\b[A-Za-z0-9]{20,}\b', '[REDACTED_TOKEN]'),
        (r'Bearer\s+[A-Za-z0-9\-_=.]+', 'Bearer [REDACTED]'),
        (r'token["\']?\s*[:=]\s*["\']?[A-Za-z0-9\-_=.]+', 'token=[REDACTED]'),
        
        # IP addresses (internal ranges)
        (r'\b192\.168\.\d{1,3}\.\d{1,3}\b', '[REDACTED_IP]'),
        (r'\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[REDACTED_IP]'),
        (r'\b172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}\b', '[REDACTED_IP]'),
        
        # Usernames in paths
        (r'/home/[^/\s]+', '/home/[REDACTED_USER]'),
        (r'C:\\Users\\[^\\]+', 'C:\\Users\\[REDACTED_USER]'),
        
        # Email addresses
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[REDACTED_EMAIL]'),
        
        # Version information that might be sensitive
        (r'Python \d+\.\d+\.\d+', 'Python [VERSION]'),
        (r'version \d+\.\d+(?:\.\d+)?', 'version [VERSION]'),
        
        # Stack trace file references (keep only filename)
        (r'File "([^"]+[/\\])([^/\\]+)"', r'File "\2"'),
    ]
    
    # Common error categories with user-friendly messages
    ERROR_CATEGORIES = {
        'FileNotFoundError': 'The requested file could not be found.',
        'PermissionError': 'Access denied. Insufficient permissions.',
        'ConnectionError': 'Unable to establish connection to the service.',
        'TimeoutError': 'The operation timed out. Please try again.',
        'ValueError': 'Invalid input provided. Please check your data.',
        'KeyError': 'Required information is missing.',
        'ImportError': 'A required component is not available.',
        'ModuleNotFoundError': 'A required component is not available.',
        'AttributeError': 'The requested operation is not supported.',
        'TypeError': 'Invalid data type provided.',
        'IndexError': 'The requested item is not available.',
        'OSError': 'A system error occurred.',
        'RuntimeError': 'An unexpected error occurred during processing.',
        'IOError': 'Input/output error occurred.',
        'MemoryError': 'Insufficient memory to complete the operation.',
    }
    
    @classmethod
    def sanitize_error_message(cls, error: Exception, include_type: bool = False, 
                             development_mode: bool = False) -> str:
        """
        Sanitize error message for safe display to users.
        
        Args:
            error: The exception to sanitize
            include_type: Whether to include the error type
            development_mode: If True, provides more detailed (but still safe) messages
            
        Returns:
            Sanitized error message safe for user display
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        if development_mode:
            # In development, provide more detail but still sanitize sensitive data
            sanitized_message = cls._sanitize_sensitive_data(error_message)
            
            if include_type:
                return f"{error_type}: {sanitized_message}"
            return sanitized_message
        else:
            # In production, use generic user-friendly messages
            user_message = cls.ERROR_CATEGORIES.get(error_type, 'An error occurred while processing your request.')
            
            if include_type:
                return f"{error_type}: {user_message}"
            return user_message
    
    @classmethod
    def _sanitize_sensitive_data(cls, message: str) -> str:
        """Remove sensitive information from error message."""
        sanitized = message
        
        for pattern, replacement in cls.SENSITIVE_PATTERNS:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    @classmethod
    def create_safe_error_response(cls, error: Exception, error_id: Optional[str] = None,
                                 development_mode: bool = False) -> Dict[str, Any]:
        """
        Create a safe error response dictionary.
        
        Args:
            error: The exception to create response for
            error_id: Optional error ID for tracking
            development_mode: Whether to include development details
            
        Returns:
            Safe error response dictionary
        """
        error_type = type(error).__name__
        
        response = {
            'error': True,
            'error_type': error_type,
            'message': cls.sanitize_error_message(error, development_mode=development_mode),
            'timestamp': None  # Will be set by caller
        }
        
        if error_id:
            response['error_id'] = error_id
        
        if development_mode:
            # Include sanitized details for development
            response['details'] = cls._sanitize_sensitive_data(str(error))
        
        # Log the full error details securely (for debugging)
        logger.error(f"Error {error_id or 'UNKNOWN'}: {error_type}: {error}", 
                    exc_info=True if development_mode else False)
        
        return response
    
    @classmethod
    def wrap_function_with_safe_errors(cls, func, development_mode: bool = False):
        """
        Decorator to wrap function calls with safe error handling.
        
        Args:
            func: Function to wrap
            development_mode: Whether to use development error messages
            
        Returns:
            Wrapped function that returns safe error responses
        """
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return cls.create_safe_error_response(
                    e, 
                    error_id=f"{func.__name__}_{id(e)}", 
                    development_mode=development_mode
                )
        
        return wrapper


# Security-focused logging formatter
class SecureLogFormatter(logging.Formatter):
    """Custom log formatter that sanitizes sensitive information."""
    
    def format(self, record):
        # Get the original formatted message
        message = super().format(record)
        
        # Sanitize the message
        sanitized = ErrorSanitizer._sanitize_sensitive_data(message)
        
        return sanitized


# Context manager for safe error handling
class SafeErrorContext:
    """Context manager for handling errors with automatic sanitization."""
    
    def __init__(self, operation_name: str, development_mode: bool = False):
        self.operation_name = operation_name
        self.development_mode = development_mode
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Log the error securely
            error_response = ErrorSanitizer.create_safe_error_response(
                exc_val, 
                error_id=f"{self.operation_name}_{id(exc_val)}", 
                development_mode=self.development_mode
            )
            
            logger.error(f"Error in {self.operation_name}: {error_response['message']}")
            
            # Don't suppress the exception, just log it safely
            return False


# Utility functions
def safe_str_representation(obj: Any, max_length: int = 100) -> str:
    """Create a safe string representation of an object."""
    try:
        str_repr = str(obj)
        
        # Truncate if too long
        if len(str_repr) > max_length:
            str_repr = str_repr[:max_length] + "..."
        
        # Sanitize sensitive data
        return ErrorSanitizer._sanitize_sensitive_data(str_repr)
        
    except Exception:
        return f"<{type(obj).__name__} object>"


def log_security_event(event_type: str, details: Dict[str, Any], 
                      severity: str = 'warning') -> None:
    """Log security-related events with sanitized details."""
    # Sanitize all details
    sanitized_details = {}
    for key, value in details.items():
        if isinstance(value, str):
            sanitized_details[key] = ErrorSanitizer._sanitize_sensitive_data(value)
        else:
            sanitized_details[key] = safe_str_representation(value)
    
    log_level = getattr(logging, severity.upper(), logging.WARNING)
    logger.log(log_level, f"Security event: {event_type}", extra={'details': sanitized_details})


# Example usage decorator
def secure_endpoint(development_mode: bool = False):
    """Decorator for API endpoints with secure error handling."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Log security event
                log_security_event('endpoint_error', {
                    'endpoint': func.__name__,
                    'error_type': type(e).__name__,
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys())
                })
                
                # Return safe error response
                return ErrorSanitizer.create_safe_error_response(
                    e, 
                    error_id=f"{func.__name__}_{id(e)}", 
                    development_mode=development_mode
                )
        
        return wrapper
    return decorator