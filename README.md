# Connascence Detection System

A comprehensive architectural quality assessment tool that detects various forms of connascence in Python codebases to reduce coupling and improve maintainability.

## Overview

This system implements Meilir Page-Jones' connascence theory to identify coupling issues in code through:

### Detection Capabilities

**Static Forms of Connascence:**
- **Name (CoN)**: Dependencies on specific names/identifiers
- **Type (CoT)**: Dependencies on data types  
- **Meaning (CoM)**: Dependencies on magic numbers/strings
- **Position (CoP)**: Dependencies on argument order
- **Algorithm (CoA)**: Dependencies on specific algorithms

**Dynamic Forms of Connascence:**
- **Execution (CoE)**: Dependencies on execution order
- **Timing (CoTi)**: Dependencies on timing/delays
- **Value (CoV)**: Dependencies on shared values
- **Identity (CoI)**: Dependencies on object identity

### Advanced Features

- **God Object Detection** (classes >20 methods or >500 lines)
- **Magic Literal Analysis** with 38% reduction targeting
- **Circular Dependency Detection**
- **Complexity Metrics** (Cyclomatic complexity, Maintainability Index)
- **AST-based Deep Analysis** with context awareness
- **Configurable Thresholds** and exclusion patterns
- **Multiple Output Formats** (JSON, HTML, text)
- **CI/CD Integration** with pre-commit hooks

## Quick Start

### 1. Basic Analysis

```bash
# Analyze current directory
python src/check_connascence.py .

# Analyze specific files with JSON output
python src/check_connascence.py src/ --format json --output report.json

# Show only high severity violations
python src/check_connascence.py . --severity high
```

### 2. Magic Literal Detection

```bash
# Detect magic literals in Python files
python scripts/magic-literal-detector.py src/

# With custom threshold (default 20%)
python scripts/magic-literal-detector.py . --threshold 15.0

# JSON output for CI integration
python scripts/magic-literal-detector.py . --json
```

### 3. Architectural Analysis

```bash
# Full architectural analysis
python src/architectural_analysis.py --project-root . --output-format html

# Generate dependency graphs and metrics
python src/architectural_analysis.py --project-root . --output-format both
```

## Configuration

### Ruff Integration

Use the provided Ruff configurations for automatic linting:

```toml
# Use config/ruff_magic_literal_rules.toml
[tool.ruff]
select = [
    "PLR2004",  # Magic value used in comparison  
    "PLR0913",  # Too many arguments (Position)
    "C90",      # Cyclomatic complexity (Algorithm)
    "N",        # Naming conventions (Name)
    "ARG",      # Unused arguments (Position)
]
```

### Thresholds

Default thresholds can be customized:

```python
POSITION_THRESHOLD = 3        # Max positional parameters
GOD_CLASS_METHODS = 20        # Max methods per class  
GOD_CLASS_LOC = 500          # Max lines per class
COMPLEXITY_THRESHOLD = 10     # Max cyclomatic complexity
MAGIC_LITERAL_EXCEPTIONS = [0, 1, -1, 2, 10, 100, 1000]
GLOBAL_VAR_LIMIT = 5         # Max global variables
```

## Integration

### Pre-commit Hook

```yaml
repos:
  - repo: local
    hooks:
      - id: connascence-check
        name: Connascence Violation Check
        entry: python src/check_connascence.py
        language: system
        files: '\.py$'
        args: ['--severity', 'high']
```

### GitHub Actions

```yaml
- name: Connascence Analysis
  run: |
    python src/check_connascence.py . --format json --output connascence-report.json
    python scripts/magic-literal-detector.py . --json > magic-literals.json
```

## File Structure

