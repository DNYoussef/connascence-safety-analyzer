# Development Guide - Connascence Safety Analyzer

**Version**: 2.0.2+
**Last Updated**: 2025-10-07

This guide covers development workflows, debugging techniques, and best practices for contributing to the Connascence Safety Analyzer project.

---

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Development Workflows](#development-workflows)
- [Debugging](#debugging)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [VSCode Extension Development](#vscode-extension-development)
- [MCP Server Development](#mcp-server-development)
- [Contributing Guidelines](#contributing-guidelines)

---

## Development Setup

### Prerequisites

See [INSTALLATION.md](./INSTALLATION.md) for complete prerequisite list.

### Initial Setup

```bash
# Clone repository
git clone https://github.com/connascence-systems/connascence-analyzer.git
cd connascence-analyzer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with development dependencies
pip install -e ".[dev,mcp,vscode,enterprise]"

# Setup pre-commit hooks
pip install pre-commit
pre-commit install

# Verify setup
pytest --version
ruff --version
mypy --version
```

### VSCode Extension Setup

```bash
cd interfaces/vscode

# Install dependencies
npm install

# Compile TypeScript
npm run compile

# Start watch mode for development
npm run watch
```

---

## Project Structure

```
connascence-analyzer/
├── analyzer/                    # Core Python analyzer
│   ├── core/                    # Analysis engine
│   ├── detectors/               # Connascence detectors
│   ├── policies/                # Safety policies
│   └── utils/                   # Utility functions
├── interfaces/
│   ├── cli/                     # Command-line interface
│   └── vscode/                  # VSCode extension (PRIMARY)
│       ├── src/
│       │   ├── commands/        # Command handlers
│       │   ├── services/        # Core services
│       │   │   ├── mcpClient.ts        # MCP communication
│       │   │   └── connascenceService.ts # Analysis service
│       │   ├── providers/       # LSP providers
│       │   ├── features/        # Extension features
│       │   └── test/            # Tests
│       ├── package.json         # Extension manifest
│       └── tsconfig.json        # TypeScript config
├── integrations/
│   └── vscode-archived/         # Deprecated extension (DO NOT USE)
├── mcp/                         # MCP server implementation
│   ├── server.py                # WebSocket server
│   └── protocol.py              # MCP protocol
├── tests/                       # Python tests
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── e2e/                     # End-to-end tests
└── docs/                        # Documentation
```

### Key Files

- **Python Analyzer**: `analyzer/core/engine.py`
- **VSCode Extension**: `interfaces/vscode/src/extension.ts`
- **MCP Client**: `interfaces/vscode/src/services/mcpClient.ts`
- **MCP Server**: `mcp/server.py`
- **CI/CD**: `.github/workflows/ci.yml`
- **Configuration**: `pyproject.toml`, `package.json`

---

## Development Workflows

### Daily Development Workflow

```bash
# 1. Pull latest changes
git pull origin main

# 2. Create feature branch
git checkout -b feature/your-feature-name

# 3. Make changes and test
pytest tests/ -v                 # Run Python tests
cd interfaces/vscode && npm test # Run extension tests

# 4. Run code quality checks
ruff check .                     # Lint Python
black .                          # Format Python
mypy analyzer interfaces mcp     # Type check
npm run lint                     # Lint TypeScript

# 5. Commit changes
git add .
git commit -m "feat: description of changes"

# 6. Push and create PR
git push origin feature/your-feature-name
```

### Building for Production

```bash
# Build Python package
python -m build

# Build VSCode extension
cd interfaces/vscode
npm run build:production
npm run package

# Output: connascence-safety-analyzer-2.0.2.vsix
```

---

## Debugging

### Debugging Python Analyzer

#### Using VS Code Debugger

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Analyze File",
      "type": "python",
      "request": "launch",
      "module": "interfaces.cli.connascence",
      "args": ["scan", "${file}", "--policy", "strict", "--format", "json"],
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}"
    },
    {
      "name": "Python: Run Tests",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["tests/", "-v", "-s"],
      "console": "integratedTerminal"
    }
  ]
}
```

#### Command Line Debugging

```bash
# Run with verbose logging
connascence scan . --verbose --log-level DEBUG

# Use Python debugger
python -m pdb -m interfaces.cli.connascence scan examples/

