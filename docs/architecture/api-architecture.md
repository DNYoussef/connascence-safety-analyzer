# API Architecture

## Overview

This document details the API architecture for the Connascence Safety Analyzer, covering the MCP server interface, VS Code extension integration points, and external API contracts.

## MCP Server API

### Base Configuration

**Server Information**:
- **Name**: "connascence"
- **Version**: "2.0.0"
- **Protocol**: MCP (Model Context Protocol)
- **Base URL**: `http://localhost:8080` (configurable)

**Authentication**: Optional (configurable via `authenticateWithServer` setting)

### Core Tools

#### 1. scan_path

**Description**: Analyze a file or directory for connascence violations

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "path": {
      "type": "string",
      "description": "File or directory path to analyze"
    },
    "policy": {
      "type": "string",
      "default": "standard",
      "enum": ["nasa-compliance", "strict", "standard", "lenient"]
    },
    "policy_preset": {
      "type": "string",
      "description": "Legacy policy name (deprecated)"
    },
    "limit_results": {
      "type": "integer",
      "description": "Maximum number of violations to return"
    }
  },
  "required": ["path"]
}
```

**Response Schema**:
```json
{
  "success": true,
  "summary": {
    "total_violations": 42,
    "critical_count": 5,
    "high_count": 12,
    "medium_count": 20,
    "low_count": 5
  },
  "violations": [
    {
      "id": "violation_id",
      "rule_id": "CON_CoM",
      "type": "CoM",
      "severity": "medium",
      "description": "Magic literal detected",
      "file_path": "/path/to/file.py",
      "line_number": 42,
      "weight": 2.0
    }
  ],
  "scan_metadata": {
    "path": "/analyzed/path",
    "policy_preset": "standard",
    "timestamp": 1640995200.0,
    "analyzer_version": "2.0.0"
  },
  "results_limited": false,
  "limit_applied": null
}
```

**Error Response**:
```json
{
  "success": false,
  "error": "Rate limit exceeded",
  "summary": {
    "total_violations": 0,
    "critical_count": 0,
    "high_count": 0,
    "medium_count": 0,
    "low_count": 0
  },
  "violations": [],
  "scan_metadata": {
    "path": "/requested/path",
    "error": true
  }
}
```

#### 2. explain_finding

**Description**: Explain a connascence violation in detail

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "violation_id": {
      "type": "string",
      "description": "Violation ID to explain"
    },
    "rule_id": {
      "type": "string",
      "description": "Rule ID (alternative to violation_id)"
    },
    "include_examples": {
      "type": "boolean",
      "default": false
    },
    "context": {
      "type": "object",
      "description": "Additional context information"
    }
  },
  "required": ["violation_id"]
}
```

**Response Schema**:
```json
{
  "success": true,
  "rule_id": "CON_CoM",
  "explanation": "Connascence of Meaning occurs when multiple components must agree on the meaning of particular values...",
  "connascence_type": "CoM",
  "impact": "Makes code harder to maintain and prone to errors when values need to change",
  "suggestions": [
    "Extract magic literals to named constants",
    "Use configuration objects or enums",
    "Create a shared constants module"
  ],
  "examples": [
    {
      "problem_code": "if value > 100:  # Magic literal",
      "solution_code": "THRESHOLD = 100\\nif value > THRESHOLD:",
      "description": "Extract magic literal to constant"
    }
  ]
}
```

#### 3. propose_autofix

