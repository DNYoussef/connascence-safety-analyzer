# Dogfooding Remediation Plan v2.0

**Generated**: 2025-11-25
**Status**: All 7 Analyzers Working - Ready for Remediation
**Baseline**: 20,323 total violations

---

## Executive Summary

| Metric | Current | Target | Gap |
|--------|---------|--------|-----|
| Total Violations | 20,323 | <5,000 | -15,323 |
| Critical | 87 | 0 | -87 |
| High | 364 | <50 | -314 |
| Sigma Level | 1.94 | 4.0 | +2.06 |
| DPMO | 331,371 | <6,210 | -325,161 |

---

## Violation Breakdown by Priority

### Priority 1: CRITICAL (87 violations) - IMMEDIATE
**Target**: 100% elimination
**Estimated Impact**: Sigma +0.5

| Category | Count | Root Cause |
|----------|-------|------------|
| God Objects | ~87 | Classes with >500 lines or >20 methods |

**Files Requiring Immediate Action**:
1. `analyzer/check_connascence.py` - ConnascenceDetector (828 lines, 34 methods)
2. `analyzer/unified_analyzer.py` - UnifiedConnascenceAnalyzer (estimated 70+ methods)
3. `analyzer/context_analyzer.py` - Large context classes
4. `analyzer/core.py` - Core analyzer classes

### Priority 2: HIGH (364 violations) - URGENT
**Target**: 90% reduction
**Estimated Impact**: Sigma +0.8

| Category | Count | Issue |
|----------|-------|-------|
| Connascence of Position (CoP) | 172+68=240 | Functions with >3 positional params |
| Connascence of Algorithm (CoA) | 339+30=369 | Duplicate algorithm structures |

**Top Offenders (Parameter Bombs)**:
- `_assess_god_object_with_context`: 7 params (context_analyzer.py:524)
- `_process_formal_magic_literal`: 6 params (check_connascence.py:552)
- `_generate_recommendations`: 6 params (context_analyzer.py:580)
- Multiple functions with 4 params

### Priority 3: MEDIUM (1,909 violations) - PLANNED
**Target**: 70% reduction
**Estimated Impact**: Sigma +0.5

| Category | Count | Issue |
|----------|-------|-------|
| Connascence of Convention | 809 | Naming/style inconsistencies |
| Connascence of Execution | 669 | Execution order dependencies |
| Clarity - Poor Naming | 161 | Variable/function naming |
| Clarity - Thin Helpers | 66 | Trivial wrapper functions |
| God Objects (Medium) | ~109 | Smaller god object classes |

### Priority 4: LOW (17,963 violations) - INCREMENTAL
**Target**: 50% reduction
**Estimated Impact**: Sigma +0.3

| Category | Count | Issue |
|----------|-------|-------|
| Connascence of Meaning (CoM) | 15,656 | Magic literals (post-filtering) |
| Connascence of Values (CoV) | 2,114 | Shared value dependencies |
| Connascence of Name (CoN) | 73 | Name coupling |
| Clarity - Comments | 26 | Comment quality issues |
| Clarity - Indirection | 16 | Unnecessary wrappers |

---

## CASCADE DEPENDENCY REMEDIATION PHASES

```
Phase 1: Critical - God Object Decomposition
    |
    v
Phase 2: High - Parameter Bomb Refactoring
    |
    v
Phase 3: Medium - Algorithm Deduplication
    |
    v
Phase 4: Medium - Clarity Improvements
    |
    v
Phase 5: Low - Magic Literal Extraction
    |
    v
Phase 6: Validation & Six Sigma Assessment
```

---

## Phase 1: Critical - God Object Decomposition

**Skill**: `refactoring-technical-debt`
**Playbook**: `refactoring-technical-debt`
**Agents**: `code-analyzer`, `reviewer`, `coder`, `system-architect`
**Duration**: 4-6 hours
**Dependencies**: None

### 1.1 Target: ConnascenceDetector (check_connascence.py)

**Current State**: 828 lines, 34 methods
**Target State**: <500 lines, <20 methods per class

