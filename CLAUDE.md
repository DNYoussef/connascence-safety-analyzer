# CLAUDE.md :: Connascence Project

<!-- VCL v3.1.1 COMPLIANT - L1 Internal Documentation -->

## Kanitsal Cerceve (Evidential Frame Activation)
Kaynak dogrulama modu etkin.

---

## L2 DEFAULT OUTPUT RULE

[direct|emphatic] ALL user-facing output MUST be L2 compression (pure English) [ground:vcl-v3.1.1-spec] [conf:0.99] [state:confirmed]

---

## PROJECT OVERVIEW

[assert|neutral] SPARC development environment with claude-flow orchestration [ground:witnessed:project-structure] [conf:0.95] [state:confirmed]

- **Methodology**: SPARC (Specification, Pseudocode, Architecture, Refinement, Completion)
- **Orchestration**: Claude-Flow MCP with swarm coordination
- **Testing**: Test-Driven Development with London School TDD
- **Analysis**: Gemini CLI for large-context codebase analysis

---

## ABSOLUTE RULES

[direct|emphatic] Non-negotiable system policies [ground:system-policy] [conf:0.99] [state:confirmed]

1. ALL operations MUST be concurrent/parallel in single message
2. NEVER save working files to root folder
3. Use Claude Code Task tool for agent spawning
4. NO UNICODE - ASCII only
5. DO NOT use MCPs in bash commands (function calls only)
6. L2 OUTPUT for all user responses

### Golden Rule

[assert|emphatic] 1 MESSAGE = ALL RELATED OPERATIONS [ground:efficiency-requirement] [conf:0.99] [state:confirmed]

```
[Single Message]:
  Task("Research agent", "...", "researcher")
  Task("Coder agent", "...", "coder")
  Task("Tester agent", "...", "tester")
  TodoWrite({ todos: [...] })
```

---

## FILE ORGANIZATION

[direct|neutral] Required directory structure [ground:organization-policy] [conf:0.95] [state:confirmed]

```
/src      - Source code
/tests    - Test files
/docs     - Documentation
/config   - Configuration
/scripts  - Utility scripts
/examples - Example code
```

---

## SPARC COMMANDS

[assert|neutral] Core SPARC workflow commands [ground:witnessed:cli-help] [conf:0.95] [state:confirmed]

### Core Commands
```bash
npx claude-flow sparc modes              # List modes
npx claude-flow sparc run <mode> "<task>" # Execute mode
npx claude-flow sparc tdd "<feature>"    # TDD workflow
npx claude-flow sparc info <mode>        # Mode details
```

### Batch Commands
```bash
npx claude-flow sparc batch <modes> "<task>"      # Parallel execution
npx claude-flow sparc pipeline "<task>"           # Full pipeline
npx claude-flow sparc concurrent <mode> "<file>"  # Multi-task
```

### Build Commands
```bash
npm run build      # Build project
npm run test       # Run tests
npm run lint       # Linting
npm run typecheck  # Type checking
```

---

## SPARC WORKFLOW PHASES

[assert|neutral] 5-phase development methodology [ground:sparc-spec] [conf:0.95] [state:confirmed]

1. **Specification** - Requirements analysis
   - Gemini: `gemini -p "@requirements/ @docs/ Analyze requirements"`
   - Claude: `sparc run spec-pseudocode`

2. **Pseudocode** - Algorithm design
   - Gemini: `gemini -p "@src/ Analyze algorithms"`
   - Claude: `sparc run spec-pseudocode`

3. **Architecture** - System design
   - Gemini: `gemini -p "@./ Analyze architecture"`
   - Claude: `sparc run architect`

4. **Refinement** - TDD implementation
   - Claude: `sparc tdd`
   - Gemini: `gemini -p "@./ @tests/ Verify TDD coverage"`

5. **Completion** - Integration
   - Claude: `sparc run integration`
   - Gemini: `gemini -p "@./ Final verification"`

---

## GEMINI CLI INTEGRATION

[assert|neutral] Large-context analysis tool [ground:witnessed:gemini-cli] [conf:0.95] [state:confirmed]

