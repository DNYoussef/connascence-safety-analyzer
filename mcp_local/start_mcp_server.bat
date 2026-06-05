@echo off
REM MCP Server Startup Script for Windows
REM Sets UTF-8 encoding to prevent Unicode errors

REM Set Python I/O encoding to UTF-8
set PYTHONIOENCODING=utf-8

REM Set console code page to UTF-8
chcp 65001 >nul 2>&1

REM Activate virtual environment if available
if exist "%~dp0..\venv-connascence\Scripts\activate.bat" (
    call "%~dp0..\venv-connascence\Scripts\activate.bat"
)

REM Start MCP server
echo Starting Connascence MCP Server...
python -m mcp.cli %*

REM Exit with the same code as the Python process
exit /b %ERRORLEVEL%
