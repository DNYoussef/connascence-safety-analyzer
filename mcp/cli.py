#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
Enhanced MCP Server CLI
=======================

Command-line interface for the enhanced MCP server.
Provides clean integration point for Claude Code without
tight coupling to Claude Flow.
"""

import argparse
import asyncio
import json
import logging
import os
from pathlib import Path
import sys
from typing import Any, Dict, Optional

# Force UTF-8 encoding for Windows compatibility
if sys.platform == "win32":
    # Set environment variables for Python I/O encoding
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    # Reconfigure stdout/stderr to use UTF-8
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from mcp.enhanced_server import create_enhanced_mcp_server, get_server_info
except ImportError as e:
    print(f"Error: Failed to import MCP server components: {e}", file=sys.stderr)
    print("This usually indicates missing dependencies or circular import issues.", file=sys.stderr)
    sys.exit(1)

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


async def analyze_file_command(args: argparse.Namespace) -> int:
    """Handle file analysis command."""
    try:
        server = create_enhanced_mcp_server(args.config)

        result = await server.analyze_file(
            file_path=args.file_path,
            analysis_type=args.analysis_type,
            include_integrations=args.include_integrations,
            format=args.format,
        )

        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
            print(f"Analysis results written to {args.output}")
        else:
            print(json.dumps(result, indent=2))

        return 0 if result.get("success", False) else 1

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return 1


async def analyze_workspace_command(args: argparse.Namespace) -> int:
    """Handle workspace analysis command."""
    try:
        server = create_enhanced_mcp_server(args.config)

        result = await server.analyze_workspace(
            workspace_path=args.workspace_path,
            analysis_type=args.analysis_type,
            file_patterns=args.file_patterns or ["*.py"],
            include_integrations=args.include_integrations,
        )

        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
            print(f"Analysis results written to {args.output}")
        else:
            print(json.dumps(result, indent=2))

        return 0 if result.get("success", False) else 1

    except Exception as e:
        logger.error(f"Workspace analysis failed: {e}")
        return 1


async def health_check_command(args: argparse.Namespace) -> int:
    """Handle health check command."""
    try:
        server = create_enhanced_mcp_server(args.config)
        result = await server.health_check()

        print(json.dumps(result, indent=2))
        return 0 if result.get("success", False) else 1

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return 1


async def mcp_server_command(args: argparse.Namespace) -> int:
    """Run the MCP server over stdio for Claude / VSCode."""
    try:
        server = create_enhanced_mcp_server(args.config)
        await run_stdio_server(server, once=args.once)
        return 0
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        return 1


async def run_stdio_server(server, once: bool = False) -> None:
    """Simple stdio transport so Claude Desktop / VSCode can talk to the server."""

    readiness = {
        "event": "server_ready",
        "info": get_server_info(),
        "health": await server.health_check(client_id="mcp-stdio"),
    }
    print(json.dumps(readiness, indent=2))
    sys.stdout.flush()

    if once:
        return

    loop = asyncio.get_event_loop()

    while True:
        line = await loop.run_in_executor(None, sys.stdin.readline)
        if not line:
            await asyncio.sleep(0.1)
            continue

        payload = line.strip()
        if not payload:
            continue

        try:
            request = json.loads(payload)
        except json.JSONDecodeError:
            print(json.dumps({"event": "error", "error": "invalid_json", "payload": payload}))
            sys.stdout.flush()
            continue

        tool = request.get("tool")
        if not tool:
            print(json.dumps({"event": "error", "error": "missing_tool"}))
            sys.stdout.flush()
            continue

        arguments = request.get("arguments", {})
        if not isinstance(arguments, dict):
            arguments = {}
        client_id = request.get("client_id", "stdio-client")

        result = await server.call_tool(tool, {**arguments, "client_id": client_id})
        print(json.dumps({"event": "tool_result", "tool": tool, "result": result}))
        sys.stdout.flush()


def server_info_command(args: argparse.Namespace) -> int:
    """Handle server info command."""
    try:
        info = get_server_info()
        print(json.dumps(info, indent=2))
        return 0
    except Exception as e:
        logger.error(f"Failed to get server info: {e}")
        return 1


def load_config(config_path: Optional[str]) -> Dict[str, Any]:
    """Load configuration from file."""
    if not config_path:
        return {}

    config_file = Path(config_path)
    if not config_file.exists():
        logger.warning(f"Config file not found: {config_path}")
        return {}

    try:
        with open(config_file) as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Enhanced MCP Server for Connascence Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a single file
  python -m mcp.cli analyze-file src/main.py

  # Analyze a workspace
  python -m mcp.cli analyze-workspace . --file-patterns "*.py" "*.js"

  # Check server health
  python -m mcp.cli health-check

  # Get server info
  python -m mcp.cli info
        """,
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    parser.add_argument("--config", "-c", type=str, help="Path to configuration file")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Analyze file command
    analyze_file_parser = subparsers.add_parser("analyze-file", help="Analyze a single file")
    analyze_file_parser.add_argument("file_path", help="Path to file to analyze")
    analyze_file_parser.add_argument(
        "--analysis-type",
        choices=["full", "connascence", "mece", "nasa"],
        default="full",
        help="Type of analysis to perform",
    )
    analyze_file_parser.add_argument(
        "--include-integrations", action="store_true", default=True, help="Include external tool integrations"
    )
    analyze_file_parser.add_argument("--format", choices=["json", "sarif"], default="json", help="Output format")
    analyze_file_parser.add_argument("--output", "-o", type=str, help="Output file path")

    # Analyze workspace command
    analyze_workspace_parser = subparsers.add_parser("analyze-workspace", help="Analyze entire workspace")
    analyze_workspace_parser.add_argument("workspace_path", help="Path to workspace to analyze")
    analyze_workspace_parser.add_argument(
        "--analysis-type",
        choices=["full", "connascence", "mece", "nasa"],
        default="full",
        help="Type of analysis to perform",
    )
    analyze_workspace_parser.add_argument(
        "--file-patterns", nargs="+", help="File patterns to include (e.g., *.py *.js)"
    )
    analyze_workspace_parser.add_argument(
        "--include-integrations", action="store_true", default=True, help="Include external tool integrations"
    )
    analyze_workspace_parser.add_argument("--output", "-o", type=str, help="Output file path")

    # Health check command
    subparsers.add_parser("health-check", help="Check server health status")

    # Server info command
    subparsers.add_parser("info", help="Get server information")

    # MCP stdio server command
    mcp_server_parser = subparsers.add_parser("mcp-server", help="Run MCP server over stdio")
    mcp_server_parser.add_argument(
        "--once",
        action="store_true",
        help="Emit readiness payload and exit (useful for automated health checks)",
    )

    return parser


async def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Load configuration
    args.config = load_config(args.config)

    # Handle commands
    if args.command == "analyze-file":
        return await analyze_file_command(args)
    elif args.command == "analyze-workspace":
        return await analyze_workspace_command(args)
    elif args.command == "health-check":
        return await health_check_command(args)
    elif args.command == "mcp-server":
        return await mcp_server_command(args)
    elif args.command == "info":
        return server_info_command(args)
    else:
        parser.print_help()
        return 1


def cli_main():
    """Entry point for setuptools console script."""
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli_main()
