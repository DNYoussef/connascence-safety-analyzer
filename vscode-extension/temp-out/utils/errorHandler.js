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
exports.ErrorHandler = exports.ConnascenceError = exports.ErrorCategory = void 0;
/**
 * Centralized error handling utilities for the Connascence extension
 */
const vscode = __importStar(require("vscode"));
var ErrorCategory;
(function (ErrorCategory) {
    ErrorCategory["NETWORK"] = "network";
    ErrorCategory["PARSE"] = "parse";
    ErrorCategory["RESOURCE_EXHAUSTED"] = "resource_exhausted";
    ErrorCategory["CONFIGURATION"] = "configuration";
    ErrorCategory["PYTHON_RUNTIME"] = "python_runtime";
    ErrorCategory["ANALYZER_NOT_FOUND"] = "analyzer_not_found";
    ErrorCategory["PERMISSION_DENIED"] = "permission_denied";
    ErrorCategory["UNKNOWN"] = "unknown";
})(ErrorCategory || (exports.ErrorCategory = ErrorCategory = {}));
class ConnascenceError extends Error {
    constructor(message, category, context, originalError, solution) {
        super(message);
        this.message = message;
        this.category = category;
        this.context = context;
        this.originalError = originalError;
        this.solution = solution;
        this.name = 'ConnascenceError';
    }
}
exports.ConnascenceError = ConnascenceError;
class ErrorHandler {
    constructor(logger, telemetry) {
        this.logger = logger;
        this.telemetry = telemetry;
        this.retryAttempts = new Map();
        this.maxRetries = 3;
        this.retryDelays = [1000, 2000, 4000]; // exponential backoff
    }
    async handleError(error, context) {
        const connascenceError = this.categorizeError(error, context);
        // Log the error
        this.logger.error(`[${connascenceError.category}] ${connascenceError.message}`, connascenceError.originalError || connascenceError);
        // Record telemetry
        this.telemetry.logError(connascenceError, context.operation);
        // Handle based on category
        await this.handleByCategory(connascenceError);
    }
    categorizeError(error, context) {
        const message = error.message || error.toString();
        // Network errors
        if (this.isNetworkError(error)) {
            return new ConnascenceError(`Network error during ${context.operation}`, ErrorCategory.NETWORK, { ...context, retryable: true }, error, {
                description: 'The extension failed to connect to the analysis service.',
                actions: [
                    {
                        label: 'Retry Analysis',
                        action: () => this.scheduleRetry(context),
                        primary: true
                    },
                    {
                        label: 'Check Configuration',
                        action: () => vscode.commands.executeCommand('connascence.openSettings')
                    }
                ]
            });
        }
        // Parse errors
        if (this.isParseError(error)) {
            return new ConnascenceError(`Failed to parse file during ${context.operation}`, ErrorCategory.PARSE, { ...context, retryable: false, userVisible: true }, error, {
                description: 'The file contains syntax errors that prevent analysis.',
                actions: [
                    {
                        label: 'View Problems',
                        action: () => vscode.commands.executeCommand('workbench.panel.problems.focus'),
                        primary: true
                    }
                ]
            });
        }
        // Python runtime errors
        if (this.isPythonRuntimeError(error)) {
            return new ConnascenceError('Python runtime not available or misconfigured', ErrorCategory.PYTHON_RUNTIME, { ...context, retryable: false, userVisible: true }, error, {
                description: 'The extension requires Python 3.7+ to perform analysis.',
                actions: [
                    {
                        label: 'Configure Python Path',
                        action: () => this.configurePythonPath(),
                        primary: true
                    },
                    {
                        label: 'Install Python',
                        action: () => vscode.env.openExternal(vscode.Uri.parse('https://python.org/downloads'))
                    }
                ]
            });
        }
        // Analyzer not found
        if (this.isAnalyzerNotFoundError(error)) {
            return new ConnascenceError('Connascence analyzer not found', ErrorCategory.ANALYZER_NOT_FOUND, { ...context, retryable: false, userVisible: true }, error, {
                description: 'The connascence analyzer is not available in the expected location.',
                actions: [
                    {
                        label: 'Check Installation',
                        action: () => this.checkAnalyzerInstallation(),
                        primary: true
                    }
                ]
            });
        }
        // Resource exhausted
        if (this.isResourceExhaustedError(error)) {
            return new ConnascenceError(`System resources exhausted during ${context.operation}`, ErrorCategory.RESOURCE_EXHAUSTED, { ...context, retryable: true }, error, {
                description: 'The analysis requires more system resources than available.',
                actions: [
                    {
                        label: 'Retry Later',
                        action: () => this.scheduleRetryLater(context),
                        primary: true
                    },
                    {
                        label: 'Reduce Scope',
                        action: () => this.suggestScopeReduction()
                    }
                ]
            });
        }
        // Default to unknown
        return new ConnascenceError(`Unexpected error during ${context.operation}: ${message}`, ErrorCategory.UNKNOWN, { ...context, retryable: false, userVisible: true }, error);
    }
    async handleByCategory(error) {
        switch (error.category) {
            case ErrorCategory.NETWORK:
                await this.handleNetworkError(error);
                break;
            case ErrorCategory.PARSE:
                await this.handleParseError(error);
                break;
            case ErrorCategory.RESOURCE_EXHAUSTED:
                await this.handleResourceError(error);
                break;
            case ErrorCategory.PYTHON_RUNTIME:
            case ErrorCategory.ANALYZER_NOT_FOUND:
                await this.handleConfigurationError(error);
                break;
            default:
                if (error.context.userVisible) {
                    await this.showErrorToUser(error);
                }
        }
    }
    async handleNetworkError(error) {
        if (error.context.retryable) {
            await this.scheduleRetryWithBackoff(error.context);
        }
        else {
            await this.showErrorToUser(error);
        }
    }
    async handleParseError(error) {
        // Parse errors are typically not retryable, show to user
        await this.showErrorToUser(error);
    }
    async handleResourceError(error) {
        // Schedule retry for later
        await this.scheduleRetryLater(error.context);
    }
    async handleConfigurationError(error) {
        // These are critical errors that prevent the extension from working
        await this.showCriticalError(error);
    }
    async showErrorToUser(error) {
        if (!error.solution) {
            vscode.window.showErrorMessage(error.message);
            return;
        }
        const actions = error.solution.actions.map(a => a.label);
        const selected = await vscode.window.showErrorMessage(error.message, { detail: error.solution.description }, ...actions);
        if (selected) {
            const action = error.solution.actions.find(a => a.label === selected);
            if (action) {
                await action.action();
            }
        }
    }
    async showCriticalError(error) {
        if (!error.solution) {
            vscode.window.showErrorMessage(`Critical Error: ${error.message}`, 'View Logs').then(selection => {
                if (selection === 'View Logs') {
                    vscode.commands.executeCommand('workbench.action.showLogs');
                }
            });
            return;
        }
        const actions = error.solution.actions.map(a => a.label);
        actions.push('View Logs');
        const selected = await vscode.window.showErrorMessage(`Critical Error: ${error.message}`, {
            detail: error.solution.description,
            modal: true
        }, ...actions);
        if (selected === 'View Logs') {
            vscode.commands.executeCommand('workbench.action.showLogs');
        }
        else if (selected) {
            const action = error.solution.actions.find(a => a.label === selected);
            if (action) {
                await action.action();
            }
        }
    }
    async scheduleRetryWithBackoff(context) {
        const key = `${context.component}:${context.operation}`;
        const attempts = this.retryAttempts.get(key) || 0;
        if (attempts >= this.maxRetries) {
            this.retryAttempts.delete(key);
            vscode.window.showErrorMessage(`Failed to ${context.operation} after ${this.maxRetries} attempts. Please try again later.`);
            return;
        }
        this.retryAttempts.set(key, attempts + 1);
        const delay = this.retryDelays[attempts] || 4000;
        setTimeout(() => {
            // Trigger retry - this would need to be implemented per context
            this.logger.info(`Retrying ${context.operation} (attempt ${attempts + 1}/${this.maxRetries})`);
        }, delay);
    }
    async scheduleRetry(context) {
        // Immediate retry
        setTimeout(() => {
            this.logger.info(`Retrying ${context.operation}`);
        }, 100);
    }
    async scheduleRetryLater(context) {
        // Retry in 30 seconds
        setTimeout(() => {
            this.logger.info(`Retrying ${context.operation} after resource recovery`);
        }, 30000);
    }
    async configurePythonPath() {
        const pythonPath = await vscode.window.showInputBox({
            prompt: 'Enter the path to your Python executable',
            placeHolder: 'e.g., /usr/bin/python3 or C:\\Python39\\python.exe',
            validateInput: (value) => {
                if (!value)
                    return 'Python path is required';
                return null;
            }
        });
        if (pythonPath) {
            const config = vscode.workspace.getConfiguration('connascence');
            await config.update('pythonPath', pythonPath, vscode.ConfigurationTarget.Workspace);
            vscode.window.showInformationMessage('Python path updated. Restarting analysis...');
        }
    }
    async checkAnalyzerInstallation() {
        // This would check if the analyzer is properly installed
        vscode.window.showInformationMessage('Please ensure the connascence analyzer is installed and accessible.', 'View Documentation').then(selection => {
            if (selection === 'View Documentation') {
                vscode.env.openExternal(vscode.Uri.parse('https://docs.connascence.io/installation'));
            }
        });
    }
    async suggestScopeReduction() {
        const selection = await vscode.window.showInformationMessage('To reduce resource usage, consider analyzing fewer files or excluding test directories.', 'Configure Exclusions', 'Analyze Current File Only');
        if (selection === 'Configure Exclusions') {
            vscode.commands.executeCommand('connascence.openSettings');
        }
        else if (selection === 'Analyze Current File Only') {
            vscode.commands.executeCommand('connascence.analyzeFile');
        }
    }
    // Error detection helpers
    isNetworkError(error) {
        const message = error.message?.toLowerCase() || '';
        return message.includes('network') ||
            message.includes('connection') ||
            message.includes('timeout') ||
            message.includes('econnrefused') ||
            error.code === 'ENOTFOUND';
    }
    isParseError(error) {
        const message = error.message?.toLowerCase() || '';
        return message.includes('syntax') ||
            message.includes('parse') ||
            message.includes('invalid syntax') ||
            message.includes('unexpected token');
    }
    isPythonRuntimeError(error) {
        const message = error.message?.toLowerCase() || '';
        return message.includes('python') &&
            (message.includes('not found') ||
                message.includes('command not found') ||
                message.includes('no such file'));
    }
    isAnalyzerNotFoundError(error) {
        const message = error.message?.toLowerCase() || '';
        return message.includes('analyzer') &&
            (message.includes('not found') ||
                message.includes('not available') ||
                message.includes('no such file'));
    }
    isResourceExhaustedError(error) {
        const message = error.message?.toLowerCase() || '';
        return message.includes('memory') ||
            message.includes('resource') ||
            message.includes('limit') ||
            message.includes('out of space') ||
            error.code === 'ENOMEM';
    }
    // Clean up retry tracking for completed operations
    clearRetryTracking(context) {
        const key = `${context.component}:${context.operation}`;
        this.retryAttempts.delete(key);
    }
    // Get retry statistics
    getRetryStatistics() {
        return {
            activeRetries: this.retryAttempts.size,
            retryDetails: Array.from(this.retryAttempts.entries()).map(([key, attempts]) => ({
                operation: key,
                attempts
            }))
        };
    }
}
exports.ErrorHandler = ErrorHandler;
//# sourceMappingURL=errorHandler.js.map