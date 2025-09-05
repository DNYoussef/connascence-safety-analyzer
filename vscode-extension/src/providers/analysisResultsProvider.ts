import * as vscode from 'vscode';
import { Finding } from '../services/connascenceService';

export class AnalysisResultItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly finding?: Finding,
        public readonly contextValue?: string,
        public readonly command?: vscode.Command,
        public readonly customIcon?: vscode.ThemeIcon,
        public readonly count?: number
    ) {
        super(label, collapsibleState);
        
        if (finding) {
            this.tooltip = `${finding.type}: ${finding.message}\nFile: ${finding.file}\nLine: ${finding.line}`;
            this.description = `${finding.file.split('/').pop()}:${finding.line}`;
            this.contextValue = contextValue || `finding-${finding.severity}`;
            this.iconPath = this.getSeverityIcon(finding.severity);
        } else if (customIcon) {
            this.iconPath = customIcon;
            this.contextValue = contextValue;
            if (count !== undefined) {
                this.description = `${count} items`;
            }
        } else if (contextValue) {
            this.iconPath = this.getContextIcon(contextValue);
            this.contextValue = contextValue;
            if (count !== undefined) {
                this.description = `${count} items`;
            }
        }
    }
    
    private getSeverityIcon(severity: string): vscode.ThemeIcon {
        switch (severity) {
            case 'critical':
                return new vscode.ThemeIcon('error', new vscode.ThemeColor('errorForeground'));
            case 'major':
                return new vscode.ThemeIcon('warning', new vscode.ThemeColor('warningForeground'));
            case 'minor':
                return new vscode.ThemeIcon('warning', new vscode.ThemeColor('testing.iconQueued'));
            case 'info':
                return new vscode.ThemeIcon('info', new vscode.ThemeColor('foreground'));
            default:
                return new vscode.ThemeIcon('circle-outline');
        }
    }
    
    private getContextIcon(contextValue: string): vscode.ThemeIcon {
        if (contextValue.startsWith('file-')) {
            return new vscode.ThemeIcon('file-code');
        }
        if (contextValue.startsWith('severity-')) {
            const severity = contextValue.replace('severity-', '');
            return this.getSeverityIcon(severity);
        }
        if (contextValue.startsWith('type-')) {
            return new vscode.ThemeIcon('tag');
        }
        if (contextValue === 'summary') {
            return new vscode.ThemeIcon('graph');
        }
        if (contextValue === 'filters') {
            return new vscode.ThemeIcon('filter');
        }
        if (contextValue === 'grouping') {
            return new vscode.ThemeIcon('group-by-ref-type');
        }
        return new vscode.ThemeIcon('circle-outline');
    }
}

export interface AnalysisFilter {
    searchQuery?: string;
    severityFilter?: string[];
    typeFilter?: string[];
    fileTypeFilter?: string[];
    regexMode?: boolean;
    showHiddenFiles?: boolean;
    minSeverity?: string;
}

