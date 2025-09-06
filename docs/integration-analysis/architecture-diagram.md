# Integration Architecture Diagram: Connascence Analyzer System

## System Overview

This document provides comprehensive architectural diagrams showing data flows, component relationships, and integration patterns across the connascence analyzer ecosystem.

---

## High-Level System Architecture

```mermaid
graph TB
    subgraph "Analyzer Core Components"
        AC[Analyzer Core<br/>analyzer/core.py]
        UA[Unified Analyzer<br/>unified_analyzer.py]
        AST[AST Engine<br/>ast_engine/]
        MECE[MECE Analyzer<br/>dup_detection/]
        GRAMMAR[Grammar Enhanced<br/>experimental/]
    end

    subgraph "Integration Layer"
        CLI[CLI Interface<br/>cli/connascence.py]
        MCP[MCP Server<br/>mcp/server.py]
        VSC[VSCode Extension<br/>vscode-extension/]
        CICD[CI/CD Pipeline<br/>.github/workflows/]
        LINT[Linter Integration<br/>Limited]
    end

    subgraph "External Systems"
        GH[GitHub<br/>Code Scanning]
        SARIF[SARIF Format<br/>Security Tools]
        LINTERS[External Linters<br/>Pylint/Flake8]
        IDE[Other IDEs<br/>Future]
    end

    %% Core connections
    CLI --> AC
    MCP --> AC
    VSC --> UA
    CICD --> CLI
    
    %% Advanced features
    VSC --> GRAMMAR
    UA --> AST
    UA --> MECE
    
    %% External integrations
    CLI --> SARIF
    VSC --> SARIF
    CICD --> GH
    LINT -.-> LINTERS
    
    %% Styling
    classDef coreComponent fill:#e1f5fe
    classDef integration fill:#f3e5f5
    classDef external fill:#fff3e0
    
    class AC,UA,AST,MECE,GRAMMAR coreComponent
    class CLI,MCP,VSC,CICD,LINT integration
    class GH,SARIF,LINTERS,IDE external
```

---

## Detailed Data Flow Architecture

### 1. CLI Integration Data Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI as CLI Interface
    participant Parser as Argument Parser
    participant Core as Analyzer Core
    participant Reporter as Report Generator
    participant FS as File System

    User->>CLI: connascence analyze ./src --format sarif
    CLI->>Parser: Parse arguments
    Parser->>Core: analyze(path, policy, format)
    Core->>Core: Load analyzer components
    Core->>Core: Perform AST analysis
    Core->>Core: Run connascence detection
    Core->>Core: Generate quality metrics
    Core->>Reporter: format_results(format='sarif')
    Reporter->>FS: Write output file
    FS->>User: results.sarif
    Core->>CLI: Return exit code
    CLI->>User: Exit with status
```

**Data Flow Characteristics**:
- **Synchronous**: Blocking execution until complete
- **Batch Processing**: Analyzes entire directory structure
- **File-based Output**: Results written to file system
- **Exit Code Communication**: Success/failure via process exit codes

### 2. MCP Server Integration Data Flow

```mermaid
sequenceDiagram
    participant Client
    participant MCP as MCP Server
    participant Auth as Auth Layer
    participant RateLimit as Rate Limiter
    participant Analyzer as Core Analyzer
    participant Audit as Audit Logger

    Client->>MCP: scan_path({"path": "./src"})
    MCP->>Auth: validate_request()
    Auth->>RateLimit: check_rate_limit()
    RateLimit->>Analyzer: analyze_path()
    Analyzer->>Analyzer: AST parsing & analysis
    Analyzer->>MCP: return results
    MCP->>Audit: log_analysis_event()
    MCP->>Client: {"success": true, "violations": [...]}
    
    Note over MCP: Async processing with<br/>security controls
