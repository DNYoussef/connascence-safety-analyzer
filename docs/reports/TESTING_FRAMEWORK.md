# Testing Framework Documentation

Comprehensive guide to running tests, interpreting results, and maintaining test quality in the Connascence Safety Analyzer project.

## Overview

The project employs a comprehensive testing strategy using pytest 7.0+ with pytest-cov for coverage tracking, supporting unit, integration, e2e, and performance tests. The framework integrates with VS Code extension testing, MCP server validation, and CI/CD pipelines.

**Current Test Infrastructure:**
- **Primary Framework**: pytest 7.0+ with coverage reporting
- **Test Suites**: 4 distinct test types with 42+ test files
- **Coverage Target**: 85% minimum (enforced by CI/CD)
- **Integration**: MCP server, VS Code extension, autofix engine
- **Performance**: Memory coordination and sequential execution

## Test Architecture

### Test Types

1. **Unit Tests** (`tests/test_*.py`) - 18 active test files
   - Individual component testing with fixtures from conftest.py
   - Mock-based isolation using unittest.mock
   - Fast execution (<100ms per test)
   - Components: analyzer, autofix, policy, CLI, MCP server
   - Coverage target: >85% enforced by pytest.ini

2. **Integration Tests** (`tests/integration/`) - 8 test modules
   - MCP server integration with memory coordination
   - Autofix engine end-to-end workflows  
   - Cross-component validation chains
   - Memory coordination system with sequential thinking
   - Real VS Code extension integration scenarios

3. **End-to-End Tests** (`tests/e2e/`) - 9 comprehensive test modules
   - CLI workflow validation (test_cli_workflows.py)
   - Enterprise-scale testing (test_enterprise_scale.py)
   - Error handling scenarios (test_error_handling.py)
   - Memory coordination validation (test_memory_coordination.py)
   - Complete report generation workflows

4. **Performance Tests** (`tests/performance/`) - Benchmarking suite
   - Load testing with performance_test.json metrics
   - Memory usage validation and leak detection
   - Large-scale analysis benchmarks (enterprise_scale.py)
   - Response time measurement for real-time analysis

## Test Configuration

### Pytest Configuration (`pytest.ini`)

```ini
[tool:pytest]
minversion = 7.0
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --strict-config
    --verbose
    --tb=short
    --cov=analyzer
    --cov=autofix  
    --cov=policy
    --cov=reporting
    --cov=cli
    --cov=mcp
    --cov-report=term-missing
    --cov-report=html:enterprise-package/artifacts/coverage
    --cov-report=xml:tests/results/coverage.xml
    --cache-dir=tests/.pytest_cache
    --cov-fail-under=85
```

### Test Markers

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Tests taking >1 second
- `@pytest.mark.autofix` - Autofix functionality tests
- `@pytest.mark.mcp` - MCP server tests
- `@pytest.mark.performance` - Performance benchmarks
- `@pytest.mark.property` - Property-based tests

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest

# Run specific test types
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
pytest -m "not slow"     # Skip slow tests

# Run specific test files
pytest tests/test_cli.py
pytest tests/e2e/

# Run with coverage
pytest --cov=analyzer --cov-report=html
```

### Advanced Test Options

```bash
# Parallel execution
pytest -n auto

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf

# Verbose output with stack traces
pytest -v --tb=long

# Run performance benchmarks
pytest tests/performance/ --benchmark-only
```

## Test Data and Fixtures

### Available Fixtures (`tests/conftest.py`) - 494 lines

**Primary Test Fixtures:**
- `sample_violations` - ConnascenceViolation instances with CoM, CoP, CoT, CoA types
- `sample_python_code` - 212-line code sample with multiple violation patterns
- `temp_project_dir` - Complete project structure with src/, tests/, docs/
- `mock_analyzer` - Mock analyzer with configurable responses
- `threshold_configs` - Strict/balanced/lenient configuration profiles
- `budget_limits` - Violation budget limits by type and severity
- `sample_autofix_patches` - PatchSuggestion instances with confidence scoring

**Advanced Test Utilities:**
- `assert_violation_present()` - Violation validation helper
- `count_violations_by_type()` - Metrics aggregation
- `create_temp_file()` - Dynamic test file generation
- Mock implementations for removed analyzer components
- ThresholdConfig class for policy testing

### Test Data Creation

```python
def test_analysis_with_fixtures(sample_violations, temp_project_dir):
    # Use pre-configured test data
    analyzer = ConnascenceAnalyzer()
    results = analyzer.analyze_directory(temp_project_dir)
    assert len(results) >= 0
