import * as vscode from 'vscode';
import * as path from 'path';
import { ConnascenceViolation } from '../diagnostics';
import { QualityGateNotificationManager } from '../features/qualityGateNotifications';

interface QualityGateResult {
    gateName: string;
    status: 'passed' | 'warning' | 'failed';
    message: string;
    threshold?: number;
    actualValue?: number;
    details?: any;
}

interface QualityMetrics {
    criticalViolations: number;
    highViolations: number;
    mediumViolations: number;
    lowViolations: number;
    totalViolations: number;
    connascenceIndex: number;
    qualityScore: number;
    overallStatus: 'passed' | 'warning' | 'failed';
}

export class QualityGateIntegrationService {
    private static instance: QualityGateIntegrationService;
    private notificationManager: QualityGateNotificationManager;
    private lastEvaluationResults: QualityGateResult[] = [];
    private lastMetrics: QualityMetrics | null = null;

    private constructor() {
        this.notificationManager = QualityGateNotificationManager.getInstance();
    }

    public static getInstance(): QualityGateIntegrationService {
        if (!QualityGateIntegrationService.instance) {
            QualityGateIntegrationService.instance = new QualityGateIntegrationService();
        }
        return QualityGateIntegrationService.instance;
    }

    public async evaluateQualityGates(violations: ConnascenceViolation[]): Promise<{
        gates: QualityGateResult[];
        metrics: QualityMetrics;
        overallStatus: 'passed' | 'warning' | 'failed';
    }> {
        const metrics = this.calculateMetrics(violations);
        const gates = this.evaluateGates(metrics, violations);
        const overallStatus = this.determineOverallStatus(gates);

        const result = {
            gates,
            metrics: { ...metrics, overallStatus },
            overallStatus
        };

        // Update extension status indicators
        await this.updateStatusIndicators(result);

        // Process notifications
        await this.notificationManager.processQualityGateResults(gates, result.metrics);

        // Store results for comparison
        this.lastEvaluationResults = gates;
        this.lastMetrics = result.metrics;

        return result;
    }

    private calculateMetrics(violations: ConnascenceViolation[]): QualityMetrics {
        const criticalViolations = violations.filter(v => v.severity === 'critical').length;
        const highViolations = violations.filter(v => v.severity === 'high').length;
        const mediumViolations = violations.filter(v => v.severity === 'medium').length;
        const lowViolations = violations.filter(v => v.severity === 'low').length;
        const totalViolations = violations.length;

        // Calculate connascence index (weighted sum)
        const weights = { critical: 10, high: 5, medium: 2, low: 1 };
        const connascenceIndex = violations.reduce((sum, v) => {
            return sum + (weights[v.severity as keyof typeof weights] || 1);
        }, 0);

        // Calculate overall quality score (0-100)
        const penalty = Math.min(connascenceIndex * 2, 100);
        const qualityScore = Math.max(0, 100 - penalty);

        return {
            criticalViolations,
            highViolations,
            mediumViolations,
            lowViolations,
            totalViolations,
            connascenceIndex,
            qualityScore,
            overallStatus: 'passed' // Will be determined by gate evaluation
        };
    }

    private evaluateGates(metrics: QualityMetrics, violations: ConnascenceViolation[]): QualityGateResult[] {
        const gates: QualityGateResult[] = [];

        // Critical Issues Gate
        gates.push({
            gateName: 'Critical Issues Gate',
            status: metrics.criticalViolations === 0 ? 'passed' : 'failed',
            message: metrics.criticalViolations === 0 
                ? 'No critical violations found' 
                : `${metrics.criticalViolations} critical violation${metrics.criticalViolations > 1 ? 's' : ''} must be fixed`,
            threshold: 0,
            actualValue: metrics.criticalViolations,
            details: violations.filter(v => v.severity === 'critical')
        });

        // Connascence Index Gate
        const indexThreshold = 50;
        const indexStatus = metrics.connascenceIndex < indexThreshold ? 'passed' :
                          metrics.connascenceIndex < indexThreshold * 1.5 ? 'warning' : 'failed';
        
        gates.push({
            gateName: 'Connascence Index Gate',
            status: indexStatus,
            message: indexStatus === 'passed' 
                ? `Connascence index within acceptable range (${metrics.connascenceIndex.toFixed(1)})`
                : `Connascence index ${indexStatus === 'warning' ? 'elevated' : 'too high'} (${metrics.connascenceIndex.toFixed(1)})`,
            threshold: indexThreshold,
            actualValue: metrics.connascenceIndex
        });

        // High Severity Percentage Gate
        const highSeverityPercentage = (metrics.highViolations + metrics.criticalViolations) / Math.max(1, metrics.totalViolations);
        const severityThreshold = 0.2; // 20%
        const severityStatus = highSeverityPercentage < severityThreshold ? 'passed' :
                             highSeverityPercentage < severityThreshold * 1.25 ? 'warning' : 'failed';

        gates.push({
            gateName: 'High Severity Percentage Gate',
            status: severityStatus,
            message: severityStatus === 'passed'
                ? `High severity violations under control (${(highSeverityPercentage * 100).toFixed(1)}%)`
                : `Too many high severity violations (${(highSeverityPercentage * 100).toFixed(1)}%)`,
            threshold: severityThreshold * 100,
            actualValue: highSeverityPercentage * 100
        });

        // Total Violations Gate (warning only)
        const totalThreshold = 25;
        const totalStatus = metrics.totalViolations < 10 ? 'passed' :
                           metrics.totalViolations < totalThreshold ? 'warning' : 'failed';

        gates.push({
            gateName: 'Total Violations Gate',
            status: totalStatus,
            message: totalStatus === 'passed'
                ? `Total violations at manageable level (${metrics.totalViolations})`
                : `Total violations ${totalStatus === 'warning' ? 'elevated' : 'excessive'} (${metrics.totalViolations})`,
            threshold: totalThreshold,
            actualValue: metrics.totalViolations
        });

        // NASA Compliance Gate (if applicable)
        const nasaViolations = violations.filter(v =>
            v.description.toLowerCase().includes('nasa') ||
            v.connascenceType.toLowerCase().includes('pot10')
        );
        
        if (nasaViolations.length > 0 || violations.some(v => v.severity === 'critical')) {
            gates.push({
                gateName: 'NASA Compliance Gate',
                status: nasaViolations.length === 0 && metrics.criticalViolations === 0 ? 'passed' : 'failed',
                message: nasaViolations.length === 0 && metrics.criticalViolations === 0
                    ? 'NASA Power of Ten compliance maintained'
                    : `NASA compliance issues detected (${nasaViolations.length} violations)`,
                threshold: 0,
                actualValue: nasaViolations.length,
                details: nasaViolations
            });
        }

        return gates;
    }

