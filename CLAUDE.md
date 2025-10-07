# Claude Code Configuration - SPARC Development Environment

## 🚨 CRITICAL: CONCURRENT EXECUTION & FILE MANAGEMENT

**ABSOLUTE RULES**:
1. ALL operations MUST be concurrent/parallel in a single message
2. **NEVER save working files, text/mds and tests to the root folder**
3. ALWAYS organize files in appropriate subdirectories
4. **USE CLAUDE CODE'S TASK TOOL** for spawning agents concurrently, not just MCP
5. **NO UNICODE** - Only ASCII text allowed in all operations
6. **DO NOT USE MCPs IN BASH COMMANDS** - MCP tools are function calls ONLY

### ⚡ GOLDEN RULE: "1 MESSAGE = ALL RELATED OPERATIONS + GEMINI COORDINATION"

**MANDATORY PATTERNS:**
- **TodoWrite**: ALWAYS batch ALL todos in ONE call (5-10+ todos minimum)
- **Task tool (Claude Code)**: ALWAYS spawn ALL agents in ONE message with full instructions
- **File operations**: ALWAYS batch ALL reads/writes/edits in ONE message
- **Bash commands**: ALWAYS batch ALL terminal operations in ONE message
- **Memory operations**: ALWAYS batch ALL memory store/retrieve in ONE message
- **Gemini CLI**: Use for large-scale analysis BEFORE Claude Code implementation

### 🎯 CRITICAL: Claude Code Task Tool for Agent Execution

**Claude Code's Task tool is the PRIMARY way to spawn agents:**
```javascript
// ✅ CORRECT: Use Claude Code's Task tool for parallel agent execution
[Single Message]:
  Task("Research agent", "Analyze requirements and patterns...", "researcher")
  Task("Coder agent", "Implement core features...", "coder")
  Task("Tester agent", "Create comprehensive tests...", "tester")
  Task("Reviewer agent", "Review code quality...", "reviewer")
  Task("Architect agent", "Design system architecture...", "system-architect")
```

**MCP tools are ONLY for coordination setup:**
- `mcp__claude-flow__swarm_init` - Initialize coordination topology
- `mcp__claude-flow__agent_spawn` - Define agent types for coordination
- `mcp__claude-flow__task_orchestrate` - Orchestrate high-level workflows

### 📁 File Organization Rules

**NEVER save to root folder. Use these directories:**
- `/src` - Source code files
- `/tests` - Test files
- `/docs` - Documentation and markdown files
- `/config` - Configuration files
- `/scripts` - Utility scripts
- `/examples` - Example code

## Project Overview

This project uses SPARC (Specification, Pseudocode, Architecture, Refinement, Completion) methodology with Claude-Flow orchestration for systematic Test-Driven Development.

## SPARC Commands

### Core Commands
- `npx claude-flow sparc modes` - List available modes
- `npx claude-flow sparc run <mode> "<task>"` - Execute specific mode
- `npx claude-flow sparc tdd "<feature>"` - Run complete TDD workflow
- `npx claude-flow sparc info <mode>` - Get mode details

### Batchtools Commands
- `npx claude-flow sparc batch <modes> "<task>"` - Parallel execution
- `npx claude-flow sparc pipeline "<task>"` - Full pipeline processing
- `npx claude-flow sparc concurrent <mode> "<tasks-file>"` - Multi-task processing

### Build Commands
- `npm run build` - Build project
- `npm run test` - Run tests
- `npm run lint` - Linting
- `npm run typecheck` - Type checking

## SPARC Workflow Phases + Gemini CLI Integration

### Enhanced SPARC Phases:

1. **Specification** - Requirements analysis
   - **Gemini CLI**: `gemini -p "@requirements/ @docs/ Analyze all requirements and identify gaps"`
   - **Claude Code**: Spawn specification agents to formalize requirements (`sparc run spec-pseudocode`)

2. **Pseudocode** - Algorithm design
   - **Gemini CLI**: `gemini -p "@src/ Analyze existing algorithms and suggest improvements"`
   - **Claude Code**: Implement pseudocode with specialized agents (`sparc run spec-pseudocode`)

