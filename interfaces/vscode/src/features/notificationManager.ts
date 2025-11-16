import * as vscode from 'vscode';
import { Finding, NormalizedFinding, AnalyzerBackend } from '../services/connascenceService';

export interface NotificationFilter {
    enabled: boolean;
    violationType: string;
    severity: 'error' | 'warning' | 'info' | 'hint';
    displayName: string;
    description: string;
    category: 'connascence' | 'nasa' | 'god_object' | 'general';
}

export class NotificationManager {
    private static instance: NotificationManager;
    private filters: Map<string, NotificationFilter> = new Map();
    private suppressedUntil: Map<string, number> = new Map(); // Temporarily suppress notifications
    private lastPublishedFindings: NormalizedFinding[] = [];
    private lastBackend: AnalyzerBackend = 'python';

    private constructor() {
        this.initializeDefaultFilters();
        this.loadUserPreferences();
        
        // Listen for configuration changes
        vscode.workspace.onDidChangeConfiguration((event) => {
            if (event.affectsConfiguration('connascence.notificationFilters')) {
                this.loadUserPreferences();
            }
        });
    }

    public static getInstance(): NotificationManager {
        if (!NotificationManager.instance) {
            NotificationManager.instance = new NotificationManager();
        }
        return NotificationManager.instance;
    }

    private initializeDefaultFilters() {
        // === 9 CONNASCENCE TYPES ===
        this.addFilter('connascence_of_name', {
            enabled: true,
            violationType: 'connascence_of_name',
            severity: 'warning',
            displayName: '🔗💔 Name Coupling',
            description: 'Multiple entities must agree on the name of an entity',
            category: 'connascence'
        });

        this.addFilter('connascence_of_type', {
            enabled: true,
            violationType: 'connascence_of_type',
            severity: 'warning',
            displayName: '⛓️💥 Type Coupling',
            description: 'Multiple entities must agree on the type of an entity',
            category: 'connascence'
        });

        this.addFilter('connascence_of_meaning', {
            enabled: true,
            violationType: 'connascence_of_meaning',
            severity: 'error',
            displayName: '🔐💢 Magic Values',
            description: 'Multiple entities must agree on the meaning of particular values',
            category: 'connascence'
        });

        this.addFilter('connascence_of_position', {
            enabled: true,
            violationType: 'connascence_of_position',
            severity: 'warning',
            displayName: '🔗📍 Position Coupling',
            description: 'Multiple entities must agree on the order of values',
            category: 'connascence'
        });

        this.addFilter('connascence_of_algorithm', {
            enabled: true,
            violationType: 'connascence_of_algorithm',
            severity: 'error',
            displayName: '⚙️🔗 Algorithm Coupling',
            description: 'Multiple entities must agree on a particular algorithm',
            category: 'connascence'
        });

        this.addFilter('connascence_of_execution', {
            enabled: true,
            violationType: 'connascence_of_execution',
            severity: 'error',
            displayName: '🏃‍♂️🔗 Execution Order',
            description: 'The order of execution of multiple entities is important',
            category: 'connascence'
        });

        this.addFilter('connascence_of_timing', {
            enabled: true,
            violationType: 'connascence_of_timing',
            severity: 'error',
            displayName: '⏰🔗 Timing Coupling',
            description: 'The timing of execution of multiple entities is important',
            category: 'connascence'
        });

        this.addFilter('connascence_of_value', {
            enabled: true,
            violationType: 'connascence_of_value',
            severity: 'warning',
            displayName: '💎🔗 Value Coupling',
            description: 'Several values relate to each other and must change together',
            category: 'connascence'
        });

        this.addFilter('connascence_of_identity', {
            enabled: true,
            violationType: 'connascence_of_identity',
            severity: 'info',
            displayName: '🆔🔗 Identity Coupling',
            description: 'Multiple entities must reference the same entity',
            category: 'connascence'
        });

        // === 10 NASA POWER OF TEN VIOLATIONS ===
        this.addFilter('nasa_rule_1', {
            enabled: true,
            violationType: 'nasa_rule_1',
            severity: 'error',
            displayName: '🚀⚠️ Control Flow Restriction',
            description: 'Avoid complex control flow (goto, setjmp, longjmp, recursion)',
            category: 'nasa'
        });

        this.addFilter('nasa_rule_2', {
            enabled: true,
            violationType: 'nasa_rule_2',
            severity: 'error',
            displayName: '🛰️🔄 Loop Bounds',
            description: 'All loops must have fixed upper bounds',
            category: 'nasa'
        });

        this.addFilter('nasa_rule_3', {
            enabled: true,
            violationType: 'nasa_rule_3',
            severity: 'error',
            displayName: '🚀💾 Dynamic Memory',
            description: 'No dynamic memory allocation after initialization',
            category: 'nasa'
        });

        this.addFilter('nasa_rule_4', {
            enabled: true,
            violationType: 'nasa_rule_4',
            severity: 'warning',
            displayName: '🌌📏 Function Length',
            description: 'Functions should not exceed 60 lines',
            category: 'nasa'
        });

        this.addFilter('nasa_rule_5', {
            enabled: true,
            violationType: 'nasa_rule_5',
            severity: 'warning',
            displayName: '🛸✅ Assertion Density',
            description: 'Maintain minimum assertion density (2 assertions per function)',
            category: 'nasa'
        });

        this.addFilter('nasa_rule_6', {
            enabled: true,
            violationType: 'nasa_rule_6',
            severity: 'warning',
            displayName: '🌠🔒 Data Scope',
            description: 'Restrict the scope of data to the smallest possible',
            category: 'nasa'
        });

        this.addFilter('nasa_rule_7', {
            enabled: true,
            violationType: 'nasa_rule_7',
            severity: 'error',
            displayName: '🚀↩️ Return Values',
            description: 'Check the return value of all non-void functions',
            category: 'nasa'
        });

        this.addFilter('nasa_rule_8', {
            enabled: true,
            violationType: 'nasa_rule_8',
            severity: 'info',
            displayName: '🌌⚡ Preprocessor Use',
            description: 'Use the preprocessor sparingly',
            category: 'nasa'
        });

        this.addFilter('nasa_rule_9', {
            enabled: true,
            violationType: 'nasa_rule_9',
            severity: 'warning',
            displayName: '🛰️👉 Pointer Use',
            description: 'Restrict pointer use (max one level of dereferencing)',
            category: 'nasa'
        });

        this.addFilter('nasa_rule_10', {
            enabled: true,
            violationType: 'nasa_rule_10',
            severity: 'info',
            displayName: '🚀🔍 Compiler Warnings',
            description: 'Compile with all possible warnings active',
            category: 'nasa'
        });

        // === GOD OBJECT DETECTION ===
        this.addFilter('god_object', {
            enabled: true,
            violationType: 'god_object',
            severity: 'error',
            displayName: '👑⚡ God Object',
            description: 'Object has too many responsibilities (anti-pattern)',
            category: 'god_object'
        });

        this.addFilter('god_class', {
            enabled: true,
            violationType: 'god_class',
            severity: 'error',
            displayName: '🏛️⚠️ God Class',
            description: 'Class is overly complex with too many methods/attributes',
            category: 'god_object'
        });

        this.addFilter('god_function', {
            enabled: true,
            violationType: 'god_function',
            severity: 'warning',
            displayName: '⚡🔥 God Function',
            description: 'Function is too long or complex',
            category: 'god_object'
        });

        this.addFilter('large_class', {
            enabled: true,
            violationType: 'large_class',
            severity: 'info',
            displayName: '🏗️📈 Large Class',
            description: 'Class is approaching god object status',
            category: 'god_object'
        });

        this.addFilter('complex_method', {
            enabled: true,
            violationType: 'complex_method',
            severity: 'info',
            displayName: '🧩🔀 Complex Method',
            description: 'Method has high cyclomatic complexity',
            category: 'god_object'
        });
    }

