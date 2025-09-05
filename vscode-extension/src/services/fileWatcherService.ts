import * as vscode from 'vscode';
import { ConnascenceDiagnosticsProvider } from '../providers/diagnosticsProvider';
import { ConfigurationService } from './configurationService';
import { ExtensionLogger } from '../utils/logger';

const debounce = require('debounce');

/**
 * File watcher service for managing real-time analysis
 */
export class FileWatcherService implements vscode.Disposable {
    private disposables: vscode.Disposable[] = [];
    private debouncedAnalysis: Map<string, () => void> = new Map();

    constructor(
        private diagnosticsProvider: ConnascenceDiagnosticsProvider,
        private configService: ConfigurationService,
        private logger: ExtensionLogger
    ) {
        this.setupDebouncing();
    }

    private setupDebouncing(): void {
        const debounceMs = this.configService.get('debounceMs', 1000);
        
        // Create debounced function factory
        this.createDebouncedAnalysis = (uri: vscode.Uri) => {
            const key = uri.toString();
            
            if (!this.debouncedAnalysis.has(key)) {
                const debouncedFn = debounce(async () => {
                    try {
                        const document = await vscode.workspace.openTextDocument(uri);
                        await this.diagnosticsProvider.updateFile(document);
                        this.logger.debug(`Debounced analysis completed for: ${uri.fsPath}`);
                    } catch (error) {
                        this.logger.error(`Failed to analyze file: ${uri.fsPath}`, error);
                    }
                }, debounceMs);
                
                this.debouncedAnalysis.set(key, debouncedFn);
            }
            
            return this.debouncedAnalysis.get(key)!;
        };
    }

    private createDebouncedAnalysis!: (uri: vscode.Uri) => () => void;

    public onFileChanged(uri: vscode.Uri): void {
        if (!this.shouldAnalyzeFile(uri)) {
            return;
        }

        const config = this.configService.get('realTimeAnalysis', true);
        if (!config) {
            return;
        }

        this.logger.debug(`File changed: ${uri.fsPath}`);
        
        // Use debounced analysis
        const analyze = this.createDebouncedAnalysis(uri);
        analyze();
    }

    public onFileCreated(uri: vscode.Uri): void {
        if (!this.shouldAnalyzeFile(uri)) {
            return;
        }

        this.logger.debug(`File created: ${uri.fsPath}`);
        
        // Analyze new files immediately (no debouncing needed)
        setTimeout(async () => {
            try {
                const document = await vscode.workspace.openTextDocument(uri);
                await this.diagnosticsProvider.updateFile(document);
            } catch (error) {
                this.logger.error(`Failed to analyze new file: ${uri.fsPath}`, error);
            }
        }, 500); // Small delay to ensure file is ready
    }

    public onFileDeleted(uri: vscode.Uri): void {
        this.logger.debug(`File deleted: ${uri.fsPath}`);
        
        // Clear diagnostics for deleted file
        this.diagnosticsProvider.clearDiagnostics(uri);
        
        // Clean up debounced function
        const key = uri.toString();
        if (this.debouncedAnalysis.has(key)) {
            this.debouncedAnalysis.delete(key);
        }
    }

    public onDocumentChanged(event: vscode.TextDocumentChangeEvent): void {
        const { document } = event;
        
        if (!this.shouldAnalyzeFile(document.uri)) {
            return;
        }

        // Skip if real-time analysis is disabled
        if (!this.configService.get('realTimeAnalysis', true)) {
            return;
        }

        // Skip if changes are too frequent (user is still typing)
        if (event.contentChanges.length === 0) {
            return;
        }

        // Only analyze on significant changes
        const hasSignificantChange = event.contentChanges.some(change => {
            const text = change.text;
            
            // Analyze on:
            // - Line breaks (user finished a statement)
            // - Function/class definitions
            // - Import statements
            // - Significant additions (more than a few characters)
            return text.includes('\n') || 
                   text.includes('def ') || 
                   text.includes('class ') || 
                   text.includes('import ') || 
                   text.length > 10;
        });

        if (!hasSignificantChange) {
            return;
        }

        this.logger.debug(`Document changed (significant): ${document.uri.fsPath}`);
        
        // Use debounced analysis for document changes
        const analyze = this.createDebouncedAnalysis(document.uri);
        analyze();
    }