export class AnalysisResultsProvider implements vscode.TreeDataProvider<AnalysisResultItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<AnalysisResultItem | undefined | null | void> = new vscode.EventEmitter<AnalysisResultItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<AnalysisResultItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private analysisResults: Map<string, Finding[]> = new Map();
    private groupBy: 'file' | 'severity' | 'type' = 'file';
    private currentFilter: AnalysisFilter = {};
    private filteredResults: Map<string, Finding[]> = new Map();
    private showSummary: boolean = true;
    private totalFindings: number = 0;
    private lastAnalysisTime: Date | null = null;

    constructor() {}

    // Search and filter methods
    setFilter(filter: AnalysisFilter): void {
        this.currentFilter = { ...this.currentFilter, ...filter };
        this.applyFilters();
        this.refresh();
    }

    clearFilter(): void {
        this.currentFilter = {};
        this.filteredResults = new Map(this.analysisResults);
        this.refresh();
    }

    getActiveFilter(): AnalysisFilter {
        return { ...this.currentFilter };
    }

    search(query: string, regexMode: boolean = false): void {
        this.setFilter({ searchQuery: query, regexMode });
    }

    filterBySeverity(severities: string[]): void {
        this.setFilter({ severityFilter: severities });
    }

    filterByType(types: string[]): void {
        this.setFilter({ typeFilter: types });
    }

    filterByFileType(fileTypes: string[]): void {
        this.setFilter({ fileTypeFilter: fileTypes });
    }

    setMinSeverity(minSeverity: string): void {
        this.setFilter({ minSeverity });
    }

    toggleRegexMode(): void {
        this.setFilter({ regexMode: !this.currentFilter.regexMode });
    }

    getFilterStats(): { total: number; filtered: number; hidden: number } {
        const total = Array.from(this.analysisResults.values()).flat().length;
        const filtered = Array.from(this.filteredResults.values()).flat().length;
        return {
            total,
            filtered,
            hidden: total - filtered
        };
    }

    private applyFilters(): void {
        this.filteredResults.clear();

        for (const [filePath, findings] of this.analysisResults) {
            const filteredFindings = this.filterFindings(findings);
            if (filteredFindings.length > 0) {
                this.filteredResults.set(filePath, filteredFindings);
            }
        }
    }

    private filterFindings(findings: Finding[]): Finding[] {
        let filtered = [...findings];

        // Search query filter
        if (this.currentFilter.searchQuery) {
            const query = this.currentFilter.searchQuery;
            
            if (this.currentFilter.regexMode) {
                try {
                    const regex = new RegExp(query, 'i');
                    filtered = filtered.filter(f => 
                        regex.test(f.message) || 
                        regex.test(f.type) || 
                        regex.test(f.file) ||
                        regex.test(f.code || '')
                    );
                } catch (e) {
                    // Invalid regex, fall back to string search
                    const lowerQuery = query.toLowerCase();
                    filtered = filtered.filter(f => 
                        f.message.toLowerCase().includes(lowerQuery) ||
                        f.type.toLowerCase().includes(lowerQuery) ||
                        f.file.toLowerCase().includes(lowerQuery) ||
                        (f.code && f.code.toLowerCase().includes(lowerQuery))
                    );
                }
            } else {
                const lowerQuery = query.toLowerCase();
                filtered = filtered.filter(f => 
                    f.message.toLowerCase().includes(lowerQuery) ||
                    f.type.toLowerCase().includes(lowerQuery) ||
                    f.file.toLowerCase().includes(lowerQuery) ||
                    (f.code && f.code.toLowerCase().includes(lowerQuery))
                );
            }
        }

        // Severity filter
        if (this.currentFilter.severityFilter?.length) {
            filtered = filtered.filter(f => 
                this.currentFilter.severityFilter!.includes(f.severity)
            );
        }

        // Type filter
        if (this.currentFilter.typeFilter?.length) {
            filtered = filtered.filter(f => 
                this.currentFilter.typeFilter!.includes(f.type)
            );
        }

        // File type filter
        if (this.currentFilter.fileTypeFilter?.length) {
            filtered = filtered.filter(f => {
                const ext = this.getFileExtension(f.file);
                return this.currentFilter.fileTypeFilter!.includes(ext);
            });
        }

        // Minimum severity filter
        if (this.currentFilter.minSeverity) {
            const severityOrder = ['info', 'minor', 'major', 'critical'];
            const minIndex = severityOrder.indexOf(this.currentFilter.minSeverity);
            if (minIndex >= 0) {
                filtered = filtered.filter(f => {
                    const currentIndex = severityOrder.indexOf(f.severity);
                    return currentIndex >= minIndex;
                });
            }
        }

        return filtered;
    }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    updateResults(results: Map<string, Finding[]>) {
        this.analysisResults = results;
        this.totalFindings = Array.from(results.values()).reduce((sum, findings) => sum + findings.length, 0);
        this.lastAnalysisTime = new Date();
        this.applyFilters();
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
            const findings = this.filteredResults.get(filePath) || [];
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

        if (element.contextValue === 'filter-status') {
            return Promise.resolve(this.getFilterStatusChildren());
        }

        return Promise.resolve([]);
    }

    private getRootElements(): AnalysisResultItem[] {
        const elements: AnalysisResultItem[] = [];

        // Add filter status if filters are active
        if (this.hasActiveFilter()) {
            const stats = this.getFilterStats();
            elements.push(new AnalysisResultItem(
                `Filter: ${stats.filtered}/${stats.total} results`,
                vscode.TreeItemCollapsibleState.Collapsed,
                undefined,
                'filter-status'
            ));
        }

        if (this.filteredResults.size === 0) {
            if (this.analysisResults.size === 0) {
                elements.push(new AnalysisResultItem(
                    'No analysis results available', 
                    vscode.TreeItemCollapsibleState.None
                ));
            } else {
                elements.push(new AnalysisResultItem(
                    'No results match current filter', 
                    vscode.TreeItemCollapsibleState.None
                ));
            }
            return elements;
        }

        switch (this.groupBy) {
            case 'file':
                elements.push(...this.getFileGroupElements());
                break;
            case 'severity':
                elements.push(...this.getSeverityGroupElements());
                break;
            case 'type':
                elements.push(...this.getTypeGroupElements());
                break;
            default:
                elements.push(...this.getFileGroupElements());
        }

        return elements;
    }

    private getFilterStatusChildren(): AnalysisResultItem[] {
        const items: AnalysisResultItem[] = [];
        
        if (this.currentFilter.searchQuery) {
            items.push(new AnalysisResultItem(
                `Search: "${this.currentFilter.searchQuery}"`,
                vscode.TreeItemCollapsibleState.None,
                undefined,
                'filter-detail'
            ));
        }
        
        if (this.currentFilter.severityFilter?.length) {
            items.push(new AnalysisResultItem(
                `Severity: ${this.currentFilter.severityFilter.join(', ')}`,
                vscode.TreeItemCollapsibleState.None,
                undefined,
                'filter-detail'
            ));
        }
        
        if (this.currentFilter.typeFilter?.length) {
            items.push(new AnalysisResultItem(
                `Types: ${this.currentFilter.typeFilter.join(', ')}`,
                vscode.TreeItemCollapsibleState.None,
                undefined,
                'filter-detail'
            ));
        }
        
        if (this.currentFilter.fileTypeFilter?.length) {
            items.push(new AnalysisResultItem(
                `Files: ${this.currentFilter.fileTypeFilter.join(', ')}`,
                vscode.TreeItemCollapsibleState.None,
                undefined,
                'filter-detail'
            ));
        }
        
        if (this.currentFilter.minSeverity) {
            items.push(new AnalysisResultItem(
                `Min Severity: ${this.currentFilter.minSeverity}`,
                vscode.TreeItemCollapsibleState.None,
                undefined,
                'filter-detail'
            ));
        }
        
        items.push(new AnalysisResultItem(
            'Clear All Filters',
            vscode.TreeItemCollapsibleState.None,
            undefined,
            'action',
            {
                command: 'connascence.clearFilter',
                title: 'Clear All Filters'
            }
        ));
        
        return items;
    }

    private hasActiveFilter(): boolean {
        return !!(this.currentFilter.searchQuery ||
                 this.currentFilter.severityFilter?.length ||
                 this.currentFilter.typeFilter?.length ||
                 this.currentFilter.fileTypeFilter?.length ||
                 this.currentFilter.minSeverity);
    }

    private getFileGroupElements(): AnalysisResultItem[] {
        const elements: AnalysisResultItem[] = [];
        
        for (const [filePath, findings] of this.filteredResults) {
            const fileName = filePath.split('/').pop() || filePath;
            const issueCount = findings.length;
            const severity = this.getHighestSeverity(findings);
            const criticalCount = findings.filter(f => f.severity === 'critical').length;
            
            const item = new AnalysisResultItem(
                fileName,
                vscode.TreeItemCollapsibleState.Collapsed,
                undefined,
                `file-${severity}`,
                {
                    command: 'vscode.open',
                    title: 'Open File',
                    arguments: [vscode.Uri.file(filePath)]
                }
            );
            
            // Enhanced description with issue counts
            const descriptions = [];
            if (criticalCount > 0) {
                descriptions.push(`${criticalCount} critical`);
            }
            if (issueCount > criticalCount) {
                descriptions.push(`${issueCount - criticalCount} other`);
            }
            
            item.description = descriptions.join(', ') || `${issueCount} issues`;
            item.tooltip = `${filePath} - ${item.description}`;
            
            elements.push(item);
        }
        
        return elements.sort((a, b) => {
            // Sort by severity first, then by name
            const severityOrder = { 'critical': 0, 'major': 1, 'minor': 2, 'info': 3 };
            const aSeverity = a.contextValue?.split('-')[1] as keyof typeof severityOrder;
            const bSeverity = b.contextValue?.split('-')[1] as keyof typeof severityOrder;
            
            const severityDiff = (severityOrder[aSeverity] || 99) - (severityOrder[bSeverity] || 99);
            if (severityDiff !== 0) {
                return severityDiff;
            }
            
            return a.label.localeCompare(b.label);
        });
    }

    private getSeverityGroupElements(): AnalysisResultItem[] {
        const severityGroups = new Map<string, Finding[]>();
        
        for (const findings of this.filteredResults.values()) {
            for (const finding of findings) {
                if (!severityGroups.has(finding.severity)) {
                    severityGroups.set(finding.severity, []);
                }
                severityGroups.get(finding.severity)!.push(finding);
            }
        }
        
        const elements: AnalysisResultItem[] = [];
        const severityOrder = ['critical', 'major', 'minor', 'info'];
        
        for (const severity of severityOrder) {
            if (severityGroups.has(severity)) {
                const findings = severityGroups.get(severity)!;
                const uniqueFiles = new Set(findings.map(f => f.file));
                
                const item = new AnalysisResultItem(
                    `${severity.toUpperCase()} (${findings.length})`,
                    vscode.TreeItemCollapsibleState.Collapsed,
                    undefined,
                    `severity-${severity}`
                );
                
                item.description = `${uniqueFiles.size} files`;
                item.tooltip = `${findings.length} ${severity} issues across ${uniqueFiles.size} files`;
                
                // Set appropriate icon color
                switch (severity) {
                    case 'critical':
                        item.iconPath = new vscode.ThemeIcon('error', new vscode.ThemeColor('errorForeground'));
                        break;
                    case 'major':
                    case 'minor':
                        item.iconPath = new vscode.ThemeIcon('warning', new vscode.ThemeColor('warningForeground'));
                        break;
                    case 'info':
                        item.iconPath = new vscode.ThemeIcon('info', new vscode.ThemeColor('foreground'));
                        break;
                }
                
                elements.push(item);
            }
        }
        
        return elements;
    }

    private getTypeGroupElements(): AnalysisResultItem[] {
        const typeGroups = new Map<string, Finding[]>();
        
        for (const findings of this.filteredResults.values()) {
            for (const finding of findings) {
                if (!typeGroups.has(finding.type)) {
                    typeGroups.set(finding.type, []);
                }
                typeGroups.get(finding.type)!.push(finding);
            }
        }
        
        const elements: AnalysisResultItem[] = [];
        
        for (const [type, findings] of typeGroups) {
            const criticalCount = findings.filter(f => f.severity === 'critical').length;
            const uniqueFiles = new Set(findings.map(f => f.file));
            
            const item = new AnalysisResultItem(
                `${type} (${findings.length})`,
                vscode.TreeItemCollapsibleState.Collapsed,
                undefined,
                `type-${type.replace(/[^a-zA-Z0-9]/g, '-')}`
            );
            
            const descriptions = [];
            if (criticalCount > 0) {
                descriptions.push(`${criticalCount} critical`);
            }
            descriptions.push(`${uniqueFiles.size} files`);
            
            item.description = descriptions.join(', ');
            item.tooltip = `${type}: ${findings.length} issues across ${uniqueFiles.size} files`;
            
            // Set icon based on highest severity
            const highestSeverity = this.getHighestSeverity(findings);
            switch (highestSeverity) {
                case 'critical':
                    item.iconPath = new vscode.ThemeIcon('error', new vscode.ThemeColor('errorForeground'));
                    break;
                case 'major':
                case 'minor':
                    item.iconPath = new vscode.ThemeIcon('warning', new vscode.ThemeColor('warningForeground'));
                    break;
                case 'info':
                    item.iconPath = new vscode.ThemeIcon('info', new vscode.ThemeColor('foreground'));
                    break;
                default:
                    item.iconPath = new vscode.ThemeIcon('circle-outline');
            }
            
            elements.push(item);
        }
        
        return elements.sort((a, b) => {
            // Sort by severity first, then by name
            const aFindings = typeGroups.get(a.label.split(' (')[0]) || [];
            const bFindings = typeGroups.get(b.label.split(' (')[0]) || [];
            const aSeverity = this.getHighestSeverity(aFindings);
            const bSeverity = this.getHighestSeverity(bFindings);
            
            const severityOrder = { 'critical': 0, 'major': 1, 'minor': 2, 'info': 3 };
            const severityDiff = (severityOrder[aSeverity as keyof typeof severityOrder] || 99) - 
                                (severityOrder[bSeverity as keyof typeof severityOrder] || 99);
            
            if (severityDiff !== 0) {
                return severityDiff;
            }
            
            return a.label.localeCompare(b.label);
        });
    }

    private getFindingElements(findings: Finding[]): AnalysisResultItem[] {
        return findings.map(finding => {
            const fileName = finding.file.split('/').pop() || finding.file;
            const item = new AnalysisResultItem(
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
                                new vscode.Position(finding.line - 1, (finding.column || 1) - 1),
                                new vscode.Position(finding.line - 1, (finding.column || 1) - 1 + 10)
                            )
                        }
                    ]
                }
            );
            
            // Enhanced display with more context
            if (this.groupBy !== 'file') {
                item.description = `${fileName}:${finding.line}`;
            }
            
            // Enhanced tooltip with more details
            const tooltipParts = [
                `${finding.type}: ${finding.message}`,
                `File: ${finding.file}`,
                `Line: ${finding.line}${finding.column ? `, Column: ${finding.column}` : ''}`,
                `Severity: ${finding.severity}`
            ];
            
            if (finding.code) {
                tooltipParts.push(`Code: ${finding.code}`);
            }
            
            item.tooltip = tooltipParts.join('\n');
            
            return item;
        });
    }

    private getFindingsBySeverity(severity: string): Finding[] {
        const findings: Finding[] = [];
        for (const fileFindings of this.filteredResults.values()) {
            findings.push(...fileFindings.filter(f => f.severity === severity));
        }
        return findings.sort(this.sortFindings.bind(this));
    }

    private getFindingsByType(type: string): Finding[] {
        const findings: Finding[] = [];
        const cleanType = type.replace(/-/g, ' ');
        for (const fileFindings of this.filteredResults.values()) {
            findings.push(...fileFindings.filter(f => f.type === cleanType || f.type.replace(/[^a-zA-Z0-9]/g, '-') === type));
        }
        return findings.sort(this.sortFindings.bind(this));
    }

    private sortFindings(a: Finding, b: Finding): number {
        // Sort by file first, then by line number
        const fileDiff = a.file.localeCompare(b.file);
        if (fileDiff !== 0) {
            return fileDiff;
        }
        return a.line - b.line;
    }

    private getFileExtension(filePath: string): string {
        const ext = filePath.split('.').pop()?.toLowerCase();
        return ext || 'unknown';
    }

    // Export filtered results for other components
    getFilteredResults(): Map<string, Finding[]> {
        return new Map(this.filteredResults);
    }

    getAllUniqueTypes(): string[] {
        const types = new Set<string>();
        for (const findings of this.analysisResults.values()) {
            findings.forEach(f => types.add(f.type));
        }
        return Array.from(types).sort();
    }

    getAllUniqueFileTypes(): string[] {
        const fileTypes = new Set<string>();
        for (const filePath of this.analysisResults.keys()) {
            fileTypes.add(this.getFileExtension(filePath));
        }
        return Array.from(fileTypes).sort();
    }

    private getHighestSeverity(findings: Finding[]): string {
        const severities = findings.map(f => f.severity);
        if (severities.includes('critical')) return 'critical';
        if (severities.includes('major')) return 'major';
        if (severities.includes('minor')) return 'minor';
        if (severities.includes('info')) return 'info';
        return 'info';
    }
}