# Print debug information
connascence scan . --debug --format json | jq .
```

### Debugging VSCode Extension

#### Launch Extension in Debug Mode

1. **Open** `interfaces/vscode` in VSCode
2. **Press** F5 (or Run → Start Debugging)
3. **Extension Development Host** window opens
4. **Set breakpoints** in TypeScript code
5. **Trigger** commands to hit breakpoints

#### Debug Configuration

`.vscode/launch.json` (already configured):

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Run Extension",
      "type": "extensionHost",
      "request": "launch",
      "args": ["--extensionDevelopmentPath=${workspaceFolder}"],
      "outFiles": ["${workspaceFolder}/out/**/*.js"],
      "preLaunchTask": "${defaultBuildTask}"
    },
    {
      "name": "Extension Tests",
      "type": "extensionHost",
      "request": "launch",
      "args": [
        "--extensionDevelopmentPath=${workspaceFolder}",
        "--extensionTestsPath=${workspaceFolder}/out/test/suite/index"
      ],
      "outFiles": ["${workspaceFolder}/out/test/**/*.js"],
      "preLaunchTask": "npm: compile"
    }
  ]
}
```

#### Console Debugging

```typescript
// In extension code
console.log('[DEBUG] Analysis started:', filePath);
console.error('[ERROR] Analysis failed:', error);

// View output
// VSCode → View → Output → Select "Connascence" or "Extension Host"
```

#### MCP Communication Debugging

```typescript
// Enable MCP debug logging in mcpClient.ts
private handleMessage(dataString: string): void {
    console.log('[MCP] Received:', dataString);  // Add this
    const message: MCPMessage = JSON.parse(dataString);
    // ...
}
```

### Debugging MCP Server

```bash
# Run server with debug logging
python -m mcp.server --debug --log-level DEBUG

# Monitor WebSocket traffic
pip install websocket-client
python -c "import websocket; websocket.enableTrace(True); ws = websocket.create_connection('ws://localhost:8765/ws')"

# Test endpoints
curl http://localhost:8765/health
curl http://localhost:8765/status
```

---

## Testing

### Python Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_analyzer.py -v

# Run with coverage
pytest tests/ --cov=analyzer --cov=interfaces --cov=mcp --cov-report=html

# Run specific test
pytest tests/unit/test_analyzer.py::TestAnalyzer::test_basic_analysis -v

# Run with markers
pytest tests/ -m "unit"          # Only unit tests
pytest tests/ -m "integration"   # Only integration tests
pytest tests/ -m "not slow"      # Exclude slow tests
```

### VSCode Extension Tests

```bash
cd interfaces/vscode

# Run all tests
npm test

# Run in watch mode (development)
npm run test:watch

# Run with coverage
npm run test:coverage

# Debug tests
# Use VSCode debugger with "Extension Tests" configuration
```

### Writing Tests

#### Python Test Example

```python
# tests/unit/test_analyzer.py
import pytest
from analyzer.core.engine import AnalysisEngine

class TestAnalyzer:
    @pytest.fixture
    def engine(self):
        return AnalysisEngine()

    def test_basic_analysis(self, engine):
        """Test basic file analysis."""
        result = engine.analyze_file('examples/sample.py')

        assert result.qualityScore > 0
        assert len(result.findings) >= 0
        assert result.summary is not None

    @pytest.mark.slow
    def test_workspace_analysis(self, engine):
        """Test workspace-level analysis."""
        result = engine.analyze_workspace('examples/')

        assert result.summary.filesAnalyzed > 0
```

#### TypeScript Test Example

```typescript
// src/test/suite/services.test.ts
import * as assert from 'assert';
import * as vscode from 'vscode';
import { ConnascenceService } from '../../services/connascenceService';

suite('ConnascenceService Test Suite', () => {
    let service: ConnascenceService;

    setup(() => {
        const context = {} as vscode.ExtensionContext;
        service = new ConnascenceService(/* dependencies */);
    });

    test('Should analyze file successfully', async () => {
        const filePath = '/path/to/test/file.py';
        const result = await service.analyzeFile(filePath);

        assert.ok(result);
        assert.ok(result.findings);
        assert.ok(result.qualityScore >= 0);
    });
});
```

---

## Code Quality

### Linting & Formatting

```bash
# Python
ruff check .                     # Lint
ruff check . --fix               # Auto-fix issues
black .                          # Format code
mypy analyzer interfaces mcp     # Type checking

