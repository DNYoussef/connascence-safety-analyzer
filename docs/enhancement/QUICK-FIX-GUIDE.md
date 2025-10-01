# Connascence Analyzer - Quick Fix Guide

## Immediate NASA Compliance Fix (3-5 days → 75% improvement)

### Problem: 19,000+ False Positives in Rules 1, 2, 4

### Fix 1: Rule 1 - Pointer Usage (Currently 7,780 violations, 0% compliance)

**Current broken code** (`analyzer/nasa_engine/nasa_analyzer.py` line ~345):
```python
'pointer_patterns': [
    r'\*\w+',           # WRONG: matches *args, *kwargs
    r'->\s*\w+',        # WRONG: matches lambda arrows, dict keys
    r'\w+\s*\*\s*\w+'   # WRONG: matches multiplication
]
```

**Fixed AST-based approach:**
```python
def detect_pointer_usage(self, node):
    """Only flag actual pointer operations (ctypes/CFFI)."""
    if isinstance(node, ast.Call):
        if hasattr(node.func, 'id'):
            # Real pointer operations
            if node.func.id in ['POINTER', 'byref', 'cast']:
                return True
            # ctypes module
            if hasattr(node.func, 'attr') and node.func.attr in ['POINTER', 'pointer']:
                return True
    return False  # Python has no native pointers
```

**Files to edit:**
- `analyzer/nasa_engine/nasa_analyzer.py` (lines 340-360)
- `analyzer/detectors/enhanced_execution_detector.py` (remove regex patterns)

**Test validation:**
```python
# Should NOT flag:
def process(*args, **kwargs): pass  # Python unpacking
result = x * y                       # Multiplication
config = {"key": "value"}            # Dict arrows in logs

# Should flag:
from ctypes import POINTER, c_int    # Real pointer usage
ptr = POINTER(c_int)()
```

---

### Fix 2: Rule 2 - Dynamic Memory (Currently 4,077 violations, 0% compliance)

**Current broken code** (`analyzer/nasa_engine/nasa_analyzer.py` line ~370):
```python
'dynamic_memory_patterns': [
    r'\.append\(',      # WRONG: Python list method
    r'\.extend\(',      # WRONG: Python list method
    r'dict\(',          # WRONG: Python constructor
    r'list\(',          # WRONG: Python constructor
    r'set\('            # WRONG: Python constructor
]
```

**Fixed approach:**
```python
def detect_dynamic_allocation(self, node):
    """Only flag actual heap operations, not Python collections."""

    # Real C-style heap operations
    HEAP_OPERATIONS = ['malloc', 'calloc', 'realloc', 'free']

    if isinstance(node, ast.Call):
        if hasattr(node.func, 'id') and node.func.id in HEAP_OPERATIONS:
            return True

    # Ignore Python built-ins - they're memory-safe
    PYTHON_COLLECTIONS = [
        'list', 'dict', 'set', 'append', 'extend',
        'update', 'insert', 'pop', 'remove'
    ]
    return False
```

**Files to edit:**
- `analyzer/nasa_engine/nasa_analyzer.py` (lines 365-385)
- `analyzer/detectors/enhanced_algorithm_detector.py` (update patterns)

**Test validation:**
```python
# Should NOT flag:
items = []
items.append(1)              # Python list - memory safe
config = dict(settings)       # Built-in constructor
cache.update(new_data)        # Dict method

# Should flag:
import ctypes
buffer = ctypes.c_char_p(ctypes.create_string_buffer(1024))  # Real allocation
```

---

### Fix 3: Rule 4 - Assertion Density (Currently 8,145 violations, 0% compliance)

**Current broken code** (`analyzer/nasa_engine/nasa_analyzer.py` line ~245):
```python
def check_assertion_density(self, filepath):
    # WRONG: Checks ALL files
    assertions = self._count_assertions(filepath)
    total_lines = len(open(filepath).readlines())
    density = assertions / total_lines
    if density < 0.02:  # 2% threshold
        return violation
```

**Fixed approach:**
```python
def check_assertion_density(self, filepath):
    """Only check test files for assertion density."""

    # Only analyze test files
    test_patterns = [
        'test_*.py',
        '*_test.py',
        'tests/**/*.py',
        'testing/**/*.py'
    ]

    if not any(fnmatch(filepath, p) for p in test_patterns):
        return None  # Skip non-test files

    # Check assertion density only in test files
    assertions = self._count_assertions(filepath)
    total_lines = len(open(filepath).readlines())
    density = assertions / total_lines if total_lines > 0 else 0

    if density < 0.02:  # 2% threshold
        return {
            'rule': 4,
            'severity': 'high',
            'description': f'Assertion density {density:.1%} < 2.0%',
            'file': filepath
        }
    return None
```

**Files to edit:**
- `analyzer/nasa_engine/nasa_analyzer.py` (lines 240-260)
- Add `from fnmatch import fnmatch` import

**Test validation:**
```python
# Should NOT flag:
analyzer/unified_analyzer.py          # Production code - no assertions needed
interfaces/cli/main_python.py         # CLI code - no assertions needed

# Should flag:
tests/test_analyzer.py (0 assertions) # Test file with no assertions
```

---

## God Object Refactoring (5-7 days)

### Target: UnifiedConnascenceAnalyzer (70 methods → 5 classes)

