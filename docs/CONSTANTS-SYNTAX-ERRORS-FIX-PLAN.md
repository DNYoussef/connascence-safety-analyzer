# Constants Syntax Errors - Fix Plan

**Date**: 2025-11-15
**Priority**: HIGH (Blocks dogfooding cycle 2 completion)
**Estimated Time**: 2-3 hours

---

## Problem Summary

During Day 7 validation, discovered that **12 extracted constants files have Python syntax errors** that prevent the analyzer from parsing them.

### Error Messages

```
invalid decimal literal in 10 files:
- analyzer\literal_constants\check_connascence_constants.py (line 22)
- analyzer\literal_constants\context_analyzer_constants.py (line 33)
- analyzer\literal_constants\core_constants.py (line 22)
- analyzer\enterprise\constants\nasa_pot10_enhanced_constants.py (line 28)
- analyzer\enterprise\sixsigma\constants\analyzer_constants.py (line 26)
- analyzer\quality_gates\constants\unified_quality_gate_constants.py (line 18)
- analyzer\reporting\constants\coordinator_constants.py (line 15)
- analyzer\streaming\constants\dashboard_reporter_constants.py (line 33)
- analyzer\theater_detection\constants\detector_constants.py (line 26)
- analyzer\theater_detection\constants\validator_constants.py (line 24)

cannot assign to literal in 2 files:
- analyzer\literal_constants\constants_constants.py (line 94)
- analyzer\reporting\constants\sarif_constants.py (line 6)
```

### Root Cause

The `extract_magic_literals.py` script created invalid Python syntax when converting literals to constant names:

**Problem Type 1: Invalid Decimal Literals**
```python
# Generated (INVALID):
MAGIC_NUMBER_5.0 = 5.0  # Variable names cannot contain dots

# Should be:
MAGIC_NUMBER_5_0 = 5.0  # Replace dots with underscores
```

**Problem Type 2: Assignment to Reserved Keywords**
```python
# Generated (INVALID):
True = True   # Cannot assign to True/False/None

# Should be:
# Skip these during extraction
```

---

## Fix Strategy

### Phase 1: Identify Exact Errors (30 minutes)

**Tasks**:
1. Read each of the 12 affected files
2. Locate the specific lines with syntax errors
3. Categorize error types
4. Document patterns

**Commands**:
```bash
# Check syntax for each file
for file in \
  analyzer/literal_constants/check_connascence_constants.py \
  analyzer/literal_constants/context_analyzer_constants.py \
  analyzer/literal_constants/core_constants.py \
  analyzer/literal_constants/constants_constants.py \
  analyzer/enterprise/constants/nasa_pot10_enhanced_constants.py \
  analyzer/enterprise/sixsigma/constants/analyzer_constants.py \
  analyzer/quality_gates/constants/unified_quality_gate_constants.py \
  analyzer/reporting/constants/coordinator_constants.py \
  analyzer/reporting/constants/sarif_constants.py \
  analyzer/streaming/constants/dashboard_reporter_constants.py \
  analyzer/theater_detection/constants/detector_constants.py \
  analyzer/theater_detection/constants/validator_constants.py
do
  echo "Checking: $file"
  python -m py_compile "$file" 2>&1 || true
  echo "---"
done
```

### Phase 2: Create Fix Script (45 minutes)

**Script**: `/scripts/fix_constants_syntax.py`

**Features**:
1. Read constants file
2. Parse with AST to find exact syntax errors
3. Apply fixes:
   - Replace dots in variable names with underscores
   - Skip reserved keywords (True, False, None)
   - Validate numeric literal formats
4. Write fixed version
5. Validate with `py_compile`
6. Backup original with `.backup` suffix

**Pseudocode**:
```python
def fix_constants_file(filepath):
    # Read original
    content = read_file(filepath)

    # Backup
    backup_file(filepath)

    # Parse and fix
    fixed_lines = []
    for line in content.split('\n'):
        if '=' in line and line.strip().startswith(('MAGIC', 'TRUE', 'FALSE', 'NONE')):
            const_name, const_value = line.split('=', 1)
            const_name = const_name.strip()

            # Fix dots in name
            if '.' in const_name:
                const_name = const_name.replace('.', '_')

            # Skip reserved keywords
            if const_name in ['TRUE', 'FALSE', 'NONE', 'True', 'False', 'None']:
                continue  # Skip this line

            # Reconstruct line
            fixed_line = f"{const_name} = {const_value}"
            fixed_lines.append(fixed_line)
        else:
            fixed_lines.append(line)

    # Write fixed version
    write_file(filepath, '\n'.join(fixed_lines))

    # Validate
    try:
        py_compile.compile(filepath)
        print(f"[OK] {filepath} fixed and validated")
    except SyntaxError as e:
        # Restore backup if validation fails
        restore_backup(filepath)
        print(f"[FAIL] {filepath} still has errors: {e}")
```

### Phase 3: Manual Review (30 minutes)

**For each fixed file**:
1. Review changes (diff against backup)
2. Verify constant names make sense
3. Check no functionality lost
4. Test imports work

