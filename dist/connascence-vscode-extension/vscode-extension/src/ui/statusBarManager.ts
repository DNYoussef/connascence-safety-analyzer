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

    private updateDisplay(): void {
        if (this.isAnalyzing) {
            this.statusBarItem.text = '$(loading~spin) Connascence: Analyzing...';
            this.statusBarItem.tooltip = 'Connascence analysis in progress';
            this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
            this.statusBarItem.command = undefined;
        } else {
            const profileIcon = this.getProfileIcon(this.currentProfile);
            this.statusBarItem.text = `${profileIcon} Connascence: ${this.formatProfile(this.currentProfile)}`;
            this.statusBarItem.tooltip = this.createTooltip();
            this.statusBarItem.backgroundColor = undefined;
            this.statusBarItem.command = 'connascence.toggleSafetyProfile';
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
                return 'NASA/JPL';
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
            `Active Profile: ${this.formatProfile(this.currentProfile)}`,
            `Real-time Analysis: ${this.configService.isRealTimeAnalysisEnabled() ? 'On' : 'Off'}`,
            `Grammar Validation: ${this.configService.isGrammarValidationEnabled() ? 'On' : 'Off'}`,
            `Framework: ${this.configService.getFrameworkProfile()}`,
            '',
            'Click to change safety profile'
        ];

        return lines.join('\n');
    }
}