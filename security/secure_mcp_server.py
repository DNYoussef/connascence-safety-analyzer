#!/usr/bin/env python3
"""
Secure MCP Server Integration

Integrates enterprise security controls with the MCP server for 
safe deployment in enterprise environments with authentication,
authorization, audit logging, and secure operations.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
import functools

from .enterprise_security import (
    SecurityManager, SecurityContext, UserRole, AuditEventType,
    require_auth, SecurityLevel
)

logger = logging.getLogger(__name__)


class SecureMCPServer:
    """MCP Server with integrated enterprise security controls."""
    
    def __init__(self, base_mcp_server, security_config_path: Optional[Path] = None,
                 air_gapped: bool = False):
        """Initialize secure MCP server wrapper."""
        
        self.base_server = base_mcp_server
        self.security_manager = SecurityManager(
            config_path=security_config_path,
            air_gapped=air_gapped
        )
        
        # Wrap all MCP tools with security
        self._secure_tools = {}
        self._setup_secure_tools()
        
        logger.info("Secure MCP server initialized")
    
    def authenticate(self, username: str, password: str, ip_address: str) -> Optional[Dict[str, Any]]:
        """Authenticate user and return session token."""
        context = self.security_manager.authenticate_user(username, password, ip_address)
        
        if context:
            return {
                "success": True,
                "session_token": context.session_token,
                "expires_at": context.expires_at.isoformat(),
                "user_id": context.user_id,
                "username": context.username,
                "roles": [role.value for role in context.roles],
                "security_clearance": context.security_clearance.value
            }
        
        return {
            "success": False,
            "error": "Invalid credentials",
            "code": "AUTHENTICATION_FAILED"
        }
    
    def logout(self, session_token: str) -> Dict[str, Any]:
        """Logout user and invalidate session."""
        success = self.security_manager.invalidate_session(session_token)
        
        return {
            "success": success,
            "message": "Logged out successfully" if success else "Session not found"
        }
    
    def get_tools(self, session_token: str, ip_address: str) -> List[Dict[str, Any]]:
        """Get available tools based on user permissions."""
        context = self.security_manager.validate_session(session_token, ip_address)
        
        if not context:
            return []
        
        # Filter tools based on user permissions
        available_tools = []
        
        for tool_name, tool_config in self._secure_tools.items():
            required_permission = tool_config.get("permission", "")
            if not required_permission:
                available_tools.append(tool_config["definition"])
                continue
            
            resource, action = required_permission.split(':') if ':' in required_permission else (required_permission, 'execute')
            
            if self.security_manager.check_permission(context, resource, action):
                available_tools.append(tool_config["definition"])
        
        return available_tools
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any],
                    session_token: str, ip_address: str) -> Dict[str, Any]:
        """Execute tool with security checks."""
        
        # Validate session
        context = self.security_manager.validate_session(session_token, ip_address)
        if not context:
            return {
                "error": "Invalid or expired session",
                "code": "AUTHENTICATION_REQUIRED"
            }
        
        # Check if tool exists
        if tool_name not in self._secure_tools:
            return {
                "error": f"Unknown tool: {tool_name}",
                "code": "UNKNOWN_TOOL"
            }
        
        tool_config = self._secure_tools[tool_name]
        
        # Check permissions
        required_permission = tool_config.get("permission", "")
        if required_permission:
            resource, action = required_permission.split(':') if ':' in required_permission else (required_permission, 'execute')
            
            if not self.security_manager.check_permission(context, resource, action):
                return {
                    "error": f"Permission denied for {tool_name}",
                    "code": "PERMISSION_DENIED"
                }
        
        # Check rate limiting
        if not self.security_manager.check_rate_limit(context, tool_name):
            return {
                "error": "Rate limit exceeded",
                "code": "RATE_LIMITED"
            }
        
        # Log tool execution start
        self.security_manager.log_analysis_event(
            context,
            AuditEventType.ANALYSIS_START,
            tool_name,
            {"arguments": self._sanitize_arguments(arguments)}
        )
        
        try:
            # Execute the actual tool
            start_time = datetime.utcnow()
            
            # Add security context to arguments for tools that need it
            secure_arguments = {
                **arguments,
                "security_context": context,
                "security_manager": self.security_manager
            }
            
            result = self.base_server.get_tool_result(tool_name, secure_arguments)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Log successful completion
            self.security_manager.log_analysis_event(
                context,
                AuditEventType.ANALYSIS_COMPLETE,
                tool_name,
                {
                    "execution_time_seconds": execution_time,
                    "result_size": len(json.dumps(result)) if result else 0
                }
            )
            
            # Filter sensitive data from results
            filtered_result = self._filter_sensitive_data(result, context)
            
            return filtered_result
            
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            
            # Log failure
            self.security_manager.log_analysis_event(
                context,
                AuditEventType.ANALYSIS_COMPLETE,
                tool_name,
                {"error": str(e), "result": "failure"}
            )
            
            return {
                "error": f"Tool execution failed: {str(e)}",
                "code": "EXECUTION_ERROR"
            }
    
    def get_audit_trail(self, session_token: str, ip_address: str,
                       start_time: Optional[str] = None,
                       end_time: Optional[str] = None,
                       user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get audit trail for compliance reporting."""
        
        context = self.security_manager.validate_session(session_token, ip_address)
        if not context:
            return {
                "error": "Invalid or expired session",
                "code": "AUTHENTICATION_REQUIRED"
            }
        
        try:
            # Parse timestamps
            start_dt = datetime.fromisoformat(start_time) if start_time else None
            end_dt = datetime.fromisoformat(end_time) if end_time else None
            
            events = self.security_manager.get_audit_trail(
                context, start_dt, end_dt, user_id
            )
            
            # Convert events to JSON-serializable format
            audit_data = []
            for event in events:
                audit_data.append({
                    "timestamp": event.timestamp.isoformat(),
                    "event_type": event.event_type.value,
                    "user_id": event.user_id,
                    "ip_address": event.ip_address,
                    "resource": event.resource,
                    "action": event.action,
                    "result": event.result,
                    "details": event.details,
                    "integrity_verified": event.verify_integrity()
                })
            
            return {
                "success": True,
                "events": audit_data,
                "total_events": len(audit_data)
            }
            
        except PermissionError:
            return {
                "error": "Insufficient permissions to access audit logs",
                "code": "PERMISSION_DENIED"
            }
        except Exception as e:
            return {
                "error": f"Failed to retrieve audit trail: {str(e)}",
                "code": "AUDIT_ERROR"
            }
    
    def get_security_status(self, session_token: str, ip_address: str) -> Dict[str, Any]:
        """Get security status and metrics."""
        
        context = self.security_manager.validate_session(session_token, ip_address)
        if not context:
            return {
                "error": "Invalid or expired session",
                "code": "AUTHENTICATION_REQUIRED"
            }
        
        # Only security officers and admins can view security status
        if not (context.has_role(UserRole.SECURITY_OFFICER) or context.has_role(UserRole.ADMIN)):
            return {
                "error": "Insufficient permissions to view security status",
                "code": "PERMISSION_DENIED"
            }
        
        # Calculate security metrics
        active_sessions = len(self.security_manager.sessions)
        
        return {
            "success": True,
            "security_status": {
                "active_sessions": active_sessions,
                "air_gapped_mode": self.security_manager.air_gapped,
                "audit_logging_enabled": True,
                "encryption_enabled": self.security_manager.config.get("encryption_enabled", True),
                "rate_limiting_enabled": True,
                "session_timeout_hours": self.security_manager.config.get("session_timeout_hours", 8)
            },
            "user_context": {
                "user_id": context.user_id,
                "username": context.username,
                "roles": [role.value for role in context.roles],
                "security_clearance": context.security_clearance.value,
                "session_expires_at": context.expires_at.isoformat()
            }
        }
    
    def _setup_secure_tools(self):
        """Setup secure tool configurations with permissions."""
        
        # Get original tools from base server
        original_tools = self.base_server.get_tools()
        
        # Define permission mappings for tools
        tool_permissions = {
            "scan_path": "analysis:execute",
            "scan_diff": "analysis:execute", 
            "explain_finding": "analysis:read",
            "propose_autofix": "code:suggest_fixes",
            "enforce_policy": "policy:enforce",
            "baseline_snapshot": "analysis:manage",
            "get_scorecard": "reports:generate",
            "grammar_validate": "analysis:execute",
            "grammar_next_tokens": "code:generate",
            "suggest_refactors": "code:suggest_fixes",
            "verify_build_flags": "compliance:validate",
            "evidence_report": "reports:generate",
            "analyze_with_grammar": "analysis:execute",
            "get_quality_score": "analysis:read",
            "suggest_grammar_fixes": "code:suggest_fixes",
            "validate_safety_profile": "compliance:validate",
            "compare_quality_trends": "analysis:read"
        }
        
        # Security clearance requirements for sensitive tools
        clearance_requirements = {
            "verify_build_flags": SecurityLevel.CONFIDENTIAL,
            "validate_safety_profile": SecurityLevel.CONFIDENTIAL,
            "evidence_report": SecurityLevel.INTERNAL,
            "baseline_snapshot": SecurityLevel.INTERNAL
        }
        
        for tool in original_tools:
            tool_name = tool["name"]
            
            self._secure_tools[tool_name] = {
                "definition": tool,
                "permission": tool_permissions.get(tool_name, ""),
                "clearance": clearance_requirements.get(tool_name, SecurityLevel.PUBLIC),
                "rate_limit_weight": self._get_tool_rate_limit_weight(tool_name)
            }
    
    def _get_tool_rate_limit_weight(self, tool_name: str) -> int:
        """Get rate limit weight for tool (heavier operations use more tokens)."""
        heavy_tools = {
            "scan_path": 5,
            "scan_diff": 3,
            "analyze_with_grammar": 10,
            "suggest_grammar_fixes": 5,
            "validate_safety_profile": 8,
            "compare_quality_trends": 6
        }
        
        return heavy_tools.get(tool_name, 1)
    
    def _sanitize_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from arguments for audit logging."""
        sanitized = arguments.copy()
        
        # Remove potentially sensitive fields
        sensitive_fields = ["password", "token", "key", "secret", "credential"]
        
        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = "[REDACTED]"
        
        # Truncate very long strings to prevent log bloat
        for key, value in sanitized.items():
            if isinstance(value, str) and len(value) > 500:
                sanitized[key] = value[:500] + "...[TRUNCATED]"
        
        return sanitized
    
    def _filter_sensitive_data(self, result: Dict[str, Any], 
                              context: SecurityContext) -> Dict[str, Any]:
        """Filter sensitive data from results based on user clearance."""
        if not result:
            return result
        
        # Clone result to avoid modifying original
        filtered = json.loads(json.dumps(result))
        
        # Apply clearance-based filtering
        if context.security_clearance in [SecurityLevel.PUBLIC, SecurityLevel.INTERNAL]:
            # Remove detailed error information for lower clearance users
            if "error" in filtered and len(filtered.get("error", "")) > 100:
                filtered["error"] = "Detailed error information not available at your clearance level"
            
            # Remove internal file paths
            self._redact_file_paths(filtered)
        
        # Remove any remaining sensitive patterns
        self._redact_sensitive_patterns(filtered)
        
        return filtered
    
    def _redact_file_paths(self, data: Any, depth: int = 0) -> None:
        """Recursively redact internal file paths from data."""
        if depth > 10:  # Prevent infinite recursion
            return
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and ("/" in value or "\\" in value):
                    # Redact internal paths, keep just filename
                    if value.startswith("/") or "\\" in value:
                        data[key] = Path(value).name
                elif isinstance(value, (dict, list)):
                    self._redact_file_paths(value, depth + 1)
                    
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    self._redact_file_paths(item, depth + 1)
    
    def _redact_sensitive_patterns(self, data: Any, depth: int = 0) -> None:
        """Recursively redact sensitive patterns from data."""
        if depth > 10:
            return
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    # Redact potential API keys, tokens, etc.
                    if len(value) > 20 and any(pattern in key.lower() for pattern in ['key', 'token', 'secret', 'password']):
                        data[key] = "[REDACTED]"
                elif isinstance(value, (dict, list)):
                    self._redact_sensitive_patterns(value, depth + 1)
                    
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    self._redact_sensitive_patterns(item, depth + 1)


def create_secure_mcp_server(base_server, security_config: Optional[Dict[str, Any]] = None) -> SecureMCPServer:
    """Factory function to create secure MCP server with default configuration."""
    
    config_path = Path(security_config.get("config_path", ".connascence_security")) if security_config else None
    air_gapped = security_config.get("air_gapped", False) if security_config else False
    
    return SecureMCPServer(
        base_mcp_server=base_server,
        security_config_path=config_path,
        air_gapped=air_gapped
    )


# Security middleware for additional protection
class SecurityMiddleware:
    """Middleware for additional security checks and monitoring."""
    
    def __init__(self, security_manager: SecurityManager):
        self.security_manager = security_manager
        self.suspicious_activity_threshold = 10  # Suspicious requests per minute
        self.activity_tracking: Dict[str, List[float]] = {}
    
    def pre_request_check(self, context: SecurityContext, tool_name: str, 
                         arguments: Dict[str, Any]) -> bool:
        """Perform pre-request security checks."""
        
        # Track activity for anomaly detection
        now = datetime.utcnow().timestamp()
        user_activity = self.activity_tracking.get(context.user_id, [])
        
        # Clean old activity (older than 1 minute)
        user_activity = [timestamp for timestamp in user_activity if now - timestamp < 60]
        user_activity.append(now)
        self.activity_tracking[context.user_id] = user_activity
        
        # Check for suspicious activity
        if len(user_activity) > self.suspicious_activity_threshold:
            self.security_manager._log_audit_event(
                AuditEventType.SECURITY_VIOLATION,
                context.user_id,
                context.session_token,
                context.ip_address,
                "activity_monitoring",
                "suspicious_activity_detected",
                "blocked",
                {"requests_per_minute": len(user_activity)}
            )
            return False
        
        # Additional security checks can be added here
        return True
    
    def post_request_check(self, context: SecurityContext, tool_name: str,
                          result: Dict[str, Any]) -> bool:
        """Perform post-request security checks."""
        
        # Check for data exfiltration attempts
        result_size = len(json.dumps(result)) if result else 0
        if result_size > 1_000_000:  # 1MB threshold
            self.security_manager._log_audit_event(
                AuditEventType.SECURITY_VIOLATION,
                context.user_id,
                context.session_token,
                context.ip_address,
                tool_name,
                "large_data_export",
                "flagged",
                {"result_size_bytes": result_size}
            )
        
        return True