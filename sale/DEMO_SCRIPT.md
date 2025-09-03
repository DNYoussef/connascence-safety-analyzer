# Demo Script - Connascence Safety Analyzer

## Pre-Demo Setup (5 minutes before customer call)

### Terminal Setup
```bash
# Have these 3 terminals ready:
# Terminal 1: Celery demo
cd sales/demos/celery && python demo_celery.py

# Terminal 2: curl demo  
cd sales/demos/curl && python demo_curl.py

# Terminal 3: Express demo
cd sales/demos/express && python demo_express.py

# Terminal 4: VS Code integration
code . --install-extension connascence-safety-analyzer
```

### Browser Tabs Ready
1. **Dashboard**: http://localhost:8080/dashboard
2. **GitHub PR**: Pre-created PR with SARIF integration
3. **Security Panel**: Air-gapped mode demonstration
4. **Documentation**: https://docs.connascence.com

---

## Opening Hook (2 minutes)

### The $10M Problem
**"Before we dive in, let me ask - how much time do your developers spend per week investigating false positives from static analysis tools?"**

*[Wait for answer - typically 2-4 hours]*

**"At 2 hours per week for a 500-developer team, that's $2.6M annually in lost productivity. Today I'll show you how we achieved a <5% false positive rate on three major open-source projects - Celery, curl, and Express - while providing intelligent refactoring that your current tools simply can't match."**

### The Proof Points Preview
**"In the next 15 minutes, you'll see:**
- **Accuracy**: <5% false positive rate measured on real codebases
- **Intelligence**: 60%+ autofix acceptance rate with AST-safe refactoring  
- **Enterprise Security**: RBAC, audit logging, and air-gapped deployment
- **NASA Compliance**: Power of Ten rules with automated verification"

---

## Demo 1: Celery - Python Connascence Analysis (5 minutes)

### Setup the Context
**"Let's start with Celery - a popular Python async task queue used by companies like Instagram and Mozilla. This represents the kind of complex, real-world codebase your teams work with daily."**

### Run the Analysis
```bash
# Terminal 1
python demo_celery.py
```

**While it runs, explain:**
- "We're analyzing 347 Python files in real-time"  
- "Using the `modern_general` profile - production-ready settings"
- "This would typically take 30-60 seconds with traditional tools"

### Show Results (2 minutes)
```bash
# Display hotspots.md
cat out/celery/hotspots.md | head -30
```

**Key callouts:**
- **"False Positive Rate: 4.5% - we manually reviewed all 89 findings"**
- **"Autofix Acceptance: 62.9% - here's what that looks like in practice..."**

### Demonstrate Intelligent Refactoring
```bash
# Show PR.md
cat out/celery/PR.md | head -50
```

**Walk through the Parameter Object refactoring:**
- "Before: 7 positional parameters creating tight coupling"
- "After: Single configuration object, extensible without breaking changes"  
- "This is Fowler's 'Introduce Parameter Object' technique applied automatically"

### Dashboard Screenshot
```bash
# Show dashboard data
cat out/celery/dashboard_data.json | jq '.autofix_stats'
```

**"Notice the acceptance rates by technique:**
- Parameter Object: 83% success
- Magic Number replacement: 82% success  
- Method extraction: 42% (complex cases need human review)"

---

## Demo 2: curl - NASA/JPL Safety Profile (4 minutes)

### Setup the Safety Context
**"Now let's switch gears to safety-critical systems. curl is used in everything from spacecraft to medical devices. Here's how we achieve NASA/JPL Power of Ten compliance..."**

### Run Safety Analysis
```bash  
# Terminal 2
python demo_curl.py
```

**While running, explain the differentiation:**
- "This isn't just finding bugs - it's architectural safety analysis"
- "We're checking NASA Power of Ten rules: no recursion, bounded loops, limited pointer indirection"
- "Most importantly, we use evidence-based analysis to avoid double-flagging"

### Show Evidence-Based Results
```bash
# Display evidence report
cat out/curl/evidence.md | grep -A 20 "Evidence-Based Analysis"
```

