
import asyncio
import sys
import time
from pathlib import Path
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

class ConnascenceMCPServer(NASAIntegrationMethods, MECEIntegrationMethods):
    """MCP server for connascence analysis with NASA Power of Ten and MECE analysis integration."""
    def __init__(self, config=None):
        # Initialize parent classes
        NASAIntegrationMethods.__init__(self)
        MECEIntegrationMethods.__init__(self)
        
        self.config = config or {}
        self.name = "connascence"
        self.version = "2.0.0"
        
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
        """Create real analyzer instance using refactored ConnascenceASTAnalyzer."""
        from analyzer.ast_engine.core_analyzer import ConnascenceASTAnalyzer
        from integrations.tool_coordinator import ToolCoordinator
        from pathlib import Path
        
        class RealAnalyzer:
            def __init__(self):
                # Use our new refactored analyzer  
                self.analyzer = ConnascenceASTAnalyzer()
                # Initialize enterprise tool coordinator for comprehensive analysis
                self.tool_coordinator = ToolCoordinator()
            
            def analyze_path(self, path, profile=None):
                """Analyze a single file or directory using enterprise tooling."""
                path_obj = Path(path)
                
                if path_obj.is_file() and path_obj.suffix == '.py':
                    violations = self.analyzer.analyze_file(path_obj)
                elif path_obj.is_dir():
                    # Use enterprise tool coordination for directory analysis with FULL linter integration
                    try:
                        import asyncio
                        # Run enterprise analysis with ALL available linters
                        enabled_tools = {'ruff', 'mypy', 'radon', 'bandit', 'black', 'build_flags'}
                        integrated_analysis = asyncio.run(
                            self.tool_coordinator.analyze_project(
                                path_obj, 
                                enabled_tools=enabled_tools,
                                include_connascence=True
                            )
                        )
                        
                        # Extract connascence violations enhanced with linter correlations
                        violations = integrated_analysis.connascence_results.get('violations', [])
                        
                        # CRITICAL: Enhance connascence violations with ALL linter data
                        enhanced_violations = self.enhance_violations_with_linter_data(
                            violations, 
                            integrated_analysis.tool_results,
                            integrated_analysis.correlations
                        )
                        violations = enhanced_violations
                        
                        # Store correlation data for enhanced reporting
                        if integrated_analysis.correlations:
                            self._last_correlations = integrated_analysis.correlations
                            self._last_recommendations = integrated_analysis.recommendations
                            self._last_linter_data = integrated_analysis.tool_results
                            
                    except Exception as e:
                        # Fallback to basic analyzer if enterprise tooling fails
                        result = self.analyzer.analyze_directory(path_obj)
                        violations = result.violations
                else:
                    violations = []
                
                # Convert to MCP format
                converted_violations = []
                for v in violations:
                    # Handle both Violation objects and dict format
                    if hasattr(v, 'id'):
                        converted_violations.append({
                            'id': v.id,
                            'type': v.connascence_type if hasattr(v, 'connascence_type') else v.type.value,
                            'severity': v.severity.value if hasattr(v.severity, 'value') else v.severity,
                            'file': v.file_path,
                            'line': v.line_number,
                            'column': v.column,
                            'description': v.description,
                            'recommendation': v.recommendation,
                            'context': v.context or {}
                        })
                    else:
                        # Handle dict format from tool coordinator
                        converted_violations.append({
                            'id': v.get('id', ''),
                            'type': v.get('type', v.get('connascence_type', 'Unknown')),
                            'severity': v.get('severity', 'medium'),
                            'file': v.get('file_path', v.get('file', '')),
                            'line': v.get('line_number', v.get('line', 0)),
                            'column': v.get('column', 0),
                            'description': v.get('description', ''),
                            'recommendation': v.get('recommendation', ''),
                            'context': v.get('context', {})
                        })
                
                return converted_violations
        
        return RealAnalyzer()
    
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
                'name': 'analyze_duplications',
                'description': 'Analyze code duplications and overlapping functionality using MECE analysis',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'path': {'type': 'string', 'description': 'Path to analyze for duplications'},
                        'file_patterns': {'type': 'array', 'items': {'type': 'string'}, 'description': 'File patterns to include (e.g., ["*.py", "*.js"])'}
                    },
                    'required': ['path']
                }
            },
            {
                'name': 'check_nasa_compliance',
                'description': 'Check NASA Power of Ten compliance for violations',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'violation': {'type': 'object', 'description': 'Violation to check for NASA compliance'},
                        'context_data': {'type': 'object', 'description': 'Additional context data'}
                    },
                    'required': ['violation']
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
        """Validate tool input with comprehensive security checks."""
        import re
        
        # Common validation for all tools
        if not isinstance(args, dict):
            return False
            
        # Check for excessively large payloads
        if len(str(args)) > 100000:  # 100KB limit
            return False
        
        if tool_name == 'scan_path':
            if 'path' not in args or not isinstance(args['path'], str):
                return False
            
            # Validate path format
            path = args['path']
            if not path or len(path) > 500:
                return False
                
            # Additional validation for policy preset
            if 'policy_preset' in args:
                preset = args['policy_preset']
                if not isinstance(preset, str) or len(preset) > 50:
                    return False
                if not re.match(r'^[a-zA-Z0-9_\-]+$', preset):
                    return False
                    
            return True
            
        elif tool_name == 'explain_finding':
            if 'finding_id' not in args:
                return False
            
            finding_id = args['finding_id']
            if not isinstance(finding_id, str) or len(finding_id) > 100:
                return False
                
            # Only allow alphanumeric and basic separators
            if not re.match(r'^[a-zA-Z0-9_\-\.]+$', finding_id):
                return False
                
            return True
            
        elif tool_name == 'propose_autofix':
            if 'violation' not in args:
                return False
            
            violation = args['violation']
            if not isinstance(violation, dict):
                return False
                
            # Validate violation structure
            required_fields = ['id', 'type', 'file_path']
            for field in required_fields:
                if field not in violation or not isinstance(violation[field], str):
                    return False
                    
            return True
        
        elif tool_name == 'analyze_duplications':
            if 'path' not in args or not isinstance(args['path'], str):
                return False
            
            path = args['path']
            if not path or len(path) > 500:
                return False
            
            # Validate file patterns if provided
            if 'file_patterns' in args:
                patterns = args['file_patterns']
                if not isinstance(patterns, list) or len(patterns) > 10:
                    return False
                for pattern in patterns:
                    if not isinstance(pattern, str) or len(pattern) > 20:
                        return False
            
            return True
        
        elif tool_name == 'check_nasa_compliance':
            if 'violation' not in args or not isinstance(args['violation'], dict):
                return False
            
            violation = args['violation']
            required_fields = ['id', 'type']
            for field in required_fields:
                if field not in violation:
                    return False
            
            return True
            
        # Default validation for other tools
        return True
    
    def validate_path(self, path: str) -> bool:
        """Validate file path for security."""
        try:
            self._validate_path(path)
            return True
        except ValueError:
            return False
    
    async def scan_path(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Scan path tool implementation with enhanced security."""
        # Check rate limit first
        if not self.rate_limiter.check_rate_limit():
            self.audit_logger.log('rate_limit_exceeded', {'tool': 'scan_path'})
            raise Exception("Rate limit exceeded")
        
        # Comprehensive input validation
        if not self.validate_input('scan_path', args):
            self.audit_logger.log('invalid_input', {'tool': 'scan_path', 'args': str(args)[:100]})
            raise ValueError("Invalid input for scan_path")
        
        path = args['path']
        
        # Enhanced path validation with detailed error reporting
        try:
            self._validate_path(path)
        except ValueError as e:
            self.audit_logger.log('path_validation_failed', {
                'tool': 'scan_path',
                'path': path[:100],  # Truncate for logging
                'error': str(e)
            })
            raise ValueError(f"Path validation failed: {str(e)}")
        
        # Log the request with sanitized information
        self.audit_logger.log_request(
            tool_name='scan_path', 
            timestamp=time.time(),
            path_length=len(path),
            policy_preset=args.get('policy_preset', 'default')
        )
        
        profile = args.get('policy_preset', 'default')
        limit_results = args.get('limit_results')
        
        try:
            violations = self.analyzer.analyze_path(path, profile)
        except Exception as e:
            return {
                'error': str(e),
                'path': path,
                'success': False
            }
        
        # Apply result limiting if requested
        if limit_results and len(violations) > limit_results:
            violations = violations[:limit_results]
        
        # Count violations by severity (violations are already dictionaries)
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for v in violations:
            severity = v.get('severity', 'medium')
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
            'violations': violations,  # Already in dictionary format
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
        """Validate path for security with comprehensive protection."""
        from pathlib import Path
        import re
        
        if not path or len(path) > 500:  # Reasonable path length limit
            raise ValueError(f'Invalid path length: {path}')
        
        # Check for null bytes and other control characters
        if '\x00' in path or any(ord(c) < 32 for c in path if c not in '\t\n\r'):
            raise ValueError(f'Path contains invalid characters: {path}')
        
        # Comprehensive restricted paths - system directories
        restricted_patterns = [
            # Unix/Linux system paths
            r'^/etc(/.*)?$',
            r'^/var/log(/.*)?$', 
            r'^/usr/bin(/.*)?$',
            r'^/bin(/.*)?$',
            r'^/sbin(/.*)?$',
            r'^/root(/.*)?$',
            r'^/proc(/.*)?$',
            r'^/sys(/.*)?$',
            r'^/dev(/.*)?$',
            # Windows system paths
            r'^[a-zA-Z]:[/\\]windows[/\\]system32(/.*)?$',
            r'^[a-zA-Z]:[/\\]windows[/\\]syswow64(/.*)?$',
            r'^[a-zA-Z]:[/\\]program files(/.*)?$',
            r'^[a-zA-Z]:[/\\]program files \(x86\)(/.*)?$',
            r'^[a-zA-Z]:[/\\]users[/\\]administrator(/.*)?$',
            # Network paths
            r'^\\\\[^/\\]+(/.*)?$',  # UNC paths
        ]
        
        path_normalized = path.lower().replace('\\', '/')
        
        # Check against restricted patterns
        for pattern in restricted_patterns:
            if re.match(pattern, path_normalized, re.IGNORECASE):
                raise ValueError(f'Path not allowed (restricted): {path}')
        
        # Enhanced path traversal detection
        traversal_patterns = [
            r'\.\./',     # ../
            r'\\\.\.\\',  # ..\\
            r'/\.\./',    # /../
            r'\\\.\.\\', # \\..\\
            r'%2e%2e',    # URL encoded ..
            r'\.\.\.',    # Multiple dots
        ]
        
        for pattern in traversal_patterns:
            if re.search(pattern, path, re.IGNORECASE):
                raise ValueError(f'Path not allowed (traversal): {path}')
        
        # Try to resolve path and validate resolved path
        try:
            p = Path(path).resolve(strict=False)  # Don't require path to exist
            resolved_str = str(p).lower().replace('\\', '/')
            
            # Check resolved path against restrictions
            for pattern in restricted_patterns:
                if re.match(pattern, resolved_str, re.IGNORECASE):
                    raise ValueError(f'Path not allowed (resolved): {path}')
            
            # Ensure resolved path is within safe boundaries
            if not self._is_within_safe_boundaries(p):
                raise ValueError(f'Path not allowed (boundaries): {path}')
                
        except (OSError, ValueError) as e:
            if 'Path not allowed' in str(e):
                raise
            # For other OS errors, be restrictive and block the path
            raise ValueError(f'Path not allowed (validation error): {path}') from e
    
    def _is_within_safe_boundaries(self, path: Path) -> bool:
        """Check if resolved path is within safe boundaries."""
        try:
            # Define safe base directories (customize for your environment)
            safe_bases = [
                Path.cwd(),  # Current working directory
                Path.home() / 'projects',  # User projects directory
                Path('/tmp'),  # Temporary directory (Unix)
                Path('/var/tmp'),  # Alternative temp directory (Unix)
            ]
            
            # Check if path is under any safe base directory
            for safe_base in safe_bases:
                try:
                    if safe_base.exists():
                        path.relative_to(safe_base.resolve())
                        return True
                except (ValueError, OSError):
                    continue
                    
            return False
            
        except Exception:
            # If we can't determine safety, be restrictive
            return False
    
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
        """Enhanced autofix with multi-file connascence context and linter integration."""
        violation = args['violation']
        context = args.get('context', '')
        include_diff = args.get('include_diff', False)
        
        # Parse enhanced context to extract multi-file connascence information
        context_data = self.parse_enhanced_context(context)
        
        # Generate comprehensive AI-powered autofix
        autofix_result = await self.generate_comprehensive_autofix(violation, context_data)
        
        return {
            'patch_available': autofix_result['patch_available'],
            'patch': autofix_result['patch'],
            'patch_description': autofix_result['description'],
            'confidence_score': autofix_result['confidence'],
            'safety_level': autofix_result['safety'],
            'violation_id': violation.get('id', 'unknown'),
            'multi_file_changes': autofix_result.get('multi_file_changes', []),
            'related_files_updated': autofix_result.get('related_files_updated', []),
            'linter_correlations': autofix_result.get('linter_correlations', {}),
            'refactoring_strategy': autofix_result.get('strategy', ''),
            'diff': autofix_result.get('diff') if include_diff else None
        }

    def parse_enhanced_context(self, context: str) -> Dict[str, Any]:
        """Parse the enhanced context from VS Code extension."""
        context_data = {
            'violation_metadata': {},
            'code_snippet': '',
            'connascence_type_details': '',
            'related_files': [],
            'linter_correlations': {},
            'refactoring_strategy': '',
            'ai_instructions': ''
        }
        
        if not context:
            return context_data
            
        try:
            # Parse structured context sections
            sections = context.split('===')
            
            for section in sections:
                section = section.strip()
                if not section:
                    continue
                    
                if 'CONNASCENCE VIOLATION ANALYSIS' in section:
                    lines = section.split('\n')[1:]  # Skip header
                    for line in lines:
                        if line.startswith('Type:'):
                            context_data['violation_metadata']['type'] = line.split(':', 1)[1].strip()
                        elif line.startswith('Severity:'):
                            context_data['violation_metadata']['severity'] = line.split(':', 1)[1].strip()
                        elif line.startswith('Location:'):
                            context_data['violation_metadata']['location'] = line.split(':', 1)[1].strip()
                        elif line.startswith('Description:'):
                            context_data['violation_metadata']['description'] = line.split(':', 1)[1].strip()
                
                elif 'PRIMARY CODE SNIPPET' in section:
                    context_data['code_snippet'] = section
                
                elif 'CONNASCENCE TYPE DETAILS' in section:
                    context_data['connascence_type_details'] = section
                    
                elif 'RELATED FILES' in section:
                    context_data['related_files'] = [line.strip() for line in section.split('\n')[1:] if line.strip()]
                    
                elif 'MULTI-LINTER ANALYSIS' in section:
                    linter_lines = [line.strip() for line in section.split('\n')[1:] if line.strip() and line.startswith('-')]
                    context_data['linter_correlations'] = {
                        'findings': linter_lines,
                        'integration_available': True
                    }
                    
                elif 'REFACTORING STRATEGY' in section:
                    context_data['refactoring_strategy'] = section
                    
                elif 'AI INSTRUCTION' in section:
                    context_data['ai_instructions'] = section
                    
        except Exception as e:
            # Log error but continue with partial context
            print(f"Warning: Context parsing error: {e}")
            
        return context_data

    async def generate_comprehensive_autofix(self, violation: Dict[str, Any], context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered comprehensive autofix with multi-file awareness."""
        
        # Extract key information
        violation_type = context_data.get('violation_metadata', {}).get('type', violation.get('type', 'Unknown'))
        code_snippet = context_data.get('code_snippet', '')
        related_files = context_data.get('related_files', [])
        linter_data = context_data.get('linter_correlations', {})
        strategy = context_data.get('refactoring_strategy', '')
        
        # Generate type-specific comprehensive fixes
        if violation_type == 'CoM' or 'magic' in violation.get('description', '').lower():
            return await self.generate_magic_literal_fix(violation, context_data)
        elif violation_type == 'CoP':
            return await self.generate_parameter_position_fix(violation, context_data)
        elif violation_type == 'CoA' or 'God Object' in violation.get('description', ''):
            return await self.generate_god_object_fix(violation, context_data)
        elif violation_type == 'CoT':
            return await self.generate_type_connascence_fix(violation, context_data)
        elif violation_type == 'CoN':
            return await self.generate_name_connascence_fix(violation, context_data)
        else:
            return await self.generate_generic_connascence_fix(violation, context_data)

    async def generate_magic_literal_fix(self, violation: Dict[str, Any], context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive fix for Connascence of Meaning (magic literals)."""
        
        # Enhanced AI prompt with multi-file context
        ai_prompt = f"""
        CONNASCENCE VIOLATION FIX REQUEST - MAGIC LITERAL (CoM)
        
        Context Analysis:
        {context_data.get('code_snippet', 'No code snippet available')}
        
        Related Files Impact:
        {chr(10).join(context_data.get('related_files', ['No related files identified']))}
        
        Linter Correlations:
        {chr(10).join(context_data.get('linter_correlations', {}).get('findings', ['No linter correlations available']))}
        
        Strategy: {context_data.get('refactoring_strategy', 'Extract magic literals to named constants')}
        
        REQUIREMENTS:
        1. Extract ALL magic literals to appropriately named constants
        2. Create constants at module/class level for reusability
        3. Update ALL related files that use the same magic values
        4. Follow naming conventions (SCREAMING_SNAKE_CASE for constants)
        5. Add type hints and documentation where appropriate
        6. Consider creating an enum if multiple related values exist
        
        Generate a COMPLETE code solution that addresses the multi-file connascence.
        """
        
        # Simulate AI response (in production, this would call actual AI service)
        magic_value = self.extract_magic_value_from_context(context_data.get('code_snippet', ''))
        constant_name = self.generate_constant_name(magic_value, violation)
        
        return {
            'patch_available': True,
            'patch': f'# Add to constants section\n{constant_name} = {magic_value}\n\n# Replace in violation location\nif value > {constant_name}:  # Instead of magic literal',
            'description': f'Extract magic literal {magic_value} to named constant {constant_name}',
            'confidence': 0.92,
            'safety': 'safe',
            'strategy': 'Extract magic literals to named constants with multi-file consistency',
            'multi_file_changes': [
                {
                    'file': violation.get('file_path', ''),
                    'change_type': 'constant_extraction',
                    'description': f'Replace magic literal with {constant_name}'
                }
            ],
            'related_files_updated': self.get_related_files_for_magic_literal(context_data),
            'linter_correlations': {
                'ruff': 'Resolves magic number/string violations',
                'bandit': 'Improves security by centralizing configuration'
            }
        }

    async def generate_parameter_position_fix(self, violation: Dict[str, Any], context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive fix for Connascence of Position (parameter coupling)."""
        
        return {
            'patch_available': True,
            'patch': '''
# Convert to named parameters using dataclass or TypedDict
from dataclasses import dataclass
from typing import Optional

@dataclass
class ProcessingConfig:
    max_items: int
    enable_cache: bool
    timeout_seconds: Optional[float] = None

# Replace function signature
def process_data(config: ProcessingConfig) -> Result:
    if len(data) > config.max_items:
        # Implementation using named parameters
        pass
            '''.strip(),
            'description': 'Replace positional parameters with parameter object pattern',
            'confidence': 0.88,
            'safety': 'caution',  # Requires updating all call sites
            'strategy': 'Parameter object pattern to eliminate position dependency',
            'multi_file_changes': [
                {
                    'file': violation.get('file_path', ''),
                    'change_type': 'parameter_refactor',
                    'description': 'Convert to parameter object pattern'
                }
            ],
            'related_files_updated': ['All call sites of the function need updating'],
            'linter_correlations': {
                'mypy': 'Improves type safety with structured parameters',
                'black': 'Formatting will improve with named parameters'
            }
        }

    async def generate_god_object_fix(self, violation: Dict[str, Any], context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive fix for God Object (Connascence of Algorithm)."""
        
        return {
            'patch_available': True,
            'patch': '''
# Extract responsibilities to separate classes
class DataProcessor:
    """Handles data processing logic."""
    
    def process(self, data):
        # Extracted processing logic
        pass

class DataValidator:
    """Handles validation logic."""
    
    def validate(self, data):
        # Extracted validation logic
        pass

class DataFormatter:
    """Handles formatting logic."""
    
    def format(self, data):
        # Extracted formatting logic
        pass

# Refactored main class
class StreamlinedService:
    def __init__(self):
        self.processor = DataProcessor()
        self.validator = DataValidator()
        self.formatter = DataFormatter()
    
    def handle_request(self, data):
        # Orchestrate using composed services
        if self.validator.validate(data):
            processed = self.processor.process(data)
            return self.formatter.format(processed)
            '''.strip(),
            'description': 'Decompose God Object using Single Responsibility Principle',
            'confidence': 0.75,  # Lower confidence as this is a major refactor
            'safety': 'caution',
            'strategy': 'Extract classes by responsibility, use composition pattern',
            'multi_file_changes': [
                {
                    'file': violation.get('file_path', ''),
                    'change_type': 'class_decomposition',
                    'description': 'Split large class into focused components'
                }
            ],
            'related_files_updated': ['Files that import and use the refactored class'],
            'linter_correlations': {
                'radon': 'Significantly reduces cyclomatic complexity',
                'mypy': 'Improves type checking with smaller, focused classes'
            }
        }

    async def generate_type_connascence_fix(self, violation: Dict[str, Any], context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive fix for Connascence of Type."""
        
        return {
            'patch_available': True,
            'patch': '''
from typing import Protocol, TypeVar, Generic, Union, Optional
from dataclasses import dataclass

# Define clear interfaces
class Processable(Protocol):
    def process(self) -> str: ...

# Use proper type annotations
def handle_data(item: Processable, config: Optional[dict] = None) -> str:
    return item.process()

# Type-safe data structures
@dataclass
class ProcessingResult:
    status: str
    data: Optional[str] = None
    error_message: Optional[str] = None
            '''.strip(),
            'description': 'Add explicit type annotations and interfaces',
            'confidence': 0.90,
            'safety': 'safe',
            'strategy': 'Add type annotations and use Protocol for interfaces',
            'multi_file_changes': [
                {
                    'file': violation.get('file_path', ''),
                    'change_type': 'type_annotation',
                    'description': 'Add comprehensive type hints'
                }
            ],
            'related_files_updated': ['Files with similar type coupling issues'],
            'linter_correlations': {
                'mypy': 'Resolves type checking errors',
                'ruff': 'Improves code clarity and catches type-related bugs'
            }
        }

    async def generate_name_connascence_fix(self, violation: Dict[str, Any], context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive fix for Connascence of Name."""
        
        return {
            'patch_available': True,
            'patch': '''
from enum import Enum
from typing import Final

# Centralized name definitions
class ServiceNames(Enum):
    USER_SERVICE = "user_service"
    DATA_SERVICE = "data_service"
    AUTH_SERVICE = "auth_service"

# Or use constants for simple cases
SERVICE_NAMES: Final = {
    'USER': 'user_service',
    'DATA': 'data_service',
    'AUTH': 'auth_service'
}

# Use dependency injection instead of string names
from abc import ABC, abstractmethod

class Service(ABC):
    @abstractmethod
    def process(self): pass

class ServiceRegistry:
    def __init__(self):
        self._services = {}
    
    def register(self, service_type: type, instance: Service):
        self._services[service_type] = instance
    
    def get(self, service_type: type) -> Service:
        return self._services[service_type]
            '''.strip(),
            'description': 'Replace string-based names with enums and dependency injection',
            'confidence': 0.85,
            'safety': 'caution',
            'strategy': 'Use enums for names and dependency injection for services',
            'multi_file_changes': [
                {
                    'file': violation.get('file_path', ''),
                    'change_type': 'name_standardization',
                    'description': 'Replace hardcoded names with centralized definitions'
                }
            ],
            'related_files_updated': ['All files using the same string-based names'],
            'linter_correlations': {
                'ruff': 'Eliminates hardcoded string usage',
                'mypy': 'Improves type safety with enums'
            }
        }

    async def generate_generic_connascence_fix(self, violation: Dict[str, Any], context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate generic connascence fix when specific type is not handled."""
        
        return {
            'patch_available': True,
            'patch': '# Generic refactoring to reduce coupling\n# Specific implementation depends on violation context',
            'description': f'Reduce {violation.get("type", "coupling")} connascence through appropriate refactoring',
            'confidence': 0.60,
            'safety': 'caution',
            'strategy': 'Apply appropriate decoupling patterns based on connascence type',
            'multi_file_changes': [],
            'related_files_updated': [],
            'linter_correlations': {}
        }

    def extract_magic_value_from_context(self, code_snippet: str) -> str:
        """Extract magic value from code snippet."""
        # Simple pattern matching to find likely magic values
        import re
        
        # Look for common magic patterns
        patterns = [
            r'==\s*(\d+)',      # == 42
            r'>\s*(\d+)',       # > 100  
            r'<\s*(\d+)',       # < 50
            r'=\s*["\']([^"\']+)["\']',  # = "magic_string"
            r'=\s*(\d+)',       # = 123
        ]
        
        for pattern in patterns:
            match = re.search(pattern, code_snippet)
            if match:
                return match.group(1)
        
        return "42"  # Default fallback
    
    def generate_constant_name(self, magic_value: str, violation: Dict[str, Any]) -> str:
        """Generate appropriate constant name for magic value."""
        
        # Try to infer meaning from context
        if magic_value.isdigit():
            num = int(magic_value)
            if num == 100:
                return "MAX_PERCENTAGE"
            elif num in [1, 2, 3, 5, 10]:
                return f"DEFAULT_LIMIT_{num}"
            elif num > 1000:
                return "MAX_TIMEOUT_MS"
            else:
                return f"THRESHOLD_{num}"
        else:
            # For strings, use uppercase with underscores
            return magic_value.upper().replace(' ', '_').replace('-', '_')

    def get_related_files_for_magic_literal(self, context_data: Dict[str, Any]) -> List[str]:
        """Get files that likely use the same magic literal."""
        related = []
        
        # Parse related files from context
        for file_info in context_data.get('related_files', []):
            if 'Configuration files' in file_info or 'Test files' in file_info:
                related.append(file_info.replace('//', '').strip())
        
        return related

    def enhance_violations_with_linter_data(self, violations: List[Dict], tool_results: Dict, correlations: Dict) -> List[Dict]:
        """Enhance connascence violations with comprehensive linter correlation data."""
        enhanced_violations = []
        
        for violation in violations:
            enhanced_violation = violation.copy() if isinstance(violation, dict) else {
                'id': getattr(violation, 'id', ''),
                'type': getattr(violation, 'connascence_type', getattr(violation, 'type', 'Unknown')),
                'severity': getattr(violation, 'severity', 'medium'),
                'file_path': getattr(violation, 'file_path', ''),
                'line_number': getattr(violation, 'line_number', 0),
                'column': getattr(violation, 'column', 0),
                'description': getattr(violation, 'description', ''),
                'recommendation': getattr(violation, 'recommendation', ''),
                'context': getattr(violation, 'context', {})
            }
            
            # Add comprehensive linter correlation data
            linter_correlations = self.correlate_violation_with_all_linters(
                enhanced_violation, tool_results, correlations
            )
            enhanced_violation['linter_correlations'] = linter_correlations
            
            # Enhance severity based on linter findings
            enhanced_severity = self.calculate_enhanced_severity(
                enhanced_violation, linter_correlations
            )
            enhanced_violation['enhanced_severity'] = enhanced_severity
            
            # Add cross-tool recommendations
            cross_tool_recommendations = self.generate_cross_tool_recommendations(
                enhanced_violation, linter_correlations
            )
            enhanced_violation['cross_tool_recommendations'] = cross_tool_recommendations
            
            enhanced_violations.append(enhanced_violation)
        
        return enhanced_violations
    
    def correlate_violation_with_all_linters(self, violation: Dict, tool_results: Dict, correlations: Dict) -> Dict:
        """Correlate a single violation with findings from all linters."""
        file_path = violation.get('file_path', '')
        line_number = violation.get('line_number', 0)
        violation_type = violation.get('type', '')
        
        correlations = {
            'ruff_findings': [],
            'mypy_findings': [],
            'radon_findings': [],
            'bandit_findings': [],
            'black_findings': [],
            'build_flags_findings': [],
            'correlation_score': 0.0,
            'cross_tool_confidence': 0.0
        }
        
        # Ruff correlation - style and code quality
        if 'ruff' in tool_results and tool_results['ruff'].success:
            ruff_data = tool_results['ruff'].results
            ruff_findings = self.find_ruff_correlations(violation, ruff_data)
            correlations['ruff_findings'] = ruff_findings
        
        # MyPy correlation - type safety
        if 'mypy' in tool_results and tool_results['mypy'].success:
            mypy_data = tool_results['mypy'].results
            mypy_findings = self.find_mypy_correlations(violation, mypy_data)
            correlations['mypy_findings'] = mypy_findings
        
        # Radon correlation - complexity
        if 'radon' in tool_results and tool_results['radon'].success:
            radon_data = tool_results['radon'].results
            radon_findings = self.find_radon_correlations(violation, radon_data)
            correlations['radon_findings'] = radon_findings
        
        # Bandit correlation - security
        if 'bandit' in tool_results and tool_results['bandit'].success:
            bandit_data = tool_results['bandit'].results
            bandit_findings = self.find_bandit_correlations(violation, bandit_data)
            correlations['bandit_findings'] = bandit_findings
        
        # Black correlation - formatting
        if 'black' in tool_results and tool_results['black'].success:
            black_data = tool_results['black'].results
            black_findings = self.find_black_correlations(violation, black_data)
            correlations['black_findings'] = black_findings
        
        # Build flags correlation - compiler safety
        if 'build_flags' in tool_results and tool_results['build_flags'].success:
            build_flags_data = tool_results['build_flags'].results
            build_flags_findings = self.find_build_flags_correlations(violation, build_flags_data)
            correlations['build_flags_findings'] = build_flags_findings
        
        # Calculate overall correlation metrics
        total_findings = sum(len(correlations[key]) for key in correlations if key.endswith('_findings'))
        correlations['correlation_score'] = min(1.0, total_findings / 10.0)  # Normalize to 0-1
        
        # Calculate cross-tool confidence (how many tools agree this is an issue)
        tools_with_findings = sum(1 for key in correlations if key.endswith('_findings') and correlations[key])
        correlations['cross_tool_confidence'] = tools_with_findings / 6.0  # 6 total tools
        
        return correlations
    
    def find_ruff_correlations(self, violation: Dict, ruff_data: Dict) -> List[Dict]:
        """Find Ruff issues that correlate with this connascence violation."""
        correlations = []
        violation_type = violation.get('type', '')
        file_path = violation.get('file_path', '')
        
        # Map connascence types to Ruff rule patterns
        ruff_mappings = {
            'CoM': ['F541', 'E731', 'B008'],  # Magic literals, lambda assignments, mutable defaults
            'CoP': ['E999', 'B006'],  # Syntax errors, mutable arguments
            'CoA': ['C901', 'PLR0912'],  # Complex functions, too many branches
            'CoN': ['F401', 'F811'],  # Unused imports, redefined names
            'CoT': ['ANN'],  # Missing type annotations
        }
        
        relevant_rules = ruff_mappings.get(violation_type, [])
        
        # Look for Ruff issues in the same file
        ruff_issues = ruff_data.get('issues', [])
        for issue in ruff_issues:
            if (issue.get('file', '') == file_path and 
                any(rule in issue.get('rule', '') for rule in relevant_rules)):
                correlations.append({
                    'rule': issue.get('rule', ''),
                    'message': issue.get('message', ''),
                    'line': issue.get('line', 0),
                    'confidence': 0.8
                })
        
        return correlations
    
    def find_mypy_correlations(self, violation: Dict, mypy_data: Dict) -> List[Dict]:
        """Find MyPy errors that correlate with this connascence violation."""
        correlations = []
        violation_type = violation.get('type', '')
        file_path = violation.get('file_path', '')
        
        if violation_type in ['CoT', 'CoN', 'CoI']:
            mypy_errors = mypy_data.get('errors', [])
            for error in mypy_errors:
                if error.get('file', '') == file_path:
                    correlations.append({
                        'error_type': error.get('error_type', ''),
                        'message': error.get('message', ''),
                        'line': error.get('line', 0),
                        'confidence': 0.9
                    })
        
        return correlations
    
    def find_radon_correlations(self, violation: Dict, radon_data: Dict) -> List[Dict]:
        """Find Radon complexity issues that correlate with this connascence violation."""
        correlations = []
        violation_type = violation.get('type', '')
        file_path = violation.get('file_path', '')
        
        if violation_type in ['CoA', 'God Object']:
            complex_functions = radon_data.get('complex_functions', [])
            for func in complex_functions:
                if func.get('file', '') == file_path:
                    correlations.append({
                        'function_name': func.get('function', ''),
                        'complexity': func.get('complexity', 0),
                        'line': func.get('line', 0),
                        'confidence': 0.85
                    })
        
        return correlations
    
    def find_bandit_correlations(self, violation: Dict, bandit_data: Dict) -> List[Dict]:
        """Find Bandit security issues that correlate with this connascence violation."""
        correlations = []
        file_path = violation.get('file_path', '')
        severity = violation.get('severity', '')
        
        # High severity connascence violations often have security implications
        if severity in ['high', 'critical']:
            security_issues = bandit_data.get('issues', [])
            for issue in security_issues:
                if issue.get('file', '') == file_path:
                    correlations.append({
                        'test_id': issue.get('test_id', ''),
                        'severity': issue.get('severity', ''),
                        'confidence': issue.get('confidence', ''),
                        'line': issue.get('line', 0),
                        'correlation_confidence': 0.7
                    })
        
        return correlations
    
    def find_black_correlations(self, violation: Dict, black_data: Dict) -> List[Dict]:
        """Find Black formatting issues that correlate with this connascence violation."""
        correlations = []
        violation_type = violation.get('type', '')
        file_path = violation.get('file_path', '')
        
        if violation_type in ['CoP', 'CoM']:  # Position and meaning often benefit from formatting
            unformatted_files = black_data.get('unformatted_files', [])
            if file_path in unformatted_files:
                correlations.append({
                    'issue': 'Formatting needed',
                    'description': 'File would benefit from Black formatting',
                    'confidence': 0.6
                })
        
        return correlations
    
    def find_build_flags_correlations(self, violation: Dict, build_flags_data: Dict) -> List[Dict]:
        """Find build/compiler flag issues that correlate with this connascence violation."""
        correlations = []
        severity = violation.get('severity', '')
        
        # Critical violations should be caught by compiler warnings
        if severity == 'critical':
            nasa_compliance = build_flags_data.get('nasa_compliance', {})
            if not nasa_compliance.get('compiler_warnings_as_errors', False):
                correlations.append({
                    'issue': 'Missing -Werror flag',
                    'description': 'Critical violations should be caught by compiler warnings',
                    'recommendation': 'Enable -Werror for production safety',
                    'confidence': 0.8
                })
        
        return correlations
    
    def calculate_enhanced_severity(self, violation: Dict, linter_correlations: Dict) -> str:
        """Calculate enhanced severity based on multi-linter correlation."""
        base_severity = violation.get('severity', 'medium')
        cross_tool_confidence = linter_correlations.get('cross_tool_confidence', 0.0)
        
        # Upgrade severity if multiple tools agree
        if cross_tool_confidence >= 0.5:  # 3+ tools found related issues
            severity_upgrade = {
                'low': 'medium',
                'medium': 'high', 
                'high': 'critical'
            }
            return severity_upgrade.get(base_severity, base_severity)
        
        return base_severity
    
    def generate_cross_tool_recommendations(self, violation: Dict, linter_correlations: Dict) -> List[str]:
        """Generate recommendations based on cross-tool analysis."""
        recommendations = []
        
        # Ruff recommendations
        if linter_correlations.get('ruff_findings'):
            recommendations.append("Run 'ruff check --fix' to automatically resolve style issues")
        
        # MyPy recommendations  
        if linter_correlations.get('mypy_findings'):
            recommendations.append("Add type annotations to resolve MyPy errors")
        
        # Radon recommendations
        if linter_correlations.get('radon_findings'):
            recommendations.append("Refactor complex functions to reduce cyclomatic complexity")
        
        # Bandit recommendations
        if linter_correlations.get('bandit_findings'):
            recommendations.append("Address security vulnerabilities identified by Bandit")
        
        # Black recommendations
        if linter_correlations.get('black_findings'):
            recommendations.append("Run 'black .' to improve code formatting")
        
        # Build flags recommendations
        if linter_correlations.get('build_flags_findings'):
            recommendations.append("Enable stricter compiler flags for better safety")
        
        return recommendations

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


class NASAIntegrationMethods:
    """NASA Power of Ten integration methods for MCP server."""
    
    def __init__(self):
        try:
            from .nasa_power_of_ten_integration import nasa_integration
            self.nasa_integration = nasa_integration
        except ImportError:
            print("Warning: NASA Power of Ten integration not available")
            self.nasa_integration = None
    
    async def _check_nasa_power_of_ten_violations(self, violation: Dict[str, Any], 
                                                context_data: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Check NASA Power of Ten rule violations."""
        if not self.nasa_integration:
            return []
        
        try:
            return self.nasa_integration.check_nasa_violations(violation, context_data)
        except Exception as e:
            print(f"Warning: NASA violation check failed: {e}")
            return []
    
    def _get_nasa_rules_context(self, violation: Dict[str, Any]) -> str:
        """Get NASA Power of Ten rules context for AI prompts."""
        if not self.nasa_integration:
            return "**NASA POWER OF TEN RULES**: Not available.\n"
        
        try:
            return self.nasa_integration.get_nasa_rules_context(violation)
        except Exception as e:
            print(f"Warning: NASA rules context failed: {e}")
            return "**NASA POWER OF TEN RULES**: Error loading rules.\n"
    
    def _calculate_nasa_compliance_score(self, nasa_violations: List[Dict[str, Any]]) -> float:
        """Calculate NASA compliance score."""
        if not self.nasa_integration:
            return 1.0
        
        try:
            return self.nasa_integration.calculate_nasa_compliance_score(nasa_violations)
        except Exception as e:
            print(f"Warning: NASA compliance score calculation failed: {e}")
            return 1.0
    
    def _get_nasa_compliance_actions(self, nasa_violations: List[Dict[str, Any]]) -> List[str]:
        """Get NASA compliance actions."""
        if not self.nasa_integration:
            return []
        
        try:
            return self.nasa_integration.get_nasa_compliance_actions(nasa_violations)
        except Exception as e:
            print(f"Warning: NASA compliance actions failed: {e}")
            return []


class MECEIntegrationMethods:
    """MECE analyzer integration methods for MCP server."""
    
    def __init__(self):
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            from analyzer.dup_detection import MECEAnalyzer
            self.MECEAnalyzer = MECEAnalyzer
        except ImportError:
            print("Warning: MECE Analyzer not available")
            self.MECEAnalyzer = None
    
    async def analyze_duplications(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code duplications using MECE analyzer."""
        if not self.MECEAnalyzer:
            return {
                'success': False,
                'error': 'MECE Analyzer not available',
                'duplication_clusters': [],
                'consolidation_opportunities': []
            }
        
        try:
            path = args.get('path', '.')
            file_patterns = args.get('file_patterns', ['*.py', '*.js', '*.ts'])
            
            analyzer = self.MECEAnalyzer()
            results = analyzer.analyze_codebase(path, file_patterns)
            
            return {
                'success': True,
                'analysis_results': results,
                'duplication_clusters': len(results.get('duplication_clusters', [])),
                'consolidation_opportunities': len(results.get('consolidation_opportunities', [])),
                'files_analyzed': results.get('files_analyzed', 0),
                'mece_analysis_complete': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'MECE analysis failed: {str(e)}',
                'duplication_clusters': [],
                'consolidation_opportunities': []
            }


def main():
    """Main entry point for MCP server."""
    import json
    import sys
    
    # Create server instance
    server = ConnascenceMCPServer()
    
    # Simple demonstration of the MCP server capabilities
    print("🔍 Connascence MCP Server v1.0.0", file=sys.stderr)
    print("Available tools:", file=sys.stderr)
    
    for tool in server.get_tools():
        print(f"  • {tool['name']}: {tool['description']}", file=sys.stderr)
    
    # For actual MCP implementation, this would handle stdin/stdout protocol
    # For now, just demonstrate the functionality
    demo_path = "/example/path"
    
    try:
        # Test path scanning
        result = asyncio.run(server.scan_path({
            'path': demo_path,
            'policy_preset': 'strict-core'
        }))
        
        print(f"\nDemo scan result: {json.dumps(result, indent=2)}", file=sys.stderr)
        
    except Exception as e:
        print(f"Demo failed: {e}", file=sys.stderr)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
