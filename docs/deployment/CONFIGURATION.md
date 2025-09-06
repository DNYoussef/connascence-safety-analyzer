# Configuration Reference - Connascence Analyzer

This guide covers all configuration options for the Connascence Analyzer, including environment variables, configuration files, and runtime options.

## Configuration Sources

Configuration is loaded in the following priority order (highest first):

1. **Command-line arguments** (`--option value`)
2. **Environment variables** (`CONNASCENCE_OPTION=value`)
3. **Project config file** (`pyproject.toml`, `.connascence.yml`)
4. **User config file** (`~/.connascence/config.yml`)
5. **Default values** (built-in defaults)

## Environment Variables

### Core Analysis Settings

```bash
# Analysis policy (default: modern_general)
export CONNASCENCE_POLICY="nasa_jpl_pot10"

# Analysis depth (default: standard)
export CONNASCENCE_ANALYSIS_DEPTH="deep"

# Output format (default: text)
export CONNASCENCE_FORMAT="json"

# Maximum analysis time per file in seconds (default: 30)
export CONNASCENCE_TIMEOUT="60"

# Enable verbose output (default: false)
export CONNASCENCE_VERBOSE="true"
```

### Quality Thresholds

```bash
# NASA compliance threshold (default: 0.95)
export CONNASCENCE_NASA_THRESHOLD="0.98"

# God object method threshold (default: 20)
export CONNASCENCE_GOD_OBJECT_METHODS="15"

# God object lines of code threshold (default: 500)
export CONNASCENCE_GOD_OBJECT_LOC="400"

# MECE similarity threshold (default: 0.8)
export CONNASCENCE_MECE_THRESHOLD="0.85"

# Overall quality threshold (default: 0.75)
export CONNASCENCE_QUALITY_THRESHOLD="0.80"
```

### File Processing

```bash
# Maximum file size in KB (default: 1000)
export CONNASCENCE_MAX_FILE_SIZE="2000"

# Maximum files per batch (default: 100)
export CONNASCENCE_MAX_FILES="50"

# File inclusion patterns (comma-separated)
export CONNASCENCE_INCLUDE="*.py,*.js,*.ts"

# File exclusion patterns (comma-separated)
export CONNASCENCE_EXCLUDE="test_*,*_test.py,node_modules"
```

### Performance Settings

```bash
# Maximum memory usage in MB (default: 1024)
export CONNASCENCE_MAX_MEMORY="2048"

# Enable parallel processing (default: true)
export CONNASCENCE_PARALLEL="false"

# Number of worker processes (default: auto)
export CONNASCENCE_WORKERS="4"

# Enable caching (default: true)
export CONNASCENCE_CACHE="false"
```

### MCP Server Configuration

```bash
# MCP server port (default: 3000)
export CONNASCENCE_MCP_PORT="8080"

# MCP server host (default: localhost)
export CONNASCENCE_MCP_HOST="0.0.0.0"

# Rate limit per minute (default: 60)
export CONNASCENCE_MCP_RATE_LIMIT="120"

# Enable MCP audit logging (default: true)
export CONNASCENCE_MCP_AUDIT="false"
```

## Configuration Files

### pyproject.toml Integration

Add configuration to your project's `pyproject.toml`:

```toml
[tool.connascence]
# Analysis policy
policy = "nasa_jpl_pot10"
analysis_depth = "deep"

# Quality thresholds
nasa_threshold = 0.95
god_object_methods = 20
god_object_loc = 500
mece_threshold = 0.8

# File patterns
include = ["*.py", "*.js", "*.ts"]
exclude = [
    "test_*", 
    "*_test.py", 
    "node_modules/*",
    "__pycache__/*",
    ".git/*"
]

# Performance settings
max_memory_mb = 1024
timeout_seconds = 30
enable_parallel = true
cache_enabled = true

# Feature flags
enable_nasa_compliance = true
enable_mece_analysis = true
enable_god_object_detection = true
enable_tool_integration = true
```

### YAML Configuration

Create `.connascence.yml` in your project root:

