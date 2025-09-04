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
exports.ConfigurationService = void 0;
const vscode = __importStar(require("vscode"));
class ConfigurationService {
    constructor() {
        this.configSection = 'connascence';
    }
    getSafetyProfile() {
        return this.getConfig('safetyProfile', 'modern_general');
    }
    isGrammarValidationEnabled() {
        return this.getConfig('grammarValidation', true);
    }
    isRealTimeAnalysisEnabled() {
        return this.getConfig('realTimeAnalysis', true);
    }
    isAutoFixSuggestionsEnabled() {
        return this.getConfig('autoFixSuggestions', true);
    }
    getServerUrl() {
        return this.getConfig('serverUrl', 'http://localhost:8080');
    }
    useMCPServer() {
        return this.getConfig('authenticateWithServer', false);
    }
    getFrameworkProfile() {
        return this.getConfig('frameworkProfile', 'generic');
    }
    showInlineHints() {
        return this.getConfig('showInlineHints', true);
    }
    getDiagnosticSeverity() {
        return this.getConfig('diagnosticSeverity', 'warning');
    }
    getMaxDiagnostics() {
        return this.getConfig('maxDiagnostics', 1000);
    }
    getDebounceDelay() {
        return this.getConfig('debounceDelay', 500);
    }
    shouldScanOnStartup() {
        return this.getConfig('scanOnStartup', false);
    }
    shouldScanOnSave() {
        return this.getConfig('scanOnSave', true);
    }
    getExcludePatterns() {
        return this.getConfig('exclude', [
            '**/node_modules/**',
            '**/venv/**',
            '**/env/**',
            '**/__pycache__/**',
            '**/dist/**',
            '**/build/**',
            '**/.git/**'
        ]);
    }
    getIncludePatterns() {
        return this.getConfig('include', [
            '**/*.py',
            '**/*.c',
            '**/*.cpp',
            '**/*.js',
            '**/*.ts'
        ]);
    }
    async updateSafetyProfile(profile) {
        await this.updateConfig('safetyProfile', profile);
    }
    async updateRealTimeAnalysis(enabled) {
        await this.updateConfig('realTimeAnalysis', enabled);
    }
    async updateGrammarValidation(enabled) {
        await this.updateConfig('grammarValidation', enabled);
    }
    async updateServerUrl(url) {
        await this.updateConfig('serverUrl', url);
    }
    async updateFrameworkProfile(profile) {
        await this.updateConfig('frameworkProfile', profile);
    }
    // Validation methods
    isValidSafetyProfile(profile) {
        const validProfiles = ['none', 'nasa_jpl_pot10', 'nasa_loc_1', 'nasa_loc_3', 'modern_general'];
        return validProfiles.includes(profile);
    }
    isValidFrameworkProfile(profile) {
        const validProfiles = ['generic', 'django', 'fastapi', 'react'];
        return validProfiles.includes(profile);
    }
    isValidDiagnosticSeverity(severity) {
        const validSeverities = ['error', 'warning', 'info', 'hint'];
        return validSeverities.includes(severity);
    }
    // Get profile-specific configuration
    getSafetyProfileConfig() {
        const profile = this.getSafetyProfile();
        switch (profile) {
            case 'nasa_jpl_pot10':
                return {
                    strictMode: true,
                    maxComplexity: 10,
                    maxNestedLoops: 2,
                    maxFunctionParams: 4,
                    maxLineLength: 80,
                    requireDocstrings: true,
                    enforceTypeHints: true
                };
            case 'nasa_loc_1':
                return {
                    strictMode: true,
                    maxComplexity: 5,
                    maxNestedLoops: 1,
                    maxFunctionParams: 3,
                    maxLineLength: 80,
                    requireDocstrings: true,
                    enforceTypeHints: true,
                    noRecursion: true,
                    noDynamicAllocation: true
                };
            case 'nasa_loc_3':
                return {
                    strictMode: true,
                    maxComplexity: 15,
                    maxNestedLoops: 3,
                    maxFunctionParams: 6,
                    maxLineLength: 120,
                    requireDocstrings: true,
                    enforceTypeHints: true
                };
            case 'modern_general':
                return {
                    strictMode: false,
                    maxComplexity: 20,
                    maxNestedLoops: 4,
                    maxFunctionParams: 8,
                    maxLineLength: 120,
                    requireDocstrings: false,
                    enforceTypeHints: false
                };
            default:
                return {
                    strictMode: false,
                    maxComplexity: 25,
                    maxNestedLoops: 5,
                    maxFunctionParams: 10,
                    maxLineLength: 150,
                    requireDocstrings: false,
                    enforceTypeHints: false
                };
        }
    }
    // Get framework-specific configuration
    getFrameworkProfileConfig() {
        const framework = this.getFrameworkProfile();
        switch (framework) {
            case 'django':
                return {
                    modelValidation: true,
                    viewComplexity: true,
                    templateAnalysis: false,
                    migrationChecks: true,
                    settingsValidation: true
                };
            case 'fastapi':
                return {
                    dependencyInjection: true,
                    schemaValidation: true,
                    routeComplexity: true,
                    asyncPatterns: true
                };
            case 'react':
                return {
                    componentComplexity: true,
                    hookUsage: true,
                    stateManagement: true,
                    propValidation: true
                };
            default:
                return {
                    genericAnalysis: true
                };
        }
    }
    // Event handlers for configuration changes
    onConfigurationChanged(callback) {
        return vscode.workspace.onDidChangeConfiguration(event => {
            if (event.affectsConfiguration(this.configSection)) {
                callback(event);
            }
        });
    }
    // Generic get method for compatibility
    get(key, defaultValue) {
        return this.getConfig(key, defaultValue);
    }
    // Helper methods
    getConfig(key, defaultValue) {
        const config = vscode.workspace.getConfiguration(this.configSection);
        return config.get(key, defaultValue);
    }
    async updateConfig(key, value, target = vscode.ConfigurationTarget.Workspace) {
        const config = vscode.workspace.getConfiguration(this.configSection);
        await config.update(key, value, target);
    }
    // Export/Import configuration
    exportConfiguration() {
        const config = vscode.workspace.getConfiguration(this.configSection);
        return {
            safetyProfile: this.getSafetyProfile(),
            grammarValidation: this.isGrammarValidationEnabled(),
            realTimeAnalysis: this.isRealTimeAnalysisEnabled(),
            autoFixSuggestions: this.isAutoFixSuggestionsEnabled(),
            serverUrl: this.getServerUrl(),
            frameworkProfile: this.getFrameworkProfile(),
            showInlineHints: this.showInlineHints(),
            diagnosticSeverity: this.getDiagnosticSeverity(),
            maxDiagnostics: this.getMaxDiagnostics(),
            debounceDelay: this.getDebounceDelay(),
            scanOnStartup: this.shouldScanOnStartup(),
            scanOnSave: this.shouldScanOnSave(),
            exclude: this.getExcludePatterns(),
            include: this.getIncludePatterns()
        };
    }
    async importConfiguration(configData) {
        const config = vscode.workspace.getConfiguration(this.configSection);
        for (const [key, value] of Object.entries(configData)) {
            await config.update(key, value, vscode.ConfigurationTarget.Workspace);
        }
    }
    // Reset to defaults
    async resetToDefaults() {
        const config = vscode.workspace.getConfiguration(this.configSection);
        const keys = [
            'safetyProfile', 'grammarValidation', 'realTimeAnalysis',
            'autoFixSuggestions', 'serverUrl', 'frameworkProfile',
            'showInlineHints', 'diagnosticSeverity', 'maxDiagnostics',
            'debounceDelay', 'scanOnStartup', 'scanOnSave', 'exclude', 'include'
        ];
        for (const key of keys) {
            await config.update(key, undefined, vscode.ConfigurationTarget.Workspace);
        }
    }
}
exports.ConfigurationService = ConfigurationService;
//# sourceMappingURL=configurationService.js.map