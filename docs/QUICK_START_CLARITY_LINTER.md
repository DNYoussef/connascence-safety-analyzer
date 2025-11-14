# Clarity Linter Quick Start Guide

**5-Minute Setup | Production-Ready Implementation**

## Files Created

```
connascence/
├── clarity_linter.yaml                    # 17 KB - Complete rule spec
├── quality_gate.config.yaml               # 9.3 KB - 6-week schedule
├── CLARITY_INTEGRATION_COMPLETE.md        # 14 KB - Full summary
├── .github/workflows/
│   ├── self-analysis.yml                 # 9.6 KB - PR automation
│   └── create-violation-issues.yml       # 12 KB - Weekly scans
├── analyzer/quality_gates/
│   ├── __init__.py                       # 279 B
│   └── unified_quality_gate.py           # 19 KB - Orchestrator
├── scripts/
│   └── cleanup-scaffolding.sh            # 11 KB - Production cleanup
└── docs/
    ├── CLARITY_LINTER_INTEGRATION.md     # 12 KB - Full guide
    └── QUICK_START_CLARITY_LINTER.md     # This file
```

## Instant Usage

### 1. Test PR Quality Gate (30 seconds)

```bash
cd /c/Users/17175/Desktop/connascence

# Create test PR
git checkout -b test/quality-gate
git commit --allow-empty -m "test: trigger clarity linter"
git push origin test/quality-gate

# Wait for GitHub Actions to run
# Check: https://github.com/YOUR_REPO/actions
```

### 2. Run Locally (1 minute)

```bash
# Install dependencies (if needed)
pip install pyyaml

# Run unified quality gate
python -m analyzer.quality_gates.unified_quality_gate \
  . \
  --config quality_gate.config.yaml \
  --fail-on high \
  --output-format json \
  --output-file results.json \
  --verbose

# View results
cat results.json | python -m json.tool
```

### 3. Manual Weekly Scan (30 seconds)

```bash
# Trigger violation issue creation
gh workflow run create-violation-issues.yml \
  --field severity_threshold=high

# Check: https://github.com/YOUR_REPO/issues?q=label:quality-gate
```

## Key Features at a Glance

### 11 Rule Categories (CLARITY001-050)

```
CLARITY001-010: Function & Method Clarity
  001: Function length >50 lines
  002: Complexity >10
  004: Parameters >6

CLARITY011-020: Naming & Semantics
  011: Unclear variable names
  012: Magic numbers
  014: Misleading function names

CLARITY021-030: Code Structure
  021: God Object >15 methods
  023: Circular dependencies
  024: High coupling

CLARITY031-040: Error Handling
  031: Missing error handling
  032: Swallowed exceptions
  034: Unhandled promises

CLARITY041-050: Testing
  041: Missing unit tests
  042: Low coverage <80%
  044: Flaky tests
```

### 6-Week Progressive Schedule

```
Week 1: Baseline (fail_on: critical)
Week 2: High Severity (fail_on: high, max_high: 5)
Week 3: Medium + NASA (fail_on: medium, max_medium: 10)
Week 4: Testing (min_coverage: 80%)
Week 5: Full Enforcement (max_low: 20)
Week 6: Zero Violations (production ready)
```

### GitHub Integration

```
PR Quality Gate:
  - Runs on every PR
  - Posts comments with findings
  - Uploads SARIF to Code Scanning
  - Blocks merge if violations

Weekly Issues:
  - Runs Monday 2 AM UTC
  - Creates issues for violations
  - Groups by file and rule
  - Auto-labels by severity
```

## Quick Commands

```bash
# View current week configuration
yq '.schedule.week_1' quality_gate.config.yaml

# List all rules
yq '.rules | keys' clarity_linter.yaml

# Check workflow status
gh workflow list

# View recent workflow runs
gh run list --workflow=self-analysis.yml --limit 5

# Download workflow artifacts
gh run download RUN_ID

# List auto-created issues
gh issue list --label quality-gate --limit 10

# View Code Scanning alerts
gh api repos/:owner/:repo/code-scanning/alerts
```

## Scoring System

```
Overall Score = (Clarity * 0.4) + (Connascence * 0.3) + (NASA * 0.3)

Base: 100 points
Penalties:
  Critical: -10 points each
  High: -5 points each
  Medium: -2 points each
  Low: -1 point each

Example:
  2 critical + 5 high = 100 - (2*10) - (5*5) = 55/100
```

