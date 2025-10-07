/**
 * VS Code Extension for Connascence Analysis
 * 
 * Provides real-time diagnostics, quick fixes, and dashboard integration
 * for connascence analysis in Python codebases.
 */

import * as vscode from 'vscode';
import { ConnascenceExtension } from './core/ConnascenceExtension';
import { ExtensionLogger } from './utils/logger';
import { TelemetryReporter } from './utils/telemetry';
import { ConnascenceDashboardProvider } from './providers/dashboardProvider';
import { AnalysisResultsProvider } from './providers/analysisResultsProvider';
import { VisualHighlightingManager } from './features/visualHighlighting';
import { NotificationManager } from './features/notificationManager';
import { BrokenChainLogoManager } from './features/brokenChainLogo';
import { AIFixSuggestionsProvider } from './features/aiFixSuggestions';
import { WelcomeScreen } from './features/welcomeScreen';
import { ConnascenceService } from './services/connascenceService';
import { ConfigurationService } from './services/configurationService';
import { EnhancedPipelineProvider } from './providers/enhancedPipelineProvider';

let extension: ConnascenceExtension;
let logger: ExtensionLogger;
let telemetry: TelemetryReporter;

// Global managers for all features
let dashboardProvider: ConnascenceDashboardProvider;
let analysisResultsProvider: AnalysisResultsProvider;
let visualHighlighting: VisualHighlightingManager;
let notificationManager: NotificationManager;
let brokenChainLogo: BrokenChainLogoManager;
let aiFixSuggestions: AIFixSuggestionsProvider;
let connascenceService: ConnascenceService;
let enhancedPipelineProvider: EnhancedPipelineProvider;

export function activate(context: vscode.ExtensionContext) {
    // Initialize logger and telemetry
    logger = new ExtensionLogger('Connascence');
    telemetry = new TelemetryReporter(context, logger);
    
    logger.info('🔗💔 Connascence Analyzer extension activating - Breaking chains!');
    telemetry.logEvent('extension.activate.start');

    try {
        // Initialize core services
        // These will be initialized after extension is created
        connascenceService = null as any;
        extension = new ConnascenceExtension(context, logger, telemetry);
        
        // Initialize all feature managers
        initializeFeatureManagers(context);
        
        // Initialize tree data providers
        initializeTreeProviders(context);
        
        // Register all commands
        registerAllCommands(context);
        
        // Activate main extension
        extension.activate();
        
        // Start background analysis after activation
        startBackgroundServices(context);
        
        telemetry.logEvent('extension.activate.success');
        logger.info('🔗✨ Connascence Analyzer extension activated successfully - Ready to break chains!');

        // Show welcome screen on first activation
        WelcomeScreen.showOnFirstActivation(context);

        // Show welcome message (delayed to avoid interrupting startup)
        setTimeout(() => showWelcomeMessage(), 2000);
        
    } catch (error) {
        logger.error('Failed to activate extension', error);
        telemetry.logEvent('extension.activate.error', {
            error: error instanceof Error ? error.message : String(error)
        });
        throw error;
    }
}

function initializeFeatureManagers(context: vscode.ExtensionContext) {
    logger.info('🔧 Initializing feature managers...');
    
    // Initialize enhanced pipeline provider first
    enhancedPipelineProvider = EnhancedPipelineProvider.getInstance();
    context.subscriptions.push(enhancedPipelineProvider);
    
    // Initialize visual highlighting
    visualHighlighting = new VisualHighlightingManager();
    context.subscriptions.push(visualHighlighting as any);
    
    // Initialize notification manager
    notificationManager = NotificationManager.getInstance();
    
    // Initialize broken chain logo
    brokenChainLogo = BrokenChainLogoManager.getInstance();
    context.subscriptions.push(brokenChainLogo as any);
    
    // Initialize AI fix suggestions
    aiFixSuggestions = AIFixSuggestionsProvider.getInstance();
    
    logger.info('✅ Feature managers initialized with enhanced pipeline support');
}

function initializeTreeProviders(context: vscode.ExtensionContext) {
    logger.info('🌳 Initializing tree data providers...');
    
    // Initialize dashboard provider
    dashboardProvider = new ConnascenceDashboardProvider(connascenceService);
    vscode.window.registerTreeDataProvider('connascenceDashboard', dashboardProvider);
    
    // Initialize analysis results provider
    analysisResultsProvider = new AnalysisResultsProvider();
    vscode.window.registerTreeDataProvider('connascenceAnalysisResults', analysisResultsProvider);
    
    logger.info('✅ Tree data providers registered');
}

