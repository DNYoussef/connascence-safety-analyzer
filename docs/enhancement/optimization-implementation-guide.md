# Performance Optimization Implementation Guide
**Target:** Connascence Analyzer - Phase 1 Quick Wins
**Estimated Effort:** 12 hours | **Impact:** 60-80% improvement

---

## Overview

This guide provides **step-by-step implementation** for the Phase 1 optimizations that will reduce import time from 2.8s to 0.56s and fix detector interface inconsistencies.

---

## Optimization 1: Lazy Detector Loading

### Current Problem
```python
# analyzer/__init__.py (SLOW - loads everything at import)
from .detectors import (
    PositionDetector,         # ← Loaded even if not used
    MagicLiteralDetector,     # ← Loaded even if not used
    AlgorithmDetector,        # ← Loaded even if not used
    GodObjectDetector,        # ← Loaded even if not used
    TimingDetector,           # ← Loaded even if not used
    ConventionDetector,       # ← Loaded even if not used
    ValuesDetector,           # ← Loaded even if not used
    ExecutionDetector         # ← Loaded even if not used
)

# Result: 2.8s import time, 24MB memory
```

### Solution: Dynamic Import Registry

#### Step 1: Create Detector Registry
**File:** `analyzer/detectors/registry.py`

```python
"""
Lazy-loading detector registry for performance optimization.
Reduces import time from 2.8s to <0.5s by deferring detector loads.
"""

import importlib
from typing import Dict, Type, Any
from pathlib import Path


class DetectorRegistry:
    """Lazy-loading registry for connascence detectors."""

    # Map detector names to module paths (no imports!)
    _DETECTOR_MAP = {
        'position': ('analyzer.detectors.position_detector', 'PositionDetector'),
        'magic_literal': ('analyzer.detectors.magic_literal_detector', 'MagicLiteralDetector'),
        'algorithm': ('analyzer.detectors.algorithm_detector', 'AlgorithmDetector'),
        'god_object': ('analyzer.detectors.god_object_detector', 'GodObjectDetector'),
        'timing': ('analyzer.detectors.timing_detector', 'TimingDetector'),
        'convention': ('analyzer.detectors.convention_detector', 'ConventionDetector'),
        'values': ('analyzer.detectors.values_detector', 'ValuesDetector'),
        'execution': ('analyzer.detectors.execution_detector', 'ExecutionDetector'),
    }

    _cache: Dict[str, Type] = {}  # Cache loaded detectors

    @classmethod
    def get_detector(cls, name: str) -> Type:
        """
        Get detector class by name, loading only when needed.

        Args:
            name: Detector name (e.g., 'position', 'magic_literal')

        Returns:
            Detector class (not instance)

        Raises:
            ValueError: If detector name not found
        """
        if name not in cls._DETECTOR_MAP:
            available = ', '.join(cls._DETECTOR_MAP.keys())
            raise ValueError(f"Unknown detector: {name}. Available: {available}")

        # Return cached if available
        if name in cls._cache:
            return cls._cache[name]

        # Lazy load detector
        module_path, class_name = cls._DETECTOR_MAP[name]
        module = importlib.import_module(module_path)
        detector_class = getattr(module, class_name)

        # Cache for future use
        cls._cache[name] = detector_class

        return detector_class

    @classmethod
    def get_all_detectors(cls) -> Dict[str, Type]:
        """Load all detectors (for batch operations)."""
        return {
            name: cls.get_detector(name)
            for name in cls._DETECTOR_MAP.keys()
        }

    @classmethod
    def list_available(cls) -> list:
        """List available detector names without loading."""
        return list(cls._DETECTOR_MAP.keys())

    @classmethod
    def clear_cache(cls):
        """Clear detector cache (useful for testing)."""
        cls._cache.clear()


# Convenience functions
def get_detector(name: str) -> Type:
    """Get detector class by name."""
    return DetectorRegistry.get_detector(name)


def list_detectors() -> list:
    """List available detector names."""
    return DetectorRegistry.list_available()
```

