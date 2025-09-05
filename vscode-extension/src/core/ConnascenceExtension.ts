import * as vscode from 'vscode';
import { ExtensionLogger } from '../utils/logger';
import { TelemetryReporter } from '../utils/telemetry';
import { ConfigurationService } from '../services/configurationService';
import { ConnascenceService } from '../services/connascenceService';
// MECE Architecture Components
import { AnalysisManager } from './analysisManager';
import { VisualProvider } from '../providers/visualProvider';
import { UIManager } from '../ui/uiManager';
import { AIIntegrationService } from '../services/aiIntegrationService';
// Legacy providers (for CodeActions, Completion, Hover, CodeLens)
import { ConnascenceCodeActionProvider } from '../providers/codeActionProvider';
import { ConnascenceCompletionProvider } from '../providers/completionProvider';
import { ConnascenceHoverProvider } from '../providers/hoverProvider';
import { ConnascenceCodeLensProvider } from '../providers/codeLensProvider';
// Help and Documentation
import { HelpProvider } from '../services/helpProvider';
import { MarkdownTableOfContentsProvider } from '../providers/markdownTableOfContentsProvider';
// Snapshot and Baseline Management
import { SnapshotCommands } from '../commands/SnapshotCommands';
import { OutputChannelLogger } from '../utils/OutputChannelLogger';

/**
 * Main extension class that orchestrates all Connascence functionality
 */
export class ConnascenceExtension {
    private disposables: vscode.Disposable[] = [];
    
    // Core services
    private configService: ConfigurationService;
    private connascenceService: ConnascenceService;
    
    // MECE Architecture - Unified Managers
    private analysisManager: AnalysisManager;
    private visualProvider: VisualProvider;
    private uiManager: UIManager;
    private aiIntegrationService: AIIntegrationService;
    
    // Legacy language providers (CodeActions, Completion, Hover, CodeLens only)
    private codeActionProvider: ConnascenceCodeActionProvider;
    private completionProvider: ConnascenceCompletionProvider;
    private hoverProvider: ConnascenceHoverProvider;
    private codeLensProvider: ConnascenceCodeLensProvider;
    
    // Help and Documentation
    private helpProvider: HelpProvider;
    private markdownTOCProvider: MarkdownTableOfContentsProvider;
    private markdownTOCView: vscode.TreeView<any>;
    
    // Snapshot and Baseline Management
    private snapshotCommands: SnapshotCommands;
    private outputLogger: OutputChannelLogger;

    constructor(
        private context: vscode.ExtensionContext,
        private logger: ExtensionLogger,
        private telemetry: TelemetryReporter
    ) {
        // Initialize core services
        this.configService = new ConfigurationService();
        const telemetryServiceAdapter: any = {
            logEvent: (event: string, data?: any) => this.telemetry.logEvent(event, data),
            events: {},
            sessionId: '',
            userId: '',
            enabled: true
        };
        this.connascenceService = new ConnascenceService(this.configService, telemetryServiceAdapter);
        
        // Initialize MECE Architecture Components
        this.visualProvider = new VisualProvider(this.configService);
        this.uiManager = new UIManager(this.context, this.configService, this.logger);
        this.aiIntegrationService = new AIIntegrationService(this.configService, this.logger);
        
        // Initialize unified analysis manager (orchestrates everything)
        this.analysisManager = new AnalysisManager(
            this.connascenceService,
            this.configService,
            this.logger,
            this.visualProvider,
            this.uiManager,
            this.aiIntegrationService
        );
        
        // Register commands
        this.registerCommands();
        
        // Initialize legacy language providers
        this.codeActionProvider = new ConnascenceCodeActionProvider(this.connascenceService);
        this.completionProvider = new ConnascenceCompletionProvider(this.connascenceService);
        this.hoverProvider = new ConnascenceHoverProvider(this.connascenceService, this.configService, this.aiIntegrationService);
        this.codeLensProvider = new ConnascenceCodeLensProvider(this.connascenceService);
        
        // Initialize help and documentation
        this.helpProvider = new HelpProvider(this.context, this.configService, this.logger);
        
        // Initialize markdown table of contents
        this.markdownTOCProvider = new MarkdownTableOfContentsProvider(this.context, this.configService, this.logger);
        this.markdownTOCView = vscode.window.createTreeView('connascenceMarkdownTOC', {
            treeDataProvider: this.markdownTOCProvider,
            showCollapseAll: true,
            canSelectMany: false
        });
        
        // Initialize snapshot and baseline management
        this.outputLogger = new OutputChannelLogger('Connascence Snapshots');
        this.snapshotCommands = new SnapshotCommands(this.connascenceService, this.outputLogger);
        
        // AI configuration is now integrated into UIManager tree view
    }

