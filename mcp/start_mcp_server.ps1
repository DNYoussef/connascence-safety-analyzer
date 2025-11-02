# MCP Server Startup Script for PowerShell
# Sets UTF-8 encoding to prevent Unicode errors

# Set Python I/O encoding to UTF-8
$env:PYTHONIOENCODING = "utf-8"

# Set console output encoding to UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Activate virtual environment if available
$VenvActivate = Join-Path $ScriptDir "..\venv-connascence\Scripts\Activate.ps1"
if (Test-Path $VenvActivate) {
    & $VenvActivate
}

# Start MCP server
Write-Host "Starting Connascence MCP Server..." -ForegroundColor Green
python -m mcp.cli $args

# Exit with the same code as the Python process
exit $LASTEXITCODE