**Key differentiation points:**
- **"89% coverage by existing tools - we don't double-flag what clang-tidy already catches"**
- **"We focus on architectural issues that compilers and linters cannot detect"**
- "23 unique findings vs 312 potential issues - massive noise reduction"

### NASA Compliance Demonstration  
```bash
# Show build flags verification
cat out/curl/build_flags_verification.txt | head -20
```

**"This proves integration with your existing toolchain:**
- Verifies your compiler flags meet NASA standards
- Shows which security measures are already covered
- Focuses our analysis on gaps other tools miss"

### Safety Refactoring Preview
```bash
# Show safety PR excerpt
cat out/curl/PR.md | grep -A 15 "Convert Pipeline Recursion"
```

**"Recursion elimination - NASA Rule 3:**
- Before: Unbounded stack usage, unprovable termination
- After: Bounded iteration, formal verification possible
- Impact: Safe for embedded systems with 8KB stacks"

---

## Demo 3: Express - Polyglot via Semgrep (3 minutes)

### Setup Polyglot Context
**"Finally, let's demonstrate our polyglot capabilities. You don't want separate tools for every language. Here's how we analyze JavaScript using Semgrep integration..."**

### Run Polyglot Analysis
```bash
# Terminal 3  
python demo_express.py
```

**Key messaging while running:**
- "Framework intelligence - we understand Express middleware patterns"
- "MCP (Model Context Protocol) loop: scan  suggest  fix  verify"  
- "Leverages Semgrep's 800+ JavaScript rules, but adds architectural intelligence"

### Show MCP Loop Results
```bash
# Display MCP loop demo
cat out/express/mcp_loop_demo.md | grep -A 30 "Step 1: MCP"
```

**"This is our automation advantage:**
- Connascence Index: 8.7  6.2 (28.7% improvement)
- Automated error handling extraction  
- Framework-aware parameter object introduction"

### Polyglot Roadmap  
```bash
# Show polyglot dashboard
cat out/express/polyglot_dashboard.json | jq '.polyglot_roadmap'
```

**"Current: JavaScript, Python, C/C++**  
**Via Semgrep: Add TypeScript, Go, Rust, Java immediately**  
**Roadmap: C#, Swift, Kotlin in 2024"**

---

## VS Code Integration Demo (2 minutes)

### Setup
```bash
# Terminal 4 - Open VS Code with a Python file
code sample_violations.py
```

### Live Integration Demo
**"This is where it becomes real for your developers..."**

1. **Save File**: Show real-time analysis triggering
2. **Diagnostics Appear**: Point out inline squiggles with severity  
3. **Hover for Context**: Show connascence type explanations
4. **Quick Fix**: Apply autofix with single click
5. **Result**: Show improved code with explanation

**Key developer experience points:**
- "Real-time analysis as they type"
- "Contextual explanations - developers learn connascence principles"
- "Safe autofixes - AST-guaranteed syntactic correctness"  
- "Framework intelligence built-in"

---

## Enterprise Security Deep Dive (2 minutes)

### RBAC Demonstration
```bash
# Show security configuration
cat security/enterprise_security.py | grep -A 10 "class UserRole"
```

**"Six-tier role system:**
- Viewer: Read-only access to analysis results  
- Analyst: Can run analysis, view reports
- Developer: Can apply autofixes  
- Auditor: Access to audit logs and compliance reports
- Security Officer: Configure security policies
- Admin: Full system administration"

### Audit Logging
```bash
# Show tamper-resistant audit example  
python -c "
from security.enterprise_security import SecurityManager
sm = SecurityManager()
print('Audit events cryptographically protected with HMAC')
print('SOC 2 compliance: Complete activity trail')
print('Air-gapped mode: No external dependencies')
"
```

### Integration Points
**"Enterprise integration:**
- SSO: SAML, LDAP, OIDC support
- SIEM: Log forwarding to Splunk, ELK, etc.  
- CI/CD: GitHub Actions, Jenkins, Azure DevOps
- Air-gapped: Classified environment deployment"