3. **Architecture** - System design
   - **Gemini CLI**: `gemini -p "@./ Analyze system architecture and identify bottlenecks"`
   - **Claude Code**: Spawn architecture agents to implement designs (`sparc run architect`)

4. **Refinement** - TDD implementation
   - **Claude Code**: TDD implementation with agent swarms (`sparc tdd`)
   - **Gemini CLI**: `gemini -p "@./ @tests/ Verify TDD coverage and implementation quality"`

5. **Completion** - Integration
   - **Claude Code**: Integration and deployment (`sparc run integration`)
   - **Gemini CLI**: `gemini -p "@./ Final verification of complete implementation"`

## Code Style & Best Practices

- **Modular Design**: Files under 500 lines
- **Environment Safety**: Never hardcode secrets
- **Test-First**: Write tests before implementation
- **Clean Architecture**: Separate concerns
- **Documentation**: Keep updated

## 🚀 Available Agents (64+ Total) ✅ **GEMINI-ENHANCED**

### Core Development ✅ **GEMINI-ENHANCED**
`coder`, `reviewer`, `tester`, `planner`, `researcher`, `gemini-analyzer`

### Swarm Coordination
`hierarchical-coordinator`, `mesh-coordinator`, `adaptive-coordinator`, `collective-intelligence-coordinator`, `swarm-memory-manager`

### Consensus & Distributed
`byzantine-coordinator`, `raft-manager`, `gossip-coordinator`, `consensus-builder`, `crdt-synchronizer`, `quorum-manager`, `security-manager`

### Performance & Optimization
`perf-analyzer`, `performance-benchmarker`, `task-orchestrator`, `memory-coordinator`, `smart-agent`

### GitHub & Repository
`github-modes`, `pr-manager`, `code-review-swarm`, `issue-tracker`, `release-manager`, `workflow-automation`, `project-board-sync`, `repo-architect`, `multi-repo-swarm`

### SPARC Methodology
`sparc-coord`, `sparc-coder`, `specification`, `pseudocode`, `architecture`, `refinement`

### Specialized Development
`backend-dev`, `mobile-dev`, `ml-developer`, `cicd-engineer`, `api-docs`, `system-architect`, `code-analyzer`, `base-template-generator`

### Testing & Validation
`tdd-london-swarm`, `production-validator`

### Migration & Planning
`migration-planner`, `swarm-init`

## 🎯 Claude Code vs MCP Tools

### Claude Code Handles ALL EXECUTION:
- **Task tool**: Spawn and run agents concurrently for actual work
- File operations (Read, Write, Edit, MultiEdit, Glob, Grep)
- Code generation and programming
- Bash commands and system operations
- Implementation work
- Project navigation and analysis
- TodoWrite and task management
- Git operations
- Package management
- Testing and debugging

### MCP Tools ONLY COORDINATE:
- Swarm initialization (topology setup)
- Agent type definitions (coordination patterns)
- Task orchestration (high-level planning)
- Memory management
- Neural features
- Performance tracking
- GitHub integration
- **NEW**: Documentation search (Ref MCP)
- **NEW**: Browser automation (Playwright MCP)  
- **NEW**: AI-powered research (Exa MCP)

**KEY**: MCP coordinates the strategy, Claude Code's Task tool executes with real agents.

## 🧠 Gemini CLI Integration - Large Context Analysis ✅ **COMPLETE AND VERIFIED**

**INTEGRATION STATUS**: 🎉 **PRODUCTION READY** - Authentication working, dual-AI patterns verified, 64+ agents enhanced

### Decision Matrix: When to Use Which Tool

**Use Gemini CLI when:**
- Analyzing entire codebases (`gemini -p "@./ analyze architecture"`)
- Files total >100KB or >50 files involved
- Need Google Search grounding for current best practices
- Verifying implementation across multiple directories
- Pattern detection across entire project
- Security analysis requiring full codebase context
- Implementation verification (`gemini -p "@src/ @tests/ Is feature X fully implemented?"`)

**Use Claude Code when:**
- Making file edits or creating new files
- Spawning agents for implementation work
- Coordinating MCP tools and swarms
- Running bash commands or system operations
- Managing git operations and commits
- Executing SPARC methodology phases
- Managing concurrent task execution

