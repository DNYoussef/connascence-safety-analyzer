import * as vscode from 'vscode';
import * as path from 'path';
import { ConnascenceService, Finding, AnalysisResult } from '../services/connascenceService';

export class ConnascenceTreeProvider implements vscode.TreeDataProvider<ConnascenceTreeItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<ConnascenceTreeItem | undefined | null | void> = new vscode.EventEmitter<ConnascenceTreeItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<ConnascenceTreeItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private findings: Finding[] = [];
    private groupBy: 'severity' | 'type' | 'file' = 'severity';

    constructor(private connascenceService: ConnascenceService) {}

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    setGroupBy(groupBy: 'severity' | 'type' | 'file'): void {
        this.groupBy = groupBy;
        this.refresh();
    }

    setFindings(findings: Finding[]): void {
        this.findings = findings;
        this.refresh();
    }

    getTreeItem(element: ConnascenceTreeItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: ConnascenceTreeItem): Thenable<ConnascenceTreeItem[]> {
        if (!element) {
            // Root level - show groups
            return Promise.resolve(this.getGroups());
        } else if (element.contextValue === 'group') {
            // Group level - show findings in group
            return Promise.resolve(this.getFindingsInGroup(element));
        } else {
            // Finding level - no children
            return Promise.resolve([]);
        }
    }

    private getGroups(): ConnascenceTreeItem[] {
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

    private getGroupsBySeverity(): ConnascenceTreeItem[] {
        const severities = ['critical', 'major', 'minor', 'info'];
        const groups: ConnascenceTreeItem[] = [];

        for (const severity of severities) {
            const severityFindings = this.findings.filter(f => f.severity === severity);
            if (severityFindings.length === 0) continue;

            const item = new ConnascenceTreeItem(
                `${this.capitalize(severity)} (${severityFindings.length})`,
                vscode.TreeItemCollapsibleState.Expanded,
                'group'
            );
            item.iconPath = this.getSeverityIcon(severity);
            item.tooltip = `${severityFindings.length} ${severity} issue(s)`;
            item.groupKey = severity;
            groups.push(item);
        }

        return groups;
    }

    private getGroupsByType(): ConnascenceTreeItem[] {
        const typeGroups = new Map<string, Finding[]>();
        
        for (const finding of this.findings) {
            if (!typeGroups.has(finding.type)) {
                typeGroups.set(finding.type, []);
            }
            typeGroups.get(finding.type)!.push(finding);
        }

        const groups: ConnascenceTreeItem[] = [];
        for (const [type, findings] of typeGroups.entries()) {
            const item = new ConnascenceTreeItem(
                `${this.formatType(type)} (${findings.length})`,
                vscode.TreeItemCollapsibleState.Expanded,
                'group'
            );
            item.iconPath = new vscode.ThemeIcon('symbol-class');
            item.tooltip = `${findings.length} ${type} issue(s)`;
            item.groupKey = type;
            groups.push(item);
        }

        return groups.sort((a, b) => a.label!.toString().localeCompare(b.label!.toString()));
    }

    private getGroupsByFile(): ConnascenceTreeItem[] {
        const fileGroups = new Map<string, Finding[]>();
        
        for (const finding of this.findings) {
            if (!fileGroups.has(finding.file)) {
                fileGroups.set(finding.file, []);
            }
            fileGroups.get(finding.file)!.push(finding);
        }

        const groups: ConnascenceTreeItem[] = [];
        for (const [filePath, findings] of fileGroups.entries()) {
            const fileName = path.basename(filePath);
            const item = new ConnascenceTreeItem(
                `${fileName} (${findings.length})`,
                vscode.TreeItemCollapsibleState.Expanded,
                'group'
            );
            item.iconPath = vscode.ThemeIcon.File;
            item.tooltip = `${filePath}\n${findings.length} issue(s)`;
            item.groupKey = filePath;
            item.resourceUri = vscode.Uri.file(filePath);
            groups.push(item);
        }

        return groups.sort((a, b) => a.label!.toString().localeCompare(b.label!.toString()));
    }

    private getFindingsInGroup(group: ConnascenceTreeItem): ConnascenceTreeItem[] {
        let groupFindings: Finding[];

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

    private createFindingItem(finding: Finding): ConnascenceTreeItem {
        const label = this.groupBy === 'file' 
            ? `Line ${finding.line}: ${finding.message}`
            : `${path.basename(finding.file)}:${finding.line} - ${finding.message}`;

        const item = new ConnascenceTreeItem(
            label,
            vscode.TreeItemCollapsibleState.None,
            'finding'
        );

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
                    selection: new vscode.Range(
                        finding.line - 1, (finding.column || 1) - 1,
                        finding.line - 1, (finding.column || 1) - 1 + 10
                    )
                }
            ]
        };

        return item;
    }

    private createFindingTooltip(finding: Finding): string {
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

    private getSeverityIcon(severity: string): vscode.ThemeIcon {
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

    private formatType(type: string): string {
        return type.replace(/_/g, ' ')
                   .replace(/\b\w/g, l => l.toUpperCase());
    }

    private capitalize(str: string): string {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    // Public methods for external control
    addFindings(newFindings: Finding[]): void {
        this.findings.push(...newFindings);
        this.refresh();
    }

    clearFindings(): void {
        this.findings = [];
        this.refresh();
    }

    filterFindings(predicate: (finding: Finding) => boolean): void {
        this.findings = this.findings.filter(predicate);
        this.refresh();
    }

    getSummary(): {
        total: number;
        bySeverity: { [severity: string]: number };
        byType: { [type: string]: number };
    } {
        const summary = {
            total: this.findings.length,
            bySeverity: {} as { [severity: string]: number },
            byType: {} as { [type: string]: number }
        };

        for (const finding of this.findings) {
            summary.bySeverity[finding.severity] = (summary.bySeverity[finding.severity] || 0) + 1;
            summary.byType[finding.type] = (summary.byType[finding.type] || 0) + 1;
        }

        return summary;
    }
}

class ConnascenceTreeItem extends vscode.TreeItem {
    groupKey?: string;
    finding?: Finding;

    constructor(
        public override readonly label: string,
        public override readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public override readonly contextValue: string
    ) {
        super(label, collapsibleState);
    }
}