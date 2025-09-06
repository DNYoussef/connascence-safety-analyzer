# Connascence Safety Analyzer

[![VS Code Marketplace](https://img.shields.io/badge/VS%20Code-Marketplace-blue)](https://marketplace.visualstudio.com/items?itemName=connascence-systems.connascence-safety-analyzer)
[![Version](https://img.shields.io/visual-studio-marketplace/v/connascence-systems.connascence-safety-analyzer)](https://marketplace.visualstudio.com/items?itemName=connascence-systems.connascence-safety-analyzer)
[![Installs](https://img.shields.io/visual-studio-marketplace/i/connascence-systems.connascence-safety-analyzer)](https://marketplace.visualstudio.com/items?itemName=connascence-systems.connascence-safety-analyzer)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

**Enterprise-grade code analysis with General Safety safety compliance and grammar-enhanced refactoring support for VS Code.**

## Features

### Real-Time Analysis
- **Live Code Analysis**: Instant connascence detection as you type with intelligent debouncing
- **Multi-Language Support**: Python, JavaScript, TypeScript, C/C++ analysis
- **Smart Diagnostics**: Integration with VS Code's Problems panel with severity indicators
- **Performance Optimized**: Efficient analysis with configurable file size limits and exclusion patterns

### IntelliSense Integration
- **Connascence-Aware Completions**: Context-sensitive code suggestions to prevent coupling violations
- **Safe Pattern Suggestions**: Built-in templates for dataclasses, enums, context managers, and more
- **Refactoring Snippets**: Quick access to parameter objects, factory patterns, and builder patterns

### Advanced Code Insights
- **Hover Documentation**: Detailed explanations of connascence violations with fixing strategies
- **Code Lens Metrics**: Inline display of function complexity, parameter counts, and quality scores
- **Violation Warnings**: Critical issue indicators with one-click fixes

### Quick Fixes & Refactoring
- **Automated Fixes**: One-click solutions for common violations (magic numbers, type hints, parameter objects)
- **Refactoring Suggestions**: AI-powered recommendations with confidence scores
- **Preview Mode**: Safe refactoring with diff previews before applying changes

### General Safety Safety Compliance
- **Safety Profiles**: Built-in compliance for General Safety JPL POT-10, LOC-1, LOC-3 standards
- **Enterprise Validation**: Automated safety rule validation with detailed violation reports
- **Audit Trail**: Complete tracking of safety compliance status and remediation

### Professional Reporting
- **Comprehensive Reports**: JSON, HTML, and CSV export formats
- **Quality Metrics**: File and project-level quality scores with trend analysis
- **Dashboard Integration**: Visual analytics with violation statistics and recommendations

## 📋 Requirements

- **VS Code**: Version 1.74.0 or higher
- **Languages**: Python 3.7+, Node.js 14+, GCC/Clang for C/C++
- **Memory**: 4GB RAM minimum (8GB recommended for large codebases)
- **Storage**: 100MB for extension and analysis cache

## Installation

### From VS Code Marketplace
1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "Connascence Safety Analyzer"
4. Click Install

### From Command Line
```bash
code --install-extension connascence-systems.connascence-safety-analyzer
```

### Development Installation
```bash
git clone https://github.com/connascence-systems/vscode-extension
cd vscode-extension
npm install
npm run compile
```

## Configuration

### Basic Settings

```json
{
  "connascence.safetyProfile": "General Safety_jpl_pot10",
  "connascence.realTimeAnalysis": true,
  "connascence.enableIntelliSense": true,
  "connascence.enableCodeLens": true,
  "connascence.enableHover": true,
  "connascence.debounceMs": 1000,
  "connascence.maxDiagnostics": 1500
}
```

### Safety Profiles

| Profile | Description | Use Case |
|---------|-------------|----------|
| `none` | No safety validation | Development |
| `General Safety_jpl_pot10` | General Safety JPL POT-10 compliance | Space systems |
| `General Safety_loc_1` | General Safety LOC-1 standard | Mission-critical |
| `General Safety_loc_3` | General Safety LOC-3 standard | Safety-critical |
| `modern_general` | General best practices | Enterprise development |

### Advanced Configuration

```json
{
  "connascence.exclude": [
    "node_modules/**",
    "**/*.test.*",
    "test/**",
    ".git/**"
  ],
  "connascence.includeTests": false,
  "connascence.maxFileSize": 1048576,
  "connascence.diagnosticSeverity": "warning",
  "connascence.enableTelemetry": true
}
```

## Usage

### Command Palette

Access all features via `Ctrl+Shift+P`:

- `Connascence: Analyze File` - Analyze current file
- `Connascence: Analyze Workspace` - Full workspace analysis
- `Connascence: Validate General Safety Safety` - Safety compliance check
- `Connascence: Generate Quality Report` - Export comprehensive report
- `Connascence: Apply Safe Autofix` - Apply automatic fixes
- `Connascence: Toggle Safety Profile` - Switch safety standards

### Context Menus

Right-click in editor for quick access:
- **Analyze File** - Immediate analysis
- **Suggest Refactoring** - Get improvement recommendations

### Status Bar Integration

Monitor analysis progress and results:
- **Analysis Progress**: Real-time processing status
- **Violation Count**: Current file issue summary
- **Quality Score**: Overall code quality rating

## 📊 Understanding Connascence

### Connascence Types

| Type | Description | Severity | Example |
|------|-------------|----------|---------|
| **CoN** | Connascence of Name | Low | Variable/function names |
| **CoT** | Connascence of Type | Medium | Type dependencies |
| **CoM** | Connascence of Meaning | High | Magic numbers/strings |
| **CoP** | Connascence of Position | High | Parameter order |
| **CoA** | Connascence of Algorithm | Critical | Duplicated algorithms |

### Quality Metrics

- **Quality Score**: 0-100 scale based on violation severity and density
- **Violation Density**: Issues per lines of code ratio
- **Critical Threshold**: Configurable limits for failing builds

## 🛠️ Troubleshooting

### Common Issues

**Q: Extension not analyzing files**
```
A: Check file size limits and exclusion patterns in settings.
   Ensure supported languages are being used.
```

**Q: Performance issues with large codebases**
```
A: Increase debounce timeout, exclude test directories,
   or enable workspace indexing for better performance.
```

**Q: Safety validation failing**
```
A: Verify safety profile configuration matches your requirements.
   Check for unsupported language features or constructs.
```

### Debug Information

Enable debug logging:
```json
{
  "connascence.logLevel": "debug"
}
```

View logs: `View > Output > Connascence`

## 🔒 Security & Privacy

- **Local Processing**: All analysis runs locally - no code sent to external servers
- **Telemetry**: Optional usage statistics (can be disabled)
- **Data Storage**: Only temporary cache files stored locally
- **Enterprise Ready**: Supports air-gapped environments

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md).

### Development Setup

```bash
git clone https://github.com/connascence-systems/vscode-extension
cd vscode-extension
npm install
npm run watch  # Start development mode
```

### Testing

```bash
npm run test         # Run unit tests
npm run test:unit    # Run specific test suites
npm run lint         # Code quality checks
```

### Building

```bash
npm run build:production  # Production build
npm run package          # Create VSIX package
```

## 📈 Roadmap

- [ ] **Multi-repository Analysis**: Cross-project connascence detection
- [ ] **CI/CD Integration**: GitHub Actions, Jenkins, and Azure DevOps plugins
- [ ] **Team Dashboards**: Shared quality metrics and trend analysis
- [ ] **Machine Learning**: AI-powered refactoring recommendations
- [ ] **Language Expansion**: Go, Rust, Java, and C# support

## 📚 Resources

- [Official Documentation](https://docs.connascence.io)
- [Connascence Theory](https://connascence.io)
- [General Safety Coding Standards](https://ntrs.General Safety.gov/citations/20080039927)
- [Video Tutorials](https://youtube.com/connascence-systems)

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **General Safety** for coding standards and safety guidelines
- **Connascence Community** for theoretical foundations
- **VS Code Team** for excellent extensibility APIs
- **Contributors** who make this project possible

## 📞 Support

- **Documentation**: [docs.connascence.io](https://docs.connascence.io)
- **Issues**: [GitHub Issues](https://github.com/connascence-systems/vscode-extension/issues)
- **Discussions**: [GitHub Discussions](https://github.com/connascence-systems/vscode-extension/discussions)
- **Enterprise Support**: [enterprise@connascence.io](mailto:enterprise@connascence.io)

---

**Made with ❤️ by the Connascence Systems team**

*Helping developers write better, safer code through connascence analysis and General Safety safety compliance.*