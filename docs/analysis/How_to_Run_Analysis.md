# How to Run Analysis

## Quick Start

### Single Command Analysis
```bash
# Analyze current directory with default policy
python -m analyzer.core

# Analyze specific path with NASA compliance
python -m analyzer.core --path /path/to/code --policy nasa_jpl_pot10

# Generate SARIF output for CI/CD integration
python -m analyzer.core --path . --format sarif --output results.sarif
```

## Command Line Interface

### Basic Usage
```bash
python -m analyzer.core [OPTIONS]
```

### Available Options

| Option | Description | Default | Choices |
|--------|-------------|---------|---------|
| `--path`, `-p` | Path to analyze | current directory | Any valid path |
| `--policy` | Analysis policy | `default` | `default`, `strict-core`, `nasa_jpl_pot10`, `lenient` |
| `--format`, `-f` | Output format | `json` | `json`, `yaml`, `sarif` |
| `--output`, `-o` | Output file path | stdout | Any writable path |
| `--nasa-validation` | Enable NASA validation | false | N/A |
| `--strict-mode` | Enable strict mode | false | N/A |
| `--exclude` | Exclude patterns | none | Space-separated patterns |

### Advanced Options

| Option | Description | Default |
|--------|-------------|---------|
| `--include-nasa-rules` | Include NASA rules in SARIF | false |
| `--include-god-objects` | Include god object analysis | false |
| `--include-mece-analysis` | Include MECE duplication analysis | false |
| `--enable-tool-correlation` | Enable cross-tool correlation | false |
| `--confidence-threshold` | Correlation confidence threshold | 0.8 |

## Analysis Policies

### `default` - Balanced Analysis
- Standard connascence detection
- Moderate severity thresholds
- Good for regular development

### `strict-core` - Strict Analysis  
- Lower tolerance for violations
- Stricter thresholds
- Recommended for critical systems

### `nasa_jpl_pot10` - NASA Compliance
- NASA Power of Ten rule enforcement
- Safety-critical thresholds
- God object detection enabled
- Parameter limits enforced (≤6)

### `lenient` - Basic Analysis
- Higher tolerance for violations
- Focuses on critical issues only
- Good for legacy code assessment

## Practical Examples

### 1. Basic Project Analysis
```bash
# Quick health check
python -m analyzer.core --path ./src

# Expected output: JSON with violation summary
```

### 2. NASA Compliance Check
```bash
# Full NASA Power of Ten validation
python -m analyzer.core --path . --policy nasa_jpl_pot10 --nasa-validation

# With SARIF output for CI/CD
python -m analyzer.core --path . --policy nasa_jpl_pot10 --format sarif --output nasa_compliance.sarif
```

### 3. CI/CD Integration
```bash
# Strict mode with exit code based on critical violations
python -m analyzer.core --path . --policy strict-core --strict-mode --format sarif --output results.sarif

# Exit code 0: No critical violations or analysis passed
# Exit code 1: Critical violations found or analysis failed
```

### 4. Code Quality Assessment
```bash
# Comprehensive analysis with all features
python -m analyzer.core \
  --path ./src \
  --policy default \
  --format json \
  --output quality_report.json \
  --include-god-objects \
  --include-mece-analysis \
  --include-nasa-rules
```

### 5. Large Codebase Analysis
```bash
# Exclude common non-source directories
python -m analyzer.core \
  --path . \
  --exclude "tests/" "__pycache__/" ".git/" "node_modules/" "build/" \
  --format sarif \
  --output analysis.sarif
```

## MCP Server Interface (Experimental)

⚠️ **Note**: MCP CLI currently has import issues. Use core analyzer for reliable results.

### File Analysis (When Working)
```bash
# Analyze single file
python -m mcp.cli analyze-file src/main.py --analysis-type full --format json

# With output file
python -m mcp.cli analyze-file src/main.py --output analysis.json
```

### Workspace Analysis (When Working)
```bash
# Analyze entire workspace
python -m mcp.cli analyze-workspace . --file-patterns "*.py" --include-integrations

# Multiple file patterns
python -m mcp.cli analyze-workspace . --file-patterns "*.py" "*.js" "*.cpp"
```

## MECE Duplication Analysis

### Standalone MECE Analysis
```bash
# Run MECE analyzer directly
python -m analyzer.dup_detection.mece_analyzer --path ./src --comprehensive

# With custom similarity threshold
python -m analyzer.dup_detection.mece_analyzer --path ./src --threshold 0.8 --output duplicates.json
```

### MECE Output Format
```json
{
  "success": true,
  "mece_score": 0.75,
  "duplications": [
    {
      "id": "cluster_1", 
      "similarity_score": 0.85,
      "block_count": 3,
      "files_involved": ["file1.py", "file2.py"],
      "blocks": [
        {
          "file_path": "file1.py",
          "start_line": 42,
          "end_line": 55,
          "lines": [42, 43, 44, ...]
        }
      ]
    }
  ]
}
```

## Output Interpretation

### JSON Output Structure
```json
{
  "success": true,
  "path": "/analyzed/path", 
  "policy": "policy_used",
  "violations": [...],           // List of violations found
  "summary": {
    "total_violations": 100,
    "critical_violations": 5,
    "overall_quality_score": 0.85
  },
  "nasa_compliance": {
    "score": 0.90,
    "passing": true
  },
  "mece_analysis": {
    "score": 0.75,
    "duplications": [...]
  },
  "metrics": {
    "files_analyzed": 42,
    "analysis_time": 2.5
  }
}
```

### Exit Codes
- **0**: Analysis successful, no critical violations (or not in strict mode)
- **1**: Analysis failed or critical violations found in strict mode

## Performance Tips

### For Large Codebases
1. **Use exclusion patterns** to skip irrelevant directories
2. **Run analysis on specific modules** rather than entire codebase
3. **Use SARIF format** for better tool integration
4. **Consider parallel analysis** for independent modules

### For CI/CD Integration
1. **Use strict mode** to fail builds on critical violations  
2. **Generate SARIF output** for IDE integration
3. **Set appropriate timeouts** for large repositories
4. **Cache analysis results** when possible

## Troubleshooting

### Common Issues

1. **"ModuleNotFoundError: core.unified_imports"**
   - MCP CLI has import issues
   - Use `python -m analyzer.core` instead

2. **"Path does not exist"**
   - Verify path exists and is accessible
   - Use absolute paths for better reliability

3. **High memory usage**
   - Use exclusion patterns for large codebases
   - Analyze modules separately if needed

4. **Slow analysis** 
   - Exclude test files and build artifacts
   - Use basic policy for initial assessment

### Getting Help
```bash
# Show all available options
python -m analyzer.core --help

# Check MECE analyzer options  
python -m analyzer.dup_detection.mece_analyzer --help
```