    private determineOverallStatus(gates: QualityGateResult[]): 'passed' | 'warning' | 'failed' {
        const failed = gates.some(g => g.status === 'failed');
        const warning = gates.some(g => g.status === 'warning');
        
        if (failed) return 'failed';
        if (warning) return 'warning';
        return 'passed';
    }

    private async updateStatusIndicators(result: {
        gates: QualityGateResult[];
        metrics: QualityMetrics;
        overallStatus: 'passed' | 'warning' | 'failed';
    }): Promise<void> {
        try {
            // Update status bar via command (if available)
            const statusBarUpdateData = {
                qualityGateStatus: result.overallStatus,
                criticalViolations: result.metrics.criticalViolations,
                connascenceIndex: result.metrics.connascenceIndex,
                totalViolations: result.metrics.totalViolations,
                qualityScore: result.metrics.qualityScore
            };

            // Try to update status bar manager if available
            const statusBarCommand = 'connascence.internal.updateQualityGates';
            try {
                await vscode.commands.executeCommand(statusBarCommand, statusBarUpdateData);
            } catch (error) {
                // Status bar command not available, continue silently
            }

            // Update broken chain logo via command if available
            const brokenChainUpdateData = {
                totalIssues: result.metrics.totalViolations,
                criticalIssues: result.metrics.criticalViolations,
                qualityScore: result.metrics.qualityScore,
                qualityGateStatus: result.overallStatus,
                connascenceIndex: result.metrics.connascenceIndex
            };

            const brokenChainCommand = 'connascence.internal.updateBrokenChainStatus';
            try {
                await vscode.commands.executeCommand(brokenChainCommand, brokenChainUpdateData);
            } catch (error) {
                // Broken chain command not available, continue silently
            }

        } catch (error) {
            console.error('Error updating status indicators:', error);
        }
    }

    public async checkPreCommitGates(): Promise<boolean> {
        if (!this.lastMetrics || this.lastEvaluationResults.length === 0) {
            return true; // No gates evaluated yet, allow commit
        }

        const failedGates = this.lastEvaluationResults.filter(g => g.status === 'failed' || g.status === 'warning');
        
        if (failedGates.length === 0) {
            return true; // All gates passed, allow commit
        }

        return await this.notificationManager.showPreCommitWarning(this.lastMetrics, failedGates);
    }

    public getLastEvaluationResults(): {
        gates: QualityGateResult[];
        metrics: QualityMetrics | null;
    } {
        return {
            gates: [...this.lastEvaluationResults],
            metrics: this.lastMetrics ? { ...this.lastMetrics } : null
        };
    }

    public async generateQualityReport(): Promise<string> {
        if (!this.lastMetrics || this.lastEvaluationResults.length === 0) {
            return 'No quality gate evaluation available';
        }

        const timestamp = new Date().toISOString();
        const { gates, metrics } = { gates: this.lastEvaluationResults, metrics: this.lastMetrics };

        let report = `# Quality Gates Report\n`;
        report += `Generated: ${timestamp}\n\n`;
        
        report += `## Overall Status: ${metrics.overallStatus.toUpperCase()}\n\n`;
        
        report += `## Metrics Summary\n`;
        report += `- Quality Score: ${metrics.qualityScore.toFixed(1)}/100\n`;
        report += `- Connascence Index: ${metrics.connascenceIndex.toFixed(1)}\n`;
        report += `- Total Violations: ${metrics.totalViolations}\n`;
        report += `- Critical Issues: ${metrics.criticalViolations}\n`;
        report += `- High Priority: ${metrics.highViolations}\n\n`;

        report += `## Quality Gate Results\n`;
        gates.forEach(gate => {
            const icon = gate.status === 'passed' ? '✅' : gate.status === 'warning' ? '⚠️' : '❌';
            report += `${icon} **${gate.gateName}**: ${gate.status.toUpperCase()}\n`;
            report += `   ${gate.message}\n`;
            if (gate.actualValue !== undefined && gate.threshold !== undefined) {
                report += `   Value: ${gate.actualValue}, Threshold: ${gate.threshold}\n`;
            }
            report += `\n`;
        });

        const failedGates = gates.filter(g => g.status === 'failed');
        if (failedGates.length > 0) {
            report += `## Action Items\n`;
            failedGates.forEach(gate => {
                report += `- Fix ${gate.gateName}: ${gate.message}\n`;
            });
        }

        return report;
    }

    public dispose(): void {
        this.notificationManager.dispose();
        this.lastEvaluationResults = [];
        this.lastMetrics = null;
    }
}