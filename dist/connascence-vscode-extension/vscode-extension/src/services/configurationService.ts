import * as vscode from 'vscode';

export class ConfigurationService {
    private readonly configSection = 'connascence';

    getSafetyProfile(): string {
        return this.getConfig('safetyProfile', 'modern_general');
    }

    isGrammarValidationEnabled(): boolean {
        return this.getConfig('grammarValidation', true);
    }

    isRealTimeAnalysisEnabled(): boolean {
        return this.getConfig('realTimeAnalysis', true);
    }

    isAutoFixSuggestionsEnabled(): boolean {
        return this.getConfig('autoFixSuggestions', true);
    }

    getServerUrl(): string {
        return this.getConfig('serverUrl', 'http://localhost:8080');
    }

    useMCPServer(): boolean {
        return this.getConfig('authenticateWithServer', false);
    }

    getFrameworkProfile(): string {
        return this.getConfig('frameworkProfile', 'generic');
    }

    showInlineHints(): boolean {
        return this.getConfig('showInlineHints', true);
    }

    getDiagnosticSeverity(): string {
        return this.getConfig('diagnosticSeverity', 'warning');
    }

    getMaxDiagnostics(): number {
        return this.getConfig('maxDiagnostics', 1000);
    }

    getDebounceDelay(): number {
        return this.getConfig('debounceDelay', 500);
    }

    shouldScanOnStartup(): boolean {
        return this.getConfig('scanOnStartup', false);
    }

    shouldScanOnSave(): boolean {
        return this.getConfig('scanOnSave', true);
    }

    getExcludePatterns(): string[] {
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

    getIncludePatterns(): string[] {
        return this.getConfig('include', [
            '**/*.py',
            '**/*.c',
            '**/*.cpp',
            '**/*.js',
            '**/*.ts'
        ]);
    }

    async updateSafetyProfile(profile: string): Promise<void> {
        await this.updateConfig('safetyProfile', profile);
    }

    async updateRealTimeAnalysis(enabled: boolean): Promise<void> {
        await this.updateConfig('realTimeAnalysis', enabled);
    }

    async updateGrammarValidation(enabled: boolean): Promise<void> {
        await this.updateConfig('grammarValidation', enabled);
    }

    async updateServerUrl(url: string): Promise<void> {
        await this.updateConfig('serverUrl', url);
    }

    async updateFrameworkProfile(profile: string): Promise<void> {
        await this.updateConfig('frameworkProfile', profile);
    }

    // Validation methods
    isValidSafetyProfile(profile: string): boolean {
        const validProfiles = ['none', 'nasa_jpl_pot10', 'nasa_loc_1', 'nasa_loc_3', 'modern_general'];
        return validProfiles.includes(profile);
    }

    isValidFrameworkProfile(profile: string): boolean {
        const validProfiles = ['generic', 'django', 'fastapi', 'react'];
        return validProfiles.includes(profile);
    }

    isValidDiagnosticSeverity(severity: string): boolean {
        const validSeverities = ['error', 'warning', 'info', 'hint'];
        return validSeverities.includes(severity);
    }

    // Get profile-specific configuration
    getSafetyProfileConfig(): any {
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
    getFrameworkProfileConfig(): any {
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
    onConfigurationChanged(callback: (event: vscode.ConfigurationChangeEvent) => void): vscode.Disposable {
        return vscode.workspace.onDidChangeConfiguration(event => {
            if (event.affectsConfiguration(this.configSection)) {
                callback(event);
            }
        });
    }

    // Helper methods
    private getConfig<T>(key: string, defaultValue: T): T {
        const config = vscode.workspace.getConfiguration(this.configSection);
        return config.get<T>(key, defaultValue);
    }

    private async updateConfig(key: string, value: any, target: vscode.ConfigurationTarget = vscode.ConfigurationTarget.Workspace): Promise<void> {
        const config = vscode.workspace.getConfiguration(this.configSection);
        await config.update(key, value, target);
    }

    // Export/Import configuration
    exportConfiguration(): any {
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

    async importConfiguration(configData: any): Promise<void> {
        const config = vscode.workspace.getConfiguration(this.configSection);
        
        for (const [key, value] of Object.entries(configData)) {
            await config.update(key, value, vscode.ConfigurationTarget.Workspace);
        }
    }

    // Reset to defaults
    async resetToDefaults(): Promise<void> {
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