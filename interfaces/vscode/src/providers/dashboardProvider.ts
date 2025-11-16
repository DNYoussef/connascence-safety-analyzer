import * as vscode from 'vscode';
import { ConnascenceService, Finding, NormalizedAnalysisPayload, BackendStatus } from '../services/connascenceService';

export class DashboardItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly value?: string,
        public readonly contextValue?: string,
        public readonly command?: vscode.Command,
        public readonly iconPath?: vscode.ThemeIcon | vscode.Uri,
        public readonly resourceUri?: vscode.Uri
    ) {
        super(label, collapsibleState);
        this.tooltip = value ? `${label}: ${value}` : label;
        this.description = value || '';
        this.contextValue = contextValue;
        this.iconPath = iconPath;
        this.resourceUri = resourceUri;
        
        // Set default icons based on context
        if (!iconPath && contextValue) {
            this.iconPath = this.getDefaultIcon(contextValue);
        }
    }
    
    private getDefaultIcon(contextValue: string): vscode.ThemeIcon {
        switch (contextValue) {
            case 'qualityOverview':
                return new vscode.ThemeIcon('dashboard');
            case 'metricsSection':
                return new vscode.ThemeIcon('graph');
            case 'safetyCompliance':
                return new vscode.ThemeIcon('shield');
            case 'recentAnalysis':
                return new vscode.ThemeIcon('history');
            case 'quickActions':
                return new vscode.ThemeIcon('tools');
            case 'configSection':
                return new vscode.ThemeIcon('settings-gear');
            case 'reportsSection':
                return new vscode.ThemeIcon('file-text');
            case 'metric':
                return new vscode.ThemeIcon('symbol-number');
            case 'action':
                return new vscode.ThemeIcon('play');
            case 'config':
                return new vscode.ThemeIcon('gear');
            case 'report':
                return new vscode.ThemeIcon('file');
            case 'progress':
                return new vscode.ThemeIcon('loading');
            case 'error':
                return new vscode.ThemeIcon('error', new vscode.ThemeColor('errorForeground'));
            case 'warning':
                return new vscode.ThemeIcon('warning', new vscode.ThemeColor('warningForeground'));
            case 'success':
                return new vscode.ThemeIcon('check', new vscode.ThemeColor('terminal.ansiGreen'));
            default:
                return new vscode.ThemeIcon('circle-outline');
        }
    }
}

export interface DashboardFilter {
    searchQuery?: string;
    severityFilter?: string[];
    fileTypeFilter?: string[];
    showCriticalOnly?: boolean;
    showRecentFiles?: boolean;
}

