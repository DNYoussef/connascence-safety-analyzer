# Connascence Analyzer - Quick Start Guide

## 🚀 30-Second Setup

```bash
# 1. Build
cd integrations/vscode
npm install && npm run compile

# 2. Package
npm install -g @vscode/vsce
vsce package

# 3. Install
code --install-extension connascence-analyzer-1.0.0.vsix

# 4. Restart VSCode
```

## 📍 Finding the Extension

**Look for the Connascence icon in the Activity Bar** (left sidebar):
- It appears below the Source Control icon
- Click it to open the sidebar with 3 panels

## 🎯 Quick Test

1. Open any Python file
2. Click **Connascence icon** in Activity Bar
3. Click **"Analyze Current File"** in Quick Actions panel
4. See violations appear in Violations panel
5. Click a violation to jump to that location

## 📊 Three Panels

### 1. Violations
- Shows all code quality issues
- Grouped by severity: Critical → High → Medium → Low
- Click to navigate to violation location
- Right-click for quick fix options

### 2. Quality Metrics
- **Quality Score**: Overall code health (0-100%)
- **Total Violations**: Count of all issues found
- **Files Analyzed**: Number of files processed
- **NASA Compliance**: Power of Ten rules adherence
- **MECE Score**: Duplication analysis score

### 3. Quick Actions
- **Analyze Current File**: Run analysis on active file
- **Show Full Report**: Open detailed HTML report
- **Fix All Violations**: Apply automated fixes
- **Configure Settings**: Change analysis policy

## ⚙️ Configuration

Press `Ctrl+,` (Settings) and search for "Connascence":

```json
{
  "connascence.policy": "standard",           // or "nasa-compliance", "strict", "lenient"
  "connascence.enableRealTime": true,         // Auto-analyze on save
  "connascence.showInlineHints": true,        // Show squiggly underlines
  "connascence.autoFix": false                // Auto-fix on save (use with caution)
}
```

## 🔧 Troubleshooting

**No icon in Activity Bar?**
- Restart VSCode
- Check Extensions view - extension should be enabled
- Run `Developer: Show Running Extensions` to verify activation

**No violations showing?**
- Click "Refresh" button in Violations panel (circular arrow)
- Or run `Connascence: Analyze` from Command Palette (Ctrl+Shift+P)

**Analysis fails?**
- Ensure Python is installed and in PATH
- Check Output panel (View → Output → Connascence Analyzer)
- Verify MCP server is running (see main README)

## 💡 Pro Tips

1. **Keep sidebar open** while coding for real-time visibility
2. **Use Quick Actions** for instant analysis without menu navigation
3. **Click violations** to navigate directly to problem areas
4. **Watch the Quality Score** - aim for 90%+ for production code
5. **Enable real-time analysis** for continuous feedback as you code

## 📚 More Help

- Full installation guide: `INSTALLATION.md`
- Extension architecture: `../../docs/VSCODE_EXTENSION_COMPLETE.md`
- Main project docs: `../../README.md`
- MCP server setup: `../../mcp/README.md`

---

**You're all set!** Start analyzing code and improving quality with just one click on the Connascence icon. 🎉