### Gemini CLI Command Patterns ✅ **VERIFIED WORKING**

#### **Basic Analysis Commands**
```bash
# Single file analysis
gemini -p "@src/main.py Explain this file's purpose and structure"

# Multiple files
gemini -p "@package.json @src/index.js Analyze the dependencies used in the code"

# Entire directory
gemini -p "@src/ Summarize the architecture of this codebase"

# Multiple directories
gemini -p "@src/ @tests/ Analyze test coverage for the source code"

# Full project analysis
gemini -p "@./ Give me an overview of this entire project"
gemini --all_files -p "Analyze the project structure and dependencies"
```

#### **Implementation Verification Examples ✅ **TESTED**
```bash
# Feature implementation check
gemini -p "@src/ @lib/ Has dark mode been implemented in this codebase? Show me the relevant files and functions"

# Authentication verification
gemini -p "@src/ @middleware/ Is JWT authentication implemented? List all auth-related endpoints and middleware"

# Pattern detection
gemini -p "@src/ Are there any React hooks that handle WebSocket connections? List them with file paths"

# Error handling verification
gemini -p "@src/ @api/ Is proper error handling implemented for all API endpoints? Show examples of try-catch blocks"

# Rate limiting check
gemini -p "@backend/ @middleware/ Is rate limiting implemented for the API? Show the implementation details"

# Caching strategy verification
gemini -p "@src/ @lib/ @services/ Is Redis caching implemented? List all cache-related functions and their usage"

# Security measures check
gemini -p "@src/ @api/ Are SQL injection protections implemented? Show how user inputs are sanitized"

# Test coverage verification
gemini -p "@src/payment/ @tests/ Is the payment processing module fully tested? List all test cases"
```

#### **Advanced Analysis Patterns**
```bash
# Architecture Analysis
gemini -p "@./ Analyze overall project architecture and identify improvement opportunities"

# Security Analysis
gemini -p "@./ Comprehensive security analysis. Check for vulnerabilities, proper input validation, and security best practices"

# Cross-directory consistency
gemini -p "@frontend/ @backend/ Verify API contract consistency between client and server"

# Pattern consistency check
gemini -p "@src/ Find all error handling patterns and identify inconsistencies"
```

### 📝 **Important Gemini CLI Notes** ✅ **PRODUCTION READY**

#### **Authentication Setup**
```bash
# Set API key for session (required)
export GEMINI_API_KEY="your_api_key_here"

# Use flash model for better rate limits
gemini -m gemini-2.5-flash -p "your_prompt"

# OAuth setup (higher limits)
echo "test" | gemini  # Follow browser authentication
```

#### **Key Usage Guidelines**
- **@ syntax paths**: Relative to current working directory when invoking gemini
- **Context capacity**: 1M tokens - can handle entire large codebases
- **Rate limits**: Free tier limited (15 RPM), use flash model or OAuth for higher limits
- **File inclusion**: Direct content inclusion in context, no --yolo flag needed
- **Specificity**: Be specific about what you're looking for to get accurate results

#### **Best Practices**
- Use Gemini CLI for large-scale analysis (>50 files or >100KB)
- Use Claude Code for implementation and file operations
- Always verify implementations with Gemini CLI cross-validation
- Store analysis results in MCP memory for cross-session use

## 🆕 NEW MCP SERVERS - Extended Capabilities (3 NEW ADDITIONS)

### 1. Ref MCP Server - Token-Efficient Documentation Search ✅ **PRODUCTION READY**

**Purpose**: Documentation search and URL reading with agentic search  
**Key Features**:
- **60-95% token reduction** for documentation searches
- **Session-aware search trajectories** with intelligent caching
- **Agentic search capabilities** with autonomous query refinement
- **No API key required** - immediate setup

**Installation & Setup**:
```bash
# Quick start
npx @anthropic/ref-mcp-server

# Global installation
npm install -g @anthropic/ref-mcp-server

# VS Code integration
claude mcp add ref-mcp npx @anthropic/ref-mcp-server
```

**When to Use Ref MCP vs Other Tools**:
- **Use Ref MCP when**: Need documentation search, want token efficiency, require agentic search
- **Use WebFetch when**: Simple static content retrieval without optimization needs
- **Use Gemini CLI when**: Large codebase analysis beyond documentation

