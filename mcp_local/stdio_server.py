#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
MCP Stdio Server for Connascence Analyzer
==========================================

Proper MCP protocol implementation using the official mcp SDK.
This server communicates via stdio using JSON-RPC 2.0 as per MCP spec.
"""

import asyncio
import importlib
import importlib.util
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Sequence

# Force UTF-8 encoding for Windows
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Import the official mcp SDK (no conflict now that local dir is mcp_local/)
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Add parent directory for local imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import our analyzer from the renamed mcp_local directory
from mcp_local.enhanced_server import create_enhanced_mcp_server, get_server_info

# Configure logging to stderr to avoid polluting stdio
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)

# Create the MCP server instance
server = Server("connascence-analyzer")

# Store the analyzer server instance
_analyzer_server = None


def get_analyzer():
    """Get or create the analyzer server instance."""
    global _analyzer_server
    if _analyzer_server is None:
        _analyzer_server = create_enhanced_mcp_server({})
    return _analyzer_server


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="analyze_file",
            description="Analyze a single file for connascence, MECE, and NASA Power of 10 violations",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to analyze",
                    },
                    "analysis_type": {
                        "type": "string",
                        "enum": ["full", "connascence", "mece", "nasa"],
                        "default": "full",
                        "description": "Type of analysis to perform",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["json", "sarif"],
                        "default": "json",
                        "description": "Output format",
                    },
                },
                "required": ["file_path"],
            },
        ),
        Tool(
            name="analyze_workspace",
            description="Analyze an entire workspace/directory for code quality violations",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_path": {
                        "type": "string",
                        "description": "Path to the workspace directory",
                    },
                    "file_patterns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": ["*.py"],
                        "description": "File patterns to include (e.g., ['*.py', '*.js'])",
                    },
                    "analysis_type": {
                        "type": "string",
                        "enum": ["full", "connascence", "mece", "nasa"],
                        "default": "full",
                        "description": "Type of analysis to perform",
                    },
                },
                "required": ["workspace_path"],
            },
        ),
        Tool(
            name="get_violations",
            description="Get violations from the last analysis with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "severity": {
                        "type": "string",
                        "enum": ["critical", "high", "medium", "low", "all"],
                        "default": "all",
                        "description": "Filter by severity level",
                    },
                    "analyzer": {
                        "type": "string",
                        "enum": ["connascence", "mece", "nasa", "clarity", "sixsigma", "theater", "safety", "all"],
                        "default": "all",
                        "description": "Filter by analyzer type",
                    },
                    "limit": {
                        "type": "integer",
                        "default": 100,
                        "description": "Maximum number of violations to return",
                    },
                },
            },
        ),
        Tool(
            name="health_check",
            description="Check the health status of the connascence analyzer server",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="server_info",
            description="Get information about the connascence analyzer server",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> Sequence[TextContent]:
    """Handle tool calls."""
    try:
        analyzer = get_analyzer()

        if name == "analyze_file":
            result = await analyzer.analyze_file(
                file_path=arguments["file_path"],
                analysis_type=arguments.get("analysis_type", "full"),
                include_integrations=True,
                format=arguments.get("format", "json"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "analyze_workspace":
            result = await analyzer.analyze_workspace(
                workspace_path=arguments["workspace_path"],
                analysis_type=arguments.get("analysis_type", "full"),
                file_patterns=arguments.get("file_patterns", ["*.py"]),
                include_integrations=True,
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_violations":
            result = await analyzer.get_violations(
                severity=arguments.get("severity", "all"),
                violation_type=arguments.get("analyzer", "all"),
                limit=arguments.get("limit", 100),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "health_check":
            result = await analyzer.health_check(client_id="mcp-stdio")
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "server_info":
            result = get_server_info()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        else:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

    except Exception as e:
        logger.error(f"Tool {name} failed: {e}")
        return [TextContent(type="text", text=json.dumps({
            "error": str(e),
            "tool": name,
            "success": False,
        }))]


async def main():
    """Run the MCP stdio server."""
    logger.info("Starting Connascence MCP stdio server...")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
