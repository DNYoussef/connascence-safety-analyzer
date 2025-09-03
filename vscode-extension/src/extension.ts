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

let extension: ConnascenceExtension;
let logger: ExtensionLogger;
let telemetry: TelemetryReporter;

export function activate(context: vscode.ExtensionContext) {
    // Initialize logger and telemetry
    logger = new ExtensionLogger('Connascence');
    telemetry = new TelemetryReporter(context, logger);
    
    logger.info('Connascence Analyzer extension activating...');
    telemetry.logEvent('extension.activate.start');

    try {
        // Initialize main extension class
        extension = new ConnascenceExtension(context, logger, telemetry);
        
        // Activate all components
        extension.activate();

        
        telemetry.logEvent('extension.activate.success');
        logger.info('Connascence Analyzer extension activated successfully');
        
    } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        logger.error('Failed to activate extension', error);
        telemetry.logEvent('extension.activate.error', { error: errorMessage });
        
        vscode.window.showErrorMessage(
            `Connascence extension failed to activate: ${errorMessage}`
        );
        throw error;
    }
}

export function deactivate() {
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
    } catch (error) {
        logger?.error('Error during deactivation', error);
    }
}