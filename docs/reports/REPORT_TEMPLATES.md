# Report Templates

Standardized output formats and templates for the Connascence Safety Analyzer reporting system.

## Overview

This document defines the current report formats, their structure, usage patterns, and customization options for generating analysis results.

## Report Formats

The analyzer currently supports 4 standardized output formats, each optimized for specific use cases:

### 1. SARIF (Static Analysis Results Interchange Format)

**Format**: JSON  
**Use Case**: IDE integration, CI/CD pipelines, GitHub security tab  
**Schema**: SARIF 2.1.0 compliant  
**Current Usage**: VS Code extension integration, GitHub Actions upload  

#### SARIF Template Structure

```json
{
  "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0.json",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "connascence-safety-analyzer",
          "version": "2.0.0",
          "informationUri": "https://connascence.io",
          "rules": [
            {
              "id": "CON_CoM",
              "name": "ConnascenceOfMeaning",
              "shortDescription": {
                "text": "Magic literals should be extracted to constants"
              },
              "fullDescription": {
                "text": "Magic literals create connascence of meaning between multiple locations that must agree on the literal's semantic meaning."
              },
              "messageStrings": {
                "default": {
                  "text": "Magic literal '{0}' should be extracted to a named constant"
                }
              },
              "properties": {
                "connascence_type": "CoM",
                "severity": "medium",
                "nasa_compliance": "rule_5"
              }
            }
          ]
        }
      },
      "results": [
        {
          "ruleId": "CON_CoM",
          "ruleIndex": 0,
          "message": {
            "id": "default",
            "arguments": ["100"]
          },
          "level": "warning",
          "locations": [
            {
              "physicalLocation": {
                "artifactLocation": {
                  "uri": "src/analyzer.py",
                  "uriBaseId": "%SRCROOT%"
                },
                "region": {
                  "startLine": 42,
                  "startColumn": 12,
                  "endColumn": 15
                }
              }
            }
          ],
          "properties": {
            "connascence_weight": 2.5,
            "suggested_fix": "MAX_THRESHOLD = 100"
          }
        }
      ],
      "invocations": [
        {
          "executionSuccessful": true,
          "startTimeUtc": "2024-09-06T10:30:00.000Z",
          "endTimeUtc": "2024-09-06T10:30:05.234Z"
        }
      ],
      "properties": {
        "nasa_compliance_summary": {
          "total_rules": 10,
          "violations": 3,
          "compliance_percentage": 70.0
        },
        "connascence_budget": {
          "total_weight": 45.2,
          "budget_limit": 50.0,
          "budget_used_percentage": 90.4
        }
      }
    }
  ]
}
```

#### SARIF Usage Examples

```bash
# Generate SARIF report
connascence scan --format sarif --output results.sarif src/

# Import to VS Code
# File -> Open -> results.sarif

# Use in GitHub Actions
- name: Upload SARIF
  uses: github/codeql-action/upload-sarif@v2
  with:
    sarif_file: results.sarif
```

### 2. JSON (Structured Data)

**Format**: JSON  
**Use Case**: API integration, dashboard systems, data analysis  
**Schema**: Custom schema with metadata and performance metrics  
**Current Usage**: Test results aggregation, CI/CD pipeline data, memory coordination  

#### JSON Template Structure