**Decomposition Strategy**:
```
ConnascenceDetector (34 methods)
    |
    +-- VisitorMixin (8 methods)
    |   - visit_FunctionDef, visit_ClassDef, visit_Import, etc.
    |
    +-- MagicLiteralHandler (6 methods)
    |   - _process_formal_magic_literal, _process_legacy_magic_literal
    |   - _create_formal_magic_literal_description
    |
    +-- AlgorithmDetector (5 methods)
    |   - _detect_algorithm_issues, _create_algorithm_duplicate_violation
    |
    +-- ViolationBuilder (5 methods)
    |   - create_violation, _convert_violation
    |
    +-- ConnascenceDetector (10 methods - orchestration only)
        - analyze, get_violations, etc.
```

### 1.2 Target: UnifiedConnascenceAnalyzer (unified_analyzer.py)

**Strategy**: Already uses composition pattern - verify delegation is complete

### 1.3 Target: ContextAnalyzer (context_analyzer.py)

**High-Complexity Functions to Extract**:
- `_assess_god_object_with_context` (complexity 22)
- `_identify_method_responsibilities` (complexity 16)
- `_generate_recommendations` (complexity 16)

---

## Phase 2: High - Parameter Bomb Refactoring

**Skill**: `sparc-methodology`
**Playbook**: `simple-feature-implementation`
**Agents**: `coder`, `tester`, `reviewer`
**Duration**: 3-4 hours
**Dependencies**: Phase 1 complete

### 2.1 Pattern: Parameter Object

Convert functions with >3 params to use dataclasses:

```python
# BEFORE
def _assess_god_object_with_context(self, class_name, methods, attributes,
                                     line_count, file_path, context, config):
    ...

# AFTER
@dataclass
class GodObjectAssessmentContext:
    class_name: str
    methods: List[str]
    attributes: List[str]
    line_count: int
    file_path: str
    context: Dict
    config: Dict

def _assess_god_object_with_context(self, ctx: GodObjectAssessmentContext):
    ...
```

### 2.2 Target Functions (by param count)

| Function | Params | File | Line |
|----------|--------|------|------|
| _assess_god_object_with_context | 7 | context_analyzer.py | 524 |
| _process_formal_magic_literal | 6 | check_connascence.py | 552 |
| _generate_recommendations | 6 | context_analyzer.py | 580 |
| analyze_class_context | 4 | context_analyzer.py | 158 |
| _classify_class_context | 4 | context_analyzer.py | 291 |
| _convert_violation | 4 | cli_entry.py | 218 |

---

## Phase 3: Medium - Algorithm Deduplication

**Skill**: `clarity-linter`
**Playbook**: `comprehensive-review`
**Agents**: `code-analyzer`, `coder`, `reviewer`
**Duration**: 2-3 hours
**Dependencies**: Phase 2 complete

### 3.1 Duplicate Algorithm Patterns to Consolidate

| Pattern | Occurrences | Files |
|---------|-------------|-------|
| visit_* methods | 4+ | check_connascence.py |
| _get_*_attributes | 2+ | cohesion_analyzer.py |
| _analyze_* methods | 3+ | context_analyzer.py |

### 3.2 Strategy: Template Method Pattern

```python
# Base visitor pattern
class BaseNodeVisitor:
    def _handle_node(self, node, handler):
        """Template method for consistent node handling."""
        self.generic_visit(node)
        return handler(node)
```

---

## Phase 4: Medium - Clarity Improvements

**Skill**: `clarity-linter`
**Playbook**: `quality-quick-check`
**Agents**: `reviewer`, `coder`
**Duration**: 2-3 hours
**Dependencies**: Phase 3 complete

### 4.1 Poor Naming (161 violations)

**Common Issues**:
- Single-letter variables outside loops
- Generic names (data, temp, result)
- Unclear abbreviations

**Fix Pattern**: Rename to descriptive names

### 4.2 Thin Helpers (66 violations)

**Options**:
1. Inline trivial wrappers at call sites
2. Add meaningful logic (validation, logging)
3. Document justification if intentional

