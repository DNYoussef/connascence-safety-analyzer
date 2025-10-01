# Connascence Safety Analyzer for VSCode

NASA-grade software quality analysis with enterprise-proven connascence detection directly in your IDE.

## Features

- **Real-time Analysis**: Get instant feedback on connascence violations as you type
- **9 Connascence Types**: Comprehensive detection of all coupling patterns
- **NASA Compliance**: Power of Ten safety rules for mission-critical software
- **Auto-fix Support**: One-click fixes for common violations
- **Inline Hints**: See recommendations directly in your code
- **Customizable Policies**: Choose from NASA, Strict, Standard, or Lenient

## Installation

1. Install from VSCode Marketplace: Search for "Connascence Safety Analyzer"
2. Or install manually: `code --install-extension connascence-analyzer-1.0.0.vsix`

## Usage

### Commands

- `Connascence: Analyze` - Analyze current file
- `Connascence: Show Report` - View detailed analysis report
- `Connascence: Fix Violations` - Apply automatic fixes
- `Connascence: Configure` - Set analysis policy

### Configuration

```json
{
  "connascence.policy": "standard",
  "connascence.enableRealTime": true,
  "connascence.showInlineHints": true,
  "connascence.autoFix": false,
  "connascence.mcpServerPort": 8765
}
```

## Policies

- **nasa-compliance**: Strictest - NASA Power of Ten rules
- **strict**: High standards for production code
- **standard**: Balanced for most projects (default)
- **lenient**: Permissive for prototypes

## Requirements

- Python 3.8+ with connascence-analyzer installed
- VSCode 1.85.0+

## Support

- [Documentation](https://docs.connascence.io)
- [GitHub Issues](https://github.com/connascence/vscode-extension/issues)
- [Discord Community](https://discord.gg/connascence)