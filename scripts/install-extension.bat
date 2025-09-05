@echo off
REM 🔗💥 Connascence Safety Analyzer - VS Code Extension Installation Script (Windows)
REM Break the chains of tight coupling with our enterprise-grade analysis tool!

echo 🔗💥 Installing Connascence Safety Analyzer VS Code Extension...
echo =========================================================

REM Check if we're in the right directory
if not exist "vscode-extension\package.json" (
    echo ❌ Error: Must run from project root directory
    echo Usage: .\scripts\install-extension.bat
    pause
    exit /b 1
)

REM Check if VS Code is installed
code --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: VS Code 'code' command not found
    echo Please install VS Code and ensure 'code' command is in PATH
    echo See: https://code.visualstudio.com/docs/editor/command-line
    pause
    exit /b 1
)

REM Check if vsce is available
vsce --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Installing vsce (Visual Studio Code Extension Manager)...
    npm install -g @vscode/vsce
    if errorlevel 1 (
        echo ❌ Failed to install vsce. Please install manually: npm install -g @vscode/vsce
        pause
        exit /b 1
    )
)

REM Change to extension directory
cd vscode-extension

echo 📦 Packaging extension...

REM Create images directory if it doesn't exist
if not exist "images" mkdir images

REM Create a temporary logo note if it doesn't exist
if not exist "images\connascence-logo.png" (
    echo ⚠️  Creating placeholder logo note (replace with actual broken chains image)
    echo TODO: Add 256x256 broken chains logo as images/connascence-logo.png > images\README.md
)

echo 🔧 Building extension package...

REM Package the extension
vsce package --no-dependencies
if errorlevel 1 (
    echo ❌ Failed to package extension
    pause
    exit /b 1
)

REM Find the generated .vsix file
for %%f in (*.vsix) do set PACKAGE_FILE=%%f

echo ✅ Extension packaged successfully: %PACKAGE_FILE%
echo 🚀 Installing extension to VS Code...

REM Install the extension
code --install-extension "%PACKAGE_FILE%"
if errorlevel 1 (
    echo ❌ Failed to install extension
    pause
    exit /b 1
)

echo.
echo 🎉 Extension installed successfully!
echo.
echo 🔗💥 CONNASCENCE SAFETY ANALYZER IS NOW READY!
echo ===============================================
echo.
echo 🎯 Features Available:
echo    • Real-time connascence analysis
echo    • NASA Power of Ten compliance checking
echo    • AI-powered refactoring suggestions
echo    • MCP server integration
echo    • CI/CD control loop automation
echo    • Self-improvement dogfooding
echo    • Enterprise policy enforcement
echo.
echo 🚀 Quick Start:
echo    1. Open any Python/C/C++/JS/TS file
echo    2. Press Ctrl+Shift+P
echo    3. Type 'Connascence' to see available commands
echo    4. Start with 'Connascence: Analyze File'
echo.
echo 🔧 MCP Server Setup:
echo    1. Run: python src/mcp/server.py
echo    2. Use 'Connascence AI: Configure MCP Server'
echo.
echo 📖 Documentation:
echo    • DOGFOOD.md - Self-improvement system
echo    • README.md - Full documentation
echo    • GitHub Issues - Support and feedback
echo.
echo Happy coupling breaking! 🔗💥
echo.

REM Optional: Clean up package file
set /p REPLY="Remove package file %PACKAGE_FILE%? (y/N) "
if /i "%REPLY%"=="y" (
    del "%PACKAGE_FILE%"
    echo 📦 Package file removed
)

echo.
echo 🔗💥 Installation complete! Restart VS Code to ensure all features are loaded.
pause