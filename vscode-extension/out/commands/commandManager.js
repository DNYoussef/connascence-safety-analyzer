"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.CommandManager = void 0;
const vscode = __importStar(require("vscode"));
/**
 * Centralized command manager for all extension commands
 */
class CommandManager {
    constructor(connascenceService, diagnosticsProvider, statusBar, outputManager, treeProvider, logger) {
        this.connascenceService = connascenceService;
        this.diagnosticsProvider = diagnosticsProvider;
        this.statusBar = statusBar;
        this.outputManager = outputManager;
        this.treeProvider = treeProvider;
        this.logger = logger;
        this.commands = new Map();
        this.registerAllCommands();
    }
    registerAllCommands() {
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
    async analyzeCurrentFile() {
        const activeEditor = vscode.window.activeTextEditor;
        if (!activeEditor) {
            vscode.window.showWarningMessage('No active file to analyze');
            return;
        }
        const document = activeEditor.document;
        if (!this.isSupportedLanguage(document.languageId)) {
            vscode.window.showWarningMessage(`Language '${document.languageId}' is not supported for connascence analysis`);
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
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            this.logger.error('File analysis failed', error);
            this.statusBar.showError('Analysis failed');
            vscode.window.showErrorMessage(`Analysis failed: ${errorMessage}`);
        }
    }
    async analyzeWorkspace() {
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
                const workspaceFolder = vscode.workspace.workspaceFolders[0];
                const analysisResult = await this.connascenceService.analyzeWorkspace(workspaceFolder.uri.fsPath);
                // Update diagnostics for all files
                for (const [filePath, fileResult] of Object.entries(analysisResult.fileResults)) {
                    if (token.isCancellationRequested)
                        break;
                    try {
                        const uri = vscode.Uri.file(filePath);
                        await this.diagnosticsProvider.updateDiagnostics(uri, fileResult);
                    }
                    catch (error) {
                        this.logger.error(`Failed to update diagnostics for ${filePath}`, error);
                    }
                }
                return analysisResult;
            }
            catch (error) {
                this.logger.error('Workspace analysis failed', error);
                throw error;
            }
        });
        if (result) {
            this.statusBar.showSuccess('Workspace analysis complete');
            this.treeProvider.refresh();
            const { summary } = result;
            vscode.window.showInformationMessage(`Workspace analysis complete: ${summary.filesAnalyzed} files, ${summary.totalIssues} issues found`);
        }
    }
    async analyzeSelection() {
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
    async applyAutofix() {
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
            const choice = await vscode.window.showInformationMessage(`${autofixes.length} automatic fixes available. Apply them?`, 'Yes', 'Preview', 'No');
            if (choice === 'Yes') {
                // Apply fixes directly
                this.applyFixesToDocument(activeEditor.document, autofixes);
            }
            else if (choice === 'Preview') {
                // Show preview in diff view
                this.showAutofixPreview(activeEditor.document, autofixes);
            }
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            vscode.window.showErrorMessage(`Autofix failed: ${errorMessage}`);
        }
    }
    async suggestRefactoring() {
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
            const suggestions = await this.connascenceService.suggestRefactoring(activeEditor.document.fileName, selection);
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
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            vscode.window.showErrorMessage(`Refactoring suggestion failed: ${errorMessage}`);
        }
    }
    async quickFix(uri, range) {
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
    async generateReport() {
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
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            vscode.window.showErrorMessage(`Report generation failed: ${errorMessage}`);
        }
    }
    async exportReport() {
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
            let content;
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
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            vscode.window.showErrorMessage(`Export failed: ${errorMessage}`);
        }
    }
    async showFileReport(uri, analysis) {
        // Create and show a detailed file report
        const panel = vscode.window.createWebviewPanel('connascenceFileReport', `Connascence Report - ${uri.fsPath.split(/[\\/]/).pop()}`, vscode.ViewColumn.Two, { enableScripts: true });
        panel.webview.html = this.generateFileReportHtml(analysis);
    }
    async showFunctionDetails(uri, functionName, analysis) {
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
    async showClassDetails(uri, className, analysis) {
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
    async validateSafety() {
        const activeEditor = vscode.window.activeTextEditor;
        if (!activeEditor) {
            vscode.window.showWarningMessage('No active file');
            return;
        }
        const config = vscode.workspace.getConfiguration('connascence');
        const profile = config.get('safetyProfile', 'modern_general');
        try {
            const result = await this.connascenceService.validateSafety(activeEditor.document.fileName, profile);
            if (result.compliant) {
                vscode.window.showInformationMessage('✅ File is compliant with safety profile');
            }
            else {
                const violationCount = result.violations.length;
                vscode.window.showWarningMessage(`⚠️ ${violationCount} safety violations found`, 'View Details').then(choice => {
                    if (choice === 'View Details') {
                        this.showSafetyViolations(result.violations);
                    }
                });
            }
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            vscode.window.showErrorMessage(`Safety validation failed: ${errorMessage}`);
        }
    }
    async toggleSafetyProfile() {
        const config = vscode.workspace.getConfiguration('connascence');
        const profiles = ['none', 'nasa_jpl_pot10', 'nasa_loc_1', 'nasa_loc_3', 'modern_general'];
        const current = config.get('safetyProfile', 'modern_general');
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
    async openSettings() {
        await vscode.commands.executeCommand('workbench.action.openSettings', 'connascence');
    }
    async openDashboard() {
        // Create dashboard webview
        const panel = vscode.window.createWebviewPanel('connascenceDashboard', 'Connascence Dashboard', vscode.ViewColumn.One, { enableScripts: true });
        panel.webview.html = this.generateDashboardHtml();
    }
    async refreshFindings() {
        this.treeProvider.refresh();
        vscode.window.showInformationMessage('Findings refreshed');
    }
    async clearFindings() {
        this.diagnosticsProvider.clearAllDiagnostics();
        this.treeProvider.refresh();
        this.statusBar.clear();
        vscode.window.showInformationMessage('All findings cleared');
    }
    async clearCache() {
        // Clear any cached analysis results
        this.diagnosticsProvider.clearAllDiagnostics();
        this.treeProvider.refresh();
        vscode.window.showInformationMessage('Analysis cache cleared');
    }
    // Information Commands
    async explainFinding(finding) {
        if (!finding) {
            vscode.window.showWarningMessage('No finding to explain');
            return;
        }
        const explanation = this.getDetailedExplanation(finding);
        const panel = vscode.window.createWebviewPanel('connascenceExplanation', `Connascence: ${finding.type}`, vscode.ViewColumn.Two, {});
        panel.webview.html = explanation;
    }
    async showError(errorMessage) {
        vscode.window.showErrorMessage(`Connascence: ${errorMessage}`);
        this.outputManager.show();
    }
    async showDocumentation() {
        await vscode.env.openExternal(vscode.Uri.parse('https://docs.connascence.io'));
    }
    // Helper methods
    isSupportedLanguage(languageId) {
        return ['python', 'javascript', 'typescript', 'c', 'cpp'].includes(languageId);
    }
    async applyFixesToDocument(document, autofixes) {
        const edit = new vscode.WorkspaceEdit();
        // Sort fixes by position (reverse order to avoid position shifts)
        const sortedFixes = autofixes.sort((a, b) => b.line - a.line);
        for (const fix of sortedFixes) {
            const range = new vscode.Range(fix.line - 1, fix.column || 0, fix.endLine ? fix.endLine - 1 : fix.line - 1, fix.endColumn || (fix.column || 0) + 10);
            edit.replace(document.uri, range, fix.replacement);
        }
        await vscode.workspace.applyEdit(edit);
    }
    async showAutofixPreview(document, autofixes) {
        // Create a preview document with fixes applied
        const originalContent = document.getText();
        // Apply fixes to content (implementation needed)
        const fixedContent = originalContent; // Simplified
        const previewDoc = await vscode.workspace.openTextDocument({
            content: fixedContent,
            language: document.languageId
        });
        await vscode.commands.executeCommand('vscode.diff', document.uri, previewDoc.uri, 'Connascence Autofix Preview');
    }
    async showRefactoringPreview(suggestion) {
        // Show refactoring suggestion details
        vscode.window.showInformationMessage(`Refactoring: ${suggestion.technique}\n\n${suggestion.description}`, { modal: true });
    }
    formatReportAsHtml(report) {
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
    formatReportAsCsv(report) {
        // Simple CSV format (would need more sophisticated implementation)
        return 'Type,Severity,File,Line,Message\n';
    }
    generateFileReportHtml(analysis) {
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
    generateDashboardHtml() {
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
    async showDetailedFunctionAnalysis(uri, functionName, analysis) {
        // Implementation for detailed function analysis
    }
    async showDetailedClassAnalysis(uri, className, analysis) {
        // Implementation for detailed class analysis
    }
    async showSafetyViolations(violations) {
        // Implementation for showing safety violations
    }
    getDetailedExplanation(finding) {
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
    getAllCommands() {
        return this.commands;
    }
    dispose() {
        this.commands.clear();
    }
}
exports.CommandManager = CommandManager;
//# sourceMappingURL=commandManager.js.map