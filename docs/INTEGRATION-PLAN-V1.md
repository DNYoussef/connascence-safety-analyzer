# SPEK v2 + Connascence Integration Plan v1

**Date**: 2025-10-19
**Iteration**: 1 of 4
**Version**: 1.0 (Pre-Premortem)
**Strategy**: ENHANCEMENT (Integrate SPEK's engines, preserve ALL connascence capabilities)

---

## Executive Summary

### Mission
Integrate SPEK v2's production-hardened NASA compliance engine, quality gates, and bug fixes into connascence while preserving all 9 connascence types, MECE, Six Sigma, multi-language support, and enterprise interfaces (CLI/VSCode/MCP).

### Approach
**8-Phase Integration** over 12-16 weeks with zero regression tolerance:

| Phase | Goal | Duration | Risk Level |
|-------|------|----------|------------|
| 0 | Validation Baseline | 1 week | Low |
| 1 | Foundation (Constants + Engines) | 2 weeks | Medium |
| 2 | NASA Engine Decision | 1 week | High |
| 3 | Quality Gates Integration | 2 weeks | Medium |
| 4 | Interface Bug Fixes | 2-3 weeks | High |
| 5 | Production Hardening | 2 weeks | Medium |
| 6 | Enterprise Validation | 1 week | Low |
| 7 | Production Deployment | 1 week | Low |

**Total**: 12-16 weeks | **Risk**: Medium-High | **Confidence**: 75% (pre-premortem)

---

## Phase 0: Validation Baseline (Week 1)

### Goal
Establish comprehensive baseline metrics BEFORE integration to measure success/failure.

### Tasks

**0.1 Test Suite Validation** (2 days)
```bash
# Run full test suite
cd C:\Users\17175\Desktop\connascence
pytest tests/ -v --tb=short > baseline_test_results.txt

# Expected issues:
# - 513 tests collected
# - 11 errors (need identification)
# - 4 skipped
```

**Deliverables**:
- [ ] `baseline_test_results.txt` - Full test output
- [ ] `test_failures.md` - Analysis of 11 errors
- [ ] Decision: Are these integration bugs or test environment issues?

**0.2 NASA Compliance Comparison** (2 days)
```bash
# Run both NASA engines on same codebase
python -m analyzer.nasa_engine.nasa_analyzer analyze connascence/src/ > nasa_connascence.json
python -m spek_analyzer.engines.compliance_validator analyze connascence/src/ > nasa_spek.json

# Compare:
# - Rule coverage (1-10 vs 3-6)
# - Compliance scores (connascence % vs SPEK 99.0%)
# - Violation detection (which finds more issues?)
```

**Deliverables**:
- [ ] `nasa_comparison.md` - Side-by-side comparison
- [ ] Decision: Replace, merge, or keep connascence NASA engine?

**0.3 Performance Baseline** (1 day)
```bash
# Benchmark connascence on 1000-file codebase
time connascence analyze test_packages/celery/ > celery_baseline.json

# Metrics to capture:
# - Total analysis time (seconds)
# - Cache hit rate (%)
# - Memory usage (MB)
# - Violations detected
```

**Deliverables**:
- [ ] `performance_baseline.md` - Current performance metrics
- [ ] Target: Maintain or improve performance after integration

**0.4 Feature Inventory** (1 day)
```bash
# Document all working features
connascence --help
code --list-extensions | grep connascence
# Test MCP server manually
```

**Deliverables**:
- [ ] `feature_inventory.md` - ALL working features documented
- [ ] Acceptance criteria: ALL features must work after integration

**Success Criteria**:
- ✅ All 513+ tests running (passing or failing documented)
- ✅ NASA comparison complete (decision documented)
- ✅ Performance baseline captured
- ✅ Feature inventory complete

---

## Phase 1: Foundation - Constants & Engines (Weeks 2-3)

### Goal
Copy SPEK's `constants/` and `engines/` into connascence without breaking existing functionality.

### Tasks

**1.1 Constants Migration** (3 days)
```bash
# Create new constants directory
cd C:\Users\17175\Desktop\connascence\analyzer
mkdir -p constants_spek

# Copy SPEK constants
cp C:\Users\17175\Desktop\spek-v2-rebuild\analyzer\constants/*.py constants_spek/

# Merge thresholds
python scripts/merge_constants.py \
  --spek constants_spek/thresholds.py \
  --connascence analyzer/constants.py \
  --output analyzer/constants/thresholds.py
```

**Merge Strategy**:
```python
# analyzer/constants/thresholds.py (UNIFIED)

# === SPEK v2 Thresholds (NASA-aligned) ===
MAXIMUM_FUNCTION_LENGTH_LINES = 60  # NASA Rule 3
NASA_PARAMETER_THRESHOLD = 6        # NASA Rule 6
GOD_OBJECT_METHOD_THRESHOLD = 20    # SPEK's threshold

# === Connascence Thresholds (Extended) ===
CONNASCENCE_GOD_OBJECT_THRESHOLD = 15  # More strict (keep)
MECE_SIMILARITY_THRESHOLD = 0.8        # Unique to connascence
SIX_SIGMA_DPMO_THRESHOLD = 3.4         # Unique to connascence

# === Unified (Best of Both) ===
# Use SPEK's NASA thresholds (proven 99.0% compliance)
# Use connascence's MECE/Six Sigma thresholds (unique capabilities)
```

**Deliverables**:
- [ ] `analyzer/constants/` - Unified constants directory
- [ ] `migration_log.md` - All changed thresholds documented
- [ ] Regression test: No connascence tests fail due to constant changes

**1.2 Engines Integration** (4 days)
```bash
# Copy SPEK engines as new modules
mkdir -p analyzer/engines_spek
cp C:\Users\17175\Desktop\spek-v2-rebuild\analyzer\engines/*.py analyzer/engines_spek/

# Adapt imports
# - Change from `..constants` to `analyzer.constants`
# - Add connascence-specific imports (utils.types, etc.)
```

**Integration Pattern**:
```python
# analyzer/engines/syntax_analyzer.py (NEW - from SPEK)
"""
SPEK v2 Syntax Analyzer - Integrated into Connascence
Provides AST-based syntax analysis with production-hardened bug fixes.
"""

import ast
from typing import Dict, List, Any
from utils.types import ConnascenceViolation  # Connascence integration

class SyntaxAnalyzer:
    """SPEK's syntax analyzer adapted for connascence."""

    def analyze(self, source_code: str, language: str = "python") -> Dict[str, Any]:
        # SPEK's implementation (259 LOC)
        # Returns ConnascenceViolation objects (adapted)
        pass
```

**Deliverables**:
- [ ] `analyzer/engines_spek/` - SPEK engines integrated
- [ ] Import adapters for connascence types
- [ ] Regression test: Existing connascence tests still pass

**1.3 Orchestrator Integration** (3 days)
```python
# analyzer/core/unified_orchestrator.py (NEW)
"""
Unified Orchestrator - Combines SPEK's engines with connascence's detectors.
"""

from analyzer.engines_spek.syntax_analyzer import SyntaxAnalyzer  # SPEK
from analyzer.engines_spek.pattern_detector import PatternDetector  # SPEK
from analyzer.engines_spek.compliance_validator import ComplianceValidator  # SPEK

from analyzer.detectors.position_detector import PositionDetector  # Connascence
from analyzer.detectors.algorithm_detector import AlgorithmDetector  # Connascence
from analyzer.dup_detection.mece_analyzer import MECEAnalyzer  # Connascence
# ... all 9 connascence detectors

class UnifiedOrchestrator:
    """Orchestrates both SPEK and connascence analyzers."""

    def analyze_file(self, file_path: str) -> List[ConnascenceViolation]:
        violations = []

        # Run SPEK engines (syntax, patterns, compliance)
        violations.extend(self.spek_syntax.analyze(...))
        violations.extend(self.spek_patterns.detect(...))
        violations.extend(self.spek_compliance.validate(...))

        # Run connascence detectors (all 9 types)
        violations.extend(self.connascence_position.detect(...))
        violations.extend(self.connascence_algorithm.detect(...))
        # ... all 9 detectors

        # Run MECE analysis (unique to connascence)
        violations.extend(self.mece_analyzer.analyze(...))

        return self._deduplicate(violations)
```

**Deliverables**:
- [ ] `analyzer/core/unified_orchestrator.py` - Unified entry point
- [ ] Deduplication logic (avoid duplicate violations from SPEK + connascence)
- [ ] Integration tests: Both engines work together

**Success Criteria**:
- ✅ SPEK constants integrated (merged with connascence)
- ✅ SPEK engines copied and adapted
- ✅ Unified orchestrator created
- ✅ Zero regressions: All baseline tests still pass
- ✅ Performance maintained: ≤5% slowdown acceptable

---

## Phase 2: NASA Engine Decision (Week 4)

### Goal
Make evidence-based decision: Replace, merge, or keep connascence's NASA engine.

### Decision Tree

**Option A: Replace with SPEK's Engine**
- **Condition**: SPEK's compliance_validator.py achieves ≥99% AND covers ≥connascence's rules
- **Action**: Replace `analyzer/nasa_engine/nasa_analyzer.py` with SPEK's validator
- **Risk**: May lose connascence-specific NASA rules

**Option B: Keep Connascence's Engine**
- **Condition**: Connascence's nasa_analyzer.py achieves ≥99% AND covers Rules 1-10 (more than SPEK's 3-6)
- **Action**: Keep connascence's, mark SPEK's as fallback
- **Risk**: Misses SPEK's production-hardening benefits

