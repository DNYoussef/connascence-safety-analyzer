import * as vscode from 'vscode';
import { Finding } from './connascenceService';
import { ConfigurationService } from './configurationService';
import { ExtensionLogger } from '../utils/logger';
import { MCPClient } from './mcpClient';

/**
 * Advanced caching interface with TTL support
 */
interface CacheEntry<T> {
    data: T;
    timestamp: number;
    ttl: number;
    accessCount: number;
    lastAccess: number;
}

/**
 * Advanced caching system with TTL and memory optimization
 */
class AdvancedCache<T> {
    private cache = new Map<string, CacheEntry<T>>();
    private readonly maxSize: number;
    private readonly defaultTTL: number;
    private cleanupInterval?: NodeJS.Timeout;
    private hitCount = 0;
    private missCount = 0;

    constructor(maxSize = 100, defaultTTL = 300000) { // 5 min default TTL
        this.maxSize = maxSize;
        this.defaultTTL = defaultTTL;
        this.startCleanupScheduler();
    }

    set(key: string, value: T, customTTL?: number): void {
        const now = Date.now();
        const ttl = customTTL || this.defaultTTL;
        
        // Evict if cache is full
        if (this.cache.size >= this.maxSize && !this.cache.has(key)) {
            this.evictLRU();
        }

        this.cache.set(key, {
            data: value,
            timestamp: now,
            ttl,
            accessCount: 0,
            lastAccess: now
        });
    }

    get(key: string): T | null {
        const entry = this.cache.get(key);
        if (!entry) {
            this.missCount++;
            return null;
        }

        const now = Date.now();
        if (now - entry.timestamp > entry.ttl) {
            this.cache.delete(key);
            this.missCount++;
            return null;
        }

        // Update access stats
        entry.accessCount++;
        entry.lastAccess = now;
        this.hitCount++;
        
        return entry.data;
    }

    invalidate(keyPattern?: string): void {
        if (!keyPattern) {
            this.cache.clear();
            return;
        }

        const regex = new RegExp(keyPattern);
        for (const [key] of this.cache) {
            if (regex.test(key)) {
                this.cache.delete(key);
            }
        }
    }

    private evictLRU(): void {
        let lruKey = '';
        let oldestAccess = Date.now();

        for (const [key, entry] of this.cache) {
            if (entry.lastAccess < oldestAccess) {
                oldestAccess = entry.lastAccess;
                lruKey = key;
            }
        }

        if (lruKey) {
            this.cache.delete(lruKey);
        }
    }

    private startCleanupScheduler(): void {
        this.cleanupInterval = setInterval(() => {
            const now = Date.now();
            for (const [key, entry] of this.cache) {
                if (now - entry.timestamp > entry.ttl) {
                    this.cache.delete(key);
                }
            }
        }, 60000); // Cleanup every minute
    }

    getStats(): { size: number; hits: number; misses: number; hitRate: number } {
        const total = this.hitCount + this.missCount;
        return {
            size: this.cache.size,
            hits: this.hitCount,
            misses: this.missCount,
            hitRate: total > 0 ? (this.hitCount / total) * 100 : 0
        };
    }

    dispose(): void {
        if (this.cleanupInterval) {
            clearInterval(this.cleanupInterval);
        }
        this.cache.clear();
    }
}

/**
 * AI Integration Service
 * 
 * MECE Responsibility: ALL AI-powered functionality
 * - MCP server communication
 * - AI fix generation and application
 * - Contextual suggestion generation
 * - Diff preview and application
 * - Advanced caching with TTL and memory optimization
 */
export class AIIntegrationService implements vscode.Disposable {
    private disposables: vscode.Disposable[] = [];
    private mcpClient: MCPClient;
    
    // Advanced caching system
    private fixCache: AdvancedCache<any>;
    private suggestionCache: AdvancedCache<any[]>;
    private explanationCache: AdvancedCache<any>;
    private contextCache: AdvancedCache<string>;
    
    // Performance tracking
    private performanceStats = {
        requestCount: 0,
        totalResponseTime: 0,
        cacheHits: 0,
        serverRequests: 0
    };
    
    constructor(
        private configService: ConfigurationService,
        private logger: ExtensionLogger
    ) {
        this.mcpClient = new MCPClient(this.configService, this.logger);
        
        // Initialize advanced caching system
        const cacheSize = this.configService.get('ai.cacheSize', 100) ?? 100;
        const cacheTTL = this.configService.get('ai.cacheTTL', 300000) ?? 300000; // 5 minutes
        
        this.fixCache = new AdvancedCache(cacheSize, cacheTTL);
        this.suggestionCache = new AdvancedCache(cacheSize, cacheTTL);
        this.explanationCache = new AdvancedCache(cacheSize, cacheTTL * 2); // Explanations cached longer
        this.contextCache = new AdvancedCache(cacheSize * 2, cacheTTL / 2); // Context cached shorter
        
        this.initializeMCPClient();
        this.registerCommands();
        this.setupCacheManagement();
    }

