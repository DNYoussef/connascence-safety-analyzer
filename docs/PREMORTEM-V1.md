# SPEK v2 + Connascence Integration - Premortem v1

**Date**: 2025-10-19
**Iteration**: 1 of 4
**Version**: 1.0 (Post-Plan-v1)
**Method**: Prospective Hindsight - "It's 16 weeks from now, the integration has FAILED catastrophically. What went wrong?"

---

## Executive Summary

### Premortem Scenario
**Date**: 16 weeks from now (Week 13)
**Situation**: Integration project has FAILED. Connascence is broken, users are angry, production systems are down.

**This document imagines that failure and works backward to identify:**
1. What specific failures occurred
2. Why they happened (root causes)
3. How likely they are (probability)
4. What damage they caused (impact)
5. How to prevent them (mitigation)

---

## Methodology: 5 Whys Root Cause Analysis

For each failure scenario, we ask "Why?" 5 times to find root causes, not symptoms.

**Example**:
- **Symptom**: "CLI is broken"
- **Why?** Imports fail
- **Why?** Module structure changed
- **Why?** SPEK integration changed paths
- **Why?** No import adapters created
- **Why?** **ROOT CAUSE**: Plan didn't account for backward compatibility layer
- **Mitigation**: Create `adapter.py` module for backward-compatible imports

---

## Part 1: Critical Failures (Project-Killing Risks)

### FAILURE 1: Connascence Taxonomy Destroyed (P0)

**Scenario**: It's Week 13. Users install connascence v2.0.0. The 9 connascence types (CoN, CoT, CoM, CoP, CoA, CoE, CoI, CoV, CoId) no longer work. Enterprise validation shows **0 connascence violations detected** vs baseline of 46,576.

**5 Whys**:
1. **Why no violations?** Connascence detectors not being called
2. **Why not called?** Unified orchestrator only calls SPEK engines
3. **Why only SPEK?** Integration overwrote connascence's detector registry
4. **Why overwrote?** Assumed SPEK's pattern detector covered connascence
5. **ROOT CAUSE**: Fundamental misunderstanding - SPEK's "pattern detector" ≠ connascence taxonomy

**Probability**: 40% (MEDIUM-HIGH)
**Impact**: CATASTROPHIC (project failure, reputation destroyed)
**Risk Score**: 0.40 × 10 = **4.0 (P0 - CRITICAL)**

**Mitigation Strategies**:

**M1.1: Regression Test Suite (MUST HAVE)**
```python
# tests/integration/test_connascence_taxonomy_preservation.py
"""
Regression tests ensuring ALL 9 connascence types still detected after integration.
"""

import pytest
from analyzer.core.unified_orchestrator import UnifiedOrchestrator

class TestConnascenceTaxonomyPreservation:
    """CRITICAL: These tests MUST pass before ANY integration."""

    def test_cop_detection_preserved(self):
        """Connascence of Position still detected."""
        code = """
def bad_function(a, b, c, d, e, f, g, h):  # 8 params > 4 threshold
    pass
        """
        orchestrator = UnifiedOrchestrator()
        violations = orchestrator.analyze_code(code)

        cop_violations = [v for v in violations if v.connascence_type == "CoP"]
        assert len(cop_violations) > 0, "CoP detection BROKEN"

    def test_con_detection_preserved(self):
        """Connascence of Name still detected."""
        # Similar test for CoN
        pass

    # ... tests for ALL 9 types
```

