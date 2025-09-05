import * as vscode from 'vscode';
import { Finding } from '../services/connascenceService';

export class AnalysisResultItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly finding?: Finding,
        public readonly contextValue?: string,
        public readonly command?: vscode.Command
    ) {
        super(label, collapsibleState);
        if (finding) {
            this.tooltip = `${finding.type}: ${finding.message}`;
            this.description = `Line ${finding.line}`;
            this.contextValue = `finding-${finding.severity}`;
            
            // Set icon based on severity
            switch (finding.severity) {
                case 'error':
                    this.iconPath = new vscode.ThemeIcon('error', new vscode.ThemeColor('errorForeground'));
                    break;
                case 'warning':
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

export class AnalysisResultsProvider implements vscode.TreeDataProvider<AnalysisResultItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<AnalysisResultItem | undefined | null | void> = new vscode.EventEmitter<AnalysisResultItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<AnalysisResultItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private analysisResults: Map<string, Finding[]> = new Map();
    private groupBy: 'file' | 'severity' | 'type' = 'file';

    constructor() {}

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    updateResults(results: Map<string, Finding[]>) {
        this.analysisResults = results;
        this.refresh();
    }

    setGroupBy(groupBy: 'file' | 'severity' | 'type') {
        this.groupBy = groupBy;
        this.refresh();
    }

    getTreeItem(element: AnalysisResultItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: AnalysisResultItem): Thenable<AnalysisResultItem[]> {
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

    private getRootElements(): AnalysisResultItem[] {
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

    private getFileGroupElements(): AnalysisResultItem[] {
        const elements: AnalysisResultItem[] = [];
        
        for (const [filePath, findings] of this.analysisResults) {
            const fileName = filePath.split('/').pop() || filePath;
            const issueCount = findings.length;
            const severity = this.getHighestSeverity(findings);
            
            elements.push(new AnalysisResultItem(
                fileName,
                vscode.TreeItemCollapsibleState.Collapsed,
                undefined,
                `file-${severity}`,
                {
                    command: 'vscode.open',
                    title: 'Open File',
                    arguments: [vscode.Uri.file(filePath)]
                }
            ));
        }
        
        return elements.sort((a, b) => a.label.localeCompare(b.label));
    }

    private getSeverityGroupElements(): AnalysisResultItem[] {
        const severityGroups = new Map<string, Finding[]>();
        
        for (const findings of this.analysisResults.values()) {
            for (const finding of findings) {
                if (!severityGroups.has(finding.severity)) {
                    severityGroups.set(finding.severity, []);
                }
                severityGroups.get(finding.severity)!.push(finding);
            }
        }
        
        const elements: AnalysisResultItem[] = [];
        const severityOrder = ['error', 'warning', 'info', 'hint'];
        
        for (const severity of severityOrder) {
            if (severityGroups.has(severity)) {
                const findings = severityGroups.get(severity)!;
                elements.push(new AnalysisResultItem(
                    `${severity.toUpperCase()} (${findings.length})`,
                    vscode.TreeItemCollapsibleState.Collapsed,
                    undefined,
                    `severity-${severity}`
                ));
            }
        }
        
        return elements;
    }

    private getTypeGroupElements(): AnalysisResultItem[] {
        const typeGroups = new Map<string, Finding[]>();
        
        for (const findings of this.analysisResults.values()) {
            for (const finding of findings) {
                if (!typeGroups.has(finding.type)) {
                    typeGroups.set(finding.type, []);
                }
                typeGroups.get(finding.type)!.push(finding);
            }
        }
        
        const elements: AnalysisResultItem[] = [];
        
        for (const [type, findings] of typeGroups) {
            elements.push(new AnalysisResultItem(
                `${type} (${findings.length})`,
                vscode.TreeItemCollapsibleState.Collapsed,
                undefined,
                `type-${type}`
            ));
        }
        
        return elements.sort((a, b) => a.label.localeCompare(b.label));
    }

    private getFindingElements(findings: Finding[]): AnalysisResultItem[] {
        return findings.map(finding => {
            const fileName = finding.file.split('/').pop() || finding.file;
            return new AnalysisResultItem(
                `${finding.message}`,
                vscode.TreeItemCollapsibleState.None,
                finding,
                `finding-${finding.severity}`,
                {
                    command: 'vscode.open',
                    title: 'Go to Finding',
                    arguments: [
                        vscode.Uri.file(finding.file),
                        {
                            selection: new vscode.Range(
                                new vscode.Position(finding.line - 1, finding.column - 1),
                                new vscode.Position(finding.line - 1, finding.column - 1 + 10)
                            )
                        }
                    ]
                }
            );
        });
    }

    private getFindingsBySeverity(severity: string): Finding[] {
        const findings: Finding[] = [];
        for (const fileFindings of this.analysisResults.values()) {
            findings.push(...fileFindings.filter(f => f.severity === severity));
        }
        return findings;
    }

    private getFindingsByType(type: string): Finding[] {
        const findings: Finding[] = [];
        for (const fileFindings of this.analysisResults.values()) {
            findings.push(...fileFindings.filter(f => f.type === type));
        }
        return findings;
    }

    private getHighestSeverity(findings: Finding[]): string {
        const severities = findings.map(f => f.severity);
        if (severities.includes('error')) return 'error';
        if (severities.includes('warning')) return 'warning';
        if (severities.includes('info')) return 'info';
        return 'hint';
    }
}