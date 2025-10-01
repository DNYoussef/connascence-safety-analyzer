import * as vscode from 'vscode';
import { ConnascenceAnalyzer } from './analyzer';
import { MCPClient } from './mcpClient';
import { DiagnosticProvider } from './diagnostics';
import { CodeActionProvider } from './codeActions';
import { ViolationsProvider, MetricsProvider, ActionsProvider } from './treeViewProviders';

let analyzer: ConnascenceAnalyzer;
let mcpClient: MCPClient;
let diagnosticProvider: DiagnosticProvider;
let violationsProvider: ViolationsProvider;
let metricsProvider: MetricsProvider;

export function activate(context: vscode.ExtensionContext) {
    console.log('Connascence Analyzer extension is activating');

    // Initialize components
    analyzer = new ConnascenceAnalyzer(context);
    mcpClient = new MCPClient(context);
    diagnosticProvider = new DiagnosticProvider(analyzer);

    // Initialize tree view providers
    violationsProvider = new ViolationsProvider();
    metricsProvider = new MetricsProvider();
    const actionsProvider = new ActionsProvider();

    // Register tree views
    vscode.window.registerTreeDataProvider('connascenceExplorer', violationsProvider);
    vscode.window.registerTreeDataProvider('connascenceMetrics', metricsProvider);
    vscode.window.registerTreeDataProvider('connascenceActions', actionsProvider);

    // Register commands
    const analyzeCommand = vscode.commands.registerCommand('connascence.analyze', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor');
            return;
        }

        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Analyzing Connascence",
            cancellable: false
        }, async (progress) => {
            progress.report({ increment: 0, message: "Starting analysis..." });

            const results = await analyzer.analyzeDocument(editor.document);

            progress.report({ increment: 50, message: "Processing violations..." });

            diagnosticProvider.updateDiagnostics(editor.document.uri, results);

            // Update sidebar views
            violationsProvider.updateViolations(results.violations || []);
            metricsProvider.updateMetrics(results.metrics || {});

            progress.report({ increment: 100, message: "Analysis complete" });

            vscode.window.showInformationMessage(
                `Analysis complete: ${results.violations.length} violations found`
            );
        });
    });

    const showReportCommand = vscode.commands.registerCommand('connascence.showReport', async () => {
        const panel = vscode.window.createWebviewPanel(
            'connascenceReport',
            'Connascence Analysis Report',
            vscode.ViewColumn.Beside,
            {
                enableScripts: true
            }
        );

        const results = await analyzer.getLastResults();
        panel.webview.html = getReportWebviewContent(results);
    });

    const fixCommand = vscode.commands.registerCommand('connascence.fix', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor');
            return;
        }

        const fixes = await analyzer.getAvailableFixes(editor.document.uri);
        if (fixes.length === 0) {
            vscode.window.showInformationMessage('No automatic fixes available');
            return;
        }

        const quickPick = await vscode.window.showQuickPick(
            fixes.map(fix => ({
                label: fix.title,
                description: fix.description,
                fix: fix
            })),
            {
                placeHolder: 'Select fixes to apply',
                canPickMany: true
            }
        );

        if (quickPick) {
            await analyzer.applyFixes(quickPick.map(item => item.fix));
            vscode.window.showInformationMessage(`Applied ${quickPick.length} fixes`);
        }
    });

    const configureCommand = vscode.commands.registerCommand('connascence.configure', async () => {
        const config = vscode.workspace.getConfiguration('connascence');
        const policy = await vscode.window.showQuickPick(
            [
                { label: 'nasa-compliance', description: 'NASA Power of Ten compliance' },
                { label: 'strict', description: 'Strict analysis mode' },
                { label: 'standard', description: 'Standard analysis' },
                { label: 'lenient', description: 'Lenient analysis' }
            ],
            {
                placeHolder: 'Select analysis policy'
            }
        );

        if (policy) {
            await config.update('policy', policy.label, vscode.ConfigurationTarget.Workspace);
            vscode.window.showInformationMessage(`Policy updated to: ${policy.label}`);
        }
    });

    // Sidebar commands
    const refreshViolationsCommand = vscode.commands.registerCommand('connascence.refreshViolations', async () => {
        violationsProvider.refresh();
        metricsProvider.refresh();
        vscode.window.showInformationMessage('Refreshed violations view');
    });

    const openViolationCommand = vscode.commands.registerCommand('connascence.openViolation',
        async (filePath: string, line: number, violation: any) => {
            if (!filePath) {
                return;
            }

            const document = await vscode.workspace.openTextDocument(filePath);
            const editor = await vscode.window.showTextDocument(document);

            if (line !== undefined && line > 0) {
                const position = new vscode.Position(line - 1, 0);
                editor.selection = new vscode.Selection(position, position);
                editor.revealRange(new vscode.Range(position, position), vscode.TextEditorRevealType.InCenter);
            }
        }
    );

    const fixViolationCommand = vscode.commands.registerCommand('connascence.fixViolation',
        async (violation: any) => {
            if (!violation) {
                vscode.window.showWarningMessage('No violation selected');
                return;
            }

            const fix = await analyzer.getSuggestedFix(violation);
            if (fix) {
                await analyzer.applyFixes([fix]);
                vscode.window.showInformationMessage('Fix applied successfully');
                violationsProvider.refresh();
            } else {
                vscode.window.showWarningMessage('No automatic fix available for this violation');
            }
        }
    );

    // Register providers
    const codeActionProvider = new CodeActionProvider(analyzer);
    context.subscriptions.push(
        vscode.languages.registerCodeActionsProvider(
            ['python', 'javascript', 'typescript'],
            codeActionProvider
        )
    );

    // Register disposables
    context.subscriptions.push(
        analyzeCommand,
        showReportCommand,
        fixCommand,
        configureCommand,
        refreshViolationsCommand,
        openViolationCommand,
        fixViolationCommand,
        diagnosticProvider,
        mcpClient
    );

    // Auto-analyze on save if enabled
    const saveListener = vscode.workspace.onDidSaveTextDocument(async (document) => {
        const config = vscode.workspace.getConfiguration('connascence');
        if (config.get('enableRealTime')) {
            const results = await analyzer.analyzeDocument(document);
            diagnosticProvider.updateDiagnostics(document.uri, results);
        }
    });

    context.subscriptions.push(saveListener);

    // Connect to MCP server
    mcpClient.connect().catch(err => {
        console.error('Failed to connect to MCP server:', err);
    });

    vscode.window.showInformationMessage('Connascence Analyzer activated');
}

