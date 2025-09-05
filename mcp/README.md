# Enhanced MCP Server for Connascence Analysis

🚀 **Clean, standalone MCP server for Claude Code integration** - NO Claude Flow coupling

## Quick Start

```bash
# Show available commands
python cli.py --help

# Analyze a single file  
python cli.py analyze-file path/to/file.py

# Analyze entire workspace
python cli.py analyze-workspace . --file-patterns "*.py"

# Check system health
python cli.py health-check

# Get server information
python cli.py info
```

## Available Commands

### Core Analysis
- **`analyze-file`** - Analyze individual files for connascence violations
- **`analyze-workspace`** - Analyze entire directories/workspaces  
- **`health-check`** - Check server health and integration status
- **`info`** - Get server information and capabilities

### Analysis Types
- `full` - Complete analysis (connascence + NASA + MECE)
- `connascence` - Connascence violations only
- `nasa` - NASA Power of Ten compliance
- `mece` - MECE duplication analysis

### Output Formats
- `json` - Structured JSON (default)
- `sarif` - SARIF 2.1.0 format

## Architecture

```
mcp/
├── enhanced_server.py  # Main enhanced MCP server
├── cli.py             # Command-line interface  
├── server.py          # Legacy server (compatibility)
└── README.md          # This file
```

## Integration with Claude Code

The enhanced MCP server provides a clean API that Claude Code can access:

```python
# Example Claude Code integration
import subprocess
import json

# Health check
result = subprocess.run(['python', 'mcp/cli.py', 'health-check'], 
                       capture_output=True, text=True)
health = json.loads(result.stdout)

# Analyze file  
result = subprocess.run(['python', 'mcp/cli.py', 'analyze-file', 'src/main.py'],
                       capture_output=True, text=True)  
analysis = json.loads(result.stdout)
```

## Server Information

```json
{
  "name": "connascence-analyzer-mcp",
  "version": "2.0.0", 
  "description": "MCP server for connascence analysis",
  "tools": [
    "analyze_file",
    "analyze_workspace",
    "get_violations", 
    "health_check"
  ],
  "features": [
    "Connascence analysis",
    "NASA compliance checking",
    "MECE duplication detection",
    "External tool integrations",
    "Rate limiting",
    "Audit logging"
  ]
}
```

## Examples

### Analyze Python File
```bash
python cli.py analyze-file ../utils/licensing.py --analysis-type connascence
```

### Analyze Workspace with Multiple File Types
```bash  
python cli.py analyze-workspace ../src --file-patterns "*.py" "*.js" --output results.json
```

### Check Integration Health
```bash
python cli.py health-check
```

## Configuration

The server uses centralized configuration from:
- `../config/central_constants.py` - Central constants
- `../config/defaults.json` - Default settings

## Architectural Improvements

This enhanced server addresses key architectural issues:

✅ **Consolidated Integrations** - Reduced from 9→4 files, eliminated 85.7% duplication  
✅ **Central Constants** - Magic literals eliminated  
✅ **Unified Imports** - No more try/except fallback hell  
✅ **Clean API** - Designed for Claude Code integration  

See `../docs/MCP_ENHANCED_SERVER_v3.md` for complete documentation.