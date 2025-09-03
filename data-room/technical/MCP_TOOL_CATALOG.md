# Connascence MCP Tool Catalog

**Version**: 1.0.0  
**Last Updated**: 2025-09-03  
**Target Audience**: Developers, DevOps Engineers, QA Teams

## Overview

The Connascence MCP (Model Context Protocol) server provides a comprehensive suite of tools for code quality analysis, focusing on connascence detection, security validation, and enterprise-grade compliance checking. This catalog documents all available tools with their inputs, outputs, and usage scenarios.

## Quick Reference

| Tool Name | Category | Description | Security Level |
|-----------|----------|-------------|----------------|
| `scan_path` | Core Analysis | Scan path for connascence violations | Standard |
| `explain_finding` | Analysis Support | Explain specific findings with context | Standard |
| `propose_autofix` | Code Improvement | Generate automated fix suggestions | Standard |
| `list_presets` | Configuration | List available policy presets | Read-only |
| `validate_policy` | Configuration | Validate policy configurations | Standard |
| `get_metrics` | Monitoring | Retrieve analysis metrics and statistics | Read-only |
| `enforce_policy` | Compliance | Enforce policy rules with budget control | Standard |
| `analyze_with_grammar` | Advanced Analysis | Grammar-enhanced comprehensive analysis | Premium |
| `get_quality_score` | Quality Assessment | Calculate weighted quality scores | Premium |
| `suggest_grammar_fixes` | Code Improvement | Grammar-constrained fix suggestions | Premium |
| `validate_safety_profile` | Compliance | Safety profile compliance validation | Premium |
| `compare_quality_trends` | Analytics | Compare quality metrics across versions | Premium |

---

## Core Analysis Tools

### 1. scan_path

**Purpose**: Primary tool for scanning codebases and detecting connascence violations.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "path": {
      "type": "string",
      "description": "File or directory path to analyze",
      "required": true
    },
    "policy_preset": {
      "type": "string",
      "description": "Policy preset to apply",
      "enum": ["strict-core", "service-defaults", "experimental", "default"],
      "default": "default"
    },
    "limit_results": {
      "type": "integer",
      "description": "Maximum number of violations to return",
      "minimum": 1,
      "maximum": 1000
    }
  }
}
```

**Output Format**:
```json
{
  "summary": {
    "total_violations": 42,
    "critical_count": 3,
    "high_count": 8,
    "medium_count": 20,
    "low_count": 11
  },
  "violations": [
    {
      "id": "violation_123",
      "type": "CoM",
      "severity": "high",
      "file": "/src/example.py",
      "line": 45,
      "description": "Magic literal '42' found in multiple locations"
    }
  ],
  "scan_metadata": {
    "path": "/project/src",
    "policy_preset": "strict-core",
    "timestamp": 1725360000.123
  },
  "results_limited": false
}
```

**Usage Scenarios**:
- **CI/CD Integration**: Automated quality checks in build pipelines
- **Developer Workflow**: Pre-commit hooks and IDE integration
- **Code Review**: Comprehensive analysis before merge requests
- **Technical Debt Assessment**: Large-scale codebase evaluation

**CLI Example**:
```bash
# Basic scan
mcp-client call scan_path '{"path": "./src"}'

# Strict policy with result limiting
mcp-client call scan_path '{
  "path": "./critical-module",
  "policy_preset": "strict-core",
  "limit_results": 50
}'
```

**VS Code Integration**:
```typescript
// Extension command
vscode.commands.executeCommand('connascence.scanPath', {
  path: vscode.workspace.rootPath,
  policy_preset: 'service-defaults'
});
```

---

### 2. explain_finding

**Purpose**: Provides detailed explanations of connascence violations with educational context.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "finding_id": {
      "type": "string",
      "description": "Violation ID or rule ID to explain",
      "required": true,
      "pattern": "^[a-zA-Z0-9_\\-\\.]+$"
    },
    "rule_id": {
      "type": "string",
      "description": "Alternative to finding_id for rule-based explanations"
    },
    "include_examples": {
      "type": "boolean",
      "description": "Include code examples in explanation",
      "default": false
    }
  }
}
```

