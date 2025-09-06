# Report Interpretation Guide

## Overview

This guide explains how to understand and interpret the output from the Connascence Safety Analyzer across different output formats (JSON, SARIF, YAML).

## JSON Report Structure

### Main Analysis Result

```json
{
  "success": true,                    // Analysis completed successfully
  "path": "/analyzed/path",           // Path that was analyzed  
  "policy": "nasa_jpl_pot10",        // Analysis policy used
  "violations": [...],                // Array of violation objects
  "summary": {...},                   // High-level metrics
  "nasa_compliance": {...},           // NASA-specific analysis
  "mece_analysis": {...},            // Duplication analysis
  "god_objects": [...],              // God object violations
  "metrics": {...},                   // Performance metrics
  "quality_gates": {...}             // Pass/fail status
}
```

### Violation Object Structure

```json
{
  "id": "violation_12345",           // Unique violation identifier
  "rule_id": "CON_CoM",             // Connascence type code
  "type": "CoM",                     // Connascence type short name
  "severity": "medium",              // Severity level
  "description": "Magic literal detected in conditional statement",
  "file_path": "/path/to/file.py",   // File containing violation
  "line_number": 42,                 // Line where violation occurs
  "weight": 2.0,                     // Severity weight for scoring
  "analysis_mode": "unified",        // Analysis engine used
  "recommendation": "Extract to named constant",  // How to fix
  "context": {                       // Additional context
    "function_name": "calculate_total",
    "magic_value": "0.08"
  }
}
```

## Violation Types and Severity

### Connascence Type Codes

| Code | Type | Description | Typical Severity |
|------|------|-------------|------------------|
| `CON_CoN` | Name | Variable/function naming coupling | Low-Medium |
| `CON_CoT` | Type | Type-based coupling | Medium |
| `CON_CoM` | Meaning | Magic literals, hardcoded values | Medium-High |
| `CON_CoP` | Position | Parameter order coupling | High |
| `CON_CoA` | Algorithm | Duplicate/similar algorithms | Medium |
| `CON_CoE` | Execution | Execution order dependencies | High |
| `CON_CoTm` | Timing | Time-based dependencies | Critical |
| `CON_CoV` | Value | Value-dependent coupling | Medium |
| `CON_CoI` | Identity | Object identity coupling | High |

### Severity Levels

| Level | Weight | Description | Action Required |
|-------|--------|-------------|-----------------|
| `critical` | 10 | System-threatening issues | **Immediate fix required** |
| `high` | 5 | Significant maintainability issues | **Fix soon** |  
| `medium` | 2 | Moderate coupling issues | **Plan to fix** |
| `low` | 1 | Minor style/best practice issues | **Fix when convenient** |

### Common Violation Patterns

#### 1. Magic Literals (CoM) - Most Common
```json
{
  "rule_id": "CON_CoM",
  "severity": "medium", 
  "description": "Magic literal '3600' detected in conditional",
  "recommendation": "Extract to named constant: SECONDS_PER_HOUR = 3600",
  "context": {
    "magic_value": "3600",
    "context_type": "conditional"
  }
}
```

#### 2. Parameter Coupling (CoP) - NASA Rule Violation
```json
{
  "rule_id": "CON_CoP", 
  "severity": "high",
  "description": "Function has 8 parameters - high connascence of position",
  "recommendation": "Use parameter objects or reduce parameters",
  "context": {
    "parameter_count": 8,
    "nasa_rule_violation": "Rule #6: Functions should have ≤6 parameters"
  }
}
```

#### 3. God Objects - Critical Safety Issue
```json
{
  "rule_id": "GOD_OBJECT",
  "severity": "critical",
  "description": "Class 'DataProcessor' is a God Object: 25 methods, ~650 lines",
  "recommendation": "Split into smaller, focused classes following Single Responsibility Principle",
  "context": {
    "method_count": 25,
    "estimated_lines": 650,
    "nasa_rule_violation": "Rule #7: Data Hiding"
  }
}
```

## Summary Metrics Interpretation

### Overall Quality Score
```json
"summary": {
  "total_violations": 150,           // Total violations found
  "critical_violations": 3,          // Critical severity count
  "overall_quality_score": 0.75     // 0.0 (worst) to 1.0 (perfect)
}
```

**Quality Score Calculation**:
- Based on violation counts weighted by severity
- 0.90-1.00: Excellent code quality
- 0.80-0.89: Good code quality  
- 0.70-0.79: Acceptable code quality
- 0.60-0.69: Poor code quality
- <0.60: Critical quality issues

