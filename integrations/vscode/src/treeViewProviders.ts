import * as vscode from 'vscode';

// Violation Tree Item
export class ViolationItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly violation?: any,
        public readonly filePath?: string,
        public readonly line?: number
    ) {
        super(label, collapsibleState);

        if (violation) {
            this.contextValue = 'violation';
            this.tooltip = `${violation.type}: ${violation.description}`;
            this.description = violation.severity;

            // Set icon based on severity
            this.iconPath = new vscode.ThemeIcon(
                violation.severity === 'critical' ? 'error' :
                violation.severity === 'high' ? 'warning' :
                'info'
            );

            // Make it clickable to navigate to file location
            if (filePath && line !== undefined) {
                this.command = {
                    command: 'connascence.openViolation',
                    title: 'Open Violation',
                    arguments: [filePath, line, violation]
                };
            }
        }
    }
}

// Violations Tree Data Provider
export class ViolationsProvider implements vscode.TreeDataProvider<ViolationItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<ViolationItem | undefined | null | void> = new vscode.EventEmitter<ViolationItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<ViolationItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private violations: any[] = [];

    constructor() {}

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    updateViolations(violations: any[]): void {
        this.violations = violations;
        this.refresh();
    }

    getTreeItem(element: ViolationItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: ViolationItem): Thenable<ViolationItem[]> {
        if (!element) {
            // Root level - group by severity
            return Promise.resolve(this.getViolationsByType());
        } else {
            // Child level - show individual violations
            return Promise.resolve([]);
        }
    }

    private getViolationsByType(): ViolationItem[] {
        if (this.violations.length === 0) {
            return [
                new ViolationItem(
                    'No violations found',
                    vscode.TreeItemCollapsibleState.None
                )
            ];
        }

        const items: ViolationItem[] = [];

        // Group by severity
        const critical = this.violations.filter(v => v.severity === 'critical');
        const high = this.violations.filter(v => v.severity === 'high');
        const medium = this.violations.filter(v => v.severity === 'medium');
        const low = this.violations.filter(v => v.severity === 'low');

        if (critical.length > 0) {
            items.push(...this.createViolationItems('Critical', critical));
        }
        if (high.length > 0) {
            items.push(...this.createViolationItems('High', high));
        }
        if (medium.length > 0) {
            items.push(...this.createViolationItems('Medium', medium));
        }
        if (low.length > 0) {
            items.push(...this.createViolationItems('Low', low));
        }

        return items;
    }

    private createViolationItems(severityLabel: string, violations: any[]): ViolationItem[] {
        return violations.map(v =>
            new ViolationItem(
                `${v.type} - ${v.file_path?.split(/[\\/]/).pop() || 'unknown'}:${v.line_number || 0}`,
                vscode.TreeItemCollapsibleState.None,
                v,
                v.file_path,
                v.line_number
            )
        );
    }
}

// Metrics Tree Item
export class MetricItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly value: string | number,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState = vscode.TreeItemCollapsibleState.None
    ) {
        super(label, collapsibleState);
        this.description = value.toString();
        this.tooltip = `${label}: ${value}`;
    }
}

// Metrics Tree Data Provider
export class MetricsProvider implements vscode.TreeDataProvider<MetricItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<MetricItem | undefined | null | void> = new vscode.EventEmitter<MetricItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<MetricItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private metrics: any = {};

    constructor() {}

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    updateMetrics(metrics: any): void {
        this.metrics = metrics;
        this.refresh();
    }

    getTreeItem(element: MetricItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: MetricItem): Thenable<MetricItem[]> {
        if (!element) {
            return Promise.resolve(this.getMetricItems());
        }
        return Promise.resolve([]);
    }

    private getMetricItems(): MetricItem[] {
        if (!this.metrics || Object.keys(this.metrics).length === 0) {
            return [
                new MetricItem('No metrics available', 'Run analysis first')
            ];
        }

        const items: MetricItem[] = [];

        // Quality Score
        if (this.metrics.quality_score !== undefined) {
            items.push(new MetricItem(
                'Quality Score',
                `${(this.metrics.quality_score * 100).toFixed(1)}%`
            ));
        }

        // Total Violations
        if (this.metrics.total_violations !== undefined) {
            items.push(new MetricItem(
                'Total Violations',
                this.metrics.total_violations
            ));
        }

        // Files Analyzed
        if (this.metrics.files_analyzed !== undefined) {
            items.push(new MetricItem(
                'Files Analyzed',
                this.metrics.files_analyzed
            ));
        }

        // NASA Compliance
        if (this.metrics.nasa_compliance_score !== undefined) {
            items.push(new MetricItem(
                'NASA Compliance',
                `${(this.metrics.nasa_compliance_score * 100).toFixed(1)}%`
            ));
        }

        // MECE Score
        if (this.metrics.mece_score !== undefined) {
            items.push(new MetricItem(
                'MECE Score',
                `${(this.metrics.mece_score * 100).toFixed(1)}%`
            ));
        }

        return items;
    }
}

// Actions Tree Item
export class ActionItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly commandId: string,
        public readonly icon: string
    ) {
        super(label, vscode.TreeItemCollapsibleState.None);
        this.command = {
            command: commandId,
            title: label
        };
        this.iconPath = new vscode.ThemeIcon(icon);
    }
}

// Actions Tree Data Provider
export class ActionsProvider implements vscode.TreeDataProvider<ActionItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<ActionItem | undefined | null | void> = new vscode.EventEmitter<ActionItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<ActionItem | undefined | null | void> = this._onDidChangeTreeData.event;

    constructor() {}

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: ActionItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: ActionItem): Thenable<ActionItem[]> {
        if (element) {
            return Promise.resolve([]);
        }

        return Promise.resolve([
            new ActionItem('Analyze Current File', 'connascence.analyze', 'search'),
            new ActionItem('Show Full Report', 'connascence.showReport', 'file-text'),
            new ActionItem('Fix All Violations', 'connascence.fix', 'wrench'),
            new ActionItem('Configure Settings', 'connascence.configure', 'settings-gear')
        ]);
    }
}
