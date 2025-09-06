# CLI Reference

**Complete command-line interface reference for Connascence Analyzer**

## Overview

The Connascence Analyzer provides two primary CLI interfaces:
- **`python -m analyzer.core`** - Main analyzer with comprehensive features
- **`python -m mcp.cli`** - Enhanced MCP server interface for Claude Code integration

Both interfaces support multiple output formats (JSON, SARIF, YAML) and various analysis policies.

---

## Main CLI: `python -m analyzer.core`

### Basic Usage

```bash
# Analyze current directory with default policy
python -m analyzer.core

# Analyze specific path
python -m analyzer.core --path /path/to/project

# Use specific policy
python -m analyzer.core --path . --policy nasa_jpl_pot10

# Output to file
python -m analyzer.core --path . --format json --output results.json
```

### Arguments

#### Required Arguments
None - all arguments have defaults

#### Optional Arguments

##### `--path, -p PATH`
**Path to analyze** (default: current directory)
```bash
python -m analyzer.core --path src/
python -m analyzer.core -p /absolute/path/to/code
```

##### `--policy POLICY`
**Analysis policy to apply**
- `default` - Balanced analysis for general use
- `strict-core` - Strict analysis for critical systems
- `nasa_jpl_pot10` - NASA JPL Power of Ten rules compliance
- `lenient` - Relaxed analysis for legacy codebases

```bash
python -m analyzer.core --policy nasa_jpl_pot10
python -m analyzer.core --policy strict-core
```

##### `--format, -f FORMAT`
**Output format**
- `json` - Structured JSON output (default)
- `yaml` - Human-readable YAML output
- `sarif` - SARIF format for GitHub Code Scanning

```bash
python -m analyzer.core --format sarif
python -m analyzer.core -f json
```

##### `--output, -o FILE`
**Output file path** (default: stdout)
```bash
python -m analyzer.core --output report.json
python -m analyzer.core -o results.sarif
```

##### `--nasa-validation`
**Enable NASA Power of Ten validation**
```bash
python -m analyzer.core --nasa-validation
```

##### `--strict-mode`
**Enable strict analysis mode** (fails on critical violations)
```bash
python -m analyzer.core --strict-mode
```

##### `--exclude PATTERN [PATTERN ...]`
**Exclude file patterns from analysis** (multiple patterns allowed)
```bash
python -m analyzer.core --exclude "*/tests/*" "*/venv/*"
python -m analyzer.core --exclude "**/test_*.py" "build/"
```

#### Advanced Options

##### `--include-nasa-rules`
**Include NASA-specific rules in SARIF output**
```bash
python -m analyzer.core --format sarif --include-nasa-rules
```

##### `--include-god-objects`
**Include god object analysis in output**
```bash
python -m analyzer.core --include-god-objects
```

##### `--include-mece-analysis`
**Include MECE duplication analysis**
```bash
python -m analyzer.core --include-mece-analysis
```

##### `--enable-tool-correlation`
**Enable cross-tool analysis correlation**
```bash
python -m analyzer.core --enable-tool-correlation
```

##### `--confidence-threshold FLOAT`
**Confidence threshold for correlations** (0.0-1.0, default: 0.8)
```bash
python -m analyzer.core --confidence-threshold 0.9
```

### Complete Example

```bash
python -m analyzer.core \
  --path ./src \
  --policy nasa_jpl_pot10 \
  --format sarif \
  --output nasa-compliance.sarif \
  --nasa-validation \
  --strict-mode \
  --include-nasa-rules \
  --include-god-objects \
  --exclude "*/tests/*" "**/venv/**" \
  --confidence-threshold 0.85
```

---

## MCP CLI: `python -m mcp.cli`

### Basic Usage

```bash
# Analyze a single file
python -m mcp.cli analyze-file src/main.py

# Analyze entire workspace
python -m mcp.cli analyze-workspace .

# Check server health
python -m mcp.cli health-check

# Get server information
python -m mcp.cli info
```

### Global Options

##### `--verbose, -v`
**Enable verbose logging**
```bash
python -m mcp.cli --verbose analyze-file main.py
```

##### `--config, -c CONFIG_FILE`
**Path to configuration file**
```bash
python -m mcp.cli --config config.json analyze-workspace .
```

### Subcommands

#### `analyze-file <file_path>`
**Analyze a single file with enhanced MCP capabilities**

```bash
python -m mcp.cli analyze-file src/main.py
```

**Arguments:**
- `file_path` - Path to file to analyze (required)

**Options:**
- `--analysis-type TYPE` - Analysis type: `full`, `connascence`, `mece`, `nasa` (default: `full`)
- `--include-integrations` - Include external tool integrations (default: True)
- `--format FORMAT` - Output format: `json`, `sarif` (default: `json`)
- `--output, -o FILE` - Output file path