```

**Data Flow Characteristics**:
- **Asynchronous**: Non-blocking tool execution
- **Security Layer**: Authentication, rate limiting, audit logging
- **Structured Responses**: JSON format with success indicators
- **Real-time Processing**: Individual file/path analysis

### 3. VSCode Extension Data Flow

```mermaid
sequenceDiagram
    participant Editor as VSCode Editor
    participant Ext as Extension Host
    participant Events as Event Handler
    participant Cache as Result Cache
    participant API as Connascence API
    participant UI as UI Components

    Editor->>Ext: Document changed
    Ext->>Events: onDidChangeTextDocument
    Events->>Events: Start debounce timer (1000ms)
    Events->>Cache: Check cached results
    alt Cache Miss
        Events->>API: analyzeDocument()
        API->>API: Call Python analyzer
        API->>Events: Return analysis results
        Events->>Cache: Update cache
    end
    Events->>UI: Update diagnostics
    Events->>UI: Update tree view
    Events->>UI: Update dashboard
    UI->>Editor: Show visual feedback
    
    Note over Events: Real-time analysis with<br/>debouncing and caching
```

**Data Flow Characteristics**:
- **Event-Driven**: Responds to document changes
- **Debounced Processing**: Prevents excessive analysis during typing
- **Multi-UI Update**: Diagnostics, tree views, dashboards updated simultaneously
- **Caching Layer**: Performance optimization for repeated analysis

### 4. CI/CD Pipeline Data Flow

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Git as Git Repository
    participant GHA as GitHub Actions
    participant Runner as CI Runner
    participant CLI as CLI Analyzer
    participant Reports as Report System
    participant CS as Code Scanning

    Dev->>Git: Push code changes
    Git->>GHA: Trigger workflow
    GHA->>Runner: Spawn runner
    Runner->>Runner: Checkout code
    Runner->>CLI: connascence analyze --format sarif
    CLI->>CLI: Analyze changed files
    CLI->>Reports: Generate reports
    Reports->>CS: Upload SARIF results
    Reports->>GHA: Update check status
    GHA->>Dev: Notify via PR comment
    
    Note over Runner: Automated quality gates<br/>with pass/fail decisions
```

**Data Flow Characteristics**:
- **Pipeline-Driven**: Triggered by git events
- **Automated Quality Gates**: Pass/fail based on thresholds
- **Multi-Format Output**: SARIF for security, JSON for metrics
- **Integration Points**: GitHub Code Scanning, PR comments, status checks

---

## Component Interaction Matrix

### Core Analyzer Component Relationships

```mermaid
graph LR
    subgraph "Core Analysis Engine"
        CORE[Core Analyzer<br/>Entry Point]
        UNIFIED[Unified Analyzer<br/>Phase Coordinator]
        DETECTOR[Connascence Detector<br/>AST Visitor]
    end
    
    subgraph "Specialized Analyzers"
        GOD[God Object Analyzer<br/>ast_engine/]
        MECE[MECE Analyzer<br/>dup_detection/]
        GRAMMAR[Grammar Enhanced<br/>experimental/]
        SMART[Smart Integration<br/>smart_integration_engine.py]
    end
    
    subgraph "Reporting System"
        JSON[JSON Reporter]
        SARIF[SARIF Reporter]
        MARKDOWN[Markdown Reporter]
        DASHBOARD[Dashboard Data]
    end
    
    %% Primary flows
    CORE --> UNIFIED
    UNIFIED --> DETECTOR
    UNIFIED --> GOD
    UNIFIED --> MECE
    UNIFIED --> SMART
    
    %% Advanced flows (VSCode only)
    UNIFIED -.-> GRAMMAR
    GRAMMAR -.-> SMART
    
    %% Output flows
    UNIFIED --> JSON
    UNIFIED --> SARIF
    UNIFIED --> MARKDOWN
    UNIFIED -.-> DASHBOARD
    
    %% Styling
    classDef core fill:#e3f2fd
    classDef specialized fill:#f1f8e9
    classDef reporting fill:#fce4ec
    
    class CORE,UNIFIED,DETECTOR core
    class GOD,MECE,GRAMMAR,SMART specialized  
    class JSON,SARIF,MARKDOWN,DASHBOARD reporting
```

---

## Integration Communication Patterns

### 1. Direct Integration Pattern (CLI)

```mermaid
graph TD
    A[Command Line Input] --> B[Argument Parsing]
    B --> C[Configuration Loading]
    C --> D[Core Analyzer Invocation]
    D --> E[Synchronous Processing]
    E --> F[Result Formatting]
    F --> G[File System Output]
    G --> H[Exit Code Return]
    
    style A fill:#ffeb3b
    style H fill:#4caf50
```

