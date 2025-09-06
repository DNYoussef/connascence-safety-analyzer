# Installation Guide - Connascence Analyzer

This guide provides step-by-step instructions for installing the Connascence Analyzer in different environments.

## Prerequisites

- **Python**: 3.8 or higher (recommended: 3.12)
- **Operating System**: Windows, macOS, or Linux
- **Memory**: Minimum 512MB free RAM
- **Disk Space**: 50MB for installation

## Quick Installation (Recommended)

### 1. Install from PyPI (Production Use)

```bash
# Install latest stable version
pip install connascence-analyzer

# Verify installation
connascence --version
```

### 2. Install with Optional Dependencies

```bash
# Install with all optional features
pip install "connascence-analyzer[dev,mcp,vscode,enterprise]"

# Or install specific feature sets:
pip install "connascence-analyzer[mcp]"      # MCP server support
pip install "connascence-analyzer[vscode]"   # VS Code extension support  
pip install "connascence-analyzer[enterprise]" # Enterprise features
```

## Installation from Source

### 1. Clone Repository

```bash
git clone https://github.com/connascence/connascence-analyzer.git
cd connascence-analyzer
```

### 2. Create Virtual Environment

```bash
# Using venv (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## Development Setup

### 1. Full Development Environment

```bash
# Clone repository
git clone https://github.com/connascence/connascence-analyzer.git
cd connascence-analyzer

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests to verify setup
pytest
```

### 2. VS Code Extension Development

```bash
# Additional requirements for VS Code extension
pip install ".[vscode]"

# Install VS Code extension from source
cd vscode-extension
npm install
npm run compile
code --install-extension connascence-safety-analyzer-1.0.0.vsix
```

### 3. MCP Server Development

```bash
# Install MCP server dependencies
pip install ".[mcp]"

# Start MCP server for testing
python -m mcp.server --port 8000
```

## Docker Installation

### 1. Using Docker Hub

```bash
# Pull and run container
docker pull connascence/analyzer:latest
docker run -v $(pwd):/workspace connascence/analyzer:latest /workspace
```

### 2. Build from Source

```bash
# Build Docker image
docker build -t connascence-analyzer .

# Run analysis on current directory
docker run -v $(pwd):/workspace connascence-analyzer /workspace
```

## Platform-Specific Instructions

### Windows

```cmd
# Using pip (requires Python from python.org)
pip install connascence-analyzer

# Using conda
conda install -c conda-forge connascence-analyzer

# Using Chocolatey
choco install connascence-analyzer
```

### macOS

```bash
# Using pip
pip install connascence-analyzer

# Using Homebrew
brew install connascence-analyzer

# Using conda
conda install -c conda-forge connascence-analyzer
```

### Linux (Ubuntu/Debian)

```bash
# Install Python dependencies
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv

# Install connascence-analyzer
pip3 install connascence-analyzer

# Add to PATH if needed
echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

### Linux (RHEL/CentOS/Fedora)

```bash
# Install Python dependencies
sudo dnf install python3 python3-pip python3-virtualenv

# Install connascence-analyzer  
pip3 install --user connascence-analyzer
```

## Enterprise Installation

### 1. Offline Installation

```bash
# Download wheel file on internet-connected machine
pip download connascence-analyzer

# Transfer files to offline machine and install
pip install connascence_analyzer-*.whl --no-index --find-links .
```

### 2. Corporate Network with Proxy

```bash
# Configure pip for corporate proxy
pip install --proxy http://user:password@proxy.company.com:8080 connascence-analyzer

# Or set environment variables
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
pip install connascence-analyzer
```

### 3. System-wide Installation

```bash
# Install system-wide (requires admin privileges)
sudo pip install connascence-analyzer

# Create symlinks for easy access
sudo ln -s /usr/local/bin/connascence /usr/bin/connascence
```

## Verification

### 1. Basic Installation Check

```bash
# Check version
connascence --version

# Show help
connascence --help

# Run basic analysis
echo "def test(): pass" > test.py
connascence test.py
```

### 2. Feature Verification

```bash
# Test analyzer core functionality
python -m analyzer.core --help

# Test CLI interface
python -m cli.connascence --help

# Test with sample file
echo "def test(): pass" > test.py
python -m analyzer.core --path test.py --policy nasa_jpl_pot10
```

## Troubleshooting

### Common Issues

1. **ImportError: No module named 'connascence'**
   ```bash
   # Ensure virtual environment is activated
   source venv/bin/activate
   # Or reinstall
   pip install --force-reinstall connascence-analyzer
   ```

2. **Permission denied errors**
   ```bash
   # Use --user flag
   pip install --user connascence-analyzer
   # Or create virtual environment
   python -m venv venv && source venv/bin/activate
   ```

3. **Command not found: connascence**
   ```bash
   # Add to PATH
   export PATH=$HOME/.local/bin:$PATH
   # Or use full path
   python -m cli.connascence
   ```

4. **SSL Certificate errors**
   ```bash
   # Use trusted hosts
   pip install --trusted-host pypi.org --trusted-host pypi.python.org connascence-analyzer
   ```

### Getting Help

- **Documentation**: https://docs.connascence.io
- **GitHub Issues**: https://github.com/connascence/connascence-analyzer/issues
- **Discussions**: https://github.com/connascence/connascence-analyzer/discussions

## Next Steps

After installation, see:
- [Configuration Guide](CONFIGURATION.md) - Configure analysis settings
- [Deployment Checklist](DEPLOYMENT_CHECKLIST.md) - Production deployment
- [User Guide](../user-guide/README.md) - How to use the analyzer