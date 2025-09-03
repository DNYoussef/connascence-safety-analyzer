# Verification Scripts - Connascence Safety Analyzer

This directory contains comprehensive verification scripts that validate README numbers match demo artifacts using memory coordination and sequential thinking.

## Files Overview

### Core Scripts

- **`verify_counts.py`** - Main Python verification script with memory coordination
- **`verify_counts.sh`** - Shell wrapper script with CI/CD integration  
- **`README.md`** - This documentation

### Features

- **Memory Coordination**: Tracks validation results for CI coordination
- **Sequential Thinking**: Systematic 6-step validation process
- **CI/CD Integration**: Proper exit codes and error handling
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Comprehensive Reporting**: Detailed JSON reports with pass/fail status

## Usage

### Python Script (Primary)

```bash
# Basic validation
python scripts/verify_counts.py

# Verbose output  
python scripts/verify_counts.py --verbose

# Generate report only (for testing)
python scripts/verify_counts.py --report-only

# Custom base path
python scripts/verify_counts.py --base-path /path/to/project
```

### Shell Script (CI/CD Wrapper)

```bash
# Basic validation
./scripts/verify_counts.sh

# Verbose output
./scripts/verify_counts.sh --verbose

# Report only mode
./scripts/verify_counts.sh --report-only

# Show help
./scripts/verify_counts.sh --help
```

## Validation Process

The scripts implement **sequential thinking** with these 6 steps:

1. **Parse README.md** for violation counts
2. **Parse DEMO_ARTIFACTS/index.json** for expected counts
3. **Validate individual artifact files** exist and parse correctly
4. **Cross-reference all counts** for consistency
5. **Generate comprehensive validation report**
6. **Store results in memory** for CI coordination

## Expected Validation Results

### Key Requirements Validated

- **README total**: 5,743 violations
- **Individual counts**: 
  - Celery: 4,630 violations
  - curl: 1,061 violations  
  - Express: 52 violations
- **File existence**: All referenced artifacts present
- **JSON validity**: All artifact files parse correctly

### Memory Coordination

The system uses memory coordination to track:
- Validation session data
- Test results and status
- Sequential step progress
- Cross-reference consistency
- Final reporting metrics

## Exit Codes

Standard exit codes for CI/CD integration:

- **0** - Success (all validations passed)
- **1** - Validation failed (counts don't match)
- **2** - Configuration error (missing files/invalid setup)
- **3** - Runtime error (script failure)

## Generated Files

### DEMO_ARTIFACTS/
- `validation_report.json` - Comprehensive test results
- `memory_coordination.json` - Memory coordination data
- `index.json` - Artifact index with expected counts
- `*_analysis.json` - Individual analysis artifacts

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Verify Counts
  run: |
    python scripts/verify_counts.py --verbose
    if [ $? -eq 0 ]; then
      echo "✓ Verification passed"
    else  
      echo "✗ Verification failed"
      exit 1
    fi
```

### Pre-commit Hook

```bash
#!/bin/bash
python scripts/verify_counts.py
exit $?
```

## Troubleshooting

### Common Issues

1. **Unicode Errors on Windows**: Script handles encoding automatically
2. **Missing DEMO_ARTIFACTS**: Directory created automatically  
3. **JSON Parsing Errors**: Detailed error reporting in verbose mode
4. **Path Issues**: Use absolute paths or run from project root

### Debug Mode

Run with `--verbose` flag for detailed step-by-step logging:

```bash
python scripts/verify_counts.py --verbose 2>&1 | tee verification.log
```

## Development

### Adding New Validations

1. Extend `SequentialThinkingValidator` class
2. Add new validation methods following the `step_X_*` pattern
3. Update the `run_validation()` method to include new steps
4. Add appropriate test cases and error handling

### Memory Coordination Extensions

The memory coordination system can be extended to support:
- Cross-session state persistence
- Distributed validation coordination  
- Integration with external CI/CD systems
- Custom validation metrics and reporting

## Performance

- **Average execution time**: 1-3 seconds
- **Memory usage**: < 50MB
- **File I/O**: Optimized for large JSON artifacts
- **Cross-platform**: Consistent performance across systems

## Support

For issues with the verification scripts:
1. Check this README for common solutions
2. Run with `--verbose` for detailed diagnostics
3. Examine generated log files and reports
4. Verify project structure and file permissions