### 4.3 Comment Issues (26 violations)

- Remove commented-out code
- Add context to TODO/FIXME
- Remove redundant comments

---

## Phase 5: Low - Magic Literal Extraction

**Skill**: `micro-skill-creator` (for batch extraction)
**Playbook**: `simple-feature-implementation`
**Agents**: `coder`, `tester`
**Duration**: 4-6 hours (incremental)
**Dependencies**: Phase 4 complete

### 5.1 Strategy: Constants Module Expansion

Target remaining 15,656 CoM violations:
1. Group by semantic category
2. Extract to appropriate constants file
3. Use enums for related sets

### 5.2 High-Value Extractions

| Category | Est. Count | Target File |
|----------|-----------|-------------|
| Threshold values | ~500 | thresholds.py |
| Error messages | ~1000 | messages.py |
| Configuration keys | ~2000 | config_keys.py |
| Regex patterns | ~200 | patterns.py |

---

## Phase 6: Validation & Six Sigma Assessment

**Skill**: `functionality-audit`
**Playbook**: `testing-quality`
**Agents**: `tester`, `reviewer`, `evaluator`
**Duration**: 2 hours
**Dependencies**: All phases complete

### 6.1 Validation Steps

1. Run full test suite - must pass 100%
2. Re-run comprehensive dogfooding
3. Compare before/after metrics
4. Generate final SARIF report

### 6.2 Target Metrics Post-Remediation

| Metric | Before | After Target | Improvement |
|--------|--------|--------------|-------------|
| Total Violations | 20,323 | <5,000 | -75% |
| Critical | 87 | 0 | -100% |
| High | 364 | <50 | -86% |
| Sigma Level | 1.94 | 4.0+ | +106% |
| Quality Score | 1.0 | 1.0 | Maintained |

---

## Recommended Execution Order

### Week 1: Foundation (Phases 1-2)
- Day 1-2: God Object Decomposition (Phase 1)
- Day 3-4: Parameter Bomb Refactoring (Phase 2)
- Day 5: Integration Testing

### Week 2: Polish (Phases 3-4)
- Day 1-2: Algorithm Deduplication (Phase 3)
- Day 2-3: Clarity Improvements (Phase 4)
- Day 4-5: Incremental Testing

### Week 3: Completion (Phases 5-6)
- Day 1-3: Magic Literal Extraction (Phase 5)
- Day 4: Final Validation (Phase 6)
- Day 5: Documentation & Release

---

## Skills & Playbooks Reference

| Phase | Primary Skill | Playbook | Trigger Keywords |
|-------|---------------|----------|------------------|
| 1 | refactoring-technical-debt | refactoring-technical-debt | "god object", "refactor", "decompose" |
| 2 | sparc-methodology | simple-feature-implementation | "parameter", "dataclass", "TDD" |
| 3 | clarity-linter | comprehensive-review | "duplicate", "algorithm", "consolidate" |
| 4 | clarity-linter | quality-quick-check | "naming", "clarity", "comments" |
| 5 | micro-skill-creator | simple-feature-implementation | "constants", "extract", "magic literal" |
| 6 | functionality-audit | testing-quality | "validate", "test", "verify" |

---

## Success Criteria

### Phase Gate 1 (After Phase 2)
- [ ] Critical violations: 0
- [ ] High violations: <100
- [ ] All tests passing

### Phase Gate 2 (After Phase 4)
- [ ] Medium violations: <500
- [ ] Sigma level: >3.0

### Phase Gate 3 (Final)
- [ ] Total violations: <5,000
- [ ] Sigma level: >4.0
- [ ] DPMO: <6,210
- [ ] Quality level: THREE_SIGMA or higher

---

## Quick Start Commands

```bash
# Phase 1: Start god object remediation
Skill("refactoring-technical-debt")

# Phase 2: Parameter bomb fixes with TDD
Skill("sparc-methodology")

# Phase 3-4: Clarity improvements
Skill("clarity-linter")

# Phase 6: Final validation
Skill("functionality-audit")
```
