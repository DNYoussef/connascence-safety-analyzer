# Component Integration Guide

## Overview

This guide provides detailed information on how components within the Connascence Safety Analyzer integrate with each other, including actual import paths, module relationships, and interface contracts.

## Core Module Integration

### 1. Unified Import Strategy

**Central Component**: `core/unified_imports.py`

The system uses a centralized import management strategy that eliminates scattered try/except import patterns:

```python
# Standard import pattern
from core.unified_imports import IMPORT_MANAGER, ImportSpec

# Import with fallbacks
spec = ImportSpec(
    module_name="analyzer.unified_analyzer",
    attribute_name="UnifiedConnascenceAnalyzer",
    fallback_modules=["analyzer.core"],
    required=False
)
result = IMPORT_MANAGER.import_module(spec)
```

**Search Paths Configuration**:
```python
# Automatically added paths
base_path = Path(__file__).parent.parent
paths = [
    base_path,
    base_path / "analyzer",      # Core analysis components
    base_path / "mcp",          # MCP server interface
    base_path / "utils",        # Shared utilities
    base_path / "config",       # Configuration management
    base_path / "integrations", # External tool integrations
    base_path / "autofix",      # Auto-fix suggestions
    base_path / "grammar",      # Grammar enhancement
    base_path / "experimental/src"  # Experimental features
]
```

### 2. Core Analysis Engine Integration

**Primary Entry Point**: `analyzer/core.py`

```python
# Integration with unified import manager
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.unified_imports import IMPORT_MANAGER, ImportSpec

# Constants import with fallback
constants_result = IMPORT_MANAGER.import_constants()
if constants_result.has_module:
    constants = constants_result.module
    NASA_COMPLIANCE_THRESHOLD = getattr(constants, 'NASA_COMPLIANCE_THRESHOLD', 0.95)

# Analyzer import with fallback
analyzer_result = IMPORT_MANAGER.import_unified_analyzer()
if analyzer_result.has_module:
    UnifiedConnascenceAnalyzer = analyzer_result.module
```

**Fallback Chain**:
1. `analyzer.unified_analyzer.UnifiedConnascenceAnalyzer` (primary)
2. `analyzer.core` (fallback mode)
3. Mock mode (minimal functionality)

### 3. Analyzer Orchestrator Integration

**Component**: `analyzer/ast_engine/analyzer_orchestrator.py`

Coordinates parallel execution of specialized analyzers:

```python
class AnalyzerOrchestrator:
    analyzers = [
        PositionAnalyzer,    # Parameter order dependencies
        MeaningAnalyzer,     # Magic numbers and literals
        AlgorithmAnalyzer,   # Duplicated algorithms
        GodObjectAnalyzer,   # Class complexity violations
        MultiLanguageAnalyzer # Cross-language support
    ]
    
    def analyze(self, ast_trees: List[AST]) -> List[Violation]:
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(analyzer().analyze, ast_trees): analyzer.__name__
                for analyzer in self.analyzers
            }
            # Collect and merge results
```

## MCP Server Integration

### 1. Server Interface

**Primary Module**: `mcp/server.py`

**Key Integration Points**:
```python
# Shared utilities import
from utils.config_loader import ConnascenceViolation, RateLimiter, load_config_defaults
from analyzer.constants import resolve_policy_name, validate_policy_name

# Error handling integration
from analyzer.unified_analyzer import StandardError, ErrorHandler
```

**Tool Registration Pattern**:
```python
def _register_tools(self):
    tools = {
        'scan_path': {
            'name': 'scan_path',
            'description': 'Analyze a file or directory for connascence violations',
            'inputSchema': {
                'type': 'object',
                'properties': {
                    'path': {'type': 'string'},
                    'policy': {'type': 'string', 'default': 'default'}
                },
                'required': ['path']
            }
        }
        # ... other tools
    }
```

**Integration with Core Analyzer**:
```python
# Analysis execution
def _execute_scan_path(self, arguments: Dict[str, Any]):
    path = arguments.get('path')
    policy = arguments.get('policy', 'standard')
    
    # Policy resolution via unified constants
    unified_policy = resolve_policy_name(policy, warn_deprecated=True)
    legacy_policy = get_legacy_policy_name(unified_policy, "mcp")
    
    # Delegate to analyzer
    result = self.analyzer.analyze_path(path, profile=legacy_policy)
```

### 2. Error Handling Integration