**Examples:**
```bash
# Full analysis with SARIF output
python -m mcp.cli analyze-file app.py --analysis-type full --format sarif

# NASA compliance check only
python -m mcp.cli analyze-file critical.py --analysis-type nasa --output nasa-report.json

# MECE duplication analysis
python -m mcp.cli analyze-file utils.py --analysis-type mece
```

#### `analyze-workspace <workspace_path>`
**Analyze entire workspace with parallel processing**

```bash
python -m mcp.cli analyze-workspace .
```

**Arguments:**
- `workspace_path` - Path to workspace to analyze (required)

**Options:**
- `--analysis-type TYPE` - Analysis type: `full`, `connascence`, `mece`, `nasa` (default: `full`)
- `--file-patterns PATTERN [PATTERN ...]` - File patterns to include
- `--include-integrations` - Include external tool integrations (default: True)
- `--output, -o FILE` - Output file path

**Examples:**
```bash
# Analyze Python files only
python -m mcp.cli analyze-workspace . --file-patterns "*.py"

# Analyze multiple file types
python -m mcp.cli analyze-workspace ./src --file-patterns "*.py" "*.js" "*.ts"

# Full workspace analysis with output
python -m mcp.cli analyze-workspace . --output workspace-report.json
```

#### `health-check`
**Check server health and component status**

```bash
python -m mcp.cli health-check
```

**No additional arguments**

Returns health status of all analyzer components.

#### `info`
**Get server information and capabilities**

```bash
python -m mcp.cli info
```

**No additional arguments**

Returns version, capabilities, and configuration information.

---

## Output Formats

### JSON Format

#### Standard JSON Output
```json
{
  "success": true,
  "path": "/analyzed/path",
  "policy": "nasa_jpl_pot10",
  "violations": [
    {
      "id": "unique_id",
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
  "metrics": {
    "files_analyzed": 156,
    "analysis_time": 2.45,
    "timestamp": 1640995800.0
  }
}
```

#### MCP Enhanced JSON Output
```json
{
  "tool": "enhanced-mcp-server",
  "version": "2.0.0",
  "analysis_result": {
    "file_path": "src/main.py",
    "analysis_type": "full",
    "violations": [...],
    "integrations": {
      "ruff_correlation": 0.85,
      "mypy_correlation": 0.72,
      "external_findings": [...]
    },
    "recommendations": [
      {
        "priority": "high",
        "action": "Extract magic constant MIN_AGE = 18",
        "confidence": 0.95
      }
    ]
  }
}
```

