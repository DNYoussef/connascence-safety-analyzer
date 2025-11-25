# Enhanced Integration Tests

This directory contains comprehensive integration tests for the enhanced connascence analyzer pipeline, covering:

- MCP Server integration
- Web Dashboard integration
- VSCode Extension integration
- Performance benchmarks

## Test Organization

- `test_mcp_server_integration.py` - MCP server enhanced pipeline tests
- `test_web_dashboard_integration.py` - Web dashboard visualization tests
- `test_vscode_integration.py` - VSCode extension integration tests
- `test_performance_benchmarks.py` - Performance and scalability benchmarks
- `test_infrastructure.py` - Shared test utilities and fixtures
- `conftest.py` - Pytest configuration with external service checks

## Running Tests

### Without External Services (Default)

By default, tests requiring external services will be **automatically skipped**:

```bash
# Run all tests (skips tests requiring external services)
pytest tests/enhanced/

# Run specific test file
pytest tests/enhanced/test_mcp_server_integration.py
```

### With External Services

To run tests that require external services, start the services first:

#### 1. MCP Server Tests

```bash
# Start MCP server on localhost:3000 (default)
npm run mcp-server  # or your start command

# Run MCP server tests
pytest tests/enhanced/test_mcp_server_integration.py

# Custom host/port
export MCP_SERVER_HOST=192.168.1.100
export MCP_SERVER_PORT=8080
pytest tests/enhanced/test_mcp_server_integration.py
```

#### 2. Web Dashboard Tests

```bash
# Start Web Dashboard on localhost:3001 (default)
npm run dashboard  # or your start command

# Run dashboard tests
pytest tests/enhanced/test_web_dashboard_integration.py

# Custom host/port
export DASHBOARD_HOST=192.168.1.100
export DASHBOARD_PORT=8081
pytest tests/enhanced/test_web_dashboard_integration.py
```

#### 3. VSCode Extension Tests

```bash
# Enable VSCode extension testing
export VSCODE_EXTENSION_TEST=1

# Optional: Set test workspace path
export VSCODE_TEST_WORKSPACE=/path/to/test/workspace

# Run VSCode extension tests
pytest tests/enhanced/test_vscode_integration.py
```

#### 4. Performance Benchmarks

```bash
# Performance tests don't require external services
pytest tests/enhanced/test_performance_benchmarks.py

# Run with verbose output
pytest tests/enhanced/test_performance_benchmarks.py -v
```

### Running All Tests with Services

```bash
# Start all services, then:
export VSCODE_EXTENSION_TEST=1
pytest tests/enhanced/ -v
```

## Test Markers

Tests are marked with pytest markers for selective execution:

```bash
# Run only MCP server tests
pytest -m mcp_server

# Run only Web dashboard tests
pytest -m web_dashboard

# Run only VSCode extension tests
pytest -m vscode

# Run only performance tests
pytest -m performance

# Run integration tests (all)
pytest -m integration

# Exclude slow/performance tests
pytest -m "not performance"

# Run multiple categories
pytest -m "mcp_server or web_dashboard"
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_SERVER_HOST` | `localhost` | MCP server hostname |
| `MCP_SERVER_PORT` | `3000` | MCP server port |
| `DASHBOARD_HOST` | `localhost` | Web Dashboard hostname |
| `DASHBOARD_PORT` | `3001` | Web Dashboard port |
| `VSCODE_EXTENSION_TEST` | `0` | Enable VSCode extension tests (set to `1`) |
| `VSCODE_TEST_WORKSPACE` | `None` | VSCode test workspace path |

### Service Availability Checks

The test suite automatically checks service availability before running tests:

- **MCP Server**: Checks TCP connection to `localhost:3000` (or configured host/port)
- **Web Dashboard**: Checks TCP connection to `localhost:3001` (or configured host/port)
- **VSCode Extension**: Checks `VSCODE_EXTENSION_TEST=1` environment variable