**Characteristics**:
- **Synchronous**: Blocking execution
- **Direct Calls**: No service layer
- **File-based I/O**: Input/output via file system
- **Process Exit Codes**: Success/failure signaling

### 2. Service Integration Pattern (MCP)

```mermaid
graph TD
    A[MCP Client Request] --> B[Security Validation]
    B --> C[Rate Limiting Check]
    C --> D[Request Routing]
    D --> E[Async Tool Execution]
    E --> F[Result Processing]
    F --> G[Response Formatting]
    G --> H[Client Response]
    
    I[Audit Logging] --> B
    I --> E
    I --> H
    
    style A fill:#ffeb3b
    style H fill:#4caf50
    style I fill:#ff9800
```

**Characteristics**:
- **Asynchronous**: Non-blocking tool execution
- **Service Layer**: Authentication, rate limiting, audit
- **Structured Communication**: JSON request/response
- **Enterprise Features**: Security, compliance, monitoring

### 3. Event-Driven Pattern (VSCode)

```mermaid
graph TD
    A[Document Change Event] --> B[Event Handler]
    B --> C[Debounce Timer]
    C --> D[Cache Check]
    D --> E{Cache Hit?}
    E -->|Yes| F[Use Cached Results]
    E -->|No| G[Async Analysis]
    G --> H[Cache Update]
    F --> I[UI Update Coordination]
    H --> I
    I --> J[Diagnostics Update]
    I --> K[Tree View Update]
    I --> L[Dashboard Update]
    
    style A fill:#ffeb3b
    style J fill:#4caf50
    style K fill:#4caf50
    style L fill:#4caf50
```

**Characteristics**:
- **Event-Driven**: Responds to document changes
- **Debounced Processing**: Prevents analysis spam
- **Multi-UI Coordination**: Updates multiple UI components
- **Caching Strategy**: Performance optimization

### 4. Pipeline Integration Pattern (CI/CD)

```mermaid
graph TD
    A[Git Hook Trigger] --> B[Workflow Execution]
    B --> C[Environment Setup]
    C --> D[Code Checkout]
    D --> E[Dependency Installation]
    E --> F[Analysis Execution]
    F --> G[Quality Gate Evaluation]
    G --> H{Quality Gate Pass?}
    H -->|Pass| I[Success Notification]
    H -->|Fail| J[Failure Notification]
    I --> K[Merge Approval]
    J --> L[Block Merge]
    
    style A fill:#ffeb3b
    style K fill:#4caf50
    style L fill:#f44336
```

**Characteristics**:
- **Pipeline-Driven**: Triggered by repository events
- **Quality Gates**: Automated pass/fail decisions
- **Environment Isolation**: Fresh environment per execution
- **Integration Points**: GitHub, SARIF, notifications

---

## Data Transformation Flow

### Analysis Result Transformation Pipeline

```mermaid
graph LR
    subgraph "Core Analysis Output"
        A[Raw AST Analysis]
        B[Violation Objects]
        C[Quality Metrics]
    end
    
    subgraph "Integration-Specific Transforms"
        D[CLI Transform<br/>Exit Codes + Files]
        E[MCP Transform<br/>JSON Tools Response]
        F[VSCode Transform<br/>Diagnostics + UI Data]
        G[CI/CD Transform<br/>SARIF + Status]
    end
    
    subgraph "Output Formats"
        H[JSON Files]
        I[SARIF Reports]
        J[Markdown Docs]
        K[HTML Dashboards]
        L[Console Output]
        M[VS Diagnostics]
        N[GitHub Checks]
    end
    
    A --> D
    B --> D
    C --> D
    
    A --> E
    B --> E
    C --> E
    
    A --> F
    B --> F
    C --> F
    
    A --> G
    B --> G
    C --> G
    
    D --> H
    D --> L
    
    E --> H
    
    F --> M
    F --> K
    
    G --> I
    G --> N
    
    classDef core fill:#e3f2fd
    classDef transform fill:#fff3e0
    classDef output fill:#e8f5e8
    
    class A,B,C core
    class D,E,F,G transform
    class H,I,J,K,L,M,N output
```

---

## Configuration Management Architecture

### Current Fragmented Configuration System