```json
{
  "metadata": {
    "timestamp": "2024-09-06T10:30:00.000Z",
    "version": "2.0.0",
    "analyzer": "connascence-safety-analyzer",
    "scan_duration_ms": 5234,
    "files_analyzed": 127,
    "lines_analyzed": 45670
  },
  "summary": {
    "total_violations": 23,
    "by_severity": {
      "critical": 0,
      "high": 5,
      "medium": 12,
      "low": 6
    },
    "by_connascence_type": {
      "CoM": 8,
      "CoP": 4,
      "CoT": 7,
      "CoA": 3,
      "CoN": 1
    },
    "connascence_budget": {
      "total_weight": 45.2,
      "budget_limit": 50.0,
      "budget_remaining": 4.8,
      "budget_used_percentage": 90.4,
      "status": "warning"
    }
  },
  "violations": [
    {
      "id": "violation_001",
      "rule_id": "CON_CoM",
      "connascence_type": "CoM",
      "severity": "medium",
      "weight": 2.5,
      "description": "Magic literal '100' should be extracted to constant",
      "file_path": "src/analyzer.py",
      "line_number": 42,
      "column_start": 12,
      "column_end": 15,
      "code_snippet": "if threshold > 100:",
      "suggested_fix": {
        "description": "Extract to constant",
        "confidence": 0.85,
        "old_code": "if threshold > 100:",
        "new_code": "MAX_THRESHOLD = 100\nif threshold > MAX_THRESHOLD:"
      },
      "nasa_compliance": {
        "rule_number": 5,
        "rule_description": "Data hiding",
        "compliant": false
      }
    }
  ],
  "nasa_compliance": {
    "overall_compliance": 70.0,
    "rules": [
      {
        "rule_number": 1,
        "description": "Avoid complex flow constructs",
        "violations": 2,
        "compliant": false
      },
      {
        "rule_number": 2,
        "description": "Fixed upper bound on loops",
        "violations": 0,
        "compliant": true
      }
    ]
  },
  "autofix_suggestions": {
    "total_suggestions": 15,
    "by_confidence": {
      "high": 8,
      "medium": 5,
      "low": 2
    },
    "estimated_fix_time_minutes": 45
  },
  "performance_metrics": {
    "analysis_speed_lines_per_second": 8734,
    "memory_peak_mb": 156,
    "cpu_usage_percentage": 23.4
  }
}
```

#### JSON Usage Examples

```bash
# Generate JSON report
connascence scan --format json --output analysis.json src/

# Use with jq for filtering
jq '.violations[] | select(.severity == "high")' analysis.json

# Import into dashboard
curl -X POST -H "Content-Type: application/json" \
     -d @analysis.json \
     https://dashboard.example.com/api/analysis
```

### 3. Markdown (Human-Readable Summary)

**Format**: Markdown  
**Use Case**: Documentation, pull request comments, executive reports  
**Features**: Rich formatting, violation summaries, autofix suggestions  
**Current Usage**: GitHub PR comments, documentation generation, team reports  

#### Markdown Template Structure

```markdown
# Connascence Analysis Report

**Generated**: September 6, 2024 10:30 AM  
**Version**: 2.0.0  
**Files Analyzed**: 127 files (45,670 lines)
**Analysis Duration**: 5.2 seconds

## 📊 Summary

| Metric | Value | Status |
|--------|--------|--------|
| Total Violations | 23 | ⚠️ Warning |
| Critical Issues | 0 | ✅ Good |
| High Priority | 5 | ⚠️ Needs Attention |
| Connascence Budget | 90.4% used | ⚠️ Near Limit |
| NASA Compliance | 70.0% | ⚠️ Partial |

## 🎯 Connascence Budget Analysis

```
Budget Usage: █████████░ 90.4% (45.2/50.0)
Remaining:    ░░░░░░░░░░  4.8 points
```

⚠️ **Warning**: Budget is 90.4% consumed. Consider refactoring high-weight violations.

## 📊 Violation Breakdown

### By Severity
- **Critical** (0): ✅ No critical issues
- **High** (5): 🗌 [View Details](#high-priority-violations)
- **Medium** (12): 🗌 [View Details](#medium-priority-violations)
- **Low** (6): 🗌 [View Details](#low-priority-violations)

### By Connascence Type
- **CoM (Connascence of Meaning)** (8): Magic literals, hardcoded strings
- **CoP (Connascence of Position)** (4): Parameter order dependencies
- **CoT (Connascence of Type)** (7): Type system issues
- **CoA (Connascence of Algorithm)** (3): Complex algorithms, god classes
- **CoN (Connascence of Name)** (1): Naming inconsistencies

## 🚨 High Priority Violations

### 1. Parameter Bomb in `OrderProcessor.calculate_discount()`

**File**: `src/order_processor.py:42`  
**Type**: CoP (Connascence of Position)  
**Severity**: High  
**Weight**: 4.0

```python
def calculate_discount(price, customer_type, season, promo_code, region, membership_level):
    # 6 positional parameters exceeds limit of 3
