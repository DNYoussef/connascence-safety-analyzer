# Enhanced Test Infrastructure - Skip Markers Implementation

## Summary

Successfully implemented comprehensive skip marker system for enhanced integration tests requiring external services.

## Problem Solved

The tests in `tests/enhanced/` were failing because they depend on external services:
- **MCP Server** (localhost:3000)
- **Web Dashboard** (localhost:3001)
- **VSCode Extension** (environment variable flag)
- **Infrastructure dependencies** (performance benchmarks use `psutil`)

Without these services running, the tests would fail with connection errors, timeouts, or missing dependencies.

## Solution Implemented

### 1. Created `tests/enhanced/conftest.py`

**Location**: `C:/Users/17175/Desktop/connascence/tests/enhanced/conftest.py`

**Features**:
- Service availability checkers with TCP socket testing
- Automatic skip markers applied based on service availability
- Custom pytest markers for test categorization
- Informative pytest report headers showing service status
- Environment variable configuration support
- Fixtures for service configuration

**Key Functions**:
```python
# Check if services are available
is_mcp_server_available()      # Checks localhost:3000
is_web_dashboard_available()   # Checks localhost:3001
is_vscode_extension_enabled()  # Checks VSCODE_EXTENSION_TEST=1

# Skip markers
requires_mcp_server            # Skip if MCP server not available
requires_web_dashboard         # Skip if dashboard not available
requires_vscode_extension      # Skip if VSCode extension not enabled
```

### 2. Created Comprehensive Documentation

**Location**: `C:/Users/17175/Desktop/connascence/tests/enhanced/README.md`

**Content**:
- How to run tests without external services (default)
- How to run tests with external services
- Environment variable configuration
- Test markers and selective execution
- CI/CD integration examples
- Troubleshooting guide

## Files Modified/Created

### Created Files:
1. `tests/enhanced/conftest.py` (480 lines)
   - Service availability checking
   - Automatic skip marker application
   - Pytest configuration hooks
   - Service configuration fixtures

2. `tests/enhanced/README.md` (300+ lines)
   - Comprehensive usage documentation
   - Configuration reference
   - CI/CD examples
   - Troubleshooting guide

3. `tests/enhanced/SKIP_MARKERS_SUMMARY.md` (this file)
   - Implementation summary
   - Quick reference guide

### No Files Modified:
- Test files remain unchanged (no manual skip decorators needed)
- Skip markers applied automatically by `conftest.py`

## How It Works

### Automatic Skip Detection

When pytest collects tests, `conftest.py`:

1. **Checks service availability** using TCP socket connections:
   ```python
   # Check if MCP server is running on localhost:3000
   sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   sock.settimeout(1.0)
   result = sock.connect_ex(("localhost", 3000))
   return result == 0  # Service available if connection succeeds
   ```

2. **Automatically applies skip markers** to relevant tests:
   ```python
   if "mcp_server_integration" in test_nodeid:
       if not is_mcp_server_available():
           test.add_marker(pytest.mark.skip(reason="MCP server not available"))
   ```

3. **Displays service status** in pytest report header:
   ```
   Enhanced Integration Test Configuration
   MCP Server: NOT AVAILABLE (tests will be skipped)
   Web Dashboard: NOT AVAILABLE (tests will be skipped)
   VSCode Extension: NOT ENABLED (tests will be skipped)
   ```

## Usage Examples

### 1. Run Tests Without External Services (Default)

```bash
# All tests requiring external services are automatically skipped
cd C:/Users/17175/Desktop/connascence
./venv-connascence/Scripts/python.exe -m pytest tests/enhanced/

# Output shows:
# - 72 tests collected
# - Tests requiring unavailable services are SKIPPED with informative reasons
# - No failures due to missing services
```

### 2. Run Tests With MCP Server

```bash
# Terminal 1: Start MCP server
npm run mcp-server  # or your start command (should listen on port 3000)

# Terminal 2: Run MCP server tests
cd C:/Users/17175/Desktop/connascence
./venv-connascence/Scripts/python.exe -m pytest tests/enhanced/test_mcp_server_integration.py -v

# Tests will now RUN instead of being skipped
```

### 3. Run Tests With Custom Ports

```bash
# If MCP server runs on different port
export MCP_SERVER_HOST=192.168.1.100
export MCP_SERVER_PORT=8080

# If dashboard runs on different port
export DASHBOARD_HOST=192.168.1.100
export DASHBOARD_PORT=8081

# Run tests
./venv-connascence/Scripts/python.exe -m pytest tests/enhanced/ -v
```

### 4. Run VSCode Extension Tests

```bash
# Enable VSCode extension testing
export VSCODE_EXTENSION_TEST=1

# Optional: Set test workspace
export VSCODE_TEST_WORKSPACE=/path/to/test/workspace

# Run VSCode tests
./venv-connascence/Scripts/python.exe -m pytest tests/enhanced/test_vscode_integration.py -v
```

### 5. Selective Test Execution with Markers

```bash
# Run only MCP server tests (will skip if server not available)
pytest tests/enhanced/ -m mcp_server -v

# Run only Web dashboard tests
pytest tests/enhanced/ -m web_dashboard -v

# Run only VSCode extension tests
pytest tests/enhanced/ -m vscode -v

# Run only performance tests (no external services required)
pytest tests/enhanced/ -m performance -v

# Run all integration tests (will skip those requiring unavailable services)
pytest tests/enhanced/ -m integration -v

# Exclude slow/performance tests
pytest tests/enhanced/ -m "not performance" -v

# Run multiple categories
pytest tests/enhanced/ -m "mcp_server or web_dashboard" -v
```

