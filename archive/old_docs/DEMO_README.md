# Six Sigma + Theater Detection Demonstration

## Overview

This demonstration shows the **practical value** of combining Six Sigma quality metrics with Theater Detection validation by analyzing the **connascence codebase itself**.

## What It Does

The `demo_analysis.py` script performs a complete quality analysis workflow:

### Phase 1: Real Connascence Analysis
- Analyzes the analyzer codebase for actual connascence violations
- Detects NASA POT10 compliance issues
- Identifies code duplication patterns
- Produces real metrics from production code

### Phase 2: Six Sigma Quality Metrics
- Calculates DPMO (Defects Per Million Opportunities)
- Determines Sigma Level (industry standard quality measure)
- Computes CTQ (Critical to Quality) metrics
- Generates quality gate decisions

### Phase 3: Quality Claims Creation
- Creates realistic quality improvement claims
- Includes both legitimate and suspicious claims
- Demonstrates various theater patterns:
  - Perfect improvements (99.99%)
  - Round number improvements (exactly 50%)
  - Missing evidence
  - Vague measurement methods

### Phase 4: Theater Detection Validation
- Validates each claim for authenticity
- Calculates confidence scores
- Identifies theater indicators
- Assesses evidence quality

### Phase 5: Systemic Theater Analysis
- Analyzes patterns across multiple claims
- Detects coordinated theater attempts
- Identifies suspicious timing patterns
- Flags unrealistic consistency

### Phase 6: Comprehensive Reporting
- Executive summary with key findings
- Practical insights from real analysis
- Actionable recommendations
- Both JSON and Markdown reports

## Running the Demonstration

### Basic Usage
```bash
# Run on the analyzer directory (default)
python demo_analysis.py

# Analyze a specific path
python demo_analysis.py --path /path/to/code

# Custom output directory
python demo_analysis.py --output my_results
```

### What You'll See

```
================================================================================
CONNASCENCE SELF-ANALYSIS DEMONSTRATION
Six Sigma + Theater Detection on Real Codebase
================================================================================

PHASE 1: Analyzing Connascence Codebase...
--------------------------------------------------------------------------------
Analyzing path: analyzer
Files analyzed: 45
Total violations: 23
Critical violations: 2
...

PHASE 2: Applying Six Sigma Quality Metrics...
--------------------------------------------------------------------------------
Calculating Six Sigma metrics...
Sigma Level: 3.85
DPMO: 12,450
Quality Score: 0.82
...

PHASE 3: Creating Quality Improvement Claims...
--------------------------------------------------------------------------------
Creating quality improvement claims...
Created 5 quality claims (mix of legitimate and suspicious)
...

PHASE 4: Validating Claims with Theater Detection...
--------------------------------------------------------------------------------
Validating claims with theater detection...
  [PASS] demo_overall_001: Reduced overall connascence violations...
        Confidence: 75%, Risk: low
  [FAIL] demo_suspicious_003: Achieved perfect Six Sigma quality...
        Confidence: 15%, Risk: high
...

PHASE 5: Detecting Systemic Theater Patterns...
--------------------------------------------------------------------------------
Analyzing systemic theater patterns...
Systemic indicators found: 3
Overall risk: medium
...

PHASE 6: Generating Comprehensive Report...
--------------------------------------------------------------------------------
EXECUTIVE SUMMARY
-----------------
The connascence analyzer codebase was subjected to self-analysis...
...

DEMONSTRATION COMPLETE
Results saved to: demo_results
================================================================================
```

## Output Files

All results are saved to the `demo_results/` directory (or your specified output):

### Phase Results (JSON)
- `phase1_connascence_analysis.json` - Raw connascence violations
- `phase2_six_sigma_metrics.json` - Six Sigma calculations
- `phase3_quality_claims.json` - Generated quality claims
- `phase4_theater_validation.json` - Validation results
- `phase5_systemic_analysis.json` - Systemic theater patterns

### Final Reports
- `final_report.json` - Complete analysis in JSON format
- `final_report.md` - Human-readable markdown report

## Understanding the Results