```yaml
# Core analysis settings
analysis:
  policy: nasa_jpl_pot10
  depth: deep
  format: json
  timeout: 30
  verbose: false

# Quality gates
thresholds:
  nasa_compliance: 0.95
  god_object_methods: 20
  god_object_loc: 500
  mece_similarity: 0.8
  overall_quality: 0.75

# File processing
files:
  include:
    - "*.py"
    - "*.js"
    - "*.ts"
    - "*.c"
    - "*.cpp"
  exclude:
    - "test_*"
    - "*_test.py"
    - "node_modules/*"
    - "__pycache__/*"
    - ".git/*"
    - "build/*"
    - "dist/*"
  max_size_kb: 1000
  max_files: 100

# Performance
performance:
  max_memory_mb: 1024
  parallel: true
  workers: auto
  cache: true

# Feature toggles
features:
  nasa_compliance: true
  mece_analysis: true
  god_object_detection: true
  tool_integration: true
  experimental: false

# Tool integrations
tools:
  ruff:
    enabled: true
    config: "pyproject.toml"
  mypy:
    enabled: true
    strict: true
  black:
    enabled: true
  radon:
    enabled: true
    complexity_threshold: 10
```

### User Configuration

Create `~/.connascence/config.yml` for user-wide defaults:

```yaml
# User preferences
user:
  default_policy: modern_general
  preferred_format: json
  enable_colors: true
  auto_fix: false

# Default thresholds (can be overridden per project)
defaults:
  nasa_threshold: 0.90
  quality_threshold: 0.70
  timeout: 30
  max_memory_mb: 512

# Editor integration
editor:
  vscode:
    auto_analyze: true
    show_inline: true
    confidence_threshold: 0.8
  
# Reporting preferences
reporting:
  include_suggestions: true
  show_examples: true
  group_by_type: true
```

## Command-Line Options

### Basic Usage

```bash
# Analyze current directory with default settings
connascence .

# Use specific policy
connascence --policy nasa_jpl_pot10 src/

# Set output format
connascence --format json --output results.json src/

# Enable verbose output
connascence --verbose --debug src/
```

### Analysis Control

```bash
# Set analysis depth
connascence --depth surface|standard|deep|comprehensive src/

# Set timeout per file
connascence --timeout 60 src/

# Control parallelism
connascence --parallel --workers 8 src/
connascence --no-parallel src/

# Memory limits
connascence --max-memory 2048 src/
```

### Quality Gates

```bash
# NASA compliance settings
connascence --nasa-threshold 0.98 src/

# God object detection
connascence --god-object-methods 15 --god-object-loc 400 src/

# MECE analysis
connascence --mece-threshold 0.85 src/

# Overall quality
connascence --quality-threshold 0.80 src/
```

### File Selection

```bash
# Include specific patterns
connascence --include "*.py,*.js" src/

# Exclude patterns
connascence --exclude "test_*,*_test.py" src/

# File size limits
connascence --max-file-size 2000 src/

# Specific files
connascence src/main.py src/utils.py
```

### Output Options

```bash
# Output formats
connascence --format text src/          # Human-readable (default)
connascence --format json src/          # JSON for tools
connascence --format sarif src/         # SARIF for security tools
connascence --format xml src/           # XML format
connascence --format csv src/           # CSV for spreadsheets

# Output destinations
connascence --output results.json src/  # File output
connascence --quiet src/                # Suppress output
connascence --verbose src/              # Detailed output
```

## Integration-Specific Configuration

### CI/CD Configuration

```yaml
# .github/workflows/connascence.yml
- name: Run Connascence Analysis
  run: |
    connascence \
      --policy nasa_jpl_pot10 \
      --format sarif \
      --output connascence.sarif \
      --nasa-threshold 0.95 \
      --fail-on critical \
      --quiet \
      src/
  env:
    CONNASCENCE_MAX_MEMORY: 2048
    CONNASCENCE_TIMEOUT: 120
```

### VS Code Settings

