import * as vscode from 'vscode';
import { AnalysisResult, Finding } from '../services/connascenceService';
import { ConfigurationService } from '../services/configurationService';
import { ExtensionLogger } from '../utils/logger';
import { generateSimpleDashboardHTML } from './simpleDashboard';

// AI Provider Configuration Interface  
export interface AIProviderConfig {
    id: string;
    name: string;
    enabled: boolean;
    apiKey?: string;
    model?: string;
    endpoint?: string;
    maxTokens?: number;
    temperature?: number;
}

// Extended TreeItem interface
interface TreeItem extends vscode.TreeItem {
    finding?: Finding;
    providerId?: string;
    children?: TreeItem[];
}

/**
 * Unified UI Manager
 * 
 * MECE Responsibility: ALL user interface concerns
 * - Status bar updates and progress indication
 * - Output channel logging and messages  
 * - Dashboard webview with charts and metrics
 * - Tree view for violation navigation
 * - Notifications and user feedback
 */
export class UIManager implements vscode.Disposable {
    // Status Bar
    private statusBarItem: vscode.StatusBarItem;
    private isAnalyzing = false;

    // Output Channel  
    private outputChannel: vscode.OutputChannel;

    // Dashboard Webview
    private dashboardPanel: vscode.WebviewPanel | undefined;
    
    // Tree View (Consolidated)
    private treeDataProvider!: ConnascenceTreeDataProvider;
    private treeView!: vscode.TreeView<TreeItem>;
    
    // AI Provider data
    private aiProviders: Map<string, AIProviderConfig> = new Map();

    // Current data
    private currentResults: Map<string, AnalysisResult> = new Map();
    private totalViolations = 0;

    constructor(
        private context: vscode.ExtensionContext,
        private configService: ConfigurationService,
        private logger: ExtensionLogger
    ) {
        // Initialize status bar
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
        this.statusBarItem.command = 'connascence.showDashboard';
        this.statusBarItem.show();
        
        // Initialize output channel
        this.outputChannel = vscode.window.createOutputChannel('Connascence Safety Analyzer');
        this.outputChannel.appendLine('=== Connascence Safety Analyzer ===');
        
        this.initializeTreeView();
        this.loadAIProviders();
    }

    // === PUBLIC API ===

    /**
     * Update AI provider configuration
     */
    public updateAIProvider(providerId: string, config: AIProviderConfig): void {
        this.aiProviders.set(providerId, config);
        this.treeDataProvider.refresh();
    }

    /**
     * Get AI provider configuration
     */
    public getAIProvider(providerId: string): AIProviderConfig | undefined {
        return this.aiProviders.get(providerId);
    }

    /**
     * Update UI with analysis results for a file
     */
    public updateFileResults(uri: vscode.Uri, results: AnalysisResult): void {
        this.currentResults.set(uri.toString(), results);
        this.recalculateStats();
        
        // Update all UI components
        this.updateStatusBar();
        this.updateTreeView();
        this.updateDashboard();
        
        // Log results
        this.logAnalysisResults(uri, results);
    }

    /**
     * Clear results for a file
     */
    public clearFileResults(uri: vscode.Uri): void {
        this.currentResults.delete(uri.toString());
        this.recalculateStats();
        this.updateStatusBar();
        this.updateTreeView();
        this.updateDashboard();
    }

    /**
     * Clear all results
     */
    public clearAllResults(): void {
        this.currentResults.clear();
        this.totalViolations = 0;
        this.updateStatusBar();
        this.updateTreeView();
        this.updateDashboard();
        this.outputChannel.clear();
    }

    /**
     * Show dashboard
     */
    public showDashboard(): void {
        if (this.dashboardPanel) {
            this.dashboardPanel.reveal();
            return;
        }

        this.createDashboardPanel();
        this.updateDashboard();
    }

    /**
     * Set analyzing state
     */
    public setAnalyzing(analyzing: boolean, fileName?: string): void {
        this.isAnalyzing = analyzing;
        this.updateStatusBar(fileName);
        
        if (analyzing && fileName) {
            this.outputChannel.appendLine(`[ANALYSIS] Starting analysis: ${fileName}`);
        }
    }

    /**
     * Show notification message
     */
    public showMessage(message: string, type: 'info' | 'warning' | 'error' = 'info'): void {
        switch (type) {
            case 'error':
                vscode.window.showErrorMessage(message);
                this.outputChannel.appendLine(`[ERROR] ${message}`);
                break;
            case 'warning':
                vscode.window.showWarningMessage(message);
                this.outputChannel.appendLine(`[WARN] ${message}`);
                break;
            default:
                vscode.window.showInformationMessage(message);
                this.outputChannel.appendLine(`[INFO] ${message}`);
        }
    }