**Option C: Merge Both**
- **Condition**: Both have unique strengths (e.g., connascence covers 1-10, SPEK has better validation)
- **Action**: Create `nasa_engine_unified.py` combining both
- **Risk**: Complexity, maintenance burden

### Tasks

**2.1 Comprehensive NASA Comparison** (2 days)
```python
# scripts/compare_nasa_engines.py
"""
Run both NASA engines on same codebase, compare:
- Rule coverage (which rules implemented?)
- Compliance scores (what %)
- Violation detection (which finds more issues?)
- False positives (which is more accurate?)
"""

import subprocess
import json

def compare_engines():
    # Run connascence NASA engine
    connascence_result = run_connascence_nasa("test_packages/celery/")

    # Run SPEK NASA engine
    spek_result = run_spek_nasa("test_packages/celery/")

    # Compare
    comparison = {
        "connascence": {
            "rule_coverage": extract_rules(connascence_result),
            "compliance_score": calc_compliance(connascence_result),
            "violations_found": count_violations(connascence_result)
        },
        "spek": {
            "rule_coverage": extract_rules(spek_result),
            "compliance_score": calc_compliance(spek_result),
            "violations_found": count_violations(spek_result)
        },
        "recommendation": decide_winner(connascence_result, spek_result)
    }

    return comparison
```

