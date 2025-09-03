/**
 * Tree view provider for Connascence violations.
 * 
 * Shows violations organized by file and severity in VS Code's Explorer panel.
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { ConnascenceViolation } from './diagnostics';

export interface FindingTreeItem extends vscode.TreeItem {
    violation?: ConnascenceViolation;
    children?: FindingTreeItem[];
    type: 'root' | 'file' | 'severity' | 'violation';
}

export class ConnascenceTreeView implements vscode.TreeDataProvider<FindingTreeItem> {
    private _onDidChangeTreeData = new vscode.EventEmitter<FindingTreeItem | undefined | null | void>();
    readonly onDidChangeTreeData = this._onDidChangeTreeData.event;
    
    private violations: ConnascenceViolation[] = [];
    
    constructor(private context: vscode.ExtensionContext) {}
    
    getTreeItem(element: FindingTreeItem): vscode.TreeItem {
        return element;
    }
    
    getChildren(element?: FindingTreeItem): FindingTreeItem[] {
        if (!element) {
            // Root level - show summary or files
            return this.getRootItems();
        }
        
        if (element.type === 'file') {
            // Show violations grouped by severity for this file
            return this.getSeverityGroups(element.violation!.filePath);
        }
        
        if (element.type === 'severity') {
            // Show individual violations for this severity level
            return this.getViolationsForSeverity(element.label as string, element.violation?.filePath);
        }
        
        return element.children || [];
    }
    
    private getRootItems(): FindingTreeItem[] {
        if (this.violations.length === 0) {
            return [{
                label: 'No violations found',
                type: 'root',
                iconPath: new vscode.ThemeIcon('check'),
                collapsibleState: vscode.TreeItemCollapsibleState.None
            }];
        }
        
        // Group violations by file
        const fileGroups = new Map<string, ConnascenceViolation[]>();
        for (const violation of this.violations) {
            if (!fileGroups.has(violation.filePath)) {
                fileGroups.set(violation.filePath, []);
            }
            fileGroups.get(violation.filePath)!.push(violation);
        }
        
        const items: FindingTreeItem[] = [];
        
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
    
    private getSeverityGroups(filePath: string): FindingTreeItem[] {
        const fileViolations = this.violations.filter(v => v.filePath === filePath);
        
        // Group by severity
        const severityGroups = new Map<string, ConnascenceViolation[]>();
        for (const violation of fileViolations) {
            if (!severityGroups.has(violation.severity)) {
                severityGroups.set(violation.severity, []);
            }
            severityGroups.get(violation.severity)!.push(violation);
        }
        
        const items: FindingTreeItem[] = [];
        const severityOrder = ['critical', 'high', 'medium', 'low'];
        
        for (const severity of severityOrder) {
            if (severityGroups.has(severity)) {
                const violations = severityGroups.get(severity)!;
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
    
    private getViolationsForSeverity(severity: string, filePath?: string): FindingTreeItem[] {
        let violations = this.violations.filter(v => 
            v.severity === severity.toLowerCase() && 
            (!filePath || v.filePath === filePath)
        );
        
        return violations.map(violation => ({
            label: `${violation.connascenceType}: ${violation.description}`,
            type: 'violation' as const,
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
                        selection: new vscode.Range(
                            new vscode.Position(violation.lineNumber - 1, 0),
                            new vscode.Position(violation.lineNumber - 1, 100)
                        )
                    }
                ]
            },
            contextValue: 'connascenceViolation'
        }));
    }
    
    private getMaxSeverity(violations: ConnascenceViolation[]): string {
        const severityOrder = { 'critical': 4, 'high': 3, 'medium': 2, 'low': 1 };
        let maxSeverity = 'low';
        let maxValue = 0;
        
        for (const violation of violations) {
            const value = severityOrder[violation.severity as keyof typeof severityOrder] || 0;
            if (value > maxValue) {
                maxValue = value;
                maxSeverity = violation.severity;
            }
        }
        
        return maxSeverity;
    }
    
    private getSeverityIcon(severity: string): vscode.ThemeIcon {
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
    
    private getConnascenceTypeIcon(connascenceType: string): vscode.ThemeIcon {
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
    
    updateViolations(violations: ConnascenceViolation[]): void {
        this.violations = violations;
        this.refresh();
    }
    
    refresh(): void {
        this._onDidChangeTreeData.fire();
    }
    
    clear(): void {
        this.violations = [];
        this.refresh();
    }
    
    getViolationCount(): number {
        return this.violations.length;
    }
    
    getSummary(): { total: number; critical: number; high: number; medium: number; low: number } {
        return {
            total: this.violations.length,
            critical: this.violations.filter(v => v.severity === 'critical').length,
            high: this.violations.filter(v => v.severity === 'high').length,
            medium: this.violations.filter(v => v.severity === 'medium').length,
            low: this.violations.filter(v => v.severity === 'low').length
        };
    }
}