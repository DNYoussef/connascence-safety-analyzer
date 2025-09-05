/**
 * Advanced Settings Panel for Connascence Safety Analyzer
 * Provides comprehensive configuration management interface
 */

import * as vscode from 'vscode';
import { ConfigurationService } from '../services/configurationService';
import { CustomAnalysisRule, PerformanceAnalysisConfig, AdvancedFilteringConfig } from '../types/index';

export class SettingsPanel {
    private readonly configService: ConfigurationService;
    private panel: vscode.WebviewPanel | undefined;

    constructor(configService: ConfigurationService) {
        this.configService = configService;
    }

    public async show(context: vscode.ExtensionContext): Promise<void> {
        if (this.panel) {
            this.panel.reveal();
            return;
        }

        this.panel = vscode.window.createWebviewPanel(
            'connascenceSettings',
            'Connascence Settings',
            vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
                localResourceRoots: [context.extensionUri]
            }
        );

        this.panel.webview.html = this.getSettingsHtml();
        this.setupMessageHandling();

        this.panel.onDidDispose(() => {
            this.panel = undefined;
        });

        // Send current configuration to the panel
        await this.sendConfigToPanel();
    }

    private setupMessageHandling(): void {
        if (!this.panel) return;

        this.panel.webview.onDidReceiveMessage(async (message) => {
            switch (message.type) {
                case 'getConfig':
                    await this.sendConfigToPanel();
                    break;
                case 'updateConfig':
                    await this.handleConfigUpdate(message.config);
                    break;
                case 'resetConfig':
                    await this.handleConfigReset();
                    break;
                case 'exportConfig':
                    await this.handleConfigExport();
                    break;
                case 'importConfig':
                    await this.handleConfigImport();
                    break;
                case 'validateRule':
                    await this.handleRuleValidation(message.rule);
                    break;
            }
        });
    }

    private async sendConfigToPanel(): Promise<void> {
        if (!this.panel) return;

        const config = this.configService.exportConfiguration();
        await this.panel.webview.postMessage({
            type: 'configData',
            config: config
        });
    }

    private async handleConfigUpdate(config: any): Promise<void> {
        try {
            // Update individual configuration items
            for (const [key, value] of Object.entries(config)) {
                switch (key) {
                    case 'safetyProfile':
                        if (this.configService.isValidSafetyProfile(value as string)) {
                            await this.configService.updateSafetyProfile(value as string);
                        }
                        break;
                    case 'frameworkProfile':
                        if (this.configService.isValidFrameworkProfile(value as string)) {
                            await this.configService.updateFrameworkProfile(value as string);
                        }
                        break;
                    case 'confidenceThreshold':
                        if (this.configService.isValidConfidenceThreshold(value as number)) {
                            await this.configService.updateConfidenceThreshold(value as number);
                        }
                        break;
                    case 'analysisDepth':
                        if (this.configService.isValidAnalysisDepth(value as string)) {
                            await this.configService.updateAnalysisDepth(value as string);
                        }
                        break;
                    case 'customRules':
                        await this.configService.updateCustomRules(value as CustomAnalysisRule[]);
                        break;
                    case 'excludePatterns':
                        await this.configService.updateExcludePatterns(value as string[]);
                        break;
                    case 'includePatterns':
                        await this.configService.updateIncludePatterns(value as string[]);
                        break;
                    case 'performanceAnalysis':
                        await this.configService.updatePerformanceAnalysis(value as PerformanceAnalysisConfig);
                        break;
                    case 'advancedFiltering':
                        await this.configService.updateAdvancedFiltering(value as AdvancedFilteringConfig);
                        break;
                    case 'enableExperimentalFeatures':
                        await this.configService.updateExperimentalFeatures(value as boolean);
                        break;
                    case 'nasaComplianceThreshold':
                        await this.configService.updateNasaComplianceThreshold(value as number);
                        break;
                    case 'meceQualityThreshold':
                        await this.configService.updateMeceQualityThreshold(value as number);
                        break;
                }
            }

            vscode.window.showInformationMessage('Configuration updated successfully');
            await this.sendConfigToPanel();
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to update configuration: ${error}`);
        }
    }

    private async handleConfigReset(): Promise<void> {
        const result = await vscode.window.showWarningMessage(
            'Are you sure you want to reset all settings to default values?',
            { modal: true },
            'Yes, Reset'
        );

        if (result === 'Yes, Reset') {
            try {
                await this.configService.resetToDefaults();
                vscode.window.showInformationMessage('Configuration reset to defaults');
                await this.sendConfigToPanel();
            } catch (error) {
                vscode.window.showErrorMessage(`Failed to reset configuration: ${error}`);
            }
        }
    }

    private async handleConfigExport(): Promise<void> {
        try {
            const config = this.configService.exportConfiguration();
            const configJson = JSON.stringify(config, null, 2);
            
            const uri = await vscode.window.showSaveDialog({
                filters: {
                    'JSON files': ['json']
                },
                defaultUri: vscode.Uri.file('connascence-config.json')
            });

            if (uri) {
                await vscode.workspace.fs.writeFile(uri, Buffer.from(configJson));
                vscode.window.showInformationMessage('Configuration exported successfully');
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to export configuration: ${error}`);
        }
    }

    private async handleConfigImport(): Promise<void> {
        try {
            const uris = await vscode.window.showOpenDialog({
                filters: {
                    'JSON files': ['json']
                },
                canSelectMany: false
            });

            if (uris && uris.length > 0) {
                const content = await vscode.workspace.fs.readFile(uris[0]);
                const configData = JSON.parse(content.toString());
                
                await this.configService.importConfiguration(configData);
                vscode.window.showInformationMessage('Configuration imported successfully');
                await this.sendConfigToPanel();
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to import configuration: ${error}`);
        }
    }

    private async handleRuleValidation(rule: CustomAnalysisRule): Promise<void> {
        if (!this.panel) return;

        const isValid = this.configService.validateCustomRule(rule);
        await this.panel.webview.postMessage({
            type: 'ruleValidation',
            isValid: isValid,
            rule: rule
        });
    }

    private getSettingsHtml(): string {
        return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connascence Settings</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
            padding: 20px;
            line-height: 1.5;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            border-bottom: 1px solid var(--vscode-panel-border);
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        
        .header h1 {
            margin: 0;
            color: var(--vscode-titleBar-activeForeground);
        }
        
        .section {
            margin-bottom: 30px;
            padding: 20px;
            border: 1px solid var(--vscode-panel-border);
            border-radius: 4px;
            background-color: var(--vscode-panel-background);
        }
        
        .section h2 {
            margin-top: 0;
            color: var(--vscode-titleBar-activeForeground);
            border-bottom: 1px solid var(--vscode-panel-border);
            padding-bottom: 10px;
        }
        
        .setting-group {
            margin-bottom: 20px;
        }
        
        .setting-label {
            display: block;
            font-weight: bold;
            margin-bottom: 5px;
            color: var(--vscode-input-foreground);
        }
        
        .setting-description {
            font-size: 0.9em;
            color: var(--vscode-descriptionForeground);
            margin-bottom: 8px;
        }
        
        input, select, textarea {
            width: 100%;
            max-width: 400px;
            padding: 8px;
            border: 1px solid var(--vscode-input-border);
            background-color: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            border-radius: 2px;
        }
        
        input[type="checkbox"] {
            width: auto;
            margin-right: 8px;
        }
        
        input[type="range"] {
            max-width: 300px;
        }
        
        .range-value {
            display: inline-block;
            margin-left: 10px;
            font-weight: bold;
            min-width: 50px;
        }
        
        .button-group {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid var(--vscode-panel-border);
        }
        
        button {
            padding: 10px 20px;
            margin-right: 10px;
            margin-bottom: 10px;
            border: none;
            border-radius: 2px;
            cursor: pointer;
            font-size: 14px;
            font-family: inherit;
        }
        
        .primary-button {
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
        }
        
        .primary-button:hover {
            background-color: var(--vscode-button-hoverBackground);
        }
        
        .secondary-button {
            background-color: var(--vscode-button-secondaryBackground);
            color: var(--vscode-button-secondaryForeground);
        }
        
        .danger-button {
            background-color: var(--vscode-errorBackground);
            color: var(--vscode-errorForeground);
        }
        
        .array-input {
            display: flex;
            flex-direction: column;
            gap: 5px;
        }
        
        .array-item {
            display: flex;
            gap: 5px;
            align-items: center;
        }
        
        .array-item input {
            flex: 1;
        }
        
        .remove-button {
            padding: 5px 10px;
            background-color: var(--vscode-errorBackground);
            color: var(--vscode-errorForeground);
            border: none;
            border-radius: 2px;
            cursor: pointer;
        }
        
        .add-button {
            padding: 5px 15px;
            background-color: var(--vscode-button-secondaryBackground);
            color: var(--vscode-button-secondaryForeground);
            border: none;
            border-radius: 2px;
            cursor: pointer;
            margin-top: 5px;
        }
        
        .rule-editor {
            border: 1px solid var(--vscode-panel-border);
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
            background-color: var(--vscode-editor-background);
        }
        
        .rule-editor h4 {
            margin-top: 0;
        }
        
        .two-column {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        
        @media (max-width: 800px) {
            .two-column {
                grid-template-columns: 1fr;
            }
        }
        
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-left: 8px;
        }
        
        .status-valid {
            background-color: var(--vscode-terminal-ansiGreen);
        }
        
        .status-invalid {
            background-color: var(--vscode-terminal-ansiRed);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔗 Connascence Safety Analyzer Settings</h1>
            <p>Configure advanced options for code quality analysis and safety compliance</p>
        </div>

        <div class="section">
            <h2>Safety & Framework Profiles</h2>
            <div class="two-column">
                <div class="setting-group">
                    <label class="setting-label" for="safetyProfile">Safety Profile</label>
                    <div class="setting-description">Choose the safety standard compliance level</div>
                    <select id="safetyProfile">
                        <option value="none">None</option>
                        <option value="modern_general">Modern General</option>
                        <option value="general_safety_strict">General Safety (Strict)</option>
                        <option value="safety_level_1">Safety Level 1 (Highest)</option>
                        <option value="safety_level_3">Safety Level 3 (High)</option>
                    </select>
                </div>
                <div class="setting-group">
                    <label class="setting-label" for="frameworkProfile">Framework Profile</label>
                    <div class="setting-description">Framework-specific analysis patterns</div>
                    <select id="frameworkProfile">
                        <option value="generic">Generic</option>
                        <option value="django">Django</option>
                        <option value="fastapi">FastAPI</option>
                        <option value="react">React</option>
                    </select>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Analysis Configuration</h2>
            <div class="two-column">
                <div class="setting-group">
                    <label class="setting-label" for="analysisDepth">Analysis Depth</label>
                    <div class="setting-description">How thorough the analysis should be</div>
                    <select id="analysisDepth">
                        <option value="surface">Surface (Fast)</option>
                        <option value="standard">Standard</option>
                        <option value="deep">Deep (Thorough)</option>
                        <option value="comprehensive">Comprehensive (Slow)</option>
                    </select>
                </div>
                <div class="setting-group">
                    <label class="setting-label" for="confidenceThreshold">Confidence Threshold</label>
                    <div class="setting-description">Minimum confidence for suggestions (0.0-1.0)</div>
                    <input type="range" id="confidenceThreshold" min="0" max="1" step="0.05" />
                    <span class="range-value" id="confidenceThresholdValue">0.8</span>
                </div>
            </div>
            <div class="two-column">
                <div class="setting-group">
                    <label class="setting-label" for="nasaComplianceThreshold">NASA Compliance Threshold</label>
                    <div class="setting-description">Threshold for NASA safety compliance (0.0-1.0)</div>
                    <input type="range" id="nasaComplianceThreshold" min="0" max="1" step="0.05" />
                    <span class="range-value" id="nasaComplianceThresholdValue">0.95</span>
                </div>
                <div class="setting-group">
                    <label class="setting-label" for="meceQualityThreshold">MECE Quality Threshold</label>
                    <div class="setting-description">Mutually Exclusive, Collectively Exhaustive quality (0.0-1.0)</div>
                    <input type="range" id="meceQualityThreshold" min="0" max="1" step="0.05" />
                    <span class="range-value" id="meceQualityThresholdValue">0.85</span>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>File Filtering</h2>
            <div class="two-column">
                <div class="setting-group">
                    <label class="setting-label">Include Patterns</label>
                    <div class="setting-description">File patterns to include in analysis</div>
                    <div id="includePatterns" class="array-input">
                        <!-- Dynamic content -->
                    </div>
                    <button class="add-button" onclick="addIncludePattern()">Add Pattern</button>
                </div>
                <div class="setting-group">
                    <label class="setting-label">Exclude Patterns</label>
                    <div class="setting-description">File patterns to exclude from analysis</div>
                    <div id="excludePatterns" class="array-input">
                        <!-- Dynamic content -->
                    </div>
                    <button class="add-button" onclick="addExcludePattern()">Add Pattern</button>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Performance Settings</h2>
            <div class="setting-group">
                <label class="setting-label">
                    <input type="checkbox" id="enableProfiling">
                    Enable Performance Profiling
                </label>
                <div class="setting-description">Track analysis performance metrics</div>
            </div>
            <div class="two-column">
                <div class="setting-group">
                    <label class="setting-label" for="maxAnalysisTime">Max Analysis Time (ms)</label>
                    <div class="setting-description">Maximum time to spend analyzing each file</div>
                    <input type="number" id="maxAnalysisTime" min="1000" max="120000" step="1000">
                </div>
                <div class="setting-group">
                    <label class="setting-label" for="memoryThreshold">Memory Threshold (MB)</label>
                    <div class="setting-description">Memory usage threshold for warnings</div>
                    <input type="number" id="memoryThreshold" min="128" max="2048" step="128">
                </div>
            </div>
            <div class="two-column">
                <div class="setting-group">
                    <label class="setting-label">
                        <input type="checkbox" id="enableCaching">
                        Enable Result Caching
                    </label>
                    <div class="setting-description">Cache analysis results for better performance</div>
                </div>
                <div class="setting-group">
                    <label class="setting-label" for="cacheSize">Cache Size</label>
                    <div class="setting-description">Maximum number of cached results</div>
                    <input type="number" id="cacheSize" min="100" max="10000" step="100">
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Advanced Filtering</h2>
            <div class="two-column">
                <div class="setting-group">
                    <label class="setting-label">
                        <input type="checkbox" id="enableGitIgnore">
                        Respect .gitignore
                    </label>
                    <div class="setting-description">Honor .gitignore patterns</div>
                </div>
                <div class="setting-group">
                    <label class="setting-label">
                        <input type="checkbox" id="enableCustomIgnore">
                        Enable .connascence-ignore
                    </label>
                    <div class="setting-description">Use custom ignore file</div>
                </div>
            </div>
            <div class="two-column">
                <div class="setting-group">
                    <label class="setting-label" for="minFileSize">Min File Size (bytes)</label>
                    <div class="setting-description">Skip files smaller than this size</div>
                    <input type="number" id="minFileSize" min="0" max="10000" step="10">
                </div>
                <div class="setting-group">
                    <label class="setting-label" for="maxFileSize">Max File Size (bytes)</label>
                    <div class="setting-description">Skip files larger than this size</div>
                    <input type="number" id="maxFileSize" min="1000" max="104857600" step="1048576">
                </div>
            </div>
            <div class="setting-group">
                <label class="setting-label">
                    <input type="checkbox" id="excludeBinaryFiles">
                    Exclude Binary Files
                </label>
                <div class="setting-description">Automatically skip binary files</div>
            </div>
        </div>

        <div class="section">
            <h2>Custom Analysis Rules</h2>
            <div class="setting-description">Define custom patterns to detect in your code</div>
            <div id="customRules">
                <!-- Dynamic content -->
            </div>
            <button class="add-button" onclick="addCustomRule()">Add Custom Rule</button>
        </div>

        <div class="section">
            <h2>Experimental Features</h2>
            <div class="setting-group">
                <label class="setting-label">
                    <input type="checkbox" id="enableExperimentalFeatures">
                    Enable Experimental Features
                </label>
                <div class="setting-description">Enable features that may be unstable or change in future versions</div>
            </div>
        </div>

        <div class="button-group">
            <button class="primary-button" onclick="saveConfiguration()">Save Settings</button>
            <button class="secondary-button" onclick="exportConfiguration()">Export Config</button>
            <button class="secondary-button" onclick="importConfiguration()">Import Config</button>
            <button class="danger-button" onclick="resetConfiguration()">Reset to Defaults</button>
        </div>
    </div>

    <script>
        const vscode = acquireVsCodeApi();
        let currentConfig = {};

        // Request initial configuration
        vscode.postMessage({ type: 'getConfig' });

        // Handle messages from extension
        window.addEventListener('message', event => {
            const message = event.data;
            switch (message.type) {
                case 'configData':
                    currentConfig = message.config;
                    populateForm(message.config);
                    break;
                case 'ruleValidation':
                    handleRuleValidation(message.isValid, message.rule);
                    break;
            }
        });

        function populateForm(config) {
            // Basic settings
            document.getElementById('safetyProfile').value = config.safetyProfile || 'modern_general';
            document.getElementById('frameworkProfile').value = config.frameworkProfile || 'generic';
            document.getElementById('analysisDepth').value = config.analysisDepth || 'standard';
            
            // Thresholds
            setRangeValue('confidenceThreshold', config.confidenceThreshold || 0.8);
            setRangeValue('nasaComplianceThreshold', config.nasaComplianceThreshold || 0.95);
            setRangeValue('meceQualityThreshold', config.meceQualityThreshold || 0.85);
            
            // File patterns
            populateArrayField('includePatterns', config.includePatterns || []);
            populateArrayField('excludePatterns', config.excludePatterns || []);
            
            // Performance settings
            const perfConfig = config.performanceAnalysis || {};
            document.getElementById('enableProfiling').checked = perfConfig.enableProfiling !== false;
            document.getElementById('maxAnalysisTime').value = perfConfig.maxAnalysisTime || 30000;
            document.getElementById('memoryThreshold').value = perfConfig.memoryThreshold || 512;
            document.getElementById('enableCaching').checked = perfConfig.enableCaching !== false;
            document.getElementById('cacheSize').value = perfConfig.cacheSize || 1000;
            
            // Advanced filtering
            const filterConfig = config.advancedFiltering || {};
            document.getElementById('enableGitIgnore').checked = filterConfig.enableGitIgnore !== false;
            document.getElementById('enableCustomIgnore').checked = filterConfig.enableCustomIgnore !== false;
            document.getElementById('minFileSize').value = filterConfig.minFileSize || 10;
            document.getElementById('maxFileSize').value = filterConfig.maxFileSize || 10485760;
            document.getElementById('excludeBinaryFiles').checked = filterConfig.excludeBinaryFiles !== false;
            
            // Custom rules
            populateCustomRules(config.customRules || []);
            
            // Experimental features
            document.getElementById('enableExperimentalFeatures').checked = config.enableExperimentalFeatures || false;
        }

        function setRangeValue(id, value) {
            const range = document.getElementById(id);
            const valueSpan = document.getElementById(id + 'Value');
            range.value = value;
            valueSpan.textContent = value.toFixed(2);
            
            range.addEventListener('input', () => {
                valueSpan.textContent = parseFloat(range.value).toFixed(2);
            });
        }

        function populateArrayField(containerId, values) {
            const container = document.getElementById(containerId);
            container.innerHTML = '';
            
            values.forEach((value, index) => {
                const item = document.createElement('div');
                item.className = 'array-item';
                item.innerHTML = \`
                    <input type="text" value="\${value}" data-index="\${index}">
                    <button class="remove-button" onclick="removeArrayItem('\${containerId}', \${index})">Remove</button>
                \`;
                container.appendChild(item);
            });
        }

        function populateCustomRules(rules) {
            const container = document.getElementById('customRules');
            container.innerHTML = '';
            
            rules.forEach((rule, index) => {
                const ruleElement = document.createElement('div');
                ruleElement.className = 'rule-editor';
                ruleElement.innerHTML = \`
                    <h4>Rule \${index + 1} <span class="status-indicator" id="rule-status-\${index}"></span></h4>
                    <div class="two-column">
                        <div class="setting-group">
                            <label class="setting-label">Name</label>
                            <input type="text" value="\${rule.name || ''}" data-rule-index="\${index}" data-field="name">
                        </div>
                        <div class="setting-group">
                            <label class="setting-label">Severity</label>
                            <select data-rule-index="\${index}" data-field="severity">
                                <option value="error" \${rule.severity === 'error' ? 'selected' : ''}>Error</option>
                                <option value="warning" \${rule.severity === 'warning' ? 'selected' : ''}>Warning</option>
                                <option value="info" \${rule.severity === 'info' ? 'selected' : ''}>Info</option>
                                <option value="hint" \${rule.severity === 'hint' ? 'selected' : ''}>Hint</option>
                            </select>
                        </div>
                    </div>
                    <div class="setting-group">
                        <label class="setting-label">Pattern (Regex)</label>
                        <input type="text" value="\${rule.pattern || ''}" data-rule-index="\${index}" data-field="pattern">
                    </div>
                    <div class="setting-group">
                        <label class="setting-label">Message</label>
                        <textarea rows="2" data-rule-index="\${index}" data-field="message">\${rule.message || ''}</textarea>
                    </div>
                    <button class="remove-button" onclick="removeCustomRule(\${index})">Remove Rule</button>
                \`;
                container.appendChild(ruleElement);
            });
        }

        function addIncludePattern() {
            addArrayItem('includePatterns', '**/*.ext');
        }

        function addExcludePattern() {
            addArrayItem('excludePatterns', '**/pattern/**');
        }

        function addArrayItem(containerId, defaultValue) {
            const container = document.getElementById(containerId);
            const index = container.children.length;
            
            const item = document.createElement('div');
            item.className = 'array-item';
            item.innerHTML = \`
                <input type="text" value="\${defaultValue}" data-index="\${index}">
                <button class="remove-button" onclick="removeArrayItem('\${containerId}', \${index})">Remove</button>
            \`;
            container.appendChild(item);
        }

        function removeArrayItem(containerId, index) {
            const container = document.getElementById(containerId);
            const items = container.children;
            if (items[index]) {
                items[index].remove();
            }
        }

        function addCustomRule() {
            const rules = collectCustomRules();
            rules.push({
                name: 'New Rule',
                pattern: '',
                severity: 'warning',
                message: ''
            });
            populateCustomRules(rules);
        }

        function removeCustomRule(index) {
            const rules = collectCustomRules();
            rules.splice(index, 1);
            populateCustomRules(rules);
        }

        function collectCustomRules() {
            const container = document.getElementById('customRules');
            const rules = [];
            
            container.querySelectorAll('.rule-editor').forEach((ruleElement, index) => {
                const rule = {
                    name: ruleElement.querySelector('[data-field="name"]').value,
                    pattern: ruleElement.querySelector('[data-field="pattern"]').value,
                    severity: ruleElement.querySelector('[data-field="severity"]').value,
                    message: ruleElement.querySelector('[data-field="message"]').value
                };
                rules.push(rule);
            });
            
            return rules;
        }

        function collectArrayValues(containerId) {
            const container = document.getElementById(containerId);
            const values = [];
            
            container.querySelectorAll('input').forEach(input => {
                if (input.value.trim()) {
                    values.push(input.value.trim());
                }
            });
            
            return values;
        }

        function saveConfiguration() {
            const config = {
                safetyProfile: document.getElementById('safetyProfile').value,
                frameworkProfile: document.getElementById('frameworkProfile').value,
                analysisDepth: document.getElementById('analysisDepth').value,
                confidenceThreshold: parseFloat(document.getElementById('confidenceThreshold').value),
                nasaComplianceThreshold: parseFloat(document.getElementById('nasaComplianceThreshold').value),
                meceQualityThreshold: parseFloat(document.getElementById('meceQualityThreshold').value),
                includePatterns: collectArrayValues('includePatterns'),
                excludePatterns: collectArrayValues('excludePatterns'),
                performanceAnalysis: {
                    enableProfiling: document.getElementById('enableProfiling').checked,
                    maxAnalysisTime: parseInt(document.getElementById('maxAnalysisTime').value),
                    memoryThreshold: parseInt(document.getElementById('memoryThreshold').value),
                    enableCaching: document.getElementById('enableCaching').checked,
                    cacheSize: parseInt(document.getElementById('cacheSize').value)
                },
                advancedFiltering: {
                    enableGitIgnore: document.getElementById('enableGitIgnore').checked,
                    enableCustomIgnore: document.getElementById('enableCustomIgnore').checked,
                    minFileSize: parseInt(document.getElementById('minFileSize').value),
                    maxFileSize: parseInt(document.getElementById('maxFileSize').value),
                    excludeBinaryFiles: document.getElementById('excludeBinaryFiles').checked
                },
                customRules: collectCustomRules(),
                enableExperimentalFeatures: document.getElementById('enableExperimentalFeatures').checked
            };

            vscode.postMessage({
                type: 'updateConfig',
                config: config
            });
        }

        function exportConfiguration() {
            vscode.postMessage({ type: 'exportConfig' });
        }

        function importConfiguration() {
            vscode.postMessage({ type: 'importConfig' });
        }

        function resetConfiguration() {
            vscode.postMessage({ type: 'resetConfig' });
        }

        function handleRuleValidation(isValid, rule) {
            // Update UI to show validation status
            console.log('Rule validation:', isValid, rule);
        }
    </script>
</body>
</html>`;
    }
}