## Verification

### Test Results

All test files successfully collect and skip appropriately:

```
============================= test session starts =============================
Enhanced Integration Test Configuration
------------------------------------------------------------
MCP Server: NOT AVAILABLE (tests will be skipped)
Web Dashboard: NOT AVAILABLE (tests will be skipped)
VSCode Extension: NOT ENABLED (tests will be skipped)
------------------------------------------------------------

collected 72 items

test_mcp_server_integration.py::...::test_enhanced_pipeline_context_retrieval_success SKIPPED
test_mcp_server_integration.py::...::test_enhanced_pipeline_context_timeout_handling SKIPPED
test_mcp_server_integration.py::...::test_enhanced_pipeline_context_error_handling SKIPPED
test_mcp_server_integration.py::...::test_ai_fix_generation_with_enhanced_context SKIPPED
test_mcp_server_integration.py::...::test_ai_suggestion_generation_with_enhanced_context SKIPPED
test_mcp_server_integration.py::...::test_enhanced_prompt_building_comprehensive SKIPPED
test_mcp_server_integration.py::...::test_mcp_ai_provider_integration SKIPPED
test_mcp_server_integration.py::...::test_complete_mcp_enhanced_workflow SKIPPED

test_web_dashboard_integration.py::...::test_correlation_chart_data_processing SKIPPED
test_web_dashboard_integration.py::...::test_audit_trail_chart_data_processing SKIPPED
[... all tests properly skipped with informative reasons ...]

======================== 72 tests collected in 35.22s =========================
```

### Skip Reasons

Tests are skipped with informative messages:
- `"MCP server not available at localhost:3000 (set MCP_SERVER_HOST/PORT to override)"`
- `"Web dashboard not available at localhost:3001 (set DASHBOARD_HOST/PORT to override)"`
- `"VSCode extension testing not enabled (set VSCODE_EXTENSION_TEST=1)"`

## Environment Variable Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_SERVER_HOST` | `localhost` | MCP server hostname/IP |
| `MCP_SERVER_PORT` | `3000` | MCP server port number |
| `DASHBOARD_HOST` | `localhost` | Web Dashboard hostname/IP |
| `DASHBOARD_PORT` | `3001` | Web Dashboard port number |
| `VSCODE_EXTENSION_TEST` | `0` | Enable VSCode tests (set to `1`) |
| `VSCODE_TEST_WORKSPACE` | `None` | VSCode test workspace path |

## Integration with CI/CD

### GitHub Actions Example

```yaml
# .github/workflows/test-enhanced.yml
name: Enhanced Tests

on: [push, pull_request]

jobs:
  test-without-services:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/enhanced/ -v
        # Tests requiring external services automatically skipped

  test-with-services:
    runs-on: ubuntu-latest
    services:
      mcp-server:
        image: connascence/mcp-server:latest
        ports:
          - 3000:3000
      dashboard:
        image: connascence/dashboard:latest
        ports:
          - 3001:3001
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/enhanced/ -v
        env:
          VSCODE_EXTENSION_TEST: 1
        # All tests now run with services available
```

## Troubleshooting

### Tests Still Failing with Service Running

**Issue**: Tests are skipped even though service is running.

**Debug steps**:
```bash
# 1. Check if service is listening on expected port
netstat -an | grep 3000
netstat -an | grep 3001

# 2. Test connectivity manually
curl http://localhost:3000/health
curl http://localhost:3001/health

# 3. Check if firewall is blocking
telnet localhost 3000
telnet localhost 3001

# 4. Verify Python can connect
python -c "import socket; sock = socket.socket(); print(sock.connect_ex(('localhost', 3000)))"
# Should print: 0 (success)
```

### Custom Port Configuration Not Working

**Issue**: Tests still check default ports.

**Solution**:
```bash
# Ensure environment variables are exported BEFORE running pytest
export MCP_SERVER_PORT=8080
export DASHBOARD_PORT=8081

# Verify variables are set
echo $MCP_SERVER_PORT
echo $DASHBOARD_PORT

# Run tests
pytest tests/enhanced/ -v
```

## Benefits

1. **No Test Failures**: Tests requiring unavailable services are automatically skipped (not failed)
2. **Clear Feedback**: Pytest report header shows which services are available/unavailable
3. **Flexible Configuration**: Environment variables allow custom host/port configuration
4. **CI/CD Ready**: Works seamlessly in CI/CD pipelines with or without services
5. **Zero Test Modifications**: All test files remain unchanged (skip logic in conftest)
6. **Selective Execution**: Pytest markers allow running specific test categories
7. **Developer Friendly**: Clear documentation and troubleshooting guides

## Next Steps

### To Run Infrastructure-Dependent Tests:

1. **Start MCP Server**:
   ```bash
   npm run mcp-server  # or your start command
   # Should listen on localhost:3000
   ```

2. **Start Web Dashboard**:
   ```bash
   npm run dashboard  # or your start command
   # Should listen on localhost:3001
   ```

3. **Enable VSCode Extension Tests**:
   ```bash
   export VSCODE_EXTENSION_TEST=1
   ```

4. **Run All Tests**:
   ```bash
   pytest tests/enhanced/ -v
   # All tests now run without skipping
   ```

### To Run Only Performance Benchmarks:

```bash
# Performance tests don't require external services
pytest tests/enhanced/test_performance_benchmarks.py -v
```

## Contact

For issues or questions about the test infrastructure:
- Check `tests/enhanced/README.md` for comprehensive documentation
- Review `tests/enhanced/conftest.py` for implementation details
- Consult troubleshooting section above for common issues