function registerAllCommands(context: vscode.ExtensionContext) {
    logger.info('📋 Registering commands...');
    
    // Notification management commands
    const notificationControlsCommand = vscode.commands.registerCommand('connascence.manageNotifications', () => {
        notificationManager.showFilterManagementQuickPick();
    });
    
    // Broken chain logo commands
    const showLogoCommand = vscode.commands.registerCommand('connascence.showBrokenChainAnimation', () => {
        brokenChainLogo.showBrokenChainAnimation();
    });

    // Welcome screen command
    const showWelcomeCommand = vscode.commands.registerCommand('connascence.showWelcome', () => {
        const welcome = new WelcomeScreen(context);
        welcome.show();
    });

    // Dashboard refresh command
    const refreshDashboardCommand = vscode.commands.registerCommand('connascence.refreshDashboard', () => {
        dashboardProvider.refresh();
        analysisResultsProvider.refresh();
    });
    
    // Analysis results grouping commands
    const groupByFileCommand = vscode.commands.registerCommand('connascence.groupByFile', () => {
        analysisResultsProvider.setGroupBy('file');
    });
    
    const groupBySeverityCommand = vscode.commands.registerCommand('connascence.groupBySeverity', () => {
        analysisResultsProvider.setGroupBy('severity');
    });
    
    const groupByTypeCommand = vscode.commands.registerCommand('connascence.groupByType', () => {
        analysisResultsProvider.setGroupBy('type');
    });
    
    // Enhanced analysis commands
    const enhancedAnalysisCommand = vscode.commands.registerCommand('connascence.runEnhancedAnalysis', async () => {
        const activeEditor = vscode.window.activeTextEditor;
        if (!activeEditor) {
            vscode.window.showErrorMessage('No active file to analyze');
            return;
        }
        
        try {
            const result = await enhancedPipelineProvider.runEnhancedAnalysis(activeEditor.document.uri);
            if (result) {
                await enhancedPipelineProvider.showEnhancedAnalysisResults(result);
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Enhanced analysis failed: ${error}`);
        }
    });

    const showCorrelationsCommand = vscode.commands.registerCommand('connascence.showCorrelations', async () => {
        const activeEditor = vscode.window.activeTextEditor;
        if (!activeEditor) {
            vscode.window.showErrorMessage('No active file to analyze');
            return;
        }
        
        const result = await enhancedPipelineProvider.runEnhancedAnalysis(activeEditor.document.uri);
        if (result?.correlations?.length) {
            await enhancedPipelineProvider.showEnhancedAnalysisResults(result);
        } else {
            vscode.window.showInformationMessage('No cross-phase correlations found');
        }
    });

    // Highlighting commands
    const toggleHighlightingCommand = vscode.commands.registerCommand('connascence.toggleHighlighting', () => {
        const config = vscode.workspace.getConfiguration('connascence');
        const currentValue = config.get<boolean>('enableVisualHighlighting', true);
        config.update('enableVisualHighlighting', !currentValue, vscode.ConfigurationTarget.Workspace);
        vscode.window.showInformationMessage(`🔗 Visual highlighting ${!currentValue ? 'enabled' : 'disabled'}`);
    });
    
    const refreshHighlightingCommand = vscode.commands.registerCommand('connascence.refreshHighlighting', () => {
        // Refresh highlighting for all visible editors
        for (const editor of vscode.window.visibleTextEditors) {
            // This would be called by the diagnostics provider
            vscode.commands.executeCommand('connascence.analyzeFile', editor.document.uri);
        }
    });
    
    // Add all commands to context subscriptions
    context.subscriptions.push(
        enhancedAnalysisCommand,
        showCorrelationsCommand,
        notificationControlsCommand,
        showLogoCommand,
        showWelcomeCommand,
        refreshDashboardCommand,
        groupByFileCommand,
        groupBySeverityCommand,
        groupByTypeCommand,
        toggleHighlightingCommand,
        refreshHighlightingCommand
    );
    
    logger.info('✅ Commands registered');
}

function startBackgroundServices(context: vscode.ExtensionContext) {
    logger.info('🚀 Starting background services for immediate loading...');
    
    // Initialize workspace analysis if files are already open
    const activeEditor = vscode.window.activeTextEditor;
    if (activeEditor && isSupportedLanguage(activeEditor.document.languageId)) {
        logger.info('📄 Active editor detected, starting immediate analysis');
        setTimeout(() => {
            vscode.commands.executeCommand('connascence.analyzeFile', activeEditor.document.uri);
        }, 500);
    }
    
    // Start workspace scanning for supported files
    startWorkspaceScanning();
    
    // Register event handlers for immediate file processing
    const documentOpenHandler = vscode.workspace.onDidOpenTextDocument((document) => {
        if (isSupportedLanguage(document.languageId)) {
            logger.info(`📂 Opened ${document.languageId} file, triggering analysis`);
            setTimeout(() => {
                vscode.commands.executeCommand('connascence.analyzeFile', document.uri);
            }, 100);
        }
    });
    
    const documentChangeHandler = vscode.workspace.onDidChangeTextDocument((event) => {
        const config = vscode.workspace.getConfiguration('connascence');
        if (config.get<boolean>('realTimeAnalysis', true) && 
            isSupportedLanguage(event.document.languageId)) {
            // Debounced analysis on change
            const debounceMs = config.get<number>('debounceMs', 1000);
            setTimeout(() => {
                vscode.commands.executeCommand('connascence.analyzeFile', event.document.uri);
            }, debounceMs);
        }
    });
    
    context.subscriptions.push(documentOpenHandler, documentChangeHandler);
    logger.info('✅ Background services initialized');
}

function startWorkspaceScanning() {
    logger.info('🔍 Starting workspace scanning for supported files...');
    
    // Scan for supported file types in background
    Promise.resolve(vscode.workspace.findFiles('**/*.{py,c,cpp,h,hpp,js,ts}', '**/node_modules/**', 100))
        .then(files => {
            logger.info(`📊 Found ${files.length} supported files in workspace`);
            
            // Update dashboard with file count
            if (dashboardProvider) {
                // Create basic quality metrics to show file count
                const basicMetrics = {
                    filesAnalyzed: files.length,
                    overallScore: 100,
                    totalIssues: 0,
                    criticalIssues: 0,
                    compliant: true,
                    safetyViolations: 0
                };
                dashboardProvider.updateData(basicMetrics, null);
            }
            
            // Optionally trigger analysis of critical files
            const config = vscode.workspace.getConfiguration('connascence');
            if (config.get<boolean>('analyzeOnStartup', false)) {
                logger.info('🚀 Auto-analyzing workspace files on startup');
                setTimeout(() => {
                    vscode.commands.executeCommand('connascence.analyzeWorkspace');
                }, 3000); // Delayed to not impact startup performance
            }
        })
        .catch((error: any) => {
            logger.error('Error scanning workspace files', error);
        });
}

function isSupportedLanguage(languageId: string): boolean {
    const supportedLanguages = ['python', 'c', 'cpp', 'javascript', 'typescript'];
    return supportedLanguages.includes(languageId);
}

function showWelcomeMessage() {
    const config = vscode.workspace.getConfiguration('connascence');
    const hasShownWelcome = config.get<boolean>('hasShownWelcome', false);
    
    if (!hasShownWelcome) {
        vscode.window.showInformationMessage(
            '🔗💔 Welcome to Connascence Safety Analyzer! Ready to break the chains of tight coupling?',
            'Show Dashboard',
            'View Documentation',
            'Configure Settings'
        ).then(selection => {
            switch (selection) {
                case 'Show Dashboard':
                    vscode.commands.executeCommand('connascence.showBrokenChainAnimation');
                    break;
                case 'View Documentation':
                    vscode.env.openExternal(vscode.Uri.parse('https://docs.connascence.io'));
                    break;
                case 'Configure Settings':
                    vscode.commands.executeCommand('connascence.openSettings');
                    break;
            }
        });
        
        // Mark as shown
        config.update('hasShownWelcome', true, vscode.ConfigurationTarget.Global);
    }
}

export function deactivate() {
    logger?.info('🔗💔 Connascence Analyzer extension deactivating...');
    
    // Dispose all managers
    try {
        visualHighlighting?.dispose();
        brokenChainLogo?.dispose();
        extension?.dispose();
        
        logger?.info('✅ Extension deactivated successfully');
        telemetry?.logEvent('extension.deactivate.success');
        
    } catch (error) {
        logger?.error('Error during deactivation', error);
        telemetry?.logEvent('extension.deactivate.error', {
            error: error instanceof Error ? error.message : String(error)
        });
    } finally {
        // Dispose logger and telemetry last
        telemetry?.dispose();
        logger?.dispose();
    }
}