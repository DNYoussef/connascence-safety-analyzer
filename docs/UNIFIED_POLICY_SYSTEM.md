# Unified Policy Standardization System

## Overview

The Unified Policy Standardization System addresses critical policy naming inconsistency across all Connascence Safety Analyzer integrations. This system provides full backwards compatibility while establishing standard names for consistent behavior.

## Problem Statement

**Previous State**: Same functionality had different names across integrations:
- **CLI**: `nasa_jpl_pot10`, `strict-core`, `default`, `lenient`
- **VSCode**: `safety_level_1`, `general_safety_strict`, `modern_general`
- **MCP**: `nasa-compliance`, `service-defaults`, `experimental`

## Solution: Unified Standard Names

### Standard Policy Names (Recommended)

| Unified Name | Description | Use Case |
|-------------|------------|----------|
| `nasa-compliance` | NASA JPL Power of Ten compliance (highest safety) | Mission-critical systems |
| `strict` | Strict code quality standards | Production systems |
| `standard` | Balanced service defaults (recommended) | General development |
| `lenient` | Relaxed experimental settings | Prototyping, legacy code |

### Policy Mapping

#### CLI Legacy → Unified
- `nasa_jpl_pot10` → `nasa-compliance`
- `strict-core` → `strict`  
- `default` → `standard`
- `service-defaults` → `standard`
- `experimental` → `lenient`

#### VSCode Legacy → Unified
- `safety_level_1` → `nasa-compliance`
- `general_safety_strict` → `strict`
- `modern_general` → `standard`
- `safety_level_3` → `lenient`

#### MCP Legacy → Unified
- `nasa-compliance` → `nasa-compliance` (already correct)
- `service-defaults` → `standard`
- `experimental` → `lenient`

## Implementation Features

### 1. Full Backwards Compatibility
- All legacy policy names continue to work
- No breaking changes to existing configurations
- Automatic resolution to unified names

### 2. Deprecation Warnings
- Legacy names emit deprecation warnings with recommendations
- Clear guidance to migrate to unified names
- Configurable warning levels

### 3. Cross-Integration Consistency
- Same policy behavior across CLI, VSCode, and MCP
- Unified configuration management
- Consistent validation rules

## Usage Examples

### CLI Usage
```bash
# New unified names (recommended)
connascence scan . --policy nasa-compliance
connascence scan . --policy strict
connascence scan . --policy standard
connascence scan . --policy lenient

# Legacy names (deprecated but supported)
connascence scan . --policy nasa_jpl_pot10  # Warns: Use 'nasa-compliance'
connascence scan . --policy strict-core     # Warns: Use 'strict'

# List all policies
connascence --list-policies
```

### MCP Server
```python
# Validate policies
await server.validate_policy({'policy_preset': 'nasa-compliance'})
await server.validate_policy({'policy_preset': 'nasa_jpl_pot10'})  # Legacy, warns

# List presets with unified/legacy separation
presets = await server.list_presets({})
print(presets['unified_presets'])  # Recommended
print(presets['legacy_presets'])   # Deprecated
```

### Policy Manager
```python
from policy.manager import PolicyManager

manager = PolicyManager()

# Get unified presets
policy = manager.get_preset('nasa-compliance')
policy = manager.get_preset('nasa_jpl_pot10')  # Resolves to nasa-compliance

# List policies
unified_only = manager.list_presets(unified_only=True)
all_policies = manager.list_presets(unified_only=False)
```

## API Reference

### Core Functions

#### `resolve_policy_name(policy_name, warn_deprecated=True)`
Resolve any policy name to unified standard name.

```python
resolve_policy_name("nasa_jpl_pot10") # → "nasa-compliance"
resolve_policy_name("strict-core")    # → "strict"
resolve_policy_name("service-defaults") # → "standard"
```

#### `validate_policy_name(policy_name)`
Validate if a policy name is recognized.

```python
validate_policy_name("nasa-compliance")  # → True
validate_policy_name("nasa_jpl_pot10")   # → True (legacy)
validate_policy_name("invalid")          # → False
```

#### `get_legacy_policy_name(unified_name, integration)`
Get legacy name for specific integration.

```python
get_legacy_policy_name("nasa-compliance", "cli")    # → "nasa_jpl_pot10"
get_legacy_policy_name("strict", "vscode")          # → "general_safety_strict"
get_legacy_policy_name("standard", "mcp")           # → "service-defaults"
```

### Migration Guide

#### Phase 1: Update Configuration (Recommended)
```yaml
# Old configuration
policy: nasa_jpl_pot10

# New configuration  
policy: nasa-compliance
```

#### Phase 2: Update Code
```python
# Old code
analyzer.analyze(path, policy="strict-core")

# New code
analyzer.analyze(path, policy="strict")
```

#### Phase 3: Update Documentation
- Replace legacy policy names in documentation
- Update examples to use unified names
- Reference this migration guide

## Policy Details

### `nasa-compliance` Policy
- **Max Parameters**: 2
- **Max Class Methods**: 15
- **Max Cyclomatic Complexity**: 8
- **Magic Literal Budget**: 3
- **Parameter Violation Budget**: 2
- **Total Violations**: 10

### `strict` Policy  
- **Max Parameters**: 2
- **Max Class Methods**: 15
- **Max Cyclomatic Complexity**: 8
- **Magic Literal Budget**: 3
- **Parameter Violation Budget**: 2
- **Total Violations**: 10

### `standard` Policy (Default)
- **Max Parameters**: 3
- **Max Class Methods**: 20
- **Max Cyclomatic Complexity**: 12
- **Magic Literal Budget**: 8
- **Parameter Violation Budget**: 5
- **Total Violations**: 30

### `lenient` Policy
- **Max Parameters**: 4
- **Max Class Methods**: 35
- **Max Cyclomatic Complexity**: 20
- **Magic Literal Budget**: 15
- **Parameter Violation Budget**: 8
- **Total Violations**: 50

## Architecture

### Components Updated

1. **`analyzer/constants.py`**: Core unified policy system
2. **`cli/connascence.py`**: CLI argument parser with deprecation warnings
3. **`mcp/server.py`**: MCP server policy validation
4. **`policy/manager.py`**: Policy manager with unified naming
5. **`utils/config_loader.py`**: Rate limiter compatibility fix

### Data Structures

- `UNIFIED_POLICY_NAMES`: List of standard policy names
- `UNIFIED_POLICY_MAPPING`: Legacy → unified name mapping
- `LEGACY_POLICY_MAPPING`: Unified → legacy name mapping per integration
- `POLICY_DEPRECATION_WARNINGS`: Deprecation messages

## Benefits

1. **Consistency**: Same policy names work across all integrations
2. **Clarity**: Self-documenting policy names (`nasa-compliance` vs `nasa_jpl_pot10`)
3. **Maintainability**: Single source of truth for policy configuration
4. **User Experience**: Clear deprecation warnings guide users to standard names
5. **Future-Proof**: Extensible system for new policy additions

## Testing

The unified policy system has been tested with:

✅ Policy name resolution (10 test cases)  
✅ CLI argument parsing with deprecation warnings  
✅ MCP server policy validation  
✅ Policy manager preset resolution  
✅ Backwards compatibility for all integrations  

## Version History

- **v2.0.0**: Initial unified policy system implementation
- Full backwards compatibility maintained
- Zero breaking changes

---

**Recommendation**: Start using unified policy names (`nasa-compliance`, `strict`, `standard`, `lenient`) for consistent behavior across all Connascence Safety Analyzer integrations.