    /**
     * Show progress notification
     */
    public async showProgress<T>(
        title: string, 
        task: (progress: vscode.Progress<{ increment?: number; message?: string }>) => Promise<T>
    ): Promise<T> {
        return vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title,
            cancellable: false
        }, task);
    }

    /**
     * Focus on specific violation
     */
    public focusViolation(finding: Finding): void {
        // Navigate to file and line
        vscode.workspace.openTextDocument(finding.file).then(document => {
            vscode.window.showTextDocument(document).then(editor => {
                const line = Math.max(0, finding.line - 1);
                const range = new vscode.Range(line, 0, line, 0);
                editor.selection = new vscode.Selection(range.start, range.end);
                editor.revealRange(range, vscode.TextEditorRevealType.InCenter);
            });
        });

        // Update dashboard to highlight this violation
        if (this.dashboardPanel) {
            this.dashboardPanel.webview.postMessage({
                type: 'focusViolation',
                finding: finding
            });
        }
    }

    /**
     * Handle AI chat messages from the webview
     */
    private async handleAIChatMessage(message: any): Promise<void> {
        try {
            const userMessage = message.message;
            const context = message.context;
            
            // Generate AI response based on current violations and context
            let aiResponse = await this.generateAIResponse(userMessage, context);
            
            // Send response back to webview
            if (this.dashboardPanel) {
                this.dashboardPanel.webview.postMessage({
                    type: 'aiResponse',
                    response: aiResponse
                });
            }
            
        } catch (error) {
            this.logger.error('AI chat handling failed', error);
            
            // Send error response
            if (this.dashboardPanel) {
                this.dashboardPanel.webview.postMessage({
                    type: 'aiResponse',
                    response: 'I apologize, but I encountered an error processing your request. Please try again or check the extension logs.'
                });
            }
        }
    }

    /**
     * Generate AI response based on user message and violation context
     */
    private async generateAIResponse(userMessage: string, context: any): Promise<string> {
        const lowerMessage = userMessage.toLowerCase();
        
        // Analyze message intent and provide contextual responses
        if (lowerMessage.includes('critical') || lowerMessage.includes('urgent')) {
            return this.generateCriticalViolationsResponse(context);
        } else if (lowerMessage.includes('fix') || lowerMessage.includes('refactor')) {
            return this.generateRefactoringResponse(context);
        } else if (lowerMessage.includes('explain') || lowerMessage.includes('theory')) {
            return this.generateTheoryResponse(context);
        } else if (lowerMessage.includes('priority') || lowerMessage.includes('order')) {
            return this.generatePriorityResponse(context);
        } else if (lowerMessage.includes('magic') || lowerMessage.includes('literal')) {
            return this.generateMagicLiteralResponse(context);
        } else if (lowerMessage.includes('algorithm') || lowerMessage.includes('god object')) {
            return this.generateAlgorithmResponse(context);
        } else if (lowerMessage.includes('position') || lowerMessage.includes('parameter')) {
            return this.generatePositionResponse(context);
        } else {
            return this.generateGeneralResponse(userMessage, context);
        }
    }

    private generateCriticalViolationsResponse(context: any): string {
        if (context.criticalCount === 0) {
            return "🎉 Great news! You have no critical connascence violations in your current analysis. Your code is in good shape from a coupling perspective. Keep following good practices to maintain this quality.";
        }
        
        return `⚠️ You have **${context.criticalCount} critical violations** that need immediate attention:\n\n` +
               `**Why Critical Violations Matter:**\n` +
               `• They represent the highest form of coupling\n` +
               `• Make code extremely fragile to changes\n` +
               `• Significantly impact maintainability and testing\n\n` +
               `**Immediate Actions:**\n` +
               `1. Focus on God Objects/Large Classes first\n` +
               `2. Extract methods and responsibilities\n` +
               `3. Use dependency injection patterns\n` +
               `4. Consider architectural refactoring\n\n` +
               `Use the hover tooltips on red highlights for specific AI-powered fix suggestions!`;
    }

    private generateRefactoringResponse(context: any): string {
        const topTypes = context.topTypes || [];
        let response = "🔧 **Refactoring Strategy for Your Code:**\n\n";
        
        if (topTypes.length === 0) {
            return response + "Your code currently has no connascence violations detected. Excellent work! Continue following SOLID principles and clean code practices.";
        }
        
        response += "**Priority Order (Fix These First):**\n";
        topTypes.forEach((type: string, index: number) => {
            const priority = index + 1;
            switch (type.toLowerCase()) {
                case 'algorithm':
                case 'god_object':
                    response += `${priority}. **${type}** - Extract methods, apply Single Responsibility Principle\n`;
                    break;
                case 'meaning':
                case 'magic_literal':
                    response += `${priority}. **${type}** - Extract constants, use configuration files\n`;
                    break;
                case 'position':
                    response += `${priority}. **${type}** - Use named parameters, parameter objects\n`;
                    break;
                default:
                    response += `${priority}. **${type}** - Reduce coupling through abstraction\n`;
            }
        });
        
        response += `\n**Pro Tips:**\n` +
                   `• Start with violations marked as "Critical" severity\n` +
                   `• Use the AI fix suggestions in hover tooltips\n` +
                   `• Test after each refactoring step\n` +
                   `• Consider using IDE refactoring tools`;
        
        return response;
    }

    private generateTheoryResponse(context: any): string {
        return `📚 **Connascence Theory Quick Guide:**\n\n` +
               `**What is Connascence?**\n` +
               `Connascence measures the degree of coupling between software elements. Lower connascence = better maintainability.\n\n` +
               `**The Connascence Hierarchy (Worst to Best):**\n` +
               `1. **Identity** - Must reference same object\n` +
               `2. **Value** - Must agree on values\n` +
               `3. **Timing** - Execution order matters\n` +
               `4. **Execution** - Order of execution\n` +
               `5. **Algorithm** - Must use same algorithm (God Objects)\n` +
               `6. **Meaning** - Must agree on meaning (Magic literals)\n` +
               `7. **Position** - Order matters (Parameters)\n` +
               `8. **Type** - Must agree on data types\n` +
               `9. **Name** - Must agree on names\n\n` +
               `**Golden Rules:**\n` +
               `• Minimize overall connascence\n` +
               `• Prefer static over dynamic connascence\n` +
               `• Convert stronger forms to weaker ones\n\n` +
               `**Your Current Status:** ${context.violations} violations found`;
    }

    private generatePriorityResponse(context: any): string {
        return `📊 **Recommended Fix Priority Order:**\n\n` +
               `**1. Critical Violations (${context.criticalCount})** 🔴\n` +
               `   - God Objects and Algorithm violations\n` +
               `   - Fix immediately - highest impact\n\n` +
               `**2. Major Violations** 🟡\n` +
               `   - Magic literals and meaning violations\n` +
               `   - Moderate effort, high value\n\n` +
               `**3. Minor Violations** 🟢\n` +
               `   - Position and naming issues\n` +
               `   - Quick wins, good for momentum\n\n` +
               `**Time Investment Strategy:**\n` +
               `• Spend 60% effort on Critical\n` +
               `• Spend 30% effort on Major\n` +
               `• Spend 10% effort on Minor\n\n` +
               `**Expected ROI:**\n` +
               `Fixing critical violations can improve maintainability by 40-60%!`;
    }

    private generateMagicLiteralResponse(context: any): string {
        return `✨ **Magic Literal Violations - Quick Fix Guide:**\n\n` +
               `**What's the Problem?**\n` +
               `Magic literals create hidden dependencies and make code harder to understand and maintain.\n\n` +
               `**Common Examples:**\n` +
               `• \`if (status === 42)\` → What does 42 mean?\n` +
               `• \`array.slice(0, 10)\` → Why 10?\n` +
               `• \`setTimeout(callback, 5000)\` → Why 5 seconds?\n\n` +
               `**Refactoring Solutions:**\n` +
               `1. **Extract Constants:**\n` +
               `   \`const MAX_RETRIES = 3;\`\n` +
               `   \`const DEFAULT_TIMEOUT = 5000;\`\n\n` +
               `2. **Configuration Files:**\n` +
               `   \`config.json: { "maxRetries": 3 }\`\n\n` +
               `3. **Named Parameters:**\n` +
               `   \`processData({ maxItems: 10, timeout: 5000 })\`\n\n` +
               `**AI Help:** Hover over red highlights for context-specific fix suggestions!`;
    }

    private generateAlgorithmResponse(context: any): string {
        return `🏛️ **God Object / Algorithm Violations:**\n\n` +
               `**The Problem:**\n` +
               `Classes or functions doing too much - violating Single Responsibility Principle.\n\n` +
               `**Warning Signs:**\n` +
               `• Classes with 500+ lines\n` +
               `• Methods with 50+ lines\n` +
               `• Multiple unrelated responsibilities\n` +
               `• Hard to test or understand\n\n` +
               `**Refactoring Strategy:**\n` +
               `1. **Extract Method** - Break large methods\n` +
               `2. **Extract Class** - Separate responsibilities\n` +
               `3. **Strategy Pattern** - Encapsulate algorithms\n` +
               `4. **Dependency Injection** - Reduce coupling\n\n` +
               `**Example Refactoring:**\n` +
               `\`\`\`\n` +
               `// Before: God Object\n` +
               `class UserManager {\n` +
               `  validateUser() { ... }\n` +
               `  saveToDatabase() { ... }\n` +
               `  sendEmail() { ... }\n` +
               `  generateReport() { ... }\n` +
               `}\n\n` +
               `// After: Single Responsibility\n` +
               `class UserValidator { ... }\n` +
               `class UserRepository { ... }\n` +
               `class EmailService { ... }\n` +
               `class ReportGenerator { ... }\n` +
               `\`\`\`\n\n` +
               `**Priority:** Fix these first - highest impact on code quality!`;
    }

    private generatePositionResponse(context: any): string {
        return `🔗 **Parameter Position Violations:**\n\n` +
               `**The Issue:**\n` +
               `Methods with many positional parameters are fragile and error-prone.\n\n` +
               `**Problems with Positional Parameters:**\n` +
               `• Easy to mix up parameter order\n` +
               `• Hard to understand at call site\n` +
               `• Brittle when signature changes\n\n` +
               `**Better Approaches:**\n` +
               `1. **Named Parameters (Object):**\n` +
               `   \`createUser({ name, email, age, role })\`\n\n` +
               `2. **Builder Pattern:**\n` +
               `   \`new UserBuilder().withName().withEmail().build()\`\n\n` +
               `3. **Parameter Object:**\n` +
               `   \`class UserConfig { name; email; age; role }\`\n\n` +
               `4. **Method Chaining:**\n` +
               `   \`user.setName().setEmail().setAge()\`\n\n` +
               `**Quick Win:** These are usually easy to fix and provide immediate clarity improvement!`;
    }

    private generateGeneralResponse(userMessage: string, context: any): string {
        const hasViolations = context.violations > 0;
        
        if (!hasViolations) {
            return `🎉 **Your code looks great!** No connascence violations detected.\n\n` +
                   `**Keep up the good work with:**\n` +
                   `• Following SOLID principles\n` +
                   `• Writing clean, readable code\n` +
                   `• Regular refactoring\n` +
                   `• Good test coverage\n\n` +
                   `Feel free to ask about connascence theory, best practices, or specific coding questions!`;
        }
        
        return `🤖 **I'm here to help with your connascence violations!**\n\n` +
               `**Current Status:**\n` +
               `• Total violations: ${context.violations}\n` +
               `• Critical issues: ${context.criticalCount}\n` +
               `• Top violation types: ${context.topTypes?.join(', ') || 'None'}\n\n` +
               `**I can help you:**\n` +
               `• Explain specific violation types\n` +
               `• Suggest refactoring strategies\n` +
               `• Prioritize fixes for maximum impact\n` +
               `• Provide theory and best practices\n\n` +
               `**Try asking:**\n` +
               `• "What are my critical violations?"\n` +
               `• "How do I fix magic literals?"\n` +
               `• "Show me refactoring priorities"\n` +
               `• "Explain connascence theory"\n\n` +
               `You can also hover over red highlights in your code for AI-powered fix suggestions!`;
    }

    // === PRIVATE METHODS ===

    private initializeStatusBar(): void {
        this.statusBarItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Right, 
            200
        );
        
        this.statusBarItem.command = 'connascence.showDashboard';
        this.updateStatusBar();
        this.statusBarItem.show();
    }

    private initializeOutputChannel(): void {
        this.outputChannel = vscode.window.createOutputChannel('Connascence Analysis');
        this.outputChannel.appendLine('=== Connascence Safety Analyzer ===');
        this.outputChannel.appendLine(`Extension activated at ${new Date().toLocaleString()}`);
    }

    private initializeTreeView(): void {
        this.treeDataProvider = new ConnascenceTreeDataProvider(this.context, this.configService, this.logger);
        this.treeView = vscode.window.createTreeView('connascenceFindings', {
            treeDataProvider: this.treeDataProvider,
            showCollapseAll: true,
            canSelectMany: false
        });

        // Handle tree item selection
        this.treeView.onDidChangeSelection(e => {
            if (e.selection.length > 0) {
                const item = e.selection[0];
                if (item.finding) {
                    this.focusViolation(item.finding);
                } else if (item.command) {
                    vscode.commands.executeCommand(item.command.command, ...(item.command.arguments || []));
                }
            }
        });
    }

    private updateStatusBar(fileName?: string): void {
        if (this.isAnalyzing) {
            this.statusBarItem.text = `$(sync~spin) Analyzing${fileName ? ` ${fileName}` : '...'}`;
            this.statusBarItem.tooltip = 'Connascence analysis in progress';
        } else if (this.totalViolations > 0) {
            this.statusBarItem.text = `$(warning) ${this.totalViolations} connascence violations`;
            this.statusBarItem.tooltip = `Found ${this.totalViolations} connascence violations. Click to view dashboard.`;
        } else {
            this.statusBarItem.text = `$(check) No connascence issues`;
            this.statusBarItem.tooltip = 'No connascence violations detected';
        }
    }

    private updateTreeView(): void {
        const allFindings: Finding[] = [];
        for (const results of this.currentResults.values()) {
            allFindings.push(...results.findings);
        }
        
        this.treeDataProvider.updateFindings(allFindings);
        this.treeDataProvider.refresh();
    }

    private updateDashboard(): void {
        if (!this.dashboardPanel) return;

        const allResults = Array.from(this.currentResults.values());
        const summary = this.generateSummary(allResults);
        const charts = this.generateChartData(allResults);
        
        this.dashboardPanel.webview.html = generateSimpleDashboardHTML(summary, charts);
    }

    private createDashboardPanel(): void {
        this.dashboardPanel = vscode.window.createWebviewPanel(
            'connascenceDashboard',
            '🔗 Connascence Dashboard',
            vscode.ViewColumn.Two,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
                localResourceRoots: [
                    vscode.Uri.joinPath(this.context.extensionUri, 'resources')
                ]
            }
        );

        this.dashboardPanel.iconPath = {
            light: vscode.Uri.joinPath(this.context.extensionUri, 'resources', 'icon-light.svg'),
            dark: vscode.Uri.joinPath(this.context.extensionUri, 'resources', 'icon-dark.svg')
        };

        this.dashboardPanel.onDidDispose(() => {
            this.dashboardPanel = undefined;
        });

        // Handle webview messages
        this.dashboardPanel.webview.onDidReceiveMessage(async message => {
            switch (message.type) {
                case 'openFile':
                    vscode.workspace.openTextDocument(message.filePath).then(doc => {
                        vscode.window.showTextDocument(doc);
                    });
                    break;
                case 'gotoViolation':
                    const finding: Finding = {
                        id: 'temp',
                        type: 'unknown',
                        severity: 'info',
                        message: '',
                        file: message.filePath,
                        line: message.lineNumber
                    };
                    this.focusViolation(finding);
                    break;
                case 'aiChat':
                    await this.handleAIChatMessage(message);
                    break;
            }
        });
    }

    private logAnalysisResults(uri: vscode.Uri, results: AnalysisResult): void {
        const fileName = uri.fsPath.split('/').pop() || uri.fsPath;
        const timestamp = new Date().toLocaleTimeString();
        
        this.outputChannel.appendLine(
            `[${timestamp}] ${fileName}: ${results.findings.length} violations (score: ${results.qualityScore})`
        );

        if (results.findings.length > 0) {
            const severityCount = results.summary.issuesBySeverity;
            this.outputChannel.appendLine(
                `  Critical: ${severityCount.critical}, Major: ${severityCount.major}, Minor: ${severityCount.minor}, Info: ${severityCount.info}`
            );
        }
    }

    private recalculateStats(): void {
        this.totalViolations = 0;
        for (const results of this.currentResults.values()) {
            this.totalViolations += results.findings.length;
        }
    }

    private generateSummary(results: AnalysisResult[]): any {
        const summary = {
            totalFiles: results.length,
            totalViolations: 0,
            averageScore: 0,
            severityBreakdown: { critical: 0, major: 0, minor: 0, info: 0 },
            typeBreakdown: new Map<string, number>()
        };

        let totalScore = 0;

        for (const result of results) {
            summary.totalViolations += result.findings.length;
            totalScore += result.qualityScore;

            // Count by severity
            for (const finding of result.findings) {
                const severity = finding.severity as keyof typeof summary.severityBreakdown;
                if (severity in summary.severityBreakdown) {
                    summary.severityBreakdown[severity]++;
                }

                // Count by type
                const count = summary.typeBreakdown.get(finding.type) || 0;
                summary.typeBreakdown.set(finding.type, count + 1);
            }
        }

        summary.averageScore = results.length > 0 ? totalScore / results.length : 100;

        return summary;
    }

    private generateChartData(results: AnalysisResult[]): any {
        const summary = this.generateSummary(results);
        
        return {
            severity: summary.severityBreakdown,
            types: Object.fromEntries(summary.typeBreakdown),
            qualityTrend: results.map(r => r.qualityScore) // Simplified trend
        };
    }

    private generateDashboardHTML(summary: any, charts: any): string {
        return generateSimpleDashboardHTML(summary, charts);
    }

    dispose(): void {
        this.statusBarItem.dispose();
        this.outputChannel.dispose();
        this.dashboardPanel?.dispose();
        this.treeView.dispose();
    }
}