### 2. Playwright MCP Server - Browser Automation with Accessibility Trees ✅ **PRODUCTION READY**

**Purpose**: Browser automation and web page interaction without screenshots  
**Revolutionary Features**:
- **Accessibility tree automation** - no screenshots needed
- **Structured semantic data** - elements as roles, labels, states
- **Multi-browser support** - Chromium, Firefox, WebKit, Edge
- **No API key required** - immediate setup

**Installation & Setup**:
```bash
# Quick start (Microsoft official)
npx @playwright/mcp@latest

# Alternative with extended features
npx @executeautomation/playwright-mcp-server

# Global installation
npm install -g @playwright/mcp

# VS Code integration
claude mcp add playwright npx @playwright/mcp@latest
```

**Available Tools**:
- `playwright_navigate()` - Page navigation
- `playwright_click()` - Element interactions  
- `playwright_fill()` - Form completion
- `playwright_screenshot()` - Visual capture
- `playwright_execute_js()` - JavaScript execution
- `playwright_get_text()` - Content extraction

**When to Use Playwright MCP vs Other Tools**:
- **Use Playwright when**: Dynamic content, form automation, accessibility testing, browser sessions
- **Use WebFetch when**: Static content retrieval, simple HTTP requests
- **Use Gemini CLI when**: Analyzing web content patterns across projects

### 3. Exa MCP Server - AI-Powered Neural Search ✅ **PRODUCTION READY**

**Purpose**: AI-powered web search and research with neural understanding  
**Advanced Capabilities**:
- **Neural semantic search** - understanding vs keyword matching
- **Deep researcher agents** - autonomous multi-step research
- **Real-time indexing** - updated every minute
- **SEO-resistant results** - bypasses manipulation
- **API key required** from `dashboard.exa.ai/api-keys`

**Installation & Setup**:
```bash
# With API key
claude mcp add exa -e EXA_API_KEY=YOUR_API_KEY -- npx -y exa-mcp-server

# Global installation
npm install -g exa-mcp-server
export EXA_API_KEY="your-api-key"

# Quick test
npx exa-mcp-server --tools=web_search_exa,company_research
```

**Available Tools**:
- `web_search_exa` - Neural semantic search
- `company_research` - Business intelligence
- `crawling` - Content extraction (articles, PDFs)
- `linkedin_search` - LinkedIn company/people search
- `deep_researcher_start` - Initiate research agent
- `deep_researcher_check` - Retrieve research results
- `research_paper_search` - Academic papers

**Deep Researcher Workflow**:
```javascript
// Step 1: Start research agent
deep_researcher_start("complex research question")

// Step 2: Check results (agent works autonomously)  
deep_researcher_check(research_id)
// Returns comprehensive, multi-source analysis
```

**When to Use Exa vs Other Search Tools**:
- **Use Exa when**: Complex research, semantic search needed, company intelligence, academic papers
- **Use WebSearch when**: Simple keyword searches, don't have API key
- **Use Gemini CLI when**: Analyzing existing project content vs external research

## 🎯 NEW TOOL DECISION MATRIX

### Documentation & Search Strategy
```javascript
// Single message pattern with optimal tool selection
[Documentation Research Workflow]:
  // For existing project documentation
  Gemini CLI: `gemini -p "@docs/ @README.md Analyze project documentation"`
  
  // For external documentation search  
  Ref MCP: search_docs("specific API documentation")
  
  // For research and intelligence
  Exa MCP: deep_researcher_start("technology comparison analysis")
  
  // For web automation needs
  Playwright MCP: playwright_navigate("dynamic documentation site")
```

### Updated Dual-AI Patterns with New MCPs

#### Enhanced Research Pattern
```javascript
[Single Message - Multi-Source Research]:
  // Phase 1: External research via Exa
  Task("Deep researcher", "Use Exa deep researcher for market analysis", "researcher")
  
  // Phase 2: Codebase analysis via Gemini  
  Task("Codebase analyzer", "Run: gemini -p '@./ analyze current implementation'", "gemini-analyzer")
  
  // Phase 3: Documentation optimization via Ref
  Task("Doc optimizer", "Use Ref MCP to search best practice docs", "reviewer")
  
  // Phase 4: Dynamic testing via Playwright
  Task("Web tester", "Use Playwright to test UI interactions", "tester")
  
  // Coordination
  TodoWrite { todos: [8-10+ todos covering all research phases] }
  mcp__claude-flow__task_orchestrate { task: "comprehensive_research_workflow" }
```

