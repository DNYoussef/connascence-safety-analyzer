import * as vscode from 'vscode';
import { ExtensionLogger } from '../utils/logger';
import { TelemetryReporter } from '../utils/telemetry';
import { TelemetryService } from '../services/telemetryService';

/**
 * Adapter to bridge TelemetryReporter and TelemetryService interfaces
 */
class TelemetryServiceAdapter extends TelemetryService {
    constructor(private reporter: TelemetryReporter) {
        super();
    }
    
    logEvent(name: string, properties?: { [key: string]: any }, measurements?: { [key: string]: number }): void {
        super.logEvent(name, properties, measurements);
        this.reporter.logEvent(name, properties);
    }
    
    logError(error: Error, context?: string): void {
        super.logError(error, context);
        this.reporter.logError(error, context);
    }
    
    logPerformance(operation: string, duration: number, success: boolean): void {
        super.logPerformance(operation, duration, success);
        this.reporter.logPerformance(operation, duration, success);
    }
}
import { ConnascenceDiagnosticsProvider } from '../providers/diagnosticsProvider';
import { ConnascenceCodeActionProvider } from '../providers/codeActionProvider';
import { ConnascenceCompletionProvider } from '../providers/completionProvider';
import { ConnascenceHoverProvider } from '../providers/hoverProvider';
import { ConnascenceCodeLensProvider } from '../providers/codeLensProvider';
import { ConnascenceTreeProvider } from '../providers/treeProvider';
import { StatusBarManager } from '../ui/statusBarManager';
import { OutputChannelManager } from '../ui/outputChannelManager';
import { ConfigurationService } from '../services/configurationService';
import { ConnascenceService } from '../services/connascenceService';
import { CommandManager } from '../commands/commandManager';
import { FileWatcherService } from '../services/fileWatcherService';

/**
 * Main extension class that orchestrates all Connascence functionality
 */
export class ConnascenceExtension {
    private disposables: vscode.Disposable[] = [];
    
    // Core services
    private configService: ConfigurationService;
    private connascenceService: ConnascenceService;
    private fileWatcherService: FileWatcherService;
    
    // UI components
    private statusBarManager: StatusBarManager;
    private outputManager: OutputChannelManager;
    
    // Language providers
    private diagnosticsProvider: ConnascenceDiagnosticsProvider;
    private codeActionProvider: ConnascenceCodeActionProvider;
    private completionProvider: ConnascenceCompletionProvider;
    private hoverProvider: ConnascenceHoverProvider;
    private codeLensProvider: ConnascenceCodeLensProvider;
    private treeDataProvider: ConnascenceTreeProvider;
    
    // Command management
    private commandManager: CommandManager;

    constructor(
        private context: vscode.ExtensionContext,
        private logger: ExtensionLogger,
        private telemetry: TelemetryReporter
    ) {
        // Initialize services first
        this.configService = new ConfigurationService();
        // TelemetryService adapter will be created in the constructor
        this.connascenceService = new ConnascenceService(this.configService, new TelemetryServiceAdapter(this.telemetry));
        
        // Initialize UI components
        this.statusBarManager = new StatusBarManager(this.connascenceService, this.configService);
        this.outputManager = new OutputChannelManager('Connascence');
        
        // Initialize providers
        this.diagnosticsProvider = new ConnascenceDiagnosticsProvider(this.connascenceService);
        this.codeActionProvider = new ConnascenceCodeActionProvider(this.connascenceService);
        this.completionProvider = new ConnascenceCompletionProvider(this.connascenceService);
        this.hoverProvider = new ConnascenceHoverProvider(this.connascenceService);
        this.codeLensProvider = new ConnascenceCodeLensProvider(this.connascenceService);
        this.treeDataProvider = new ConnascenceTreeProvider(this.connascenceService);
        
        // Initialize file watcher
        this.fileWatcherService = new FileWatcherService(
            this.diagnosticsProvider,
            this.configService,
            this.logger
        );
        
        // Initialize command manager
        this.commandManager = new CommandManager(
            this.connascenceService,
            this.diagnosticsProvider,
            this.statusBarManager,
            this.outputManager,
            this.treeDataProvider,
            this.logger,
            this.configService,
            this.context
        );
    }

    public activate(): void {
        this.logger.info('Activating Connascence extension components...');
        
        try {
            // Register language providers
            this.registerLanguageProviders();
            
            // Register UI components
            this.registerUIComponents();
            
            // Register commands
            this.registerCommands();
            
            // Setup file watching
            this.setupFileWatching();
            
            // Setup configuration handling
            this.setupConfigurationHandling();
            
            // Initialize workspace scan if enabled
            this.initializeWorkspaceScan();
            
            this.logger.info('All Connascence extension components activated successfully');
            
        } catch (error) {
            this.logger.error('Failed to activate extension components', error);
            throw error;
        }
    }