```

**🛠️ Suggested Fix** (Confidence: 85%):
```python
def calculate_discount(price: float, *, customer_type: str, season: str, 
                      promo_code: str, region: str, membership_level: str):
```

**NASA Rule Impact**: Violates Rule 5 (Data Hiding)

### 2. God Class: `OrderProcessor`

**File**: `src/order_processor.py:120`  
**Type**: CoA (Connascence of Algorithm)  
**Severity**: High  
**Weight**: 5.0

Class has 25 methods (limit: 20). Consider splitting into smaller, focused classes.

**🛠️ Suggested Refactoring**:
- Extract payment processing to `PaymentProcessor`
- Extract shipping logic to `ShippingCalculator`
- Extract inventory management to `InventoryManager`

## 🗌 Medium Priority Violations

<details>
<summary>Magic Literals (8 violations)</summary>

1. **src/analyzer.py:42** - Magic literal `100` → `MAX_THRESHOLD`
2. **src/validator.py:67** - Magic string `"premium"` → `PREMIUM_TIER`
3. **src/calculator.py:23** - Magic literal `0.15` → `DEFAULT_DISCOUNT_RATE`

[View all magic literal violations...](#magic-literals-detailed)

</details>

<details>
<summary>Type Hints Missing (7 violations)</summary>

1. **src/utils.py:15** - `process_data()` missing return type
2. **src/helpers.py:34** - `validate_input()` missing parameter types

[View all type hint violations...](#type-hints-detailed)

</details>

## 🎯 NASA JPL Compliance Report

| Rule | Description | Violations | Status |
|------|-------------|------------|---------|
| 1 | Avoid complex flow constructs | 2 | ❌ Failed |
| 2 | Fixed upper bound on loops | 0 | ✅ Passed |
| 3 | No dynamic memory allocation | 1 | ❌ Failed |
| 4 | Limit function size | 3 | ❌ Failed |
| 5 | Data hiding | 5 | ❌ Failed |
| 6 | Check return values | 0 | ✅ Passed |
| 7 | Limit preprocessor use | 0 | ✅ Passed |
| 8 | Restrict function pointers | 1 | ❌ Failed |
| 9 | Be selective with recursion | 0 | ✅ Passed |
| 10 | Test assertions | 2 | ❌ Failed |

**Overall Compliance**: 70.0% (7/10 rules passed)

## ⚙️ Autofix Opportunities

🤖 **15 violations** can be automatically fixed with high confidence:

- **8 high-confidence fixes** (85%+ confidence)
- **5 medium-confidence fixes** (70-84% confidence)
- **2 low-confidence fixes** (<70% confidence)

**Estimated fix time**: 45 minutes

```bash
# Apply all high-confidence fixes
connascence autofix --confidence-threshold 85 src/

# Preview changes before applying
connascence autofix --dry-run --show-diff src/
```

## 📈 Performance Metrics

- **Analysis Speed**: 8,734 lines/second
- **Memory Usage**: 156 MB peak
- **CPU Usage**: 23.4% average
- **File Processing Rate**: 24.3 files/second

## 📝 Recommendations

### Immediate Actions (High Priority)
1. 🔴 **Refactor `OrderProcessor`** - Split into 3-4 smaller classes
2. 🔴 **Fix parameter bombs** - Convert to keyword-only parameters
3. 🔴 **Extract magic literals** - Create constants module

### Medium Term (This Sprint)
1. 🟡 **Add missing type hints** - Improve type safety
2. 🟡 **NASA compliance improvements** - Address rules 1, 3, 4, 5, 8, 10
3. 🟡 **Connascence budget management** - Target <80% usage

### Long Term (Next Quarter)
1. 🟢 **Architecture review** - Reduce coupling between components
2. 🟢 **Performance optimization** - Target <3 second analysis time
3. 🟢 **Documentation updates** - Align with coding standards

## 🛠️ Tools and Resources

- **VS Code Extension**: Install `connascence-analyzer` for real-time feedback
- **Pre-commit Hooks**: Prevent violations before commit
- **CI/CD Integration**: Automate quality gates
- **Documentation**: [Connascence Patterns Guide](https://connascence.io/guide)

---

📅 **Next Analysis**: Schedule weekly analysis runs  
📊 **Dashboard**: View trends at [dashboard.connascence.io](https://dashboard.connascence.io)  
🗞️ **Support**: [Issues](https://github.com/connascence/analyzer/issues) | [Docs](https://connascence.io/docs)

*Generated by Connascence Safety Analyzer v2.0.0*
```

