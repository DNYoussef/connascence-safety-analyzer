#!/bin/bash
# MCP Server Startup Script for Unix/Linux/macOS
# Sets UTF-8 encoding to prevent Unicode errors

# Set Python I/O encoding to UTF-8
export PYTHONIOENCODING=utf-8

# Set locale to UTF-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment if available
if [ -f "$SCRIPT_DIR/../venv-connascence/bin/activate" ]; then
    source "$SCRIPT_DIR/../venv-connascence/bin/activate"
fi

# Start MCP server
echo "Starting Connascence MCP Server..."
python -m mcp.cli "$@"

# Exit with the same code as the Python process
exit $?