// Consolidated Tree Data Provider with multiple tabs/sections
class ConnascenceTreeDataProvider implements vscode.TreeDataProvider<TreeItem> {
    private _onDidChangeTreeData = new vscode.EventEmitter<TreeItem | undefined | null | void>();
    readonly onDidChangeTreeData = this._onDidChangeTreeData.event;
    
    private findings: Finding[] = [];
    private markdownFiles: Map<string, vscode.Uri[]> = new Map();
    private aiProviders: Map<string, AIProviderConfig> = new Map();
    private mcpServerUrl: string;

    constructor(
        private context: vscode.ExtensionContext,
        private configService: any,
        private logger: any
    ) {
        this.mcpServerUrl = this.configService.get('serverUrl', 'http://localhost:8080');
        this.scanMarkdownFiles();
        this.setupFileWatcher();
    }
    
    setAIProviders(providers: Map<string, AIProviderConfig>): void {
        this.aiProviders = providers;
        this._onDidChangeTreeData.fire();
    }

    refresh(): void {
        this.scanMarkdownFiles();
        this._onDidChangeTreeData.fire();
    }

    updateFindings(findings: Finding[]): void {
        this.findings = findings;
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: TreeItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: TreeItem): TreeItem[] {
        if (!element) {
            return this.getRootSections();
        }
        
        switch (element.contextValue) {
            case 'violationsSection':
                return this.getViolationGroups();
            case 'severityGroup':
                return element.children || [];
            case 'markdownSection':
                return this.getMarkdownFiles();
            case 'markdownFolder':
                return this.getMarkdownFolderChildren(element);
            case 'aiSection':
                return this.getAIProviders();
            case 'aiProvider':
                return this.getAIProviderDetails(element);
            default:
                return element.children || [];
        }
    }

