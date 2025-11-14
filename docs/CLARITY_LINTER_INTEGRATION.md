# Clarity Linter Integration & Dogfooding CI/CD

## Overview

This document describes the Clarity Linter integration and dogfooding CI/CD implementation for the Connascence Analyzer project.

**Status:** Production-Ready Implementation
**Created:** 2025-11-13
**Version:** 1.0.0

## Architecture

### Component Overview

```
connascence/
├── clarity_linter.yaml              # Complete YAML specification
├── quality_gate.config.yaml         # Progressive 6-week schedule
├── .github/workflows/
│   ├── self-analysis.yml           # PR quality gate automation
│   └── create-violation-issues.yml # Weekly violation tracking
├── analyzer/quality_gates/
│   ├── __init__.py
│   └── unified_quality_gate.py     # Unified analyzer orchestration
└── scripts/
    └── cleanup-scaffolding.sh      # Production cleanup script
```

## 1. Clarity Linter YAML Specification

**File:** `clarity_linter.yaml`

### Key Features

- **11 Rule Categories:** CLARITY001-CLARITY050
- **Language-Agnostic:** Supports Python, JavaScript, TypeScript, Java, Go, Rust, C++
- **NASA Mapping:** All rules mapped to NASA-STD-8739.8
- **Connascence Types:** Each rule annotated with connascence type
- **SARIF Output:** Full GitHub Code Scanning integration

### Rule Categories

1. **CLARITY001-010:** Function & Method Clarity
   - Function length, complexity, nesting, parameters, documentation

2. **CLARITY011-020:** Naming & Semantics
   - Variable names, magic numbers, naming consistency, semantic correctness

3. **CLARITY021-030:** Code Structure & Organization
   - God objects, file length, circular dependencies, coupling, abstraction

4. **CLARITY031-040:** Error Handling & Edge Cases
   - Error handling, exceptions, null safety, promise handling

5. **CLARITY041-050:** Testing & Quality Assurance
   - Test coverage, edge cases, flaky tests, test isolation

### Configuration

```yaml
config:
  severity_levels:
    critical: 90      # Block PR/CI
    high: 70          # Warning with fix required
    medium: 50        # Warning
    low: 30           # Info
    info: 0           # Informational only
```

### Usage

```bash
# Run Clarity Linter
python -m clarity_linter \
  --config clarity_linter.yaml \
  --output-format sarif \
  --output-file clarity_results.sarif \
  --fail-on high
```

## 2. GitHub Actions Workflows

### 2.1 Self-Analysis Workflow

**File:** `.github/workflows/self-analysis.yml`

#### Trigger Events
- Pull requests to `main` or `develop`
- Pushes to `main`
- Manual dispatch

#### Steps

1. **Run Clarity Linter:** Analyze code for clarity violations
2. **Run Connascence Analysis:** Detect coupling patterns
3. **Run NASA Standards:** Check compliance with NASA-STD-8739.8
4. **Merge SARIF:** Combine results from all analyzers
5. **Upload to Code Scanning:** GitHub Security tab integration
6. **Generate Report:** Markdown summary with top violations
7. **Post PR Comment:** Automated feedback on pull requests
8. **Quality Gate Check:** Pass/fail based on violation thresholds

#### Quality Gate Logic

```python
# Fail if critical or high violations detected
if critical > 0 or high > 0:
    exit(1)  # Quality gate failed
else:
    exit(0)  # Quality gate passed
```

### 2.2 Violation Issue Creation Workflow

**File:** `.github/workflows/create-violation-issues.yml`

#### Trigger Events
- Weekly schedule: Every Monday at 2 AM UTC
- Manual dispatch with severity threshold

#### Features

1. **Automated Scanning:** Weekly full project scan
2. **Issue Grouping:** Group violations by file and rule
3. **Duplicate Detection:** Skip existing open issues
4. **Auto-Labeling:** Severity and category labels
5. **Fix Suggestions:** Include actionable remediation steps
6. **Summary Issue:** Weekly rollup with statistics

#### Issue Template

Each violation issue includes:
- File path and line number
- Rule ID and description
- Severity and category
- Code snippets (up to 10 occurrences)
- Suggested fix
- NASA standard mapping
- Connascence type

