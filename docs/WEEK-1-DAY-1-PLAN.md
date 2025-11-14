# Week 1 Day 1 Implementation Plan
## Connascence Analyzer - Critical Blockers Resolution

**Date**: 2025-11-13
**Target Completion**: Week 1 (5 working days)
**Total Effort**: 28.5-48.5 hours
**Critical Path**: ISSUE-001 -> ISSUE-002 -> ISSUE-003 (parallel: ISSUE-004)

---

## Executive Summary

This plan addresses **4 CRITICAL blocking issues** preventing CI/CD deployment and 100% test collection. Issues are ordered by dependency chain and include complete implementation details, verification commands, and rollback strategies.

**Success Criteria**:
- 100% test collection (496/496 tests)
- All 10 blocked tests passing
- Real god object thresholds enforced
- CI/CD pipeline green

---

## Table of Contents

1. [ISSUE-001: Fix Detector Pool AttributeError](#issue-001-fix-detector-pool-attributeerror)
2. [ISSUE-002: Fix Import Path Issues](#issue-002-fix-import-path-issues)
3. [ISSUE-003: Register Missing Pytest Markers](#issue-003-register-missing-pytest-markers)
4. [ISSUE-004: Fix CI/CD Threshold Manipulation](#issue-004-fix-cicd-threshold-manipulation)
5. [Dependency Graph](#dependency-graph)
6. [Daily Schedule](#daily-schedule)
7. [Risk Mitigation](#risk-mitigation)

---

## ISSUE-001: Fix Detector Pool AttributeError

### Priority: P0 - BLOCKING
**Effort**: 16-24 hours
**Blocks**: 10/16 tests, ISSUE-005, ISSUE-008
**Can Run Parallel To**: ISSUE-004

### Problem Analysis

**Root Cause**: `DetectorBase` class missing `should_analyze_file()` method required by `DetectorPool.acquire_all_detectors()` at line 274.

**Current Behavior**:
```python
# detector_pool.py:274
for detector_name in self._detector_types:
    detector = self.acquire_detector(detector_name, file_path, source_lines)
    # Later calls detector.should_analyze_file() -> AttributeError
```

**Impact**:
- 10/16 tests blocked
- Detector pool non-functional
- Architecture components disabled

### Current Code State

**File**: `analyzer/detectors/base.py` (152 lines)

**Status**: MISSING METHOD - No `should_analyze_file()` method exists

**Existing Structure**:
```python
class DetectorBase(ABC):
    def __init__(self, file_path: str = "", source_lines: Optional[List[str]] = None):
        # ... initialization ...

    def get_code_snippet(self, node: ast.AST, context_lines: int = 2) -> str:
        # ... implementation ...

    @abstractmethod
    def detect_violations(self, tree: ast.AST) -> List[ConnascenceViolation]:
        pass

    def analyze_from_data(self, collected_data: "ASTNodeData") -> List[ConnascenceViolation]:
        # ... implementation ...

    # MISSING: should_analyze_file() method
```

### Proposed Fix

**Step 1**: Add `should_analyze_file()` method to `DetectorBase`

```python
# File: analyzer/detectors/base.py
# Insert after line 56 (after __init__)

    def should_analyze_file(self, file_path: str) -> bool:
        """
        Determine if detector should analyze given file.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation

        Args:
            file_path: Path to file to analyze

        Returns:
            True if detector supports this file type
        """
        # NASA Rule 5: Input validation
        assert isinstance(file_path, str), "file_path must be string"

        # Check file extension against supported types
        supported_extensions = getattr(self, 'SUPPORTED_EXTENSIONS', ['.py'])
        return any(file_path.endswith(ext) for ext in supported_extensions)
```

**Step 2**: Add `SUPPORTED_EXTENSIONS` to detector subclasses

```python
# File: analyzer/detectors/god_object_detector.py
class GodObjectDetector(DetectorBase):
    SUPPORTED_EXTENSIONS = ['.py', '.js', '.ts']  # Add at class level

    def detect_violations(self, tree: ast.AST) -> List[ConnascenceViolation]:
        # Existing implementation
        pass

# File: analyzer/detectors/magic_literal_detector.py
class MagicLiteralDetector(DetectorBase):
    SUPPORTED_EXTENSIONS = ['.py', '.js', '.ts', '.java']

    def detect_violations(self, tree: ast.AST) -> List[ConnascenceViolation]:
        # Existing implementation
        pass

# Apply to all 8 detectors:
# - position_detector.py
# - algorithm_detector.py
# - timing_detector.py
# - convention_detector.py
# - values_detector.py
# - execution_detector.py
```

### Implementation Script

```bash
#!/bin/bash
# File: scripts/fix_detector_pool.sh

echo "=== ISSUE-001: Fixing Detector Pool AttributeError ==="

# Step 1: Add should_analyze_file() to base.py
cat >> analyzer/detectors/base.py << 'EOF'

    def should_analyze_file(self, file_path: str) -> bool:
        """
        Determine if detector should analyze given file.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation

        Args:
            file_path: Path to file to analyze

        Returns:
            True if detector supports this file type
        """
        assert isinstance(file_path, str), "file_path must be string"

        supported_extensions = getattr(self, 'SUPPORTED_EXTENSIONS', ['.py'])
        return any(file_path.endswith(ext) for ext in supported_extensions)
EOF

# Step 2: Add SUPPORTED_EXTENSIONS to all detectors
DETECTORS=(
    "god_object_detector"
    "magic_literal_detector"
    "position_detector"
    "algorithm_detector"
    "timing_detector"
    "convention_detector"
    "values_detector"
    "execution_detector"
)

for detector in "${DETECTORS[@]}"; do
    # Add SUPPORTED_EXTENSIONS at class level
    sed -i "/class.*Detector.*:/a\    SUPPORTED_EXTENSIONS = ['.py']" \
        analyzer/detectors/${detector}.py
done

echo "✅ Added should_analyze_file() method to DetectorBase"
echo "✅ Added SUPPORTED_EXTENSIONS to all 8 detector classes"
```

### Test Verification

```bash
# Step 1: Verify base detector has method
python -c "
from analyzer.detectors.base import DetectorBase
import inspect

# Check method exists
assert hasattr(DetectorBase, 'should_analyze_file'), 'Method missing'

# Verify signature
sig = inspect.signature(DetectorBase.should_analyze_file)
assert 'file_path' in sig.parameters, 'file_path parameter missing'
assert sig.return_annotation == bool, 'Return type should be bool'

print('✅ DetectorBase.should_analyze_file() exists with correct signature')
"

# Step 2: Verify detector pool can use the method
python -c "
from analyzer.architecture.detector_pool import DetectorPool

pool = DetectorPool()
detectors = pool.acquire_all_detectors('test.py', ['# test code'])

assert len(detectors) > 0, 'No detectors acquired'
print(f'✅ DetectorPool acquired {len(detectors)} detectors')

# Verify each detector has method
for name, detector in detectors.items():
    assert hasattr(detector, 'should_analyze_file'), f'{name} missing method'
    result = detector.should_analyze_file('test.py')
    assert isinstance(result, bool), f'{name} returned non-bool'
    print(f'  - {name}: should_analyze_file() works')

pool.release_all_detectors(detectors)
print('✅ All detectors have working should_analyze_file()')
"

# Step 3: Run previously blocked tests
pytest tests/architecture/test_detector_pool.py -v
pytest tests/detectors/test_detector_factory.py -v

# Step 4: Full test suite (10 previously blocked tests should pass)
pytest tests/ -v --tb=short | grep -E "PASSED|FAILED" | tee test_results.txt
```

### Rollback Strategy

```bash
# If fix breaks something, rollback:

# 1. Save current state
git diff HEAD > /tmp/issue-001-fix.patch

# 2. Revert changes
git checkout analyzer/detectors/base.py
for detector in analyzer/detectors/*_detector.py; do
    git checkout "$detector"
done

# 3. Verify rollback
pytest tests/architecture/test_detector_pool.py -v

# 4. Restore if needed
git apply /tmp/issue-001-fix.patch
```

### Risk Assessment

| Risk Factor | Level | Mitigation |
|-------------|-------|------------|
| **Blast Radius** | MEDIUM | 16 detector files, 10 tests, 1 pool file |
| **Breaking Changes** | NO | Adding missing method, backward compatible |
| **Regression Risk** | LOW | Method is defensive (defaults to .py files) |
| **Rollback Time** | <5 minutes | Single git checkout |

---

## ISSUE-002: Fix Import Path Issues

### Priority: P0 - BLOCKING
**Effort**: 4-8 hours
**Depends On**: ISSUE-001
**Blocks**: ISSUE-003, 8 E2E test modules
**Can Run Parallel To**: ISSUE-004, ISSUE-005

### Problem Analysis

**Root Cause**: Tests expect `cli.connascence` import path, but actual implementation is `interfaces.cli.connascence`.

**Current Behavior**:
```python
# tests/e2e/test_cli_workflows.py:34
from cli.connascence import ConnascenceCLI  # ModuleNotFoundError
```

**Actual Path**:
```python
# interfaces/cli/connascence.py
class ConnascenceCLI:
    # implementation
```

**Impact**:
- 8 E2E test modules fail to collect
- 2,000+ LOC of tests untested
- Test coverage gaps

### Current Directory Structure

```
C:\Users\17175\Desktop\connascence\
├── interfaces/
│   └── cli/
│       └── connascence.py  (actual implementation)
└── tests/
    └── e2e/
        ├── test_cli_workflows.py  (imports cli.connascence)
        ├── test_enterprise_scale.py
        ├── test_error_handling.py
        ├── test_exit_codes.py
        ├── test_memory_coordination.py
        ├── test_performance.py
        ├── test_report_generation.py
        └── test_repository_analysis.py
```

### Proposed Fix (Option A: CLI Package Alias - RECOMMENDED)

**Create**: `cli/__init__.py` (backward compatibility shim)

```python
# File: cli/__init__.py
"""CLI package alias for backward compatibility.

This module provides backward-compatible imports for tests
expecting 'cli.connascence' while actual implementation lives
in 'interfaces.cli.connascence'.
"""
from interfaces.cli.connascence import *

__all__ = [
    'ConnascenceCLI',
    'CLIFormatter',
    'CLIError',
]
```

### Implementation Script

```bash
#!/bin/bash
# File: scripts/fix_import_paths.sh

echo "=== ISSUE-002: Fixing Import Paths ==="

# Option A: Create CLI alias (RECOMMENDED)
mkdir -p cli

cat > cli/__init__.py << 'EOF'
"""CLI package alias for backward compatibility.

This module provides backward-compatible imports for tests
expecting 'cli.connascence' while actual implementation lives
in 'interfaces.cli.connascence'.
"""
from interfaces.cli.connascence import *

__all__ = [
    'ConnascenceCLI',
    'CLIFormatter',
    'CLIError',
]
EOF

echo "✅ Created cli/__init__.py alias"

# Verify alias works
python3 -c "
from cli.connascence import ConnascenceCLI
print('✅ CLI alias import successful')
"

# Test E2E collection
echo "Testing E2E test collection..."
pytest tests/e2e/test_cli_workflows.py --collect-only --quiet

if [ $? -eq 0 ]; then
    echo "✅ E2E tests can now collect"
else
    echo "❌ E2E test collection still failing"
    exit 1
fi
```

### Test Verification

```bash
# Step 1: Verify alias works
python -c "from cli.connascence import ConnascenceCLI; print('✅ Import works')"

# Step 2: Test each blocked E2E module
pytest tests/e2e/test_cli_workflows.py --collect-only
pytest tests/e2e/test_enterprise_scale.py --collect-only
pytest tests/e2e/test_error_handling.py --collect-only
pytest tests/e2e/test_exit_codes.py --collect-only
pytest tests/e2e/test_memory_coordination.py --collect-only
pytest tests/e2e/test_performance.py --collect-only
pytest tests/e2e/test_report_generation.py --collect-only
pytest tests/e2e/test_repository_analysis.py --collect-only

# Step 3: Run full E2E suite
pytest tests/e2e/ -v

# Step 4: Verify no regressions
pytest tests/ -v | tee test_results.log
```

### Rollback Strategy

```bash
# If fix breaks something, rollback:

# 1. Delete CLI alias directory
rm -rf cli/

# 2. Verify original state
pytest tests/e2e/test_cli_workflows.py --collect-only

# Rollback time: <1 minute
```

### Risk Assessment

| Risk Factor | Level | Mitigation |
|-------------|-------|------------|
| **Blast Radius** | LOW | 8 E2E test files, 1 new package |
| **Breaking Changes** | NO | Adds alias, doesn't modify existing code |
| **Regression Risk** | VERY LOW | Only adds backward compatibility |
| **Rollback Time** | <1 minute | Delete cli/ directory |

---

## ISSUE-003: Register Missing Pytest Markers

### Priority: P0 - BLOCKING
**Effort**: 0.5 hours (30 minutes)
**Depends On**: ISSUE-002
**Blocks**: 4 enhanced test modules
**Can Run Parallel To**: ISSUE-004, ISSUE-005

### Problem Analysis

**Root Cause**: Tests use markers (`@pytest.mark.cli`, `@pytest.mark.mcp_server`, etc.) not registered in `pyproject.toml`.

**Current Configuration**:
```toml
# pyproject.toml (lines 253-259)
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
    "property: marks tests as property-based tests",
    "e2e: marks tests as end-to-end tests",
    "performance: marks tests as performance tests",
]
# MISSING: cli, mcp_server, vscode, web_dashboard
```

**Impact**:
- 4 enhanced integration test modules fail
- PytestUnknownMarkWarning errors

### Proposed Fix

**Update**: `pyproject.toml` lines 253-259

```toml
# File: pyproject.toml
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
    "property: marks tests as property-based tests",
    "e2e: marks tests as end-to-end tests",
    "performance: marks tests as performance tests",
    "cli: marks tests for CLI interface",
    "mcp_server: marks tests for MCP server integration",
    "vscode: marks tests for VSCode extension",
    "web_dashboard: marks tests for web dashboard",
]
```

### Implementation Script

```bash
#!/bin/bash
# File: scripts/fix_pytest_markers.sh

echo "=== ISSUE-003: Registering Missing Pytest Markers ==="

# Backup original
cp pyproject.toml pyproject.toml.backup

# Add missing markers using Python
python3 << 'EOF'
import tomli
import tomli_w

# Load config
with open('pyproject.toml', 'rb') as f:
    config = tomli.load(f)

# Add missing markers
missing_markers = [
    'cli: marks tests for CLI interface',
    'mcp_server: marks tests for MCP server integration',
    'vscode: marks tests for VSCode extension',
    'web_dashboard: marks tests for web dashboard',
]

for marker in missing_markers:
    if marker not in config['tool']['pytest']['ini_options']['markers']:
        config['tool']['pytest']['ini_options']['markers'].append(marker)

# Save updated config
with open('pyproject.toml', 'wb') as f:
    tomli_w.dump(config, f)

print('✅ Added 4 missing pytest markers')
EOF

# Verify markers registered
pytest --markers | grep -E "cli|mcp_server|vscode|web_dashboard"

if [ $? -eq 0 ]; then
    echo "✅ All markers now registered"
else
    echo "❌ Marker registration failed"
    exit 1
fi
```

### Test Verification

```bash
# Step 1: Verify markers registered
pytest --markers | grep -E "@pytest.mark.cli"
pytest --markers | grep -E "@pytest.mark.mcp_server"
pytest --markers | grep -E "@pytest.mark.vscode"
pytest --markers | grep -E "@pytest.mark.web_dashboard"

# Step 2: Test each enhanced module
pytest tests/enhanced/test_cli_integration.py --collect-only
pytest tests/enhanced/test_mcp_server_integration.py --collect-only
pytest tests/enhanced/test_vscode_integration.py --collect-only
pytest tests/enhanced/test_web_dashboard_integration.py --collect-only

# Step 3: Run enhanced suite
pytest tests/enhanced/ -v

# Step 4: Full test collection check
pytest tests/ --collect-only | grep -E "error|ERROR"
```

### Rollback Strategy

```bash
# If fix breaks something, rollback:

# 1. Restore backup
cp pyproject.toml.backup pyproject.toml

# 2. Verify rollback
pytest --markers | grep -E "cli|mcp_server"

# Rollback time: <30 seconds
```

### Risk Assessment

| Risk Factor | Level | Mitigation |
|-------------|-------|------------|
| **Blast Radius** | MINIMAL | 1 file, 4 test modules |
| **Breaking Changes** | NO | Only adds markers |
| **Regression Risk** | NONE | Purely additive configuration |
| **Rollback Time** | <30 seconds | Restore backup |

---

## ISSUE-004: Fix CI/CD Threshold Manipulation

### Priority: P0 - QUALITY ISSUE
**Effort**: 8-16 hours
**Blocks**: ISSUE-006 (god object refactoring)
**Can Run Parallel To**: ISSUE-001, ISSUE-002, ISSUE-003

### Problem Analysis

**Root Cause**: CI/CD threshold deliberately increased from 15 to 19 to hide violations.

**Current Code** (analyzer/constants.py:27):
```python
GOD_OBJECT_METHOD_THRESHOLD_CI = 19  # Temporary increase to allow CI/CD to pass
```

**Original Threshold**:
```python
GOD_OBJECT_METHOD_THRESHOLD = 15  # General development
```

**Impact**:
- False sense of security
- Masks real god object violations:
  - `ParallelConnascenceAnalyzer`: 18 methods (violates 15 threshold)
  - `UnifiedReportingCoordinator`: 18 methods (violates 15 threshold)

### Two-Phase Approach

**Phase 1**: Revert Threshold + Document Violations (2-4 hours)

```python
# File: analyzer/constants.py (line 27)
# BEFORE:
GOD_OBJECT_METHOD_THRESHOLD_CI = 19  # Temporary increase

# AFTER:
GOD_OBJECT_METHOD_THRESHOLD_CI = 15  # Restored to correct threshold
```

**Phase 2**: Refactor Violating Classes (6-12 hours)

See REMEDIATION_PLAN_GITHUB.md ISSUE-006 for detailed refactoring steps.

### Implementation Script (Phase 1)

```bash
#!/bin/bash
# File: scripts/fix_threshold_phase1.sh

echo "=== ISSUE-004 Phase 1: Reverting CI/CD Threshold ==="

# Backup constants file
cp analyzer/constants.py analyzer/constants.py.backup

# Revert threshold from 19 to 15
sed -i 's/GOD_OBJECT_METHOD_THRESHOLD_CI = 19/GOD_OBJECT_METHOD_THRESHOLD_CI = 15/' \
    analyzer/constants.py

# Verify change
grep -n "GOD_OBJECT_METHOD_THRESHOLD_CI" analyzer/constants.py

# Document violations that will now be caught
cat > docs/GOD_OBJECT_VIOLATIONS_REVEALED.md << 'EOF'
# God Object Violations Revealed by Threshold Restoration

## Violations Caught After Reverting GOD_OBJECT_METHOD_THRESHOLD_CI to 15:

1. **ParallelConnascenceAnalyzer**: 18 methods -> needs extraction
2. **UnifiedReportingCoordinator**: 18 methods -> needs extraction

## Next Steps:

See REMEDIATION_PLAN_GITHUB.md ISSUE-006 for refactoring plan.
EOF

echo "✅ Reverted GOD_OBJECT_METHOD_THRESHOLD_CI to 15"
echo "✅ Documented violations to fix"
```

### Test Verification

```bash
# Step 1: Verify threshold reverted
grep -n "GOD_OBJECT_METHOD_THRESHOLD_CI" analyzer/constants.py
# Should show: GOD_OBJECT_METHOD_THRESHOLD_CI = 15

# Step 2: Run god object detection (should catch violations)
python -m analyzer.core --god-objects analyzer/ 2>&1 | grep -E "18 methods"

# Step 3: CI/CD will fail (expected) - document violations
python -m analyzer.core --god-objects analyzer/ --threshold 15 --strict > god_object_report.txt

# Step 4: Full test suite (may fail on god object tests)
pytest tests/ -v

# Step 5: Verify violations documented
cat docs/GOD_OBJECT_VIOLATIONS_REVEALED.md
```

### Rollback Strategy

```bash
# If fix breaks something, rollback:

# 1. Restore original threshold
cp analyzer/constants.py.backup analyzer/constants.py

# 2. Verify rollback
grep -n "GOD_OBJECT_METHOD_THRESHOLD_CI" analyzer/constants.py
# Should show: GOD_OBJECT_METHOD_THRESHOLD_CI = 19

# 3. Re-run tests
pytest tests/ -v

# Rollback time: 1-2 minutes
```

### Risk Assessment

| Risk Factor | Level | Mitigation |
|-------------|-------|------------|
| **Blast Radius** | HIGH | Threshold changes affect all code |
| **Breaking Changes** | POSSIBLY | CI/CD will fail until classes refactored |
| **Regression Risk** | MEDIUM | Reveals hidden violations |
| **Rollback Time** | 1-2 minutes | Restore backup |

---

## Dependency Graph

```
DAY 1 (8 hours):
=================
ISSUE-001 (Start)
    |
    +-- Blocks --> ISSUE-002 (Start after 16-24h)
    |
    +-- Enables -> 10 blocked tests
    |
    +-- Independent of --> ISSUE-004 (Can run parallel)

ISSUE-004 (Parallel)
    |
    +-- Independent --> Can start immediately
    |
    +-- Documents --> Violations for ISSUE-006


DAY 2 (8 hours):
=================
ISSUE-001 (Complete)
    |
    v
ISSUE-002 (Start + Complete 4-8h)
    |
    +-- Blocks --> ISSUE-003 (Start after 4-8h)
    |
    +-- Enables -> 8 E2E test modules


DAY 3 (8 hours):
=================
ISSUE-002 (Complete)
    |
    v
ISSUE-003 (Complete 0.5h)
    |
    +-- Enables -> 4 enhanced test modules
    |
    v
ISSUE-004 (Continue/Complete)


DAY 4-5 (16 hours):
====================
ISSUE-004 Phase 2 (Refactoring)
    |
    +-- Prepares for --> ISSUE-006 (Month 1)
    |
    v
MILESTONE ACHIEVED: All tests pass, CI/CD green
```

---

## Daily Schedule

### Day 1 (8 hours)

**Morning (4 hours)**:
- Start ISSUE-001: Add `should_analyze_file()` to `DetectorBase`
- Add `SUPPORTED_EXTENSIONS` to 8 detector classes
- Run detector pool tests

**Afternoon (4 hours)**:
- Complete ISSUE-001 verification
- Start ISSUE-004 Phase 1: Revert threshold
- Document god object violations

**Parallel Work**:
- ISSUE-004 can run independently (different developer)

---

### Day 2 (8 hours)

**Morning (4 hours)**:
- Complete ISSUE-001 full test suite validation
- Start ISSUE-002: Create CLI alias package
- Verify E2E test collection

**Afternoon (4 hours)**:
- Complete ISSUE-002 verification
- Run full E2E test suite
- Start ISSUE-003: Add pytest markers

---

### Day 3 (8 hours)

**Morning (2 hours)**:
- Complete ISSUE-003: Pytest markers
- Verify enhanced test collection
- Full test collection check (496/496 tests)

**Afternoon (6 hours)**:
- Continue ISSUE-004 Phase 1 if needed
- Begin documenting Phase 2 refactoring plan
- Integration testing

---

### Day 4 (8 hours)

**Morning (4 hours)**:
- ISSUE-004 Phase 2: Begin refactoring `ParallelConnascenceAnalyzer`
- Extract methods into focused classes

**Afternoon (4 hours)**:
- Continue refactoring
- Write tests for extracted classes
- Verify god object thresholds pass

---

### Day 5 (8 hours)

**Morning (4 hours)**:
- Complete ISSUE-004 Phase 2 refactoring
- Refactor `UnifiedReportingCoordinator`
- Full test suite validation

**Afternoon (4 hours)**:
- CI/CD pipeline verification
- Final integration testing
- **MILESTONE**: Week 1 complete

---

## Risk Mitigation

### Pre-Implementation Checklist

```bash
# 1. Create feature branch
git checkout -b week-1-critical-blockers

# 2. Backup critical files
cp analyzer/detectors/base.py analyzer/detectors/base.py.backup
cp analyzer/constants.py analyzer/constants.py.backup
cp pyproject.toml pyproject.toml.backup

# 3. Run baseline tests
pytest tests/ -v > baseline_tests.txt

# 4. Document current state
git status > pre_implementation_state.txt
```

### During Implementation

```bash
# After each issue fix:

# 1. Run affected tests
pytest tests/<affected_area>/ -v

# 2. Run full test suite
pytest tests/ -v

# 3. Commit atomically
git add <changed_files>
git commit -m "[ISSUE-00X] <description>"

# 4. Tag milestones
git tag issue-001-complete
```

### Post-Implementation Validation

```bash
# 1. Full test suite
pytest tests/ -v --tb=short

# 2. Test collection verification
pytest tests/ --collect-only | grep -c "test"
# Should show 496 tests

# 3. CI/CD simulation
python -m analyzer.core --god-objects analyzer/ --threshold 15 --strict

# 4. Integration smoke test
python -m analyzer.core analyzer/ --format json --output test_report.json
```

### Rollback Plan

```bash
# Emergency rollback script
# File: scripts/emergency_rollback.sh

#!/bin/bash
echo "=== EMERGENCY ROLLBACK ==="

# 1. Restore backups
cp analyzer/detectors/base.py.backup analyzer/detectors/base.py
cp analyzer/constants.py.backup analyzer/constants.py
cp pyproject.toml.backup pyproject.toml

# 2. Remove CLI alias
rm -rf cli/

# 3. Reset git
git reset --hard HEAD

# 4. Verify rollback
pytest tests/ -v --tb=short

echo "✅ Rollback complete"
```

---

## Success Metrics

### Acceptance Criteria

- [ ] **ISSUE-001**: All 10 blocked tests pass
- [ ] **ISSUE-002**: All 8 E2E test modules collect successfully
- [ ] **ISSUE-003**: All 4 enhanced test modules collect successfully
- [ ] **ISSUE-004**: Real thresholds enforced, violations documented
- [ ] **Overall**: 100% test collection (496/496 tests)
- [ ] **CI/CD**: Pipeline green (or documented violations)

### Verification Commands

```bash
# Final verification checklist

# 1. Test collection
pytest tests/ --collect-only | tail -1
# Should show: 496 tests collected

# 2. Test pass rate
pytest tests/ -v | tail -1
# Should show: 457+ passed

# 3. Detector pool functional
python -c "
from analyzer.architecture.detector_pool import DetectorPool
pool = DetectorPool()
detectors = pool.acquire_all_detectors('test.py', ['code'])
assert len(detectors) == 8, f'Expected 8 detectors, got {len(detectors)}'
print('✅ Detector pool functional')
"

# 4. God object detection accurate
python -m analyzer.core --god-objects analyzer/ --threshold 15 | grep -E "violations|PASS"

# 5. CLI imports work
python -c "from cli.connascence import ConnascenceCLI; print('✅ CLI imports work')"
```

---

## Appendix A: File Paths

### Critical Files

```
C:\Users\17175\Desktop\connascence\
├── analyzer\
│   ├── constants.py                     (ISSUE-004)
│   ├── detectors\
│   │   ├── base.py                      (ISSUE-001)
│   │   ├── god_object_detector.py       (ISSUE-001)
│   │   ├── magic_literal_detector.py    (ISSUE-001)
│   │   ├── position_detector.py         (ISSUE-001)
│   │   ├── algorithm_detector.py        (ISSUE-001)
│   │   ├── timing_detector.py           (ISSUE-001)
│   │   ├── convention_detector.py       (ISSUE-001)
│   │   ├── values_detector.py           (ISSUE-001)
│   │   └── execution_detector.py        (ISSUE-001)
│   └── architecture\
│       └── detector_pool.py
├── cli\
│   └── __init__.py                      (ISSUE-002, NEW)
├── interfaces\
│   └── cli\
│       └── connascence.py
├── pyproject.toml                       (ISSUE-003)
├── tests\
│   ├── e2e\                            (ISSUE-002 unblocks)
│   └── enhanced\                       (ISSUE-003 unblocks)
└── docs\
    ├── REMEDIATION_PLAN_GITHUB.md
    └── WEEK-1-DAY-1-PLAN.md            (THIS FILE)
```

---

## Appendix B: Command Quick Reference

```bash
# ISSUE-001 Commands
bash scripts/fix_detector_pool.sh
pytest tests/architecture/test_detector_pool.py -v

# ISSUE-002 Commands
bash scripts/fix_import_paths.sh
pytest tests/e2e/ -v

# ISSUE-003 Commands
bash scripts/fix_pytest_markers.sh
pytest --markers | grep -E "cli|mcp_server|vscode|web_dashboard"

# ISSUE-004 Commands
bash scripts/fix_threshold_phase1.sh
python -m analyzer.core --god-objects analyzer/ --threshold 15

# Full Verification
pytest tests/ -v --tb=short | tee full_test_results.txt
```

---

**Generated By**: Strategic Planning Agent
**Report Version**: 1.0
**Date**: 2025-11-13
**Confidence**: HIGH (based on comprehensive codebase analysis)