#### Markdown Usage Examples

```bash
# Generate markdown report
connascence scan --format markdown --output report.md src/

# Use in pull request comments
gh pr comment --body-file report.md $PR_NUMBER

# Convert to other formats
pandoc report.md -o report.html
pandoc report.md -o report.pdf
```

### 4. Text (Plain Text Summary)

**Format**: Plain text  
**Use Case**: CI/CD logs, email reports, terminal output, command line usage  
**Features**: Console-friendly, scriptable, exit code integration  
**Current Usage**: CLI default output, CI/CD pipeline logs, automated reporting  

#### Text Template Structure

```
=============================================================================
              CONNASCENCE SAFETY ANALYZER REPORT v2.0.0
=============================================================================

Generated: September 6, 2024 10:30 AM
Files Analyzed: 127 files (45,670 lines)
Analysis Duration: 5.2 seconds

-----------------------------------------------------------------------------
                             SUMMARY
-----------------------------------------------------------------------------

Total Violations: 23

By Severity:
  Critical: 0  ✅
  High:     5  ⚠️
  Medium:   12 ⚠️
  Low:      6  🟨

By Connascence Type:
  CoM (Connascence of Meaning):     8
  CoP (Connascence of Position):    4
  CoT (Connascence of Type):        7
  CoA (Connascence of Algorithm):   3
  CoN (Connascence of Name):        1

Connascence Budget:
  Used:      45.2/50.0 (90.4%)
  Remaining: 4.8 points
  Status:    WARNING - Near budget limit

NASA Compliance: 70.0% (7/10 rules passed)

-----------------------------------------------------------------------------
                         HIGH PRIORITY VIOLATIONS
-----------------------------------------------------------------------------

[1] Parameter Bomb - HIGH SEVERITY (Weight: 4.0)
    File: src/order_processor.py:42
    Rule: CON_CoP (Connascence of Position)
    Description: Function has 6 positional parameters (max: 3)
    Code: def calculate_discount(price, customer_type, season, promo_code, ...)
    Fix: Convert to keyword-only parameters
    NASA Rule: Violates Rule 5 (Data hiding)

[2] God Class - HIGH SEVERITY (Weight: 5.0)
    File: src/order_processor.py:120
    Rule: CON_CoA (Connascence of Algorithm)
    Description: Class has 25 methods (max: 20)
    Code: class OrderProcessor:
    Fix: Split into smaller, focused classes
    NASA Rule: Violates Rule 4 (Limit function size)

[3] Magic Literal - HIGH SEVERITY (Weight: 3.5)
    File: src/analyzer.py:42
    Rule: CON_CoM (Connascence of Meaning)
    Description: Magic literal '100' should be extracted to constant
    Code: if threshold > 100:
    Fix: MAX_THRESHOLD = 100
    NASA Rule: Violates Rule 5 (Data hiding)

[4] Recursive Function - HIGH SEVERITY (Weight: 4.2)
    File: src/tree_processor.py:89
    Rule: CON_CoA (Connascence of Algorithm)
    Description: Recursive function without depth limit
    Code: def process_tree(node):
    Fix: Add maximum depth check
    NASA Rule: Violates Rule 9 (Be selective with recursion)

[5] Unchecked Return Value - HIGH SEVERITY (Weight: 3.8)
    File: src/database.py:156
    Rule: CON_CoA (Connascence of Algorithm)
    Description: Function return value not checked
    Code: database.execute(query)
    Fix: Check return value and handle errors
    NASA Rule: Violates Rule 6 (Check return values)

-----------------------------------------------------------------------------
                              AUTOFIX SUMMARY
-----------------------------------------------------------------------------

Autofix Opportunities: 15 violations can be automatically fixed
  High Confidence (85%+): 8 fixes
  Medium Confidence (70-84%): 5 fixes
  Low Confidence (<70%): 2 fixes

Estimated Fix Time: 45 minutes

To apply fixes:
  connascence autofix --confidence-threshold 85 src/
  connascence autofix --dry-run --show-diff src/  # Preview changes

-----------------------------------------------------------------------------
                          NASA COMPLIANCE DETAILS
-----------------------------------------------------------------------------

Rule 1: Avoid complex flow constructs          [FAILED] 2 violations
Rule 2: Fixed upper bound on loops             [PASSED] 0 violations
Rule 3: No dynamic memory allocation           [FAILED] 1 violation
Rule 4: Limit function size                    [FAILED] 3 violations
Rule 5: Data hiding                           [FAILED] 5 violations
Rule 6: Check return values                   [PASSED] 0 violations
Rule 7: Limit preprocessor use               [PASSED] 0 violations
Rule 8: Restrict function pointers           [FAILED] 1 violation
Rule 9: Be selective with recursion          [PASSED] 0 violations
Rule 10: Test assertions                     [FAILED] 2 violations

Overall Compliance: 70.0%

-----------------------------------------------------------------------------
                           PERFORMANCE METRICS
-----------------------------------------------------------------------------

Analysis Speed: 8,734 lines/second
Memory Usage: 156 MB peak
CPU Usage: 23.4% average
File Processing Rate: 24.3 files/second

-----------------------------------------------------------------------------
                             RECOMMENDATIONS
-----------------------------------------------------------------------------

Immediate Actions (High Priority):
  1. Refactor OrderProcessor class - split into 3-4 smaller classes
  2. Fix parameter bombs - convert to keyword-only parameters
  3. Extract magic literals - create constants module

Medium Term (This Sprint):
  1. Add missing type hints - improve type safety
  2. NASA compliance improvements - address rules 1, 3, 4, 5, 8, 10
  3. Connascence budget management - target <80% usage

-----------------------------------------------------------------------------
                               NEXT STEPS
-----------------------------------------------------------------------------

1. Apply high-confidence autofix suggestions
2. Manual review of medium-confidence fixes
3. Refactor high-weight violations
4. Schedule follow-up analysis in 1 week

For detailed analysis: connascence scan --format json --output full-report.json
For web dashboard: https://dashboard.connascence.io

=============================================================================
                       Analysis Complete - Review Required
=============================================================================
```