#### Step 2: Update Main Analyzer
**File:** `analyzer/consolidated_analyzer.py`

```python
# BEFORE (Eager Import)
from .detectors import (
    PositionDetector,
    MagicLiteralDetector,
    AlgorithmDetector,
    GodObjectDetector,
    TimingDetector
)

# AFTER (Lazy Import)
from .detectors.registry import DetectorRegistry

class ConsolidatedConnascenceAnalyzer:
    def __init__(self, project_path: str = ".", policy_preset: str = "strict"):
        self.project_path = Path(project_path)
        self.policy_preset = policy_preset
        self._detector_registry = DetectorRegistry
        # No detector instances created yet!

    def _initialize_detectors(self) -> List:
        """Initialize detectors only when analysis starts."""
        detectors = []

        # Load only needed detectors based on config
        detector_names = self._get_enabled_detectors()

        for name in detector_names:
            # Lazy load: only imports when this line runs
            detector_class = self._detector_registry.get_detector(name)
            detectors.append((name, detector_class))

        return detectors

    def _get_enabled_detectors(self) -> List[str]:
        """Determine which detectors to load based on policy."""
        if self.policy_preset == "strict":
            return ['position', 'magic_literal', 'algorithm', 'god_object', 'timing']
        elif self.policy_preset == "minimal":
            return ['position', 'god_object']
        else:
            return self._detector_registry.list_available()
```

#### Step 3: Update Package Exports
**File:** `analyzer/__init__.py`

```python
# BEFORE (imports everything immediately)
from .consolidated_analyzer import ConsolidatedConnascenceAnalyzer
from .detectors import (
    PositionDetector,
    MagicLiteralDetector,
    # ... etc
)

# AFTER (lazy imports)
from .consolidated_analyzer import ConsolidatedConnascenceAnalyzer
from .detectors.registry import DetectorRegistry, get_detector, list_detectors

__all__ = [
    'ConsolidatedConnascenceAnalyzer',
    'DetectorRegistry',
    'get_detector',
    'list_detectors'
]

# Optional: Provide lazy attribute access
def __getattr__(name):
    """Lazy load detectors on attribute access."""
    detector_map = {
        'PositionDetector': 'position',
        'MagicLiteralDetector': 'magic_literal',
        'AlgorithmDetector': 'algorithm',
        'GodObjectDetector': 'god_object',
        'TimingDetector': 'timing',
    }

    if name in detector_map:
        return get_detector(detector_map[name])

    raise AttributeError(f"module 'analyzer' has no attribute '{name}'")
```

#### Expected Results:
- **Import time:** 2.8s → **0.5-0.8s** (64-82% reduction)
- **Initial memory:** 24MB → **6-8MB** (67-75% reduction)
- **Detector load:** On-demand only

---

## Optimization 2: Configuration Lazy Loading

### Current Problem
```python
# analyzer/detectors/base.py
class DetectorBase:
    def __init__(self):
        # Loads ALL configs at initialization
        self.config = ConfigManager.load_all_configs()  # ← SLOW
```

### Solution: Deferred Configuration

#### Implementation
**File:** `analyzer/config/lazy_config.py`

```python
"""Lazy configuration loading for performance."""

from functools import lru_cache
from pathlib import Path
import yaml
from typing import Dict, Any


class LazyConfigManager:
    """Configuration manager with lazy loading and caching."""

    _config_dir = Path(__file__).parent.parent / "config"
    _cache: Dict[str, Dict[str, Any]] = {}

    @classmethod
    @lru_cache(maxsize=32)
    def get_config(cls, detector_name: str) -> Dict[str, Any]:
        """
        Load configuration for specific detector, cached.

        Args:
            detector_name: Name of detector (e.g., 'position_detector')

        Returns:
            Configuration dictionary
        """
        if detector_name in cls._cache:
            return cls._cache[detector_name]

        config_file = cls._config_dir / f"{detector_name}.yaml"

        if not config_file.exists():
            # Return default config
            return cls._get_default_config(detector_name)

        with open(config_file) as f:
            config = yaml.safe_load(f)

        cls._cache[detector_name] = config
        return config

    @classmethod
    def _get_default_config(cls, detector_name: str) -> Dict[str, Any]:
        """Return default configuration for detector."""
        defaults = {
            'position_detector': {
                'thresholds': {'max_positional_params': 3},
                'severity_mapping': {'4-6': 'medium', '7-10': 'high', '11+': 'critical'}
            },
            'magic_literal_detector': {
                'thresholds': {'number_repetition': 3, 'string_repetition': 2},
                'exclusions': {
                    'common_numbers': [0, 1, -1, 2, 10, 100],
                    'common_strings': ['', ' ', '\\n', '\\t', 'utf-8']
                }
            },
            # ... other defaults
        }
        return defaults.get(detector_name, {})

    @classmethod
    def clear_cache(cls):
        """Clear configuration cache."""
        cls._cache.clear()
        cls.get_config.cache_clear()
```

