# Phase 2 - Task 5: Further Detector Integration - Kickoff

**Date**: 2025-10-19
**Status**: 🚀 **STARTING**
**Priority**: P2 (Nice to Have)
**Estimated Time**: 8 hours
**Dependencies**: Tasks 1-4 complete ✅

## Objective

Apply Phase 0 utilities (ASTUtils, ViolationFactory, DetectorResult) to remaining 6 detectors, standardizing APIs and reducing code duplication.

## Background

### Phase 0 Achievements ✅

In Phase 0, we successfully refactored 2 detectors:
- `NameDetector` - Uses ASTUtils, ViolationFactory, NASA compliant
- `PositionDetector` - Uses DetectorResult, standardized API

**Results**:
- ✅ 100% NASA compliance in new detectors
- ✅ Reduced code duplication by ~40%
- ✅ Standardized violation creation
- ✅ Consistent error handling

### Current State

**Detectors Status**:
- ✅ **Refactored (2)**: NameDetector, PositionDetector
- ⏳ **Legacy (6)**: AlgorithmDetector, TimingDetector, ExecutionDetector, GodObjectDetector, ConventionDetector, MagicLiteralDetector
- **Total**: 8 detectors operational

**Problem**: 6 detectors still use legacy patterns:
- Direct AST traversal (no ASTUtils)
- Manual violation creation (no ViolationFactory)
- Inconsistent APIs
- Code duplication (~400 LOC)

## Success Criteria

### Required Deliverables

1. **Detector Refactoring** ✅
   - All 6 detectors use Phase 0 utilities
   - ASTUtils for AST traversal
   - ViolationFactory for violation creation
   - DetectorResult for result structures

2. **API Standardization** ✅
   - Consistent `detect()` method signature
   - Standardized error handling
   - Uniform violation format

3. **Code Quality** ✅
   - NASA Rule 4 compliance (≤60 LOC per function)
   - Reduced code duplication (≥30%)
   - 100% test coverage maintained

4. **Testing** ✅
   - 0 test regressions
   - All 598+ tests passing
   - Performance maintained (<10ms)

### Quality Gates

- ✅ All 6 detectors use ASTUtils, ViolationFactory, DetectorResult
- ✅ Code duplication reduced ≥30% (400 LOC → ≤280 LOC)
- ✅ NASA compliance 100% for refactored code
- ✅ All tests passing (598+)
- ✅ Performance maintained (<10ms per detector)

## Target Detectors

### Priority Order

**Batch 1 (High Priority - 4 hours)**:
1. **AlgorithmDetector** - Most code duplication
2. **TimingDetector** - Complex AST traversal
3. **ExecutionDetector** - Similar patterns to TimingDetector

**Batch 2 (Medium Priority - 4 hours)**:
4. **GodObjectDetector** - Large detector, needs refactoring
5. **ConventionDetector** - Simple patterns, quick win
6. **MagicLiteralDetector** - Already partially refactored

## Implementation Plan

### Phase 0 Utilities Available

**1. ASTUtils** (analyzer/utils/ast_utils.py):
```python
class ASTUtils:
    @staticmethod
    def extract_functions(tree: ast.AST) -> List[ast.FunctionDef]:
        """Extract all function definitions."""

    @staticmethod
    def extract_classes(tree: ast.AST) -> List[ast.ClassDef]:
        """Extract all class definitions."""

    @staticmethod
    def get_node_location(node: ast.AST) -> Dict[str, int]:
        """Get source location (line, col, end_line, end_col)."""
```

**2. ViolationFactory** (analyzer/utils/violation_factory.py):
```python
class ViolationFactory:
    @staticmethod
    def create_violation(
        type: str,
        severity: str,
        message: str,
        location: Dict[str, int]
    ) -> Dict:
        """Create standardized violation object."""
```

**3. DetectorResult** (analyzer/utils/detector_result.py):
```python
@dataclass
class DetectorResult:
    violations: List[Dict]
    metadata: Dict
    timing_ms: float
```

### Refactoring Pattern

**Before** (Legacy pattern):
```python
class LegacyDetector:
    def detect(self, source_code: str) -> List[Dict]:
        # Manual AST parsing
        tree = ast.parse(source_code)

        # Manual traversal
        violations = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Manual violation creation
                violations.append({
                    "type": "CoA",
                    "severity": "warning",
                    "message": f"Found {node.name}",
                    "line": node.lineno
                })

        return violations
```