## 3. Progressive Quality Gate Configuration

**File:** `quality_gate.config.yaml`

### 6-Week Dogfooding Schedule

```
Week 1: Baseline & Critical Only
  fail_on: critical
  max_critical: 0
  Focus: Establish baseline, block critical

Week 2: High Severity Enforcement
  fail_on: high
  max_critical: 0, max_high: 5
  Focus: High violations, NASA checks

Week 3: Medium Severity + NASA Compliance
  fail_on: medium
  max_critical: 0, max_high: 0, max_medium: 10
  Focus: Medium violations, full NASA standards

Week 4: Testing & Coverage
  fail_on: medium
  min_test_coverage: 80%, min_branch_coverage: 75%
  Focus: Test quality and coverage

Week 5: Full Enforcement
  fail_on: any
  max_critical: 0, max_high: 0, max_medium: 0, max_low: 20
  Focus: All rules, strict thresholds

Week 6: Production Ready
  fail_on: any
  max_critical: 0, max_high: 0, max_medium: 0, max_low: 0
  Focus: Zero violations, 90% coverage
```

### Configuration Structure

```yaml
schedule:
  week_N:
    name: "Phase Name"
    fail_on: critical|high|medium|low|any
    analyzers:
      clarity_linter: true
      connascence_analyzer: true
      nasa_standards: true
    thresholds:
      max_critical: N
      max_high: N
      max_medium: N
      max_low: N
      min_test_coverage: N%
    actions:
      create_issues: true
      block_pr: true
      require_fixes: true
```

## 4. Unified Quality Gate

**File:** `analyzer/quality_gates/unified_quality_gate.py`

### Architecture

```python
class UnifiedQualityGate:
    """
    Orchestrates multiple analyzers:
    - Clarity Linter
    - Connascence Analyzer
    - NASA Standards Checker
    """

    def analyze_project(path, fail_on, output_format):
        # Run all enabled analyzers
        # Calculate metrics and scores
        # Export results
        pass
```

### Features

1. **Multi-Analyzer Integration:** Runs Clarity, Connascence, NASA checks
2. **Unified Scoring:** Weighted average of all analyzer scores
3. **Multiple Output Formats:** JSON, SARIF, Markdown
4. **Configurable Thresholds:** Per-severity and per-analyzer limits
5. **Quality Gate Logic:** Pass/fail based on progressive schedule

### Scoring Algorithm

```
Overall Score = (Clarity * 0.4) + (Connascence * 0.3) + (NASA * 0.3)

Base: 100 points
Penalties:
  - Critical: -10 points each
  - High: -5 points each
  - Medium: -2 points each
  - Low: -1 point each
```

### Usage

```python
from analyzer.quality_gates import UnifiedQualityGate

gate = UnifiedQualityGate(config_path="quality_gate.config.yaml")
results = gate.analyze_project(
    project_path=".",
    fail_on="high",
    output_format="sarif"
)

gate.export_sarif("results.sarif")
gate.export_json("results.json")
gate.export_markdown("results.md")
```

### CLI Usage

```bash
python -m analyzer.quality_gates.unified_quality_gate \
  . \
  --config quality_gate.config.yaml \
  --fail-on high \
  --output-format sarif \
  --output-file results.sarif \
  --verbose
```

## 5. Cleanup Scaffolding Script

**File:** `scripts/cleanup-scaffolding.sh`

### Purpose

Transition project from development scaffolding to production structure.

### Actions

1. **Move Content:** Migrate `.claude/` and `.claude-flow/` to `docs/development/`
2. **Archive:** Create timestamped tar.gz backup
3. **Delete Scaffolding:** Remove development directories
4. **Update .gitignore:** Remove obsolete entries
5. **Generate Documentation:** Create migration guides

### Usage

```bash
cd /c/Users/17175/Desktop/connascence
./scripts/cleanup-scaffolding.sh
```

### Interactive Confirmation

Script prompts before deletion:
```
This will DELETE the following directories:
  - .claude
  - .claude-flow

Content has been backed up to docs/archive/scaffolding_archive_20251113_120000.tar.gz

Continue with deletion? (y/N):
```