#### Update Detectors
**File:** `analyzer/detectors/base.py`

```python
from analyzer.config.lazy_config import LazyConfigManager

class DetectorBase:
    def __init__(self, file_path: str, source_lines: List[str]):
        self.file_path = file_path
        self.source_lines = source_lines
        self._config = None  # Lazy-loaded

    @property
    def config(self) -> Dict[str, Any]:
        """Lazy-load configuration on first access."""
        if self._config is None:
            detector_name = self.__class__.__name__.lower().replace('detector', '_detector')
            self._config = LazyConfigManager.get_config(detector_name)
        return self._config
```

---

## Optimization 3: Standardize Detector Interfaces

### Current Problem
```python
# Inconsistent signatures across detectors
class PositionDetector:
    def __init__(self, file_path: str, source_lines: List[str]):  # ← Args in init
        pass
    def detect(self) -> List[Violation]:  # ← No args
        pass

class TimingDetector:
    def __init__(self):  # ← No args
        pass
    # Missing detect() method entirely!
```

### Solution: Unified Base Class

#### Implementation
**File:** `analyzer/detectors/base.py`

```python
"""Unified detector base class with standard interface."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import ast
from dataclasses import dataclass


@dataclass
class Violation:
    """Standardized violation structure."""
    type: str
    severity: str
    file_path: str
    line_number: int
    description: str
    column: int = 0
    connascence_type: str = None


class DetectorBase(ABC):
    """
    Base class for all connascence detectors.

    Enforces consistent interface:
    - All detectors implement detect(ast_tree, file_path)
    - Configuration is lazy-loaded
    - Results use standard Violation dataclass
    """

    def __init__(self):
        """Initialize detector with lazy configuration."""
        self._config = None

    @property
    def config(self) -> Dict[str, Any]:
        """Lazy-load configuration."""
        if self._config is None:
            from analyzer.config.lazy_config import LazyConfigManager
            detector_name = self.__class__.__name__.lower()
            self._config = LazyConfigManager.get_config(detector_name)
        return self._config

    @abstractmethod
    def detect(self, ast_tree: ast.AST, file_path: str) -> List[Violation]:
        """
        Detect violations in AST tree.

        Args:
            ast_tree: Parsed AST of source code
            file_path: Path to file being analyzed

        Returns:
            List of detected violations
        """
        pass

    def _create_violation(
        self,
        violation_type: str,
        severity: str,
        file_path: str,
        line_number: int,
        description: str,
        **kwargs
    ) -> Violation:
        """Helper to create standardized violations."""
        return Violation(
            type=violation_type,
            severity=severity,
            file_path=file_path,
            line_number=line_number,
            description=description,
            **kwargs
        )
```

#### Update Existing Detectors

**File:** `analyzer/detectors/position_detector.py`

