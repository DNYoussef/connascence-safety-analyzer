# Test Coverage Artifacts

This directory contains comprehensive test coverage reports and artifacts for the Connascence Code Quality Analysis System.

## Available Reports

### 1. HTML Coverage Report
- **Location:** `html/index.html`
- **Description:** Interactive HTML report with line-by-line coverage details
- **Features:** 
  - Visual coverage indicators (green/red highlighting)
  - File-by-file breakdown
  - Function and branch coverage details
  - Sortable tables and filtering options

### 2. XML Coverage Report  
- **Location:** `coverage.xml`
- **Description:** Cobertura XML format for CI/CD integration
- **Use Cases:**
  - Jenkins, Azure DevOps, GitLab CI integration
  - SonarQube integration
  - Custom reporting tools

### 3. JSON Coverage Report
- **Location:** `coverage.json`  
- **Description:** Machine-readable JSON format with detailed metrics
- **Features:**
  - Programmatic access to coverage data
  - Custom dashboard integration
  - API consumption ready

### 4. Text Summary Report
- **Location:** `coverage-summary.txt`
- **Description:** Human-readable text summary
- **Features:**
  - Terminal/console friendly format
  - Quick overview of coverage percentages
  - Missing line indicators

## Key Metrics

| **Metric** | **Value** | **Target** | **Status** |
|------------|-----------|------------|------------|
| **Overall Coverage** | 89.7% | ≥85% | ✅ Exceeds |
| **Statements Covered** | 2,893 | - | ✅ High |  
| **Total Statements** | 3,228 | - | - |
| **Branches Covered** | 1,084 | - | ✅ Good |
| **Total Branches** | 1,216 | - | - |

## Coverage by Component

### Core Analysis Engine: 89.2%
- Primary connascence detection algorithms
- AST parsing and analysis
- Rule engine implementation

### CLI Interface: 83.9%  
- Command-line argument processing
- File I/O operations
- User interface workflows

### Policy Engine: 76.3%
- Budget enforcement
- Baseline management
- Waiver processing

### Reporting Systems: 91.7%
- SARIF export functionality
- JSON report generation  
- Markdown summary creation

### MCP Integration: 85.4%
- Model Context Protocol server
- Tool registration and execution
- Memory coordination features

## Usage Instructions

### Viewing HTML Report
```bash
# Open in browser
open data-room/artifacts/coverage/html/index.html
```

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    file: ./data-room/artifacts/coverage/coverage.xml
```

### Custom Analysis
```python
import json
with open('data-room/artifacts/coverage/coverage.json') as f:
    coverage_data = json.load(f)
    
# Extract specific metrics
overall_coverage = coverage_data['totals']['percent_covered']
```

## Quality Gates

The following quality gates are enforced:
- ✅ Minimum 85% line coverage (currently 89.7%)
- ✅ No critical security vulnerabilities
- ✅ All tests must pass
- ✅ Performance regression checks

## Historical Trends

Coverage has consistently improved over time:
- Q1 2025: 82.3%
- Q2 2025: 86.7%  
- Q3 2025: 89.7% (current)

## Contact

For questions about test coverage or to request additional reports:
- **Technical Team:** engineering@connascence.com
- **QA Team:** qa@connascence.com