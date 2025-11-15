# Connascence CLI Usage Guide

## Overview

The connascence analyzer now provides a simple, flake8-style command-line interface that's easy to use while preserving all advanced functionality.

## Modern Subcommands (shared with VSCode)

Use the explicit verbs below for parity with the VSCode extension and the MCP bridge:

| Command | When to use it |
|---------|----------------|
| `connascence analyze <file>` | Run AST connascence analysis for a single file or module |
| `connascence analyze-workspace <root>` | Recursively analyze an entire workspace (defaults to Python files) |
| `connascence validate-safety <file>` | Enforce a safety profile/NASA preset and emit violations |
| `connascence suggest-refactoring <file>` | Generate prioritized refactoring techniques for the current file |
| `connascence scan ...` | **Legacy alias** kept for backwards compatibility (prints a warning) |

```bash
# File analysis returned as JSON (default)
connascence analyze src/service.py --profile strict --format json

# Workspace analysis with explicit patterns and report output
connascence analyze-workspace . --file-patterns "*.py" "*.pyi" --output workspace-report.json

# NASA compliance validation (non-zero exit code if violations remain)
connascence validate-safety avionics/control.py --profile nasa-compliance

# Refactoring hints near a selected line
connascence suggest-refactoring src/utils.py --line 128 --limit 3
```

## Basic Usage (Flake8-style)

### Simple Commands

```bash
# Analyze current directory (like flake8 .)
connascence .

# Analyze specific directory
connascence src/

# Analyze single file
connascence myfile.py

# Analyze multiple paths
connascence src/ tests/ scripts/
```

### Output Formats

```bash
# JSON output (default)
connascence .

# Human-readable text output (like flake8)
connascence --format=text .

# SARIF format for CI/IDE integration
connascence --format=sarif .
```

### Example Text Output

```
src/myfile.py:15:1: CoM Magic literal detected: 3.14159
src/myfile.py:23:1: CoP Too many positional parameters: 6 (limit: 4)
src/utils.py:45:1: CoA Duplicated algorithm detected

Found 3 connascence violations (0 critical)
```

## Configuration

### Configuration File Discovery

The analyzer automatically discovers configuration in this order:

1. `pyproject.toml` [tool.connascence] section
2. `setup.cfg` [connascence] section  
3. `.connascence.cfg` file
4. Environment variables

### pyproject.toml Configuration

```toml
[tool.connascence]
# Analysis policy (default, strict-core, nasa_jpl_pot10, lenient)
policy = "default"

# Output format (json, text, sarif)
format = "text"

# Files to exclude
exclude = [
    "tests/*",
    "*/migrations/*",
    "venv/*"
]

# Minimum severity to report
severity = "medium"

# Show source code excerpts
show-source = true

# Exit with 0 even if violations found
exit-zero = false
```

### setup.cfg Configuration

```ini
[connascence]
policy = default
format = text
exclude = tests/*,venv/*,*/migrations/*
severity = medium
show-source = true
exit-zero = false
```

### Environment Variables

```bash
export CONNASCENCE_POLICY=strict-core
export CONNASCENCE_FORMAT=text
export CONNASCENCE_SEVERITY=high
export CONNASCENCE_EXIT_ZERO=true
```

## Advanced Usage

### Policy Selection

```bash
# Auto-detect policy based on project structure (default)
connascence .

# Use specific policy
connascence --policy=strict-core .
connascence --policy=nasa_jpl_pot10 .
connascence --policy=lenient .

# List available policies
connascence --list-policies
```

### Filtering Options

```bash
# Only show high and critical violations
connascence --severity=high .

# Exclude specific patterns
connascence --exclude="tests/*,venv/*" .

# Include only specific patterns
connascence --include="src/**/*.py" .

# Show source code excerpts
connascence --show-source .
```

### Output Control

```bash
# Save results to file
connascence --output=results.json .
connascence --format=sarif --output=results.sarif .

# Exit with 0 even if violations found (for CI)
connascence --exit-zero .
```

### NASA/Safety-Critical Analysis

```bash
# Enable NASA Power of Ten rules
connascence --nasa-validation .

# Strict mode for critical systems
connascence --strict-mode .
```

## Integration Examples

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: connascence
        name: connascence
        entry: connascence
        language: system
        args: ['--format=text', '--severity=high']
        types: [python]
```

### CI/CD Pipeline

```yaml
# GitHub Actions
- name: Run Connascence Analysis
  run: |
    pip install connascence-analyzer
    connascence --format=sarif --output=connascence.sarif .
    
- name: Upload SARIF results
  uses: github/codeql-action/upload-sarif@v2
  with:
    sarif_file: connascence.sarif
```

### VS Code Integration

Add to your VS Code settings:

```json
{
    "python.linting.enabled": true,
    "python.linting.connascenceEnabled": true,
    "python.linting.connascencePath": "connascence",
    "python.linting.connascenceArgs": ["--format=text"]
}
```

## Policy Auto-Detection

The analyzer automatically detects the best policy based on:

- **nasa_jpl_pot10**: Aerospace, embedded, safety-critical keywords
- **strict-core**: Enterprise, production, complex architecture indicators  
- **lenient**: Prototypes, examples, experimental code
- **default**: Balanced projects with reasonable test coverage

Auto-detection considers:
- File and directory names
- Dependencies in requirements.txt/pyproject.toml
- Configuration files (Docker, CI/CD, etc.)
- Code content and patterns

## Backwards Compatibility

### Legacy CLI Access

```bash
# Use full legacy interface
connascence --legacy-cli [old-style-args]

# Old analyzer interface still works
connascence-analyzer --path . --policy nasa_jpl_pot10 --format json

# Old CLI interface still works  
connascence-cli scan --path .
```

### Migration from Old CLI

| Old Command | New Command |
|-------------|-------------|
| `python -m analyzer.core --path .` | `connascence .` |
| `python -m analyzer.core --path . --format json` | `connascence . --format=json` |
| `python -m analyzer.core --policy strict-core` | `connascence --policy=strict-core .` |
| `python -m analyzer.core --output results.json` | `connascence --output=results.json .` |

## Comparison with Flake8

| Feature | Flake8 | Connascence |
|---------|--------|-------------|
| Basic usage | `flake8 .` | `connascence .` |
| Config files | `setup.cfg`, `tox.ini` | `pyproject.toml`, `setup.cfg` |
| Output format | Text | Text, JSON, SARIF |
| Exit codes | 0/1 | 0/1 with `--exit-zero` |
| Exclusion | `--exclude` | `--exclude` |
| Severity | Error codes | `--severity` levels |
| Show source | `--show-source` | `--show-source` |

The goal is to make connascence as easy to adopt as flake8, while providing more sophisticated coupling analysis.

## Getting Help

```bash
connascence --help              # Show all options
connascence --list-policies     # List available policies  
connascence --version           # Show version information
```