    private getRootSections(): TreeItem[] {
        const sections: TreeItem[] = [];
        
        // Violations Section
        const violationCount = this.findings.length;
        sections.push({
            label: `Violations (${violationCount})`,
            collapsibleState: violationCount > 0 ? vscode.TreeItemCollapsibleState.Expanded : vscode.TreeItemCollapsibleState.Collapsed,
            contextValue: 'violationsSection',
            iconPath: new vscode.ThemeIcon('warning'),
            description: violationCount > 0 ? `${violationCount} issues found` : 'No issues'
        });
        
        // AI Configuration Section
        const enabledProviders = Array.from(this.aiProviders.values()).filter((p: any) => p.enabled).length;
        const totalProviders = this.aiProviders.size;
        sections.push({
            label: `AI Providers (${enabledProviders}/${totalProviders})`,
            collapsibleState: vscode.TreeItemCollapsibleState.Collapsed,
            contextValue: 'aiSection',
            iconPath: new vscode.ThemeIcon('robot'),
            description: enabledProviders > 0 ? `${enabledProviders} enabled` : 'Configure API keys'
        });
        
        // Markdown Files Section
        const markdownCount = Array.from(this.markdownFiles.values()).reduce((sum, files) => sum + files.length, 0);
        sections.push({
            label: `Documentation (${markdownCount})`,
            collapsibleState: vscode.TreeItemCollapsibleState.Collapsed,
            contextValue: 'markdownSection',
            iconPath: new vscode.ThemeIcon('book'),
            description: markdownCount > 0 ? `${markdownCount} files` : 'No markdown files'
        });
        
        return sections;
    }

