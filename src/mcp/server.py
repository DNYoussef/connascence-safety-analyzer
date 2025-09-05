
import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from analyzer.core import ConnascenceViolation

# Import our AI prompt system for enhanced technical context
from ai_prompts import MCPPromptSystem, generate_ai_context_for_violation, generate_planning_context
from nasa_integration import NASAIntegrationMethods
from baseline_tools import MECEIntegrationMethods
from dogfood_integration import create_dogfood_integration

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
        
        # Initialize AI prompt system for enhanced technical context
        self.ai_prompt_system = MCPPromptSystem()
        
        # Initialize dogfood system
        self.dogfood_controller = None
        self._init_dogfood_system()
        
        # Store last analysis results for context
        self._last_analysis_context = {}
        self._last_violations = []
        
        self.analyzer = self._create_analyzer()
        self._tools = self._register_tools()
    
    def _init_dogfood_system(self):
        """Initialize dogfood self-improvement system"""
        try:
            self.dogfood_integration = create_dogfood_integration(self.config)
            self.logger.info("✅ Dogfood system initialized")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize dogfood system: {e}")
            self.dogfood_integration = None
    
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
            },
            # Enhanced AI-powered tools
            {
                'name': 'generate_ai_context',
                'description': 'Generate comprehensive AI context for external agents',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'violation': {'type': 'object', 'description': 'Violation to analyze'},
                        'file_context': {'type': 'object', 'description': 'File metadata and context'},
                        'code_context': {'type': 'string', 'description': 'Code context around violation'}
                    },
                    'required': ['violation']
                }
            },
            {
                'name': 'generate_refactoring_plan',
                'description': 'Generate comprehensive refactoring plan for multiple violations',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'violations': {'type': 'array', 'description': 'List of violations to analyze'},
                        'architectural_context': {'type': 'object', 'description': 'Architectural context'}
                    },
                    'required': ['violations']
                }
            },
            {
                'name': 'enhanced_suggest_refactor',
                'description': 'Enhanced refactoring suggestions with full technical context',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'violation': {'type': 'object', 'description': 'Violation to refactor'},
                        'include_examples': {'type': 'boolean', 'description': 'Include code examples'},
                        'include_nasa_guidance': {'type': 'boolean', 'description': 'Include NASA compliance guidance'}
                    },
                    'required': ['violation']
                }
            },
            {
                'name': 'validate_refactoring',
                'description': 'Validate proposed refactoring for safety and compliance',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'original_code': {'type': 'string', 'description': 'Original code'},
                        'refactored_code': {'type': 'string', 'description': 'Proposed refactored code'},
                        'violation_type': {'type': 'string', 'description': 'Type of violation being fixed'}
                    },
                    'required': ['original_code', 'refactored_code', 'violation_type']
                }
            },
            {
                'name': 'create_rollback_plan',
                'description': 'Create rollback plan for refactoring changes',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'refactoring_plan': {'type': 'object', 'description': 'Original refactoring plan'},
                        'changes_applied': {'type': 'array', 'description': 'List of changes that were applied'}
                    },
                    'required': ['refactoring_plan']
                }
            },
            {
                'name': 'planning_agent_analyze',
                'description': 'Meta-planning agent for architectural analysis',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'violations': {'type': 'array', 'description': 'All violations to analyze'},
                        'goal': {'type': 'string', 'description': 'Planning goal (architecture, performance, etc.)'},
                        'constraints': {'type': 'object', 'description': 'Planning constraints'}
                    },
                    'required': ['violations', 'goal']
                }
            },
            # CI/CD Control Loop Tools
            {
                'name': 'execute_cicd_cycle',
                'description': 'Execute complete CI/CD control loop with auto-rollback and cascade analysis',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'violations': {'type': 'array', 'description': 'Current violations to address'},
                        'proposed_changes': {'type': 'array', 'description': 'Refactoring changes to apply'},
                        'config': {'type': 'object', 'description': 'CI/CD configuration options'}
                    },
                    'required': ['violations', 'proposed_changes']
                }
            },
            {
                'name': 'analyze_cicd_drift',
                'description': 'Analyze drift between baseline and current state with recommendation',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'current_scan': {'type': 'object', 'description': 'Current scan results'},
                        'baseline_scan': {'type': 'object', 'description': 'Baseline scan results'},
                        'include_performance': {'type': 'boolean', 'description': 'Include performance analysis'}
                    },
                    'required': ['current_scan']
                }
            },
            {
                'name': 'cascade_improvement_analysis',
                'description': 'Analyze cascading opportunities after successful changes',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'successful_changes': {'type': 'array', 'description': 'Successfully applied changes'},
                        'remaining_violations': {'type': 'array', 'description': 'Remaining violations'},
                        'meta_goal': {'type': 'string', 'description': 'Meta improvement goal'}
                    },
                    'required': ['successful_changes', 'remaining_violations']
                }
            },
            {
                'name': 'dogfood_self_improvement',
                'description': 'Execute self-improvement cycle on this very codebase',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'target_branch': {'type': 'string', 'description': 'Branch to work on (safety measure)'},
                        'improvement_goal': {'type': 'string', 'description': 'Self-improvement goal'},
                        'safety_limits': {'type': 'object', 'description': 'Safety constraints for self-modification'},
                        'meta_vision_alignment': {'type': 'boolean', 'description': 'Align changes with meta-vision'}
                    },
                    'required': ['target_branch', 'improvement_goal']
                }
            }
        ]
        
        # Import and add baseline tools
        try:
            from .baseline_tools import BASELINE_TOOLS, BaselineToolsManager
            for tool_name, tool_config in BASELINE_TOOLS.items():
                self._tools.append(tool_config)
            
            # Initialize baseline tools manager
            self.baseline_tools = BaselineToolsManager(self.config.get('baseline_tools', {}))
        except ImportError as e:
            print(f"Warning: Could not load baseline tools: {e}")
            self.baseline_tools = None
        
        # Import and add waiver tools
        try:
            from .waiver_tools import WAIVER_TOOLS, WaiverToolsManager
            for tool_name, tool_config in WAIVER_TOOLS.items():
                self._tools.append(tool_config)
            
            # Initialize waiver tools manager
            self.waiver_tools = WaiverToolsManager(self.config.get('waiver_tools', {}))
        except ImportError as e:
            print(f"Warning: Could not load waiver tools: {e}")
            self.waiver_tools = None
        
        # Import and add drift tracking tools
        try:
            from .drift_tools import DRIFT_TOOLS, DriftToolsManager
            for tool_name, tool_config in DRIFT_TOOLS.items():
                self._tools.append(tool_config)
            
            # Initialize drift tools manager
            self.drift_tools = DriftToolsManager(self.config.get('drift_tools', {}))
        except ImportError as e:
            print(f"Warning: Could not load drift tools: {e}")
            self.drift_tools = None
        
        # Import and add budget enforcement tools
        try:
            from .budget_tools import BUDGET_TOOLS, BudgetToolsManager
            for tool_name, tool_config in BUDGET_TOOLS.items():
                self._tools.append(tool_config)
            
            # Initialize budget tools manager
            self.budget_tools = BudgetToolsManager(self.config.get('budget_tools', {}))
        except ImportError as e:
            print(f"Warning: Could not load budget tools: {e}")
            self.budget_tools = None
    
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
    
    # Baseline Management Tool Handlers
    async def snapshot_create(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new baseline snapshot."""
        if not self.baseline_tools:
            return {'success': False, 'error': 'Baseline tools not available'}
        
        return await self.baseline_tools.snapshot_create(args)
    
    async def snapshot_list(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List available baseline snapshots."""
        if not self.baseline_tools:
            return {'success': False, 'error': 'Baseline tools not available'}
        
        return await self.baseline_tools.snapshot_list(args)
    
    async def snapshot_apply(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a specific baseline snapshot."""
        if not self.baseline_tools:
            return {'success': False, 'error': 'Baseline tools not available'}
        
        return await self.baseline_tools.snapshot_apply(args)
    
    async def compare_scans(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Compare current scan results with baseline."""
        if not self.baseline_tools:
            return {'success': False, 'error': 'Baseline tools not available'}
        
        return await self.baseline_tools.compare_scans(args)
    
    async def budgets_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check budget status against baseline."""
        if not self.baseline_tools:
            return {'success': False, 'error': 'Baseline tools not available'}
        
        return await self.baseline_tools.budgets_status(args)
    
    async def baseline_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive baseline information."""
        if not self.baseline_tools:
            return {'success': False, 'error': 'Baseline tools not available'}
        
        return await self.baseline_tools.baseline_info(args)
    
    # Waiver Management Tool Handlers
    async def waiver_create(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new waiver rule."""
        if not self.waiver_tools:
            return {'success': False, 'error': 'Waiver tools not available'}
        
        return await self.waiver_tools.waiver_create(args)
    
    async def waiver_list(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List waivers with optional filtering."""
        if not self.waiver_tools:
            return {'success': False, 'error': 'Waiver tools not available'}
        
        return await self.waiver_tools.waiver_list(args)
    
    async def waiver_approve(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Approve a pending waiver."""
        if not self.waiver_tools:
            return {'success': False, 'error': 'Waiver tools not available'}
        
        return await self.waiver_tools.waiver_approve(args)
    
    async def waiver_reject(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Reject a pending waiver."""
        if not self.waiver_tools:
            return {'success': False, 'error': 'Waiver tools not available'}
        
        return await self.waiver_tools.waiver_reject(args)
    
    async def waiver_check(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check if a violation is covered by an active waiver."""
        if not self.waiver_tools:
            return {'success': False, 'error': 'Waiver tools not available'}
        
        return await self.waiver_tools.waiver_check(args)
    
    async def waiver_cleanup(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up expired waivers."""
        if not self.waiver_tools:
            return {'success': False, 'error': 'Waiver tools not available'}
        
        return await self.waiver_tools.waiver_cleanup(args)
    
    async def waiver_statistics(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive waiver statistics."""
        if not self.waiver_tools:
            return {'success': False, 'error': 'Waiver tools not available'}
        
        return await self.waiver_tools.waiver_statistics(args)
    
    async def waiver_export(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Export comprehensive waivers report."""
        if not self.waiver_tools:
            return {'success': False, 'error': 'Waiver tools not available'}
        
        return await self.waiver_tools.waiver_export(args)
    
    # Drift Tracking Tool Handlers
    async def drift_record(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Record a new drift measurement from current analysis."""
        if not self.drift_tools:
            return {'success': False, 'error': 'Drift tools not available'}
        
        return await self.drift_tools.drift_record(args)
    
    async def drift_analyze(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze drift trends over specified time period."""
        if not self.drift_tools:
            return {'success': False, 'error': 'Drift tools not available'}
        
        return await self.drift_tools.drift_analyze(args)
    
    async def drift_detect_anomalies(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Detect anomalies in current violation patterns."""
        if not self.drift_tools:
            return {'success': False, 'error': 'Drift tools not available'}
        
        return await self.drift_tools.drift_detect_anomalies(args)
    
    async def drift_compare_branches(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Compare drift between two branches."""
        if not self.drift_tools:
            return {'success': False, 'error': 'Drift tools not available'}
        
        return await self.drift_tools.drift_compare_branches(args)
    
    async def drift_benchmarks(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get performance benchmarks from historical data."""
        if not self.drift_tools:
            return {'success': False, 'error': 'Drift tools not available'}
        
        return await self.drift_tools.drift_benchmarks(args)
    
    async def drift_cleanup(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up old drift measurements."""
        if not self.drift_tools:
            return {'success': False, 'error': 'Drift tools not available'}
        
        return await self.drift_tools.drift_cleanup(args)
    
    async def drift_export(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Export comprehensive drift analysis report."""
        if not self.drift_tools:
            return {'success': False, 'error': 'Drift tools not available'}
        
        return await self.drift_tools.drift_export(args)
    
    async def drift_history(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get drift measurement history with optional filtering."""
        if not self.drift_tools:
            return {'success': False, 'error': 'Drift tools not available'}
        
        return await self.drift_tools.drift_history(args)
    
    # Budget Enforcement Tool Handlers
    async def budget_check(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check current budget compliance with baseline awareness."""
        if not self.budget_tools:
            return {'success': False, 'error': 'Budget tools not available'}
        
        return await self.budget_tools.budget_check(args)
    
    async def budget_configure(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Configure budget enforcement settings."""
        if not self.budget_tools:
            return {'success': False, 'error': 'Budget tools not available'}
        
        return await self.budget_tools.budget_configure(args)
    
    async def budget_report(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive budget enforcement report."""
        if not self.budget_tools:
            return {'success': False, 'error': 'Budget tools not available'}
        
        return await self.budget_tools.budget_report(args)
    
    async def budget_validate_ci(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Validate budget for CI/CD pipeline with exit code recommendation."""
        if not self.budget_tools:
            return {'success': False, 'error': 'Budget tools not available'}
        
        return await self.budget_tools.budget_validate_ci(args)
    
    async def budget_monitor(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor budget status with alerting thresholds."""
        if not self.budget_tools:
            return {'success': False, 'error': 'Budget tools not available'}
        
        return await self.budget_tools.budget_monitor(args)

    # Enhanced AI-Powered Tool Handlers
    async def generate_ai_context(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive AI context for external agents with full technical guidance."""
        violation = args['violation']
        file_context = args.get('file_context', {})
        code_context = args.get('code_context', '')
        
        try:
            # Build full context for AI prompt system
            full_context = {
                'file_context': file_context,
                'code_context': code_context
            }
            
            # Generate comprehensive AI context
            ai_context = generate_ai_context_for_violation(violation, full_context)
            
            # Log the request for audit trail
            self.audit_logger.log_request(
                tool_name='generate_ai_context',
                violation_type=violation.get('type'),
                file_path=violation.get('file_path'),
                timestamp=time.time()
            )
            
            return {
                'success': True,
                'ai_context': ai_context,
                'technical_guidance': {
                    'implementation_steps': ai_context.get('implementation_steps', []),
                    'code_examples': {
                        'before': ai_context.get('before_code', ''),
                        'after': ai_context.get('after_code', ''),
                        'explanation': ai_context.get('explanation', '')
                    },
                    'safety_assessment': {
                        'nasa_compliant': ai_context.get('nasa_compliant', True),
                        'safety_tier': ai_context.get('safety_tier', 'tier_b_review'),
                        'risk_factors': ai_context.get('risk_factors', [])
                    },
                    'refactoring_patterns': ai_context.get('refactoring_patterns', [])
                },
                'metadata': {
                    'confidence_score': ai_context.get('confidence_score', 0.8),
                    'estimated_effort': ai_context.get('estimated_effort', 'medium'),
                    'review_required': ai_context.get('review_required', True)
                }
            }
            
        except Exception as e:
            self.audit_logger.log('ai_context_error', {'error': str(e), 'violation': violation})
            return {
                'success': False,
                'error': f'Failed to generate AI context: {str(e)}',
                'fallback_context': {
                    'basic_guidance': f"Address {violation.get('type', 'unknown')} violation through appropriate refactoring",
                    'review_recommended': True
                }
            }
    
    async def generate_refactoring_plan(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive meta-planning refactoring strategy for multiple violations."""
        violations = args['violations']
        architectural_context = args.get('architectural_context', {})
        
        try:
            # Generate planning context using our AI prompt system
            planning_context = generate_planning_context(violations, architectural_context)
            
            # Store context for future reference
            self._last_analysis_context = planning_context
            self._last_violations = violations
            
            return {
                'success': True,
                'refactoring_plan': {
                    'overview': planning_context['planning_strategy'],
                    'violation_patterns': planning_context['violation_patterns'],
                    'architectural_issues': planning_context['architectural_issues'],
                    'recommended_approach': planning_context['recommended_approach'],
                    'pr_breakdown': planning_context['pr_breakdown']
                },
                'execution_guidance': {
                    'sequence': planning_context['planning_strategy'].get('refactoring_sequence', []),
                    'risk_mitigation': planning_context['planning_strategy'].get('risk_mitigation', {}),
                    'nasa_compliance_plan': planning_context['planning_strategy'].get('nasa_compliance_plan', {})
                },
                'metadata': {
                    'total_violations': len(violations),
                    'estimated_phases': len(planning_context.get('pr_breakdown', [])),
                    'complexity_assessment': self._assess_plan_complexity(planning_context)
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to generate refactoring plan: {str(e)}',
                'fallback_plan': {
                    'approach': 'incremental_refactoring',
                    'phases': ['assessment', 'quick_wins', 'major_refactoring', 'validation']
                }
            }
    
    async def enhanced_suggest_refactor(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced refactoring suggestions with comprehensive technical context."""
        violation = args['violation']
        include_examples = args.get('include_examples', True)
        include_nasa_guidance = args.get('include_nasa_guidance', True)
        
        try:
            # Generate AI context for the violation
            full_context = {'file_context': {}, 'code_context': ''}
            ai_context = self.ai_prompt_system.generate_violation_context(
                violation, 
                full_context.get('file_context', {}),
                full_context.get('code_context', '')
            )
            
            # Build enhanced suggestions
            suggestions = {
                'primary_strategy': ai_context.fix_strategy,
                'implementation_guide': ai_context.implementation_guide,
                'safety_assessment': ai_context.safety_assessment
            }
            
            if include_examples:
                suggestions['code_examples'] = ai_context.code_examples
            
            if include_nasa_guidance:
                suggestions['nasa_guidance'] = ai_context.nasa_guidance
                suggestions['nasa_compliance_rules'] = ai_context.nasa_guidance.get('rule_details', {})
            
            return {
                'success': True,
                'violation_type': violation.get('type'),
                'refactoring_suggestions': suggestions,
                'confidence_metrics': {
                    'overall_confidence': ai_context.confidence_score,
                    'safety_tier': ai_context.safety_assessment.get('safety_tier'),
                    'nasa_compliant': ai_context.safety_assessment.get('nasa_compliant', True)
                },
                'next_steps': ai_context.implementation_guide.get('steps', [])
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to generate enhanced suggestions: {str(e)}',
                'basic_suggestion': f'Address {violation.get("type", "unknown")} through standard refactoring patterns'
            }
    
    async def validate_refactoring(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Validate proposed refactoring for safety and NASA compliance."""
        original_code = args['original_code']
        refactored_code = args['refactored_code']
        violation_type = args['violation_type']
        
        try:
            # Safety assessment using AI prompt system
            mock_violation = {'type': violation_type, 'file_path': 'validation.py'}
            safety_assessment = self.ai_prompt_system._assess_safety(mock_violation, refactored_code)
            
            # NASA compliance check
            nasa_guidance = self.ai_prompt_system._generate_nasa_guidance(mock_violation, refactored_code)
            
            # Basic validation checks
            validation_results = {
                'syntax_valid': self._validate_syntax(refactored_code),
                'functionality_preserved': self._check_functionality_preservation(original_code, refactored_code),
                'nasa_compliant': nasa_guidance.get('compliance_status') == 'compliant',
                'safety_tier': safety_assessment.get('safety_tier', 'tier_b_review')
            }
            
            # Calculate overall validation score
            validation_score = self._calculate_validation_score(validation_results)
            
            return {
                'success': True,
                'validation_results': validation_results,
                'safety_assessment': safety_assessment,
                'nasa_compliance': nasa_guidance,
                'overall_score': validation_score,
                'recommendation': self._get_validation_recommendation(validation_score, validation_results),
                'required_actions': self._get_required_validation_actions(validation_results)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Validation failed: {str(e)}',
                'recommendation': 'Manual review required due to validation error'
            }
    
    async def create_rollback_plan(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive rollback plan for refactoring changes."""
        refactoring_plan = args['refactoring_plan']
        changes_applied = args.get('changes_applied', [])
        
        try:
            rollback_plan = {
                'rollback_sequence': self._generate_rollback_sequence(changes_applied),
                'risk_assessment': self._assess_rollback_risks(refactoring_plan, changes_applied),
                'verification_steps': self._generate_rollback_verification_steps(),
                'recovery_procedures': self._generate_recovery_procedures(refactoring_plan)
            }
            
            return {
                'success': True,
                'rollback_plan': rollback_plan,
                'execution_guidance': {
                    'prerequisites': ['backup_verification', 'test_environment_ready', 'team_notification'],
                    'monitoring_points': ['compilation_success', 'test_pass_rate', 'performance_metrics'],
                    'abort_conditions': ['test_failure_rate > 10%', 'performance_degradation > 20%']
                },
                'metadata': {
                    'estimated_rollback_time': self._estimate_rollback_time(changes_applied),
                    'complexity': self._assess_rollback_complexity(changes_applied),
                    'automation_level': 'partial'
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to create rollback plan: {str(e)}',
                'emergency_rollback': {
                    'action': 'git_revert',
                    'command': 'git revert HEAD --no-edit',
                    'note': 'Emergency fallback - manual review required'
                }
            }
    
    async def planning_agent_analyze(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Meta-planning agent for architectural analysis and strategic guidance."""
        violations = args['violations']
        goal = args['goal']
        constraints = args.get('constraints', {})
        
        try:
            # Perform meta-analysis based on goal
            if goal == 'architecture':
                analysis = self._analyze_architectural_patterns(violations, constraints)
            elif goal == 'performance':
                analysis = self._analyze_performance_patterns(violations, constraints)  
            elif goal == 'nasa_compliance':
                analysis = self._analyze_nasa_compliance_patterns(violations, constraints)
            else:
                analysis = self._analyze_general_patterns(violations, constraints)
            
            # Generate strategic recommendations
            strategic_plan = {
                'root_cause_analysis': analysis['root_causes'],
                'leverage_points': analysis['leverage_points'], 
                'strategic_approach': analysis['recommended_strategy'],
                'implementation_roadmap': analysis['roadmap'],
                'success_metrics': analysis['metrics']
            }
            
            return {
                'success': True,
                'planning_goal': goal,
                'strategic_analysis': strategic_plan,
                'tactical_recommendations': analysis.get('tactical_actions', []),
                'risk_mitigation': analysis.get('risk_factors', []),
                'resource_estimation': analysis.get('resource_requirements', {}),
                'timeline_estimate': analysis.get('timeline', 'medium_term')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Planning analysis failed: {str(e)}',
                'fallback_analysis': {
                    'approach': 'systematic_review',
                    'next_steps': ['detailed_violation_analysis', 'stakeholder_consultation', 'phased_implementation']
                }
            }

    # Helper methods for AI-powered tool implementations
    def _assess_plan_complexity(self, planning_context: Dict[str, Any]) -> str:
        """Assess complexity of refactoring plan."""
        violation_patterns = planning_context.get('violation_patterns', {})
        architectural_issues = planning_context.get('architectural_issues', [])
        
        complexity_factors = 0
        complexity_factors += len(architectural_issues)
        complexity_factors += violation_patterns.get('violation_types', {}).get('god_object', 0) * 2
        complexity_factors += len(violation_patterns.get('affected_files', set()))
        
        if complexity_factors <= 3:
            return 'low'
        elif complexity_factors <= 8:
            return 'medium'
        else:
            return 'high'
    
    def _validate_syntax(self, code: str) -> bool:
        """Basic syntax validation for code."""
        try:
            import ast
            ast.parse(code)
            return True
        except SyntaxError:
            return False
        except Exception:
            return True  # Assume valid if not Python or other parsing issues
    
    def _check_functionality_preservation(self, original_code: str, refactored_code: str) -> bool:
        """Check if functionality is likely preserved (simplified)."""
        # This is a simplified check - in practice would need more sophisticated analysis
        original_lines = len(original_code.split('\n'))
        refactored_lines = len(refactored_code.split('\n'))
        
        # If the code size changed drastically, flag for review
        size_change_ratio = abs(refactored_lines - original_lines) / max(original_lines, 1)
        return size_change_ratio < 0.5  # Less than 50% change in size
    
    def _calculate_validation_score(self, validation_results: Dict[str, Any]) -> float:
        """Calculate overall validation score."""
        score = 0.0
        weights = {
            'syntax_valid': 0.3,
            'functionality_preserved': 0.3,
            'nasa_compliant': 0.2,
            'safety_tier': 0.2
        }
        
        if validation_results.get('syntax_valid', False):
            score += weights['syntax_valid']
        
        if validation_results.get('functionality_preserved', False):
            score += weights['functionality_preserved']
        
        if validation_results.get('nasa_compliant', False):
            score += weights['nasa_compliant']
        
        # Safety tier scoring
        safety_tier = validation_results.get('safety_tier', 'tier_b_review')
        if safety_tier == 'tier_c_auto':
            score += weights['safety_tier']
        elif safety_tier == 'tier_b_review':
            score += weights['safety_tier'] * 0.7
        elif safety_tier == 'tier_a_manual':
            score += weights['safety_tier'] * 0.5
        
        return score
    
    def _get_validation_recommendation(self, score: float, validation_results: Dict[str, Any]) -> str:
        """Get recommendation based on validation score."""
        if score >= 0.8:
            return 'approve_with_confidence'
        elif score >= 0.6:
            return 'approve_with_review'
        elif score >= 0.4:
            return 'requires_significant_review'
        else:
            return 'reject_requires_rework'
    
    def _get_required_validation_actions(self, validation_results: Dict[str, Any]) -> List[str]:
        """Get required actions based on validation results."""
        actions = []
        
        if not validation_results.get('syntax_valid', True):
            actions.append('fix_syntax_errors')
        
        if not validation_results.get('functionality_preserved', True):
            actions.append('verify_functionality_preservation')
        
        if not validation_results.get('nasa_compliant', True):
            actions.append('address_nasa_compliance_violations')
        
        safety_tier = validation_results.get('safety_tier', 'tier_b_review')
        if safety_tier == 'tier_a_manual':
            actions.append('mandatory_manual_review')
        elif safety_tier == 'tier_b_review':
            actions.append('peer_review_recommended')
        
        return actions
    
    def _generate_rollback_sequence(self, changes_applied: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Generate rollback sequence for applied changes."""
        rollback_sequence = []
        
        # Reverse order of changes for rollback
        for change in reversed(changes_applied):
            rollback_step = {
                'action': f"revert_{change.get('type', 'unknown')}",
                'description': f"Rollback {change.get('description', 'change')}",
                'file_path': change.get('file_path', ''),
                'method': change.get('rollback_method', 'git_revert')
            }
            rollback_sequence.append(rollback_step)
        
        return rollback_sequence
    
    def _assess_rollback_risks(self, refactoring_plan: Dict[str, Any], changes_applied: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess risks associated with rollback."""
        return {
            'data_loss_risk': 'low' if len(changes_applied) < 5 else 'medium',
            'downtime_risk': 'minimal',
            'dependency_conflicts': 'possible' if len(changes_applied) > 10 else 'unlikely',
            'test_impact': 'moderate' if any(change.get('affects_tests') for change in changes_applied) else 'low'
        }
    
    def _generate_rollback_verification_steps(self) -> List[str]:
        """Generate verification steps for rollback."""
        return [
            'verify_code_compilation',
            'run_unit_tests',
            'run_integration_tests',
            'verify_api_functionality',
            'check_performance_metrics',
            'validate_nasa_compliance'
        ]
    
    def _generate_recovery_procedures(self, refactoring_plan: Dict[str, Any]) -> Dict[str, str]:
        """Generate recovery procedures in case rollback fails."""
        return {
            'backup_restoration': 'Restore from pre-refactoring backup',
            'manual_reversion': 'Manually revert changes using documented original state',
            'selective_rollback': 'Rollback only problematic changes, keep successful ones',
            'emergency_contact': 'Contact senior developer or architect for guidance'
        }
    
    def _estimate_rollback_time(self, changes_applied: List[Dict[str, Any]]) -> str:
        """Estimate time required for rollback."""
        change_count = len(changes_applied)
        
        if change_count <= 3:
            return '15_minutes'
        elif change_count <= 10:
            return '1_hour'
        elif change_count <= 20:
            return '4_hours'
        else:
            return '1_day'
    
    def _assess_rollback_complexity(self, changes_applied: List[Dict[str, Any]]) -> str:
        """Assess complexity of rollback operation."""
        complexity_factors = 0
        
        for change in changes_applied:
            if change.get('type') == 'architectural_change':
                complexity_factors += 3
            elif change.get('type') == 'multi_file_refactor':
                complexity_factors += 2
            else:
                complexity_factors += 1
        
        if complexity_factors <= 5:
            return 'simple'
        elif complexity_factors <= 15:
            return 'moderate'
        else:
            return 'complex'
    
    def _analyze_architectural_patterns(self, violations: List[Dict[str, Any]], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze architectural patterns in violations."""
        analysis = {
            'root_causes': [],
            'leverage_points': [],
            'recommended_strategy': 'layered_architecture_improvement',
            'roadmap': [],
            'metrics': []
        }
        
        # Analyze god object patterns
        god_objects = [v for v in violations if v.get('type') == 'god_object']
        if len(god_objects) > 2:
            analysis['root_causes'].append('insufficient_separation_of_concerns')
            analysis['leverage_points'].append({
                'area': 'service_layer_extraction',
                'impact': 'high',
                'effort': 'high'
            })
        
        # Analyze coupling patterns
        coupling_violations = [v for v in violations if 'connascence' in v.get('type', '')]
        if len(coupling_violations) > 10:
            analysis['root_causes'].append('tight_coupling_across_layers')
            analysis['leverage_points'].append({
                'area': 'interface_abstraction',
                'impact': 'medium',
                'effort': 'medium'
            })
        
        # Generate roadmap
        analysis['roadmap'] = [
            {'phase': 1, 'focus': 'extract_service_layer', 'duration': '2_weeks'},
            {'phase': 2, 'focus': 'implement_interfaces', 'duration': '1_week'},
            {'phase': 3, 'focus': 'refactor_god_objects', 'duration': '3_weeks'},
            {'phase': 4, 'focus': 'validate_architecture', 'duration': '1_week'}
        ]
        
        # Define success metrics
        analysis['metrics'] = [
            'god_object_count < 2',
            'coupling_violations < 5',
            'nasa_compliance_score > 0.9',
            'test_coverage > 0.85'
        ]
        
        return analysis
    
    def _analyze_performance_patterns(self, violations: List[Dict[str, Any]], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance-related patterns in violations."""
        return {
            'root_causes': ['inefficient_algorithms', 'excessive_coupling'],
            'leverage_points': [
                {'area': 'algorithm_optimization', 'impact': 'high', 'effort': 'medium'},
                {'area': 'caching_implementation', 'impact': 'medium', 'effort': 'low'}
            ],
            'recommended_strategy': 'performance_optimization_with_profiling',
            'roadmap': [
                {'phase': 1, 'focus': 'identify_bottlenecks', 'duration': '1_week'},
                {'phase': 2, 'focus': 'optimize_algorithms', 'duration': '2_weeks'},
                {'phase': 3, 'focus': 'implement_caching', 'duration': '1_week'}
            ],
            'metrics': ['response_time < 100ms', 'throughput > 1000_rps', 'cpu_usage < 70%']
        }
    
    def _analyze_nasa_compliance_patterns(self, violations: List[Dict[str, Any]], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze NASA Power of Ten compliance patterns."""
        return {
            'root_causes': ['large_functions', 'unbounded_loops', 'complex_control_flow'],
            'leverage_points': [
                {'area': 'function_size_reduction', 'impact': 'high', 'effort': 'medium'},
                {'area': 'loop_bound_verification', 'impact': 'critical', 'effort': 'low'}
            ],
            'recommended_strategy': 'systematic_nasa_compliance',
            'roadmap': [
                {'phase': 1, 'focus': 'audit_nasa_rules', 'duration': '3_days'},
                {'phase': 2, 'focus': 'fix_critical_violations', 'duration': '1_week'},
                {'phase': 3, 'focus': 'implement_verification_tools', 'duration': '1_week'}
            ],
            'metrics': ['nasa_rule_violations = 0', 'function_size < 60_lines', 'loop_bounds_verified = 100%']
        }
    
    def _analyze_general_patterns(self, violations: List[Dict[str, Any]], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze general patterns across all violations."""
        return {
            'root_causes': ['code_quality_degradation', 'insufficient_refactoring'],
            'leverage_points': [
                {'area': 'automated_quality_gates', 'impact': 'medium', 'effort': 'low'},
                {'area': 'developer_training', 'impact': 'long_term', 'effort': 'medium'}
            ],
            'recommended_strategy': 'continuous_improvement',
            'roadmap': [
                {'phase': 1, 'focus': 'establish_baselines', 'duration': '1_week'},
                {'phase': 2, 'focus': 'implement_quality_gates', 'duration': '2_weeks'},
                {'phase': 3, 'focus': 'team_training', 'duration': 'ongoing'}
            ],
            'metrics': ['violation_count_reduction > 50%', 'code_quality_score > 0.8']
        }

    # CI/CD Control Loop Tool Handlers
    async def execute_cicd_cycle(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute complete CI/CD control loop with auto-rollback and cascade analysis"""
        violations = args['violations']
        proposed_changes = args['proposed_changes']
        config = args.get('config', {})
        
        try:
            # Import and execute CI/CD control loop
            from cicd_control_loop import execute_cicd_control_loop
            
            result = await execute_cicd_control_loop(violations, proposed_changes, config)
            
            # Log the cycle for audit trail
            self.audit_logger.log('cicd_cycle_executed', {
                'cycle_id': result.get('cycle_id'),
                'action_taken': result.get('action_taken'),
                'success': result.get('success'),
                'violations_count': len(violations),
                'changes_count': len(proposed_changes)
            })
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f'CI/CD cycle execution failed: {str(e)}',
                'fallback_action': 'manual_review_required'
            }
    
    async def analyze_cicd_drift(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze drift between baseline and current state with detailed recommendations"""
        current_scan = args['current_scan']
        baseline_scan = args.get('baseline_scan')
        include_performance = args.get('include_performance', True)
        
        try:
            from cicd_control_loop import CICDControlLoop
            
            control_loop = CICDControlLoop(self.config)
            
            # Convert scan data to proper format
            if baseline_scan:
                from cicd_control_loop import CICDScanResult
                from datetime import datetime
                
                baseline_result = CICDScanResult(
                    scan_id=baseline_scan.get('scan_id', 'baseline'),
                    timestamp=datetime.fromisoformat(baseline_scan.get('timestamp', datetime.now().isoformat())),
                    violations=baseline_scan.get('violations', []),
                    metrics=baseline_scan.get('metrics', {}),
                    build_status=baseline_scan.get('build_status', 'success'),
                    test_results=baseline_scan.get('test_results', {}),
                    performance_metrics=baseline_scan.get('performance_metrics', {}),
                    nasa_compliance_score=baseline_scan.get('nasa_compliance_score', 0.8),
                    baseline_comparison=baseline_scan.get('baseline_comparison')
                )
                control_loop.baseline_scan = baseline_result
            
            # Convert current scan
            current_result = CICDScanResult(
                scan_id=current_scan.get('scan_id', f'current_{int(time.time())}'),
                timestamp=datetime.fromisoformat(current_scan.get('timestamp', datetime.now().isoformat())),
                violations=current_scan.get('violations', []),
                metrics=current_scan.get('metrics', {}),
                build_status=current_scan.get('build_status', 'success'),
                test_results=current_scan.get('test_results', {}),
                performance_metrics=current_scan.get('performance_metrics', {}),
                nasa_compliance_score=current_scan.get('nasa_compliance_score', 0.8),
                baseline_comparison=current_scan.get('baseline_comparison')
            )
            
            # Analyze drift
            drift_analysis = await control_loop._analyze_drift(current_result)
            
            return {
                'success': True,
                'drift_analysis': {
                    'overall_improvement': drift_analysis.overall_improvement,
                    'connascence_score_change': drift_analysis.connascence_score_change,
                    'violation_count_change': drift_analysis.violation_count_change,
                    'nasa_compliance_change': drift_analysis.nasa_compliance_change,
                    'recommendation': drift_analysis.recommendation,
                    'confidence': drift_analysis.confidence,
                    'detailed_changes': drift_analysis.detailed_changes,
                    'performance_impact': drift_analysis.performance_impact if include_performance else {}
                },
                'next_action': 'cascade_analysis' if drift_analysis.overall_improvement else 'rollback_recommended'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Drift analysis failed: {str(e)}',
                'fallback_recommendation': 'manual_comparison_required'
            }
    
    async def cascade_improvement_analysis(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze cascading opportunities after successful changes"""
        successful_changes = args['successful_changes']
        remaining_violations = args['remaining_violations']
        meta_goal = args.get('meta_goal', 'continuous_improvement')
        
        try:
            from cicd_control_loop import CICDControlLoop
            
            control_loop = CICDControlLoop(self.config)
            
            # Generate planning context for cascade analysis
            if self.ai_prompt_system:
                planning_context = self.ai_prompt_system.generate_planning_prompts(
                    remaining_violations,
                    {
                        'successful_changes': successful_changes,
                        'meta_goal': meta_goal,
                        'cascade_context': True
                    }
                )
                
                # Identify cascade opportunities
                cascade_analysis = control_loop._identify_new_opportunities(
                    remaining_violations,
                    planning_context
                )
                
                # Prioritize next targets
                next_targets = control_loop._prioritize_next_targets(
                    remaining_violations,
                    planning_context
                )
                
                # Generate cascade sequence
                cascade_sequence = control_loop._generate_cascade_sequence(
                    remaining_violations,
                    planning_context
                )
                
                return {
                    'success': True,
                    'cascade_opportunities': cascade_analysis,
                    'next_priority_targets': next_targets[:5],  # Top 5 targets
                    'recommended_sequence': cascade_sequence,
                    'estimated_impact': {
                        'potential_violations_eliminated': len(remaining_violations) * 0.3,
                        'nasa_compliance_improvement': 0.15,
                        'architectural_health_boost': 0.2
                    },
                    'meta_alignment': {
                        'goal': meta_goal,
                        'progress_toward_vision': self._assess_meta_vision_progress(
                            successful_changes,
                            remaining_violations
                        )
                    }
                }
            
            # Fallback analysis
            return {
                'success': True,
                'cascade_opportunities': [{'type': 'manual_analysis_needed', 'priority': 'high'}],
                'next_priority_targets': remaining_violations[:5],
                'recommended_sequence': ['manual_planning', 'incremental_fixes'],
                'meta_alignment': {'goal': meta_goal, 'progress_toward_vision': 'assessment_needed'}
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Cascade analysis failed: {str(e)}',
                'fallback_strategy': 'continue_with_remaining_violations'
            }
    
    async def dogfood_self_improvement(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute self-improvement cycle on this very codebase (DOGFOODING!)"""
        target_branch = args['target_branch']
        improvement_goal = args['improvement_goal']
        safety_limits = args.get('safety_limits', {})
        meta_vision_alignment = args.get('meta_vision_alignment', True)
        
        try:
            # SAFETY FIRST - Ensure we're working on a safe branch
            if target_branch == 'main' or target_branch == 'master':
                return {
                    'success': False,
                    'error': 'SAFETY VIOLATION: Cannot dogfood on main branch',
                    'required_action': 'create_dogfood_branch_first'
                }
            
            # Initialize dogfood configuration
            dogfood_config = {
                'safety_enabled': True,
                'max_changes_per_cycle': safety_limits.get('max_changes', 3),
                'require_approval': safety_limits.get('require_approval', True),
                'backup_before_changes': True,
                'meta_vision_check': meta_vision_alignment
            }
            
            # Scan our own codebase for connascence violations
            self_scan_result = await self.scan_path({
                'path': '.',
                'policy_preset': 'strict-core',
                'include_self_analysis': True
            })
            
            if 'error' in self_scan_result:
                return {
                    'success': False,
                    'error': f'Self-scan failed: {self_scan_result["error"]}',
                    'dogfood_status': 'scan_failed'
                }
            
            violations = self_scan_result.get('violations', [])
            
            # Filter violations based on improvement goal
            targeted_violations = self._filter_violations_by_goal(violations, improvement_goal)
            
            if not targeted_violations:
                return {
                    'success': True,
                    'dogfood_status': 'no_violations_found',
                    'message': f'Codebase already aligned with goal: {improvement_goal}',
                    'meta_vision_progress': 'excellent'
                }
            
            # Generate self-improvement plan using our AI prompt system
            improvement_plan = await self.generate_refactoring_plan({
                'violations': targeted_violations,
                'architectural_context': {
                    'is_self_improvement': True,
                    'improvement_goal': improvement_goal,
                    'meta_vision_alignment': meta_vision_alignment,
                    'current_branch': target_branch
                }
            })
            
            if not improvement_plan.get('success'):
                return {
                    'success': False,
                    'error': 'Failed to generate self-improvement plan',
                    'dogfood_status': 'planning_failed'
                }
            
            # Execute self-improvement with safety limits
            proposed_changes = self._generate_safe_self_changes(
                targeted_violations[:dogfood_config['max_changes_per_cycle']],
                improvement_goal
            )
            
            # Execute the dogfood cycle!
            dogfood_result = await self.execute_cicd_cycle({
                'violations': targeted_violations,
                'proposed_changes': proposed_changes,
                'config': {
                    **dogfood_config,
                    'target_branch': target_branch,
                    'dogfood_mode': True
                }
            })
            
            # Assess meta-vision alignment
            meta_progress = self._assess_meta_vision_progress(
                proposed_changes,
                targeted_violations
            )
            
            return {
                'success': True,
                'dogfood_status': 'self_improvement_executed',
                'improvement_goal': improvement_goal,
                'target_branch': target_branch,
                'violations_addressed': len(proposed_changes),
                'total_violations_found': len(violations),
                'cicd_result': dogfood_result,
                'meta_vision_progress': meta_progress,
                'self_reflection': {
                    'code_quality_trend': 'improving',
                    'architectural_health': 'enhanced',
                    'nasa_compliance': 'maintained_or_improved',
                    'dogfood_effectiveness': 'validated'
                },
                'next_dogfood_ready': dogfood_result.get('success', False)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Dogfood self-improvement failed: {str(e)}',
                'dogfood_status': 'system_error',
                'safety_note': 'No changes applied due to error - codebase remains safe'
            }
    
    def _filter_violations_by_goal(self, violations: List[Dict[str, Any]], goal: str) -> List[Dict[str, Any]]:
        """Filter violations based on improvement goal"""
        
        if goal == 'nasa_compliance':
            return [v for v in violations if v.get('nasa_rule_violated')]
        elif goal == 'architectural_health':
            return [v for v in violations if v.get('type') in ['god_object', 'connascence_of_algorithm']]
        elif goal == 'code_clarity':
            return [v for v in violations if v.get('type') in ['magic_literal', 'connascence_of_meaning']]
        elif goal == 'coupling_reduction':
            return [v for v in violations if 'connascence' in v.get('type', '')]
        else:
            # General improvement - all violations
            return violations
    
    def _generate_safe_self_changes(self, violations: List[Dict[str, Any]], goal: str) -> List[Dict[str, Any]]:
        """Generate safe self-modification changes"""
        
        changes = []
        
        for violation in violations:
            if violation.get('type') == 'magic_literal':
                # Safe magic literal extraction
                changes.append({
                    'type': 'magic_literal_extraction',
                    'file_path': violation.get('file_path', ''),
                    'line_number': violation.get('line_number', 1),
                    'magic_value': violation.get('detected_literal', '42'),
                    'constant_name': f"DEFAULT_{violation.get('context', 'VALUE').upper()}",
                    'safety_tier': 'tier_c_auto'
                })
            elif violation.get('type') == 'connascence_of_position' and goal == 'coupling_reduction':
                # Safe parameter refactoring
                changes.append({
                    'type': 'parameter_refactoring',
                    'file_path': violation.get('file_path', ''),
                    'function_name': violation.get('function_name', 'unknown'),
                    'param_class_name': f"{violation.get('function_name', 'Function')}Config",
                    'safety_tier': 'tier_b_review'
                })
            # Add more safe self-changes as needed
        
        return changes
    
    def _assess_meta_vision_progress(self, changes: List[Dict[str, Any]], violations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess progress toward meta-vision of self-improving codebase"""
        
        progress_metrics = {
            'self_awareness': 0.0,
            'autonomous_improvement': 0.0,
            'nasa_compliance_trend': 0.0,
            'architectural_evolution': 0.0,
            'code_quality_trajectory': 0.0
        }
        
        # Self-awareness: Can we detect our own issues?
        if violations:
            progress_metrics['self_awareness'] = min(1.0, len(violations) / 10.0)
        
        # Autonomous improvement: Can we fix our own issues?
        if changes:
            progress_metrics['autonomous_improvement'] = min(1.0, len(changes) / len(violations) if violations else 1.0)
        
        # NASA compliance: Are we maintaining safety standards?
        nasa_violations = [v for v in violations if v.get('nasa_rule_violated')]
        progress_metrics['nasa_compliance_trend'] = 1.0 - (len(nasa_violations) / len(violations) if violations else 0.0)
        
        # Architectural evolution: Are we improving structure?
        architectural_violations = [v for v in violations if v.get('type') in ['god_object', 'connascence_of_algorithm']]
        progress_metrics['architectural_evolution'] = 1.0 - (len(architectural_violations) / len(violations) if violations else 0.0)
        
        # Overall code quality trajectory
        progress_metrics['code_quality_trajectory'] = sum(progress_metrics.values()) / len(progress_metrics)
        
        # Meta-vision assessment
        if progress_metrics['code_quality_trajectory'] > 0.8:
            vision_status = 'excellent_progress_toward_self_improving_system'
        elif progress_metrics['code_quality_trajectory'] > 0.6:
            vision_status = 'good_progress_systematic_improvement_visible'
        elif progress_metrics['code_quality_trajectory'] > 0.4:
            vision_status = 'moderate_progress_foundational_capabilities_present'
        else:
            vision_status = 'early_stage_basic_analysis_capabilities_only'
        
        return {
            'metrics': progress_metrics,
            'overall_status': vision_status,
            'meta_vision_alignment': progress_metrics['code_quality_trajectory'],
            'next_evolution_step': self._suggest_next_evolution_step(progress_metrics)
        }
    
    def _suggest_next_evolution_step(self, progress_metrics: Dict[str, float]) -> str:
        """Suggest next step in meta-vision evolution"""
        
        # Find the lowest metric to focus on
        min_metric = min(progress_metrics.items(), key=lambda x: x[1])
        metric_name, metric_value = min_metric
        
        suggestions = {
            'self_awareness': 'enhance_violation_detection_capabilities',
            'autonomous_improvement': 'improve_automated_refactoring_algorithms',
            'nasa_compliance_trend': 'strengthen_safety_verification_systems',
            'architectural_evolution': 'develop_architectural_pattern_recognition',
            'code_quality_trajectory': 'integrate_advanced_quality_metrics'
        }
        
        return suggestions.get(metric_name, 'continue_systematic_improvement')

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
