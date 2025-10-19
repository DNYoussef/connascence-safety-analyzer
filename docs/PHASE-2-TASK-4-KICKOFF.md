# Phase 2 - Task 4: Add SARIF Output Format - Kickoff

**Date**: 2025-10-19
**Status**: 🚀 **STARTING**
**Priority**: P1
**Estimated Time**: 4 hours
**Dependencies**: Task 3 complete ✅

## Objective

Add SARIF (Static Analysis Results Interchange Format) output to the connascence analyzer, enabling integration with modern CI/CD pipelines and code quality tools.

## Background

### What is SARIF?

SARIF (Static Analysis Results Interchange Format) is a standard JSON format for static analysis tool output, defined by OASIS.

**Key Benefits**:
- ✅ Industry standard format (OASIS specification)
- ✅ Native support in GitHub Code Scanning
- ✅ Integration with VS Code, Azure DevOps, GitLab
- ✅ Rich metadata (rules, locations, fix suggestions)
- ✅ Human-readable and machine-parseable

**Specification**: [SARIF v2.1.0](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html)

### Why SARIF for Connascence?

Current analyzer outputs:
- `summary` - Human-readable text
- `json` - Custom JSON schema
- `detailed` - Verbose text output

**Problems**:
1. Custom JSON format not compatible with CI/CD tools
2. No native GitHub integration
3. Manual result interpretation required
4. No standard tooling support

**SARIF Solves**:
- Automatic GitHub Code Scanning integration
- VS Code problem panel integration
- Standard CI/CD pipeline support
- Unified analysis across multiple tools

## Success Criteria

### Required Deliverables

1. **SARIF Exporter Implementation** ✅
   - Convert connascence violations to SARIF format
   - Map connascence types to SARIF rules
   - Include source locations (file, line, column)
   - Add severity levels (error, warning, note)

2. **CLI Integration** ✅
   - Add `--sarif` flag to analyzer CLI
   - Add `--sarif-output <file>` for file output
   - Maintain compatibility with existing formats

3. **Rule Metadata** ✅
   - Full rule descriptions for all 9 connascence types
   - Help URLs linking to documentation
   - Severity mappings (CoI/CoE/CoV → error, others → warning)

4. **Testing** ✅
   - Validate SARIF schema compliance
   - Test with real connascence violations
   - Verify GitHub upload compatibility

5. **Documentation** ✅
   - SARIF usage examples
   - GitHub integration guide
   - Rule reference documentation

### Quality Gates

- ✅ SARIF output validates against official schema
- ✅ All 9 connascence types mapped correctly
- ✅ Source locations accurate (file:line:column)
- ✅ Compatible with `gh api` upload to GitHub
- ✅ Zero syntax errors, all tests passing

## SARIF Format Overview

### Minimal SARIF Structure

```json
{
  "version": "2.1.0",
  "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "Connascence Analyzer",
          "version": "1.0.0",
          "informationUri": "https://github.com/connascence/connascence.io",
          "rules": [...]
        }
      },
      "results": [...]
    }
  ]
}
```

### SARIF Result Structure

Each connascence violation becomes a SARIF result:

```json
{
  "ruleId": "CoN",
  "level": "warning",
  "message": {
    "text": "Connascence of Name detected: Variable 'foo' referenced 5 times"
  },
  "locations": [
    {
      "physicalLocation": {
        "artifactLocation": {
          "uri": "analyzer/core.py"
        },
        "region": {
          "startLine": 42,
          "startColumn": 5
        }
      }
    }
  ]
}
```

### Connascence → SARIF Severity Mapping

| Connascence Type | SARIF Level | Rationale |
|------------------|-------------|-----------|
| CoI (Identity) | `error` | Most dangerous, runtime bugs |
| CoE (Execution) | `error` | Timing-dependent, hard to debug |
| CoV (Value) | `error` | Magic numbers, high coupling |
| CoT (Type) | `warning` | Type coupling, moderate risk |
| CoP (Position) | `warning` | Parameter order coupling |
| CoM (Meaning) | `warning` | Semantic coupling |
| CoA (Algorithm) | `note` | Acceptable in some contexts |
| CoN (Name) | `note` | Lowest coupling, mostly acceptable |
| CoC (Convention) | `note` | Style/convention issues |

## Implementation Plan

### Phase 1: SARIF Exporter (1.5 hours)

**Files to Create**:
- `analyzer/formatters/sarif.py` - SARIF exporter implementation

**Key Functions**:
1. `generate_sarif()` - Main SARIF generation
2. `_create_tool_metadata()` - Tool description
3. `_create_rules()` - Rule definitions (all 9 types)
4. `_create_results()` - Convert violations to SARIF results
5. `_map_severity()` - Connascence → SARIF level mapping

**Design**:
```python
class SARIFExporter:
    """Export connascence violations to SARIF format."""

    def generate_sarif(self, violations: List[Dict], file_path: str) -> Dict:
        """Generate SARIF report from violations."""
        return {
            "version": "2.1.0",
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "runs": [{
                "tool": self._create_tool_metadata(),
                "results": self._create_results(violations, file_path)
            }]
        }

    def _create_tool_metadata(self) -> Dict:
        """Create tool and rule metadata."""
        return {
            "driver": {
                "name": "Connascence Analyzer",
                "version": "1.0.0",
                "informationUri": "https://github.com/connascence/connascence.io",
                "rules": self._create_rules()
            }
        }

    def _create_rules(self) -> List[Dict]:
        """Create SARIF rule definitions for all connascence types."""
        # Return all 9 connascence type definitions
        pass

    def _create_results(self, violations: List[Dict], file_path: str) -> List[Dict]:
        """Convert violations to SARIF results."""
        pass

    def _map_severity(self, connascence_type: str) -> str:
        """Map connascence type to SARIF severity level."""
        mapping = {
            "CoI": "error",
            "CoE": "error",
            "CoV": "error",
            # ... etc
        }
        return mapping.get(connascence_type, "warning")
```

