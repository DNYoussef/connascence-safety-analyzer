# Current Analysis Capabilities

## Overview

The Connascence Safety Analyzer provides comprehensive code analysis capabilities through multiple integrated engines. This document describes the **actual working features** based on the current codebase implementation.

## Core Analysis Engines

### 1. Unified Connascence Analyzer (`analyzer/core.py`)

**Primary Interface**: The main analysis engine with three operational modes:
- **Unified Mode**: Full-featured analysis using `UnifiedConnascenceAnalyzer`
- **Fallback Mode**: Basic analysis using `FallbackAnalyzer` 
- **Mock Mode**: Testing/fallback when analyzers unavailable

**Analysis Policies**:
- `default` → `service-defaults` preset
- `strict-core` → `strict-analysis` preset  
- `nasa_jpl_pot10` → `nasa-compliance` preset
- `lenient` → `basic-analysis` preset

### 2. AST-Based Analysis (`analyzer/ast_engine/`)

**Capabilities**:
- Python AST parsing and analysis
- Function complexity calculation
- Class structure analysis
- Import dependency tracking

### 3. MECE Duplication Detection (`analyzer/dup_detection/mece_analyzer.py`)

**Key Features**:
- **Algorithm Normalization**: Extracts structural patterns from functions
- **Cross-File Duplicate Detection**: Finds similar code blocks across files
- **Similarity Scoring**: Configurable threshold-based clustering
- **MECE Compliance**: Mutually Exclusive, Collectively Exhaustive analysis

**Configuration**:
- Similarity Threshold: Default from `MECE_SIMILARITY_THRESHOLD` constant
- Minimum Block Size: 3 lines of code
- Minimum Cluster Size: From `MECE_CLUSTER_MIN_SIZE` constant

## Connascence Types Detection

### Currently Supported (9 Types)

1. **CoN - Connascence of Name**: Import and reference analysis
2. **CoT - Connascence of Type**: Type coupling detection  
3. **CoM - Connascence of Meaning**: Magic literal detection (most common)
4. **CoP - Connascence of Position**: Parameter count analysis (NASA Rule #6)
5. **CoA - Connascence of Algorithm**: Duplicate function detection via MECE
6. **CoE - Connascence of Execution**: Execution order dependencies
7. **CoTm - Connascence of Timing**: Sleep() call detection
8. **CoV - Connascence of Value**: Value-dependent coupling
9. **CoI - Connascence of Identity**: Global variable analysis

## NASA Power of Ten Integration

**Built-in Safety Analysis**:
- **Rule #6 Parameter Limits**: Functions with >6 parameters flagged as high severity
- **God Object Detection**: Classes >20 methods or >500 lines flagged as critical
- **Complexity Analysis**: Cyclomatic complexity >10 flagged
- **Global Usage**: >5 globals trigger identity connascence violations

## Multi-Language Support

### Python (Full AST Analysis)
- Complete syntax tree parsing
- Function/class structure analysis
- Import dependency mapping
- Magic literal detection in context

### JavaScript/Node.js (Pattern-Based)
- Function signature extraction
- Parameter counting
- Basic complexity metrics

### C/C++ (Pattern-Based)  
- Function declaration parsing
- Magic literal detection
- Basic structure analysis

## Output Formats

### JSON Format
```json
{
  "success": true,
  "path": "/path/to/code",
  "policy": "default",
  "violations": [...],
  "summary": {
    "total_violations": 100,
    "critical_violations": 5,
    "overall_quality_score": 0.85
  },
  "nasa_compliance": {
    "score": 0.90,
    "violations": [...],
    "passing": true
  },
  "mece_analysis": {
    "score": 0.75,
    "duplications": [...],
    "passing": true
  },
  "god_objects": [...],
  "metrics": {
    "files_analyzed": 42,
    "analysis_time": 2.5,
    "timestamp": 1696123456.789
  }
}
```

### SARIF Format
- Industry-standard security tool format
- IDE integration support
- Structured violation reporting
- Tool correlation support

## Quality Thresholds

**Default Thresholds** (from constants):
- NASA Compliance: ≥0.95
- MECE Quality: ≥0.80  
- Overall Quality: ≥0.75

**Violation Severity Weights**:
- Critical: 10 points
- High: 5 points
- Medium: 2 points
- Low: 1 point

## Performance Characteristics

**Typical Analysis Times**:
- Single file: ~0.1-0.5 seconds
- Small project (~100 files): ~2-5 seconds
- Large project (~1000+ files): ~30-60 seconds

**Memory Usage**:
- Scales linearly with codebase size
- AST parsing requires ~2-3x file size in memory
- MECE analysis adds ~1.5x overhead for duplicate detection

## Integration Points

### Command Line Interface
```bash
python -m analyzer.core --path /code --policy nasa_jpl_pot10 --format sarif
```

### MCP Server Interface  
```bash
python -m mcp.cli analyze-file src/main.py --analysis-type full --format json
python -m mcp.cli analyze-workspace . --file-patterns "*.py" --include-integrations
```

### Programmatic API
```python
from analyzer.core import ConnascenceAnalyzer
analyzer = ConnascenceAnalyzer()
result = analyzer.analyze_path("/path/to/code", policy="strict-core")
```

## Limitations and Known Issues

1. **MCP CLI**: Currently has import issues with `core.unified_imports`
2. **Language Support**: JavaScript/C++ analysis is pattern-based, not AST-based  
3. **MECE Analysis**: Only analyzes functions >3 lines (configurable)
4. **Memory Usage**: Large codebases may require significant RAM

## Version Information

- **Core Analyzer Version**: 2.0.0
- **Analysis Modes**: 3 (unified, fallback, mock)
- **Supported Languages**: Python (full), JavaScript (basic), C/C++ (basic)
- **Output Formats**: JSON, SARIF, YAML