**Output Format**:
```json
{
  "connascence_type": "CoM",
  "explanation": "Connascence of Meaning occurs when multiple components must agree on the meaning of particular values...",
  "severity_rationale": "High severity due to maintenance overhead and error-prone refactoring",
  "examples": [
    {
      "problem_code": "if user_status == \"ACTIVE\":\\n    # code",
      "solution_code": "USER_STATUS_ACTIVE = \"ACTIVE\"\\nif user_status == USER_STATUS_ACTIVE:"
    }
  ],
  "suggested_actions": [
    "Extract magic literals to named constants",
    "Use enums for status values",
    "Review similar patterns across codebase"
  ]
}
```

**Usage Scenarios**:
- **Developer Education**: Learning about connascence principles
- **Code Review Training**: Understanding violation severity and impact
- **Documentation Generation**: Automated explanation for reports
- **IDE Tooltips**: Contextual help in development environments

---

### 3. propose_autofix

**Purpose**: Generates automated fix suggestions for detected violations.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "violation": {
      "type": "object",
      "description": "Violation object from scan results",
      "required": true,
      "properties": {
        "id": {"type": "string", "required": true},
        "type": {"type": "string", "required": true},
        "file_path": {"type": "string", "required": true},
        "line": {"type": "integer"},
        "severity": {"type": "string"}
      }
    },
    "include_diff": {
      "type": "boolean",
      "description": "Include unified diff in response",
      "default": false
    }
  }
}
```

**Output Format**:
```json
{
  "patch_available": true,
  "patch_description": "Extract magic literal to named constant",
  "confidence_score": 0.85,
  "safety_level": "safe",
  "violation_id": "violation_123",
  "diff": "+ THRESHOLD = 100\\n- if value > 100:\\n+ if value > THRESHOLD:",
  "estimated_effort": "5 minutes",
  "risk_assessment": "Low risk - isolated change"
}
```

**Usage Scenarios**:
- **Automated Remediation**: Batch fixing of common violations
- **Developer Assistance**: Suggested improvements during coding
- **Technical Debt Reduction**: Systematic cleanup of legacy code
- **Quality Gate Integration**: Automatic fixes in deployment pipeline

---

## Configuration Tools

### 4. list_presets

**Purpose**: Retrieve available policy presets for different project types.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {}
}
```

**Output Format**:
```json
{
  "presets": [
    {
      "id": "strict-core",
      "name": "Strict Core",
      "description": "Strict rules for core systems",
      "target_environments": ["production", "critical-systems"],
      "violation_threshold": 0,
      "recommended_for": ["financial", "healthcare", "aerospace"]
    },
    {
      "id": "service-defaults",
      "name": "Service Defaults",
      "description": "Balanced rules for microservices",
      "target_environments": ["development", "staging", "production"],
      "violation_threshold": 10,
      "recommended_for": ["web-services", "apis", "business-logic"]
    }
  ]
}
```

### 5. validate_policy

**Purpose**: Validate policy configurations before application.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "policy_preset": {
      "type": "string",
      "description": "Policy preset ID to validate"
    },
    "policy": {
      "type": "object",
      "description": "Custom policy configuration"
    }
  }
}
```

**Output Format**:
```json
{
  "valid": true,
  "policy_preset": "strict-core",
  "issues": [],
  "recommendations": [
    "Consider enabling nasa_rule_validation for aerospace projects"
  ],
  "compatibility": {
    "frameworks": ["django", "fastapi", "flask"],
    "languages": ["python", "javascript", "typescript"]
  }
}
```

---

## Monitoring & Analytics Tools

### 6. get_metrics

**Purpose**: Retrieve comprehensive analysis metrics and performance data.

**Output Format**:
```json
{
  "request_count": 1247,
  "response_times": {
    "avg": 125.5,
    "min": 45,
    "max": 320,
    "p95": 280,
    "p99": 310
  },
  "tool_usage": {
    "scan_path": 892,
    "explain_finding": 234,
    "propose_autofix": 89,
    "analyze_with_grammar": 32
  },
  "violation_trends": {
    "total_scanned_files": 15420,
    "violation_density": 2.3,
    "most_common_types": ["CoM", "CoP", "CoT"],
    "improvement_rate": 0.15
  },
  "performance_metrics": {
    "cache_hit_rate": 0.73,
    "average_scan_time": 2.1,
    "memory_usage": "45MB"
  }
}
```

### 7. enforce_policy

**Purpose**: Enforce policy rules with budget controls and compliance reporting.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "policy_preset": {
      "type": "string",
      "description": "Policy preset to enforce"
    },
    "budget_limits": {
      "type": "object",
      "properties": {
        "total_violations": {"type": "integer"},
        "critical_violations": {"type": "integer"},
        "high_violations": {"type": "integer"}
      }
    },
    "violations": {
      "type": "array",
      "description": "Existing violations to check against budget"
    }
  }
}
```