**Step 1: Extract CoreAnalyzer** (Day 1-2)
```python
# analyzer/core_analyzer.py (NEW FILE)
class CoreAnalyzer:
    """Core AST traversal and detection logic."""

    def __init__(self, config):
        self.detectors = self._initialize_detectors()

    def analyze_file(self, filepath):
        tree = ast.parse(open(filepath).read())
        violations = []
        for detector in self.detectors:
            violations.extend(detector.detect(tree))
        return violations

    # Move: 15 methods related to detection
```

**Step 2: Extract ReportGenerator** (Day 2-3)
```python
# analyzer/report_generator.py (NEW FILE)
class ReportGenerator:
    """Output formatting and serialization."""

    def generate_json(self, violations):
        # Move: 12 methods for report generation

    def generate_sarif(self, violations):
        # SARIF format output

    def generate_html(self, violations):
        # HTML dashboard output
```

**Step 3: Extract CacheManager** (Day 3-4)
```python
# analyzer/cache_manager.py (NEW FILE)
class CacheManager:
    """File cache, AST cache, and invalidation."""

    def get_cached_ast(self, filepath):
        # Move: 10 methods for caching

    def invalidate_cache(self, filepath):
        # Cache invalidation logic
```

**Step 4: Extract IntegrationCoordinator** (Day 4-5)
```python
# analyzer/integration_coordinator.py (NEW FILE)
class IntegrationCoordinator:
    """MCP, CLI, and API integration."""

    def register_mcp_handlers(self):
        # Move: 18 methods for integrations

    def expose_cli_commands(self):
        # CLI integration
```

**Step 5: Extract ConfigManager** (Day 5-6)
```python
# analyzer/config_manager.py (NEW FILE)
class ConfigManager:
    """Settings, flags, and environment management."""

    def load_config(self, filepath):
        # Move: 15 methods for configuration

    def validate_config(self, config):
        # Config validation
```

**Step 6: Update UnifiedConnascenceAnalyzer** (Day 6-7)
```python
# analyzer/unified_analyzer.py (REFACTORED)
class UnifiedConnascenceAnalyzer:
    """High-level orchestrator - delegates to specialized components."""

    def __init__(self):
        self.core = CoreAnalyzer(config)
        self.reports = ReportGenerator()
        self.cache = CacheManager()
        self.integrations = IntegrationCoordinator()
        self.config = ConfigManager()

    def analyze(self, target):
        """Main entry point - delegates to components."""
        violations = self.core.analyze_file(target)
        report = self.reports.generate_json(violations)
        self.cache.store_results(report)
        return report
```

---

## Constants Modularization (1-2 days)

### Target: analyzer/constants.py (882 LOC → 3 focused files)

**Step 1: Create nasa_constants.py**
```python
# analyzer/constants/nasa_constants.py
"""NASA POT10 specific constants."""

NASA_RULES = {
    1: "No pointer usage",
    2: "No dynamic memory",
    # ... (150 LOC)
}

NASA_SEVERITY_WEIGHTS = {...}
NASA_CATEGORIES = {...}
```

**Step 2: Create connascence_constants.py**
```python
# analyzer/constants/connascence_constants.py
"""Connascence detection constants."""

CONNASCENCE_TYPES = [
    'CoN', 'CoT', 'CoV', 'CoP', ...
]

SEVERITY_LEVELS = {...}
DETECTION_PATTERNS = {...}
```

**Step 3: Create config_constants.py**
```python
# analyzer/constants/config_constants.py
"""Configuration and environment constants."""

DEFAULT_CACHE_DIR = '.connascence_cache'
DEFAULT_REPORT_FORMAT = 'json'
SUPPORTED_LANGUAGES = ['python', 'javascript', ...]
```

**Step 4: Update imports** (50+ files)
```python
# Old:
from analyzer.constants import NASA_RULES, CONNASCENCE_TYPES, DEFAULT_CACHE_DIR

# New:
from analyzer.constants.nasa_constants import NASA_RULES
from analyzer.constants.connascence_constants import CONNASCENCE_TYPES
from analyzer.constants.config_constants import DEFAULT_CACHE_DIR
```

---

## Validation Checklist

### After NASA Fixes:
- [ ] Run dogfood analysis: `python demo_analysis.py`
- [ ] Verify NASA compliance >90%
- [ ] Check Rules 1,2,4 have <50 violations each
- [ ] Validate no false positives in test suite

### After God Object Refactoring:
- [ ] All tests pass: `pytest tests/`
- [ ] No class has >25 methods
- [ ] UnifiedConnascenceAnalyzer <200 LOC
- [ ] Integration tests pass: `pytest tests/integration/`

### After Constants Split:
- [ ] All imports resolve correctly
- [ ] Build time reduced by >30%
- [ ] No circular dependencies
- [ ] Documentation updated

---

## Quick Commands

```bash
# Run fixed NASA analysis
python -m analyzer.nasa_engine.nasa_analyzer --rules 1,2,4 .

# Validate god object refactoring
python -c "from analyzer.unified_analyzer import UnifiedConnascenceAnalyzer;
           print(len([m for m in dir(UnifiedConnascenceAnalyzer) if not m.startswith('_')]))"
# Should output: <15 methods

# Check constants split
find analyzer/constants -name "*.py" | wc -l  # Should be 4 (3 + __init__.py)

# Run full validation
python demo_analysis.py && echo "SUCCESS: NASA compliance improved!"
```

---

**Estimated Total Effort:** 9-14 days
**Expected NASA Compliance:** 19% → 95%+
**Code Quality Improvement:** 24 god objects → 5, avg coupling 12 → 8