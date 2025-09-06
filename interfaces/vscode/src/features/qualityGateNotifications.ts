import * as vscode from 'vscode';

interface QualityGateResult {
    gateName: string;
    status: 'passed' | 'warning' | 'failed';
    message: string;
    threshold?: number;
    actualValue?: number;
    changedFrom?: 'passed' | 'warning' | 'failed';
}

interface QualityMetrics {
    criticalViolations: number;
    connascenceIndex: number;
    totalViolations: number;
    qualityScore: number;
    overallStatus: 'passed' | 'warning' | 'failed';
}

export class QualityGateNotificationManager {
    private static instance: QualityGateNotificationManager;
    private lastQualityState: QualityMetrics | null = null;
    private notificationHistory: Map<string, { status: string; timestamp: number }> = new Map();

    private constructor() {}

    public static getInstance(): QualityGateNotificationManager {
        if (!QualityGateNotificationManager.instance) {
            QualityGateNotificationManager.instance = new QualityGateNotificationManager();
        }
        return QualityGateNotificationManager.instance;
    }

    public async processQualityGateResults(
        gateResults: QualityGateResult[],
        metrics: QualityMetrics
    ): Promise<void> {
        // Check for status changes
        const hasStatusChanged = this.hasOverallStatusChanged(metrics);
        const criticalGateFailures = gateResults.filter(g => g.status === 'failed');
        const newWarnings = gateResults.filter(g => g.status === 'warning' && 
            this.hasGateStatusChanged(g.gateName, 'warning'));

        // Show notifications based on changes and severity
        if (criticalGateFailures.length > 0) {
            await this.showCriticalGateFailureNotification(criticalGateFailures, metrics);
        } else if (hasStatusChanged && metrics.overallStatus === 'passed') {
            await this.showQualityGatePassedNotification(metrics);
        } else if (newWarnings.length > 0) {
            await this.showWarningNotification(newWarnings, metrics);
        }

        // Show threshold crossed notifications
        await this.checkThresholdCrossings(metrics);

        // Update state
        this.updateLastState(metrics, gateResults);
    }

    private hasOverallStatusChanged(metrics: QualityMetrics): boolean {
        return this.lastQualityState?.overallStatus !== metrics.overallStatus;
    }

    private hasGateStatusChanged(gateName: string, newStatus: string): boolean {
        const lastStatus = this.notificationHistory.get(gateName);
        return !lastStatus || lastStatus.status !== newStatus;
    }

    private async showCriticalGateFailureNotification(
        failures: QualityGateResult[],
        metrics: QualityMetrics
    ): Promise<void> {
        const failureCount = failures.length;
        const criticalCount = metrics.criticalViolations;
        
        const message = `🚨 ${failureCount} Quality Gate${failureCount > 1 ? 's' : ''} Failed!`;
        const detail = criticalCount > 0 
            ? `${criticalCount} critical violation${criticalCount > 1 ? 's' : ''} blocking progress`
            : `Quality standards not met`;

        const action = await vscode.window.showErrorMessage(
            `${message} ${detail}`,
            {
                modal: false,
                detail: this.buildFailureDetails(failures)
            },
            'View Dashboard',
            'Fix Issues',
            'Ignore for Now'
        );

        await this.handleNotificationAction(action, failures);
    }

    private async showQualityGatePassedNotification(metrics: QualityMetrics): Promise<void> {
        // Only show if we had failures before or this is a significant achievement
        const wasFailedBefore = this.lastQualityState?.overallStatus === 'failed';
        const highQuality = metrics.qualityScore >= 90;

        if (wasFailedBefore || highQuality) {
            const message = highQuality 
                ? '🎉 Excellent Code Quality Achieved!'
                : '✅ All Quality Gates Passed!';
            
            const detail = `Quality Score: ${metrics.qualityScore.toFixed(1)}/100, ` +
                          `Connascence Index: ${metrics.connascenceIndex.toFixed(1)}`;

            const action = await vscode.window.showInformationMessage(
                `${message} ${detail}`,
                'View Dashboard',
                'Continue Coding'
            );

            if (action === 'View Dashboard') {
                vscode.commands.executeCommand('connascence.showDashboard');
            }
        }
    }

    private async showWarningNotification(
        warnings: QualityGateResult[],
        metrics: QualityMetrics
    ): Promise<void> {
        const warningCount = warnings.length;
        const message = `⚠️ ${warningCount} Quality Warning${warningCount > 1 ? 's' : ''}`;
        const detail = `Consider reviewing: ${warnings[0].gateName}${warningCount > 1 ? ' and others' : ''}`;

        const action = await vscode.window.showWarningMessage(
            `${message} - ${detail}`,
            'View Details',
            'Dismiss'
        );

        if (action === 'View Details') {
            vscode.commands.executeCommand('connascence.showDashboard');
        }
    }

    private async checkThresholdCrossings(metrics: QualityMetrics): Promise<void> {
        if (!this.lastQualityState) return;

        const thresholds = [
            {
                name: 'Connascence Index',
                current: metrics.connascenceIndex,
                previous: this.lastQualityState.connascenceIndex,
                threshold: 50,
                isHigherBad: true
            },
            {
                name: 'Quality Score',
                current: metrics.qualityScore,
                previous: this.lastQualityState.qualityScore,
                threshold: 75,
                isHigherBad: false
            }
        ];

        for (const threshold of thresholds) {
            const crossedThreshold = this.checkSingleThresholdCrossing(threshold);
            if (crossedThreshold) {
                await this.showThresholdCrossingNotification(threshold, crossedThreshold);
            }
        }
    }

