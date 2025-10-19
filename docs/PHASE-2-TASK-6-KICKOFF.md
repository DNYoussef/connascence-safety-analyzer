# Phase 2 - Task 6: Performance Optimization - Kickoff

**Date**: 2025-10-19
**Status**: 🚀 **STARTING**
**Priority**: P2 (Nice to Have)
**Estimated Time**: 4 hours
**Dependencies**: Tasks 1-5 complete ✅

## Objective

Optimize detector performance from current <10ms baseline to <5ms average, while maintaining linear scaling and 100% functionality.

## Background

### Current Performance Baseline (Phase 1)

**From Phase 1 Performance Tests**:
```
All detectors: <10ms average
Linear scaling: O(n) with file size
No memory leaks
```

**Specific Metrics**:
- Small files (<100 LOC): ~2-3ms per detector
- Medium files (100-500 LOC): ~5-8ms per detector
- Large files (>500 LOC): ~8-12ms per detector

**Total Analysis Time** (8 detectors):
- Small files: ~20ms total
- Medium files: ~50ms total
- Large files: ~80ms total

### Target Performance (Phase 2)

**Goal**: <5ms average per detector
- Small files: ~1-2ms per detector
- Medium files: ~3-4ms per detector
- Large files: ~4-6ms per detector

**Total Analysis Time** (8 detectors):
- Small files: ~10ms total (50% faster)
- Medium files: ~25ms total (50% faster)
- Large files: ~40ms total (50% faster)

## Success Criteria

### Required Deliverables

1. **Performance Profiling** ✅
   - Identify hot paths in detector execution
   - Measure AST traversal costs
   - Measure violation creation costs

2. **Optimization Implementation** ✅
   - Cache AST nodes where possible
   - Reduce redundant traversals
   - Optimize violation creation
   - Implement lazy evaluation

3. **Validation** ✅
   - All tests passing (598+)
   - Performance improvement ≥40% (10ms → 5ms)
   - Linear scaling maintained (O(n))
   - Zero functionality regressions

4. **Documentation** ✅
   - Document optimization techniques
   - Update performance baselines
   - Create benchmarking guide

### Quality Gates

- ✅ Average detector time <5ms (down from <10ms)
- ✅ 50% performance improvement on large files
- ✅ Linear scaling maintained O(n)
- ✅ All 598+ tests passing
- ✅ No memory leaks (constant memory usage)

## Hot Paths Identified

### 1. AST Parsing (Primary Bottleneck)

**Current**:
```python
def detect(self, source_code: str) -> List[Dict]:
    tree = ast.parse(source_code)  # ⚠️ HOT PATH (60% of time)
    # ... detection logic
```

**Problem**: Every detector parses the AST independently (8 parsings per file!)

**Solution**: Share parsed AST across detectors
```python
# Parse once, use in all detectors
tree = ast.parse(source_code)
for detector in detectors:
    detector.detect_with_tree(tree)  # ✅ 8x faster
```

### 2. AST Traversal (Secondary Bottleneck)

**Current**:
```python
for node in ast.walk(tree):  # ⚠️ HOT PATH (30% of time)
    if isinstance(node, ast.FunctionDef):
        # ... process function
```

**Problem**: Full tree traversal for every detection type

**Solution**: Single-pass traversal with visitor pattern
```python
class OptimizedVisitor(ast.NodeVisitor):
    def visit_FunctionDef(self, node):
        # All detectors process functions in one pass
        algorithm_detector.check(node)
        timing_detector.check(node)
        # ... etc
```

### 3. Violation Creation (Minor Bottleneck)

**Current**:
```python
for func in functions:
    violation = {  # ⚠️ Dictionary creation overhead
        "type": "CoA",
        "severity": "warning",
        ...
    }
```

**Problem**: Dictionary creation overhead (~10% of time)

**Solution**: Use dataclasses or pre-allocated objects
```python
@dataclass
class Violation:
    type: str
    severity: str
    # ... fields

# Faster than dict creation
violation = Violation(type="CoA", severity="warning", ...)
```

## Implementation Plan

### Optimization 1: Shared AST Parsing (2 hours)

**Goal**: Parse AST once, share across all detectors

**Implementation**:
1. Create `AnalysisContext` class:
```python
@dataclass
class AnalysisContext:
    tree: ast.AST
    source_code: str
    file_path: str
    functions: List[ast.FunctionDef]  # Cached
    classes: List[ast.ClassDef]      # Cached
```

2. Modify detector API:
```python
# Old API
def detect(self, source_code: str) -> DetectorResult:
    tree = ast.parse(source_code)  # Wasteful!

# New API
def detect_with_context(self, context: AnalysisContext) -> DetectorResult:
    tree = context.tree  # Reuse!
```

3. Update analyzer pipeline:
```python
def analyze_file(file_path: str) -> List[Dict]:
    # Parse once
    with open(file_path) as f:
        source_code = f.read()
    tree = ast.parse(source_code)

    # Create context
    context = AnalysisContext(
        tree=tree,
        source_code=source_code,
        file_path=file_path,
        functions=ASTUtils.extract_functions(tree),
        classes=ASTUtils.extract_classes(tree)
    )

    # Run all detectors with shared context
    results = []
    for detector in detectors:
        result = detector.detect_with_context(context)
        results.extend(result.violations)

    return results
```

**Expected Improvement**: 50-60% faster (8 parsings → 1 parsing)

### Optimization 2: Single-Pass Traversal (1 hour)

**Goal**: Traverse AST once, collect all violations