**Standardized Error Responses**:
```python
class ErrorHandler:
    def __init__(self, integration: str):
        self.integration = integration
    
    def create_error(self, error_type: str, message: str, **kwargs) -> StandardError:
        return StandardError(
            code=ERROR_CODE_MAPPING.get(error_type, 5001),
            message=message,
            integration=self.integration,
            **kwargs
        )
```

## VS Code Extension Integration

### 1. Extension Architecture

**Main Entry Point**: `vscode-extension/src/extension.ts`

**Core Component Initialization**:
```typescript
import { ConnascenceExtension } from './core/ConnascenceExtension';
import { ConnascenceService } from './services/connascenceService';
import { VisualHighlightingManager } from './features/visualHighlighting';
import { NotificationManager } from './features/notificationManager';
import { BrokenChainLogoManager } from './features/brokenChainLogo';
import { AIFixSuggestionsProvider } from './features/aiFixSuggestions';

export function activate(context: vscode.ExtensionContext) {
    // Initialize core services
    extension = new ConnascenceExtension(context, logger, telemetry);
    
    // Initialize feature managers
    visualHighlighting = new VisualHighlightingManager();
    notificationManager = NotificationManager.getInstance();
    brokenChainLogo = BrokenChainLogoManager.getInstance();
    aiFixSuggestions = AIFixSuggestionsProvider.getInstance();
}
```

### 2. Service Integration Pattern

**Connascence Service Integration**:
```typescript
class ConnascenceService {
    async analyzeFile(document: TextDocument): Promise<Violation[]> {
        const analysisRequest = {
            code: document.getText(),
            language: document.languageId,
            policy: this.getActivePolicy()
        };
        
        // Integration with MCP server or direct analysis
        return await this.mcpServer.analyze(analysisRequest);
    }
}
```

**Configuration Integration**:
```typescript
// Multi-layer configuration
const config = vscode.workspace.getConfiguration('connascence');
const safetyProfile = config.get<string>('safetyProfile', 'modern_general');
const realTimeAnalysis = config.get<boolean>('realTimeAnalysis', true);
const debounceMs = config.get<number>('debounceMs', 1000);
```

### 3. Provider Pattern Integration

**Dashboard Provider**:
```typescript
class ConnascenceDashboardProvider implements vscode.TreeDataProvider<DashboardItem> {
    constructor(private connascenceService: ConnascenceService) {}
    
    getTreeItem(element: DashboardItem): vscode.TreeItem {
        return element;
    }
    
    getChildren(element?: DashboardItem): Promise<DashboardItem[]> {
        if (!element) {
            return this.getRootElements();
        }
        return this.getElementChildren(element);
    }
    
    updateData(metrics: QualityMetrics, violations: Violation[] | null) {
        // Update internal data model
        this._onDidChangeTreeData.fire();
    }
}
```

## CLI Integration

### 1. Node.js CLI Interface

**Configuration**: `cli/package.json`

```json
{
  "name": "@connascence/cli",
  "main": "dist/index.js",
  "bin": {
    "connascence": "./dist/index.js",
    "connascence-mcp": "./dist/mcp-server.js"
  },
  "dependencies": {
    "commander": "^11.1.0",
    "@anthropic-ai/sdk": "^0.17.1",
    "express": "^4.18.2"
  }
}
```

**Integration with Core**:
```typescript
// TypeScript CLI that shells to Python core
import { spawn } from 'child_process';

export async function analyzeProject(options: AnalysisOptions): Promise<AnalysisResult> {
    const pythonProcess = spawn('python', [
        '-m', 'analyzer.core',
        '--path', options.path,
        '--policy', options.policy,
        '--format', 'json'
    ]);
    
    // Process output and return structured results
}
```

## Inter-Component Communication Patterns

### 1. Synchronous Integration (CLI ↔ Core)

```python
# Direct module import and execution
analyzer = ConnascenceAnalyzer()
result = analyzer.analyze_path(path='./src', policy='nasa_jpl_pot10')
```

### 2. Asynchronous Integration (VS Code ↔ MCP)

```typescript
// Event-driven communication
vscode.workspace.onDidChangeTextDocument(async (event) => {
    if (config.get<boolean>('realTimeAnalysis', true)) {
        const violations = await connascenceService.analyzeDocument(event.document);
        diagnosticCollection.set(event.document.uri, violations);
    }
});
```

### 3. Service Communication (MCP Server)

