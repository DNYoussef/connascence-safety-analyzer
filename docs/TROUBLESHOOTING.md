# Troubleshooting Guide - Connascence Safety Analyzer

**Version**: 2.0.2+
**Last Updated**: 2025-10-07

This guide helps you diagnose and resolve common issues with the Connascence Safety Analyzer.

---

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Installation Issues](#installation-issues)
- [VSCode Extension Issues](#vscode-extension-issues)
- [Python Analyzer Issues](#python-analyzer-issues)
- [MCP Server Issues](#mcp-server-issues)
- [Performance Issues](#performance-issues)
- [Error Messages](#error-messages)
- [Getting Additional Help](#getting-additional-help)

---

## Quick Diagnostics

Run this diagnostic script to check your installation:

```bash
# Check versions
connascence --version
code --list-extensions | grep connascence
python --version
node --version

# Test basic functionality
connascence scan examples/ --format json

# Check MCP server
curl http://localhost:8765/health

# View logs
tail -f ~/.connascence/logs/analyzer.log
```

---

## Installation Issues

### Issue: "connascence: command not found"

**Symptoms:**
```bash
$ connascence --version
bash: connascence: command not found
```

**Solutions:**

1. **Verify installation:**
   ```bash
   pip show connascence-analyzer
   ```

2. **Install if missing:**
   ```bash
   pip install connascence-analyzer
   ```

3. **Check PATH:**
   ```bash
   # Find where pip installed it
   which connascence
   pip show connascence-analyzer | grep Location

   # Add to PATH (if needed)
   export PATH="$PATH:$HOME/.local/bin"  # Linux/macOS
   ```

4. **Use python -m as workaround:**
   ```bash
   python -m interfaces.cli.connascence --version
   ```

---

### Issue: pip install fails with permissions error

**Symptoms:**
```
ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied
```

**Solutions:**

1. **Install for user only:**
   ```bash
   pip install --user connascence-analyzer
   ```

2. **Use virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install connascence-analyzer
   ```

3. **On Linux/macOS, avoid sudo:**
   ```bash
   # DON'T: sudo pip install connascence-analyzer
   # DO: pip install --user connascence-analyzer
   ```

---

### Issue: VSCode extension not installing

**Symptoms:**
- Extension doesn't appear in Extensions panel
- Installation hangs or fails

**Solutions:**

1. **Check VSCode version:**
   ```bash
   code --version
   # Must be 1.74.0 or higher
   ```

2. **Install manually from VSIX:**
   ```bash
   code --install-extension path/to/connascence-safety-analyzer-2.0.2.vsix
   ```

3. **Clear extension cache:**
   ```bash
   # Close VSCode first
   rm -rf ~/.vscode/extensions/connascence*
   # Reinstall
   code --install-extension connascence-systems.connascence-safety-analyzer
   ```

4. **Check logs:**
   ```bash
   # View extension host log
   # VSCode → Help → Toggle Developer Tools → Console
   ```

---

## VSCode Extension Issues

### Issue: Extension not activating

**Symptoms:**
- Extension shows as "Installed" but doesn't work
- Commands not appearing in Command Palette
- No analysis results in Problems panel

**Solutions:**

1. **Reload VSCode:**
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS)
   - Type "Developer: Reload Window"
   - Press Enter

2. **Check Output panel:**
   - View → Output
   - Select "Connascence" from dropdown
   - Look for error messages

3. **Verify Python analyzer is installed:**
   ```bash
   connascence --version
   # Should output: connascence-analyzer 2.0.x
   ```

4. **Check activation events:**
   - Open a `.py`, `.js`, or `.ts` file
   - Extension should activate automatically

5. **Reinstall extension:**
   ```bash
   code --uninstall-extension connascence-systems.connascence-safety-analyzer
   code --install-extension connascence-systems.connascence-safety-analyzer
   ```

---

### Issue: "MCP server not available" error

**Symptoms:**
```
[Connascence] MCP server not connected, using CLI fallback
```

**Solutions:**

1. **This is normal** - Extension automatically falls back to CLI
   - Analysis still works, just slower
   - No action needed unless you want MCP performance

2. **To enable MCP server:**
   ```bash
   # Install MCP dependencies
   pip install connascence-analyzer[mcp]

   # Start MCP server
   python -m mcp.server

   # Keep server running in background
   # Or use systemd/supervisor for production
   ```

3. **Configure server URL:**
   ```json
   // VSCode settings.json
   {
     "connascence.serverUrl": "http://localhost:8080"
   }
   ```

4. **Verify server is running:**
   ```bash
   curl http://localhost:8765/health
   # Should return: {"status": "healthy"}
   ```

---

### Issue: Analysis not showing in Problems panel

**Symptoms:**
- Extension is active
- No violations shown even in problematic code

**Solutions:**

1. **Check file language:**
   - Only analyzes Python, JavaScript, TypeScript
   - Check bottom-right language indicator in VSCode

2. **Verify real-time analysis is enabled:**
   ```json
   {
     "connascence.realTimeAnalysis": true
   }
   ```

3. **Manually trigger analysis:**
   - Press `Ctrl+Shift+P`
   - Type "Connascence: Analyze File"
   - Press Enter

4. **Check exclusion patterns:**
   ```json
   {
     "connascence.exclude": [
       "node_modules/**",
       // Remove patterns that might exclude your files
     ]
   }
   ```

5. **View raw analysis output:**
   ```bash
   connascence scan path/to/file.py --format json
   ```

---

## Python Analyzer Issues

### Issue: Analysis is very slow

**Symptoms:**
- Takes > 10 seconds to analyze single file
- Workspace analysis times out

**Solutions:**

1. **Enable parallel analysis:**
   ```bash
   connascence scan . --parallel --workers 4
   ```

2. **Exclude unnecessary directories:**
   ```yaml
   # .connascence.yml
   exclude:
     - node_modules
     - venv
     - __pycache__
     - "*.pyc"
     - .git
     - build
     - dist
   ```

3. **Increase file size limit:**
   ```json
   {
     "connascence.maxFileSize": 2097152  // 2MB
   }
   ```

4. **Use MCP server for better performance:**
   ```bash
   # 2.8-4.4x faster with MCP
   python -m mcp.server &
   ```

---

### Issue: "ModuleNotFoundError" when running analyzer

**Symptoms:**
```python
ModuleNotFoundError: No module named 'analyzer'
```

**Solutions:**

1. **Install in editable mode:**
   ```bash
   pip install -e .
   ```

2. **Verify PYTHONPATH:**
   ```bash
   echo $PYTHONPATH
   # Should include your project directory
   ```

3. **Add to PYTHONPATH manually:**
   ```bash
   export PYTHONPATH="${PYTHONPATH}:/path/to/connascence-analyzer"
   ```

---

### Issue: False positives in analysis

**Symptoms:**
- Analyzer reports violations in valid code
- Too many low-severity warnings

**Solutions:**

1. **Adjust policy:**
   ```bash
   # Use more lenient policy
   connascence scan . --policy lenient

   # Or customize thresholds
   connascence scan . --max-parameters 8 --max-methods 25
   ```

2. **Configure in .connascence.yml:**
   ```yaml
   policy: standard

   thresholds:
     max_parameters: 6
     max_methods: 20
     max_nested_depth: 4
     max_class_dependencies: 15

   ignore_patterns:
     - "test_*.py"
     - "*_test.py"
   ```

3. **Suppress specific warnings:**
   ```python
   # In code
   def my_function(a, b, c, d, e, f):  # connascence: ignore CoP
       pass
   ```

---

## MCP Server Issues

### Issue: MCP server won't start

**Symptoms:**
```
Error: Address already in use
```

**Solutions:**

1. **Check if already running:**
   ```bash
   # Linux/macOS
   lsof -i :8765

   # Windows
   netstat -ano | findstr :8765
   ```

2. **Kill existing process:**
   ```bash
   # Linux/macOS
   pkill -f "mcp.server"

   # Windows
   taskkill /F /IM python.exe /FI "WINDOWTITLE eq *mcp.server*"
   ```

3. **Use different port:**
   ```bash
   python -m mcp.server --port 8766

   # Update VSCode config
   {
     "connascence.mcpServerPort": 8766
   }
   ```

---

### Issue: MCP WebSocket connection fails

**Symptoms:**
```
[MCP] Connection error: Connection refused
```

**Solutions:**

1. **Verify server is running:**
   ```bash
   curl http://localhost:8765/health
   ```

2. **Check firewall:**
   ```bash
   # Allow port 8765
   # Windows: Windows Defender Firewall → Allow app
   # Linux: sudo ufw allow 8765
   # macOS: System Preferences → Security → Firewall → Options
   ```

3. **Test WebSocket connection:**
   ```javascript
   // Browser console
   const ws = new WebSocket('ws://localhost:8765/ws');
   ws.onopen = () => console.log('Connected!');
   ws.onerror = (e) => console.error('Error:', e);
   ```

---

## Performance Issues

### Issue: High memory usage

**Symptoms:**
- Extension uses > 500MB RAM
- System becomes sluggish during analysis

**Solutions:**

1. **Limit workspace size:**
   ```json
   {
     "connascence.exclude": [
       "node_modules/**",
       "venv/**",
       "**/*.min.js"
     ],
     "connascence.maxFilesAnalyzed": 1000
   }
   ```

2. **Disable real-time analysis for large files:**
   ```json
   {
     "connascence.realTimeAnalysis": false,
     "connascence.maxFileSize": 524288  // 512KB
   }
   ```

3. **Analyze on-demand instead:**
   - Disable auto-analysis
   - Use manual `Connascence: Analyze File` command

---

### Issue: Extension slows down VSCode

**Symptoms:**
- VSCode becomes unresponsive
- Typing lag in editor

**Solutions:**

1. **Increase debounce timeout:**
   ```json
   {
     "connascence.debounceMs": 2000  // Wait 2s before analyzing
   }
   ```

2. **Disable Code Lens:**
   ```json
   {
     "connascence.enableCodeLens": false
   }
   ```

3. **Limit diagnostic count:**
   ```json
   {
     "connascence.maxDiagnostics": 500
   }
   ```

---

## Error Messages

### "Failed to parse file: invalid syntax"

**Cause**: Python syntax errors in file

**Solution**:
```bash
# Fix syntax errors first
python -m py_compile file.py

# Then run analysis
connascence scan file.py
```

---

### "Policy 'nasa-compliance' not found"

**Cause**: Trying to use unavailable policy

**Solution**:
```bash
# List available policies
connascence policies list

# Use valid policy
connascence scan . --policy strict
```

---

### "SARIF output failed: invalid JSON"

**Cause**: SARIF generation error

**Solution**:
```bash
# Use JSON format instead
connascence scan . --format json --output results.json

# Or upgrade analyzer
pip install --upgrade connascence-analyzer
```

---

## Getting Additional Help

### Collect Diagnostic Information

```bash
# Create diagnostic report
cat > diagnostics.txt << EOF
# System Information
OS: $(uname -a)
Python: $(python --version)
Node: $(node --version)
VSCode: $(code --version)

# Package versions
$(pip show connascence-analyzer)

# Extension status
$(code --list-extensions | grep connascence)

# Test analysis
$(connascence scan examples/ --format json 2>&1)

# MCP status
$(curl http://localhost:8765/health 2>&1)
EOF

cat diagnostics.txt
```

### Where to Get Help

1. **Documentation**:
   - Installation: [INSTALLATION.md](./INSTALLATION.md)
   - Development: [DEVELOPMENT.md](./DEVELOPMENT.md)

2. **GitHub Issues**:
   - Search existing: https://github.com/connascence-systems/connascence-analyzer/issues
   - Create new issue with diagnostic info

3. **Discussions**:
   - Q&A: https://github.com/connascence-systems/connascence-analyzer/discussions

4. **Logs**:
   - VSCode: View → Output → Connascence
   - Python: `~/.connascence/logs/analyzer.log`
   - MCP: `~/.connascence/logs/mcp-server.log`

---

## Known Issues

### Windows-specific

- **PowerShell Execution Policy**: May need `Set-ExecutionPolicy RemoteSigned`
- **Long paths**: Enable long path support in Windows 10+

### macOS-specific

- **Gatekeeper**: May need to allow unsigned extension
- **Homebrew Python**: Use `python3` instead of `python`

### Linux-specific

- **Snap VSCode**: Extension path differs, use flatpak or .deb
- **SELinux**: May need `chcon` on executable files

---

**Still having issues?** Open an issue with your diagnostic information: https://github.com/connascence-systems/connascence-analyzer/issues/new
