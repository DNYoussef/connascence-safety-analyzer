# VS Code Extension Developer Guide

**Complete guide for developing with and extending the Connascence Safety Analyzer VS Code Extension**

## Overview

The Connascence Safety Analyzer VS Code Extension provides real-time code analysis, visual highlighting, and AI-powered suggestions for improving code quality by reducing coupling.

**Key Features:**
- Real-time connascence violation detection
- Visual highlighting with severity-based colors
- Interactive dashboard with quality metrics
- AI-powered fix suggestions and explanations
- NASA Power of Ten compliance checking
- Broken chain logo and animations
- MECE duplication analysis

---

## Extension Architecture

### Core Components

#### 1. Extension Entry Point
**File:** `src/extension.ts`

```typescript
export function activate(context: vscode.ExtensionContext) {
  // Initialize core services
  const extension = new ConnascenceExtension(context, logger, telemetry);
  
  // Initialize feature managers
  initializeFeatureManagers(context);
  
  // Register tree data providers
  initializeTreeProviders(context);
  
  // Register commands
  registerAllCommands(context);
  
  // Start background services
  startBackgroundServices(context);
}
```

#### 2. Core Extension Class
**File:** `src/core/ConnascenceExtension.ts`

The main extension coordinator that manages all services and features.

#### 3. Service Layer
**Files:** `src/services/`

##### `ConnascenceService`
Primary analysis coordination service:

```typescript
class ConnascenceService {
  constructor(
    private configService: ConfigurationService,
    private telemetryService: TelemetryService
  )
  
  // Core analysis methods
  async analyzeFile(filePath: string): Promise<AnalysisResult>
  async analyzeWorkspace(workspacePath: string): Promise<WorkspaceAnalysisResult>
  async validateSafety(filePath: string, profile: string): Promise<SafetyValidationResult>
  async suggestRefactoring(filePath: string, selection?: Range): Promise<RefactoringSuggestion[]>
  async getAutofixes(filePath: string): Promise<AutoFix[]>
  
  // Advanced features
  private async enhanceAnalysisResult(baseResult: AnalysisResult, filePath: string): Promise<AnalysisResult>
  private async runMECEAnalysis(projectPath: string): Promise<DuplicationCluster[]>
  private async checkNASACompliance(findings: Finding[]): Promise<NASAComplianceResult>
}
```

##### `ConnascenceApiClient`
Handles backend integration:

```typescript
class ConnascenceApiClient {
  // Unified analyzer integration
  private async runUnifiedAnalyzer(options: any): Promise<any>
  
  // Fallback analysis when Python is unavailable
  private async fallbackAnalyzeFile(filePath: string): Promise<AnalysisResult>
  
  // Configuration helpers
  private getSafetyProfile(): string
  private getExcludePatterns(): string[]
}
```

##### `ConfigurationService`
**File:** `src/services/configurationService.ts`

Manages VS Code settings and workspace configuration.

##### `TelemetryService`
**File:** `src/services/telemetryService.ts`

Handles analytics and usage tracking.

#### 4. Providers
**Files:** `src/providers/`

##### `ConnascenceDashboardProvider`
**File:** `src/providers/dashboardProvider.ts`

Tree view provider for the dashboard sidebar:

```typescript
class ConnascenceDashboardProvider implements vscode.TreeDataProvider<DashboardItem> {
  constructor(private connascenceService: ConnascenceService)
  
  getTreeItem(element: DashboardItem): vscode.TreeItem
  getChildren(element?: DashboardItem): Thenable<DashboardItem[]>
  updateData(metrics: QualityMetrics, trendData: any): void
  refresh(): void
}
```

##### `AnalysisResultsProvider`
**File:** `src/providers/analysisResultsProvider.ts`

Tree view provider for analysis results with grouping:

```typescript
class AnalysisResultsProvider implements vscode.TreeDataProvider<ResultItem> {
  setGroupBy(groupBy: 'file' | 'severity' | 'type'): void
  refresh(): void
  updateResults(results: AnalysisResult[]): void
}
```

#### 5. Feature Managers
**Files:** `src/features/`

##### `VisualHighlightingManager`
**File:** `src/features/visualHighlighting.ts`

Handles code highlighting and decorations:

```typescript
class VisualHighlightingManager {
  updateHighlighting(editor: vscode.TextEditor, findings: Finding[]): void
  private createDecorationTypes(): void
  private getDecorationForSeverity(severity: string): vscode.TextEditorDecorationType
}
```

