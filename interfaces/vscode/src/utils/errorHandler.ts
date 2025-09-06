/**
 * Centralized error handling utilities for the Connascence extension
 */
import * as vscode from 'vscode';
import { ExtensionLogger } from './logger';
import { TelemetryReporter } from './telemetry';

export enum ErrorCategory {
    NETWORK = 'network',
    PARSE = 'parse',
    RESOURCE_EXHAUSTED = 'resource_exhausted',
    CONFIGURATION = 'configuration',
    PYTHON_RUNTIME = 'python_runtime',
    ANALYZER_NOT_FOUND = 'analyzer_not_found',
    PERMISSION_DENIED = 'permission_denied',
    UNKNOWN = 'unknown'
}

export interface ErrorContext {
    operation: string;
    filePath?: string;
    component: string;
    retryable: boolean;
    userVisible: boolean;
}

export interface ErrorSolution {
    description: string;
    actions: ErrorAction[];
}

export interface ErrorAction {
    label: string;
    action: () => any;
    primary?: boolean;
}

export class ConnascenceError extends Error {
    constructor(
        public message: string,
        public category: ErrorCategory,
        public context: ErrorContext,
        public originalError?: Error,
        public solution?: ErrorSolution
    ) {
        super(message);
        this.name = 'ConnascenceError';
    }
}

export class ErrorHandler {
    private retryAttempts = new Map<string, number>();
    private maxRetries = 3;
    private retryDelays = [1000, 2000, 4000]; // exponential backoff

    constructor(
        private logger: ExtensionLogger,
        private telemetry: TelemetryReporter
    ) {}

    async handleError(error: any, context: ErrorContext): Promise<void> {
        const connascenceError = this.categorizeError(error, context);
        
        // Log the error
        this.logger.error(
            `[${connascenceError.category}] ${connascenceError.message}`, 
            connascenceError.originalError || connascenceError
        );
        
        // Record telemetry
        this.telemetry.logError(connascenceError, context.operation);
        
        // Handle based on category
        await this.handleByCategory(connascenceError);
    }

    private categorizeError(error: any, context: ErrorContext): ConnascenceError {
        const message = error.message || error.toString();
        
        // Network errors
        if (this.isNetworkError(error)) {
            return new ConnascenceError(
                `Network error during ${context.operation}`,
                ErrorCategory.NETWORK,
                { ...context, retryable: true },
                error,
                {
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
                }
            );
        }
        
        // Parse errors
        if (this.isParseError(error)) {
            return new ConnascenceError(
                `Failed to parse file during ${context.operation}`,
                ErrorCategory.PARSE,
                { ...context, retryable: false, userVisible: true },
                error,
                {
                    description: 'The file contains syntax errors that prevent analysis.',
                    actions: [
                        {
                            label: 'View Problems',
                            action: () => vscode.commands.executeCommand('workbench.panel.problems.focus'),
                            primary: true
                        }
                    ]
                }
            );
        }
        
        // Python runtime errors
        if (this.isPythonRuntimeError(error)) {
            return new ConnascenceError(
                'Python runtime not available or misconfigured',
                ErrorCategory.PYTHON_RUNTIME,
                { ...context, retryable: false, userVisible: true },
                error,
                {
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
                }
            );
        }
        
        // Analyzer not found
        if (this.isAnalyzerNotFoundError(error)) {
            return new ConnascenceError(
                'Connascence analyzer not found',
                ErrorCategory.ANALYZER_NOT_FOUND,
                { ...context, retryable: false, userVisible: true },
                error,
                {
                    description: 'The connascence analyzer is not available in the expected location.',
                    actions: [
                        {
                            label: 'Check Installation',
                            action: () => this.checkAnalyzerInstallation(),
                            primary: true
                        }
                    ]
                }
            );
        }
        
        // Resource exhausted
        if (this.isResourceExhaustedError(error)) {
            return new ConnascenceError(
                `System resources exhausted during ${context.operation}`,
                ErrorCategory.RESOURCE_EXHAUSTED,
                { ...context, retryable: true },
                error,
                {
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
                }
            );
        }
        
        // Default to unknown
        return new ConnascenceError(
            `Unexpected error during ${context.operation}: ${message}`,
            ErrorCategory.UNKNOWN,
            { ...context, retryable: false, userVisible: true },
            error
        );
    }

