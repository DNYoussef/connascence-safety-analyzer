# Installation Guide - Connascence Safety Analyzer

**Version**: 2.0.2+
**Last Updated**: 2025-10-07

This guide provides step-by-step instructions for installing and setting up the Connascence Safety Analyzer for development and production use.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Installation Methods](#installation-methods)
  - [1. For End Users](#1-for-end-users-vscode-extension)
  - [2. For Developers](#2-for-developers-full-setup)
  - [3. For CI/CD](#3-for-cicd-integration)
- [Verification](#verification)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Next Steps](#next-steps)

---

## Prerequisites

### System Requirements
- **Operating System**: Windows, macOS, or Linux
- **Memory**: 4GB RAM minimum (8GB recommended)
- **Disk Space**: 500MB for installation

### Software Dependencies

#### For End Users (VSCode Extension Only)
- **VSCode**: Version 1.74.0 or higher
- **Python**: 3.8+ (for backend analyzer)
- **Node.js**: 14+ (for extension runtime)

#### For Developers (Full Setup)
- **Python**: 3.8, 3.9, 3.10, 3.11, or 3.12
- **Node.js**: 18+ (recommended)
- **Git**: Latest version
- **npm**: 8+ (comes with Node.js)

---

## Quick Start

### 5-Minute Setup (End Users)

```bash
# Install VSCode extension
code --install-extension connascence-systems.connascence-safety-analyzer

# Install Python analyzer
pip install connascence-analyzer

# Verify installation
connascence --version
```

### 10-Minute Setup (Developers)

```bash
# Clone repository
git clone https://github.com/connascence-systems/connascence-analyzer.git
cd connascence-analyzer

# Install Python dependencies
pip install -e ".[dev,mcp,vscode,enterprise]"

# Setup VSCode extension
cd interfaces/vscode
npm install
npm run compile

# Run tests
npm test
```

---

## Installation Methods

### 1. For End Users (VSCode Extension)

#### Option A: From VSCode Marketplace

1. **Open VSCode**
2. **Go to Extensions** (Ctrl+Shift+X or Cmd+Shift+X)
3. **Search**: "Connascence Safety Analyzer"
4. **Click Install**
5. **Reload VSCode**

#### Option B: From Command Line

```bash
code --install-extension connascence-systems.connascence-safety-analyzer
```

#### Option C: From VSIX File

```bash
# Download latest .vsix from releases
code --install-extension connascence-safety-analyzer-2.0.2.vsix
```

#### Install Python Analyzer Backend

The VSCode extension requires the Python analyzer backend:

```bash
# Install from PyPI
pip install connascence-analyzer

# Or install from source
git clone https://github.com/connascence-systems/connascence-analyzer.git
cd connascence-analyzer
pip install -e .
```

#### Verify Installation

```bash
# Check Python analyzer
connascence --version
# Expected output: connascence-analyzer 2.0.x

# Check VSCode extension
code --list-extensions | grep connascence
# Expected: connascence-systems.connascence-safety-analyzer
```

---

### 2. For Developers (Full Setup)

#### Step 1: Clone Repository

```bash
git clone https://github.com/connascence-systems/connascence-analyzer.git
cd connascence-analyzer
```

#### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate
```

#### Step 3: Install Python Dependencies

```bash
# Install with all extras
pip install -e ".[dev,mcp,vscode,enterprise]"

# Or minimal installation
pip install -e .
```

**Available extras:**
- `dev` - Development tools (pytest, ruff, mypy, black)
- `mcp` - MCP server dependencies (websockets, asyncio)
- `vscode` - VSCode integration dependencies
- `enterprise` - Enterprise features (telemetry, advanced analytics)

#### Step 4: Setup VSCode Extension

```bash
cd interfaces/vscode

# Install Node dependencies
npm install

# Compile TypeScript
npm run compile

# Run linting
npm run lint
```

#### Step 5: Verify Development Setup

```bash
# Run Python tests
cd ../..
pytest tests/ -v

# Run VSCode extension tests
cd interfaces/vscode
npm test

# Build production extension
npm run package
```

---

### 3. For CI/CD Integration

#### GitHub Actions

Add to `.github/workflows/analysis.yml`:

```yaml
name: Connascence Analysis

on: [push, pull_request]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install Connascence Analyzer
        run: |
          pip install connascence-analyzer

      - name: Run Analysis
        run: |
          connascence scan . --policy strict --format sarif --output results.sarif

      - name: Upload Results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: results.sarif
```

#### Docker

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install Connascence Analyzer
RUN pip install connascence-analyzer

# Copy project files
COPY . .

# Run analysis
CMD ["connascence", "scan", ".", "--format", "json"]
```

#### Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: connascence
        name: Connascence Analysis
        entry: connascence scan --policy strict --fail-on-critical
        language: system
        pass_filenames: false
```

---

## Verification

### Verify Python Analyzer

```bash
# Check version
connascence --version

# Test basic analysis
connascence scan examples/ --format json

# Check available policies
connascence policies list
```

### Verify VSCode Extension

1. **Open VSCode**
2. **Check Extension is Active**:
   - Go to Extensions (Ctrl+Shift+X)
   - Search "Connascence"
   - Should show as "Installed"

3. **Test Commands**:
   - Open Command Palette (Ctrl+Shift+P)
   - Type "Connascence"
   - Should see: "Analyze File", "Show Dashboard", etc.

4. **Test Analysis**:
   - Open a Python/JavaScript file
   - Extension should show analysis in Problems panel

### Verify MCP Server (Optional)

```bash
# Start MCP server
python -m mcp.server

# Test health endpoint (in another terminal)
curl http://localhost:8765/health

# Expected response: {"status": "healthy", "version": "2.0.x"}
```

---

## Configuration

### VSCode Extension Settings

Open VSCode Settings (Ctrl+,) and configure:

```json
{
  // Safety profile
  "connascence.safetyProfile": "standard",

  // Real-time analysis
  "connascence.realTimeAnalysis": true,

  // IntelliSense integration
  "connascence.enableIntelliSense": true,

  // Backend server
  "connascence.serverUrl": "http://localhost:8080",

  // Exclusions
  "connascence.exclude": [
    "node_modules/**",
    "**/*.test.*",
    ".git/**"
  ]
}
```

### Python Analyzer Configuration

Create `.connascence.yml` in project root:

```yaml
# Policy configuration
policy: standard

# Exclusions
exclude:
  - node_modules
  - venv
  - __pycache__
  - "*.pyc"

# Thresholds
thresholds:
  max_parameters: 5
  max_methods: 20
  max_nested_depth: 4

# NASA compliance
nasa_compliance:
  enabled: false
  profile: nasa_jpl_pot10
```

---

## Troubleshooting

### Common Issues

#### Issue: "connascence: command not found"

**Solution:**
```bash
# Make sure pip installed to correct location
pip install --user connascence-analyzer

# Or use python -m
python -m connascence --version
```

#### Issue: Extension not activating

**Solution:**
1. Check VSCode version (must be 1.74.0+)
2. Reload VSCode (Ctrl+Shift+P → "Developer: Reload Window")
3. Check Output panel (View → Output → Select "Connascence")

#### Issue: "MCP server not available"

**Solution:**
```bash
# Extension falls back to CLI automatically
# To use MCP server:
python -m mcp.server

# Then restart VSCode
```

#### Issue: Permission denied on Windows

**Solution:**
```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Getting Help

- **Documentation**: See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- **Development Guide**: See [DEVELOPMENT.md](./DEVELOPMENT.md)
- **Issues**: https://github.com/connascence-systems/connascence-analyzer/issues
- **Discussions**: https://github.com/connascence-systems/connascence-analyzer/discussions

---

## Next Steps

### For End Users

1. **Configure Extension**: Adjust settings for your project
2. **Run First Analysis**: Open a file and see violations
3. **Explore Features**: Try code actions, hover info, IntelliSense

### For Developers

1. **Read Development Guide**: [DEVELOPMENT.md](./DEVELOPMENT.md)
2. **Run Tests**: Ensure everything works
3. **Contribute**: See [CONTRIBUTING.md](./CONTRIBUTING.md)

### For CI/CD Users

1. **Add Workflow**: Integrate into your pipeline
2. **Set Quality Gates**: Configure failure thresholds
3. **Monitor Results**: Track quality over time

---

## Updates & Maintenance

### Updating VSCode Extension

```bash
# Update to latest version
code --install-extension connascence-systems.connascence-safety-analyzer --force

# Or through VSCode UI
# Extensions → Connascence → Update
```

### Updating Python Analyzer

```bash
# Update from PyPI
pip install --upgrade connascence-analyzer

# Or from source
cd connascence-analyzer
git pull
pip install -e . --upgrade
```

### Checking for Updates

```bash
# Check current version
connascence --version

# Check latest available
pip index versions connascence-analyzer
```

---

## Uninstallation

### Remove VSCode Extension

```bash
code --uninstall-extension connascence-systems.connascence-safety-analyzer
```

### Remove Python Analyzer

```bash
pip uninstall connascence-analyzer
```

### Clean Configuration

```bash
# Remove config files
rm ~/.connascence.yml
rm .connascence.yml

# Remove VSCode settings (optional)
# Edit .vscode/settings.json and remove connascence.* entries
```

---

**Installation complete!** 🎉

For development setup, proceed to [DEVELOPMENT.md](./DEVELOPMENT.md).

For usage instructions, see the main [README.md](../README.md).