**After** (Phase 0 pattern):
```python
class RefactoredDetector:
    def detect(self, source_code: str, file_path: str = "") -> DetectorResult:
        # Use ASTUtils
        tree = ast.parse(source_code)
        functions = ASTUtils.extract_functions(tree)

        # Use ViolationFactory
        violations = []
        for func in functions:
            location = ASTUtils.get_node_location(func)
            violation = ViolationFactory.create_violation(
                type="CoA",
                severity="warning",
                message=f"Found {func.name}",
                location=location
            )
            violations.append(violation)

        # Use DetectorResult
        return DetectorResult(
            violations=violations,
            metadata={"detector": "Algorithm"},
            timing_ms=0.0
        )
```

### Implementation Steps (Per Detector)

**Step 1: Analyze Current Implementation** (15 min)
- Read detector source code
- Identify AST traversal patterns
- Identify violation creation patterns
- Check NASA compliance

**Step 2: Create Refactoring Script** (15 min)
- Similar to Task 3 approach
- Extract helpers for NASA compliance
- Apply Phase 0 utilities

**Step 3: Implement Refactoring** (30 min)
- Replace AST traversal with ASTUtils
- Replace violation creation with ViolationFactory
- Return DetectorResult instead of List[Dict]
- Extract helper functions (≤60 LOC)

**Step 4: Test & Validate** (20 min)
- Run detector unit tests
- Run full test suite
- Verify no regressions
- Check performance (<10ms)

**Total per detector**: ~1.5 hours × 6 detectors = 9 hours (1 hour buffer)

## Expected Outcomes

### Code Duplication Reduction

**Before Task 5**:
```python
# AlgorithmDetector
tree = ast.parse(source_code)
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        # ... 20 LOC

# TimingDetector
tree = ast.parse(source_code)
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        # ... 20 LOC (duplicate!)
```

**After Task 5**:
```python
# AlgorithmDetector
functions = ASTUtils.extract_functions(tree)  # 1 LOC

# TimingDetector
functions = ASTUtils.extract_functions(tree)  # 1 LOC
```

**Savings**: ~400 LOC → ~280 LOC (30% reduction)

### API Standardization

**Before Task 5**:
```python
# Inconsistent signatures
AlgorithmDetector.detect(source_code: str) -> List[Dict]
TimingDetector.analyze(code: str, options: Dict) -> Dict
ExecutionDetector.check(source: str) -> Tuple[List, int]
```

**After Task 5**:
```python
# Unified signature
All detectors: detect(source_code: str, file_path: str = "") -> DetectorResult
```

## Timeline

### 8-Hour Breakdown

**Hours 1-2**: AlgorithmDetector refactoring
- Analyze current implementation
- Apply Phase 0 utilities
- Test and validate

**Hours 3-4**: TimingDetector + ExecutionDetector refactoring
- Similar patterns, can batch together
- Apply utilities to both
- Test and validate

**Hours 5-6**: GodObjectDetector refactoring
- Largest detector, needs careful refactoring
- Apply utilities and extract helpers
- Test and validate

**Hours 7-8**: ConventionDetector + MagicLiteralDetector refactoring
- Quick wins, simple patterns
- Apply utilities
- Final testing and documentation

### Milestones

1. ✅ Batch 1 complete (AlgorithmDetector, TimingDetector, ExecutionDetector) - 4 hours
2. ✅ Batch 2 complete (GodObjectDetector, ConventionDetector, MagicLiteralDetector) - 4 hours
3. ✅ All tests passing, code duplication reduced ≥30%

## Risks & Mitigations

### Identified Risks

**Risk 1: Test Regressions**
- **Impact**: P2 (Medium)
- **Mitigation**: Test after each detector refactoring, not in batch

**Risk 2: Performance Degradation**
- **Impact**: P2 (Medium)
- **Mitigation**: Run performance tests after each refactoring

**Risk 3: API Breaking Changes**
- **Impact**: P3 (Low)
- **Mitigation**: Maintain backward compatibility via adapter pattern

### No Blocking Risks
All risks are P2-P3 and have clear mitigations.

## Dependencies

### Prerequisites (All Met ✅)
- ✅ Phase 0 utilities implemented (ASTUtils, ViolationFactory, DetectorResult)
- ✅ 2 detectors already refactored (NameDetector, PositionDetector)
- ✅ All tests passing (598+)

### External Dependencies
- None (all utilities internal)

## Next Steps

1. Analyze AlgorithmDetector current implementation
2. Create refactoring script for AlgorithmDetector
3. Apply Phase 0 utilities
4. Test and validate
5. Repeat for remaining 5 detectors

---

## Kickoff Summary

**Task**: Apply Phase 0 utilities to 6 remaining detectors
**Goal**: Standardize APIs, reduce code duplication ≥30%, maintain performance
**Time**: 8 hours (budgeted)
**Status**: Ready to start! 🚀

**First Action**: Analyze AlgorithmDetector implementation

---

**Created**: 2025-10-19
**Status**: 🚀 **READY TO START**
**Estimated Completion**: 2025-10-19 (8 hours)