**Output Format**:
```json
{
  "budget_status": {
    "budget_exceeded": false,
    "total_violations": 23,
    "budget_limit": 50,
    "utilization_percentage": 46
  },
  "violations_over_budget": [],
  "policy_preset": "service-defaults",
  "compliance_score": 0.87,
  "next_review_date": "2025-10-03",
  "enforcement_actions": [
    "Block deployment if critical violations exceed 0",
    "Require manager approval for medium violations > 20"
  ]
}
```

---

## Advanced Analysis Tools (Premium)

### 8. analyze_with_grammar

**Purpose**: Comprehensive analysis using grammar-enhanced backend with safety profiles.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "path": {
      "type": "string",
      "description": "Path to analyze",
      "required": true
    },
    "safety_profile": {
      "type": "string",
      "enum": ["general_safety_strict", "safety_level_1", "safety_level_3", "modern_general"],
      "description": "NASA/ESA safety profile to apply"
    },
    "framework_profile": {
      "type": "string",
      "enum": ["django", "fastapi", "react", "generic"],
      "default": "generic"
    },
    "include_refactoring": {
      "type": "boolean",
      "default": true
    },
    "include_safety_compliance": {
      "type": "boolean",
      "default": false
    }
  }
}
```

**Output Format**:
```json
{
  "success": true,
  "summary": {
    "total_files": 127,
    "average_quality_score": 0.847,
    "files_with_violations": 23,
    "safety_profile": "general_safety_strict",
    "framework_profile": "django"
  },
  "results": [
    {
      "file_path": "/src/models.py",
      "language": "python",
      "quality_score": 0.89,
      "grammar_validation": {
        "is_valid": true,
        "violations": [],
        "has_safety_violations": false
      },
      "refactoring_opportunities": [
        {
          "technique": "extract_method",
          "description": "Large function can be broken down",
          "confidence": 0.92,
          "location": "145:12"
        }
      ],
      "safety_compliance": {
        "nasa_compliant": true,
        "violations": [],
        "risk_level": "low"
      }
    }
  ]
}
```

### 9. get_quality_score

**Purpose**: Calculate comprehensive quality scores using weighted metrics.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "path": {"type": "string", "required": true},
    "profile": {
      "type": "string",
      "enum": ["general_safety_strict", "modern_general", "enterprise"],
      "default": "modern_general"
    },
    "weights": {
      "type": "object",
      "properties": {
        "grammar": {"type": "number", "default": 0.3},
        "connascence": {"type": "number", "default": 0.25},
        "cohesion": {"type": "number", "default": 0.25},
        "magic_literals": {"type": "number", "default": 0.2}
      }
    }
  }
}
```

**Output Format**:
```json
{
  "success": true,
  "project_quality_score": 0.847,
  "profile": "modern_general",
  "weights": {
    "grammar": 0.3,
    "connascence": 0.25,
    "cohesion": 0.25,
    "magic_literals": 0.2
  },
  "summary": {
    "total_files": 89,
    "total_violations": {
      "connascence": 45,
      "magic_literals": 23,
      "god_objects": 7,
      "safety": 2
    }
  },
  "file_scores": [
    {
      "file_path": "/src/utils.py",
      "overall_score": 0.92,
      "component_scores": {
        "grammar": 1.0,
        "safety": 1.0,
        "connascence": 0.85,
        "cohesion": 0.90
      }
    }
  ],
  "improvement_suggestions": [
    "Focus on reducing Connascence of Meaning violations",
    "Consider extracting utility functions to reduce coupling"
  ]
}
```

### 10. suggest_grammar_fixes

