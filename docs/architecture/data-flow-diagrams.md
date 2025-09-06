# Data Flow Diagrams

## Overview

This document provides comprehensive data flow diagrams showing how data moves through the Connascence Safety Analyzer system, from input processing through analysis to output generation.

## High-Level System Data Flow

```mermaid
graph TD
    A[Source Code Input] --> B[Unified Import Manager]
    B --> C[Multi-Language Parser]
    C --> D[AST Enhancement]
    D --> E[Analyzer Orchestrator]
    
    E --> F[Position Analyzer]
    E --> G[Meaning Analyzer]
    E --> H[Algorithm Analyzer]
    E --> I[God Object Analyzer]
    E --> J[Multi-Language Analyzer]
    
    F --> K[Violation Collection]
    G --> K
    H --> K
    I --> K
    J --> K
    
    K --> L[NASA Compliance Validation]
    K --> M[MECE Analysis Engine]
    K --> N[Quality Gate Evaluation]
    
    L --> O[Output Generation]
    M --> O
    N --> O
    
    O --> P[JSON/SARIF Export]
    O --> Q[VS Code Diagnostics]
    O --> R[MCP Server Response]
    O --> S[CI/CD Artifacts]
```

## Component-Level Data Flow

### 1. Input Processing Pipeline

```mermaid
sequenceDiagram
    participant UI as User Interface (CLI/VSCode/MCP)
    participant UIM as Unified Import Manager
    participant Parser as Multi-Language Parser
    participant AST as AST Enhancement
    
    UI->>UIM: Request analysis (path, policy)
    UIM->>UIM: Resolve dependencies
    UIM->>Parser: Initialize language parsers
    
    Parser->>Parser: Discover source files
    Parser->>AST: Generate Python AST
    Parser->>AST: Generate JavaScript AST
    Parser->>AST: Generate C/C++ AST
    
    AST->>AST: Add context metadata
    AST->>AST: Resolve references
    AST->>UI: Enhanced AST trees
```

### 2. Analysis Engine Data Flow

```mermaid
graph TD
    subgraph "Analyzer Orchestrator"
        A[Enhanced AST Trees] --> B[Thread Pool Executor]
        
        B --> C[Position Analyzer<br/>CoP Detection]
        B --> D[Meaning Analyzer<br/>CoM Detection]
        B --> E[Algorithm Analyzer<br/>CoA Detection]
        B --> F[God Object Analyzer<br/>SOLID Violations]
        B --> G[Multi-Language Analyzer<br/>Cross-language patterns]
        
        C --> H[Violation Results]
        D --> H
        E --> H
        F --> H
        G --> H
    end
    
    H --> I[Violation Consolidation]
    I --> J[Severity Classification]
    J --> K[Context Enhancement]
```

### 3. MECE Analysis Data Flow

```mermaid
stateDiagram-v2
    [*] --> CodeRegistryBuilding: Input: Codebase
    
    state "Phase 1: Code Registry" as CodeRegistryBuilding {
        [*] --> ASTSignatureGeneration
        ASTSignatureGeneration --> FunctionMapping
        FunctionMapping --> ClassMapping
        ClassMapping --> [*]
    }
    
    CodeRegistryBuilding --> ExactDuplicationDetection
    
    state "Phase 2: Exact Duplicates" as ExactDuplicationDetection {
        [*] --> HashComparison
        HashComparison --> ExactMatches
        ExactMatches --> [*]
    }
    
    ExactDuplicationDetection --> SimilarFunctionDetection
    
    state "Phase 3: Similar Functions" as SimilarFunctionDetection {
        [*] --> StructuralAnalysis
        StructuralAnalysis --> SimilarityScoring
        SimilarityScoring --> [*]
    }
    
    SimilarFunctionDetection --> FunctionalOverlapDetection
    
    state "Phase 4: Functional Overlaps" as FunctionalOverlapDetection {
        [*] --> SemanticAnalysis
        SemanticAnalysis --> OverlapIdentification
        OverlapIdentification --> [*]
    }
    
    FunctionalOverlapDetection --> ConsolidationRecommendations
    ConsolidationRecommendations --> MECEOutput: Output: MECE Results
    MECEOutput --> [*]
```

### 4. NASA Compliance Data Flow

```mermaid
graph LR
    A[Violations + AST Trees] --> B[NASA Rules Engine]
    
    subgraph "NASA Power of Ten Rules"
        B --> C[Rule 1: Control Flow]
        B --> D[Rule 2: Loop Bounds]
        B --> E[Rule 3: Heap Usage]
        B --> F[Rule 4: Function Size]
        B --> G[Rule 5: Assertions]
        B --> H[Rule 6: Variable Scope]
        B --> I[Rule 7: Parameter Limits]
        B --> J[Rule 8: Preprocessor]
        B --> K[Rule 9: Pointers]
        B --> L[Rule 10: Warnings]
    end
    
    C --> M[Compliance Scoring]
    D --> M
    E --> M
    F --> M
    G --> M
    H --> M
    I --> M
    J --> M
    K --> M
    L --> M
    
    M --> N[Safety Assessment]
    N --> O[Compliance Report]
```