    private getViolationGroups(): TreeItem[] {
        const groups = new Map<string, Finding[]>();
        this.findings.forEach(f => {
            const severity = f.severity;
            if (!groups.has(severity)) groups.set(severity, []);
            groups.get(severity)!.push(f);
        });

        const items: TreeItem[] = [];
        for (const [severity, findings] of groups) {
            items.push({
                label: `${severity.toUpperCase()} (${findings.length})`,
                collapsibleState: vscode.TreeItemCollapsibleState.Expanded,
                contextValue: 'severityGroup',
                iconPath: this.getSeverityIcon(severity),
                children: findings.map(f => ({
                    label: f.message,
                    description: `${f.file.split('/').pop()}:${f.line}`,
                    collapsibleState: vscode.TreeItemCollapsibleState.None,
                    contextValue: 'violation',
                    finding: f,
                    command: {
                        command: 'vscode.open',
                        arguments: [vscode.Uri.file(f.file), { selection: new vscode.Range(f.line - 1, 0, f.line - 1, 0) }]
                    }
                }))
            });
        }
        return items;
    }

    private getMarkdownFiles(): TreeItem[] {
        const items: TreeItem[] = [];
        
        // Add root level markdown files first
        const rootFiles = this.markdownFiles.get('.') || [];
        for (const file of rootFiles) {
            const fileName = file.fsPath.split('/').pop() || file.fsPath;
            items.push({
                label: this.formatMarkdownFileName(fileName),
                collapsibleState: vscode.TreeItemCollapsibleState.None,
                contextValue: 'markdownFile',
                iconPath: new vscode.ThemeIcon('markdown'),
                command: {
                    command: 'vscode.open',
                    arguments: [file]
                },
                resourceUri: file
            });
        }
        
        // Add directories
        const directories = new Set<string>();
        for (const [dir] of this.markdownFiles) {
            if (dir !== '.') {
                const topLevel = dir.split('/')[0];
                directories.add(topLevel);
            }
        }
        
        for (const dirName of Array.from(directories).sort()) {
            items.push({
                label: dirName,
                collapsibleState: vscode.TreeItemCollapsibleState.Collapsed,
                contextValue: 'markdownFolder',
                iconPath: vscode.ThemeIcon.Folder,
                resourceUri: vscode.Uri.file(dirName)
            });
        }
        
        return items;
    }

