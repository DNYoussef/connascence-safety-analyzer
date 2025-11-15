# Root Cause Analysis Plan - 6 Failing Workflows

**Date**: 2025-11-15
**Objective**: Systematically diagnose and fix 6 failing GitHub Actions workflows
**Approach**: SPARC methodology with specialized agents and skills
**Expected Duration**: 4-8 hours (depending on complexity)

---

## Phase 1: Reconnaissance & Analysis (1-2 hours)

### Step 1.1: Intent Analysis & Planning
**Skill**: `intent-analyzer` + `planner`
**Objective**: Understand failure patterns and create systematic investigation plan

**Actions**:
```javascript
[Single Message - Parallel Intent Analysis]:
  Skill("intent-analyzer")  // Analyze underlying issues
  Task("Planner", "Create systematic RCA plan for 6 workflows", "planner")
  Task("Researcher", "Gather workflow logs and error patterns", "researcher")

  TodoWrite({ todos: [
    {content: "Analyze all 6 workflow failure logs", status: "pending"},
    {content: "Identify common failure patterns", status: "pending"},
    {content: "Categorize by root cause type", status: "pending"},
    {content: "Prioritize by severity and dependencies", status: "pending"}
  ]})
```

### Step 1.2: Download and Analyze Workflow Logs
**Tools**: `gh run view --log`, `gh workflow list`
**Agents**: `researcher`, `code-analyzer`

**Workflows to Investigate**:
1. Quality Gates / Code Quality Analysis
2. Quality Gates / Dependency Security Audit
3. Quality Gates / Generate Metrics Dashboard
4. Self-Analysis Quality Gate / Quality Gate Analysis
5. Quality Gates / Security Scanning
6. Quality Gates / Test Coverage Analysis

**Commands**:
```bash
# Get recent run IDs for each workflow
gh run list --workflow=code-quality.yml --limit 3
gh run list --workflow=dependency-audit.yml --limit 3
gh run list --workflow=metrics-dashboard.yml --limit 3
gh run list --workflow=self-analysis-quality-gate.yml --limit 3
gh run list --workflow=security-scan.yml --limit 3
gh run list --workflow=test-coverage.yml --limit 3

# Download logs for failed runs
gh run view <run_id> --log > logs/workflow_<name>_failure.log
```

---

## Phase 2: Root Cause Analysis (2-3 hours)

### Step 2.1: Systematic Debugging
**Skill**: `root-cause-analyzer` (quality-analysis agent)
**Agents**: `root-cause-analyzer`, `code-analyzer`, `analyst`

**Analysis Pattern**:
```javascript
[Single Message - Parallel RCA]:
  Task("Root Cause Analyzer", "Analyze Code Quality workflow failures", "root-cause-analyzer")
  Task("Security Analyst", "Analyze security-related workflow failures", "security-testing-agent")
  Task("Code Analyzer", "Analyze dashboard and metrics workflows", "code-analyzer")

  TodoWrite({ todos: [
    {content: "RCA: Code Quality Analysis workflow", status: "in_progress"},
    {content: "RCA: Dependency Security Audit workflow", status: "pending"},
    {content: "RCA: Generate Metrics Dashboard workflow", status: "pending"},
    {content: "RCA: Self-Analysis Quality Gate workflow", status: "pending"},
    {content: "RCA: Security Scanning workflow", status: "pending"},
    {content: "RCA: Test Coverage Analysis workflow", status: "pending"}
  ]})
```

### Step 2.2: Categorize Root Causes
**Expected Root Cause Categories**:
- **Configuration Issues**: Missing environment variables, wrong paths, incorrect settings
- **Dependency Issues**: Missing packages, version conflicts, broken dependencies
- **Code Issues**: Bugs in analyzer scripts, API changes, breaking changes
- **Infrastructure Issues**: GitHub Actions runner issues, timeout problems
- **Integration Issues**: Cross-workflow dependencies, artifact dependencies

---

## Phase 3: Workflow-Specific Investigation

### Workflow 1: Code Quality Analysis
**Likely Issues**:
- Linter configuration errors
- Missing code quality tools (ESLint, Pylint, etc.)
- Threshold violations triggering failures

**Investigation Commands**:
```bash
gh run view <run_id> --log | grep -i "error\|fail\|exception"
```

**Skills to Use**: `clarity-linter`, `code-analyzer`

### Workflow 2: Dependency Security Audit
**Likely Issues**:
- Vulnerable dependencies detected
- `npm audit` or `pip-audit` failures
- Security threshold violations

**Investigation Commands**:
```bash
gh run view <run_id> --log | grep -i "vulnerability\|CVE\|critical"
```

**Skills to Use**: `security-testing-agent`

### Workflow 3: Generate Metrics Dashboard
**Likely Issues**:
- Missing input files (metrics JSON)
- Dashboard generation script errors
- Template or dependency issues

**Investigation Commands**:
```bash
gh run view <run_id> --log | grep -i "dashboard\|metrics\|template"
```

**Skills to Use**: `planner`, `code-analyzer`

### Workflow 4: Self-Analysis Quality Gate
**Likely Issues**:
- Different from Self-Dogfooding workflow (which we fixed)
- Quality gate threshold violations
- Missing analysis results

**Investigation Commands**:
```bash
gh run view <run_id> --log | grep -i "quality gate\|threshold\|violation"
```

**Skills to Use**: `quality-audit-production-readiness-checker`

### Workflow 5: Security Scanning
**Likely Issues**:
- Bandit, Safety, or other security tool failures
- High-severity findings
- Configuration issues

**Investigation Commands**:
```bash
gh run view <run_id> --log | grep -i "bandit\|safety\|security"
```