    private addFilter(key: string, filter: NotificationFilter) {
        this.filters.set(key, filter);
    }

    private loadUserPreferences() {
        const config = vscode.workspace.getConfiguration('connascence');
        const userFilters = config.get<{ [key: string]: Partial<NotificationFilter> }>('notificationFilters', {});
        
        // Update filters with user preferences
        for (const [key, userFilter] of Object.entries(userFilters)) {
            const existingFilter = this.filters.get(key);
            if (existingFilter) {
                this.filters.set(key, { ...existingFilter, ...userFilter });
            }
        }
    }

    public shouldShowNotification(finding: Finding): boolean {
        const filter = this.filters.get(finding.type);
        
        if (!filter || !filter.enabled) {
            return false;
        }

        // Check if temporarily suppressed
        const suppressedKey = `${finding.type}_${finding.file}_${finding.line}`;
        const suppressedUntil = this.suppressedUntil.get(suppressedKey);
        if (suppressedUntil && Date.now() < suppressedUntil) {
            return false;
        }

        // Check severity threshold
        const config = vscode.workspace.getConfiguration('connascence');
        const minSeverity = config.get<string>('diagnosticSeverity', 'warning');
        
        return this.compareSeverity(finding.severity, minSeverity) >= 0;
    }

    public getFilteredFindings(findings: Finding[]): Finding[] {
        return findings.filter(finding => this.shouldShowNotification(finding));
    }

    public getAllFilters(): NotificationFilter[] {
        return Array.from(this.filters.values());
    }

    public getFiltersByCategory(category: 'connascence' | 'nasa' | 'god_object' | 'general'): NotificationFilter[] {
        return Array.from(this.filters.values()).filter(filter => filter.category === category);
    }