    private getMarkdownFolderChildren(element: TreeItem): TreeItem[] {
        // Implementation for markdown folder children - simplified for now
        return [];
    }

    private getAIProviders(): TreeItem[] {
        const providers: TreeItem[] = [];
        
        this.aiProviders.forEach((provider, id) => {
            const icon = provider.enabled ? '✅' : '⚙️';
            const status = provider.enabled ? 'Enabled' : 'Not Configured';
            const label = `${icon} ${provider.name}`;
            const description = provider.model ? `(${provider.model})` : status;
            
            providers.push({
                label,
                description,
                collapsibleState: vscode.TreeItemCollapsibleState.Collapsed,
                contextValue: 'aiProvider',
                providerId: id,
                iconPath: provider.enabled ? 
                    new vscode.ThemeIcon('check', new vscode.ThemeColor('testing.iconPassed')) :
                    new vscode.ThemeIcon('gear', new vscode.ThemeColor('foreground'))
            });
        });
        
        // Add MCP Server configuration
        providers.push({
            label: '🌐 MCP Server',
            description: this.mcpServerUrl,
            collapsibleState: vscode.TreeItemCollapsibleState.None,
            contextValue: 'mcpConfig',
            iconPath: new vscode.ThemeIcon('server-environment'),
            command: {
                command: 'connascence.configureServer',
                title: 'Configure MCP Server'
            }
        });
        
        return providers;
    }