## 🚀 Quick Setup

```bash
# Add Claude Flow MCP server
claude mcp add claude-flow npx claude-flow@alpha mcp start

# Add ruv-swarm MCP server  
claude mcp add ruv-swarm npx ruv-swarm@latest mcp start

# Add new MCP servers (3 NEW ADDITIONS)
claude mcp add ref-mcp npx @anthropic/ref-mcp-server
claude mcp add playwright npx @playwright/mcp@latest
claude mcp add exa -e EXA_API_KEY=YOUR_API_KEY -- npx -y exa-mcp-server

# Setup Gemini CLI authentication
export GEMINI_API_KEY="your_api_key_here"
```

## MCP Tool Categories

### Coordination
`swarm_init`, `agent_spawn`, `task_orchestrate`

### Monitoring
`swarm_status`, `agent_list`, `agent_metrics`, `task_status`, `task_results`

### Memory & Neural
`memory_usage`, `neural_status`, `neural_train`, `neural_patterns`

### GitHub Integration
`github_swarm`, `repo_analyze`, `pr_enhance`, `issue_triage`, `code_review`

### NEW: Documentation & Search (3 NEW SERVERS)
`ref_mcp_search`, `playwright_navigate`, `playwright_automation`, `exa_web_search`, `exa_deep_research`, `exa_company_research`

### System
`benchmark_run`, `features_detect`, `swarm_monitor`

## 🚀 Agent Execution Flow with Claude Code

### The Correct Pattern:

1. **Optional**: Use MCP tools to set up coordination topology
2. **REQUIRED**: Use Claude Code's Task tool to spawn agents that do actual work
3. **REQUIRED**: Each agent runs hooks for coordination
4. **REQUIRED**: Batch all operations in single messages

### Example Full-Stack Development:

```javascript
// Single message with all agent spawning via Claude Code's Task tool
[Parallel Agent Execution]:
  Task("Backend Developer", "Build REST API with Express. Use hooks for coordination.", "backend-dev")
  Task("Frontend Developer", "Create React UI. Coordinate with backend via memory.", "coder")
  Task("Database Architect", "Design PostgreSQL schema. Store schema in memory.", "code-analyzer")
  Task("Test Engineer", "Write Jest tests. Check memory for API contracts.", "tester")
  Task("DevOps Engineer", "Setup Docker and CI/CD. Document in memory.", "cicd-engineer")
  Task("Security Auditor", "Review authentication. Report findings via hooks.", "reviewer")
  
  // All todos batched together
  TodoWrite { todos: [...8-10 todos...] }
  
  // All file operations together
  Write "backend/server.js"
  Write "frontend/App.jsx"
  Write "database/schema.sql"
```

## 📋 Agent Coordination Protocol

### Every Agent Spawned via Task Tool MUST:

**1️⃣ BEFORE Work:**
```bash
npx claude-flow@alpha hooks pre-task --description "[task]"
npx claude-flow@alpha hooks session-restore --session-id "swarm-[id]"
```

**2️⃣ DURING Work:**
```bash
npx claude-flow@alpha hooks post-edit --file "[file]" --memory-key "swarm/[agent]/[step]"
npx claude-flow@alpha hooks notify --message "[what was done]"
```

**3️⃣ AFTER Work:**
```bash
npx claude-flow@alpha hooks post-task --task-id "[task]"
npx claude-flow@alpha hooks session-end --export-metrics true
```

## 🔄 Dual-AI Concurrent Execution Patterns

### Phase-Based Workflow Pattern

#### Phase 1: Analysis (Gemini CLI)
```bash
# Large-scale analysis first
gemini -p "@./ @tests/ Analyze current state of [feature/requirement]"
```

