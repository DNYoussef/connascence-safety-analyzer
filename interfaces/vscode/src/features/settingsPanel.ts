/**
 * Advanced Settings Panel for Connascence Safety Analyzer
 * Provides comprehensive configuration management interface
 */

import * as vscode from 'vscode';
import { ConfigurationService, PolicyPreset, PolicyComparison, ImpactAnalysis } from '../services/configurationService';
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
                case 'getPolicyPresets':
                    await this.handleGetPolicyPresets();
                    break;
                case 'applyPolicyPreset':
                    await this.handleApplyPolicyPreset(message.presetId);
                    break;
                case 'comparePolicyPresets':
                    await this.handleComparePolicyPresets(message.preset1Id, message.preset2Id);
                    break;
                case 'createCustomPolicy':
                    await this.handleCreateCustomPolicy(message.name, message.description, message.settings);
                    break;
                case 'exportPolicyConfiguration':
                    await this.handleExportPolicyConfiguration(message.presetId);
                    break;
                case 'getPolicyImpactPreview':
                    await this.handleGetPolicyImpactPreview(message.presetId);
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

    // =====================================================
    // POLICY MANAGEMENT MESSAGE HANDLERS
    // =====================================================

    private async handleGetPolicyPresets(): Promise<void> {
        if (!this.panel) return;

        const presets = this.configService.getPolicyPresets();
        const customPresets: any[] = []; // Custom presets are stored in the configuration
        const allPresets = [...presets, ...customPresets];
        
        await this.panel.webview.postMessage({
            type: 'policyPresets',
            presets: allPresets,
            appliedPreset: this.configService.getAppliedPolicyPreset()
        });
    }

    private async handleApplyPolicyPreset(presetId: string): Promise<void> {
        if (!this.panel) return;

        try {
            const result = await this.configService.applyPolicyPreset(presetId);
            
            if (result.success) {
                vscode.window.showInformationMessage('Policy preset applied successfully');
                await this.sendConfigToPanel(); // Refresh UI with new settings
            } else {
                const errors = result.errors?.join(', ') || 'Unknown error';
                vscode.window.showErrorMessage(`Failed to apply policy preset: ${errors}`);
            }

            await this.panel.webview.postMessage({
                type: 'policyApplyResult',
                success: result.success,
                errors: result.errors
            });

        } catch (error) {
            vscode.window.showErrorMessage(`Error applying policy preset: ${error}`);
            await this.panel.webview.postMessage({
                type: 'policyApplyResult',
                success: false,
                errors: [`Error: ${error}`]
            });
        }
    }

    private async handleComparePolicyPresets(preset1Id: string, preset2Id: string): Promise<void> {
        if (!this.panel) return;

        const comparison = this.configService.comparePolicyPresets(preset1Id, preset2Id);
        
        await this.panel.webview.postMessage({
            type: 'policyComparison',
            comparison: comparison
        });
    }

    private async handleCreateCustomPolicy(name: string, description: string, settings: any): Promise<void> {
        if (!this.panel) return;

        try {
            const result = await this.configService.createCustomPolicy(name, description, settings);
            
            if (result.success) {
                vscode.window.showInformationMessage('Custom policy created successfully');
                await this.handleGetPolicyPresets(); // Refresh presets list
            } else {
                const errors = result.errors?.join(', ') || 'Unknown error';
                vscode.window.showErrorMessage(`Failed to create custom policy: ${errors}`);
            }

            await this.panel.webview.postMessage({
                type: 'customPolicyCreateResult',
                success: result.success,
                preset: result.preset,
                errors: result.errors
            });

        } catch (error) {
            vscode.window.showErrorMessage(`Error creating custom policy: ${error}`);
            await this.panel.webview.postMessage({
                type: 'customPolicyCreateResult',
                success: false,
                errors: [`Error: ${error}`]
            });
        }
    }

    private async handleExportPolicyConfiguration(presetId?: string): Promise<void> {
        if (!this.panel) return;

        try {
            const result = await this.configService.exportPolicyConfiguration(presetId);
            
            if (result.success && result.data) {
                const configJson = JSON.stringify(result.data, null, 2);
                const fileName = presetId ? `${presetId}-policy.json` : 'policy-export.json';
                
                const uri = await vscode.window.showSaveDialog({
                    filters: {
                        'JSON files': ['json']
                    },
                    defaultUri: vscode.Uri.file(fileName)
                });

                if (uri) {
                    await vscode.workspace.fs.writeFile(uri, Buffer.from(configJson));
                    vscode.window.showInformationMessage('Policy configuration exported successfully');
                }
            } else {
                const errors = result.errors?.join(', ') || 'Unknown error';
                vscode.window.showErrorMessage(`Failed to export policy configuration: ${errors}`);
            }

            await this.panel.webview.postMessage({
                type: 'policyExportResult',
                success: result.success,
                errors: result.errors
            });

        } catch (error) {
            vscode.window.showErrorMessage(`Error exporting policy configuration: ${error}`);
        }
    }

    private async handleGetPolicyImpactPreview(presetId: string): Promise<void> {
        if (!this.panel) return;

        const preset = this.configService.getPolicyPresetById(presetId);
        if (!preset) {
            await this.panel.webview.postMessage({
                type: 'policyImpactPreview',
                error: 'Policy preset not found'
            });
            return;
        }

        // Calculate impact analysis by comparing with current settings
        const currentPresetId = this.configService.getAppliedPolicyPreset();
        let impactAnalysis: ImpactAnalysis | null = null;
        
        if (currentPresetId) {
            const comparison = this.configService.comparePolicyPresets(currentPresetId, presetId);
            impactAnalysis = comparison?.impactAnalysis || null;
        }

        await this.panel.webview.postMessage({
            type: 'policyImpactPreview',
            preset: preset,
            impactAnalysis: impactAnalysis
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
        
        /* Policy Management Styles */
        .preset-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }
        
        .preset-card {
            border: 2px solid var(--vscode-panel-border);
            border-radius: 8px;
            padding: 15px;
            background-color: var(--vscode-editor-background);
            cursor: pointer;
            transition: all 0.2s ease;
            position: relative;
        }
        
        .preset-card:hover {
            border-color: var(--vscode-button-background);
            background-color: var(--vscode-panel-background);
        }
        
        .preset-card.active {
            border-color: var(--vscode-button-background);
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
        }
        
        .preset-card.active::before {
            content: "✓ Applied";
            position: absolute;
            top: 5px;
            right: 10px;
            font-size: 12px;
            font-weight: bold;
            color: var(--vscode-terminal-ansiGreen);
        }
        
        .preset-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        
        .preset-title {
            font-weight: bold;
            font-size: 16px;
            margin: 0;
        }
        
        .preset-impact {
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .impact-low {
            background-color: var(--vscode-terminal-ansiGreen);
            color: var(--vscode-editor-background);
        }
        
        .impact-medium {
            background-color: var(--vscode-terminal-ansiYellow);
            color: var(--vscode-editor-background);
        }
        
        .impact-high {
            background-color: var(--vscode-terminal-ansiRed);
            color: var(--vscode-editor-foreground);
        }
        
        .preset-description {
            color: var(--vscode-descriptionForeground);
            font-size: 14px;
            margin-bottom: 10px;
            line-height: 1.4;
        }
        
        .preset-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }
        
        .preset-tag {
            background-color: var(--vscode-panel-border);
            color: var(--vscode-foreground);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 11px;
        }
        
        .preset-actions {
            display: flex;
            justify-content: flex-end;
            gap: 5px;
            margin-top: 10px;
        }
        
        .preset-action-btn {
            padding: 4px 8px;
            font-size: 12px;
            border: 1px solid var(--vscode-button-border);
            background-color: var(--vscode-button-secondaryBackground);
            color: var(--vscode-button-secondaryForeground);
            border-radius: 3px;
            cursor: pointer;
        }
        
        .preset-action-btn:hover {
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
        }
        
        .policy-actions {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid var(--vscode-panel-border);
        }
        
        .policy-impact-preview {
            margin-top: 20px;
            padding: 15px;
            border: 1px solid var(--vscode-panel-border);
            border-radius: 8px;
            background-color: var(--vscode-panel-background);
        }
        
        .impact-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        
        .impact-metric {
            text-align: center;
            padding: 10px;
            border: 1px solid var(--vscode-panel-border);
            border-radius: 6px;
        }
        
        .impact-value {
            font-size: 20px;
            font-weight: bold;
            color: var(--vscode-button-background);
            display: block;
        }
        
        .impact-label {
            font-size: 12px;
            color: var(--vscode-descriptionForeground);
            margin-top: 5px;
        }
        
        .policy-comparison {
            margin-top: 20px;
            padding: 15px;
            border: 1px solid var(--vscode-panel-border);
            border-radius: 8px;
            background-color: var(--vscode-panel-background);
        }
        
        .comparison-controls {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .comparison-controls select {
            flex: 1;
        }
        
        .vs-label {
            font-weight: bold;
            color: var(--vscode-button-background);
            font-size: 16px;
        }
        
        .comparison-results {
            margin-top: 20px;
        }
        
        .differences-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        
        .differences-table th,
        .differences-table td {
            padding: 8px 12px;
            border: 1px solid var(--vscode-panel-border);
            text-align: left;
        }
        
        .differences-table th {
            background-color: var(--vscode-panel-background);
            font-weight: bold;
        }
        
        .difference-high {
            background-color: var(--vscode-diffEditor-removedTextBackground);
        }
        
        .difference-medium {
            background-color: var(--vscode-diffEditor-insertedTextBackground);
        }
        
        .difference-low {
            background-color: var(--vscode-panel-background);
        }
        
        .custom-policy-builder {
            margin-top: 20px;
            padding: 20px;
            border: 1px solid var(--vscode-panel-border);
            border-radius: 8px;
            background-color: var(--vscode-panel-background);
        }
        
        .builder-form .setting-group {
            margin-bottom: 20px;
        }
        
        .builder-settings {
            margin: 20px 0;
            padding: 15px;
            border: 1px dashed var(--vscode-panel-border);
            border-radius: 6px;
            min-height: 100px;
        }
        
        .builder-actions {
            display: flex;
            gap: 10px;
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid var(--vscode-panel-border);
        }
        
        .drag-drop-area {
            border: 2px dashed var(--vscode-panel-border);
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            color: var(--vscode-descriptionForeground);
            margin: 10px 0;
            transition: border-color 0.2s ease;
        }
        
        .drag-drop-area.drag-over {
            border-color: var(--vscode-button-background);
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
        }
        
        .rule-component {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            margin: 5px 0;
            border: 1px solid var(--vscode-panel-border);
            border-radius: 4px;
            background-color: var(--vscode-editor-background);
            cursor: move;
        }
        
        .rule-component:hover {
            border-color: var(--vscode-button-background);
        }
        
        .toggle-button {
            background: none;
            border: none;
            color: var(--vscode-button-background);
            cursor: pointer;
            font-size: 14px;
            padding: 5px;
        }
        
        .toggle-button:hover {
            color: var(--vscode-button-hoverBackground);
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
            <h2>Policy Management</h2>
            <p class="setting-description">Quickly apply comprehensive policy presets or create custom configurations</p>
            
            <div class="policy-preset-selector">
                <h3>Available Policy Presets</h3>
                <div id="policyPresets" class="preset-grid">
                    <!-- Dynamic content -->
                </div>
                
                <div class="policy-actions">
                    <button class="secondary-button" onclick="showPolicyComparison()">Compare Policies</button>
                    <button class="secondary-button" onclick="showCustomPolicyBuilder()">Create Custom Policy</button>
                    <button class="secondary-button" onclick="exportCurrentPolicy()">Export Current Policy</button>
                </div>
            </div>
            
            <div id="policyImpactPreview" class="policy-impact-preview" style="display: none;">
                <h3>Policy Impact Preview</h3>
                <div class="impact-details">
                    <!-- Dynamic content -->
                </div>
            </div>
            
            <div id="policyComparison" class="policy-comparison" style="display: none;">
                <h3>Policy Comparison</h3>
                <div class="comparison-controls">
                    <select id="comparePreset1">
                        <option value="">Select first policy...</option>
                    </select>
                    <span class="vs-label">vs</span>
                    <select id="comparePreset2">
                        <option value="">Select second policy...</option>
                    </select>
                    <button class="primary-button" onclick="comparePolicies()">Compare</button>
                </div>
                <div id="comparisonResults" class="comparison-results">
                    <!-- Dynamic content -->
                </div>
            </div>
            
            <div id="customPolicyBuilder" class="custom-policy-builder" style="display: none;">
                <h3>Custom Policy Builder</h3>
                <div class="builder-form">
                    <div class="setting-group">
                        <label class="setting-label" for="customPolicyName">Policy Name</label>
                        <input type="text" id="customPolicyName" placeholder="My Custom Policy">
                    </div>
                    <div class="setting-group">
                        <label class="setting-label" for="customPolicyDescription">Description</label>
                        <textarea id="customPolicyDescription" rows="2" placeholder="Description of this policy..."></textarea>
                    </div>
                    <div class="setting-group">
                        <label class="setting-label">Base Template</label>
                        <select id="customPolicyBase">
                            <option value="default_balanced">Default Balanced</option>
                            <option value="strict_core">Strict Core Safety</option>
                            <option value="lenient_dev">Lenient Development</option>
                            <option value="nasa_jpl_pot10">NASA JPL Power of Ten</option>
                        </select>
                    </div>
                    <div class="builder-settings">
                        <!-- Will be populated with draggable rule components -->
                    </div>
                    <div class="builder-actions">
                        <button class="primary-button" onclick="createCustomPolicy()">Create Policy</button>
                        <button class="secondary-button" onclick="hideCustomPolicyBuilder()">Cancel</button>
                    </div>
                </div>
            </div>
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
                case 'policyPresets':
                    populatePolicyPresets(message.presets, message.appliedPreset);
                    break;
                case 'policyApplyResult':
                    handlePolicyApplyResult(message.success, message.errors);
                    break;
                case 'policyComparison':
                    displayPolicyComparison(message.comparison);
                    break;
                case 'policyImpactPreview':
                    displayPolicyImpactPreview(message.preset, message.impactAnalysis, message.error);
                    break;
                case 'customPolicyCreateResult':
                    handleCustomPolicyCreateResult(message.success, message.preset, message.errors);
                    break;
                case 'policyExportResult':
                    handlePolicyExportResult(message.success, message.errors);
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

        // =====================================================
        // POLICY MANAGEMENT FUNCTIONS
        // =====================================================

        // Request policy presets when the page loads
        vscode.postMessage({ type: 'getPolicyPresets' });

        function populatePolicyPresets(presets, appliedPreset) {
            const container = document.getElementById('policyPresets');
            container.innerHTML = '';

            presets.forEach(preset => {
                const presetCard = document.createElement('div');
                presetCard.className = 'preset-card' + (preset.id === appliedPreset ? ' active' : '');
                presetCard.onclick = () => applyPolicyPreset(preset.id);
                
                presetCard.innerHTML = \`
                    <div class="preset-header">
                        <h4 class="preset-title">\${preset.name}</h4>
                        <span class="preset-impact impact-\${preset.impact}">\${preset.impact}</span>
                    </div>
                    <div class="preset-description">\${preset.description}</div>
                    <div class="preset-tags">
                        \${preset.tags.map(tag => \`<span class="preset-tag">\${tag}</span>\`).join('')}
                    </div>
                    <div class="preset-actions">
                        <button class="preset-action-btn" onclick="event.stopPropagation(); previewPolicyImpact('\${preset.id}')">Preview</button>
                        <button class="preset-action-btn" onclick="event.stopPropagation(); exportPolicyPreset('\${preset.id}')">Export</button>
                    </div>
                \`;
                
                container.appendChild(presetCard);
            });

            // Populate comparison dropdowns
            populateComparisonDropdowns(presets);
        }

        function populateComparisonDropdowns(presets) {
            const dropdown1 = document.getElementById('comparePreset1');
            const dropdown2 = document.getElementById('comparePreset2');
            
            dropdown1.innerHTML = '<option value="">Select first policy...</option>';
            dropdown2.innerHTML = '<option value="">Select second policy...</option>';
            
            presets.forEach(preset => {
                dropdown1.innerHTML += \`<option value="\${preset.id}">\${preset.name}</option>\`;
                dropdown2.innerHTML += \`<option value="\${preset.id}">\${preset.name}</option>\`;
            });
        }

        function applyPolicyPreset(presetId) {
            vscode.postMessage({ 
                type: 'applyPolicyPreset', 
                presetId: presetId 
            });
        }

        function handlePolicyApplyResult(success, errors) {
            if (success) {
                // Refresh the policy presets to show the new applied state
                vscode.postMessage({ type: 'getPolicyPresets' });
                // Refresh config to update all other settings
                vscode.postMessage({ type: 'getConfig' });
            } else {
                console.error('Policy apply failed:', errors);
            }
        }

        function previewPolicyImpact(presetId) {
            vscode.postMessage({ 
                type: 'getPolicyImpactPreview', 
                presetId: presetId 
            });
        }

        function displayPolicyImpactPreview(preset, impactAnalysis, error) {
            const container = document.getElementById('policyImpactPreview');
            
            if (error) {
                container.innerHTML = \`<p style="color: var(--vscode-errorForeground);">Error: \${error}</p>\`;
                container.style.display = 'block';
                return;
            }

            const impactDetails = document.querySelector('.impact-details');
            
            let impactHtml = \`
                <h4>\${preset.name} - Impact Analysis</h4>
                <p>\${preset.description}</p>
            \`;

            if (impactAnalysis) {
                impactHtml += \`
                    <div class="impact-grid">
                        <div class="impact-metric">
                            <span class="impact-value">\${impactAnalysis.performanceImpact > 0 ? '+' : ''}\${impactAnalysis.performanceImpact}%</span>
                            <div class="impact-label">Performance Impact</div>
                        </div>
                        <div class="impact-metric">
                            <span class="impact-value">\${impactAnalysis.thoroughnessImpact}%</span>
                            <div class="impact-label">Thoroughness</div>
                        </div>
                        <div class="impact-metric">
                            <span class="impact-value">\${impactAnalysis.falsePositiveRate.toFixed(1)}%</span>
                            <div class="impact-label">Est. False Positives</div>
                        </div>
                        <div class="impact-metric">
                            <span class="impact-value">\${impactAnalysis.estimatedAnalysisTime}</span>
                            <div class="impact-label">Analysis Time</div>
                        </div>
                        <div class="impact-metric">
                            <span class="impact-value">\${impactAnalysis.memoryUsage}</span>
                            <div class="impact-label">Memory Usage</div>
                        </div>
                    </div>
                \`;
            } else {
                impactHtml += '<p>No current policy for comparison. Impact will be calculated after applying a policy.</p>';
            }

            impactDetails.innerHTML = impactHtml;
            container.style.display = 'block';
        }

        function showPolicyComparison() {
            document.getElementById('policyComparison').style.display = 'block';
        }

        function hidePolicyComparison() {
            document.getElementById('policyComparison').style.display = 'none';
        }

        function comparePolicies() {
            const preset1Id = document.getElementById('comparePreset1').value;
            const preset2Id = document.getElementById('comparePreset2').value;
            
            if (!preset1Id || !preset2Id) {
                alert('Please select two policies to compare');
                return;
            }
            
            if (preset1Id === preset2Id) {
                alert('Please select different policies to compare');
                return;
            }
            
            vscode.postMessage({ 
                type: 'comparePolicyPresets', 
                preset1Id: preset1Id,
                preset2Id: preset2Id
            });
        }

        function displayPolicyComparison(comparison) {
            const container = document.getElementById('comparisonResults');
            
            if (!comparison) {
                container.innerHTML = '<p>Comparison failed. Please try again.</p>';
                return;
            }

            let html = \`
                <div class="comparison-header">
                    <h4>Comparing: \${comparison.preset1.name} vs \${comparison.preset2.name}</h4>
                </div>
                
                <div class="impact-grid">
                    <div class="impact-metric">
                        <span class="impact-value">\${comparison.impactAnalysis.performanceImpact > 0 ? '+' : ''}\${comparison.impactAnalysis.performanceImpact}%</span>
                        <div class="impact-label">Performance Difference</div>
                    </div>
                    <div class="impact-metric">
                        <span class="impact-value">\${comparison.impactAnalysis.thoroughnessImpact}%</span>
                        <div class="impact-label">Thoroughness Level</div>
                    </div>
                    <div class="impact-metric">
                        <span class="impact-value">\${comparison.differences.length}</span>
                        <div class="impact-label">Different Settings</div>
                    </div>
                </div>
            \`;
            
            if (comparison.differences.length > 0) {
                html += \`
                    <table class="differences-table">
                        <thead>
                            <tr>
                                <th>Setting</th>
                                <th>\${comparison.preset1.name}</th>
                                <th>\${comparison.preset2.name}</th>
                                <th>Impact</th>
                                <th>Description</th>
                            </tr>
                        </thead>
                        <tbody>
                \`;
                
                comparison.differences.forEach(diff => {
                    html += \`
                        <tr class="difference-\${diff.impact}">
                            <td><strong>\${diff.setting}</strong></td>
                            <td>\${formatSettingValue(diff.value1)}</td>
                            <td>\${formatSettingValue(diff.value2)}</td>
                            <td><span class="preset-impact impact-\${diff.impact}">\${diff.impact}</span></td>
                            <td>\${diff.description}</td>
                        </tr>
                    \`;
                });
                
                html += \`
                        </tbody>
                    </table>
                \`;
            }
            
            container.innerHTML = html;
        }

        function formatSettingValue(value) {
            if (typeof value === 'object') {
                return JSON.stringify(value, null, 1);
            }
            return String(value);
        }

        function showCustomPolicyBuilder() {
            document.getElementById('customPolicyBuilder').style.display = 'block';
            initializeCustomPolicyBuilder();
        }

        function hideCustomPolicyBuilder() {
            document.getElementById('customPolicyBuilder').style.display = 'none';
        }

        function initializeCustomPolicyBuilder() {
            const builderSettings = document.querySelector('.builder-settings');
            builderSettings.innerHTML = \`
                <div class="drag-drop-area">
                    <p>Drag and drop configuration components here to build your custom policy</p>
                    <div class="available-components">
                        <h4>Available Components:</h4>
                        <div class="rule-component" draggable="true" data-setting="analysisDepth">
                            <span>Analysis Depth</span>
                            <select>
                                <option value="surface">Surface</option>
                                <option value="standard">Standard</option>
                                <option value="deep">Deep</option>
                                <option value="comprehensive">Comprehensive</option>
                            </select>
                        </div>
                        <div class="rule-component" draggable="true" data-setting="confidenceThreshold">
                            <span>Confidence Threshold</span>
                            <input type="range" min="0" max="1" step="0.05" value="0.8">
                        </div>
                        <div class="rule-component" draggable="true" data-setting="realTimeAnalysis">
                            <span>Real-time Analysis</span>
                            <input type="checkbox" checked>
                        </div>
                        <div class="rule-component" draggable="true" data-setting="grammarValidation">
                            <span>Grammar Validation</span>
                            <input type="checkbox" checked>
                        </div>
                        <div class="rule-component" draggable="true" data-setting="autoFixSuggestions">
                            <span>Auto-fix Suggestions</span>
                            <input type="checkbox" checked>
                        </div>
                    </div>
                </div>
            \`;
        }

        function createCustomPolicy() {
            const name = document.getElementById('customPolicyName').value;
            const description = document.getElementById('customPolicyDescription').value;
            const baseTemplate = document.getElementById('customPolicyBase').value;
            
            if (!name.trim()) {
                alert('Please enter a policy name');
                return;
            }
            
            if (!description.trim()) {
                alert('Please enter a policy description');
                return;
            }
            
            // Collect settings from the builder
            const settings = collectBuilderSettings(baseTemplate);
            
            vscode.postMessage({ 
                type: 'createCustomPolicy', 
                name: name,
                description: description,
                settings: settings
            });
        }

        function collectBuilderSettings(baseTemplate) {
            // For now, return the base template settings
            // In a full implementation, this would collect from the drag-and-drop interface
            const baseSettings = {};
            
            // Add any custom overrides based on the builder interface
            const analysisDepth = document.querySelector('[data-setting="analysisDepth"] select')?.value;
            if (analysisDepth) {
                baseSettings.analysisDepth = analysisDepth;
            }
            
            const confidenceThreshold = document.querySelector('[data-setting="confidenceThreshold"] input')?.value;
            if (confidenceThreshold) {
                baseSettings.confidenceThreshold = parseFloat(confidenceThreshold);
            }
            
            const realTimeAnalysis = document.querySelector('[data-setting="realTimeAnalysis"] input')?.checked;
            if (realTimeAnalysis !== undefined) {
                baseSettings.realTimeAnalysis = realTimeAnalysis;
            }
            
            const grammarValidation = document.querySelector('[data-setting="grammarValidation"] input')?.checked;
            if (grammarValidation !== undefined) {
                baseSettings.grammarValidation = grammarValidation;
            }
            
            const autoFixSuggestions = document.querySelector('[data-setting="autoFixSuggestions"] input')?.checked;
            if (autoFixSuggestions !== undefined) {
                baseSettings.autoFixSuggestions = autoFixSuggestions;
            }
            
            return baseSettings;
        }

        function handleCustomPolicyCreateResult(success, preset, errors) {
            if (success) {
                alert('Custom policy created successfully!');
                hideCustomPolicyBuilder();
                vscode.postMessage({ type: 'getPolicyPresets' }); // Refresh presets
            } else {
                const errorMessage = errors ? errors.join('\\n') : 'Unknown error';
                alert('Failed to create custom policy:\\n' + errorMessage);
            }
        }

        function exportCurrentPolicy() {
            vscode.postMessage({ type: 'exportPolicyConfiguration' });
        }

        function exportPolicyPreset(presetId) {
            vscode.postMessage({ 
                type: 'exportPolicyConfiguration', 
                presetId: presetId 
            });
        }

        function handlePolicyExportResult(success, errors) {
            if (!success) {
                const errorMessage = errors ? errors.join('\\n') : 'Export failed';
                alert('Export failed:\\n' + errorMessage);
            }
            // Success message is shown by the extension
        }
    </script>
</body>
</html>`;
    }
}