import * as vscode from 'vscode';
import { ConfigurationService } from './configurationService';
import { ExtensionLogger } from '../utils/logger';

/**
 * Comprehensive Help Documentation System
 * 
 * Provides contextual help, tutorials, and documentation for all Connascence features
 * Includes quick start guides, violation explanations, and best practices
 */
export class HelpProvider implements vscode.Disposable {
    private disposables: vscode.Disposable[] = [];
    private helpPanel: vscode.WebviewPanel | undefined;

    constructor(
        private context: vscode.ExtensionContext,
        private configService: ConfigurationService,
        private logger: ExtensionLogger
    ) {
        this.registerCommands();
    }

    /**
     * Show main help documentation
     */
    public showHelp(): void {
        if (this.helpPanel) {
            this.helpPanel.reveal();
            return;
        }

        this.createHelpPanel();
        this.updateHelpContent('overview');
    }

    /**
     * Show help for specific topic
     */
    public showTopicHelp(topic: string): void {
        if (!this.helpPanel) {
            this.createHelpPanel();
        }
        
        this.updateHelpContent(topic);
        this.helpPanel?.reveal();
    }

    /**
     * Show quick start guide
     */
    public showQuickStart(): void {
        this.showTopicHelp('quickstart');
    }

    /**
     * Show violation-specific help
     */
    public showViolationHelp(violationType: string): void {
        this.showTopicHelp(`violations/${violationType}`);
    }

    // === PRIVATE METHODS ===

    private registerCommands(): void {
        this.disposables.push(
            vscode.commands.registerCommand('connascence.showHelp', () => {
                this.showHelp();
            })
        );

        this.disposables.push(
            vscode.commands.registerCommand('connascence.showQuickStart', () => {
                this.showQuickStart();
            })
        );

        this.disposables.push(
            vscode.commands.registerCommand('connascence.showViolationHelp', (args) => {
                const violationType = args?.type || 'overview';
                this.showViolationHelp(violationType);
            })
        );

        this.disposables.push(
            vscode.commands.registerCommand('connascence.showAIHelp', () => {
                this.showTopicHelp('ai-features');
            })
        );

        this.disposables.push(
            vscode.commands.registerCommand('connascence.showSettings', () => {
                this.showTopicHelp('configuration');
            })
        );
    }

    private createHelpPanel(): void {
        this.helpPanel = vscode.window.createWebviewPanel(
            'connascenceHelp',
            '📚 Connascence Help & Documentation',
            vscode.ViewColumn.Two,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
                localResourceRoots: [
                    vscode.Uri.joinPath(this.context.extensionUri, 'resources')
                ]
            }
        );

        this.helpPanel.iconPath = {
            light: vscode.Uri.joinPath(this.context.extensionUri, 'resources', 'help-light.svg'),
            dark: vscode.Uri.joinPath(this.context.extensionUri, 'resources', 'help-dark.svg')
        };

        this.helpPanel.onDidDispose(() => {
            this.helpPanel = undefined;
        });