##### `NotificationManager`
**File:** `src/features/notificationManager.ts`

Manages user notifications and filtering:

```typescript
class NotificationManager {
  static getInstance(): NotificationManager
  showFilterManagementQuickPick(): void
  shouldShowNotification(type: string): boolean
}
```

##### `BrokenChainLogoManager`
**File:** `src/features/brokenChainLogo.ts`

Manages the broken chain logo and animations:

```typescript
class BrokenChainLogoManager {
  static getInstance(): BrokenChainLogoManager
  showBrokenChainAnimation(): void
  updateLogoBasedOnQuality(qualityScore: number): void
}
```

##### `AIFixSuggestionsProvider`
**File:** `src/features/aiFixSuggestions.ts`

Provides AI-powered fix suggestions:

```typescript
class AIFixSuggestionsProvider {
  static getInstance(): AIFixSuggestionsProvider
  getSuggestionsForFinding(finding: Finding): Promise<FixSuggestion[]>
  applyFix(fix: FixSuggestion, document: vscode.TextDocument): Promise<boolean>
}
```

---

## Extension Configuration

### VS Code Settings Schema

The extension uses these VS Code settings (defined in `package.json`):

```json
{
  "configuration": {
    "properties": {
      "connascence.safetyProfile": {
        "type": "string",
        "enum": ["none", "general_safety_strict", "safety_level_1", "safety_level_3", "modern_general"],
        "default": "modern_general",
        "description": "Safety profile for analysis"
      },
      "connascence.realTimeAnalysis": {
        "type": "boolean",
        "default": true,
        "description": "Enable real-time analysis as you type"
      },
      "connascence.debounceMs": {
        "type": "number",
        "default": 1000,
        "description": "Debounce time for real-time analysis (ms)"
      },
      "connascence.maxDiagnostics": {
        "type": "number",
        "default": 1500,
        "description": "Maximum diagnostics to show"
      },
      "connascence.enableVisualHighlighting": {
        "type": "boolean",
        "default": true,
        "description": "Enable visual code highlighting"
      },
      "connascence.threshold": {
        "type": "number",
        "default": 0.8,
        "description": "Quality threshold for analysis"
      },
      "connascence.strictMode": {
        "type": "boolean",
        "default": false,
        "description": "Enable strict analysis mode"
      },
      "connascence.includeTests": {
        "type": "boolean",
        "default": false,
        "description": "Include test files in analysis"
      },
      "connascence.exclude": {
        "type": "array",
        "items": { "type": "string" },
        "default": ["node_modules/**", "**/__pycache__/**"],
        "description": "File patterns to exclude"
      },
      "connascence.pythonPath": {
        "type": "string",
        "description": "Path to Python executable"
      },
      "connascence.enableParallelProcessing": {
        "type": "boolean",
        "default": true,
        "description": "Enable parallel analysis processing"
      },
      "connascence.maxWorkers": {
        "type": "number",
        "default": 4,
        "description": "Maximum worker processes for parallel analysis"
      }
    }
  }
}
```

### Type Definitions

#### Core Types
**File:** `src/types/index.ts`

```typescript
interface ConnascenceConfiguration {
  safetyProfile: 'none' | 'general_safety_strict' | 'safety_level_1' | 'safety_level_3' | 'modern_general';
  realTimeAnalysis: boolean;
  debounceMs: number;
  maxDiagnostics: number;
  threshold: number;
  strictMode: boolean;
  includeTests: boolean;
  exclude: string[];
  pythonPath?: string;
  
  // Advanced configuration
  confidenceThreshold: number;
  nasaComplianceThreshold: number;
  meceQualityThreshold: number;
  performanceAnalysis: PerformanceAnalysisConfig;
  advancedFiltering: AdvancedFilteringConfig;
  analysisDepth: 'surface' | 'standard' | 'deep' | 'comprehensive';
  enableExperimentalFeatures: boolean;
  customRules: CustomAnalysisRule[];
}

interface AnalysisResult {
  findings: Finding[];
  qualityScore: number;
  summary: {
    totalIssues: number;
    issuesBySeverity: {
      critical: number;
      major: number;
      minor: number;
      info: number;
    };
  };
  // Enhanced capabilities
  performanceMetrics?: PerformanceMetrics;
  duplicationClusters?: DuplicationCluster[];
  nasaCompliance?: NASAComplianceResult;
  smartIntegrationResults?: SmartIntegrationResult;
}

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

---

## Development Workflow

### Setting Up Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-org/connascence-analyzer.git
   cd connascence-analyzer/vscode-extension
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Build the extension:**
   ```bash
   npm run compile
   ```

4. **Run tests:**
   ```bash
   npm run test
   ```

5. **Launch extension development host:**
   - Press `F5` in VS Code
   - Or run `npm run dev`

### Project Structure
```
vscode-extension/
├── src/
│   ├── core/              # Core extension logic
│   ├── services/          # Business logic services
│   ├── providers/         # Tree view and content providers
│   ├── features/          # Feature-specific managers
│   ├── ui/               # UI components and managers
│   ├── utils/            # Utility functions
│   ├── types/            # TypeScript type definitions
│   └── extension.ts      # Extension entry point
├── package.json          # Extension manifest
├── tsconfig.json         # TypeScript configuration
└── README.md
```

### Key Development Commands

```bash
# Build extension
npm run compile

