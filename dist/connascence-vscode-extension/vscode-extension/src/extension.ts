/**
 * VS Code Extension for Connascence Analysis
 * 
 * Provides real-time diagnostics, quick fixes, and dashboard integration
 * for connascence analysis in Python codebases.
 */

import * as vscode from 'vscode';
import { ConnascenceDiagnostics } from './diagnostics';
import { ConnascenceCodeActions } from './codeActions';
import { ConnascenceTreeView } from './treeView';
import { ConnascenceStatusBar } from './statusBar';
import { ConnascenceDashboard } from './dashboard';

let diagnosticsProvider: ConnascenceDiagnostics;
let codeActionsProvider: ConnascenceCodeActions;
let treeViewProvider: ConnascenceTreeView;
let statusBar: ConnascenceStatusBar;
let dashboard: ConnascenceDashboard;

export function activate(context: vscode.ExtensionContext) {
    console.log('Connascence Analyzer extension is now active');

    // Initialize providers
    diagnosticsProvider = new ConnascenceDiagnostics(context);
    codeActionsProvider = new ConnascenceCodeActions(context);
    treeViewProvider = new ConnascenceTreeView(context);
    statusBar = new ConnascenceStatusBar(context);
    dashboard = new ConnascenceDashboard(context);

    // Register diagnostics collection
    const diagnosticCollection = vscode.languages.createDiagnosticCollection('connascence');
    diagnosticsProvider.setCollection(diagnosticCollection);
    context.subscriptions.push(diagnosticCollection);

    // Register code actions provider
    context.subscriptions.push(
        vscode.languages.registerCodeActionsProvider(
            { language: 'python' },
            codeActionsProvider,
            {
                providedCodeActionKinds: [
                    vscode.CodeActionKind.QuickFix,
                    vscode.CodeActionKind.Refactor
                ]
            }
        )
    );

    // Register tree view
    context.subscriptions.push(
        vscode.window.createTreeView('connascenceFindings', {
            treeDataProvider: treeViewProvider,
            showCollapseAll: true
        })
    );

    // Register commands
    const commands = [
        vscode.commands.registerCommand('connascence.scanFile', () => {
            const activeEditor = vscode.window.activeTextEditor;
            if (activeEditor && activeEditor.document.languageId === 'python') {
                diagnosticsProvider.scanFile(activeEditor.document);
            } else {
                vscode.window.showWarningMessage('Please open a Python file to scan');
            }
        }),

        vscode.commands.registerCommand('connascence.scanWorkspace', () => {
            diagnosticsProvider.scanWorkspace();
        }),

        vscode.commands.registerCommand('connascence.autofixCurrent', async () => {
            const activeEditor = vscode.window.activeTextEditor;
            if (activeEditor && activeEditor.document.languageId === 'python') {
                await codeActionsProvider.autofixFile(activeEditor.document);
            } else {
                vscode.window.showWarningMessage('Please open a Python file to autofix');
            }
        }),

        vscode.commands.registerCommand('connascence.toggleBaseline', () => {
            const config = vscode.workspace.getConfiguration('connascence');
            const current = config.get('baselineMode', false);
            config.update('baselineMode', !current, vscode.ConfigurationTarget.Workspace);
            vscode.window.showInformationMessage(`Baseline mode ${!current ? 'enabled' : 'disabled'}`);
        }),

        vscode.commands.registerCommand('connascence.openDashboard', () => {
            dashboard.show();
        }),

        vscode.commands.registerCommand('connascence.explainFinding', (item: any) => {
            if (item && item.finding) {
                dashboard.explainFinding(item.finding);
            }
        }),

        vscode.commands.registerCommand('connascence.refreshFindings', () => {
            treeViewProvider.refresh();
        }),

        vscode.commands.registerCommand('connascence.clearFindings', () => {
            diagnosticsProvider.clearAll();
            treeViewProvider.clear();
        })
    ];

    context.subscriptions.push(...commands);

    // File watcher for auto-scanning
    const watcher = vscode.workspace.createFileSystemWatcher('**/*.py');
    
    watcher.onDidChange((uri) => {
        const config = vscode.workspace.getConfiguration('connascence');
        if (config.get('autoScanOnSave', true)) {
            vscode.workspace.openTextDocument(uri).then(doc => {
                diagnosticsProvider.scanFileDebounced(doc);
            });
        }
    });

    watcher.onDidCreate((uri) => {
        vscode.workspace.openTextDocument(uri).then(doc => {
            diagnosticsProvider.scanFileDebounced(doc);
        });
    });

    watcher.onDidDelete((uri) => {
        diagnosticsProvider.clearFile(uri);
    });

    context.subscriptions.push(watcher);

    // Configuration change handler
    context.subscriptions.push(
        vscode.workspace.onDidChangeConfiguration(event => {
            if (event.affectsConfiguration('connascence')) {
                // Refresh diagnostics with new configuration
                diagnosticsProvider.refreshAll();
                statusBar.update();
            }
        })
    );

    // Initial workspace scan
    setTimeout(() => {
        const config = vscode.workspace.getConfiguration('connascence');
        if (config.get('scanOnStartup', true)) {
            vscode.commands.executeCommand('connascence.scanWorkspace');
        }
    }, 2000); // Delay to let VS Code fully initialize

    // Set context for when findings exist
    vscode.commands.executeCommand('setContext', 'connascence.hasFindings', false);
}

export function deactivate() {
    // Clean up resources
    if (diagnosticsProvider) {
        diagnosticsProvider.dispose();
    }
    if (dashboard) {
        dashboard.dispose();
    }
    console.log('Connascence Analyzer extension deactivated');
}