```json
{
  "connascence.policy": "nasa_jpl_pot10",
  "connascence.analysisDepth": "standard",
  "connascence.confidenceThreshold": 0.8,
  "connascence.autoAnalyze": true,
  "connascence.showInline": true,
  "connascence.enableColors": true,
  "connascence.thresholds": {
    "nasaCompliance": 0.95,
    "godObjectMethods": 20,
    "godObjectLoc": 500,
    "meceThreshold": 0.8
  }
}
```

### Docker Configuration

```dockerfile
# Set environment variables in Dockerfile
ENV CONNASCENCE_POLICY=nasa_jpl_pot10
ENV CONNASCENCE_FORMAT=json
ENV CONNASCENCE_MAX_MEMORY=1024
ENV CONNASCENCE_PARALLEL=true

# Or use config file
COPY .connascence.yml /app/.connascence.yml
```

## Policy Presets

### Available Policies

```bash
# Modern general (default)
connascence --policy modern_general

# NASA JPL Power of Ten rules
connascence --policy nasa_jpl_pot10

# Strict core development
connascence --policy strict_core

# Enterprise standard
connascence --policy enterprise_standard

# Custom policy file
connascence --policy-file custom_policy.yml
```

### Custom Policy Definition

Create `custom_policy.yml`:

```yaml
name: custom_policy
description: "Custom policy for our project"

thresholds:
  nasa_compliance: 0.90
  god_object_methods: 25
  god_object_loc: 600
  mece_similarity: 0.75
  overall_quality: 0.70
  
rules:
  max_parameters: 5
  max_function_lines: 100
  max_complexity: 15
  require_type_hints: true
  require_docstrings: false
  
violations:
  critical:
    - recursive_functions
    - goto_statements
    - global_variables
  high:
    - god_objects
    - high_coupling
  medium:
    - magic_literals
    - long_functions
```

## Validation and Testing

### Validate Configuration

```bash
# Check configuration syntax
connascence --check-config

# Show effective configuration
connascence --show-config

# Validate policy
connascence --validate-policy custom_policy.yml
```

### Test Configuration

```bash
# Dry run (no actual analysis)
connascence --dry-run --policy nasa_jpl_pot10 src/

# Analyze single file for testing
connascence --test-mode test.py

# Show what files would be analyzed
connascence --list-files src/
```

## Troubleshooting Configuration

### Common Issues

1. **Config file not found**
   ```bash
   # Check search paths
   connascence --show-config-paths
   
   # Use specific config file
   connascence --config-file /path/to/.connascence.yml
   ```

2. **Environment variables ignored**
   ```bash
   # Check environment
   connascence --show-env
   
   # Force environment variable loading
   connascence --reload-env
   ```

3. **Invalid policy settings**
   ```bash
   # Validate policy
   connascence --validate-policy
   
   # Use default policy
   connascence --policy default
   ```

### Debug Configuration

```bash
# Enable debug output
connascence --debug --verbose

# Show configuration sources
connascence --trace-config

# Export effective configuration
connascence --export-config config.yml
```

## Migration Guide

### Upgrading from v1.x to v2.x

Configuration changes in v2.0:
- `exclude` → `excludePatterns`
- `include` → `includePatterns`
- `debounceDelay` → `timeout`
- New section: `[tool.connascence.performance]`

Automatic migration:
```bash
# Migrate old config
connascence --migrate-config v1_config.yml > v2_config.yml
```

## Best Practices

1. **Use project-specific configuration** in `pyproject.toml`
2. **Set user defaults** in `~/.connascence/config.yml`
3. **Override for CI/CD** with environment variables
4. **Validate configuration** before deployment
5. **Document custom policies** in your project
6. **Start with lenient thresholds** and gradually tighten
7. **Use appropriate policies** for your domain (NASA for safety-critical)

## See Also

- [Installation Guide](INSTALLATION.md) - Getting started
- [Deployment Checklist](DEPLOYMENT_CHECKLIST.md) - Production deployment
- [CI/CD Setup](ci-cd-setup.md) - Continuous integration