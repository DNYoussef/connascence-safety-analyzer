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
        
        // AI configuration is now integrated into UIManager tree view
    }

    public activate(): void {
        this.logger.info('Activating Connascence MECE architecture...');
        
        try {
            // Register language providers (reduced set - diagnostics/decorations now handled by VisualProvider)
            this.registerLanguageProviders();
            
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
        } catch (error) {
            this.logger.error('Error disposing MECE components', error);
        }
        
        this.disposables = [];
        this.logger.info('Connascence MECE architecture disposed');
    }
}