# TypeScript
cd interfaces/vscode
npm run lint                     # ESLint
npm run lint:fix                 # Auto-fix issues
```

### Pre-commit Hooks

Automatically run on commit:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### Code Review Checklist

- [ ] All tests pass
- [ ] Code coverage > 80%
- [ ] No linting errors
- [ ] Type checking passes
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No TODOs in production code
- [ ] Graceful error handling
- [ ] Performance considered

---

## VSCode Extension Development

### Hot Reload During Development

```bash
# Terminal 1: Watch TypeScript compilation
npm run watch

# Terminal 2: Launch Extension Host (F5)
# Changes automatically recompile
# Press Ctrl+R in Extension Host to reload
```

### Adding New Commands

1. **Define command in package.json**:

```json
{
  "contributes": {
    "commands": [
      {
        "command": "connascence.myNewCommand",
        "title": "My New Command",
        "category": "Connascence"
      }
    ]
  }
}
```

2. **Register command in extension.ts**:

```typescript
const disposable = vscode.commands.registerCommand(
    'connascence.myNewCommand',
    async () => {
        // Command implementation
        vscode.window.showInformationMessage('Command executed!');
    }
);

context.subscriptions.push(disposable);
```

3. **Add tests**:

```typescript
test('My new command should be registered', async () => {
    const commands = await vscode.commands.getCommands(true);
    assert.ok(commands.includes('connascence.myNewCommand'));
});
```

### Adding New Configuration Options

1. **Add to package.json**:

```json
{
  "contributes": {
    "configuration": {
      "properties": {
        "connascence.myNewOption": {
          "type": "boolean",
          "default": true,
          "description": "Enable my new feature"
        }
      }
    }
  }
}
```

2. **Access in code**:

```typescript
const config = vscode.workspace.getConfiguration('connascence');
const myOption = config.get<boolean>('myNewOption', true);
```

---

## MCP Server Development

### Running MCP Server Locally

```bash
# Start server
python -m mcp.server --port 8765 --debug

# Test WebSocket connection
# Use web socket client or browser console
const ws = new WebSocket('ws://localhost:8765/ws');
ws.onopen = () => ws.send(JSON.stringify({type: 'register', data: {}}));
ws.onmessage = (e) => console.log('Received:', e.data);
```

### Testing MCP Protocol

```python
# tests/mcp/test_server.py
import asyncio
import websockets
import json

async def test_mcp_connection():
    uri = "ws://localhost:8765/ws"
    async with websockets.connect(uri) as websocket:
        # Send register message
        await websocket.send(json.dumps({
            'type': 'register',
            'data': {'client': 'test'}
        }))

        # Receive response
        response = await websocket.recv()
        data = json.dumps(response)

        assert data['type'] == 'registered'
```

---

## Contributing Guidelines

### Branch Naming

- `feature/short-description` - New features
- `fix/short-description` - Bug fixes
- `docs/short-description` - Documentation
- `refactor/short-description` - Code refactoring
- `test/short-description` - Test improvements

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new connascence detector for dynamic coupling
fix: resolve MCP reconnection issue
docs: update installation guide
test: add integration tests for VSCode extension
refactor: simplify analysis engine architecture
```

### Pull Request Process

1. **Create feature branch**
2. **Make changes with tests**
3. **Run quality checks**:
   ```bash
   pytest tests/ -v
   ruff check . --fix
   black .
   mypy analyzer interfaces mcp
   ```
4. **Update documentation**
5. **Create PR** with description
6. **Wait for CI checks**
7. **Address review comments**
8. **Merge after approval**

---

## Troubleshooting Development Issues

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common development issues and solutions.

---

## Resources

- **API Documentation**: Generated with Sphinx (run `make docs`)
- **TypeScript Docs**: Generated with TypeDoc (run `npm run docs`)
- **Architecture Decisions**: See `docs/EXTENSION_CONSOLIDATION_ANALYSIS.md`
- **Progress Tracking**: See `docs/PRODUCTION_READINESS_PROGRESS.md`

---

**Happy coding!** 🚀

For installation help, see [INSTALLATION.md](./INSTALLATION.md).
