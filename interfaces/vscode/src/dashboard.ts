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
                        this.exportReport(message.format, message.options);
                        break;
                    case 'exportMultiFormat':
                        this.exportMultiFormatReport(message.formats, message.options);
                        break;
                    case 'previewReport':
                        this.previewReport(message.format);
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
        
        /* Quality Gates Enhanced */
        .quality-gates-dashboard {
            margin-bottom: 30px;
        }
        
        .gates-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
        }
        
        .gate-card {
            background: var(--vscode-editor-inactiveSelectionBackground);
            border: 1px solid var(--vscode-panel-border);
            border-radius: 12px;
            padding: 20px;
            position: relative;
            transition: all 0.3s ease;
        }
        
        .gate-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }
        
        .gate-card.passed {
            border-left: 4px solid #28a745;
            background: linear-gradient(145deg, var(--vscode-editor-inactiveSelectionBackground), rgba(40, 167, 69, 0.05));
        }
        
        .gate-card.warning {
            border-left: 4px solid #ffc107;
            background: linear-gradient(145deg, var(--vscode-editor-inactiveSelectionBackground), rgba(255, 193, 7, 0.05));
        }
        
        .gate-card.failed {
            border-left: 4px solid #dc3545;
            background: linear-gradient(145deg, var(--vscode-editor-inactiveSelectionBackground), rgba(220, 53, 69, 0.05));
        }
        
        .gate-icon {
            font-size: 24px;
            margin-bottom: 10px;
        }
        
        .gate-content {
            flex: 1;
        }
        
        .gate-name {
            font-weight: 600;
            font-size: 16px;
            margin-bottom: 5px;
            color: var(--vscode-foreground);
        }
        
        .gate-description {
            font-size: 13px;
            color: var(--vscode-descriptionForeground);
            margin-bottom: 15px;
        }
        
        .gate-metrics {
            display: flex;
            align-items: baseline;
            gap: 5px;
            margin-bottom: 15px;
        }
        
        .metric-value {
            font-size: 24px;
            font-weight: bold;
        }
        
        .metric-value.success {
            color: #28a745;
        }
        
        .metric-value.warning {
            color: #ffc107;
        }
        
        .metric-value.error {
            color: #dc3545;
        }
        
        .metric-threshold {
            font-size: 14px;
            color: var(--vscode-descriptionForeground);
        }
        
        .threshold-progress {
            margin-top: 10px;
        }
        
        .progress-bar {
            height: 8px;
            background: var(--vscode-panel-border);
            border-radius: 4px;
            position: relative;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.8s ease;
        }
        
        .progress-fill.success {
            background: linear-gradient(90deg, #28a745, #20c997);
        }
        
        .progress-fill.warning {
            background: linear-gradient(90deg, #ffc107, #fd7e14);
        }
        
        .progress-fill.error {
            background: linear-gradient(90deg, #dc3545, #e74c3c);
        }
        
        .progress-threshold {
            position: absolute;
            top: 0;
            width: 2px;
            height: 100%;
            background: var(--vscode-foreground);
            opacity: 0.7;
        }
        
        .progress-labels {
            display: flex;
            justify-content: space-between;
            margin-top: 5px;
            font-size: 11px;
            color: var(--vscode-descriptionForeground);
        }
        
        .gate-status-badge {
            position: absolute;
            top: 15px;
            right: 15px;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .gate-status-badge.passed {
            background: #28a745;
            color: white;
        }
        
        .gate-status-badge.warning {
            background: #ffc107;
            color: #212529;
        }
        
        .gate-status-badge.failed {
            background: #dc3545;
            color: white;
        }
        
        /* Heat Map Styles */
        .heat-map-container {
            background: var(--vscode-editor-inactiveSelectionBackground);
            border-radius: 8px;
            padding: 20px;
        }
        
        .heat-map-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 8px;
            margin-bottom: 15px;
        }
        
        .heat-map-cell {
            aspect-ratio: 1;
            border-radius: 8px;
            padding: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            font-size: 11px;
            position: relative;
            overflow: hidden;
        }
        
        .heat-map-cell:hover {
            transform: scale(1.05);
            z-index: 10;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }
        
        .heat-map-cell.low {
            background: linear-gradient(135deg, #d4edda, #c3e6cb);
            color: #155724;
        }
        
        .heat-map-cell.medium {
            background: linear-gradient(135deg, #fff3cd, #ffeeba);
            color: #856404;
        }
        
        .heat-map-cell.high {
            background: linear-gradient(135deg, #f8d7da, #f5c6cb);
            color: #721c24;
        }
        
        .heat-map-cell.critical {
            background: linear-gradient(135deg, #dc3545, #c82333);
            color: white;
        }
        
        .cell-name {
            font-weight: 600;
            word-wrap: break-word;
        }
        
        .cell-score {
            font-size: 16px;
            font-weight: bold;
            text-align: center;
        }
        
        .heat-map-legend {
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
        }
        
        .legend-color {
            width: 16px;
            height: 16px;
            border-radius: 4px;
        }
        
        .legend-color.low {
            background: #28a745;
        }
        
        .legend-color.medium {
            background: #ffc107;
        }
        
        .legend-color.high {
            background: #fd7e14;
        }
        
        .legend-color.critical {
            background: #dc3545;
        }
        
        /* Impact Analysis Styles */
        .impact-analysis {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        
        .impact-item {
            border-radius: 8px;
            padding: 20px;
            border-left: 4px solid;
        }
        
        .impact-item.critical {
            background: rgba(220, 53, 69, 0.1);
            border-left-color: #dc3545;
        }
        
        .impact-item.warning {
            background: rgba(255, 193, 7, 0.1);
            border-left-color: #ffc107;
        }
        
        .impact-item.error {
            background: rgba(220, 53, 69, 0.1);
            border-left-color: #dc3545;
        }
        
        .impact-item.success {
            background: rgba(40, 167, 69, 0.1);
            border-left-color: #28a745;
        }
        
        .impact-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 10px;
        }
        
        .impact-icon {
            font-size: 20px;
        }
        
        .impact-title {
            font-weight: 600;
            font-size: 16px;
            flex: 1;
        }
        
        .impact-count {
            font-weight: bold;
            padding: 4px 12px;
            border-radius: 20px;
            background: var(--vscode-badge-background);
            color: var(--vscode-badge-foreground);
            font-size: 12px;
        }
        
        .impact-details {
            margin-left: 32px;
        }
        
        .blocking-files {
            font-size: 13px;
            color: var(--vscode-descriptionForeground);
            margin-bottom: 8px;
        }
        
        .impact-suggestion {
            font-size: 14px;
            line-height: 1.4;
        }
        
        /* Roadmap Styles */
        .roadmap-container {
            background: var(--vscode-editor-inactiveSelectionBackground);
            border-radius: 8px;
            padding: 20px;
        }
        
        .roadmap-steps {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        
        .roadmap-step {
            display: flex;
            align-items: flex-start;
            gap: 15px;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid var(--vscode-panel-border);
            transition: all 0.3s ease;
        }
        
        .roadmap-step.active {
            background: rgba(13, 110, 253, 0.1);
            border-color: #0d6efd;
        }
        
        .roadmap-step.completed {
            background: rgba(40, 167, 69, 0.1);
            border-color: #28a745;
            opacity: 0.8;
        }
        
        .roadmap-step.critical {
            background: rgba(220, 53, 69, 0.1);
            border-color: #dc3545;
        }
        
        .roadmap-step.high {
            background: rgba(255, 193, 7, 0.1);
            border-color: #ffc107;
        }
        
        .roadmap-step.warning {
            background: rgba(255, 193, 7, 0.1);
            border-color: #ffc107;
        }
        
        .roadmap-step.info {
            background: rgba(13, 202, 240, 0.1);
            border-color: #0dcaf0;
        }
        
        .step-number {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            flex-shrink: 0;
        }
        
        .roadmap-step.completed .step-number {
            background: #28a745;
            color: white;
        }
        
        .roadmap-step.active .step-number {
            background: #0d6efd;
            color: white;
        }
        
        .step-content {
            flex: 1;
        }
        
        .step-title {
            font-weight: 600;
            font-size: 16px;
            margin-bottom: 5px;
        }
        
        .step-description {
            font-size: 14px;
            color: var(--vscode-descriptionForeground);
            margin-bottom: 10px;
        }
        
        .step-actions {
            display: flex;
            gap: 10px;
        }
        
        .step-action {
            background: var(--vscode-button-secondaryBackground);
            color: var(--vscode-button-secondaryForeground);
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .step-action:hover {
            background: var(--vscode-button-secondaryHoverBackground);
        }
        
        .step-status {
            font-size: 12px;
            font-weight: 600;
            padding: 6px 12px;
            border-radius: 20px;
            background: var(--vscode-badge-background);
            color: var(--vscode-badge-foreground);
            flex-shrink: 0;
        }
        
        /* Custom Gates Styles */
        .custom-gates {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 25px;
        }
        
        .custom-gate-form {
            background: var(--vscode-input-background);
            border: 1px solid var(--vscode-panel-border);
            border-radius: 8px;
            padding: 20px;
        }
        
        .custom-gate-form h4 {
            margin-bottom: 15px;
            color: var(--vscode-foreground);
        }
        
        .form-row {
            display: flex;
            flex-direction: column;
            margin-bottom: 15px;
        }
        
        .form-row label {
            font-weight: 500;
            margin-bottom: 5px;
            font-size: 13px;
        }
        
        .form-row input,
        .form-row select {
            background: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            border: 1px solid var(--vscode-input-border);
            border-radius: 4px;
            padding: 8px 12px;
            font-size: 13px;
            font-family: inherit;
        }
        
        .form-row input:focus,
        .form-row select:focus {
            outline: none;
            border-color: var(--vscode-focusBorder);
        }
        
        .custom-gates-list {
            background: var(--vscode-input-background);
            border: 1px solid var(--vscode-panel-border);
            border-radius: 8px;
            padding: 20px;
        }
        
        .custom-gates-list h4 {
            margin-bottom: 15px;
            color: var(--vscode-foreground);
        }
        
        .empty-state {
            text-align: center;
            color: var(--vscode-descriptionForeground);
            font-style: italic;
            padding: 40px 20px;
        }
        
        /* Trends and Benchmarks */
        .trends-container {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 25px;
        }
        
        .trend-chart-placeholder {
            background: var(--vscode-editor-inactiveSelectionBackground);
            border: 1px solid var(--vscode-panel-border);
            border-radius: 8px;
            padding: 20px;
        }
        
        .chart-title {
            font-weight: 600;
            margin-bottom: 15px;
        }
        
        .placeholder-content {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .trend-line {
            flex: 1;
        }
        
        .trend-info {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        
        .current-score {
            text-align: center;
        }
        
        .score-value {
            font-size: 36px;
            font-weight: bold;
            color: var(--vscode-foreground);
        }
        
        .score-label {
            font-size: 14px;
            color: var(--vscode-descriptionForeground);
        }
        
        .trend-indicators {
            display: flex;
            justify-content: center;
        }
        
        .trend-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 5px;
        }
        
        .trend-arrow {
            font-size: 24px;
        }
        
        .benchmark-comparison {
            background: var(--vscode-editor-inactiveSelectionBackground);
            border: 1px solid var(--vscode-panel-border);
            border-radius: 8px;
            padding: 20px;
        }
        
        .benchmark-title {
            font-weight: 600;
            margin-bottom: 15px;
        }
        
        .benchmark-items {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        
        .benchmark-item {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        .benchmark-label {
            font-size: 13px;
            font-weight: 500;
        }
        
        .benchmark-bar {
            height: 8px;
            background: var(--vscode-panel-border);
            border-radius: 4px;
            overflow: hidden;
        }
        
        .benchmark-fill {
            height: 100%;
            transition: width 0.8s ease;
            border-radius: 4px;
        }
        
        .benchmark-fill.success {
            background: #28a745;
        }
        
        .benchmark-fill.error {
            background: #dc3545;
        }
        
        .benchmark-item.excellent .benchmark-fill {
            background: linear-gradient(90deg, #28a745, #20c997);
        }
        
        .benchmark-item.good .benchmark-fill {
            background: linear-gradient(90deg, #20c997, #17a2b8);
        }
        
        .benchmark-item.needs-work .benchmark-fill {
            background: linear-gradient(90deg, #ffc107, #fd7e14);
        }
        
        .benchmark-score {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            color: var(--vscode-descriptionForeground);
        }
        
        /* Info Panels */
        .info-panels {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 25px;
        }
        
        .info-panel {
            background: var(--vscode-editor-inactiveSelectionBackground);
            border: 1px solid var(--vscode-panel-border);
            border-radius: 8px;
            padding: 20px;
        }
        
        .info-panel h4 {
            margin-bottom: 10px;
            color: var(--vscode-foreground);
        }
        
        .info-panel p {
            color: var(--vscode-descriptionForeground);
            line-height: 1.5;
            margin-bottom: 15px;
        }
        
        .info-panel ul {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .info-panel li {
            margin-bottom: 8px;
            padding-left: 20px;
            position: relative;
            color: var(--vscode-foreground);
            line-height: 1.4;
        }
        
        .info-panel li:before {
            content: "•";
            color: var(--vscode-focusBorder);
            position: absolute;
            left: 0;
            font-weight: bold;
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
        @media (max-width: 1200px) {
            .gates-grid {
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            }
            
            .custom-gates {
                grid-template-columns: 1fr;
            }
            
            .trends-container {
                grid-template-columns: 1fr;
            }
            
            .info-panels {
                grid-template-columns: 1fr;
            }
        }
        
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
            
            .gates-grid {
                grid-template-columns: 1fr;
                gap: 15px;
            }
            
            .gate-card {
                padding: 15px;
            }
            
            .heat-map-grid {
                grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
                gap: 6px;
            }
            
            .roadmap-step {
                flex-direction: column;
                gap: 10px;
                align-items: flex-start;
            }
            
            .step-number {
                align-self: flex-start;
            }
            
            .step-status {
                align-self: flex-end;
            }
            
            .impact-header {
                flex-direction: column;
                align-items: flex-start;
                gap: 8px;
            }
            
            .benchmark-items {
                gap: 10px;
            }
            
            .form-row {
                margin-bottom: 12px;
            }
            
            .form-row input,
            .form-row select {
                padding: 10px;
                font-size: 14px;
            }
        }
        
        @media (max-width: 480px) {
            .header {
                flex-direction: column;
                gap: 10px;
                text-align: center;
            }
            
            .title {
                font-size: 18px;
            }
            
            .tab-navigation {
                justify-content: center;
            }
            
            .tab-button {
                padding: 10px 15px;
                font-size: 13px;
            }
            
            .summary-cards {
                grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
                gap: 12px;
            }
            
            .card-value {
                font-size: 24px;
            }
            
            .gate-metrics {
                flex-direction: column;
                align-items: flex-start;
                gap: 5px;
            }
            
            .metric-value {
                font-size: 20px;
            }
            
            .heat-map-grid {
                grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
            }
            
            .heat-map-legend {
                flex-direction: column;
                align-items: center;
                gap: 10px;
            }
            
            .placeholder-content {
                flex-direction: column;
                gap: 15px;
            }
            
            .current-score .score-value {
                font-size: 28px;
            }
            
            .roadmap-steps {
                gap: 12px;
            }
            
            .step-actions {
                flex-direction: column;
                gap: 8px;
            }
            
            .step-action {
                width: 100%;
                text-align: center;
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
        <!-- Quality Gates Status Dashboard -->
        <div class="quality-gates-dashboard">
            <div class="section-title">🎯 Quality Gates Status</div>
            <div class="gates-grid">
                <div class="gate-card ${summary.critical === 0 ? 'passed' : 'failed'}">
                    <div class="gate-icon">${summary.critical === 0 ? '✅' : '❌'}</div>
                    <div class="gate-content">
                        <div class="gate-name">Critical Issues Gate</div>
                        <div class="gate-description">Zero critical violations required</div>
                        <div class="gate-metrics">
                            <div class="metric-value ${summary.critical === 0 ? 'success' : 'error'}">${summary.critical}</div>
                            <div class="metric-threshold">/ 0 allowed</div>
                        </div>
                    </div>
                    <div class="gate-status-badge ${summary.critical === 0 ? 'passed' : 'failed'}">
                        ${summary.critical === 0 ? 'PASSED' : 'FAILED'}
                    </div>
                </div>
                
                <div class="gate-card ${summary.connascenceIndex < 50 ? 'passed' : summary.connascenceIndex < 75 ? 'warning' : 'failed'}">
                    <div class="gate-icon">${summary.connascenceIndex < 50 ? '✅' : summary.connascenceIndex < 75 ? '⚠️' : '❌'}</div>
                    <div class="gate-content">
                        <div class="gate-name">Connascence Index Gate</div>
                        <div class="gate-description">Keep overall coupling manageable</div>
                        <div class="gate-metrics">
                            <div class="metric-value ${summary.connascenceIndex < 50 ? 'success' : summary.connascenceIndex < 75 ? 'warning' : 'error'}">${summary.connascenceIndex.toFixed(1)}</div>
                            <div class="metric-threshold">/ 50.0 target</div>
                        </div>
                        <div class="threshold-progress">
                            <div class="progress-bar">
                                <div class="progress-fill ${summary.connascenceIndex < 50 ? 'success' : summary.connascenceIndex < 75 ? 'warning' : 'error'}" 
                                     style="width: ${Math.min(summary.connascenceIndex / 100 * 100, 100)}%"></div>
                                <div class="progress-threshold" style="left: 50%"></div>
                            </div>
                            <div class="progress-labels">
                                <span>0</span>
                                <span>50 (target)</span>
                                <span>100</span>
                            </div>
                        </div>
                    </div>
                    <div class="gate-status-badge ${summary.connascenceIndex < 50 ? 'passed' : summary.connascenceIndex < 75 ? 'warning' : 'failed'}">
                        ${summary.connascenceIndex < 50 ? 'PASSED' : summary.connascenceIndex < 75 ? 'WARNING' : 'FAILED'}
                    </div>
                </div>
                
                <div class="gate-card ${(summary.high + summary.critical) / Math.max(1, summary.total) < 0.2 ? 'passed' : 'failed'}">
                    <div class="gate-icon">${(summary.high + summary.critical) / Math.max(1, summary.total) < 0.2 ? '✅' : '❌'}</div>
                    <div class="gate-content">
                        <div class="gate-name">High Severity Gate</div>
                        <div class="gate-description">Less than 20% high/critical violations</div>
                        <div class="gate-metrics">
                            <div class="metric-value ${(summary.high + summary.critical) / Math.max(1, summary.total) < 0.2 ? 'success' : 'error'}">${(((summary.high + summary.critical) / Math.max(1, summary.total)) * 100).toFixed(1)}%</div>
                            <div class="metric-threshold">/ 20.0% limit</div>
                        </div>
                        <div class="threshold-progress">
                            <div class="progress-bar">
                                <div class="progress-fill ${(summary.high + summary.critical) / Math.max(1, summary.total) < 0.2 ? 'success' : 'error'}" 
                                     style="width: ${Math.min(((summary.high + summary.critical) / Math.max(1, summary.total)) * 100 / 20 * 100, 100)}%"></div>
                                <div class="progress-threshold" style="left: 100%"></div>
                            </div>
                            <div class="progress-labels">
                                <span>0%</span>
                                <span>20% (limit)</span>
                            </div>
                        </div>
                    </div>
                    <div class="gate-status-badge ${(summary.high + summary.critical) / Math.max(1, summary.total) < 0.2 ? 'passed' : 'failed'}">
                        ${(summary.high + summary.critical) / Math.max(1, summary.total) < 0.2 ? 'PASSED' : 'FAILED'}
                    </div>
                </div>
                
                <div class="gate-card ${summary.total < 10 ? 'passed' : summary.total < 25 ? 'warning' : 'failed'}">
                    <div class="gate-icon">${summary.total < 10 ? '✅' : summary.total < 25 ? '⚠️' : '❌'}</div>
                    <div class="gate-content">
                        <div class="gate-name">Total Violations Gate</div>
                        <div class="gate-description">Keep total violations manageable</div>
                        <div class="gate-metrics">
                            <div class="metric-value ${summary.total < 10 ? 'success' : summary.total < 25 ? 'warning' : 'error'}">${summary.total}</div>
                            <div class="metric-threshold">/ 10 recommended</div>
                        </div>
                    </div>
                    <div class="gate-status-badge ${summary.total < 10 ? 'passed' : summary.total < 25 ? 'warning' : 'failed'}">
                        ${summary.total < 10 ? 'PASSED' : summary.total < 25 ? 'WARNING' : 'FAILED'}
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Quality Risk Heat Map -->
        <div class="quality-metrics">
            <div class="section-title">🔥 Risk Heat Map</div>
            <div class="heat-map-container">
                <div class="heat-map-grid">
                    ${fileAnalysis.slice(0, 12).map((file: any, index: any) => {
                        const riskLevel = file.critical > 0 ? 'critical' : file.high > 0 ? 'high' : file.index > 10 ? 'medium' : 'low';
                        const riskScore = Math.min(file.index / 20 * 100, 100);
                        return `
                        <div class="heat-map-cell ${riskLevel}" onclick="openFile('${file.filePath}')" 
                             style="opacity: ${0.3 + (riskScore / 100) * 0.7}"
                             title="${file.fileName}: ${file.index} risk score, ${file.total} violations">
                            <div class="cell-name">${file.fileName.substring(0, 12)}${file.fileName.length > 12 ? '...' : ''}</div>
                            <div class="cell-score">${file.index}</div>
                        </div>`;
                    }).join('')}
                </div>
                <div class="heat-map-legend">
                    <div class="legend-item">
                        <div class="legend-color low"></div>
                        <span>Low Risk (0-5)</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color medium"></div>
                        <span>Medium Risk (6-15)</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color high"></div>
                        <span>High Risk (16-30)</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color critical"></div>
                        <span>Critical Risk (30+)</span>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Gate Impact Analysis -->
        <div class="quality-metrics">
            <div class="section-title">🎯 Gate Impact Analysis</div>
            <div class="impact-analysis">
                ${summary.critical > 0 ? `
                <div class="impact-item critical">
                    <div class="impact-header">
                        <div class="impact-icon">🚨</div>
                        <div class="impact-title">Critical Issues Blocking Quality Gates</div>
                        <div class="impact-count">${summary.critical} issues</div>
                    </div>
                    <div class="impact-details">
                        <div class="blocking-files">
                            Files affected: ${fileAnalysis.filter((f: any) => f.critical > 0).map((f: any) => f.fileName).join(', ')}
                        </div>
                        <div class="impact-suggestion">
                            🔧 <strong>Action Required:</strong> Fix all critical violations to pass quality gates
                        </div>
                    </div>
                </div>
                ` : ''}
                
                ${summary.connascenceIndex >= 50 ? `
                <div class="impact-item warning">
                    <div class="impact-header">
                        <div class="impact-icon">⚠️</div>
                        <div class="impact-title">High Connascence Index</div>
                        <div class="impact-count">${summary.connascenceIndex.toFixed(1)} / 50</div>
                    </div>
                    <div class="impact-details">
                        <div class="blocking-files">
                            Top contributors: ${summary.topTypes.slice(0, 3).map(([type, count]: any) => `${type} (${count})`).join(', ')}
                        </div>
                        <div class="impact-suggestion">
                            🔧 <strong>Recommendation:</strong> Focus on reducing ${summary.topTypes[0] ? summary.topTypes[0][0] : 'coupling'} violations
                        </div>
                    </div>
                </div>
                ` : ''}
                
                ${((summary.high + summary.critical) / Math.max(1, summary.total)) >= 0.2 ? `
                <div class="impact-item error">
                    <div class="impact-header">
                        <div class="impact-icon">🔴</div>
                        <div class="impact-title">Too Many High Severity Issues</div>
                        <div class="impact-count">${summary.high + summary.critical} / ${summary.total}</div>
                    </div>
                    <div class="impact-details">
                        <div class="blocking-files">
                            ${summary.high} high + ${summary.critical} critical violations = ${(((summary.high + summary.critical) / Math.max(1, summary.total)) * 100).toFixed(1)}%
                        </div>
                        <div class="impact-suggestion">
                            🔧 <strong>Priority:</strong> Reduce high-severity violations to under 20% of total
                        </div>
                    </div>
                </div>
                ` : ''}
                
                ${summary.critical === 0 && summary.connascenceIndex < 50 && ((summary.high + summary.critical) / Math.max(1, summary.total)) < 0.2 ? `
                <div class="impact-item success">
                    <div class="impact-header">
                        <div class="impact-icon">🎉</div>
                        <div class="impact-title">All Quality Gates Passed!</div>
                        <div class="impact-count">Excellent</div>
                    </div>
                    <div class="impact-details">
                        <div class="impact-suggestion">
                            ✨ <strong>Great job!</strong> Your code quality meets all standards. Consider tackling remaining ${summary.total} minor issues.
                        </div>
                    </div>
                </div>
                ` : ''}
            </div>
        </div>
        
        <!-- Quality Improvement Roadmap -->
        <div class="quality-metrics">
            <div class="section-title">🛣️ Quality Improvement Roadmap</div>
            <div class="roadmap-container">
                <div class="roadmap-steps">
                    ${summary.critical > 0 ? `
                    <div class="roadmap-step active critical">
                        <div class="step-number">1</div>
                        <div class="step-content">
                            <div class="step-title">Fix Critical Issues</div>
                            <div class="step-description">Address ${summary.critical} critical violations immediately</div>
                            <div class="step-actions">
                                <button class="step-action" onclick="filterViolations('critical')">View Critical Issues</button>
                            </div>
                        </div>
                        <div class="step-status">🚨 URGENT</div>
                    </div>
                    ` : `
                    <div class="roadmap-step completed">
                        <div class="step-number">✓</div>
                        <div class="step-content">
                            <div class="step-title">Critical Issues</div>
                            <div class="step-description">No critical issues found</div>
                        </div>
                        <div class="step-status">✅ DONE</div>
                    </div>
                    `}
                    
                    ${summary.high > 5 ? `
                    <div class="roadmap-step ${summary.critical === 0 ? 'active' : ''} high">
                        <div class="step-number">2</div>
                        <div class="step-content">
                            <div class="step-title">Reduce High Severity Issues</div>
                            <div class="step-description">Target the ${summary.high} high-priority violations</div>
                            <div class="step-actions">
                                <button class="step-action" onclick="filterViolations('high')">View High Issues</button>
                            </div>
                        </div>
                        <div class="step-status">⚡ HIGH</div>
                    </div>
                    ` : `
                    <div class="roadmap-step completed">
                        <div class="step-number">✓</div>
                        <div class="step-content">
                            <div class="step-title">High Severity Issues</div>
                            <div class="step-description">High severity issues under control</div>
                        </div>
                        <div class="step-status">✅ DONE</div>
                    </div>
                    `}
                    
                    ${summary.connascenceIndex >= 50 ? `
                    <div class="roadmap-step ${summary.critical === 0 && summary.high <= 5 ? 'active' : ''} warning">
                        <div class="step-number">3</div>
                        <div class="step-content">
                            <div class="step-title">Reduce Connascence Index</div>
                            <div class="step-description">Current: ${summary.connascenceIndex.toFixed(1)}, Target: <50</div>
                            <div class="step-actions">
                                <button class="step-action" onclick="focusTopConnascenceType()">Focus on ${summary.topTypes[0] ? summary.topTypes[0][0] : 'Top Type'}</button>
                            </div>
                        </div>
                        <div class="step-status">📊 MEDIUM</div>
                    </div>
                    ` : `
                    <div class="roadmap-step completed">
                        <div class="step-number">✓</div>
                        <div class="step-content">
                            <div class="step-title">Connascence Index</div>
                            <div class="step-description">Index within acceptable range</div>
                        </div>
                        <div class="step-status">✅ DONE</div>
                    </div>
                    `}
                    
                    <div class="roadmap-step ${summary.critical === 0 && summary.high <= 5 && summary.connascenceIndex < 50 ? 'active' : ''} info">
                        <div class="step-number">4</div>
                        <div class="step-content">
                            <div class="step-title">Polish Remaining Issues</div>
                            <div class="step-description">Address ${summary.medium + summary.low} medium/low priority items</div>
                            <div class="step-actions">
                                <button class="step-action" onclick="showImprovementSuggestions()">Get Suggestions</button>
                            </div>
                        </div>
                        <div class="step-status">✨ POLISH</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Custom Gate Builder -->
        <div class="quality-metrics">
            <div class="section-title">🔧 Custom Quality Gates</div>
            <div class="custom-gates">
                <div class="custom-gate-form">
                    <h4>Create Custom Gate</h4>
                    <div class="form-row">
                        <label>Gate Name:</label>
                        <input type="text" id="customGateName" placeholder="e.g., Team Code Quality Standard" />
                    </div>
                    <div class="form-row">
                        <label>Metric:</label>
                        <select id="customGateMetric">
                            <option value="total_violations">Total Violations</option>
                            <option value="critical_violations">Critical Violations</option>
                            <option value="connascence_index">Connascence Index</option>
                            <option value="high_severity_percentage">High Severity Percentage</option>
                        </select>
                    </div>
                    <div class="form-row">
                        <label>Threshold:</label>
                        <input type="number" id="customGateThreshold" placeholder="e.g., 15" />
                        <select id="customGateOperator">
                            <option value="lte">≤ (less than or equal)</option>
                            <option value="gte">≥ (greater than or equal)</option>
                            <option value="lt">< (less than)</option>
                            <option value="gt">> (greater than)</option>
                        </select>
                    </div>
                    <div class="form-row">
                        <label>Action:</label>
                        <select id="customGateAction">
                            <option value="warn">Warning</option>
                            <option value="fail">Fail Build</option>
                            <option value="info">Information Only</option>
                        </select>
                    </div>
                    <button class="btn" onclick="addCustomGate()">Add Custom Gate</button>
                </div>
                
                <div class="custom-gates-list">
                    <h4>Active Custom Gates</h4>
                    <div id="customGatesList">
                        <div class="empty-state">No custom gates defined. Create one above to get started.</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Quality Trends Section -->
        <div class="quality-metrics">
            <div class="section-title">📈 Quality Trends & Benchmarks</div>
            <div class="trends-container">
                <div class="trend-chart-placeholder">
                    <div class="chart-title">Quality Evolution Over Time</div>
                    <div class="placeholder-content">
                        <div class="trend-line">
                            <svg width="100%" height="200" viewBox="0 0 400 200">
                                <defs>
                                    <linearGradient id="trendGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                                        <stop offset="0%" style="stop-color:#4ecdc4;stop-opacity:0.8" />
                                        <stop offset="100%" style="stop-color:#4ecdc4;stop-opacity:0.1" />
                                    </linearGradient>
                                </defs>
                                <polyline fill="url(#trendGradient)" stroke="#4ecdc4" stroke-width="3" 
                                         points="0,150 80,140 160,120 240,100 320,85 400,75" />
                                <circle cx="400" cy="75" r="4" fill="#4ecdc4" />
                            </svg>
                        </div>
                        <div class="trend-info">
                            <div class="current-score">
                                <div class="score-value">${(100 - summary.connascenceIndex).toFixed(1)}</div>
                                <div class="score-label">Quality Score</div>
                            </div>
                            <div class="trend-indicators">
                                <div class="trend-item">
                                    <span class="trend-arrow ${summary.connascenceIndex < 30 ? 'up' : 'down'}">
                                        ${summary.connascenceIndex < 30 ? '📈' : '📉'}
                                    </span>
                                    <span>Trend</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="benchmark-comparison">
                    <div class="benchmark-title">Industry Benchmarks</div>
                    <div class="benchmark-items">
                        <div class="benchmark-item ${summary.connascenceIndex < 25 ? 'excellent' : summary.connascenceIndex < 50 ? 'good' : 'needs-work'}">
                            <div class="benchmark-label">Enterprise Standard</div>
                            <div class="benchmark-bar">
                                <div class="benchmark-fill" style="width: ${Math.min((50 - summary.connascenceIndex) / 50 * 100, 100)}%"></div>
                            </div>
                            <div class="benchmark-score">${summary.connascenceIndex < 50 ? 'MEETS' : 'BELOW'}</div>
                        </div>
                        
                        <div class="benchmark-item ${summary.critical === 0 ? 'excellent' : 'needs-work'}">
                            <div class="benchmark-label">Safety Critical</div>
                            <div class="benchmark-bar">
                                <div class="benchmark-fill ${summary.critical === 0 ? 'success' : 'error'}" 
                                     style="width: ${summary.critical === 0 ? 100 : 0}%"></div>
                            </div>
                            <div class="benchmark-score">${summary.critical === 0 ? 'MEETS' : 'BELOW'}</div>
                        </div>
                        
                        <div class="benchmark-item ${(summary.high + summary.critical) / Math.max(1, summary.total) < 0.1 ? 'excellent' : (summary.high + summary.critical) / Math.max(1, summary.total) < 0.2 ? 'good' : 'needs-work'}">
                            <div class="benchmark-label">High Quality Code</div>
                            <div class="benchmark-bar">
                                <div class="benchmark-fill" 
                                     style="width: ${Math.max(0, 100 - (((summary.high + summary.critical) / Math.max(1, summary.total)) * 100 * 5))}%"></div>
                            </div>
                            <div class="benchmark-score">${(summary.high + summary.critical) / Math.max(1, summary.total) < 0.1 ? 'EXCEEDS' : (summary.high + summary.critical) / Math.max(1, summary.total) < 0.2 ? 'MEETS' : 'BELOW'}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="quality-metrics">
            <div class="section-title">ℹ️ About Quality Gates & Connascence</div>
            <div class="info-panels">
                <div class="info-panel">
                    <h4>🎯 Quality Gates</h4>
                    <p>Automated quality checkpoints that prevent problematic code from being merged. Gates evaluate multiple metrics and can block deployments or trigger warnings when quality thresholds are exceeded.</p>
                    <ul>
                        <li><strong>Critical Gate:</strong> Blocks builds with critical violations</li>
                        <li><strong>Index Gate:</strong> Ensures manageable coupling levels</li>
                        <li><strong>Severity Gate:</strong> Limits high-severity issue percentage</li>
                        <li><strong>Custom Gates:</strong> Team-specific quality criteria</li>
                    </ul>
                </div>
                
                <div class="info-panel">
                    <h4>🔗 Connascence Types</h4>
                    <p>Connascence measures coupling strength between software components. Lower connascence indicates better maintainability.</p>
                    <ul>
                        <li><strong>CoM (Meaning):</strong> Magic literals and unclear values</li>
                        <li><strong>CoP (Position):</strong> Parameter order dependencies</li>
                        <li><strong>CoT (Type):</strong> Missing or unclear type information</li>
                        <li><strong>CoA (Algorithm):</strong> Duplicated or complex logic</li>
                        <li><strong>CoN (Name):</strong> Name dependencies between components</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Reports Tab -->
    <div class="tab-content" id="reports">
        <div class="reports-section">
            <div class="section-title">📋 Export Reports</div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-bottom: 20px;">
                <div>
                    <h4 style="margin-bottom: 8px;">Single Format Export</h4>
                    <div style="display: flex; flex-direction: column; gap: 8px;">
                        <button class="btn" onclick="exportReport('sarif')">📄 Export SARIF</button>
                        <button class="btn" onclick="exportReport('json')">📊 Export JSON</button>
                        <button class="btn" onclick="exportReport('markdown')">📝 Export Markdown</button>
                        <button class="btn" onclick="exportReport('csv')">📈 Export CSV</button>
                        <button class="btn" onclick="exportReport('html')">🌐 Export HTML</button>
                    </div>
                </div>
                
                <div>
                    <h4 style="margin-bottom: 8px;">Multi-Format Export</h4>
                    <div style="display: flex; flex-direction: column; gap: 8px;">
                        <button class="btn" onclick="exportMultiFormat(['sarif', 'json', 'markdown'])">📦 Export All Formats</button>
                        <button class="btn" onclick="exportMultiFormat(['sarif', 'json'])">⚡ Quick Export</button>
                        <button class="btn-secondary" onclick="showExportOptions()">⚙️ Custom Export</button>
                    </div>
                </div>
                
                <div>
                    <h4 style="margin-bottom: 8px;">Report Preview</h4>
                    <div style="display: flex; flex-direction: column; gap: 8px;">
                        <button class="btn-secondary" onclick="previewReport('sarif')">👀 Preview SARIF</button>
                        <button class="btn-secondary" onclick="previewReport('json')">👀 Preview JSON</button>
                        <button class="btn-secondary" onclick="previewReport('markdown')">👀 Preview Markdown</button>
                    </div>
                </div>
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
        
        function exportReport(format, options) {
            vscode.postMessage({
                type: 'exportReport',
                format: format,
                options: options || {}
            });
        }
        
        function exportMultiFormat(formats, options) {
            vscode.postMessage({
                type: 'exportMultiFormat',
                formats: formats,
                options: options || {}
            });
        }
        
        function previewReport(format) {
            vscode.postMessage({
                type: 'previewReport',
                format: format
            });
        }
        
        function showExportOptions() {
            // Create a dynamic dialog for custom export options
            const modal = document.createElement('div');
            modal.innerHTML = \`
                <div style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 1000; display: flex; align-items: center; justify-content: center;">
                    <div style="background: var(--vscode-editor-background); padding: 30px; border-radius: 8px; max-width: 400px; width: 90%;">
                        <h3>Custom Export Options</h3>
                        <div style="margin: 15px 0;">
                            <label>Select Formats:</label>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 8px;">
                                <label><input type="checkbox" value="sarif" checked> SARIF</label>
                                <label><input type="checkbox" value="json" checked> JSON</label>
                                <label><input type="checkbox" value="markdown"> Markdown</label>
                                <label><input type="checkbox" value="html"> HTML</label>
                                <label><input type="checkbox" value="csv"> CSV</label>
                            </div>
                        </div>
                        <div style="display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px;">
                            <button class="btn-secondary" onclick="this.parentElement.parentElement.parentElement.remove()">Cancel</button>
                            <button class="btn" onclick="executeCustomExport(this.parentElement.parentElement)">Export</button>
                        </div>
                    </div>
                </div>
            \`;
            document.body.appendChild(modal);
        }
        
        function executeCustomExport(dialog) {
            const checkboxes = dialog.querySelectorAll('input[type="checkbox"]:checked');
            const selectedFormats = Array.from(checkboxes).map(cb => cb.value);
            
            if (selectedFormats.length === 0) {
                alert('Please select at least one format');
                return;
            }
            
            exportMultiFormat(selectedFormats);
            dialog.parentElement.remove();
        }
        
        // Quality Gates Interactive Functions
        function filterViolations(severity) {
            const severityFilter = document.getElementById('severityFilter');
            if (severityFilter) {
                severityFilter.value = severity;
                // Trigger change event to apply filter
                severityFilter.dispatchEvent(new Event('change'));
            }
            
            // Switch to violations tab
            const violationsTab = document.querySelector('[data-tab="violations"]');
            if (violationsTab) {
                violationsTab.click();
            }
        }
        
        function focusTopConnascenceType() {
            const typeFilter = document.getElementById('typeFilter');
            if (typeFilter && ${JSON.stringify(summary.topTypes[0] ? summary.topTypes[0][0] : '')}) {
                typeFilter.value = ${JSON.stringify(summary.topTypes[0] ? summary.topTypes[0][0] : '')};
                typeFilter.dispatchEvent(new Event('change'));
            }
            
            // Switch to violations tab
            const violationsTab = document.querySelector('[data-tab="violations"]');
            if (violationsTab) {
                violationsTab.click();
            }
        }
        
        function showImprovementSuggestions() {
            // Switch to violations tab and apply medium/low severity filter
            const violationsTab = document.querySelector('[data-tab="violations"]');
            if (violationsTab) {
                violationsTab.click();
            }
            
            // Show info message
            setTimeout(() => {
                const message = document.createElement('div');
                message.className = 'improvement-suggestion-popup';
                message.style.cssText = \`
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    background: var(--vscode-notifications-background);
                    color: var(--vscode-notifications-foreground);
                    border: 1px solid var(--vscode-notifications-border);
                    border-radius: 8px;
                    padding: 20px;
                    max-width: 400px;
                    z-index: 1000;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                \`;
                
                message.innerHTML = \`
                    <h4 style="margin: 0 0 10px 0;">💡 Improvement Suggestions</h4>
                    <p style="margin: 0 0 15px 0; line-height: 1.4;">Focus on these areas for incremental improvements:</p>
                    <ul style="margin: 0; padding-left: 20px; line-height: 1.4;">
                        <li>Refactor functions with high cyclomatic complexity</li>
                        <li>Add type annotations where missing</li>
                        <li>Extract common code patterns to reduce duplication</li>
                        <li>Improve variable and function naming clarity</li>
                    </ul>
                    <button onclick="this.parentElement.remove()" style="
                        margin-top: 15px;
                        background: var(--vscode-button-background);
                        color: var(--vscode-button-foreground);
                        border: none;
                        padding: 8px 16px;
                        border-radius: 4px;
                        cursor: pointer;
                        float: right;
                    ">Got it</button>
                \`;
                
                document.body.appendChild(message);
                
                // Auto-remove after 10 seconds
                setTimeout(() => {
                    if (message.parentElement) {
                        message.remove();
                    }
                }, 10000);
            }, 300);
        }
        
        function addCustomGate() {
            const name = document.getElementById('customGateName').value;
            const metric = document.getElementById('customGateMetric').value;
            const threshold = document.getElementById('customGateThreshold').value;
            const operator = document.getElementById('customGateOperator').value;
            const action = document.getElementById('customGateAction').value;
            
            if (!name || !threshold) {
                alert('Please fill in all required fields');
                return;
            }
            
            // Create custom gate object
            const customGate = {
                name,
                metric,
                threshold: parseFloat(threshold),
                operator,
                action,
                id: Date.now() // Simple ID generation
            };
            
            // Add to list
            const gatesList = document.getElementById('customGatesList');
            if (gatesList) {
                // Remove empty state if it exists
                const emptyState = gatesList.querySelector('.empty-state');
                if (emptyState) {
                    emptyState.remove();
                }
                
                // Create gate card
                const gateCard = document.createElement('div');
                gateCard.className = 'custom-gate-card';
                gateCard.style.cssText = \`
                    background: var(--vscode-editor-inactiveSelectionBackground);
                    border: 1px solid var(--vscode-panel-border);
                    border-radius: 8px;
                    padding: 15px;
                    margin-bottom: 10px;
                \`;
                
                gateCard.innerHTML = \`
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                        <div style="font-weight: 600; color: var(--vscode-foreground);">\${name}</div>
                        <button onclick="removeCustomGate(\${customGate.id})" style="
                            background: var(--vscode-errorForeground);
                            color: white;
                            border: none;
                            border-radius: 4px;
                            padding: 4px 8px;
                            font-size: 11px;
                            cursor: pointer;
                        ">Remove</button>
                    </div>
                    <div style="font-size: 13px; color: var(--vscode-descriptionForeground); margin-bottom: 5px;">
                        \${metric} \${operator} \${threshold}
                    </div>
                    <div style="font-size: 12px; padding: 2px 8px; background: var(--vscode-badge-background); 
                                color: var(--vscode-badge-foreground); border-radius: 12px; display: inline-block;">
                        \${action.toUpperCase()}
                    </div>
                \`;
                
                gateCard.dataset.gateId = customGate.id;
                gatesList.appendChild(gateCard);
            }
            
            // Clear form
            document.getElementById('customGateName').value = '';
            document.getElementById('customGateThreshold').value = '';
            
            // Store in localStorage (for persistence across sessions)
            const customGates = JSON.parse(localStorage.getItem('connascence-custom-gates') || '[]');
            customGates.push(customGate);
            localStorage.setItem('connascence-custom-gates', JSON.stringify(customGates));
            
            // Show success message
            const successMsg = document.createElement('div');
            successMsg.style.cssText = \`
                position: fixed;
                top: 20px;
                right: 20px;
                background: var(--vscode-notifications-background);
                color: var(--vscode-notifications-foreground);
                border: 1px solid var(--vscode-notifications-border);
                border-radius: 4px;
                padding: 12px 16px;
                z-index: 1000;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            \`;
            successMsg.textContent = \`Custom gate "\${name}" added successfully!\`;
            document.body.appendChild(successMsg);
            
            setTimeout(() => successMsg.remove(), 3000);
        }
        
        function removeCustomGate(gateId) {
            // Remove from DOM
            const gateCard = document.querySelector(\`[data-gate-id="\${gateId}"]\`);
            if (gateCard) {
                gateCard.remove();
            }
            
            // Remove from localStorage
            const customGates = JSON.parse(localStorage.getItem('connascence-custom-gates') || '[]');
            const updatedGates = customGates.filter(gate => gate.id !== gateId);
            localStorage.setItem('connascence-custom-gates', JSON.stringify(updatedGates));
            
            // Show empty state if no gates left
            const gatesList = document.getElementById('customGatesList');
            if (gatesList && gatesList.children.length === 0) {
                const emptyState = document.createElement('div');
                emptyState.className = 'empty-state';
                emptyState.textContent = 'No custom gates defined. Create one above to get started.';
                gatesList.appendChild(emptyState);
            }
        }
        
        function loadCustomGates() {
            const customGates = JSON.parse(localStorage.getItem('connascence-custom-gates') || '[]');
            const gatesList = document.getElementById('customGatesList');
            
            if (customGates.length === 0 || !gatesList) {
                return;
            }
            
            // Clear empty state
            gatesList.innerHTML = '';
            
            customGates.forEach(gate => {
                const gateCard = document.createElement('div');
                gateCard.className = 'custom-gate-card';
                gateCard.style.cssText = \`
                    background: var(--vscode-editor-inactiveSelectionBackground);
                    border: 1px solid var(--vscode-panel-border);
                    border-radius: 8px;
                    padding: 15px;
                    margin-bottom: 10px;
                \`;
                
                gateCard.innerHTML = \`
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                        <div style="font-weight: 600; color: var(--vscode-foreground);">\${gate.name}</div>
                        <button onclick="removeCustomGate(\${gate.id})" style="
                            background: var(--vscode-errorForeground);
                            color: white;
                            border: none;
                            border-radius: 4px;
                            padding: 4px 8px;
                            font-size: 11px;
                            cursor: pointer;
                        ">Remove</button>
                    </div>
                    <div style="font-size: 13px; color: var(--vscode-descriptionForeground); margin-bottom: 5px;">
                        \${gate.metric} \${gate.operator} \${gate.threshold}
                    </div>
                    <div style="font-size: 12px; padding: 2px 8px; background: var(--vscode-badge-background); 
                                color: var(--vscode-badge-foreground); border-radius: 12px; display: inline-block;">
                        \${gate.action.toUpperCase()}
                    </div>
                \`;
                
                gateCard.dataset.gateId = gate.id;
                gatesList.appendChild(gateCard);
            });
        }
        
        // Load custom gates on page load
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(loadCustomGates, 100);
        });

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
                    
                case 'updateQualityGates':
                    // Update quality gates display when new analysis results come in
                    if (message.gates) {
                        updateQualityGatesDisplay(message.gates);
                    }
                    break;
            }
        });
    </script>
</body>
</html>`;
    }
    
    private async exportReport(format: string, options?: any): Promise<void> {
        const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        if (!workspacePath) {
            vscode.window.showErrorMessage('No workspace folder found');
            return;
        }

        try {
            // Show progress for advanced formats
            if (['sarif', 'markdown', 'md'].includes(format.toLowerCase())) {
                await vscode.window.withProgress({
                    location: vscode.ProgressLocation.Notification,
                    title: `Exporting ${format.toUpperCase()} report...`,
                    cancellable: false
                }, async (progress) => {
                    progress.report({ increment: 20, message: 'Initializing export...' });
                    
                    const timestamp = new Date().toISOString().replace(/:/g, '-').split('.')[0];
                    const outputDir = options?.outputPath || workspacePath;
                    const filename = `connascence-report-${timestamp}.${this.getFileExtension(format)}`;
                    const outputPath = path.join(outputDir, filename);
                    
                    progress.report({ increment: 60, message: 'Generating report content...' });
                    
                    // Use integrated service for advanced formats
                    let content: string;
                    if (format.toLowerCase() === 'sarif') {
                        content = this.generateSARIFReport();
                    } else if (['markdown', 'md'].includes(format.toLowerCase())) {
                        content = this.generateMarkdownReport();
                    } else {
                        content = this.generateLegacyReport(format);
                    }
                    
                    await vscode.workspace.fs.writeFile(vscode.Uri.file(outputPath), Buffer.from(content));
                    
                    progress.report({ increment: 100, message: 'Export complete' });
                    
                    // Show success message
                    const openAction = await vscode.window.showInformationMessage(
                        `Report exported: ${filename}`,
                        'Open File',
                        'Show in Explorer'
                    );
                    
                    if (openAction === 'Open File') {
                        vscode.commands.executeCommand('vscode.open', vscode.Uri.file(outputPath));
                    } else if (openAction === 'Show in Explorer') {
                        vscode.commands.executeCommand('revealFileInOS', vscode.Uri.file(outputPath));
                    }
                });
            } else {
                // Legacy formats - no progress needed
                this.exportLegacyReport(format, options);
            }
            
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            vscode.window.showErrorMessage(`Export failed: ${errorMessage}`);
        }
    }

    private async exportMultiFormatReport(formats: string[], options?: any): Promise<void> {
        const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        if (!workspacePath) {
            vscode.window.showErrorMessage('No workspace folder found');
            return;
        }

        try {
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: 'Exporting multi-format reports...',
                cancellable: false
            }, async (progress) => {
                const outputDir = options?.outputPath || workspacePath;
                const timestamp = new Date().toISOString().replace(/:/g, '-').split('.')[0];
                const results: string[] = [];
                
                for (let i = 0; i < formats.length; i++) {
                    const format = formats[i];
                    const progressPercent = ((i + 1) / formats.length) * 100;
                    
                    progress.report({ 
                        increment: progressPercent / formats.length, 
                        message: `Exporting ${format}...` 
                    });
                    
                    const filename = `connascence-report-${timestamp}.${this.getFileExtension(format)}`;
                    const outputPath = path.join(outputDir, filename);
                    
                    let content: string;
                    if (format.toLowerCase() === 'sarif') {
                        content = this.generateSARIFReport();
                    } else if (['markdown', 'md'].includes(format.toLowerCase())) {
                        content = this.generateMarkdownReport();
                    } else {
                        content = this.generateLegacyReport(format);
                    }
                    
                    await vscode.workspace.fs.writeFile(vscode.Uri.file(outputPath), Buffer.from(content));
                    results.push(filename);
                }
                
                const openAction = await vscode.window.showInformationMessage(
                    `${results.length} reports exported successfully`,
                    'Show in Explorer'
                );
                
                if (openAction === 'Show in Explorer') {
                    vscode.commands.executeCommand('revealFileInOS', vscode.Uri.file(outputDir));
                }
            });
            
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            vscode.window.showErrorMessage(`Multi-format export failed: ${errorMessage}`);
        }
    }

    private async previewReport(format: string): Promise<void> {
        try {
            let content: string;
            let language: string;
            
            switch (format.toLowerCase()) {
                case 'sarif':
                    content = this.generateSARIFReport();
                    language = 'json';
                    break;
                case 'json':
                    content = this.generateLegacyReport('json');
                    language = 'json';
                    break;
                case 'markdown':
                case 'md':
                    content = this.generateMarkdownReport();
                    language = 'markdown';
                    break;
                default:
                    vscode.window.showErrorMessage(`Preview not supported for format: ${format}`);
                    return;
            }
            
            // Open preview in new document
            const doc = await vscode.workspace.openTextDocument({
                content,
                language
            });
            
            await vscode.window.showTextDocument(doc, vscode.ViewColumn.Beside);
            
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            vscode.window.showErrorMessage(`Preview failed: ${errorMessage}`);
        }
    }

    private exportLegacyReport(format: string, options?: any): void {
        const content = this.generateLegacyReport(format);
        const timestamp = new Date().toISOString().replace(/:/g, '-').split('.')[0];
        const filename = `connascence-report-${timestamp}.${this.getFileExtension(format)}`;
        
        if (content) {
            const outputPath = options?.outputPath || 
                (vscode.workspace.workspaceFolders?.[0]?.uri.fsPath + '/' + filename);
                
            Promise.resolve(vscode.workspace.fs.writeFile(
                vscode.Uri.file(outputPath),
                Buffer.from(content)
            )).then(() => {
                vscode.window.showInformationMessage(`Report exported: ${filename}`);
            }).catch((error: any) => {
                vscode.window.showErrorMessage(`Failed to export report: ${error.message}`);
            });
        }
    }

    private generateLegacyReport(format: string): string {
        const summary = this.generateSummary();
        const fileAnalysis = this.generateFileAnalysis();
        
        switch (format) {
            case 'json':
                return JSON.stringify({
                    timestamp: new Date().toISOString(),
                    summary,
                    fileAnalysis,
                    violations: this.violations
                }, null, 2);
                
            case 'csv':
                const csvHeaders = 'File,Line,Type,Severity,Description\n';
                const csvRows = this.violations.map(v => 
                    `"${v.filePath}",${v.lineNumber},"${v.connascenceType}","${v.severity}","${v.description}"`
                ).join('\n');
                return csvHeaders + csvRows;
                
            case 'html':
                return this.generateHtmlReport(summary, fileAnalysis);
                
            default:
                return '';
        }
    }

    private generateSARIFReport(): string {
        const timestamp = new Date().toISOString();
        
        const sarifReport = {
            "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "connascence",
                            "version": "1.0.0",
                            "informationUri": "https://github.com/connascence/connascence-analyzer",
                            "shortDescription": {
                                "text": "Connascence analysis for reducing coupling in codebases"
                            }
                        }
                    },
                    "invocations": [
                        {
                            "executionSuccessful": true,
                            "startTimeUtc": timestamp
                        }
                    ],
                    "results": this.violations.map(violation => ({
                        "ruleId": `CON_${violation.connascenceType}`,
                        "level": this.severityToSarifLevel(violation.severity),
                        "message": {
                            "text": violation.description
                        },
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {
                                        "uri": violation.filePath
                                    },
                                    "region": {
                                        "startLine": violation.lineNumber,
                                        "startColumn": 1
                                    }
                                }
                            }
                        ]
                    }))
                }
            ]
        };
        
        return JSON.stringify(sarifReport, null, 2);
    }

    private generateMarkdownReport(): string {
        const summary = this.generateSummary();
        const fileAnalysis = this.generateFileAnalysis();
        const timestamp = new Date().toLocaleString();
        
        const criticalCount = summary.critical;
        const totalCount = summary.total;
        
        let statusEmoji = '';
        let status = '';
        
        if (criticalCount > 0) {
            statusEmoji = '🔴';
            status = `${criticalCount} critical issues found`;
        } else if (totalCount > 20) {
            statusEmoji = '🟡';
            status = `${totalCount} issues found`;
        } else if (totalCount > 0) {
            statusEmoji = '🟠';
            status = `${totalCount} minor issues`;
        } else {
            statusEmoji = '✅';
            status = 'No issues found';
        }
        
        return `# ${statusEmoji} Connascence Analysis Report

**Status:** ${status} | **Policy:** default | **Duration:** N/A

## 📊 Summary

${totalCount === 0 ? '**✅ Great work!** No connascence violations detected.' : `Found ${totalCount} violations across ${fileAnalysis.length} files.`}

${totalCount > 0 ? `**By Severity:** 🔴 ${summary.critical} Critical | 🟡 ${summary.high} High | 🟠 ${summary.medium} Medium | ⚪ ${summary.low} Low` : ''}

**Files Affected:** ${fileAnalysis.length}

## 📁 Top Risk Files

${fileAnalysis.slice(0, 5).map(file => 
`- **${file.fileName}** - ${file.total} issues (🔴 ${file.critical} Critical, 🟡 ${file.high} High)`
).join('\n')}

## 🔍 Recommendations

${totalCount === 0 ? 
'**Keep up the great work!** Your code shows excellent connascence practices.' :
'- Focus on critical violations first\n- Review files with high violation counts\n- Consider refactoring to reduce coupling'}

---

_Analysis completed on ${timestamp}_

**What is Connascence?** Connascence is a software engineering metric that measures the strength of coupling between components. Lower connascence leads to more maintainable code.

🔗 [Learn More](https://connascence.io) | 🛠 [Connascence Analyzer](https://github.com/connascence/connascence-analyzer)`;
    }

    private severityToSarifLevel(severity: string): string {
        switch (severity.toLowerCase()) {
            case 'critical':
                return 'error';
            case 'high':
                return 'error';
            case 'medium':
                return 'warning';
            case 'low':
            default:
                return 'note';
        }
    }

    private getFileExtension(format: string): string {
        const extensionMap: { [key: string]: string } = {
            'sarif': 'sarif',
            'json': 'json',
            'markdown': 'md',
            'md': 'md',
            'html': 'html',
            'csv': 'csv'
        };
        return extensionMap[format.toLowerCase()] || format.toLowerCase();
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