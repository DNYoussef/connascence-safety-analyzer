import * as vscode from 'vscode';

// Policy preset interface definitions
export interface PolicyPreset {
    id: string;
    name: string;
    description: string;
    impact: 'low' | 'medium' | 'high';
    category: 'nasa' | 'strict' | 'default' | 'lenient' | 'custom';
    settings: PolicySettings;
    tags: string[];
    deprecated?: boolean;
}

export interface PolicySettings {
    safetyProfile: string;
    confidenceThreshold: number;
    nasaComplianceThreshold: number;
    meceQualityThreshold: number;
    analysisDepth: string;
    enableExperimentalFeatures: boolean;
    maxDiagnostics: number;
    realTimeAnalysis: boolean;
    grammarValidation: boolean;
    autoFixSuggestions: boolean;
    performanceAnalysis: any;
    advancedFiltering: any;
    customRules: any[];
}

export interface PolicyComparison {
    preset1: PolicyPreset;
    preset2: PolicyPreset;
    differences: PolicyDifference[];
    impactAnalysis: ImpactAnalysis;
}

export interface PolicyDifference {
    setting: string;
    value1: any;
    value2: any;
    impact: 'low' | 'medium' | 'high';
    description: string;
}

export interface ImpactAnalysis {
    performanceImpact: number; // -100 to 100 (negative = faster, positive = slower)
    thoroughnessImpact: number; // 0 to 100 (higher = more thorough)
    falsePositiveRate: number; // 0 to 100 (percentage)
    estimatedAnalysisTime: string; // human readable
    memoryUsage: string; // estimated memory impact
}

export class ConfigurationService {
    private readonly configSection = 'connascence';
    private readonly policyPresets: PolicyPreset[] = this.initializePolicyPresets();

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