**Deliverables**:
- [ ] `nasa_engine_comparison.json` - Quantitative comparison
- [ ] `nasa_engine_decision.md` - Recommendation with evidence
- [ ] Decision: Option A, B, or C with justification

**2.2 Implementation** (2 days)

**If Option A (Replace)**:
```bash
# Backup connascence NASA engine
mv analyzer/nasa_engine analyzer/nasa_engine_legacy

# Copy SPEK's compliance validator as new NASA engine
mkdir analyzer/nasa_engine
cp analyzer/engines_spek/compliance_validator.py analyzer/nasa_engine/nasa_analyzer.py

# Adapt to connascence interfaces
sed -i 's/ComplianceValidator/NASAAnalyzer/g' analyzer/nasa_engine/nasa_analyzer.py
```

**If Option B (Keep)**:
```bash
# No changes to nasa_engine/
# Mark SPEK's compliance_validator as supplementary

# Document decision
echo "Keeping connascence's NASA engine (superior coverage)" > docs/NASA_ENGINE_DECISION.md
```

**If Option C (Merge)**:
```python
# analyzer/nasa_engine/nasa_analyzer_unified.py
"""
Unified NASA Analyzer - Best of SPEK + Connascence
"""

from ..engines_spek.compliance_validator import ComplianceValidator  # SPEK's validator
from .nasa_analyzer_legacy import NASAAnalyzer as ConnascenceNASA  # Connascence's

class UnifiedNASAAnalyzer:
    def __init__(self):
        self.spek_validator = ComplianceValidator()  # SPEK: Rules 3-6, 99.0% accuracy
        self.connascence_analyzer = ConnascenceNASA()  # Connascence: Rules 1-10, unknown %

    def analyze_file(self, file_path: str) -> List[ConnascenceViolation]:
        violations = []

        # Run both analyzers
        spek_violations = self.spek_validator.validate(...)
        connascence_violations = self.connascence_analyzer.analyze_file(...)

        # Merge (deduplicate, choose highest-confidence)
        violations = self._merge_violations(spek_violations, connascence_violations)

        return violations
```