**Purpose**: Generate grammar-constrained fix suggestions with safety validation.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "path": {"type": "string", "required": true},
    "safety_profile": {
      "type": "string",
      "enum": ["general_safety_strict", "safety_level_1", "modern_general"]
    },
    "max_fixes": {
      "type": "integer",
      "default": 5,
      "minimum": 1,
      "maximum": 20
    },
    "confidence_threshold": {
      "type": "number",
      "default": 0.7,
      "minimum": 0.0,
      "maximum": 1.0
    },
    "dry_run": {
      "type": "boolean",
      "default": true
    }
  }
}
```

**Output Format**:
```json
{
  "success": true,
  "file_path": "/src/calculator.py",
  "safety_profile": "general_safety_strict",
  "dry_run": true,
  "fixes_found": 3,
  "fixes": [
    {
      "id": "fix_001",
      "type": "extract_constant",
      "confidence": 0.95,
      "description": "Extract magic number 3.14159 to named constant PI",
      "location": {
        "line": 42,
        "column": 15
      },
      "preview": {
        "before": "area = radius * radius * 3.14159",
        "after": "PI = 3.14159\\narea = radius * radius * PI"
      },
      "safety_impact": "none",
      "estimated_effort": "2 minutes"
    }
  ],
  "analysis_summary": {
    "quality_score": 0.78,
    "grammar_valid": false,
    "refactoring_opportunities": 5
  }
}
```

### 11. validate_safety_profile

**Purpose**: Comprehensive safety profile compliance validation for critical systems.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "path": {"type": "string", "required": true},
    "profile": {
      "type": "string",
      "enum": ["general_safety_strict", "safety_level_1", "safety_level_3"],
      "required": true
    },
    "generate_report": {"type": "boolean", "default": true},
    "include_evidence": {"type": "boolean", "default": true}
  }
}
```

**Output Format**:
```json
{
  "success": true,
  "profile": "general_safety_strict",
  "compliance_summary": {
    "total_files": 156,
    "compliant_files": 142,
    "compliance_percentage": 91.0,
    "total_violations": 28
  },
  "file_results": [
    {
      "file_path": "/src/flight_controller.py",
      "compliant": false,
      "violations": 3,
      "nasa_compliant": false,
      "evidence": {
        "violations": [
          {
            "rule": "nasa_rule_1",
            "description": "Recursive function detected",
            "line": 89,
            "severity": "critical"
          }
        ]
      }
    }
  ],
  "detailed_report": {
    "violation_breakdown": {
      "nasa_rule_1": 8,
      "nasa_rule_2": 12,
      "nasa_rule_4": 8
    },
    "recommendations": [
      "Replace goto statements and recursion with structured control flow",
      "Add loop bound annotations and convert infinite loops to bounded iterations"
    ],
    "next_steps": [
      "Focus on critical violations first",
      "Implement pre-commit hooks for compliance"
    ],
    "certification_readiness": {
      "do_178b_level": "not_ready",
      "missing_requirements": ["formal_verification", "test_coverage_100%"]
    }
  }
}
```

---

## Integration Examples

### CLI Integration

```bash
# Basic project scan
connascence-mcp scan_path '{"path": "./src", "policy_preset": "strict-core"}'

# Quality assessment pipeline
connascence-mcp get_quality_score '{
  "path": "./",
  "profile": "enterprise",
  "weights": {"safety": 0.4, "connascence": 0.3, "grammar": 0.3}
}'

# Safety validation for aerospace
connascence-mcp validate_safety_profile '{
  "path": "./flight-software",
  "profile": "general_safety_strict",
  "generate_report": true
}'
```

### VS Code Extension Integration

```typescript
// Extension configuration
interface ConnascenceConfig {
  mcpServerPath: string;
  defaultPreset: string;
  autoScanOnSave: boolean;
  realTimeAnalysis: boolean;
}

// Tool execution
class ConnascenceAnalyzer {
  async scanWorkspace(config: ConnascenceConfig): Promise<ScanResults> {
    return await this.mcpClient.call('scan_path', {
      path: vscode.workspace.rootPath,
      policy_preset: config.defaultPreset
    });
  }

  async explainViolation(violationId: string): Promise<ExplanationResult> {
    return await this.mcpClient.call('explain_finding', {
      finding_id: violationId,
      include_examples: true
    });
  }
}
```

