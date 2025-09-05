/**
 * Dashboard webview for detailed connascence analysis.
 * 
 * Provides rich visualizations and detailed violation information
 * in a webview panel within VS Code.
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { ConnascenceViolation } from './diagnostics';

export class ConnascenceDashboard {
    private panel: vscode.WebviewPanel | undefined;
    private violations: ConnascenceViolation[] = [];
    
    constructor(private context: vscode.ExtensionContext) {}
    
    show(): void {
        if (this.panel) {
            this.panel.reveal();
            return;
        }
        
        this.panel = vscode.window.createWebviewPanel(
            'connascenceDashboard',
            'Connascence Dashboard',
            vscode.ViewColumn.Two,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
                localResourceRoots: [
                    vscode.Uri.joinPath(this.context.extensionUri, 'resources')
                ]
            }
        );
        
        this.panel.iconPath = vscode.Uri.joinPath(this.context.extensionUri, 'images', 'broken-chain-logo.png');
        
        this.panel.onDidDispose(() => {
            this.panel = undefined;
        }, null, this.context.subscriptions);
        
        // Handle messages from webview
        this.panel.webview.onDidReceiveMessage(
            message => {
                switch (message.type) {
                    case 'openFile':
                        vscode.window.showTextDocument(vscode.Uri.file(message.filePath));
                        break;
                    case 'gotoViolation':
                        vscode.window.showTextDocument(vscode.Uri.file(message.filePath)).then(editor => {
                            const position = new vscode.Position(message.lineNumber - 1, 0);
                            editor.selection = new vscode.Selection(position, position);
                            editor.revealRange(new vscode.Range(position, position));
                        });
                        break;
                    case 'exportReport':
                        this.exportReport(message.format);
                        break;
                }
            },
            null,
            this.context.subscriptions
        );
        
        this.updateContent();
    }
    
    updateViolations(violations: ConnascenceViolation[]): void {
        this.violations = violations;
        if (this.panel) {
            this.updateContent();
        }
    }
    
    explainFinding(violation: ConnascenceViolation): void {
        this.show();
        
        // Send message to webview to focus on specific violation
        if (this.panel) {
            this.panel.webview.postMessage({
                type: 'focusViolation',
                violation: violation
            });
        }
    }
    
    private updateContent(): void {
        if (!this.panel) return;
        
        const summary = this.generateSummary();
        const chartData = this.generateChartData();
        const fileAnalysis = this.generateFileAnalysis();
        
        this.panel.webview.html = this.getWebviewContent(summary, chartData, fileAnalysis);
    }
    
    private generateSummary() {
        const total = this.violations.length;
        const critical = this.violations.filter(v => v.severity === 'critical').length;
        const high = this.violations.filter(v => v.severity === 'high').length;
        const medium = this.violations.filter(v => v.severity === 'medium').length;
        const low = this.violations.filter(v => v.severity === 'low').length;
        
        // Calculate connascence index
        const weights = { critical: 10, high: 5, medium: 2, low: 1 };
        const connascenceIndex = this.violations.reduce((sum, v) => {
            return sum + (weights[v.severity as keyof typeof weights] || 1);
        }, 0);
        
        // Group by type
        const byType = new Map<string, number>();
        this.violations.forEach(v => {
            const type = v.connascenceType;
            byType.set(type, (byType.get(type) || 0) + 1);
        });
        
        return {
            total,
            critical,
            high,
            medium,
            low,
            connascenceIndex,
            byType: Object.fromEntries(byType),
            topTypes: Array.from(byType.entries())
                .sort(([, a], [, b]) => b - a)
                .slice(0, 5)
        };
    }
    
    private generateChartData() {
        // Severity distribution
        const severityData = {
            critical: this.violations.filter(v => v.severity === 'critical').length,
            high: this.violations.filter(v => v.severity === 'high').length,
            medium: this.violations.filter(v => v.severity === 'medium').length,
            low: this.violations.filter(v => v.severity === 'low').length
        };
        
        // Type distribution
        const typeData = new Map<string, number>();
        this.violations.forEach(v => {
            const type = v.connascenceType;
            typeData.set(type, (typeData.get(type) || 0) + 1);
        });
        
        return {
            severity: severityData,
            types: Object.fromEntries(typeData)
        };
    }
    
    private generateFileAnalysis() {
        // Group violations by file
        const fileMap = new Map<string, ConnascenceViolation[]>();
        this.violations.forEach(v => {
            if (!fileMap.has(v.filePath)) {
                fileMap.set(v.filePath, []);
            }
            fileMap.get(v.filePath)!.push(v);
        });
        
        // Calculate metrics per file
        const fileAnalysis = Array.from(fileMap.entries()).map(([filePath, violations]) => {
            const fileName = path.basename(filePath);
            const critical = violations.filter(v => v.severity === 'critical').length;
            const high = violations.filter(v => v.severity === 'high').length;
            
            // Calculate file connascence index
            const weights = { critical: 10, high: 5, medium: 2, low: 1 };
            const fileIndex = violations.reduce((sum, v) => {
                return sum + (weights[v.severity as keyof typeof weights] || 1);
            }, 0);
            
            return {
                fileName,
                filePath,
                total: violations.length,
                critical,
                high,
                index: fileIndex,
                violations
            };
        }).sort((a, b) => b.index - a.index); // Sort by index descending
        
        return fileAnalysis;
    }
    
    private getWebviewContent(summary: any, chartData: any, fileAnalysis: any): string {
        const config = vscode.workspace.getConfiguration('connascence');
        const theme = vscode.window.activeColorTheme.kind === vscode.ColorThemeKind.Dark ? 'dark' : 'light';
        
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connascence Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            box-sizing: border-box;
        }
        
        body {
            font-family: var(--vscode-font-family);
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
            margin: 0;
            padding: 0;
            line-height: 1.5;
            overflow-x: hidden;
        }
        
        /* Header */
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 25px 15px 25px;
            border-bottom: 1px solid var(--vscode-panel-border);
            background: var(--vscode-editor-background);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .title {
            font-size: 20px;
            font-weight: 600;
            color: var(--vscode-foreground);
        }
        
        .connascence-index {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
        }
        
        .index-badge {
            background: var(--vscode-badge-background);
            color: var(--vscode-badge-foreground);
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: 600;
        }
        
        /* Tab Navigation */
        .tab-navigation {
            background: var(--vscode-tab-inactiveBackground);
            border-bottom: 1px solid var(--vscode-panel-border);
            display: flex;
            overflow-x: auto;
        }
        
        .tab-button {
            background: transparent;
            border: none;
            color: var(--vscode-tab-inactiveForeground);
            padding: 12px 20px;
            cursor: pointer;
            font-size: 14px;
            font-family: inherit;
            white-space: nowrap;
            display: flex;
            align-items: center;
            gap: 8px;
            border-bottom: 2px solid transparent;
            transition: all 0.2s ease;
            min-width: fit-content;
        }
        
        .tab-button:hover {
            background: var(--vscode-tab-hoverBackground);
            color: var(--vscode-tab-activeForeground);
        }
        
        .tab-button.active {
            background: var(--vscode-tab-activeBackground);
            color: var(--vscode-tab-activeForeground);
            border-bottom-color: var(--vscode-focusBorder);
        }
        
        .tab-badge {
            background: var(--vscode-badge-background);
            color: var(--vscode-badge-foreground);
            border-radius: 10px;
            padding: 2px 8px;
            font-size: 11px;
            font-weight: 600;
            min-width: 20px;
            text-align: center;
        }
        
        .tab-badge.critical {
            background: var(--vscode-errorForeground);
            color: white;
        }
        
        .tab-badge.high {
            background: var(--vscode-warningForeground);
            color: black;
        }
        
        /* Tab Content */
        .tab-content {
            display: none;
            padding: 25px;
            animation: fadeIn 0.3s ease;
        }
        
        .tab-content.active {
            display: block;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Cards */
        .summary-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-bottom: 25px;
        }
        
        .card {
            background: var(--vscode-editor-inactiveSelectionBackground);
            border: 1px solid var(--vscode-panel-border);
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        
        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        
        .card-value {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 5px;
        }
        
        .card-label {
            color: var(--vscode-descriptionForeground);
            font-size: 13px;
            text-transform: uppercase;
            font-weight: 500;
        }
        
        .critical { color: var(--vscode-errorForeground); }
        .high { color: var(--vscode-warningForeground); }
        .medium { color: var(--vscode-foreground); }
        .low { color: var(--vscode-descriptionForeground); }
        
        /* Charts */
        .charts-section {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 25px;
            margin-bottom: 25px;
        }
        
        .chart-container {
            background: var(--vscode-editor-inactiveSelectionBackground);
            border: 1px solid var(--vscode-panel-border);
            border-radius: 8px;
            padding: 20px;
        }
        
        .chart-title {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 15px;
            text-align: center;
            color: var(--vscode-foreground);
        }
        
        /* File Analysis */
        .file-analysis, .violation-details, .quality-metrics, .reports-section, .settings-section {
            background: var(--vscode-editor-inactiveSelectionBackground);
            border: 1px solid var(--vscode-panel-border);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .section-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 20px;
            color: var(--vscode-foreground);
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .file-item, .violation-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px;
            margin: 5px 0;
            border-radius: 6px;
            cursor: pointer;
            transition: background-color 0.2s ease;
        }
        
        .file-item:hover, .violation-item:hover {
            background: var(--vscode-list-hoverBackground);
        }
        
        .file-name {
            font-weight: 600;
        }
        
        .file-stats {
            display: flex;
            gap: 15px;
            font-size: 13px;
        }
        
        .violation-item {
            flex-direction: column;
            align-items: flex-start;
            border-left: 4px solid var(--vscode-panel-border);
            background: var(--vscode-input-background);
        }
        
        .violation-item.critical {
            border-left-color: var(--vscode-errorForeground);
        }
        
        .violation-item.high {
            border-left-color: var(--vscode-warningForeground);
        }
        
        .violation-header {
            font-weight: 600;
            margin-bottom: 4px;
        }
        
        .violation-location {
            font-size: 12px;
            color: var(--vscode-descriptionForeground);
        }
        
        /* Filter Controls */
        .filter-controls {
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .filter-select, .filter-input {
            background: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            border: 1px solid var(--vscode-input-border);
            border-radius: 4px;
            padding: 8px 12px;
            font-size: 13px;
            font-family: inherit;
        }
        
        .filter-select:focus, .filter-input:focus {
            outline: none;
            border-color: var(--vscode-focusBorder);
        }
        
        /* Quality Gates */
        .quality-gate {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            margin: 10px 0;
            border-radius: 6px;
            background: var(--vscode-input-background);
        }
        
        .quality-gate.passed {
            border-left: 4px solid #73c991;
        }
        
        .quality-gate.failed {
            border-left: 4px solid var(--vscode-errorForeground);
        }
        
        .gate-name {
            font-weight: 600;
        }
        
        .gate-status {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .gate-status.passed {
            background: #73c991;
            color: white;
        }
        
        .gate-status.failed {
            background: var(--vscode-errorForeground);
            color: white;
        }
        
        /* Buttons */
        .btn {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            cursor: pointer;
            font-size: 13px;
            font-family: inherit;
            transition: background-color 0.2s ease;
        }
        
        .btn:hover {
            background: var(--vscode-button-hoverBackground);
        }
        
        .btn-secondary {
            background: var(--vscode-button-secondaryBackground);
            color: var(--vscode-button-secondaryForeground);
        }
        
        .btn-secondary:hover {
            background: var(--vscode-button-secondaryHoverBackground);
        }
        
        /* Settings */
        .setting-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid var(--vscode-panel-border);
        }
        
        .setting-item:last-child {
            border-bottom: none;
        }
        
        .setting-label {
            font-weight: 500;
        }
        
        .setting-description {
            font-size: 12px;
            color: var(--vscode-descriptionForeground);
            margin-top: 2px;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .charts-section {
                grid-template-columns: 1fr;
            }
            
            .tab-content {
                padding: 15px;
            }
            
            .filter-controls {
                flex-direction: column;
            }
            
            .file-item, .violation-item {
                flex-direction: column;
                align-items: flex-start;
                gap: 8px;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">🔗 Connascence Dashboard</div>
        <div class="connascence-index">
            <span>Index:</span>
            <span class="index-badge">${summary.connascenceIndex.toFixed(1)}</span>
        </div>
    </div>
    
    <div class="tab-navigation">
        <button class="tab-button active" data-tab="overview">
            📊 Overview
        </button>
        <button class="tab-button" data-tab="violations">
            🚨 Violations
            <span class="tab-badge ${summary.critical > 0 ? 'critical' : summary.high > 0 ? 'high' : ''}">${summary.total}</span>
        </button>
        <button class="tab-button" data-tab="quality">
            ⭐ Quality
        </button>
        <button class="tab-button" data-tab="reports">
            📋 Reports
        </button>
        <button class="tab-button" data-tab="settings">
            ⚙️ Settings
        </button>
    </div>
    
    <!-- Overview Tab -->
    <div class="tab-content active" id="overview">
        <div class="summary-cards">
            <div class="card">
                <div class="card-value">${summary.total}</div>
                <div class="card-label">Total Violations</div>
            </div>
            <div class="card">
                <div class="card-value critical">${summary.critical}</div>
                <div class="card-label">Critical</div>
            </div>
            <div class="card">
                <div class="card-value high">${summary.high}</div>
                <div class="card-label">High</div>
            </div>
            <div class="card">
                <div class="card-value medium">${summary.medium}</div>
                <div class="card-label">Medium</div>
            </div>
            <div class="card">
                <div class="card-value low">${summary.low}</div>
                <div class="card-label">Low</div>
            </div>
        </div>
        
        <div class="charts-section">
            <div class="chart-container">
                <div class="chart-title">Severity Distribution</div>
                <canvas id="severityChart" width="300" height="200"></canvas>
            </div>
            <div class="chart-container">
                <div class="chart-title">Connascence Types</div>
                <canvas id="typesChart" width="300" height="200"></canvas>
            </div>
        </div>
        
        <div class="file-analysis">
            <div class="section-title">📁 Top Risk Files</div>
            ${fileAnalysis.slice(0, 5).map((file: any) => `
                <div class="file-item" onclick="openFile('${file.filePath}')">
                    <div class="file-name">${file.fileName}</div>
                    <div class="file-stats">
                        <span>Total: ${file.total}</span>
                        <span class="critical">Critical: ${file.critical}</span>
                        <span class="high">High: ${file.high}</span>
                        <span>Index: ${file.index}</span>
                    </div>
                </div>
            `).join('')}
        </div>
    </div>
    
    <!-- Violations Tab -->
    <div class="tab-content" id="violations">
        <div class="filter-controls">
            <select class="filter-select" id="severityFilter">
                <option value="">All Severities</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
            </select>
            <select class="filter-select" id="typeFilter">
                <option value="">All Types</option>
                ${Object.keys(summary.byType).map(type => `<option value="${type}">${type}</option>`).join('')}
            </select>
            <input type="text" class="filter-input" id="searchFilter" placeholder="Search violations...">
        </div>
        
        <div class="file-analysis">
            <div class="section-title">📁 Files by Impact</div>
            <div id="fileList">
                ${fileAnalysis.map((file: any) => `
                    <div class="file-item" onclick="openFile('${file.filePath}')" data-severity="${file.critical > 0 ? 'critical' : file.high > 0 ? 'high' : 'medium'}">
                        <div class="file-name">${file.fileName}</div>
                        <div class="file-stats">
                            <span>Total: ${file.total}</span>
                            <span class="critical">Critical: ${file.critical}</span>
                            <span class="high">High: ${file.high}</span>
                            <span>Index: ${file.index}</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
        
        <div class="violation-details">
            <div class="section-title">🔍 All Violations</div>
            <div id="violationList">
                ${this.violations.map(v => `
                    <div class="violation-item ${v.severity}" onclick="gotoViolation('${v.filePath}', ${v.lineNumber})" 
                         data-severity="${v.severity}" data-type="${v.connascenceType}" data-search="${v.description.toLowerCase()}">
                        <div class="violation-header">${v.connascenceType} - ${v.description}</div>
                        <div class="violation-location">${path.basename(v.filePath)}:${v.lineNumber}</div>
                    </div>
                `).join('')}
            </div>
        </div>
    </div>
    
    <!-- Quality Tab -->
    <div class="tab-content" id="quality">
        <div class="quality-metrics">
            <div class="section-title">⭐ Quality Gates</div>
            <div class="quality-gate ${summary.critical === 0 ? 'passed' : 'failed'}">
                <div>
                    <div class="gate-name">No Critical Issues</div>
                    <div class="setting-description">Project must have zero critical connascence violations</div>
                </div>
                <div class="gate-status ${summary.critical === 0 ? 'passed' : 'failed'}">
                    ${summary.critical === 0 ? 'PASSED' : 'FAILED'}
                </div>
            </div>
            
            <div class="quality-gate ${summary.connascenceIndex < 50 ? 'passed' : 'failed'}">
                <div>
                    <div class="gate-name">Connascence Index < 50</div>
                    <div class="setting-description">Overall project connascence should be manageable</div>
                </div>
                <div class="gate-status ${summary.connascenceIndex < 50 ? 'passed' : 'failed'}">
                    ${summary.connascenceIndex < 50 ? 'PASSED' : 'FAILED'}
                </div>
            </div>
            
            <div class="quality-gate ${(summary.high + summary.critical) < Math.max(1, summary.total * 0.2) ? 'passed' : 'failed'}">
                <div>
                    <div class="gate-name">High Severity < 20%</div>
                    <div class="setting-description">Less than 20% of violations should be high or critical</div>
                </div>
                <div class="gate-status ${(summary.high + summary.critical) < Math.max(1, summary.total * 0.2) ? 'passed' : 'failed'}">
                    ${(summary.high + summary.critical) < Math.max(1, summary.total * 0.2) ? 'PASSED' : 'FAILED'}
                </div>
            </div>
        </div>
        
        <div class="quality-metrics">
            <div class="section-title">📈 Quality Trends</div>
            <div class="chart-container">
                <div class="chart-title">Connascence Index: ${summary.connascenceIndex.toFixed(1)}</div>
                <div style="text-align: center; padding: 40px 0; color: var(--vscode-descriptionForeground);">
                    Quality trends will be available after multiple analysis runs
                </div>
            </div>
        </div>
        
        <div class="quality-metrics">
            <div class="section-title">ℹ️ About Connascence</div>
            <p><strong>Connascence</strong> measures the strength of coupling between software components. Lower connascence indicates better maintainability and flexibility.</p>
            
            <h4>Types Detected:</h4>
            <ul>
                <li><strong>CoM (Meaning):</strong> Magic literals and unclear values</li>
                <li><strong>CoP (Position):</strong> Parameter order dependencies</li>
                <li><strong>CoT (Type):</strong> Missing or unclear type information</li>
                <li><strong>CoA (Algorithm):</strong> Duplicated or complex logic</li>
                <li><strong>CoN (Name):</strong> Name dependencies between components</li>
            </ul>
        </div>
    </div>
    
    <!-- Reports Tab -->
    <div class="tab-content" id="reports">
        <div class="reports-section">
            <div class="section-title">📋 Export Reports</div>
            <div style="display: flex; gap: 12px; margin-bottom: 20px;">
                <button class="btn" onclick="exportReport('json')">Export JSON</button>
                <button class="btn" onclick="exportReport('csv')">Export CSV</button>
                <button class="btn" onclick="exportReport('html')">Export HTML</button>
            </div>
            
            <div class="section-title">📊 Analysis Summary</div>
            <div style="background: var(--vscode-input-background); padding: 15px; border-radius: 6px; font-family: monospace; font-size: 12px;">
                <div>Analysis Date: ${new Date().toLocaleString()}</div>
                <div>Total Files Analyzed: ${fileAnalysis.length}</div>
                <div>Total Violations: ${summary.total}</div>
                <div>Connascence Index: ${summary.connascenceIndex.toFixed(1)}</div>
                <div>Most Common Type: ${summary.topTypes[0] ? summary.topTypes[0][0] : 'None'}</div>
            </div>
        </div>
        
        <div class="reports-section">
            <div class="section-title">🕒 Analysis History</div>
            <div style="text-align: center; padding: 40px 0; color: var(--vscode-descriptionForeground);">
                Analysis history will be available in future versions
            </div>
        </div>
    </div>
    
    <!-- Settings Tab -->
    <div class="tab-content" id="settings">
        <div class="settings-section">
            <div class="section-title">⚙️ Analysis Settings</div>
            
            <div class="setting-item">
                <div>
                    <div class="setting-label">Enable Critical Violations</div>
                    <div class="setting-description">Show violations with critical severity</div>
                </div>
                <input type="checkbox" checked>
            </div>
            
            <div class="setting-item">
                <div>
                    <div class="setting-label">Maximum Connascence Index</div>
                    <div class="setting-description">Threshold for quality gate failure</div>
                </div>
                <input type="number" value="50" style="width: 80px; background: var(--vscode-input-background); color: var(--vscode-input-foreground); border: 1px solid var(--vscode-input-border); border-radius: 4px; padding: 4px 8px;">
            </div>
            
            <div class="setting-item">
                <div>
                    <div class="setting-label">Auto-refresh Dashboard</div>
                    <div class="setting-description">Automatically update when files change</div>
                </div>
                <input type="checkbox" checked>
            </div>
            
            <div class="setting-item">
                <div>
                    <div class="setting-label">Show Quality Notifications</div>
                    <div class="setting-description">Display notifications for quality gate changes</div>
                </div>
                <input type="checkbox">
            </div>
        </div>
        
        <div class="settings-section">
            <div class="section-title">🎨 Display Preferences</div>
            
            <div class="setting-item">
                <div>
                    <div class="setting-label">Default Tab</div>
                    <div class="setting-description">Tab to show when opening dashboard</div>
                </div>
                <select class="filter-select">
                    <option value="overview">Overview</option>
                    <option value="violations">Violations</option>
                    <option value="quality">Quality</option>
                </select>
            </div>
            
            <div class="setting-item">
                <div>
                    <div class="setting-label">Items per Page</div>
                    <div class="setting-description">Number of violations to show at once</div>
                </div>
                <select class="filter-select">
                    <option value="10">10</option>
                    <option value="25" selected>25</option>
                    <option value="50">50</option>
                    <option value="100">100</option>
                </select>
            </div>
        </div>
    </div>
    
    <script>
        // Tab switching functionality
        document.addEventListener('DOMContentLoaded', function() {
            const tabButtons = document.querySelectorAll('.tab-button');
            const tabContents = document.querySelectorAll('.tab-content');
            
            tabButtons.forEach(button => {
                button.addEventListener('click', () => {
                    const targetTab = button.dataset.tab;
                    
                    // Update active button
                    tabButtons.forEach(b => b.classList.remove('active'));
                    button.classList.add('active');
                    
                    // Update active content
                    tabContents.forEach(content => {
                        content.classList.remove('active');
                        if (content.id === targetTab) {
                            content.classList.add('active');
                            
                            // Initialize charts for overview tab
                            if (targetTab === 'overview') {
                                setTimeout(initializeCharts, 100);
                            }
                        }
                    });
                });
            });
            
            // Initialize charts on load
            initializeCharts();
            
            // Setup filters
            setupFilters();
        });
        
        function initializeCharts() {
            // Only initialize if elements exist and are visible
            const severityCanvas = document.getElementById('severityChart');
            const typesCanvas = document.getElementById('typesChart');
            
            if (!severityCanvas || !typesCanvas) return;
            
            // Destroy existing charts if they exist
            if (window.severityChart) {
                window.severityChart.destroy();
            }
            if (window.typesChart) {
                window.typesChart.destroy();
            }
            
            // Severity Chart
            const severityCtx = severityCanvas.getContext('2d');
            window.severityChart = new Chart(severityCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Critical', 'High', 'Medium', 'Low'],
                    datasets: [{
                        data: [${chartData.severity.critical}, ${chartData.severity.high}, ${chartData.severity.medium}, ${chartData.severity.low}],
                        backgroundColor: [
                            '#f14c4c', // Critical - red
                            '#ff8c00', // High - orange  
                            '#ffcd3c', // Medium - yellow
                            '#73c991'  // Low - green
                        ],
                        borderWidth: 2,
                        borderColor: '${theme === 'dark' ? '#333' : '#fff'}'
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: 'var(--vscode-foreground)',
                                usePointStyle: true,
                                padding: 15
                            }
                        }
                    }
                }
            });
            
            // Types Chart
            const typesCtx = typesCanvas.getContext('2d');
            const typeLabels = ${JSON.stringify(Object.keys(chartData.types))};
            const typeData = ${JSON.stringify(Object.values(chartData.types))};
            
            window.typesChart = new Chart(typesCtx, {
                type: 'bar',
                data: {
                    labels: typeLabels,
                    datasets: [{
                        label: 'Violations',
                        data: typeData,
                        backgroundColor: '#007acc',
                        borderColor: '#005a9e',
                        borderWidth: 1,
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                color: 'var(--vscode-foreground)',
                                stepSize: 1
                            }
                        },
                        x: {
                            ticks: {
                                color: 'var(--vscode-foreground)'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            labels: {
                                color: 'var(--vscode-foreground)'
                            }
                        }
                    }
                }
            });
        }
        
        function setupFilters() {
            const severityFilter = document.getElementById('severityFilter');
            const typeFilter = document.getElementById('typeFilter');
            const searchFilter = document.getElementById('searchFilter');
            
            if (!severityFilter || !typeFilter || !searchFilter) return;
            
            function applyFilters() {
                const severity = severityFilter.value;
                const type = typeFilter.value;
                const search = searchFilter.value.toLowerCase();
                
                // Filter violations
                const violationItems = document.querySelectorAll('#violationList .violation-item');
                violationItems.forEach(item => {
                    const itemSeverity = item.dataset.severity;
                    const itemType = item.dataset.type;
                    const itemSearch = item.dataset.search;
                    
                    const matchesSeverity = !severity || itemSeverity === severity;
                    const matchesType = !type || itemType === type;
                    const matchesSearch = !search || itemSearch.includes(search);
                    
                    item.style.display = matchesSeverity && matchesType && matchesSearch ? 'flex' : 'none';
                });
                
                // Filter files
                const fileItems = document.querySelectorAll('#fileList .file-item');
                fileItems.forEach(item => {
                    const itemSeverity = item.dataset.severity;
                    const matchesSeverity = !severity || itemSeverity === severity;
                    item.style.display = matchesSeverity ? 'flex' : 'none';
                });
            }
            
            severityFilter.addEventListener('change', applyFilters);
            typeFilter.addEventListener('change', applyFilters);
            searchFilter.addEventListener('input', applyFilters);
        }
        
        // VS Code API
        const vscode = acquireVsCodeApi();
        
        function openFile(filePath) {
            vscode.postMessage({
                type: 'openFile',
                filePath: filePath
            });
        }
        
        function gotoViolation(filePath, lineNumber) {
            vscode.postMessage({
                type: 'gotoViolation',
                filePath: filePath,
                lineNumber: lineNumber
            });
        }
        
        function exportReport(format) {
            vscode.postMessage({
                type: 'exportReport',
                format: format
            });
        }
        
        // Listen for messages from extension
        window.addEventListener('message', event => {
            const message = event.data;
            switch (message.type) {
                case 'focusViolation':
                    // Switch to violations tab and focus on specific violation
                    const violationsTab = document.querySelector('[data-tab="violations"]');
                    if (violationsTab) {
                        violationsTab.click();
                    }
                    
                    const violation = message.violation;
                    // Scroll to the violation in the UI
                    setTimeout(() => {
                        const violationElements = document.querySelectorAll('.violation-item');
                        violationElements.forEach(el => {
                            if (el.textContent.includes(violation.description)) {
                                el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                el.style.background = 'var(--vscode-focusBorder)';
                                setTimeout(() => {
                                    el.style.background = '';
                                }, 2000);
                            }
                        });
                    }, 300);
                    break;
            }
        });
    </script>
</body>
</html>`;
    }
    
    private exportReport(format: string): void {
        const summary = this.generateSummary();
        const fileAnalysis = this.generateFileAnalysis();
        const timestamp = new Date().toISOString().replace(/:/g, '-').split('.')[0];
        
        let content = '';
        let filename = '';
        let contentType = '';
        
        switch (format) {
            case 'json':
                content = JSON.stringify({
                    timestamp: new Date().toISOString(),
                    summary,
                    fileAnalysis,
                    violations: this.violations
                }, null, 2);
                filename = `connascence-report-${timestamp}.json`;
                contentType = 'application/json';
                break;
                
            case 'csv':
                const csvHeaders = 'File,Line,Type,Severity,Description\n';
                const csvRows = this.violations.map(v => 
                    `"${v.filePath}",${v.lineNumber},"${v.connascenceType}","${v.severity}","${v.description}"`
                ).join('\n');
                content = csvHeaders + csvRows;
                filename = `connascence-violations-${timestamp}.csv`;
                contentType = 'text/csv';
                break;
                
            case 'html':
                content = this.generateHtmlReport(summary, fileAnalysis);
                filename = `connascence-report-${timestamp}.html`;
                contentType = 'text/html';
                break;
        }
        
        if (content) {
            vscode.workspace.fs.writeFile(
                vscode.Uri.file(vscode.workspace.workspaceFolders?.[0]?.uri.fsPath + '/' + filename),
                Buffer.from(content)
            ).then(() => {
                vscode.window.showInformationMessage(`Report exported: ${filename}`);
            }).catch(error => {
                vscode.window.showErrorMessage(`Failed to export report: ${error.message}`);
            });
        }
    }
    
    private generateHtmlReport(summary: any, fileAnalysis: any): string {
        return `<!DOCTYPE html>
<html>
<head>
    <title>Connascence Analysis Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { border: 1px solid #ddd; border-radius: 8px; padding: 20px; text-align: center; }
        .critical { color: #d73a49; }
        .high { color: #fb8500; }
        .medium { color: #ffd60a; }
        .low { color: #52b788; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #f6f8fa; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Connascence Analysis Report</h1>
        <p>Generated on ${new Date().toLocaleString()}</p>
        <p><strong>Connascence Index:</strong> ${summary.connascenceIndex.toFixed(1)}</p>
    </div>
    
    <div class="summary">
        <div class="card">
            <h3>${summary.total}</h3>
            <p>Total Violations</p>
        </div>
        <div class="card">
            <h3 class="critical">${summary.critical}</h3>
            <p>Critical</p>
        </div>
        <div class="card">
            <h3 class="high">${summary.high}</h3>
            <p>High</p>
        </div>
        <div class="card">
            <h3 class="medium">${summary.medium}</h3>
            <p>Medium</p>
        </div>
        <div class="card">
            <h3 class="low">${summary.low}</h3>
            <p>Low</p>
        </div>
    </div>
    
    <h2>File Analysis</h2>
    <table>
        <thead>
            <tr>
                <th>File</th>
                <th>Total</th>
                <th>Critical</th>
                <th>High</th>
                <th>Index</th>
            </tr>
        </thead>
        <tbody>
            ${fileAnalysis.map((file: any) => `
                <tr>
                    <td>${file.fileName}</td>
                    <td>${file.total}</td>
                    <td class="critical">${file.critical}</td>
                    <td class="high">${file.high}</td>
                    <td>${file.index}</td>
                </tr>
            `).join('')}
        </tbody>
    </table>
    
    <h2>All Violations</h2>
    <table>
        <thead>
            <tr>
                <th>File</th>
                <th>Line</th>
                <th>Type</th>
                <th>Severity</th>
                <th>Description</th>
            </tr>
        </thead>
        <tbody>
            ${this.violations.map(v => `
                <tr>
                    <td>${path.basename(v.filePath)}</td>
                    <td>${v.lineNumber}</td>
                    <td>${v.connascenceType}</td>
                    <td class="${v.severity}">${v.severity}</td>
                    <td>${v.description}</td>
                </tr>
            `).join('')}
        </tbody>
    </table>
</body>
</html>`;
    }
    
    dispose(): void {
        if (this.panel) {
            this.panel.dispose();
        }
    }
}