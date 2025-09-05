"use strict";
/**
 * Tree view provider for Connascence violations.
 *
 * Shows violations organized by file and severity in VS Code's Explorer panel.
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
exports.ConnascenceTreeView = void 0;
const vscode = __importStar(require("vscode"));
const path = __importStar(require("path"));
class ConnascenceTreeView {
    constructor(context) {
        this.context = context;
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
        this.violations = [];
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        if (!element) {
            // Root level - show summary or files
            return this.getRootItems();
        }
        if (element.type === 'file') {
            // Show violations grouped by severity for this file
            return this.getSeverityGroups(element.violation.filePath);
        }
        if (element.type === 'severity') {
            // Show individual violations for this severity level
            return this.getViolationsForSeverity(element.label, element.violation?.filePath);
        }
        return element.children || [];
    }
    getRootItems() {
        if (this.violations.length === 0) {
            return [{
                    label: 'No violations found',
                    type: 'root',
                    iconPath: new vscode.ThemeIcon('check'),
                    collapsibleState: vscode.TreeItemCollapsibleState.None
                }];
        }
        // Group violations by file
        const fileGroups = new Map();
        for (const violation of this.violations) {
            if (!fileGroups.has(violation.filePath)) {
                fileGroups.set(violation.filePath, []);
            }
            fileGroups.get(violation.filePath).push(violation);
        }
        const items = [];
        // Add summary item
        const totalViolations = this.violations.length;
        const criticalCount = this.violations.filter(v => v.severity === 'critical').length;
        const highCount = this.violations.filter(v => v.severity === 'high').length;
        items.push({
            label: `${totalViolations} violations found`,
            type: 'root',
            description: `${criticalCount} critical, ${highCount} high`,
            iconPath: new vscode.ThemeIcon('warning'),
            collapsibleState: vscode.TreeItemCollapsibleState.None
        });
        // Add file groups
        for (const [filePath, violations] of fileGroups) {
            const fileName = path.basename(filePath);
            const violationCount = violations.length;
            const maxSeverity = this.getMaxSeverity(violations);
            items.push({
                label: fileName,
                type: 'file',
                description: `${violationCount} violations`,
                tooltip: filePath,
                violation: { ...violations[0], filePath }, // Use first violation but ensure filePath
                iconPath: this.getSeverityIcon(maxSeverity),
                collapsibleState: vscode.TreeItemCollapsibleState.Expanded,
                resourceUri: vscode.Uri.file(filePath)
            });
        }
        return items;
    }
    getSeverityGroups(filePath) {
        const fileViolations = this.violations.filter(v => v.filePath === filePath);
        // Group by severity
        const severityGroups = new Map();
        for (const violation of fileViolations) {
            if (!severityGroups.has(violation.severity)) {
                severityGroups.set(violation.severity, []);
            }
            severityGroups.get(violation.severity).push(violation);
        }
        const items = [];
        const severityOrder = ['critical', 'high', 'medium', 'low'];
        for (const severity of severityOrder) {
            if (severityGroups.has(severity)) {
                const violations = severityGroups.get(severity);
                items.push({
                    label: severity.charAt(0).toUpperCase() + severity.slice(1),
                    type: 'severity',
                    description: `${violations.length} violations`,
                    violation: { ...violations[0], filePath }, // Pass filePath context
                    iconPath: this.getSeverityIcon(severity),
                    collapsibleState: vscode.TreeItemCollapsibleState.Expanded
                });
            }
        }
        return items;
    }
    getViolationsForSeverity(severity, filePath) {
        let violations = this.violations.filter(v => v.severity === severity.toLowerCase() &&
            (!filePath || v.filePath === filePath));
        return violations.map(violation => ({
            label: `${violation.connascenceType}: ${violation.description}`,
            type: 'violation',
            description: `Line ${violation.lineNumber}`,
            tooltip: `${violation.ruleId}: ${violation.description}\nFile: ${violation.filePath}\nLine: ${violation.lineNumber}`,
            violation,
            iconPath: this.getConnascenceTypeIcon(violation.connascenceType),
            collapsibleState: vscode.TreeItemCollapsibleState.None,
            command: {
                command: 'vscode.open',
                title: 'Open File',
                arguments: [
                    vscode.Uri.file(violation.filePath),
                    {
                        selection: new vscode.Range(new vscode.Position(violation.lineNumber - 1, 0), new vscode.Position(violation.lineNumber - 1, 100))
                    }
                ]
            },
            contextValue: 'connascenceViolation'
        }));
    }
    getMaxSeverity(violations) {
        const severityOrder = { 'critical': 4, 'high': 3, 'medium': 2, 'low': 1 };
        let maxSeverity = 'low';
        let maxValue = 0;
        for (const violation of violations) {
            const value = severityOrder[violation.severity] || 0;
            if (value > maxValue) {
                maxValue = value;
                maxSeverity = violation.severity;
            }
        }
        return maxSeverity;
    }
    getSeverityIcon(severity) {
        switch (severity) {
            case 'critical':
                return new vscode.ThemeIcon('error', new vscode.ThemeColor('errorForeground'));
            case 'high':
                return new vscode.ThemeIcon('warning', new vscode.ThemeColor('warningForeground'));
            case 'medium':
                return new vscode.ThemeIcon('info', new vscode.ThemeColor('foreground'));
            case 'low':
            default:
                return new vscode.ThemeIcon('lightbulb', new vscode.ThemeColor('descriptionForeground'));
        }
    }
    getConnascenceTypeIcon(connascenceType) {
        switch (connascenceType) {
            case 'CoN': // Name
                return new vscode.ThemeIcon('symbol-variable');
            case 'CoT': // Type
                return new vscode.ThemeIcon('symbol-interface');
            case 'CoM': // Meaning (magic literals)
                return new vscode.ThemeIcon('symbol-number');
            case 'CoP': // Position
                return new vscode.ThemeIcon('symbol-parameter');
            case 'CoA': // Algorithm
                return new vscode.ThemeIcon('symbol-method');
            case 'CoE': // Execution
                return new vscode.ThemeIcon('debug-step-over');
            case 'CoTi': // Timing
                return new vscode.ThemeIcon('clock');
            case 'CoV': // Value
                return new vscode.ThemeIcon('symbol-constant');
            case 'CoI': // Identity
                return new vscode.ThemeIcon('symbol-object');
            default:
                return new vscode.ThemeIcon('question');
        }
    }
    updateViolations(violations) {
        this.violations = violations;
        this.refresh();
    }
    refresh() {
        this._onDidChangeTreeData.fire();
    }
    clear() {
        this.violations = [];
        this.refresh();
    }
    getViolationCount() {
        return this.violations.length;
    }
    getSummary() {
        return {
            total: this.violations.length,
            critical: this.violations.filter(v => v.severity === 'critical').length,
            high: this.violations.filter(v => v.severity === 'high').length,
            medium: this.violations.filter(v => v.severity === 'medium').length,
            low: this.violations.filter(v => v.severity === 'low').length
        };
    }
}
exports.ConnascenceTreeView = ConnascenceTreeView;
//# sourceMappingURL=treeView.js.map