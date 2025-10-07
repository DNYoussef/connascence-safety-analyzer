/**
 * Welcome Screen for Connascence Safety Analyzer
 *
 * Provides an interactive welcome experience with quick start guide,
 * configuration wizard, and helpful resources.
 */

import * as vscode from 'vscode';
import * as path from 'path';

export class WelcomeScreen {
    private panel: vscode.WebviewPanel | undefined;
    private readonly extensionUri: vscode.Uri;

    constructor(private context: vscode.ExtensionContext) {
        this.extensionUri = context.extensionUri;
    }

    /**
     * Show welcome screen
     */
    public show(): void {
        const column = vscode.ViewColumn.One;

        // If panel already exists, reveal it
        if (this.panel) {
            this.panel.reveal(column);
            return;
        }

        // Create new panel
        this.panel = vscode.window.createWebviewPanel(
            'connascenceWelcome',
            'Welcome to Connascence Analyzer',
            column,
            {
                enableScripts: true,
                localResourceRoots: [this.extensionUri]
            }
        );

        // Set HTML content
        this.panel.webview.html = this.getHtmlContent(this.panel.webview);

        // Handle messages from webview
        this.panel.webview.onDidReceiveMessage(
            message => this.handleMessage(message),
            undefined,
            this.context.subscriptions
        );

        // Clean up when panel is closed
        this.panel.onDidDispose(
            () => { this.panel = undefined; },
            undefined,
            this.context.subscriptions
        );
    }

    /**
     * Handle messages from webview
     */
    private async handleMessage(message: any): Promise<void> {
        switch (message.command) {
            case 'analyzeCurrentFile':
                await vscode.commands.executeCommand('connascence.analyzeFile');
                break;

            case 'analyzeWorkspace':
                await vscode.commands.executeCommand('connascence.analyzeWorkspace');
                break;

            case 'openSettings':
                await vscode.commands.executeCommand('workbench.action.openSettings', 'connascence');
                break;

            case 'viewDocs':
                const docsUri = vscode.Uri.parse('https://github.com/connascence/connascence-analyzer');
                await vscode.env.openExternal(docsUri);
                break;

            case 'setSafetyProfile':
                const profile = message.value;
                const config = vscode.workspace.getConfiguration('connascence');
                await config.update('safetyProfile', profile, vscode.ConfigurationTarget.Global);
                vscode.window.showInformationMessage(`Safety profile set to: ${profile}`);
                break;

            case 'enableMCP':
                const mcpConfig = vscode.workspace.getConfiguration('connascence');
                await mcpConfig.update('useMCP', true, vscode.ConfigurationTarget.Global);
                vscode.window.showInformationMessage('MCP protocol enabled');
                break;

            case 'runQuickStart':
                await this.runQuickStartWizard();
                break;

            case 'dontShowAgain':
                await this.context.globalState.update('welcomeScreenShown', true);
                if (this.panel) {
                    this.panel.dispose();
                }
                break;
        }
    }

    /**
     * Run quick start configuration wizard
     */
    private async runQuickStartWizard(): Promise<void> {
        // Step 1: Choose safety profile
        const profileChoice = await vscode.window.showQuickPick([
            { label: 'Strict', description: 'Maximum safety, catches all issues', value: 'strict' },
            { label: 'Standard', description: 'Balanced approach (recommended)', value: 'standard' },
            { label: 'Lenient', description: 'Focus on critical issues only', value: 'lenient' }
        ], {
            placeHolder: 'Select a safety profile'
        });

        if (profileChoice) {
            const config = vscode.workspace.getConfiguration('connascence');
            await config.update('safetyProfile', profileChoice.value, vscode.ConfigurationTarget.Global);
        }

        // Step 2: Enable real-time analysis
        const realtimeChoice = await vscode.window.showQuickPick([
            { label: 'Yes', description: 'Analyze files as you type', value: true },
            { label: 'No', description: 'Manual analysis only', value: false }
        ], {
            placeHolder: 'Enable real-time analysis?'
        });

        if (realtimeChoice) {
            const config = vscode.workspace.getConfiguration('connascence');
            await config.update('realtimeAnalysis', realtimeChoice.value, vscode.ConfigurationTarget.Global);
        }

        // Step 3: Run first analysis
        const analyzeChoice = await vscode.window.showQuickPick([
            { label: 'Analyze current file', value: 'file' },
            { label: 'Analyze entire workspace', value: 'workspace' },
            { label: 'Skip for now', value: 'skip' }
        ], {
            placeHolder: 'Run your first analysis?'
        });

        if (analyzeChoice?.value === 'file') {
            await vscode.commands.executeCommand('connascence.analyzeFile');
        } else if (analyzeChoice?.value === 'workspace') {
            await vscode.commands.executeCommand('connascence.analyzeWorkspace');
        }

        vscode.window.showInformationMessage('Quick start complete! Check the Problems panel for results.');
    }