### Phase 2: CLI Integration (1 hour)

**Files to Modify**:
- `analyzer/core.py` - Add SARIF format handling

**Changes**:
1. Add `--sarif` flag to `create_parser()`
2. Handle SARIF output in `_handle_output_format()`
3. Support `--output <file>` with SARIF format

**Example Usage**:
```bash
# Output to stdout
python -m analyzer.core.api analyze --source analyzer/ --format sarif

# Output to file
python -m analyzer.core.api analyze --source analyzer/ --format sarif --output results.sarif

# Upload to GitHub
python -m analyzer.core.api analyze --source . --format sarif --output results.sarif
gh api repos/{owner}/{repo}/code-scanning/sarifs --method POST --input results.sarif
```

### Phase 3: Rule Metadata (0.5 hours)

**Create**: `analyzer/formatters/sarif_rules.py`

All 9 connascence types with:
- Full descriptions
- Help URLs (connascence.io)
- Examples
- Severity justifications

### Phase 4: Testing & Validation (1 hour)

**Tests to Create**:
1. `tests/unit/test_sarif_exporter.py` - Unit tests for SARIF exporter
2. `tests/integration/test_sarif_format.py` - Integration test with real violations

**Validation**:
- SARIF schema validation (against official JSON schema)
- Test with real codebase violations
- Verify GitHub upload compatibility

## Expected Outcomes

### Functionality

**Before Task 4**:
```bash
# Only custom JSON format
python -m analyzer.core.api analyze --source analyzer/ --format json
```

**After Task 4**:
```bash
# SARIF format supported
python -m analyzer.core.api analyze --source analyzer/ --format sarif

# GitHub integration
python -m analyzer.core.api analyze --source . --format sarif --output results.sarif
gh api repos/{owner}/{repo}/code-scanning/sarifs --method POST --input results.sarif
```

### GitHub Integration Example

1. Run analyzer with SARIF output
2. Upload to GitHub Code Scanning
3. View violations in GitHub UI with inline annotations
4. Get PR comments for new violations

### Sample SARIF Output

```json
{
  "version": "2.1.0",
  "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "Connascence Analyzer",
          "version": "1.0.0",
          "informationUri": "https://github.com/connascence/connascence.io",
          "rules": [
            {
              "id": "CoV",
              "name": "ConnascenceOfValue",
              "shortDescription": {
                "text": "Connascence of Value"
              },
              "fullDescription": {
                "text": "Multiple components must agree on the value of something (e.g., magic numbers)"
              },
              "helpUri": "https://connascence.io/value.html",
              "defaultConfiguration": {
                "level": "error"
              }
            }
          ]
        }
      },
      "results": [
        {
          "ruleId": "CoV",
          "level": "error",
          "message": {
            "text": "Magic number literal '60' used in multiple locations"
          },
          "locations": [
            {
              "physicalLocation": {
                "artifactLocation": {
                  "uri": "analyzer/core.py",
                  "uriBaseId": "SRCROOT"
                },
                "region": {
                  "startLine": 42,
                  "startColumn": 15
                }
              }
            }
          ]
        }
      ]
    }
  ]
}
```

## Timeline

### Estimated 4 Hours Breakdown

- **Hour 1**: Research SARIF spec, design exporter ✅
- **Hour 2**: Implement SARIF exporter (generate_sarif, rules) ✅
- **Hour 3**: CLI integration, rule metadata ✅
- **Hour 4**: Testing, validation, documentation ✅

### Milestones

1. ✅ SARIF exporter implemented
2. ✅ CLI flag working
3. ✅ All 9 connascence types mapped
4. ✅ Tests passing
5. ✅ GitHub upload compatible

## Risks & Mitigations

### Identified Risks

**Risk 1: SARIF Schema Complexity**
- **Impact**: P2 (Medium)
- **Mitigation**: Use minimal valid SARIF structure, test with schema validator

**Risk 2: Source Location Accuracy**
- **Impact**: P2 (Medium)
- **Mitigation**: Reuse existing AST line/column info, validate with real files

**Risk 3: GitHub Upload Compatibility**
- **Impact**: P3 (Low)
- **Mitigation**: Test with `gh api` before declaring complete

### No Blocking Risks
All risks are P2-P3 and have clear mitigations.

## Dependencies

### Prerequisites (All Met ✅)
- ✅ Task 3 complete (NASA compliance)
- ✅ Analyzer produces structured violations
- ✅ CLI framework in place

### External Dependencies
- SARIF v2.1.0 specification (public)
- JSON Schema validator (pytest plugin)
- GitHub CLI (`gh`) for testing (optional)

## Next Steps

1. Create SARIF exporter implementation
2. Add CLI integration
3. Write tests
4. Validate with GitHub upload
5. Document usage

---

## Kickoff Summary

**Task**: Add SARIF output format to connascence analyzer
**Goal**: Enable GitHub Code Scanning integration and CI/CD pipeline support
**Time**: 4 hours (budgeted)
**Status**: Ready to start! 🚀

**First Action**: Implement `analyzer/formatters/sarif.py` with SARIF exporter

---

**Created**: 2025-10-19
**Status**: 🚀 **READY TO START**
**Estimated Completion**: 2025-10-19 (same day, 4 hours)
