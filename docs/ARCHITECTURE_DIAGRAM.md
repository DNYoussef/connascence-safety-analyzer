# Clarity Linter Architecture Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLARITY LINTER SYSTEM                        │
│                         Production-Ready v1.0.0                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                       CONFIGURATION LAYER                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  clarity_linter.yaml                quality_gate.config.yaml        │
│  ┌──────────────────┐              ┌─────────────────────┐          │
│  │ 11 Rule Categories│              │ 6-Week Schedule     │          │
│  │ CLARITY001-050   │              │ Progressive Gates   │          │
│  │                  │              │                     │          │
│  │ - Function       │              │ Week 1: Critical    │          │
│  │ - Naming         │              │ Week 2: High        │          │
│  │ - Structure      │              │ Week 3: Medium      │          │
│  │ - Error Handling │              │ Week 4: Testing     │          │
│  │ - Testing        │              │ Week 5: Full        │          │
│  │                  │              │ Week 6: Zero        │          │
│  │ NASA Mappings    │              │                     │          │
│  │ Connascence Types│              │ Thresholds          │          │
│  │ Fix Suggestions  │              │ Analyzers           │          │
│  └──────────────────┘              └─────────────────────┘          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    UNIFIED QUALITY GATE CORE                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  analyzer/quality_gates/unified_quality_gate.py                     │
│  ┌─────────────────────────────────────────────────────────┐        │
│  │           UnifiedQualityGate Class                      │        │
│  │                                                         │        │
│  │  analyze_project()                                     │        │
│  │  ├── _run_clarity_linter()                            │        │
│  │  ├── _run_connascence_analyzer()                      │        │
│  │  ├── _run_nasa_standards()                            │        │
│  │  ├── _calculate_metrics()                             │        │
│  │  └── _calculate_scores()                              │        │
│  │                                                         │        │
│  │  Scoring: (Clarity*0.4) + (Connascence*0.3) + (NASA*0.3)│      │
│  │  Base: 100 points                                      │        │
│  │  Penalties: Critical(-10), High(-5), Medium(-2), Low(-1)│       │
│  │                                                         │        │
│  │  export_sarif()   export_json()   export_markdown()   │        │
│  └─────────────────────────────────────────────────────────┘        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
                ▼              ▼              ▼
    ┌───────────────┐  ┌──────────────┐  ┌─────────────┐
    │ CLARITY       │  │ CONNASCENCE  │  │ NASA        │
    │ LINTER        │  │ ANALYZER     │  │ STANDARDS   │
    └───────────────┘  └──────────────┘  └─────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      GITHUB AUTOMATION LAYER                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │                    PR Quality Gate                         │     │
│  │            .github/workflows/self-analysis.yml             │     │
│  │                                                            │     │
│  │  Triggers: PR to main/develop, Push to main              │     │
│  │                                                            │     │
│  │  1. Checkout code                                          │     │
│  │  2. Run Clarity Linter        ─┐                          │     │
│  │  3. Run Connascence Analyzer  ─┼─► Merge SARIF Results    │     │
│  │  4. Run NASA Standards        ─┘                          │     │
│  │  5. Upload to Code Scanning                               │     │
│  │  6. Generate Quality Report                               │     │
│  │  7. Post PR Comment                                        │     │
│  │  8. Create Check Run                                       │     │
│  │  9. Quality Gate: PASS/FAIL                               │     │
│  │                                                            │     │
│  │  Fail if: critical > 0 OR high > 0                        │     │
│  └────────────────────────────────────────────────────────────┘     │
│                               │                                     │
│                               ▼                                     │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │               Weekly Violation Tracking                    │     │
│  │       .github/workflows/create-violation-issues.yml        │     │
│  │                                                            │     │
│  │  Schedule: Every Monday 2 AM UTC                           │     │
│  │                                                            │     │
│  │  1. Full project scan                                      │     │
│  │  2. Group violations by file and rule                      │     │
│  │  3. Check for duplicate issues                             │     │
│  │  4. Create issues with:                                    │     │
│  │     - Severity labels                                      │     │
│  │     - Category labels                                      │     │
│  │     - Code snippets                                        │     │
│  │     - Fix suggestions                                      │     │
│  │     - NASA mappings                                        │     │
│  │  5. Create weekly summary issue                            │     │
│  │  6. Upload artifacts (90-day retention)                    │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
                ▼              ▼              ▼
    ┌───────────────┐  ┌──────────────┐  ┌─────────────┐
    │ GitHub Code   │  │ GitHub       │  │ GitHub      │
    │ Scanning      │  │ Issues       │  │ Check Runs  │
    │               │  │              │  │             │
    │ Security Tab  │  │ quality-gate │  │ Pass/Fail   │
    │ SARIF Upload  │  │ labels       │  │ Status      │
    └───────────────┘  └──────────────┘  └─────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        OUTPUT FORMATS                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  SARIF 2.1.0            JSON                  Markdown              │
