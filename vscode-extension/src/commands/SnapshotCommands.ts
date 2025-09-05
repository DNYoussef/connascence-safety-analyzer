/**
 * Snapshot Commands for VS Code Extension
 * =======================================
 * 
 * Provides comprehensive baseline snapshot management through VS Code commands:
 * - Create baseline snapshots from current codebase
 * - List and manage existing snapshots
 * - View baseline comparison and budget status
 * - Integrate with MCP server for enterprise features
 * 
 * Commands exposed:
 * - connascence.createSnapshot
 * - connascence.listSnapshots
 * - connascence.compareWithBaseline
 * - connascence.showBudgetStatus
 * - connascence.showBaselineInfo
 */

import * as vscode from 'vscode';
import { ConnascenceService } from '../services/connascenceService';
import { OutputChannelLogger } from '../utils/OutputChannelLogger';

export class SnapshotCommands {
    private connascenceService: ConnascenceService;
    private logger: OutputChannelLogger;
    private statusBarItem: vscode.StatusBarItem;

    constructor(
        connascenceService: ConnascenceService, 
        logger: OutputChannelLogger
    ) {
        this.connascenceService = connascenceService;
        this.logger = logger;
        
        // Create status bar item for baseline status
        this.statusBarItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Left, 
            100
        );
        this.statusBarItem.command = 'connascence.showBudgetStatus';
        this.statusBarItem.show();
        
