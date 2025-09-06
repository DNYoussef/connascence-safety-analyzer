# System Architecture Overview

## Executive Summary

The Connascence Safety Analyzer is a multi-layered software quality analysis system that provides NASA-grade safety compliance and MECE (Mutually Exclusive, Collectively Exhaustive) code quality assessment. The system implements a unified import strategy and modular architecture supporting multiple interfaces: CLI, MCP server, VS Code extension, and CI/CD integration.

## Core Architecture Principles

- **Unified Import Strategy**: Centralized dependency management via `core/unified_imports.py`
- **Modular Design**: Independent analyzers coordinated by `analyzer/ast_engine/analyzer_orchestrator.py`
- **Multi-Interface Support**: CLI, MCP, VS Code extension, and CI/CD endpoints
- **Graceful Fallbacks**: System degrades gracefully when components are unavailable
- **NASA Compliance**: Built-in Power of Ten rules validation

## System Components

### 1. Core Analysis Engine (`analyzer/`)

**Primary Module**: `analyzer/core.py`
- Main entry point for all analysis operations
- Supports unified (`UnifiedConnascenceAnalyzer`) and fallback modes
- Policy-based analysis with NASA compliance validation

**Key Components**:
- `check_connascence.py` - Legacy fallback analyzer
- `constants.py` - Policy definitions and thresholds
- `ast_engine/analyzer_orchestrator.py` - Parallel analyzer coordination
- `dup_detection/mece_analyzer.py` - MECE duplication analysis

**Supported Languages**:
- Python (full AST analysis)
- JavaScript/TypeScript (pattern-based)
- C/C++ (safety-focused analysis)

### 2. Unified Import Manager (`core/`)

**Primary Module**: `core/unified_imports.py`
- Eliminates fragmented import patterns across the codebase
- Provides graceful fallback handling and dependency resolution
- Manages search paths for analyzer, MCP, utils, config, and experimental modules

**Key Features**:
```python
# Import with fallbacks
spec = ImportSpec(
    module_name="analyzer.unified_analyzer",
    fallback_modules=["analyzer.core"],
    required=False
)
result = IMPORT_MANAGER.import_module(spec)
```

### 3. MCP Server Interface (`mcp/`)

**Primary Module**: `mcp/server.py`
- Claude integration with tool coordination capabilities
- Rate limiting, audit logging, and path validation
- Async tool execution with standardized error handling

**Available Tools**:
- `scan_path` - File/directory analysis
- `explain_finding` - Detailed violation explanations
- `propose_autofix` - Automated fix suggestions
- `list_presets` - Available policy configurations
- `validate_policy` - Policy validation
- `get_metrics` - Server performance metrics

**Configuration Options**:
```python
config = {
    'max_requests_per_minute': 60,
    'enable_audit_logging': True,
    'allowed_paths': ['/workspace', '/project']
}
```

### 4. VS Code Extension (`vscode-extension/`)

**Primary Module**: `vscode-extension/src/extension.ts`
- Real-time diagnostics and IntelliSense integration
- Interactive dashboard and visual highlighting
- Framework-specific profiles (Django, FastAPI, React)

**Key Features**:
- Real-time analysis with configurable debouncing
- Visual highlighting of connascence violations
- Interactive dashboard with broken chain logo
- AI-powered fix suggestions
- Comprehensive configuration options

**Architecture Components**:
```typescript
- ConnascenceExtension (core orchestrator)
- ConnascenceService (analysis coordination)
- VisualHighlightingManager (code highlighting)
- NotificationManager (user notifications)
- BrokenChainLogoManager (visual branding)
- AIFixSuggestionsProvider (automated fixes)
```

### 5. CLI Interface (`cli/`)

**Primary Module**: `cli/package.json` + core integration
- Command-line interface with Node.js toolchain
- Multiple output formats (JSON, SARIF, console)
- Batch processing capabilities

**Supported Commands**:
```bash
connascence analyze --path ./src --policy nasa-compliance --format sarif
```

## System Integration Patterns

### 1. Direct Integration
**Used by**: CLI → Core Analyzer
- Direct Python module imports
- Synchronous execution
- File-based configuration

### 2. Service Integration
**Used by**: VS Code Extension → MCP Server
- HTTP/WebSocket communication
- Async request/response
- Real-time capabilities