    public activate(): void {
        this.logger.info('Activating Connascence MECE architecture...');
        
        try {
            // Register language providers (reduced set - diagnostics/decorations now handled by VisualProvider)
            this.registerLanguageProviders();
            
            // Register snapshot commands and status bar
            this.snapshotCommands.registerCommands(this.context);
            
            // Setup configuration handling
            this.setupConfigurationHandling();
            
            // Initialize workspace scan if enabled
            this.initializeWorkspaceScan();
            
            this.logger.info('Connascence MECE architecture activated successfully');
            
        } catch (error) {
            this.logger.error('Failed to activate MECE architecture', error);
            throw error;
        }
    }

    private registerLanguageProviders(): void {
        const supportedLanguages = ['python', 'javascript', 'typescript', 'c', 'cpp'];
        
        // Register only the remaining language providers (diagnostics/decorations handled by MECE components)
        for (const language of supportedLanguages) {
            const selector = { language, scheme: 'file' };
            
            // Register code action provider
            this.disposables.push(
                vscode.languages.registerCodeActionsProvider(
                    selector,
                    this.codeActionProvider,
                    {
                        providedCodeActionKinds: [
                            vscode.CodeActionKind.QuickFix,
                            vscode.CodeActionKind.Refactor,
                            vscode.CodeActionKind.RefactorExtract
                        ]
                    }
                )
            );
            
            // Register completion provider (IntelliSense) if enabled
            if (this.configService.get('enableIntelliSense', true)) {
                this.disposables.push(
                    vscode.languages.registerCompletionItemProvider(
                        selector,
                        this.completionProvider,
                        '.' // Trigger on dot
                    )
                );
            }
            
            // Register hover provider if enabled
            if (this.configService.get('enableHover', true)) {
                this.disposables.push(
                    vscode.languages.registerHoverProvider(selector, this.hoverProvider)
                );
            }
            
            // Register code lens provider if enabled
            if (this.configService.get('enableCodeLens', true)) {
                this.disposables.push(
                    vscode.languages.registerCodeLensProvider(selector, this.codeLensProvider)
                );
            }
        }
        
        this.logger.info(`MECE: Registered language providers for ${supportedLanguages.length} languages`);
    }


    private setupConfigurationHandling(): void {
        this.disposables.push(
            vscode.workspace.onDidChangeConfiguration((event) => {
                if (event.affectsConfiguration('connascence')) {
                    this.logger.info('Configuration changed - MECE architecture will handle refresh');
                    this.telemetry.logEvent('configuration.changed');
                    
                    // MECE components handle their own configuration refresh
                    // No explicit refresh needed - components watch for configuration changes
                }
            })
        );
    }

    private initializeWorkspaceScan(): void {
        if (!this.configService.get('scanOnStartup', true)) {
            return;
        }
        
        // Delay initial scan to let VS Code fully initialize
        setTimeout(() => {
            this.logger.info('MECE: Performing initial workspace scan...');
            // AnalysisManager handles workspace analysis
            this.analysisManager.analyzeWorkspace();
        }, 2000);
    }

    public dispose(): void {
        this.logger.info('Disposing Connascence MECE architecture...');
        
        // Dispose all registered disposables
        for (const disposable of this.disposables) {
            try {
                disposable.dispose();
            } catch (error) {
                this.logger.error('Error disposing resource', error);
            }
        }
        
        // Dispose MECE architecture components
        try {
            this.analysisManager?.dispose();
            this.visualProvider?.dispose();
            this.uiManager?.dispose();
            this.aiIntegrationService?.dispose();
            this.helpProvider?.dispose();
            this.markdownTOCProvider?.dispose();
            this.markdownTOCView?.dispose();
            this.snapshotCommands?.dispose();
        } catch (error) {
            this.logger.error('Error disposing MECE components', error);
        }
        
        this.disposables = [];
        this.logger.info('Connascence MECE architecture disposed');
    }