### When to Use Gemini CLI
- Files total >100KB or >50 files
- Full codebase analysis
- Pattern detection across project
- Implementation verification

### When to Use Claude Code
- File edits and creation
- Agent spawning for implementation
- MCP coordination
- Bash commands and git operations

### Command Patterns
```bash
# Single file
gemini -p "@src/main.py Explain this file"

# Directory
gemini -p "@src/ Summarize architecture"

# Multiple directories
gemini -p "@src/ @tests/ Analyze test coverage"

# Full project
gemini -p "@./ Project overview"
```

---

## AVAILABLE AGENTS (64+)

[assert|neutral] Agent categories [ground:witnessed:agent-registry] [conf:0.95] [state:confirmed]

### Core Development
`coder`, `reviewer`, `tester`, `planner`, `researcher`, `gemini-analyzer`

### Swarm Coordination
`hierarchical-coordinator`, `mesh-coordinator`, `adaptive-coordinator`

### Consensus & Distributed
`byzantine-coordinator`, `raft-manager`, `gossip-coordinator`

### SPARC Methodology
`sparc-coord`, `sparc-coder`, `specification`, `pseudocode`, `architecture`

### Specialized
`backend-dev`, `mobile-dev`, `ml-developer`, `cicd-engineer`, `system-architect`

---

## CLAUDE CODE VS MCP TOOLS

[assert|neutral] Tool responsibility separation [ground:architecture-design] [conf:0.95] [state:confirmed]

### Claude Code Handles Execution
- Task tool: Spawn and run agents
- File operations (Read, Write, Edit, Glob, Grep)
- Code generation
- Bash commands
- Git operations

### MCP Tools Coordinate
- Swarm initialization
- Agent type definitions
- Task orchestration
- Memory management
- GitHub integration

---

## DUAL-AI WORKFLOW

[assert|neutral] Gemini + Claude coordination pattern [ground:best-practices] [conf:0.90] [state:confirmed]

```
Phase 1 (Gemini): Analysis
  gemini -p "@./ @tests/ Analyze current state"

Phase 2 (Claude): Implementation
  [Single Message]:
    TodoWrite({ todos: [8-10+ tasks] })
    Task("Coder", "Implement based on analysis", "coder")
    Task("Tester", "Create tests", "tester")
    mcp__claude-flow__task_orchestrate(...)

Phase 3 (Gemini): Verification
  gemini -p "@./ Verify implementation meets requirements"
```

---

## AGENT COORDINATION PROTOCOL

[direct|neutral] Required hooks for agent execution [ground:system-policy] [conf:0.95] [state:confirmed]

### Before Work
```bash
npx claude-flow@alpha hooks pre-task --description "[task]"
npx claude-flow@alpha hooks session-restore --session-id "swarm-[id]"
```

### During Work
```bash
npx claude-flow@alpha hooks post-edit --file "[file]" --memory-key "swarm/[agent]/[step]"
npx claude-flow@alpha hooks notify --message "[what was done]"
```

### After Work
```bash
npx claude-flow@alpha hooks post-task --task-id "[task]"
npx claude-flow@alpha hooks session-end --export-metrics true
```

---

## CODE STYLE

[assert|neutral] Best practices [ground:code-quality-standards] [conf:0.95] [state:confirmed]

- Modular design: Files under 500 lines
- Environment safety: Never hardcode secrets
- Test-first: Write tests before implementation
- Clean architecture: Separate concerns
- Documentation: Keep updated

---

## QUICK SETUP

```bash
# Add MCP servers
claude mcp add claude-flow npx claude-flow@alpha mcp start
claude mcp add ruv-swarm npx ruv-swarm@latest mcp start
claude mcp add ref-mcp npx @anthropic/ref-mcp-server
claude mcp add playwright npx @playwright/mcp@latest

# Gemini CLI auth
export GEMINI_API_KEY="your_api_key"
```

---

<promise>CONNASCENCE_CLAUDE_MD_VCL_V3.1.1_COMPLIANT</promise>