    getCliCommand(): string {
        return this.getConfig('cliCommand', 'connascence');
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

    // =====================================================
    // POLICY MANAGEMENT METHODS
    // =====================================================

    /**
     * Initialize predefined policy presets
     */
    private initializePolicyPresets(): PolicyPreset[] {
        return [
            // NASA JPL Power of Ten Rules (Strictest)
            {
                id: 'nasa_jpl_pot10',
                name: 'NASA JPL Power of Ten',
                description: 'Extremely strict safety rules based on NASA JPL Power of Ten coding standards',
                impact: 'high',
                category: 'nasa',
                tags: ['nasa', 'safety-critical', 'embedded', 'aerospace'],
                settings: {
                    safetyProfile: 'safety_level_1',
                    confidenceThreshold: 0.99,
                    nasaComplianceThreshold: 1.0,
                    meceQualityThreshold: 0.95,
                    analysisDepth: 'comprehensive',
                    enableExperimentalFeatures: false,
                    maxDiagnostics: 50,
                    realTimeAnalysis: true,
                    grammarValidation: true,
                    autoFixSuggestions: false, // Manual review required
                    performanceAnalysis: {
                        enableProfiling: true,
                        maxAnalysisTime: 120000, // 2 minutes per file
                        memoryThreshold: 256,
                        enableCaching: false, // Force fresh analysis
                        cacheSize: 0
                    },
                    advancedFiltering: {
                        enableGitIgnore: true,
                        enableCustomIgnore: true,
                        minFileSize: 1,
                        maxFileSize: 5242880, // 5MB max
                        excludeBinaryFiles: true
                    },
                    customRules: []
                }
            },
            // Strict Core (High Safety)
            {
                id: 'strict_core',
                name: 'Strict Core Safety',
                description: 'High safety standards for critical business applications',
                impact: 'high',
                category: 'strict',
                tags: ['safety', 'business-critical', 'high-reliability'],
                settings: {
                    safetyProfile: 'general_safety_strict',
                    confidenceThreshold: 0.9,
                    nasaComplianceThreshold: 0.95,
                    meceQualityThreshold: 0.88,
                    analysisDepth: 'deep',
                    enableExperimentalFeatures: false,
                    maxDiagnostics: 200,
                    realTimeAnalysis: true,
                    grammarValidation: true,
                    autoFixSuggestions: true,
                    performanceAnalysis: {
                        enableProfiling: true,
                        maxAnalysisTime: 60000,
                        memoryThreshold: 512,
                        enableCaching: true,
                        cacheSize: 500
                    },
                    advancedFiltering: {
                        enableGitIgnore: true,
                        enableCustomIgnore: true,
                        minFileSize: 10,
                        maxFileSize: 10485760,
                        excludeBinaryFiles: true
                    },
                    customRules: []
                }
            },
            // Default Balanced
            {
                id: 'default_balanced',
                name: 'Default Balanced',
                description: 'Balanced approach suitable for most development projects',
                impact: 'medium',
                category: 'default',
                tags: ['general', 'balanced', 'recommended'],
                settings: {
                    safetyProfile: 'modern_general',
                    confidenceThreshold: 0.8,
                    nasaComplianceThreshold: 0.85,
                    meceQualityThreshold: 0.75,
                    analysisDepth: 'standard',
                    enableExperimentalFeatures: false,
                    maxDiagnostics: 1000,
                    realTimeAnalysis: true,
                    grammarValidation: true,
                    autoFixSuggestions: true,
                    performanceAnalysis: {
                        enableProfiling: true,
                        maxAnalysisTime: 30000,
                        memoryThreshold: 512,
                        enableCaching: true,
                        cacheSize: 1000
                    },
                    advancedFiltering: {
                        enableGitIgnore: true,
                        enableCustomIgnore: true,
                        minFileSize: 10,
                        maxFileSize: 10485760,
                        excludeBinaryFiles: true
                    },
                    customRules: []
                }
            },
            // Lenient Development
            {
                id: 'lenient_dev',
                name: 'Lenient Development',
                description: 'Relaxed settings for rapid prototyping and development',
                impact: 'low',
                category: 'lenient',
                tags: ['prototype', 'development', 'fast'],
                settings: {
                    safetyProfile: 'none',
                    confidenceThreshold: 0.6,
                    nasaComplianceThreshold: 0.5,
                    meceQualityThreshold: 0.5,
                    analysisDepth: 'surface',
                    enableExperimentalFeatures: true,
                    maxDiagnostics: 2000,
                    realTimeAnalysis: false,
                    grammarValidation: false,
                    autoFixSuggestions: true,
                    performanceAnalysis: {
                        enableProfiling: false,
                        maxAnalysisTime: 15000,
                        memoryThreshold: 1024,
                        enableCaching: true,
                        cacheSize: 2000
                    },
                    advancedFiltering: {
                        enableGitIgnore: true,
                        enableCustomIgnore: false,
                        minFileSize: 50,
                        maxFileSize: 52428800, // 50MB
                        excludeBinaryFiles: true
                    },
                    customRules: []
                }
            }
        ];
    }

    /**
     * Get all available policy presets
     */
    getPolicyPresets(): PolicyPreset[] {
        return [...this.policyPresets];
    }

    /**
     * Get policy preset by ID
     */
    getPolicyPresetById(id: string): PolicyPreset | undefined {
        return this.policyPresets.find(preset => preset.id === id);
    }

    /**
     * Apply a policy preset to the current configuration
     */
    async applyPolicyPreset(presetId: string): Promise<{ success: boolean; errors?: string[] }> {
        const preset = this.getPolicyPresetById(presetId);
        if (!preset) {
            return { success: false, errors: [`Policy preset '${presetId}' not found`] };
        }

        const errors: string[] = [];
        
        try {
            // Validate settings before applying
            const validation = this.validatePolicySettings(preset.settings);
            if (!validation.isValid) {
                return { success: false, errors: validation.errors };
            }

            // Apply each setting
            const config = vscode.workspace.getConfiguration(this.configSection);
            
            for (const [key, value] of Object.entries(preset.settings)) {
                try {
                    await config.update(key, value, vscode.ConfigurationTarget.Workspace);
                } catch (error) {
                    errors.push(`Failed to update ${key}: ${error}`);
                }
            }

            // Store the applied preset ID for tracking
            await config.update('appliedPolicyPreset', presetId, vscode.ConfigurationTarget.Workspace);
            
            return { success: errors.length === 0, errors: errors.length > 0 ? errors : undefined };
            
        } catch (error) {
            return { success: false, errors: [`Failed to apply policy preset: ${error}`] };
        }
    }

    /**
     * Create a custom policy based on user selections
     */
    async createCustomPolicy(name: string, description: string, settings: Partial<PolicySettings>): Promise<{ success: boolean; preset?: PolicyPreset; errors?: string[] }> {
        try {
            // Merge with defaults to create complete settings
            const defaultPreset = this.getPolicyPresetById('default_balanced');
            if (!defaultPreset) {
                return { success: false, errors: ['Default preset not found'] };
            }

            const customSettings: PolicySettings = { ...defaultPreset.settings, ...settings };
            
            // Validate the custom settings
            const validation = this.validatePolicySettings(customSettings);
            if (!validation.isValid) {
                return { success: false, errors: validation.errors };
            }

            const customPreset: PolicyPreset = {
                id: `custom_${Date.now()}`,
                name,
                description,
                impact: this.calculatePolicyImpact(customSettings),
                category: 'custom',
                tags: ['custom', 'user-defined'],
                settings: customSettings
            };

            // Store custom preset in workspace settings
            const customPresets = this.getCustomPresets();
            customPresets.push(customPreset);
            await this.saveCustomPresets(customPresets);

            return { success: true, preset: customPreset };

        } catch (error) {
            return { success: false, errors: [`Failed to create custom policy: ${error}`] };
        }
    }

    /**
     * Export policy configuration for sharing
     */
    async exportPolicyConfiguration(presetId?: string): Promise<{ success: boolean; data?: any; errors?: string[] }> {
        try {
            let exportData: any;
            
            if (presetId) {
                const preset = this.getPolicyPresetById(presetId);
                if (!preset) {
                    return { success: false, errors: [`Policy preset '${presetId}' not found`] };
                }
                exportData = preset;
            } else {
                // Export current configuration as custom preset
                exportData = {
                    id: 'exported_config',
                    name: 'Exported Configuration',
                    description: 'Configuration exported from workspace',
                    impact: this.calculatePolicyImpact(this.getCurrentPolicySettings()),
                    category: 'custom',
                    tags: ['exported'],
                    settings: this.getCurrentPolicySettings(),
                    exportedAt: new Date().toISOString()
                };
            }

            return { success: true, data: exportData };

        } catch (error) {
            return { success: false, errors: [`Failed to export policy configuration: ${error}`] };
        }
    }

    /**
     * Compare two policy presets
     */
    comparePolicyPresets(preset1Id: string, preset2Id: string): PolicyComparison | null {
        const preset1 = this.getPolicyPresetById(preset1Id);
        const preset2 = this.getPolicyPresetById(preset2Id);
        
        if (!preset1 || !preset2) {
            return null;
        }

        const differences = this.calculatePolicyDifferences(preset1.settings, preset2.settings);
        const impactAnalysis = this.calculateImpactAnalysis(preset1.settings, preset2.settings);

        return {
            preset1,
            preset2,
            differences,
            impactAnalysis
        };
    }

    /**
     * Get currently applied policy preset ID
     */
    getAppliedPolicyPreset(): string | undefined {
        return this.getConfig('appliedPolicyPreset', undefined);
    }

    /**
     * Validate policy settings
     */
    private validatePolicySettings(settings: PolicySettings): { isValid: boolean; errors: string[] } {
        const errors: string[] = [];

        // Validate thresholds
        if (settings.confidenceThreshold < 0 || settings.confidenceThreshold > 1) {
            errors.push('Confidence threshold must be between 0 and 1');
        }
        if (settings.nasaComplianceThreshold < 0 || settings.nasaComplianceThreshold > 1) {
            errors.push('NASA compliance threshold must be between 0 and 1');
        }
        if (settings.meceQualityThreshold < 0 || settings.meceQualityThreshold > 1) {
            errors.push('MECE quality threshold must be between 0 and 1');
        }

        // Validate safety profile
        const validProfiles = ['none', 'general_safety_strict', 'safety_level_1', 'safety_level_3', 'modern_general'];
        if (!validProfiles.includes(settings.safetyProfile)) {
            errors.push(`Invalid safety profile: ${settings.safetyProfile}`);
        }

        // Validate analysis depth
        const validDepths = ['surface', 'standard', 'deep', 'comprehensive'];
        if (!validDepths.includes(settings.analysisDepth)) {
            errors.push(`Invalid analysis depth: ${settings.analysisDepth}`);
        }

        // Validate max diagnostics
        if (settings.maxDiagnostics < 1 || settings.maxDiagnostics > 10000) {
            errors.push('Max diagnostics must be between 1 and 10000');
        }

        return { isValid: errors.length === 0, errors };
    }

    /**
     * Calculate policy impact level
     */
    private calculatePolicyImpact(settings: PolicySettings): 'low' | 'medium' | 'high' {
        let impactScore = 0;

        // Factors that increase impact
        if (settings.analysisDepth === 'comprehensive') impactScore += 3;
        else if (settings.analysisDepth === 'deep') impactScore += 2;
        else if (settings.analysisDepth === 'standard') impactScore += 1;

        if (settings.confidenceThreshold > 0.9) impactScore += 2;
        else if (settings.confidenceThreshold > 0.8) impactScore += 1;

        if (settings.nasaComplianceThreshold > 0.9) impactScore += 2;
        else if (settings.nasaComplianceThreshold > 0.8) impactScore += 1;

        if (settings.realTimeAnalysis) impactScore += 1;
        if (settings.grammarValidation) impactScore += 1;
        if (settings.performanceAnalysis.enableProfiling) impactScore += 1;

        // Determine impact level
        if (impactScore >= 7) return 'high';
        if (impactScore >= 4) return 'medium';
        return 'low';
    }

    /**
     * Calculate differences between two policy settings
     */
    private calculatePolicyDifferences(settings1: PolicySettings, settings2: PolicySettings): PolicyDifference[] {
        const differences: PolicyDifference[] = [];
        
        // Compare each setting
        const settingKeys = Object.keys(settings1) as (keyof PolicySettings)[];
        
        for (const key of settingKeys) {
            const value1 = settings1[key];
            const value2 = settings2[key];
            
            if (JSON.stringify(value1) !== JSON.stringify(value2)) {
                differences.push({
                    setting: key,
                    value1,
                    value2,
                    impact: this.calculateSettingImpact(key, value1, value2),
                    description: this.getSettingDescription(key)
                });
            }
        }

        return differences;
    }

    /**
     * Calculate impact analysis between two settings
     */
    private calculateImpactAnalysis(settings1: PolicySettings, settings2: PolicySettings): ImpactAnalysis {
        const performanceImpact = this.calculatePerformanceImpact(settings1, settings2);
        const thoroughnessImpact = this.calculateThoroughnessImpact(settings1, settings2);
        
        return {
            performanceImpact,
            thoroughnessImpact,
            falsePositiveRate: Math.max(0, 20 - thoroughnessImpact * 0.2),
            estimatedAnalysisTime: this.estimateAnalysisTime(settings2),
            memoryUsage: this.estimateMemoryUsage(settings2)
        };
    }

    /**
     * Helper methods for impact analysis
     */
    private calculatePerformanceImpact(settings1: PolicySettings, settings2: PolicySettings): number {
        let impact = 0;
        
        // Analysis depth impact
        const depthScores = { 'surface': 1, 'standard': 2, 'deep': 3, 'comprehensive': 4 };
        impact += (depthScores[settings2.analysisDepth as keyof typeof depthScores] - 
                  depthScores[settings1.analysisDepth as keyof typeof depthScores]) * 25;
        
        // Threshold impacts
        impact += (settings2.confidenceThreshold - settings1.confidenceThreshold) * 30;
        impact += (settings2.nasaComplianceThreshold - settings1.nasaComplianceThreshold) * 20;
        
        return Math.max(-100, Math.min(100, impact));
    }

    private calculateThoroughnessImpact(settings1: PolicySettings, settings2: PolicySettings): number {
        let thoroughness = 0;
        
        const depthScores = { 'surface': 25, 'standard': 50, 'deep': 75, 'comprehensive': 100 };
        thoroughness += depthScores[settings2.analysisDepth as keyof typeof depthScores] * 0.4;
        
        thoroughness += settings2.confidenceThreshold * 30;
        thoroughness += settings2.nasaComplianceThreshold * 20;
        thoroughness += settings2.meceQualityThreshold * 10;
        
        return Math.max(0, Math.min(100, thoroughness));
    }

    private estimateAnalysisTime(settings: PolicySettings): string {
        const baseTime = 1000; // ms per file
        let multiplier = 1;
        
        switch (settings.analysisDepth) {
            case 'surface': multiplier = 0.5; break;
            case 'standard': multiplier = 1; break;
            case 'deep': multiplier = 2; break;
            case 'comprehensive': multiplier = 4; break;
        }
        
        multiplier *= (1 + settings.confidenceThreshold);
        
        const estimatedMs = baseTime * multiplier;
        
        if (estimatedMs < 2000) return '< 2 seconds per file';
        if (estimatedMs < 10000) return '2-10 seconds per file';
        if (estimatedMs < 30000) return '10-30 seconds per file';
        return '> 30 seconds per file';
    }

    private estimateMemoryUsage(settings: PolicySettings): string {
        let baseMemory = 50; // MB
        
        switch (settings.analysisDepth) {
            case 'surface': baseMemory *= 0.5; break;
            case 'standard': baseMemory *= 1; break;
            case 'deep': baseMemory *= 2; break;
            case 'comprehensive': baseMemory *= 4; break;
        }
        
        if (settings.performanceAnalysis.enableProfiling) {
            baseMemory *= 1.5;
        }
        
        if (baseMemory < 100) return 'Low (< 100MB)';
        if (baseMemory < 300) return 'Medium (100-300MB)';
        return 'High (> 300MB)';
    }

    private calculateSettingImpact(key: string, value1: any, value2: any): 'low' | 'medium' | 'high' {
        const highImpactSettings = ['safetyProfile', 'analysisDepth', 'confidenceThreshold'];
        const mediumImpactSettings = ['nasaComplianceThreshold', 'meceQualityThreshold', 'realTimeAnalysis'];
        
        if (highImpactSettings.includes(key)) return 'high';
        if (mediumImpactSettings.includes(key)) return 'medium';
        return 'low';
    }

    private getSettingDescription(key: string): string {
        const descriptions: { [key: string]: string } = {
            safetyProfile: 'Controls the overall safety compliance level',
            confidenceThreshold: 'Minimum confidence required for suggestions',
            nasaComplianceThreshold: 'NASA safety standard compliance threshold',
            meceQualityThreshold: 'Mutually Exclusive, Collectively Exhaustive quality threshold',
            analysisDepth: 'How thorough the code analysis should be',
            enableExperimentalFeatures: 'Enable unstable experimental features',
            maxDiagnostics: 'Maximum number of diagnostic messages to show',
            realTimeAnalysis: 'Enable real-time analysis while typing',
            grammarValidation: 'Enable grammar validation in code analysis',
            autoFixSuggestions: 'Enable automatic fix suggestions'
        };
        
        return descriptions[key] || `Configuration setting: ${key}`;
    }

    /**
     * Get current policy settings from workspace configuration
     */
    private getCurrentPolicySettings(): PolicySettings {
        return {
            safetyProfile: this.getSafetyProfile(),
            confidenceThreshold: this.getConfidenceThreshold(),
            nasaComplianceThreshold: this.getNasaComplianceThreshold(),
            meceQualityThreshold: this.getMeceQualityThreshold(),
            analysisDepth: this.getAnalysisDepth(),
            enableExperimentalFeatures: this.isExperimentalFeaturesEnabled(),
            maxDiagnostics: this.getMaxDiagnostics(),
            realTimeAnalysis: this.isRealTimeAnalysisEnabled(),
            grammarValidation: this.isGrammarValidationEnabled(),
            autoFixSuggestions: this.isAutoFixSuggestionsEnabled(),
            performanceAnalysis: this.getPerformanceAnalysisConfig(),
            advancedFiltering: this.getAdvancedFilteringConfig(),
            customRules: this.getCustomRules()
        };
    }

    /**
     * Get custom presets from workspace settings
     */
    private getCustomPresets(): PolicyPreset[] {
        return this.getConfig('customPolicyPresets', []);
    }

    /**
     * Save custom presets to workspace settings
     */
    private async saveCustomPresets(presets: PolicyPreset[]): Promise<void> {
        await this.updateConfig('customPolicyPresets', presets);
    }
}