    private shouldAnalyzeFile(uri: vscode.Uri): boolean {
        // Check file extension
        const supportedExtensions = ['.py', '.js', '.ts', '.c', '.cpp', '.jsx', '.tsx'];
        const extension = uri.fsPath.toLowerCase().split('.').pop();
        
        if (!extension || !supportedExtensions.includes(`.${extension}`)) {
            return false;
        }

        // Skip files in certain directories
        const skipDirectories = ['node_modules', '.git', '__pycache__', '.pytest_cache', 'venv', '.env'];
        const path = uri.fsPath.toLowerCase();
        
        for (const skipDir of skipDirectories) {
            if (path.includes(skipDir)) {
                return false;
            }
        }

        // Skip very large files
        try {
            const stats = require('fs').statSync(uri.fsPath);
            const maxFileSize = this.configService.get('maxFileSize', 1024 * 1024); // 1MB default
            
            if (maxFileSize && stats.size > maxFileSize) {
                this.logger.warn(`Skipping analysis of large file: ${uri.fsPath} (${stats.size} bytes)`);
                return false;
            }
        } catch (error) {
            // File might not exist or be accessible, let the analysis handle it
        }

        return true;
    }

    public async analyzeOpenDocuments(): Promise<void> {
        const openDocs = vscode.workspace.textDocuments.filter(doc => 
            this.shouldAnalyzeFile(doc.uri)
        );

        this.logger.info(`Analyzing ${openDocs.length} open documents`);

        const analysisPromises = openDocs.map(async (doc) => {
            try {
                await this.diagnosticsProvider.updateFile(doc);
            } catch (error) {
                this.logger.error(`Failed to analyze open document: ${doc.uri.fsPath}`, error);
            }
        });

        await Promise.allSettled(analysisPromises);
        this.logger.info('Finished analyzing open documents');
    }

    public async analyzeWorkspace(): Promise<void> {
        if (!vscode.workspace.workspaceFolders) {
            return;
        }

        const workspaceFolder = vscode.workspace.workspaceFolders[0];
        this.logger.info(`Starting workspace analysis: ${workspaceFolder.uri.fsPath}`);

        // Find all supported files in workspace
        const patterns = [
            '**/*.py',
            '**/*.js',
            '**/*.ts',
            '**/*.jsx',
            '**/*.tsx',
            '**/*.c',
            '**/*.cpp'
        ];

        const excludePatterns = [
            '**/node_modules/**',
            '**/.git/**',
            '**/__pycache__/**',
            '**/venv/**',
            '**/.env/**'
        ];

        for (const pattern of patterns) {
            try {
                const files = await vscode.workspace.findFiles(
                    pattern,
                    `{${excludePatterns.join(',')}}`,
                    1000 // Limit to 1000 files per pattern
                );

                this.logger.info(`Found ${files.length} files matching ${pattern}`);

                // Process files in batches to avoid overwhelming the system
                const batchSize = 10;
                for (let i = 0; i < files.length; i += batchSize) {
                    const batch = files.slice(i, i + batchSize);
                    
                    const batchPromises = batch.map(async (uri) => {
                        try {
                            const document = await vscode.workspace.openTextDocument(uri);
                            await this.diagnosticsProvider.updateFile(document);
                        } catch (error) {
                            this.logger.error(`Failed to analyze workspace file: ${uri.fsPath}`, error);
                        }
                    });

                    await Promise.allSettled(batchPromises);
                    
                    // Small delay between batches
                    await new Promise(resolve => setTimeout(resolve, 100));
                }

            } catch (error) {
                this.logger.error(`Error processing pattern ${pattern}`, error);
            }
        }

        this.logger.info('Workspace analysis completed');
    }

    public clearAllAnalysis(): void {
        this.logger.info('Clearing all analysis results');
        this.diagnosticsProvider.clearAllDiagnostics();
        
        // Clear all debounced functions
        this.debouncedAnalysis.clear();
    }

    public refreshConfiguration(): void {
        this.logger.info('Refreshing file watcher configuration');
        
        // Clear existing debounced functions
        this.debouncedAnalysis.clear();
        
        // Recreate debouncing with new settings
        this.setupDebouncing();
        
        // Re-analyze open documents if real-time analysis was enabled
        if (this.configService.get('realTimeAnalysis', true)) {
            this.analyzeOpenDocuments();
        } else {
            // Clear diagnostics if real-time analysis was disabled
            this.clearAllAnalysis();
        }
    }

    public getStatistics(): {
        watchedFiles: number;
        pendingAnalysis: number;
        totalAnalyzed: number;
    } {
        return {
            watchedFiles: this.debouncedAnalysis.size,
            pendingAnalysis: 0, // Would need to track this in a real implementation
            totalAnalyzed: 0 // Would need to track this in a real implementation
        };
    }

    public dispose(): void {
        this.logger.info('Disposing file watcher service');
        
        // Clear all debounced functions
        this.debouncedAnalysis.clear();
        
        // Dispose all event subscriptions
        for (const disposable of this.disposables) {
            disposable.dispose();
        }
        this.disposables = [];
    }
}