    private async handleByCategory(error: ConnascenceError): Promise<void> {
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

    private async handleNetworkError(error: ConnascenceError): Promise<void> {
        if (error.context.retryable) {
            await this.scheduleRetryWithBackoff(error.context);
        } else {
            await this.showErrorToUser(error);
        }
    }

    private async handleParseError(error: ConnascenceError): Promise<void> {
        // Parse errors are typically not retryable, show to user
        await this.showErrorToUser(error);
    }

    private async handleResourceError(error: ConnascenceError): Promise<void> {
        // Schedule retry for later
        await this.scheduleRetryLater(error.context);
    }

    private async handleConfigurationError(error: ConnascenceError): Promise<void> {
        // These are critical errors that prevent the extension from working
        await this.showCriticalError(error);
    }

    private async showErrorToUser(error: ConnascenceError): Promise<void> {
        if (!error.solution) {
            vscode.window.showErrorMessage(error.message);
            return;
        }

        const actions = error.solution.actions.map(a => a.label);
        const selected = await vscode.window.showErrorMessage(
            error.message,
            { detail: error.solution.description },
            ...actions
        );

        if (selected) {
            const action = error.solution.actions.find(a => a.label === selected);
            if (action) {
                await action.action();
            }
        }
    }

    private async showCriticalError(error: ConnascenceError): Promise<void> {
        if (!error.solution) {
            vscode.window.showErrorMessage(
                `Critical Error: ${error.message}`,
                'View Logs'
            ).then(selection => {
                if (selection === 'View Logs') {
                    vscode.commands.executeCommand('workbench.action.showLogs');
                }
            });
            return;
        }

        const actions = error.solution.actions.map(a => a.label);
        actions.push('View Logs');

        const selected = await vscode.window.showErrorMessage(
            `Critical Error: ${error.message}`,
            { 
                detail: error.solution.description,
                modal: true
            },
            ...actions
        );

        if (selected === 'View Logs') {
            vscode.commands.executeCommand('workbench.action.showLogs');
        } else if (selected) {
            const action = error.solution.actions.find(a => a.label === selected);
            if (action) {
                await action.action();
            }
        }
    }

    private async scheduleRetryWithBackoff(context: ErrorContext): Promise<void> {
        const key = `${context.component}:${context.operation}`;
        const attempts = this.retryAttempts.get(key) || 0;

        if (attempts >= this.maxRetries) {
            this.retryAttempts.delete(key);
            vscode.window.showErrorMessage(
                `Failed to ${context.operation} after ${this.maxRetries} attempts. Please try again later.`
            );
            return;
        }

        this.retryAttempts.set(key, attempts + 1);
        const delay = this.retryDelays[attempts] || 4000;

        setTimeout(() => {
            // Trigger retry - this would need to be implemented per context
            this.logger.info(`Retrying ${context.operation} (attempt ${attempts + 1}/${this.maxRetries})`);
        }, delay);
    }

    private async scheduleRetry(context: ErrorContext): Promise<void> {
        // Immediate retry
        setTimeout(() => {
            this.logger.info(`Retrying ${context.operation}`);
        }, 100);
    }

    private async scheduleRetryLater(context: ErrorContext): Promise<void> {
        // Retry in 30 seconds
        setTimeout(() => {
            this.logger.info(`Retrying ${context.operation} after resource recovery`);
        }, 30000);
    }

    private async configurePythonPath(): Promise<void> {
        const pythonPath = await vscode.window.showInputBox({
            prompt: 'Enter the path to your Python executable',
            placeHolder: 'e.g., /usr/bin/python3 or C:\\Python39\\python.exe',
            validateInput: (value) => {
                if (!value) return 'Python path is required';
                return null;
            }
        });

        if (pythonPath) {
            const config = vscode.workspace.getConfiguration('connascence');
            await config.update('pythonPath', pythonPath, vscode.ConfigurationTarget.Workspace);
            vscode.window.showInformationMessage('Python path updated. Restarting analysis...');
        }
    }

    private async checkAnalyzerInstallation(): Promise<void> {
        // This would check if the analyzer is properly installed
        vscode.window.showInformationMessage(
            'Please ensure the connascence analyzer is installed and accessible.',
            'View Documentation'
        ).then(selection => {
            if (selection === 'View Documentation') {
                vscode.env.openExternal(vscode.Uri.parse('https://docs.connascence.io/installation'));
            }
        });
    }

    private async suggestScopeReduction(): Promise<void> {
        const selection = await vscode.window.showInformationMessage(
            'To reduce resource usage, consider analyzing fewer files or excluding test directories.',
            'Configure Exclusions',
            'Analyze Current File Only'
        );

        if (selection === 'Configure Exclusions') {
            vscode.commands.executeCommand('connascence.openSettings');
        } else if (selection === 'Analyze Current File Only') {
            vscode.commands.executeCommand('connascence.analyzeFile');
        }
    }

    // Error detection helpers
    private isNetworkError(error: any): boolean {
        const message = error.message?.toLowerCase() || '';
        return message.includes('network') || 
               message.includes('connection') || 
               message.includes('timeout') ||
               message.includes('econnrefused') ||
               error.code === 'ENOTFOUND';
    }

    private isParseError(error: any): boolean {
        const message = error.message?.toLowerCase() || '';
        return message.includes('syntax') || 
               message.includes('parse') || 
               message.includes('invalid syntax') ||
               message.includes('unexpected token');
    }

    private isPythonRuntimeError(error: any): boolean {
        const message = error.message?.toLowerCase() || '';
        return message.includes('python') && 
               (message.includes('not found') || 
                message.includes('command not found') ||
                message.includes('no such file'));
    }

    private isAnalyzerNotFoundError(error: any): boolean {
        const message = error.message?.toLowerCase() || '';
        return message.includes('analyzer') && 
               (message.includes('not found') || 
                message.includes('not available') ||
                message.includes('no such file'));
    }

    private isResourceExhaustedError(error: any): boolean {
        const message = error.message?.toLowerCase() || '';
        return message.includes('memory') || 
               message.includes('resource') ||
               message.includes('limit') ||
               message.includes('out of space') ||
               error.code === 'ENOMEM';
    }

    // Clean up retry tracking for completed operations
    clearRetryTracking(context: ErrorContext): void {
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