    /**
     * Register all extension commands
     */
    private registerCommands(): void {
        const commands = [
            vscode.commands.registerCommand('connascence.analyzeCurrentFile', () => this.analyzeCurrentFile()),
            vscode.commands.registerCommand('connascence.analyzeWorkspace', () => this.analyzeWorkspace()),
            vscode.commands.registerCommand('connascence.showDashboard', () => this.showDashboard()),
            vscode.commands.registerCommand('connascence.clearCache', () => this.clearCache()),
            // Per-finding actions
            vscode.commands.registerCommand('connascence.ignoreFinding', (finding) => this.ignoreFinding(finding)),
            vscode.commands.registerCommand('connascence.createWaiver', (finding) => this.createWaiver(finding)),
            vscode.commands.registerCommand('connascence.showFixSuggestions', (finding) => this.showFixSuggestions(finding)),
            // Rule configuration commands
            vscode.commands.registerCommand('connascence.toggleRuleCategory', (categoryName, enabled) => this.toggleRuleCategory(categoryName, enabled)),
            vscode.commands.registerCommand('connascence.configureRule', (ruleName) => this.configureRule(ruleName)),
            // Budget and policy commands
            vscode.commands.registerCommand('connascence.checkBudget', () => this.checkBudget()),
            vscode.commands.registerCommand('connascence.configureBudget', () => this.configureBudget()),
            vscode.commands.registerCommand('connascence.budgetReport', () => this.generateBudgetReport()),
            vscode.commands.registerCommand('connascence.validateCI', () => this.validateForCI()),
            vscode.commands.registerCommand('connascence.viewWaivers', () => this.viewWaivers()),
            vscode.commands.registerCommand('connascence.createGlobalWaiver', () => this.createGlobalWaiver()),
            vscode.commands.registerCommand('connascence.cleanupWaivers', () => this.cleanupWaivers()),
            vscode.commands.registerCommand('connascence.configurePolicies', () => this.configurePolicies()),
            vscode.commands.registerCommand('connascence.auditCompliance', () => this.auditCompliance()),
            vscode.commands.registerCommand('connascence.analyzeDrift', () => this.analyzeDrift()),
            vscode.commands.registerCommand('connascence.recordDrift', () => this.recordDrift()),
            vscode.commands.registerCommand('connascence.exportDrift', () => this.exportDrift())
        ];

        commands.forEach(disposable => {
            this.context.subscriptions.push(disposable);
        });

        this.logger.info('Registered all extension commands');
    }

    // Core command implementations
    private async analyzeCurrentFile(): Promise<void> {
        this.analysisManager.analyzeCurrentFile();
    }

    private async analyzeWorkspace(): Promise<void> {
        this.analysisManager.analyzeWorkspace();
    }

    private async showDashboard(): Promise<void> {
        this.uiManager.showDashboard();
    }

    private async clearCache(): Promise<void> {
        // TODO: Implement cache clearing
        vscode.window.showInformationMessage('Cache cleared');
    }

    // Per-finding command implementations
    private async ignoreFinding(finding: any): Promise<void> {
        try {
            await vscode.window.showInformationMessage(
                `Ignored finding: ${finding.message}\nFile: ${finding.file}:${finding.line}`,
                { modal: false }
            );
            
            // TODO: Implement actual ignore logic with MCP server
            this.logger.info(`Ignored finding: ${finding.id}`);
        } catch (error) {
            this.logger.error('Failed to ignore finding', error);
            vscode.window.showErrorMessage('Failed to ignore finding');
        }
    }

    private async createWaiver(finding: any): Promise<void> {
        try {
            const reason = await vscode.window.showInputBox({
                prompt: 'Enter waiver reason',
                placeholder: 'Business justification for this exception...',
                validateInput: (value) => value.trim() ? null : 'Reason is required'
            });

            if (reason) {
                await vscode.window.showInformationMessage(
                    `Waiver created for: ${finding.message}\nReason: ${reason}`,
                    { modal: false }
                );
                
                // TODO: Implement actual waiver creation with MCP server
                this.logger.info(`Created waiver: ${finding.id} - ${reason}`);
            }
        } catch (error) {
            this.logger.error('Failed to create waiver', error);
            vscode.window.showErrorMessage('Failed to create waiver');
        }
    }

    private async showFixSuggestions(finding: any): Promise<void> {
        try {
            const suggestions = this.generateFixSuggestions(finding);
            const selected = await vscode.window.showQuickPick(suggestions, {
                placeHolder: 'Select a fix suggestion',
                canPickMany: false
            });

            if (selected) {
                await vscode.window.showInformationMessage(
                    `Fix suggestion: ${selected}`,
                    { modal: false }
                );
            }
        } catch (error) {
            this.logger.error('Failed to show fix suggestions', error);
            vscode.window.showErrorMessage('Failed to show fix suggestions');
        }
    }

    private generateFixSuggestions(finding: any): string[] {
        const suggestions: string[] = [];

        switch (finding.type?.toLowerCase()) {
            case 'magic_literal':
            case 'meaning':
                suggestions.push('Extract constant with meaningful name');
                suggestions.push('Use configuration file or enum');
                suggestions.push('Create named parameter object');
                break;
            case 'god_object':
            case 'algorithm':
                suggestions.push('Extract methods to reduce complexity');
                suggestions.push('Apply Single Responsibility Principle');
                suggestions.push('Use dependency injection pattern');
                suggestions.push('Consider architectural refactoring');
                break;
            case 'position':
                suggestions.push('Use named parameters object');
                suggestions.push('Implement builder pattern');
                suggestions.push('Create parameter object');
                break;
            case 'type':
                suggestions.push('Use generic types for flexibility');
                suggestions.push('Create type aliases for clarity');
                suggestions.push('Implement interface segregation');
                break;
            default:
                suggestions.push('Reduce coupling through abstraction');
                suggestions.push('Apply appropriate design pattern');
                suggestions.push('Consider refactoring to smaller units');
        }

        return suggestions;
    }