#### Text Usage Examples

```bash
# Generate text report
connascence scan --format text src/

# Save to file
connascence scan --format text --output report.txt src/

# Use in CI/CD pipeline
connascence scan --format text --quiet src/ || exit 1

# Email report
connascence scan --format text src/ | mail -s "Code Analysis" team@company.com
```

## Report Customization

### Configuration Options

```yaml
# .connascence.yml
reporting:
  formats:
    sarif:
      include_fixes: true
      include_nasa_compliance: true
      schema_version: "2.1.0"
    
    json:
      include_metadata: true
      include_performance_metrics: true
      pretty_print: true
    
    markdown:
      include_charts: true
      include_autofix_preview: true
      max_violations_shown: 50
      show_code_snippets: true
    
    text:
      width: 80
      show_progress: true
      color_output: auto
      summary_only: false

  output:
    directory: "./reports"
    filename_template: "connascence-{timestamp}-{format}"
    archive_reports: true
    max_archived_reports: 10
```

### Template Customization

#### Custom Markdown Template

```python
# custom_markdown_template.py
from reporting.md_summary import MarkdownReporter

class CustomMarkdownReporter(MarkdownReporter):
    def _generate_header(self, metadata):
        return f"""
# {metadata.get('project_name', 'Project')} Analysis Report

**Team**: {metadata.get('team', 'Development Team')}
**Sprint**: {metadata.get('sprint', 'Current Sprint')}
**Generated**: {metadata['timestamp']}
        """
    
    def _generate_summary_section(self, summary):
        # Custom summary with team-specific metrics
        return super()._generate_summary_section(summary) + \
               self._add_team_metrics(summary)
```