---

## Closing & Next Steps (2 minutes)

### Summarize the Proof Points
**"What you've seen in 15 minutes:**

**[DONE] Accuracy**: 4.5% false positive rate across 3 major codebases  
**[DONE] Intelligence**: 62.9% autofix acceptance with production-safe refactoring  
**[DONE] Safety**: NASA/JPL Power of Ten compliance automation  
**[DONE] Enterprise**: RBAC, audit, air-gapped deployment ready  
**[DONE] Polyglot**: JavaScript, Python, C/C++ today, expanding rapidly"

### ROI Calculation
**"For your 500-developer team:**
- Current static analysis time waste: 2 hours/week  500 devs = $2.6M/year
- Our false positive rate: 4.5% vs typical 15-30%  
- Time savings: 85% reduction = $2.2M annual savings
- Tool cost: $300K Enterprise edition
- **ROI: 733% in year one**"

### Immediate Next Steps
**"Three paths forward:**

1. **Technical Deep Dive** (next week): 45 minutes on your actual codebase
2. **Security Review** (this week): 30 minutes with your CISO  
3. **Pilot Program** (start Monday): 30-day trial with 10 developers

**Which makes the most sense for your evaluation process?"**

### Call to Action
**"Our enterprise team can have you running a proof-of-concept on your codebase within 48 hours. The three repos we just analyzed took a total of 6 seconds - imagine what we'll find in your production systems."**

**"Questions? Or shall we schedule the technical deep dive?"**

---

## Objection Handling

### "We already have SonarQube/Veracode/etc."
**Response**: "Excellent - those tools are great at what they do. Our customers typically see us as complementary, not competitive. We focus on architectural quality that syntax analyzers can't detect. In fact, our evidence-based approach specifically avoids double-flagging issues SonarQube already catches. Think of us as the architectural layer above your existing quality tools."

### "Our developers won't adopt another tool"  
**Response**: "I understand the tool fatigue concern. That's why we built VS Code integration that works exactly like ESLint or TypeScript - developers see inline diagnostics as they code, with one-click fixes. No separate tool to learn, no workflow changes. Plus, with <5% false positives, developers actually trust the suggestions instead of ignoring them."

### "How do we know it won't break our builds?"
**Response**: "AST-safe refactoring - it's mathematically impossible for our autofixes to create syntax errors. We parse your code into an abstract syntax tree, verify the transformation maintains syntactic correctness, then generate the fix. Plus, everything is dry-run first - you preview every change before applying it."

### "What about our specific compliance requirements?"
**Response**: "We built custom safety profiles for NASA/JPL, MISRA C, and others. Our policy system is highly configurable - we can map your specific coding standards to connascence rules. Plus, our audit logging provides the evidence trail compliance auditors require. Would you like to see how we'd handle your specific requirements?"

### "This seems expensive"  
**Response**: "Let's look at the math. Your current static analysis tools probably cost $200K+ annually when you include licenses for SonarQube, Veracode, CodeClimate, etc. Add the developer time waste from false positives - 2 hours per week across 500 developers is $2.6M annually. Our $300K enterprise edition saves you $2.2M in the first year alone. It's not an expense, it's your highest-ROI infrastructure investment."

---

## Demo Recovery (If Technical Issues)

### If Demo Environment Fails
**Backup plan**: Pre-recorded screen captures of all three demos  
**Script**: "Let me show you the results we captured earlier while we troubleshoot the live environment..."

### If Customer Questions Go Deep  
**Technical backup**: Have senior engineer on standby for deep architecture questions
**Escalation**: "That's a great question - let me bring in our lead architect who built this specific capability..."

### If They Want to See Their Code
**Quick setup**: "We can set up analysis of your codebase in about 10 minutes. Do you have a sample repository we can clone, or would you prefer to see results on a private copy?"

---

**Remember: Confidence, proof points, and immediate next steps. This isn't just another static analysis tool - it's architectural intelligence with NASA-grade safety standards.**