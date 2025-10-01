# Connascence Analyzer VSCode Extension - Installation Guide

## Overview

The Connascence Analyzer extension provides real-time code quality analysis with:
- **Activity Bar Sidebar** with three panels:
  - Violations Explorer (grouped by severity)
  - Quality Metrics Dashboard
  - Quick Actions Panel
- Real-time diagnostics as you type
- One-click fixes for violations
- NASA Power of Ten compliance checking
- MECE duplication detection

## Features

### Activity Bar Integration
- Custom icon in the VSCode activity bar (left sidebar)
- Three integrated panels:
  1. **Violations** - Browse violations by severity, click to navigate
  2. **Quality Metrics** - View quality score, NASA compliance, MECE score
  3. **Quick Actions** - One-click access to analysis commands

### Commands Available
- `Connascence: Analyze` - Analyze current file
- `Connascence: Show Report` - View full HTML report
- `Connascence: Fix Violations` - Apply automated fixes
- `Connascence: Configure` - Change analysis policy

## Installation Steps

### Step 1: Build the Extension

```bash
cd integrations/vscode
npm install
npm run compile
```

### Step 2: Package the Extension

```bash
# Install vsce (VSCode Extension packaging tool)
npm install -g @vscode/vsce

# Package the extension
vsce package
```

This creates a `.vsix` file (e.g., `connascence-analyzer-1.0.0.vsix`)

### Step 3: Install in VSCode

**Option A: From VSCode UI**
1. Open VSCode
2. Go to Extensions view (Ctrl+Shift+X / Cmd+Shift+X)
3. Click the "..." menu (top right)
4. Select "Install from VSIX..."
5. Choose the generated `.vsix` file

**Option B: From Command Line**
```bash
code --install-extension connascence-analyzer-1.0.0.vsix
```

### Step 4: Verify Installation

1. Restart VSCode
2. You should see a new **Connascence icon** in the Activity Bar (left sidebar)
3. Click the icon to see three panels:
   - Violations
   - Quality Metrics
   - Quick Actions

## Configuration

Open VSCode Settings (Ctrl+, / Cmd+,) and search for "Connascence":

```json
{
  "connascence.policy": "standard",
  "connascence.enableRealTime": true,
  "connascence.showInlineHints": true,
  "connascence.autoFix": false,
  "connascence.mcpServerPort": 8765
}
```

### Policy Options
- `nasa-compliance` - Strict NASA Power of Ten rules
- `strict` - High sensitivity to violations
- `standard` - Balanced analysis (default)
- `lenient` - Relaxed rules for prototyping

## Usage

### Using the Sidebar

1. **Click the Connascence icon** in the Activity Bar
2. **Violations Panel**:
   - Shows violations grouped by severity (Critical, High, Medium, Low)
   - Click any violation to jump to that location in code
   - Right-click for quick fix options
3. **Quality Metrics Panel**:
   - Quality Score percentage
   - Total violations count
   - Files analyzed
   - NASA Compliance score
   - MECE score
4. **Quick Actions Panel**:
   - Analyze Current File
   - Show Full Report
   - Fix All Violations
   - Configure Settings

### Using Commands

Press `Ctrl+Shift+P` / `Cmd+Shift+P` and type:
- `Connascence: Analyze`
- `Connascence: Show Report`
- `Connascence: Fix Violations`
- `Connascence: Configure`

### Real-Time Analysis

With `enableRealTime: true`, analysis runs automatically:
- As you type (with debouncing)
- When you save files
- Violations appear as squiggly underlines
- Hover for details and fix suggestions

## Testing the Extension

### Quick Test

1. Open a Python file with coupling issues:
```python
# test.py
def process_data(data):
    if data[0] == "special":  # Connascence of Position
        return data[1]        # Connascence of Position
    return None
```

2. Click the **Connascence icon** in the Activity Bar
3. Click **"Analyze Current File"** in Quick Actions
4. See violations appear in the Violations panel
5. Click a violation to jump to that line
6. View quality metrics in the Metrics panel

### Full Integration Test

1. Clone a sample project:
```bash
git clone https://github.com/celery/celery
cd celery
code .
```

2. Open any Python file
3. Click Connascence icon in Activity Bar
4. Run analysis from Quick Actions
5. Explore violations in the sidebar
6. Click violations to navigate
7. View metrics dashboard

## Troubleshooting

### Extension Not Appearing in Activity Bar

**Solution**: Check that the extension is activated:
1. Open Command Palette (Ctrl+Shift+P)
2. Run "Developer: Show Running Extensions"
3. Search for "Connascence Analyzer"
4. Check activation status

### No Violations Showing

**Solution**: Run manual analysis:
1. Click Connascence icon in Activity Bar
2. Click "Refresh" button (circular arrow) in Violations panel
3. Or run "Connascence: Analyze" command

### Icon Not Displaying

**Solution**: The icon.svg must be in the correct location:
```
integrations/vscode/resources/icon.svg
```

If missing, the extension will use a default icon.

### MCP Server Connection Issues

**Solution**: Check MCP server is running:
```bash
# Start MCP server
cd ../../
python -m mcp.server

# Check port (default 8765)
netstat -an | grep 8765
```

Update port in settings if needed:
```json
{
  "connascence.mcpServerPort": 8765
}
```

## Uninstallation

1. Open Extensions view (Ctrl+Shift+X)
2. Find "Connascence Safety Analyzer"
3. Click "Uninstall"
4. Restart VSCode

Or from command line:
```bash
code --uninstall-extension connascence.connascence-analyzer
```

## Development

### Running in Debug Mode

1. Open `integrations/vscode` in VSCode
2. Press F5 to launch Extension Development Host
3. New VSCode window opens with extension loaded
4. Test features in the new window
5. Console logs appear in original window's Debug Console

### Making Changes

1. Edit TypeScript files in `src/`
2. Run `npm run compile` to rebuild
3. Reload Extension Development Host (Ctrl+R / Cmd+R)
4. Test changes

### Debugging

- Set breakpoints in TypeScript files
- Press F5 to start debugging
- Debug Console shows logs and errors
- Use `console.log()` for debugging output

## Support

- GitHub Issues: https://github.com/yourusername/connascence/issues
- Documentation: See `README.md` in project root
- MCP Server: See `mcp/README.md` for server setup

## Next Steps

1. ✅ Install extension
2. ✅ Configure policy settings
3. ✅ Run analysis on sample code
4. ✅ Explore sidebar panels
5. 📝 Review violations and improve code quality
6. 🎯 Aim for 90%+ quality score!

---

**Pro Tip**: Keep the Connascence sidebar open while coding for continuous visibility into code quality. Use the Quick Actions panel for instant analysis without interrupting your workflow!
