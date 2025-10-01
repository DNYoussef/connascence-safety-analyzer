# VSCode Connascence Analyzer Extension - Complete User Guide

**Version**: 2.0.2
**Wrapper Version**: 2.0.0 (Security Hardened)
**Status**: Production Ready - Security Validated
**Last Updated**: 2025-09-23

---

##  Table of Contents

1. [Quick Start](#quick-start)
2. [What is This?](#what-is-this)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Using the Extension](#using-the-extension)
6. [Features](#features)
7. [Troubleshooting](#troubleshooting)
8. [Architecture](#architecture)
9. [Development](#development)
10. [FAQ](#faq)

---

##  Quick Start

**Get up and running in 5 minutes:**

### Step 1: Update PATH (5 minutes)

Open PowerShell and run:

```powershell
# Add wrapper directory to PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
$newPath = "C:\Users\17175\AppData\Local\Programs;" + $currentPath
[Environment]::SetEnvironmentVariable("Path", $newPath, "User")
```

### Step 2: Restart VSCode (2 minutes)

- Close **ALL** VSCode windows
- Relaunch VSCode

### Step 3: Verify (1 minute)

Open integrated terminal and run:
```bash
where connascence
```

**Expected output** (wrapper should be FIRST):
```
C:\Users\17175\AppData\Local\Programs\connascence.bat
C:\Users\17175\AppData\Roaming\Python\Python312\Scripts\connascence.exe
```

### Step 4: Test Extension (2 minutes)

1. Open any Python file
2. Press `Ctrl+Alt+A` (Analyze Current File)
3. Check the **Problems panel** (bottom) for violations
4. Look for **colored squiggles** in the editor:
   -  **Red** = Critical violations
   -  **Yellow** = High severity warnings
   -  **Blue** = Medium info
   -  **Gray** = Low hints

** If you see violations, you're ready to go!**

---

##  What is This?

The **VSCode Connascence Analyzer Extension** is a real-time code quality analyzer that detects:

- **Duplicate Code**: Algorithm similarities, copy-paste violations
- **God Objects**: Classes that do too much
- **NASA POT10 Compliance**: Defense industry code standards
- **MECE Violations**: Mutually Exclusive, Collectively Exhaustive patterns
- **Connascence Patterns**: Code coupling and dependencies

### Key Features:

 **Real-Time Analysis** - Detects issues as you type (1s debounce)
 **Color-Coded Violations** - Red/Yellow/Blue/Gray squiggles by severity
 **Quick Fixes** - Press `Ctrl+.` for refactoring suggestions
 **Quality Dashboard** - Visual metrics and trends (`Ctrl+Alt+D`)
 **19 Commands** - Comprehensive analysis toolset
 **Multi-Language** - Python, C, C++, JavaScript, TypeScript

---

##  Installation

### Prerequisites:

1. **VSCode Extension** (already installed):
   - Location: `C:\Users\17175\.vscode\extensions\connascence-systems.connascence-safety-analyzer-2.0.2`

2. **Python CLI** (already installed):
   - Package: `spek-connascence-analyzer 2.0.0`
   - Location: `C:\Users\17175\AppData\Roaming\Python\Python312\Scripts\connascence.exe`

3. **Wrapper Script v2.0.0** (Security Hardened):
   - Files: `connascence-wrapper.bat`, `connascence.bat`
   - Location: `C:\Users\17175\AppData\Local\Programs\`
   - Security Features: Command injection protection, dynamic paths, input validation

### What's Already Done:

-  Extension installed in VSCode
-  Python CLI operational
-  Wrapper v2.0.0 deployed with security hardening
-  5 Python syntax errors fixed
-  All security vulnerabilities resolved (CVSS 8.1  0)

### What You Need to Do:

1. **Update PATH** (see Quick Start Step 1)
2. **Restart VSCode** (see Quick Start Step 2)
3. **Test Extension** (see Quick Start Step 4)

---

##  Configuration

###  Visual Highlights vs Squiggles (NEW!)

**Problem**: Many linters (ESLint, Pylint) use squiggles, causing visual overlap.

**Solution**: Enable **color highlights with emojis** instead!

**Quick Setup** (Copy to `settings.json`):
```json
{
  // Enable visual highlighting (background colors + emojis)
  "connascence.enableVisualHighlighting": true,
  "connascence.highlightingIntensity": "normal",  // "subtle" | "normal" | "bright"
  "connascence.showEmojis": true,

  // Reduce squiggles to hints (avoid linter overlap)
  "connascence.severityMap": {
    "critical": "hint",  // Gray instead of red
    "high": "hint",      // Gray instead of yellow
    "medium": "hint",
    "low": "hint"
  }
}
```

**Or use our ready-made config**: Copy `.vscode/connascence-highlights.json`  `settings.json`

**See**: `.claude/.artifacts/VISUAL-HIGHLIGHTING-GUIDE.md` for complete details

### VSCode Settings

The extension is pre-configured with these settings:

```json
{
  "connascence.safetyProfile": "modern_general",
  "connascence.realTimeAnalysis": true,
  "connascence.debounceMs": 1000,
  "connascence.grammarValidation": true,
  "connascence.nasaComplianceThreshold": 0.95,
  "connascence.meceQualityThreshold": 0.85
}
```

### Available Safety Profiles:

| Profile | Description | Use Case |
|---------|-------------|----------|
| `modern_general` | Balanced modern practices (DEFAULT) | General development |
| `nasa-compliance` | NASA POT10 strict rules | Defense industry |
| `strict` | Strictest quality enforcement | High-reliability systems |
| `standard` | Standard quality checks | Business applications |
| `lenient` | Relaxed thresholds | Prototyping, learning |
| `nasa_jpl_pot10` | JPL Power of Ten | Space/aviation software |

### Changing Settings:

**Via VSCode UI**:
1. File  Preferences  Settings
2. Search for "connascence"
3. Change settings as needed

**Via settings.json**:
```json
{
  "connascence.safetyProfile": "strict",
  "connascence.realTimeAnalysis": true,
  "connascence.debounceMs": 500
}
```

---

##  Using the Extension

### 19 Available Commands

Press `Ctrl+Shift+P` and type "Connascence" to see all commands:

#### Analysis Commands

| Command | Shortcut | Description |
|---------|----------|-------------|
| Analyze Current File | `Ctrl+Alt+A` | Analyze the active file |
| Analyze Workspace | `Ctrl+Alt+W` | Analyze entire workspace |
| Analyze Selection | `Ctrl+Alt+S` | Analyze selected code |
| Re-analyze All Files | - | Refresh all analysis |

#### Refactoring Commands

| Command | Shortcut | Description |
|---------|----------|-------------|
| Suggest Refactoring | `Ctrl+Alt+R` | Get refactoring suggestions |
| Quick Fix | `Ctrl+.` | Apply quick fixes |
| Extract Method | - | Extract duplicate code |

#### Visualization Commands

| Command | Shortcut | Description |
|---------|----------|-------------|
| Show Dashboard | `Ctrl+Alt+D` | Open quality dashboard |
| Show Metrics | - | Display code metrics |
| Show Trends | - | View quality trends |

#### Configuration Commands

| Command | Shortcut | Description |
|---------|----------|-------------|
| Change Safety Profile | - | Switch analysis profile |
| Configure Thresholds | - | Adjust quality gates |
| Toggle Real-Time | - | Enable/disable auto-analysis |

#### Utility Commands

| Command | Shortcut | Description |
|---------|----------|-------------|
| Export Report | - | Export analysis to JSON/SARIF |
| Clear Cache | - | Clear analysis cache |
| Show Output | - | Open extension output log |

### Context Menu Integration

Right-click in editor:
- **Analyze Current File** - Quick analysis
- **Suggest Refactoring** - Get improvement ideas
- **Show Connascence Graph** - Visualize dependencies

---

##  Features

### 1. Real-Time Analysis

**How it works**:
- File watcher monitors your edits
- Analysis triggers 1 second after you stop typing
- Results appear in Problems panel
- Squiggles update in real-time

**Configuration**:
```json
{
  "connascence.realTimeAnalysis": true,
  "connascence.debounceMs": 1000  // Delay in milliseconds
}
```

### 2. Color-Coded Violations

**Severity Mapping**:

| Severity | Color | Visual | Meaning |
|----------|-------|--------|---------|
| **Critical** |  Red | Squiggly underline | Must fix immediately |
| **High** |  Yellow | Squiggly underline | Should fix soon |
| **Medium** |  Blue | Squiggly underline | Plan to fix |
| **Low** |  Gray | Dotted underline | Nice to fix |

**Example**:
```python
def calculate_area(length, width):
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  Critical: Duplicate algorithm
    result = length * width
    return result
```

### 3. Hover Tooltips

**Hover over any squiggle** to see:
- Violation description
- Severity and type
- Similar code locations
- Refactoring recommendation
- Similarity score

**Example**:
```
 Connascence: Duplicate Algorithm

Severity: Critical
Type: algorithm_duplication
Method: COA Algorithm

Description:
Found 2 functions with identical algorithm patterns

Files Involved:
- utils.py (lines 10-15)
- helpers.py (lines 34-39)

Recommendation:
Extract common logic into shared utility function

Similarity Score: 95%
```

### 4. Quick Fixes

**Press `Ctrl+.` on any violation** to get:
- Automatic refactoring options
- Extract method suggestions
- Rename variable recommendations
- Import optimization

**Example**:
```python
# Duplicate code detected:
def foo():
    x = 1
    return x * 2

def bar():
    y = 1
    return y * 2

# Quick Fix options:
# 1. Extract method 'multiply_by_two'
# 2. Create shared utility function
# 3. Inline duplicate logic
```

### 5. Quality Dashboard

**Press `Ctrl+Alt+D`** to open:
- Quality score meter (0.0-1.0)
- Violation breakdown by severity
- Trend charts (quality over time)
- File hotspots (most violations)
- Recommendation priority list

**Metrics displayed**:
- Total violations
- Critical count
- Quality score
- NASA compliance %
- MECE quality %
- Average code similarity

### 6. Tree View Panel

**Left sidebar panel** shows:
- Violations organized by file
- Color-coded icons by severity
- Click to jump to violation
- Filter by severity/type

**Filters**:
- Show only critical
- Show only duplications
- Show only NASA violations
- Show only god objects

### 7. Code Lens

**Inline metrics** above functions/classes:
```python
#  2 duplicates | 85% similarity | 5 violations
def process_data(data):
    ...
```

Click metrics to:
- See all violations
- Get refactoring suggestions
- View similarity analysis

---

##  Troubleshooting

### Issue 1: Extension Commands Don't Work

**Symptom**: Pressing `Ctrl+Alt+A` does nothing

**Diagnosis**:
```bash
# Check if wrapper is found first
where connascence
```

**Expected**:
```
C:\Users\17175\AppData\Local\Programs\connascence.bat   Must be FIRST
C:\Users\17175\AppData\Roaming\Python\Python312\Scripts\connascence.exe
```

**Fix**:
1. Update PATH (see Quick Start Step 1)
2. Restart VSCode completely
3. Test again

### Issue 2: No Violations Shown

**Symptom**: Analysis runs but Problems panel is empty

**Diagnosis**:
```bash
# Test CLI directly
cd "C:\Users\17175\AppData\Local\Programs"
connascence-wrapper.bat analyze test.py --profile modern_general --format json
```

**Expected**: JSON output with violations

**Fix**:
- If CLI fails: Check Python installation
- If CLI works: Check VSCode output log (View  Output  Connascence)
- If no output: Restart extension (Ctrl+Shift+P  "Reload Window")

### Issue 3: Real-Time Analysis Not Working

**Symptom**: Violations don't update when editing

**Check Settings**:
```json
{
  "connascence.realTimeAnalysis": true,  // Must be true
  "connascence.debounceMs": 1000        // Try lowering to 500
}
```

**Verify File Watcher**:
1. Make a change
2. Save file (Ctrl+S)
3. Wait 1 second
4. Check if Problems panel updates

### Issue 4: Wrapper Not Found

**Symptom**: `connascence: command not found`

**Check Files Exist**:
```bash
dir "C:\Users\17175\AppData\Local\Programs\connascence*.bat"
```

**Expected**:
```
connascence.bat
connascence-wrapper.bat (v2.0.0 Security Hardened - 260 lines)
```

**Verify Wrapper Version**:
```bash
connascence-wrapper.bat --wrapper-version
```

**Expected Output**:
```
VSCode Connascence Wrapper v2.0.0 (Security Hardened)
CLI Executable: C:\Users\17175\AppData\Roaming\Python\Python312\Scripts\connascence.exe
```

**Fix**: Re-create wrapper files (see Installation section)

### Issue 5: Security/Injection Warnings

**Symptom**: `[ERROR] Invalid policy profile` or `[ERROR] Invalid output format`

**Cause**: Wrapper v2.0.0 implements strict whitelisting for security

**Valid Policies**:
- `modern_general`, `strict`, `lenient`, `nasa-compliance`, `standard`
- `nasa_jpl_pot10`, `pot10`, `basic`, `core`, `default`
- `experimental`, `general_safety_strict`, `jpl`, `loose`, `nasa`, `power-of-ten`

**Valid Formats**:
- `json`, `yaml`, `sarif`, `text`

**Fix**: Use only whitelisted values (protection against command injection)

### Issue 6: Debug Mode

**Enable Wrapper Debug Logging**:
```bash
set CONNASCENCE_DEBUG=1
connascence-wrapper.bat analyze test.py --profile strict --format json
```

**Debug Output Shows**:
- Wrapper version
- Input arguments
- Translated command
- CLI path used
- Exit code

### Issue 7: Parse Errors

**Symptom**: `Warning: Could not parse file.py`

**Common Causes**:
1. Syntax errors in Python file
2. Invalid Python syntax
3. Mismatched parentheses/brackets

**Check Syntax**:
```bash
python -m py_compile file.py
```

**Fix**: Correct syntax errors, then re-analyze

### Issue 6: Slow Performance

**Symptom**: Analysis takes >30 seconds

**Check File Size**:
- Small (<1000 LOC): Should be <2s
- Medium (1000-5000 LOC): Should be <5s
- Large (5000+ LOC): Should be <10s

**Optimization**:
```json
{
  "connascence.debounceMs": 2000,  // Increase delay
  "connascence.excludePatterns": [
    "**/*.test.py",
    "**/vendor/**"
  ]
}
```

---

##  Architecture

### Integration Flow

```
User Edit in VSCode
    
File Watcher (1s debounce)
    
Extension Triggers Analysis
    
spawn('connascence', ['analyze', file, '--profile', X, '--format', 'json'])
    
Windows PATH Resolution
    
Wrapper Script (C:\...\Local\Programs\connascence.bat)
    
Argument Translation
     analyze file --profile X  --path file --policy X
Python CLI (connascence.exe)
    
Analysis Engine (25,640 LOC Python)
    
JSON Results
    
Extension Diagnostics Provider
    
VSCode Problems Panel + Squiggles
```

### Component Details

**1. VSCode Extension (TypeScript)**
- Location: `.vscode/extensions/connascence-systems.connascence-safety-analyzer-2.0.2`
- Size: 3.49 MB
- Main files:
  - `extension.js` - Entry point
  - `connascenceService.js` - CLI integration
  - `diagnosticsProvider.js` - Problem visualization
  - `codeActionsProvider.js` - Quick fixes

**2. Wrapper Script v2.0.0 (Batch) - Security Hardened**
- Location: `C:\Users\17175\AppData\Local\Programs\`
- Files: `connascence-wrapper.bat` (260 lines), `connascence.bat`
- Purpose: Translate extension CLI args + security validation
- Security Features:
  -  Command injection protection (argument whitelisting)
  -  Dynamic path resolution (no hardcoded paths)
  -  Input validation (policies, formats, file existence)
  -  DoS prevention (max 30 arguments)
  -  Special character escaping (&, |, <, >)
  -  Support for --arg=value format
- Version Check: `connascence-wrapper.bat --wrapper-version`

**3. Python CLI**
- Package: `spek-connascence-analyzer 2.0.0`
- Executable: `connascence.exe`
- Analysis engine: 25,640 LOC
- Detectors: 9 specialized modules

### Analysis Methods

**1. COA Algorithm** (Code Algorithm Analysis)
- Detects duplicate algorithms
- Ignores variable names
- 70% similarity threshold

**2. MECE Similarity**
- Finds copy-paste code
- Exact text matching
- Reports 100% duplicates

**3. NASA POT10 Compliance**
- Power of Ten rules
- Defense industry standards
- 95% compliance threshold

**4. God Object Detection**
- Class complexity analysis
- 500+ LOC or 50+ methods
- Recommends decomposition

---

##  Development

### Building from Source

**Prerequisites**:
- Node.js 16+
- Python 3.12+
- TypeScript 4.5+

**Build Extension**:
```bash
cd .vscode/extensions/connascence-systems.connascence-safety-analyzer-2.0.2
npm install
npm run compile
vsce package
code --install-extension connascence-safety-analyzer-2.0.2.vsix
```

**Build Python CLI**:
```bash
cd C:\Users\17175\Desktop\connascence
pip install -e .
pytest tests/
```

### Testing

**Test Wrapper**:
```bash
cd tests/wrapper-integration
.\wrapper-test-suite.ps1  # PowerShell (28 tests)
.\wrapper-test-suite.bat  # Batch (24 tests)
```

**Test Extension**:
1. Press F5 in VSCode (Extension Development Host)
2. Open Python file
3. Test all commands

**Dogfooding**:
```bash
# Analyze analyzer itself
connascence --path C:\Users\17175\Desktop\connascence\analyzer --policy strict --format json
```

### Debugging

**Enable Debug Logging**:
```json
{
  "connascence.debug": true,
  "connascence.logLevel": "verbose"
}
```

**Check Logs**:
- Extension log: View  Output  Connascence
- CLI log: `%TEMP%\connascence-debug.log`
- Wrapper log: `C:\Users\17175\AppData\Local\Programs\wrapper.log`

---

##  FAQ

### Q: Does this work on Linux/Mac?

**A**: Currently Windows-only (`.bat` wrapper). Cross-platform support planned.

**Workaround**: Use Python CLI directly:
```bash
connascence --path file.py --policy modern_general --format json
```

### Q: Can I use different Python versions?

**A**: Yes! Wrapper v2.0.0 automatically detects Python installations.

**How it works**:
1. Searches PATH for `connascence.exe`
2. Fallback to Python 3.12 (if exists)
3. Fallback to Python 3.11 (if exists)

**Supported**: Python 3.11, 3.12
**No manual configuration needed** - dynamic path resolution!

### Q: How do I disable real-time analysis?

**A**: Update VSCode settings:
```json
{
  "connascence.realTimeAnalysis": false
}
```

Then manually trigger with `Ctrl+Alt+A`.

### Q: Can I analyze non-Python files?

**A**: Yes! Supports:
- Python (.py)
- C (.c, .h)
- C++ (.cpp, .hpp)
- JavaScript (.js)
- TypeScript (.ts)

### Q: How do I export results?

**A**: Use Export Report command:
1. `Ctrl+Shift+P`
2. "Connascence: Export Report"
3. Choose format (JSON/SARIF)
4. Select output location

### Q: What's the quality score calculation?

**A**:
```
Quality Score = 1.0 - (Total Violations  Severity Weights) / Max Possible
```

Severity weights:
- Critical: 1.0
- High: 0.7
- Medium: 0.4
- Low: 0.1

### Q: How do I customize violation severity?

**A**: Create `.connascence.json` in project root:
```json
{
  "severityOverrides": {
    "duplicate_code": "medium",
    "god_object": "critical"
  }
}
```

### Q: Can I ignore specific violations?

**A**: Use inline comments:
```python
# connascence-ignore: duplicate_code
def my_function():
    ...
```

Or add to `.connascence.json`:
```json
{
  "ignore": [
    "tests/**",
    "**/generated/**"
  ]
}
```

---

##  Additional Resources

### Documentation:
- **Integration Report**: `.claude/.artifacts/FINAL-INTEGRATION-REPORT.md`
- **Test Results**: `.claude/.artifacts/VSCODE-EXTENSION-TEST-RESULTS.md`
- **Security Audit**: `.claude/.artifacts/SECURITY-AUDIT-REPORT.md`
- **Security Validation**: `.claude/.artifacts/SECURITY-WRAPPER-VALIDATION-REPORT.md` 
- **Security Changelog**: `.claude/.artifacts/WRAPPER-SECURITY-CHANGELOG.md` 
- **Specialist Findings**: `.claude/.artifacts/SPECIALIST-AGENTS-FINAL-REPORT.md`
- **Dogfooding Report**: `.claude/.artifacts/DOGFOODING-VALIDATION-REPORT.md`

### Security (Wrapper v2.0.0):
-  **CVSS 8.1** Command injection  BLOCKED (whitelisting)
-  **CVSS 7.3** Hardcoded paths  FIXED (dynamic resolution)
-  **CVSS 6.5** Path traversal  BLOCKED (file validation)
-  **CVSS 5.0** DoS attacks  PREVENTED (max 30 args)
-  **Security Score**: 95/100 (Production Ready)

### Support:
- GitHub Issues: [Report bugs/features]
- Documentation: [Full technical docs]
- Examples: `tests/wrapper-integration/test-files/`

### Performance Benchmarks:
- Small files (8 LOC): 450ms
- Medium files (500 LOC): 550ms
- Large files (1500 LOC): 650ms
- Workspace (72 files, 25,640 LOC): 15.4s

---

##  Quick Reference Card

### Essential Commands:
```bash
# Analyze file
Ctrl+Alt+A

# Analyze workspace
Ctrl+Alt+W

# Quick fix
Ctrl+.

# Show dashboard
Ctrl+Alt+D

# Test wrapper
where connascence

# Direct CLI
connascence --path file.py --policy modern_general --format json
```

### Status Check:
```bash
# 1. Verify PATH
where connascence
# Expected: C:\...\Local\Programs\connascence.bat (FIRST)

# 2. Test wrapper
connascence-wrapper.bat --version

# 3. Test CLI
connascence --help
```

### Emergency Reset:
```powershell
# Remove wrapper from PATH
$path = [Environment]::GetEnvironmentVariable("Path", "User")
$newPath = $path -replace 'C:\\Users\\17175\\AppData\\Local\\Programs;', ''
[Environment]::SetEnvironmentVariable("Path", $newPath, "User")

# Restart VSCode
```

---

**Version**: 2.0.2
**Last Updated**: 2025-09-23
**Status**:  Production Ready (after PATH update)

**Quick Start**: Update PATH  Restart VSCode  Press Ctrl+Alt+A  Start analyzing!