# CacheManager Integration Guide

**Quick Reference for Integrating CacheManager into UnifiedConnascenceAnalyzer**

## Overview

This guide shows how to integrate the newly extracted CacheManager component into UnifiedConnascenceAnalyzer.

## Step 1: Import CacheManager

**Location**: `analyzer/unified_analyzer.py` (top of file, around line 40)

```python
# Add to existing architecture imports
from .architecture.cache_manager import CacheManager
```

## Step 2: Initialize in __init__()

**Location**: `analyzer/unified_analyzer.py` (around line 452-458)

**BEFORE** (lines to remove):
```python
# Initialize enhanced file cache for optimized I/O with intelligent warming
self.file_cache = (
    FileContentCache(max_memory=100 * 1024 * 1024) if CACHE_AVAILABLE else None
)  # 100MB for large projects
self._cache_stats = {"hits": 0, "misses": 0, "warm_requests": 0, "batch_loads": 0}
self._analysis_patterns = {}  # Track file access patterns for intelligent caching
self._file_priorities = {}  # Cache file priority scores for better eviction
```

**AFTER** (replacement):
```python
# Initialize centralized cache manager
cache_config = {
    "max_memory": 100 * 1024 * 1024,  # 100MB for large projects
    "warm_file_count": 15,
}
self.cache_manager = CacheManager(cache_config)

# Keep backward compatibility (optional, for gradual migration)
self.file_cache = self.cache_manager.file_cache if self.cache_manager.cache_available else None
```

## Step 3: Replace Cache Method Calls

### Method Mapping Table

| OLD Method (unified_analyzer.py) | NEW Method (CacheManager) |
|----------------------------------|---------------------------|
| `self._warm_cache_intelligently()` | `self.cache_manager.warm_cache()` |
| `self._get_cached_content_with_tracking()` | `self.cache_manager.get_cached_content()` |
| `self._get_cached_lines_with_tracking()` | `self.cache_manager.get_cached_lines()` |
| `self._get_cache_hit_rate()` | `self.cache_manager.get_hit_rate()` |
| `self._log_cache_performance()` | `self.cache_manager.log_performance()` |
| `self._optimize_cache_for_future_runs()` | `self.cache_manager.optimize_for_future_runs()` |
| `self._batch_preload_files()` | `self.cache_manager.batch_preload()` |
| `self._calculate_file_priority()` | `self.cache_manager._calculate_file_priority()` |
| Direct `file_cache.get_ast_tree()` | `self.cache_manager.get_cached_ast()` |

### Example Replacements

#### Cache Warming
**BEFORE**:
```python
self._warm_cache_intelligently(project_path)
```

**AFTER**:
```python
self.cache_manager.warm_cache(project_path)
```

#### Get Cached Content
**BEFORE**:
```python
content = self._get_cached_content_with_tracking(file_path)
```

**AFTER**:
```python
content = self.cache_manager.get_cached_content(file_path)
```

#### Get Cached AST
**BEFORE**:
```python
if self.file_cache:
    tree = self.file_cache.get_ast_tree(file_path)
```

**AFTER**:
```python
tree = self.cache_manager.get_cached_ast(file_path)
```

#### Cache Performance Logging
**BEFORE**:
```python
self._log_cache_performance()
```

**AFTER**:
```python
self.cache_manager.log_performance()
```

#### Batch Preload
**BEFORE**:
```python
self._batch_preload_files(prioritized_files)
```

**AFTER**:
```python
self.cache_manager.batch_preload(prioritized_files)
```

## Step 4: Remove Old Methods

**Location**: `analyzer/unified_analyzer.py` (lines 1152-1331)

Remove these methods (now in CacheManager):
- `_warm_cache_intelligently()` (lines 1152-1192)
- `_calculate_file_priority()` (lines 1193-1219)
- `_get_prioritized_python_files()` (lines 1221-1231)
- `_batch_preload_files()` (lines 1233-1249)
- `_get_cached_content_with_tracking()` (lines 1251-1267)
- `_get_cached_lines_with_tracking()` (lines 1269-1280)
- `_get_cache_hit_rate()` (lines 1282-1285)
- `_log_cache_performance()` (lines 1287-1312)
- `_optimize_cache_for_future_runs()` (lines 1313-1331)

## Step 5: Update Cache Cleanup Methods

**Location**: `analyzer/unified_analyzer.py` (around lines 1377-1399)

**BEFORE**:
```python
def _emergency_memory_cleanup(self) -> None:
    """Emergency memory cleanup procedures."""
    logger.critical("Executing emergency memory cleanup")

    try:
        # Clear all caches
        if self.file_cache:
            self.file_cache.clear_cache()

        # ... rest of cleanup
```

**AFTER**:
```python
def _emergency_memory_cleanup(self) -> None:
    """Emergency memory cleanup procedures."""
    logger.critical("Executing emergency memory cleanup")

    try:
        # Clear all caches via CacheManager
        if self.cache_manager:
            self.cache_manager.clear_all()

        # ... rest of cleanup
```

## Step 6: Update Statistics Methods