**Skills to Use**: `security-testing-agent`

### Workflow 6: Test Coverage Analysis
**Likely Issues**:
- Coverage below threshold
- pytest or unittest failures
- Coverage report generation errors

**Investigation Commands**:
```bash
gh run view <run_id> --log | grep -i "coverage\|pytest\|test"
```

**Skills to Use**: `tester`, `production-validator`

---

## Phase 4: Fix Implementation (2-4 hours)

### Step 4.1: Prioritization
**Priority Order** (based on dependencies and severity):
1. **HIGH**: Dependency Security Audit (blocks deployment)
2. **HIGH**: Security Scanning (blocks deployment)
3. **MEDIUM**: Code Quality Analysis (blocks merge)
4. **MEDIUM**: Test Coverage Analysis (quality metric)
5. **LOW**: Generate Metrics Dashboard (reporting only)
6. **LOW**: Self-Analysis Quality Gate (self-assessment)

### Step 4.2: Parallel Fix Implementation
**Skill**: `cicd-intelligent-recovery` (Loop 3 of Three-Loop System)
**Agents**: `coder`, `tester`, `reviewer`, `cicd-engineer`

**Fix Pattern**:
```javascript
[Single Message - Parallel Fixes]:
  Task("CI/CD Engineer", "Fix Dependency Security Audit workflow", "cicd-engineer")
  Task("Security Specialist", "Fix Security Scanning workflow", "security-testing-agent")
  Task("Code Analyzer", "Fix Code Quality Analysis workflow", "code-analyzer")
  Task("Tester", "Fix Test Coverage Analysis workflow", "tester")
  Task("DevOps", "Fix Metrics Dashboard workflow", "cicd-engineer")
  Task("Reviewer", "Fix Self-Analysis Quality Gate workflow", "reviewer")

  TodoWrite({ todos: [
    {content: "Fix and test Dependency Security Audit", status: "in_progress"},
    {content: "Fix and test Security Scanning", status: "pending"},
    {content: "Fix and test Code Quality Analysis", status: "pending"},
    {content: "Fix and test Test Coverage", status: "pending"},
    {content: "Fix and test Metrics Dashboard", status: "pending"},
    {content: "Fix and test Self-Analysis Quality Gate", status: "pending"},
    {content: "Trigger all workflows and validate", status: "pending"},
    {content: "Document all fixes", status: "pending"}
  ]})
```

---

## Phase 5: Validation & Testing (1 hour)

### Step 5.1: Sequential Workflow Testing
**Objective**: Validate each fix works independently and together

**Testing Commands**:
```bash
# Trigger each workflow manually
gh workflow run code-quality.yml
gh workflow run dependency-audit.yml
gh workflow run security-scan.yml
gh workflow run test-coverage.yml
gh workflow run metrics-dashboard.yml
gh workflow run self-analysis-quality-gate.yml

# Monitor results
gh run watch
```

### Step 5.2: Integration Testing
**Skill**: `production-validator`
**Objective**: Ensure all workflows pass on a real push

**Actions**:
1. Create a test commit with documentation update
2. Push to trigger all workflows
3. Monitor all workflow runs
4. Validate 6/6 pass (or identify remaining issues)

---

## Success Criteria

### Phase Completion:
- [ ] All 6 workflow logs downloaded and analyzed
- [ ] Root causes identified for each workflow
- [ ] Fixes implemented and tested individually
- [ ] All workflows passing on test push
- [ ] Documentation updated with fixes

### Final Metrics:
- **Before**: 6 failing workflows
- **Target**: 0 failing workflows (100% pass rate)
- **Stretch Goal**: Improve workflow performance and reliability

---

## Execution Strategy

### Recommended Approach:
1. **Start with reconnaissance** (Phase 1) - understand all failures first
2. **Systematic RCA** (Phase 2) - categorize and prioritize
3. **Parallel investigation** (Phase 3) - use multiple agents concurrently
4. **Sequential fixes** (Phase 4) - fix by priority order
5. **Comprehensive validation** (Phase 5) - ensure no regressions

### Skills to Invoke:
```javascript
// Initial analysis
Skill("intent-analyzer")
Skill("root-cause-analyzer")

// Domain-specific analysis
Skill("clarity-linter")  // For code quality issues
Skill("security-testing-agent")  // For security issues
Skill("cicd-intelligent-recovery")  // For CI/CD fixes
Skill("production-validator")  // For final validation
```

### Agents to Spawn (in order of usage):
1. `planner` - Create systematic plan
2. `researcher` - Gather logs and evidence
3. `root-cause-analyzer` - Identify root causes
4. `code-analyzer` - Analyze code-related issues
5. `security-testing-agent` - Fix security workflows
6. `cicd-engineer` - Fix CI/CD configurations
7. `tester` - Fix test coverage workflow
8. `reviewer` - Final review and validation
9. `production-validator` - Ensure production readiness

---

## Next Steps

**To Execute This Plan**:
1. Read this plan thoroughly
2. Invoke `Skill("intent-analyzer")` to confirm approach
3. Begin Phase 1 with log collection
4. Use `root-cause-analyzer` agent for systematic debugging
5. Follow priority order for fixes
6. Validate with comprehensive testing

**Estimated Timeline**:
- Phase 1: 1-2 hours
- Phase 2: 2-3 hours
- Phase 3: Parallel with Phase 2
- Phase 4: 2-4 hours
- Phase 5: 1 hour
- **Total**: 6-10 hours (can be reduced with parallel execution)

**Expected Outcome**:
- All 6 failing workflows fixed
- Comprehensive documentation of issues and fixes
- Improved CI/CD reliability
- Ready for Phase 2 (if needed) or production deployment