```python
# BEFORE
class PositionDetector:
    def __init__(self, file_path: str, source_lines: List[str]):
        self.file_path = file_path
        self.source_lines = source_lines

    def detect(self) -> List[Dict]:  # Wrong signature
        # ... implementation
        pass

# AFTER
from .base import DetectorBase, Violation
import ast

class PositionDetector(DetectorBase):
    def detect(self, ast_tree: ast.AST, file_path: str) -> List[Violation]:
        """Detect positional parameter violations."""
        violations = []

        for node in ast.walk(ast_tree):
            if isinstance(node, ast.FunctionDef):
                num_params = len(node.args.args)
                max_allowed = self.config.get('thresholds', {}).get('max_positional_params', 3)

                if num_params > max_allowed:
                    violations.append(self._create_violation(
                        violation_type='connascence_of_position',
                        severity='high' if num_params > 6 else 'medium',
                        file_path=file_path,
                        line_number=node.lineno,
                        description=f"Function '{node.name}' has {num_params} positional params (max: {max_allowed})",
                        connascence_type='position'
                    ))

        return violations
```

**File:** `analyzer/detectors/god_object_detector.py`

```python
# BEFORE
class GodObjectDetector:
    def __init__(self):
        pass
    # Missing detect() method

# AFTER
from .base import DetectorBase, Violation
import ast

class GodObjectDetector(DetectorBase):
    def detect(self, ast_tree: ast.AST, file_path: str) -> List[Violation]:
        """Detect god object violations."""
        violations = []

        for node in ast.walk(ast_tree):
            if isinstance(node, ast.ClassDef):
                method_count = sum(1 for n in node.body if isinstance(n, ast.FunctionDef))
                max_methods = self.config.get('thresholds', {}).get('max_methods', 20)

                if method_count > max_methods:
                    violations.append(self._create_violation(
                        violation_type='god_object',
                        severity='critical' if method_count > 50 else 'high',
                        file_path=file_path,
                        line_number=node.lineno,
                        description=f"Class '{node.name}' has {method_count} methods (max: {max_methods})",
                        connascence_type='complexity'
                    ))

        return violations
```

---

## Implementation Checklist

### Phase 1: Lazy Loading (4 hours)

- [ ] **Step 1:** Create `analyzer/detectors/registry.py` (1 hour)
  - [ ] Implement DetectorRegistry class
  - [ ] Add lazy loading logic
  - [ ] Add caching mechanism
  - [ ] Write unit tests

- [ ] **Step 2:** Update `analyzer/consolidated_analyzer.py` (1 hour)
  - [ ] Replace eager imports with registry
  - [ ] Update _initialize_detectors()
  - [ ] Test with different policy presets

- [ ] **Step 3:** Update `analyzer/__init__.py` (0.5 hours)
  - [ ] Add __getattr__ for lazy imports
  - [ ] Update __all__ exports
  - [ ] Verify backward compatibility

- [ ] **Step 4:** Benchmark and Validate (1.5 hours)
  - [ ] Measure new import time (target: <0.8s)
  - [ ] Verify memory usage (target: <10MB)
  - [ ] Run full test suite
  - [ ] Update documentation

### Phase 2: Config Optimization (2 hours)

- [ ] **Step 1:** Create `analyzer/config/lazy_config.py` (0.5 hours)
  - [ ] Implement LazyConfigManager
  - [ ] Add LRU caching
  - [ ] Add default configs

- [ ] **Step 2:** Update detector base class (0.5 hours)
  - [ ] Add lazy config property
  - [ ] Update all detectors to use new config

- [ ] **Step 3:** Test and Benchmark (1 hour)
  - [ ] Verify config loading works
  - [ ] Measure performance improvement
  - [ ] Update tests

### Phase 3: Interface Standardization (6 hours)

- [ ] **Step 1:** Update base class (1 hour)
  - [ ] Create unified DetectorBase
  - [ ] Define standard detect() signature
  - [ ] Add Violation dataclass

- [ ] **Step 2:** Update all detectors (3 hours)
  - [ ] PositionDetector → new interface
  - [ ] MagicLiteralDetector → new interface
  - [ ] AlgorithmDetector → new interface
  - [ ] GodObjectDetector → add detect() method
  - [ ] TimingDetector → add detect() method
  - [ ] ConventionDetector → new interface
  - [ ] ValuesDetector → new interface
  - [ ] ExecutionDetector → new interface

