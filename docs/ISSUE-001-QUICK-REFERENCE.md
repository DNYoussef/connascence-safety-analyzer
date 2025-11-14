# ISSUE-001 Quick Reference

## Problem
AttributeError: Detectors missing `should_analyze_file()` method in detector_pool.py

## Solution
1. Added `should_analyze_file()` method to `DetectorBase`
2. Added `SUPPORTED_EXTENSIONS` to all 8 detector classes

## File Extension Support

| Detector | Extensions |
|----------|------------|
| Algorithm | .py, .js, .ts |
| GodObject | .py, .js, .ts |
| MagicLiteral | .py, .js, .ts, .java |
| Convention | .py |
| Position | .py, .js, .ts |
| Execution | .py |
| Values | .py |
| Timing | .py |

## Usage Example

```python
from analyzer.architecture.detector_pool import DetectorPool

pool = DetectorPool()
detector = pool.acquire_detector('algorithm', 'test.py', ['# code'])

# Check if detector should analyze file
if detector.should_analyze_file('myfile.js'):
    violations = detector.detect_violations(tree)

pool.release_detector(detector)
```

## Verification Command

```bash
cd C:\Users\17175\Desktop\connascence
python -c "
from analyzer.architecture.detector_pool import DetectorPool
pool = DetectorPool()
detector = pool.acquire_detector('algorithm', 'test.py', [])
print('Has method:', hasattr(detector, 'should_analyze_file'))
print('Can analyze .py:', detector.should_analyze_file('test.py'))
pool.release_detector(detector)
"
```

## Status
**RESOLVED** - All tests passing, ready for production use.
