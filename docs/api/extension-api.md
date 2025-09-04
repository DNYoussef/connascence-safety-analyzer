# Extension API Documentation

This document describes the internal API architecture of the Connascence Safety Analyzer extension.

## 🏗️ Architecture Overview

The extension follows a MECE (Mutually Exclusive, Collectively Exhaustive) architecture with the following core components:

### Core Services

#### ConnascenceService
- **Purpose**: Core analysis logic and violation detection
- **Location**: `src/services/connascenceService.ts`
- **Key Methods**:
  - `analyzeFile(uri: vscode.Uri): Promise<AnalysisResult>`
  - `analyzeWorkspace(): Promise<Map<string, AnalysisResult>>`
  - `suggestRefactoring(file: string, range: vscode.Range): Promise<Suggestion[]>`

#### AIIntegrationService  
- **Purpose**: AI-powered features and MCP client integration
- **Location**: `src/services/aiIntegrationService.ts`
- **Key Methods**:
  - `requestAIFix(finding: Finding): Promise<void>`
  - `getAISuggestions(finding: Finding): Promise<void>`
  - `getAIExplanation(finding: Finding): Promise<void>`

### Providers

#### VisualProvider
- **Purpose**: All visual highlighting and decorations
- **Location**: `src/providers/visualProvider.ts` 
- **Responsibilities**:
  - Color-coded violation highlighting
  - Diagnostic creation and management
  - Visual decoration updates

#### HoverProvider
- **Purpose**: Enhanced hover tooltips with AI integration
- **Location**: `src/providers/hoverProvider.ts`
- **Features**:
  - Violation explanations
  - AI suggestion previews
  - Confidence scoring
  - Quick action buttons

#### MarkdownTableOfContentsProvider
- **Purpose**: Sidebar markdown file navigation
- **Location**: `src/providers/markdownTableOfContentsProvider.ts`
- **Features**:
  - Hierarchical file organization
  - Click-to-open functionality
  - File creation and preview

### UI Components

#### UIManager
- **Purpose**: Unified UI management
- **Location**: `src/ui/uiManager.ts`
- **Responsibilities**:
  - Dashboard webview
  - AI chat interface
  - Status bar updates
  - Notification management

#### HelpProvider
- **Purpose**: Comprehensive documentation system
- **Location**: `src/services/helpProvider.ts`
- **Features**:
  - Interactive help documentation
  - Quick start guides
  - Contextual tutorials

## 📊 Data Flow

```
File Change → AnalysisManager → ConnascenceService → VisualProvider
                                     ↓
                            AIIntegrationService ← HoverProvider
                                     ↓
                                UIManager (Dashboard)
```

## 🔌 Extension Points

### Commands

All extension commands are registered in `ConnascenceExtension.ts`:

```typescript
// Analysis Commands
'connascence.analyzeFile'
'connascence.analyzeWorkspace'
'connascence.showDashboard'

// AI Commands  
'connascence.requestAIFix'
'connascence.getAISuggestions'
'connascence.aiExplain'

// Help Commands
'connascence.showHelp'
'connascence.showQuickStart'

// Markdown Commands
'connascence.refreshMarkdownTOC'
'connascence.createMarkdownFile'
'connascence.openMarkdownFile'
```

### Configuration

Settings are managed through `ConfigurationService`:

```typescript
// Core Settings
'connascence.realTimeAnalysis': boolean
'connascence.debounceMs': number  
'connascence.maxDiagnostics': number

// AI Settings
'connascence.aiIntegration': boolean
'connascence.serverUrl': string
'connascence.ai.cacheSize': number
'connascence.ai.cacheTTL': number

// Visual Settings
'connascence.enableVisualHighlighting': boolean
'connascence.highlightingIntensity': 'subtle' | 'normal' | 'bright'
'connascence.showEmojis': boolean
```

### Events

The extension listens for several VS Code events:

- `onDidChangeTextDocument`: Real-time analysis
- `onDidSaveTextDocument`: Full file analysis
- `onDidChangeConfiguration`: Settings updates
- `onDidChangeWorkspaceFolders`: Workspace changes

## 🎯 Key Interfaces

### Finding
```typescript
interface Finding {
    id: string;
    type: string;
    severity: 'critical' | 'major' | 'minor' | 'info';
    message: string;
    file: string;
    line: number;
    column?: number;
    suggestion?: string;
}
```

### AnalysisResult
```typescript
interface AnalysisResult {
    findings: Finding[];
    qualityScore: number;
    summary: {
        issuesBySeverity: Record<string, number>;
        issuesByType: Record<string, number>;
    };
    timestamp: number;
}
```

### CacheEntry
```typescript
interface CacheEntry<T> {
    data: T;
    timestamp: number;
    ttl: number;
    accessCount: number;
    lastAccess: number;
}
```

## 🚀 Performance Optimizations

### Caching Strategy
- **Fix Cache**: AI-generated fixes with confidence-based TTL
- **Suggestion Cache**: Refactoring suggestions with 5-minute TTL
- **Explanation Cache**: Theory explanations with 10-minute TTL  
- **Context Cache**: Code context with 2.5-minute TTL

### Debouncing
- Real-time analysis debounced to 1000ms (configurable)
- UI updates batched for performance
- File watching optimized to avoid excessive scanning

### Memory Management
- LRU eviction for cache entries
- Automatic cleanup intervals (1 minute)
- Disposable pattern throughout for proper cleanup

## 🧪 Testing Hooks

The extension provides several testing utilities:

- `connascence.clearCache`: Reset all caches for testing
- `connascence.showCacheStats`: View cache performance metrics
- Development mode logging with detailed analysis timing

## 🔧 Extension Development

### Adding New Violation Types

1. Update `ConnascenceService.analyzeContent()`
2. Add severity mapping in `VisualProvider`
3. Update hover explanations in `HoverProvider`
4. Add AI response patterns in `UIManager`

### Adding New AI Features

1. Extend `AIIntegrationService` with new methods
2. Add MCP client integration if needed
3. Update cache strategies as appropriate
4. Register new commands in `ConnascenceExtension`

### Extending the UI

1. Update `UIManager` for new webview features
2. Add CSS styling with VS Code theme variables
3. Implement message passing for interactivity
4. Add error handling and loading states

This API documentation covers the main extension points and architecture. For implementation details, refer to the individual source files.