│  ┌────────────┐         ┌────────────┐        ┌────────────┐       │
│  │ GitHub     │         │ Machine    │        │ Human      │       │
│  │ Code       │         │ Readable   │        │ Readable   │       │
│  │ Scanning   │         │            │        │            │       │
│  │            │         │ Metrics    │        │ Reports    │       │
│  │ Annotations│         │ Scores     │        │ Summaries  │       │
│  │ Security   │         │ Trends     │        │ PR Comments│       │
│  └────────────┘         └────────────┘        └────────────┘       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    PRODUCTION UTILITIES                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  scripts/cleanup-scaffolding.sh                                     │
│  ┌────────────────────────────────────────────────────────┐         │
│  │ Production Cleanup (After Week 6)                      │         │
│  │                                                        │         │
│  │ 1. Move .claude/ → docs/development/agents/          │         │
│  │ 2. Move .claude-flow/ → docs/development/workflows/  │         │
│  │ 3. Create archive (tar.gz)                            │         │
│  │ 4. Delete scaffolding directories                     │         │
│  │ 5. Update .gitignore                                  │         │
│  │ 6. Generate documentation                             │         │
│  │    - CLEANUP_SUMMARY.md                               │         │
│  │    - MIGRATION_FROM_SCAFFOLDING.md                    │         │
│  └────────────────────────────────────────────────────────┘         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
┌──────────────┐
│  Developer   │
│  Creates PR  │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│  GitHub Actions Trigger                     │
│  .github/workflows/self-analysis.yml        │
└──────┬──────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│  UnifiedQualityGate.analyze_project()       │
│  analyzer/quality_gates/unified_quality_gate.py │
└──────┬──────────────────────────────────────┘
       │
       ├─────────────────────────────────────┐
       │                                     │
       ▼                                     ▼
┌──────────────┐                    ┌──────────────┐
│ Clarity      │                    │ Connascence  │
│ Linter       │                    │ Analyzer     │
│              │                    │              │
│ clarity_     │                    │ analyzer/    │
│ linter.yaml  │                    │ ...          │
└──────┬───────┘                    └──────┬───────┘
       │                                   │
       │        ┌──────────────┐           │
       └────────┤ NASA         ├───────────┘
                │ Standards    │
                │              │
                │ NASA-STD-    │
                │ 8739.8       │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────────┐
                │ Violation List   │
                │ + Metrics        │
                │ + Scores         │
                └──────┬───────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────┐   ┌──────────┐   ┌──────────┐
│ SARIF    │   │ JSON     │   │ Markdown │
│ results  │   │ results  │   │ report   │
│ .sarif   │   │ .json    │   │ .md      │
└────┬─────┘   └────┬─────┘   └────┬─────┘
     │              │              │
     ▼              ▼              ▼
