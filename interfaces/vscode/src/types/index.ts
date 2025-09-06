/**
 * Type definitions for the Connascence VS Code Extension
 */

export interface ConnascenceConfiguration {
    safetyProfile: 'none' | 'general_safety_strict' | 'safety_level_1' | 'safety_level_3' | 'modern_general';
    grammarValidation: boolean;
    realTimeAnalysis: boolean;
    debounceMs: number;
    maxDiagnostics: number;
    enableIntelliSense: boolean;
    enableCodeLens: boolean;
    enableHover: boolean;
    autoFixSuggestions: boolean;
    serverUrl: string;
    authenticateWithServer: boolean;
    frameworkProfile: 'generic' | 'django' | 'fastapi' | 'react';
    showInlineHints: boolean;
    diagnosticSeverity: 'error' | 'warning' | 'info' | 'hint';
    pythonPath?: string;
    enableTelemetry: boolean;
    threshold: number;
    includeTests: boolean;
    strictMode: boolean;
    safeMode: boolean;
    exclude: string[];
    // Enhanced configuration options
    confidenceThreshold: number;
    excludePatterns: string[];
    includePatterns: string[];
    nasaComplianceThreshold: number;
    meceQualityThreshold: number;
    performanceAnalysis: PerformanceAnalysisConfig;
    advancedFiltering: AdvancedFilteringConfig;
    analysisDepth: 'surface' | 'standard' | 'deep' | 'comprehensive';
    enableExperimentalFeatures: boolean;
    customRules: CustomAnalysisRule[];
}

export interface PerformanceAnalysisConfig {
    enableProfiling: boolean;
    maxAnalysisTime: number;
    memoryThreshold: number;
    enableCaching: boolean;
    cacheSize: number;
}

export interface AdvancedFilteringConfig {
    enableGitIgnore: boolean;
    enableCustomIgnore: boolean;
    minFileSize: number;
    maxFileSize: number;
    excludeBinaryFiles: boolean;
}

export interface CustomAnalysisRule {
    name: string;
    pattern: string;
    severity: 'error' | 'warning' | 'info' | 'hint';
    message: string;
    enabled?: boolean;
    category?: string;
    tags?: string[];
}

export interface FrameworkSpecificConfig {
    [key: string]: any;
    confidenceThreshold: number;
    analysisDepth: string;
    customRules: CustomAnalysisRule[];
    performanceSettings: PerformanceAnalysisConfig;
    filteringSettings: AdvancedFilteringConfig;
}

export interface SafetyProfileConfig {
    strictMode: boolean;
    maxComplexity: number;
    maxNestedLoops: number;
    maxFunctionParams: number;
    maxLineLength: number;
    requireDocstrings: boolean;
    enforceTypeHints: boolean;
    enableNasaCompliance: boolean;
    confidenceThreshold: number;
    nasaComplianceThreshold: number;
    meceQualityThreshold: number;
    analysisDepth: string;
    experimentalFeatures: boolean;
    noRecursion?: boolean;
    noDynamicAllocation?: boolean;
}

export interface AnalysisOptions {
    inputPath: string;
    outputPath?: string;
    format: 'json' | 'sarif' | 'html';
    verbose?: boolean;
    includeTests?: boolean;
    safetyProfile: string;
    threshold?: number;
    exclude?: string[];
    mode?: 'single-file' | 'workspace' | 'safety-validation' | 'refactoring-suggestions' | 'automated-fixes';
    generateMetrics?: boolean;
    includeRecommendations?: boolean;
}

export interface PythonAnalyzerResult {
    findings: PythonFinding[];
    quality_score?: number;
    overall_score?: number;
    safety_compliant?: boolean;
    safety_violations?: SafetyViolation[];
    suggestions?: RefactoringSuggestion[];
    fixes?: AutoFix[];
    files?: { [filePath: string]: PythonAnalyzerResult };
}

export interface PythonFinding {
    id?: string;
    type: string;
    rule_id?: string;
    severity: string;
    message: string;
    description?: string;
    file: string;
    file_path?: string;
    line: number;
    line_number?: number;
    column?: number;
    column_number?: number;
    suggestion?: string;
    recommendation?: string;
}

export interface SafetyViolation {
    rule: string;
    message: string;
    line: number;
    severity: string;
}

export interface RefactoringSuggestion {
    technique: string;
    description: string;
    confidence: number;
    preview?: string;
}

export interface AutoFix {
    line: number;
    column?: number;
    endLine?: number;
    endColumn?: number;
    issue: string;
    description: string;
    replacement: string;
}

export interface ExtensionState {
    isAnalyzing: boolean;
    lastAnalysisTime: number | null;
    analysisQueue: string[];
    configurationValid: boolean;
    pythonAvailable: boolean;
    analyzerAvailable: boolean;
}

export interface PerformanceMetrics {
    analysisTime: number;
    fileCount: number;
    issueCount: number;
    memoryUsage: number;
    cacheHitRate: number;
}

export interface CacheEntry<T> {
    data: T;
    timestamp: number;
    fileHash: string;
    dependencies: string[];
}

export interface LRUCacheOptions {
    maxSize: number;
    ttlMs: number;
}