**Description**: Propose automated fixes for violations

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "violation": {
      "type": "object",
      "description": "Single violation to fix"
    },
    "violations": {
      "type": "array",
      "description": "Multiple violations to fix"
    },
    "safety_level": {
      "type": "string",
      "enum": ["conservative", "moderate", "aggressive"],
      "default": "conservative"
    },
    "include_diff": {
      "type": "boolean",
      "default": false
    }
  }
}
```

**Response Schema (Single Violation)**:
```json
{
  "success": true,
  "patch_available": true,
  "patch_description": "Extract magic literal to constant",
  "confidence_score": 0.85,
  "safety_level": "safe",
  "old_code": "value = 100",
  "new_code": "THRESHOLD = 100\\nvalue = THRESHOLD"
}
```

**Response Schema (Multiple Violations)**:
```json
{
  "success": true,
  "fixes": [
    {
      "violation_id": "viol_1",
      "fix_type": "extract_constant",
      "description": "Extract magic literal to named constant",
      "safety_score": 0.8,
      "estimated_effort": "low"
    }
  ],
  "safety_level": "conservative",
  "total_fixes": 5
}
```

#### 4. list_presets

**Description**: List available policy presets

**Input Schema**:
```json
{
  "type": "object",
  "properties": {},
  "required": []
}
```

**Response Schema**:
```json
{
  "success": true,
  "presets": [
    {
      "name": "nasa-compliance",
      "description": "NASA JPL Power of Ten compliance (highest safety)",
      "type": "unified"
    },
    {
      "name": "nasa_jpl_pot10",
      "description": "NASA JPL Power of Ten (deprecated)",
      "type": "legacy",
      "unified_equivalent": "nasa-compliance"
    }
  ],
  "unified_presets": [...],
  "legacy_presets": [...],
  "policy_system_version": "2.0",
  "recommendation": "Use unified policy names for consistent behavior across all integrations"
}
```

#### 5. validate_policy

**Description**: Validate policy configuration

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "policy_preset": {
      "type": "string",
      "description": "Policy name to validate"
    }
  }
}
```

**Response Schema (Valid)**:
```json
{
  "success": true,
  "valid": true,
  "policy_preset": "nasa-compliance",
  "unified_name": "nasa-compliance",
  "is_legacy": false,
  "validation_details": "Policy nasa-compliance is valid",
  "deprecation_warning": false
}
```

**Response Schema (Invalid)**:
```json
{
  "success": true,
  "valid": false,
  "error": "Invalid policy preset: unknown_policy",
  "available_policies": ["nasa-compliance", "strict", "standard", "lenient"]
}
```

#### 6. get_metrics

**Description**: Get server performance metrics

**Response Schema**:
```json
{
  "success": true,
  "request_count": 150,
  "response_times": {
    "avg": 0.1,
    "min": 0.05,
    "max": 0.2
  },
  "tool_usage": {
    "scan_path": 100,
    "explain_finding": 30,
    "propose_autofix": 20,
    "list_presets": 5
  }
}
```

#### 7. enforce_policy

