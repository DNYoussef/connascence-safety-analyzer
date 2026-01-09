# Connascence Safety Analyzer

[![CI/CD Pipeline](https://github.com/DNYoussef/connascence-safety-analyzer/actions/workflows/ci.yml/badge.svg)](https://github.com/DNYoussef/connascence-safety-analyzer/actions)
[![Quality Gates](https://github.com/DNYoussef/connascence-safety-analyzer/actions/workflows/quality-gates.yml/badge.svg)](https://github.com/DNYoussef/connascence-safety-analyzer/actions)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready static analysis tool that detects and measures connascence (implicit dependencies) in Python codebases. Helps teams reduce coupling, improve maintainability, and build more resilient software.

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI (recommended)
pip install connascence-analyzer

# Or install from source
git clone https://github.com/DNYoussef/connascence-safety-analyzer.git
cd connascence-safety-analyzer
pip install -e ".[dev]"
```

### Basic Usage

```bash
# Analyze a single file
connascence analyze myfile.py

# Analyze entire project
connascence analyze-workspace .

# With safety profile
connascence analyze . --profile strict

# Validate NASA compliance for one file
connascence validate-safety src/flight.py --profile nasa-compliance

# Generate refactoring suggestions for a hotspot line
connascence suggest-refactoring src/utils.py --line 42
```

### CLI verbs at a glance

| Command | Description |
|---------|-------------|
| `analyze <file>` | AST-based connascence analysis for a single file or module |
| `analyze-workspace <root>` | Recursively analyze a workspace (defaults to `*.py` patterns) |
| `validate-safety <file>` | Run a safety profile/NASA compliance check and return structured violations |
| `suggest-refactoring <file>` | Generate prioritized refactoring techniques for the most severe findings |
| `scan` | **Legacy alias** for compatibility – prints a deprecation warning |

### VSCode Extension

Install the **Connascence Safety Analyzer** extension from the VSCode Marketplace for real-time analysis, quick fixes, and interactive diagnostics.

```bash
# Or install from VSIX
cd interfaces/vscode
npm install && npm run package
code --install-extension connascence-safety-analyzer-*.vsix
```

---

## ✨ Features

### Comprehensive Analysis Suite

**7 Integrated Analyzers:**
1. **Connascence Analyzer** - 9 types of implicit coupling detection
2. **NASA Safety Analyzer** - Power of 10 rules compliance (aerospace standards)
3. **MECE Analyzer** - Code organization and logical completeness
4. **Duplication Analyzer** - Semantic similarity and code clone detection
5. **Clarity Linter** - Cognitive load and code readability scoring
6. **Safety Violation Detector** - God objects, parameter bombs, deep nesting
7. **Six Sigma Quality Metrics** - Statistical process control and quality gates

### Core Analysis Capabilities
- **9 Types of Connascence Detection**: CoP, CoN, CoT, CoM, CoA, CoE, CoI, CoV, CoId
- **Real-time Analysis**: Instant feedback as you code (VSCode extension)
- **Intelligent Caching**: 50-90% faster re-analysis through content-based caching
- **Graceful Degradation**: MCP protocol with automatic CLI fallback

### Safety & Compliance
- **Connascence Detection**: 9 types (CoP, CoN, CoT, CoM, CoA, CoE, CoI, CoV, CoId)
- **NASA Power of 10 Rules**: Critical safety standards enforcement (10 rules)
- **MECE Analysis**: Mutually Exclusive, Collectively Exhaustive code organization
- **Duplication Detection**: Semantic similarity and code clone detection
- **Clarity Linting**: Cognitive load analysis with rubric-based scoring
- **Safety Violation Detection**: Parameter bombs, god objects, deep nesting
- **Six Sigma Quality Metrics**: DPMO, CTQ, process capability analysis
- **Configurable Profiles**: Strict, Standard, Lenient, NASA-compliant

### Enterprise Features
- **Parallel Analysis**: Multi-core processing for faster results
- **CI/CD Integration**: GitHub Actions, Jenkins, GitLab CI support
- **SARIF Output**: Security Analysis Results Interchange Format
- **Quality Dashboard**: Visual metrics and trend analysis

### Developer Experience
- **Interactive Welcome Screen**: 3-step quick start wizard (VSCode)
- **CodeLens Annotations**: Inline issue counts and quick actions
- **Auto-fix Suggestions**: Automated refactoring recommendations
- **Comprehensive Documentation**: 2,300+ lines across multiple guides

---

## 🔗 Integration with AI Development Systems

The Connascence Safety Analyzer integrates seamlessly with intelligent AI development systems:

**Context Cascade Cognitive Architecture** - [https://github.com/DNYoussef/context-cascade](https://github.com/DNYoussef/context-cascade)
- **FrozenHarness Integration**: ConnascenceBridge wired into evaluation pipeline
- **7-Analyzer Quality Gate**: sigma_level, dpmo, nasa_compliance, mece_score, theater_risk
- **Telemetry to Memory MCP**: WHO/WHEN/PROJECT/WHY tagged metrics storage
- **Four-Loop Architecture**: Loop 1 (execution), Loop 1.5 (reflection), Loop 2 (quality), Loop 3 (meta-optimization)
- **Quality Gate Enforcement**: 10% penalty on lenient gate failure, hard block on strict failure

**Memory MCP Triple System** - [https://github.com/DNYoussef/memory-mcp-triple-system](https://github.com/DNYoussef/memory-mcp-triple-system)
- Persistent memory with automatic tagging protocol
- Cross-session violation tracking and pattern detection
- Triple-layer retention (24h/7d/30d+)
- Mode-aware context adaptation

**ruv-SPARC Three-Loop System** - [https://github.com/DNYoussef/ruv-sparc-three-loop-system](https://github.com/DNYoussef/ruv-sparc-three-loop-system)
- 86+ specialized agents with SOPs
- Agent access control (14 code quality agents have Connascence access)
- Complete skill and command integration
- Evidence-based prompting techniques

### ConnascenceBridge (Cognitive Architecture Integration)

The `ConnascenceBridge` class provides programmatic access from Python applications:

```python
from connascence_bridge import ConnascenceBridge, ConnascenceResult

bridge = ConnascenceBridge()  # Auto-detects CLI or mock fallback

# Analyze a single file
result: ConnascenceResult = bridge.analyze_file(Path("src/module.py"))

# Analyze entire directory
result: ConnascenceResult = bridge.analyze_directory(Path("src/"))

# Check quality gates
if result.passes_gate(strict=True):
    print(f"Quality PASS - Sigma: {result.sigma_level}, DPMO: {result.dpmo}")
else:
    print(f"Quality FAIL - {result.violations_count} violations")

# Access all metrics
print(f"NASA Compliance: {result.nasa_compliance}")
print(f"MECE Score: {result.mece_score}")
print(f"Theater Risk: {result.theater_risk}")
print(f"Clarity Score: {result.clarity_score}")
```

**Quality Thresholds**:
| Metric | Strict | Lenient |
|--------|--------|---------|
| sigma_level | >= 4.0 | - |
| dpmo | <= 6210 | - |
| nasa_compliance | >= 0.95 | - |
| mece_score | >= 0.80 | - |
| theater_risk | < 0.20 | - |
| critical_violations | == 0 | == 0 |

**MCP Integration Guide**: See [docs/MCP-INTEGRATION.md](docs/MCP-INTEGRATION.md) for complete setup instructions.

---

## 📊 What is Connascence?

Connascence is a taxonomy of software coupling, providing a vocabulary for discussing different types of dependencies. Understanding connascence helps you:

- **Identify hidden dependencies** that make code fragile
- **Reduce coupling** between modules and components
- **Improve maintainability** through explicit design
- **Make better architectural decisions** based on coupling strength

### Connascence Types (Weakest → Strongest)

| Type | Name | Description | Example |
|------|------|-------------|---------|
| **CoN** | Name | Multiple components must agree on names | Variable/function names |
| **CoT** | Type | Multiple components must agree on types | Type signatures |
| **CoM** | Meaning | Multiple components must agree on value meaning | Magic numbers, enums |
| **CoP** | Position | Order of elements matters | Function parameters |
| **CoA** | Algorithm | Components must agree on algorithm | Hashing, serialization |
| **CoE** | Execution | Order of execution matters | Initialization sequences |
| **CoV** | Value | Values must be synchronized | Configuration values |
| **CoI** | Identity | Multiple components reference same entity | Singletons |
| **CoId** | Identity of Operation | Timing matters | Race conditions |

---

## 📁 Project Structure

```
connascence-safety-analyzer/
├── analyzer/                 # Core analysis engine
│   ├── connascence_analyzer.py
│   ├── unified_analyzer.py
│   └── six_sigma/           # Six Sigma integration
├── interfaces/
│   └── vscode/              # VSCode extension (primary)
│       ├── src/
│       │   ├── services/    # MCP client, caching, telemetry
│       │   ├── features/    # Welcome screen, highlighting
│       │   └── test/        # Unit tests (900+ lines, 50+ tests)
│       └── package.json
├── mcp/                     # MCP server implementation
├── tests/                   # Python test suite
│   ├── e2e/                # End-to-end tests
│   ├── integration/        # Integration tests
│   └── fixtures/           # Test fixtures
├── docs/                    # Documentation
│   ├── INSTALLATION.md     # Setup guide (520 lines)
│   ├── DEVELOPMENT.md      # Dev workflow (620 lines)
│   ├── TROUBLESHOOTING.md  # Problem solving (640 lines)
│   └── PRODUCTION_READINESS_REPORT.md
├── scripts/                 # Utility scripts
│   └── generate_quality_dashboard.py
└── .github/workflows/       # CI/CD automation
    ├── ci.yml              # Main CI pipeline
    ├── quality-gates.yml   # Weekly quality checks
    └── release.yml         # Automated releases
```

---

## 🔧 Configuration

### Safety Profiles

Choose a profile based on your needs:

```yaml
# .connascence.yml
profile: standard  # strict | standard | lenient | nasa-compliance

analysis:
  parallel: true
  max_workers: 4
  cache_enabled: true

reporting:
  format: json  # json | html | sarif | markdown
  severity_threshold: medium  # low | medium | high | critical
```

### VSCode Extension Settings

```json
{
  "connascence.safetyProfile": "standard",
  "connascence.realtimeAnalysis": true,
  "connascence.useMCP": false,
  "connascence.debounceMs": 1000,
  "connascence.enableVisualHighlighting": true
}
```

---

## 📖 Documentation

| Guide | Description | Lines |
|-------|-------------|-------|
| [Installation](docs/INSTALLATION.md) | Complete setup guide with troubleshooting | 520 |
| [Development](docs/DEVELOPMENT.md) | Developer workflow and debugging | 620 |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common issues and solutions | 640 |
| [Production Readiness](docs/PRODUCTION_READINESS_REPORT.md) | Deployment status and metrics | 540 |
| [Quick Start](docs/QUICK_START.md) | 5-minute getting started guide | - |

---

## 🧪 Testing

### Run Tests

```bash
# Python tests
pytest tests/

# With coverage
pytest --cov=analyzer --cov=interfaces --cov=mcp tests/

# VSCode extension tests
cd interfaces/vscode
npm test
```

### Test Coverage

- **Python**: 60%+ coverage target
- **TypeScript**: 900+ lines of tests, 50+ test cases
- **E2E Tests**: Critical workflows validated

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Run tests**: `pytest tests/` and `npm test`
5. **Commit**: `git commit -m 'Add amazing feature'`
6. **Push**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Development Setup

```bash
# Clone and install
git clone https://github.com/DNYoussef/connascence-safety-analyzer.git
cd connascence-safety-analyzer
pip install -e ".[dev,test]"

# Install pre-commit hooks
pre-commit install

# Run quality checks
ruff check analyzer/ interfaces/ mcp/
mypy analyzer/ interfaces/ mcp/
```

See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed guidelines.

---

## 📈 Performance

| Metric | Value | Improvement |
|--------|-------|-------------|
| **File Analysis** | 0.1-0.5s (cached) | 10-50x faster |
| **Workspace Analysis** | 5-15s (incremental) | 4-6x faster |
| **Cache Hit Rate** | 50-90% | - |
| **Memory Usage** | <100MB | Optimized |
| **Parallel Speedup** | 2.8-4.4x | Multi-core |

---

## 🛣️ Roadmap

### v2.1 (Next Release)
- [ ] Multi-language support (JavaScript, TypeScript)
- [ ] Enhanced ML-powered pattern detection
- [ ] Real-time collaboration features
- [ ] Cloud-based analysis service

### v2.2 (Future)
- [ ] IntelliJ IDEA plugin
- [ ] GitHub App integration
- [ ] Team dashboard and analytics
- [ ] Custom rule engine

---

## 🏆 Quality Metrics

**Production Status**: ✅ **READY**

- **Tasks Completed**: 23/23 (100%)
- **Test Coverage**: 900+ lines, 50+ tests
- **Documentation**: 2,320+ lines
- **CI/CD**: Fully automated
- **Release Process**: One-click deployment

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Connascence Taxonomy**: [connascence.io](https://connascence.io)
- **NASA Power of 10**: [NASA JPL Coding Standards](https://web.archive.org/web/20111015064908/http://lars-lab.jpl.nasa.gov/JPL_Coding_Standard_C.pdf)
- **Six Sigma Methodology**: Statistical process control and quality management

---

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/DNYoussef/connascence-safety-analyzer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/DNYoussef/connascence-safety-analyzer/discussions)

---

## 🔗 Links

- [VSCode Marketplace](https://marketplace.visualstudio.com/items?itemName=connascence-systems.connascence-safety-analyzer)
- [PyPI Package](https://pypi.org/project/connascence-analyzer/)
- [Documentation](docs/)
- [Changelog](CHANGELOG.md)

---

<div align="center">

**Built with ❤️ for better software**

[⭐ Star us on GitHub](https://github.com/DNYoussef/connascence-safety-analyzer) | [📦 Try it now](docs/INSTALLATION.md) | [📖 Read the docs](docs/)

</div>