    private registerLanguageProviders(): void {
        const supportedLanguages = ['python', 'javascript', 'typescript', 'c', 'cpp'];
        
        // Register diagnostics provider
        this.context.subscriptions.push(this.diagnosticsProvider);
        
        // Register code action provider
        for (const language of supportedLanguages) {
            const selector = { language, scheme: 'file' };
            
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
            
            // Register completion provider (IntelliSense)
            if (this.configService.get('enableIntelliSense', true)) {
                this.disposables.push(
                    vscode.languages.registerCompletionItemProvider(
                        selector,
                        this.completionProvider,
                        '.' // Trigger on dot
                    )
                );
            }
            
            // Register hover provider
            if (this.configService.get('enableHover', true)) {
                this.disposables.push(
                    vscode.languages.registerHoverProvider(selector, this.hoverProvider)
                );
            }
            
            // Register code lens provider
            if (this.configService.get('enableCodeLens', true)) {
                this.disposables.push(
                    vscode.languages.registerCodeLensProvider(selector, this.codeLensProvider)
                );
            }
        }
        
        this.logger.info(`Registered language providers for: ${supportedLanguages.join(', ')}`);
    }

    private registerUIComponents(): void {
        // Register tree view
        const treeView = vscode.window.createTreeView('connascenceFindings', {
            treeDataProvider: this.treeDataProvider,
            showCollapseAll: true,
            canSelectMany: false
        });
        
        this.disposables.push(treeView);
        
        // Update tree view on selection
        this.disposables.push(
            treeView.onDidChangeSelection((e) => {
                if (e.selection.length > 0) {
                    const item = e.selection[0];
                    this.telemetry.logEvent('treeView.itemSelected', { 
                        type: item.contextValue || 'unknown' 
                    });
                }
            })
        );
        
        // Initialize status bar
        this.statusBarManager.initialize();
        
        this.logger.info('UI components registered successfully');
    }

    private registerCommands(): void {
        const commands = this.commandManager.getAllCommands();
        
        for (const [commandId, handler] of commands) {
            this.disposables.push(
                vscode.commands.registerCommand(commandId, handler)
            );
        }
        
        this.logger.info(`Registered ${commands.size} commands`);
    }

    private setupFileWatching(): void {
        // Setup file watcher for supported languages
        const patterns = ['**/*.py', '**/*.js', '**/*.ts', '**/*.c', '**/*.cpp'];
        
        for (const pattern of patterns) {
            const watcher = vscode.workspace.createFileSystemWatcher(pattern);
            
            this.disposables.push(watcher);
            this.disposables.push(
                watcher.onDidChange((uri) => this.fileWatcherService.onFileChanged(uri))
            );
            this.disposables.push(
                watcher.onDidCreate((uri) => this.fileWatcherService.onFileCreated(uri))
            );
            this.disposables.push(
                watcher.onDidDelete((uri) => this.fileWatcherService.onFileDeleted(uri))
            );
        }
        
        // Watch for document changes for real-time analysis
        this.disposables.push(
            vscode.workspace.onDidChangeTextDocument((e) => {
                if (this.configService.get('realTimeAnalysis', true)) {
                    this.fileWatcherService.onDocumentChanged(e);
                }
            })
        );
        
        this.logger.info('File watching setup completed');
    }

    private setupConfigurationHandling(): void {
        this.disposables.push(
            vscode.workspace.onDidChangeConfiguration((event) => {
                if (event.affectsConfiguration('connascence')) {
                    this.logger.info('Configuration changed, refreshing providers');
                    this.telemetry.logEvent('configuration.changed');
                    
                    // Refresh all providers with new configuration
                    this.refreshProviders();
                    
                    // Update UI components
                    this.statusBarManager.refresh();
                }
            })
        );
    }

    private refreshProviders(): void {
        // Clear existing diagnostics if real-time analysis was disabled
        if (!this.configService.get('realTimeAnalysis', true)) {
            this.diagnosticsProvider.clearAllDiagnostics();
        }
        
        // Refresh analysis for open documents
        const openDocuments = vscode.workspace.textDocuments.filter(doc => 
            this.isSupportedLanguage(doc.languageId)
        );
        
        for (const document of openDocuments) {
            this.diagnosticsProvider.updateFile(document);
        }
        
        // Refresh tree view
        this.treeDataProvider.refresh();
    }

    private initializeWorkspaceScan(): void {
        if (!this.configService.get('scanOnStartup', true)) {
            return;
        }
        
        // Delay initial scan to let VS Code fully initialize
        setTimeout(() => {
            this.logger.info('Performing initial workspace scan...');
            vscode.commands.executeCommand('connascence.analyzeWorkspace');
        }, 2000);
    }

    private isSupportedLanguage(languageId: string): boolean {
        return ['python', 'javascript', 'typescript', 'c', 'cpp'].includes(languageId);
    }

    public dispose(): void {
        this.logger.info('Disposing Connascence extension...');
        
        // Dispose all registered disposables
        for (const disposable of this.disposables) {
            try {
                disposable.dispose();
            } catch (error) {
                this.logger.error('Error disposing resource', error);
            }
        }
        
        // Dispose individual components
        try {
            this.diagnosticsProvider?.dispose();
            this.statusBarManager?.dispose();
            this.outputManager?.dispose();
            this.fileWatcherService?.dispose();
            this.commandManager?.dispose();
        } catch (error) {
            this.logger.error('Error disposing extension components', error);
        }
        
        this.disposables = [];
        this.logger.info('Connascence extension disposed');
    }
}