┌────────────────────────────────────────┐
│  GitHub Integration                    │
├────────────────────────────────────────┤
│  1. Upload SARIF → Code Scanning       │
│  2. Post JSON metrics → PR Comment     │
│  3. Display Markdown → PR Comment      │
│  4. Create Check Run → Pass/Fail       │
│  5. Block merge if violations          │
└────────────────────────────────────────┘
```

## Progressive Enforcement Timeline

```
Week 1          Week 2          Week 3          Week 4          Week 5          Week 6
┌────────┐      ┌────────┐      ┌────────┐      ┌────────┐      ┌────────┐      ┌────────┐
│Baseline│      │ High   │      │ Medium │      │Testing │      │  Full  │      │  Zero  │
│Critical│  →   │Severity│  →   │+ NASA  │  →   │+ Cover │  →   │Enforce │  →   │Violate │
│        │      │        │      │        │      │        │      │        │      │        │
│fail_on:│      │fail_on:│      │fail_on:│      │fail_on:│      │fail_on:│      │fail_on:│
│critical│      │ high   │      │ medium │      │ medium │      │  any   │      │  any   │
│        │      │        │      │        │      │        │      │        │      │        │
│max:    │      │max:    │      │max:    │      │min:    │      │max:    │      │max:    │
│  C: 0  │      │  C: 0  │      │  C: 0  │      │  C: 0  │      │  C: 0  │      │  C: 0  │
│  H: ∞  │      │  H: 5  │      │  H: 0  │      │  H: 0  │      │  H: 0  │      │  H: 0  │
│  M: ∞  │      │  M: ∞  │      │  M: 10 │      │  M: 5  │      │  M: 0  │      │  M: 0  │
│  L: ∞  │      │  L: ∞  │      │  L: ∞  │      │  L: ∞  │      │  L: 20 │      │  L: 0  │
│        │      │        │      │        │      │Cov:80% │      │Cov:85% │      │Cov:90% │
└────────┘      └────────┘      └────────┘      └────────┘      └────────┘      └────────┘
```

## File Dependencies

```
clarity_linter.yaml
    │
    ├─── Used by: UnifiedQualityGate._run_clarity_linter()
    │
    └─── Referenced in: .github/workflows/self-analysis.yml

quality_gate.config.yaml
    │
    ├─── Used by: UnifiedQualityGate.__init__()
    │
    ├─── Referenced in: .github/workflows/self-analysis.yml
    │
    └─── Referenced in: .github/workflows/create-violation-issues.yml

unified_quality_gate.py
    │
    ├─── Imports: yaml, json, datetime, pathlib
    │
    ├─── Used by: .github/workflows/self-analysis.yml
    │
    └─── Used by: .github/workflows/create-violation-issues.yml

.github/workflows/self-analysis.yml
    │
    ├─── Triggered by: pull_request, push, workflow_dispatch
    │
    ├─── Runs: unified_quality_gate.py
    │
    └─── Uploads: SARIF to Code Scanning, Artifacts

.github/workflows/create-violation-issues.yml
    │
    ├─── Triggered by: schedule (cron), workflow_dispatch
    │
    ├─── Runs: unified_quality_gate.py
    │
    └─── Creates: GitHub Issues, Summary Issue, Artifacts
```

## Integration Points

```
┌──────────────────────────────────────────────────────────┐
│                   External Integrations                   │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  GitHub                                                   │
│  ├── Code Scanning API (SARIF upload)                    │
│  ├── Issues API (auto-creation)                          │
│  ├── Checks API (status updates)                         │
│  ├── Pull Request API (comments)                         │
│  └── Actions API (workflow execution)                    │
│                                                           │
│  Connascence Analyzer                                     │
│  ├── analyzer/ module                                     │
│  ├── CoN, CoT, CoM, CoP, CoA, CoE, CoV, CoI, CoC        │
│  └── NASA standards checking                             │
│                                                           │
│  External Tools (Future)                                  │
│  ├── SonarQube (quality reports)                         │
│  ├── GitLab (merge request integration)                  │
│  └── Slack (notifications)                               │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

## Security & Permissions

```
GitHub Actions Permissions Required:
┌──────────────────────────────────────┐
│ contents: read                       │
│ pull-requests: write                 │
│ security-events: write               │
│ checks: write                        │
│ issues: write                        │
└──────────────────────────────────────┘

Sensitive Data:
┌──────────────────────────────────────┐
│ secrets.GITHUB_TOKEN (auto-provided) │
│ No additional secrets required       │
└──────────────────────────────────────┘
```

---

**Status:** Production-Ready
**Version:** 1.0.0
**Last Updated:** 2025-11-13
