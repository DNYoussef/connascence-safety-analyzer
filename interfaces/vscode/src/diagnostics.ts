/**
 * Diagnostics provider for Connascence violations.
 * 
 * Integrates with VS Code's diagnostic system to show connascence violations
 * as problems in the Problems panel and as squiggle underlines in the editor.
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { spawn } from 'child_process';
import { MCPClient } from './services/mcpClient';
import { CacheService, IncrementalAnalysisTracker } from './services/cacheService';

export interface ConnascenceViolation {
    id: string;
    ruleId: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    connascenceType: string;
    description: string;
    filePath: string;
    lineNumber: number;
    columnNumber?: number;
    weight: number;
    recommendation?: string;
}

export class ConnascenceDiagnostics {
    private diagnosticCollection?: vscode.DiagnosticCollection;
    private debounceTimer?: NodeJS.Timeout;
    private scanPromises = new Map<string, Promise<void>>();
    private mcpClient: MCPClient | null = null;
    private cacheService: CacheService;
    private incrementalTracker: IncrementalAnalysisTracker;

    constructor(private context: vscode.ExtensionContext) {
        this.cacheService = new CacheService(context);
        this.incrementalTracker = new IncrementalAnalysisTracker();
        this.initializeMCPClient();
        this.setupFileWatcher();
    }

    /**
     * Initialize MCP client with graceful fallback
     */
    private async initializeMCPClient(): Promise<void> {
        const config = vscode.workspace.getConfiguration('connascence');
        const useMCP = config.get<boolean>('useMCP', false);

        if (!useMCP) {
            return; // MCP disabled, use CLI
        }

        try {
            this.mcpClient = new MCPClient(this.context);
            await this.mcpClient.connect();
            console.log('[ConnascenceDiagnostics] MCP client connected');
        } catch (error) {
            console.warn('[ConnascenceDiagnostics] MCP client unavailable, using CLI fallback:', error);
            this.mcpClient = null;
        }
    }

    setCollection(collection: vscode.DiagnosticCollection) {
        this.diagnosticCollection = collection;
    }

    async scanFile(document: vscode.TextDocument): Promise<void> {
        if (document.languageId !== 'python') return;

        const filePath = document.uri.fsPath;

        try {
            // Generate content hash for cache validation
            const content = document.getText();
            const contentHash = CacheService.generateHash(content);
            const cacheKey = CacheService.generateFileKey(filePath, 'diagnostics');

            // Check cache first
            const cachedViolations = await this.cacheService.get<ConnascenceViolation[]>(cacheKey, contentHash);
            if (cachedViolations) {
                console.log(`[Diagnostics] Using cached results for ${path.basename(filePath)}`);
                this.updateDiagnostics(document.uri, cachedViolations);
                return;
            }

            // Run fresh analysis
            const violations = await this.runConnascenceAnalysis(filePath);

            // Cache results
            await this.cacheService.set(cacheKey, violations, contentHash, { persistent: true });

            this.updateDiagnostics(document.uri, violations);
        } catch (error) {
            console.error(`Failed to scan ${filePath}:`, error);
        }
    }

    scanFileDebounced(document: vscode.TextDocument): void {
        const config = vscode.workspace.getConfiguration('connascence');
        const debounceMs = config.get<number>('debounceMs', 1000);
        
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }
        
        this.debounceTimer = setTimeout(() => {
            this.scanFile(document);
        }, debounceMs);
    }

    async scanWorkspace(): Promise<void> {
        if (!vscode.workspace.workspaceFolders) return;
        
        vscode.window.withProgress({
            location: vscode.ProgressLocation.Window,
            title: 'Scanning workspace for connascence violations',
            cancellable: false
        }, async (progress) => {
            const workspaceRoot = vscode.workspace.workspaceFolders![0].uri.fsPath;
            
            try {
                const violations = await this.runConnascenceAnalysis(workspaceRoot, true);
                this.updateWorkspaceDiagnostics(violations);
                
                // Update context for when findings exist
                vscode.commands.executeCommand('setContext', 'connascence.hasFindings', violations.length > 0);
                
                vscode.window.showInformationMessage(
                    `Connascence scan complete: ${violations.length} violations found`
                );
            } catch (error) {
                vscode.window.showErrorMessage(`Connascence scan failed: ${error}`);
            }
        });
    }

    private async runConnascenceAnalysis(targetPath: string, isWorkspace = false): Promise<ConnascenceViolation[]> {
        const config = vscode.workspace.getConfiguration('connascence');
        const binaryPath = config.get<string>('pathToBinary', 'connascence');
        const policyPreset = config.get<string>('policyPreset', 'service-defaults');
        const useMCP = config.get<boolean>('useMCP', false);
        
        if (useMCP) {
            return this.runMCPAnalysis(targetPath, isWorkspace);
        } else {
            return this.runCLIAnalysis(binaryPath, targetPath, policyPreset);
        }
    }

    private async runCLIAnalysis(binaryPath: string, targetPath: string, policy: string): Promise<ConnascenceViolation[]> {
        return new Promise((resolve, reject) => {
            const args = ['scan', targetPath, '--format', 'json', '--policy', policy];
            const process = spawn(binaryPath, args);
            
            let stdout = '';
            let stderr = '';
            
            process.stdout.on('data', (data) => {
                stdout += data.toString();
            });
            
            process.stderr.on('data', (data) => {
                stderr += data.toString();
            });
            
            process.on('close', (code) => {
                if (code === 0) {
                    try {
                        const result = JSON.parse(stdout);
                        const violations = this.parseViolations(result);
                        resolve(violations);
                    } catch (error) {
                        reject(new Error(`Failed to parse connascence output: ${error}`));
                    }
                } else {
                    reject(new Error(`Connascence CLI failed (code ${code}): ${stderr}`));
                }
            });
            
            process.on('error', (error) => {
                reject(new Error(`Failed to run connascence: ${error.message}`));
            });
        });
    }

    private async runMCPAnalysis(targetPath: string, isWorkspace: boolean): Promise<ConnascenceViolation[]> {
        if (!this.mcpClient || !this.mcpClient.isServerConnected()) {
            console.warn('[ConnascenceDiagnostics] MCP not available, falling back to CLI');
            const config = vscode.workspace.getConfiguration('connascence');
            const binaryPath = config.get<string>('pathToBinary', 'connascence');
            const policy = config.get<string>('policyPreset', 'service-defaults');
            return this.runCLIAnalysis(binaryPath, targetPath, policy);
        }

        try {
            let result: any;

            if (isWorkspace) {
                // Workspace analysis
                result = await this.mcpClient.analyzeWorkspace(targetPath, {
                    format: 'json',
                    includeTests: vscode.workspace.getConfiguration('connascence').get('includeTests', false)
                });
            } else {
                // Single file analysis
                result = await this.mcpClient.analyzeFile(targetPath, {
                    format: 'json'
                });
            }

            // Parse the result
            const violations = this.parseViolations(result);
            return violations;

        } catch (error) {
            console.error('[ConnascenceDiagnostics] MCP analysis failed:', error);

            // Fallback to CLI on error
            const config = vscode.workspace.getConfiguration('connascence');
            const binaryPath = config.get<string>('pathToBinary', 'connascence');
            const policy = config.get<string>('policyPreset', 'service-defaults');
            return this.runCLIAnalysis(binaryPath, targetPath, policy);
        }
    }

    private parseViolations(result: any): ConnascenceViolation[] {
        if (!result.violations || !Array.isArray(result.violations)) {
            return [];
        }
        
        const config = vscode.workspace.getConfiguration('connascence');
        const severityThreshold = config.get<string>('severityThreshold', 'medium');
        const maxDiagnostics = config.get<number>('maxDiagnostics', 1500);
        
        const severityOrder = { 'low': 1, 'medium': 2, 'high': 3, 'critical': 4 };
        const minSeverity = severityOrder[severityThreshold as keyof typeof severityOrder] || 2;
        
        return result.violations
            .filter((v: any) => severityOrder[v.severity as keyof typeof severityOrder] >= minSeverity)
            .slice(0, maxDiagnostics)
            .map((v: any) => ({
                id: v.id,
                ruleId: v.rule_id,
                severity: v.severity,
                connascenceType: v.connascence_type || v.rule_id.replace('CON_', ''),
                description: v.description,
                filePath: v.file_path,
                lineNumber: v.line_number,
                columnNumber: v.column_number,
                weight: v.weight || 1,
                recommendation: v.recommendation
            }));
    }

    private updateDiagnostics(uri: vscode.Uri, violations: ConnascenceViolation[]): void {
        if (!this.diagnosticCollection) return;
        
        const diagnostics: vscode.Diagnostic[] = violations
            .filter(v => path.resolve(v.filePath) === uri.fsPath)
            .map(v => this.violationToDiagnostic(v));
        
        this.diagnosticCollection.set(uri, diagnostics);
    }

    private updateWorkspaceDiagnostics(violations: ConnascenceViolation[]): void {
        if (!this.diagnosticCollection) return;
        
        // Clear existing diagnostics
        this.diagnosticCollection.clear();
        
        // Group violations by file
        const violationsByFile = new Map<string, ConnascenceViolation[]>();
        
        for (const violation of violations) {
            const filePath = path.resolve(violation.filePath);
            if (!violationsByFile.has(filePath)) {
                violationsByFile.set(filePath, []);
            }
            violationsByFile.get(filePath)!.push(violation);
        }
        
        // Set diagnostics for each file
        for (const [filePath, fileViolations] of violationsByFile) {
            const uri = vscode.Uri.file(filePath);
            const diagnostics = fileViolations.map(v => this.violationToDiagnostic(v));
            this.diagnosticCollection.set(uri, diagnostics);
        }
    }

    private violationToDiagnostic(violation: ConnascenceViolation): vscode.Diagnostic {
        const line = Math.max(0, violation.lineNumber - 1); // VS Code uses 0-based line numbers
        const startChar = Math.max(0, (violation.columnNumber || 1) - 1);
        
        const range = new vscode.Range(
            new vscode.Position(line, startChar),
            new vscode.Position(line, startChar + 10) // Approximate end position
        );
        
        const diagnostic = new vscode.Diagnostic(
            range,
            violation.description,
            this.severityToVSCodeSeverity(violation.severity)
        );
        
        diagnostic.code = violation.ruleId;
        diagnostic.source = 'connascence';
        
        // Add related information
        if (violation.recommendation) {
            diagnostic.relatedInformation = [
                new vscode.DiagnosticRelatedInformation(
                    new vscode.Location(vscode.Uri.file(violation.filePath), range),
                    `Recommendation: ${violation.recommendation}`
                )
            ];
        }
        
        // Add tags for certain violation types
        if (violation.severity === 'critical') {
            diagnostic.tags = [vscode.DiagnosticTag.Deprecated]; // Use deprecated tag for critical issues
        }
        
        return diagnostic;
    }

    private severityToVSCodeSeverity(severity: string): vscode.DiagnosticSeverity {
        switch (severity) {
            case 'critical':
                return vscode.DiagnosticSeverity.Error;
            case 'high':
                return vscode.DiagnosticSeverity.Warning;
            case 'medium':
                return vscode.DiagnosticSeverity.Information;
            case 'low':
            default:
                return vscode.DiagnosticSeverity.Hint;
        }
    }

    clearFile(uri: vscode.Uri): void {
        if (this.diagnosticCollection) {
            this.diagnosticCollection.delete(uri);
        }
    }

    clearAll(): void {
        if (this.diagnosticCollection) {
            this.diagnosticCollection.clear();
        }
    }

    refreshAll(): void {
        // Re-scan all open Python files
        vscode.workspace.textDocuments
            .filter(doc => doc.languageId === 'python')
            .forEach(doc => this.scanFileDebounced(doc));
    }

    /**
     * Setup file watcher for incremental analysis
     */
    private setupFileWatcher(): void {
        const watcher = vscode.workspace.createFileSystemWatcher('**/*.py');

        watcher.onDidChange((uri) => {
            this.incrementalTracker.trackModification(uri.fsPath);
            const cacheKey = CacheService.generateFileKey(uri.fsPath, 'diagnostics');
            this.cacheService.invalidate(cacheKey);
        });

        watcher.onDidDelete((uri) => {
            const cacheKey = CacheService.generateFileKey(uri.fsPath, 'diagnostics');
            this.cacheService.invalidate(cacheKey);
            if (this.diagnosticCollection) {
                this.diagnosticCollection.delete(uri);
            }
        });

        this.context.subscriptions.push(watcher);
    }

    dispose(): void {
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }

        // Cancel any running scan promises
        this.scanPromises.clear();

        // Disconnect MCP client
        if (this.mcpClient) {
            this.mcpClient.dispose();
            this.mcpClient = null;
        }

        // Save cache before disposing
        this.cacheService.dispose();
    }
}