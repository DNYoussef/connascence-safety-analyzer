# Connascence Safety Analyzer

Welcome to the Connascence Safety Analyzer - an enterprise-grade VS Code extension for detecting and fixing code coupling issues.

## 🚀 Installation & Setup

### Local Installation

1. **Package the extension:**
   ```bash
   cd vscode-extension
   npm install -g @vscode/vsce
   vsce package
   ```

2. **Install in VS Code:**
   ```bash
   code --install-extension connascence-safety-analyzer-1.0.0.vsix
   ```

3. **Install CLI interface:**
   ```bash
   npm install -g ./cli
   connascence --version
   ```

4. **Setup MCP server:**
   ```bash
   npm install -g @connascence/mcp-server
   connascence-mcp start --port 8080
   ```

### Quick Start

1. Open a Python, JavaScript, TypeScript, C, or C++ file
2. Configure your AI API keys in the sidebar
3. View violations highlighted in your code
4. Hover over violations for AI-powered fix suggestions
5. Use the dashboard for comprehensive analysis

## 📊 Features

- **Real-time Analysis**: Detect 9 types of connascence violations as you type
- **AI-Powered Fixes**: Get intelligent refactoring suggestions with confidence scores
- **Visual Dashboard**: Track code quality metrics and trends
- **Comprehensive Help**: Built-in documentation and tutorials

## 🔗 Connascence Types Detected

1. **Critical Violations** (Fix First!)
   - God Objects / Algorithm violations
   - Identity coupling
   - Value coupling
   - Timing violations

2. **Major Violations**
   - Magic literals / Meaning violations
   - Execution order dependencies

3. **Minor Violations**
   - Parameter position coupling
   - Type coupling
   - Naming inconsistencies

## 📚 Documentation

### VS Code Interface
- Press `Ctrl+Shift+P` and search for "Connascence: Show Help"
- Use the Markdown TOC sidebar to browse documentation
- Configure AI models in the AI Configuration sidebar

### Command Line Interface
```bash
# Analyze a file
connascence analyze file.py

# Analyze entire project
connascence analyze --recursive .

# Generate report
connascence report --format json --output report.json

# Start MCP server
connascence-mcp start --config ./mcp-config.json
```

## 🤝 Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines on how to contribute to this project.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.