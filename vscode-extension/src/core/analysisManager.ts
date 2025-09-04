import * as vscode from 'vscode';
import { ConnascenceService, AnalysisResult } from '../services/connascenceService';
import { ConfigurationService } from '../services/configurationService';
import { ExtensionLogger } from '../utils/logger';
import { VisualProvider } from '../providers/visualProvider';
import { UIManager } from '../ui/uiManager';
import { AIIntegrationService } from '../services/aiIntegrationService';

/**
 * Unified Analysis Manager
 * 
 * MECE Responsibility: ALL analysis-related operations
 * - File analysis coordination
 * - Results caching and distribution  
 * - Real-time analysis coordination
 * - Performance optimization
 */
export class AnalysisManager implements vscode.Disposable {
    private disposables: vscode.Disposable[] = [];
    private analysisCache = new Map<string, AnalysisResult>();
    private analysisInProgress = new Set<string>();
    
    // Event emitter for analysis results
    private _onAnalysisComplete = new vscode.EventEmitter<{
        document: vscode.TextDocument;
        results: AnalysisResult;
    }>();
    public readonly onAnalysisComplete = this._onAnalysisComplete.event;

    constructor(
        private connascenceService: ConnascenceService,
        private configService: ConfigurationService,
        private logger: ExtensionLogger,
        private visualProvider: VisualProvider,
        private uiManager: UIManager,
        private aiIntegrationService: AIIntegrationService
    ) {
        this.setupRealtimeAnalysis();
        this.setupComponentCoordination();
    }

    /**
     * Analyze a single file and emit results
     */
    public async analyzeFile(document: vscode.TextDocument): Promise<AnalysisResult> {
        const uri = document.uri.toString();
        
        // Prevent duplicate analysis
        if (this.analysisInProgress.has(uri)) {
            return this.analysisCache.get(uri) || { findings: [], qualityScore: 100, summary: { totalIssues: 0, issuesBySeverity: { critical: 0, major: 0, minor: 0, info: 0 } } };
        }

        this.analysisInProgress.add(uri);

        try {
            this.logger.debug(`Starting analysis for ${document.fileName}`);
            const results = await this.connascenceService.analyzeFile(document.fileName);
            
            // Cache results
            this.analysisCache.set(uri, results);
            
            // Update all visual feedback (diagnostics + decorations)
            this.visualProvider.updateVisuals(document, results);
            
            // Update UI components (status bar, dashboard, tree view)
            this.uiManager.updateFileResults(document.uri, results);
            
            // Emit results to any other subscribers
            this._onAnalysisComplete.fire({ document, results });
            
            this.logger.debug(`Analysis complete for ${document.fileName}: ${results.findings.length} violations found`);
            return results;

        } catch (error) {
            this.logger.error(`Analysis failed for ${document.fileName}`, error);
            const emptyResults: AnalysisResult = {
                findings: [],
                qualityScore: 100,
                summary: { totalIssues: 0, issuesBySeverity: { critical: 0, major: 0, minor: 0, info: 0 } }
            };
            return emptyResults;

        } finally {
            this.analysisInProgress.delete(uri);
        }
    }

    /**
     * Get cached results for a document
     */
    public getCachedResults(uri: vscode.Uri): AnalysisResult | undefined {
        return this.analysisCache.get(uri.toString());
    }

    /**
     * Clear cache for a document
     */
    public clearCache(uri: vscode.Uri): void {
        this.analysisCache.delete(uri.toString());
        this.visualProvider.clearDocument(uri);
        this.uiManager.clearFileResults(uri);
    }

    /**
     * Clear all cached results
     */
    public clearAllCache(): void {
        this.analysisCache.clear();
        this.analysisInProgress.clear();
        this.visualProvider.clearAll();
        this.uiManager.clearAllResults();
    }

    /**
     * Check if a file should be analyzed
     */
    public shouldAnalyze(document: vscode.TextDocument): boolean {
        // Only analyze supported languages
        const supportedLanguages = ['python', 'javascript', 'typescript', 'c', 'cpp'];
        if (!supportedLanguages.includes(document.languageId)) {
            return false;
        }

        // Skip if real-time analysis is disabled
        if (!this.configService.get('realTimeAnalysis', true)) {
            return false;
        }

        // Skip very large files for performance
        const maxFileSize = this.configService.get('maxFileSizeKB', 1000) * 1024;
        if (document.getText().length > maxFileSize) {
            this.logger.warn(`Skipping analysis of large file: ${document.fileName} (${Math.round(document.getText().length / 1024)}KB)`);
            return false;
        }

        return true;
    }