export class ConnascenceDashboardProvider implements vscode.TreeDataProvider<DashboardItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<DashboardItem | undefined | null | void> = new vscode.EventEmitter<DashboardItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<DashboardItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private qualityMetrics: any = null;
    private analysisResults: any = null;
    private analysisProgress: { isRunning: boolean; currentFile?: string; progress?: number } = { isRunning: false };
    private configData: any = null;
    private reportHistory: any[] = [];
    private currentFilter: DashboardFilter = {};
    private allFindings: Finding[] = [];
    private backendStatus: BackendStatus | null = null;
    private findingsByFile: Map<string, Finding[]> = new Map();
    private serviceSubscriptions: vscode.Disposable[] = [];
    private lastAnalysisTime: Date | null = null;

    constructor(private connascenceService: ConnascenceService) {
        if (this.connascenceService) {
            this.serviceSubscriptions.push(
                this.connascenceService.onAnalysisUpdated(event => this.handleAnalysisUpdate(event))
            );
            this.serviceSubscriptions.push(
                this.connascenceService.onBackendStatusChanged(status => {
                    this.backendStatus = status;
                    this.refresh();
                })
            );
        }
    }

    dispose(): void {
        for (const disposable of this.serviceSubscriptions) {
            disposable.dispose();
        }
        this.serviceSubscriptions = [];
    }

    // Search and filter methods
    setFilter(filter: DashboardFilter): void {
        this.currentFilter = { ...this.currentFilter, ...filter };
        this.refresh();
    }

    clearFilter(): void {
        this.currentFilter = {};
        this.refresh();
    }

    getActiveFilter(): DashboardFilter {
        return { ...this.currentFilter };
    }

    search(query: string): void {
        this.setFilter({ searchQuery: query });
    }

    filterBySeverity(severities: string[]): void {
        this.setFilter({ severityFilter: severities });
    }

    filterByFileType(fileTypes: string[]): void {
        this.setFilter({ fileTypeFilter: fileTypes });
    }

    toggleCriticalOnly(): void {
        this.setFilter({ showCriticalOnly: !this.currentFilter.showCriticalOnly });
    }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    updateData(qualityMetrics: any, analysisResults: any, findings?: Finding[]) {
        this.qualityMetrics = qualityMetrics;
        this.analysisResults = analysisResults;
        if (findings) {
            this.allFindings = findings;
        }
        this.refresh();
    }
    
    updateProgress(progress: { isRunning: boolean; currentFile?: string; progress?: number }) {
        this.analysisProgress = progress;
        this.refresh();
    }
    
    updateConfig(configData: any) {
        this.configData = configData;
        this.refresh();
    }
    
    addReport(report: any) {
        this.reportHistory.unshift(report);
        if (this.reportHistory.length > 10) {
            this.reportHistory = this.reportHistory.slice(0, 10);
        }
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
            case 'metricsSection':
                return Promise.resolve(this.getMetricsSectionChildren());
            case 'safetyCompliance':
                return Promise.resolve(this.getSafetyComplianceChildren());
            case 'recentAnalysis':
                return Promise.resolve(this.getRecentAnalysisChildren());
            case 'quickActions':
                return Promise.resolve(this.getQuickActionsChildren());
            case 'configSection':
                return Promise.resolve(this.getConfigSectionChildren());
            case 'reportsSection':
                return Promise.resolve(this.getReportsSectionChildren());
            case 'analysisSettings':
                return Promise.resolve(this.getAnalysisSettingsChildren());
            case 'qualityGates':
                return Promise.resolve(this.getQualityGatesChildren());
            case 'thresholds':
                return Promise.resolve(this.getThresholdsChildren());
            default:
                return Promise.resolve([]);
        }
    }

    private getRootElements(): DashboardItem[] {
        const elements = [
            new DashboardItem(
                'Quality Overview',
                vscode.TreeItemCollapsibleState.Expanded,
                undefined,
                'qualityOverview'
            ),
            new DashboardItem(
                'Metrics & Analysis',
                vscode.TreeItemCollapsibleState.Collapsed,
                undefined,
                'metricsSection'
            ),
            new DashboardItem(
                'Safety & Compliance',
                vscode.TreeItemCollapsibleState.Collapsed,
                undefined,
                'safetyCompliance'
            ),
            new DashboardItem(
                'Recent Activity',
                vscode.TreeItemCollapsibleState.Collapsed,
                undefined,
                'recentAnalysis'
            ),
            new DashboardItem(
                'Configuration',
                vscode.TreeItemCollapsibleState.Collapsed,
                undefined,
                'configSection'
            ),
            new DashboardItem(
                'Reports & Export',
                vscode.TreeItemCollapsibleState.Collapsed,
                undefined,
                'reportsSection'
            ),
            new DashboardItem(
                'Quick Actions',
                vscode.TreeItemCollapsibleState.Collapsed,
                undefined,
                'quickActions'
            )
        ];

        if (this.backendStatus) {
            elements.unshift(new DashboardItem(
                `Analyzer Health: ${this.backendStatus.active.toUpperCase()}`,
                vscode.TreeItemCollapsibleState.None,
                this.getHealthDescription(),
                'health',
                { command: 'connascence.showAnalyzerHealth', title: 'Show Analyzer Health' },
                new vscode.ThemeIcon(this.backendStatus.active === 'mcp' ? 'cloud' : 'circuit-board')
            ));
        }

        // Add progress indicator if analysis is running
        if (this.analysisProgress.isRunning) {
            elements.unshift(new DashboardItem(
                `Analyzing${this.analysisProgress.currentFile ? ': ' + this.analysisProgress.currentFile : '...'}`,
                vscode.TreeItemCollapsibleState.None,
                this.analysisProgress.progress ? `${this.analysisProgress.progress}%` : 'In Progress',
                'progress',
                undefined,
                new vscode.ThemeIcon('sync~spin')
            ));
        }
        
        return elements;
    }

    private handleAnalysisUpdate(event: NormalizedAnalysisPayload): void {
        this.findingsByFile.set(event.filePath, event.result.findings);
        this.allFindings = Array.from(this.findingsByFile.values()).flat();
        this.analysisResults = event.result;
        this.lastAnalysisTime = new Date(event.timestamp);
        this.refresh();
    }

    private getHealthDescription(): string {
        if (!this.backendStatus) {
            return 'Analyzer health unknown';
        }

        const { availability, mcpConnected } = this.backendStatus;
        const pythonStatus = availability.python.available ? 'Python analyzer ready' : availability.python.reason || 'Python missing';
        const cliStatus = availability.cli.available ? 'CLI available' : availability.cli.reason || 'CLI missing';
        const mcpStatus = mcpConnected ? 'MCP connected' : 'MCP offline';
        return `${pythonStatus} • ${cliStatus} • ${mcpStatus}`;
    }

    private getQualityOverviewChildren(): DashboardItem[] {
        if (!this.qualityMetrics) {
            return [
                new DashboardItem(
                    'No data available',
                    vscode.TreeItemCollapsibleState.None,
                    'Run analysis first',
                    'info',
                    {
                        command: 'connascence.analyzeWorkspace',
                        title: 'Run Analysis'
                    }
                )
            ];
        }

        const filteredMetrics = this.applyFilterToMetrics();
        const score = filteredMetrics.overallScore || 0;
        const scoreIcon = score >= 80 ? 'success' : score >= 60 ? 'warning' : 'error';
        
        const children = [
            new DashboardItem(
                'Overall Quality Score',
                vscode.TreeItemCollapsibleState.None,
                `${score}/100`,
                scoreIcon
            ),
            new DashboardItem(
                'Project Health Status',
                vscode.TreeItemCollapsibleState.None,
                this.getHealthStatus(score),
                scoreIcon
            ),
            new DashboardItem(
                'Last Analysis',
                vscode.TreeItemCollapsibleState.None,
                this.qualityMetrics.lastAnalysis || 'Never',
                'metric'
            ),
            new DashboardItem(
                'Trend',
                vscode.TreeItemCollapsibleState.None,
                this.qualityMetrics.trend || 'No data',
                'metric'
            )
        ];

        // Add filter status indicator
        if (this.hasActiveFilter()) {
            children.push(new DashboardItem(
                'Active Filters',
                vscode.TreeItemCollapsibleState.None,
                this.getFilterDescription(),
                'filter-indicator',
                {
                    command: 'connascence.clearFilter',
                    title: 'Clear Filters'
                }
            ));
        }

        return children;
    }
    
    private getHealthStatus(score: number): string {
        if (score >= 90) return 'Excellent';
        if (score >= 80) return 'Good';
        if (score >= 70) return 'Fair';
        if (score >= 60) return 'Poor';
        return 'Critical';
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

        let recentFiles = this.analysisResults.recentFiles;
        
        // Apply search filter to recent files
        if (this.currentFilter.searchQuery) {
            const query = this.currentFilter.searchQuery.toLowerCase();
            recentFiles = recentFiles.filter((file: any) => 
                file.name.toLowerCase().includes(query) ||
                file.path.toLowerCase().includes(query)
            );
        }

        // Apply file type filter
        if (this.currentFilter.fileTypeFilter?.length) {
            recentFiles = recentFiles.filter((file: any) => {
                const ext = this.getFileExtension(file.path);
                return this.currentFilter.fileTypeFilter!.includes(ext);
            });
        }

        // Show critical-only files if filter is active
        if (this.currentFilter.showCriticalOnly) {
            recentFiles = recentFiles.filter((file: any) => file.criticalIssues > 0);
        }

        const limitedFiles = recentFiles.slice(0, 10); // Increased limit when filtering
        
        return limitedFiles.map((file: any) => 
            new DashboardItem(
                file.name,
                vscode.TreeItemCollapsibleState.None,
                this.getFileIssueDescription(file),
                'recentFile',
                {
                    command: 'vscode.open',
                    title: 'Open File',
                    arguments: [vscode.Uri.file(file.path)]
                }
            )
        );
    }

    private getFileIssueDescription(file: any): string {
        const parts = [];
        if (file.criticalIssues > 0) {
            parts.push(`${file.criticalIssues} critical`);
        }
        if (file.issues > file.criticalIssues) {
            parts.push(`${file.issues - file.criticalIssues} other`);
        }
        if (parts.length === 0) {
            parts.push('No issues');
        }
        return parts.join(', ');
    }

    private getQuickActionsChildren(): DashboardItem[] {
        const actions = [
            new DashboardItem(
                'Search & Filter',
                vscode.TreeItemCollapsibleState.None,
                undefined,
                'action',
                {
                    command: 'connascence.showSearchPanel',
                    title: 'Open Search Panel'
                }
            ),
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
                'Filter by Critical',
                vscode.TreeItemCollapsibleState.None,
                this.currentFilter.showCriticalOnly ? 'Active' : 'Inactive',
                'action',
                {
                    command: 'connascence.toggleCriticalFilter',
                    title: 'Toggle Critical Filter'
                }
            )
        ];

        // Add clear filter action if filters are active
        if (this.hasActiveFilter()) {
            actions.push(new DashboardItem(
                'Clear All Filters',
                vscode.TreeItemCollapsibleState.None,
                undefined,
                'action',
                {
                    command: 'connascence.clearFilter',
                    title: 'Clear All Filters'
                }
            ));
        }

        actions.push(
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
        );

        return actions;
    }

    private getMetricsSectionChildren(): DashboardItem[] {
        if (!this.qualityMetrics) {
            return [
                new DashboardItem(
                    'No metrics available',
                    vscode.TreeItemCollapsibleState.None,
                    'Run analysis first',
                    'info'
                )
            ];
        }

        return [
            new DashboardItem(
                'Code Quality Metrics',
                vscode.TreeItemCollapsibleState.Expanded,
                undefined,
                'metricsGroup'
            ),
            new DashboardItem(
                '  Total Issues',
                vscode.TreeItemCollapsibleState.None,
                `${this.qualityMetrics.totalIssues || 0}`,
                'metric'
            ),
            new DashboardItem(
                '  Critical Issues',
                vscode.TreeItemCollapsibleState.None,
                `${this.qualityMetrics.criticalIssues || 0}`,
                this.qualityMetrics.criticalIssues > 0 ? 'error' : 'success'
            ),
            new DashboardItem(
                '  Files Analyzed',
                vscode.TreeItemCollapsibleState.None,
                `${this.qualityMetrics.filesAnalyzed || 0}`,
                'metric'
            ),
            new DashboardItem(
                '  Lines of Code',
                vscode.TreeItemCollapsibleState.None,
                `${this.qualityMetrics.linesOfCode || 0}`,
                'metric'
            ),
            new DashboardItem(
                'Issue Distribution',
                vscode.TreeItemCollapsibleState.Expanded,
                undefined,
                'distributionGroup'
            ),
            new DashboardItem(
                '  Critical',
                vscode.TreeItemCollapsibleState.None,
                `${this.qualityMetrics.critical || 0}`,
                'error'
            ),
            new DashboardItem(
                '  Major',
                vscode.TreeItemCollapsibleState.None,
                `${this.qualityMetrics.major || 0}`,
                'warning'
            ),
            new DashboardItem(
                '  Minor',
                vscode.TreeItemCollapsibleState.None,
                `${this.qualityMetrics.minor || 0}`,
                'warning'
            ),
            new DashboardItem(
                '  Info',
                vscode.TreeItemCollapsibleState.None,
                `${this.qualityMetrics.info || 0}`,
                'info'
            )
        ];
    }

    private getConfigSectionChildren(): DashboardItem[] {
        const config = vscode.workspace.getConfiguration('connascence');
        
        return [
            new DashboardItem(
                'Analysis Settings',
                vscode.TreeItemCollapsibleState.Collapsed,
                undefined,
                'analysisSettings'
            ),
            new DashboardItem(
                'Quality Gates',
                vscode.TreeItemCollapsibleState.Collapsed,
                undefined,
                'qualityGates'
            ),
            new DashboardItem(
                'File Exclusions',
                vscode.TreeItemCollapsibleState.None,
                `${config.get('excludePatterns', []).length} patterns`,
                'config',
                {
                    command: 'connascence.editExclusions',
                    title: 'Edit Exclusions'
                }
            ),
            new DashboardItem(
                'Safety Profile',
                vscode.TreeItemCollapsibleState.None,
                config.get<string>('safetyProfile', 'modern_general'),
                'config',
                {
                    command: 'connascence.changeSafetyProfile',
                    title: 'Change Safety Profile'
                }
            ),
            new DashboardItem(
                'Open Settings File',
                vscode.TreeItemCollapsibleState.None,
                undefined,
                'action',
                {
                    command: 'connascence.openSettings',
                    title: 'Open Settings'
                },
                new vscode.ThemeIcon('settings-gear')
            )
        ];
    }

    private getReportsSectionChildren(): DashboardItem[] {
        return [
            new DashboardItem(
                'Export Options',
                vscode.TreeItemCollapsibleState.Expanded,
                undefined,
                'exportGroup'
            ),
            new DashboardItem(
                '  HTML Report',
                vscode.TreeItemCollapsibleState.None,
                undefined,
                'action',
                {
                    command: 'connascence.exportHTML',
                    title: 'Generate HTML Report'
                },
                new vscode.ThemeIcon('browser')
            ),
            new DashboardItem(
                '  JSON Export',
                vscode.TreeItemCollapsibleState.None,
                undefined,
                'action',
                {
                    command: 'connascence.exportJSON',
                    title: 'Export as JSON'
                },
                new vscode.ThemeIcon('json')
            ),
            new DashboardItem(
                '  CSV Export',
                vscode.TreeItemCollapsibleState.None,
                undefined,
                'action',
                {
                    command: 'connascence.exportCSV',
                    title: 'Export as CSV'
                },
                new vscode.ThemeIcon('table')
            ),
            new DashboardItem(
                'Report History',
                vscode.TreeItemCollapsibleState.Collapsed,
                `${this.reportHistory.length} reports`,
                'historyGroup'
            ),
            ...this.reportHistory.slice(0, 5).map((report: any) => 
                new DashboardItem(
                    `  ${report.name}`,
                    vscode.TreeItemCollapsibleState.None,
                    report.date,
                    'report',
                    {
                        command: 'vscode.open',
                        title: 'Open Report',
                        arguments: [vscode.Uri.file(report.path)]
                    },
                    new vscode.ThemeIcon('file')
                )
            )
        ];
    }

    private getAnalysisSettingsChildren(): DashboardItem[] {
        const config = vscode.workspace.getConfiguration('connascence');
        
        return [
            new DashboardItem(
                'Analysis Depth',
                vscode.TreeItemCollapsibleState.None,
                config.get<string>('analysisDepth', 'moderate'),
                'config'
            ),
            new DashboardItem(
                'Include Tests',
                vscode.TreeItemCollapsibleState.None,
                config.get<boolean>('includeTests', true) ? 'Yes' : 'No',
                'config'
            ),
            new DashboardItem(
                'Max File Size',
                vscode.TreeItemCollapsibleState.None,
                `${config.get<number>('maxFileSize', 1000)}KB`,
                'config'
            )
        ];
    }

    private getQualityGatesChildren(): DashboardItem[] {
        const config = vscode.workspace.getConfiguration('connascence');
        
        return [
            new DashboardItem(
                'Critical Issues',
                vscode.TreeItemCollapsibleState.None,
                `Max: ${config.get<number>('gates.critical', 0)}`,
                'config'
            ),
            new DashboardItem(
                'Overall Score',
                vscode.TreeItemCollapsibleState.None,
                `Min: ${config.get<number>('gates.score', 80)}`,
                'config'
            ),
            new DashboardItem(
                'Coverage Threshold',
                vscode.TreeItemCollapsibleState.None,
                `Min: ${config.get<number>('gates.coverage', 80)}%`,
                'config'
            )
        ];
    }

    private getThresholdsChildren(): DashboardItem[] {
        const config = vscode.workspace.getConfiguration('connascence');
        
        return [
            new DashboardItem(
                'Complexity Threshold',
                vscode.TreeItemCollapsibleState.None,
                `${config.get<number>('thresholds.complexity', 10)}`,
                'config'
            ),
            new DashboardItem(
                'File Size Threshold',
                vscode.TreeItemCollapsibleState.None,
                `${config.get<number>('thresholds.fileSize', 500)} lines`,
                'config'
            ),
            new DashboardItem(
                'Connascence Distance',
                vscode.TreeItemCollapsibleState.None,
                `Max: ${config.get<number>('thresholds.distance', 5)}`,
                'config'
            )
        ];
    }

    // Filter and search helper methods
    private applyFilterToMetrics(): any {
        if (!this.hasActiveFilter() || !this.allFindings.length) {
            return this.qualityMetrics;
        }

        const filteredFindings = this.applyFilterToFindings(this.allFindings);
        const criticalFindings = filteredFindings.filter(f => f.severity === 'critical');
        const majorFindings = filteredFindings.filter(f => f.severity === 'major');
        const uniqueFiles = new Set(filteredFindings.map(f => f.file));

        return {
            overallScore: this.calculateFilteredScore(filteredFindings),
            totalIssues: filteredFindings.length,
            filesAnalyzed: uniqueFiles.size,
            criticalIssues: criticalFindings.length,
            majorIssues: majorFindings.length
        };
    }

    private calculateFilteredScore(findings: Finding[]): number {
        if (!findings.length) return 100;
        
        const severityWeights = { critical: 10, major: 5, minor: 2, info: 1 };
        const totalWeight = findings.reduce((sum, f) => sum + (severityWeights[f.severity as keyof typeof severityWeights] || 1), 0);
        const maxScore = 100;
        const penalty = Math.min(totalWeight * 2, maxScore);
        
        return Math.max(0, maxScore - penalty);
    }

    private hasActiveFilter(): boolean {
        return !!(this.currentFilter.searchQuery ||
                 this.currentFilter.severityFilter?.length ||
                 this.currentFilter.fileTypeFilter?.length ||
                 this.currentFilter.showCriticalOnly);
    }

    private getFilterDescription(): string {
        const descriptions = [];
        
        if (this.currentFilter.searchQuery) {
            descriptions.push(`Search: "${this.currentFilter.searchQuery}"`);
        }
        if (this.currentFilter.severityFilter?.length) {
            descriptions.push(`Severity: ${this.currentFilter.severityFilter.join(', ')}`);
        }
        if (this.currentFilter.fileTypeFilter?.length) {
            descriptions.push(`Files: ${this.currentFilter.fileTypeFilter.join(', ')}`);
        }
        if (this.currentFilter.showCriticalOnly) {
            descriptions.push('Critical only');
        }
        
        return descriptions.join(' | ');
    }

    private applyFilterToFindings(findings: Finding[]): Finding[] {
        let filtered = [...findings];

        // Search query filter
        if (this.currentFilter.searchQuery) {
            const query = this.currentFilter.searchQuery.toLowerCase();
            const isRegex = this.isRegexPattern(query);
            
            if (isRegex) {
                try {
                    const regex = new RegExp(query.slice(1, -1), 'i');
                    filtered = filtered.filter(f => 
                        regex.test(f.message) || 
                        regex.test(f.type) || 
                        regex.test(f.file)
                    );
                } catch (e) {
                    // Invalid regex, fall back to string search
                    filtered = filtered.filter(f => 
                        f.message.toLowerCase().includes(query) ||
                        f.type.toLowerCase().includes(query) ||
                        f.file.toLowerCase().includes(query)
                    );
                }
            } else {
                filtered = filtered.filter(f => 
                    f.message.toLowerCase().includes(query) ||
                    f.type.toLowerCase().includes(query) ||
                    f.file.toLowerCase().includes(query)
                );
            }
        }

        // Severity filter
        if (this.currentFilter.severityFilter?.length) {
            filtered = filtered.filter(f => 
                this.currentFilter.severityFilter!.includes(f.severity)
            );
        }

        // File type filter
        if (this.currentFilter.fileTypeFilter?.length) {
            filtered = filtered.filter(f => {
                const ext = this.getFileExtension(f.file);
                return this.currentFilter.fileTypeFilter!.includes(ext);
            });
        }

        // Critical only filter
        if (this.currentFilter.showCriticalOnly) {
            filtered = filtered.filter(f => f.severity === 'critical');
        }

        return filtered;
    }

    private isRegexPattern(query: string): boolean {
        return query.startsWith('/') && query.endsWith('/') && query.length > 2;
    }

    private getFileExtension(filePath: string): string {
        const ext = filePath.split('.').pop()?.toLowerCase();
        return ext || 'unknown';
    }
}