```mermaid
graph TD
    subgraph "CLI Configuration"
        A1[Command Line Args]
        A2[Environment Variables]
    end
    
    subgraph "VSCode Configuration"
        B1[User Settings]
        B2[Workspace Settings]
        B3[Extension Manifest]
    end
    
    subgraph "MCP Configuration"
        C1[Server Config Files]
        C2[Client Config]
        C3[Tool Parameters]
    end
    
    subgraph "CI/CD Configuration"
        D1[Workflow YAML]
        D2[Repository Settings]
        D3[Environment Secrets]
    end
    
    E[Core Analyzer] 
    
    A1 --> E
    A2 --> E
    B1 --> E
    B2 --> E
    B3 --> E
    C1 --> E
    C2 --> E
    C3 --> E
    D1 --> E
    D2 --> E
    D3 --> E
    
    style E fill:#ff9800
    classDef config fill:#f3e5f5
    class A1,A2,B1,B2,B3,C1,C2,C3,D1,D2,D3 config
```

**Problems with Current Architecture**:
- **No Configuration Synchronization**: Changes in one integration don't propagate
- **Inconsistent Schema**: Different configuration formats across integrations
- **Policy Name Conflicts**: Same functionality, different names
- **No Validation**: Invalid configurations discovered at runtime

### Proposed Unified Configuration Architecture

```mermaid
graph TD
    subgraph "Unified Configuration Layer"
        UC[Unified Config Schema]
        CS[Config Store]
        CV[Config Validator]
        CP[Config Propagator]
    end
    
    subgraph "Integration Adapters"
        CA[CLI Adapter]
        MA[MCP Adapter]
        VA[VSCode Adapter]
        GA[CI/CD Adapter]
    end
    
    subgraph "Configuration Sources"
        F1[.connascence.json]
        F2[Environment Variables]
        F3[User Overrides]
    end
    
    F1 --> UC
    F2 --> UC
    F3 --> UC
    
    UC --> CS
    CS --> CV
    CV --> CP
    
    CP --> CA
    CP --> MA
    CP --> VA
    CP --> GA
    
    CA --> E[Core Analyzer]
    MA --> E
    VA --> E
    GA --> E
    
    classDef unified fill:#4caf50
    classDef adapter fill:#2196f3
    classDef source fill:#ff9800
    
    class UC,CS,CV,CP unified
    class CA,MA,VA,GA adapter
    class F1,F2,F3 source
```

---

## Security and Audit Flow

### MCP Server Security Architecture

```mermaid
sequenceDiagram
    participant Client
    participant Gateway as Security Gateway
    participant Auth as Authentication
    participant RateLimit as Rate Limiter
    participant Validator as Path Validator
    participant Analyzer as Core Analyzer
    participant Audit as Audit Logger

    Client->>Gateway: Tool Request
    Gateway->>Auth: Validate session
    Auth->>Auth: Check credentials
    Auth->>RateLimit: Check request limits
    RateLimit->>RateLimit: Update rate counters
    RateLimit->>Validator: Validate request paths
    Validator->>Validator: Sandbox path validation
    Validator->>Analyzer: Execute analysis
    Analyzer->>Audit: Log analysis start
    Analyzer->>Analyzer: Perform analysis
    Analyzer->>Audit: Log analysis complete
    Audit->>Gateway: Return with audit trail
    Gateway->>Client: Secure response

    Note over Gateway: Multi-layer security with<br/>comprehensive audit logging
```

---

## Performance and Scalability Architecture

### Parallel Processing Patterns

```mermaid
graph TD
    subgraph "File Discovery"
        A[Input Path] --> B[File Enumeration]
        B --> C[Filter Application]
        C --> D[File Chunking]
    end
    
    subgraph "Parallel Processing"
        D --> E[Worker Pool]
        E --> F[Worker 1<br/>Files 1-100]
        E --> G[Worker 2<br/>Files 101-200]  
        E --> H[Worker 3<br/>Files 201-300]
        E --> I[Worker N<br/>Files N-M]
    end
    
    subgraph "Result Aggregation"
        F --> J[Result Merger]
        G --> J
        H --> J
        I --> J
        J --> K[Quality Metrics]
        K --> L[Final Report]
    end
    
    classDef discovery fill:#e3f2fd
    classDef parallel fill:#f1f8e9
    classDef aggregation fill:#fce4ec
    
    class A,B,C,D discovery
    class E,F,G,H,I parallel
    class J,K,L aggregation
```