```
connascence/
 src/                    # Core detection engines
    check_connascence.py          # Main AST-based detector (546 lines)
    connascence_analyzer.py       # Simplified analyzer (252 lines)
    architectural_analysis.py     # Full architectural analysis (606 lines)
    magic_literal_analyzer.py     # Magic literal analyzer (423 lines)
 config/                 # Linting configurations
    ruff_magic_literal_rules.toml # Ruff config for magic literals
    enhanced-ruff-config.toml     # Comprehensive Ruff config
 scripts/               # CI/CD integration scripts
    magic-literal-detector.py    # Pre-commit magic literal detector
 tests/                 # Comprehensive test suite
    test_connascence_detection.py     # Core detection tests
    test_connascence_compliance.py    # Meta-testing for test quality
    test_connascence_refactoring.py   # Refactoring validation
 docs/                  # Documentation and reports
 examples/              # Usage examples and templates
 README.md              # This file
```

## Usage Examples

### 1. Finding Position Connascence

```python
# BAD: Too many positional arguments
def calculate_price(item_type, user_level, season, promo_code, quantity):
    pass

# GOOD: Use keyword arguments or data classes
@dataclass
class PriceRequest:
    item_type: str
    user_level: str
    season: str
    promo_code: str = None
    quantity: int = 1

def calculate_price(request: PriceRequest):
    pass
```

### 2. Eliminating Magic Numbers

```python
# BAD: Magic numbers
if timeout > 30:
    raise TimeoutError()

# GOOD: Named constants
TIMEOUT_SECONDS = 30
if timeout > TIMEOUT_SECONDS:
    raise TimeoutError()
```

### 3. Breaking Algorithm Connascence

```python
# BAD: Duplicated validation logic
def validate_email(email):
    return "@" in email and "." in email

def is_valid_email(email):
    return "@" in email and "." in email

# GOOD: Shared validation function
def is_valid_email_format(email: str) -> bool:
    return "@" in email and "." in email

def validate_email(email):
    return is_valid_email_format(email)

def check_email(email):
    return is_valid_email_format(email)
```

## Severity Levels

- **Critical**: Security-related magic literals, syntax errors, god objects
- **High**: Magic literals in conditionals, excessive positional parameters, identity connascence
- **Medium**: Algorithm duplication, timing dependencies, general magic literals
- **Low**: Type-related issues, minor naming violations

## Output Formats

### Text Report
```
===============================================================================
CONNASCENCE ANALYSIS REPORT
===============================================================================

Total violations: 42
Files analyzed: 15

Severity breakdown:
  Critical:   2
  High:      12
  Medium:    18
  Low:       10

DETAILED VIOLATIONS
===============================================================================

CRITICAL SEVERITY (2 violations)
----------------------------------------

god_object: Class 'UserManager' is a God Object: 25 methods, ~650 lines
File: src/user_manager.py:15:0
Recommendation: Split into smaller, focused classes following Single Responsibility Principle
```

### JSON Report
```json
{
  "timestamp": "2024-01-15T10:30:00",
  "summary": {
    "total_violations": 42,
    "files_analyzed": 15,
    "severity_breakdown": {
      "critical": 2,
      "high": 12,
      "medium": 18,
      "low": 10
    }
  },
  "violations": [
    {
      "type": "god_object",
      "severity": "critical",
      "file_path": "src/user_manager.py",
      "line_number": 15,
      "description": "Class 'UserManager' is a God Object: 25 methods, ~650 lines",
      "recommendation": "Split into smaller, focused classes"
    }
  ]
}
```

## Performance

- Analyzes 1000+ files in under 30 seconds
- Memory efficient AST traversal
- Configurable exclusion patterns for performance
- Parallel analysis support for large codebases

## Contributing

1. Run the test suite: `python -m pytest tests/`
2. Check your changes: `python src/check_connascence.py .`
3. Ensure no regressions in connascence compliance

## License

Extracted from AIVillage project - maintains original architectural quality standards.

## References

- Meilir Page-Jones: "What Every Programmer Should Know About Object-Oriented Design"
- Martin Fowler: "Reducing Coupling" 
- Clean Architecture principles by Robert C. Martin