**Commands**:
```bash
# Review changes
git diff --no-index file.py.backup file.py

# Test import
python -c "from analyzer.literal_constants.check_connascence_constants import *; print('OK')"
```

### Phase 4: Validation & Testing (30 minutes)

**Full Validation**:
```bash
# 1. Check all constants files parse
find analyzer/ -name "*constants.py" -exec python -m py_compile {} \;

# 2. Run test suite
python -m pytest -xvs

# 3. Run analyzer on itself
python -m analyzer --path analyzer/ --format json > docs/dogfooding/cycle2-clean.json 2>&1

# 4. Check for parsing warnings
grep "Warning.*parse" docs/dogfooding/cycle2-clean.json
```

**Success Criteria**:
- All 12 files compile without errors
- Test suite still passes (98.4%+ rate)
- No parsing warnings when running analyzer
- cycle2-clean.json generated successfully

---

## Alternative: Manual Fix (If Script Fails)

### For "invalid decimal literal" errors:

**Example**: `analyzer/literal_constants/core_constants.py:22`

**Steps**:
1. Open file in editor
2. Find line 22
3. Look for variable names containing dots: `MAGIC_NUMBER_5.0`
4. Replace with underscores: `MAGIC_NUMBER_5_0`
5. Save and test: `python -m py_compile core_constants.py`

### For "cannot assign to literal" errors:

**Example**: `analyzer/literal_constants/constants_constants.py:94`

**Steps**:
1. Open file in editor
2. Find line 94
3. Look for: `True = True` or `False = False` or `None = None`
4. Delete these lines (they're reserved keywords)
5. Save and test: `python -m py_compile constants_constants.py`

---

## Post-Fix Actions

### 1. Update extract_magic_literals.py

Add validation during extraction to prevent future syntax errors:

```python
def is_valid_python_identifier(name):
    """Check if name is a valid Python identifier."""
    import keyword

    # Check for dots
    if '.' in name:
        return False

    # Check reserved keywords
    if keyword.iskeyword(name) or name in ['True', 'False', 'None']:
        return False

    # Check starts with letter or underscore
    if not (name[0].isalpha() or name[0] == '_'):
        return False

    # Check contains only alphanumeric and underscores
    if not all(c.isalnum() or c == '_' for c in name):
        return False

    return True

# In generate_constant_name():
const_name = generate_candidate_name(value)
if not is_valid_python_identifier(const_name):
    const_name = sanitize_identifier(const_name)  # Fix dots, etc.
```

### 2. Add py_compile Check to Extraction Script

```python
# After writing constants file:
import py_compile
try:
    py_compile.compile(output_file)
    print(f"[OK] {output_file} syntax validated")
except SyntaxError as e:
    print(f"[FAIL] {output_file} has syntax error: {e}")
    # Don't continue - fix extraction logic
```

### 3. Rerun Extraction on Affected Files

After fixing the extraction script, re-extract constants from the 12 affected files to ensure clean output:

```bash
python scripts/extract_magic_literals.py --file analyzer/check_connascence.py --output analyzer/literal_constants/ --apply
# etc. for all affected files
```

---

## Success Metrics

**Before Fix**:
- 12 constants files fail `py_compile`
- Analyzer shows 12+ parsing warnings
- Dogfooding cycle 2 runs in degraded mode

**After Fix**:
- 0 constants files fail `py_compile` ✅
- Analyzer shows 0 parsing warnings ✅
- Dogfooding cycle 2 completes successfully ✅
- Metrics comparison shows actual improvement ✅

---

## Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| Phase 1: Identify | 30 min | Read 12 files, categorize errors |
| Phase 2: Script | 45 min | Create fix_constants_syntax.py |
| Phase 3: Review | 30 min | Manual review of fixes |
| Phase 4: Validate | 30 min | Test suite, analyzer run |
| **TOTAL** | **2h 15min** | **Complete fix** |

**Buffer**: +45 minutes for unexpected issues = **3 hours total**

---

## Risk Assessment

**Risks**:
1. **Fix script introduces new errors**: Use backups, validate with py_compile
2. **Semantic meaning lost**: Manual review catches this
3. **Imports break**: Test imports after each fix
4. **Test suite fails**: Run tests after all fixes

**Mitigation**:
- Git commit before starting
- Backup each file before fixing
- Incremental validation (one file at a time)
- Rollback plan (restore from backup or Git)

---

## Next Steps After Fix

1. **Complete Dogfooding Cycle 2** (30 min):
   - Run analyzer on itself
   - Generate clean JSON output
   - Compare metrics with cycle 1

2. **Update Documentation** (15 min):
   - Add fix summary to Day 7 report
   - Document lessons learned
   - Update extract_magic_literals.py docs

3. **Proceed with Import Automation** (4-6 hours):
   - Install asttokens
   - Enhance apply_constants_v2.py
   - Test incremental imports

---

**Status**: Ready to execute
**Priority**: HIGH - Blocks Week 6 completion
**Owner**: To be assigned
**Estimated Completion**: +3 hours from start
