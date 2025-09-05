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
Shared configuration utilities for the Connascence Safety Analyzer.

Provides common configuration loading and mock classes used across components.
"""

from typing import Dict, Any, Optional


class ConnascenceViolation:
    """Mock ConnascenceViolation class for removed analyzer dependency."""
    
    def __init__(self, id=None, rule_id=None, connascence_type=None, severity=None, 
                 description=None, file_path=None, line_number=None, weight=None, 
                 type=None, **kwargs):
        self.id = id
        self.rule_id = rule_id
        self.connascence_type = connascence_type or type
        self.type = type or connascence_type
        self.severity = severity
        self.description = description
        self.file_path = file_path
        self.line_number = line_number
        self.weight = weight
        self.context = kwargs.get('context', {})
        
        # Set additional attributes from kwargs
        for k, v in kwargs.items():
            if not hasattr(self, k):
                setattr(self, k, v)


class ThresholdConfig:
    """Mock ThresholdConfig class for removed analyzer dependency."""
    
    def __init__(self, max_positional_params=3, god_class_methods=20, max_cyclomatic_complexity=10):
        self.max_positional_params = max_positional_params
        self.god_class_methods = god_class_methods
        self.max_cyclomatic_complexity = max_cyclomatic_complexity


class RateLimiter:
    """Rate limiter utility class."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []
    
    def is_allowed(self) -> bool:
        """Check if a request is allowed."""
        import time
        now = time.time()
        
        # Remove old requests outside the window
        self.requests = [req_time for req_time in self.requests if now - req_time < self.window_seconds]
        
        # Check if we're under the limit
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False


def load_config_defaults(component_name: str) -> Dict[str, Any]:
    """Load default configuration values for a component."""
    
    # Common configuration defaults across components
    base_defaults = {
        'rate_limit_requests': 100,
        'rate_limit_window_seconds': 60,
        'audit_enabled': True,
        'max_positional_params': 4,
        'god_class_methods': 25,
        'max_cyclomatic_complexity': 12
    }
    
    # Component-specific defaults
    component_defaults = {
        'mcp_server': {
            'rate_limit_requests': 100,
            'rate_limit_window_seconds': 60,
            'audit_enabled': True,
        },
        'policy_manager': {
            'max_positional_params': 2,
            'god_class_methods': 15,
            'max_cyclomatic_complexity': 8,
            'com_limit': 3,
            'cop_limit': 2,
            'total_violations_limit': 10,
        },
        'policy_budgets': {
            'max_positional_params': 4,
            'god_class_methods': 25,
            'max_cyclomatic_complexity': 12,
        }
    }
    
    config = base_defaults.copy()
    if component_name in component_defaults:
        config.update(component_defaults[component_name])
    
    return config


def create_rate_limiter(config: Optional[Dict[str, Any]] = None) -> RateLimiter:
    """Create a rate limiter with default or custom configuration."""
    if config is None:
        config = {}
    
    max_requests = config.get('rate_limit_requests', 100)
    window_seconds = config.get('rate_limit_window_seconds', 60)
    
    return RateLimiter(max_requests, window_seconds)