#### Phase 2: Planning & Implementation (Claude Code)
```javascript
[Single Message - All Operations]:
  // Based on Gemini analysis, plan implementation
  TodoWrite { todos: [8-10+ specific tasks from Gemini insights] }
  
  // Spawn agents concurrently
  Task("Implement core feature", "gemini_analysis_results", "coder")
  Task("Create comprehensive tests", "test_requirements", "tester")  
  Task("Update documentation", "doc_updates", "reviewer")
  Task("Security validation", "security_concerns", "security-manager")
  
  // MCP coordination
  mcp__claude-flow__swarm_init { topology: "hierarchical", maxAgents: 8 }
  mcp__claude-flow__task_orchestrate { task: "implement_based_on_gemini_analysis" }
```

#### Phase 3: Verification (Gemini CLI)
```bash
# Verify implementation across full codebase
gemini -p "@./ Verify that implementation meets all original requirements"
```

### Hybrid Execution Example
```javascript
[Single Message]:
  // Based on: gemini -p '@./ analyze authentication implementation'
  
  // Claude Code implementation based on Gemini findings
  Task("Fix auth vulnerabilities found by Gemini", "vulnerability_list", "security-manager")
  Task("Add missing auth tests", "test_gaps", "tester")
  Task("Update auth documentation", "doc_gaps", "reviewer")
  
  TodoWrite { todos: [
    {content: "Fix JWT token validation", status: "in_progress", activeForm: "Fixing JWT validation"},
    {content: "Add rate limiting to auth endpoints", status: "pending", activeForm: "Adding rate limiting"},
    {content: "Implement session timeout", status: "pending", activeForm: "Implementing session timeout"},
    {content: "Add auth integration tests", status: "pending", activeForm: "Adding auth tests"},
    {content: "Update auth documentation", status: "pending", activeForm: "Updating documentation"}
  ]}
  
  // MCP coordination for the fixes
  mcp__claude-flow__task_orchestrate { task: "auth_security_fixes" }
```

## 🎯 Concurrent Execution Examples

### ✅ CORRECT WORKFLOW: MCP Coordinates, Claude Code Executes

```javascript
// Step 1: MCP tools set up coordination (optional, for complex tasks)
[Single Message - Coordination Setup]:
  mcp__claude-flow__swarm_init { topology: "mesh", maxAgents: 6 }
  mcp__claude-flow__agent_spawn { type: "researcher" }
  mcp__claude-flow__agent_spawn { type: "coder" }
  mcp__claude-flow__agent_spawn { type: "tester" }

// Step 2: Claude Code Task tool spawns ACTUAL agents that do the work
[Single Message - Parallel Agent Execution]:
  // Claude Code's Task tool spawns real agents concurrently
  Task("Research agent", "Analyze API requirements and best practices. Check memory for prior decisions.", "researcher")
  Task("Coder agent", "Implement REST endpoints with authentication. Coordinate via hooks.", "coder")
  Task("Database agent", "Design and implement database schema. Store decisions in memory.", "code-analyzer")
  Task("Tester agent", "Create comprehensive test suite with 90% coverage.", "tester")
  Task("Reviewer agent", "Review code quality and security. Document findings.", "reviewer")
  
  // Batch ALL todos in ONE call
  TodoWrite { todos: [
    {id: "1", content: "Research API patterns", status: "in_progress", priority: "high"},
    {id: "2", content: "Design database schema", status: "in_progress", priority: "high"},
    {id: "3", content: "Implement authentication", status: "pending", priority: "high"},
    {id: "4", content: "Build REST endpoints", status: "pending", priority: "high"},
    {id: "5", content: "Write unit tests", status: "pending", priority: "medium"},
    {id: "6", content: "Integration tests", status: "pending", priority: "medium"},
    {id: "7", content: "API documentation", status: "pending", priority: "low"},
    {id: "8", content: "Performance optimization", status: "pending", priority: "low"}
  ]}
  
  // Parallel file operations
  Bash "mkdir -p app/{src,tests,docs,config}"
  Write "app/package.json"
  Write "app/src/server.js"
  Write "app/tests/server.test.js"
  Write "app/docs/API.md"
```

### ❌ WRONG (Multiple Messages):
```javascript
Message 1: mcp__claude-flow__swarm_init
Message 2: Task("agent 1")
Message 3: TodoWrite { todos: [single todo] }
Message 4: Write "file.js"
// This breaks parallel coordination!
```

