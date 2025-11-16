# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
Enhanced MCP Server for Connascence Analysis
============================================

Clean, standalone MCP server that Claude Code can access without tight
coupling to Claude Flow. Integrates all the architectural improvements:
- Central constants from config/central_constants.py
- Consolidated integrations from integrations/
- Unified import strategy from core/unified_imports.py

This provides a clean API for code analysis while maintaining separation
of concerns and avoiding tight coupling.
"""

from dataclasses import dataclass
import asyncio
import logging
from pathlib import Path

# Import using our unified import strategy
import sys
import time
import traceback
from typing import Any, Dict, List, Optional

from fixes.phase0.production_safe_assertions import ProductionAssert
from mcp.analysis_bridge import AnalyzerBridge

sys.path.append(str(Path(__file__).parent.parent))

try:
    from config.central_constants import MCPConstants, PerformanceLimits
except ImportError:
    # Fallback constants for MCP CLI
    class MCPConstants:
        MAX_PARALLEL_TASKS = 10
        TASK_TIMEOUT = 300
        SERVER_NAME = "connascence-mcp-enhanced"
        SERVER_VERSION = "2.0.0"
        SERVER_DESCRIPTION = "Enhanced MCP Server for Connascence Analysis"
        TOOL_ANALYZE_FILE = "analyze_file"
        TOOL_ANALYZE_WORKSPACE = "analyze_workspace"
        TOOL_GET_VIOLATIONS = "get_violations"
        TOOL_HEALTH_CHECK = "health_check"
        DEFAULT_MAX_FILE_SIZE = 1024  # KB
        DEFAULT_RATE_LIMIT = 60
        DEFAULT_AUDIT_ENABLED = True

    class PerformanceLimits:
        MAX_MEMORY_MB = 512
        MAX_FILES_PER_BATCH = 100


try:
    from core.unified_imports import IMPORT_MANAGER
except ImportError:
    # Fallback for when unified imports not available
    IMPORT_MANAGER = None

logger = logging.getLogger(__name__)


@dataclass
class AnalysisRequest:
    """Request for code analysis."""

    file_path: str
    analysis_type: str = "full"  # full, connascence, mece, nasa
    include_integrations: bool = True
    max_violations: Optional[int] = None
    format: str = "json"  # json, sarif, markdown


@dataclass
class AnalysisResponse:
    """Response from code analysis."""

    success: bool
    payload: Dict[str, Any]
    execution_time: float = 0.0
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = dict(self.payload)
        data["success"] = self.success
        data["execution_time"] = self.execution_time
        if self.error_message:
            data["error"] = self.error_message
        return data


class EnhancedConnascenceMCPServer:
    """
    Enhanced MCP server for connascence analysis.

    Provides clean API for Claude Code access with:
    - Centralized configuration
    - Consolidated integrations
    - Unified error handling
    - Rate limiting and security
    - Comprehensive logging
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.name = MCPConstants.SERVER_NAME
        self.version = MCPConstants.SERVER_VERSION
        self.description = MCPConstants.SERVER_DESCRIPTION

        # Initialize components with central constants
        self.rate_limiter = self._create_rate_limiter()
        self.audit_logger = self._create_audit_logger()

        # Security settings
        self.allowed_paths = self.config.get("allowed_paths", [])
        self.max_file_size = self.config.get("max_file_size", MCPConstants.DEFAULT_MAX_FILE_SIZE)

        # Load analyzer bridge and integrations
        self.analysis_bridge = AnalyzerBridge()
        self.integrations = self._load_integrations()

        # Register tools
        self._tools = self._register_tools()

        logger.info(f"Enhanced MCP Server initialized: {self.name} v{self.version}")

    def _create_rate_limiter(self):
        """Create rate limiter with central config."""
        try:
            from utils.config_loader import RateLimiter

            max_requests = self.config.get("rate_limit", MCPConstants.DEFAULT_RATE_LIMIT)
            return RateLimiter(max_requests=max_requests)
        except ImportError:
            logger.warning("RateLimiter not available, using mock")
            return self._create_mock_rate_limiter()

    def _create_mock_rate_limiter(self):
        """Create mock rate limiter for fallback."""

        class MockRateLimiter:
            def __init__(self, max_requests=60):
                self.max_requests = max_requests
                self.requests = {}

            def is_allowed(self, client_id="default"):
                ProductionAssert.not_none(client_id, "client_id")

                ProductionAssert.not_none(client_id, "client_id")

                return True

            def record_request(self, client_id="default"):
                ProductionAssert.not_none(client_id, "client_id")

                ProductionAssert.not_none(client_id, "client_id")

                pass

        return MockRateLimiter()

    def _create_audit_logger(self):
        """Create audit logger with central config."""

        class AuditLogger:
            def __init__(self, enabled=True):
                self.logs = []
                self.enabled = enabled

            def log(self, event: str, details: Optional[Dict[str, Any]] = None):
                ProductionAssert.not_none(event, "event")

                if self.enabled:
                    self.logs.append({"timestamp": time.time(), "event": event, "details": details or {}})

            def get_logs(self, limit: Optional[int] = None) -> List[Dict]:
                """Get audit logs."""
                logs = self.logs
                if limit:
                    logs = logs[-limit:]
                return logs

        audit_enabled = self.config.get("audit_enabled", MCPConstants.DEFAULT_AUDIT_ENABLED)
        return AuditLogger(enabled=audit_enabled)

    def _load_integrations(self):
        """Load consolidated integrations."""
        if IMPORT_MANAGER is not None:
            try:
                from core.unified_imports import ImportSpec

                spec = ImportSpec(module_name="integrations", required=False)
                integrations_result = IMPORT_MANAGER.import_module(spec)

                if integrations_result.has_module:
                    try:
                        # Get available integrations from consolidated module
                        get_available = getattr(integrations_result.module, "get_available_integrations", None)
                        if get_available:
                            return get_available(self.config)
                        else:
                            # Fallback: create integrations manually
                            return self._create_fallback_integrations(integrations_result.module)
                    except Exception as e:
                        logger.error(f"Failed to load integrations: {e}")
            except ImportError:
                logger.debug("Unified imports not available for integrations")

        # Try direct import fallback
        try:
            import integrations

            get_available = getattr(integrations, "get_available_integrations", None)
            if get_available:
                return get_available(self.config)
            else:
                return self._create_fallback_integrations(integrations)
        except ImportError:
            logger.debug("Direct integrations import failed")

        return {}

    def _create_fallback_integrations(self, integrations_module):
        """Create fallback integrations from module."""
        integrations = {}

        for name in ["BlackIntegration", "MyPyIntegration", "RuffIntegration"]:
            integration_class = getattr(integrations_module, name, None)
            if integration_class:
                try:
                    integration = integration_class(self.config)
                    if hasattr(integration, "is_available") and integration.is_available():
                        integrations[name.lower().replace("integration", "")] = integration
                except Exception as e:
                    logger.debug(f"Failed to create {name}: {e}")

        return integrations

    def _register_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register MCP tools with metadata."""
        tools = {
            MCPConstants.TOOL_ANALYZE_FILE: {
                "description": "Analyze a single file for connascence violations",
                "parameters": {
                    "file_path": {"type": "string", "description": "Path to file to analyze"},
                    "analysis_type": {
                        "type": "string",
                        "description": "Type of analysis (full, connascence, mece, nasa)",
                        "default": "full",
                    },
                    "include_integrations": {
                        "type": "boolean",
                        "description": "Include external tool integrations",
                        "default": True,
                    },
                    "format": {"type": "string", "description": "Output format (json, sarif)", "default": "json"},
                },
            },
            MCPConstants.TOOL_ANALYZE_WORKSPACE: {
                "description": "Analyze entire workspace/directory for connascence violations",
                "parameters": {
                    "workspace_path": {"type": "string", "description": "Path to workspace to analyze"},
                    "analysis_type": {
                        "type": "string",
                        "description": "Type of analysis (full, connascence, mece, nasa)",
                        "default": "full",
                    },
                    "file_patterns": {"type": "array", "description": "File patterns to include", "default": ["*.py"]},
                    "include_integrations": {
                        "type": "boolean",
                        "description": "Include external tool integrations",
                        "default": True,
                    },
                },
            },
            MCPConstants.TOOL_GET_VIOLATIONS: {
                "description": "Get violations by type or severity",
                "parameters": {
                    "file_path": {"type": "string", "description": "Path to file"},
                    "violation_type": {
                        "type": "string",
                        "description": "Type of violations to retrieve",
                        "optional": True,
                    },
                    "severity": {
                        "type": "string",
                        "description": "Severity filter (critical, high, medium, low)",
                        "optional": True,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of violations to return",
                        "default": 100,
                    },
                },
            },
            MCPConstants.TOOL_HEALTH_CHECK: {
                "description": "Check health status of the analyzer and integrations",
                "parameters": {},
            },
        }

        return tools

    # =================================================================
    # MCP TOOL IMPLEMENTATIONS
    # =================================================================

    async def analyze_file(
        self,
        file_path: str,
        *,
        client_id: str = "mcp-cli",
        _apply_guard: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """Analyze a single file for connascence violations."""
        start_time = time.time()

        try:
            if _apply_guard:
                self._guard_request(MCPConstants.TOOL_ANALYZE_FILE, client_id, {"file_path": file_path})

            # Create analysis request
            request = AnalysisRequest(
                file_path=file_path,
                analysis_type=kwargs.get("analysis_type", "full"),
                include_integrations=kwargs.get("include_integrations", True),
                format=kwargs.get("format", "json"),
            )

            # Log the request
            self.audit_logger.log(
                "analyze_file_request", {"file_path": file_path, "analysis_type": request.analysis_type}
            )

            # Validate request
            validation_result = self._validate_analysis_request(request)
            if not validation_result["valid"]:
                return self._create_error_response(request, validation_result["error"], start_time)

            # Perform analysis
            analysis_result = await self._perform_analysis(request)

            # Add execution time
            analysis_result.execution_time = time.time() - start_time

            # Log completion
            self.audit_logger.log(
                "analyze_file_complete",
                {
                    "file_path": file_path,
                    "success": analysis_result.success,
                    "violation_count": len(analysis_result.payload.get("findings", [])),
                    "execution_time": analysis_result.execution_time,
                },
            )

            return analysis_result.to_dict()

        except Exception as e:
            error_msg = f"Analysis failed: {e!s}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")

            return self._create_error_response(AnalysisRequest(file_path=file_path), error_msg, start_time).to_dict()

    async def analyze_workspace(
        self,
        workspace_path: str,
        *,
        client_id: str = "mcp-cli",
        **kwargs,
    ) -> Dict[str, Any]:
        """Analyze entire workspace for connascence violations."""
        start_time = time.time()

        try:
            self._guard_request(
                MCPConstants.TOOL_ANALYZE_WORKSPACE,
                client_id,
                {"workspace_path": workspace_path},
            )
            workspace_path = Path(workspace_path)
            if not workspace_path.exists():
                return {
                    "success": False,
                    "error": f"Workspace path does not exist: {workspace_path}",
                    "execution_time": time.time() - start_time,
                }

            file_patterns = kwargs.get("file_patterns", ["*.py"])
            files_to_analyze = []

            # Find files matching patterns
            for pattern in file_patterns:
                files_to_analyze.extend(workspace_path.rglob(pattern))

            # Limit number of files for performance
            max_files = PerformanceLimits.MAX_FILES_PER_BATCH
            if len(files_to_analyze) > max_files:
                files_to_analyze = files_to_analyze[:max_files]
                logger.warning(f"Limited analysis to {max_files} files")

            analysis_type = kwargs.get("analysis_type", "full")
            bridge_result = await asyncio.to_thread(
                self.analysis_bridge.analyze_workspace,
                workspace_path,
                files_to_analyze,
                analysis_type,
            )

            return {
                "success": True,
                **bridge_result,
                "analysis_type": analysis_type,
                "files_considered": len(files_to_analyze),
                "metrics": {
                    "files_considered": len(files_to_analyze),
                    "file_patterns": file_patterns,
                    "execution_time": time.time() - start_time,
                },
            }

        except Exception as e:
            error_msg = f"Workspace analysis failed: {e!s}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")

            return {
                "success": False,
                "workspace_path": workspace_path,
                "error": error_msg,
                "execution_time": time.time() - start_time,
            }

    async def get_violations(
        self,
        file_path: str,
        *,
        client_id: str = "mcp-cli",
        **kwargs,
    ) -> Dict[str, Any]:
        """Get violations by type or severity."""
        try:
            self._guard_request("get_violations", client_id, {"file_path": file_path})
            # First analyze the file
            analysis_result = await self.analyze_file(
                file_path, client_id=client_id, _apply_guard=False, format="json"
            )

            if not analysis_result.get("success", False):
                return analysis_result

            violations = analysis_result.get("findings", [])

            # Apply filters
            violation_type = kwargs.get("violation_type")
            severity = kwargs.get("severity")
            limit = kwargs.get("limit", 100)

            if violation_type:
                violations = [v for v in violations if v.get("type") == violation_type]

            if severity:
                violations = [v for v in violations if v.get("severity") == severity]

            # Apply limit
            if limit and len(violations) > limit:
                violations = violations[:limit]

            return {
                "success": True,
                "file_path": file_path,
                "findings": violations,
                "total_found": len(violations),
                "filters_applied": {"violation_type": violation_type, "severity": severity, "limit": limit},
            }

        except Exception as e:
            error_msg = f"Failed to get violations: {e!s}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    async def health_check(self, *, client_id: str = "mcp-cli") -> Dict[str, Any]:
        """Check health status of analyzer and integrations."""
        try:
            self._guard_request(MCPConstants.TOOL_HEALTH_CHECK, client_id)
            analyzer_snapshot = self.analysis_bridge.health_snapshot()

            integrations_health: Dict[str, Any] = {}
            for name, integration in self.integrations.items():
                try:
                    is_available = integration.is_available() if hasattr(integration, "is_available") else True
                    version = integration.get_version() if hasattr(integration, "get_version") else "unknown"
                    integrations_health[name] = {
                        "available": is_available,
                        "version": version,
                        "type": type(integration).__name__,
                    }
                except Exception as exc:
                    integrations_health[name] = {"available": False, "error": str(exc)}

            return {
                "success": True,
                "timestamp": time.time(),
                "server": {
                    "name": self.name,
                    "version": self.version,
                    "status": "healthy",
                    "description": MCPConstants.SERVER_DESCRIPTION,
                },
                "analyzer": analyzer_snapshot,
                "integrations": integrations_health,
                "configuration": {
                    "rate_limit": self.rate_limiter.max_requests,
                    "audit_enabled": self.audit_logger.enabled,
                    "max_file_size_kb": self.max_file_size,
                    "import_status": IMPORT_MANAGER.get_import_status() if IMPORT_MANAGER else "fallback_mode",
                },
            }

        except Exception as e:
            error_msg = f"Health check failed: {e!s}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "timestamp": time.time()}

    # =================================================================
    # HELPER METHODS
    # =================================================================

    def _validate_analysis_request(self, request: AnalysisRequest) -> Dict[str, Any]:
        """Validate analysis request."""
        file_path = Path(request.file_path)

        # Check if file exists
        if not file_path.exists():
            return {"valid": False, "error": f"File does not exist: {request.file_path}"}

        # Check file size
        if file_path.stat().st_size > self.max_file_size * 1024:
            return {"valid": False, "error": f"File too large (max {self.max_file_size}KB): {request.file_path}"}

        # Check allowed paths (if configured)
        if self.allowed_paths:
            allowed = any(str(file_path).startswith(str(Path(allowed_path))) for allowed_path in self.allowed_paths)
            if not allowed:
                return {"valid": False, "error": f"File path not allowed: {request.file_path}"}

        return {"valid": True}

    async def _perform_analysis(self, request: AnalysisRequest) -> AnalysisResponse:
        """Perform the actual analysis."""
        try:
            core_payload = await asyncio.to_thread(
                self.analysis_bridge.analyze_file,
                request.file_path,
                request.analysis_type,
            )

            if request.include_integrations:
                core_payload["integrations"] = self._run_integrations(request)

            return AnalysisResponse(success=True, payload=core_payload)

        except Exception as e:
            return AnalysisResponse(
                success=False,
                payload={"target": request.file_path, "findings": [], "summary": {}},
                error_message=str(e),
            )

    def _count_by_severity(self, violations: List[Dict]) -> Dict[str, int]:
        """Count violations by severity."""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for violation in violations:
            severity = violation.get("severity", "medium")
            if severity in counts:
                counts[severity] += 1
        return counts

    def _count_by_type(self, violations: List[Dict]) -> Dict[str, int]:
        """Count violations by type."""
        counts = {}
        for violation in violations:
            violation_type = violation.get("type", "unknown")
            counts[violation_type] = counts.get(violation_type, 0) + 1
        return counts

    def _run_integrations(self, request: AnalysisRequest) -> Dict[str, Any]:
        """Run configured integrations for a file analysis."""
        integration_results: Dict[str, Any] = {}
        for name, integration in self.integrations.items():
            try:
                if hasattr(integration, "run_analysis"):
                    result = integration.run_analysis(request.file_path)
                    integration_results[name] = {
                        "success": getattr(result, "success", True),
                        "issues": getattr(result, "issues", []),
                    }
                else:
                    integration_results[name] = {"success": True, "issues": []}
            except Exception as exc:
                logger.warning("Integration %s failed: %s", name, exc)
                integration_results[name] = {"success": False, "error": str(exc)}
        return integration_results

    def _create_error_response(
        self, request: AnalysisRequest, error_message: str, start_time: float
    ) -> AnalysisResponse:
        """Create error response."""
        return AnalysisResponse(
            success=False,
            payload={"target": request.file_path, "findings": [], "summary": {}},
            error_message=error_message,
            execution_time=time.time() - start_time,
        )

    def _guard_request(
        self,
        tool_name: str,
        client_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Apply shared rate limiting + audit logging."""

        ProductionAssert.not_none(tool_name, "tool_name")
        ProductionAssert.not_none(client_id, "client_id")

        if not self.rate_limiter.check_rate_limit(client_id):
            raise RuntimeError("Rate limit exceeded")

        self.audit_logger.log(
            "tool_request",
            {
                "tool": tool_name,
                "client_id": client_id,
                "context": context or {},
                "timestamp": time.time(),
            },
        )

    # =================================================================
    # MCP PROTOCOL METHODS
    # =================================================================

    def list_tools(self) -> List[Dict[str, Any]]:
        """List available MCP tools."""
        return [{"name": tool_name, **tool_info} for tool_name, tool_info in self._tools.items()]

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool."""
        if name not in self._tools:
            return {"success": False, "error": f"Tool '{name}' not found"}

        try:
            client_id = arguments.pop("client_id", "mcp-tool")

            # Route to appropriate method
            if name == MCPConstants.TOOL_ANALYZE_FILE:
                return await self.analyze_file(client_id=client_id, **arguments)
            elif name == MCPConstants.TOOL_ANALYZE_WORKSPACE:
                return await self.analyze_workspace(client_id=client_id, **arguments)
            elif name == MCPConstants.TOOL_GET_VIOLATIONS:
                return await self.get_violations(client_id=client_id, **arguments)
            elif name == MCPConstants.TOOL_HEALTH_CHECK:
                return await self.health_check(client_id=client_id)
            else:
                return {"success": False, "error": f"Tool '{name}' not implemented"}

        except Exception as e:
            error_msg = f"Tool execution failed: {e!s}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            return {"success": False, "error": error_msg}


# =============================================================================
# CONVENIENCE FUNCTIONS FOR CLAUDE CODE INTEGRATION
# =============================================================================


def create_enhanced_mcp_server(config: Optional[Dict] = None) -> EnhancedConnascenceMCPServer:
    """Create enhanced MCP server instance."""
    return EnhancedConnascenceMCPServer(config)


def get_server_info() -> Dict[str, Any]:
    """Get server information for Claude Code integration."""
    return {
        "name": MCPConstants.SERVER_NAME,
        "version": MCPConstants.SERVER_VERSION,
        "description": MCPConstants.SERVER_DESCRIPTION,
        "tools": [
            MCPConstants.TOOL_ANALYZE_FILE,
            MCPConstants.TOOL_ANALYZE_WORKSPACE,
            MCPConstants.TOOL_GET_VIOLATIONS,
            MCPConstants.TOOL_HEALTH_CHECK,
        ],
        "features": [
            "Connascence analysis",
            "NASA compliance checking",
            "MECE duplication detection",
            "External tool integrations",
            "Rate limiting",
            "Audit logging",
        ],
    }


# Export for Claude Code usage
__all__ = [
    "AnalysisRequest",
    "AnalysisResponse",
    "EnhancedConnascenceMCPServer",
    "create_enhanced_mcp_server",
    "get_server_info",
]