**Description**: Enforce policy with budget limits

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "policy_preset": {
      "type": "string",
      "default": "standard"
    },
    "budget_limits": {
      "type": "object",
      "description": "Violation type limits",
      "properties": {
        "CoM": {"type": "integer"},
        "CoP": {"type": "integer"},
        "CoA": {"type": "integer"}
      }
    }
  }
}
```

**Response Schema**:
```json
{
  "success": true,
  "budget_status": {
    "budget_exceeded": true,
    "policy_preset": "strict",
    "violation_counts": {
      "CoM": 15,
      "CoP": 8,
      "CoA": 3
    }
  },
  "violations_over_budget": [...]
}
```

### Server Configuration

**Rate Limiting**:
- Default: 60 requests per minute per client
- Configurable via `max_requests_per_minute`
- Client identification via `client_id` parameter

**Path Security**:
- Automatic traversal attack prevention
- Optional allow-list configuration
- Restricted path enforcement

**Audit Logging**:
```python
{
  "timestamp": 1640995200.0,
  "event": "tool_request",
  "details": {
    "tool_name": "scan_path",
    "client_id": "vscode_user_123",
    "path": "/workspace/src"
  }
}
```

## VS Code Extension API

### Configuration Schema

The extension exposes comprehensive configuration through VS Code settings:

#### Core Settings
```json
{
  "connascence.safetyProfile": {
    "type": "string",
    "enum": ["none", "general_safety_strict", "safety_level_1", "safety_level_3", "modern_general"],
    "default": "modern_general",
    "description": "Active safety profile for analysis"
  },
  "connascence.realTimeAnalysis": {
    "type": "boolean",
    "default": true,
    "description": "Enable real-time analysis as you type"
  },
  "connascence.debounceMs": {
    "type": "number",
    "default": 1000,
    "description": "Debounce delay in milliseconds for real-time analysis"
  }
}
```

#### Advanced Configuration
```json
{
  "connascence.linterIntegration": {
    "type": "object",
    "properties": {
      "enableRuffCorrelation": {"type": "boolean", "default": true},
      "enablePylintCorrelation": {"type": "boolean", "default": true},
      "unifiedDiagnostics": {"type": "boolean", "default": true}
    }
  },
  "connascence.performanceAnalysis": {
    "type": "object",
    "properties": {
      "enableProfiling": {"type": "boolean", "default": true},
      "maxAnalysisTime": {"type": "number", "default": 30000},
      "memoryThreshold": {"type": "number", "default": 512},
      "enableCaching": {"type": "boolean", "default": true}
    }
  }
}
```

### Commands API

The extension provides comprehensive command integration:

#### Analysis Commands
- `connascence.analyzeFile` - Analyze current file
- `connascence.analyzeWorkspace` - Analyze entire workspace
- `connascence.analyzeSelection` - Analyze selected code
- `connascence.validateSafety` - Validate safety standards

#### Refactoring Commands
- `connascence.suggestRefactoring` - Suggest code improvements
- `connascence.applyAutofix` - Apply safe auto-fixes

#### Reporting Commands
- `connascence.generateReport` - Generate quality report
- `connascence.exportSarif` - Export SARIF report
- `connascence.exportJson` - Export JSON report

#### Configuration Commands
- `connascence.openSettings` - Open settings
- `connascence.toggleSafetyProfile` - Switch safety profile
- `connascence.exportConfiguration` - Export configuration
- `connascence.importConfiguration` - Import configuration

#### View Commands
- `connascence.showDashboard` - Show quality dashboard
- `connascence.toggleHighlighting` - Toggle code highlighting
- `connascence.showBrokenChainAnimation` - Show broken chain animation

### Diagnostic Integration

**Diagnostic Provider**:
```typescript
interface ConnascenceDiagnostic extends vscode.Diagnostic {
  readonly connascenceType: string;
  readonly ruleId: string;
  readonly weight: number;
  readonly suggestions?: string[];
}
```

**Diagnostic Collection**:
```typescript
const diagnosticCollection = vscode.languages.createDiagnosticCollection('connascence');

// Set diagnostics for a document
diagnosticCollection.set(document.uri, [
  new vscode.Diagnostic(
    range,
    "Magic literal detected (CoM violation)",
    vscode.DiagnosticSeverity.Warning
  )
]);
```

### Language Server Protocol Support

**Hover Provider**:
```typescript
vscode.languages.registerHoverProvider('python', {
  provideHover(document, position, token) {
    // Provide connascence explanations on hover
    return new vscode.Hover([
      "**Connascence of Meaning (CoM)**",
      "Multiple components must agree on the meaning of particular values.",
      "Suggestion: Extract to named constant"
    ]);
  }
});
```

**Code Action Provider**:
```typescript
vscode.languages.registerCodeActionsProvider('python', {
  provideCodeActions(document, range, context, token) {
    const codeActions: vscode.CodeAction[] = [];
    
    for (const diagnostic of context.diagnostics) {
      if (diagnostic.source === 'connascence') {
        const action = new vscode.CodeAction(
          'Extract magic literal to constant',
          vscode.CodeActionKind.QuickFix
        );
        action.edit = createWorkspaceEdit(document, range);
        codeActions.push(action);
      }
    }
    
    return codeActions;
  }
});
```

### Tree Data Providers

**Dashboard Provider**:
```typescript
interface DashboardItem extends vscode.TreeItem {
  readonly type: 'metric' | 'violation' | 'category';
  readonly value?: string | number;
  readonly children?: DashboardItem[];
}

class ConnascenceDashboardProvider implements vscode.TreeDataProvider<DashboardItem> {
  getTreeItem(element: DashboardItem): vscode.TreeItem {
    return element;
  }
  
  getChildren(element?: DashboardItem): Promise<DashboardItem[]> {
    if (!element) {
      return this.getRootElements();
    }
    return this.getElementChildren(element);
  }
}
```

**Analysis Results Provider**:
```typescript
class AnalysisResultsProvider implements vscode.TreeDataProvider<ViolationItem> {
  private groupBy: 'file' | 'severity' | 'type' = 'file';
  