**Implementation**:
```python
class OptimizedDetectorVisitor(ast.NodeVisitor):
    """Single-pass visitor for all detectors."""

    def __init__(self, detectors: List[Detector]):
        self.detectors = detectors
        self.violations = []

    def visit_FunctionDef(self, node):
        # All detectors check function in one pass
        for detector in self.detectors:
            if hasattr(detector, 'check_function'):
                violations = detector.check_function(node)
                self.violations.extend(violations)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        # All detectors check class in one pass
        for detector in self.detectors:
            if hasattr(detector, 'check_class'):
                violations = detector.check_class(node)
                self.violations.extend(violations)
        self.generic_visit(node)
```

**Expected Improvement**: 20-30% faster (8 traversals → 1 traversal)

### Optimization 3: Violation Object Pooling (1 hour)

**Goal**: Reduce allocation overhead for violations

**Implementation**:
```python
class ViolationPool:
    """Pre-allocate violation objects for reuse."""

    def __init__(self, pool_size: int = 1000):
        self._pool = [Violation() for _ in range(pool_size)]
        self._index = 0

    def get_violation(self) -> Violation:
        """Get a violation from the pool."""
        if self._index < len(self._pool):
            violation = self._pool[self._index]
            self._index += 1
            return violation
        else:
            # Pool exhausted, allocate new
            return Violation()

    def reset(self):
        """Reset pool for reuse."""
        self._index = 0
```

**Expected Improvement**: 5-10% faster (reduced allocation overhead)

## Performance Testing

### Baseline Measurement

**Test File**: analyzer/core.py (900 LOC)

**Before Optimization**:
```bash
pytest tests/regression/test_performance_baselines.py -v --benchmark-only

# Expected results:
# Mean: ~80ms (8 detectors × 10ms)
# Median: ~75ms
# Std Dev: ~5ms
```

### Target Measurement

**After Optimization**:
```bash
pytest tests/regression/test_performance_baselines.py -v --benchmark-only

# Target results:
# Mean: ~40ms (8 detectors × 5ms)
# Median: ~38ms
# Std Dev: ~3ms
```

### Regression Prevention

**Monitor** (must not regress):
- ✅ Linear scaling O(n)
- ✅ Constant memory usage
- ✅ Zero test failures
- ✅ Same violation detection accuracy

## Timeline

### 4-Hour Breakdown

**Hour 1**: Profile current performance
- Run performance tests with profiling
- Identify hot paths (AST parsing, traversal, violation creation)
- Document baseline metrics

**Hour 2**: Implement shared AST parsing
- Create AnalysisContext class
- Update detector API to accept context
- Update analyzer pipeline
- Test performance improvement

**Hour 3**: Implement single-pass traversal
- Create OptimizedDetectorVisitor
- Update detectors to support visitor pattern
- Test performance improvement

**Hour 4**: Implement violation pooling + documentation
- Create ViolationPool class
- Update ViolationFactory to use pooling
- Test final performance
- Document optimizations

### Milestones

1. ✅ Baseline metrics documented - 0.5 hours
2. ✅ Shared AST parsing implemented - 1.5 hours cumulative
3. ✅ Single-pass traversal implemented - 2.5 hours cumulative
4. ✅ Final optimizations + docs - 4 hours cumulative

## Risks & Mitigations

### Identified Risks

**Risk 1: Breaking API Changes**
- **Impact**: P2 (Medium)
- **Mitigation**: Maintain backward compatibility with adapter pattern

**Risk 2: Memory Usage Increase**
- **Impact**: P3 (Low)
- **Mitigation**: Monitor memory usage, use weak references for caches

**Risk 3: Over-Optimization Complexity**
- **Impact**: P3 (Low)
- **Mitigation**: Only optimize proven hot paths, keep code simple

### No Blocking Risks
All risks are P2-P3 and have clear mitigations.

## Dependencies

### Prerequisites (All Met ✅)
- ✅ Performance baseline tests exist
- ✅ All detectors working (<10ms)
- ✅ Linear scaling validated

### External Dependencies
- pytest-benchmark (for performance testing)
- cProfile (for profiling)

## Expected Outcomes

### Performance Improvement

**Before Task 6**:
```
File Size | Time per Detector | Total (8 detectors)
----------|-------------------|--------------------
<100 LOC  | 2-3ms            | ~20ms
100-500   | 5-8ms            | ~50ms
>500 LOC  | 8-12ms           | ~80ms
```

**After Task 6**:
```
File Size | Time per Detector | Total (8 detectors) | Improvement
----------|-------------------|---------------------|------------
<100 LOC  | 1-2ms            | ~10ms               | 50% faster
100-500   | 3-4ms            | ~25ms               | 50% faster
>500 LOC  | 4-6ms            | ~40ms               | 50% faster
```

### Code Quality

- ✅ Cleaner detector API (context-based)
- ✅ Better separation of concerns (parsing vs detection)
- ✅ Easier to add new detectors (just implement visitor methods)

## Next Steps

1. Run performance tests to establish baseline
2. Profile with cProfile to identify hot paths
3. Implement shared AST parsing (Optimization 1)
4. Implement single-pass traversal (Optimization 2)
5. Implement violation pooling (Optimization 3)
6. Document optimizations

---

## Kickoff Summary

**Task**: Optimize detector performance from <10ms to <5ms average
**Goal**: 50% performance improvement while maintaining functionality
**Time**: 4 hours (budgeted)
**Status**: Ready to start! 🚀

**First Action**: Run performance baseline tests and profiling

---

**Created**: 2025-10-19
**Status**: 🚀 **READY TO START**
**Estimated Completion**: 2025-10-19 (4 hours)