        // Handle webview messages
        this.helpPanel.webview.onDidReceiveMessage(message => {
            switch (message.type) {
                case 'navigateTo':
                    this.updateHelpContent(message.topic);
                    break;
                case 'openSettings':
                    vscode.commands.executeCommand('workbench.action.openSettings', 'connascence');
                    break;
                case 'runCommand':
                    vscode.commands.executeCommand(message.command, message.args);
                    break;
            }
        });
    }

    private updateHelpContent(topic: string): void {
        if (!this.helpPanel) return;

        const content = this.generateHelpContent(topic);
        this.helpPanel.webview.html = content;
    }

    private generateHelpContent(topic: string): string {
        const theme = vscode.window.activeColorTheme.kind === vscode.ColorThemeKind.Dark ? 'dark' : 'light';
        
        return `<!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Connascence Help</title>
            <style>
                body {
                    font-family: var(--vscode-font-family);
                    color: var(--vscode-foreground);
                    background: var(--vscode-editor-background);
                    margin: 0; padding: 0; line-height: 1.6;
                }
                .container { max-width: 1000px; margin: 0 auto; display: flex; min-height: 100vh; }
                
                /* Navigation Sidebar */
                .nav-sidebar {
                    width: 250px; background: var(--vscode-sideBar-background);
                    border-right: 1px solid var(--vscode-panel-border);
                    padding: 20px; overflow-y: auto;
                }
                .nav-title { font-size: 18px; font-weight: bold; margin-bottom: 20px; color: var(--vscode-foreground); }
                .nav-section { margin-bottom: 20px; }
                .nav-section-title { 
                    font-size: 14px; font-weight: bold; margin-bottom: 10px; 
                    color: var(--vscode-descriptionForeground); text-transform: uppercase;
                }
                .nav-item {
                    display: block; padding: 8px 12px; margin: 2px 0; border-radius: 4px;
                    color: var(--vscode-foreground); text-decoration: none; cursor: pointer;
                    transition: background-color 0.2s;
                }
                .nav-item:hover { background: var(--vscode-list-hoverBackground); }
                .nav-item.active { background: var(--vscode-list-activeSelectionBackground); }
                
                /* Main Content */
                .main-content { flex: 1; padding: 30px; overflow-y: auto; }
                .content-header { 
                    display: flex; justify-content: between; align-items: center;
                    margin-bottom: 30px; padding-bottom: 20px; 
                    border-bottom: 1px solid var(--vscode-panel-border);
                }
                .content-title { font-size: 28px; font-weight: bold; margin: 0; }
                .breadcrumb { color: var(--vscode-descriptionForeground); font-size: 14px; }
                
                /* Content Styling */
                h1, h2, h3, h4 { color: var(--vscode-foreground); }
                h1 { font-size: 24px; margin: 30px 0 15px 0; }
                h2 { font-size: 20px; margin: 25px 0 12px 0; }
                h3 { font-size: 16px; margin: 20px 0 10px 0; }
                
                p { margin: 15px 0; }
                ul, ol { margin: 15px 0; padding-left: 25px; }
                li { margin: 8px 0; }
                
                .callout {
                    background: var(--vscode-textBlockQuote-background);
                    border-left: 4px solid var(--vscode-textBlockQuote-border);
                    padding: 15px 20px; margin: 20px 0; border-radius: 0 4px 4px 0;
                }
                .callout.info { border-left-color: #007acc; }
                .callout.warning { border-left-color: #ff8c00; }
                .callout.error { border-left-color: #f14c4c; }
                .callout.success { border-left-color: #73c991; }
                
                .code-block {
                    background: var(--vscode-textPreformat-background);
                    border: 1px solid var(--vscode-panel-border);
                    border-radius: 4px; padding: 15px; margin: 15px 0;
                    overflow-x: auto; font-family: var(--vscode-editor-font-family);
                }
                
                .action-buttons { margin: 20px 0; display: flex; gap: 10px; flex-wrap: wrap; }
                .btn {
                    background: var(--vscode-button-background); color: var(--vscode-button-foreground);
                    border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;
                    font-family: var(--vscode-font-family); text-decoration: none; display: inline-block;
                }
                .btn:hover { background: var(--vscode-button-hoverBackground); }
                .btn-secondary {
                    background: var(--vscode-button-secondaryBackground);
                    color: var(--vscode-button-secondaryForeground);
                }
                .btn-secondary:hover { background: var(--vscode-button-secondaryHoverBackground); }
                
                .feature-grid {
                    display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px; margin: 30px 0;
                }
                .feature-card {
                    background: var(--vscode-editor-inactiveSelectionBackground);
                    border: 1px solid var(--vscode-panel-border); border-radius: 8px;
                    padding: 20px; cursor: pointer; transition: transform 0.2s;
                }
                .feature-card:hover { transform: translateY(-2px); }
                .feature-icon { font-size: 24px; margin-bottom: 10px; }
                .feature-title { font-size: 16px; font-weight: bold; margin-bottom: 8px; }
                .feature-desc { color: var(--vscode-descriptionForeground); font-size: 14px; }
                
                .violation-types { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }
                .violation-card {
                    background: var(--vscode-editor-inactiveSelectionBackground);
                    border: 1px solid var(--vscode-panel-border); border-radius: 6px;
                    padding: 15px; cursor: pointer;
                }
                .violation-card:hover { background: var(--vscode-list-hoverBackground); }
                .violation-name { font-weight: bold; margin-bottom: 5px; }
                .violation-severity { font-size: 12px; padding: 2px 6px; border-radius: 3px; }
                .severity-critical { background: #f14c4c; color: white; }
                .severity-major { background: #ff8c00; color: white; }
                .severity-minor { background: #007acc; color: white; }
                
                @media (max-width: 768px) {
                    .container { flex-direction: column; }
                    .nav-sidebar { width: 100%; height: auto; border-right: none; border-bottom: 1px solid var(--vscode-panel-border); }
                    .violation-types { grid-template-columns: 1fr; }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="nav-sidebar">
                    <div class="nav-title">📚 Help Topics</div>
                    
                    <div class="nav-section">
                        <div class="nav-section-title">Getting Started</div>
                        <a class="nav-item ${topic === 'overview' ? 'active' : ''}" onclick="navigateTo('overview')">📖 Overview</a>
                        <a class="nav-item ${topic === 'quickstart' ? 'active' : ''}" onclick="navigateTo('quickstart')">🚀 Quick Start</a>
                        <a class="nav-item ${topic === 'installation' ? 'active' : ''}" onclick="navigateTo('installation')">⚙️ Installation</a>
                    </div>
                    
                    <div class="nav-section">
                        <div class="nav-section-title">Core Features</div>
                        <a class="nav-item ${topic === 'analysis' ? 'active' : ''}" onclick="navigateTo('analysis')">🔍 Code Analysis</a>
                        <a class="nav-item ${topic === 'violations' ? 'active' : ''}" onclick="navigateTo('violations')">⚠️ Violation Types</a>
                        <a class="nav-item ${topic === 'ai-features' ? 'active' : ''}" onclick="navigateTo('ai-features')">🤖 AI Features</a>
                        <a class="nav-item ${topic === 'dashboard' ? 'active' : ''}" onclick="navigateTo('dashboard')">📊 Dashboard</a>
                    </div>
                    
                    <div class="nav-section">
                        <div class="nav-section-title">Configuration</div>
                        <a class="nav-item ${topic === 'configuration' ? 'active' : ''}" onclick="navigateTo('configuration')">⚙️ Settings</a>
                        <a class="nav-item ${topic === 'commands' ? 'active' : ''}" onclick="navigateTo('commands')">📋 Commands</a>
                        <a class="nav-item ${topic === 'keybindings' ? 'active' : ''}" onclick="navigateTo('keybindings')">⌨️ Keybindings</a>
                    </div>
                    
                    <div class="nav-section">
                        <div class="nav-section-title">Advanced</div>
                        <a class="nav-item ${topic === 'theory' ? 'active' : ''}" onclick="navigateTo('theory')">🎓 Theory</a>
                        <a class="nav-item ${topic === 'best-practices' ? 'active' : ''}" onclick="navigateTo('best-practices')">✨ Best Practices</a>
                        <a class="nav-item ${topic === 'troubleshooting' ? 'active' : ''}" onclick="navigateTo('troubleshooting')">🔧 Troubleshooting</a>
                    </div>
                </div>
                
                <div class="main-content">
                    ${this.generateTopicContent(topic)}
                </div>
            </div>
            
            <script>
                const vscode = acquireVsCodeApi();
                
                function navigateTo(topic) {
                    vscode.postMessage({ type: 'navigateTo', topic: topic });
                }
                
                function openSettings() {
                    vscode.postMessage({ type: 'openSettings' });
                }
                
                function runCommand(command, args) {
                    vscode.postMessage({ type: 'runCommand', command, args });
                }
            </script>
        </body>
        </html>`;
    }

    private generateTopicContent(topic: string): string {
        switch (topic) {
            case 'overview':
                return this.generateOverviewContent();
            case 'quickstart':
                return this.generateQuickStartContent();
            case 'installation':
                return this.generateInstallationContent();
            case 'analysis':
                return this.generateAnalysisContent();
            case 'violations':
                return this.generateViolationsContent();
            case 'ai-features':
                return this.generateAIFeaturesContent();
            case 'dashboard':
                return this.generateDashboardContent();
            case 'configuration':
                return this.generateConfigurationContent();
            case 'commands':
                return this.generateCommandsContent();
            case 'keybindings':
                return this.generateKeybindingsContent();
            case 'theory':
                return this.generateTheoryContent();
            case 'best-practices':
                return this.generateBestPracticesContent();
            case 'troubleshooting':
                return this.generateTroubleshootingContent();
            default:
                return this.generateOverviewContent();
        }
    }

    private generateOverviewContent(): string {
        return `
            <div class="content-header">
                <div class="content-title">🔗 Connascence Extension Overview</div>
            </div>
            
            <p>The Connascence extension for VS Code helps you identify and fix coupling issues in your code, making it more maintainable and testable.</p>
            
            <div class="callout info">
                <strong>💡 What is Connascence?</strong><br>
                Connascence is a metric for measuring coupling between software components. It provides a more nuanced view of code dependencies than traditional coupling metrics.
            </div>
            
            <h2>Key Features</h2>
            <div class="feature-grid">
                <div class="feature-card" onclick="navigateTo('analysis')">
                    <div class="feature-icon">🔍</div>
                    <div class="feature-title">Real-time Analysis</div>
                    <div class="feature-desc">Automatically detects 9 types of connascence violations as you code</div>
                </div>
                
                <div class="feature-card" onclick="navigateTo('ai-features')">
                    <div class="feature-icon">🤖</div>
                    <div class="feature-title">AI-Powered Fixes</div>
                    <div class="feature-desc">Get intelligent refactoring suggestions with confidence scores</div>
                </div>
                
                <div class="feature-card" onclick="navigateTo('dashboard')">
                    <div class="feature-icon">📊</div>
                    <div class="feature-title">Visual Dashboard</div>
                    <div class="feature-desc">Track code quality metrics and violation trends</div>
                </div>
                
                <div class="feature-card" onclick="navigateTo('violations')">
                    <div class="feature-icon">⚠️</div>
                    <div class="feature-title">Violation Detection</div>
                    <div class="feature-desc">Comprehensive detection of coupling anti-patterns</div>
                </div>
            </div>
            
            <h2>Getting Started</h2>
            <div class="action-buttons">
                <button class="btn" onclick="navigateTo('quickstart')">🚀 Quick Start Guide</button>
                <button class="btn btn-secondary" onclick="navigateTo('installation')">⚙️ Installation Help</button>
                <button class="btn btn-secondary" onclick="runCommand('connascence.showDashboard')">📊 Open Dashboard</button>
            </div>
            
            <h2>Support & Resources</h2>
            <ul>
                <li><strong>Documentation:</strong> Complete guides and API reference</li>
                <li><strong>Examples:</strong> Real-world refactoring scenarios</li>
                <li><strong>Community:</strong> Join our Discord for help and discussions</li>
                <li><strong>Issues:</strong> Report bugs on our GitHub repository</li>
            </ul>
        `;
    }

    private generateQuickStartContent(): string {
        return `
            <div class="content-header">
                <div class="content-title">🚀 Quick Start Guide</div>
                <div class="breadcrumb">Getting Started > Quick Start</div>
            </div>
            
            <p>Get up and running with the Connascence extension in just a few minutes!</p>
            
            <h2>Step 1: Enable Analysis</h2>
            <div class="callout info">
                The extension automatically analyzes your code when you open files. Look for colored underlines indicating violations.
            </div>
            
            <div class="action-buttons">
                <button class="btn" onclick="runCommand('connascence.analyzeWorkspace')">🔍 Analyze Current Workspace</button>
                <button class="btn btn-secondary" onclick="runCommand('connascence.showDashboard')">📊 Open Dashboard</button>
            </div>
            
            <h2>Step 2: Understand Violations</h2>
            <p>The extension detects 9 types of connascence violations, each with different severity levels:</p>
            
            <div class="violation-types">
                <div class="violation-card" onclick="navigateTo('violations/algorithm')">
                    <div class="violation-name">🏛️ God Objects</div>
                    <span class="violation-severity severity-critical">Critical</span>
                    <p>Large classes with too many responsibilities</p>
                </div>
                
                <div class="violation-card" onclick="navigateTo('violations/meaning')">
                    <div class="violation-name">✨ Magic Literals</div>
                    <span class="violation-severity severity-major">Major</span>
                    <p>Hardcoded values without clear meaning</p>
                </div>
                
                <div class="violation-card" onclick="navigateTo('violations/position')">
                    <div class="violation-name">🔗 Parameter Coupling</div>
                    <span class="violation-severity severity-minor">Minor</span>
                    <p>Methods with too many positional parameters</p>
                </div>
                
                <div class="violation-card" onclick="navigateTo('violations')">
                    <div class="violation-name">📋 View All Types</div>
                    <span class="violation-severity severity-minor">Info</span>
                    <p>See complete list of violation types</p>
                </div>
            </div>
            
            <h2>Step 3: Get AI-Powered Help</h2>
            <p>Hover over any violation to see:</p>
            <ul>
                <li><strong>Explanation:</strong> What the violation means and why it matters</li>
                <li><strong>AI Suggestions:</strong> Specific refactoring recommendations with confidence scores</li>
                <li><strong>Quick Actions:</strong> One-click fixes for common issues</li>
            </ul>
            
            <div class="code-block">
// Example: Hover over this magic literal for AI suggestions
const timeout = 5000; // ← Hover here!
            </div>
            
            <h2>Step 4: Use the Dashboard</h2>
            <p>The dashboard provides a comprehensive view of your code quality:</p>
            <ul>
                <li>📊 Quality score and trends</li>
                <li>📈 Violation breakdown by type and severity</li>
                <li>🤖 AI chat assistant for interactive help</li>
                <li>📝 Detailed analysis reports</li>
            </ul>
            
            <div class="action-buttons">
                <button class="btn" onclick="runCommand('connascence.showDashboard')">📊 Open Dashboard Now</button>
            </div>
            
            <div class="callout success">
                <strong>🎉 Pro Tip:</strong> Start by fixing Critical violations first - they have the highest impact on code maintainability!
            </div>
            
            <h2>Next Steps</h2>
            <div class="action-buttons">
                <button class="btn btn-secondary" onclick="navigateTo('configuration')">⚙️ Configure Settings</button>
                <button class="btn btn-secondary" onclick="navigateTo('ai-features')">🤖 Explore AI Features</button>
                <button class="btn btn-secondary" onclick="navigateTo('theory')">🎓 Learn Theory</button>
            </div>
        `;
    }

    private generateInstallationContent(): string {
        return `
            <div class="content-header">
                <div class="content-title">⚙️ Installation & Setup</div>
                <div class="breadcrumb">Getting Started > Installation</div>
            </div>
            
            <h2>Prerequisites</h2>
            <ul>
                <li><strong>VS Code:</strong> Version 1.80.0 or higher</li>
                <li><strong>Node.js:</strong> Version 16.0 or higher (for MCP features)</li>
                <li><strong>Supported Languages:</strong> Python, JavaScript, TypeScript, C/C++</li>
            </ul>
            
            <h2>Installation Methods</h2>
            
            <h3>Method 1: VS Code Marketplace</h3>
            <ol>
                <li>Open VS Code</li>
                <li>Go to Extensions (Ctrl+Shift+X)</li>
                <li>Search for "Connascence"</li>
                <li>Click "Install"</li>
            </ol>
            
            <h3>Method 2: Command Line</h3>
            <div class="code-block">
code --install-extension connascence.connascence-analyzer
            </div>
            
            <h3>Method 3: VSIX Package</h3>
            <p>Download the VSIX file and install manually:</p>
            <div class="code-block">
code --install-extension connascence-analyzer.vsix
            </div>
            
            <h2>Post-Installation Setup</h2>
            
            <h3>1. Verify Installation</h3>
            <p>Check that the extension is active:</p>
            <div class="action-buttons">
                <button class="btn" onclick="runCommand('connascence.showDashboard')">📊 Open Dashboard</button>
            </div>
            
            <h3>2. Configure Analysis</h3>
            <p>Customize the extension for your needs:</p>
            <div class="action-buttons">
                <button class="btn btn-secondary" onclick="openSettings()">⚙️ Open Settings</button>
            </div>
            
            <h3>3. Optional: MCP Server Setup</h3>
            <div class="callout warning">
                <strong>⚠️ Advanced Feature:</strong> MCP (Model Context Protocol) server enables advanced AI features. This is optional for basic usage.
            </div>
            
            <div class="code-block">
# Install MCP server dependencies
npm install -g @connascence/mcp-server

# Configure server URL in settings
"connascence.serverUrl": "http://localhost:8080"
            </div>
            
            <h2>Troubleshooting</h2>
            
            <h3>Extension Not Working?</h3>
            <ul>
                <li>Check VS Code version compatibility</li>
                <li>Restart VS Code after installation</li>
                <li>Ensure supported file types are open</li>
                <li>Check the Output panel for error messages</li>
            </ul>
            
            <h3>No Violations Detected?</h3>
            <ul>
                <li>Verify file language is supported</li>
                <li>Check that analysis is enabled in settings</li>
                <li>Try opening a different file</li>
                <li>Manually trigger analysis</li>
            </ul>
            
            <div class="action-buttons">
                <button class="btn btn-secondary" onclick="navigateTo('troubleshooting')">🔧 More Troubleshooting</button>
            </div>
            
            <h2>Verification Checklist</h2>
            <ul>
                <li>✅ Extension shows in Extensions list</li>
                <li>✅ Status bar shows connascence information</li>
                <li>✅ Dashboard opens successfully</li>
                <li>✅ Violations appear with colored underlines</li>
                <li>✅ Hover tooltips show violation details</li>
            </ul>
        `;
    }

    private generateViolationsContent(): string {
        return `
            <div class="content-header">
                <div class="content-title">⚠️ Connascence Violation Types</div>
                <div class="breadcrumb">Core Features > Violation Types</div>
            </div>
            
            <p>The extension detects 9 types of connascence violations, organized by strength and impact:</p>
            
            <div class="callout info">
                <strong>💡 Connascence Hierarchy:</strong> Violations are ranked from strongest (worst) to weakest (best). Focus on fixing stronger forms first.
            </div>
            
            <h2>Dynamic Connascence (Strongest - Fix First!)</h2>
            
            <div class="violation-card" style="margin: 10px 0;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 24px;">🆔</span>
                    <div>
                        <div class="violation-name">Connascence of Identity (CoI)</div>
                        <span class="violation-severity severity-critical">Critical</span>
                        <p><strong>Problem:</strong> Multiple components must reference the exact same object</p>
                        <p><strong>Example:</strong> Shared mutable state, singleton abuse</p>
                        <p><strong>Fix:</strong> Use immutable data, dependency injection</p>
                    </div>
                </div>
            </div>
            
            <div class="violation-card" style="margin: 10px 0;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 24px;">💎</span>
                    <div>
                        <div class="violation-name">Connascence of Value (CoV)</div>
                        <span class="violation-severity severity-critical">Critical</span>
                        <p><strong>Problem:</strong> Multiple components must agree on specific values</p>
                        <p><strong>Example:</strong> Hardcoded constants, magic numbers</p>
                        <p><strong>Fix:</strong> Extract constants, configuration files</p>
                    </div>
                </div>
            </div>
            
            <div class="violation-card" style="margin: 10px 0;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 24px;">⏰</span>
                    <div>
                        <div class="violation-name">Connascence of Timing (CoTi)</div>
                        <span class="violation-severity severity-critical">Critical</span>
                        <p><strong>Problem:</strong> Components must execute at specific times relative to each other</p>
                        <p><strong>Example:</strong> Race conditions, initialization order dependencies</p>
                        <p><strong>Fix:</strong> Event-driven architecture, dependency injection</p>
                    </div>
                </div>
            </div>
            
            <div class="violation-card" style="margin: 10px 0;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 24px;">📝</span>
                    <div>
                        <div class="violation-name">Connascence of Execution (CoE)</div>
                        <span class="violation-severity severity-major">Major</span>
                        <p><strong>Problem:</strong> Order of execution matters for correctness</p>
                        <p><strong>Example:</strong> Method call order dependencies</p>
                        <p><strong>Fix:</strong> Fluent interfaces, state machines</p>
                    </div>
                </div>
            </div>
            
            <h2>Static Connascence (Weaker - Still Important)</h2>
            
            <div class="violation-card" style="margin: 10px 0;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 24px;">🏛️</span>
                    <div>
                        <div class="violation-name">Connascence of Algorithm (CoA)</div>
                        <span class="violation-severity severity-major">Major</span>
                        <p><strong>Problem:</strong> Multiple components must use the same algorithm (God Objects)</p>
                        <p><strong>Example:</strong> Large classes with multiple responsibilities</p>
                        <p><strong>Fix:</strong> Extract methods/classes, Single Responsibility Principle</p>
                    </div>
                </div>
            </div>
            
            <div class="violation-card" style="margin: 10px 0;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 24px;">✨</span>
                    <div>
                        <div class="violation-name">Connascence of Meaning (CoM)</div>
                        <span class="violation-severity severity-major">Major</span>
                        <p><strong>Problem:</strong> Multiple components must agree on meaning of values</p>
                        <p><strong>Example:</strong> Magic literals, undefined constants</p>
                        <p><strong>Fix:</strong> Named constants, enums, configuration</p>
                    </div>
                </div>
            </div>
            
            <div class="violation-card" style="margin: 10px 0;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 24px;">🔗</span>
                    <div>
                        <div class="violation-name">Connascence of Position (CoP)</div>
                        <span class="violation-severity severity-minor">Minor</span>
                        <p><strong>Problem:</strong> Multiple components must agree on order of values</p>
                        <p><strong>Example:</strong> Long parameter lists, positional arguments</p>
                        <p><strong>Fix:</strong> Named parameters, parameter objects, builder pattern</p>
                    </div>
                </div>
            </div>
            
            <div class="violation-card" style="margin: 10px 0;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 24px;">🏷️</span>
                    <div>
                        <div class="violation-name">Connascence of Type (CoT)</div>
                        <span class="violation-severity severity-minor">Minor</span>
                        <p><strong>Problem:</strong> Multiple components must agree on data types</p>
                        <p><strong>Example:</strong> Type coupling, primitive obsession</p>
                        <p><strong>Fix:</strong> Interfaces, abstract types, generics</p>
                    </div>
                </div>
            </div>
            
            <div class="violation-card" style="margin: 10px 0;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 24px;">📛</span>
                    <div>
                        <div class="violation-name">Connascence of Name (CoN)</div>
                        <span class="violation-severity severity-minor">Minor</span>
                        <p><strong>Problem:</strong> Multiple components must agree on names</p>
                        <p><strong>Example:</strong> Method/variable naming inconsistencies</p>
                        <p><strong>Fix:</strong> Consistent naming conventions, refactoring tools</p>
                    </div>
                </div>
            </div>
            
            <h2>Refactoring Priority</h2>
            <div class="callout success">
                <strong>🎯 Golden Rules:</strong>
                <ol>
                    <li><strong>Minimize overall connascence</strong> - Fewer dependencies = better design</li>
                    <li><strong>Prefer static over dynamic</strong> - Static violations are easier to detect and fix</li>
                    <li><strong>Convert stronger to weaker</strong> - Transform dynamic violations to static ones</li>
                </ol>
            </div>
            
            <div class="action-buttons">
                <button class="btn" onclick="navigateTo('best-practices')">✨ Best Practices</button>
                <button class="btn btn-secondary" onclick="navigateTo('ai-features')">🤖 AI-Powered Fixes</button>
                <button class="btn btn-secondary" onclick="navigateTo('theory')">🎓 Deep Dive Theory</button>
            </div>
        `;
    }

    private generateAIFeaturesContent(): string {
        return `
            <div class="content-header">
                <div class="content-title">🤖 AI-Powered Features</div>
                <div class="breadcrumb">Core Features > AI Features</div>
            </div>
            
            <p>The extension includes advanced AI capabilities to help you understand and fix connascence violations intelligently.</p>
            
            <div class="callout info">
                <strong>💡 Smart Analysis:</strong> Our AI understands your specific code context and provides tailored refactoring suggestions.
            </div>
            
            <h2>AI Hover Assistance</h2>
            <p>Hover over any violation to get:</p>
            
            <div class="feature-card" style="margin: 15px 0;">
                <div class="feature-icon">🎯</div>
                <div class="feature-title">Contextual Explanations</div>
                <div class="feature-desc">Understand why the violation matters and its impact on your codebase</div>
            </div>
            
            <div class="feature-card" style="margin: 15px 0;">
                <div class="feature-icon">🔧</div>
                <div class="feature-title">Refactoring Suggestions</div>
                <div class="feature-desc">Get specific techniques with confidence scores (🟢 80%+ 🟡 60-80% 🔴 &lt;60%)</div>
            </div>
            
            <div class="feature-card" style="margin: 15px 0;">
                <div class="feature-icon">⚡</div>
                <div class="feature-title">One-Click Fixes</div>
                <div class="feature-desc">Apply AI-generated fixes directly from hover tooltips</div>
            </div>
            
            <h2>AI Chat Assistant</h2>
            <p>The dashboard includes an interactive AI assistant that can:</p>
            
            <ul>
                <li><strong>Analyze your violations:</strong> "What are my critical violations?"</li>
                <li><strong>Provide refactoring guidance:</strong> "How do I fix magic literals?"</li>
                <li><strong>Explain theory:</strong> "Tell me about connascence hierarchy"</li>
                <li><strong>Suggest priorities:</strong> "What should I fix first?"</li>
            </ul>
            
            <div class="code-block">
💬 Try these chat prompts:
• "Explain the critical violations"
• "Show me refactoring priorities"  
• "How can I fix God Objects?"
• "What are the top 3 improvements I can make?"
            </div>
            
            <div class="action-buttons">
                <button class="btn" onclick="runCommand('connascence.showDashboard')">💬 Open AI Chat</button>
            </div>
            
            <h2>AI-Powered Commands</h2>
            
            <h3>Intelligent Fix Generation</h3>
            <p>Generate context-aware fixes with confidence scoring:</p>
            <div class="action-buttons">
                <button class="btn btn-secondary" onclick="runCommand('connascence.requestAIFix')">🔧 Generate AI Fix</button>
            </div>
            
            <h3>Smart Suggestions</h3>
            <p>Get multiple refactoring approaches ranked by effectiveness:</p>
            <div class="action-buttons">
                <button class="btn btn-secondary" onclick="runCommand('connascence.getAISuggestions')">💡 Get AI Suggestions</button>
            </div>
            
            <h3>Batch Processing</h3>
            <p>Process multiple violations simultaneously:</p>
            <div class="action-buttons">
                <button class="btn btn-secondary" onclick="runCommand('connascence.batchAIFix')">⚡ Batch Fix</button>
            </div>
            
            <h2>Diff Preview System</h2>
            <p>Before applying any AI-generated fix, you can:</p>
            <ul>
                <li>👀 <strong>Preview changes</strong> in VS Code's native diff editor</li>
                <li>✅ <strong>Accept or reject</strong> fixes with confidence</li>
                <li>↩️ <strong>Undo changes</strong> easily with full history tracking</li>
                <li>📝 <strong>Review explanations</strong> for each suggested change</li>
            </ul>
            
            <h2>AI Configuration</h2>
            
            <h3>Basic Settings</h3>
            <div class="code-block">
{
  "connascence.aiIntegration": true,
  "connascence.ai.cacheSize": 100,
  "connascence.ai.cacheTTL": 300000
}
            </div>
            
            <h3>MCP Server (Advanced)</h3>
            <div class="callout warning">
                <strong>🔧 Optional:</strong> For enhanced AI capabilities, configure an MCP server. This enables more sophisticated analysis and fixes.
            </div>
            
            <div class="code-block">
{
  "connascence.serverUrl": "http://localhost:8080",
  "connascence.authenticateWithServer": false
}
            </div>
            
            <div class="action-buttons">
                <button class="btn btn-secondary" onclick="openSettings()">⚙️ Configure AI Settings</button>
            </div>
            
            <h2>AI Performance</h2>
            <p>The AI system includes smart caching for optimal performance:</p>
            <ul>
                <li>📊 <strong>Cache Statistics:</strong> Monitor hit rates and response times</li>
                <li>⚡ <strong>Fast Response:</strong> Cached results return in &lt;50ms</li>
                <li>🧠 <strong>Smart TTL:</strong> High-confidence fixes cached longer</li>
                <li>💾 <strong>Memory Optimization:</strong> Automatic cleanup and LRU eviction</li>
            </ul>
            
            <div class="action-buttons">
                <button class="btn btn-secondary" onclick="runCommand('connascence.showCacheStats')">📊 View Cache Stats</button>
            </div>
            
            <div class="callout success">
                <strong>🎉 Pro Tip:</strong> The AI learns from your codebase patterns and provides increasingly relevant suggestions over time!
            </div>
        `;
    }

    // Additional content generation methods...
    private generateDashboardContent(): string {
        return `<div class="content-header"><div class="content-title">📊 Dashboard Features</div></div><p>Dashboard documentation coming soon...</p>`;
    }

    private generateConfigurationContent(): string {
        return `<div class="content-header"><div class="content-title">⚙️ Configuration</div></div><p>Configuration documentation coming soon...</p>`;
    }

    private generateCommandsContent(): string {
        return `<div class="content-header"><div class="content-title">📋 Commands</div></div><p>Commands documentation coming soon...</p>`;
    }

    private generateKeybindingsContent(): string {
        return `<div class="content-header"><div class="content-title">⌨️ Keybindings</div></div><p>Keybindings documentation coming soon...</p>`;
    }

    private generateTheoryContent(): string {
        return `<div class="content-header"><div class="content-title">🎓 Connascence Theory</div></div><p>Theory documentation coming soon...</p>`;
    }

    private generateBestPracticesContent(): string {
        return `<div class="content-header"><div class="content-title">✨ Best Practices</div></div><p>Best practices documentation coming soon...</p>`;
    }

    private generateTroubleshootingContent(): string {
        return `<div class="content-header"><div class="content-title">🔧 Troubleshooting</div></div><p>Troubleshooting documentation coming soon...</p>`;
    }

    dispose(): void {
        this.helpPanel?.dispose();
        for (const disposable of this.disposables) {
            disposable.dispose();
        }
    }
}