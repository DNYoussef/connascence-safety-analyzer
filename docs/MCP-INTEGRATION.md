# Connascence Analyzer - MCP Server Integration

**Version**: 2.0.0
**Date**: 2025-11-01
**Status**: PRODUCTION READY

---

## Overview

The Connascence Safety Analyzer can be run as an MCP (Model Context Protocol) server, providing code quality analysis and coupling detection to AI assistants like Claude Code.

## Quick Setup

### Claude Code / Claude Desktop Configuration

Add to your MCP configuration (`C:\Users\<username>\AppData\Roaming\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "connascence-analyzer": {
      "command": "/path/to/connascence/venv/bin/python",
      "args": ["-u", "mcp/cli.py", "mcp-server"],
      "cwd": "/path/to/connascence-safety-analyzer",
      "env": {
        "PYTHONPATH": "/path/to/connascence-safety-analyzer",
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

**Windows Example**:
```json
"connascence-analyzer": {
  "command": "C:\\Projects\\connascence\\venv\\Scripts\\python.exe",
  "args": ["-u", "mcp/cli.py", "mcp-server"],
  "cwd": "C:\\Projects\\connascence-safety-analyzer"
}
```

## Available MCP Tools

### 1. `analyze_file`

Analyze a single file for connascence violations and code quality issues.

**Parameters**:
- `file_path` (required): Path to file to analyze
- `analysis_type` (optional): "quick" | "full" | "nasa-compliance" (default: "full")

**Returns**: JSON with violations, summary, and execution time

**Example**:
```json
{
  "success": true,
  "violations": [
    {
      "id": "god_object_UserManager",
      "type": "god_object",
      "severity": "high",
      "description": "Class has 26 methods (threshold: 15)",
      "line_number": 15,
      "file_path": "src/user.py"
    }
  ],
  "summary": {
    "total_violations": 7,
    "by_severity": {"high": 4, "medium": 3}
  }
}
```

### 2. `analyze_workspace`

Analyze entire workspace with pattern detection.

**Parameters**:
- `workspace_path` (required): Path to workspace/project root
- `file_patterns` (optional): Patterns to match (default: "*.py")
- `analysis_type` (optional): "quick" | "full" | "nasa-compliance"

**Returns**: Aggregated violations across all files

### 3. `health_check`

Verify MCP server status and analyzer availability.

**Parameters**: None

**Returns**: Server status, version, and capabilities

## Detection Capabilities

### 7+ Violation Types

1. **God Objects**: Classes with too many methods (>15 threshold)
2. **Parameter Bombs (CoP)**: Functions with excessive parameters (NASA limit: 6)
3. **Cyclomatic Complexity**: Complex branching logic (threshold: 10)
4. **Deep Nesting**: Nested blocks exceeding NASA limit (4 levels)
5. **Long Functions**: Functions exceeding 50-60 lines (NASA Rule 10)
6. **Magic Literals (CoM)**: Hardcoded ports, timeouts, configuration values
7. **Configuration Values**: Should be named constants

### Performance

- **Analysis Speed**: ~0.018 seconds per file
- **Workspace Speed**: ~0.07 seconds for 9 files
- **Accuracy**: 100% detection rate (7/7 violations in comprehensive test)

## Integration with Memory MCP

The Connascence Analyzer works seamlessly with the [Memory MCP Triple System](https://github.com/DNYoussef/memory-mcp-triple-system) to provide persistent code quality insights:

**Workflow Example**:
```javascript
[Code Quality Agent]:
  // 1. Analyze file with Connascence
  Connascence.analyze_file("src/auth.js", "full")

  // 2. Store violations in Memory MCP
  MemoryMCP.memory_store({
    text: JSON.stringify(violations),
    metadata: {
      agent: "code-analyzer",
      project: "auth-service",
      intent: "quality-analysis",
      timestamp: new Date().toISOString()
    }
  })

  // 3. Search prior violations for patterns
  MemoryMCP.vector_search("parameter bomb violations in auth", 10)
```

See [Memory MCP Integration](https://github.com/DNYoussef/memory-mcp-triple-system/blob/main/docs/MCP-INTEGRATION.md) for tagging protocol details.

## Agent Access Control

### Code Quality Agents (Full Access)

14 specialized agents have access to Connascence + Memory MCP:

- `coder`, `reviewer`, `tester`, `code-analyzer`
- `functionality-audit`, `theater-detection-audit`, `production-validator`
- `sparc-coder`, `analyst`, `backend-dev`, `mobile-dev`
- `ml-developer`, `base-template-generator`, `code-review-swarm`

### Planning Agents (No Access)

Planning agents (planner, researcher, system-architect, etc.) do NOT have access to Connascence to prevent non-code agents from code analysis.

**Access Control Implementation**: See [`agent-mcp-access-control.js`](https://github.com/DNYoussef/ruv-sparc-three-loop-system/blob/main/hooks/12fa/agent-mcp-access-control.js)

## Testing

### Health Check
```bash
cd /path/to/connascence-safety-analyzer
python mcp/cli.py health-check
```

Expected output:
```json
{
  "success": true,
  "server": {
    "name": "connascence-analyzer-mcp",
    "version": "2.0.0",
    "status": "healthy"
  },
  "analyzer": {
    "available": true,
    "type": "SmartIntegrationEngine"
  }
}
```

### File Analysis
```bash
python mcp/cli.py analyze-file tests/comprehensive_test.py --analysis-type full
```

Should detect 7 violations in ~0.018 seconds.

## Related Systems

- **Memory MCP Triple System**: [https://github.com/DNYoussef/memory-mcp-triple-system](https://github.com/DNYoussef/memory-mcp-triple-system)
  - Persistent cross-session memory with triple-layer retention
  - Automatic tagging protocol (WHO/WHEN/PROJECT/WHY)
  - Mode-aware context adaptation

- **ruv-SPARC Three-Loop System**: [https://github.com/DNYoussef/ruv-sparc-three-loop-system](https://github.com/DNYoussef/ruv-sparc-three-loop-system)
  - 86+ specialized agents with SOPs
  - 104+ production-ready skills
  - Complete agent coordination framework

## Troubleshooting

### Server Not Starting

1. Verify Python environment:
   ```bash
   python --version  # Should be 3.12+
   ```

2. Check dependencies:
   ```bash
   pip list | grep -E "(tree-sitter|radon|networkx)"
   ```

3. Test CLI directly:
   ```bash
   python mcp/cli.py health-check
   ```

### Unicode Encoding Errors

Ensure `PYTHONIOENCODING=utf-8` is set in environment variables:

```json
"env": {
  "PYTHONIOENCODING": "utf-8"
}
```

### No Violations Detected

Ensure tree-sitter is installed for AST parsing:

```bash
pip install tree-sitter tree-sitter-python
```

## Support

- **GitHub Issues**: [https://github.com/DNYoussef/connascence-safety-analyzer/issues](https://github.com/DNYoussef/connascence-safety-analyzer/issues)
- **Documentation**: [https://github.com/DNYoussef/connascence-safety-analyzer/blob/main/README.md](https://github.com/DNYoussef/connascence-safety-analyzer/blob/main/README.md)

---

**Version**: 2.0.0
**Updated**: 2025-11-01
**Status**: PRODUCTION READY
