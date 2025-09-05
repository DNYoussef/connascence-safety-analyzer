#!/bin/bash

# 🔗💥 Connascence Safety Analyzer - VS Code Extension Installation Script
# Break the chains of tight coupling with our enterprise-grade analysis tool!

set -e  # Exit on error

echo "🔗💥 Installing Connascence Safety Analyzer VS Code Extension..."
echo "========================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "vscode-extension/package.json" ]; then
    echo -e "${RED}❌ Error: Must run from project root directory${NC}"
    echo "Usage: ./scripts/install-extension.sh"
    exit 1
fi

# Check if VS Code is installed
if ! command -v code &> /dev/null; then
    echo -e "${RED}❌ Error: VS Code 'code' command not found${NC}"
    echo "Please install VS Code and ensure 'code' command is in PATH"
    echo "See: https://code.visualstudio.com/docs/editor/command-line"
    exit 1
fi

# Check if vsce (VS Code Extension Manager) is available
if ! command -v vsce &> /dev/null; then
    echo -e "${YELLOW}⚠️  Installing vsce (Visual Studio Code Extension Manager)...${NC}"
    npm install -g @vscode/vsce
fi

# Change to extension directory
cd vscode-extension

echo -e "${BLUE}📦 Packaging extension...${NC}"

# Create images directory if it doesn't exist
mkdir -p images

# Create a temporary logo if it doesn't exist (placeholder)
if [ ! -f "images/connascence-logo.png" ]; then
    echo -e "${YELLOW}⚠️  Creating placeholder logo (replace with actual broken chains image)${NC}"
    # Create a simple 256x256 placeholder PNG (this would normally be a proper broken chains logo)
    # For now, we'll create the directory structure and note that the logo needs to be added
    echo "TODO: Add 256x256 broken chains logo as images/connascence-logo.png" > images/README.md
fi

echo -e "${BLUE}🔧 Building extension package...${NC}"

# Package the extension
if vsce package --no-dependencies; then
    PACKAGE_FILE=$(ls *.vsix | head -n1)
    echo -e "${GREEN}✅ Extension packaged successfully: ${PACKAGE_FILE}${NC}"
    
    echo -e "${BLUE}🚀 Installing extension to VS Code...${NC}"
    
    # Install the extension
    if code --install-extension "$PACKAGE_FILE"; then
        echo -e "${GREEN}🎉 Extension installed successfully!${NC}"
        echo
        echo "🔗💥 CONNASCENCE SAFETY ANALYZER IS NOW READY!"
        echo "==============================================="
        echo
        echo "🎯 Features Available:"
        echo "   • Real-time connascence analysis"
        echo "   • NASA Power of Ten compliance checking"
        echo "   • AI-powered refactoring suggestions"
        echo "   • MCP server integration"
        echo "   • CI/CD control loop automation"
        echo "   • Self-improvement dogfooding"
        echo "   • Enterprise policy enforcement"
        echo
        echo "🚀 Quick Start:"
        echo "   1. Open any Python/C/C++/JS/TS file"
        echo "   2. Press Ctrl+Shift+P (Cmd+Shift+P on Mac)"
        echo "   3. Type 'Connascence' to see available commands"
        echo "   4. Start with 'Connascence: Analyze File'"
        echo
        echo "🔧 MCP Server Setup:"
        echo "   1. Run: python src/mcp/server.py"
        echo "   2. Use 'Connascence AI: Configure MCP Server'"
        echo
        echo "📖 Documentation:"
        echo "   • DOGFOOD.md - Self-improvement system"
        echo "   • README.md - Full documentation"
        echo "   • GitHub Issues - Support and feedback"
        echo
        echo -e "${BLUE}Happy coupling breaking! 🔗💥${NC}"
        
    else
        echo -e "${RED}❌ Failed to install extension${NC}"
        exit 1
    fi
    
else
    echo -e "${RED}❌ Failed to package extension${NC}"
    exit 1
fi

# Optional: Clean up package file
read -p "Remove package file ${PACKAGE_FILE}? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm "$PACKAGE_FILE"
    echo -e "${GREEN}📦 Package file removed${NC}"
fi

echo
echo "🔗💥 Installation complete! Restart VS Code to ensure all features are loaded."