- [ ] **Step 3:** Update analyzer integration (1 hour)
  - [ ] Update batch processing
  - [ ] Update result aggregation
  - [ ] Verify all code paths

- [ ] **Step 4:** Comprehensive Testing (1 hour)
  - [ ] Unit tests for each detector
  - [ ] Integration tests
  - [ ] Performance benchmarks
  - [ ] Update documentation

---

## Testing Strategy

### Unit Tests
```python
# tests/test_detector_registry.py
def test_lazy_loading():
    """Verify detectors load only when accessed."""
    # Clear any cached imports
    DetectorRegistry.clear_cache()

    # Registry creation should be instant
    start = time.time()
    registry = DetectorRegistry()
    assert time.time() - start < 0.01, "Registry init too slow"

    # First detector access loads it
    start = time.time()
    detector = registry.get_detector('position')
    load_time = time.time() - start
    assert load_time < 0.1, f"Detector load too slow: {load_time}s"

    # Second access uses cache
    start = time.time()
    detector2 = registry.get_detector('position')
    assert time.time() - start < 0.001, "Cache not working"
    assert detector is detector2, "Should return same instance"

def test_detector_interface():
    """Verify all detectors implement standard interface."""
    import ast

    for name in DetectorRegistry.list_available():
        detector_class = DetectorRegistry.get_detector(name)
        detector = detector_class()

        # Must have detect method
        assert hasattr(detector, 'detect'), f"{name} missing detect()"

        # Test with sample AST
        code = "def test(): pass"
        tree = ast.parse(code)

        violations = detector.detect(tree, "test.py")
        assert isinstance(violations, list), f"{name} must return list"

        if violations:
            v = violations[0]
            assert hasattr(v, 'type'), f"{name} violation missing type"
            assert hasattr(v, 'severity'), f"{name} violation missing severity"
```

### Performance Benchmarks
```python
# tests/benchmark_optimization.py
def benchmark_import_time():
    """Measure import performance improvement."""
    # Clear module cache
    for mod in list(sys.modules.keys()):
        if 'analyzer' in mod:
            del sys.modules[mod]

    start = time.time()
    import analyzer
    import_time = time.time() - start

    print(f"Import time: {import_time:.3f}s")
    assert import_time < 0.8, f"Import too slow: {import_time}s (target: <0.8s)"

    # Measure memory
    mem_usage = psutil.Process().memory_info().rss / 1024 / 1024
    print(f"Memory usage: {mem_usage:.1f}MB")
    assert mem_usage < 50, f"Memory too high: {mem_usage}MB (target: <50MB)"
```

---

## Rollout Plan

### Step 1: Development (8 hours)
1. Implement lazy loading (4h)
2. Implement config optimization (2h)
3. Standardize interfaces (2h)

### Step 2: Testing (3 hours)
1. Unit tests (1h)
2. Integration tests (1h)
3. Performance benchmarks (1h)

### Step 3: Deployment (1 hour)
1. Update documentation
2. Create migration guide
3. Merge to main branch
4. Tag release v2.0.0

---

## Success Metrics

### Performance Targets
- ✅ Import time: 2.8s → **<0.8s** (71% improvement)
- ✅ Memory usage: 24MB → **<10MB** (58% reduction)
- ✅ All detectors: Unified interface
- ✅ No regression: All tests pass

### Verification Commands
```bash
# Measure import time
python -c "import time; start=time.time(); import analyzer; print(f'Import: {time.time()-start:.3f}s')"

# Expected: <0.8s (was 2.8s)

# Verify all detectors work
python -m pytest tests/test_detector_*.py -v

# Expected: All pass

# Benchmark performance
python tests/benchmark_optimization.py

# Expected: All metrics green
```

---

## Next Steps

After Phase 1 completion, consider:

1. **Phase 2: Parallelization** (if workload >5000 files)
2. **Phase 3: AST Caching** (for IDE integration)
3. **Phase 4: Incremental Analysis** (for CI/CD optimization)

Current analysis shows **Phase 1 is sufficient** for production deployment at 95% NASA compliance with 1000+ file codebases.