import * as vscode from 'vscode';
import { ConnascenceService } from '../services/connascenceService';
import { ConnascenceDiagnosticsProvider } from '../providers/diagnosticsProvider';
import { StatusBarManager } from '../ui/statusBarManager';
import { OutputChannelManager } from '../ui/outputChannelManager';
import { ConnascenceTreeProvider } from '../providers/treeProvider';
import { ExtensionLogger } from '../utils/logger';

/**
 * Centralized command manager for all extension commands
 */
export class CommandManager implements vscode.Disposable {
    private commands = new Map<string, (...args: any[]) => any>();

    constructor(
        private connascenceService: ConnascenceService,
        private diagnosticsProvider: ConnascenceDiagnosticsProvider,
        private statusBar: StatusBarManager,
        private outputManager: OutputChannelManager,
        private treeProvider: ConnascenceTreeProvider,
        private logger: ExtensionLogger
    ) {
        this.registerAllCommands();
    }

    private registerAllCommands(): void {
        // Analysis commands
        this.commands.set('connascence.analyzeFile', this.analyzeCurrentFile.bind(this));
        this.commands.set('connascence.analyzeWorkspace', this.analyzeWorkspace.bind(this));
        this.commands.set('connascence.analyzeSelection', this.analyzeSelection.bind(this));
        
        // Quick fix commands
        this.commands.set('connascence.applyAutofix', this.applyAutofix.bind(this));
        this.commands.set('connascence.suggestRefactoring', this.suggestRefactoring.bind(this));
        this.commands.set('connascence.quickFix', this.quickFix.bind(this));
        
        // Report commands
        this.commands.set('connascence.generateReport', this.generateReport.bind(this));
        this.commands.set('connascence.exportReport', this.exportReport.bind(this));
        this.commands.set('connascence.showFileReport', this.showFileReport.bind(this));
        this.commands.set('connascence.showFunctionDetails', this.showFunctionDetails.bind(this));
        this.commands.set('connascence.showClassDetails', this.showClassDetails.bind(this));
        
        // Safety commands
        this.commands.set('connascence.validateSafety', this.validateSafety.bind(this));
        this.commands.set('connascence.toggleSafetyProfile', this.toggleSafetyProfile.bind(this));
        
        // UI commands
        this.commands.set('connascence.openSettings', this.openSettings.bind(this));
        this.commands.set('connascence.openDashboard', this.openDashboard.bind(this));
        this.commands.set('connascence.refreshFindings', this.refreshFindings.bind(this));
        this.commands.set('connascence.clearFindings', this.clearFindings.bind(this));
        this.commands.set('connascence.clearCache', this.clearCache.bind(this));
        
        // Information commands
        this.commands.set('connascence.explainFinding', this.explainFinding.bind(this));
        this.commands.set('connascence.showError', this.showError.bind(this));
        this.commands.set('connascence.showDocumentation', this.showDocumentation.bind(this));
        
        this.logger.info(`Registered ${this.commands.size} commands`);
    }

    // Analysis Commands
    private async analyzeCurrentFile(): Promise<void> {
        const activeEditor = vscode.window.activeTextEditor;
        if (!activeEditor) {
            vscode.window.showWarningMessage('No active file to analyze');
            return;
        }

        const document = activeEditor.document;
        if (!this.isSupportedLanguage(document.languageId)) {
            vscode.window.showWarningMessage(
                `Language '${document.languageId}' is not supported for connascence analysis`
            );
            return;
        }

        this.logger.info(`Analyzing file: ${document.uri.fsPath}`);
        this.statusBar.showProgress('Analyzing file...');

        try {
            await this.diagnosticsProvider.updateFile(document);
            this.statusBar.showSuccess('Analysis complete');
            
            // Show results in tree view
            this.treeProvider.refresh();
            
            vscode.window.showInformationMessage('File analysis completed');
            
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            this.logger.error('File analysis failed', error);
            this.statusBar.showError('Analysis failed');
            vscode.window.showErrorMessage(`Analysis failed: ${errorMessage}`);
        }
    }