## Common Workflows

### Fix Critical Violations

```bash
# 1. View violations
gh api repos/:owner/:repo/code-scanning/alerts \
  --jq '.[] | select(.rule.security_severity_level=="critical")'

# 2. Create fix branch
git checkout -b fix/critical-violations

# 3. Fix and commit
git commit -am "fix: resolve critical violations"

# 4. Create PR (will auto-check)
gh pr create --title "Fix critical violations"
```

### Monitor Progress

```bash
# View violation trends
gh run list --workflow=self-analysis.yml --json conclusion,createdAt | \
  jq -r '.[] | "\(.createdAt): \(.conclusion)"'

# Check current quality scores
python -c "
import json
from pathlib import Path
results = json.loads(Path('results.json').read_text())
print(f'Overall: {results[\"scores\"][\"overall\"]:.2f}/100')
"
```

### Production Cleanup (Week 6)

```bash
# After reaching Week 6 success criteria
./scripts/cleanup-scaffolding.sh

# Review archived content
ls -lh docs/archive/

# Commit cleanup
git add .
git commit -m "chore: production cleanup - remove scaffolding"
```

## Troubleshooting

### Workflow Not Triggering

```bash
# Check workflow file syntax
yq .github/workflows/self-analysis.yml > /dev/null

# Verify push succeeded
git push -v

# Check workflow permissions
gh api repos/:owner/:repo/actions/permissions
```

### High Violation Count

```bash
# Generate exemptions for legacy code
cat >> quality_gate.config.yaml << 'EOF'
exemptions:
  temporary:
    - rule: CLARITY021
      files: ["legacy_system.py"]
      expires: "2025-12-31"
      reason: "Legacy code scheduled for refactor"
EOF
```

### Test Coverage Below Threshold

```bash
# Run coverage analysis
pytest --cov=. --cov-report=html

# Open report
open htmlcov/index.html

# Add tests for uncovered lines
# (check htmlcov/index.html for details)
```

## Success Indicators

- [ ] PR quality gate runs on every PR
- [ ] Code Scanning shows violations in Security tab
- [ ] Weekly issues auto-created on Mondays
- [ ] PR comments show quality metrics
- [ ] Quality score trending upward
- [ ] Zero critical violations by Week 2
- [ ] 80%+ test coverage by Week 4
- [ ] Zero violations by Week 6

## Next Steps

1. **Read Full Guide:** `docs/CLARITY_LINTER_INTEGRATION.md`
2. **Review Summary:** `CLARITY_INTEGRATION_COMPLETE.md`
3. **Check Configuration:** `clarity_linter.yaml`
4. **Monitor Workflows:** GitHub Actions tab
5. **Track Issues:** GitHub Issues with `quality-gate` label

## Support

- **GitHub Actions Logs:** View workflow run details
- **Code Scanning:** Security tab for SARIF results
- **Issues:** Auto-created with `quality-gate` label
- **Documentation:** `docs/CLARITY_LINTER_INTEGRATION.md`

## Examples

### Example PR Comment

```markdown
# Quality Gate Report
**Generated:** 2025-11-13T12:00:00Z

## Summary

### Clarity Linter
- **Total Violations:** 8
- **Critical:** 0
- **High:** 2
- **Medium:** 4
- **Low:** 2

### Top 10 Clarity Violations

1. CLARITY001: Function exceeds maximum length
   - File: example.py:42
   - Fix: Break into smaller functions

2. CLARITY021: God Object detected
   - File: module.py:10
   - Fix: Split class following SRP
```

### Example Weekly Issue

```markdown
# [Quality] CLARITY001: Function Length Violation in example.py

**File:** example.py
**Rule:** CLARITY001
**Severity:** high
**Occurrences:** 3

## Description
Functions should be concise and focused (max 50 lines)

## Violations

### 1. Line 42
(code snippet)

### 2. Line 158
(code snippet)

## Suggested Fix
Break large function into smaller, focused functions

## NASA Mapping
NASA-STD-8739.8 Section 4.2.1
```

---

**Status:** READY FOR USE
**Time to Deploy:** <5 minutes
**Maintenance:** Automated via GitHub Actions