# Watch mode during development
npm run watch

# Run tests
npm run test

# Lint code
npm run lint

# Package extension
vsce package
```

---

## Extending the Extension

### Adding New Violation Types

1. **Update the analyzer backend** to detect the new violation type
2. **Add type definition** in `src/types/index.ts`:
   ```typescript
   interface CustomViolation extends Finding {
     customProperty: string;
   }
   ```

3. **Update severity mapping** in `ConnascenceApiClient`:
   ```typescript
   private mapSeverity(severity: string): 'critical' | 'major' | 'minor' | 'info' {
     const severityMap = {
       'your_new_type': 'major',
       // ... existing mappings
     };
     return severityMap[severity] || 'info';
   }
   ```

4. **Add visual highlighting** in `VisualHighlightingManager`:
   ```typescript
   private getDecorationForSeverity(severity: string): vscode.TextEditorDecorationType {
     switch (severity) {
       case 'your_new_type':
         return this.customDecorationTypes.yourNewType;
       // ... existing cases
     }
   }
   ```

### Adding New Commands

1. **Register command** in `src/extension.ts`:
   ```typescript
   const myNewCommand = vscode.commands.registerCommand('connascence.myNewCommand', () => {
     // Command implementation
   });
   context.subscriptions.push(myNewCommand);
   ```

2. **Add command to `package.json`:**
   ```json
   {
     "commands": [
       {
         "command": "connascence.myNewCommand",
         "title": "My New Command",
         "category": "Connascence"
       }
     ]
   }
   ```

### Adding New Configuration Options

1. **Add to VS Code settings schema** in `package.json`:
   ```json
   {
     "connascence.myNewSetting": {
       "type": "boolean",
       "default": false,
       "description": "My new setting description"
     }
   }
   ```

2. **Update TypeScript types** in `src/types/index.ts`:
   ```typescript
   interface ConnascenceConfiguration {
     myNewSetting: boolean;
     // ... existing properties
   }
   ```

3. **Use in services:**
   ```typescript
   class MyService {
     private getMyNewSetting(): boolean {
       const config = vscode.workspace.getConfiguration('connascence');
       return config.get('myNewSetting', false);
     }
   }
   ```

### Adding New Providers

1. **Create provider class:**
   ```typescript
   class MyTreeProvider implements vscode.TreeDataProvider<MyItem> {
     private _onDidChangeTreeData = new vscode.EventEmitter<MyItem | undefined | null | void>();
     readonly onDidChangeTreeData = this._onDidChangeTreeData.event;
     
     getTreeItem(element: MyItem): vscode.TreeItem {
       return element;
     }
     
     getChildren(element?: MyItem): Thenable<MyItem[]> {
       // Implementation
     }
     
     refresh(): void {
       this._onDidChangeTreeData.fire();
     }
   }
   ```

2. **Register provider** in `src/extension.ts`:
   ```typescript
   const myProvider = new MyTreeProvider();
   vscode.window.registerTreeDataProvider('myView', myProvider);
   ```

3. **Add view to `package.json`:**
   ```json
   {
     "views": {
       "connascence": [
         {
           "id": "myView",
           "name": "My View",
           "when": "workspaceHasConnascenceFiles"
         }
       ]
     }
   }
   ```

---

## Testing and Debugging

### Unit Testing

**Test Files:** `src/test/`

```typescript
import * as assert from 'assert';
import * as vscode from 'vscode';
import { ConnascenceService } from '../services/connascenceService';