    private getAIProviderDetails(element: TreeItem): TreeItem[] {
        const providerId = element.providerId;
        if (!providerId) return [];
        
        const provider = this.aiProviders.get(providerId);
        if (!provider) return [];
        
        const details: TreeItem[] = [];
        
        // Model selection
        details.push({
            label: `Model: ${provider.model || 'Not set'}`,
            contextValue: 'providerDetail',
            command: {
                command: 'connascence.changeModel',
                title: 'Change Model',
                arguments: [providerId]
            },
            iconPath: new vscode.ThemeIcon('symbol-method')
        });
        
        // API Key status
        const hasApiKey = !!provider.apiKey;
        details.push({
            label: `API Key: ${hasApiKey ? 'Configured' : 'Not set'}`,
            contextValue: 'providerDetail',
            command: {
                command: 'connascence.setApiKey',
                title: 'Set API Key',
                arguments: [providerId]
            },
            iconPath: new vscode.ThemeIcon(hasApiKey ? 'key' : 'unlock')
        });
        
        // Toggle provider
        details.push({
            label: provider.enabled ? 'Disable Provider' : 'Enable Provider',
            contextValue: 'providerAction',
            command: {
                command: 'connascence.toggleProvider',
                title: provider.enabled ? 'Disable' : 'Enable',
                arguments: [providerId]
            },
            iconPath: new vscode.ThemeIcon(provider.enabled ? 'stop-circle' : 'play-circle')
        });
        
        return details;
    }