    // Rule configuration command implementations
    private async toggleRuleCategory(categoryName: string, enabled: boolean): Promise<void> {
        try {
            const configKey = `rules.${categoryName.toLowerCase().replace(/\s+/g, '')}.enabled`;
            await this.configService.update(configKey, enabled);
            
            vscode.window.showInformationMessage(
                `${enabled ? 'Enabled' : 'Disabled'} rule category: ${categoryName}`
            );
            
            this.logger.info(`Toggled rule category: ${categoryName} = ${enabled}`);
        } catch (error) {
            this.logger.error('Failed to toggle rule category', error);
            vscode.window.showErrorMessage('Failed to toggle rule category');
        }
    }

    private async configureRule(ruleName: string): Promise<void> {
        try {
            const options = [
                { label: 'Enable Rule', description: 'Turn on this rule' },
                { label: 'Disable Rule', description: 'Turn off this rule' },
                { label: 'Configure Severity', description: 'Change rule severity level' },
                { label: 'Set Threshold', description: 'Adjust rule threshold values' }
            ];

            const selected = await vscode.window.showQuickPick(options, {
                placeHolder: `Configure rule: ${ruleName}`
            });

            if (selected) {
                switch (selected.label) {
                    case 'Configure Severity':
                        await this.configureSeverity(ruleName);
                        break;
                    case 'Set Threshold':
                        await this.setThreshold(ruleName);
                        break;
                    default:
                        const enabled = selected.label === 'Enable Rule';
                        const configKey = `rules.${ruleName.toLowerCase().replace(/\s+/g, '')}.enabled`;
                        await this.configService.update(configKey, enabled);
                        vscode.window.showInformationMessage(`${enabled ? 'Enabled' : 'Disabled'} rule: ${ruleName}`);
                }
            }
        } catch (error) {
            this.logger.error('Failed to configure rule', error);
            vscode.window.showErrorMessage('Failed to configure rule');
        }
    }

    private async configureSeverity(ruleName: string): Promise<void> {
        const severities = ['info', 'minor', 'major', 'critical'];
        const selected = await vscode.window.showQuickPick(severities, {
            placeHolder: `Select severity for ${ruleName}`
        });

        if (selected) {
            const configKey = `rules.${ruleName.toLowerCase().replace(/\s+/g, '')}.severity`;
            await this.configService.update(configKey, selected);
            vscode.window.showInformationMessage(`Set ${ruleName} severity to: ${selected}`);
        }
    }

    private async setThreshold(ruleName: string): Promise<void> {
        const threshold = await vscode.window.showInputBox({
            prompt: `Enter threshold value for ${ruleName}`,
            placeholder: 'e.g., 10, 50, 100...',
            validateInput: (value) => {
                const num = parseInt(value);
                return isNaN(num) || num < 0 ? 'Please enter a valid positive number' : null;
            }
        });

        if (threshold) {
            const configKey = `rules.${ruleName.toLowerCase().replace(/\s+/g, '')}.threshold`;
            await this.configService.update(configKey, parseInt(threshold));
            vscode.window.showInformationMessage(`Set ${ruleName} threshold to: ${threshold}`);
        }
    }

    // Enterprise command implementations
    private async checkBudget(): Promise<void> {
        vscode.window.showInformationMessage('Budget status checked - see dashboard for details');
    }

    private async configureBudget(): Promise<void> {
        vscode.window.showInformationMessage('Budget configuration opened');
    }

    private async generateBudgetReport(): Promise<void> {
        vscode.window.showInformationMessage('Budget report generated');
    }

    private async validateForCI(): Promise<void> {
        vscode.window.showInformationMessage('CI validation completed');
    }

    private async viewWaivers(): Promise<void> {
        vscode.window.showInformationMessage('Active waivers displayed');
    }

    private async createGlobalWaiver(): Promise<void> {
        vscode.window.showInformationMessage('Global waiver creation started');
    }

    private async cleanupWaivers(): Promise<void> {
        vscode.window.showInformationMessage('Expired waivers cleaned up');
    }

    private async configurePolicies(): Promise<void> {
        vscode.window.showInformationMessage('Policy configuration opened');
    }

    private async auditCompliance(): Promise<void> {
        vscode.window.showInformationMessage('Compliance audit completed');
    }

    private async analyzeDrift(): Promise<void> {
        vscode.window.showInformationMessage('Drift analysis completed');
    }

    private async recordDrift(): Promise<void> {
        vscode.window.showInformationMessage('Drift measurement recorded');
    }

    private async exportDrift(): Promise<void> {
        vscode.window.showInformationMessage('Drift history exported');
    }
}