    private checkSingleThresholdCrossing(threshold: {
        name: string;
        current: number;
        previous: number;
        threshold: number;
        isHigherBad: boolean;
    }): 'improved' | 'degraded' | null {
        const { current, previous, threshold: limit, isHigherBad } = threshold;
        
        if (isHigherBad) {
            // For metrics where higher is worse (like connascence index)
            if (previous <= limit && current > limit) {
                return 'degraded';
            } else if (previous > limit && current <= limit) {
                return 'improved';
            }
        } else {
            // For metrics where higher is better (like quality score)
            if (previous >= limit && current < limit) {
                return 'degraded';
            } else if (previous < limit && current >= limit) {
                return 'improved';
            }
        }
        
        return null;
    }

    private async showThresholdCrossingNotification(
        threshold: any,
        direction: 'improved' | 'degraded'
    ): Promise<void> {
        const icon = direction === 'improved' ? '📈' : '📉';
        const action = direction === 'improved' ? 'improved' : 'degraded';
        const message = `${icon} ${threshold.name} ${action}`;
        const detail = `From ${threshold.previous.toFixed(1)} to ${threshold.current.toFixed(1)} (threshold: ${threshold.threshold})`;

        if (direction === 'degraded') {
            const actionResponse = await vscode.window.showWarningMessage(
                `${message} - ${detail}`,
                'Review Quality',
                'Dismiss'
            );
            
            if (actionResponse === 'Review Quality') {
                vscode.commands.executeCommand('connascence.showDashboard');
            }
        } else {
            vscode.window.showInformationMessage(`${message} - ${detail}`);
        }
    }

    private buildFailureDetails(failures: QualityGateResult[]): string {
        const details = failures.map(f => {
            let detail = `• ${f.gateName}: ${f.message}`;
            if (f.actualValue !== undefined && f.threshold !== undefined) {
                detail += ` (${f.actualValue} vs threshold ${f.threshold})`;
            }
            return detail;
        }).join('\n');

        return `Failed Quality Gates:\n${details}\n\nThese issues must be resolved before your code meets quality standards.`;
    }

    private async handleNotificationAction(
        action: string | undefined,
        failures: QualityGateResult[]
    ): Promise<void> {
        switch (action) {
            case 'View Dashboard':
                await vscode.commands.executeCommand('connascence.showDashboard');
                break;
                
            case 'Fix Issues':
                // Switch to the Quality tab and focus on failed gates
                await vscode.commands.executeCommand('connascence.showDashboard');
                // Could send a message to focus on specific issues
                break;
                
            case 'Ignore for Now':
                // Log the ignore action
                const ignoredGates = failures.map(f => f.gateName).join(', ');
                console.log(`User chose to ignore failed quality gates: ${ignoredGates}`);
                break;
        }
    }

    private updateLastState(metrics: QualityMetrics, gateResults: QualityGateResult[]): void {
        this.lastQualityState = { ...metrics };
        
        // Update notification history
        const timestamp = Date.now();
        gateResults.forEach(gate => {
            this.notificationHistory.set(gate.gateName, {
                status: gate.status,
                timestamp
            });
        });

        // Clean up old entries (older than 1 hour)
        const oneHourAgo = timestamp - (60 * 60 * 1000);
        for (const [gateName, entry] of this.notificationHistory) {
            if (entry.timestamp < oneHourAgo) {
                this.notificationHistory.delete(gateName);
            }
        }
    }

    public async showPreCommitWarning(
        metrics: QualityMetrics,
        failedGates: QualityGateResult[]
    ): Promise<boolean> {
        if (failedGates.length === 0) return true; // Allow commit

        const criticalCount = failedGates.filter(g => g.status === 'failed').length;
        
        if (criticalCount > 0) {
            const message = `🚫 Cannot commit: ${criticalCount} critical quality gate${criticalCount > 1 ? 's' : ''} failed`;
            const detail = `Fix these issues before committing:\n${failedGates.map(g => `• ${g.gateName}`).join('\n')}`;

            const action = await vscode.window.showErrorMessage(
                message,
                {
                    modal: true,
                    detail
                },
                'Fix Issues',
                'Force Commit (Not Recommended)'
            );

            if (action === 'Fix Issues') {
                await vscode.commands.executeCommand('connascence.showDashboard');
                return false; // Block commit
            } else if (action === 'Force Commit (Not Recommended)') {
                // Log the force commit
                console.warn('User forced commit despite quality gate failures');
                return true; // Allow commit
            }
            
            return false; // Block commit by default
        }

        // For warnings, just show notification but allow commit
        const warningCount = failedGates.length;
        if (warningCount > 0) {
            vscode.window.showWarningMessage(
                `⚠️ Committing with ${warningCount} quality warning${warningCount > 1 ? 's' : ''}`
            );
        }

        return true; // Allow commit
    }

    public dispose(): void {
        this.notificationHistory.clear();
        this.lastQualityState = null;
    }
}