---

## Integration Maturity Assessment

### Feature Implementation Maturity by Integration

```mermaid
graph TD
    subgraph "CLI Integration - 77% Mature"
        CLI1[✅ Batch Processing]
        CLI2[✅ Multi-format Output]
        CLI3[⚠️ Limited Real-time]
        CLI4[❌ No Interactive Features]
    end
    
    subgraph "MCP Server - 75% Mature"
        MCP1[✅ Security Controls]
        MCP2[✅ Audit Logging]
        MCP3[⚠️ Basic Grammar Support]
        MCP4[❌ No Dashboard Features]
    end
    
    subgraph "VSCode Extension - 88% Mature"
        VSC1[✅ Real-time Analysis]
        VSC2[✅ Interactive Dashboard]
        VSC3[✅ Advanced Grammar]
        VSC4[⚠️ Limited Batch Processing]
    end
    
    subgraph "CI/CD Pipeline - 73% Mature"
        CICD1[✅ Automated Workflows]
        CICD2[✅ Quality Gates]
        CICD3[⚠️ Basic NASA Support]
        CICD4[❌ No Connascence Gates]
    end
    
    subgraph "Linter Integration - 35% Mature"
        LINT1[⚠️ Basic ESLint Config]
        LINT2[❌ No Pylint Plugin]
        LINT3[❌ No Ruff Integration]
        LINT4[❌ No IDE Plugins]
    end
    
    classDef high fill:#4caf50
    classDef medium fill:#ff9800
    classDef low fill:#f44336
    
    class CLI1,CLI2,MCP1,MCP2,VSC1,VSC2,VSC3,CICD1,CICD2 high
    class CLI3,MCP3,VSC4,CICD3,LINT1 medium
    class CLI4,MCP4,CICD4,LINT2,LINT3,LINT4 low
```

---

## Recommended Target Architecture

### Unified Integration Framework

```mermaid
graph TD
    subgraph "Core Engine"
        CE[Core Engine<br/>Standardized API]
    end
    
    subgraph "Integration Framework"
        IF[Integration Framework<br/>Common Base Classes]
        CM[Config Manager<br/>Unified Configuration]
        RM[Result Manager<br/>Standard Transformations]
        EM[Event Manager<br/>Cross-Integration Events]
    end
    
    subgraph "Standardized Integrations"
        CLI2[CLI Integration<br/>Framework-based]
        MCP2[MCP Server<br/>Framework-based]
        VSC2[VSCode Extension<br/>Framework-based]
        CICD2[CI/CD Pipeline<br/>Framework-based]
        LINT2[Linter Plugins<br/>Framework-based]
    end
    
    CE --> IF
    IF --> CM
    IF --> RM
    IF --> EM
    
    CM --> CLI2
    CM --> MCP2
    CM --> VSC2
    CM --> CICD2
    CM --> LINT2
    
    RM --> CLI2
    RM --> MCP2
    RM --> VSC2
    RM --> CICD2
    RM --> LINT2
    
    EM --> CLI2
    EM --> MCP2
    EM --> VSC2
    EM --> CICD2
    EM --> LINT2
    
    classDef core fill:#4caf50
    classDef framework fill:#2196f3
    classDef integration fill:#ff9800
    
    class CE core
    class IF,CM,RM,EM framework
    class CLI2,MCP2,VSC2,CICD2,LINT2 integration
```

This target architecture would provide:
- **Unified Configuration Management**: Single source of truth for settings
- **Standardized Integration API**: Common interface for all integrations
- **Cross-Integration Events**: Coordination between different integration points
- **Framework-based Development**: Reduced code duplication and consistent patterns
- **Plugin Architecture**: Easy addition of new integrations

---

## Implementation Timeline

### Phase 1: Foundation (90 days)
- Unified configuration schema
- Standard integration base classes
- Policy name standardization

### Phase 2: Feature Parity (180 days)
- Add missing features to each integration
- Implement cross-integration testing
- Create migration tools

### Phase 3: Advanced Architecture (365 days)
- Plugin framework implementation
- Advanced cross-integration coordination
- Performance optimization and scalability

This architectural analysis provides the roadmap for evolving the connascence analyzer from a collection of independent integrations into a cohesive, enterprise-ready analysis platform.