    public toggleFilter(violationType: string, enabled: boolean): void {
        const filter = this.filters.get(violationType);
        if (filter) {
            filter.enabled = enabled;
            this.saveUserPreferences();
            
            // Notify other components about the change
            vscode.commands.executeCommand('connascence.refreshDiagnostics');
        }
    }

    public setSeverity(violationType: string, severity: 'error' | 'warning' | 'info' | 'hint'): void {
        const filter = this.filters.get(violationType);
        if (filter) {
            filter.severity = severity;
            this.saveUserPreferences();
            vscode.commands.executeCommand('connascence.refreshDiagnostics');
        }
    }

    public suppressTemporarily(finding: Finding, durationMinutes: number = 60): void {
        const suppressedKey = `${finding.type}_${finding.file}_${finding.line}`;
        const suppressedUntil = Date.now() + (durationMinutes * 60 * 1000);
        this.suppressedUntil.set(suppressedKey, suppressedUntil);

        vscode.window.showInformationMessage(
            `🔇 Suppressed "${finding.type}" for ${durationMinutes} minutes`,
            'Undo'
        ).then(selection => {
            if (selection === 'Undo') {
                this.suppressedUntil.delete(suppressedKey);
                vscode.commands.executeCommand('connascence.refreshDiagnostics');
            }
        });

        vscode.commands.executeCommand('connascence.refreshDiagnostics');
    }

    public clearAllSuppressions(): void {
        this.suppressedUntil.clear();
        vscode.commands.executeCommand('connascence.refreshDiagnostics');
        vscode.window.showInformationMessage('🔊 All notification suppressions cleared');
    }

    public publishFindings(findings: NormalizedFinding[], metadata: { backend: AnalyzerBackend; fromCache: boolean }): void {
        this.lastPublishedFindings = findings;
        this.lastBackend = metadata.backend;

        if (findings.length === 0) {
            return;
        }

        const actionable = this.getFilteredFindings(findings).slice(0, 3);
        if (actionable.length === 0) {
            return;
        }

        const summary = actionable
            .map(f => `${(f as NormalizedFinding).emoji || '🔗'} ${f.message}`)
            .join(' • ');

        const suffix = metadata.fromCache ? ' (cache)' : '';
        vscode.window.setStatusBarMessage(
            `Connascence[${metadata.backend.toUpperCase()}] ${summary}${suffix}`,
            4000
        );
    }

    private saveUserPreferences(): void {
        const config = vscode.workspace.getConfiguration('connascence');
        const userFilters: { [key: string]: Partial<NotificationFilter> } = {};
        
        for (const [key, filter] of this.filters) {
            userFilters[key] = {
                enabled: filter.enabled,
                severity: filter.severity
            };
        }
        
        config.update('notificationFilters', userFilters, vscode.ConfigurationTarget.Workspace);
    }

    private compareSeverity(severity1: string, severity2: string): number {
        const severityOrder = ['hint', 'info', 'warning', 'error'];
        const index1 = severityOrder.indexOf(severity1);
        const index2 = severityOrder.indexOf(severity2);
        return index1 - index2;
    }

    public showFilterManagementQuickPick(): void {
        const items: vscode.QuickPickItem[] = [];
        
        // Group by category
        const categories = ['connascence', 'nasa', 'god_object'] as const;
        
        for (const category of categories) {
            const filters = this.getFiltersByCategory(category);
            
            // Add category separator
            items.push({
                label: '',
                kind: vscode.QuickPickItemKind.Separator
            });
            
            items.push({
                label: `${this.getCategoryEmoji(category)} ${category.toUpperCase()} VIOLATIONS`,
                kind: vscode.QuickPickItemKind.Separator
            });
            
            for (const filter of filters) {
                items.push({
                    label: filter.displayName,
                    description: filter.enabled ? '✅ Enabled' : '❌ Disabled',
                    detail: filter.description,
                    picked: filter.enabled
                });
            }
        }

        const quickPick = vscode.window.createQuickPick();
        quickPick.items = items;
        quickPick.canSelectMany = true;
        quickPick.title = '🔗💔 Connascence Notification Controls - Break the Chains!';
        quickPick.placeholder = 'Select violation types to enable/disable notifications';
        
        // Pre-select enabled items
        quickPick.selectedItems = items.filter(item => item.picked);
        
        quickPick.onDidAccept(() => {
            const selectedLabels = new Set(quickPick.selectedItems.map(item => item.label));
            
            for (const [key, filter] of this.filters) {
                const shouldBeEnabled = selectedLabels.has(filter.displayName);
                if (filter.enabled !== shouldBeEnabled) {
                    this.toggleFilter(key, shouldBeEnabled);
                }
            }
            
            quickPick.hide();
            vscode.window.showInformationMessage('🔗 Notification preferences updated!');
        });
        
        quickPick.show();
    }

    private getCategoryEmoji(category: string): string {
        switch (category) {
            case 'connascence': return '🔗💔';
            case 'nasa': return '🚀';
            case 'god_object': return '👑⚡';
            default: return '🚨';
        }
    }
}