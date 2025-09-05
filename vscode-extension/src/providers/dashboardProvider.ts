import * as vscode from 'vscode';
import { ConnascenceService } from '../services/connascenceService';

export class DashboardItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly value?: string,
        public readonly contextValue?: string,
        public readonly command?: vscode.Command
    ) {
        super(label, collapsibleState);
        this.tooltip = value ? `${label}: ${value}` : label;
        this.description = value || '';
        this.contextValue = contextValue;
    }
}

export class ConnascenceDashboardProvider implements vscode.TreeDataProvider<DashboardItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<DashboardItem | undefined | null | void> = new vscode.EventEmitter<DashboardItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<DashboardItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private qualityMetrics: any = null;
    private analysisResults: any = null;

    constructor(private connascenceService: ConnascenceService) {}

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    updateData(qualityMetrics: any, analysisResults: any) {
        this.qualityMetrics = qualityMetrics;
        this.analysisResults = analysisResults;
        this.refresh();
    }

    getTreeItem(element: DashboardItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: DashboardItem): Thenable<DashboardItem[]> {
        if (!element) {
            return Promise.resolve(this.getRootElements());
        }
        
        switch (element.contextValue) {
            case 'qualityOverview':
                return Promise.resolve(this.getQualityOverviewChildren());
            case 'recentAnalysis':
                return Promise.resolve(this.getRecentAnalysisChildren());
            case 'safetyCompliance':
                return Promise.resolve(this.getSafetyComplianceChildren());
            case 'quickActions':
                return Promise.resolve(this.getQuickActionsChildren());
            default:
                return Promise.resolve([]);
        }
    }

    private getRootElements(): DashboardItem[] {
        return [
            new DashboardItem(
                'Quality Overview',
                vscode.TreeItemCollapsibleState.Expanded,
                undefined,
                'qualityOverview'
            ),
            new DashboardItem(
                'Safety Compliance',
                vscode.TreeItemCollapsibleState.Expanded,
                undefined,
                'safetyCompliance'
            ),
            new DashboardItem(
                'Recent Analysis',
                vscode.TreeItemCollapsibleState.Expanded,
                undefined,
                'recentAnalysis'
            ),
            new DashboardItem(
                'Quick Actions',
                vscode.TreeItemCollapsibleState.Expanded,
                undefined,
                'quickActions'
            )
        ];
    }

    private getQualityOverviewChildren(): DashboardItem[] {
        if (!this.qualityMetrics) {
            return [
                new DashboardItem('No data available', vscode.TreeItemCollapsibleState.None, 'Run analysis first')
            ];
        }

        return [
            new DashboardItem(
                'Overall Score',
                vscode.TreeItemCollapsibleState.None,
                `${this.qualityMetrics.overallScore || 0}/100`,
                'metric'
            ),
            new DashboardItem(
                'Total Issues',
                vscode.TreeItemCollapsibleState.None,
                `${this.qualityMetrics.totalIssues || 0}`,
                'metric'
            ),
            new DashboardItem(
                'Files Analyzed',
                vscode.TreeItemCollapsibleState.None,
                `${this.qualityMetrics.filesAnalyzed || 0}`,
                'metric'
            ),
            new DashboardItem(
                'Critical Issues',
                vscode.TreeItemCollapsibleState.None,
                `${this.qualityMetrics.criticalIssues || 0}`,
                'metric'
            )
        ];
    }

    private getSafetyComplianceChildren(): DashboardItem[] {
        const config = vscode.workspace.getConfiguration('connascence');
        const safetyProfile = config.get<string>('safetyProfile', 'modern_general');
        
        return [
            new DashboardItem(
                'Current Profile',
                vscode.TreeItemCollapsibleState.None,
                safetyProfile,
                'profile'
            ),
            new DashboardItem(
                'Compliance Status',
                vscode.TreeItemCollapsibleState.None,
                this.qualityMetrics?.compliant ? '✅ Compliant' : '❌ Non-Compliant',
                'compliance'
            ),
            new DashboardItem(
                'Safety Violations',
                vscode.TreeItemCollapsibleState.None,
                `${this.qualityMetrics?.safetyViolations || 0}`,
                'violations'
            )
        ];
    }

    private getRecentAnalysisChildren(): DashboardItem[] {
        if (!this.analysisResults || !this.analysisResults.recentFiles) {
            return [
                new DashboardItem('No recent analysis', vscode.TreeItemCollapsibleState.None)
            ];
        }

        return this.analysisResults.recentFiles.slice(0, 5).map((file: any) => 
            new DashboardItem(
                file.name,
                vscode.TreeItemCollapsibleState.None,
                `${file.issues} issues`,
                'recentFile',
                {
                    command: 'vscode.open',
                    title: 'Open File',
                    arguments: [vscode.Uri.file(file.path)]
                }
            )
        );
    }

    private getQuickActionsChildren(): DashboardItem[] {
        return [
            new DashboardItem(
                'Analyze Current File',
                vscode.TreeItemCollapsibleState.None,
                undefined,
                'action',
                {
                    command: 'connascence.analyzeFile',
                    title: 'Analyze Current File'
                }
            ),
            new DashboardItem(
                'Analyze Workspace',
                vscode.TreeItemCollapsibleState.None,
                undefined,
                'action',
                {
                    command: 'connascence.analyzeWorkspace',
                    title: 'Analyze Workspace'
                }
            ),
            new DashboardItem(
                'Generate Report',
                vscode.TreeItemCollapsibleState.None,
                undefined,
                'action',
                {
                    command: 'connascence.generateReport',
                    title: 'Generate Report'
                }
            ),
            new DashboardItem(
                'Open Settings',
                vscode.TreeItemCollapsibleState.None,
                undefined,
                'action',
                {
                    command: 'connascence.openSettings',
                    title: 'Open Settings'
                }
            )
        ];
    }
}