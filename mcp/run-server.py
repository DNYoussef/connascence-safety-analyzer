#!/usr/bin/env python3
"""
Connascence MCP Server Runner

This script starts the Connascence MCP server in a way that can be used by AI agents.
It implements the MCP (Model Context Protocol) server specification.
"""

import asyncio
import json
import sys
from server import ConnascenceMCPServer

async def handle_request(server, method, params=None):
    """Handle MCP requests."""
    params = params or {}
    
    if method == "tools/list":
        return {
            "tools": server.get_tools()
        }
    
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "scan_path":
            return await server.scan_path(arguments)
        elif tool_name == "explain_finding":
            return await server.explain_finding(arguments)
        elif tool_name == "propose_autofix":
            return await server.propose_autofix(arguments)
        elif tool_name == "list_presets":
            return await server.list_presets(arguments)
        elif tool_name == "validate_policy":
            return await server.validate_policy(arguments)
        elif tool_name == "get_metrics":
            return await server.get_metrics(arguments)
        elif tool_name == "enforce_policy":
            return await server.enforce_policy(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    elif method == "ping":
        return {"status": "pong"}
    
    else:
        raise ValueError(f"Unknown method: {method}")

async def main():
    """Main MCP server loop."""
    server = ConnascenceMCPServer()
    
    print("Connascence MCP Server started", file=sys.stderr)
    print("Available tools:", file=sys.stderr)
    
    for tool in server.get_tools():
        print(f"  - {tool['name']}: {tool['description']}", file=sys.stderr)
    
    # Simple demonstration mode
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        print("\nRunning in demo mode...", file=sys.stderr)
        
        # Test all tools
        demo_results = {}
        
        # Test scan_path
        try:
            demo_results["scan_path"] = await handle_request(server, "tools/call", {
                "name": "scan_path",
                "arguments": {"path": ".", "policy_preset": "strict-core"}
            })
        except Exception as e:
            demo_results["scan_path"] = {"error": str(e)}
        
        # Test list_presets
        try:
            demo_results["list_presets"] = await handle_request(server, "tools/call", {
                "name": "list_presets",
                "arguments": {}
            })
        except Exception as e:
            demo_results["list_presets"] = {"error": str(e)}
        
        # Test get_metrics
        try:
            demo_results["get_metrics"] = await handle_request(server, "tools/call", {
                "name": "get_metrics",
                "arguments": {}
            })
        except Exception as e:
            demo_results["get_metrics"] = {"error": str(e)}
        
        print("\nDemo Results:", file=sys.stderr)
        print(json.dumps(demo_results, indent=2), file=sys.stderr)
        
        return 0
    
    # For a real MCP server, this would handle stdin/stdout protocol
    print("Use --demo flag for demonstration mode", file=sys.stderr)
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))