### Legitimate Claims (High Confidence)
```json
{
  "claim_id": "demo_overall_001",
  "is_valid": true,
  "confidence_score": 0.75,
  "risk_level": "low",
  "evidence_quality": 0.80,
  "theater_indicators": []
}
```

**Why it passes:**
- Realistic improvement (33%)
- Comprehensive evidence files
- Detailed measurement method
- Appropriate timestamp

### Suspicious Claims (Low Confidence)
```json
{
  "claim_id": "demo_suspicious_003",
  "is_valid": false,
  "confidence_score": 0.15,
  "risk_level": "high",
  "evidence_quality": 0.0,
  "theater_indicators": [
    "perfect_improvement",
    "missing_evidence",
    "vague_method"
  ]
}
```

**Why it fails:**
- Perfect improvement (99.99%) - unrealistic
- No evidence files provided
- Vague measurement method
- Multiple red flags

## Practical Value Demonstrated

### 1. Real Code Analysis
- Analyzes actual production code (the analyzer itself)
- Finds genuine violations and quality issues
- Provides actionable metrics

### 2. Quality Quantification
- Six Sigma metrics provide industry-standard measures
- DPMO and Sigma Level track quality over time
- CTQ metrics identify critical areas

### 3. Theater Prevention
- Detects fake quality improvements automatically
- Prevents misleading reports from reaching stakeholders
- Validates evidence and measurement methods

### 4. Systemic Detection
- Identifies patterns across multiple claims
- Catches coordinated theater attempts
- Flags unrealistic consistency

### 5. Decision Support
- Quality gate decisions based on real metrics
- Risk assessment for each claim
- Actionable recommendations

## Integration Examples

### CI/CD Pipeline
```bash
# Run in CI/CD to validate quality claims
python demo_analysis.py --path . --output ci_results

# Check exit code
if [ $? -eq 0 ]; then
  echo "Quality validation passed"
else
  echo "Theater detected - quality claims suspicious"
  exit 1
fi
```

### Pull Request Validation
```bash
# Analyze changed files
git diff --name-only main | grep "\.py$" > changed_files.txt
python demo_analysis.py --path . --output pr_validation

# Validate improvement claims in PR description
# Theater detection will flag suspicious claims
```

### Quality Dashboard
```python
import json
from pathlib import Path

# Load results
with open('demo_results/final_report.json') as f:
    report = json.load(f)

# Extract metrics for dashboard
sigma_level = report['detailed_results']['six_sigma_metrics']['sigma_level']
theater_rate = report['detailed_results']['theater_detection']['summary']['invalid_claims']

# Update dashboard metrics
update_dashboard({
    'sigma_level': sigma_level,
    'theater_detection_rate': theater_rate,
    'timestamp': report['demonstration_metadata']['timestamp']
})
```

## Key Insights

1. **Self-Analysis Works**: The connascence analyzer successfully analyzes its own codebase, proving the tool works on real production code.

2. **Six Sigma Provides Context**: DPMO and Sigma Level give meaningful quality measurements that can be compared across projects and industries.

3. **Theater Detection Catches Fakes**: The system successfully identifies suspicious claims (perfect improvements, missing evidence) while validating legitimate ones.

4. **Evidence Matters**: Claims with comprehensive evidence and detailed methods receive higher confidence scores.

5. **Systemic Patterns Reveal Truth**: Analyzing multiple claims together reveals coordinated theater attempts that individual validation might miss.

## Next Steps

After running the demonstration:

1. Review the generated reports in `demo_results/`
2. Examine how theater detection identified suspicious claims
3. Note the difference in confidence scores between legitimate and fake claims
4. Integrate similar validation into your own quality processes

## Questions?

The demonstration shows both systems working together on **real code with real violations**. This isn't a toy example - it's production-ready quality validation that can prevent misleading quality reports.

For more details, see:
- `tests/test_sixsigma_theater_integration.py` - Integration tests
- `analyzer/enterprise/sixsigma/` - Six Sigma implementation
- `analyzer/theater_detection/` - Theater detection system