### SARIF Format

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
          "informationUri": "https://connascence.io",
          "rules": [
            {
              "id": "CON_CoM",
              "name": "ConnascenceOfMeaning",
              "shortDescription": {
                "text": "Connascence of Meaning (Magic Literals)"
              },
              "fullDescription": {
                "text": "Magic literals create connascence of meaning where multiple code locations must agree on the interpretation of a literal value."
              },
              "helpUri": "https://connascence.io/meaning.html",
              "defaultConfiguration": {
                "level": "warning"
              }
            }
          ]
        }
      },
      "results": [
        {
          "ruleId": "CON_CoM",
          "level": "warning", 
          "message": {
            "text": "Magic literal '18' detected. Consider extracting to named constant."
          },
          "locations": [
            {
              "physicalLocation": {
                "artifactLocation": {
                  "uri": "src/user_validator.py"
                },
                "region": {
                  "startLine": 15,
                  "startColumn": 20,
                  "endColumn": 22
                }
              }
            }
          ],
          "fixes": [
            {
              "description": {
                "text": "Extract to named constant"
              },
              "artifactChanges": [
                {
                  "artifactLocation": {
                    "uri": "src/user_validator.py"
                  },
                  "replacements": [
                    {
                      "deletedRegion": {
                        "startLine": 15,
                        "startColumn": 20,
                        "endColumn": 22
                      },
                      "insertedContent": {
                        "text": "MIN_AGE"
                      }
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

---

## Exit Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | Success | Analysis completed successfully with no critical violations |
| 1 | Violations Found | Analysis completed but found violations (or critical violations in strict mode) |
| 2 | Configuration Error | Invalid configuration or command-line arguments |
| 3 | Runtime Error | Execution error (file not found, permission denied, etc.) |
| 4 | Policy Validation Failed | Policy-specific validation failed |
| 5 | NASA Compliance Failed | NASA Power of Ten compliance check failed |

### Using Exit Codes in Scripts

```bash
#!/bin/bash

# Run analysis and handle different exit codes
python -m analyzer.core --path . --policy nasa_jpl_pot10 --strict-mode

case $? in
  0)
    echo "✅ Analysis passed - no critical violations"
    ;;
  1)
    echo "⚠️  Analysis found violations - check output"
    exit 1
    ;;
  2)
    echo "❌ Configuration error"
    exit 1
    ;;
  *)
    echo "❌ Analysis failed"
    exit 1
    ;;
esac
```

---

## Configuration Files

### `.connascence.json`
**Project-level configuration file**

```json
{
  "safetyProfile": "nasa_jpl_pot10",
  "threshold": 0.8,
  "strictMode": false,
  "analysisDepth": "comprehensive",
  "excludePatterns": [
    "**/tests/**",
    "**/node_modules/**",
    "**/__pycache__/**",
    "**/venv/**"
  ],
  "includePatterns": [
    "**/*.py",
    "**/*.js",
    "**/*.ts"
  ],
  "performanceAnalysis": {
    "enableProfiling": true,
    "maxAnalysisTime": 30000,
    "enableCaching": true
  },
  "customRules": [
    {
      "name": "no-legacy-imports",
      "pattern": "from legacy_module import",
      "severity": "warning",
      "message": "Legacy module usage detected"
    }
  ]
}
```

### MCP Server Configuration
**`mcp_config.json` for enhanced server**

```json
{
  "server": {
    "name": "connascence-analyzer",
    "version": "2.0.0",
    "timeout": 30000
  },
  "analysis": {
    "enableAdvancedFeatures": true,
    "enableToolIntegration": true,
    "enableNASACompliance": true,
    "enableMECEAnalysis": true
  },
  "integrations": {
    "ruff": {
      "enabled": true,
      "confidence_threshold": 0.8
    },
    "mypy": {
      "enabled": true,
      "confidence_threshold": 0.7
    }
  }
}
```

---

## Integration Examples

### CI/CD Pipeline (GitHub Actions)

```yaml
name: Code Quality Analysis
on: [push, pull_request]

jobs:
  connascence-analysis:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run Connascence Analysis
      run: |
        python -m analyzer.core \
          --path . \
          --policy nasa_jpl_pot10 \
          --format sarif \
          --output connascence-results.sarif \
          --include-nasa-rules \
          --strict-mode
    
    - name: Upload SARIF to GitHub
      uses: github/codeql-action/upload-sarif@v2
      if: always()
      with:
        sarif_file: connascence-results.sarif
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: connascence-analysis
        name: Connascence Analysis
        entry: python -m analyzer.core
        args: ['--path', '.', '--policy', 'nasa_jpl_pot10', '--strict-mode']
        language: python
        types: [python]
        pass_filenames: false
```

### Docker Integration

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Set default command for analysis
ENTRYPOINT ["python", "-m", "analyzer.core"]
CMD ["--help"]
```

```bash
# Build and run in Docker
docker build -t connascence-analyzer .

# Analyze current directory
docker run --rm -v $(pwd):/app connascence-analyzer \
  --path /app \
  --format json \
  --policy nasa_jpl_pot10
```

### Makefile Integration

```makefile
.PHONY: analyze analyze-strict analyze-sarif

# Basic analysis
analyze:
	python -m analyzer.core --path . --format json

# Strict analysis (fails on critical violations)
analyze-strict:
	python -m analyzer.core --path . --policy nasa_jpl_pot10 --strict-mode

# Generate SARIF report
analyze-sarif:
	python -m analyzer.core \
		--path . \
		--format sarif \
		--output reports/connascence-report.sarif \
		--include-nasa-rules \
		--include-god-objects

# MCP analysis with integrations
analyze-mcp:
	python -m mcp.cli analyze-workspace . \
		--analysis-type full \
		--include-integrations \
		--output reports/mcp-analysis.json
```

---

## Troubleshooting

### Common Issues

#### 1. `ModuleNotFoundError: No module named 'analyzer'`
**Solution:** Ensure you're in the correct directory and dependencies are installed
```bash
cd /path/to/connascence-analyzer
pip install -r requirements.txt
```

#### 2. `Permission denied` errors
**Solution:** Check file permissions or use sudo if needed
```bash
chmod +x analyzer/core.py
# or
sudo python -m analyzer.core --path .
```

#### 3. `Analysis timeout` errors
**Solution:** Increase timeout or exclude large directories
```bash
python -m analyzer.core --path . --exclude "**/node_modules/**" "**/.git/**"
```

#### 4. Empty or invalid output
**Solution:** Check that target files exist and are readable
```bash
# Verify files exist
python -m analyzer.core --path . --verbose

# Check specific file
python -m analyzer.core --path specific_file.py --format json
```

### Debug Mode

```bash
# Enable verbose output
python -m analyzer.core --path . --verbose

# For MCP CLI
python -m mcp.cli --verbose analyze-file main.py
```

### Getting Help

```bash
# Main CLI help
python -m analyzer.core --help

# MCP CLI help  
python -m mcp.cli --help

# Subcommand help
python -m mcp.cli analyze-file --help
python -m mcp.cli analyze-workspace --help
```

This CLI reference provides complete documentation for all command-line interfaces. All commands and options are based on the actual implementation and tested for accuracy.