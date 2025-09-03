# Installation Guide

## System Requirements

- Python 3.8 or higher
- Required dependencies: `ast`, `networkx`, `radon`, `pytest` (for testing)

## Installation Steps

### 1. Install Dependencies

```bash
# Core dependencies for connascence detection
pip install networkx radon

# Optional: For testing
pip install pytest

# Optional: For enhanced linting integration
pip install ruff
```

### 2. Verify Installation

```bash
# Test the main detector
python src/check_connascence.py --help

# Test magic literal detector  
python scripts/magic-literal-detector.py --help

# Run example analysis
python examples/basic_usage.py
```

### 3. Integration Setup

#### Pre-commit Integration

1. Install pre-commit: `pip install pre-commit`
2. Copy `examples/pre_commit_config.yaml` to your project root as `.pre-commit-config.yaml`
3. Install hooks: `pre-commit install`

#### CI/CD Integration

1. Copy `examples/ci_integration.yaml` to `.github/workflows/connascence-check.yml`
2. Customize paths and thresholds as needed

#### Ruff Integration

Add to your `pyproject.toml`:

```toml
[tool.ruff]
select = [
    "PLR2004",  # Magic value detection
    "PLR0913",  # Too many arguments  
    "C90",      # Complexity
    "N",        # Naming
]

[tool.ruff.pylint]
max-args = 3
```

## Configuration

### Threshold Customization

Edit the constants in `src/check_connascence.py`:

```python
POSITION_THRESHOLD = 3        # Max positional parameters
GOD_CLASS_METHODS = 20        # Max methods per class  
GOD_CLASS_LOC = 500          # Max lines per class
COMPLEXITY_THRESHOLD = 10     # Max cyclomatic complexity
MAGIC_LITERAL_EXCEPTIONS = [0, 1, -1, 2, 10, 100, 1000]
```

### Exclusion Patterns

Modify the exclusion patterns in analyzers:

```python
exclusions = [
    "test_*", "tests/", "*_test.py", "conftest.py", 
    "deprecated/", "archive/", "experimental/",
    "__pycache__/", ".git/", "build/", "dist/"
]
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure Python path includes the `src/` directory
2. **Permission Errors**: Run with appropriate permissions for file access
3. **Memory Issues**: Use exclusion patterns for large codebases
4. **Windows Path Issues**: Use forward slashes in paths when possible

### Performance Optimization

For large codebases:
- Use specific file patterns instead of analyzing entire directories
- Increase exclusion patterns
- Run analysis on specific modules/packages
- Use the `--severity` flag to filter results

### Getting Help

1. Check the examples in `examples/` directory
2. Review test cases in `tests/` directory  
3. Read the comprehensive documentation in `README.md`