**M1.2: Orchestrator Architecture Review (MUST HAVE)**
```python
# analyzer/core/unified_orchestrator.py
"""
Unified Orchestrator - MUST call both SPEK and connascence detectors.
"""

class UnifiedOrchestrator:
    def __init__(self):
        # SPEK engines (syntax, patterns, compliance)
        self.spek_engines = [SyntaxAnalyzer(), PatternDetector(), ComplianceValidator()]

        # Connascence detectors (ALL 9 TYPES - CRITICAL)
        self.connascence_detectors = [
            PositionDetector(),      # CoP
            NameDetector(),          # CoN (if exists)
            TypeDetector(),          # CoT (if exists)
            MeaningDetector(),       # CoM (magic literals)
            AlgorithmDetector(),     # CoA
            ExecutionDetector(),     # CoE
            IdentityDetector(),      # CoI (if exists)
            ValueDetector(),         # CoV
            TimingDetector(),        # CoId
        ]

        # CRITICAL CHECK: Ensure ALL 9 detectors registered
        assert len(self.connascence_detectors) == 9, "Missing connascence detectors!"

    def analyze_file(self, file_path):
        violations = []

        # Run SPEK engines
        for engine in self.spek_engines:
            violations.extend(engine.analyze(file_path))

        # Run connascence detectors (CRITICAL - DO NOT SKIP)
        for detector in self.connascence_detectors:
            violations.extend(detector.detect(file_path))

        # Deduplicate (some violations may overlap)
        return self._deduplicate_violations(violations)
```

**M1.3: Pre-Integration Inventory (MUST HAVE)**
```bash
# scripts/inventory_connascence_detectors.py
"""
Before integration, document ALL existing connascence detectors.
"""

import os
import re

def find_all_connascence_detectors():
    detectors = []
    for root, dirs, files in os.walk("analyzer/detectors"):
        for file in files:
            if file.endswith("_detector.py"):
                # Extract detector purpose
                path = os.path.join(root, file)
                with open(path) as f:
                    content = f.read()
                    if "Connascence" in content or "CoN" in content or "CoP" in content:
                        detectors.append((file, path))

    print(f"Found {len(detectors)} connascence detectors:")
    for name, path in detectors:
        print(f"  - {name} ({path})")

    return detectors

# BEFORE integration, run this and save output
# AFTER integration, run again and COMPARE
# If count decreases → FAILURE
```

**M1.4: Phase 0 Validation (MUST HAVE)**
```bash
# Phase 0: Baseline ALL 9 connascence types
connascence analyze test_packages/celery/ --output baseline_connascence.json

# Extract counts per type
python scripts/count_by_type.py baseline_connascence.json
# Output:
# CoN: 5,234
# CoT: 892
# CoM: 12,456
# CoP: 1,234
# CoA: 892
# CoE: 456
# CoI: 123
# CoV: 234
# CoId: 78

# AFTER integration, run again
# If ANY type shows 0 violations → FAILURE
# If ANY type shows >50% decrease → INVESTIGATE
```

**Prevention Checklist**:
- [ ] ALL 9 connascence types inventoried (with examples)
- [ ] Regression tests created for EACH type
- [ ] Unified orchestrator explicitly calls ALL detectors
- [ ] Phase 0 baseline established
- [ ] Phase 6 validation compares ALL types
- [ ] Rollback plan if ANY type broken

---

### FAILURE 2: Interface Apocalypse - CLI/VSCode/MCP All Broken (P0)

**Scenario**: Week 13. Users install v2.0.0. CLI gives import errors. VSCode extension crashes on startup. MCP server won't connect. **100% of user-facing interfaces unusable.**