### Output Files

- `docs/archive/scaffolding_archive_*.tar.gz` - Full backup
- `docs/archive/CLEANUP_SUMMARY.md` - Cleanup documentation
- `docs/MIGRATION_FROM_SCAFFOLDING.md` - Migration guide

## Integration Flow

### Development Workflow

```
1. Developer creates PR
2. GitHub Actions trigger self-analysis.yml
3. Run all analyzers (Clarity, Connascence, NASA)
4. Merge SARIF results
5. Upload to GitHub Code Scanning
6. Generate quality report
7. Post PR comment with findings
8. Quality gate check: PASS or FAIL
9. Block merge if violations exceed threshold
```

### Weekly Maintenance

```
1. Scheduled workflow runs Monday 2 AM UTC
2. Full project scan with all analyzers
3. Group violations by file and rule
4. Create GitHub issues for new violations
5. Skip duplicate issues (check existing open issues)
6. Auto-label by severity and category
7. Create summary issue with statistics
8. Upload scan results as artifacts
```

### Progressive Enforcement

```
Week 1 → Week 2 → Week 3 → Week 4 → Week 5 → Week 6
Critical  High     Medium   Testing  Full     Zero
  ↓         ↓         ↓        ↓       ↓        ↓
Block    Block    Block    Block   Block    Block
Critical Critical Critical Medium   All      All
                   +NASA   +Cover  +Low    +Zero
```

## Metrics & Reporting

### Key Metrics

1. **Violation Counts:** By severity, category, analyzer
2. **Quality Scores:** Clarity, Connascence, NASA, Overall (0-100)
3. **Test Coverage:** Line and branch coverage percentages
4. **NASA Compliance:** Percentage compliance with NASA-STD-8739.8
5. **Trend Analysis:** Historical data tracking improvement

### Report Formats

1. **SARIF:** GitHub Code Scanning integration
2. **JSON:** Machine-readable for tooling
3. **Markdown:** Human-readable PR comments
4. **HTML:** Visual dashboard reports

### GitHub Integration

- **Code Scanning Tab:** View violations in Security tab
- **PR Comments:** Automated feedback on pull requests
- **Check Runs:** Pass/fail status checks
- **Issue Tracking:** Auto-created issues with labels
- **Artifacts:** Downloadable reports for 30-90 days

## Success Criteria

### Week 1: Baseline & Critical Only
- Zero critical violations
- Baseline established

### Week 2: High Severity Enforcement
- Zero critical violations
- High violations under threshold (≤5)
- NASA checks passing

### Week 3: Medium Severity + NASA Compliance
- Zero critical and high violations
- Medium violations under threshold (≤10)
- NASA compliance ≥70%

### Week 4: Testing & Coverage
- Zero critical, high violations
- Test coverage ≥80%
- Branch coverage ≥75%

### Week 5: Full Enforcement
- Zero critical, high, medium violations
- Test coverage ≥85%
- Documentation complete
- NASA compliance ≥90%

### Week 6: Production Ready
- Zero violations (all severities)
- Test coverage ≥90%
- NASA compliance ≥95%
- Production readiness checklist complete

## Next Steps

1. **Install Dependencies:** `pip install -r requirements.txt`
2. **Test Workflows:** Create test PR to trigger self-analysis
3. **Monitor Weekly Issues:** Review auto-created violation issues
4. **Track Progress:** Monitor quality gate progression week-by-week
5. **Adjust Thresholds:** Tune configuration based on baseline results
6. **Production Cleanup:** Run `cleanup-scaffolding.sh` after Week 6

## References

- **Clarity Linter Spec:** `clarity_linter.yaml`
- **Quality Gate Config:** `quality_gate.config.yaml`
- **Unified Gate Code:** `analyzer/quality_gates/unified_quality_gate.py`
- **Self-Analysis Workflow:** `.github/workflows/self-analysis.yml`
- **Issue Creation Workflow:** `.github/workflows/create-violation-issues.yml`

## Support

For issues or questions, refer to:
- Project documentation in `docs/`
- GitHub Actions workflow logs
- Quality gate artifacts in CI runs