### 3. Event-Driven Integration
**Used by**: VS Code Extension Internal Components
- Extension activation events
- Document change listeners
- Configuration update handlers

### 4. Pipeline Integration
**Used by**: GitHub Actions CI/CD
- Shell command execution
- Artifact generation
- Quality gate enforcement

## Data Flow Architecture

### Input Processing
1. **File Discovery**: Supported extensions (.py, .c, .cpp, .js, .ts)
2. **Multi-Language Parsing**: Language-specific AST generation
3. **Grammar Enhancement**: Context and metadata enrichment

### Analysis Pipeline
1. **Parallel Analyzer Execution**: 5 specialized analyzers
   - PositionAnalyzer (CoP - parameter dependencies)
   - MeaningAnalyzer (CoM - magic literals)
   - AlgorithmAnalyzer (CoA - duplicated logic)
   - GodObjectAnalyzer (SOLID violations)
   - MultiLanguageAnalyzer (cross-language support)

2. **MECE Analysis**: 8-phase duplication detection
   - Code registry building → Exact duplicates → Similar functions → Functional overlaps
   - Responsibility overlaps → Consolidation recommendations → Metrics calculation → Actionable recommendations

3. **NASA Compliance Validation**: 10 Power of Ten rules
   - Real-time safety-critical software validation
   - Compliance scoring and violation tracking
   - Defense industry readiness assessment

### Output Generation
1. **Violation Collection**: Standardized violation objects
2. **Multi-Format Export**: JSON, SARIF, HTML, console output
3. **Quality Gate Evaluation**: Pass/fail determinations
4. **Dashboard Updates**: Real-time UI updates

## Performance Characteristics

### Analysis Throughput
- Small files (<500 lines): ~2000 lines/second
- Medium files (500-2000 lines): ~1000 lines/second
- Large files (2000+ lines): ~500 lines/second
- Parallel processing scales linearly

### Memory Usage
- AST Parsing: ~10MB per 1000 lines
- Analysis Engine: ~20MB base + 5MB per analyzer
- MECE Processing: ~15MB + 2MB per duplication cluster
- VS Code Extension: <50MB typical usage

### Real-World Performance
- Celery (4,630 violations): 8.2 seconds
- curl (1,061 violations): 3.1 seconds
- Express (52 violations): 0.8 seconds
- Self-analysis (46,576 violations): 11.978 seconds

## Security Architecture

### Path Validation
- Traversal attack prevention (`..` detection)
- Restricted path enforcement
- Allow-list configuration support

### Rate Limiting
- Client-based request limiting
- Configurable thresholds (60 requests/minute default)
- Graceful degradation on limit exceeded

### Audit Logging
- Complete request/response logging
- Performance metrics tracking
- Security event monitoring

## Quality Gates

### NASA Compliance
- **Threshold**: 95% compliance required
- **Rules**: 10 Power of Ten safety rules
- **Scope**: Safety-critical software validation

### MECE Quality
- **Threshold**: 80% duplication elimination
- **Scope**: Code duplication and responsibility overlap
- **Metrics**: Consolidation opportunities and recommendations

### Overall Quality
- **Threshold**: 75% overall quality score
- **Calculation**: Weighted violation severity assessment
- **Scope**: Comprehensive code quality evaluation

## Deployment Patterns

### Local Development
- VS Code extension with real-time analysis
- CLI for batch processing
- Local MCP server for Claude integration

### CI/CD Integration
- GitHub Actions workflow integration
- Quality gate enforcement
- SARIF report generation for Code Scanning

### Enterprise Deployment
- Centralized MCP server deployment
- Multi-tenant configuration support
- Audit logging and compliance reporting

## Technology Stack

### Core Languages
- **Python 3.12+**: Core analysis engine
- **TypeScript**: VS Code extension
- **Node.js**: CLI interface and tooling

### Key Dependencies
- **Python**: AST analysis, NASA rules validation
- **VS Code API**: Extension integration
- **GitHub Actions**: CI/CD integration
- **SARIF**: Industry-standard reporting

### Development Tools
- **Unified Import Manager**: Dependency resolution
- **Error Handling**: Standardized error responses
- **Configuration Management**: Multi-layer config support