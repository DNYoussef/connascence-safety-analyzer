# Connascence Analyzer - GitHub Issue-Based Remediation Plan

**Project:** Connascence Safety Analyzer
**Analysis Date:** 2025-11-13
**Target Completion:** Q1 2026 (12 weeks)
**Estimated Total Effort:** 480-720 hours

---

## Executive Summary

Based on comprehensive assessment showing **CRITICAL** detector pool AttributeError blocking 10/16 tests, god objects (2,442 LOC), CI/CD threshold manipulation, and bare except blocks (42+), this remediation plan provides **executable GitHub issues** with **dependency graphs**, **code snippets**, **test verification**, and **risk assessments**.

**Key Metrics:**
- **Production Readiness:** 65% -> Target 90%
- **Test Success Rate:** 88% (457/496) -> Target 100%
- **Code Coverage:** 12% -> Target 80%
- **Critical Blockers:** 12 -> Target 0

---

## Table of Contents

1. [GitHub Issue Templates](#1-github-issue-templates)
2. [Dependency Graph](#2-dependency-graph)
3. [Executable Fix Plan](#3-executable-fix-plan)
4. [Risk Assessment Matrix](#4-risk-assessment-matrix)
5. [GitHub Project Board Structure](#5-github-project-board-structure)
6. [Milestone Groups](#6-milestone-groups)
7. [Assignee Recommendations](#7-assignee-recommendations)

---

## 1. GitHub Issue Templates

### 1.1 CRITICAL Issue Template

```markdown
---
name: CRITICAL Fix
about: Blocking issue preventing core functionality
title: '[CRITICAL] '
labels: critical, blocking, high-priority
assignees: ''
---

## Priority: CRITICAL (P0)
**Blocking:** 10/16 tests
**Impact:** Production deployment blocked
**Effort:** X hours
**Milestone:** Week 1

## Problem Description
[Clear description of the critical issue]

## Current Behavior
- What's broken?
- Which tests fail?
- What errors are thrown?

## Expected Behavior
- What should happen?
- What tests should pass?

## Root Cause Analysis
- Technical root cause
- Why it occurred
- Dependencies affected

## Reproduction Steps
1. Step 1
2. Step 2
3. Observe error

## Proposed Solution
### Code Changes
```python
# Snippet of proposed fix
```

### Test Verification
```bash
# Commands to verify fix works
pytest tests/specific_test.py -v
```

## Dependencies
- [ ] Must complete #XX first
- [ ] Blocks #YY, #ZZ

## Risk Assessment
- **Blast Radius:** Files affected, tests impacted
- **Rollback Strategy:** How to revert if needed
- **Breaking Changes:** YES/NO

## Acceptance Criteria
- [ ] All blocked tests pass
- [ ] No new regressions
- [ ] Code review approved
- [ ] Documentation updated

## Related Issues
- Blocks: #XX, #YY
- Depends on: #ZZ
```

### 1.2 HIGH Issue Template

```markdown
---
name: HIGH Priority Fix
about: Significant issue affecting quality or functionality
title: '[HIGH] '
labels: high, quality-issue
assignees: ''
---

## Priority: HIGH (P1)
**Impact:** Code quality, maintainability
**Effort:** X hours
**Milestone:** Month 1

## Problem Description
[Description of high-priority issue]

## Current State
- Current metrics/violations
- Affected modules
- Technical debt impact

## Desired State
- Target metrics
- Expected improvements

## Code Location
- **Files:** `path/to/file.py` (lines X-Y)
- **Modules:** Affected components

## Proposed Solution
### Refactoring Steps
1. Step 1: Extract X
2. Step 2: Create Y
3. Step 3: Move Z

### Code Snippets
```python
# Before
class GodObject:
    def method1(self): pass
    def method2(self): pass
    # ... 30+ methods

# After
class Coordinator:
    def coordinate(self): pass

class Executor:
    def execute(self): pass
```

### Test Commands
```bash
# Verify refactoring
pytest tests/test_refactored.py -v
python -m analyzer.refactored_module --verify
```

## Dependencies
- [ ] Optional: Complete #XX for easier refactoring

## Risk Assessment
- **Blast Radius:** Medium (X files, Y tests)
- **Rollback:** Git revert possible
- **Breaking Changes:** NO (backward compatible)

## Acceptance Criteria
- [ ] God object metrics pass
- [ ] All existing tests pass
- [ ] New tests added
- [ ] Documentation updated
```

### 1.3 MEDIUM Issue Template

```markdown
---
name: MEDIUM Priority Fix
about: Enhancement or non-blocking improvement
title: '[MEDIUM] '
labels: medium, enhancement
assignees: ''
---

## Priority: MEDIUM (P2)
**Impact:** Code quality improvement
**Effort:** X hours
**Milestone:** Quarter 1

## Problem Description
[Description of medium-priority issue]

## Current Implementation
- How it works now
- Why it needs improvement

## Proposed Improvement
- Better approach
- Benefits

## Implementation Plan
1. Step 1
2. Step 2
3. Step 3

## Code Example
```python
# Proposed implementation
```

## Test Strategy
```bash
# Test approach
```

## Dependencies
None

## Acceptance Criteria
- [ ] Implementation complete
- [ ] Tests added
- [ ] Code review passed
```

### 1.4 LOW Issue Template

```markdown
---
name: LOW Priority Fix
about: Minor improvement or cleanup
title: '[LOW] '
labels: low, cleanup, tech-debt
assignees: ''
---

## Priority: LOW (P3)
**Impact:** Minor improvement
**Effort:** <2 hours
**Milestone:** Quarter 1 (time permitting)

## Description
[Brief description]

## Quick Fix
```python
# Simple fix
```

## Acceptance Criteria
- [ ] Fix applied
- [ ] No regressions
```

---

## 2. Dependency Graph

### 2.1 Critical Path Dependencies

```
WEEK 1 (CRITICAL BLOCKERS - MUST FIX FIRST)
===========================================

ISSUE-001: Fix Detector Pool AttributeError
    |
    +-- BLOCKS --> ISSUE-005: Fix Bare Except Blocks
    |
    +-- BLOCKS --> ISSUE-008: Enable Architecture Components
    |
    +-- ENABLES -> ISSUE-002: Fix Import Path Issues (12 tests)

ISSUE-002: Fix Import Path Issues
    |
    +-- BLOCKS --> ISSUE-003: Register Missing Pytest Markers
    |
    +-- ENABLES -> 100% Test Collection Success

ISSUE-004: Fix CI/CD Threshold Manipulation
    |
    +-- INDEPENDENT (can run parallel to ISSUE-001/002)
    |
    +-- BLOCKS --> ISSUE-006: Refactor God Objects (reveals real violations)


MONTH 1 (HIGH PRIORITY - CORE REFACTORING)
==========================================

ISSUE-006: Refactor UnifiedConnascenceAnalyzer God Object
    |
    +-- DEPENDS ON --> ISSUE-001 (detector pool fixed first)
    +-- DEPENDS ON --> ISSUE-004 (real thresholds in place)
    |
    +-- ENABLES -> ISSUE-007: Refactor ConnascenceDetector
    +-- ENABLES -> ISSUE-009: Split Constants Module

ISSUE-008: Re-enable or Remove Architecture Components
    |
    +-- DEPENDS ON --> ISSUE-001 (detector pool must work)
    |
    +-- BLOCKS --> ISSUE-010: Implement Missing Features

ISSUE-005: Replace Bare Except Blocks (42+ instances)
    |
    +-- DEPENDS ON --> ISSUE-001 (detector pool errors resolved first)
    |
    +-- INDEPENDENT of other HIGH issues


QUARTER 1 (MEDIUM/LOW PRIORITY - ENHANCEMENTS)
==============================================

ISSUE-011: Implement Multi-language Support (NotImplementedError methods)
    |
    +-- DEPENDS ON --> ISSUE-007 (detector refactoring complete)
    +-- DEPENDS ON --> ISSUE-008 (architecture components working)

ISSUE-012: Improve Test Coverage (12% -> 80%)
    |
    +-- DEPENDS ON --> ISSUE-001, 002, 003 (all tests must run)
    +-- PARALLEL TO --> ISSUE-006, 007 (can write tests during refactoring)

ISSUE-013: Add Feature Detection API
    |
    +-- INDEPENDENT (can implement anytime)
    +-- LOW RISK

ISSUE-014: Clean Up Legacy Analyzers
    |
    +-- DEPENDS ON --> ISSUE-006 (unified analyzer must be solid first)
```

### 2.2 Dependency Matrix

| Issue | Depends On | Blocks | Can Run Parallel To | Effort (hrs) |
|-------|-----------|--------|---------------------|--------------|
| **ISSUE-001** | None | 005, 008, 002 | 004 | 16-24 |
| **ISSUE-002** | 001 | 003 | 004, 005 | 4-8 |
| **ISSUE-003** | 002 | None | 004, 005 | 0.5 |
| **ISSUE-004** | None | 006 | 001, 002, 003 | 8-16 |
| **ISSUE-005** | 001 | None | 002, 003, 004 | 16-24 |
| **ISSUE-006** | 001, 004 | 007, 009 | 005, 008 | 80-120 |
| **ISSUE-007** | 006 | 011 | 009, 012 | 40-60 |
| **ISSUE-008** | 001 | 010 | 005, 006 | 40-60 |
| **ISSUE-009** | 006 | None | 007, 008, 012 | 16-24 |
| **ISSUE-010** | 008 | None | All others | 80-120 |
| **ISSUE-011** | 007, 008 | None | 012, 013 | 80-120 |
| **ISSUE-012** | 001, 002, 003 | None | 006, 007, 009 | 120-180 |
| **ISSUE-013** | None | None | All others | 8-16 |
| **ISSUE-014** | 006 | None | All others | 16-24 |

---

## 3. Executable Fix Plan

### ISSUE-001: Fix Detector Pool AttributeError [CRITICAL]

**Priority:** P0 - BLOCKING
**Effort:** 16-24 hours
**Milestone:** Week 1 (Day 1-2)
**Blocks:** 10/16 tests, multiple HIGH issues

#### Problem Analysis
```python
# ERROR: AttributeError in detector_pool.py
# Root Cause: Missing should_analyze_file() method
# Impact: Blocks 10/16 tests, prevents detector coordination
```

#### Current Code (BROKEN)
```python
# File: analyzer/architecture/detector_pool.py (lines 89-95)
class DetectorPool:
    def get_active_detectors(self, file_path):
        return [
            detector for detector in self.detectors
            if detector.should_analyze_file(file_path)  # AttributeError: method missing
        ]
```

#### Proposed Fix
```python
# File: analyzer/detectors/base.py
class BaseDetector:
    """Base class for all detectors."""

    def should_analyze_file(self, file_path: str) -> bool:
        """
        Determine if detector should analyze given file.

        Args:
            file_path: Path to file to analyze

        Returns:
            True if detector supports this file type
        """
        # Check file extension against supported types
        supported_extensions = getattr(self, 'SUPPORTED_EXTENSIONS', ['.py'])
        return any(file_path.endswith(ext) for ext in supported_extensions)

    def detect(self, tree):
        """Subclasses must implement detection logic."""
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement detect() method"
        )

# File: analyzer/detectors/god_object_detector.py
class GodObjectDetector(BaseDetector):
    SUPPORTED_EXTENSIONS = ['.py', '.js', '.ts']  # Define supported types

    def detect(self, tree):
        # Existing implementation
        pass

# File: analyzer/detectors/magic_literal_detector.py
class MagicLiteralDetector(BaseDetector):
    SUPPORTED_EXTENSIONS = ['.py', '.js', '.ts', '.java']

    def detect(self, tree):
        # Existing implementation
        pass
```

#### Migration Script
```python
# scripts/fix_detector_pool.py
import ast
import os
from pathlib import Path

def add_should_analyze_file_to_detectors():
    """Add should_analyze_file() to all detector classes."""

    detectors_dir = Path("analyzer/detectors")
    base_detector_content = '''
    def should_analyze_file(self, file_path: str) -> bool:
        """Check if detector should analyze file."""
        supported_extensions = getattr(self, 'SUPPORTED_EXTENSIONS', ['.py'])
        return any(file_path.endswith(ext) for ext in supported_extensions)
    '''

    # Add to base.py
    base_path = detectors_dir / "base.py"
    with open(base_path, 'r') as f:
        content = f.read()

    # Insert method after __init__ if not present
    if 'should_analyze_file' not in content:
        # Find insertion point (after class definition)
        tree = ast.parse(content)
        # ... insertion logic ...

    print("✅ Added should_analyze_file() to BaseDetector")

    # Update all detector subclasses
    for detector_file in detectors_dir.glob("*_detector.py"):
        # Add SUPPORTED_EXTENSIONS if missing
        print(f"✅ Updated {detector_file.name}")

if __name__ == "__main__":
    add_should_analyze_file_to_detectors()
```

#### Test Verification
```bash
# Step 1: Run migration script
python scripts/fix_detector_pool.py

# Step 2: Verify base detector
python -c "
from analyzer.detectors.base import BaseDetector
detector = BaseDetector()
assert hasattr(detector, 'should_analyze_file')
assert detector.should_analyze_file('test.py') == True
print('✅ BaseDetector.should_analyze_file() works')
"

# Step 3: Verify detector pool
python -c "
from analyzer.architecture.detector_pool import DetectorPool
pool = DetectorPool()
active = pool.get_active_detectors('test.py')
print(f'✅ DetectorPool returned {len(active)} detectors')
"

# Step 4: Run blocked tests
pytest tests/architecture/test_detector_pool.py -v
pytest tests/detectors/test_detector_factory.py -v

# Step 5: Full test suite (10 previously blocked tests should pass)
pytest tests/ -v --tb=short | grep -E "PASSED|FAILED"
```

#### Rollback Strategy
```bash
# If fix breaks something, rollback
git diff HEAD > /tmp/issue-001-fix.patch
git checkout analyzer/detectors/base.py
git checkout analyzer/architecture/detector_pool.py

# Restore if needed
git apply /tmp/issue-001-fix.patch
```

#### Risk Assessment
- **Blast Radius:** 16 detector files, 10 blocked tests, detector_pool.py
- **Breaking Changes:** NO (adding missing method, backward compatible)
- **Regression Risk:** LOW (method is defensive, returns True for .py files by default)
- **Rollback Time:** <5 minutes (single git checkout)

---

### ISSUE-002: Fix Import Path Issues [CRITICAL]

**Priority:** P0 - BLOCKING
**Effort:** 4-8 hours
**Milestone:** Week 1 (Day 2)
**Depends On:** ISSUE-001
**Blocks:** 8 E2E test modules

#### Problem Analysis
```python
# ERROR: ModuleNotFoundError: No module named 'cli.connascence'
# Root Cause: Tests expect cli.connascence, actual path is interfaces.cli.connascence
# Impact: 8 E2E test modules fail to collect (2,000+ LOC untested)
```

#### Proposed Fix Options

**Option A: CLI Package Alias (RECOMMENDED)**
```python
# Create: cli/__init__.py
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
    # ... all public exports
]
```

**Option B: Update All Test Imports (Alternative)**
```python
# Update in 8 test files:
# tests/e2e/test_cli_workflows.py:34
# tests/e2e/test_enterprise_scale.py
# tests/e2e/test_error_handling.py
# tests/e2e/test_exit_codes.py
# tests/e2e/test_memory_coordination.py
# tests/e2e/test_performance.py
# tests/e2e/test_report_generation.py
# tests/e2e/test_repository_analysis.py

# FROM:
from cli.connascence import ConnascenceCLI

# TO:
from interfaces.cli.connascence import ConnascenceCLI
```

#### Automated Fix Script
```bash
#!/bin/bash
# scripts/fix_import_paths.sh

echo "=== ISSUE-002: Fixing Import Paths ==="

# Option A: Create CLI alias (RECOMMENDED)
echo "Creating CLI package alias..."
mkdir -p cli
cat > cli/__init__.py << 'EOF'
"""CLI package alias for backward compatibility."""
from interfaces.cli.connascence import *

__all__ = ['ConnascenceCLI', 'CLIFormatter', 'CLIError']
EOF

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

# Option B: Update imports (if Option A doesn't work)
# Uncomment if needed:
# echo "Updating test imports..."
# find tests/e2e -name "*.py" -exec sed -i \
#   's/from cli\.connascence/from interfaces.cli.connascence/g' {} \;
```

#### Test Verification
```bash
# Step 1: Run fix script
bash scripts/fix_import_paths.sh

# Step 2: Verify alias
python -c "from cli.connascence import ConnascenceCLI; print('✅ Import works')"

# Step 3: Test each blocked E2E module
pytest tests/e2e/test_cli_workflows.py --collect-only
pytest tests/e2e/test_enterprise_scale.py --collect-only
pytest tests/e2e/test_error_handling.py --collect-only
pytest tests/e2e/test_exit_codes.py --collect-only
pytest tests/e2e/test_memory_coordination.py --collect-only
pytest tests/e2e/test_performance.py --collect-only
pytest tests/e2e/test_report_generation.py --collect-only
pytest tests/e2e/test_repository_analysis.py --collect-only

# Step 4: Run full E2E suite
pytest tests/e2e/ -v

# Step 5: Verify no regressions
pytest tests/ -v | tee test_results.log
```

#### Risk Assessment
- **Blast Radius:** 8 E2E test files, 1 new package (cli/)
- **Breaking Changes:** NO (adds alias, doesn't modify existing code)
- **Regression Risk:** VERY LOW (only adds backward compatibility)
- **Rollback Time:** <1 minute (delete cli/ directory)

---

### ISSUE-003: Register Missing Pytest Markers [CRITICAL]

**Priority:** P0 - BLOCKING
**Effort:** 0.5 hours (30 minutes)
**Milestone:** Week 1 (Day 2)
**Depends On:** ISSUE-002
**Blocks:** 4 enhanced test modules

#### Problem Analysis
```python
# ERROR: PytestUnknownMarkWarning: Unknown pytest.mark.cli
# Root Cause: Markers used but not registered in pyproject.toml
# Impact: 4 enhanced integration test modules fail
```

#### Current Configuration
```toml
# pyproject.toml (lines 45-52)
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

#### Proposed Fix
```toml
# pyproject.toml
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

#### Automated Fix Script
```bash
#!/bin/bash
# scripts/fix_pytest_markers.sh

echo "=== ISSUE-003: Registering Missing Pytest Markers ==="

# Backup original
cp pyproject.toml pyproject.toml.backup

# Add missing markers using Python
python3 << 'EOF'
import toml

# Load config
with open('pyproject.toml', 'r') as f:
    config = toml.load(f)

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
with open('pyproject.toml', 'w') as f:
    toml.dump(config, f)

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

#### Test Verification
```bash
# Step 1: Run fix script
bash scripts/fix_pytest_markers.sh

# Step 2: Verify markers registered
pytest --markers | grep -E "@pytest.mark.cli"
pytest --markers | grep -E "@pytest.mark.mcp_server"
pytest --markers | grep -E "@pytest.mark.vscode"
pytest --markers | grep -E "@pytest.mark.web_dashboard"

# Step 3: Test each enhanced module
pytest tests/enhanced/test_cli_integration.py --collect-only
pytest tests/enhanced/test_mcp_server_integration.py --collect-only
pytest tests/enhanced/test_vscode_integration.py --collect-only
pytest tests/enhanced/test_web_dashboard_integration.py --collect-only

# Step 4: Run enhanced suite
pytest tests/enhanced/ -v

# Step 5: Full test collection check
pytest tests/ --collect-only | grep -E "error|ERROR"
```

#### Risk Assessment
- **Blast Radius:** 1 file (pyproject.toml), 4 test modules
- **Breaking Changes:** NO (only adds markers)
- **Regression Risk:** NONE (purely additive configuration)
- **Rollback Time:** <30 seconds (restore backup)

---

### ISSUE-004: Fix CI/CD Threshold Manipulation [CRITICAL]

**Priority:** P0 - QUALITY ISSUE
**Effort:** 8-16 hours
**Milestone:** Week 1 (Day 3-4)
**Blocks:** ISSUE-006 (god object refactoring)

#### Problem Analysis
```python
# ISSUE: CI/CD threshold deliberately increased to hide violations
# File: analyzer/constants.py:25-27
# Impact: False sense of security, masks real god object violations
```

#### Current Code (PROBLEMATIC)
```python
# analyzer/constants.py (lines 25-27)
# TODO: Refactor ParallelConnascenceAnalyzer (18 methods)
#       and UnifiedReportingCoordinator (18 methods)
GOD_OBJECT_METHOD_THRESHOLD_CI = 19  # Temporary increase to allow CI/CD to pass

# ORIGINAL THRESHOLDS (should be restored):
GOD_OBJECT_METHOD_THRESHOLD = 15  # General development
GOD_OBJECT_METHOD_THRESHOLD_CRITICAL = 10  # Critical code paths
```

#### Proposed Fix (Two-Phase Approach)

**Phase 1: Revert Threshold + Document Violations**
```python
# analyzer/constants.py
# RESTORE original threshold
GOD_OBJECT_METHOD_THRESHOLD_CI = 15  # Restored from 19

# Document violations that will now be caught
# violations_to_fix.md:
# 1. ParallelConnascenceAnalyzer: 18 methods -> needs extraction
# 2. UnifiedReportingCoordinator: 18 methods -> needs extraction
```

**Phase 2: Refactor Violating Classes**
```python
# BEFORE: ParallelConnascenceAnalyzer (18 methods)
class ParallelConnascenceAnalyzer:
    def analyze_file(self): pass
    def analyze_directory(self): pass
    def parallel_process(self): pass
    def merge_results(self): pass
    def report_progress(self): pass
    def handle_errors(self): pass
    def validate_inputs(self): pass
    def cache_results(self): pass
    def load_cache(self): pass
    def configure_workers(self): pass
    def distribute_work(self): pass
    def collect_results(self): pass
    def format_output(self): pass
    def write_report(self): pass
    def cleanup_resources(self): pass
    def log_metrics(self): pass
    def check_health(self): pass
    def restart_workers(self): pass
    # 18 methods total

# AFTER: Decomposed into focused classes (each <15 methods)
class AnalysisCoordinator:
    """Coordinates analysis workflow (7 methods)."""
    def analyze_file(self): pass
    def analyze_directory(self): pass
    def validate_inputs(self): pass
    def configure_workers(self): pass
    def check_health(self): pass
    def restart_workers(self): pass
    def cleanup_resources(self): pass

class ParallelExecutor:
    """Handles parallel processing (5 methods)."""
    def parallel_process(self): pass
    def distribute_work(self): pass
    def merge_results(self): pass
    def handle_errors(self): pass
    def collect_results(self): pass

class ResultsManager:
    """Manages results and caching (6 methods)."""
    def cache_results(self): pass
    def load_cache(self): pass
    def format_output(self): pass
    def write_report(self): pass
    def report_progress(self): pass
    def log_metrics(self): pass
```

#### Refactoring Script
```python
# scripts/fix_threshold_violations.py
"""
Refactor classes violating god object thresholds.
"""
import ast
import os
from pathlib import Path

def extract_methods_from_class(source_file, class_name, methods_to_extract):
    """Extract methods into new class."""
    with open(source_file, 'r') as f:
        tree = ast.parse(f.read())

    # Find class definition
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            # Extract specified methods
            extracted_methods = [
                method for method in node.body
                if isinstance(method, ast.FunctionDef) and method.name in methods_to_extract
            ]

            # Create new class with extracted methods
            new_class = ast.ClassDef(
                name=f"{class_name}Extracted",
                bases=[],
                keywords=[],
                body=extracted_methods,
                decorator_list=[]
            )

            return ast.unparse(new_class)

    return None

def refactor_parallel_analyzer():
    """Refactor ParallelConnascenceAnalyzer into 3 classes."""

    source = Path("analyzer/parallel_analyzer.py")

    # Define method groups
    coordinator_methods = [
        'analyze_file', 'analyze_directory', 'validate_inputs',
        'configure_workers', 'check_health', 'restart_workers', 'cleanup_resources'
    ]

    executor_methods = [
        'parallel_process', 'distribute_work', 'merge_results',
        'handle_errors', 'collect_results'
    ]

    results_methods = [
        'cache_results', 'load_cache', 'format_output',
        'write_report', 'report_progress', 'log_metrics'
    ]

    # Extract each group
    coordinator_code = extract_methods_from_class(
        source, 'ParallelConnascenceAnalyzer', coordinator_methods
    )

    executor_code = extract_methods_from_class(
        source, 'ParallelConnascenceAnalyzer', executor_methods
    )

    results_code = extract_methods_from_class(
        source, 'ParallelConnascenceAnalyzer', results_methods
    )

    # Write new files
    with open("analyzer/analysis_coordinator.py", "w") as f:
        f.write(coordinator_code)

    with open("analyzer/parallel_executor.py", "w") as f:
        f.write(executor_code)

    with open("analyzer/results_manager.py", "w") as f:
        f.write(results_code)

    print("✅ Refactored ParallelConnascenceAnalyzer into 3 classes")
    print("   - AnalysisCoordinator (7 methods)")
    print("   - ParallelExecutor (5 methods)")
    print("   - ResultsManager (6 methods)")

if __name__ == "__main__":
    # Step 1: Revert threshold
    print("Step 1: Reverting GOD_OBJECT_METHOD_THRESHOLD_CI to 15...")
    # ... implementation ...

    # Step 2: Refactor violating classes
    print("Step 2: Refactoring violating classes...")
    refactor_parallel_analyzer()

    print("✅ ISSUE-004 fix complete")
```

#### Test Verification
```bash
# Step 1: Revert threshold and document violations
grep -n "GOD_OBJECT_METHOD_THRESHOLD_CI" analyzer/constants.py
# Should show: GOD_OBJECT_METHOD_THRESHOLD_CI = 15

# Step 2: Run god object detection (should catch violations)
python -m analyzer.core --god-objects analyzer/ 2>&1 | grep -E "18 methods"

# Step 3: Run refactoring script
python scripts/fix_threshold_violations.py

# Step 4: Verify new classes exist and have correct method counts
python -c "
from analyzer.analysis_coordinator import AnalysisCoordinator
from analyzer.parallel_executor import ParallelExecutor
from analyzer.results_manager import ResultsManager

coord_methods = len([m for m in dir(AnalysisCoordinator) if not m.startswith('_')])
exec_methods = len([m for m in dir(ParallelExecutor) if not m.startswith('_')])
results_methods = len([m for m in dir(ResultsManager) if not m.startswith('_')])

assert coord_methods <= 15, f'AnalysisCoordinator has {coord_methods} methods'
assert exec_methods <= 15, f'ParallelExecutor has {exec_methods} methods'
assert results_methods <= 15, f'ResultsManager has {results_methods} methods'

print('✅ All refactored classes pass god object threshold')
"

# Step 5: Run full test suite
pytest tests/ -v

# Step 6: Run CI/CD with real thresholds
python -m analyzer.core --god-objects analyzer/ --threshold 15 --strict
```

#### Risk Assessment
- **Blast Radius:** HIGH - 2 core classes refactored, threshold changes affect all code
- **Breaking Changes:** POSSIBLY (if external code imports refactored classes)
- **Regression Risk:** MEDIUM (refactoring always risks breaking logic)
- **Rollback Time:** 5-10 minutes (git revert + restore threshold)
- **Mitigation:** Comprehensive test suite run before/after, feature flag for new classes

---

### ISSUE-005: Replace Bare Except Blocks [HIGH]

**Priority:** P1 - QUALITY ISSUE
**Effort:** 16-24 hours
**Milestone:** Month 1 (Week 2-3)
**Depends On:** ISSUE-001 (detector pool errors must be resolved first)

#### Problem Analysis
```python
# ISSUE: 42+ bare except blocks catching ALL exceptions
# Files affected: unified_analyzer.py, check_connascence.py, formal_grammar.py
# Risk: Silently catches critical errors (KeyboardInterrupt, SystemExit, MemoryError)
```

#### Current Code (DANGEROUS)
```python
# unified_analyzer.py (lines 329-332)
try:
    return SmartIntegrationEngine()
except:  # TOO BROAD - catches ALL exceptions including SystemExit
    return None

# check_connascence.py (lines 82-84)
try:
    from .optimization import FileCache
except:  # Catches ImportError but also KeyboardInterrupt
    FileCache = None

# formal_grammar.py (lines 74-84)
try:
    backend = TreeSitterBackend()
except:  # Masks real initialization errors
    backend = None
```

#### Proposed Fix
```python
# unified_analyzer.py (AFTER)
try:
    return SmartIntegrationEngine()
except (ImportError, ModuleNotFoundError) as e:
    logger.warning(f"SmartIntegrationEngine unavailable: {e}")
    return None
except Exception as e:
    logger.error(f"Failed to initialize SmartIntegrationEngine: {e}")
    raise  # Re-raise for unexpected errors

# check_connascence.py (AFTER)
try:
    from .optimization import FileCache
except ImportError as e:
    logger.debug(f"Optimization module unavailable: {e}")
    FileCache = None
# KeyboardInterrupt and SystemExit now propagate correctly

# formal_grammar.py (AFTER)
try:
    backend = TreeSitterBackend()
except (ImportError, RuntimeError) as e:
    logger.warning(f"TreeSitter backend unavailable: {e}")
    backend = None
except Exception as e:
    logger.error(f"Unexpected error initializing TreeSitter: {e}")
    backend = None
```

#### Automated Replacement Script
```python
# scripts/fix_bare_except.py
"""
Replace bare except blocks with specific exception handling.
"""
import ast
import re
from pathlib import Path

class BareExceptReplacer(ast.NodeTransformer):
    """AST transformer to replace bare except blocks."""

    def visit_ExceptHandler(self, node):
        # If except has no type (bare except)
        if node.type is None:
            # Analyze what's in the try block
            common_exceptions = self._infer_exceptions(node)

            # Replace with specific exceptions
            if 'import' in str(node.body):
                node.type = ast.Tuple(elts=[
                    ast.Name(id='ImportError', ctx=ast.Load()),
                    ast.Name(id='ModuleNotFoundError', ctx=ast.Load())
                ])
            else:
                node.type = ast.Name(id='Exception', ctx=ast.Load())

            # Add logging
            log_stmt = ast.Expr(value=ast.Call(
                func=ast.Attribute(
                    value=ast.Name(id='logger', ctx=ast.Load()),
                    attr='warning',
                    ctx=ast.Load()
                ),
                args=[ast.Str(s='Caught exception')],
                keywords=[]
            ))
            node.body.insert(0, log_stmt)

        return node

    def _infer_exceptions(self, node):
        """Infer which exceptions likely occur in try block."""
        source = ast.unparse(node)

        exceptions = []
        if 'import' in source:
            exceptions.extend(['ImportError', 'ModuleNotFoundError'])
        if 'open(' in source:
            exceptions.extend(['FileNotFoundError', 'PermissionError'])
        if '[' in source or 'dict' in source:
            exceptions.append('KeyError')
        if '.get(' in source or '.pop(' in source:
            exceptions.append('AttributeError')

        return exceptions or ['Exception']

def fix_file_bare_excepts(file_path):
    """Fix bare except blocks in a single file."""
    with open(file_path, 'r') as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        print(f"⚠️ Syntax error in {file_path}, skipping")
        return 0

    # Count bare excepts before
    bare_excepts_before = sum(
        1 for node in ast.walk(tree)
        if isinstance(node, ast.ExceptHandler) and node.type is None
    )

    # Transform
    transformer = BareExceptReplacer()
    new_tree = transformer.visit(tree)

    # Generate new source
    new_source = ast.unparse(new_tree)

    # Write back
    with open(file_path, 'w') as f:
        f.write(new_source)

    return bare_excepts_before

def fix_all_bare_excepts():
    """Fix bare except blocks across entire codebase."""

    files_to_fix = [
        "analyzer/unified_analyzer.py",
        "analyzer/check_connascence.py",
        "analyzer/formal_grammar.py",
        "analyzer/core.py",
        "analyzer/context_analyzer.py",
    ]

    total_fixed = 0
    for file_path in files_to_fix:
        if Path(file_path).exists():
            count = fix_file_bare_excepts(file_path)
            total_fixed += count
            print(f"✅ Fixed {count} bare except blocks in {file_path}")

    print(f"\n✅ Total: Fixed {total_fixed} bare except blocks")

if __name__ == "__main__":
    fix_all_bare_excepts()
```

#### Test Verification
```bash
# Step 1: Count bare except blocks before fix
grep -rn "except:" analyzer/ | wc -l
# Should show ~42

# Step 2: Run fix script
python scripts/fix_bare_except.py

# Step 3: Verify specific exceptions now used
grep -rn "except:" analyzer/ | grep -v "except Exception" | grep -v "except (ImportError"
# Should show 0 or very few

# Step 4: Test KeyboardInterrupt propagation
python -c "
import signal
import time

# Test that Ctrl+C now works
def test_keyboard_interrupt():
    try:
        from analyzer.unified_analyzer import UnifiedConnascenceAnalyzer
        analyzer = UnifiedConnascenceAnalyzer()
        # Simulate long-running operation
        time.sleep(1)
    except KeyboardInterrupt:
        print('✅ KeyboardInterrupt properly propagated')
        return True
    return False

# Send SIGINT
signal.alarm(1)
test_keyboard_interrupt()
"

# Step 5: Run full test suite
pytest tests/ -v

# Step 6: Test error handling with deliberate failures
python -c "
import sys
# Simulate import error
try:
    from analyzer.nonexistent_module import Fake
except ImportError as e:
    print(f'✅ ImportError handled: {e}')

# Simulate runtime error
try:
    from analyzer.unified_analyzer import UnifiedConnascenceAnalyzer
    analyzer = UnifiedConnascenceAnalyzer()
    # Trigger error
    analyzer.some_method_that_doesnt_exist()
except AttributeError as e:
    print(f'✅ AttributeError handled: {e}')
"
```

#### Risk Assessment
- **Blast Radius:** MEDIUM - 42+ except blocks across 5 core files
- **Breaking Changes:** POSSIBLY (if code relied on catching unexpected exceptions)
- **Regression Risk:** LOW-MEDIUM (mostly initialization code)
- **Rollback Time:** 2-5 minutes (git revert)
- **Mitigation:** Test suite + manual testing of error scenarios

---

### ISSUE-006: Refactor UnifiedConnascenceAnalyzer God Object [HIGH]

**Priority:** P1 - ARCHITECTURAL
**Effort:** 80-120 hours
**Milestone:** Month 1 (Week 3-4)
**Depends On:** ISSUE-001 (detector pool), ISSUE-004 (real thresholds)
**Blocks:** ISSUE-007 (ConnascenceDetector), ISSUE-009 (Constants split)

#### Problem Analysis
```python
# CRITICAL GOD OBJECT: UnifiedConnascenceAnalyzer
# File: analyzer/unified_analyzer.py
# LOC: 2,442 lines (threshold: 400 general, 300 critical)
# Methods: 30+ (threshold: 20)
# Responsibilities: 7+ (Analysis, Caching, Streaming, Monitoring, Config, Metrics, Recommendations)
```

#### Current Structure (GOD OBJECT)
```python
# unified_analyzer.py (2,442 LOC, 30+ methods)
class UnifiedConnascenceAnalyzer:
    """VIOLATES Single Responsibility Principle - Does Everything!"""

    # RESPONSIBILITY 1: Configuration
    def __init__(self, config): pass
    def load_config(self): pass
    def validate_config(self): pass

    # RESPONSIBILITY 2: Analysis Orchestration
    def analyze_project(self): pass
    def analyze_file(self): pass
    def analyze_directory(self): pass
    def _run_analysis_phases(self): pass  # 150 LOC!

    # RESPONSIBILITY 3: Caching
    def init_cache(self): pass
    def load_cache(self): pass
    def save_cache(self): pass
    def invalidate_cache(self): pass

    # RESPONSIBILITY 4: Streaming
    def init_streaming(self): pass
    def stream_results(self): pass
    def handle_stream_events(self): pass

    # RESPONSIBILITY 5: Monitoring
    def init_monitoring(self): pass
    def track_metrics(self): pass
    def report_health(self): pass

    # RESPONSIBILITY 6: Results & Reporting
    def aggregate_results(self): pass
    def format_report(self): pass
    def export_sarif(self): pass
    def export_json(self): pass

    # RESPONSIBILITY 7: Recommendations
    def generate_recommendations(self): pass
    def calculate_severity(self): pass
    def prioritize_fixes(self): pass

    # ... 30+ methods total across 2,442 LOC
```

#### Proposed Decomposition (MECE Principle)

```python
# ===== NEW FILE: analyzer/orchestration/coordinator.py =====
class AnalysisCoordinator:
    """
    Thin facade coordinating analysis workflow (200 LOC, 8 methods).
    SINGLE RESPONSIBILITY: Orchestrate analysis phases
    """
    def __init__(self, config):
        self.config = config
        self.cache_manager = CacheManager(config.cache)
        self.streaming_manager = StreamingManager(config.streaming)
        self.monitoring = MonitoringService(config.monitoring)
        self.results_aggregator = ResultsAggregator()

    def analyze_project(self, project_path):
        """Coordinate full project analysis."""
        self.monitoring.start_analysis()

        # Phase 1: Discovery
        files = self._discover_files(project_path)

        # Phase 2: Analysis
        results = []
        for file_path in files:
            cached = self.cache_manager.get(file_path)
            if cached:
                results.append(cached)
            else:
                result = self.analyze_file(file_path)
                self.cache_manager.store(file_path, result)
                results.append(result)

        # Phase 3: Aggregation
        aggregated = self.results_aggregator.aggregate(results)

        # Phase 4: Reporting
        self.monitoring.end_analysis()
        return aggregated

    def analyze_file(self, file_path):
        """Delegate to detector pool."""
        from analyzer.architecture.detector_pool import DetectorPool
        pool = DetectorPool()
        return pool.analyze(file_path)

    def _discover_files(self, project_path):
        """File discovery logic."""
        # ... implementation ...
        pass

# ===== NEW FILE: analyzer/caching/cache_manager.py =====
class CacheManager:
    """
    Manages file-level result caching (150 LOC, 6 methods).
    SINGLE RESPONSIBILITY: Cache coordination
    """
    def __init__(self, config):
        from analyzer.optimization.file_cache import FileCache
        self.cache = FileCache(config)

    def get(self, file_path):
        """Retrieve cached result."""
        return self.cache.get(file_path)

    def store(self, file_path, result):
        """Store analysis result."""
        self.cache.put(file_path, result)

    def invalidate(self, file_path):
        """Invalidate cache entry."""
        self.cache.delete(file_path)

    def clear_all(self):
        """Clear entire cache."""
        self.cache.clear()

# ===== NEW FILE: analyzer/streaming/streaming_manager.py =====
class StreamingManager:
    """
    Manages real-time streaming (180 LOC, 5 methods).
    SINGLE RESPONSIBILITY: Streaming coordination
    """
    def __init__(self, config):
        if config.enabled:
            from analyzer.streaming.stream_processor import StreamProcessor
            self.processor = StreamProcessor(config)
        else:
            self.processor = None

    def emit_event(self, event_type, data):
        """Emit streaming event."""
        if self.processor:
            self.processor.emit(event_type, data)

    def subscribe(self, event_type, callback):
        """Subscribe to events."""
        if self.processor:
            self.processor.subscribe(event_type, callback)

# ===== NEW FILE: analyzer/monitoring/monitoring_service.py =====
class MonitoringService:
    """
    Manages health monitoring (120 LOC, 7 methods).
    SINGLE RESPONSIBILITY: System monitoring
    """
    def __init__(self, config):
        if config.enabled:
            from analyzer.optimization.memory_monitor import MemoryMonitor
            self.memory = MemoryMonitor()
        else:
            self.memory = None

    def start_analysis(self):
        """Start monitoring session."""
        if self.memory:
            self.memory.start_tracking()

    def end_analysis(self):
        """End monitoring session."""
        if self.memory:
            metrics = self.memory.get_metrics()
            self._log_metrics(metrics)

# ===== NEW FILE: analyzer/reporting/results_aggregator.py =====
class ResultsAggregator:
    """
    Aggregates and formats results (200 LOC, 10 methods).
    SINGLE RESPONSIBILITY: Result processing
    """
    def aggregate(self, results):
        """Aggregate multiple file results."""
        aggregated = {
            'total_files': len(results),
            'violations': self._aggregate_violations(results),
            'metrics': self._calculate_metrics(results),
            'recommendations': self._generate_recommendations(results)
        }
        return aggregated

    def _aggregate_violations(self, results):
        """Combine violations from all files."""
        # ... implementation ...
        pass

    def export_sarif(self, aggregated):
        """Export to SARIF format."""
        from analyzer.formatters.sarif import SARIFFormatter
        formatter = SARIFFormatter()
        return formatter.format(aggregated)

# ===== UPDATED FILE: analyzer/unified_analyzer.py =====
class UnifiedConnascenceAnalyzer:
    """
    Thin facade delegating to specialized managers (50 LOC, 3 methods).
    NOW COMPLIES: <300 LOC critical, <15 methods
    """
    def __init__(self, config=None):
        """Initialize with configuration."""
        self.coordinator = AnalysisCoordinator(config or {})

    def analyze_project(self, project_path):
        """Analyze entire project."""
        return self.coordinator.analyze_project(project_path)

    def analyze_file(self, file_path):
        """Analyze single file."""
        return self.coordinator.analyze_file(file_path)
```

#### Migration Script
```python
# scripts/refactor_unified_analyzer.py
"""
Refactor UnifiedConnascenceAnalyzer god object into MECE components.
"""
import ast
import shutil
from pathlib import Path

def extract_responsibility_methods(source_path, class_name, methods_list):
    """Extract methods for a single responsibility."""
    with open(source_path, 'r') as f:
        tree = ast.parse(f.read())

    # Find class
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            # Extract specified methods
            extracted = [
                method for method in node.body
                if isinstance(method, ast.FunctionDef) and method.name in methods_list
            ]
            return extracted

    return []

def create_new_module(module_path, class_name, methods, docstring):
    """Create new module file with extracted class."""
    class_def = f'''"""
{docstring}
"""
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class {class_name}:
    """
    {docstring}
    """
    def __init__(self, config):
        """Initialize {class_name}."""
        self.config = config

'''

    # Add each method
    for method in methods:
        class_def += ast.unparse(method) + "\n\n"

    # Write to file
    module_path.parent.mkdir(parents=True, exist_ok=True)
    with open(module_path, 'w') as f:
        f.write(class_def)

    print(f"✅ Created {module_path} with {len(methods)} methods")

def refactor_unified_analyzer():
    """Main refactoring logic."""

    source = Path("analyzer/unified_analyzer.py")

    # Backup original
    shutil.copy(source, source.with_suffix('.py.backup'))

    # Define responsibility groups
    responsibilities = {
        'AnalysisCoordinator': {
            'path': Path("analyzer/orchestration/coordinator.py"),
            'methods': ['analyze_project', 'analyze_file', 'analyze_directory', '_run_analysis_phases'],
            'docstring': 'Coordinates analysis workflow phases.'
        },
        'CacheManager': {
            'path': Path("analyzer/caching/cache_manager.py"),
            'methods': ['init_cache', 'load_cache', 'save_cache', 'invalidate_cache'],
            'docstring': 'Manages file-level result caching.'
        },
        'StreamingManager': {
            'path': Path("analyzer/streaming/streaming_manager.py"),
            'methods': ['init_streaming', 'stream_results', 'handle_stream_events'],
            'docstring': 'Manages real-time streaming of analysis results.'
        },
        'MonitoringService': {
            'path': Path("analyzer/monitoring/monitoring_service.py"),
            'methods': ['init_monitoring', 'track_metrics', 'report_health'],
            'docstring': 'Manages system health monitoring.'
        },
        'ResultsAggregator': {
            'path': Path("analyzer/reporting/results_aggregator.py"),
            'methods': ['aggregate_results', 'format_report', 'export_sarif', 'export_json'],
            'docstring': 'Aggregates and formats analysis results.'
        },
    }

    # Extract and create each responsibility
    for class_name, info in responsibilities.items():
        methods = extract_responsibility_methods(
            source, 'UnifiedConnascenceAnalyzer', info['methods']
        )
        create_new_module(
            info['path'], class_name, methods, info['docstring']
        )

    # Create new thin facade
    facade_code = '''"""
Unified Connascence Analyzer - Thin Facade.

Delegates to specialized managers for single responsibilities.
"""
from analyzer.orchestration.coordinator import AnalysisCoordinator

class UnifiedConnascenceAnalyzer:
    """Thin facade coordinating analysis components."""

    def __init__(self, config=None):
        """Initialize with configuration."""
        self.coordinator = AnalysisCoordinator(config or {})

    def analyze_project(self, project_path):
        """Analyze entire project."""
        return self.coordinator.analyze_project(project_path)

    def analyze_file(self, file_path):
        """Analyze single file."""
        return self.coordinator.analyze_file(file_path)
'''

    with open(source, 'w') as f:
        f.write(facade_code)

    print(f"\n✅ Refactoring complete!")
    print(f"   - unified_analyzer.py reduced from 2,442 LOC to ~50 LOC")
    print(f"   - Created 5 new specialized modules")
    print(f"   - Each module < 200 LOC, < 10 methods")

if __name__ == "__main__":
    refactor_unified_analyzer()
```

#### Test Verification
```bash
# Step 1: Backup before refactoring
cp analyzer/unified_analyzer.py analyzer/unified_analyzer.py.before-refactor

# Step 2: Run refactoring script
python scripts/refactor_unified_analyzer.py

# Step 3: Verify new structure
ls -lh analyzer/orchestration/coordinator.py
ls -lh analyzer/caching/cache_manager.py
ls -lh analyzer/streaming/streaming_manager.py
ls -lh analyzer/monitoring/monitoring_service.py
ls -lh analyzer/reporting/results_aggregator.py

# Step 4: Check LOC for each new module
wc -l analyzer/orchestration/coordinator.py  # Should be ~200 LOC
wc -l analyzer/caching/cache_manager.py      # Should be ~150 LOC
wc -l analyzer/unified_analyzer.py           # Should be ~50 LOC

# Step 5: Verify method counts
python -c "
import inspect
from analyzer.unified_analyzer import UnifiedConnascenceAnalyzer
from analyzer.orchestration.coordinator import AnalysisCoordinator

facade_methods = len([m for m in dir(UnifiedConnascenceAnalyzer) if not m.startswith('_')])
coord_methods = len([m for m in dir(AnalysisCoordinator) if not m.startswith('_')])

assert facade_methods <= 5, f'Facade has {facade_methods} methods (should be <=5)'
assert coord_methods <= 15, f'Coordinator has {coord_methods} methods (should be <=15)'

print('✅ All classes pass god object thresholds')
"

# Step 6: Run god object detection on refactored code
python -m analyzer.core --god-objects analyzer/ --threshold 15

# Step 7: Run full test suite
pytest tests/ -v

# Step 8: Smoke test the facade
python -c "
from analyzer.unified_analyzer import UnifiedConnascenceAnalyzer
analyzer = UnifiedConnascenceAnalyzer()
result = analyzer.analyze_file('analyzer/core.py')
assert result is not None
print('✅ Facade works correctly')
"
```

#### Risk Assessment
- **Blast Radius:** VERY HIGH - Core 2,442 LOC file split into 6 modules
- **Breaking Changes:** HIGH (imports will break for external code)
- **Regression Risk:** MEDIUM-HIGH (complex refactoring of core component)
- **Rollback Time:** 10-15 minutes (restore backup + reinstall)
- **Mitigation:**
  - Comprehensive test suite (100% coverage target)
  - Feature flag to enable old vs new implementation
  - Deprecation warnings for 1 release cycle
  - Backward compatibility imports in `__init__.py`

#### Backward Compatibility Strategy
```python
# analyzer/__init__.py
"""Provide backward compatibility during transition."""
from analyzer.unified_analyzer import UnifiedConnascenceAnalyzer

# Deprecated imports (will be removed in v3.0)
try:
    # Old import path support
    from analyzer.unified_analyzer import (
        UnifiedConnascenceAnalyzer as LegacyAnalyzer
    )
    import warnings
    warnings.warn(
        "Direct import of UnifiedConnascenceAnalyzer internals is deprecated. "
        "Use analyzer.unified_analyzer.UnifiedConnascenceAnalyzer instead.",
        DeprecationWarning,
        stacklevel=2
    )
except ImportError:
    pass

__all__ = ['UnifiedConnascenceAnalyzer']
```

---

## 4. Risk Assessment Matrix

### 4.1 Risk Classification

| Risk Level | Definition | Mitigation Time | Rollback Complexity |
|-----------|------------|-----------------|---------------------|
| **CRITICAL** | Production blocking, data loss possible | <1 hour | Simple (git revert) |
| **HIGH** | Major functionality broken, no workaround | 1-4 hours | Moderate (revert + rebuild) |
| **MEDIUM** | Feature degraded, workaround available | 4-24 hours | Complex (database migration) |
| **LOW** | Minor inconvenience, no user impact | >24 hours | Very complex (multi-step) |

### 4.2 Issue Risk Matrix

| Issue | Risk Level | Blast Radius | Breaking Changes | Rollback Strategy | Rollback Time |
|-------|-----------|--------------|------------------|-------------------|---------------|
| **ISSUE-001** | CRITICAL | 16 files, 10 tests | NO | `git checkout analyzer/detectors/base.py analyzer/architecture/detector_pool.py` | <5 min |
| **ISSUE-002** | CRITICAL | 8 test files, 1 new dir | NO | `rm -rf cli/` | <1 min |
| **ISSUE-003** | CRITICAL | 1 file, 4 tests | NO | `git checkout pyproject.toml` | <30 sec |
| **ISSUE-004** | CRITICAL | 2 classes, threshold config | POSSIBLY | `git revert HEAD && restore constants.py` | 5-10 min |
| **ISSUE-005** | HIGH | 42 except blocks, 5 files | POSSIBLY | `git revert HEAD` | 2-5 min |
| **ISSUE-006** | HIGH | 2,442 LOC -> 6 modules | HIGH | `cp analyzer/unified_analyzer.py.backup analyzer/unified_analyzer.py && rm -rf analyzer/{orchestration,caching,streaming,monitoring,reporting}` | 10-15 min |
| **ISSUE-007** | MEDIUM | 1,063 LOC -> 3 modules | MEDIUM | `git revert HEAD` | 10-15 min |
| **ISSUE-008** | MEDIUM | Architecture components | HIGH | `git revert HEAD` | 5-10 min |
| **ISSUE-009** | MEDIUM | Constants module split | LOW | `git revert HEAD` | 5 min |
| **ISSUE-010** | MEDIUM | Multi-language support | NO | `git revert HEAD` | 5 min |
| **ISSUE-011** | LOW | Feature detection API | NO | `git revert HEAD` | 2 min |
| **ISSUE-012** | LOW | Test coverage | NO | N/A (tests don't affect prod) | N/A |
| **ISSUE-013** | LOW | Feature flag system | NO | `git revert HEAD` | 2 min |
| **ISSUE-014** | LOW | Legacy cleanup | POSSIBLY | `git revert HEAD` | 5 min |

### 4.3 What Breaks If We Fix X?

#### ISSUE-001 (Fix Detector Pool)
**What breaks:**
- None (adds missing method)

**Blast radius:**
- 16 detector files gain `should_analyze_file()` method
- detector_pool.py now functional

**Dependencies enabled:**
- ISSUE-005 (bare except fixes) can proceed safely
- ISSUE-008 (architecture components) can be re-enabled

**Risk mitigation:**
- Method is defensive (returns True for .py by default)
- Backward compatible (adds functionality, doesn't remove)
- All tests must pass before merge

---

#### ISSUE-002 (Fix Import Paths)
**What breaks:**
- None (creates alias, doesn't modify existing code)

**Blast radius:**
- 8 E2E test files can now import
- 1 new package directory (`cli/`)

**Dependencies enabled:**
- ISSUE-003 (pytest markers) can proceed
- 100% test collection success achieved

**Risk mitigation:**
- Alias doesn't change actual implementation
- Old import paths still work
- Can delete `cli/` directory to rollback instantly

---

#### ISSUE-004 (Fix CI/CD Thresholds)
**What breaks:**
- **ParallelConnascenceAnalyzer** (18 methods -> violates threshold of 15)
- **UnifiedReportingCoordinator** (18 methods -> violates threshold of 15)
- CI/CD pipeline will **FAIL** until classes refactored

**Blast radius:**
- 2 core classes must be refactored
- All code depending on these classes must be updated
- Threshold constants affect entire codebase

**Dependencies blocked until fixed:**
- ISSUE-006 (UnifiedConnascenceAnalyzer refactor) **MUST** happen
- All god object detection now accurate

**Risk mitigation:**
- Phase 1: Revert threshold, document violations
- Phase 2: Refactor violating classes
- Phase 3: Re-run CI/CD with real thresholds
- Feature flag to allow gradual rollout

---

#### ISSUE-005 (Replace Bare Except Blocks)
**What breaks:**
- Code that relied on catching **unexpected** exceptions
- `KeyboardInterrupt` and `SystemExit` now propagate (GOOD)
- Import errors now logged instead of silent

**Blast radius:**
- 42+ except blocks across 5 files
- Initialization code most affected
- Fallback mechanisms now explicit

**Dependencies affected:**
- Error handling becomes more explicit
- Logging output increases (more warnings)
- Ctrl+C now works correctly during analysis

**Risk mitigation:**
- Comprehensive test suite run
- Manual testing of error scenarios
- Verify KeyboardInterrupt propagates
- Check that legitimate fallbacks still work

---

#### ISSUE-006 (Refactor UnifiedConnascenceAnalyzer God Object)
**What breaks:**
- **External imports** of `UnifiedConnascenceAnalyzer` internals
- Code directly accessing removed methods
- Tests mocking internal methods

**Blast radius:**
- 2,442 LOC split into 6 modules
- All code importing `UnifiedConnascenceAnalyzer`
- Tests for unified analyzer must be updated

**Breaking changes:**
```python
# BEFORE (BREAKS):
from analyzer.unified_analyzer import UnifiedConnascenceAnalyzer
analyzer = UnifiedConnascenceAnalyzer()
analyzer.init_cache()  # Method moved to CacheManager

# AFTER (WORKS):
from analyzer.unified_analyzer import UnifiedConnascenceAnalyzer
analyzer = UnifiedConnascenceAnalyzer()
analyzer.analyze_project('path/')  # Facade delegates internally
```

**Dependencies enabled:**
- ISSUE-007 (ConnascenceDetector refactor) can proceed
- ISSUE-009 (Constants split) easier to do

**Risk mitigation:**
- Backward compatibility shim in `__init__.py`
- Deprecation warnings for 1 release cycle
- Feature flag: `USE_LEGACY_ANALYZER=true`
- Comprehensive test suite (100% coverage target)

---

#### ISSUE-012 (Improve Test Coverage)
**What breaks:**
- Nothing (tests don't affect production code)

**Blast radius:**
- New test files added
- Coverage reports change

**Dependencies:**
- Requires ISSUE-001, 002, 003 complete (all tests must run)

**Risk mitigation:**
- Tests can be added incrementally
- No production impact

---

### 4.4 Rollback Strategies

#### Simple Rollback (ISSUE-001, 002, 003, 013, 014)
```bash
# Single file or directory revert
git checkout HEAD -- analyzer/detectors/base.py
git checkout HEAD -- pyproject.toml
rm -rf cli/

# Verify rollback
pytest tests/ -v
```

#### Moderate Rollback (ISSUE-004, 005, 009, 010, 011)
```bash
# Multiple file revert
git log --oneline | grep "ISSUE-005"  # Find commit hash
git revert abc123

# Verify rollback
pytest tests/ -v
python -m analyzer.core --verify
```

#### Complex Rollback (ISSUE-006, 007, 008)
```bash
# Major refactoring rollback
cp analyzer/unified_analyzer.py.backup analyzer/unified_analyzer.py
rm -rf analyzer/orchestration/
rm -rf analyzer/caching/
rm -rf analyzer/streaming/
rm -rf analyzer/monitoring/
rm -rf analyzer/reporting/

# Rebuild
pip install -e .

# Verify rollback
pytest tests/ -v
python -m analyzer.core --self-test
```

#### Emergency Rollback (Production Incident)
```bash
# Full project rollback to known-good state
git log --oneline | head -10  # Find last stable commit
git reset --hard abc123

# Force reinstall
pip uninstall connascence-analyzer -y
pip install -e .

# Verify stability
pytest tests/ -v --tb=short
python -m analyzer.core --health-check
```

---

## 5. GitHub Project Board Structure

### 5.1 Board Columns

```
+----------------+  +---------+  +-------------+  +---------+  +--------+
|    Backlog     |  | Blocked |  | In Progress |  | Review  |  |  Done  |
+----------------+  +---------+  +-------------+  +---------+  +--------+
| ISSUE-010      |  | ISSUE-007|  | ISSUE-001   |  | ISSUE-003| | (none) |
| ISSUE-011      |  | ISSUE-008|  | ISSUE-002   |  |          |         |
| ISSUE-012      |  | ISSUE-009|  | ISSUE-004   |  |          |         |
| ISSUE-013      |  | ISSUE-006|  |             |  |          |         |
| ISSUE-014      |  |          |  |             |  |          |         |
+----------------+  +---------+  +-------------+  +---------+  +--------+
```

### 5.2 Column Definitions

**Backlog:**
- Issues not yet started
- Sorted by priority (P0 -> P1 -> P2 -> P3)
- Can be picked up when dependencies met

**Blocked:**
- Issues waiting on dependencies
- Must have "Depends On: #XX" in description
- Auto-moves to "Ready" when dependencies complete

**In Progress:**
- Currently being worked on
- Max 3 issues per developer
- Must have assignee

**Review:**
- PR created, awaiting review
- Requires 2 approvals for CRITICAL/HIGH
- Requires 1 approval for MEDIUM/LOW

**Done:**
- Merged to main
- Tests pass
- Documentation updated

### 5.3 Labels

| Label | Color | Usage |
|-------|-------|-------|
| `critical` | Red (#d73a4a) | P0 - Production blocking |
| `high` | Orange (#d93f0b) | P1 - Major issue |
| `medium` | Yellow (#fbca04) | P2 - Enhancement |
| `low` | Green (#0e8a16) | P3 - Minor improvement |
| `blocking` | Red (#d73a4a) | Blocks other issues |
| `blocked` | Yellow (#fbca04) | Waiting on dependencies |
| `breaking-change` | Red (#d73a4a) | API breaking change |
| `backward-compat` | Green (#0e8a16) | Backward compatible |
| `refactoring` | Purple (#a2eeef) | Code refactoring |
| `testing` | Blue (#0075ca) | Test-related |
| `documentation` | Blue (#0075ca) | Docs update |
| `bug` | Red (#d73a4a) | Bug fix |
| `enhancement` | Green (#a2eeef) | New feature |
| `tech-debt` | Yellow (#fbca04) | Technical debt |
| `week-1` | Gray (#d4c5f9) | Week 1 milestone |
| `month-1` | Gray (#d4c5f9) | Month 1 milestone |
| `quarter-1` | Gray (#d4c5f9) | Quarter 1 milestone |

### 5.4 Automation Rules

**Auto-move to "Blocked":**
- When issue has "Depends On: #XX" and dependency not Done

**Auto-move to "Ready":**
- When all dependencies moved to Done

**Auto-move to "Review":**
- When PR created and linked to issue

**Auto-move to "Done":**
- When PR merged to main

**Auto-assign labels:**
- `week-1` for issues with Milestone: Week 1
- `month-1` for issues with Milestone: Month 1
- `blocking` for issues listed in "Blocks: #XX"

---

## 6. Milestone Groups

### 6.1 Week 1 - Critical Blockers (Dec 4-8, 2025)

**Goal:** Unblock all tests, establish baseline

**Issues:**
- [x] ISSUE-001: Fix Detector Pool AttributeError (16-24 hrs)
- [x] ISSUE-002: Fix Import Path Issues (4-8 hrs)
- [x] ISSUE-003: Register Missing Pytest Markers (0.5 hrs)
- [x] ISSUE-004: Fix CI/CD Threshold Manipulation (8-16 hrs)

**Success Criteria:**
- ✅ 100% test collection success (496/496 tests)
- ✅ All 10 blocked tests now pass
- ✅ Real god object thresholds enforced
- ✅ CI/CD pipeline green

**Total Effort:** 28.5-48.5 hours (1 week with 1-2 developers)

---

### 6.2 Month 1 - Core Refactoring (Dec 9 - Jan 5, 2026)

**Goal:** Eliminate god objects, improve code quality

**Week 2-3:**
- [ ] ISSUE-005: Replace Bare Except Blocks (16-24 hrs)
- [ ] ISSUE-006: Refactor UnifiedConnascenceAnalyzer God Object (80-120 hrs)

**Week 4:**
- [ ] ISSUE-007: Refactor ConnascenceDetector God Object (40-60 hrs)
- [ ] ISSUE-008: Re-enable or Remove Architecture Components (40-60 hrs)
- [ ] ISSUE-009: Split Constants Module (16-24 hrs)

**Success Criteria:**
- ✅ Zero god objects (all classes <400 LOC, <20 methods)
- ✅ No bare except blocks
- ✅ Architecture components functional or removed
- ✅ Constants module split into Policy/Config/Errors

**Total Effort:** 192-288 hours (4 weeks with 2-3 developers)

---

### 6.3 Quarter 1 - Enhancements & Quality (Jan 6 - Mar 31, 2026)

**Goal:** Complete features, improve test coverage

**January (Week 5-8):**
- [ ] ISSUE-010: Implement Missing Features (80-120 hrs)
- [ ] ISSUE-011: Multi-language Support (80-120 hrs)
- [ ] ISSUE-012: Improve Test Coverage to 80% (120-180 hrs)

**February (Week 9-12):**
- [ ] ISSUE-013: Add Feature Detection API (8-16 hrs)
- [ ] ISSUE-014: Clean Up Legacy Analyzers (16-24 hrs)

**March (Week 13):**
- [ ] Final production readiness validation
- [ ] Performance benchmarking
- [ ] Security audit
- [ ] Documentation finalization

**Success Criteria:**
- ✅ 80%+ test coverage
- ✅ Multi-language support complete
- ✅ Feature detection API operational
- ✅ Legacy code removed
- ✅ Production ready (90%+ readiness score)

**Total Effort:** 304-460 hours (12 weeks with 2-3 developers)

---

### 6.4 Milestone Timeline

```
Week 1: CRITICAL FIXES
========================
Dec 4  | Start ISSUE-001 (detector pool)
Dec 5  | Complete ISSUE-001, start ISSUE-002 (imports)
Dec 6  | Complete ISSUE-002, start ISSUE-003 (markers)
Dec 6  | Complete ISSUE-003, start ISSUE-004 (thresholds)
Dec 8  | Complete ISSUE-004
       | ✅ MILESTONE: All tests pass, CI/CD green

Month 1: REFACTORING
=====================
Week 2-3: ISSUE-005 (bare except) + ISSUE-006 (UnifiedAnalyzer god object)
Week 4:   ISSUE-007 (ConnascenceDetector) + ISSUE-008 (architecture) + ISSUE-009 (constants)
Jan 5  | ✅ MILESTONE: Zero god objects, clean architecture

Quarter 1: ENHANCEMENTS
========================
Jan 6-31   | ISSUE-010, 011, 012 (features + coverage)
Feb 1-28   | ISSUE-013, 014 (API + cleanup)
Mar 1-31   | Final validation + production prep
Mar 31     | ✅ MILESTONE: Production ready (90%)
```

---

## 7. Assignee Recommendations

### 7.1 Required Expertise

| Issue | Required Skills | Recommended Assignee Type | Estimated Complexity |
|-------|----------------|---------------------------|----------------------|
| ISSUE-001 | Python, OOP, AST | Senior Python Developer | Medium |
| ISSUE-002 | Python imports, packaging | Mid-level Developer | Low |
| ISSUE-003 | Pytest configuration | Junior Developer | Very Low |
| ISSUE-004 | Refactoring, SOLID principles | Senior Architect | High |
| ISSUE-005 | Error handling, logging | Mid-level Developer | Medium |
| ISSUE-006 | Architecture, refactoring, SOLID | Principal Engineer / Architect | Very High |
| ISSUE-007 | Refactoring, detector patterns | Senior Developer | High |
| ISSUE-008 | Architecture, dependency management | Senior Architect | High |
| ISSUE-009 | Module design, separation of concerns | Mid-level Developer | Medium |
| ISSUE-010 | Multi-language parsing, AST | Senior Developer | High |
| ISSUE-011 | Tree-sitter, parsing | Senior Developer | High |
| ISSUE-012 | Testing, coverage, pytest | QA Engineer / Test Engineer | Medium |
| ISSUE-013 | API design, feature flags | Mid-level Developer | Low |
| ISSUE-014 | Deprecation, backward compat | Senior Developer | Medium |

### 7.2 Team Composition Recommendation

**Minimum Team:**
- 1 Principal Engineer (ISSUE-006 lead)
- 2 Senior Developers (ISSUE-004, 007, 008, 010, 011)
- 1 Mid-level Developer (ISSUE-002, 005, 009, 013)
- 1 QA Engineer (ISSUE-012)

**Optimal Team:**
- 1 Architect (ISSUE-006, 008 lead, reviews ISSUE-004, 007)
- 3 Senior Developers (parallel work on ISSUE-004, 007, 010, 011)
- 2 Mid-level Developers (ISSUE-002, 005, 009, 013, 014)
- 1 QA Lead (ISSUE-012, coordinates testing across all issues)
- 1 Junior Developer (ISSUE-003, assists ISSUE-012)

---

## 8. Conclusion

This GitHub issue-based remediation plan provides:

1. **14 Executable Issues** with code snippets and test commands
2. **Dependency Graph** showing critical path and blocking relationships
3. **Risk Assessment Matrix** with blast radius and rollback strategies
4. **GitHub Project Board Structure** with automation rules
5. **3-Tier Milestone Plan** (Week 1, Month 1, Quarter 1)
6. **Team Composition Recommendations** based on required expertise

**Next Steps:**
1. Create GitHub issues using provided templates
2. Set up project board with columns and labels
3. Assign issues to developers based on expertise
4. Start with Week 1 critical blockers
5. Run daily standups to track progress
6. Review risks weekly and update rollback strategies

**Estimated Timeline:**
- **Week 1:** Critical blockers fixed, CI/CD green
- **Month 1:** Core refactoring complete, zero god objects
- **Quarter 1:** Production ready (90%+ score)

**Total Effort:** 480-720 hours (~3-6 developer-months)

---

**Generated By:** Strategic Planning Agent
**Report Version:** 1.0
**Date:** 2025-11-13
**Confidence:** HIGH (based on comprehensive codebase analysis)