### NASA Compliance Analysis
```json
"nasa_compliance": {
  "score": 0.85,                     // NASA compliance score (0-1)
  "violations": [...],               // NASA-specific violations
  "passing": false,                  // Meets NASA threshold (≥0.95)
  "rules_evaluated": {
    "rule_1": "passed",              // Code simplicity
    "rule_6": "failed",              // Parameter limits
    "rule_7": "failed"               // God objects detected
  }
}
```

### MECE Duplication Analysis
```json
"mece_analysis": {
  "score": 0.70,                     // MECE score (1.0 = no duplicates)
  "duplications": [...],             // Duplicate code clusters
  "passing": false,                  // Meets MECE threshold (≥0.80)
  "summary": {
    "total_duplications": 5,
    "high_similarity_count": 2,      // >80% similarity
    "files_analyzed": 42,
    "blocks_analyzed": 156
  }
}
```

## SARIF Report Structure

### SARIF Benefits
- **IDE Integration**: Direct in-editor violation highlighting
- **Tool Standardization**: Common format across security tools  
- **CI/CD Integration**: Native support in many platforms
- **Rich Metadata**: Detailed violation context

### Key SARIF Sections

```json
{
  "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0.json",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "Connascence Safety Analyzer",
          "version": "2.0.0"
        }
      },
      "results": [
        {
          "ruleId": "CON_CoM",                    // Rule identifier
          "level": "warning",                     // SARIF severity
          "message": {
            "text": "Magic literal detected"
          },
          "locations": [
            {
              "physicalLocation": {
                "artifactLocation": {
                  "uri": "src/main.py"            // File path
                },
                "region": {
                  "startLine": 42,                // Line number
                  "startColumn": 15               // Column position
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

## Performance Metrics

### Analysis Metrics
```json
"metrics": {
  "files_analyzed": 42,              // Number of files processed
  "analysis_time": 2.5,             // Total analysis time (seconds)
  "timestamp": 1696123456.789,      // Analysis completion time
  "connascence_index": 0.82,        // Overall connascence health
  "analysis_mode": "unified"         // Engine used (unified/fallback/mock)
}
```

### Performance Interpretation
- **Analysis Time**: 
  - <1s: Small files/projects
  - 1-10s: Medium projects (~100 files)
  - >30s: Large projects (1000+ files)
- **Files Analyzed**: Excludes test files, build artifacts
- **Connascence Index**: Higher is better (less coupling)

## Quality Gates Interpretation

### Gate Status
```json
"quality_gates": {
  "overall_passing": true,           // Overall quality ≥0.75
  "nasa_passing": false,             // NASA compliance ≥0.95
  "mece_passing": false              // MECE score ≥0.80
}
```

### Gate Thresholds (Configurable)
- **Overall Quality**: ≥0.75 (good maintainability)
- **NASA Compliance**: ≥0.95 (safety-critical systems)
- **MECE Quality**: ≥0.80 (low code duplication)

## Practical Interpretation Examples

### Example 1: Legacy Codebase
```json
{
  "summary": {
    "total_violations": 2456,
    "critical_violations": 15,
    "overall_quality_score": 0.42
  },
  "nasa_compliance": {
    "score": 0.68,
    "passing": false
  }
}
```

**Interpretation**: 
- High violation count indicates legacy technical debt
- Critical violations need immediate attention
- Quality score below 0.60 suggests significant refactoring needed
- NASA compliance failing - not suitable for safety-critical use

**Recommended Actions**:
1. Address critical violations first
2. Focus on god objects and parameter coupling
3. Plan systematic refactoring effort
4. Consider modular improvement approach

### Example 2: Well-Maintained Project
```json
{
  "summary": {
    "total_violations": 23,
    "critical_violations": 0, 
    "overall_quality_score": 0.89
  },
  "nasa_compliance": {
    "score": 0.96,
    "passing": true
  }
}
```

**Interpretation**:
- Low violation count indicates good practices
- No critical violations - safe for production
- High quality score shows good maintainability  
- NASA compliant - suitable for safety-critical use

**Recommended Actions**:
1. Address remaining violations gradually
2. Maintain current quality standards
3. Use as reference for other projects

## Troubleshooting Report Issues

### Common Issues

1. **Empty Violations Array**
   - Very high-quality code (rare)
   - Analysis engine issues
   - Path/file access problems

2. **All Violations Same Type**
   - Usually CoM (magic literals) in certain codebases
   - May indicate specific coding patterns

3. **Unrealistic Scores**
   - Check analysis_mode (mock mode gives dummy data)
   - Verify analyzer import success

4. **Missing Sections**
   - Some features require specific flags
   - Check policy settings and options used

### Validation Checklist
- ✅ `success: true` in main result
- ✅ `analysis_mode: "unified"` for full analysis
- ✅ Realistic violation counts for codebase size
- ✅ Violation file paths match analyzed directory
- ✅ Performance metrics reasonable for project size