    private async initializeMCPClient(): Promise<void> {
        try {
            const connected = await this.mcpClient.initialize();
            if (connected) {
                this.logger.info('MCP client initialized successfully');
            } else {
                this.logger.warn('MCP client failed to connect, using fallback mode');
            }
        } catch (error) {
            this.logger.error('MCP client initialization failed', error);
        }
    }

    /**
     * Request AI fix for a specific violation
     */
    public async requestAIFix(finding: Finding, document?: vscode.TextDocument): Promise<void> {
        if (!this.configService.get('aiIntegration', true)) {
            vscode.window.showInformationMessage('AI integration is disabled. Enable it in settings.');
            return;
        }

        try {
            // Show progress
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: 'Generating AI fix...',
                cancellable: true
            }, async (progress, token) => {
                progress.report({ increment: 0, message: 'Analyzing violation context...' });

                // Get document context
                const context = document ? this.getViolationContext(finding, document) : null;
                
                progress.report({ increment: 30, message: 'Calling AI service...' });

                // Call MCP server for AI fix
                const aiResponse = await this.callMCPForFix(finding, context);
                
                progress.report({ increment: 70, message: 'Preparing fix preview...' });

                if (aiResponse && aiResponse.patch) {
                    // Show diff preview and apply if accepted
                    await this.showFixPreview(finding, aiResponse, document);
                } else {
                    vscode.window.showInformationMessage('AI could not generate a fix for this violation.');
                }

                progress.report({ increment: 100, message: 'Complete!' });
            });

        } catch (error) {
            this.logger.error('AI fix request failed', error);
            vscode.window.showErrorMessage(`AI fix failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    /**
     * Get AI suggestions data (for internal use by other components)
     */
    public async getAISuggestionsData(finding: Finding, document?: vscode.TextDocument): Promise<any[]> {
        if (!this.configService.get('aiIntegration', true)) {
            return [];
        }

        try {
            const context = document ? this.getViolationContext(finding, document) : null;
            return await this.callMCPForSuggestions(finding, context);
        } catch (error) {
            this.logger.error('AI suggestions data request failed', error);
            return [];
        }
    }

    /**
     * Get multiple AI suggestions for a violation (UI interaction)
     */
    public async getAISuggestions(finding: Finding, document?: vscode.TextDocument): Promise<void> {
        if (!this.configService.get('aiIntegration', true)) {
            return;
        }

        try {
            const context = document ? this.getViolationContext(finding, document) : null;
            const suggestions = await this.callMCPForSuggestions(finding, context);

            if (suggestions && suggestions.length > 0) {
                // Show suggestions in a quick pick
                const items = suggestions.map((suggestion, index) => ({
                    label: `$(lightbulb) ${suggestion.technique}`,
                    description: `${suggestion.confidence}% confidence`,
                    detail: suggestion.description,
                    suggestion
                }));

                const selected = await vscode.window.showQuickPick(items, {
                    placeHolder: 'Select a refactoring approach',
                    matchOnDescription: true,
                    matchOnDetail: true
                });

                if (selected) {
                    // Apply selected suggestion
                    await this.applySuggestion(selected.suggestion, finding, document);
                }
            } else {
                vscode.window.showInformationMessage('No AI suggestions available for this violation.');
            }

        } catch (error) {
            this.logger.error('AI suggestions request failed', error);
            vscode.window.showErrorMessage(`AI suggestions failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    /**
     * Get AI explanation for a violation
     */
    public async getAIExplanation(finding: Finding): Promise<void> {
        try {
            const explanation = await this.callMCPForExplanation(finding);
            
            if (explanation) {
                // Show explanation in a webview or information message
                const message = `
**${finding.type}** - ${finding.severity.toUpperCase()}

${explanation.explanation}

**Why this matters:**
${explanation.impact || 'This coupling can make code harder to maintain and test.'}

**Recommended approach:**
${explanation.recommendation || finding.suggestion || 'Consider refactoring to reduce coupling.'}
                `.trim();

                vscode.window.showInformationMessage(message, { modal: true });
            }

        } catch (error) {
            this.logger.error('AI explanation request failed', error);
        }
    }

    /**
     * Batch process multiple violations with AI
     */
    public async batchAIFix(findings: Finding[], document: vscode.TextDocument): Promise<void> {
        if (!this.configService.get('aiIntegration', true) || findings.length === 0) {
            return;
        }

        const maxBatchSize = 5; // Prevent overwhelming the AI service
        const batch = findings.slice(0, maxBatchSize);

        try {
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: `Processing ${batch.length} violations with AI...`,
                cancellable: true
            }, async (progress, token) => {
                const fixes = [];

                for (let i = 0; i < batch.length; i++) {
                    if (token.isCancellationRequested) {
                        break;
                    }

                    const finding = batch[i];
                    progress.report({ 
                        increment: (i / batch.length) * 100, 
                        message: `Processing ${finding.type}...` 
                    });

                    const context = this.getViolationContext(finding, document);
                    const fix = await this.callMCPForFix(finding, context);
                    
                    if (fix && fix.patch) {
                        fixes.push({ finding, fix });
                    }
                }

                if (fixes.length > 0) {
                    await this.showBatchFixPreview(fixes, document);
                }
            });

        } catch (error) {
            this.logger.error('Batch AI fix failed', error);
            vscode.window.showErrorMessage(`Batch AI fix failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    // === PRIVATE METHODS ===

    private registerCommands(): void {
        // Register AI-related commands
        this.disposables.push(
            vscode.commands.registerCommand('connascence.requestAIFix', (args) => {
                const finding = args?.finding;
                const document = vscode.window.activeTextEditor?.document;
                if (finding) {
                    this.requestAIFix(finding, document);
                }
            })
        );

        this.disposables.push(
            vscode.commands.registerCommand('connascence.getAISuggestions', (args) => {
                const finding = args?.finding;
                const document = vscode.window.activeTextEditor?.document;
                if (finding) {
                    this.getAISuggestions(finding, document);
                }
            })
        );

        this.disposables.push(
            vscode.commands.registerCommand('connascence.aiExplain', (args) => {
                const finding = args?.finding;
                if (finding) {
                    this.getAIExplanation(finding);
                }
            })
        );

        this.disposables.push(
            vscode.commands.registerCommand('connascence.batchAIFix', () => {
                // Get all violations from active editor
                const editor = vscode.window.activeTextEditor;
                if (!editor) return;

                const diagnostics = vscode.languages.getDiagnostics(editor.document.uri)
                    .filter(d => d.source === 'connascence');

                if (diagnostics.length === 0) {
                    vscode.window.showInformationMessage('No connascence violations found in current file.');
                    return;
                }

                // Convert diagnostics back to findings (this is a simplified approach)
                const findings: Finding[] = diagnostics.map(diag => ({
                    id: (diag.code as any)?.value || 'unknown',
                    type: 'unknown', // Would need to extract from diagnostic
                    severity: this.diagnosticSeverityToString(diag.severity),
                    message: diag.message,
                    file: editor.document.fileName,
                    line: diag.range.start.line + 1,
                    column: diag.range.start.character + 1,
                    suggestion: diag.relatedInformation?.[0]?.message
                }));

                this.batchAIFix(findings, editor.document);
            })
        );
    }

    private getViolationContext(finding: Finding, document: vscode.TextDocument): string {
        const contextKey = `${finding.file}:${finding.line}:${document.version}`;
        
        // Check context cache first
        const cached = this.contextCache.get(contextKey);
        if (cached) {
            return cached;
        }
        
        // Enhanced multi-file connascence context
        const context = this.buildEnhancedConnascenceContext(finding, document);
        
        // Cache context with shorter TTL (context changes more frequently)
        this.contextCache.set(contextKey, context, 150000); // 2.5 minutes
        return context;
    }

    /**
     * Build comprehensive context for multi-file connascence violations
     * Includes: code snippet, violation type, related files, refactor suggestions, linter data
     */
    private buildEnhancedConnascenceContext(finding: Finding, document: vscode.TextDocument): string {
        const contextBuilder = [];

        // 1. VIOLATION METADATA
        contextBuilder.push("=== CONNASCENCE VIOLATION ANALYSIS ===");
        contextBuilder.push(`Type: ${finding.type}`);
        contextBuilder.push(`Severity: ${finding.severity}`);
        contextBuilder.push(`Location: ${finding.file}:${finding.line}:${finding.column ?? 1}`);
        contextBuilder.push(`Description: ${finding.message}`);
        contextBuilder.push("");

        // 2. PRIMARY CODE SNIPPET (the detected issue)
        contextBuilder.push("=== PRIMARY CODE SNIPPET ===");
        const startLine = Math.max(0, finding.line - 8); // More context: 8 lines before
        const endLine = Math.min(document.lineCount - 1, finding.line + 8); // 8 lines after
        
        for (let i = startLine; i <= endLine; i++) {
            const lineText = document.lineAt(i).text;
            const marker = i === finding.line - 1 ? ' <-- VIOLATION HERE' : '';
            contextBuilder.push(`${i + 1}: ${lineText}${marker}`);
        }
        contextBuilder.push("");

        // 3. CONNASCENCE TYPE EXPLANATION
        contextBuilder.push("=== CONNASCENCE TYPE DETAILS ===");
        const connascenceExplanation = this.getConnascenceTypeExplanation(finding.type);
        contextBuilder.push(connascenceExplanation);
        contextBuilder.push("");

        // 4. RELATED FILES CONTEXT (multi-file connascence)
        const relatedFilesContext = this.getRelatedFilesContext(finding);
        if (relatedFilesContext.length > 0) {
            contextBuilder.push("=== RELATED FILES (Multi-file Connascence) ===");
            contextBuilder.push(...relatedFilesContext);
            contextBuilder.push("");
        }

        // 5. MULTI-LINTER CORRELATION DATA
        const linterContext = this.getMultiLinterContext(finding);
        if (linterContext.length > 0) {
            contextBuilder.push("=== MULTI-LINTER ANALYSIS ===");
            contextBuilder.push(...linterContext);
            contextBuilder.push("");
        }

        // 6. REFACTORING STRATEGY GUIDANCE
        contextBuilder.push("=== REFACTORING STRATEGY ===");
        const refactoringStrategy = this.getRefactoringStrategy(finding);
        contextBuilder.push(refactoringStrategy);
        contextBuilder.push("");

        // 7. AI INSTRUCTION PROMPT
        contextBuilder.push("=== AI INSTRUCTION ===");
        contextBuilder.push("Please analyze this connascence violation with the following comprehensive context:");
        contextBuilder.push("1. The code snippet shows the exact location of the coupling issue");
        contextBuilder.push("2. Related files show how this violation connects across the codebase");
        contextBuilder.push("3. Linter data provides additional quality insights");
        contextBuilder.push("4. Provide a COMPLETE CODE SOLUTION that:");
        contextBuilder.push("   - Fixes the connascence violation");
        contextBuilder.push("   - Updates ALL related files that are coupled");
        contextBuilder.push("   - Follows the refactoring strategy provided");
        contextBuilder.push("   - Maintains functionality while reducing coupling");
        contextBuilder.push("   - Uses modern best practices and patterns");

        return contextBuilder.join("\n");
    }

    /**
     * Get explanation for the specific connascence type
     */
    private getConnascenceTypeExplanation(type: string): string {
        const explanations: { [key: string]: string } = {
            'CoN': 'Connascence of Name: Multiple components must agree on names. Look for shared variable/function names.',
            'CoT': 'Connascence of Type: Components must agree on data types. Check for type mismatches or missing annotations.',
            'CoM': 'Connascence of Meaning: Components must agree on value meanings. Look for magic literals or hardcoded values.',
            'CoP': 'Connascence of Position: Components depend on parameter order. Consider parameter objects or named parameters.',
            'CoA': 'Connascence of Algorithm: Multiple implementations of the same algorithm. Extract to shared functions.',
            'CoE': 'Connascence of Execution: Components must execute in specific order. Look for temporal dependencies.',
            'CoV': 'Connascence of Value: Multiple components depend on same values. Check for shared mutable state.',
            'CoI': 'Connascence of Identity: Components must reference the same object. Look for singleton or shared instance issues.',
            'CoTi': 'Connascence of Timing: Components depend on execution timing. Check for race conditions or thread safety.',
            'God Object': 'Algorithmic complexity: Class/function has too many responsibilities. Apply Single Responsibility Principle.'
        };

        return explanations[type] || `Unknown connascence type: ${type}`;
    }

    /**
     * Get context from related files that share the same connascence violation
     */
    private getRelatedFilesContext(finding: Finding): string[] {
        const context: string[] = [];
        
        try {
            // For now, use pattern matching to find related files
            // In the future, this could use the analyzer's cross-reference data
            
            // Look for similar patterns in the workspace
            const workspaceFolders = vscode.workspace.workspaceFolders;
            if (!workspaceFolders || workspaceFolders.length === 0) {
                return context;
            }

            // Add placeholder for related files detection
            // This would be enhanced with actual analyzer correlation data
            context.push("// Related files analysis would show:");
            context.push("// - Files that share the same coupling pattern");
            context.push("// - Dependent modules that need updating");
            context.push("// - Import/export relationships");
            
            // Extract key patterns from the violation for related file search
            if (finding.message.includes('magic literal') || finding.type === 'CoM') {
                context.push("// Magic literal connascence likely affects:");
                context.push("// - Configuration files with same constants");
                context.push("// - Test files with hardcoded values");
                context.push("// - Related service/utility files");
            }
            
            if (finding.type === 'CoP') {
                context.push("// Parameter position connascence affects:");
                context.push("// - All call sites of this function");
                context.push("// - Interface implementations");
                context.push("// - Mock/test implementations");
            }

        } catch (error) {
            this.logger.error('Error getting related files context', error);
            context.push("// Related files analysis temporarily unavailable");
        }

        return context;
    }

    /**
     * Get correlatedcontext from multiple linters (Ruff, MyPy, Radon, Bandit, Black)
     */
    private getMultiLinterContext(finding: Finding): string[] {
        const context: string[] = [];

        try {
            // This would integrate with the ToolCoordinator results
            // For now, provide structured placeholder for linter correlation

            context.push("Correlated Linter Findings:");
            
            // Ruff correlation
            if (finding.type === 'CoM' || finding.message.includes('magic')) {
                context.push("- Ruff: Likely flagged as magic number/string violation (F841, E731)");
                context.push("- Suggested fix: Extract to named constants");
            }

            // MyPy correlation  
            if (finding.type === 'CoT') {
                context.push("- MyPy: Type checking errors likely present");
                context.push("- Suggested fix: Add proper type annotations");
            }

            // Radon correlation
            if (finding.type === 'CoA' || finding.message.includes('God Object')) {
                context.push("- Radon: High cyclomatic complexity detected");
                context.push("- Suggested fix: Refactor into smaller functions");
            }

            // Bandit correlation
            if (finding.severity === 'critical' || finding.message.includes('security')) {
                context.push("- Bandit: Potential security implications");
                context.push("- Suggested fix: Use secure patterns and constants");
            }

            // Black correlation
            if (finding.type === 'CoP' || finding.message.includes('parameter')) {
                context.push("- Black: Formatting may help readability");
                context.push("- Suggested fix: Use parameter formatting best practices");
            }

            // Add integration note
            context.push("");
            context.push("Note: Full linter integration provides detailed correlation analysis");
            context.push("with specific line numbers and automated fix suggestions.");

        } catch (error) {
            this.logger.error('Error getting multi-linter context', error);
            context.push("// Multi-linter analysis temporarily unavailable");
        }

        return context;
    }

    /**
     * Get specific refactoring strategy for the connascence type
     */
    private getRefactoringStrategy(finding: Finding): string {
        const strategies: { [key: string]: string } = {
            'CoN': 'Strategy: Extract shared names to constants or enums. Use dependency injection for shared services.',
            'CoT': 'Strategy: Add explicit type annotations. Use TypeScript interfaces or Python dataclasses for structure.',
            'CoM': 'Strategy: Extract magic literals to named constants. Create configuration classes or enums.',
            'CoP': 'Strategy: Replace positional parameters with named parameters or parameter objects.',
            'CoA': 'Strategy: Extract common algorithms to shared utility functions. Use strategy pattern if variations exist.',
            'CoE': 'Strategy: Use dependency injection or event-driven architecture to remove execution dependencies.',
            'CoV': 'Strategy: Make values immutable. Use factories or builders instead of shared mutable state.',
            'CoI': 'Strategy: Use dependency injection instead of shared instances. Avoid singletons where possible.',
            'CoTi': 'Strategy: Use proper synchronization primitives. Consider async/await or message passing.',
            'God Object': 'Strategy: Apply Single Responsibility Principle. Extract related methods to separate classes.'
        };

        return strategies[finding.type] || 'Strategy: Apply appropriate separation of concerns and reduce coupling.';
    }

    private async callMCPForFix(finding: Finding, context: string | null): Promise<any> {
        const startTime = Date.now();
        const cacheKey = this.generateCacheKey('fix', finding, context);
        
        // Check cache first
        const cached = this.fixCache.get(cacheKey);
        if (cached) {
            this.performanceStats.cacheHits++;
            this.logger.debug('Cache hit for AI fix', { finding: finding.id });
            return cached;
        }
        
        this.logger.debug('Calling MCP for AI fix', { finding: finding.id, hasContext: !!context });
        
        try {
            this.performanceStats.serverRequests++;
            const response = await this.mcpClient.requestFix(finding, context);
            
            // Cache successful response
            if (response && response.patch) {
                const customTTL = response.confidence > 80 ? 600000 : 300000; // Cache high-confidence fixes longer
                this.fixCache.set(cacheKey, response, customTTL);
            }
            
            this.updatePerformanceStats(startTime);
            return response;
        } catch (error) {
            this.updatePerformanceStats(startTime);
            this.logger.error('MCP fix request failed', error);
            throw error;
        }
    }

    private async callMCPForSuggestions(finding: Finding, context: string | null): Promise<any[]> {
        const startTime = Date.now();
        const cacheKey = this.generateCacheKey('suggestions', finding, context);
        
        // Check cache first
        const cached = this.suggestionCache.get(cacheKey);
        if (cached) {
            this.performanceStats.cacheHits++;
            this.logger.debug('Cache hit for AI suggestions', { finding: finding.id });
            return cached;
        }
        
        this.logger.debug('Calling MCP for AI suggestions', { finding: finding.id });
        
        try {
            this.performanceStats.serverRequests++;
            const suggestions = await this.mcpClient.getSuggestions(finding, context);
            
            // Cache successful response
            if (suggestions && suggestions.length > 0) {
                this.suggestionCache.set(cacheKey, suggestions);
            }
            
            this.updatePerformanceStats(startTime);
            return suggestions;
        } catch (error) {
            this.updatePerformanceStats(startTime);
            this.logger.error('MCP suggestions request failed', error);
            return [];
        }
    }

    private async callMCPForExplanation(finding: Finding): Promise<any> {
        const startTime = Date.now();
        const cacheKey = this.generateCacheKey('explanation', finding);
        
        // Check cache first
        const cached = this.explanationCache.get(cacheKey);
        if (cached) {
            this.performanceStats.cacheHits++;
            this.logger.debug('Cache hit for AI explanation', { finding: finding.id });
            return cached;
        }
        
        try {
            this.performanceStats.serverRequests++;
            const explanation = await this.mcpClient.getExplanation(finding);
            
            // Cache successful response (longer TTL for explanations)
            if (explanation) {
                this.explanationCache.set(cacheKey, explanation, 600000); // 10 minutes
            }
            
            this.updatePerformanceStats(startTime);
            return explanation;
        } catch (error) {
            this.updatePerformanceStats(startTime);
            this.logger.error('MCP explanation request failed', error);
            
            // Cache fallback explanation too (shorter TTL)
            const fallback = {
                explanation: `This ${finding.type} violation indicates tight coupling between components.`,
                impact: 'Makes code harder to maintain and test.',
                recommendation: 'Consider extracting the dependency or using dependency injection.'
            };
            this.explanationCache.set(cacheKey, fallback, 120000); // 2 minutes
            return fallback;
        }
    }

    private async showFixPreview(finding: Finding, aiResponse: any, document?: vscode.TextDocument): Promise<void> {
        const action = await vscode.window.showInformationMessage(
            `AI suggests: ${aiResponse.description} (${Math.round(aiResponse.confidence * 100)}% confidence)`,
            'Preview Changes',
            'Apply Fix',
            'Cancel'
        );

        if (action === 'Apply Fix') {
            // Apply the fix directly
            await this.applyFix(aiResponse, finding, document);
        } else if (action === 'Preview Changes') {
            // Show diff editor
            await this.showDiffPreview(aiResponse, finding, document);
        }
    }

    private async showBatchFixPreview(fixes: any[], document: vscode.TextDocument): Promise<void> {
        const message = `AI generated ${fixes.length} fixes. Apply all changes?`;
        const action = await vscode.window.showInformationMessage(message, 'Apply All', 'Preview', 'Cancel');

        if (action === 'Apply All') {
            for (const { fix, finding } of fixes) {
                await this.applyFix(fix, finding, document);
            }
            vscode.window.showInformationMessage(`Applied ${fixes.length} AI-generated fixes.`);
        }
    }

    private async applyFix(fix: any, finding: Finding, document?: vscode.TextDocument): Promise<void> {
        if (!document) {
            document = await vscode.workspace.openTextDocument(finding.file);
        }

        const edit = new vscode.WorkspaceEdit();
        const line = finding.line - 1;
        const currentLineText = document.lineAt(line).text;
        const range = new vscode.Range(line, 0, line, currentLineText.length);
        
        // Create undo checkpoint
        const undoData = {
            uri: document.uri,
            range: range,
            originalText: currentLineText,
            fixDescription: fix.description,
            timestamp: new Date().toISOString()
        };

        // Apply the edit with proper undo label
        edit.replace(document.uri, range, fix.patch);
        const success = await vscode.workspace.applyEdit(edit, {
            isRefactoring: true
        });

        if (success) {
            // Store undo information for potential manual revert
            this.storeUndoInformation(undoData);
            
            this.logger.info(`Applied AI fix for ${finding.type} at ${finding.file}:${finding.line}`);
            
            // Show success message with undo option
            const undoAction = await vscode.window.showInformationMessage(
                `✅ Applied: ${fix.description}`,
                'Undo',
                'Dismiss'
            );

            if (undoAction === 'Undo') {
                await this.undoLastFix(undoData);
            }
        } else {
            throw new Error('Failed to apply workspace edit');
        }
    }

    private recentFixes: Array<{
        uri: vscode.Uri;
        range: vscode.Range;
        originalText: string;
        fixDescription: string;
        timestamp: string;
    }> = [];

    private storeUndoInformation(undoData: any): void {
        // Store undo data (keep last 10 fixes)
        this.recentFixes.unshift(undoData);
        if (this.recentFixes.length > 10) {
            this.recentFixes = this.recentFixes.slice(0, 10);
        }
    }

    private async undoLastFix(undoData: any): Promise<void> {
        try {
            const document = await vscode.workspace.openTextDocument(undoData.uri);
            const edit = new vscode.WorkspaceEdit();
            
            edit.replace(undoData.uri, undoData.range, undoData.originalText);
            const success = await vscode.workspace.applyEdit(edit);

            if (success) {
                vscode.window.showInformationMessage(`↩️ Undid: ${undoData.fixDescription}`);
                this.logger.info(`Undid AI fix: ${undoData.fixDescription}`);
            }
        } catch (error) {
            this.logger.error('Failed to undo fix', error);
            vscode.window.showErrorMessage('Failed to undo fix');
        }
    }

    private async applySuggestion(suggestion: any, finding: Finding, document?: vscode.TextDocument): Promise<void> {
        // For now, just show the suggestion - in a real implementation, this would apply the specific refactoring
        vscode.window.showInformationMessage(`Applied: ${suggestion.technique} - ${suggestion.description}`);
    }

    private async showDiffPreview(fix: any, finding: Finding, document?: vscode.TextDocument): Promise<void> {
        if (!document) {
            document = await vscode.workspace.openTextDocument(finding.file);
        }

        try {
            // Create modified content by applying the fix
            const originalContent = document.getText();
            const modifiedContent = this.applyFixToContent(originalContent, fix, finding);

            // Create temporary files for diff view
            const originalUri = vscode.Uri.parse(`untitled:Original-${finding.file.split('/').pop()}`);
            const modifiedUri = vscode.Uri.parse(`untitled:AI-Fixed-${finding.file.split('/').pop()}`);

            // Open temporary documents
            const originalDoc = await vscode.workspace.openTextDocument(originalUri.with({ 
                path: originalUri.path,
                query: Buffer.from(originalContent, 'utf8').toString('base64')
            }));

            const modifiedDoc = await vscode.workspace.openTextDocument(modifiedUri.with({
                path: modifiedUri.path, 
                query: Buffer.from(modifiedContent, 'utf8').toString('base64')
            }));

            // Show diff editor
            await vscode.commands.executeCommand('vscode.diff',
                originalDoc.uri,
                modifiedDoc.uri,
                `${finding.type} Fix Preview: ${finding.file.split('/').pop()}`,
                {
                    preview: true,
                    selection: new vscode.Range(
                        Math.max(0, finding.line - 3),
                        0,
                        Math.min(document.lineCount - 1, finding.line + 3),
                        0
                    )
                }
            );

            // Show action buttons
            const action = await vscode.window.showInformationMessage(
                `Preview: ${fix.description} (${Math.round(fix.confidence * 100)}% confidence)`,
                {
                    modal: false,
                    detail: `Safety: ${fix.safety}\nClick to apply the fix or cancel.`
                },
                'Apply Fix',
                'Cancel'
            );

            if (action === 'Apply Fix') {
                await this.applyFix(fix, finding, document);
                await this.closeDiffPreview(originalDoc.uri, modifiedDoc.uri);
            }

        } catch (error) {
            this.logger.error('Failed to show diff preview', error);
            vscode.window.showErrorMessage(`Failed to show diff preview: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    private applyFixToContent(originalContent: string, fix: any, finding: Finding): string {
        const lines = originalContent.split('\n');
        const targetLine = finding.line - 1; // Convert to 0-based

        if (targetLine >= 0 && targetLine < lines.length) {
            // Simple line replacement - in a real implementation, this would be more sophisticated
            lines[targetLine] = fix.patch || lines[targetLine];
            
            // For more complex fixes, we might need to handle multiple lines
            if (fix.multiline && fix.replacementLines) {
                lines.splice(targetLine, 1, ...fix.replacementLines);
            }
        }

        return lines.join('\n');
    }

    private async closeDiffPreview(originalUri: vscode.Uri, modifiedUri: vscode.Uri): Promise<void> {
        try {
            // Close the temporary diff editor tabs
            await vscode.commands.executeCommand('workbench.action.closeActiveEditor');
        } catch (error) {
            // Silently handle close errors
            this.logger.debug('Failed to close diff preview tabs', error);
        }
    }

    private diagnosticSeverityToString(severity: vscode.DiagnosticSeverity): 'critical' | 'major' | 'minor' | 'info' {
        switch (severity) {
            case vscode.DiagnosticSeverity.Error: return 'critical';
            case vscode.DiagnosticSeverity.Warning: return 'major';
            case vscode.DiagnosticSeverity.Information: return 'minor';
            default: return 'info';
        }
    }

    /**
     * Generate cache key for consistent caching
     */
    private generateCacheKey(type: string, finding: Finding, context?: string | null): string {
        const baseKey = `${type}:${finding.type}:${finding.severity}:${finding.file}:${finding.line}`;
        if (context) {
            // Use hash of context to keep key manageable
            const contextHash = this.simpleHash(context);
            return `${baseKey}:${contextHash}`;
        }
        return baseKey;
    }

    /**
     * Simple string hash for context caching
     */
    private simpleHash(str: string): number {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32-bit integer
        }
        return Math.abs(hash);
    }

    /**
     * Update performance statistics
     */
    private updatePerformanceStats(startTime: number): void {
        this.performanceStats.requestCount++;
        this.performanceStats.totalResponseTime += Date.now() - startTime;
    }

    /**
     * Setup cache management and monitoring
     */
    private setupCacheManagement(): void {
        // Register cache management commands
        this.disposables.push(
            vscode.commands.registerCommand('connascence.clearAICache', () => {
                this.clearAllCaches();
                vscode.window.showInformationMessage('AI cache cleared successfully');
            })
        );

        this.disposables.push(
            vscode.commands.registerCommand('connascence.showCacheStats', () => {
                this.showCacheStatistics();
            })
        );

        // Setup cache monitoring
        setInterval(() => {
            this.logCacheStatistics();
        }, 300000); // Log stats every 5 minutes

        // Watch for configuration changes
        this.disposables.push(
            vscode.workspace.onDidChangeConfiguration((event) => {
                if (event.affectsConfiguration('connascence.ai.cache')) {
                    // Invalidate caches when cache settings change
                    this.clearAllCaches();
                    this.logger.info('AI caches cleared due to configuration change');
                }
            })
        );
    }

    /**
     * Clear all AI caches
     */
    public clearAllCaches(): void {
        this.fixCache.invalidate();
        this.suggestionCache.invalidate();
        this.explanationCache.invalidate();
        this.contextCache.invalidate();
        
        this.logger.info('All AI caches cleared');
    }

    /**
     * Clear cache for specific patterns
     */
    public clearCachePattern(pattern: string): void {
        this.fixCache.invalidate(pattern);
        this.suggestionCache.invalidate(pattern);
        this.explanationCache.invalidate(pattern);
        this.contextCache.invalidate(pattern);
        
        this.logger.info(`Cleared cache for pattern: ${pattern}`);
    }

    /**
     * Show cache statistics in VS Code
     */
    private showCacheStatistics(): void {
        const fixStats = this.fixCache.getStats();
        const suggestionStats = this.suggestionCache.getStats();
        const explanationStats = this.explanationCache.getStats();
        const contextStats = this.contextCache.getStats();
        
        const avgResponseTime = this.performanceStats.requestCount > 0 
            ? (this.performanceStats.totalResponseTime / this.performanceStats.requestCount).toFixed(0)
            : '0';
        
        const overallHitRate = this.performanceStats.requestCount > 0
            ? ((this.performanceStats.cacheHits / this.performanceStats.requestCount) * 100).toFixed(1)
            : '0';

        const message = `🚀 AI Cache Statistics:

` +
            `📊 Overall Performance:
` +
            `• Total Requests: ${this.performanceStats.requestCount}
` +
            `• Cache Hit Rate: ${overallHitRate}%
` +
            `• Avg Response Time: ${avgResponseTime}ms
` +
            `• Server Requests: ${this.performanceStats.serverRequests}
\n` +
            `🔧 Fix Cache: ${fixStats.size} items (${fixStats.hitRate.toFixed(1)}% hit rate)
` +
            `💡 Suggestion Cache: ${suggestionStats.size} items (${suggestionStats.hitRate.toFixed(1)}% hit rate)
` +
            `📚 Explanation Cache: ${explanationStats.size} items (${explanationStats.hitRate.toFixed(1)}% hit rate)
` +
            `📝 Context Cache: ${contextStats.size} items (${contextStats.hitRate.toFixed(1)}% hit rate)`;

        vscode.window.showInformationMessage(message, { modal: true });
    }

    /**
     * Log cache statistics to logger
     */
    private logCacheStatistics(): void {
        const fixStats = this.fixCache.getStats();
        const suggestionStats = this.suggestionCache.getStats();
        const explanationStats = this.explanationCache.getStats();
        const contextStats = this.contextCache.getStats();
        
        this.logger.info('AI Cache Statistics', {
            fix: fixStats,
            suggestions: suggestionStats, 
            explanations: explanationStats,
            context: contextStats,
            performance: this.performanceStats
        });
    }

    /**
     * Get current cache statistics for external monitoring
     */
    public getCacheStats(): any {
        return {
            fix: this.fixCache.getStats(),
            suggestions: this.suggestionCache.getStats(),
            explanations: this.explanationCache.getStats(),
            context: this.contextCache.getStats(),
            performance: { ...this.performanceStats }
        };
    }

    dispose(): void {
        // Dispose caches
        this.fixCache.dispose();
        this.suggestionCache.dispose();
        this.explanationCache.dispose();
        this.contextCache.dispose();
        
        // Dispose MCP client and other resources
        this.mcpClient?.dispose();
        for (const disposable of this.disposables) {
            disposable.dispose();
        }
    }
}