### CI/CD Pipeline Integration

```yaml
# GitHub Actions example
name: Code Quality Check
on: [push, pull_request]

jobs:
  quality-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Connascence MCP
        run: pip install connascence-analyzer[mcp]
      
      - name: Run Analysis
        run: |
          connascence-mcp scan_path '{
            "path": "./src",
            "policy_preset": "strict-core"
          }' > analysis.json
      
      - name: Enforce Policy
        run: |
          connascence-mcp enforce_policy '{
            "policy_preset": "strict-core",
            "budget_limits": {"critical_violations": 0, "high_violations": 5}
          }'
      
      - name: Generate Report
        run: |
          connascence-mcp get_quality_score '{
            "path": "./",
            "profile": "enterprise"
          }' > quality-report.json
```

### Docker Integration

```dockerfile
# Dockerfile for containerized analysis
FROM python:3.11-slim

RUN pip install connascence-analyzer[mcp,security]

# Copy analysis configuration
COPY connascence-config.json /app/config.json
COPY security-profile.json /app/security.json

WORKDIR /app

# Health check using metrics endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s \
  CMD connascence-mcp get_metrics || exit 1

ENTRYPOINT ["connascence-mcp-server", "--config", "/app/config.json"]
```

---

## Security & Authentication

### Enterprise Security Features

For enterprise deployments, the MCP server supports:

- **Session-based Authentication**: Token-based auth with expiration
- **Role-based Access Control**: Tool access based on user roles
- **Audit Logging**: Comprehensive logging of all tool executions
- **Rate Limiting**: Per-user and per-tool rate limits
- **Air-gapped Deployment**: No external network dependencies
- **Security Clearance Levels**: Different access levels for classified projects

### Secure Tool Execution

```python
# Example of secure tool execution
response = secure_mcp_server.execute_tool(
    tool_name="validate_safety_profile",
    arguments={
        "path": "/classified/flight-control",
        "profile": "general_safety_strict"
    },
    session_token="secure_session_token",
    ip_address="192.168.1.100"
)
```

---

## Performance Considerations

### Optimization Guidelines

1. **Path Scanning**: Use `limit_results` for large codebases
2. **Batch Operations**: Group related analysis calls
3. **Caching**: MCP server caches analysis results for 15 minutes
4. **Parallel Processing**: Use async operations for multiple tools
5. **Memory Management**: Monitor memory usage for large projects

### Performance Metrics

- **Typical Scan Speed**: 500-1000 files/minute
- **Memory Usage**: ~2MB per 1000 lines of code
- **Cache Hit Rate**: 70-80% for repeated scans
- **Response Time**: < 200ms for cached results

---

## Error Handling & Troubleshooting

### Common Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| `RATE_LIMIT_EXCEEDED` | Too many requests | Wait and retry, or increase limits |
| `PATH_NOT_ALLOWED` | Security restriction | Check path permissions |
| `FEATURE_UNAVAILABLE` | Premium feature without license | Upgrade license |
| `ANALYSIS_ERROR` | Internal analysis failure | Check input format and retry |
| `VALIDATION_ERROR` | Input validation failed | Review input schema |

### Debugging Tips

1. **Enable Verbose Logging**: Set `LOG_LEVEL=DEBUG`
2. **Check Tool Availability**: Use `get_metrics` to verify setup
3. **Validate Inputs**: Use JSON schema validation
4. **Monitor Resources**: Check memory and disk usage
5. **Review Audit Logs**: Check security logs for access issues

---

## Support & Documentation

### Additional Resources

- **API Documentation**: Complete OpenAPI specification available
- **Enterprise Support**: 24/7 support for enterprise customers
- **Training Materials**: Video tutorials and best practices guide
- **Integration Examples**: Sample code for popular CI/CD platforms
- **Security Guidelines**: Enterprise deployment security checklist

### Version Compatibility

- **MCP Protocol**: 0.4.0+
- **Python Runtime**: 3.8+
- **Node.js Runtime**: 16+
- **VS Code**: 1.75+
- **Docker**: 20.10+

---

*This catalog is automatically updated with each release. For the latest information, refer to the official documentation at [docs.connascence-analyzer.com](https://docs.connascence-analyzer.com).*