**BEFORE**:
```python
def _cleanup_analysis_resources(self) -> None:
    """Cleanup analysis-specific resources."""
    try:
        # Clear analysis patterns and priorities
        self._analysis_patterns.clear()
        self._file_priorities.clear()

        # Reset cache stats
        self._cache_stats = {"hits": 0, "misses": 0, "warm_requests": 0, "batch_loads": 0}
```

**AFTER**:
```python
def _cleanup_analysis_resources(self) -> None:
    """Cleanup analysis-specific resources."""
    try:
        # Delegate to CacheManager
        if self.cache_manager:
            self.cache_manager.clear_all()
```

## Step 7: Test Integration

### Unit Test Template

```python
# tests/test_cache_manager_integration.py

import pytest
from pathlib import Path
from analyzer.unified_analyzer import UnifiedConnascenceAnalyzer

def test_cache_manager_initialization():
    """Test CacheManager is properly initialized"""
    analyzer = UnifiedConnascenceAnalyzer()

    # Verify CacheManager exists
    assert hasattr(analyzer, 'cache_manager')
    assert analyzer.cache_manager is not None

    # Verify it's operational
    assert analyzer.cache_manager.cache_available

def test_cache_warming_integration():
    """Test cache warming through analyzer"""
    analyzer = UnifiedConnascenceAnalyzer()
    project_path = Path("test_project")

    # Warm cache
    analyzer.cache_manager.warm_cache(project_path)

    # Verify warming occurred
    stats = analyzer.cache_manager.get_cache_stats()
    assert stats['warm_requests'] > 0

def test_cached_ast_retrieval():
    """Test AST caching through analyzer"""
    analyzer = UnifiedConnascenceAnalyzer()
    test_file = Path("test.py")

    # First access (miss)
    tree1 = analyzer.cache_manager.get_cached_ast(test_file)

    # Second access (should hit if file exists)
    tree2 = analyzer.cache_manager.get_cached_ast(test_file)

    # Verify caching occurred
    hit_rate = analyzer.cache_manager.get_hit_rate()
    assert hit_rate > 0

def test_cache_statistics():
    """Test cache statistics access"""
    analyzer = UnifiedConnascenceAnalyzer()

    # Get statistics
    stats = analyzer.cache_manager.get_cache_stats()

    # Verify expected keys
    assert 'hits' in stats
    assert 'misses' in stats
    assert 'hit_rate' in stats
```

## Step 8: Verification Checklist

- [ ] CacheManager imported in unified_analyzer.py
- [ ] CacheManager initialized in `__init__()`
- [ ] All cache method calls replaced
- [ ] Old cache methods removed (9 methods)
- [ ] Cleanup methods updated
- [ ] Unit tests created
- [ ] Integration tests pass
- [ ] Performance benchmarks run
- [ ] Documentation updated

## Performance Validation

### Before Integration
```bash
# Measure baseline performance
python -m pytest tests/ --benchmark-only
```

### After Integration
```bash
# Verify no performance regression
python -m pytest tests/ --benchmark-only

# Check cache statistics
python -c "
from analyzer.unified_analyzer import UnifiedConnascenceAnalyzer
from pathlib import Path

analyzer = UnifiedConnascenceAnalyzer()
analyzer.cache_manager.warm_cache(Path('.'))
stats = analyzer.cache_manager.get_cache_stats()
print(f'Hit rate: {stats[\"hit_rate\"]:.1%}')
print(f'Warm requests: {stats[\"warm_requests\"]}')
"
```

## Troubleshooting

### Issue: Import Error
```
ImportError: cannot import name 'CacheManager'
```

**Solution**: Verify file exists at `analyzer/architecture/cache_manager.py`

### Issue: Attribute Error
```
AttributeError: 'CacheManager' object has no attribute 'X'
```

**Solution**: Check method name mapping table above for correct method names

### Issue: Low Cache Hit Rate
```
Warning: Low cache hit rate - consider increasing warm-up files
```

**Solution**: Increase `warm_file_count` in config:
```python
cache_config = {"warm_file_count": 30}  # Increase from 15
```

### Issue: Memory Usage Too High
```
Memory usage: 150MB / 100MB (150%)
```

**Solution**: Reduce max_memory or increase limit:
```python
cache_config = {"max_memory": 200 * 1024 * 1024}  # 200MB
```

## Rollback Plan

If integration fails, revert with:

```bash
# Restore original unified_analyzer.py from git
git checkout analyzer/unified_analyzer.py

# Or manually restore removed methods from backup
```

## Migration Timeline

1. **Phase 1** (1-2 hours): Import and initialize CacheManager
2. **Phase 2** (2-3 hours): Replace method calls systematically
3. **Phase 3** (1-2 hours): Remove old methods and test
4. **Phase 4** (1-2 hours): Integration testing and validation
5. **Phase 5** (1 hour): Documentation and cleanup

**Total Estimated Time**: 6-10 hours

## Success Metrics

- ✅ All tests pass
- ✅ Cache hit rate >80%
- ✅ No performance regression
- ✅ Memory usage within limits
- ✅ Code reduction in unified_analyzer.py (~300 LOC removed)

---

**Status**: Ready for integration
**Risk Level**: Low (well-tested extraction)
**Recommended By**: Cache extraction analysis
