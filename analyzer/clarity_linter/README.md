# Clarity Linter Orchestrator

Complete orchestration system for coordinating 5 specialized clarity detectors with unified API and SARIF 2.1.0 export.

## Architecture Overview

```
clarity_linter/
├── __init__.py           # ClarityLinter orchestrator class
├── base.py               # BaseClarityDetector abstract class
├── models.py             # ClarityViolation and ClaritySummary dataclasses
├── config_loader.py      # YAML configuration loader
├── sarif_exporter.py     # SARIF 2.1.0 exporter
└── README.md            # This file
```

## Components

### 1. ClarityLinter (Orchestrator)

Main coordinator class that:
- Loads configuration from `clarity_linter.yaml`
- Registers and initializes all 5 detectors
- Provides unified `analyze_project()` and `analyze_file()` methods
- Generates SARIF 2.1.0 output for GitHub Code Scanning
- Manages exclusions and file filtering

### 2. BaseClarityDetector (Abstract Base)

Abstract base class for all detectors providing:
- Common interface via `detect()` method
- Configuration loading and validation
- Severity mapping and rule enablement
- Code snippet extraction utilities
- Violation creation helpers

### 3. ClarityViolation (Data Model)

Dataclass representing violations with:
- Rule ID, name, and severity
- File location (path, line, column)
- Description and recommendation
- Optional code snippet and context
- Conversion methods for SARIF and ConnascenceViolation formats

### 4. ClarityConfigLoader

YAML configuration loader with:
- Automatic config file discovery
- Validation of required sections
- Default fallback configuration
- Rule-specific config extraction

### 5. SARIFExporter

SARIF 2.1.0 format exporter with:
- GitHub Code Scanning compatibility
- Full tool metadata
- Rule definitions with NASA/Connascence mappings
- Result locations and fix suggestions

## Usage Examples

### Basic Project Analysis

```python
from pathlib import Path
from analyzer.clarity_linter import ClarityLinter

# Initialize with default config
linter = ClarityLinter()

# Analyze entire project
project_path = Path("/path/to/project")
violations = linter.analyze_project(project_path)

# Print violations
for violation in violations:
    print(violation)

# Export to SARIF
sarif_doc = linter.export_sarif(violations, Path("clarity_results.sarif"))

# Get summary
summary = linter.get_summary()
print(f"Analyzed {summary['total_files_analyzed']} files")
print(f"Found {summary['total_violations_found']} violations")
```

### Single File Analysis

```python
from pathlib import Path
from analyzer.clarity_linter import ClarityLinter

linter = ClarityLinter()

# Analyze single file
file_path = Path("src/module.py")
violations = linter.analyze_file(file_path)

# Group by severity
critical = [v for v in violations if v.severity == 'critical']
high = [v for v in violations if v.severity == 'high']
medium = [v for v in violations if v.severity == 'medium']

print(f"Critical: {len(critical)}, High: {len(high)}, Medium: {len(medium)}")
```

### Custom Configuration

```python
from pathlib import Path
from analyzer.clarity_linter import ClarityLinter

# Use custom config file
config_path = Path("config/custom_clarity.yaml")
linter = ClarityLinter(config_path=config_path)

violations = linter.analyze_project(Path("src"))
```

### Integration with Quality Gates

```python
from pathlib import Path
from analyzer.clarity_linter import ClarityLinter
from analyzer.quality_gates.unified_quality_gate import UnifiedQualityGate

# Run clarity analysis
linter = ClarityLinter()
clarity_violations = linter.analyze_project(Path("src"))

# Convert to connascence violations for quality gate
connascence_violations = [
    v.to_connascence_violation() for v in clarity_violations
]

# Add to quality gate
quality_gate = UnifiedQualityGate()
quality_gate.add_violations("clarity_linter", connascence_violations)

# Check if quality gate passes
result = quality_gate.evaluate()
print(f"Quality gate: {'PASS' if result.passed else 'FAIL'}")
```

## Configuration

The orchestrator loads configuration from `clarity_linter.yaml`:

