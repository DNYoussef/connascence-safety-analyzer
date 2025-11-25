# Connascence Analyzer - Test/Implementation Remediation Plan

**Generated**: 2025-11-25
**Status**: Active Remediation Required
**Severity**: HIGH - CI/CD Pipeline Blocked

---

## Executive Summary

The Connascence Analyzer has **real, functional implementation code** but suffers from **test-implementation mismatch**. Tests were written for a planned architecture that evolved differently during development.

**Impact**: GitHub Actions CI/CD tests are failing
**Root Cause**: 5 missing modules + 4 missing API methods + architectural split between two analyzer implementations

---

## Missing Modules (5)

| Module | Location Expected | Reason | Priority |
|--------|------------------|--------|----------|
| `analyzer.ast_engine.visitors` | test_smoke_imports.py:47 | AST visitor pattern implementations | HIGH |
| `analyzer.cohesion_analyzer` | test_smoke_imports.py:49 | Cohesion metrics analysis | HIGH |
| `analyzer.architectural_analysis` | test_smoke_imports.py:50 | Architecture extraction logic | HIGH |
| `analyzer.grammar_enhanced_analyzer` | test_smoke_imports.py:51 | Grammar-based detection (formal_grammar.py exists with different name) | HIGH |
| `reporting` | test_smoke_imports.py:95 | Report generation package | MEDIUM |

---

## Missing API Methods (4)

| Class | Method | Expected In | Current Status | Priority |
|-------|--------|-------------|----------------|----------|
| `ConnascenceAnalyzer` (core.py) | `analyze_file()` | test_basic_functionality.py:160 | Exists in check_connascence.py only | HIGH |
| `ConnascenceAnalyzer` (core.py) | `analyze_directory()` | test_basic_functionality.py:161 | Exists in check_connascence.py only | HIGH |
| `ConnascenceAnalyzer` (core.py) | `should_analyze_file()` | test_basic_functionality.py:162 | Exists in check_connascence.py only | MEDIUM |
| `src.cli_handlers` | Module export | test_smoke_imports.py:205-209 | Handlers in interfaces.cli.connascence | MEDIUM |

---

## Architecture Issue

The project has **TWO analyzer implementations**:

```
analyzer/core.py
  - ConnascenceAnalyzer class
  - Modern API: analyze_path()
  - Missing legacy methods

analyzer/check_connascence.py
  - ConnascenceAnalyzer class (different implementation!)
  - Legacy API: analyze_file(), analyze_directory(), should_analyze_file()
  - Contains actual detection logic (1000+ lines)
```

**Tests expect BOTH APIs to be available on the same class.**

---

## Remediation Steps

### Phase 1: Fix Tests (Quick CI Fix)

1. **Update test_smoke_imports.py**
   - Remove/skip tests for non-existent modules
   - Update module paths to match actual structure

2. **Update test_basic_functionality.py**
   - Fix API expectations to match actual implementation
   - Use correct import paths

### Phase 2: Implement Missing Modules

1. **Create analyzer/ast_engine/visitors.py**
   - Implement AST visitor base classes
   - Delegate to existing detectors

2. **Create analyzer/cohesion_analyzer.py**
   - Extract cohesion analysis from check_connascence.py
   - Provide standalone cohesion metrics

3. **Create analyzer/architectural_analysis.py**
   - Implement architecture extraction
   - Use existing dependency analysis

4. **Create analyzer/grammar_enhanced_analyzer.py**
   - Wrapper for existing formal_grammar.py
   - Maintain backward compatibility

5. **Create reporting/ package**
   - Move/consolidate reporting functionality
   - Provide unified reporting API

### Phase 3: Unify Architecture

1. **Consolidate ConnascenceAnalyzer classes**
   - Make core.py delegate to check_connascence.py
   - Or merge implementations

2. **Create src/cli_handlers.py facade**
   - Re-export handlers from interfaces.cli.connascence

---

## Test Files Affected

| Test File | Status | Issues |
|-----------|--------|--------|
| test_smoke_imports.py | FAILING | 5 missing modules |
| test_basic_functionality.py | PARTIAL | 1 API mismatch |
| test_benchmarks.py | FAILING | Detection expectations |
| Other unit tests | PASSING | ~35+ tests pass |

---

## Existing Working Components

These components are verified working:

- `analyzer/check_connascence.py` - Main analyzer (1000+ lines)
- `analyzer/detectors/*` - Modular detector implementations
- `analyzer/formal_grammar.py` - Magic literal detection
- `autofix/*` - All autofix modules
- `policy/*` - All policy modules
- `utils/types.py` - ConnascenceViolation dataclass
- `interfaces/cli/connascence.py` - CLI implementation

---

## Success Criteria

1. All smoke import tests pass
2. All basic functionality tests pass
3. CI/CD pipeline goes green
4. No regressions in working tests

---

## Timeline Estimate

| Phase | Effort | Impact |
|-------|--------|--------|
| Phase 1 (Fix Tests) | 2-4 hours | CI Green |
| Phase 2 (Implement Modules) | 8-16 hours | Full Compatibility |
| Phase 3 (Unify Architecture) | 4-8 hours | Long-term Maintainability |

---

## Notes

- The codebase is NOT mock code - it has substantial real implementation
- The test-code drift is common in fast-moving projects
- Recommend fixing tests first for quick CI win, then implementing modules