Tests requiring unavailable services are **automatically skipped** with informative messages.

## Test Report

When running tests, pytest displays service availability status:

```
Enhanced Integration Test Configuration
------------------------------------------------------------
MCP Server: NOT AVAILABLE (tests will be skipped)
Web Dashboard: AVAILABLE
VSCode Extension: NOT ENABLED (tests will be skipped)
------------------------------------------------------------
To run with external services:
  1. MCP Server: Start server on localhost:3000 (or set MCP_SERVER_HOST/PORT)
  2. Web Dashboard: Start dashboard on localhost:3001 (or set DASHBOARD_HOST/PORT)
  3. VSCode Extension: Set VSCODE_EXTENSION_TEST=1 environment variable
```

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/test-enhanced.yml
name: Enhanced Integration Tests

on: [push, pull_request]

jobs:
  test-with-services:
    runs-on: ubuntu-latest

    services:
      mcp-server:
        image: connascence/mcp-server:latest
        ports:
          - 3000:3000

      web-dashboard:
        image: connascence/dashboard:latest
        ports:
          - 3001:3001

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run enhanced tests
        env:
          VSCODE_EXTENSION_TEST: 1
        run: |
          pytest tests/enhanced/ -v --cov

  test-without-services:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run unit tests only (no external services)
        run: |
          pytest tests/enhanced/ -v -m "not integration"
```

## Troubleshooting

### Tests Skipped Unexpectedly

**Issue**: Tests are being skipped even though services are running.

**Solution**: Check service connectivity:

```bash
# Test MCP server connectivity
curl http://localhost:3000/health

# Test Web Dashboard connectivity
curl http://localhost:3001/health

# Check if ports are listening
netstat -an | grep 3000
netstat -an | grep 3001
```

### Connection Refused Errors

**Issue**: Service availability check fails with "Connection refused".

**Possible causes**:
1. Service not started
2. Service running on different host/port
3. Firewall blocking connections

**Solution**:
```bash
# Verify service is running
ps aux | grep mcp-server
ps aux | grep dashboard

# Check configured ports
echo $MCP_SERVER_PORT
echo $DASHBOARD_PORT

# Test direct connection
telnet localhost 3000
telnet localhost 3001
```

### VSCode Extension Tests Not Running

**Issue**: VSCode extension tests are skipped.

**Solution**: Enable VSCode extension testing:

```bash
export VSCODE_EXTENSION_TEST=1
pytest tests/enhanced/test_vscode_integration.py -v
```

## Development

### Adding New Integration Tests

When adding tests that require external services:

1. Use the `@integration_test` decorator from `test_infrastructure.py`
2. Apply appropriate markers (`@pytest.mark.mcp_server`, etc.)
3. The conftest will automatically handle skip logic

Example:

```python
from test_infrastructure import integration_test

class TestNewFeature:
    @integration_test(["mcp_server"])
    def test_new_mcp_feature(self):
        # This test requires MCP server
        # Will be automatically skipped if server is unavailable
        pass
```

### Testing Skip Logic

To verify skip markers are working correctly:

```bash
# Run with verbose output to see skip reasons
pytest tests/enhanced/ -v --tb=short

# Show skip summary
pytest tests/enhanced/ --tb=no -ra
```

## Performance Benchmarks

Performance tests measure:
- Analysis execution time
- Memory usage patterns
- Scalability across project sizes
- Concurrent analysis performance
- Interface response times

Performance tests **do not require external services** and can be run anytime:

```bash
pytest tests/enhanced/test_performance_benchmarks.py -v
```

## Additional Resources

- [Connascence Analyzer Documentation](../../docs/)
- [MCP Server API Reference](../../docs/mcp-server.md)
- [Web Dashboard Guide](../../docs/web-dashboard.md)
- [VSCode Extension Documentation](../../docs/vscode-extension.md)
