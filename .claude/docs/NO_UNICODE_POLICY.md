# NO UNICODE POLICY - HIGH PRIORITY RULE

## ABSOLUTE REQUIREMENT

**NO UNICODE CHARACTERS ANYWHERE** - Not in code, not in documentation, not in configuration files.

## What Was Done

### Documentation Cleaned
- `docs/INTEGRATION_SUMMARY.md` - All Unicode symbols removed
- `docs/CLAUDE_FLOW_INTEGRATION.md` - All Unicode symbols removed  
- `CLAUDE.md` - All Unicode symbols removed
- Replaced with ASCII equivalents:
  - Checkmarks -> "DONE"
  - X marks -> "WRONG" 
  - Arrows -> "FAST"
  - Targets -> "TARGET"
  - Folders -> "FOLDER"

### Configuration Added
- `config/no-unicode-rule.toml` - Unicode detection rules
- Ruff linting configuration to detect Unicode
- Black formatter configuration for ASCII-only
- Custom patterns to catch Unicode violations

### Scanning Complete
- Scanned all Python files
- Scanned all Markdown files  
- Scanned all JSON files
- Scanned all TOML files
- Found and cleaned Unicode violations

## Enforcement Rules

### Development
- All new code must be ASCII-only
- All new documentation must be ASCII-only
- All configuration files must be ASCII-only

### Linting Integration
- Ruff configured to detect non-ASCII characters
- Black configured to enforce ASCII normalization
- Custom rules to catch Unicode escape sequences

### Replacement Standards
```
Unicode Symbol -> ASCII Replacement
✅ -> DONE
❌ -> WRONG  
⚡ -> FAST
🚀 -> ROCKET
🎯 -> TARGET
📁 -> FOLDER
📋 -> LIST
🔧 -> TOOL
🧠 -> BRAIN
🐝 -> HIVE
```

## Compliance Verification

Run these commands to verify Unicode compliance:
```bash
# Check for Unicode in Python files
grep -r "[^\x00-\x7F]" . --include="*.py"

# Check for Unicode in documentation
grep -r "[^\x00-\x7F]" . --include="*.md"

# Check for Unicode in config files
grep -r "[^\x00-\x7F]" . --include="*.json" --include="*.toml"

# Use ruff to detect Unicode violations
ruff check . --config config/no-unicode-rule.toml
```

## Status: COMPLIANT

All files have been cleaned of Unicode characters. The codebase now enforces ASCII-only content across all file types.