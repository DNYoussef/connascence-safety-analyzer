"use strict";
/**
 * VS Code Extension for Connascence Analysis
 *
 * Provides real-time diagnostics, quick fixes, and dashboard integration
 * for connascence analysis in Python codebases.
 */
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
exports.activate = activate;
exports.deactivate = deactivate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const ConnascenceExtension_1 = require("./core/ConnascenceExtension");
const logger_1 = require("./utils/logger");
const telemetry_1 = require("./utils/telemetry");
const dashboardProvider_1 = require("./providers/dashboardProvider");
const analysisResultsProvider_1 = require("./providers/analysisResultsProvider");
const visualHighlighting_1 = require("./features/visualHighlighting");
const notificationManager_1 = require("./features/notificationManager");
const brokenChainLogo_1 = require("./features/brokenChainLogo");
const aiFixSuggestions_1 = require("./features/aiFixSuggestions");
const connascenceService_1 = require("./services/connascenceService");
let extension;
let logger;
let telemetry;
// Global managers for all features
let dashboardProvider;
let analysisResultsProvider;
let visualHighlighting;
let notificationManager;
let brokenChainLogo;
let aiFixSuggestions;
let connascenceService;
function activate(context) {
    // Initialize logger and telemetry
    logger = new logger_1.ExtensionLogger('Connascence');
    telemetry = new telemetry_1.TelemetryReporter(context, logger);
    logger.info('🔗💔 Connascence Analyzer extension activating - Breaking chains!');
    telemetry.logEvent('extension.activate.start');
    try {
        // Initialize core services
        connascenceService = new connascenceService_1.ConnascenceService();
        extension = new ConnascenceExtension_1.ConnascenceExtension(context, logger, telemetry);
        // Initialize all feature managers
        initializeFeatureManagers(context);
        // Initialize tree data providers
        initializeTreeProviders(context);
        // Register all commands
        registerAllCommands(context);
        // Activate main extension
        extension.activate();
        telemetry.logEvent('extension.activate.success');
        logger.info('🔗✨ Connascence Analyzer extension activated successfully - Ready to break chains!');
        // Show welcome message
        showWelcomeMessage();
    }
    catch (error) {
        logger.error('Failed to activate extension', error);
        telemetry.logEvent('extension.activate.error', {
            error: error instanceof Error ? error.message : String(error)
        });
        throw error;
    }
}
function initializeFeatureManagers(context) {
    logger.info('🔧 Initializing feature managers...');
    // Initialize visual highlighting
    visualHighlighting = new visualHighlighting_1.VisualHighlightingManager();
    context.subscriptions.push(visualHighlighting);
    // Initialize notification manager
    notificationManager = notificationManager_1.NotificationManager.getInstance();
    // Initialize broken chain logo
    brokenChainLogo = brokenChainLogo_1.BrokenChainLogoManager.getInstance();
    context.subscriptions.push(brokenChainLogo);
    // Initialize AI fix suggestions
    aiFixSuggestions = aiFixSuggestions_1.AIFixSuggestionsProvider.getInstance();
    logger.info('✅ Feature managers initialized');
}
function initializeTreeProviders(context) {
    logger.info('🌳 Initializing tree data providers...');
    // Initialize dashboard provider
    dashboardProvider = new dashboardProvider_1.ConnascenceDashboardProvider(connascenceService);
    vscode.window.registerTreeDataProvider('connascenceDashboard', dashboardProvider);
    // Initialize analysis results provider
    analysisResultsProvider = new analysisResultsProvider_1.AnalysisResultsProvider();
    vscode.window.registerTreeDataProvider('connascenceAnalysisResults', analysisResultsProvider);
    logger.info('✅ Tree data providers registered');
}
function registerAllCommands(context) {
    logger.info('📋 Registering commands...');
    // Notification management commands
    const notificationControlsCommand = vscode.commands.registerCommand('connascence.manageNotifications', () => {
        notificationManager.showFilterManagementQuickPick();
    });
    // Broken chain logo commands
    const showLogoCommand = vscode.commands.registerCommand('connascence.showBrokenChainAnimation', () => {
        brokenChainLogo.showBrokenChainAnimation();
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
    // Highlighting commands
    const toggleHighlightingCommand = vscode.commands.registerCommand('connascence.toggleHighlighting', () => {
        const config = vscode.workspace.getConfiguration('connascence');
        const currentValue = config.get('enableVisualHighlighting', true);
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
    context.subscriptions.push(notificationControlsCommand, showLogoCommand, refreshDashboardCommand, groupByFileCommand, groupBySeverityCommand, groupByTypeCommand, toggleHighlightingCommand, refreshHighlightingCommand);
    logger.info('✅ Commands registered');
}
function showWelcomeMessage() {
    const config = vscode.workspace.getConfiguration('connascence');
    const hasShownWelcome = config.get('hasShownWelcome', false);
    if (!hasShownWelcome) {
        vscode.window.showInformationMessage('🔗💔 Welcome to Connascence Safety Analyzer! Ready to break the chains of tight coupling?', 'Show Dashboard', 'View Documentation', 'Configure Settings').then(selection => {
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
function deactivate() {
    logger?.info('🔗💔 Connascence Analyzer extension deactivating...');
    // Dispose all managers
    try {
        visualHighlighting?.dispose();
        brokenChainLogo?.dispose();
        extension?.deactivate();
        logger?.info('✅ Extension deactivated successfully');
        telemetry?.logEvent('extension.deactivate.success');
    }
    catch (error) {
        logger?.error('Error during deactivation', error);
        telemetry?.logEvent('extension.deactivate.error', {
            error: error instanceof Error ? error.message : String(error)
        });
    }
    finally {
        // Dispose logger and telemetry last
        telemetry?.dispose();
        logger?.dispose();
    }
}
telemetry.logEvent('extension.activate.error', { error: errorMessage });
vscode.window.showErrorMessage(`Connascence extension failed to activate: ${errorMessage}`);
throw error;
function deactivate() {
    logger?.info('Connascence Analyzer extension deactivating...');
    telemetry?.logEvent('extension.deactivate.start');
    try {
        // Clean up extension resources
        if (extension) {
            extension.dispose();
        }
        if (telemetry) {
            telemetry.dispose();
        }
        logger?.info('Connascence Analyzer extension deactivated successfully');
    }
    catch (error) {
        logger?.error('Error during deactivation', error);
    }
}
//# sourceMappingURL=extension_backup.js.map