**5 Whys (CLI)**:
1. **Why import errors?** `from analyzer.check_connascence import ConnascenceDetector` fails
2. **Why fails?** `check_connascence.py` was refactored to use `unified_orchestrator.py`
3. **Why breaks imports?** Old imports not redirected to new modules
4. **Why no redirection?** No backward compatibility layer created
5. **ROOT CAUSE**: Assumed users would update their code (they won't)

**5 Whys (VSCode)**:
1. **Why crashes on startup?** TypeScript calls Python analyzer via spawn
2. **Why spawn fails?** Analyzer entry point changed from `python -m analyzer.check_connascence` to `python -m analyzer.core.unified_orchestrator`
3. **Why entry point changed?** Integration refactored structure
4. **Why breaks VSCode?** Extension hardcoded old entry point
5. **ROOT CAUSE**: No integration testing of VSCode → Python interface

**5 Whys (MCP)**:
1. **Why won't connect?** MCP server expects `ConnascenceAnalyzer` class
2. **Why doesn't exist?** Replaced with `UnifiedOrchestrator`
3. **Why breaks MCP?** Class signature incompatible
4. **Why incompatible?** Different method names (`analyze()` vs `analyze_file()`)
5. **ROOT CAUSE**: No API versioning or backward compatibility

**Probability**: 60% (HIGH)
**Impact**: CATASTROPHIC (100% user impact)
**Risk Score**: 0.60 × 10 = **6.0 (P0 - CRITICAL)**

**Mitigation Strategies**:

**M2.1: Backward Compatibility Layer (MUST HAVE)**
```python
# analyzer/check_connascence.py (KEEP for backward compatibility)
"""
Backward Compatibility Adapter

This module provides the OLD API for existing users while delegating to new architecture.
"""

import warnings
from analyzer.core.unified_orchestrator import UnifiedOrchestrator

# Deprecated class - redirects to new implementation
class ConnascenceDetector:
    """
    DEPRECATED: Use UnifiedOrchestrator instead.

    This class maintained for backward compatibility with:
    - CLI (old imports)
    - VSCode extension (Python spawn calls)
    - MCP server (class expectations)
    - Legacy user code
    """

    def __init__(self, file_path: str, source_lines: list):
        warnings.warn(
            "ConnascenceDetector is deprecated. Use UnifiedOrchestrator.",
            DeprecationWarning,
            stacklevel=2
        )
        self.file_path = file_path
        self.source_lines = source_lines
        self._orchestrator = UnifiedOrchestrator()

    def analyze(self):
        """Old API - redirects to new analyze_file()."""
        return self._orchestrator.analyze_file(self.file_path)

    # ... all old methods redirected to new implementation

# Old function - redirects to new API
def analyze_file(file_path: str):
    """DEPRECATED: Old top-level function."""
    warnings.warn("Use UnifiedOrchestrator.analyze_file()", DeprecationWarning)
    orchestrator = UnifiedOrchestrator()
    return orchestrator.analyze_file(file_path)
```

**M2.2: Interface Integration Tests (MUST HAVE)**
```bash
# tests/integration/test_interfaces.py
"""
CRITICAL: Test ALL interfaces work with new architecture.
"""

def test_cli_still_works():
    """CLI commands work after integration."""
    result = subprocess.run(["connascence", "analyze", "test.py"], capture_output=True)
    assert result.returncode == 0, "CLI BROKEN"
    assert "violations" in result.stdout.decode(), "CLI output malformed"

def test_vscode_extension_still_works():
    """VSCode extension can call analyzer."""
    # Simulate VSCode's Python spawn call
    result = subprocess.run(
        ["python", "-m", "analyzer.check_connascence", "test.py"],
        capture_output=True
    )
    assert result.returncode == 0, "VSCode integration BROKEN"

def test_mcp_server_still_works():
    """MCP server can instantiate analyzer."""
    from mcp.server import MCPServer
    server = MCPServer()
    response = server.handle_analyze_request({"file_path": "test.py"})
    assert response["success"], "MCP integration BROKEN"
```

**M2.3: Phased Interface Migration (MUST HAVE)**
```markdown
# Phase 4: Interface Bug Fixes (REVISED)

## Sub-Phase 4a: Fix Existing Bugs (Week 7)
- Investigate 11 test errors
- Fix WITHOUT changing architecture
- Goal: Get to 0 errors with current structure

## Sub-Phase 4b: Create Compatibility Layer (Week 8)
- Create backward compatibility adapters
- Test OLD interfaces with NEW architecture
- Ensure 100% API compatibility

## Sub-Phase 4c: Gradual Migration (Week 9)
- Update CLI to use new architecture (behind compat layer)
- Update VSCode extension (behind compat layer)
- Update MCP server (behind compat layer)
- OLD API still works (deprecated but functional)

## Sub-Phase 4d: Deprecation Warnings (Post-Launch)
- Add deprecation warnings to old API
- Document migration guide
- Plan removal for v3.0.0 (6 months later)
```

**M2.4: Pre-Integration Interface Testing (MUST HAVE)**
```bash
# BEFORE Phase 1 (before ANY integration):
# 1. Fix existing 11 test errors
pytest tests/ -v
# Must achieve 0 errors before proceeding

# 2. Document ALL interface entry points
# - CLI: `connascence` command
# - VSCode: `python -m analyzer.check_connascence`
# - MCP: `from analyzer.check_connascence import ConnascenceDetector`
# - Legacy user code: Various imports

# 3. Create regression tests for EACH entry point
# 4. Run tests AFTER each phase
# 5. If ANY interface breaks → ROLLBACK phase

# VALIDATION GATE:
# Phase 1, 2, 3 → Can break internal structure
# Phase 4 → MUST restore all interfaces
# Phase 5+ → ALL interfaces 100% functional
```

**Prevention Checklist**:
- [ ] Backward compatibility layer created
- [ ] ALL interface entry points documented
- [ ] Regression tests for EACH interface
- [ ] Phased migration (fix bugs → compat layer → gradual migration)
- [ ] Deprecation warnings (not removal) in v2.0.0
- [ ] Actual removal deferred to v3.0.0

---

### FAILURE 3: NASA Engine Catastrophe - Compliance Drops to 60% (P0)

**Scenario**: Week 13. Enterprise validation shows NASA compliance dropped from baseline (unknown %) to 60%. Connascence is now **LESS compliant** than before integration. Users reject v2.0.0.

**5 Whys**:
1. **Why compliance dropped?** Replaced connascence NASA engine with SPEK's
2. **Why was replacement wrong?** SPEK covers Rules 3-6, connascence covers Rules 1-10
3. **Why didn't we know?** Phase 2 comparison was incomplete
4. **Why incomplete?** Only compared compliance %, not rule coverage
5. **ROOT CAUSE**: Assumed higher % = better engine (missed that SPEK only checks subset of rules)

**Probability**: 35% (MEDIUM)
**Impact**: CRITICAL (compliance is core selling point)
**Risk Score**: 0.35 × 9 = **3.15 (P0 - CRITICAL)**

**Mitigation Strategies**:

**M3.1: Comprehensive NASA Engine Comparison (MUST HAVE)**
```python
# scripts/compare_nasa_engines.py
"""
Compare BOTH NASA engines on EVERY dimension.
"""

def comprehensive_comparison():
    comparison = {
        "rule_coverage": compare_rule_coverage(),
        "compliance_score": compare_compliance_score(),
        "violation_detection": compare_violation_detection(),
        "false_positives": compare_false_positives(),
        "performance": compare_performance()
    }

    return comparison

def compare_rule_coverage():
    """CRITICAL: Check which rules each engine implements."""
    return {
        "spek": {
            "rules": ["RULE_3", "RULE_4", "RULE_5", "RULE_6"],  # 4 rules
            "description": {
                "RULE_3": "Functions ≤60 lines",
                "RULE_4": "≥2 assertions",
                "RULE_5": "No recursion",
                "RULE_6": "≤6 parameters"
            }
        },
        "connascence": {
            "rules": ["RULE_1", "RULE_2", ..., "RULE_10"],  # Check actual coverage
            "description": {
                # Document EACH rule connascence checks
            }
        },
        "analysis": {
            "spek_only": [],  # Rules SPEK has but connascence doesn't
            "connascence_only": [],  # Rules connascence has but SPEK doesn't
            "overlap": ["RULE_3", "RULE_4", "RULE_5", "RULE_6"],
            "recommendation": "DO NOT REPLACE - connascence has broader coverage"
        }
    }

def compare_compliance_score():
    """Compare % compliance on SAME codebase."""
    test_code = Path("test_packages/celery/")

    spek_score = run_spek_compliance(test_code)
    conn_score = run_connascence_compliance(test_code)

    return {
        "spek": {"score": spek_score, "rules_checked": 4},
        "connascence": {"score": conn_score, "rules_checked": 10},
        "winner": "connascence" if conn_score > spek_score else "spek",
        "note": "SPEK may show higher % but checks FEWER rules!"
    }
```

**M3.2: NASA Engine Decision Matrix (MUST HAVE)**
```markdown
# Phase 2: NASA Engine Decision (REVISED)

## Decision Criteria (ALL must be TRUE to replace)

| Criterion | SPEK | Connascence | Decision |
|-----------|------|-------------|----------|
| Rule Coverage (count) | 4 rules | ? rules | REQUIRED: Connascence ≤ SPEK |
| Compliance Score (%) | 99.0% | ? % | REQUIRED: Connascence ≤ SPEK |
| Violation Detection | ? violations | ? violations | REQUIRED: Equal or better |
| False Positives | ? FPs | ? FPs | REQUIRED: Equal or fewer |
| Performance | ? ms | ? ms | NICE TO HAVE: Faster |

### Replacement Scenarios

**Scenario A: Replace** (ALL criteria TRUE)
- SPEK covers ≥10 rules (same or more than connascence)
- SPEK achieves ≥connascence's compliance %
- SPEK detects ≥connascence's violations
- SPEK has ≤connascence's false positives
- **Action**: Replace connascence NASA engine with SPEK's

**Scenario B: Keep** (ANY criterion FALSE)
- SPEK covers <10 rules (LIKELY - only 4 rules known)
- SPEK achieves <connascence's compliance %
- SPEK detects <connascence's violations
- **Action**: Keep connascence NASA engine, integrate SPEK as SUPPLEMENTARY

**Scenario C: Merge** (Mixed results)
- SPEK better on some dimensions, connascence better on others
- **Action**: Create UnifiedNASAAnalyzer combining both
```

**M3.3: Phase 2 Go/No-Go Gate (MUST HAVE)**
```bash
# Phase 2 CANNOT proceed to Phase 3 unless:
# 1. NASA engine comparison complete
# 2. Decision documented with evidence
# 3. Regression tests pass
# 4. NASA compliance ≥baseline (preferably ≥99%)

# VALIDATION:
python scripts/validate_nasa_decision.py
# Must output: "✅ NASA engine decision validated"
# If outputs: "❌ NASA engine decision invalid" → BLOCK Phase 3
```

**Prevention Checklist**:
- [ ] Comprehensive NASA comparison (5 dimensions)
- [ ] Decision matrix (ALL criteria must be TRUE to replace)
- [ ] Phase 2 Go/No-Go gate (blocks Phase 3 if invalid)
- [ ] Regression tests for NASA compliance
- [ ] Fallback plan (keep connascence if SPEK worse)

---

## Part 2: High-Impact Failures (Severe but Recoverable)

### FAILURE 4: Performance Apocalypse - 10x Slowdown (P1)

**Scenario**: Week 13. Users report connascence v2.0.0 is 10x slower. Analysis that took 5s now takes 50s. Enterprise users revert to v1.x.

**5 Whys**:
1. **Why 10x slower?** Running both SPEK and connascence analyzers sequentially
2. **Why sequential?** Unified orchestrator calls each detector one-by-one
3. **Why not parallel?** No parallelization implemented
4. **Why not implemented?** Plan assumed sequential was acceptable
5. **ROOT CAUSE**: Underestimated cumulative overhead of dual analysis

**Probability**: 25% (LOW-MEDIUM)
**Impact**: HIGH (user abandonment)
**Risk Score**: 0.25 × 8 = **2.0 (P1 - HIGH)**

**Mitigation**: See full document for detailed mitigations...

### FAILURE 5: MECE Analysis Destroyed (P1)

**Scenario**: Week 13. MECE de-duplication analysis no longer works. 8-phase analysis crashes. Enterprise users lose unique capability.

**Probability**: 30% (MEDIUM)
**Impact**: HIGH (unique feature lost)
**Risk Score**: 0.30 × 7 = **2.1 (P1 - HIGH)**

**Mitigation**: See full document for detailed mitigations...

---

## Part 3: Medium-Impact Failures (Annoying but Non-Fatal)

### FAILURE 6: Test Suite Explosion - 10+ Hour CI/CD (P2)

**Scenario**: Week 13. CI/CD now takes 10+ hours (was 30 minutes). SPEK's 171 tests + connascence's 513 tests + integration tests = 800+ tests.

**Probability**: 40% (MEDIUM-HIGH)
**Impact**: MEDIUM (developer productivity)
**Risk Score**: 0.40 × 5 = **2.0 (P2 - MEDIUM)**

**Mitigation**: Parallel test execution, test categorization (smoke vs full)

### FAILURE 7: Constants Chaos - Conflicting Thresholds (P2)

**Scenario**: Week 13. God object detection inconsistent. Some code shows 15-method threshold, others 20-method. Users confused.

**Probability**: 50% (HIGH)
**Impact**: LOW (cosmetic, documentation fix)
**Risk Score**: 0.50 × 3 = **1.5 (P2 - MEDIUM)**

**Mitigation**: Document ALL threshold changes, make configurable

---

## Part 4: Low-Impact Failures (Recoverable, Low Priority)

### FAILURE 8: Documentation Rot (P3)

**Scenario**: Week 13. Documentation still references old APIs. Users confused but can figure it out.

**Probability**: 60% (HIGH)
**Impact**: LOW (user frustration)
**Risk Score**: 0.60 × 2 = **1.2 (P3 - LOW)**

### FAILURE 9: VSCode Extension Visual Bugs (P3)

**Scenario**: Week 13. VSCode extension works but CodeLens shows wrong counts. Minor visual glitches.

**Probability**: 40% (MEDIUM)
**Impact**: LOW (cosmetic)
**Risk Score**: 0.40 × 2 = **0.8 (P3 - LOW)**

---

## Part 5: Risk Summary & Prioritization

### Risk Matrix

| ID | Failure | Probability | Impact | Score | Priority |
|----|---------|-------------|--------|-------|----------|
| F1 | Connascence Taxonomy Destroyed | 40% | 10 | 4.0 | **P0** |
| F2 | Interface Apocalypse | 60% | 10 | 6.0 | **P0** |
| F3 | NASA Engine Catastrophe | 35% | 9 | 3.15 | **P0** |
| F4 | Performance Apocalypse | 25% | 8 | 2.0 | P1 |
| F5 | MECE Analysis Destroyed | 30% | 7 | 2.1 | P1 |
| F6 | Test Suite Explosion | 40% | 5 | 2.0 | P2 |
| F7 | Constants Chaos | 50% | 3 | 1.5 | P2 |
| F8 | Documentation Rot | 60% | 2 | 1.2 | P3 |
| F9 | VSCode Visual Bugs | 40% | 2 | 0.8 | P3 |

### Total Risk Score: **23.35** (HIGH)

**Risk Categories**:
- **P0 (Critical)**: 3 failures, total score 13.15 (56% of risk)
- **P1 (High)**: 2 failures, total score 4.1 (18% of risk)
- **P2 (Medium)**: 2 failures, total score 3.5 (15% of risk)
- **P3 (Low)**: 2 failures, total score 2.6 (11% of risk)

---

## Part 6: Go/No-Go Decision

### Current Assessment (Pre-Mitigation)

**Total Risk**: 23.35 (HIGH)
**P0 Risk**: 13.15 (Unacceptable)
**Recommendation**: **NO-GO** ❌

**Rationale**:
- 3 P0 failures with 40-60% probability = 135% chance of at least one P0 failure
- Interface Apocalypse (F2) has 60% probability alone = LIKELY
- Connascence Taxonomy (F1) would destroy core value proposition
- Without mitigations, failure is more likely than success

### Mitigation Requirements for GO

**To achieve GO status, MUST reduce P0 risk to <3.0:**

**F2 (Interface Apocalypse) - HIGHEST PRIORITY**:
- **Current**: 6.0 risk (60% × 10)
- **Mitigation**: Backward compatibility layer + phased migration + pre-integration bug fixes
- **Target**: Reduce probability to 15% → 1.5 risk
- **Required**: ALL 4 sub-mitigations (M2.1-M2.4)

**F1 (Connascence Taxonomy) - SECOND PRIORITY**:
- **Current**: 4.0 risk (40% × 10)
- **Mitigation**: Regression tests + orchestrator review + detector inventory
- **Target**: Reduce probability to 10% → 1.0 risk
- **Required**: ALL 4 sub-mitigations (M1.1-M1.4)

**F3 (NASA Engine Catastrophe) - THIRD PRIORITY**:
- **Current**: 3.15 risk (35% × 9)
- **Mitigation**: Comprehensive comparison + decision matrix + Go/No-Go gate
- **Target**: Reduce probability to 5% → 0.45 risk
- **Required**: ALL 3 sub-mitigations (M3.1-M3.3)

**Post-Mitigation P0 Risk Target**: <3.0
- F2: 1.5 (from 6.0) ✅
- F1: 1.0 (from 4.0) ✅
- F3: 0.45 (from 3.15) ✅
- **Total**: 2.95 (from 13.15) → **ACCEPTABLE** ✅

---

## Part 7: Mandatory Mitigations (Required for GO)

### Must-Have Mitigations (All P0 Risks)

1. **M1.1-M1.4**: Connascence Taxonomy Preservation
   - Regression tests for ALL 9 types
   - Orchestrator explicitly calls ALL detectors
   - Pre-integration inventory
   - Phase 0 baseline validation

2. **M2.1-M2.4**: Interface Stability
   - Backward compatibility layer
   - Interface integration tests
   - Phased migration (fix bugs → compat → gradual)
   - Pre-integration bug fixes (0 errors before Phase 1)

3. **M3.1-M3.3**: NASA Engine Validation
   - Comprehensive comparison (5 dimensions)
   - Decision matrix (evidence-based)
   - Phase 2 Go/No-Go gate

### Should-Have Mitigations (P1 Risks)

4. **M4.1-M4.3**: Performance Optimization
   - Parallel execution where possible
   - Benchmark after each phase
   - Cache integration

5. **M5.1-M5.2**: MECE Protection
   - Keep MECE entirely separate
   - Integration via orchestrator only

---

## Part 8: Revised Plan Requirements

### Changes Required to Plan v1

**Phase 0 (NEW REQUIREMENTS)**:
- [ ] Fix ALL 11 test errors BEFORE Phase 1
- [ ] Achieve 0 test failures baseline
- [ ] Create regression tests for ALL 9 connascence types
- [ ] Inventory ALL interface entry points
- [ ] Document NASA engine rule coverage

**Phase 1 (NEW REQUIREMENTS)**:
- [ ] Create backward compatibility layer (analyzer/check_connascence.py kept)
- [ ] Test ALL interfaces after constants integration
- [ ] Rollback if ANY interface breaks

**Phase 2 (NEW REQUIREMENTS)**:
- [ ] Comprehensive NASA comparison (5 dimensions, not just %)
- [ ] Decision matrix (ALL criteria must be TRUE to replace)
- [ ] Go/No-Go gate (blocks Phase 3 if invalid)

**Phase 4 (REVISED)**:
- [ ] Sub-Phase 4a: Fix existing bugs (no architecture changes)
- [ ] Sub-Phase 4b: Backward compatibility layer
- [ ] Sub-Phase 4c: Gradual migration
- [ ] Sub-Phase 4d: Deprecation warnings (removal deferred to v3.0.0)

---

## Next Steps (Iteration 1 → Iteration 2)

### Iteration 2 Research Focus

**Deep Dive into P0 Risks**:
1. **F2 (Interface Apocalypse)**:
   - Research: Run full test suite, identify ALL 11 errors
   - Research: Document ALL interface entry points (CLI, VSCode, MCP, legacy)
   - Research: Test backward compatibility strategies

2. **F1 (Connascence Taxonomy)**:
   - Research: Inventory ALL 9 connascence detectors (confirm they exist)
   - Research: Create test cases for EACH type
   - Research: Verify orchestrator can call both SPEK + connascence

3. **F3 (NASA Engine)**:
   - Research: Run BOTH NASA engines on same codebase
   - Research: Compare rule coverage (1-10 vs 3-6)
   - Research: Measure compliance % for BOTH engines

### Plan v2 Requirements

**Must Address**:
- [ ] All P0 mitigations integrated into phases
- [ ] Phase 0 expanded (baseline validation + bug fixes)
- [ ] Phase 2 Go/No-Go gate formalized
- [ ] Phase 4 revised (phased migration)
- [ ] Timeline updated (likely 16-20 weeks with mitigations)

---

**Document Version**: 1.0 (Post-Plan-v1)
**Last Updated**: 2025-10-19
**Status**: ✅ Premortem v1 Complete → Next: Research P0 Risks (Iteration 2)
**Risk Level**: HIGH (23.35) → Target: MEDIUM (<10.0 post-mitigation)
**Confidence**: 60% (need Iteration 2 research to validate mitigations)
**Recommendation**: **NO-GO** (until P0 mitigations implemented)