## Interface-Specific Data Flows

### 1. VS Code Extension Data Flow

```mermaid
sequenceDiagram
    participant Editor as VS Code Editor
    participant Ext as Extension
    participant Service as Connascence Service
    participant MCP as MCP Server
    participant Dashboard as Dashboard Provider
    
    Editor->>Ext: Document changed
    Ext->>Ext: Debounce (1000ms)
    Ext->>Service: Analyze document
    Service->>MCP: scan_path request
    
    MCP->>MCP: Rate limit check
    MCP->>MCP: Path validation
    MCP->>MCP: Run analysis
    MCP->>Service: Analysis results
    
    Service->>Ext: Processed violations
    Ext->>Editor: Update diagnostics
    Ext->>Dashboard: Update metrics
    
    Dashboard->>Dashboard: Refresh tree view
    Dashboard->>Editor: Show quality indicators
```

### 2. MCP Server Request/Response Flow

```mermaid
graph TD
    A[Client Request] --> B[Rate Limiter]
    B --> C{Rate OK?}
    C -->|No| D[Rate Limit Error]
    C -->|Yes| E[Path Validator]
    
    E --> F{Path Valid?}
    F -->|No| G[Path Error]
    F -->|Yes| H[Audit Logger]
    
    H --> I[Tool Router]
    I --> J[scan_path]
    I --> K[explain_finding]
    I --> L[propose_autofix]
    I --> M[list_presets]
    
    J --> N[Core Analyzer]
    K --> O[Explanation Engine]
    L --> P[Autofix Engine]
    M --> Q[Policy Manager]
    
    N --> R[Response Formatter]
    O --> R
    P --> R
    Q --> R
    
    R --> S[JSON Response]
    D --> T[Error Response]
    G --> T
```

### 3. CLI Analysis Flow

```mermaid
graph TD
    A[CLI Command] --> B[Argument Parser]
    B --> C[Configuration Loader]
    C --> D[Core Analyzer Init]
    
    D --> E{Mode Selection}
    E -->|Unified Available| F[Unified Analyzer]
    E -->|Fallback Mode| G[Fallback Analyzer]
    E -->|Mock Mode| H[Mock Analyzer]
    
    F --> I[Project Analysis]
    G --> J[Directory Scan]
    H --> K[Mock Results]
    
    I --> L[Result Processing]
    J --> L
    K --> L
    
    L --> M{Output Format}
    M -->|JSON| N[JSON Reporter]
    M -->|SARIF| O[SARIF Reporter]
    M -->|Console| P[Console Output]
    
    N --> Q[File Output]
    O --> Q
    P --> R[Terminal Display]
```

## Data Transformation Stages

### 1. Input Normalization

```mermaid
graph TD
    A[Raw Source Files] --> B{File Type}
    
    B -->|.py| C[Python AST Parser]
    B -->|.js/.ts| D[JavaScript Parser]
    B -->|.c/.cpp| E[C/C++ Parser]
    
    C --> F[Python AST Tree]
    D --> G[JavaScript AST Tree]
    E --> H[C/C++ AST Tree]
    
    F --> I[Normalized AST Format]
    G --> I
    H --> I
    
    I --> J[Context Enhancement]
    J --> K[Reference Resolution]
    K --> L[Metadata Annotation]
    L --> M[Enhanced AST Trees]
```

### 2. Violation Processing

```mermaid
graph LR
    A[Raw Violations] --> B[Severity Classification]
    
    subgraph "10-Level Severity System"
        B --> C[Level 10: CATASTROPHIC]
        B --> D[Level 9: CRITICAL]
        B --> E[Level 8: MAJOR]
        B --> F[Level 7: SIGNIFICANT]
        B --> G[Level 6: MODERATE]
        B --> H[Level 5: MINOR]
        B --> I[Level 4: TRIVIAL]
        B --> J[Level 3: INFORMATIONAL]
        B --> K[Level 2: ADVISORY]
        B --> L[Level 1: NOTICE]
    end
    
    C --> M[Context Analysis]
    D --> M
    E --> M
    F --> M
    G --> M
    H --> M
    I --> M
    J --> M
    K --> M
    L --> M
    
    M --> N[Weight Calculation]
    N --> O[Priority Ranking]
    O --> P[Grouped Violations]
```

### 3. Output Generation

