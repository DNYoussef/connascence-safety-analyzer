# Comprehensive Dogfooding Analysis Report

**Generated**: 2025-11-25
**Target**: analyzer/
**Analysis Time**: 33.74s
**Analyzers Run**: 7

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Violations | 20641 |
| Critical | 51 |
| High | 375 |
| Medium | 1945 |
| Low | 18270 |
| Quality Score | 1.000 |
| NASA Compliance | 100.0% |
| Duplication Score | 1.000 |

## Results by Analyzer

### 1. Connascence Analyzer

**Total Violations**: 20361
**Connascence Index**: 37795.00

| Type | Count |
|------|-------|
| connascence_of_meaning | 15936 |
| CoV | 2133 |
| connascence_of_convention | 809 |
| connascence_of_execution | 697 |
| connascence_of_algorithm | 343 |
| connascence_of_position | 177 |
| connascence_of_name | 77 |
| god_object | 73 |
| CoP | 71 |
| CoA | 30 |

### 2. NASA Safety Analyzer

**Total Violations**: 0
**Compliance Score**: 100.0%

### 3. MECE Analyzer

**Completeness Score**: 100.0%

### 4. Duplication Analyzer

**Total Clusters**: 9
**Duplication Score**: 1.000

### 5. Clarity Linter

**Total Violations**: 280
**Files Analyzed**: 156

| Rule | Count |
|------|-------|
| CLARITY_POOR_NAMING | 169 |
| CLARITY_THIN_HELPER | 69 |
| CLARITY_COMMENT_ISSUES | 26 |
| CLARITY_USELESS_INDIRECTION | 16 |

### 6. Safety Violation Detector

**Total Violations**: 174
**God Objects**: 73
**Parameter Bombs (CoP)**: 71
**Complexity Issues (CoA)**: 30

### 7. Six Sigma Quality Metrics

**Sigma Level**: 1.94
**DPMO**: 331977
**RTY**: 0.000
**Quality Level**: ONE_SIGMA

**Improvement Suggestions**:
- Improve sigma level by 3.1 to reach 5.0 target
- Reduce DPMO by 331744 to reach target of 233.0
- Priority: Eliminate 51 critical violations immediately
- Focus on connascence_of_meaning violations (15936 found) - CTQ weight: 0%
- Focus on CoV violations (2133 found) - CTQ weight: 0%

---

## Recommendations

*No specific recommendations generated*