```

## Coverage Requirements

### Coverage Targets

- **Overall Coverage**: >85%
- **Critical Components**: >90%
- **New Code**: 100% (enforced by pre-commit hooks)

### Coverage Reports

- **Terminal**: `--cov-report=term-missing`
- **HTML**: `enterprise-package/artifacts/coverage/`
- **XML**: `tests/results/coverage.xml`

### Viewing Coverage

```bash
# Generate and view HTML coverage report
pytest --cov --cov-report=html
open enterprise-package/artifacts/coverage/index.html
```

## Test Quality Standards

### Test Structure (AAA Pattern)

```python
def test_feature_behavior():
    # Arrange
    analyzer = ConnascenceAnalyzer()
    sample_code = "def func(a, b, c, d, e): pass"
    
    # Act
    violations = analyzer.analyze_string(sample_code)
    
    # Assert
    assert len(violations) > 0
    assert any(v.connascence_type == "CoP" for v in violations)
```

### Test Naming Conventions

```python
# Good: Descriptive and behavior-focused
def test_analyzer_detects_parameter_bomb_violations()
def test_cli_returns_error_code_on_invalid_input()
def test_autofix_safely_extracts_magic_literals()

# Poor: Implementation-focused
def test_get_violations()
def test_main_function()
```

### Test Isolation

- Each test must be independent
- Use fixtures for shared setup
- Clean up resources in teardown
- Mock external dependencies

## Interpreting Test Results

### Success Indicators

```
====== 245 passed in 12.34s ======
Coverage: 87%
All quality gates passed
```

### Failure Analysis

```
FAILED tests/test_cli.py::test_scan_command - AssertionError
FAILED tests/e2e/test_workflows.py::test_full_pipeline - TimeoutError
```

**Debugging Steps:**
1. Run specific failing test with `-v --tb=long`
2. Check test data and fixture setup
3. Validate mock configurations
4. Review test isolation

### Performance Benchmarks

```
Name (time in ms)          Min      Max     Mean    StdDev
test_analyze_large_file   45.23   67.89   52.14    4.32
test_generate_report      12.45   18.76   15.23    1.87
```

## Continuous Integration

### Pre-commit Hooks

```yaml
- repo: local
  hooks:
    - id: pytest
      name: pytest
      entry: pytest
      language: system
      pass_filenames: false
      always_run: true
```

### CI Pipeline Integration

```yaml
- name: Run Tests
  run: |
    pytest --cov --cov-report=xml
    coverage report --fail-under=85
```

## Test Maintenance

### Regular Tasks

1. **Weekly**: Review test coverage reports
2. **Sprint**: Update test data for new features
3. **Monthly**: Performance benchmark review
4. **Quarterly**: Test suite cleanup and optimization

### Adding New Tests

```python
# 1. Create test file following naming convention
# tests/test_new_feature.py

# 2. Add appropriate markers
@pytest.mark.unit
def test_new_feature_basic_behavior():
    pass

# 3. Update conftest.py if new fixtures needed
# 4. Run tests to verify integration
```

### Test Data Management

- Store test data in `tests/fixtures/`
- Use factories for complex test objects
- Version test data with code changes
- Document test data dependencies

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Fix PYTHONPATH issues
   export PYTHONPATH=$PWD:$PYTHONPATH
   pytest
   ```

2. **Coverage Gaps**
   ```bash
   # Generate detailed coverage report
   coverage report --show-missing
   ```

3. **Slow Tests**
   ```bash
   # Profile test execution
   pytest --durations=10
   ```

4. **Flaky Tests**
   ```bash
   # Run tests multiple times
   pytest --count=10 tests/test_flaky.py
   ```

### Debug Configuration

```python
# Add to pytest.ini for debugging
[tool:pytest]
log_cli = true
log_cli_level = DEBUG
log_cli_format = %(asctime)s [%(levelname)8s] %(name)s: %(message)s
```

## Best Practices

### Test Design

- One assertion per test (where possible)
- Test edge cases and error conditions
- Use descriptive test names
- Follow the AAA pattern (Arrange, Act, Assert)

### Performance

- Keep unit tests under 100ms
- Use mocking for external dependencies
- Parallel test execution where appropriate
- Regular performance regression testing

### Maintenance

- Regular test review and cleanup
- Update tests with feature changes
- Monitor and improve test coverage
- Document complex test scenarios

---

*Last Updated: September 2024*  
*Framework Version: pytest 7.0+*  
*Coverage Target: 85%+*