```python
# Async tool execution
async def scan_path(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
    # Rate limiting
    if not self.rate_limiter.check_rate_limit(client_id):
        raise Exception("Rate limit exceeded")
    
    # Path validation
    if not self.validate_path(arguments.get('path')):
        raise ValueError("Path not allowed")
    
    # Analysis delegation
    return await self.analyzer.analyze_directory(arguments.get('path'))
```

## Configuration Integration

### 1. Unified Policy Management

**Constants Module**: `analyzer/constants.py`

```python
UNIFIED_POLICY_NAMES = {
    'nasa-compliance': 'NASA JPL Power of Ten compliance',
    'strict': 'Strict code quality standards',
    'standard': 'Balanced service defaults',
    'lenient': 'Relaxed experimental settings'
}

def resolve_policy_name(input_policy: str, warn_deprecated: bool = True) -> str:
    # Legacy to unified mapping
    legacy_mappings = {
        'nasa_jpl_pot10': 'nasa-compliance',
        'strict-core': 'strict',
        'service-defaults': 'standard',
        'experimental': 'lenient'
    }
    return legacy_mappings.get(input_policy, input_policy)
```

### 2. Multi-Layer Configuration

**VS Code Extension Configuration**:
```json
{
  "connascence.safetyProfile": {
    "type": "string",
    "enum": ["none", "general_safety_strict", "safety_level_1", "safety_level_3", "modern_general"],
    "default": "modern_general"
  },
  "connascence.linterIntegration": {
    "type": "object",
    "properties": {
      "enableRuffCorrelation": {"type": "boolean", "default": true},
      "enablePylintCorrelation": {"type": "boolean", "default": true}
    }
  }
}
```

## Error Handling Integration

### 1. Standardized Error Responses

```python
class StandardError:
    def __init__(self, code: int, message: str, integration: str, **kwargs):
        self.code = code
        self.message = message
        self.integration = integration
        self.context = kwargs
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'code': self.code,
            'message': self.message,
            'integration': self.integration,
            'context': self.context
        }
```

### 2. Integration-Specific Error Handling

```python
# MCP Server errors
def _create_async_error_response(self, error: StandardError) -> Dict[str, Any]:
    return {
        'success': False,
        'error': error.to_dict(),
        'summary': {'total_violations': 0, 'critical_count': 0},
        'violations': [],
        'scan_metadata': {'error': True, 'timestamp': time.time()}
    }
```

## Performance Optimization Integration

### 1. Caching Strategy

```python
# Unified Import Manager caching
class UnifiedImportManager:
    def __init__(self):
        self._import_cache: Dict[str, ImportResult] = {}
    
    def import_module(self, spec: ImportSpec) -> ImportResult:
        cache_key = f"{spec.module_name}::{spec.attribute_name or ''}"
        if cache_key in self._import_cache:
            return self._import_cache[cache_key]
        # ... perform import and cache result
```

### 2. Parallel Processing

```python
# Analyzer orchestrator parallel execution
def analyze(self, ast_trees: List[AST]) -> List[Violation]:
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(analyzer().analyze, ast_trees): analyzer_type
            for analyzer_type, analyzer in self.analyzers.items()
        }
        # Collect results in parallel
```

### 3. Resource Management

```typescript
// VS Code extension resource management
export function deactivate() {
    visualHighlighting?.dispose();
    brokenChainLogo?.dispose();
    extension?.dispose();
    telemetry?.dispose();
    logger?.dispose();
}
```

## Testing Integration

### 1. Mock Integration Points

```python
# MCP Server testing
class MockAnalyzer:
    def analyze_directory(self, path: str, profile: str = None) -> List[ConnascenceViolation]:
        return [
            ConnascenceViolation(
                id="test_violation",
                rule_id="CON_CoM",
                connascence_type="CoM",
                severity="medium",
                description="Test magic literal",
                file_path=f"{path}/test_file.py",
                line_number=42
            )
        ]
```

### 2. Integration Test Patterns

```python
# Core analyzer integration testing
def test_analyze_path_integration():
    analyzer = ConnascenceAnalyzer()
    result = analyzer.analyze_path('./test_fixtures/sample_code.py')
    
    assert result['success'] is True
    assert len(result['violations']) > 0
    assert 'nasa_compliance' in result
    assert 'mece_analysis' in result
```

This integration guide provides the foundation for understanding how components communicate and depend on each other within the Connascence Safety Analyzer system.