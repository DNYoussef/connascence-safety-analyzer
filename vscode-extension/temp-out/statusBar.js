"use strict";
/**
 * Status bar integration for Connascence analyzer.
 *
 * Shows current connascence status and metrics in VS Code's status bar.
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.ConnascenceStatusBar = void 0;
const vscode = __importStar(require("vscode"));
class ConnascenceStatusBar {
    constructor(context) {
        this.context = context;
        this.isScanning = false;
        this.lastScanResults = null;
        // Create status bar item
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100 // Priority - higher number = more to the left
        );
        this.statusBarItem.command = 'connascence.openDashboard';
        this.statusBarItem.tooltip = 'Click to open Connascence Dashboard';
        // Start with default state
        this.update();
        this.statusBarItem.show();
        // Register for disposal
        this.context.subscriptions.push(this.statusBarItem);
    }
    update(scanResults) {
        if (scanResults) {
            this.lastScanResults = scanResults;
        }
        const config = vscode.workspace.getConfiguration('connascence');
        const baselineMode = config.get('baselineMode', false);
        if (this.isScanning) {
            this.statusBarItem.text = '$(loading~spin) Connascence: Scanning...';
            this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
            return;
        }
        if (!this.lastScanResults) {
            this.statusBarItem.text = '$(link) Connascence: Ready';
            this.statusBarItem.backgroundColor = undefined;
            return;
        }
        const results = this.lastScanResults;
        const violationCount = results.violations?.length || 0;
        if (violationCount === 0) {
            this.statusBarItem.text = '$(check) Connascence: Clean';
            this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.prominentBackground');
            this.statusBarItem.tooltip = 'No connascence violations found';
        }
        else {
            // Calculate connascence index if available
            const connascenceIndex = results.summary?.connascence_index || this.calculateSimpleIndex(results.violations);
            // Determine status based on violation severity
            const critical = results.violations?.filter((v) => v.severity === 'critical').length || 0;
            const high = results.violations?.filter((v) => v.severity === 'high').length || 0;
            let icon = '$(warning)';
            let bgColor = new vscode.ThemeColor('statusBarItem.warningBackground');
            if (critical > 0) {
                icon = '$(error)';
                bgColor = new vscode.ThemeColor('statusBarItem.errorBackground');
            }
            else if (high === 0) {
                icon = '$(info)';
                bgColor = new vscode.ThemeColor('statusBarItem.prominentBackground');
            }
            this.statusBarItem.text = `${icon} Connascence: ${violationCount} (${connascenceIndex.toFixed(1)})`;
            this.statusBarItem.backgroundColor = bgColor;
            // Build detailed tooltip
            const tooltip = this.buildTooltip(results, baselineMode);
            this.statusBarItem.tooltip = tooltip;
        }
    }
    calculateSimpleIndex(violations) {
        if (!violations || violations.length === 0)
            return 0.0;
        // Simple connascence index calculation
        // Based on violation count and severity weights
        const weights = { critical: 10, high: 5, medium: 2, low: 1 };
        let totalWeight = 0;
        for (const violation of violations) {
            const weight = weights[violation.severity] || 1;
            totalWeight += weight;
        }
        return totalWeight;
    }
    buildTooltip(results, baselineMode) {
        const violations = results.violations || [];
        const summary = results.summary || {};
        const critical = violations.filter((v) => v.severity === 'critical').length;
        const high = violations.filter((v) => v.severity === 'high').length;
        const medium = violations.filter((v) => v.severity === 'medium').length;
        const low = violations.filter((v) => v.severity === 'low').length;
        const lines = [
            `Connascence Analysis Results`,
            ``,
            `Total Violations: ${violations.length}`,
            `• Critical: ${critical}`,
            `• High: ${high}`,
            `• Medium: ${medium}`,
            `• Low: ${low}`
        ];
        if (summary.connascence_index) {
            lines.push(``);
            lines.push(`Connascence Index: ${summary.connascence_index.toFixed(1)}`);
        }
        if (baselineMode) {
            lines.push(``);
            lines.push(`🔒 Baseline Mode: Only new violations shown`);
        }
        // Add most common violation types
        if (summary.violations_by_type) {
            const topTypes = Object.entries(summary.violations_by_type)
                .sort(([, a], [, b]) => b - a)
                .slice(0, 3);
            if (topTypes.length > 0) {
                lines.push(``);
                lines.push(`Top Issues:`);
                for (const [type, count] of topTypes) {
                    lines.push(`• ${type}: ${count}`);
                }
            }
        }
        lines.push(``);
        lines.push(`Click to open dashboard`);
        return lines.join('\n');
    }
    setScanningState(scanning) {
        this.isScanning = scanning;
        this.update();
    }
    showTemporaryMessage(message, durationMs = 3000) {
        const originalText = this.statusBarItem.text;
        const originalBg = this.statusBarItem.backgroundColor;
        this.statusBarItem.text = message;
        this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.prominentBackground');
        setTimeout(() => {
            this.statusBarItem.text = originalText;
            this.statusBarItem.backgroundColor = originalBg;
        }, durationMs);
    }
    dispose() {
        this.statusBarItem.dispose();
    }
}
exports.ConnascenceStatusBar = ConnascenceStatusBar;
//# sourceMappingURL=statusBar.js.map