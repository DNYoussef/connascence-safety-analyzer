#!/bin/bash
# VS Code Extension Build Script

cd vscode-extension

# Install dependencies
npm install

# Compile TypeScript
npm run compile

# Package extension
npx vsce package

# Move package to dist
mv *.vsix ../connascence-vscode-extension-1.0.0.vsix

echo "VS Code extension packaged successfully"