    private initializeAIProviders(): void {
        const defaultProviders = [
            { name: 'openai', displayName: 'OpenAI', enabled: false, model: 'gpt-4', hasApiKey: false },
            { name: 'anthropic', displayName: 'Anthropic Claude', enabled: false, model: 'claude-3-sonnet-20240229', hasApiKey: false },
            { name: 'google', displayName: 'Google Gemini', enabled: false, model: 'gemini-pro', hasApiKey: false },
            { name: 'cohere', displayName: 'Cohere', enabled: false, model: 'command', hasApiKey: false },
        ];
        
        for (const provider of defaultProviders) {
            this.aiProviders.set(provider.name, provider);
        }
    }

    private async scanMarkdownFiles(): Promise<void> {
        if (!vscode.workspace.workspaceFolders) return;
        
        try {
            const pattern = new vscode.RelativePattern(vscode.workspace.workspaceFolders[0], '**/*.{md,markdown,mdx}');
            const files = await vscode.workspace.findFiles(pattern, '**/node_modules/**');
            
            this.markdownFiles.clear();
            const directoryMap = new Map<string, vscode.Uri[]>();
            
            for (const file of files) {
                const relativePath = vscode.workspace.asRelativePath(file, false);
                const directory = relativePath.includes('/') ? relativePath.substring(0, relativePath.lastIndexOf('/')) : '.';
                
                if (!directoryMap.has(directory)) {
                    directoryMap.set(directory, []);
                }
                directoryMap.get(directory)!.push(file);
            }
            
            this.markdownFiles = directoryMap;
        } catch (error) {
            this.logger?.error('Failed to scan markdown files', error);
        }
    }

    private setupFileWatcher(): void {
        const watcher = vscode.workspace.createFileSystemWatcher('**/*.{md,markdown,mdx}');
        watcher.onDidCreate(() => this.refresh());
        watcher.onDidDelete(() => this.refresh());
    }

    private formatMarkdownFileName(fileName: string): string {
        const nameWithoutExt = fileName.replace(/\.(md|markdown|mdx)$/i, '');
        
        if (nameWithoutExt.toLowerCase() === 'readme') return '📖 README';
        if (nameWithoutExt.toLowerCase() === 'changelog') return '📝 CHANGELOG';
        if (nameWithoutExt.toLowerCase() === 'license') return '⚖️ LICENSE';
        if (nameWithoutExt.toLowerCase() === 'contributing') return '🤝 CONTRIBUTING';
        
        return nameWithoutExt.replace(/[-_]/g, ' ').replace(/\b\w/g, char => char.toUpperCase());
    }

    private getProviderIcon(name: string): vscode.ThemeIcon {
        const iconMap: { [key: string]: string } = {
            'openai': 'robot',
            'anthropic': 'hubot',
            'google': 'search',
            'cohere': 'comment-discussion'
        };
        return new vscode.ThemeIcon(iconMap[name] || 'circuit-board');
    }

    private getSeverityIcon(severity: string): vscode.ThemeIcon {
        const icons = {
            critical: new vscode.ThemeIcon('error'),
            major: new vscode.ThemeIcon('warning'),
            minor: new vscode.ThemeIcon('info'),
            info: new vscode.ThemeIcon('lightbulb')
        };
        return icons[severity as keyof typeof icons] || icons.info;
    }
}

interface TreeItem extends vscode.TreeItem {
    children?: TreeItem[];
    finding?: Finding;
    provider?: any;
    resourceUri?: vscode.Uri;
}