"""
Mock MCP Server implementation for test compatibility.
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional


# Mock ConnascenceViolation for removed analyzer dependency
class ConnascenceViolation:
    def __init__(self, id=None, rule_id=None, connascence_type=None, severity=None, 
                 description=None, file_path=None, line_number=None, weight=None, type=None, **kwargs):
        self.id = id
        self.rule_id = rule_id
        self.connascence_type = connascence_type or type
        self.type = type or connascence_type
        self.severity = severity
        self.description = description
        self.file_path = file_path
        self.line_number = line_number
        self.weight = weight
        for k, v in kwargs.items():
            setattr(self, k, v)


# MCP Server Configuration Constants (CoM Improvement - Pass 2)
DEFAULT_RATE_LIMIT_REQUESTS = 100
DEFAULT_RATE_LIMIT_WINDOW_SECONDS = 60
DEFAULT_AUDIT_ENABLED = True

class RateLimiter:
    """Rate limiter for MCP server."""
    def __init__(self, max_requests=DEFAULT_RATE_LIMIT_REQUESTS, window_seconds=DEFAULT_RATE_LIMIT_WINDOW_SECONDS):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        # Clean old requests
        self.requests[client_id] = [req_time for req_time in self.requests[client_id] 
                                   if now - req_time < self.window_seconds]
        
        # Check if within limit
        if len(self.requests[client_id]) < self.max_requests:
            self.requests[client_id].append(now)
            return True
        return False
    
    def check_rate_limit(self, client_id: str = 'default') -> bool:
        """Check if client is within rate limits."""
        return self.is_allowed(client_id)

class AuditLogger:
    """Audit logger for MCP server."""
    def __init__(self, enabled=True):
        self.logs = []
        self.enabled = enabled
    
    def log(self, event: str, details: Dict[str, Any] = None):
        if self.enabled:
            self.logs.append({
                'timestamp': time.time(),
                'event': event,
                'details': details or {}
            })
    
    def log_request(self, tool_name: str, timestamp: float = None, **kwargs):
        """Log tool request."""
        self.log('tool_request', {
            'tool_name': tool_name,
            'timestamp': timestamp or time.time(),
            **kwargs
        })

class ConnascenceMCPServer:
    """Mock MCP server for connascence analysis."""
    def __init__(self, config=None):
        self.config = config or {}
        self.name = "connascence"
        self.version = "2.0.0"  # Updated version to match test expectations
        
        # Initialize components with custom config
        rate_limit = self.config.get('max_requests_per_minute', DEFAULT_RATE_LIMIT_REQUESTS)
        self.rate_limiter = RateLimiter(max_requests=rate_limit)
        
        audit_enabled = self.config.get('enable_audit_logging', DEFAULT_AUDIT_ENABLED)
        self.audit_logger = AuditLogger(enabled=audit_enabled)
        
        # Path restrictions
        self.allowed_paths = self.config.get('allowed_paths', [])
        
        self.analyzer = self._create_analyzer()
        self._tools = self._register_tools()
    
    def _create_analyzer(self):
        """Create mock analyzer instance for tests."""
        
        class MockAnalyzer:
            def __init__(self):
                pass
            
            def analyze_path(self, path, profile=None):
                """Mock analyze_path method."""
                return {
                    'violations': [
                        ConnascenceViolation(
                            id="mock_violation_1",
                            rule_id="CON_CoM", 
                            connascence_type="CoM",
                            severity="medium",
                            description="Mock magic literal violation",
                            file_path=str(path),
                            line_number=1,
                            weight=2.0
                        )
                    ],
                    'metrics': {
                        'files_analyzed': 1,
                        'violations_found': 1,
                        'analysis_time': 0.1
                    }
                }
            
            def analyze_directory(self, path, profile=None):
                """Mock analyze_directory method for test compatibility."""
                return {
                    'violations': [
                        ConnascenceViolation(
                            id="mock_dir_violation_1",
                            rule_id="CON_CoP", 
                            connascence_type="CoP",
                            severity="high",
                            description="Mock parameter violation",
                            file_path=f"{path}/mock_file.py",
                            line_number=10,
                            weight=3.0
                        ),
                        ConnascenceViolation(
                            id="mock_dir_violation_2",
                            rule_id="CON_CoM", 
                            connascence_type="CoM",
                            severity="medium",
                            description="Mock magic literal",
                            file_path=f"{path}/another_file.py",
                            line_number=5,
                            weight=2.0
                        )
                    ],
                    'metrics': {
                        'files_analyzed': 2,
                        'violations_found': 2,
                        'analysis_time': 0.3
                    }
                }
        
        return MockAnalyzer()
    
    def _register_tools(self):
        """Register available MCP tools."""
        tools = {
            'scan_path': {
                'name': 'scan_path',
                'description': 'Analyze a file or directory for connascence violations',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'path': {'type': 'string'},
                        'policy': {'type': 'string', 'default': 'default'}
                    },
                    'required': ['path']
                }
            },
            'explain_finding': {
                'name': 'explain_finding',
                'description': 'Explain a connascence violation in detail',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'violation_id': {'type': 'string'},
                        'context': {'type': 'object'}
                    },
                    'required': ['violation_id']
                }
            },
            'propose_autofix': {
                'name': 'propose_autofix',
                'description': 'Propose automated fixes for violations',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'violations': {'type': 'array'},
                        'safety_level': {'type': 'string', 'default': 'conservative'}
                    },
                    'required': ['violations']
                }
            }
        }
        return tools
    
    def get_tools(self):
        """Return list of available tools."""
        return list(self._tools.values())
    
    def validate_path(self, path: str) -> bool:
        """Validate if path is allowed."""
        if not self.allowed_paths:
            return True  # No restrictions
        
        path_obj = Path(path).resolve()
        for allowed in self.allowed_paths:
            allowed_path = Path(allowed).resolve()
            try:
                path_obj.relative_to(allowed_path)
                return True
            except ValueError:
                continue
        return False
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any], client_id: str = 'default'):
        """Execute a tool with given arguments."""
        # Rate limiting check
        if not self.rate_limiter.check_rate_limit(client_id):
            raise Exception("Rate limit exceeded")
        
        # Audit logging
        self.audit_logger.log_request(tool_name, client_id=client_id)
        
        if tool_name == 'scan_path':
            return self._execute_scan_path(arguments)
        elif tool_name == 'explain_finding':
            return self._execute_explain_finding(arguments)
        elif tool_name == 'propose_autofix':
            return self._execute_propose_autofix(arguments)
        else:
            raise Exception(f"Unknown tool: {tool_name}")
    
    def _execute_scan_path(self, arguments: Dict[str, Any]):
        """Execute scan_path tool."""
        path = arguments.get('path')
        policy = arguments.get('policy', 'default')
        
        if not path:
            raise ValueError("Path is required")
        
        if not self.validate_path(path):
            raise ValueError(f"Path not allowed: {path}")
        
        path_obj = Path(path)
        if path_obj.is_dir():
            result = self.analyzer.analyze_directory(path, profile=policy)
        else:
            result = self.analyzer.analyze_path(path, profile=policy)
        
        return {
            'success': True,
            'path': path,
            'policy': policy,
            'violations': [self._violation_to_dict(v) for v in result['violations']],
            'metrics': result.get('metrics', {}),
            'timestamp': time.time()
        }
    
    def _execute_explain_finding(self, arguments: Dict[str, Any]):
        """Execute explain_finding tool."""
        violation_id = arguments.get('violation_id')
        context = arguments.get('context', {})
        
        return {
            'success': True,
            'violation_id': violation_id,
            'explanation': {
                'type': 'Mock Explanation',
                'description': f'This is a mock explanation for violation {violation_id}',
                'impact': 'Medium coupling detected',
                'suggestions': [
                    'Extract constant to reduce connascence of meaning',
                    'Use configuration object instead of magic literals'
                ]
            },
            'context': context
        }
    
    def _execute_propose_autofix(self, arguments: Dict[str, Any]):
        """Execute propose_autofix tool."""
        violations = arguments.get('violations', [])
        safety_level = arguments.get('safety_level', 'conservative')
        
        fixes = []
        for violation in violations:
            fixes.append({
                'violation_id': violation.get('id', 'unknown'),
                'fix_type': 'extract_constant',
                'description': 'Extract magic literal to named constant',
                'safety_score': 0.8,
                'estimated_effort': 'low'
            })
        
        return {
            'success': True,
            'fixes': fixes,
            'safety_level': safety_level,
            'total_fixes': len(fixes)
        }
    
    def _violation_to_dict(self, violation):
        """Convert violation to dictionary format."""
        if hasattr(violation, 'id'):
            return {
                'id': violation.id,
                'rule_id': violation.rule_id,
                'type': violation.connascence_type,
                'severity': violation.severity,
                'description': violation.description,
                'file_path': violation.file_path,
                'line_number': violation.line_number,
                'weight': violation.weight
            }
        else:
            return violation
    
    def get_metrics(self):
        """Get server metrics."""
        return {
            'requests_processed': sum(len(reqs) for reqs in self.rate_limiter.requests.values()),
            'rate_limit_violations': 0,
            'audit_logs': len(self.audit_logger.logs),
            'uptime': time.time()
        }
    
    def get_info(self):
        """Get server information."""
        return {
            'name': self.name,
            'version': self.version,
            'tools': list(self._tools.keys()),
            'config': {
                'rate_limit': self.rate_limiter.max_requests,
                'audit_enabled': self.audit_logger.enabled,
                'path_restrictions': len(self.allowed_paths) > 0
            }
        }


# Tool class for compatibility
class MCPConnascenceTool:
    """Mock MCP Connascence Tool."""
    def __init__(self, name: str, server: ConnascenceMCPServer):
        self.name = name
        self.server = server
        self.description = f"Mock tool {name}"
        self.input_schema = {"type": "object", "properties": {}}
    
    def execute(self, arguments: Dict[str, Any]):
        """Execute the tool."""
        return self.server.execute_tool(self.name, arguments)
    
    def validate(self, arguments: Dict[str, Any]) -> bool:
        """Validate tool arguments."""
        return True  # Mock validation always passes