```yaml
metadata:
  name: "Clarity Linter"
  version: "1.0.0"

rules:
  CLARITY_THIN_HELPER:
    enabled: true
    severity: medium
    threshold: 3

  CLARITY_USELESS_INDIRECTION:
    enabled: true
    severity: medium
    threshold: 1

  CLARITY_CALL_CHAIN:
    enabled: true
    severity: high
    threshold: 3

  CLARITY_POOR_NAMING:
    enabled: true
    severity: medium
    min_length: 3

  CLARITY_COMMENT_ISSUES:
    enabled: true
    severity: low

exclusions:
  directories:
    - node_modules
    - venv
    - __pycache__
  files:
    - "*.min.js"
    - "*_pb2.py"
```

## Registered Detectors

The orchestrator automatically registers these 5 detectors:

1. **ThinHelperDetector** (`CLARITY_THIN_HELPER`)
   - Detects thin helper functions (1-3 lines wrapping other calls)
   - Identifies useless abstraction layers

2. **UselessIndirectionDetector** (`CLARITY_USELESS_INDIRECTION`)
   - Detects unnecessary indirection patterns
   - Finds wrapper functions that add no value

3. **CallChainDepthDetector** (`CLARITY_CALL_CHAIN`)
   - Detects excessive call chain depth (>3 levels)
   - Identifies hard-to-trace execution paths

4. **PoorNamingDetector** (`CLARITY_POOR_NAMING`)
   - Detects unclear variable/function names
   - Checks for abbreviations, single letters, Hungarian notation

5. **CommentIssuesDetector** (`CLARITY_COMMENT_ISSUES`)
   - Detects commented-out code
   - Finds TODO/FIXME without context
   - Identifies low-quality comments

## SARIF Export

Export violations in SARIF 2.1.0 format for GitHub Code Scanning:

```python
from pathlib import Path
from analyzer.clarity_linter import ClarityLinter

linter = ClarityLinter()
violations = linter.analyze_project(Path("src"))

# Export to SARIF file
sarif_doc = linter.export_sarif(violations, Path("clarity_results.sarif"))

# SARIF document structure:
# {
#   "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
#   "version": "2.1.0",
#   "runs": [{
#     "tool": {
#       "driver": {
#         "name": "Clarity Linter",
#         "version": "1.0.0",
#         "rules": [...]
#       }
#     },
#     "results": [...]
#   }]
# }
```

## NASA Compliance

All components follow NASA coding standards:

- **NASA Rule 4**: All functions under 60 lines
- **NASA Rule 5**: Input validation with assertions
- **NASA Rule 6**: Clear variable scoping
- Clear, focused, testable functions

## Error Handling

The orchestrator handles errors gracefully:

- Syntax errors in analyzed files (skipped with warning)
- Missing configuration files (uses defaults)
- Invalid YAML (falls back to defaults)
- Missing detectors (continues with available detectors)

## Performance

- **File caching**: Reuses parsed AST trees when available
- **Parallel detection**: All detectors run on same AST pass
- **Incremental analysis**: Can analyze single files
- **Lazy loading**: Detectors loaded only if enabled

## Testing

Unit tests cover:

- Orchestrator initialization
- Configuration loading
- Detector registration
- Violation aggregation
- SARIF export
- Error handling

## Integration Points

### With Connascence Analyzer

```python
# Convert clarity violations to connascence format
connascence_violations = [
    v.to_connascence_violation() for v in clarity_violations
]
```

### With Quality Gates

```python
# Add to unified quality gate
quality_gate.add_violations("clarity_linter", clarity_violations)
```

### With CI/CD

```bash
# Run in CI pipeline
python -m analyzer.clarity_linter \
  --project-path src/ \
  --output clarity_results.sarif \
  --fail-on critical,high
```

## Future Enhancements

1. **Additional detectors**: More clarity rules
2. **Auto-fix suggestions**: Automated refactoring
3. **IDE integration**: VS Code extension
4. **GitHub Actions**: Pre-built workflow
5. **Custom rules**: User-defined detectors

## License

MIT License - Same as parent connascence analyzer project
