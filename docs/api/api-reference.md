# API Reference

**Complete interface documentation for all Connascence Analyzer APIs**

## Overview

The Connascence Analyzer provides four primary API interfaces:

- **[CLI API](#cli-api)** - Command-line analysis with JSON/SARIF output
- **[MCP Server API](#mcp-server-api)** - Enhanced MCP server for Claude Code integration
- **[VS Code Extension API](#vs-code-extension-api)** - Real-time analysis in VS Code
- **[Configuration API](#configuration-api)** - Shared configuration interfaces

---

## CLI API

### Core Commands

#### `python -m analyzer.core`
**Primary command-line interface**

```bash
# Basic analysis
python -m analyzer.core --path /path/to/project --policy nasa_jpl_pot10

# Output formats
python -m analyzer.core --path . --format json --output results.json
python -m analyzer.core --path . --format sarif --output results.sarif

# Analysis policies
python -m analyzer.core --path . --policy strict-core
python -m analyzer.core --path . --policy lenient
```

**Arguments:**
- `--path, -p` - Path to analyze (default: current directory)
- `--policy` - Analysis policy: `default`, `strict-core`, `nasa_jpl_pot10`, `lenient`
- `--format, -f` - Output format: `json`, `yaml`, `sarif`
- `--output, -o` - Output file path
- `--nasa-validation` - Enable NASA Power of Ten validation
- `--strict-mode` - Enable strict analysis mode
- `--exclude` - Paths to exclude from analysis (multiple allowed)

**Advanced Options:**
- `--include-nasa-rules` - Include NASA-specific rules in SARIF output
- `--include-god-objects` - Include god object analysis
- `--include-mece-analysis` - Include MECE duplication analysis
- `--enable-tool-correlation` - Enable cross-tool analysis correlation
- `--confidence-threshold` - Confidence threshold for correlations (0.0-1.0)

#### `python -m mcp.cli`
**Enhanced MCP server command-line interface**

```bash
# Single file analysis
python -m mcp.cli analyze-file src/main.py --analysis-type full

# Workspace analysis
python -m mcp.cli analyze-workspace . --file-patterns "*.py" "*.js"

# Health check
python -m mcp.cli health-check

# Server information
python -m mcp.cli info
```

**Sub-commands:**

##### `analyze-file <file_path>`
- `--analysis-type` - Type: `full`, `connascence`, `mece`, `nasa`
- `--include-integrations` - Include external tool integrations
- `--format` - Output format: `json`, `sarif`
- `--output, -o` - Output file path

##### `analyze-workspace <workspace_path>`
- `--analysis-type` - Analysis type (same as file)
- `--file-patterns` - File patterns to include (e.g., "*.py" "*.js")
- `--include-integrations` - Include external integrations
- `--output, -o` - Output file path

##### `health-check`
No additional arguments. Returns server health status.

##### `info`
No additional arguments. Returns server information and capabilities.

**Global Options:**
- `--verbose, -v` - Enable verbose logging
- `--config, -c` - Path to configuration file

### Output Formats

#### JSON Output Schema
```json
{
  "success": true,
  "path": "/analyzed/path",
  "policy": "nasa_jpl_pot10",
  "violations": [
    {
      "id": "unique_violation_id",
      "rule_id": "CON_CoM",
      "type": "CoM",
      "severity": "medium",
      "description": "Magic literal detected",
      "file_path": "/path/to/file.py",
      "line_number": 42,
      "weight": 2.0,
      "analysis_mode": "unified"
    }
  ],
  "summary": {
    "total_violations": 15,
    "critical_violations": 3,
    "overall_quality_score": 0.85
  },
  "nasa_compliance": {
    "score": 0.92,
    "violations": [],
    "passing": true
  },
  "mece_analysis": {
    "score": 0.78,
    "duplications": [],
    "passing": true
  },
  "god_objects": [],
  "metrics": {
    "files_analyzed": 156,
    "analysis_time": 2.45,
    "timestamp": 1640995800.0,
    "connascence_index": 0.73
  },
  "quality_gates": {
    "overall_passing": true,
    "nasa_passing": true,
    "mece_passing": true
  }
}
```

#### SARIF Output Schema
Compatible with GitHub Code Scanning and VS Code Problems panel:

```json
{
  "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0.json",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "connascence",
          "version": "2.0.0",
          "informationUri": "https://connascence.io"
        }
      },
      "results": [
        {
          "ruleId": "CON_CoM",
          "level": "warning",
          "message": {
            "text": "Magic literal detected: Consider extracting to named constant"
          },
          "locations": [
            {
              "physicalLocation": {
                "artifactLocation": {
                  "uri": "src/example.py"
                },
                "region": {
                  "startLine": 42,
                  "startColumn": 15
                }
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### Exit Codes
- `0` - Analysis successful, no critical violations
- `1` - Analysis completed with violations (or --strict-mode with critical violations)
- `2` - Configuration error
- `3` - Runtime/execution error

---

## MCP Server API

### Server Configuration

```python
from mcp import enhanced_server

# Create server instance
server = enhanced_server.create_enhanced_mcp_server(config={
    'analysis_timeout': 30,
    'max_file_size': 1048576,
    'enable_caching': True
})

# Get server information
info = enhanced_server.get_server_info()
```

### Available Methods

#### `analyze_file(file_path, analysis_type, include_integrations, format)`
**Analyze single file with enhanced capabilities**

```python
result = await server.analyze_file(
    file_path="src/main.py",
    analysis_type="full",  # full | connascence | mece | nasa
    include_integrations=True,
    format="json"  # json | sarif
)
```

**Returns:** Enhanced analysis result with tool integrations

#### `analyze_workspace(workspace_path, analysis_type, file_patterns, include_integrations)`
**Analyze entire workspace with parallel processing**

```python
result = await server.analyze_workspace(
    workspace_path="/project/root",
    analysis_type="full",
    file_patterns=["*.py", "*.js", "*.ts"],
    include_integrations=True
)
```

**Returns:** Workspace analysis with per-file breakdown

#### `health_check()`
**Check server health and capabilities**

```python
health = await server.health_check()
# Returns: { "success": True, "components": {...}, "timestamp": ... }
```

### Integration Points

The MCP server provides enhanced integration with:
- **External Tools** - Ruff, MyPy, ESLint correlation
- **NASA Compliance** - Power of Ten rules validation
- **MECE Analysis** - Duplication detection and clustering
- **Smart Recommendations** - AI-powered improvement suggestions

---

## VS Code Extension API

### Core Services

#### `ConnascenceService`
**Primary analysis coordination service**

```typescript
import { ConnascenceService } from './services/connascenceService';

class ConnascenceService {
  async analyzeFile(filePath: string): Promise<AnalysisResult>
  async analyzeWorkspace(workspacePath: string): Promise<WorkspaceAnalysisResult>
  async validateSafety(filePath: string, profile: string): Promise<SafetyValidationResult>
  async suggestRefactoring(filePath: string, selection?: Range): Promise<RefactoringSuggestion[]>
  async getAutofixes(filePath: string): Promise<AutoFix[]>
  async generateReport(workspacePath: string): Promise<any>
}
```

#### `ConnascenceApiClient`
**API client for backend integration**

```typescript
import { ConnascenceApiClient } from './services/connascenceApiClient';

class ConnascenceApiClient {
  async analyzeFile(filePath: string): Promise<AnalysisResult>
  async analyzeWorkspace(workspacePath: string): Promise<WorkspaceAnalysisResult>
  async validateSafety(filePath: string, profile: string): Promise<SafetyValidationResult>
  async suggestRefactoring(filePath: string, selection?: any): Promise<RefactoringSuggestion[]>
  async getAutofixes(filePath: string): Promise<AutoFix[]>
  async generateReport(workspacePath: string): Promise<any>
}
```

### Data Types

#### `AnalysisResult`
```typescript
interface AnalysisResult {
  findings: Finding[];
  qualityScore: number;
  summary: {
    totalIssues: number;
    issuesBySeverity: {
      critical: number;
      major: number;
      minor: number;
      info: number;
    };
  };
  // Enhanced capabilities
  performanceMetrics?: PerformanceMetrics;
  duplicationClusters?: DuplicationCluster[];
  nasaCompliance?: NASAComplianceResult;
  smartIntegrationResults?: SmartIntegrationResult;
}
```

#### `Finding`
```typescript
interface Finding {
  id: string;
  type: string;
  severity: 'critical' | 'major' | 'minor' | 'info';
  message: string;
  file: string;
  line: number;
  column?: number;
  suggestion?: string;
}
```

#### `PerformanceMetrics`
```typescript
interface PerformanceMetrics {
  analysisTime: number;
  parallelProcessing: boolean;
  speedupFactor?: number;
  workerCount?: number;
  memoryUsage?: number;
  efficiency?: number;
}
```

#### `NASAComplianceResult`
```typescript
interface NASAComplianceResult {
  compliant: boolean;
  score: number;
  violations: NASAViolation[];
  powerOfTenRules: PowerOfTenRule[];
}

interface NASAViolation {
  rule: string;
  message: string;
  file: string;
  line: number;
  severity: 'critical' | 'major' | 'minor' | 'info';
  powerOfTenRule?: number;
}
```

### Commands

**Registered VS Code Commands:**
- `connascence.analyzeFile` - Analyze current file
- `connascence.analyzeWorkspace` - Analyze entire workspace
- `connascence.showDashboard` - Show analysis dashboard
- `connascence.refreshDashboard` - Refresh dashboard data
- `connascence.toggleHighlighting` - Toggle visual highlighting
- `connascence.manageNotifications` - Manage notification settings
- `connascence.showBrokenChainAnimation` - Show broken chain logo
- `connascence.groupByFile` - Group results by file
- `connascence.groupBySeverity` - Group results by severity
- `connascence.groupByType` - Group results by violation type

---

## Configuration API

### Shared Configuration Interface

#### `ConnascenceConfiguration`
```typescript
interface ConnascenceConfiguration {
  // Core Analysis
  safetyProfile: 'none' | 'general_safety_strict' | 'safety_level_1' | 'safety_level_3' | 'modern_general';
  realTimeAnalysis: boolean;
  debounceMs: number;
  maxDiagnostics: number;
  threshold: number;
  strictMode: boolean;
  
  // Advanced Features
  confidenceThreshold: number;
  nasaComplianceThreshold: number;
  meceQualityThreshold: number;
  analysisDepth: 'surface' | 'standard' | 'deep' | 'comprehensive';
  enableExperimentalFeatures: boolean;
  
  // Performance
  performanceAnalysis: PerformanceAnalysisConfig;
  advancedFiltering: AdvancedFilteringConfig;
  
  // File Processing
  excludePatterns: string[];
  includePatterns: string[];
  includeTests: boolean;
  exclude: string[];
  
  // VS Code Specific
  enableVisualHighlighting: boolean;
  enableCodeLens: boolean;
  enableHover: boolean;
  autoFixSuggestions: boolean;
  frameworkProfile: 'generic' | 'django' | 'fastapi' | 'react';
  
  // External Integration
  serverUrl: string;
  authenticateWithServer: boolean;
  pythonPath?: string;
  
  // Custom Rules
  customRules: CustomAnalysisRule[];
}
```

#### `PerformanceAnalysisConfig`
```typescript
interface PerformanceAnalysisConfig {
  enableProfiling: boolean;
  maxAnalysisTime: number;
  memoryThreshold: number;
  enableCaching: boolean;
  cacheSize: number;
}
```

#### `CustomAnalysisRule`
```typescript
interface CustomAnalysisRule {
  name: string;
  pattern: string;
  severity: 'error' | 'warning' | 'info' | 'hint';
  message: string;
  enabled?: boolean;
  category?: string;
  tags?: string[];
}
```

### Configuration Files

#### `.connascence.json`
```json
{
  "safetyProfile": "nasa_jpl_pot10",
  "threshold": 0.8,
  "strictMode": true,
  "analysisDepth": "comprehensive",
  "performanceAnalysis": {
    "enableProfiling": true,
    "maxAnalysisTime": 30000,
    "enableCaching": true,
    "cacheSize": 1000
  },
  "excludePatterns": [
    "**/node_modules/**",
    "**/__pycache__/**",
    "**/test/**"
  ],
  "customRules": [
    {
      "name": "project-specific-pattern",
      "pattern": "legacy_\\w+",
      "severity": "warning",
      "message": "Legacy pattern detected - consider refactoring",
      "category": "maintainability"
    }
  ]
}
```

---

## Error Handling

### Standard Error Format
```json
{
  "success": false,
  "error": {
    "code": "ANALYSIS_ERROR",
    "message": "Failed to parse Python AST",
    "details": {
      "file": "src/broken.py",
      "line": 15,
      "column": 8,
      "syntax_error": "invalid syntax"
    }
  },
  "fallback_data": {
    "violations": [],
    "summary": { "total_violations": 0 }
  }
}
```

### Common Error Codes
- `ANALYSIS_ERROR` - Analysis execution failed
- `CONFIGURATION_ERROR` - Invalid configuration
- `FILE_NOT_FOUND` - Target file/directory not found
- `PERMISSION_DENIED` - Insufficient file permissions
- `TIMEOUT_ERROR` - Analysis timeout exceeded
- `DEPENDENCY_ERROR` - Missing Python dependencies

---

## Integration Examples

### CI/CD Pipeline (GitHub Actions)
```yaml
- name: Connascence Analysis
  run: |
    python -m analyzer.core \
      --path . \
      --policy nasa_jpl_pot10 \
      --format sarif \
      --output connascence-report.sarif \
      --strict-mode

- name: Upload to GitHub Code Scanning
  uses: github/codeql-action/upload-sarif@v2
  with:
    sarif_file: connascence-report.sarif
```

### Pre-commit Hook
```yaml
- repo: local
  hooks:
  - id: connascence-analysis
    name: Connascence Analysis
    entry: python -m analyzer.core
    args: ['--path', '.', '--policy', 'nasa_jpl_pot10', '--strict-mode']
    language: python
    types: [python]
```

### MCP Integration with Claude Code
```python
# Claude Code can directly invoke MCP tools
result = await claude_code.invoke_tool("analyze_connascence", {
    "code": source_code,
    "language": "python",
    "policy": "nasa_jpl_pot10",
    "include_fixes": True
})
```

This API reference provides complete interface documentation for all Connascence Analyzer components. All interfaces are based on the actual codebase implementation and tested for accuracy.