```mermaid
graph TD
    A[Processed Analysis Results] --> B{Output Target}
    
    B -->|VS Code| C[Diagnostic Collection]
    B -->|MCP Client| D[JSON Response]
    B -->|CLI| E[Format Selection]
    B -->|CI/CD| F[SARIF Generation]
    
    C --> G[VS Code Diagnostics API]
    G --> H[Editor Highlighting]
    G --> I[Problems Panel]
    
    D --> J[MCP Response Format]
    J --> K[Client Processing]
    
    E --> L{Format Type}
    L -->|JSON| M[Structured JSON]
    L -->|SARIF| N[SARIF 2.1.0]
    L -->|Console| O[Human Readable]
    
    F --> P[GitHub Code Scanning]
    P --> Q[Security Advisories]
    P --> R[PR Comments]
```

## Performance Optimization Data Flow

### 1. Caching Strategy

```mermaid
graph TD
    A[Analysis Request] --> B{Cache Hit?}
    
    B -->|Yes| C[Return Cached Result]
    B -->|No| D[Perform Analysis]
    
    D --> E[Generate Result]
    E --> F[Store in Cache]
    F --> G[Return Result]
    
    C --> H[Update Access Time]
    G --> I[Log Performance Metrics]
    H --> I
    
    subgraph "Cache Management"
        J[LRU Eviction]
        K[TTL Expiration]
        L[Manual Invalidation]
        
        F --> J
        F --> K
        F --> L
    end
```

### 2. Parallel Processing Flow

```mermaid
graph TD
    subgraph "Thread Pool Executor"
        A[AST Trees] --> B[Task Queue]
        
        B --> C[Worker Thread 1<br/>Position Analysis]
        B --> D[Worker Thread 2<br/>Meaning Analysis]
        B --> E[Worker Thread 3<br/>Algorithm Analysis]
        B --> F[Worker Thread 4<br/>God Object Analysis]
        B --> G[Worker Thread 5<br/>Multi-Lang Analysis]
        
        C --> H[Result Collection]
        D --> H
        E --> H
        F --> H
        G --> H
    end
    
    H --> I[Result Consolidation]
    I --> J[Violation Deduplication]
    J --> K[Final Results]
```

## Error Handling Data Flow

```mermaid
graph TD
    A[Operation Start] --> B{Try Operation}
    
    B -->|Success| C[Normal Flow]
    B -->|Exception| D[Error Handler]
    
    D --> E{Error Type}
    
    E -->|Validation Error| F[Create Validation Error]
    E -->|Security Error| G[Create Security Error]
    E -->|System Error| H[Create System Error]
    E -->|Unknown Error| I[Create Generic Error]
    
    F --> J[StandardError Object]
    G --> J
    H --> J
    I --> J
    
    J --> K[Log Error]
    K --> L[Create Error Response]
    L --> M[Return Error to Client]
    
    C --> N[Continue Processing]
```

## Real-Time Analysis Data Flow (VS Code)

```mermaid
sequenceDiagram
    participant User as Developer
    participant Editor as VS Code Editor
    participant Ext as Extension
    participant Debouncer as Debounce Manager
    participant Analyzer as Analysis Service
    participant UI as Visual Feedback
    
    User->>Editor: Types code
    Editor->>Ext: onDidChangeTextDocument
    Ext->>Debouncer: Schedule analysis (1000ms delay)
    
    Note over Debouncer: Wait for typing pause
    
    Debouncer->>Analyzer: Trigger analysis
    Analyzer->>Analyzer: Parse changed document
    Analyzer->>Analyzer: Run connascence analysis
    Analyzer->>Ext: Analysis results
    
    Ext->>UI: Update diagnostics
    Ext->>UI: Update highlighting
    Ext->>UI: Update dashboard metrics
    
    UI->>Editor: Show squiggly underlines
    UI->>Editor: Update problems panel
    UI->>Editor: Update status bar
```

## Batch Processing Data Flow (CI/CD)

```mermaid
graph TD
    A[CI/CD Trigger] --> B[Checkout Code]
    B --> C[Install Dependencies]
    C --> D[Run Connascence Analysis]
    
    D --> E[Discover Files]
    E --> F[Parallel Analysis]
    
    subgraph "Parallel Analysis"
        F --> G[Analyze Module 1]
        F --> H[Analyze Module 2]
        F --> I[Analyze Module 3]
        F --> J[Analyze Module N]
    end
    
    G --> K[Collect Results]
    H --> K
    I --> K
    J --> K
    
    K --> L[Quality Gate Check]
    L --> M{Thresholds Met?}
    
    M -->|Yes| N[Generate SARIF Report]
    M -->|No| O[Fail Build]
    
    N --> P[Upload to GitHub Code Scanning]
    P --> Q[Update PR Status]
    Q --> R[Success]
    
    O --> S[Log Failures]
    S --> T[Exit with Error Code]
```

This comprehensive set of data flow diagrams illustrates how data moves through every major component and interface of the Connascence Safety Analyzer system, providing clear visualization of the system's internal workings and integration patterns.