# SARIF Usage Guide - Connascence Analyzer

**Date**: 2025-10-19
**SARIF Version**: 2.1.0
**Analyzer Version**: 1.0.0

## Overview

The Connascence Analyzer supports SARIF (Static Analysis Results Interchange Format) output for seamless integration with modern CI/CD pipelines and code quality tools.

## What is SARIF?

SARIF is an OASIS standard JSON format for static analysis tool output. It enables:

- ✅ **GitHub Code Scanning** - Automatic PR annotations
- ✅ **VS Code Integration** - Problems panel integration
- ✅ **Azure DevOps** - Build pipeline integration
- ✅ **GitLab** - Security dashboard integration
- ✅ **Universal Tooling** - Standard format across all tools

**Specification**: [SARIF v2.1.0](https://docs.oasis-open.org/sarif/sarif/v2.1.0/)

## Basic Usage

### Generate SARIF Output

```bash
# Output to stdout
python analyzer/core.py --path analyzer/ --format sarif

# Output to file
python analyzer/core.py --path analyzer/ --format sarif --output results.sarif
```

### Output Formats Supported

| Format | Description | Use Case |
|--------|-------------|----------|
| `sarif` | SARIF v2.1.0 JSON | CI/CD integration, GitHub |
| `json` | Custom JSON schema | Custom tooling |
| `yaml` | YAML format | Human-readable reports |

## GitHub Integration

### Setup GitHub Code Scanning

1. **Generate SARIF report**:
```bash
python analyzer/core.py --path . --format sarif --output connascence.sarif
```

2. **Upload to GitHub** (via GitHub CLI):
```bash
gh api repos/{owner}/{repo}/code-scanning/sarifs \\
  --method POST \\
  --input connascence.sarif
```

3. **Via GitHub Actions** (recommended):
```yaml
name: Connascence Analysis

on: [push, pull_request]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install analyzer
        run: pip install -r requirements.txt

      - name: Run connascence analysis
        run: python analyzer/core.py --path . --format sarif --output connascence.sarif

      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: connascence.sarif
          category: connascence
```

### GitHub Code Scanning Features

Once uploaded, GitHub provides:
- 📍 **Inline annotations** on PR diffs
- 🔍 **Security tab** with all violations
- 📊 **Trend analysis** over time
- 🚨 **PR checks** blocking on critical violations

## SARIF Structure

### Minimal SARIF Output

```json
{
  "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0.json",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "connascence",
          "version": "1.0.0",
          "informationUri": "https://github.com/connascence/connascence-analyzer"
        }
      },
      "results": [...]
    }
  ]
}
```

### Sample Violation Result

```json
{
  "ruleId": "CON_CoV",
  "level": "warning",
  "message": {
    "text": "Magic number literal '60' used 5 times"
  },
  "locations": [
    {
      "physicalLocation": {
        "artifactLocation": {
          "uri": "analyzer/core.py"
        },
        "region": {
          "startLine": 42,
          "startColumn": 15
        }
      }
    }
  ]
}
```

## Connascence Types in SARIF

### Rule Mappings

| Connascence Type | SARIF Rule ID | Severity | Description |
|------------------|---------------|----------|-------------|
| **Static Connascences** |
| Name (CoN) | `CON_CoN` | `note` | Name dependencies |
| Type (CoT) | `CON_CoT` | `note` | Type dependencies |
| Meaning (CoM) | `CON_CoM` | `warning` | Magic literals |
| Position (CoP) | `CON_CoP` | `warning` | Parameter order |
| Algorithm (CoA) | `CON_CoA` | `note` | Algorithm agreement |
| **Dynamic Connascences** |
| Execution (CoE) | `CON_CoE` | `error` | Execution order |
| Timing (CoT2) | `CON_CoT2` | `error` | Timing dependencies |
| Value (CoV) | `CON_CoV` | `error` | Value agreement |
| Identity (CoI) | `CON_CoI` | `error` | Instance identity |

### Severity Levels

**SARIF Level → Meaning**:
- `error` - Critical coupling, high risk (CoI, CoE, CoV, CoT2)
- `warning` - Moderate coupling, should fix (CoM, CoP)
- `note` - Low coupling, acceptable (CoN, CoT, CoA)

## Advanced Usage

### Include NASA Compliance Rules

```bash
python analyzer/core.py --path . \\
  --format sarif \\
  --include-nasa-rules \\
  --output results.sarif
```

### Enable Enhanced Analysis

```bash
python analyzer/core.py --path . \\
  --format sarif \\
  --enable-correlations \\
  --enable-smart-recommendations \\
  --output results.sarif
```

### Filter by Policy

```bash
# Strict policy (more violations)
python analyzer/core.py --path . --policy strict --format sarif

# Lenient policy (fewer violations)
python analyzer/core.py --path . --policy lenient --format sarif

# NASA compliance policy
python analyzer/core.py --path . --policy nasa-compliance --format sarif
```

## CI/CD Integration Examples

### Azure DevOps

```yaml
- task: PythonScript@0
  inputs:
    scriptSource: 'inline'
    script: |
      python analyzer/core.py --path . --format sarif --output $(Build.ArtifactStagingDirectory)/connascence.sarif
  displayName: 'Run Connascence Analysis'

- task: PublishBuildArtifacts@1
  inputs:
    pathtoPublish: '$(Build.ArtifactStagingDirectory)'
    artifactName: 'CodeAnalysisLogs'
```

### GitLab CI

```yaml
connascence-analysis:
  stage: test
  script:
    - pip install -r requirements.txt
    - python analyzer/core.py --path . --format sarif --output connascence.sarif
  artifacts:
    reports:
      sast: connascence.sarif
    expire_in: 1 week
```

### Jenkins

```groovy
pipeline {
    agent any

    stages {
        stage('Connascence Analysis') {
            steps {
                sh 'python analyzer/core.py --path . --format sarif --output connascence.sarif'
                publishHTML([
                    reportDir: '.',
                    reportFiles: 'connascence.sarif',
                    reportName: 'Connascence Report'
                ])
            }
        }
    }
}
```

## Validation

### Validate SARIF Schema

```bash
# Using Python json module
cat results.sarif | python -m json.tool > /dev/null && echo "Valid JSON"

# Using SARIF validator (if installed)
sarif validate results.sarif
```

### SARIF Schema URL

The analyzer outputs SARIF v2.1.0 with schema:
```
https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0.json
```

## Troubleshooting

### Common Issues

**Issue 1: Empty SARIF Output**
```bash
# Problem: No violations found
Analysis completed successfully. 0 total violations (0 critical)

# Solution: Check if code actually has connascence violations
# or use stricter policy
python analyzer/core.py --path . --policy strict --format sarif
```

**Issue 2: GitHub Upload Failed**
```bash
# Problem: SARIF validation error on GitHub

# Solution: Verify schema compliance
cat results.sarif | python -m json.tool

# Ensure using correct GitHub API
gh api repos/{owner}/{repo}/code-scanning/sarifs --method POST --input results.sarif
```

**Issue 3: Large SARIF Files**
```bash
# Problem: SARIF file too large for GitHub (max 10MB)

# Solution: Analyze in chunks or exclude low-severity violations
python analyzer/core.py --path . --format sarif --fail-on-critical
```

## Best Practices

### 1. Continuous Integration

Run connascence analysis on every PR:
```yaml
# .github/workflows/connascence.yml
on: [pull_request]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Analyze
        run: python analyzer/core.py --path . --format sarif --output connascence.sarif
      - name: Upload
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: connascence.sarif
```

### 2. Fail on Critical Violations

```bash
python analyzer/core.py --path . \\
  --format sarif \\
  --fail-on-critical \\
  --output results.sarif
```

Exit code will be non-zero if critical violations found, failing CI builds.

### 3. Track Trends Over Time

Store SARIF results as artifacts:
```yaml
- name: Archive SARIF
  uses: actions/upload-artifact@v3
  with:
    name: connascence-sarif
    path: connascence.sarif
    retention-days: 30
```

### 4. Combine with Other Tools

SARIF enables multi-tool analysis:
```bash
# Run connascence analyzer
python analyzer/core.py --path . --format sarif --output connascence.sarif

# Merge with other SARIF reports
sarif merge connascence.sarif eslint.sarif bandit.sarif --output combined.sarif
```

## Examples

### Example 1: Basic CI/CD

```bash
# 1. Run analysis
python analyzer/core.py --path . --format sarif --output results.sarif

# 2. Upload to GitHub
gh api repos/myorg/myrepo/code-scanning/sarifs --method POST --input results.sarif

# 3. View results at
# https://github.com/myorg/myrepo/security/code-scanning
```

### Example 2: Local Development

```bash
# 1. Generate SARIF
python analyzer/core.py --path . --format sarif --output local.sarif

# 2. View in VS Code (with SARIF extension)
code local.sarif
```

### Example 3: Custom Policies

```bash
# Analyze with custom thresholds
python analyzer/core.py --path . \\
  --policy nasa-compliance \\
  --compliance-threshold 95 \\
  --max-god-objects 5 \\
  --format sarif \\
  --output strict.sarif
```

## Resources

- **SARIF Specification**: https://docs.oasis-open.org/sarif/sarif/v2.1.0/
- **GitHub Code Scanning**: https://docs.github.com/en/code-security/code-scanning
- **SARIF Tutorials**: https://github.com/microsoft/sarif-tutorials
- **VS Code SARIF Extension**: https://marketplace.visualstudio.com/items?itemName=MS-SarifVSCode.sarif-viewer

---

## Quick Reference

```bash
# Basic SARIF output
python analyzer/core.py --path . --format sarif --output results.sarif

# With GitHub upload
python analyzer/core.py --path . --format sarif --output results.sarif \\
  && gh api repos/{owner}/{repo}/code-scanning/sarifs --method POST --input results.sarif

# Fail on critical violations
python analyzer/core.py --path . --format sarif --fail-on-critical

# Enhanced analysis
python analyzer/core.py --path . --format sarif \\
  --enable-correlations --enable-smart-recommendations
```

---

**Last Updated**: 2025-10-19
**SARIF Version**: 2.1.0
**Analyzer Version**: 1.0.0