    private async analyzeWorkspace(): Promise<void> {
        if (!vscode.workspace.workspaceFolders) {
            vscode.window.showWarningMessage('No workspace folder open');
            return;
        }

        this.logger.info('Starting workspace analysis');
        
        const result = await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'Analyzing workspace for connascence violations...',
            cancellable: true
        }, async (progress, token) => {
            try {
                const workspaceFolder = vscode.workspace.workspaceFolders![0];
                const analysisResult = await this.connascenceService.analyzeWorkspace(workspaceFolder.uri.fsPath);
                
                // Update diagnostics for all files
                for (const [filePath, fileResult] of Object.entries(analysisResult.fileResults)) {
                    if (token.isCancellationRequested) break;
                    
                    try {
                        const uri = vscode.Uri.file(filePath);
                        await this.diagnosticsProvider.updateDiagnostics(uri, fileResult);
                    } catch (error) {
                        this.logger.error(`Failed to update diagnostics for ${filePath}`, error);
                    }
                }
                
                return analysisResult;
                
            } catch (error) {
                this.logger.error('Workspace analysis failed', error);
                throw error;
            }
        });

        if (result) {
            this.statusBar.showSuccess('Workspace analysis complete');
            this.treeProvider.refresh();
            
            const { summary } = result;
            vscode.window.showInformationMessage(
                `Workspace analysis complete: ${summary.filesAnalyzed} files, ${summary.totalIssues} issues found`
            );
        }
    }

    private async analyzeSelection(): Promise<void> {
        const activeEditor = vscode.window.activeTextEditor;
        if (!activeEditor) {
            vscode.window.showWarningMessage('No active editor');
            return;
        }

        const selection = activeEditor.selection;
        if (selection.isEmpty) {
            vscode.window.showWarningMessage('Please select code to analyze');
            return;
        }

        // For now, analyze the whole file - selection analysis would need more advanced implementation
        await this.analyzeCurrentFile();
    }

    // Quick Fix Commands
    private async applyAutofix(): Promise<void> {
        const activeEditor = vscode.window.activeTextEditor;
        if (!activeEditor) {
            vscode.window.showWarningMessage('No active file');
            return;
        }

        try {
            const autofixes = await this.connascenceService.getAutofixes(activeEditor.document.fileName);
            
            if (autofixes.length === 0) {
                vscode.window.showInformationMessage('No automatic fixes available');
                return;
            }

            const choice = await vscode.window.showInformationMessage(
                `${autofixes.length} automatic fixes available. Apply them?`,
                'Yes', 'Preview', 'No'
            );

            if (choice === 'Yes') {
                // Apply fixes directly
                this.applyFixesToDocument(activeEditor.document, autofixes);
            } else if (choice === 'Preview') {
                // Show preview in diff view
                this.showAutofixPreview(activeEditor.document, autofixes);
            }

        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            vscode.window.showErrorMessage(`Autofix failed: ${errorMessage}`);
        }
    }

    private async suggestRefactoring(): Promise<void> {
        const activeEditor = vscode.window.activeTextEditor;
        if (!activeEditor) {
            vscode.window.showWarningMessage('No active file');
            return;
        }

        const selection = activeEditor.selection.isEmpty ? undefined : {
            start: { line: activeEditor.selection.start.line, character: activeEditor.selection.start.character },
            end: { line: activeEditor.selection.end.line, character: activeEditor.selection.end.character }
        };

        try {
            const suggestions = await this.connascenceService.suggestRefactoring(
                activeEditor.document.fileName,
                selection
            );

            if (suggestions.length === 0) {
                vscode.window.showInformationMessage('No refactoring suggestions available');
                return;
            }

            // Show suggestions in quick pick
            const items = suggestions.map(s => ({
                label: s.technique,
                description: `Confidence: ${Math.round(s.confidence * 100)}%`,
                detail: s.description,
                suggestion: s
            }));

            const choice = await vscode.window.showQuickPick(items, {
                placeHolder: 'Select a refactoring technique'
            });

            if (choice) {
                // Show preview or apply refactoring
                this.showRefactoringPreview(choice.suggestion);
            }

        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            vscode.window.showErrorMessage(`Refactoring suggestion failed: ${errorMessage}`);
        }
    }

    private async quickFix(uri: vscode.Uri, range: vscode.Range): Promise<void> {
        // Get diagnostics at the specified range
        const diagnostics = vscode.languages.getDiagnostics(uri)
            .filter(d => d.range.intersection(range) && d.source === 'connascence');

        if (diagnostics.length === 0) {
            vscode.window.showInformationMessage('No fixes available');
            return;
        }

        // Trigger code actions
        await vscode.commands.executeCommand('editor.action.quickFix', {
            uri,
            range
        });
    }

    // Report Commands
    private async generateReport(): Promise<void> {
        if (!vscode.workspace.workspaceFolders) {
            vscode.window.showWarningMessage('No workspace folder open');
            return;
        }

        try {
            const workspacePath = vscode.workspace.workspaceFolders[0].uri.fsPath;
            const report = await this.connascenceService.generateReport(workspacePath);
            
            // Show report in new document
            const doc = await vscode.workspace.openTextDocument({
                content: JSON.stringify(report, null, 2),
                language: 'json'
            });
            
            await vscode.window.showTextDocument(doc);
            
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            vscode.window.showErrorMessage(`Report generation failed: ${errorMessage}`);
        }
    }

    private async exportReport(): Promise<void> {
        const saveUri = await vscode.window.showSaveDialog({
            defaultUri: vscode.Uri.file('connascence-report.json'),
            filters: {
                'JSON': ['json'],
                'HTML': ['html'],
                'CSV': ['csv']
            }
        });

        if (!saveUri) {
            return;
        }

        try {
            if (!vscode.workspace.workspaceFolders) {
                throw new Error('No workspace folder open');
            }

            const workspacePath = vscode.workspace.workspaceFolders[0].uri.fsPath;
            const report = await this.connascenceService.generateReport(workspacePath);
            
            const extension = saveUri.fsPath.split('.').pop()?.toLowerCase();
            let content: string;
            
            switch (extension) {
                case 'html':
                    content = this.formatReportAsHtml(report);
                    break;
                case 'csv':
                    content = this.formatReportAsCsv(report);
                    break;
                default:
                    content = JSON.stringify(report, null, 2);
            }
            
            await vscode.workspace.fs.writeFile(saveUri, Buffer.from(content, 'utf8'));
            vscode.window.showInformationMessage(`Report exported to ${saveUri.fsPath}`);
            
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            vscode.window.showErrorMessage(`Export failed: ${errorMessage}`);
        }
    }

    private async showFileReport(uri: vscode.Uri, analysis: any): Promise<void> {
        // Create and show a detailed file report
        const panel = vscode.window.createWebviewPanel(
            'connascenceFileReport',
            `Connascence Report - ${uri.fsPath.split(/[\\/]/).pop()}`,
            vscode.ViewColumn.Two,
            { enableScripts: true }
        );

        panel.webview.html = this.generateFileReportHtml(analysis);
    }

    private async showFunctionDetails(uri: vscode.Uri, functionName: string, analysis: any): Promise<void> {
        const message = `Function: ${functionName}\n` +
                       `Parameters: ${analysis.parameterCount}\n` +
                       `Complexity: ${analysis.complexity}\n` +
                       `Lines: ${analysis.lineCount}`;

        vscode.window.showInformationMessage(message, 'View Details').then(choice => {
            if (choice === 'View Details') {
                this.showDetailedFunctionAnalysis(uri, functionName, analysis);
            }
        });
    }

    private async showClassDetails(uri: vscode.Uri, className: string, analysis: any): Promise<void> {
        const message = `Class: ${className}\n` +
                       `Methods: ${analysis.methodCount}\n` +
                       `Dependencies: ${analysis.dependencyCount}`;

        vscode.window.showInformationMessage(message, 'View Details').then(choice => {
            if (choice === 'View Details') {
                this.showDetailedClassAnalysis(uri, className, analysis);
            }
        });
    }

    // Safety Commands
    private async validateSafety(): Promise<void> {
        const activeEditor = vscode.window.activeTextEditor;
        if (!activeEditor) {
            vscode.window.showWarningMessage('No active file');
            return;
        }

        const config = vscode.workspace.getConfiguration('connascence');
        const profile = config.get<string>('safetyProfile', 'modern_general');

        try {
            const result = await this.connascenceService.validateSafety(
                activeEditor.document.fileName,
                profile
            );

            if (result.compliant) {
                vscode.window.showInformationMessage('✅ File is compliant with safety profile');
            } else {
                const violationCount = result.violations.length;
                vscode.window.showWarningMessage(
                    `⚠️ ${violationCount} safety violations found`,
                    'View Details'
                ).then(choice => {
                    if (choice === 'View Details') {
                        this.showSafetyViolations(result.violations);
                    }
                });
            }

        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            vscode.window.showErrorMessage(`Safety validation failed: ${errorMessage}`);
        }
    }

    private async toggleSafetyProfile(): Promise<void> {
        const config = vscode.workspace.getConfiguration('connascence');
        const profiles = ['none', 'nasa_jpl_pot10', 'nasa_loc_1', 'nasa_loc_3', 'modern_general'];
        const current = config.get<string>('safetyProfile', 'modern_general');

        const items = profiles.map(profile => ({
            label: profile,
            description: profile === current ? '(current)' : '',
            profile
        }));

        const choice = await vscode.window.showQuickPick(items, {
            placeHolder: 'Select safety profile'
        });

        if (choice && choice.profile !== current) {
            await config.update('safetyProfile', choice.profile, vscode.ConfigurationTarget.Workspace);
            vscode.window.showInformationMessage(`Safety profile changed to: ${choice.profile}`);
        }
    }

    // UI Commands
    private async openSettings(): Promise<void> {
        await vscode.commands.executeCommand('workbench.action.openSettings', 'connascence');
    }

    private async openDashboard(): Promise<void> {
        // Create dashboard webview
        const panel = vscode.window.createWebviewPanel(
            'connascenceDashboard',
            'Connascence Dashboard',
            vscode.ViewColumn.One,
            { enableScripts: true }
        );

        panel.webview.html = this.generateDashboardHtml();
    }

    private async refreshFindings(): Promise<void> {
        this.treeProvider.refresh();
        vscode.window.showInformationMessage('Findings refreshed');
    }

    private async clearFindings(): Promise<void> {
        this.diagnosticsProvider.clearAllDiagnostics();
        this.treeProvider.refresh();
        this.statusBar.clear();
        vscode.window.showInformationMessage('All findings cleared');
    }

    private async clearCache(): Promise<void> {
        // Clear any cached analysis results
        this.diagnosticsProvider.clearAllDiagnostics();
        this.treeProvider.refresh();
        
        vscode.window.showInformationMessage('Analysis cache cleared');
    }

    // Information Commands
    private async explainFinding(finding: any): Promise<void> {
        if (!finding) {
            vscode.window.showWarningMessage('No finding to explain');
            return;
        }

        const explanation = this.getDetailedExplanation(finding);
        
        const panel = vscode.window.createWebviewPanel(
            'connascenceExplanation',
            `Connascence: ${finding.type}`,
            vscode.ViewColumn.Two,
            {}
        );

        panel.webview.html = explanation;
    }

    private async showError(errorMessage: string): Promise<void> {
        vscode.window.showErrorMessage(`Connascence: ${errorMessage}`);
        this.outputManager.show();
    }

    private async showDocumentation(): Promise<void> {
        await vscode.env.openExternal(vscode.Uri.parse('https://docs.connascence.io'));
    }

    // Helper methods
    private isSupportedLanguage(languageId: string): boolean {
        return ['python', 'javascript', 'typescript', 'c', 'cpp'].includes(languageId);
    }

    private async applyFixesToDocument(document: vscode.TextDocument, autofixes: any[]): Promise<void> {
        const edit = new vscode.WorkspaceEdit();
        
        // Sort fixes by position (reverse order to avoid position shifts)
        const sortedFixes = autofixes.sort((a, b) => b.line - a.line);
        
        for (const fix of sortedFixes) {
            const range = new vscode.Range(
                fix.line - 1, fix.column || 0,
                fix.endLine ? fix.endLine - 1 : fix.line - 1,
                fix.endColumn || (fix.column || 0) + 10
            );
            
            edit.replace(document.uri, range, fix.replacement);
        }
        
        await vscode.workspace.applyEdit(edit);
    }

    private async showAutofixPreview(document: vscode.TextDocument, autofixes: any[]): Promise<void> {
        // Create a preview document with fixes applied
        const originalContent = document.getText();
        // Apply fixes to content (implementation needed)
        const fixedContent = originalContent; // Simplified
        
        const previewDoc = await vscode.workspace.openTextDocument({
            content: fixedContent,
            language: document.languageId
        });
        
        await vscode.commands.executeCommand('vscode.diff',
            document.uri,
            previewDoc.uri,
            'Connascence Autofix Preview'
        );
    }

    private async showRefactoringPreview(suggestion: any): Promise<void> {
        // Show refactoring suggestion details
        vscode.window.showInformationMessage(
            `Refactoring: ${suggestion.technique}\n\n${suggestion.description}`,
            { modal: true }
        );
    }

    private formatReportAsHtml(report: any): string {
        return `
        <html>
        <head><title>Connascence Report</title></head>
        <body>
            <h1>Connascence Analysis Report</h1>
            <pre>${JSON.stringify(report, null, 2)}</pre>
        </body>
        </html>
        `;
    }

    private formatReportAsCsv(report: any): string {
        // Simple CSV format (would need more sophisticated implementation)
        return 'Type,Severity,File,Line,Message\n';
    }

    private generateFileReportHtml(analysis: any): string {
        return `
        <html>
        <head><title>File Analysis</title></head>
        <body>
            <h1>Connascence Analysis</h1>
            <pre>${JSON.stringify(analysis, null, 2)}</pre>
        </body>
        </html>
        `;
    }

    private generateDashboardHtml(): string {
        return `
        <html>
        <head><title>Connascence Dashboard</title></head>
        <body>
            <h1>Connascence Dashboard</h1>
            <p>Dashboard implementation coming soon...</p>
        </body>
        </html>
        `;
    }

    private async showDetailedFunctionAnalysis(uri: vscode.Uri, functionName: string, analysis: any): Promise<void> {
        // Implementation for detailed function analysis
    }

    private async showDetailedClassAnalysis(uri: vscode.Uri, className: string, analysis: any): Promise<void> {
        // Implementation for detailed class analysis
    }

    private async showSafetyViolations(violations: any[]): Promise<void> {
        // Implementation for showing safety violations
    }

    private getDetailedExplanation(finding: any): string {
        return `
        <html>
        <head><title>Connascence Explanation</title></head>
        <body>
            <h1>${finding.type}</h1>
            <p>${finding.message}</p>
        </body>
        </html>
        `;
    }

    public getAllCommands(): Map<string, (...args: any[]) => any> {
        return this.commands;
    }

    public dispose(): void {
        this.commands.clear();
    }
}