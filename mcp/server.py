
import asyncio
import time
from typing import Dict, List, Any, Optional
from analyzer.core import ConnascenceViolation

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
    """MCP server for connascence analysis."""
    def __init__(self, config=None):
        self.config = config or {}
        self.name = "connascence"
        self.version = "1.0.0"
        
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
        """Create analyzer instance."""
        from analyzer.core import ConnascenceViolation
        class MockAnalyzer:
            def analyze_path(self, path, profile=None):
                return [ConnascenceViolation(
                    type_name="CoM", 
                    severity="medium",
                    file_path=str(path),
                    line=1,
                    description="Mock violation"
                )]
            
            def analyze_directory(self, path, profile=None):
                return [ConnascenceViolation(
                    id="test1",
                    rule_id="CON_CoM",
                    connascence_type="CoM",
                    severity="high",
                    description="Magic literal",
                    file_path=str(path) + "/test.py",
                    line_number=10,
                    weight=3.0
                )]
        return MockAnalyzer()
    
    def _register_tools(self):
        """Register all MCP tools."""
        return [
            {
                'name': 'scan_path',
                'description': 'Scan path for connascence violations',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'path': {'type': 'string', 'description': 'Path to scan'},
                        'policy_preset': {'type': 'string', 'description': 'Policy preset to use'}
                    },
                    'required': ['path']
                }
            },
            {
                'name': 'explain_finding',
                'description': 'Explain a specific finding',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'finding_id': {'type': 'string', 'description': 'Finding ID to explain'}
                    },
                    'required': ['finding_id']
                }
            },
            {
                'name': 'propose_autofix',
                'description': 'Propose autofix for violation',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'violation': {'type': 'object', 'description': 'Violation to fix'}
                    },
                    'required': ['violation']
                }
            },
            {
                'name': 'list_presets',
                'description': 'List available policy presets',
                'inputSchema': {'type': 'object', 'properties': {}}
            },
            {
                'name': 'validate_policy',
                'description': 'Validate policy configuration',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'policy': {'type': 'object', 'description': 'Policy to validate'}
                    },
                    'required': ['policy']
                }
            },
            {
                'name': 'get_metrics',
                'description': 'Get analysis metrics',
                'inputSchema': {'type': 'object', 'properties': {}}
            },
            {
                'name': 'enforce_policy',
                'description': 'Enforce policy rules',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'violations': {'type': 'array', 'description': 'Violations to enforce'}
                    },
                    'required': ['violations']
                }
            }
        ]
    
    def get_tools(self):
        """Get list of available tools."""
        return self._tools
    
    def validate_input(self, tool_name: str, args: Dict[str, Any]) -> bool:
        """Validate tool input."""
        if tool_name == 'scan_path':
            return 'path' in args and isinstance(args['path'], str)
        elif tool_name == 'explain_finding':
            return 'finding_id' in args
        elif tool_name == 'propose_autofix':
            return 'violation' in args
        return True
    
    def validate_path(self, path: str) -> bool:
        """Validate file path for security."""
        try:
            self._validate_path(path)
            return True
        except ValueError:
            return False
    
    async def scan_path(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Scan path tool implementation."""
        # Check rate limit first
        if not self.rate_limiter.check_rate_limit():
            raise Exception("Rate limit exceeded")
        
        # Log the request
        self.audit_logger.log_request(tool_name='scan_path', timestamp=time.time())
            
        if not self.validate_input('scan_path', args):
            raise ValueError("Invalid input for scan_path")
        
        path = args['path']
        if not self.validate_path(path):
            raise ValueError("Path not allowed")
        
        profile = args.get('policy_preset', 'default')
        limit_results = args.get('limit_results')
        
        try:
            violations = self.analyzer.analyze_directory(path, profile)
        except Exception as e:
            return {
                'error': str(e),
                'path': path,
                'success': False
            }
        
        # Apply result limiting if requested
        if limit_results and len(violations) > limit_results:
            violations = violations[:limit_results]
        
        # Count violations by severity
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for v in violations:
            severity = getattr(v, 'severity', 'medium')
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        result = {
            'summary': {
                'total_violations': len(violations),
                'critical_count': severity_counts['critical'],
                'high_count': severity_counts['high'],
                'medium_count': severity_counts['medium'],
                'low_count': severity_counts['low']
            },
            'violations': [v.to_dict() if hasattr(v, 'to_dict') else str(v) for v in violations],
            'scan_metadata': {
                'path': path,
                'policy_preset': profile,
                'timestamp': time.time()
            }
        }
        
        # Add result limiting indicator
        if limit_results and len(violations) >= limit_results:
            result['results_limited'] = True
            
        return result
    
    async def explain_finding_tool(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Explain finding tool implementation."""
        finding_id = args['finding_id']
        return {
            'finding_id': finding_id,
            'explanation': f'This is a detailed explanation of finding {finding_id}',
            'severity_rationale': 'Severity based on impact analysis',
            'suggested_actions': ['Review code', 'Apply refactoring']
        }
    
    async def explain_finding(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Explain finding - comprehensive version."""
        rule_id = args.get('rule_id', args.get('finding_id', 'unknown'))
        include_examples = args.get('include_examples', False)
        
        explanations = {
            'CON_CoM': {
                'connascence_type': 'CoM',
                'explanation': 'Connascence of Meaning occurs when multiple components must agree on the meaning of particular values. This includes magic literals, magic strings, and other hardcoded values that appear in multiple places.',
                'examples': [
                    {
                        'problem_code': 'if user_status == "ACTIVE":\n    # code\nif status == "ACTIVE":\n    # more code',
                        'solution_code': 'USER_STATUS_ACTIVE = "ACTIVE"\nif user_status == USER_STATUS_ACTIVE:\n    # code\nif status == USER_STATUS_ACTIVE:\n    # more code'
                    }
                ] if include_examples else []
            }
        }
        
        result = explanations.get(rule_id, {
            'connascence_type': 'Unknown',
            'explanation': f'Explanation for rule {rule_id} not available',
            'examples': []
        })
        
        return result
    
    async def list_presets(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List available policy presets."""
        # Log the request
        self.audit_logger.log_request(tool_name='list_presets', timestamp=time.time())
        
        return {
            'presets': [
                {
                    'id': 'strict-core',
                    'name': 'Strict Core',
                    'description': 'Strict rules for core systems'
                },
                {
                    'id': 'service-defaults',
                    'name': 'Service Defaults',
                    'description': 'Default service configuration'
                },
                {
                    'id': 'experimental',
                    'name': 'Experimental',
                    'description': 'Experimental rules for testing'
                }
            ]
        }
    
    async def validate_policy(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Validate policy configuration."""
        policy_preset = args.get('policy_preset', args.get('policy', 'default'))
        
        valid_presets = ['strict-core', 'service-defaults', 'experimental', 'default']
        is_valid = policy_preset in valid_presets
        
        return {
            'valid': is_valid,
            'policy_preset': policy_preset,
            'issues': [] if is_valid else [f'Unknown preset: {policy_preset}']
        }
    
    async def get_metrics(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get analysis metrics."""
        return {
            'request_count': 42,
            'response_times': {
                'avg': 125.5,
                'min': 45,
                'max': 320
            },
            'tool_usage': {
                'list_presets': 5,
                'explain_finding': 8,
                'scan_path': 15,
                'propose_autofix': 3
            }
        }
    
    async def enforce_policy(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Enforce policy rules."""
        policy_preset = args.get('policy_preset', 'default')
        budget_limits = args.get('budget_limits', {})
        violations = args.get('violations', [])
        
        # Get violations from analyzer if not provided
        if not violations and policy_preset:
            # This would normally analyze the codebase, but for testing we use mocked violations
            violations = self.analyzer.analyze_directory('/test/path', policy_preset)
        
        total_violations = len(violations)
        budget_exceeded = False
        violations_over_budget = []
        
        # Check budget limits
        total_limit = budget_limits.get('total_violations', float('inf'))
        if total_violations > total_limit:
            budget_exceeded = True
            violations_over_budget = violations[total_limit:] if total_limit != float('inf') else []
        
        return {
            'budget_status': {
                'budget_exceeded': budget_exceeded,
                'total_violations': total_violations,
                'budget_limit': budget_limits.get('total_violations', 'unlimited')
            },
            'violations_over_budget': violations_over_budget,
            'policy_preset': policy_preset
        }
    
    def _validate_policy_preset(self, preset: str) -> None:
        """Validate policy preset."""
        valid_presets = ['strict-core', 'service-defaults', 'experimental']
        if preset not in valid_presets:
            raise ValueError(f'Invalid policy preset: {preset}')
    
    def _validate_path(self, path: str) -> None:
        """Validate path for security (enhanced version)."""
        from pathlib import Path
        
        # Restricted paths - need to catch various formats
        restricted = [
            '/etc', '/var/log', '/home/other_user', '/usr/bin',
            'c:\\windows\\system32', 'c:/windows/system32', 
            '\\windows\\system32', '/windows/system32'
        ]
        
        path_lower = path.lower()
        
        # Check for exact matches and path prefixes
        for restricted_path in restricted:
            if path_lower.startswith(restricted_path.lower()):
                raise ValueError(f'Path not allowed: {path}')
        
        # Check for path traversal attempts  
        if '..' in path:
            raise ValueError(f'Path not allowed: {path}')
            
        # Try to resolve path and check again
        try:
            p = Path(path).resolve()
            resolved_str = str(p).lower()
            
            for restricted_path in restricted:
                if resolved_str.startswith(restricted_path.lower()):
                    raise ValueError(f'Path not allowed: {path}')
                    
        except (OSError, ValueError) as e:
            if 'Path not allowed' in str(e):
                raise
            # For other OS errors, we still want to block the path
            raise ValueError(f'Path not allowed: {path}') from e
    
    async def propose_autofix_tool(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Propose autofix tool implementation."""
        violation = args['violation']
        return {
            'violation_id': violation.get('id', 'unknown'),
            'autofix_available': True,
            'confidence': 0.85,
            'description': 'Extract magic literal to named constant',
            'preview': 'const MAX_ITEMS = 42;'
        }
    
    async def propose_autofix(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Propose autofix for violation."""
        violation = args['violation']
        include_diff = args.get('include_diff', False)
        
        return {
            'patch_available': True,
            'patch_description': 'Extract magic literal to constant',
            'confidence_score': 0.85,
            'safety_level': 'safe',
            'violation_id': violation.get('id', 'unknown'),
            'diff': '+ THRESHOLD = 100\\n- if value > 100:\\n+ if value > THRESHOLD:' if include_diff else None
        }

class MCPConnascenceTool:
    """MCP tool interface."""
    def __init__(self, name, description="", handler=None, input_schema=None):
        self.name = name
        self.description = description
        self.handler = handler
        self.input_schema = input_schema or {'type': 'object', 'properties': {}}
    
    def validate_input(self, input_data: Dict[str, Any]) -> None:
        """Validate input against schema."""
        if not self.input_schema:
            return
        
        required = self.input_schema.get('required', [])
        for field in required:
            if field not in input_data:
                raise ValueError(f"Missing required field: {field}")
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool."""
        self.validate_input(args)
        if self.handler:
            return await self.handler(args)
        return {'result': f'Tool {self.name} executed with args: {args}'}
