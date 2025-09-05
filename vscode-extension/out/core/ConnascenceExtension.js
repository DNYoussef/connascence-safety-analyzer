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
exports.ConnascenceExtension = void 0;
const vscode = __importStar(require("vscode"));
const diagnosticsProvider_1 = require("../providers/diagnosticsProvider");
const codeActionProvider_1 = require("../providers/codeActionProvider");
const completionProvider_1 = require("../providers/completionProvider");
const hoverProvider_1 = require("../providers/hoverProvider");
const codeLensProvider_1 = require("../providers/codeLensProvider");
const treeProvider_1 = require("../providers/treeProvider");
const statusBarManager_1 = require("../ui/statusBarManager");
const outputChannelManager_1 = require("../ui/outputChannelManager");
const configurationService_1 = require("../services/configurationService");
const connascenceService_1 = require("../services/connascenceService");
const commandManager_1 = require("../commands/commandManager");
const fileWatcherService_1 = require("../services/fileWatcherService");
/**
 * Main extension class that orchestrates all Connascence functionality
 */
class ConnascenceExtension {
    constructor(context, logger, telemetry) {
        this.context = context;
        this.logger = logger;
        this.telemetry = telemetry;
        this.disposables = [];
        // Initialize services first
        this.configService = new configurationService_1.ConfigurationService();
        this.connascenceService = new connascenceService_1.ConnascenceService(this.configService, this.telemetry);
        // Initialize UI components
        this.statusBarManager = new statusBarManager_1.StatusBarManager(context);
        this.outputManager = new outputChannelManager_1.OutputChannelManager('Connascence');
        // Initialize providers
        this.diagnosticsProvider = new diagnosticsProvider_1.ConnascenceDiagnosticsProvider(this.connascenceService);
        this.codeActionProvider = new codeActionProvider_1.ConnascenceCodeActionProvider(this.connascenceService);
        this.completionProvider = new completionProvider_1.ConnascenceCompletionProvider(this.connascenceService);
        this.hoverProvider = new hoverProvider_1.ConnascenceHoverProvider(this.connascenceService);
        this.codeLensProvider = new codeLensProvider_1.ConnascenceCodeLensProvider(this.connascenceService);
        this.treeDataProvider = new treeProvider_1.ConnascenceTreeDataProvider(this.connascenceService);
        // Initialize file watcher
        this.fileWatcherService = new fileWatcherService_1.FileWatcherService(this.diagnosticsProvider, this.configService, this.logger);
        // Initialize command manager
        this.commandManager = new commandManager_1.CommandManager(this.connascenceService, this.diagnosticsProvider, this.statusBarManager, this.outputManager, this.treeDataProvider, this.logger);
    }
    activate() {
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
        }
        catch (error) {
            this.logger.error('Failed to activate extension components', error);
            throw error;
        }
    }
    registerLanguageProviders() {
        const supportedLanguages = ['python', 'javascript', 'typescript', 'c', 'cpp'];
        // Register diagnostics provider
        this.context.subscriptions.push(this.diagnosticsProvider);
        // Register code action provider
        for (const language of supportedLanguages) {
            const selector = { language, scheme: 'file' };
            this.disposables.push(vscode.languages.registerCodeActionsProvider(selector, this.codeActionProvider, {
                providedCodeActionKinds: [
                    vscode.CodeActionKind.QuickFix,
                    vscode.CodeActionKind.Refactor,
                    vscode.CodeActionKind.RefactorExtract
                ]
            }));
            // Register completion provider (IntelliSense)
            if (this.configService.get('enableIntelliSense', true)) {
                this.disposables.push(vscode.languages.registerCompletionItemProvider(selector, this.completionProvider, '.' // Trigger on dot
                ));
            }
            // Register hover provider
            if (this.configService.get('enableHover', true)) {
                this.disposables.push(vscode.languages.registerHoverProvider(selector, this.hoverProvider));
            }
            // Register code lens provider
            if (this.configService.get('enableCodeLens', true)) {
                this.disposables.push(vscode.languages.registerCodeLensProvider(selector, this.codeLensProvider));
            }
        }
        this.logger.info(`Registered language providers for: ${supportedLanguages.join(', ')}`);
    }
    registerUIComponents() {
        // Register tree view
        const treeView = vscode.window.createTreeView('connascenceFindings', {
            treeDataProvider: this.treeDataProvider,
            showCollapseAll: true,
            canSelectMany: false
        });
        this.disposables.push(treeView);
        // Update tree view on selection
        this.disposables.push(treeView.onDidChangeSelection((e) => {
            if (e.selection.length > 0) {
                const item = e.selection[0];
                this.telemetry.logEvent('treeView.itemSelected', {
                    type: item.contextValue || 'unknown'
                });
            }
        }));
        // Initialize status bar
        this.statusBarManager.initialize();
        this.logger.info('UI components registered successfully');
    }
    registerCommands() {
        const commands = this.commandManager.getAllCommands();
        for (const [commandId, handler] of commands) {
            this.disposables.push(vscode.commands.registerCommand(commandId, handler));
        }
        this.logger.info(`Registered ${commands.size} commands`);
    }
    setupFileWatching() {
        // Setup file watcher for supported languages
        const patterns = ['**/*.py', '**/*.js', '**/*.ts', '**/*.c', '**/*.cpp'];
        for (const pattern of patterns) {
            const watcher = vscode.workspace.createFileSystemWatcher(pattern);
            this.disposables.push(watcher);
            this.disposables.push(watcher.onDidChange((uri) => this.fileWatcherService.onFileChanged(uri)));
            this.disposables.push(watcher.onDidCreate((uri) => this.fileWatcherService.onFileCreated(uri)));
            this.disposables.push(watcher.onDidDelete((uri) => this.fileWatcherService.onFileDeleted(uri)));
        }
        // Watch for document changes for real-time analysis
        this.disposables.push(vscode.workspace.onDidChangeTextDocument((e) => {
            if (this.configService.get('realTimeAnalysis', true)) {
                this.fileWatcherService.onDocumentChanged(e);
            }
        }));
        this.logger.info('File watching setup completed');
    }
    setupConfigurationHandling() {
        this.disposables.push(vscode.workspace.onDidChangeConfiguration((event) => {
            if (event.affectsConfiguration('connascence')) {
                this.logger.info('Configuration changed, refreshing providers');
                this.telemetry.logEvent('configuration.changed');
                // Refresh all providers with new configuration
                this.refreshProviders();
                // Update UI components
                this.statusBarManager.refresh();
            }
        }));
    }
    refreshProviders() {
        // Clear existing diagnostics if real-time analysis was disabled
        if (!this.configService.get('realTimeAnalysis', true)) {
            this.diagnosticsProvider.clearAllDiagnostics();
        }
        // Refresh analysis for open documents
        const openDocuments = vscode.workspace.textDocuments.filter(doc => this.isSupportedLanguage(doc.languageId));
        for (const document of openDocuments) {
            this.diagnosticsProvider.updateFile(document);
        }
        // Refresh tree view
        this.treeDataProvider.refresh();
    }
    initializeWorkspaceScan() {
        if (!this.configService.get('scanOnStartup', true)) {
            return;
        }
        // Delay initial scan to let VS Code fully initialize
        setTimeout(() => {
            this.logger.info('Performing initial workspace scan...');
            vscode.commands.executeCommand('connascence.analyzeWorkspace');
        }, 2000);
    }
    isSupportedLanguage(languageId) {
        return ['python', 'javascript', 'typescript', 'c', 'cpp'].includes(languageId);
    }
    dispose() {
        this.logger.info('Disposing Connascence extension...');
        // Dispose all registered disposables
        for (const disposable of this.disposables) {
            try {
                disposable.dispose();
            }
            catch (error) {
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
        }
        catch (error) {
            this.logger.error('Error disposing extension components', error);
        }
        this.disposables = [];
        this.logger.info('Connascence extension disposed');
    }
}
exports.ConnascenceExtension = ConnascenceExtension;
//# sourceMappingURL=ConnascenceExtension.js.map