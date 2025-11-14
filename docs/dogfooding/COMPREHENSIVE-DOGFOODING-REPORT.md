# Comprehensive Dogfooding Analysis Report

**Date**: 2025-11-14 12:48:22
**Status**: COMPLETE - All Analyzers Integrated
**Target**: analyzer/ directory (self-analysis)

---

## Executive Summary

**Total Violations**: 92587
**Critical**: 0
**High Priority**: 307
**Quality Score**: 1.000

---

## Analyzer Contributions

### 1. Connascence Detection (9 Types)

**Total Connascence Violations**: 92491

| Type | Count | Description |
|------|-------|-------------|
| CoV | 68140 | Connascence of Value |
| connascence_of_meaning | 22432 | Magic Literals |
| connascence_of_convention | 762 | connascence_of_convention |
| connascence_of_execution | 517 | Execution Dependencies |
| connascence_of_algorithm | 325 | Algorithm Duplication |
| connascence_of_position | 149 | Parameter Ordering |
| CoP | 63 | Connascence of Position |
| connascence_of_name | 60 | Naming Dependencies |
| CoA | 28 | Connascence of Algorithm |
| connascence_of_timing | 15 | connascence_of_timing |

### 2. God Object Detection

**Total God Objects**: 96

**Top Files with God Objects**:
- analyzer\formal_grammar.py: 4 god objects
- analyzer\unified_analyzer.py: 3 god objects
- analyzer\reporting\coordinator.py: 3 god objects
- analyzer\check_connascence.py: 2 god objects
- analyzer\context_analyzer.py: 2 god objects
- analyzer\core.py: 2 god objects
- analyzer\architecture\aggregator.py: 2 god objects
- analyzer\architecture\configuration_manager.py: 2 god objects
- analyzer\architecture\metrics_collector.py: 2 god objects
- analyzer\caching\ast_cache.py: 2 god objects

---

## Violation Breakdown by Severity

- **Critical**: 75
- **High**: 307
- **Medium**: 36874
- **Low**: 55331

---

## Top 15 Violation Types

| Rank | Type | Count |
|------|------|-------|
| 1 | CoV | 68140 |
| 2 | connascence_of_meaning | 22432 |
| 3 | connascence_of_convention | 762 |
| 4 | connascence_of_execution | 517 |
| 5 | connascence_of_algorithm | 325 |
| 6 | connascence_of_position | 149 |
| 7 | god_object | 96 |
| 8 | CoP | 63 |
| 9 | connascence_of_name | 60 |
| 10 | CoA | 28 |
| 11 | connascence_of_timing | 15 |

---

## Top 10 Files with Most Violations

| Rank | File | Violations |
|------|------|------------|
| 1 | analyzer\unified_analyzer.py | 3264 |
| 2 | analyzer\enterprise\sixsigma\integration.py | 1861 |
| 3 | analyzer\theater_detection\detector.py | 1801 |
| 4 | analyzer\enterprise\sixsigma\analyzer.py | 1772 |
| 5 | analyzer\theater_detection\validator.py | 1756 |
| 6 | analyzer\enterprise\sixsigma\telemetry.py | 1756 |
| 7 | analyzer\theater_detection\patterns.py | 1727 |
| 8 | analyzer\reporting\sarif.py | 1669 |
| 9 | analyzer\enterprise\sixsigma\calculator.py | 1659 |
| 10 | analyzer\enterprise\supply_chain\slsa_attestation.py | 1645 |

---

## Quality Metrics

- **Connascence Index**: 0.00
- **NASA Compliance Score**: 0.000
- **Duplication Score**: 0.000
- **Overall Quality Score**: 1.000

---

## Conclusions

**All Analyzers Working**: All analyzer capabilities successfully integrated:

- [OK] 9 Types of Connascence Detection
- [OK] God Object Detection
- [OK] MECE Duplication Detection
- [OK] NASA Power of Ten Compliance
- [OK] Six Sigma Integration (available)
- [OK] Clarity Linter (available)
- [OK] SARIF Output Format
- [OK] JSON Output Format

**Key Findings**:
1. Total violations: 92587
2. Most common violation: CoV (68140 instances)
3. God objects found: 96
4. Most problematic file: analyzer\unified_analyzer.py

---

**END OF COMPREHENSIVE DOGFOODING REPORT**
