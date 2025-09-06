# Connascence Simple CLI

A flake8-style command-line interface for the connascence analyzer.

## Quick Start

```bash
# Install
pip install connascence-analyzer

# Analyze current directory (like flake8)
connascence .

# Analyze specific files/directories  
connascence src/ tests/

# Get text output
connascence --format=text .

# Use specific policy
connascence --policy=strict-core .
```

## Features

- **Flake8-style interface**: Simple `connascence .` command
- **Auto-configuration discovery**: Finds config in pyproject.toml, setup.cfg
- **Policy auto-detection**: Detects best policy based on project structure
- **Multiple output formats**: JSON, text, SARIF
- **Full backwards compatibility**: All existing CLI options preserved

## Files Created

- `cli/__init__.py` - Package entry point
- `cli/simple_cli.py` - Main flake8-style CLI implementation  
- `cli/config_discovery.py` - Configuration file discovery
- `cli/policy_detection.py` - Automatic policy detection
- `examples/simple_usage.py` - Usage examples
- `docs/cli-usage.md` - Complete usage documentation

## Implementation Details

### Entry Points (in pyproject.toml)

```toml
[project.scripts]
# Simple flake8-style interface (primary)
connascence = "cli:main"
# Legacy interfaces (backwards compatibility)
connascence-cli = "interfaces.cli.connascence:main"
connascence-analyzer = "analyzer.core:main"
```

### Configuration Discovery Order

1. `pyproject.toml` [tool.connascence] section
2. `setup.cfg` [connascence] section
3. `.connascence.cfg` file  
4. Environment variables (CONNASCENCE_*)

### Policy Auto-Detection

Analyzes project for indicators of:
- **nasa_jpl_pot10**: Aerospace/embedded/safety-critical
- **strict-core**: Enterprise/production systems
- **lenient**: Prototypes/examples/experiments  
- **default**: Balanced projects

### Backwards Compatibility

- `--legacy-cli` flag delegates to full CLI
- All existing commands still work
- Old entry points preserved

## Usage Examples

### Basic Analysis
```bash
connascence .                    # Current directory
connascence src/                 # Specific directory
connascence file.py              # Single file
```

### Configuration  
```bash
connascence --config=setup.cfg . # Specific config
connascence --policy=strict .    # Specific policy
connascence --format=sarif .     # SARIF output
```

### Filtering
```bash
connascence --severity=high .    # High severity only
connascence --exclude="tests/*" . # Exclude patterns
connascence --show-source .      # Show source excerpts
```

### CI/CD Integration
```bash
connascence --exit-zero .        # Always exit 0
connascence --output=results.sarif --format=sarif .
```

This implementation successfully creates a flake8-style interface while preserving all existing functionality and ensuring smooth migration paths for current users.