## Performance Benefits

- **84.8% SWE-Bench solve rate**
- **32.3% token reduction**
- **2.8-4.4x speed improvement**
- **27+ neural models**

## Hooks Integration

### Pre-Operation
- Auto-assign agents by file type
- Validate commands for safety
- Prepare resources automatically
- Optimize topology by complexity
- Cache searches

### Post-Operation
- Auto-format code
- Train neural patterns
- Update memory
- Analyze performance
- Track token usage

### Session Management
- Generate summaries
- Persist state
- Track metrics
- Restore context
- Export workflows

## Advanced Features (v2.0.0)

- 🚀 Automatic Topology Selection
- ⚡ Parallel Execution (2.8-4.4x speed)
- 🧠 Neural Training
- 📊 Bottleneck Analysis
- 🤖 Smart Auto-Spawning
- 🛡️ Self-Healing Workflows
- 💾 Cross-Session Memory
- 🔗 GitHub Integration

## Integration Tips

1. Start with basic swarm init
2. Scale agents gradually
3. Use memory for context
4. Monitor progress regularly
5. Train patterns from success
6. Enable hooks automation
7. Use GitHub tools first

## Support

- Documentation: https://github.com/ruvnet/claude-flow
- Issues: https://github.com/ruvnet/claude-flow/issues

---

## 📋 NEW MCP SERVER GITHUB CLI COMMANDS

### Ref MCP Server Commands
```bash
# Installation options
npx @anthropic/ref-mcp-server                    # Quick start
npm install -g @anthropic/ref-mcp-server        # Global install
claude mcp add ref-mcp npx @anthropic/ref-mcp-server  # VS Code integration

# Usage patterns
ref_search_docs("API documentation")             # Token-efficient doc search
ref_agentic_search("complex query")              # Autonomous search refinement
```

### Playwright MCP Server Commands  
```bash
# Installation options (Microsoft official)
npx @playwright/mcp@latest                       # Quick start (official)
npm install -g @playwright/mcp                  # Global install (official)
npx @executeautomation/playwright-mcp-server    # Extended features version

# Configuration options
npx @playwright/mcp@latest --headless --isolated # Headless mode
npx @playwright/mcp@latest --caps vision,pdf     # Enable capabilities

# VS Code integration
claude mcp add playwright npx @playwright/mcp@latest

# Tool usage examples
playwright_navigate("https://example.com")       # Navigate to page
playwright_click("#submit-button")               # Click element
playwright_fill("#username", "testuser")         # Fill form field
playwright_screenshot()                          # Capture screenshot
playwright_execute_js("console.log('test')")     # Execute JavaScript
```

### Exa MCP Server Commands
```bash
# Installation with API key (REQUIRED)
claude mcp add exa -e EXA_API_KEY=YOUR_API_KEY -- npx -y exa-mcp-server
npm install -g exa-mcp-server                   # Global install
export EXA_API_KEY="your-api-key-here"          # Set environment variable

# Get API key from: https://dashboard.exa.ai/api-keys

# Tool-specific installation
npx exa-mcp-server --tools=web_search_exa,company_research
npx exa-mcp-server --list-tools                 # List available tools

# Usage patterns
web_search_exa("semantic search query")         # Neural search
company_research("OpenAI")                      # Business intelligence  
deep_researcher_start("complex research topic") # Start research agent
deep_researcher_check(research_id)              # Get research results
linkedin_search("company:OpenAI")               # LinkedIn search
crawling("https://example.com/article")         # Extract content
```

### Integration Commands
```bash
# Test all three servers
npx @anthropic/ref-mcp-server &
npx @playwright/mcp@latest &  
npx -y exa-mcp-server &

# VS Code setup (all three)
claude mcp add ref-mcp npx @anthropic/ref-mcp-server
claude mcp add playwright npx @playwright/mcp@latest
claude mcp add exa -e EXA_API_KEY=YOUR_KEY -- npx -y exa-mcp-server

# Verify installations
claude mcp list                                 # List all MCP servers
```

---

Remember: **Claude Flow coordinates, Claude Code creates, New MCPs extend capabilities!**

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
Never save working files, text/mds and tests to the root folder.
