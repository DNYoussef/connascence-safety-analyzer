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
        return this.getConfig('debounceMs', 1000);
    }

    // New advanced configuration methods
    getConfidenceThreshold(): number {
        return this.getConfig('confidenceThreshold', 0.8);
    }

    getNasaComplianceThreshold(): number {
        return this.getConfig('nasaComplianceThreshold', 0.95);
    }

    getMeceQualityThreshold(): number {
        return this.getConfig('meceQualityThreshold', 0.85);
    }

    getPerformanceAnalysisConfig(): any {
        return this.getConfig('performanceAnalysis', {
            enableProfiling: true,
            maxAnalysisTime: 30000,
            memoryThreshold: 512,
            enableCaching: true,
            cacheSize: 1000
        });
    }

    getAdvancedFilteringConfig(): any {
        return this.getConfig('advancedFiltering', {
            enableGitIgnore: true,
            enableCustomIgnore: true,
            minFileSize: 10,
            maxFileSize: 10485760,
            excludeBinaryFiles: true
        });
    }

    getAnalysisDepth(): string {
        return this.getConfig('analysisDepth', 'standard');
    }

    isExperimentalFeaturesEnabled(): boolean {
        return this.getConfig('enableExperimentalFeatures', false);
    }

    getCustomRules(): any[] {
        return this.getConfig('customRules', []);
    }

    shouldScanOnStartup(): boolean {
        return this.getConfig('scanOnStartup', false);
    }

    shouldScanOnSave(): boolean {
        return this.getConfig('scanOnSave', true);
    }

    getExcludePatterns(): string[] {
        return this.getConfig('excludePatterns', [
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
        return this.getConfig('includePatterns', [
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

    // New update methods for advanced settings
    async updateConfidenceThreshold(threshold: number): Promise<void> {
        if (this.isValidConfidenceThreshold(threshold)) {
            await this.updateConfig('confidenceThreshold', threshold);
        }
    }

    async updateNasaComplianceThreshold(threshold: number): Promise<void> {
        if (this.isValidConfidenceThreshold(threshold)) {
            await this.updateConfig('nasaComplianceThreshold', threshold);
        }
    }

    async updateMeceQualityThreshold(threshold: number): Promise<void> {
        if (this.isValidConfidenceThreshold(threshold)) {
            await this.updateConfig('meceQualityThreshold', threshold);
        }
    }

    async updateAnalysisDepth(depth: string): Promise<void> {
        if (this.isValidAnalysisDepth(depth)) {
            await this.updateConfig('analysisDepth', depth);
        }
    }

    async updateExperimentalFeatures(enabled: boolean): Promise<void> {
        await this.updateConfig('enableExperimentalFeatures', enabled);
    }

    async updateExcludePatterns(patterns: string[]): Promise<void> {
        await this.updateConfig('excludePatterns', patterns);
    }

    async updateIncludePatterns(patterns: string[]): Promise<void> {
        await this.updateConfig('includePatterns', patterns);
    }

    async updatePerformanceAnalysis(config: any): Promise<void> {
        await this.updateConfig('performanceAnalysis', config);
    }

    async updateAdvancedFiltering(config: any): Promise<void> {
        await this.updateConfig('advancedFiltering', config);
    }

    // Advanced analyzer capabilities configuration
    getEnableParallelAnalysis(): boolean {
        return this.getConfig('enableParallelAnalysis', true);
    }

    getEnableMECEAnalysis(): boolean {
        return this.getConfig('enableMECEAnalysis', true);
    }

    getEnableNASACompliance(): boolean {
        return this.getConfig('enableNASACompliance', true);
    }

    getEnableSmartIntegration(): boolean {
        return this.getConfig('enableSmartIntegration', true);
    }

    getMaxWorkers(): number {
        return this.getConfig('maxWorkers', 4);
    }

    getMECESimilarityThreshold(): number {
        return this.getConfig('meceSimilarityThreshold', 0.7);
    }

    getMECEClusterMinSize(): number {
        return this.getConfig('meceClusterMinSize', 2);
    }

    getParallelAnalysisConfig(): any {
        return this.getConfig('parallelAnalysis', {
            maxWorkers: this.getMaxWorkers(),
            chunkSize: 5,
            useProcesses: true,
            timeoutSeconds: 300,
            memoryLimitMb: 1024,
            enableProfiling: false
        });
    }

    async updateEnableParallelAnalysis(enabled: boolean): Promise<void> {
        await this.updateConfig('enableParallelAnalysis', enabled);
    }

    async updateEnableMECEAnalysis(enabled: boolean): Promise<void> {
        await this.updateConfig('enableMECEAnalysis', enabled);
    }

    async updateEnableNASACompliance(enabled: boolean): Promise<void> {
        await this.updateConfig('enableNASACompliance', enabled);
    }

    async updateEnableSmartIntegration(enabled: boolean): Promise<void> {
        await this.updateConfig('enableSmartIntegration', enabled);
    }

    async updateMaxWorkers(workers: number): Promise<void> {
        if (workers >= 1 && workers <= 16) {
            await this.updateConfig('maxWorkers', workers);
        }
    }

    async updateMECESimilarityThreshold(threshold: number): Promise<void> {
        if (this.isValidConfidenceThreshold(threshold)) {
            await this.updateConfig('meceSimilarityThreshold', threshold);
        }
    }

    async updateCustomRules(rules: any[]): Promise<void> {
        const validRules = rules.filter(rule => this.validateCustomRule(rule));
        await this.updateConfig('customRules', validRules);
    }

    // Enhanced validation methods
    isValidSafetyProfile(profile: string): boolean {
        const validProfiles = ['none', 'general_safety_strict', 'safety_level_1', 'safety_level_3', 'modern_general'];
        return validProfiles.includes(profile);
    }

    isValidConfidenceThreshold(threshold: number): boolean {
        return typeof threshold === 'number' && threshold >= 0.0 && threshold <= 1.0;
    }

    isValidAnalysisDepth(depth: string): boolean {
        const validDepths = ['surface', 'standard', 'deep', 'comprehensive'];
        return validDepths.includes(depth);
    }

    validateCustomRule(rule: any): boolean {
        if (!rule || typeof rule !== 'object') return false;
        return rule.name && rule.pattern && rule.severity && rule.message &&
               typeof rule.name === 'string' &&
               typeof rule.pattern === 'string' &&
               ['error', 'warning', 'info', 'hint'].includes(rule.severity) &&
               typeof rule.message === 'string';
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
        const baseConfig = this.getBaseProfileConfig(profile);
        const confidenceThreshold = this.getConfidenceThreshold();
        const nasaThreshold = this.getNasaComplianceThreshold();
        const meceThreshold = this.getMeceQualityThreshold();
        
        return {
            ...baseConfig,
            confidenceThreshold,
            nasaComplianceThreshold: nasaThreshold,
            meceQualityThreshold: meceThreshold,
            analysisDepth: this.getAnalysisDepth(),
            experimentalFeatures: this.isExperimentalFeaturesEnabled()
        };
    }

    private getBaseProfileConfig(profile: string): any {
        switch (profile) {
            case 'general_safety_strict':
                return {
                    strictMode: true,
                    maxComplexity: 10,
                    maxNestedLoops: 2,
                    maxFunctionParams: 4,
                    maxLineLength: 80,
                    requireDocstrings: true,
                    enforceTypeHints: true,
                    enableNasaCompliance: true
                };
            case 'safety_level_1':
                return {
                    strictMode: true,
                    maxComplexity: 5,
                    maxNestedLoops: 1,
                    maxFunctionParams: 3,
                    maxLineLength: 80,
                    requireDocstrings: true,
                    enforceTypeHints: true,
                    noRecursion: true,
                    noDynamicAllocation: true,
                    enableNasaCompliance: true
                };
            case 'safety_level_3':
                return {
                    strictMode: true,
                    maxComplexity: 15,
                    maxNestedLoops: 3,
                    maxFunctionParams: 6,
                    maxLineLength: 120,
                    requireDocstrings: true,
                    enforceTypeHints: true,
                    enableNasaCompliance: true
                };
            case 'modern_general':
                return {
                    strictMode: false,
                    maxComplexity: 20,
                    maxNestedLoops: 4,
                    maxFunctionParams: 8,
                    maxLineLength: 120,
                    requireDocstrings: false,
                    enforceTypeHints: false,
                    enableNasaCompliance: false
                };
            default:
                return {
                    strictMode: false,
                    maxComplexity: 25,
                    maxNestedLoops: 5,
                    maxFunctionParams: 10,
                    maxLineLength: 150,
                    requireDocstrings: false,
                    enforceTypeHints: false,
                    enableNasaCompliance: false
                };
        }
    }

    // Get framework-specific configuration with enhanced options
    getFrameworkProfileConfig(): any {
        const framework = this.getFrameworkProfile();
        const confidenceThreshold = this.getConfidenceThreshold();
        const analysisDepth = this.getAnalysisDepth();
        
        const baseConfig = this.getFrameworkSpecificConfig(framework);
        
        return {
            ...baseConfig,
            confidenceThreshold,
            analysisDepth,
            customRules: this.getCustomRules(),
            performanceSettings: this.getPerformanceAnalysisConfig(),
            filteringSettings: this.getAdvancedFilteringConfig()
        };
    }

    private getFrameworkSpecificConfig(framework: string): any {
        switch (framework) {
            case 'django':
                return {
                    modelValidation: true,
                    viewComplexity: true,
                    templateAnalysis: false,
                    migrationChecks: true,
                    settingsValidation: true,
                    ormPatterns: true,
                    securityPatterns: true,
                    middlewareAnalysis: true
                };
            case 'fastapi':
                return {
                    dependencyInjection: true,
                    schemaValidation: true,
                    routeComplexity: true,
                    asyncPatterns: true,
                    pydanticModels: true,
                    swaggerCompliance: true,
                    authPatterns: true
                };
            case 'react':
                return {
                    componentComplexity: true,
                    hookUsage: true,
                    stateManagement: true,
                    propValidation: true,
                    jsxPatterns: true,
                    performancePatterns: true,
                    accessibilityChecks: true
                };
            default:
                return {
                    genericAnalysis: true,
                    codeSmells: true,
                    designPatterns: true,
                    maintainabilityMetrics: true
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

    // Generic get method for compatibility
    get<T>(key: string, defaultValue?: T): T | undefined {
        return this.getConfig(key, defaultValue);
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

    // Export/Import configuration with all advanced settings
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
            debounceMs: this.getDebounceDelay(),
            scanOnStartup: this.shouldScanOnStartup(),
            scanOnSave: this.shouldScanOnSave(),
            excludePatterns: this.getExcludePatterns(),
            includePatterns: this.getIncludePatterns(),
            // Advanced settings
            confidenceThreshold: this.getConfidenceThreshold(),
            nasaComplianceThreshold: this.getNasaComplianceThreshold(),
            meceQualityThreshold: this.getMeceQualityThreshold(),
            performanceAnalysis: this.getPerformanceAnalysisConfig(),
            advancedFiltering: this.getAdvancedFilteringConfig(),
            analysisDepth: this.getAnalysisDepth(),
            enableExperimentalFeatures: this.isExperimentalFeaturesEnabled(),
            customRules: this.getCustomRules(),
            // Advanced analyzer capabilities
            enableParallelAnalysis: this.getEnableParallelAnalysis(),
            enableMECEAnalysis: this.getEnableMECEAnalysis(),
            enableNASACompliance: this.getEnableNASACompliance(),
            enableSmartIntegration: this.getEnableSmartIntegration(),
            maxWorkers: this.getMaxWorkers(),
            meceSimilarityThreshold: this.getMECESimilarityThreshold(),
            meceClusterMinSize: this.getMECEClusterMinSize(),
            parallelAnalysis: this.getParallelAnalysisConfig()
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
            'debounceMs', 'scanOnStartup', 'scanOnSave', 'excludePatterns', 'includePatterns',
            // Advanced settings keys
            'confidenceThreshold', 'nasaComplianceThreshold', 'meceQualityThreshold',
            'performanceAnalysis', 'advancedFiltering', 'analysisDepth',
            'enableExperimentalFeatures', 'customRules',
            // Advanced analyzer capabilities keys
            'enableParallelAnalysis', 'enableMECEAnalysis', 'enableNASACompliance',
            'enableSmartIntegration', 'maxWorkers', 'meceSimilarityThreshold',
            'meceClusterMinSize', 'parallelAnalysis'
        ];

        for (const key of keys) {
            await config.update(key, undefined, vscode.ConfigurationTarget.Workspace);
        }
    }
}