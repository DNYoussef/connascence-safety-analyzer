/**
 * Status bar integration for Connascence analyzer.
 * 
 * Shows current connascence status and metrics in VS Code's status bar.
 */

import * as vscode from 'vscode';

export class ConnascenceStatusBar {
    private statusBarItem: vscode.StatusBarItem;
    private isScanning = false;
    private lastScanResults: any = null;
    
    constructor(private context: vscode.ExtensionContext) {
        // Create status bar item
        this.statusBarItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Right,
            100 // Priority - higher number = more to the left
        );
        
        this.statusBarItem.command = 'connascence.openDashboard';
        this.statusBarItem.tooltip = 'Click to open Connascence Dashboard';
        
        // Start with default state
        this.update();
        this.statusBarItem.show();
        
        // Register for disposal
        this.context.subscriptions.push(this.statusBarItem);
    }
    
    update(scanResults?: any): void {
        if (scanResults) {
            this.lastScanResults = scanResults;
        }
        
        const config = vscode.workspace.getConfiguration('connascence');
        const baselineMode = config.get<boolean>('baselineMode', false);
        
        if (this.isScanning) {
            this.statusBarItem.text = '$(loading~spin) Connascence: Scanning...';\n            this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');\n            return;\n        }\n        \n        if (!this.lastScanResults) {\n            this.statusBarItem.text = '$(link) Connascence: Ready';\n            this.statusBarItem.backgroundColor = undefined;\n            return;\n        }\n        \n        const results = this.lastScanResults;\n        const violationCount = results.violations?.length || 0;\n        \n        if (violationCount === 0) {\n            this.statusBarItem.text = '$(check) Connascence: Clean';\n            this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.prominentBackground');\n            this.statusBarItem.tooltip = 'No connascence violations found';\n        } else {\n            // Calculate connascence index if available\n            const connascenceIndex = results.summary?.connascence_index || this.calculateSimpleIndex(results.violations);\n            \n            // Determine status based on violation severity\n            const critical = results.violations?.filter((v: any) => v.severity === 'critical').length || 0;\n            const high = results.violations?.filter((v: any) => v.severity === 'high').length || 0;\n            \n            let icon = '$(warning)';\n            let bgColor = new vscode.ThemeColor('statusBarItem.warningBackground');\n            \n            if (critical > 0) {\n                icon = '$(error)';\n                bgColor = new vscode.ThemeColor('statusBarItem.errorBackground');\n            } else if (high === 0) {\n                icon = '$(info)';\n                bgColor = undefined;\n            }\n            \n            this.statusBarItem.text = `${icon} Connascence: ${violationCount} (${connascenceIndex.toFixed(1)})`;\n            this.statusBarItem.backgroundColor = bgColor;\n            \n            // Build detailed tooltip\n            const tooltip = this.buildTooltip(results, baselineMode);\n            this.statusBarItem.tooltip = tooltip;\n        }\n    }\n    \n    private calculateSimpleIndex(violations: any[]): number {\n        if (!violations || violations.length === 0) return 0.0;\n        \n        // Simple connascence index calculation\n        // Based on violation count and severity weights\n        const weights = { critical: 10, high: 5, medium: 2, low: 1 };\n        let totalWeight = 0;\n        \n        for (const violation of violations) {\n            const weight = weights[violation.severity as keyof typeof weights] || 1;\n            totalWeight += weight;\n        }\n        \n        return totalWeight;\n    }\n    \n    private buildTooltip(results: any, baselineMode: boolean): string {\n        const violations = results.violations || [];\n        const summary = results.summary || {};\n        \n        const critical = violations.filter((v: any) => v.severity === 'critical').length;\n        const high = violations.filter((v: any) => v.severity === 'high').length;\n        const medium = violations.filter((v: any) => v.severity === 'medium').length;\n        const low = violations.filter((v: any) => v.severity === 'low').length;\n        \n        const lines = [\n            `Connascence Analysis Results`,\n            ``,\n            `Total Violations: ${violations.length}`,\n            `• Critical: ${critical}`,\n            `• High: ${high}`,\n            `• Medium: ${medium}`,\n            `• Low: ${low}`\n        ];\n        \n        if (summary.connascence_index) {\n            lines.push(``);\n            lines.push(`Connascence Index: ${summary.connascence_index.toFixed(1)}`);\n        }\n        \n        if (baselineMode) {\n            lines.push(``);\n            lines.push(`🔒 Baseline Mode: Only new violations shown`);\n        }\n        \n        // Add most common violation types\n        if (summary.violations_by_type) {\n            const topTypes = Object.entries(summary.violations_by_type)\n                .sort(([, a]: any, [, b]: any) => b - a)\n                .slice(0, 3);\n            \n            if (topTypes.length > 0) {\n                lines.push(``);\n                lines.push(`Top Issues:`);\n                for (const [type, count] of topTypes) {\n                    lines.push(`• ${type}: ${count}`);\n                }\n            }\n        }\n        \n        lines.push(``);\n        lines.push(`Click to open dashboard`);\n        \n        return lines.join('\\n');\n    }\n    \n    setScanningState(scanning: boolean): void {\n        this.isScanning = scanning;\n        this.update();\n    }\n    \n    showTemporaryMessage(message: string, durationMs = 3000): void {\n        const originalText = this.statusBarItem.text;\n        const originalBg = this.statusBarItem.backgroundColor;\n        \n        this.statusBarItem.text = message;\n        this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.prominentBackground');\n        \n        setTimeout(() => {\n            this.statusBarItem.text = originalText;\n            this.statusBarItem.backgroundColor = originalBg;\n        }, durationMs);\n    }\n    \n    dispose(): void {\n        this.statusBarItem.dispose();\n    }\n}