    /**
     * Get analysis statistics
     */
    public getStatistics(): {
        totalFiles: number;
        totalViolations: number;
        violationsBySeverity: { [severity: string]: number };
        cacheHitRate: number;
    } {
        let totalViolations = 0;
        const violationsBySeverity: { [severity: string]: number } = {
            critical: 0,
            major: 0,
            minor: 0,
            info: 0
        };

        for (const results of this.analysisCache.values()) {
            totalViolations += results.findings.length;
            for (const finding of results.findings) {
                violationsBySeverity[finding.severity] = (violationsBySeverity[finding.severity] || 0) + 1;
            }
        }

        return {
            totalFiles: this.analysisCache.size,
            totalViolations,
            violationsBySeverity,
            cacheHitRate: this.analysisCache.size / (this.analysisCache.size + this.analysisInProgress.size || 1)
        };
    }

    private setupRealtimeAnalysis(): void {
        const debounceMs = this.configService.get('debounceMs', 1000);
        const debouncedAnalysis = new Map<string, NodeJS.Timeout>();

        // Real-time document change handling
        this.disposables.push(
            vscode.workspace.onDidChangeTextDocument((event) => {
                const uri = event.document.uri.toString();
                
                if (!this.shouldAnalyze(event.document)) {
                    return;
                }

                // Clear existing timeout
                const existingTimeout = debouncedAnalysis.get(uri);
                if (existingTimeout) {
                    clearTimeout(existingTimeout);
                }

                // Set new debounced analysis
                const timeout = setTimeout(() => {
                    this.uiManager.setAnalyzing(true, event.document.fileName);
                    this.analyzeFile(event.document).finally(() => {
                        this.uiManager.setAnalyzing(false);
                    });
                    debouncedAnalysis.delete(uri);
                }, debounceMs);

                debouncedAnalysis.set(uri, timeout);
            })
        );

        // File system changes
        this.disposables.push(
            vscode.workspace.onDidSaveTextDocument((document) => {
                if (this.shouldAnalyze(document)) {
                    this.uiManager.setAnalyzing(true, document.fileName);
                    this.analyzeFile(document).finally(() => {
                        this.uiManager.setAnalyzing(false);
                    });
                }
            })
        );

        this.disposables.push(
            vscode.workspace.onDidCloseTextDocument((document) => {
                this.clearCache(document.uri);
            })
        );
    }

    private setupComponentCoordination(): void {
        // Handle active editor changes for visual updates
        this.disposables.push(
            vscode.window.onDidChangeActiveTextEditor((editor) => {
                if (editor && this.configService.get('enableVisualHighlighting', true)) {
                    this.visualProvider.updateEditorDecorations(editor);
                }
            })
        );

        // Handle visible editor changes
        this.disposables.push(
            vscode.window.onDidChangeVisibleTextEditors((editors) => {
                if (this.configService.get('enableVisualHighlighting', true)) {
                    for (const editor of editors) {
                        this.visualProvider.updateEditorDecorations(editor);
                    }
                }
            })
        );

        // Register AI integration commands through analysis manager
        this.disposables.push(
            vscode.commands.registerCommand('connascence.batchAIFix', async () => {
                const editor = vscode.window.activeTextEditor;
                if (!editor) {
                    this.uiManager.showMessage('No active editor found', 'warning');
                    return;
                }

                const results = this.getCachedResults(editor.document.uri);
                if (!results || results.findings.length === 0) {
                    this.uiManager.showMessage('No violations found in current file', 'info');
                    return;
                }

                await this.aiIntegrationService.batchAIFix(results.findings, editor.document);
            })
        );

        // Register workspace analysis command
        this.disposables.push(
            vscode.commands.registerCommand('connascence.analyzeWorkspace', async () => {
                await this.analyzeWorkspace();
            })
        );
    }

    /**
     * Analyze all files in the workspace
     */
    public async analyzeWorkspace(): Promise<void> {
        const files = await vscode.workspace.findFiles(
            '**/*.{py,js,ts,c,cpp}', 
            '**/node_modules/**'
        );

        if (files.length === 0) {
            this.uiManager.showMessage('No supported files found in workspace', 'info');
            return;
        }

        await this.uiManager.showProgress(
            `Analyzing ${files.length} files...`,
            async (progress) => {
                const increment = 100 / files.length;
                let completed = 0;

                for (const file of files) {
                    try {
                        const document = await vscode.workspace.openTextDocument(file);
                        if (this.shouldAnalyze(document)) {
                            await this.analyzeFile(document);
                        }
                    } catch (error) {
                        this.logger.error(`Failed to analyze ${file.fsPath}`, error);
                    }
                    
                    completed++;
                    progress.report({ 
                        increment, 
                        message: `${completed}/${files.length} files analyzed` 
                    });
                }
            }
        );

        this.uiManager.showMessage(`Workspace analysis complete: ${files.length} files analyzed`, 'info');
    }

    dispose(): void {
        this._onAnalysisComplete.dispose();
        for (const disposable of this.disposables) {
            disposable.dispose();
        }
        this.clearAllCache();
    }
}