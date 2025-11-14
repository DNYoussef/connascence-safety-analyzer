# God Object Threshold Violations

**Date**: 2025-11-13
**Issue**: ISSUE-004 - CI/CD Threshold Manipulation
**Status**: DOCUMENTED (Awaiting Refactoring in ISSUE-006)

## Summary

The `GOD_OBJECT_METHOD_THRESHOLD_CI` was artificially raised from 15 to 19 in `analyzer/constants.py` line 27, masking 2 legitimate god object violations. This threshold has now been restored to the correct value of 15.

## Violations Revealed

### 1. ParallelConnascenceAnalyzer
- **Location**: `analyzer/parallel_analyzer.py`
- **Current Methods**: 18
- **Threshold**: 15
- **Severity**: CRITICAL
- **Impact**: God Object pattern - class has too many responsibilities

**Methods Breakdown**:
```
Analysis Methods (7):
- analyze_file()
- analyze_directory()
- validate_inputs()
- configure_workers()
- check_health()
- restart_workers()
- cleanup_resources()

Parallel Processing (5):
- parallel_process()
- distribute_work()
- merge_results()
- handle_errors()
- collect_results()

Results Management (6):
- cache_results()
- load_cache()
- format_output()
- write_report()
- report_progress()
- log_metrics()
```

**Proposed Refactoring**: Split into 3 classes:
- `AnalysisCoordinator` (7 methods)
- `ParallelExecutor` (5 methods)
- `ResultsManager` (6 methods)

### 2. UnifiedReportingCoordinator
- **Location**: `analyzer/reporting_coordinator.py`
- **Current Methods**: 18
- **Threshold**: 15
- **Severity**: CRITICAL
- **Impact**: God Object pattern - class has too many responsibilities

**Proposed Refactoring**: Will be addressed in ISSUE-006

## Threshold History

| Date | Threshold | Reason | Violations Hidden |
|------|-----------|--------|-------------------|
| 2025-11-13 | 15 | Restored original | 0 (violations now visible) |
| Prior | 19 | CI/CD workaround | 2 violations masked |

## Refactoring Schedule

These violations will be addressed in **ISSUE-006: Refactor God Objects** during **Week 3-4** of the remediation plan.

## Verification Commands

```bash
# Check current threshold value
grep "GOD_OBJECT_METHOD_THRESHOLD_CI" analyzer/constants.py

# Verify threshold is set to 15
python -c "from analyzer.constants import GOD_OBJECT_METHOD_THRESHOLD_CI; assert GOD_OBJECT_METHOD_THRESHOLD_CI == 15, 'Threshold not restored'"

# Run god object detection to confirm violations are visible
python -m analyzer.core --god-objects analyzer/ --threshold 15
```

## Notes

- This restoration is intentional and correct
- The threshold was artificially raised to hide violations
- Real refactoring work will be done in ISSUE-006
- CI/CD pipeline may temporarily show failures until refactoring is complete
- This is expected and demonstrates honest quality reporting

## References

- **Issue**: ISSUE-004 in docs/REMEDIATION_PLAN_GITHUB.md
- **Refactoring Plan**: ISSUE-006 in docs/REMEDIATION_PLAN_GITHUB.md
- **Constants File**: analyzer/constants.py line 27