        // Initialize with baseline info
        this.updateStatusBar();
    }

    /**
     * Register all snapshot-related commands with VS Code
     */
    registerCommands(context: vscode.ExtensionContext): void {
        const commands = [
            vscode.commands.registerCommand(
                'connascence.createSnapshot', 
                () => this.createSnapshot()
            ),
            vscode.commands.registerCommand(
                'connascence.listSnapshots', 
                () => this.listSnapshots()
            ),
            vscode.commands.registerCommand(
                'connascence.compareWithBaseline', 
                () => this.compareWithBaseline()
            ),
            vscode.commands.registerCommand(
                'connascence.showBudgetStatus', 
                () => this.showBudgetStatus()
            ),
            vscode.commands.registerCommand(
                'connascence.showBaselineInfo', 
                () => this.showBaselineInfo()
            ),
            vscode.commands.registerCommand(
                'connascence.refreshBaseline', 
                () => this.refreshBaseline()
            )
        ];

        commands.forEach(disposable => {
            context.subscriptions.push(disposable);
        });

        context.subscriptions.push(this.statusBarItem);
    }

    /**
     * Create a new baseline snapshot
     */
    async createSnapshot(): Promise<void> {
        try {
            this.logger.info('Creating baseline snapshot...');

            // Get description from user
            const description = await vscode.window.showInputBox({
                prompt: 'Enter a description for this baseline snapshot',
                placeHolder: 'e.g., "Release 1.0 baseline", "After refactoring cleanup"',
                value: `Snapshot created on ${new Date().toLocaleDateString()}`
            });

            if (description === undefined) {
                return; // User cancelled
            }

            // Show progress
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: 'Creating baseline snapshot',
                cancellable: false
            }, async (progress) => {
                progress.report({ message: 'Analyzing codebase...' });

                try {
                    // Call MCP server to create snapshot
                    const result = await this.connascenceService.callMcpTool('snapshot_create', {
                        description: description,
                        project_path: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '.'
                    });

                    if (result.success) {
                        progress.report({ message: 'Snapshot created successfully' });
                        
                        // Show success message with details
                        const action = await vscode.window.showInformationMessage(
                            `Baseline snapshot created successfully!\\n` +
                            `Created: ${new Date(result.snapshot_created_at).toLocaleString()}\\n` +
                            `Violations captured: ${result.total_violations}\\n` +
                            `Commit: ${result.commit_hash?.substring(0, 8) || 'N/A'}`,
                            'View Details', 'Compare Now'
                        );

                        if (action === 'View Details') {
                            await this.showBaselineInfo();
                        } else if (action === 'Compare Now') {
                            await this.compareWithBaseline();
                        }

                        // Update status bar
                        await this.updateStatusBar();
                        
                        this.logger.info(`Snapshot created: ${result.baseline_file}`);
                    } else {
                        throw new Error(result.error || result.message || 'Unknown error');
                    }

                } catch (error) {
                    progress.report({ message: 'Failed to create snapshot' });
                    throw error;
                }
            });

        } catch (error) {
            const errorMessage = `Failed to create baseline snapshot: ${error}`;
            this.logger.error(errorMessage);
            vscode.window.showErrorMessage(errorMessage);
        }
    }

    /**
     * List available baseline snapshots
     */
    async listSnapshots(): Promise<void> {
        try {
            this.logger.info('Listing baseline snapshots...');

            const result = await this.connascenceService.callMcpTool('snapshot_list', {});

            if (result.success) {
                if (result.snapshots.length === 0) {
                    const action = await vscode.window.showInformationMessage(
                        'No baseline snapshots found. Create your first snapshot to start tracking changes.',
                        'Create Snapshot'
                    );
                    
                    if (action === 'Create Snapshot') {
                        await this.createSnapshot();
                    }
                    return;
                }

                // Create quick pick items from snapshots
                const items = result.snapshots.map((snapshot: any) => ({
                    label: snapshot.description || 'Unnamed snapshot',
                    description: `${new Date(snapshot.created_at).toLocaleString()}`,
                    detail: `Violations: ${snapshot.total_violations} | Commit: ${snapshot.commit_hash?.substring(0, 8) || 'N/A'}`,
                    snapshot: snapshot
                }));

                const selected = await vscode.window.showQuickPick(items, {
                    placeHolder: 'Select a baseline snapshot to view details',
                    title: 'Baseline Snapshots'
                });

                if (selected) {
                    // Show detailed information about selected snapshot
                    await this.showSnapshotDetails(selected.snapshot);
                }

            } else {
                throw new Error(result.error || result.message || 'Failed to list snapshots');
            }

        } catch (error) {
            const errorMessage = `Failed to list snapshots: ${error}`;
            this.logger.error(errorMessage);
            vscode.window.showErrorMessage(errorMessage);
        }
    }

    /**
     * Compare current codebase with baseline
     */
    async compareWithBaseline(): Promise<void> {
        try {
            this.logger.info('Comparing with baseline...');

            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: 'Comparing with baseline',
                cancellable: false
            }, async (progress) => {
                progress.report({ message: 'Analyzing current codebase...' });

                const result = await this.connascenceService.callMcpTool('compare_scans', {
                    project_path: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '.',
                    include_details: true
                });

                if (result.success) {
                    progress.report({ message: 'Comparison complete' });
                    
                    const comparison = result.comparison;
                    
                    if (comparison.status === 'no_baseline') {
                        const action = await vscode.window.showWarningMessage(
                            'No baseline found. Create a baseline snapshot to start tracking changes.',
                            'Create Snapshot'
                        );
                        
                        if (action === 'Create Snapshot') {
                            await this.createSnapshot();
                        }
                        return;
                    }

                    // Show comparison results
                    await this.showComparisonResults(comparison, result);
                    
                    // Update status bar
                    await this.updateStatusBar();

                } else {
                    throw new Error(result.error || result.message || 'Comparison failed');
                }
            });

        } catch (error) {
            const errorMessage = `Failed to compare with baseline: ${error}`;
            this.logger.error(errorMessage);
            vscode.window.showErrorMessage(errorMessage);
        }
    }

    /**
     * Show budget status
     */
    async showBudgetStatus(): Promise<void> {
        try {
            this.logger.info('Checking budget status...');

            const result = await this.connascenceService.callMcpTool('budgets_status', {
                project_path: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '.'
            });

            if (result.success) {
                await this.showBudgetStatusDetails(result);
            } else {
                throw new Error(result.error || result.message || 'Failed to get budget status');
            }

        } catch (error) {
            const errorMessage = `Failed to check budget status: ${error}`;
            this.logger.error(errorMessage);
            vscode.window.showErrorMessage(errorMessage);
        }
    }

    /**
     * Show detailed baseline information
     */
    async showBaselineInfo(): Promise<void> {
        try {
            this.logger.info('Getting baseline information...');

            const result = await this.connascenceService.callMcpTool('baseline_info', {});

            if (result.success) {
                const info = result.baseline_info;
                
                if (info.status === 'no_baseline') {
                    const action = await vscode.window.showInformationMessage(
                        'No baseline exists yet. Create one to start tracking code quality over time.',
                        'Create Baseline'
                    );
                    
                    if (action === 'Create Baseline') {
                        await this.createSnapshot();
                    }
                    return;
                }

                // Show detailed baseline information
                const message = [
                    `**Baseline Information**`,
                    ``,
                    `Created: ${new Date(info.created_at).toLocaleString()}`,
                    `Commit: ${info.commit_hash?.substring(0, 8) || 'N/A'} (${info.branch || 'unknown branch'})`,
                    `Description: ${info.description}`,
                    `Total violations: ${info.total_violations}`,
                    ``,
                    `**Severity breakdown:**`,
                    `• Critical: ${info.metadata?.severity_counts?.critical || 0}`,
                    `• High: ${info.metadata?.severity_counts?.high || 0}`,
                    `• Medium: ${info.metadata?.severity_counts?.medium || 0}`,
                    `• Low: ${info.metadata?.severity_counts?.low || 0}`,
                    ``,
                    `Location: ${result.file_info?.path || 'Unknown'}`
                ].join('\\n');

                const action = await vscode.window.showInformationMessage(
                    message,
                    'Compare Now', 'Create New Snapshot'
                );

                if (action === 'Compare Now') {
                    await this.compareWithBaseline();
                } else if (action === 'Create New Snapshot') {
                    await this.createSnapshot();
                }

            } else {
                throw new Error(result.error || result.message || 'Failed to get baseline info');
            }

        } catch (error) {
            const errorMessage = `Failed to get baseline information: ${error}`;
            this.logger.error(errorMessage);
            vscode.window.showErrorMessage(errorMessage);
        }
    }

    /**
     * Refresh baseline status
     */
    private async refreshBaseline(): Promise<void> {
        await this.updateStatusBar();
        vscode.window.showInformationMessage('Baseline status refreshed');
    }

    /**
     * Update status bar with current baseline status
     */
    private async updateStatusBar(): Promise<void> {
        try {
            const result = await this.connascenceService.callMcpTool('budgets_status', {
                project_path: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '.'
            });

            if (result.success) {
                const budgetStatus = result.budget_status;
                const newViolations = budgetStatus.new_violations?.current || 0;
                const budget = budgetStatus.new_violations?.budget || 0;
                
                if (result.overall_status === 'over_budget') {
                    this.statusBarItem.text = `$(error) New Debt: ${newViolations}/${budget}`;
                    this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
                    this.statusBarItem.tooltip = `Budget exceeded! ${newViolations} new violations (budget: ${budget})`;
                } else if (newViolations > 0) {
                    this.statusBarItem.text = `$(warning) New Debt: ${newViolations}/${budget}`;
                    this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
                    this.statusBarItem.tooltip = `${newViolations} new violations within budget (${budget})`;
                } else {
                    this.statusBarItem.text = `$(check) No New Debt`;
                    this.statusBarItem.backgroundColor = undefined;
                    this.statusBarItem.tooltip = 'No new violations detected';
                }
            } else {
                // No baseline or error
                this.statusBarItem.text = `$(info) No Baseline`;
                this.statusBarItem.backgroundColor = undefined;
                this.statusBarItem.tooltip = 'No baseline snapshot available. Click to create one.';
            }
        } catch (error) {
            this.statusBarItem.text = `$(error) Baseline Error`;
            this.statusBarItem.backgroundColor = undefined;
            this.statusBarItem.tooltip = `Error checking baseline status: ${error}`;
        }
    }

    /**
     * Show detailed comparison results
     */
    private async showComparisonResults(comparison: any, fullResult: any): Promise<void> {
        const message = [
            `**Baseline Comparison Results**`,
            ``,
            `Baseline: ${new Date(comparison.baseline_created_at).toLocaleString()}`,
            `Branch: ${comparison.baseline_branch || 'unknown'}`,
            `Commit: ${comparison.baseline_commit?.substring(0, 8) || 'N/A'}`,
            ``,
            `**Changes:**`,
            `• Current violations: ${comparison.total_current}`,
            `• Baseline violations: ${comparison.total_baseline}`,
            `• New violations: ${comparison.new_violations}`,
            `• Resolved violations: ${comparison.resolved_violations}`,
            `• Net change: ${comparison.net_change >= 0 ? '+' : ''}${comparison.net_change}`,
            ``,
            `**Budget Status:**`,
            `• High severity new: ${fullResult.budget_impact?.new_high_severity || 0}`,
            `• Budget exceeded: ${fullResult.budget_impact?.budget_exceeded ? 'Yes' : 'No'}`,
            ``,
            `Improvement: ${comparison.improvement_percentage.toFixed(1)}%`
        ].join('\\n');

        const buttons = [];
        if (comparison.new_violations > 0) {
            buttons.push('Show New Violations');
        }
        buttons.push('View Budget Details');

        const action = await vscode.window.showInformationMessage(message, ...buttons);

        if (action === 'Show New Violations') {
            await this.showNewViolations(fullResult.new_violations_only || []);
        } else if (action === 'View Budget Details') {
            await this.showBudgetStatus();
        }
    }

    /**
     * Show new violations in detail
     */
    private async showNewViolations(newViolations: any[]): Promise<void> {
        if (newViolations.length === 0) {
            vscode.window.showInformationMessage('No new violations found!');
            return;
        }

        // Create quick pick items for new violations
        const items = newViolations.map((violation, index) => ({
            label: `${violation.type || 'Unknown'}: ${violation.description || 'No description'}`,
            description: `${violation.file}:${violation.line}`,
            detail: `Severity: ${violation.severity}`,
            violation: violation
        }));

        const selected = await vscode.window.showQuickPick(items, {
            placeHolder: 'Select a new violation to view details',
            title: `New Violations (${newViolations.length})`
        });

        if (selected) {
            // Open file and go to violation location
            const uri = vscode.Uri.file(selected.violation.file);
            const document = await vscode.workspace.openTextDocument(uri);
            const editor = await vscode.window.showTextDocument(document);
            
            const line = Math.max(0, selected.violation.line - 1);
            const position = new vscode.Position(line, selected.violation.column || 0);
            
            editor.selection = new vscode.Selection(position, position);
            editor.revealRange(new vscode.Range(position, position));
        }
    }

    /**
     * Show detailed budget status
     */
    private async showBudgetStatusDetails(result: any): Promise<void> {
        const budgetStatus = result.budget_status;
        
        const message = [
            `**Budget Status: ${result.overall_status.toUpperCase()}**`,
            ``,
            `**Total Violations:**`,
            `• Current: ${budgetStatus.total_violations.current}`,
            `• Budget: ${budgetStatus.total_violations.budget}`,
            `• Status: ${budgetStatus.total_violations.over_budget ? '❌ Over Budget' : '✅ Within Budget'}`,
            ``,
            `**Critical Violations:**`,
            `• Current: ${budgetStatus.critical_violations.current}`,
            `• Budget: ${budgetStatus.critical_violations.budget}`,
            `• Status: ${budgetStatus.critical_violations.over_budget ? '❌ Over Budget' : '✅ Within Budget'}`,
            ``,
            `**High Violations:**`,
            `• Current: ${budgetStatus.high_violations.current}`,
            `• Budget: ${budgetStatus.high_violations.budget}`,
            `• Status: ${budgetStatus.high_violations.over_budget ? '❌ Over Budget' : '✅ Within Budget'}`,
            ``,
            `**New Violations (this PR):**`,
            `• Current: ${budgetStatus.new_violations.current}`,
            `• Budget: ${budgetStatus.new_violations.budget}`,
            `• Status: ${budgetStatus.new_violations.over_budget ? '❌ Over Budget' : '✅ Within Budget'}`,
            ``,
            `CI Status: ${result.should_fail_ci ? 'Would FAIL' : 'Would PASS'}`
        ].join('\\n');

        const action = await vscode.window.showInformationMessage(
            message,
            'Compare with Baseline', 'Create New Snapshot'
        );

        if (action === 'Compare with Baseline') {
            await this.compareWithBaseline();
        } else if (action === 'Create New Snapshot') {
            await this.createSnapshot();
        }
    }

    /**
     * Show detailed snapshot information
     */
    private async showSnapshotDetails(snapshot: any): Promise<void> {
        const message = [
            `**Snapshot Details**`,
            ``,
            `Description: ${snapshot.description}`,
            `Created: ${new Date(snapshot.created_at).toLocaleString()}`,
            `Commit: ${snapshot.commit_hash?.substring(0, 8) || 'N/A'}`,
            `Branch: ${snapshot.branch || 'unknown'}`,
            `Total violations: ${snapshot.total_violations}`,
            ``,
            `**Severity breakdown:**`,
            `• Critical: ${snapshot.metadata?.severity_counts?.critical || 0}`,
            `• High: ${snapshot.metadata?.severity_counts?.high || 0}`,
            `• Medium: ${snapshot.metadata?.severity_counts?.medium || 0}`,
            `• Low: ${snapshot.metadata?.severity_counts?.low || 0}`,
            ``,
            `Files affected: ${snapshot.metadata?.files_affected || 'Unknown'}`
        ].join('\\n');

        vscode.window.showInformationMessage(message);
    }

    dispose(): void {
        this.statusBarItem.dispose();
    }
}