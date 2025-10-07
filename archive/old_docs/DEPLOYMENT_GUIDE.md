# Connascence Analyzer - Deployment Guide

## Quick Start

### 1. Install CLI Tool
```bash
# From source
git clone https://github.com/DNYoussef/connascence-safety-analyzer.git
cd connascence-safety-analyzer
pip install -e .

# Verify installation
connascence --help
```

### 2. Install VSCode Extension
```bash
# Build extension
cd integrations/vscode
npm install
npm run compile

# Install in VSCode
code --install-extension .
```

### 3. Start MCP Server
```bash
# Run MCP server for agent integration
python -m mcp.server
# Server runs on port 8765
```

## Component Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│  CLI Tool       │────▶│  Analyzer    │◀────│  VSCode     │
│  (connascence)  │     │  Core Engine │     │  Extension  │
└─────────────────┘     └──────────────┘     └─────────────┘
                               ▲
                               │
                        ┌──────────────┐
                        │  MCP Server  │
                        │  (Port 8765) │
                        └──────────────┘
```

## CLI Usage

### Basic Analysis
```bash
# Analyze single file
connascence scan myfile.py

# Analyze directory
connascence scan src/ --policy standard

# NASA compliance check
connascence scan . --nasa-validation --policy nasa-compliance
```

### Advanced Features
```bash
# Generate SARIF report for CI/CD
connascence scan . --format sarif --output results.sarif

# Auto-fix violations
connascence autofix --dry-run
connascence autofix --apply

# Baseline management
connascence baseline snapshot
connascence baseline compare
```

## VSCode Extension Usage

### Commands (Cmd/Ctrl+Shift+P)
- `Connascence: Analyze` - Analyze current file
- `Connascence: Show Report` - View analysis report
- `Connascence: Fix Violations` - Apply fixes
- `Connascence: Configure` - Set policy

### Settings
```json
{
  "connascence.policy": "standard",
  "connascence.enableRealTime": true,
  "connascence.showInlineHints": true,
  "connascence.autoFix": false
}
```

## MCP Server Integration

### For AI Agents
```python
import websocket
import json

ws = websocket.WebSocket()
ws.connect("ws://localhost:8765")

# Request analysis
ws.send(json.dumps({
    "type": "analyze",
    "filePath": "/path/to/file.py",
    "options": {"policy": "standard"}
}))

result = json.loads(ws.recv())
```

### For Tool Integration
```javascript
const WebSocket = require('ws');
const ws = new WebSocket('ws://localhost:8765');

ws.on('open', () => {
    ws.send(JSON.stringify({
        type: 'register',
        client: 'my-tool',
        capabilities: ['analyze', 'autofix']
    }));
});
```

## CI/CD Integration

### GitHub Actions
```yaml
- name: Connascence Analysis
  run: |
    pip install connascence-analyzer
    connascence scan . --fail-on-critical --format sarif

- name: Upload SARIF
  uses: github/codeql-action/upload-sarif@v2
  with:
    sarif_file: results.sarif
```

### GitLab CI
```yaml
connascence:
  script:
    - pip install connascence-analyzer
    - connascence scan . --policy strict
  artifacts:
    reports:
      sast: results.sarif
```

## Docker Deployment

```dockerfile
FROM python:3.12-slim

RUN pip install connascence-analyzer

WORKDIR /app
COPY . .

CMD ["connascence", "mcp", "serve", "--host", "0.0.0.0"]
```

```bash
docker build -t connascence-analyzer .
docker run -p 8765:8765 connascence-analyzer
```

## Production Configuration

### Enterprise Setup
```yaml
# .connascence.yml
policy: nasa-compliance
thresholds:
  critical: 0
  high: 5
  medium: 20
  low: 100

exclusions:
  - "tests/**"
  - "vendor/**"

integrations:
  github: true
  slack: true
  jira: true
```

### Performance Tuning
```bash
# Enable caching
export CONNASCENCE_CACHE_DIR=/var/cache/connascence

# Parallel processing
connascence scan . --parallel --workers 8

# Incremental analysis
connascence scan . --incremental --since HEAD~1
```

## Monitoring & Metrics

### Prometheus Integration
```python
# metrics endpoint at http://localhost:8765/metrics
connascence_violations_total{severity="critical"} 0
connascence_nasa_compliance_score 0.95
connascence_analysis_duration_seconds 2.34
```

### Logging
```bash
# Set log level
export CONNASCENCE_LOG_LEVEL=INFO

# Log to file
connascence scan . --log-file analysis.log
```

## Troubleshooting

### Common Issues

**Import Error**: `ModuleNotFoundError: No module named 'analyzer'`
```bash
# Reinstall with development dependencies
pip install -e ".[dev]"
```

**VSCode Extension Not Working**
```bash
# Check CLI is installed
which connascence

# Rebuild extension
cd integrations/vscode
npm run compile
```

**MCP Server Connection Failed**
```bash
# Check port availability
netstat -an | grep 8765

# Run with debug logging
python -m mcp.server --debug
```

## Support

- **Documentation**: https://docs.connascence.io
- **GitHub Issues**: https://github.com/DNYoussef/connascence-safety-analyzer/issues
- **Discord**: https://discord.gg/connascence
- **Email**: support@connascence.io

---
Version: 1.0.0 | Status: Production Ready