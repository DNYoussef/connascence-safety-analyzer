"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.StatusBarManager = void 0;
const vscode = __importStar(require("vscode"));
class StatusBarManager {
    constructor(connascenceService, configService) {
        this.connascenceService = connascenceService;
        this.configService = configService;
        this.isAnalyzing = false;
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 200);
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
    setAnalyzing(analyzing) {
        this.isAnalyzing = analyzing;
        this.updateDisplay();
    }
    updateSafetyProfile(profile) {
        this.currentProfile = profile;
        this.updateDisplay();
    }
    show() {
        this.statusBarItem.show();
    }
    hide() {
        this.statusBarItem.hide();
    }
    dispose() {
        this.statusBarItem.dispose();
    }
    // Additional methods required by CommandManager
    initialize() {
        this.updateDisplay();
    }
    showProgress(message) {
        this.statusBarItem.text = `$(loading~spin) ${message || 'Processing...'}`;
        this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
    }
    showSuccess(message) {
        this.statusBarItem.text = `$(check) ${message || 'Success'}`;
        this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.prominentBackground');
        // Restore original state after 3 seconds
        setTimeout(() => {
            this.updateDisplay();
        }, 3000);
    }
    showError(message) {
        this.statusBarItem.text = `$(error) ${message || 'Error'}`;
        this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
        // Restore original state after 5 seconds
        setTimeout(() => {
            this.updateDisplay();
        }, 5000);
    }
    clear() {
        this.statusBarItem.text = '';
        this.statusBarItem.backgroundColor = undefined;
    }
    refresh() {
        this.updateDisplay();
    }
    updateDisplay() {
        if (this.isAnalyzing) {
            this.statusBarItem.text = '$(loading~spin) Connascence: Analyzing...';
            this.statusBarItem.tooltip = 'Connascence analysis in progress';
            this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
            this.statusBarItem.command = undefined;
        }
        else {
            const profileIcon = this.getProfileIcon(this.currentProfile);
            this.statusBarItem.text = `${profileIcon} Connascence: ${this.formatProfile(this.currentProfile)}`;
            this.statusBarItem.tooltip = this.createTooltip();
            this.statusBarItem.backgroundColor = undefined;
            this.statusBarItem.command = 'connascence.toggleSafetyProfile';
        }
    }
    getProfileIcon(profile) {
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
    formatProfile(profile) {
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
    createTooltip() {
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
exports.StatusBarManager = StatusBarManager;
//# sourceMappingURL=statusBarManager.js.map