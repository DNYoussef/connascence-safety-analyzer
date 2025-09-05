"use strict";
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
exports.AnalysisResultsProvider = exports.AnalysisResultItem = void 0;
const vscode = __importStar(require("vscode"));
class AnalysisResultItem extends vscode.TreeItem {
    constructor(label, collapsibleState, finding, contextValue, command) {
        super(label, collapsibleState);
        this.label = label;
        this.collapsibleState = collapsibleState;
        this.finding = finding;
        this.contextValue = contextValue;
        this.command = command;
        if (finding) {
            this.tooltip = `${finding.type}: ${finding.message}`;
            this.description = `Line ${finding.line}`;
            this.contextValue = `finding-${finding.severity}`;
            // Set icon based on severity
            switch (finding.severity) {
                case 'critical':
                    this.iconPath = new vscode.ThemeIcon('error', new vscode.ThemeColor('errorForeground'));
                    break;
                case 'major':
                    this.iconPath = new vscode.ThemeIcon('warning', new vscode.ThemeColor('warningForeground'));
                    break;
                case 'minor':
                    this.iconPath = new vscode.ThemeIcon('warning', new vscode.ThemeColor('warningForeground'));
                    break;
                case 'info':
                    this.iconPath = new vscode.ThemeIcon('info', new vscode.ThemeColor('foreground'));
                    break;
                default:
                    this.iconPath = new vscode.ThemeIcon('circle-outline');
            }
        }
    }
}
exports.AnalysisResultItem = AnalysisResultItem;
class AnalysisResultsProvider {
    constructor() {
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
        this.analysisResults = new Map();
        this.groupBy = 'file';
    }
    refresh() {
        this._onDidChangeTreeData.fire();
    }
    updateResults(results) {
        this.analysisResults = results;
        this.refresh();
    }
    setGroupBy(groupBy) {
        this.groupBy = groupBy;
        this.refresh();
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        if (!element) {
            return Promise.resolve(this.getRootElements());
        }
        if (element.contextValue?.startsWith('file-')) {
            const filePath = element.label;
            const findings = this.analysisResults.get(filePath) || [];
            return Promise.resolve(this.getFindingElements(findings));
        }
        if (element.contextValue?.startsWith('severity-')) {
            const severity = element.contextValue.replace('severity-', '');
            const findings = this.getFindingsBySeverity(severity);
            return Promise.resolve(this.getFindingElements(findings));
        }
        if (element.contextValue?.startsWith('type-')) {
            const type = element.contextValue.replace('type-', '');
            const findings = this.getFindingsByType(type);
            return Promise.resolve(this.getFindingElements(findings));
        }
        return Promise.resolve([]);
    }
    getRootElements() {
        if (this.analysisResults.size === 0) {
            return [
                new AnalysisResultItem('No analysis results available', vscode.TreeItemCollapsibleState.None)
            ];
        }
        switch (this.groupBy) {
            case 'file':
                return this.getFileGroupElements();
            case 'severity':
                return this.getSeverityGroupElements();
            case 'type':
                return this.getTypeGroupElements();
            default:
                return this.getFileGroupElements();
        }
    }
    getFileGroupElements() {
        const elements = [];
        for (const [filePath, findings] of this.analysisResults) {
            const fileName = filePath.split('/').pop() || filePath;
            const issueCount = findings.length;
            const severity = this.getHighestSeverity(findings);
            elements.push(new AnalysisResultItem(fileName, vscode.TreeItemCollapsibleState.Collapsed, undefined, `file-${severity}`, {
                command: 'vscode.open',
                title: 'Open File',
                arguments: [vscode.Uri.file(filePath)]
            }));
        }
        return elements.sort((a, b) => a.label.localeCompare(b.label));
    }
    getSeverityGroupElements() {
        const severityGroups = new Map();
        for (const findings of this.analysisResults.values()) {
            for (const finding of findings) {
                if (!severityGroups.has(finding.severity)) {
                    severityGroups.set(finding.severity, []);
                }
                severityGroups.get(finding.severity).push(finding);
            }
        }
        const elements = [];
        const severityOrder = ['critical', 'major', 'minor', 'info'];
        for (const severity of severityOrder) {
            if (severityGroups.has(severity)) {
                const findings = severityGroups.get(severity);
                elements.push(new AnalysisResultItem(`${severity.toUpperCase()} (${findings.length})`, vscode.TreeItemCollapsibleState.Collapsed, undefined, `severity-${severity}`));
            }
        }
        return elements;
    }
    getTypeGroupElements() {
        const typeGroups = new Map();
        for (const findings of this.analysisResults.values()) {
            for (const finding of findings) {
                if (!typeGroups.has(finding.type)) {
                    typeGroups.set(finding.type, []);
                }
                typeGroups.get(finding.type).push(finding);
            }
        }
        const elements = [];
        for (const [type, findings] of typeGroups) {
            elements.push(new AnalysisResultItem(`${type} (${findings.length})`, vscode.TreeItemCollapsibleState.Collapsed, undefined, `type-${type}`));
        }
        return elements.sort((a, b) => a.label.localeCompare(b.label));
    }
    getFindingElements(findings) {
        return findings.map(finding => {
            const fileName = finding.file.split('/').pop() || finding.file;
            return new AnalysisResultItem(`${finding.message}`, vscode.TreeItemCollapsibleState.None, finding, `finding-${finding.severity}`, {
                command: 'vscode.open',
                title: 'Go to Finding',
                arguments: [
                    vscode.Uri.file(finding.file),
                    {
                        selection: new vscode.Range(new vscode.Position(finding.line - 1, (finding.column || 1) - 1), new vscode.Position(finding.line - 1, (finding.column || 1) - 1 + 10))
                    }
                ]
            });
        });
    }
    getFindingsBySeverity(severity) {
        const findings = [];
        for (const fileFindings of this.analysisResults.values()) {
            findings.push(...fileFindings.filter(f => f.severity === severity));
        }
        return findings;
    }
    getFindingsByType(type) {
        const findings = [];
        for (const fileFindings of this.analysisResults.values()) {
            findings.push(...fileFindings.filter(f => f.type === type));
        }
        return findings;
    }
    getHighestSeverity(findings) {
        const severities = findings.map(f => f.severity);
        if (severities.includes('critical'))
            return 'critical';
        if (severities.includes('major'))
            return 'major';
        if (severities.includes('minor'))
            return 'minor';
        if (severities.includes('info'))
            return 'info';
        return 'info';
    }
}
exports.AnalysisResultsProvider = AnalysisResultsProvider;
//# sourceMappingURL=analysisResultsProvider.js.map