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
        body {
            font-family: var(--vscode-font-family);
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
            margin: 0;
            padding: 20px;
            line-height: 1.5;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            border-bottom: 1px solid var(--vscode-panel-border);
            padding-bottom: 20px;
        }
        .title {
            font-size: 24px;
            font-weight: bold;
        }
        .summary-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: var(--vscode-editor-inactiveSelectionBackground);
            border: 1px solid var(--vscode-panel-border);
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }
        .card-value {
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .card-label {
            color: var(--vscode-descriptionForeground);
            font-size: 14px;
        }
        .critical { color: var(--vscode-errorForeground); }
        .high { color: var(--vscode-warningForeground); }
        .medium { color: var(--vscode-foreground); }
        .low { color: var(--vscode-descriptionForeground); }
        
        .charts-section {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }
        .chart-container {
            background: var(--vscode-editor-inactiveSelectionBackground);
            border: 1px solid var(--vscode-panel-border);
            border-radius: 8px;
            padding: 20px;
        }
        .chart-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 15px;
            text-align: center;
        }
        
        .file-analysis {
            background: var(--vscode-editor-inactiveSelectionBackground);
            border: 1px solid var(--vscode-panel-border);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 30px;
        }
        .file-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid var(--vscode-panel-border);
            cursor: pointer;
        }
        .file-item:hover {
            background: var(--vscode-list-hoverBackground);
        }
        .file-name {
            font-weight: bold;
        }
        .file-stats {
            display: flex;
            gap: 15px;
            font-size: 14px;
        }
        
        .violation-details {
            background: var(--vscode-editor-inactiveSelectionBackground);
            border: 1px solid var(--vscode-panel-border);
            border-radius: 8px;
            padding: 20px;
        }
        .violation-item {
            padding: 10px;
            margin: 5px 0;
            border-left: 4px solid var(--vscode-panel-border);
            background: var(--vscode-input-background);
            border-radius: 4px;
        }
        .violation-item.critical {
            border-left-color: var(--vscode-errorForeground);
        }
        .violation-item.high {
            border-left-color: var(--vscode-warningForeground);
        }
        
        .connascence-explanation {
            background: var(--vscode-textBlockQuote-background);
            border: 1px solid var(--vscode-textBlockQuote-border);
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
        }
        
        @media (max-width: 768px) {
            .charts-section {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">🔗 Connascence Dashboard</div>
        <div class="connascence-index">
            <strong>Index: ${summary.connascenceIndex.toFixed(1)}</strong>
        </div>
    </div>
    
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
        <h3>📁 File Analysis</h3>
        ${fileAnalysis.map((file: any) => `
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
    
    <div class="violation-details">
        <h3>🔍 Recent Violations</h3>
        ${this.violations.slice(0, 10).map(v => `
            <div class="violation-item ${v.severity}" onclick="gotoViolation('${v.filePath}', ${v.lineNumber})">
                <strong>${v.connascenceType}</strong> - ${v.description}
                <br>
                <small>${path.basename(v.filePath)}:${v.lineNumber}</small>
            </div>
        `).join('')}
    </div>
    
    <div class="connascence-explanation">
        <h3>ℹ️ About Connascence</h3>
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
    
    <script>
        // Severity Chart
        const severityCtx = document.getElementById('severityChart').getContext('2d');
        new Chart(severityCtx, {
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
                            color: 'var(--vscode-foreground)'
                        }
                    }
                }
            }
        });
        
        // Types Chart
        const typesCtx = document.getElementById('typesChart').getContext('2d');
        const typeLabels = ${JSON.stringify(Object.keys(chartData.types))};
        const typeData = ${JSON.stringify(Object.values(chartData.types))};
        
        new Chart(typesCtx, {
            type: 'bar',
            data: {
                labels: typeLabels,
                datasets: [{
                    label: 'Violations',
                    data: typeData,
                    backgroundColor: '#007acc',
                    borderColor: '#005a9e',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: 'var(--vscode-foreground)'
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
        
        // Listen for messages from extension
        window.addEventListener('message', event => {
            const message = event.data;
            switch (message.type) {
                case 'focusViolation':
                    // Scroll to and highlight specific violation
                    const violation = message.violation;
                    // Implementation would scroll to the violation in the UI
                    break;
            }
        });
    </script>
</body>
</html>`;
    }
    
    dispose(): void {
        if (this.panel) {
            this.panel.dispose();
        }
    }
}