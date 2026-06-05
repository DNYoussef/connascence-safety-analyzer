# Connascence Analyzer Dogfooding Remediation Plan

**Generated**: 2025-11-25
**Analysis Tool**: Connascence Safety Analyzer v2.0 (7 Integrated Analyzers)
**Target**: analyzer/ directory (self-analysis)

---

## Executive Summary (Updated with All 7 Analyzers)

| Analyzer | Metric | Value | Status |
|----------|--------|-------|--------|
| **Connascence** | Violations | 26,675 | NEEDS WORK |
| **NASA Safety** | Compliance | 100% | EXCELLENT |
| **MECE** | Completeness | 0% | CONFIG ISSUE |
| **Duplication** | Clusters | 4 | GOOD |
| **Clarity** | Violations | 0 | IMPORT ERROR |
| **Safety** | Violations | 199 | NEEDS WORK |
| **Six Sigma** | Level | 1.94 sigma | NEEDS IMPROVEMENT |

### Severity Breakdown

| Severity | Count |
|----------|-------|
| Critical | 82 |
| High | 348 |
| Medium | 1,783 |
| Low | 24,462 |
| **Total** | **26,675** |

### Violation Distribution by Type

| Type | Count | Description |
|------|-------|-------------|
| CoM (Meaning) | 22,362 | Magic literals - hardcoded values |
| CoV (Values) | 2,090 | Shared value dependencies |
| Convention | 800 | Convention violations |
| CoE (Execution) | 644 | Execution order dependencies |
| CoA (Algorithm) | 331 | Complex methods, god classes |
| CoP (Position) | 161 | Parameter position issues |
| God Object | 104 | Classes with too many methods |
| CoN (Name) | 73 | Name dependencies |

### Six Sigma Quality Gap

| Metric | Current | Enterprise Target | Gap |
|--------|---------|-------------------|-----|
| Sigma Level | 1.94 | 5.0 | -3.06 |
| DPMO | 331,898 | 233 | -331,665 |
| Quality Level | ONE_SIGMA | ENTERPRISE | 4 levels |

---

## Critical Violations (Priority 1)

### 1. God Class: UnifiedConnascenceAnalyzer (70 methods!)

**File**: `analyzer/unified_analyzer.py:443`
**Severity**: CRITICAL
**Methods**: 70 (threshold: 15)

**Remediation Strategy**: Extract to multiple focused analyzers
- Create `CoreAnalyzer` - basic analysis methods
- Create `MetricsCalculator` - metrics-related methods
- Create `ReportGenerator` - reporting methods
- Create `CacheManager` - caching methods
- Use composition pattern

### 2. God Class: ConnascenceDetector (34 methods)

**File**: `analyzer/check_connascence.py:54`
**Severity**: CRITICAL
**Methods**: 34 (threshold: 15)

**Remediation Strategy**: Strategy pattern refactoring
- Extract detection methods to separate detector classes
- Create DetectorRegistry for dynamic dispatch
- Each connascence type gets its own detector class

### 3. Magic Literal: 1048576

**File**: `analyzer/constants.py:627`
**Severity**: CRITICAL

**Remediation**: Extract to named constant
```python
MAX_FILE_SIZE_BYTES = 1048576  # 1MB
```

### 4. Magic Literal: 1048576 (duplicate)

**File**: `analyzer/literal_constants/constants_constants.py:18`
**Severity**: CRITICAL

**Remediation**: Reference the existing constant or consolidate

---

## Major Violations (Priority 2)

### God Classes (11 instances)

| Class | Methods | File |
|-------|---------|------|
| UnifiedCoordinator | 28 | unified_coordinator.py |
| ViolationAggregator | 21 | architecture/aggregator.py |
| ConfigurationManager | 21 | architecture/configuration_manager.py |
| EnhancedMetricsCalculator | 20 | architecture/enhanced_metrics.py |
| ContextAnalyzer | 20 | context_analyzer.py |
| LanguageStrategy | 17 | language_strategies.py |
| RefactoredConnascenceDetector | 17 | refactored_detector.py |

### High Cyclomatic Complexity Functions

| Function | Complexity | Max | File |
|----------|------------|-----|------|
| _assess_god_object_with_context | 22 | 10 | context_analyzer.py:524 |
| _identify_method_responsibilities | 16 | 10 | context_analyzer.py:385 |
| _generate_recommendations | 16 | 10 | context_analyzer.py:580 |

---

## Remediation Phases

### Phase 1: Critical Fixes (Immediate)

1. **Extract magic literal 1048576 to named constant**
   - Create `MAX_FILE_SIZE_BYTES` constant
   - Update all references

2. **Plan UnifiedConnascenceAnalyzer decomposition**
   - Document method groupings
   - Design new class structure
   - Plan migration path

### Phase 2: God Class Refactoring (Short-term)

1. **Split UnifiedConnascenceAnalyzer** (70 -> 5x14 methods)
   - CoreAnalyzer
   - MetricsCalculator
   - ReportGenerator
   - CacheManager
   - ValidationHelper

2. **Split ConnascenceDetector** (34 -> strategy pattern)
   - BaseDetector
   - CoMDetector
   - CoTDetector
   - CoADetector
   - CoEDetector
   - CoVDetector
   - DetectorRegistry

### Phase 3: Complexity Reduction (Medium-term)

1. **Refactor high-complexity functions**
   - Extract helper methods
   - Use early returns
   - Simplify conditionals

2. **Add missing type hints** (160 CoT violations)
   - Prioritize public APIs
   - Use typing module

### Phase 4: Magic Literal Cleanup (Long-term)

1. **Extract remaining 1,663 magic literals**
   - Create constants modules by domain
   - Use enums for related values
   - Document constant meanings

---

## Files Requiring Most Attention

| File | Violations | Priority |
|------|------------|----------|
| constants.py | 126 | Low (constants file) |
| unified_analyzer.py | 80 | HIGH (god class) |
| constants_constants.py | 77 | Low (constants file) |
| theater_detection/detector.py | 70 | Medium |
| theater_detection/validator.py | 69 | Medium |
| context_analyzer.py | 57 | HIGH (complexity) |

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Critical Violations | 4 | 0 |
| Major Violations | 31 | < 10 |
| God Classes | 11 | 0 |
| Max Cyclomatic Complexity | 22 | 10 |
| Quality Score | 0.0 | > 70.0 |

---

## Next Steps

1. [ ] Fix magic literal 1048576 -> MAX_FILE_SIZE_BYTES
2. [ ] Document UnifiedConnascenceAnalyzer method groups
3. [ ] Create refactoring PRs for god classes
4. [ ] Add type hints to public APIs
5. [ ] Re-run analysis to verify improvements