#### Custom SARIF Rules

```python
# custom_sarif_rules.py
from reporting.sarif_export import SARIFReporter

class CustomSARIFReporter(SARIFReporter):
    def _get_custom_rules(self):
        return [
            {
                "id": "TEAM_001",
                "name": "TeamSpecificRule",
                "shortDescription": {
                    "text": "Team-specific coding standard"
                },
                "properties": {
                    "team_rule": True,
                    "severity": "info"
                }
            }
        ]
```

## Integration Examples

### CI/CD Integration

#### GitHub Actions

```yaml
# .github/workflows/connascence-analysis.yml
name: Connascence Analysis

on: [push, pull_request]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Connascence Analysis
        run: |
          connascence scan \
            --format sarif \
            --output connascence.sarif \
            --format markdown \
            --output analysis-report.md \
            src/
      
      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: connascence.sarif
      
      - name: Comment on PR
        if: github.event_name == 'pull_request'
        run: |
          gh pr comment ${{ github.event.number }} \
            --body-file analysis-report.md
```

#### Jenkins Pipeline

```groovy
pipeline {
    agent any
    stages {
        stage('Connascence Analysis') {
            steps {
                sh '''
                    connascence scan \
                      --format json \
                      --output connascence-report.json \
                      --format text \
                      src/
                '''
                
                archiveArtifacts artifacts: 'connascence-report.json'
                
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: false,
                    keepAll: true,
                    reportDir: '.',
                    reportFiles: 'connascence-report.html',
                    reportName: 'Connascence Analysis Report'
                ])
            }
        }
    }
}
```

### IDE Integration

#### VS Code Settings

```json
{
  "connascence.reportFormat": "sarif",
  "connascence.autoAnalyze": true,
  "connascence.showInlineHints": true,
  "connascence.realTimeAnalysis": true
}
```

### API Integration

```python
# api_integration_example.py
import requests
import json
from pathlib import Path

def upload_analysis_results(report_file):
    """Upload analysis results to dashboard API."""
    with open(report_file) as f:
        report_data = json.load(f)
    
    response = requests.post(
        "https://api.connascence.io/v1/analysis",
        json=report_data,
        headers={"Authorization": f"Bearer {API_TOKEN}"}
    )
    
    return response.json()

# Usage
result = upload_analysis_results("connascence-report.json")
print(f"Analysis uploaded: {result['analysis_id']}")
```

## Report Storage and Archival

### Automated Archival

```python
# archival_script.py
from pathlib import Path
import shutil
from datetime import datetime, timedelta

def archive_old_reports(reports_dir="./reports", archive_dir="./reports-archive", days_to_keep=30):
    """Archive reports older than specified days."""
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    reports_path = Path(reports_dir)
    archive_path = Path(archive_dir)
    archive_path.mkdir(exist_ok=True)
    
    for report_file in reports_path.glob("connascence-*.{json,sarif,md,txt}"):
        if report_file.stat().st_mtime < cutoff_date.timestamp():
            shutil.move(str(report_file), str(archive_path / report_file.name))
            print(f"Archived: {report_file.name}")
```

### Report Comparison

```bash
# Compare reports over time
connascence compare \
  --baseline reports-archive/connascence-2024-08-01.json \
  --current reports/connascence-2024-09-01.json \
  --format markdown \
  --output trend-analysis.md
```

---

*Last Updated: September 2024*  
*Supported Formats: SARIF 2.1.0, JSON, Markdown, Text*  
*Schema Versions: See individual format specifications*