describe('ConnascenceService', () => {
  test('should analyze file successfully', async () => {
    const service = new ConnascenceService(mockConfigService, mockTelemetryService);
    const result = await service.analyzeFile('/path/to/test/file.py');
    
    assert.ok(result);
    assert.ok(result.findings);
    assert.strictEqual(typeof result.qualityScore, 'number');
  });
});
```

Run tests:
```bash
npm run test
```

### Integration Testing

**File:** `src/test/integration.test.ts`

```typescript
describe('Extension Integration Tests', () => {
  test('should activate extension successfully', async () => {
    const extension = vscode.extensions.getExtension('connascence.connascence-analyzer');
    assert.ok(extension);
    
    await extension.activate();
    assert.ok(extension.isActive);
  });
  
  test('should register all commands', async () => {
    const commands = await vscode.commands.getCommands(true);
    assert.ok(commands.includes('connascence.analyzeFile'));
    assert.ok(commands.includes('connascence.showDashboard'));
  });
});
```

### Debugging

1. **Enable debug mode** in VS Code settings:
   ```json
   {
     "connascence.debugMode": true
   }
   ```

2. **Use debug logging:**
   ```typescript
   import { ExtensionLogger } from './utils/logger';
   
   const logger = new ExtensionLogger('MyComponent');
   logger.debug('Debug message', { context: 'additional data' });
   logger.info('Info message');
   logger.error('Error message', error);
   ```

3. **Set breakpoints** in TypeScript source files
4. **Use VS Code debugger** with F5 to launch extension development host

---

## Performance Optimization

### Caching Strategy

The extension implements multiple caching layers:

```typescript
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
  accessCount: number;
  lastAccess: number;
}

class AnalysisCache {
  private fixCache = new Map<string, CacheEntry<FixSuggestion[]>>();
  private suggestionCache = new Map<string, CacheEntry<RefactoringSuggestion[]>>();
  
  get(key: string, cache: Map<string, CacheEntry<any>>): any | null {
    const entry = cache.get(key);
    if (!entry || this.isExpired(entry)) {
      cache.delete(key);
      return null;
    }
    
    entry.accessCount++;
    entry.lastAccess = Date.now();
    return entry.data;
  }
}
```

### Debouncing

Real-time analysis uses debouncing to prevent excessive API calls:

```typescript
class DebounceManager {
  private debounceTimers = new Map<string, NodeJS.Timeout>();
  
  debounce(key: string, fn: () => void, delay: number): void {
    if (this.debounceTimers.has(key)) {
      clearTimeout(this.debounceTimers.get(key)!);
    }
    
    const timer = setTimeout(() => {
      fn();
      this.debounceTimers.delete(key);
    }, delay);
    
    this.debounceTimers.set(key, timer);
  }
}
```

### Memory Management

```typescript
class ResourceManager {
  private disposables: vscode.Disposable[] = [];
  
  register(disposable: vscode.Disposable): void {
    this.disposables.push(disposable);
  }
  
  dispose(): void {
    this.disposables.forEach(d => d.dispose());
    this.disposables.length = 0;
  }
}
```

---

## Best Practices

### Code Organization
- **Separate concerns** - Keep services, providers, and features in separate modules
- **Use dependency injection** - Pass dependencies through constructors
- **Implement proper disposal** - Clean up resources when components are destroyed
- **Handle errors gracefully** - Provide fallbacks when backend is unavailable

### Configuration Management
- **Use workspace configuration** - Respect user and workspace settings
- **Provide sensible defaults** - Extension should work out of the box
- **Validate configuration** - Check for invalid settings and provide warnings

### User Experience
- **Progressive disclosure** - Don't overwhelm users with too many options
- **Provide feedback** - Show progress indicators for long operations
- **Handle offline scenarios** - Graceful degradation when backend is unavailable
- **Respect user preferences** - Allow customization of notifications and features

### Performance
- **Cache analysis results** - Avoid redundant computations
- **Use debouncing** - Limit frequency of real-time analysis
- **Lazy load features** - Initialize components only when needed
- **Monitor memory usage** - Clean up resources promptly

This developer guide provides comprehensive information for working with and extending the Connascence Safety Analyzer VS Code Extension. All APIs and examples are based on the actual codebase implementation.