  setGroupBy(groupBy: 'file' | 'severity' | 'type') {
    this.groupBy = groupBy;
    this._onDidChangeTreeData.fire();
  }
  
  getChildren(element?: ViolationItem): Promise<ViolationItem[]> {
    switch (this.groupBy) {
      case 'file': return this.getViolationsByFile(element);
      case 'severity': return this.getViolationsBySeverity(element);
      case 'type': return this.getViolationsByType(element);
    }
  }
}
```

## CLI API

### Command-Line Interface

**Base Command Structure**:
```bash
connascence [command] [options]
connascence-mcp [mcp-options]
```

**Analysis Commands**:
```bash
# Basic analysis
connascence analyze --path ./src --policy nasa-compliance

# Advanced analysis with options
connascence analyze \
  --path ./src \
  --policy strict \
  --format sarif \
  --output report.sarif \
  --nasa-validation \
  --strict-mode \
  --exclude tests/ node_modules/ \
  --enable-tool-correlation \
  --confidence-threshold 0.8
```

**MCP Server Commands**:
```bash
# Start MCP server
connascence-mcp --port 8080 --host localhost

# Start with configuration
connascence-mcp --config ./mcp-config.json
```

### Exit Codes

- `0` - Success (no critical violations or acceptable violations)
- `1` - Analysis failed or critical violations found in strict mode
- `2` - Configuration error
- `3` - Path not found or access denied

### Output Formats

#### JSON Output
```json
{
  "success": true,
  "path": "./src",
  "policy": "nasa-compliance",
  "violations": [...],
  "summary": {
    "total_violations": 42,
    "critical_violations": 5,
    "overall_quality_score": 0.85
  },
  "nasa_compliance": {
    "score": 0.92,
    "passing": false,
    "violations": [...]
  },
  "mece_analysis": {
    "score": 0.78,
    "duplications": [...],
    "passing": true
  },
  "metrics": {
    "files_analyzed": 25,
    "analysis_time": 2.5,
    "timestamp": 1640995200.0
  }
}
```

#### SARIF Output
```json
{
  "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0.json",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "Connascence Safety Analyzer",
          "version": "2.0.0",
          "informationUri": "https://docs.connascence.io",
          "rules": [...]
        }
      },
      "results": [
        {
          "ruleId": "CON_CoM",
          "message": {
            "text": "Magic literal detected"
          },
          "locations": [
            {
              "physicalLocation": {
                "artifactLocation": {
                  "uri": "src/main.py"
                },
                "region": {
                  "startLine": 42,
                  "startColumn": 10,
                  "endLine": 42,
                  "endColumn": 13
                }
              }
            }
          ],
          "level": "warning",
          "properties": {
            "connascence_type": "CoM",
            "weight": 2.0,
            "nasa_rule": null
          }
        }
      ]
    }
  ]
}
```

## Error Handling

### Standard Error Response Format

All APIs use a consistent error response format:

```json
{
  "success": false,
  "error": {
    "code": 5001,
    "message": "Path not allowed: ../etc/passwd",
    "integration": "mcp",
    "context": {
      "path": "../etc/passwd",
      "client_id": "user_123",
      "timestamp": 1640995200.0
    }
  }
}
```

### Error Code Mapping

- `5001` - General analysis error
- `5002` - Path validation error
- `5003` - Policy validation error
- `5004` - Rate limit exceeded
- `5005` - Configuration error
- `5006` - Dependency missing
- `5007` - Timeout error

### Security Considerations

**Path Traversal Protection**:
- All path inputs validated for `..` sequences
- Restricted paths enforced (`/etc`, `/var/log`, Windows system paths)
- Optional allow-list configuration

**Rate Limiting**:
- Per-client request limiting
- Configurable thresholds
- Graceful degradation

**Input Validation**:
- JSON schema validation for all inputs
- SQL injection prevention (though no SQL used)
- Command injection prevention

This API architecture ensures consistent, secure, and performant integration across all interfaces of the Connascence Safety Analyzer.