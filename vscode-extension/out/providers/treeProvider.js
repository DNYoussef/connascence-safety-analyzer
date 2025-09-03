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
exports.ConnascenceTreeProvider = void 0;
const vscode = __importStar(require("vscode"));
const path = __importStar(require("path"));
class ConnascenceTreeProvider {
    constructor(connascenceService) {
        this.connascenceService = connascenceService;
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
        this.findings = [];
        this.groupBy = 'severity';
    }
    refresh() {
        this._onDidChangeTreeData.fire();
    }
    setGroupBy(groupBy) {
        this.groupBy = groupBy;
        this.refresh();
    }
    setFindings(findings) {
        this.findings = findings;
        this.refresh();
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        if (!element) {
            // Root level - show groups
            return Promise.resolve(this.getGroups());
        }
        else if (element.contextValue === 'group') {
            // Group level - show findings in group
            return Promise.resolve(this.getFindingsInGroup(element));
        }
        else {
            // Finding level - no children
            return Promise.resolve([]);
        }
    }
    getGroups() {
        switch (this.groupBy) {
            case 'severity':
                return this.getGroupsBySeverity();
            case 'type':
                return this.getGroupsByType();
            case 'file':
                return this.getGroupsByFile();
            default:
                return [];
        }
    }
    getGroupsBySeverity() {
        const severities = ['critical', 'major', 'minor', 'info'];
        const groups = [];
        for (const severity of severities) {
            const severityFindings = this.findings.filter(f => f.severity === severity);
            if (severityFindings.length === 0)
                continue;
            const item = new ConnascenceTreeItem(`${this.capitalize(severity)} (${severityFindings.length})`, vscode.TreeItemCollapsibleState.Expanded, 'group');
            item.iconPath = this.getSeverityIcon(severity);
            item.tooltip = `${severityFindings.length} ${severity} issue(s)`;
            item.groupKey = severity;
            groups.push(item);
        }
        return groups;
    }
    getGroupsByType() {
        const typeGroups = new Map();
        for (const finding of this.findings) {
            if (!typeGroups.has(finding.type)) {
                typeGroups.set(finding.type, []);
            }
            typeGroups.get(finding.type).push(finding);
        }
        const groups = [];
        for (const [type, findings] of typeGroups.entries()) {
            const item = new ConnascenceTreeItem(`${this.formatType(type)} (${findings.length})`, vscode.TreeItemCollapsibleState.Expanded, 'group');
            item.iconPath = new vscode.ThemeIcon('symbol-class');
            item.tooltip = `${findings.length} ${type} issue(s)`;
            item.groupKey = type;
            groups.push(item);
        }
        return groups.sort((a, b) => a.label.toString().localeCompare(b.label.toString()));
    }
    getGroupsByFile() {
        const fileGroups = new Map();
        for (const finding of this.findings) {
            if (!fileGroups.has(finding.file)) {
                fileGroups.set(finding.file, []);
            }
            fileGroups.get(finding.file).push(finding);
        }
        const groups = [];
        for (const [filePath, findings] of fileGroups.entries()) {
            const fileName = path.basename(filePath);
            const item = new ConnascenceTreeItem(`${fileName} (${findings.length})`, vscode.TreeItemCollapsibleState.Expanded, 'group');
            item.iconPath = vscode.ThemeIcon.File;
            item.tooltip = `${filePath}\n${findings.length} issue(s)`;
            item.groupKey = filePath;
            item.resourceUri = vscode.Uri.file(filePath);
            groups.push(item);
        }
        return groups.sort((a, b) => a.label.toString().localeCompare(b.label.toString()));
    }
    getFindingsInGroup(group) {
        let groupFindings;
        switch (this.groupBy) {
            case 'severity':
                groupFindings = this.findings.filter(f => f.severity === group.groupKey);
                break;
            case 'type':
                groupFindings = this.findings.filter(f => f.type === group.groupKey);
                break;
            case 'file':
                groupFindings = this.findings.filter(f => f.file === group.groupKey);
                break;
            default:
                groupFindings = [];
        }
        return groupFindings.map(finding => this.createFindingItem(finding));
    }
    createFindingItem(finding) {
        const label = this.groupBy === 'file'
            ? `Line ${finding.line}: ${finding.message}`
            : `${path.basename(finding.file)}:${finding.line} - ${finding.message}`;
        const item = new ConnascenceTreeItem(label, vscode.TreeItemCollapsibleState.None, 'finding');
        item.tooltip = this.createFindingTooltip(finding);
        item.iconPath = this.getSeverityIcon(finding.severity);
        item.finding = finding;
        // Command to navigate to the finding
        item.command = {
            command: 'vscode.open',
            title: 'Open File',
            arguments: [
                vscode.Uri.file(finding.file),
                {
                    selection: new vscode.Range(finding.line - 1, (finding.column || 1) - 1, finding.line - 1, (finding.column || 1) - 1 + 10)
                }
            ]
        };
        return item;
    }
    createFindingTooltip(finding) {
        const lines = [
            `Type: ${this.formatType(finding.type)}`,
            `Severity: ${this.capitalize(finding.severity)}`,
            `File: ${finding.file}`,
            `Line: ${finding.line}`,
            `Message: ${finding.message}`
        ];
        if (finding.suggestion) {
            lines.push(`Suggestion: ${finding.suggestion}`);
        }
        return lines.join('\n');
    }
    getSeverityIcon(severity) {
        switch (severity) {
            case 'critical':
                return new vscode.ThemeIcon('error', new vscode.ThemeColor('errorForeground'));
            case 'major':
                return new vscode.ThemeIcon('warning', new vscode.ThemeColor('warningForeground'));
            case 'minor':
                return new vscode.ThemeIcon('info', new vscode.ThemeColor('foreground'));
            case 'info':
            default:
                return new vscode.ThemeIcon('lightbulb', new vscode.ThemeColor('foreground'));
        }
    }
    formatType(type) {
        return type.replace(/_/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase());
    }
    capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
    // Public methods for external control
    addFindings(newFindings) {
        this.findings.push(...newFindings);
        this.refresh();
    }
    clearFindings() {
        this.findings = [];
        this.refresh();
    }
    filterFindings(predicate) {
        this.findings = this.findings.filter(predicate);
        this.refresh();
    }
    getSummary() {
        const summary = {
            total: this.findings.length,
            bySeverity: {},
            byType: {}
        };
        for (const finding of this.findings) {
            summary.bySeverity[finding.severity] = (summary.bySeverity[finding.severity] || 0) + 1;
            summary.byType[finding.type] = (summary.byType[finding.type] || 0) + 1;
        }
        return summary;
    }
}
exports.ConnascenceTreeProvider = ConnascenceTreeProvider;
class ConnascenceTreeItem extends vscode.TreeItem {
    constructor(label, collapsibleState, contextValue) {
        super(label, collapsibleState);
        this.label = label;
        this.collapsibleState = collapsibleState;
        this.contextValue = contextValue;
    }
}
//# sourceMappingURL=treeProvider.js.map