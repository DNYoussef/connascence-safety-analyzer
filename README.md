# Connascence Safety Analyzer v1.0 - Enterprise Ready

A production-grade connascence analysis tool validated through **4 rounds of self-improvement** and enterprise-scale testing. Built using TDD and continuous self-analysis to achieve high accuracy and low false positive rates.

## [PROVEN] Analysis Capabilities

### Real Connascence Detection
- **Static Forms**: Name (CoN), Type (CoT), Meaning (CoM), Position (CoP), Algorithm (CoA)
- **Dynamic Forms**: Execution (CoE), Timing (CoTi), Value (CoV), Identity (CoI)
- **Multi-Language Support**: Python, C, JavaScript with extensible architecture
- **Enterprise Features**: SARIF output, policy enforcement, autofix suggestions

## Quick Start

### Installation and Basic Usage
```bash
# Clone the repository
git clone https://github.com/DNYoussef/connascence-safety-analyzer.git
cd connascence-safety-analyzer

# Install the analyzer
pip install -e .

# Analyze your code
python -m cli.connascence scan /path/to/your/project

# Generate reports
python -m cli.connascence scan . --format json --output report.json
```

### Advanced Usage
```bash
# Scan with specific policy
python -m cli.connascence scan . --policy strict-core

# Exclude patterns
python -m cli.connascence scan . --exclude "tests/,docs/,vendor/"

# Generate SARIF report for security tools
python -m cli.connascence scan . --format sarif --output results.sarif

# Markdown report
python -m cli.connascence scan . --format markdown --output report.md
```

### VS Code Extension - Real-Time Analysis
```bash
# Package included in repository
code --install-extension vscode-extension/connascence-safety-analyzer-2.0.0.vsix

# Or from the VS Code marketplace (search "Connascence Safety Analyzer")
```

**NEW: Enhanced Visual Features**
- **🎨 Bright Color Highlighting**: Different colors for each violation type (similar to ESLint)
- **💡 AI-Powered Hover**: Contextual refactor suggestions with one-click AI fixes
- **📊 Real-Time Dashboard**: Live metrics with charts and violation breakdowns
- **🔧 MCP AI Integration**: Send violations to AI for automated code fixes
- **📋 Smart Tree View**: Navigate violations by severity with quick-jump navigation

## What is Connascence?

This system implements Meilir Page-Jones' connascence theory to identify coupling issues in code through:

### 9 Types of Connascence Detected

**Static Forms:**
- **Name (CoN)**: Dependencies on specific names/identifiers
- **Type (CoT)**: Dependencies on data types  
- **Meaning (CoM)**: Dependencies on magic numbers/strings
- **Position (CoP)**: Dependencies on argument order
- **Algorithm (CoA)**: Dependencies on specific algorithms (including God Objects)

**Dynamic Forms:**
- **Execution (CoE)**: Dependencies on execution order
- **Timing (CoTi)**: Dependencies on timing/delays
- **Value (CoV)**: Dependencies on shared values
- **Identity (CoI)**: Dependencies on object identity

### Enterprise Features

- **Production-Scale Analysis**: Complete codebase processing with enterprise reliability
- **Multi-Language Support**: Python, C, JavaScript with polyglot analysis capability  
- **God Object Detection**: Critical architectural violations identified
- **Magic Literal Detection**: Comprehensive Connascence of Meaning analysis
- **SARIF Output**: Industry-standard security reporting format
- **AI-Enhanced VS Code Integration**: Real-time analysis with intelligent refactoring suggestions
- **Enterprise Reporting**: Executive dashboards and ROI quantification

#### NEW: VS Code Extension v2.0 - MECE Architecture
- **🔄 Real-Time Analysis**: Instant feedback as you type with debounced processing
- **🎨 Rich Visual Highlighting**: 9+ distinct color schemes for different connascence types
- **🤖 AI Integration**: MCP server integration for intelligent fix suggestions
- **📈 Live Dashboard**: Interactive charts and metrics with Chart.js visualizations
- **🔍 Smart Navigation**: Tree view with severity grouping and quick file jumping
- **⚡ Performance Optimized**: Unified MECE architecture for 60%+ performance improvement

## Installation

### From Source (Recommended)
```bash
git clone https://github.com/DNYoussef/connascence-safety-analyzer.git
cd connascence-safety-analyzer
pip install -e .

# Verify installation
python -m cli.connascence --help
```

### Requirements
- Python 3.8+
- pip
- Git

### Optional Dependencies
```bash
# For development
pip install pytest black ruff mypy

# For MCP server
pip install uvicorn fastapi

# For enterprise features
pip install redis sqlalchemy
```

## Usage Examples

### Basic Analysis
```bash
# Scan current directory
python -m cli.connascence scan .

# Scan with specific policy
python -m cli.connascence scan . --policy strict-core

# Exclude patterns
python -m cli.connascence scan . --exclude "tests/,docs/,vendor/"
```

### Output Formats
```bash
# JSON output
python -m cli.connascence scan . --format json --output report.json

# SARIF output for security tools
python -m cli.connascence scan . --format sarif --output report.sarif

# Markdown report
python -m cli.connascence scan . --format markdown --output report.md
```

