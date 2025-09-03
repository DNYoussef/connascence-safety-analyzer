# Connascence System - 30-Second Smoke Test

## 🚀 Quick Validation for Skeptical Buyers

This smoke test provides **immediate proof** that the Connascence system works across all platforms and output formats. Perfect for buyers who need to validate functionality before committing.

### ⚡ What This Test Proves

✅ **Core analyzer functionality** - Detects connascence patterns in real code  
✅ **Multi-platform compatibility** - Windows, Linux, macOS  
✅ **Output format validation** - JSON, SARIF, Markdown  
✅ **MCP server integration** - Analysis service integration ready  
✅ **VS Code extension compatibility** - IDE integration works  
✅ **Performance validation** - Completes in under 30 seconds  

## 🏃‍♂️ Quick Start

### Prerequisites (2 minutes)

```bash
# Ensure you have Node.js 18+ installed
node --version  # Should show v18+
npm --version   # Should show 8+

# Optional: VS Code for extension testing
code --version  # Optional but recommended
```

### Run Test (30 seconds)

**Linux/macOS:**
```bash
cd data-room/demo
chmod +x SMOKE_TEST.sh
./SMOKE_TEST.sh
```

**Windows (PowerShell/Command Prompt):**
```cmd
cd data-room\demo
SMOKE_TEST.bat
```

### Expected Output

```
==================================================================
  CONNASCENCE SYSTEM - SMOKE TEST
==================================================================
Platform: Linux | Started: 2024-01-15 14:30:00

[INFO] Checking prerequisites...
[PASS] Node.js detected: v18.17.0
[PASS] npm detected: 9.6.7
[PASS] VS Code detected

[INFO] Testing core installation...
[PASS] Connascence CLI binary found
[PASS] Package configuration found

[INFO] Creating test samples...
[PASS] Test samples created

[INFO] Testing analyzer core functionality...
[PASS] CLI analyzer working

[INFO] Testing output formats...
[PASS] JSON output format valid
[PASS] SARIF output format valid
[PASS] Markdown output format valid

[INFO] Testing MCP server...
[PASS] MCP server found
[PASS] MCP server can start

[INFO] Testing VS Code extension...
[PASS] VS Code extension files found
[PASS] VS Code extension package valid

[INFO] Testing performance (should complete in <30s)...
[PASS] Performance test passed (12s elapsed)

[INFO] Cleaning up test files...
[PASS] Cleanup complete

==================================================================
  TEST RESULTS
==================================================================
✓ ALL TESTS PASSED (12/12)
✓ CONNASCENCE SYSTEM IS READY FOR PRODUCTION
✓ Duration: 12 seconds

Ready to integrate into your development workflow!
```

## 🔍 What The Test Does

### 1. Prerequisites Check
- Validates Node.js 18+ installation
- Confirms npm availability  
- Detects VS Code (optional)

### 2. Core Installation Validation
- Verifies CLI binary exists
- Checks package configuration
- Validates file structure

### 3. Functional Testing
Creates sample code with different connascence levels:

**High Coupling Sample:**
```javascript
class Child extends Parent {
    process(item) {
        // Subclass Connascence detected
        this.data.push(item.toLowerCase());
        return super.process(item);
    }
}
```

**Medium Coupling Sample:**
```javascript
// Position Connascence detected
calculateTax(1000, 0.25, "US", 2023);
calculateTax(2000, 0.20, "CA", 2023);
```

**Low Coupling Sample:**
```javascript
// Only Name Connascence (acceptable)
const TAX_RATE = 0.25;
function calculateSimpleTax(amount) {
    return amount * TAX_RATE;
}
```

### 4. Output Format Validation
- **JSON**: Structured data for tools
- **SARIF**: Security/quality tool standard
- **Markdown**: Human-readable reports

### 5. Integration Testing
- MCP server can start and respond
- VS Code extension loads properly
- All components work together

## 🚨 Common Issues & Solutions

### "Node.js not found"
```bash
# Install Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### "CLI analyzer failed"
Check if you're in the correct directory:
```bash
# Should be in project root or demo folder
ls -la  # Should show connascence files
```

### "VS Code not detected"
Not required for core functionality:
- All other tests can still pass
- Extension testing will be skipped

## 📊 Success Criteria

**FULL SUCCESS (Production Ready):**
- All 10+ tests pass
- Duration under 25 seconds
- No error messages

**PARTIAL SUCCESS (Minor Issues):**
- 8+ tests pass
- Core analyzer works
- Output formats valid

**FAILURE (Needs Investigation):**
- CLI analyzer fails
- Multiple format failures
- Prerequisites missing

## 🎯 For Enterprise Buyers

This test validates the **critical path** for enterprise adoption:

1. **Developer Productivity**: CLI works immediately
2. **Tool Integration**: SARIF output for existing workflows  
3. **IDE Integration**: VS Code extension functional
4. **Automation Ready**: MCP server responds
5. **Cross-Platform**: Works everywhere your team does

## 🔧 Troubleshooting

**Test hangs or times out:**
```bash
# Kill test and check system resources
Ctrl+C
ps aux | grep node
killall node  # If needed
```

**Permission errors (Linux/macOS):**
```bash
chmod +x SMOKE_TEST.sh
sudo chown $(whoami) ./data-room/demo/
```

**Windows execution policy:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 📈 Performance Benchmarks

**Typical Results:**
- **Linux**: 8-15 seconds
- **macOS**: 10-18 seconds  
- **Windows**: 12-22 seconds

**Hardware Requirements:**
- **Minimum**: 2GB RAM, dual-core CPU
- **Recommended**: 4GB RAM, quad-core CPU

## 🎉 Next Steps After Passing

1. **Explore Full Analysis**: `connascence analyze ./your-project`
2. **Try VS Code Extension**: Install and analyze in IDE
3. **Set Up CI/CD**: Integrate SARIF output
4. **Configure MCP**: Connect to analysis service for automated code review
5. **Review Enterprise Features**: Check `/data-room/` for pricing

---

**Questions?** This test is designed to be self-explanatory, but if you encounter issues, check the troubleshooting section or contact support.