    /**
     * Get HTML content for webview
     */
    private getHtmlContent(webview: vscode.Webview): string {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; script-src ${webview.cspSource} 'unsafe-inline';">
    <title>Welcome to Connascence Analyzer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: var(--vscode-font-family);
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
            padding: 30px;
            line-height: 1.6;
        }
        .container { max-width: 900px; margin: 0 auto; }
        h1 { font-size: 32px; margin-bottom: 10px; color: var(--vscode-textLink-foreground); }
        h2 { font-size: 24px; margin: 30px 0 15px; color: var(--vscode-textLink-foreground); }
        h3 { font-size: 18px; margin: 20px 0 10px; }
        p { margin-bottom: 15px; }
        .hero {
            background: var(--vscode-editor-selectionBackground);
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
        }
        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .card {
            background: var(--vscode-editor-inactiveSelectionBackground);
            padding: 20px;
            border-radius: 6px;
            border: 1px solid var(--vscode-panel-border);
        }
        .card h3 { margin-top: 0; }
        button {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin-right: 10px;
            margin-top: 10px;
        }
        button:hover {
            background: var(--vscode-button-hoverBackground);
        }
        button.secondary {
            background: var(--vscode-button-secondaryBackground);
            color: var(--vscode-button-secondaryForeground);
        }
        button.secondary:hover {
            background: var(--vscode-button-secondaryHoverBackground);
        }
        .quick-actions {
            display: flex;
            gap: 10px;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        .profile-selector {
            display: flex;
            gap: 10px;
            margin: 20px 0;
        }
        .profile-button {
            flex: 1;
            padding: 15px;
            background: var(--vscode-editor-inactiveSelectionBackground);
            border: 2px solid var(--vscode-panel-border);
            border-radius: 6px;
            cursor: pointer;
            text-align: center;
        }
        .profile-button:hover {
            border-color: var(--vscode-textLink-foreground);
        }
        .profile-button.active {
            border-color: var(--vscode-textLink-activeForeground);
            background: var(--vscode-editor-selectionBackground);
        }
        .feature-list {
            list-style: none;
            padding: 0;
        }
        .feature-list li {
            padding: 10px 0;
            border-bottom: 1px solid var(--vscode-panel-border);
        }
        .feature-list li:before {
            content: "✓ ";
            color: var(--vscode-textLink-foreground);
            font-weight: bold;
            margin-right: 10px;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid var(--vscode-panel-border);
            text-align: center;
            color: var(--vscode-descriptionForeground);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <h1>🔍 Welcome to Connascence Safety Analyzer</h1>
            <p>Analyze and improve code quality through connascence detection. Find implicit dependencies, reduce coupling, and build more maintainable software.</p>
        </div>

        <h2>Quick Start</h2>
        <div class="quick-actions">
            <button onclick="runQuickStart()">🚀 Run Quick Start Wizard</button>
            <button onclick="analyzeFile()">📄 Analyze Current File</button>
            <button onclick="analyzeWorkspace()">📁 Analyze Workspace</button>
            <button class="secondary" onclick="openSettings()">⚙️ Open Settings</button>
        </div>

        <h2>Choose Your Safety Profile</h2>
        <div class="profile-selector">
            <div class="profile-button" onclick="setProfile('strict')">
                <h3>Strict</h3>
                <p>Maximum safety</p>
            </div>
            <div class="profile-button" onclick="setProfile('standard')">
                <h3>Standard</h3>
                <p>Recommended</p>
            </div>
            <div class="profile-button" onclick="setProfile('lenient')">
                <h3>Lenient</h3>
                <p>Critical only</p>
            </div>
        </div>

        <h2>Key Features</h2>
        <div class="cards">
            <div class="card">
                <h3>Real-time Analysis</h3>
                <p>Get instant feedback as you code with intelligent caching and debouncing.</p>
            </div>
            <div class="card">
                <h3>MCP Integration</h3>
                <p>High-performance analysis with graceful CLI fallback.</p>
            </div>
            <div class="card">
                <h3>Smart Suggestions</h3>
                <p>Automated refactoring suggestions to reduce coupling.</p>
            </div>
            <div class="card">
                <h3>Quality Metrics</h3>
                <p>Track code quality trends and improvement over time.</p>
            </div>
        </div>

        <h2>What's Included</h2>
        <ul class="feature-list">
            <li>9 types of connascence detection (CoP, CoN, CoT, CoM, CoA, CoE, CoI, CoV, CoId)</li>
            <li>NASA Power of 10 compliance checking</li>
            <li>MECE (Mutually Exclusive, Collectively Exhaustive) analysis</li>
            <li>Intelligent caching for fast re-analysis</li>
            <li>Comprehensive diagnostics in Problems panel</li>
            <li>CodeLens annotations showing issue counts</li>
            <li>Quick fixes and refactoring suggestions</li>
        </ul>

        <h2>Resources</h2>
        <div class="quick-actions">
            <button onclick="viewDocs()">📚 Documentation</button>
            <button class="secondary" onclick="enableMCP()">🔌 Enable MCP</button>
            <button class="secondary" onclick="dontShowAgain()">✕ Don't Show Again</button>
        </div>

        <div class="footer">
            <p>Connascence Safety Analyzer v2.0.2</p>
            <p>Built with ❤️ for better software</p>
        </div>
    </div>

    <script>
        const vscode = acquireVsCodeApi();

        function runQuickStart() {
            vscode.postMessage({ command: 'runQuickStart' });
        }

        function analyzeFile() {
            vscode.postMessage({ command: 'analyzeCurrentFile' });
        }

        function analyzeWorkspace() {
            vscode.postMessage({ command: 'analyzeWorkspace' });
        }

        function openSettings() {
            vscode.postMessage({ command: 'openSettings' });
        }

        function viewDocs() {
            vscode.postMessage({ command: 'viewDocs' });
        }

        function setProfile(profile) {
            vscode.postMessage({ command: 'setSafetyProfile', value: profile });
            document.querySelectorAll('.profile-button').forEach(btn => btn.classList.remove('active'));
            event.target.closest('.profile-button').classList.add('active');
        }

        function enableMCP() {
            vscode.postMessage({ command: 'enableMCP' });
        }

        function dontShowAgain() {
            vscode.postMessage({ command: 'dontShowAgain' });
        }
    </script>
</body>
</html>`;
    }

    /**
     * Check if welcome screen should be shown automatically
     */
    public static shouldShowWelcome(context: vscode.ExtensionContext): boolean {
        const hasShown = context.globalState.get<boolean>('welcomeScreenShown', false);
        return !hasShown;
    }

    /**
     * Show welcome screen on first activation
     */
    public static showOnFirstActivation(context: vscode.ExtensionContext): void {
        if (WelcomeScreen.shouldShowWelcome(context)) {
            const welcome = new WelcomeScreen(context);
            welcome.show();
        }
    }
}