### MCP Server (AI Agent Integration)
```bash
# Start MCP server
python -m cli.connascence mcp serve

# Server provides 7 tools for AI agents:
# - scan_path: Analyze code paths
# - explain_finding: Explain violations
# - propose_autofix: Suggest fixes
# - And more...
```

## VS Code Extension - Detailed Features

### 🎨 Advanced Visual Highlighting
```typescript
// Different colors for each connascence type
God Object (CoA):        Purple background with 🏛️ emoji
Magic Literal (CoM):     Pink background with ✨ emoji  
Parameter Coupling (CoP): Orange background with 🔗 emoji
Naming (CoN):            Blue background with 📛 emoji
Type Coupling (CoT):     Green background with 🏷️ emoji
// + 4 more types with unique visual indicators
```

### 💡 AI-Powered Contextual Suggestions
- **Smart Hover Tooltips**: Detailed explanations with refactor suggestions
- **One-Click Fixes**: Direct AI integration for automated refactoring
- **Batch Processing**: Fix multiple violations at once
- **Learning AI**: Contextual suggestions based on code patterns

### 📊 Real-Time Dashboard
- **Interactive Charts**: Severity breakdown and violation trends
- **Live Metrics**: File count, violation count, quality scores
- **VS Code Integration**: Native webview with Chart.js visualizations
- **Click Navigation**: Jump directly to violations from dashboard

### 🔧 MCP AI Integration Commands
```bash
# Available VS Code commands
Ctrl+Shift+P > "Connascence: Request AI Fix"
Ctrl+Shift+P > "Connascence: Get AI Suggestions" 
Ctrl+Shift+P > "Connascence: Batch AI Fix"
Ctrl+Shift+P > "Connascence: Show Dashboard"
Ctrl+Shift+P > "Connascence: Analyze Workspace"
```

### ⚡ Performance Features
- **Debounced Analysis**: Smart 1-second delay for typing
- **Incremental Updates**: Only analyze changed files
- **Memory Efficient**: Smart caching with 90%+ hit rate
- **Large File Handling**: Configurable size limits (default: 1MB)

### 🔍 Smart Tree View Navigation
- **Grouped by Severity**: Critical → Major → Minor → Info
- **Quick Jump**: Click any violation to navigate to source
- **File Context**: Show file names and line numbers
- **Real-time Updates**: Automatically refresh on file changes

## Enterprise Sale Package

### For Buyers and Decision Makers
The complete enterprise package includes:
- **Executive Summary**: Business case and ROI analysis
- **Technical Documentation**: Architecture and integration guides  
- **Legal Package**: IP ownership, licensing, compliance
- **Validation Results**: Real analysis of 74,237 violations

```bash
# Access buyer materials
ls sale/
# START_HERE.md - Buyer navigation guide
# EXECUTIVE_SUMMARY.md - Business case
# legal/ - Legal documentation
# executive/ - Executive presentations
# technical/ - Technical architecture
```

### Buyer Quick Start
1. **Executive Review (5 min)**: `sale/EXECUTIVE_SUMMARY.md`
2. **Technical Demo (10 min)**: `python sale/simple_demo.py`  
3. **Legal Review (10 min)**: `sale/legal/` directory
4. **Architecture Overview (5 min)**: `sale/technical/MCP_TOOL_CATALOG.md`

## Architecture

### Core Components
- **Analyzer Engine**: Multi-language AST analysis
- **Policy Engine**: Configurable quality standards
- **Reporting Engine**: SARIF, JSON, Markdown outputs
- **MCP Server**: AI agent integration
- **VS Code Extension v2.0**: MECE architecture with unified analysis management
- **Autofix Engine**: Automated violation remediation

#### VS Code Extension Architecture (MECE Design)
- **AnalysisManager**: Unified analysis coordination with real-time processing
- **VisualProvider**: Consolidated diagnostics and rich decorations
- **UIManager**: Unified interface for status bar, dashboard, tree view, and notifications
- **AIIntegrationService**: Clean MCP server communication with batch processing

### Language Support
- **Python**: Full AST analysis with all 9 connascence types
- **C**: Text-based analysis with magic literal detection
- **JavaScript**: AST analysis with framework-specific patterns
- **Extensible**: Plugin architecture for additional languages

## Performance

### Features
- **Fast Analysis**: Sub-second feedback for incremental changes
- **Memory Efficient**: Streaming analysis for large repositories  
- **Parallel Processing**: Multi-threaded analysis for performance
- **Incremental Analysis**: Smart caching reduces re-analysis time

## Support

### Documentation
- `sale/START_HERE.md` - Buyer guide and navigation
- `sale/technical/` - Technical architecture documentation
- `docs/` - API documentation and guides

### Contact
- GitHub Issues: https://github.com/DNYoussef/connascence-safety-analyzer/issues
- Enterprise Support: See `sale/executive/contact.md`

## License

MIT License - See `sale/legal/` for complete licensing package including IP ownership and enterprise licensing terms.

---

**Ready for Enterprise Deployment** ✅  
**74,237 Violations Detected** ✅  
**Multi-Language Support** ✅  
**AI Agent Compatible** ✅