export function deactivate() {
    if (mcpClient) {
        mcpClient.disconnect();
    }
}

function getReportWebviewContent(results: any): string {
    return `<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Connascence Analysis Report</title>
        <style>
            body {
                font-family: var(--vscode-font-family);
                color: var(--vscode-foreground);
                background-color: var(--vscode-editor-background);
                padding: 20px;
            }
            h1 { color: var(--vscode-textLink-foreground); }
            .violation {
                margin: 10px 0;
                padding: 10px;
                border-left: 3px solid;
                background: var(--vscode-textBlockQuote-background);
            }
            .critical { border-color: #ff0000; }
            .high { border-color: #ff8800; }
            .medium { border-color: #ffff00; }
            .low { border-color: #00ff00; }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }
            .stat {
                padding: 15px;
                background: var(--vscode-input-background);
                border-radius: 5px;
                text-align: center;
            }
            .stat-value {
                font-size: 2em;
                font-weight: bold;
                color: var(--vscode-textLink-foreground);
            }
        </style>
    </head>
    <body>
        <h1>Connascence Analysis Report</h1>
        <div class="stats">
            <div class="stat">
                <div class="stat-value">${results.violations?.length || 0}</div>
                <div>Total Violations</div>
            </div>
            <div class="stat">
                <div class="stat-value">${results.nasaCompliance || 'N/A'}%</div>
                <div>NASA Compliance</div>
            </div>
            <div class="stat">
                <div class="stat-value">${results.duplications || 0}</div>
                <div>Duplications</div>
            </div>
            <div class="stat">
                <div class="stat-value">${results.godObjects || 0}</div>
                <div>God Objects</div>
            </div>
        </div>
        <h2>Violations</h2>
        ${results.violations?.map((v: any) => `
            <div class="violation ${v.severity}">
                <strong>${v.type}</strong> - ${v.severity.toUpperCase()}<br>
                <code>${v.file}:${v.line}</code><br>
                ${v.message}
            </div>
        `).join('') || '<p>No violations found</p>'}
    </body>
    </html>`;
}