**Deliverables**:
- [ ] NASA engine integrated (Option A, B, or C implemented)
- [ ] Regression tests: NASA compliance ≥baseline
- [ ] Documentation: Decision rationale documented

**Success Criteria**:
- ✅ Evidence-based decision made (not arbitrary)
- ✅ NASA compliance ≥99.0% (SPEK's standard)
- ✅ No regressions in NASA rule detection
- ✅ Backward compatibility: Existing connascence NASA tests pass

---

## Phase 3: Quality Gates Integration (Weeks 5-6)

### Goal
Integrate SPEK's quality gates, test coverage strategy, and edge case handling into connascence.

### Tasks

**3.1 Coverage Configuration** (2 days)
```ini
# .coveragerc (NEW - adapted from SPEK)
[run]
source = analyzer
omit =
    # Legacy modules (0% coverage, deferred)
    analyzer/archive/*
    analyzer/enterprise/*  # Enterprise features (separate coverage target)

    # Test files
    tests/*

[report]
include =
    # Core modules (80% coverage target)
    analyzer/core/*
    analyzer/engines_spek/*
    analyzer/detectors/*
    analyzer/nasa_engine/*

fail_under = 80.0  # SPEK's standard
precision = 2
show_missing = True
skip_covered = False
```

**Run Coverage**:
```bash
pytest tests/ --cov=analyzer --cov-config=.coveragerc --cov-report=html --cov-report=term

# Expected:
# - Core modules: ≥80% coverage
# - Total: May be <80% (due to legacy code)
# - Strategy: Focused on production-ready core
```

**Deliverables**:
- [ ] `.coveragerc` - Coverage configuration (SPEK's strategy)
- [ ] Coverage report: ≥80% on core modules
- [ ] CI/CD integration: `coverage.yml` workflow

**3.2 Quality Gates** (3 days)
```yaml
# .github/workflows/quality_gates.yml (ENHANCED from SPEK)
name: Quality Gates

on: [push, pull_request]

jobs:
  quality-gates:
    runs-on: ubuntu-latest
    steps:
      - name: Run tests
        run: pytest tests/ --tb=short

      - name: Check coverage
        run: |
          pytest --cov=analyzer --cov-config=.coveragerc --cov-report=term
          # Fail if <80% on core modules

      - name: NASA compliance check
        run: |
          python -m analyzer.nasa_engine.nasa_analyzer analyze analyzer/
          # Fail if <99% compliance

      - name: Zero regressions policy
        run: |
          python scripts/check_regressions.py
          # Fail if ANY critical bugs introduced

      - name: Performance validation
        run: |
          python scripts/benchmark.py
          # Fail if >10% slowdown vs baseline
```

**Deliverables**:
- [ ] `.github/workflows/quality_gates.yml` - Automated quality checks
- [ ] Zero regressions policy enforced
- [ ] Performance regression detection

**3.3 Edge Case Documentation** (2 days)
```markdown
# docs/EDGE_CASES.md (NEW - adopted from SPEK)

## Edge Cases (Non-Blocking)

### 1. C++ Regex Pattern Matching (3 failures)
- **Issue**: `strcpy|sprintf|gets` detects 2/3 instances
- **Impact**: Minor (Python is primary language)
- **Fix**: Enhance regex patterns in Phase 5
- **Workaround**: Manual code review for C/C++ files

### 2. Binary Literal Detection (1 failure)
- **Issue**: `0b1010` binary literals not detected as magic literals
- **Impact**: Minor (rare in practice)
- **Fix**: Add binary literal patterns
- **Workaround**: Manual review

... (document all edge cases)
```

**Deliverables**:
- [ ] `docs/EDGE_CASES.md` - All known edge cases documented
- [ ] Acceptance criteria: Edge cases don't block production
- [ ] Roadmap: Edge case fixes planned for post-launch

**Success Criteria**:
- ✅ Coverage ≥80% on core modules (SPEK's standard)
- ✅ Quality gates automated in CI/CD
- ✅ Edge cases documented (non-blocking)
- ✅ Zero regressions policy enforced

---

## Phase 4: Interface Bug Fixes (Weeks 7-9)

### Goal
Fix 11 test errors, restore CLI/VSCode/MCP to 100% functionality.

### Tasks

**4.1 Test Failure Analysis** (3 days)
```bash
# Run full test suite with verbose output
pytest tests/ -v --tb=long > test_failures_detailed.txt

# Analyze each of 11 errors
python scripts/analyze_test_failures.py test_failures_detailed.txt
```

**Expected Categories**:
1. **Import errors** (connascence vs SPEK module conflicts)
2. **Interface bugs** (CLI/VSCode/MCP integration)
3. **Test environment issues** (paths, dependencies)

**Deliverables**:
- [ ] `test_failures_detailed.txt` - Full error traces
- [ ] `test_failure_analysis.md` - Categorized failures
- [ ] Fix plan: Priority order (critical → low)

**4.2 CLI Bug Fixes** (3 days)
```bash
# Test CLI workflows
connascence analyze --help
connascence analyze . --profile strict
connascence analyze . --format html --output report.html

# Common issues:
# - Import errors after SPEK integration
# - Threshold changes breaking output
# - SARIF format incompatible with new structure
```

**Fix Strategy**:
```python
# cli/__init__.py (FIX imports)
# BEFORE:
from analyzer.check_connascence import ConnascenceDetector

# AFTER:
from analyzer.core.unified_orchestrator import UnifiedOrchestrator
```

**Deliverables**:
- [ ] CLI 100% functional (all workflows working)
- [ ] Regression tests: CLI workflow tests passing
- [ ] Documentation: CLI changes documented

**4.3 VSCode Extension Fixes** (4 days)
```typescript
// interfaces/vscode/src/services/analyzer-client.ts
// Fix integration with new analyzer structure

import { UnifiedOrchestrator } from '../../../../analyzer/core/unified_orchestrator';

class AnalyzerClient {
  async analyzeFile(filePath: string): Promise<Violation[]> {
    // Before: Called old ConnascenceDetector
    // After: Call UnifiedOrchestrator

    const orchestrator = new UnifiedOrchestrator();
    const violations = await orchestrator.analyze_file(filePath);

    return this.convertToVSCodeFormat(violations);
  }
}
```

**Testing**:
```bash
cd interfaces/vscode
npm install
npm test  # Run all 50+ tests

# Manual testing:
code --install-extension connascence-safety-analyzer-*.vsix
# Test real-time analysis, CodeLens, auto-fix
```

**Deliverables**:
- [ ] VSCode extension 100% functional
- [ ] All TypeScript tests passing
- [ ] Real-time analysis working
- [ ] CodeLens annotations working
- [ ] Auto-fix suggestions working

**4.4 MCP Server Fixes** (3 days)
```python
# mcp/server.py (FIX integration)
from analyzer.core.unified_orchestrator import UnifiedOrchestrator

class MCPServer:
    def __init__(self):
        self.orchestrator = UnifiedOrchestrator()

    async def handle_analyze_request(self, params):
        # Use unified orchestrator instead of old analyzer
        violations = self.orchestrator.analyze_file(params['file_path'])
        return self.format_response(violations)
```

**Testing**:
```bash
# Start MCP server
python -m mcp.server

# Test with Claude
# (manually verify Claude integration works)
```

**Deliverables**:
- [ ] MCP server 100% functional
- [ ] Claude integration verified
- [ ] Response format compatible

**Success Criteria**:
- ✅ All 513+ tests passing (0 errors, 0 failures)
- ✅ CLI 100% functional (all workflows)
- ✅ VSCode extension 100% functional (all features)
- ✅ MCP server 100% functional (Claude integration)
- ✅ Zero regressions: All features work as before integration

---

## Phase 5: Production Hardening (Weeks 10-11)

### Goal
Apply SPEK's production-hardening lessons, validate bug fixes, performance optimization.

### Tasks

**5.1 God Object Bug Validation** (2 days)
```python
# scripts/validate_god_object_detection.py
"""
Verify all god object detection uses correct line counting:
- CORRECT: node.end_lineno - node.lineno + 1
- WRONG: len(node.body)
"""

import ast
import re

def validate_line_counting(file_path):
    with open(file_path) as f:
        code = f.read()

    # Search for line counting patterns
    if "len(node.body)" in code:
        print(f"❌ {file_path}: Using WRONG statement counting")
        return False

    if "end_lineno - lineno" in code:
        print(f"✅ {file_path}: Using CORRECT line counting")
        return True

    return True  # Not applicable

# Check all detectors
files = [
    "analyzer/detectors/god_object_detector.py",
    "analyzer/ast_engine/analyzer_orchestrator.py",
    "analyzer/engines_spek/pattern_detector.py",
    # ... all files with god object detection
]

for file in files:
    validate_line_counting(file)
```

**Deliverables**:
- [ ] `god_object_validation_report.md` - All detectors validated
- [ ] Bug fixes applied if needed (unlikely based on research)
- [ ] Regression tests: God object detection accurate

**5.2 Performance Optimization** (3 days)
```bash
# Benchmark before/after integration
python scripts/benchmark.py --baseline baseline_performance.json --current current_performance.json

# Expected:
# - Analysis time: Maintain ±5% of baseline
# - Cache hit rate: Maintain 50-90%
# - Memory usage: ±10% acceptable
```

**Optimization Targets**:
- Unified orchestrator efficiency (avoid duplicate AST parsing)
- Cache integration (SPEK engines use connascence caching)
- Memory management (cleanup after large analyses)

**Deliverables**:
- [ ] Performance maintained: ≤5% slowdown
- [ ] Cache hit rate: ≥50%
- [ ] Memory usage: <150MB typical

**5.3 Edge Case Fixes** (3 days)
```python
# Fix documented edge cases from SPEK + connascence
# - C++ regex patterns (enhance `strcpy|sprintf|gets` detection)
# - Binary literals (add `0b` pattern)
# - Execution time precision (update test expectations)
```

**Deliverables**:
- [ ] Edge cases fixed (if blocking)
- [ ] Tests updated (for non-blocking edge cases)
- [ ] Documentation: Remaining edge cases noted

**5.4 Zero Regressions Validation** (2 days)
```bash
# Run comprehensive regression suite
pytest tests/ --tb=short -v > regression_validation.txt

# Compare to baseline
python scripts/compare_test_results.py baseline_test_results.txt regression_validation.txt

# Expected:
# - 0 new failures
# - ≥baseline pass rate
# - All critical tests passing
```

**Deliverables**:
- [ ] Zero regressions confirmed
- [ ] All tests passing (513+)
- [ ] Production readiness validated

**Success Criteria**:
- ✅ God object detection validated (correct line counting)
- ✅ Performance maintained (≤5% slowdown)
- ✅ Edge cases addressed (fixes or documentation)
- ✅ Zero regressions: All tests passing, no features broken

---

## Phase 6: Enterprise Validation (Week 12)

### Goal
Validate integration on real enterprise codebases (Fortune 500 scale).

### Tasks

**6.1 Enterprise Codebase Testing** (3 days)
```bash
# Test on same codebases as original connascence validation
connascence analyze test_packages/celery/ > celery_integrated.json
connascence analyze test_packages/curl/ > curl_integrated.json
connascence analyze test_packages/express/ > express_integrated.json

# Compare to baseline
python scripts/compare_enterprise_results.py \
  --baseline celery_baseline.json \
  --current celery_integrated.json
```

**Expected Results**:
- **Celery (4,630 violations baseline)**: ≥4,630 violations detected (may increase with SPEK's engines)
- **curl (1,061 violations)**: ≥1,061 violations
- **Express (52 violations)**: ≥52 violations

**Deliverables**:
- [ ] Enterprise validation report
- [ ] Violation count comparison (baseline vs integrated)
- [ ] Decision: If violations significantly different, investigate why

**6.2 Self-Analysis Validation** (2 days)
```bash
# Run on connascence itself (dogfooding)
connascence analyze . --exclude test_packages/ > self_analysis_integrated.json

# Compare to baseline (46,576 violations)
python scripts/compare_self_analysis.py \
  --baseline self_analysis_baseline.json \
  --current self_analysis_integrated.json
```

**Deliverables**:
- [ ] Self-analysis report
- [ ] Violation comparison (should be similar ±10%)
- [ ] New violations (if any) analyzed and justified

**Success Criteria**:
- ✅ Enterprise validation: ≥baseline violations detected
- ✅ Self-analysis: Similar violation count (±10%)
- ✅ No unexpected regressions in detection accuracy
- ✅ Performance at scale: <30s for 1000-file codebase

---

## Phase 7: Production Deployment (Week 13)

### Goal
Deploy integrated analyzer to production, monitor for issues.

### Tasks

**7.1 Release Preparation** (2 days)
```bash
# Version bump
# connascence v2.0.0 (major version - breaking changes in internal structure)

# Changelog
cat > CHANGELOG.md << 'EOF'
# Changelog

## [2.0.0] - 2025-XX-XX

### Added
- SPEK v2 NASA compliance engine (99.0% compliance)
- Production-hardened quality gates
- Enhanced syntax analysis (SPEK's engines)
- Unified orchestrator (best of SPEK + connascence)

### Fixed
- CLI integration bugs (11 test errors)
- VSCode extension stability
- MCP server Claude integration

### Changed
- Unified constants (SPEK's structure + connascence values)
- Enhanced NASA compliance (≥99.0%)
- Improved test coverage (≥80% core modules)

### Maintained
- All 9 connascence types (CoN, CoT, CoM, CoP, CoA, CoE, CoI, CoV, CoId)
- MECE de-duplication analysis
- Six Sigma integration
- Multi-language support (Python, C/C++, JS)
- Intelligent caching (50-90% speedup)
EOF
```

**Deliverables**:
- [ ] Version bump to v2.0.0
- [ ] Changelog complete
- [ ] Release notes drafted

**7.2 Deployment** (1 day)
```bash
# Build packages
python -m build

# Build VSCode extension
cd interfaces/vscode
npm run package

# Publish to PyPI (test first)
python -m twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ connascence-analyzer==2.0.0

# If successful, publish to production PyPI
python -m twine upload dist/*
```

**Deliverables**:
- [ ] PyPI package published (v2.0.0)
- [ ] VSCode extension published (Marketplace)
- [ ] Documentation updated (installation guides)

**7.3 Post-Deployment Monitoring** (2 days)
```bash
# Monitor for issues
# - GitHub issues (user bug reports)
# - Download metrics (adoption)
# - CI/CD failures (enterprise users)
```

**Rollback Plan**:
```bash
# If critical issues discovered:
# 1. Unpublish v2.0.0 from PyPI
# 2. Republish v1.x (last stable)
# 3. Investigate and fix
# 4. Re-release as v2.0.1
```

**Deliverables**:
- [ ] Production deployment successful
- [ ] Monitoring dashboard active
- [ ] Rollback plan tested (dry run)

**Success Criteria**:
- ✅ PyPI package published and installable
- ✅ VSCode extension published and installable
- ✅ No critical bugs in first 48 hours
- ✅ Positive user feedback / no major complaints

---

## Acceptance Criteria (100% Production Ready)

### Functionality ✅
- [ ] All 9 connascence types detection working
- [ ] MECE de-duplication analysis working
- [ ] Six Sigma integration working
- [ ] Multi-language support (Python, C/C++, JS) working
- [ ] NASA compliance ≥99.0%

### Interfaces ✅
- [ ] CLI 100% functional (all workflows)
- [ ] VSCode extension 100% functional (real-time analysis, CodeLens, auto-fix)
- [ ] MCP server 100% functional (Claude integration)

### Quality ✅
- [ ] ≥80% test coverage on core modules
- [ ] 513+ tests passing (0 failures, 0 errors)
- [ ] Zero regressions (all features work)
- [ ] Edge cases documented (non-blocking)

### Performance ✅
- [ ] Maintain 50-90% caching speedup
- [ ] <2s analysis time for typical file
- [ ] <30s for 1000-file codebase
- [ ] ≤5% slowdown vs baseline

### Documentation ✅
- [ ] Integration plan documented
- [ ] NASA engine decision documented
- [ ] Edge cases documented
- [ ] Changelog complete
- [ ] Release notes complete

---

## Risk Mitigation Strategies

### High Risks

**Risk 1: Breaking Connascence Taxonomy**
- **Mitigation**: Regression tests for ALL 9 types before ANY integration
- **Validation**: Run connascence-specific tests after each phase
- **Rollback**: Revert integration if any type breaks

**Risk 2: CLI/VSCode/MCP Breakage**
- **Mitigation**: Fix existing bugs BEFORE integration
- **Validation**: Test all interfaces after each phase
- **Rollback**: Keep v1.x interfaces as fallback

**Risk 3: NASA Engine Regression**
- **Mitigation**: Evidence-based decision (Phase 2)
- **Validation**: Comprehensive comparison before replacement
- **Rollback**: Keep connascence NASA engine as backup

### Medium Risks

**Risk 4: Performance Degradation**
- **Mitigation**: Benchmark after each phase
- **Validation**: ≤5% slowdown acceptable
- **Rollback**: Remove SPEK engines if >10% slowdown

**Risk 5: Test Suite Conflicts**
- **Mitigation**: Separate SPEK/connascence tests initially
- **Validation**: Gradual integration of test suites
- **Rollback**: Revert test changes if CI/CD breaks

---

## Timeline & Milestones

```
Week 1  : Phase 0 - Validation Baseline
Week 2-3: Phase 1 - Foundation (Constants + Engines)
Week 4  : Phase 2 - NASA Engine Decision
Week 5-6: Phase 3 - Quality Gates Integration
Week 7-9: Phase 4 - Interface Bug Fixes
Week 10-11: Phase 5 - Production Hardening
Week 12: Phase 6 - Enterprise Validation
Week 13: Phase 7 - Production Deployment
```

**Critical Path**:
1. Phase 0 (baseline) → Phase 1 (foundation) → Phase 2 (NASA decision)
2. Phase 4 (interface fixes) - **HIGH RISK** (11 test errors)
3. Phase 6 (enterprise validation) - **GO/NO-GO GATE**

**Buffers**:
- Phase 4: 2-3 weeks (high uncertainty)
- Phase 5: +1 week if performance issues
- Total: 12-16 weeks (4-week buffer)

---

## Next Steps (Pre-Premortem)

### Before Premortem v1
1. [ ] Review plan for completeness
2. [ ] Identify missing tasks/phases
3. [ ] Estimate effort (hours) for each task
4. [ ] Identify dependencies (which tasks block others?)

### Premortem v1 Questions
1. What could cause Phase 4 (interface fixes) to fail?
2. What if NASA comparison shows connascence is worse?
3. What if performance degrades >10%?
4. What if enterprise validation finds new bugs?
5. What are the unknown unknowns?

---

**Document Version**: 1.0 (Pre-Premortem)
**Last Updated**: 2025-10-19
**Status**: ✅ Plan v1 Complete → Next: Run Premortem v1
**Confidence**: 70% (need premortem to validate assumptions)
**Risk Level**: Medium-High (Phase 4 is critical path with high uncertainty)
