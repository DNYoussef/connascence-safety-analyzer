import * as vscode from 'vscode';
import { ConnascenceService } from '../services/connascenceService';
import { ConfigurationService } from '../services/configurationService';

export class StatusBarManager {
    private statusBarItem: vscode.StatusBarItem;
    private isAnalyzing = false;
    private currentProfile: string;

    constructor(
        private connascenceService: ConnascenceService,
        private configService: ConfigurationService
    ) {
        this.statusBarItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Right,
            200
        );

        this.currentProfile = this.configService.getSafetyProfile();
        this.updateDisplay();
        this.statusBarItem.show();

        // Listen for configuration changes
        this.configService.onConfigurationChanged(() => {
            const newProfile = this.configService.getSafetyProfile();
            if (newProfile !== this.currentProfile) {
                this.currentProfile = newProfile;
                this.updateDisplay();
            }
        });
    }

    setAnalyzing(analyzing: boolean): void {
        this.isAnalyzing = analyzing;
        this.updateDisplay();
    }

    updateSafetyProfile(profile: string): void {
        this.currentProfile = profile;
        this.updateDisplay();
    }

    show(): void {
        this.statusBarItem.show();
    }

    hide(): void {
        this.statusBarItem.hide();
    }

    dispose(): void {
        this.statusBarItem.dispose();
    }

    // Additional methods required by CommandManager
    initialize(): void {
        this.updateDisplay();
    }

    showProgress(message?: string): void {
        this.statusBarItem.text = `$(loading~spin) ${message || 'Processing...'}`;
        this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
    }

    showSuccess(message?: string): void {
        this.statusBarItem.text = `$(check) ${message || 'Success'}`;
        this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.prominentBackground');
        
        // Restore original state after 3 seconds
        setTimeout(() => {
            this.updateDisplay();
        }, 3000);
    }

    showError(message?: string): void {
        this.statusBarItem.text = `$(error) ${message || 'Error'}`;
        this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
        
        // Restore original state after 5 seconds
        setTimeout(() => {
            this.updateDisplay();
        }, 5000);
    }

    clear(): void {
        this.statusBarItem.text = '';
        this.statusBarItem.backgroundColor = undefined;
    }

    refresh(): void {
        this.updateDisplay();
    }

    private qualityGateStatus: 'passed' | 'warning' | 'failed' = 'passed';
    private qualityMetrics: {
        criticalViolations: number;
        connascenceIndex: number;
        totalViolations: number;
        qualityScore: number;
    } = {
        criticalViolations: 0,
        connascenceIndex: 0,
        totalViolations: 0,
        qualityScore: 100
    };

    updateQualityGateStatus(status: 'passed' | 'warning' | 'failed', metrics?: any): void {
        this.qualityGateStatus = status;
        if (metrics) {
            this.qualityMetrics = {
                criticalViolations: metrics.criticalViolations || 0,
                connascenceIndex: metrics.connascenceIndex || 0,
                totalViolations: metrics.totalViolations || 0,
                qualityScore: metrics.qualityScore || 100
            };
        }
        this.updateDisplay();
    }

    private updateDisplay(): void {
        if (this.isAnalyzing) {
            this.statusBarItem.text = '$(loading~spin) Connascence: Analyzing...';
            this.statusBarItem.tooltip = 'Connascence analysis in progress';
            this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
            this.statusBarItem.command = undefined;
        } else {
            const profileIcon = this.getProfileIcon(this.currentProfile);
            const gateStatusIcon = this.getQualityGateIcon();
            
            // Include quality gate status in display
            this.statusBarItem.text = `${profileIcon}${gateStatusIcon} Connascence: ${this.formatProfile(this.currentProfile)}`;
            this.statusBarItem.tooltip = this.createTooltip();
            this.statusBarItem.backgroundColor = this.getQualityGateColor();
            this.statusBarItem.command = 'connascence.showDashboard'; // Changed to show dashboard instead
        }
    }

    private getQualityGateIcon(): string {
        switch (this.qualityGateStatus) {
            case 'passed':
                return ' ✅';
            case 'warning':
                return ' ⚠️';
            case 'failed':
                return ' ❌';
            default:
                return '';
        }
    }

    private getQualityGateColor(): vscode.ThemeColor | undefined {
        switch (this.qualityGateStatus) {
            case 'failed':
                return new vscode.ThemeColor('statusBarItem.errorBackground');
            case 'warning':
                return new vscode.ThemeColor('statusBarItem.warningBackground');
            case 'passed':
                return new vscode.ThemeColor('statusBarItem.prominentBackground');
            default:
                return undefined;
        }
    }

    private getProfileIcon(profile: string): string {
        switch (profile) {
            case 'nasa_jpl_pot10':
            case 'nasa_loc_1':
            case 'nasa_loc_3':
                return '$(shield)';
            case 'modern_general':
                return '$(check)';
            case 'none':
                return '$(circle-outline)';
            default:
                return '$(gear)';
        }
    }

    private formatProfile(profile: string): string {
        switch (profile) {
            case 'nasa_jpl_pot10':
                return 'General Safety';
            case 'nasa_loc_1':
                return 'LOC-1';
            case 'nasa_loc_3':
                return 'LOC-3';
            case 'modern_general':
                return 'Modern';
            case 'none':
                return 'Off';
            default:
                return profile;
        }
    }

    private createTooltip(): string {
        const lines = [
            'Connascence Safety Analyzer',
            '',
            `Quality Gates: ${this.qualityGateStatus.toUpperCase()}`,
            `Critical Issues: ${this.qualityMetrics.criticalViolations}`,
            `Connascence Index: ${this.qualityMetrics.connascenceIndex.toFixed(1)}`,
            `Total Violations: ${this.qualityMetrics.totalViolations}`,
            `Quality Score: ${this.qualityMetrics.qualityScore.toFixed(1)}/100`,
            '',
            `Active Profile: ${this.formatProfile(this.currentProfile)}`,
            `Real-time Analysis: ${this.configService.isRealTimeAnalysisEnabled() ? 'On' : 'Off'}`,
            `Grammar Validation: ${this.configService.isGrammarValidationEnabled() ? 'On' : 'Off'}`,
            `Framework: ${this.configService.getFrameworkProfile()}`,
            '',
            'Click to view quality dashboard'
        ];

        return lines.join('\n');
    }
}