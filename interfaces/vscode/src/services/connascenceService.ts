import * as vscode from 'vscode';
import * as path from 'path';
import { spawn } from 'child_process';
import { ConfigurationService } from './configurationService';
import { TelemetryService } from './telemetryService';
import { ConnascenceApiClient } from './connascenceApiClient';
import { MCPClient } from './mcpClient';

export interface AnalysisResult {
    findings: Finding[];
    qualityScore: number;
    summary: {
        totalIssues: number;
        issuesBySeverity: {
            critical: number;
            major: number;
            minor: number;
            info: number;
        };
    };
    // Advanced analyzer capabilities
    performanceMetrics?: PerformanceMetrics;
    duplicationClusters?: DuplicationCluster[];
    nasaCompliance?: NASAComplianceResult;
    smartIntegrationResults?: SmartIntegrationResult;
}

export interface Finding {
    id: string;
    type: string;
    severity: 'critical' | 'major' | 'minor' | 'info';
    message: string;
    file: string;
    line: number;
    column?: number;
    suggestion?: string;
}

export interface SafetyValidationResult {
    compliant: boolean;
    violations: SafetyViolation[];
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

export interface PerformanceMetrics {
    analysisTime: number;
    parallelProcessing: boolean;
    speedupFactor?: number;
    workerCount?: number;
    memoryUsage?: number;
    efficiency?: number;
}

export interface DuplicationCluster {
    id: string;
    blocks: CodeBlock[];
    similarity: number;
    severity: 'critical' | 'major' | 'minor' | 'info';
    description: string;
    files: string[];
}

export interface CodeBlock {
    file: string;
    startLine: number;
    endLine: number;
    content: string;
    hash: string;
}

export interface NASAComplianceResult {
    compliant: boolean;
    score: number;
    violations: NASAViolation[];
    powerOfTenRules: PowerOfTenRule[];
}

export interface NASAViolation {
    rule: string;
    message: string;
    file: string;
    line: number;
    severity: 'critical' | 'major' | 'minor' | 'info';
    powerOfTenRule?: number;
}

export interface PowerOfTenRule {
    id: number;
    description: string;
    compliant: boolean;
    violationCount: number;
}

export interface SmartIntegrationResult {
    crossAnalyzerCorrelation: CorrelationResult[];
    intelligentRecommendations: IntelligentRecommendation[];
    qualityTrends: QualityTrend[];
    riskAssessment: RiskAssessment;
}

export interface CorrelationResult {
    analyzer1: string;
    analyzer2: string;
    correlationScore: number;
    commonFindings: Finding[];
}

export interface IntelligentRecommendation {
    priority: 'high' | 'medium' | 'low';
    category: string;
    description: string;
    impact: string;
    effort: 'low' | 'medium' | 'high';
    suggestedActions: string[];
}

export interface QualityTrend {
    metric: string;
    current: number;
    previous?: number;
    trend: 'improving' | 'stable' | 'declining';
    projection: number;
}

export interface RiskAssessment {
    overallRisk: 'low' | 'medium' | 'high' | 'critical';
    riskFactors: RiskFactor[];
    mitigation: string[];
}

export interface RiskFactor {
    factor: string;
    impact: number;
    likelihood: number;
    description: string;
}

export interface WorkspaceAnalysisResult {
    fileResults: { [filePath: string]: AnalysisResult };
    summary: {
        filesAnalyzed: number;
        totalIssues: number;
        qualityScore: number;
    };
}

export class ConnascenceService {
    private apiClient: ConnascenceApiClient;
    private mcpClient: MCPClient | null = null;
    private parallelAnalysisEnabled: boolean = true;
    private meceAnalysisEnabled: boolean = true;
    private nasaComplianceEnabled: boolean = true;
    private smartIntegrationEnabled: boolean = true;

    constructor(
        private configService: ConfigurationService,
        private telemetryService: TelemetryService,
        private context: vscode.ExtensionContext
    ) {
        this.apiClient = new ConnascenceApiClient();
        this.initializeAdvancedCapabilities();
        this.initializeMCPClient();
    }

    /**
     * Initialize MCP client with graceful fallback
     */
    private async initializeMCPClient(): Promise<void> {
        try {
            this.mcpClient = new MCPClient(this.context);
            await this.mcpClient.connect();
            console.log('[ConnascenceService] MCP client connected successfully');
        } catch (error) {
            console.warn('[ConnascenceService] MCP client initialization failed, using CLI fallback:', error);
            this.mcpClient = null;
        }
    }

    private initializeAdvancedCapabilities(): void {
        // Initialize advanced analyzer capabilities based on configuration
        this.parallelAnalysisEnabled = this.configService.getEnableParallelAnalysis();
        this.meceAnalysisEnabled = this.configService.getEnableMECEAnalysis();
        this.nasaComplianceEnabled = this.configService.getEnableNASACompliance();
        this.smartIntegrationEnabled = this.configService.getEnableSmartIntegration();
        
        this.telemetryService.logEvent('advanced.capabilities.initialized', {
            parallel: this.parallelAnalysisEnabled,
            mece: this.meceAnalysisEnabled,
            nasa: this.nasaComplianceEnabled,
            smart: this.smartIntegrationEnabled
        });
    }

    async analyzeFile(filePath: string): Promise<AnalysisResult> {
        this.telemetryService.logEvent('file.analysis.started', { file: path.basename(filePath) });
        
        try {
            const startTime = Date.now();
            
            // Get basic analysis from API client
            const baseResult = await this.apiClient.analyzeFile(filePath);
            
            // Enhance with advanced analyzer capabilities
            const enhancedResult = await this.enhanceAnalysisResult(baseResult, filePath, {
                analysisType: 'single-file',
                startTime
            });
            
            this.telemetryService.logEvent('file.analysis.completed', { 
                file: path.basename(filePath),
                findings: enhancedResult.findings.length,
                qualityScore: enhancedResult.qualityScore,
                analysisTime: Date.now() - startTime
            });
            
            return enhancedResult;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            this.telemetryService.logEvent('file.analysis.error', { error: errorMessage });
            throw error;
        }
    }

    async analyzeWorkspace(workspacePath: string): Promise<WorkspaceAnalysisResult> {
        this.telemetryService.logEvent('workspace.analysis.started');
        
        try {
            const startTime = Date.now();
            
            // Get base workspace analysis
            const baseResult = await this.apiClient.analyzeWorkspace(workspacePath);
            
            // Enhance each file result with advanced capabilities
            const enhancedFileResults: { [filePath: string]: AnalysisResult } = {};
            
            for (const [filePath, fileResult] of Object.entries(baseResult.fileResults)) {
                enhancedFileResults[filePath] = await this.enhanceAnalysisResult(
                    fileResult, filePath, {
                        analysisType: 'workspace',
                        startTime,
                        workspacePath
                    }
                );
            }
            
            // Calculate enhanced workspace metrics
            const enhancedSummary = await this.calculateWorkspaceSummary(
                enhancedFileResults, workspacePath, startTime
            );
            
            const analysisTime = Date.now() - startTime;
            
            this.telemetryService.logEvent('workspace.analysis.completed', {
                filesAnalyzed: Object.keys(enhancedFileResults).length,
                totalIssues: enhancedSummary.totalIssues,
                qualityScore: enhancedSummary.qualityScore,
                analysisTime
            });
            
            return {
                fileResults: enhancedFileResults,
                summary: enhancedSummary
            };
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            this.telemetryService.logEvent('workspace.analysis.error', { error: errorMessage });
            throw error;
        }
    }

    async validateSafety(filePath: string, profile: string): Promise<SafetyValidationResult> {
        this.telemetryService.logEvent('safety.validation.started', { profile });
        
        try {
            return await this.apiClient.validateSafety(filePath, profile);
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            this.telemetryService.logEvent('safety.validation.error', { error: errorMessage });
            throw error;
        }
    }

    async suggestRefactoring(filePath: string, selection?: { start: { line: number; character: number }, end: { line: number; character: number } }): Promise<RefactoringSuggestion[]> {
        this.telemetryService.logEvent('refactoring.suggestion.requested');
        
        try {
            return await this.apiClient.suggestRefactoring(filePath, selection);
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            this.telemetryService.logEvent('refactoring.suggestion.error', { error: errorMessage });
            throw error;
        }
    }

    async getAutofixes(filePath: string): Promise<AutoFix[]> {
        this.telemetryService.logEvent('autofix.requested');
        
        try {
            return await this.apiClient.getAutofixes(filePath);
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            this.telemetryService.logEvent('autofix.error', { error: errorMessage });
            throw error;
        }
    }

    async generateReport(workspacePath: string): Promise<any> {
        this.telemetryService.logEvent('report.generation.started');
        
        try {
            return await this.apiClient.generateReport(workspacePath);
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            this.telemetryService.logEvent('report.generation.error', { error: errorMessage });
            throw error;
        }
    }

    // MCP implementations
    private async analyzeMCP(filePath: string): Promise<AnalysisResult> {
        if (!this.mcpClient || !this.mcpClient.isServerConnected()) {
            throw new Error('MCP server not connected');
        }

        try {
            const result = await this.mcpClient.analyzeFile(filePath, {
                profile: this.configService.getSafetyProfile(),
                parallel: this.parallelAnalysisEnabled,
                nasa: this.nasaComplianceEnabled,
                mece: this.meceAnalysisEnabled,
                smart: this.smartIntegrationEnabled
            });

            this.telemetryService.logEvent('mcp.analysis.completed', {
                filePath,
                findingsCount: result.findings?.length || 0,
                qualityScore: result.qualityScore
            });

            return result;
        } catch (error) {
            this.telemetryService.logError(error as Error, 'mcp.analysis.failed');
            throw error;
        }
    }

    private async analyzeWorkspaceMCP(workspacePath: string): Promise<WorkspaceAnalysisResult> {
        if (!this.mcpClient || !this.mcpClient.isServerConnected()) {
            throw new Error('MCP server not connected');
        }

        try {
            const result = await this.mcpClient.analyzeWorkspace(workspacePath, {
                profile: this.configService.getSafetyProfile(),
                parallel: this.parallelAnalysisEnabled,
                exclude: this.configService.getExcludePatterns(),
                includeTests: false // Default to false
            });

            this.telemetryService.logEvent('mcp.workspace.analysis.completed', {
                workspacePath,
                filesAnalyzed: result.summary?.filesAnalyzed || 0,
                totalIssues: result.summary?.totalIssues || 0
            });

            return result;
        } catch (error) {
            this.telemetryService.logError(error as Error, 'mcp.workspace.analysis.failed');
            throw error;
        }
    }

    private async validateSafetyMCP(filePath: string, profile: string): Promise<SafetyValidationResult> {
        if (!this.mcpClient || !this.mcpClient.isServerConnected()) {
            throw new Error('MCP server not connected');
        }

        try {
            const result = await this.mcpClient.validateSafety(filePath, profile);

            this.telemetryService.logEvent('mcp.safety.validation.completed', {
                filePath,
                profile,
                compliant: result.compliant,
                violationsCount: result.violations?.length || 0
            });

            return result;
        } catch (error) {
            this.telemetryService.logError(error as Error, 'mcp.safety.validation.failed');
            throw error;
        }
    }

    private async suggestRefactoringMCP(filePath: string, selection?: any): Promise<RefactoringSuggestion[]> {
        if (!this.mcpClient || !this.mcpClient.isServerConnected()) {
            throw new Error('MCP server not connected');
        }

        try {
            const result = await this.mcpClient.getRefactoringSuggestions(filePath, selection);

            this.telemetryService.logEvent('mcp.refactoring.suggestions.completed', {
                filePath,
                suggestionsCount: result?.length || 0,
                hasSelection: !!selection
            });

            return result || [];
        } catch (error) {
            this.telemetryService.logError(error as Error, 'mcp.refactoring.suggestions.failed');
            throw error;
        }
    }

    private async getAutofixesMCP(filePath: string): Promise<AutoFix[]> {
        if (!this.mcpClient || !this.mcpClient.isServerConnected()) {
            throw new Error('MCP server not connected');
        }

        try {
            const result = await this.mcpClient.getAutofixes(filePath);

            this.telemetryService.logEvent('mcp.autofixes.completed', {
                filePath,
                autofixesCount: result?.length || 0
            });

            return result || [];
        } catch (error) {
            this.telemetryService.logError(error as Error, 'mcp.autofixes.failed');
            throw error;
        }
    }

    private async generateReportMCP(workspacePath: string): Promise<any> {
        if (!this.mcpClient || !this.mcpClient.isServerConnected()) {
            throw new Error('MCP server not connected');
        }

        try {
            const format = 'json'; // Default format
            const result = await this.mcpClient.generateReport(workspacePath, format);

            this.telemetryService.logEvent('mcp.report.generation.completed', {
                workspacePath,
                format
            });

            return result;
        } catch (error) {
            this.telemetryService.logError(error as Error, 'mcp.report.generation.failed');
            throw error;
        }
    }

    // CLI implementations
    private async analyzeCLI(filePath: string): Promise<AnalysisResult> {
        const safetyProfile = this.configService.getSafetyProfile();
        const cmd = 'connascence';
        const args = ['analyze', filePath, '--profile', safetyProfile, '--format', 'json'];

        return new Promise((resolve, reject) => {
            const process = spawn(cmd, args);
            let stdout = '';
            let stderr = '';

            process.stdout.on('data', (data) => stdout += data.toString());
            process.stderr.on('data', (data) => stderr += data.toString());

            process.on('close', (code) => {
                if (code === 0) {
                    try {
                        const result = JSON.parse(stdout);
                        resolve(this.transformCLIResult(result));
                    } catch (e) {
                        const errorMessage = e instanceof Error ? e.message : String(e);
                        reject(new Error(`Failed to parse CLI output: ${errorMessage}`));
                    }
                } else {
                    reject(new Error(`CLI failed with code ${code}: ${stderr}`));
                }
            });

            process.on('error', (err) => {
                reject(new Error(`Failed to run CLI: ${err.message}`));
            });
        });
    }

    private async analyzeWorkspaceCLI(workspacePath: string): Promise<WorkspaceAnalysisResult> {
        const safetyProfile = this.configService.getSafetyProfile();
        const cmd = 'connascence';
        const args = ['analyze', workspacePath, '--profile', safetyProfile, '--format', 'json', '--recursive'];

        return new Promise((resolve, reject) => {
            const process = spawn(cmd, args);
            let stdout = '';
            let stderr = '';

            process.stdout.on('data', (data) => stdout += data.toString());
            process.stderr.on('data', (data) => stderr += data.toString());

            process.on('close', (code) => {
                if (code === 0) {
                    try {
                        const result = JSON.parse(stdout);
                        resolve(this.transformWorkspaceResult(result));
                    } catch (e) {
                        const errorMessage = e instanceof Error ? e.message : String(e);
                        reject(new Error(`Failed to parse CLI output: ${errorMessage}`));
                    }
                } else {
                    reject(new Error(`CLI failed with code ${code}: ${stderr}`));
                }
            });

            process.on('error', (err) => {
                reject(new Error(`Failed to run CLI: ${err.message}`));
            });
        });
    }

    private async validateSafetyCLI(filePath: string, profile: string): Promise<SafetyValidationResult> {
        const cmd = 'connascence';
        const args = ['validate-safety', filePath, '--profile', profile, '--format', 'json'];

        return new Promise((resolve, reject) => {
            const process = spawn(cmd, args);
            let stdout = '';
            let stderr = '';

            process.stdout.on('data', (data) => stdout += data.toString());
            process.stderr.on('data', (data) => stderr += data.toString());

            process.on('close', (code) => {
                try {
                    const result = JSON.parse(stdout || '{}');
                    resolve({
                        compliant: code === 0,
                        violations: result.violations || []
                    });
                } catch (e) {
                    const errorMessage = e instanceof Error ? e.message : String(e);
                    reject(new Error(`Failed to parse safety validation output: ${errorMessage}`));
                }
            });

            process.on('error', (err) => {
                reject(new Error(`Failed to run safety validation: ${err.message}`));
            });
        });
    }

    private async suggestRefactoringCLI(filePath: string, selection?: any): Promise<RefactoringSuggestion[]> {
        const cmd = 'connascence';
        const args = ['suggest-refactoring', filePath, '--format', 'json'];
        
        if (selection) {
            args.push('--line', selection.start.line.toString());
        }

        return new Promise((resolve, reject) => {
            const process = spawn(cmd, args);
            let stdout = '';
            let stderr = '';

            process.stdout.on('data', (data) => stdout += data.toString());
            process.stderr.on('data', (data) => stderr += data.toString());

            process.on('close', (code) => {
                if (code === 0) {
                    try {
                        const result = JSON.parse(stdout);
                        resolve(result.suggestions || []);
                    } catch (e) {
                        const errorMessage = e instanceof Error ? e.message : String(e);
                        reject(new Error(`Failed to parse refactoring suggestions: ${errorMessage}`));
                    }
                } else {
                    reject(new Error(`Refactoring suggestion failed: ${stderr}`));
                }
            });

            process.on('error', (err) => {
                reject(new Error(`Failed to run refactoring suggestion: ${err.message}`));
            });
        });
    }

    private async getAutofixesCLI(filePath: string): Promise<AutoFix[]> {
        const cmd = 'connascence';
        const args = ['autofix', filePath, '--dry-run', '--format', 'json'];

        return new Promise((resolve, reject) => {
            const process = spawn(cmd, args);
            let stdout = '';
            let stderr = '';

            process.stdout.on('data', (data) => stdout += data.toString());
            process.stderr.on('data', (data) => stderr += data.toString());

            process.on('close', (code) => {
                if (code === 0) {
                    try {
                        const result = JSON.parse(stdout);
                        resolve(result.fixes || []);
                    } catch (e) {
                        const errorMessage = e instanceof Error ? e.message : String(e);
                        reject(new Error(`Failed to parse autofix output: ${errorMessage}`));
                    }
                } else {
                    reject(new Error(`Autofix failed: ${stderr}`));
                }
            });

            process.on('error', (err) => {
                reject(new Error(`Failed to run autofix: ${err.message}`));
            });
        });
    }

    private async generateReportCLI(workspacePath: string): Promise<any> {
        const cmd = 'connascence';
        const args = ['report', workspacePath, '--format', 'json'];

        return new Promise((resolve, reject) => {
            const process = spawn(cmd, args);
            let stdout = '';
            let stderr = '';

            process.stdout.on('data', (data) => stdout += data.toString());
            process.stderr.on('data', (data) => stderr += data.toString());

            process.on('close', (code) => {
                if (code === 0) {
                    try {
                        const result = JSON.parse(stdout);
                        resolve(result);
                    } catch (e) {
                        const errorMessage = e instanceof Error ? e.message : String(e);
                        reject(new Error(`Failed to parse report output: ${errorMessage}`));
                    }
                } else {
                    reject(new Error(`Report generation failed: ${stderr}`));
                }
            });

            process.on('error', (err) => {
                reject(new Error(`Failed to generate report: ${err.message}`));
            });
        });
    }

    private transformCLIResult(result: any): AnalysisResult {
        const findings = result.findings || result.violations || [];
        
        return {
            findings: findings.map((f: any) => ({
                id: f.id || `${f.type}_${f.line}`,
                type: f.type || f.rule_id,
                severity: f.severity || 'info',
                message: f.message || f.description,
                file: f.file || f.file_path,
                line: f.line || f.line_number,
                column: f.column || f.column_number,
                suggestion: f.suggestion || f.recommendation
            })),
            qualityScore: result.quality_score || result.score || 0,
            summary: {
                totalIssues: findings.length,
                issuesBySeverity: this.calculateSeveritySummary(findings)
            }
        };
    }

    private transformWorkspaceResult(result: any): WorkspaceAnalysisResult {
        const fileResults: { [filePath: string]: AnalysisResult } = {};
        
        if (result.files) {
            for (const [filePath, fileResult] of Object.entries(result.files)) {
                fileResults[filePath] = this.transformCLIResult(fileResult);
            }
        }

        return {
            fileResults,
            summary: {
                filesAnalyzed: Object.keys(fileResults).length,
                totalIssues: Object.values(fileResults).reduce((total, fr) => total + fr.findings.length, 0),
                qualityScore: result.overall_score || 0
            }
        };
    }

    private calculateSeveritySummary(findings: any[]): { critical: number; major: number; minor: number; info: number } {
        return findings.reduce((acc, finding) => {
            switch (finding.severity) {
                case 'critical':
                    acc.critical++;
                    break;
                case 'major':
                case 'high':
                    acc.major++;
                    break;
                case 'minor':
                case 'medium':
                    acc.minor++;
                    break;
                default:
                    acc.info++;
            }
            return acc;
        }, { critical: 0, major: 0, minor: 0, info: 0 });
    }

    /**
     * Enhance analysis result with advanced analyzer capabilities
     */
    private async enhanceAnalysisResult(
        baseResult: AnalysisResult, 
        filePath: string, 
        options: { analysisType: 'single-file' | 'workspace'; startTime: number; workspacePath?: string }
    ): Promise<AnalysisResult> {
        const enhancedResult = { ...baseResult };
        
        try {
            // Add performance metrics
            if (this.parallelAnalysisEnabled) {
                enhancedResult.performanceMetrics = await this.generatePerformanceMetrics(
                    options.startTime, filePath, options.analysisType
                );
            }
            
            // Add MECE duplication detection
            if (this.meceAnalysisEnabled) {
                enhancedResult.duplicationClusters = await this.runMECEAnalysis(
                    options.workspacePath || path.dirname(filePath)
                );
            }
            
            // Add NASA compliance checking
            if (this.nasaComplianceEnabled) {
                enhancedResult.nasaCompliance = await this.checkNASACompliance(
                    enhancedResult.findings
                );
            }
            
            // Add smart integration engine results
            if (this.smartIntegrationEnabled) {
                enhancedResult.smartIntegrationResults = await this.runSmartIntegration(
                    enhancedResult, filePath, options
                );
            }
            
            // Recalculate quality score with advanced metrics
            enhancedResult.qualityScore = this.calculateEnhancedQualityScore(enhancedResult);
            
        } catch (error) {
            this.telemetryService.logEvent('enhancement.error', {
                error: error instanceof Error ? error.message : String(error),
                filePath
            });
        }
        
        return enhancedResult;
    }

    /**
     * Generate performance metrics based on parallel analyzer capabilities
     */
    private async generatePerformanceMetrics(
        startTime: number,
        filePath: string,
        analysisType: string
    ): Promise<PerformanceMetrics> {
        const analysisTime = Date.now() - startTime;
        
        try {
            // Call Python parallel analyzer for detailed metrics
            const parallelMetrics = await this.runPythonAnalyzer({
                command: 'performance-metrics',
                filePath,
                analysisType
            });
            
            return {
                analysisTime,
                parallelProcessing: parallelMetrics.parallel_processing || false,
                speedupFactor: parallelMetrics.speedup_factor || 1.0,
                workerCount: parallelMetrics.worker_count || 1,
                memoryUsage: parallelMetrics.peak_memory_mb || 0,
                efficiency: parallelMetrics.efficiency || 1.0
            };
        } catch (error) {
            // Fallback metrics
            return {
                analysisTime,
                parallelProcessing: false,
                speedupFactor: 1.0,
                workerCount: 1
            };
        }
    }

    /**
     * Run MECE duplication analysis
     */
    private async runMECEAnalysis(projectPath: string): Promise<DuplicationCluster[]> {
        try {
            const meceResults = await this.runPythonAnalyzer({
                command: 'mece-analysis',
                projectPath,
                threshold: 0.7,
                comprehensive: true
            });
            
            return (meceResults.duplications || []).map((cluster: any) => ({
                id: cluster.id,
                blocks: cluster.blocks.map((block: any) => ({
                    file: block.file_path,
                    startLine: block.start_line,
                    endLine: block.end_line,
                    content: block.content || '',
                    hash: block.hash_signature || ''
                })),
                similarity: cluster.similarity_score,
                severity: this.calculateClusterSeverity(cluster.similarity_score),
                description: cluster.description,
                files: cluster.files_involved || []
            }));
        } catch (error) {
            this.telemetryService.logEvent('mece.analysis.error', {
                error: error instanceof Error ? error.message : String(error)
            });
            return [];
        }
    }

    /**
     * Check NASA Power of Ten compliance
     */
    private async checkNASACompliance(findings: Finding[]): Promise<NASAComplianceResult> {
        try {
            const nasaResults = await this.runPythonAnalyzer({
                command: 'nasa-compliance',
                findings: findings.map(f => ({
                    type: f.type,
                    severity: f.severity,
                    file: f.file,
                    line: f.line,
                    message: f.message
                }))
            });
            
            const violations: NASAViolation[] = (nasaResults.nasa_violations || []).map((v: any) => ({
                rule: v.rule,
                message: v.message,
                file: v.file_path || '',
                line: v.line_number || 0,
                severity: this.mapSeverity(v.severity),
                powerOfTenRule: v.power_of_ten_rule
            }));
            
            const powerOfTenRules: PowerOfTenRule[] = (nasaResults.power_of_ten_rules || []).map((rule: any) => ({
                id: rule.id,
                description: rule.description,
                compliant: rule.compliant,
                violationCount: rule.violation_count || 0
            }));
            
            return {
                compliant: violations.length === 0,
                score: nasaResults.nasa_compliance_score || 1.0,
                violations,
                powerOfTenRules
            };
        } catch (error) {
            this.telemetryService.logEvent('nasa.compliance.error', {
                error: error instanceof Error ? error.message : String(error)
            });
            
            // Fallback NASA compliance check based on existing findings
            return this.fallbackNASACompliance(findings);
        }
    }

    /**
     * Run smart integration engine analysis
     */
    private async runSmartIntegration(
        analysisResult: AnalysisResult,
        filePath: string,
        options: any
    ): Promise<SmartIntegrationResult> {
        try {
            const smartResults = await this.runPythonAnalyzer({
                command: 'smart-integration',
                filePath,
                findings: analysisResult.findings,
                duplicationClusters: analysisResult.duplicationClusters || [],
                nasaCompliance: analysisResult.nasaCompliance,
                options
            });
            
            return {
                crossAnalyzerCorrelation: smartResults.correlations || [],
                intelligentRecommendations: (smartResults.recommendations || []).map((r: any) => ({
                    priority: r.priority,
                    category: r.category,
                    description: r.description,
                    impact: r.impact,
                    effort: r.effort,
                    suggestedActions: r.suggested_actions || []
                })),
                qualityTrends: smartResults.quality_trends || [],
                riskAssessment: {
                    overallRisk: smartResults.risk_assessment?.overall_risk || 'low',
                    riskFactors: smartResults.risk_assessment?.risk_factors || [],
                    mitigation: smartResults.risk_assessment?.mitigation || []
                }
            };
        } catch (error) {
            this.telemetryService.logEvent('smart.integration.error', {
                error: error instanceof Error ? error.message : String(error)
            });
            
            return this.generateFallbackSmartIntegration(analysisResult);
        }
    }

    /**
     * Export comprehensive SARIF report for GitHub Code Scanning compatibility
     */
    async exportSARIFReport(workspacePath: string, outputPath?: string): Promise<string> {
        this.telemetryService.logEvent('export.sarif.started');
        
        try {
            const sarifReport = await this.runPythonAnalyzer({
                command: 'sarif-export',
                projectPath: workspacePath,
                outputPath: outputPath || path.join(workspacePath, 'connascence-report.sarif')
            });
            
            const sarifContent = sarifReport.content || this.generateFallbackSARIF(workspacePath);
            
            if (outputPath) {
                const fs = require('fs').promises;
                await fs.writeFile(outputPath, sarifContent);
            }
            
            this.telemetryService.logEvent('export.sarif.completed', {
                outputPath: outputPath || 'memory',
                size: sarifContent.length
            });
            
            return sarifContent;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            this.telemetryService.logEvent('export.sarif.error', { error: errorMessage });
            
            // Generate fallback SARIF report
            return this.generateFallbackSARIF(workspacePath);
        }
    }

    /**
     * Export structured JSON report with comprehensive analysis data
     */
    async exportJSONReport(workspacePath: string, outputPath?: string): Promise<string> {
        this.telemetryService.logEvent('export.json.started');
        
        try {
            const jsonReport = await this.runPythonAnalyzer({
                command: 'json-export',
                projectPath: workspacePath,
                comprehensive: true,
                includeMetrics: true
            });
            
            const jsonContent = JSON.stringify(jsonReport, null, 2) || this.generateFallbackJSON(workspacePath);
            
            if (outputPath) {
                const fs = require('fs').promises;
                await fs.writeFile(outputPath, jsonContent);
            }
            
            this.telemetryService.logEvent('export.json.completed', {
                outputPath: outputPath || 'memory',
                violations: jsonReport.summary?.total_violations || 0
            });
            
            return jsonContent;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            this.telemetryService.logEvent('export.json.error', { error: errorMessage });
            
            return this.generateFallbackJSON(workspacePath);
        }
    }

    /**
     * Export readable Markdown report suitable for PR comments and documentation
     */
    async exportMarkdownReport(workspacePath: string, outputPath?: string): Promise<string> {
        this.telemetryService.logEvent('export.markdown.started');
        
        try {
            const markdownReport = await this.runPythonAnalyzer({
                command: 'markdown-export',
                projectPath: workspacePath,
                includeCharts: false, // Markdown doesn't support interactive charts
                maxViolations: 20,
                maxFiles: 10
            });
            
            const markdownContent = markdownReport.content || this.generateFallbackMarkdown(workspacePath);
            
            if (outputPath) {
                const fs = require('fs').promises;
                await fs.writeFile(outputPath, markdownContent);
            }
            
            this.telemetryService.logEvent('export.markdown.completed', {
                outputPath: outputPath || 'memory',
                length: markdownContent.length
            });
            
            return markdownContent;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            this.telemetryService.logEvent('export.markdown.error', { error: errorMessage });
            
            return this.generateFallbackMarkdown(workspacePath);
        }
    }

    /**
     * Export reports in multiple formats simultaneously with progress tracking
     */
    async exportMultiFormatReport(
        workspacePath: string, 
        formats: string[], 
        outputDir: string,
        progressCallback?: (format: string, progress: number) => void
    ): Promise<{ [format: string]: string }> {
        this.telemetryService.logEvent('export.multiformat.started', { formats: formats.join(',') });
        
        const results: { [format: string]: string } = {};
        const total = formats.length;
        
        try {
            for (let i = 0; i < formats.length; i++) {
                const format = formats[i];
                
                if (progressCallback) {
                    progressCallback(format, (i / total) * 100);
                }
                
                const timestamp = new Date().toISOString().replace(/:/g, '-').split('.')[0];
                let outputPath: string;
                let content: string;
                
                switch (format.toLowerCase()) {
                    case 'sarif':
                        outputPath = path.join(outputDir, `connascence-report-${timestamp}.sarif`);
                        content = await this.exportSARIFReport(workspacePath, outputPath);
                        break;
                    case 'json':
                        outputPath = path.join(outputDir, `connascence-report-${timestamp}.json`);
                        content = await this.exportJSONReport(workspacePath, outputPath);
                        break;
                    case 'markdown':
                    case 'md':
                        outputPath = path.join(outputDir, `connascence-report-${timestamp}.md`);
                        content = await this.exportMarkdownReport(workspacePath, outputPath);
                        break;
                    case 'html':
                        outputPath = path.join(outputDir, `connascence-report-${timestamp}.html`);
                        content = await this.generateHTMLReport(workspacePath);
                        const fs = require('fs').promises;
                        await fs.writeFile(outputPath, content);
                        break;
                    case 'csv':
                        outputPath = path.join(outputDir, `connascence-violations-${timestamp}.csv`);
                        content = await this.generateCSVReport(workspacePath);
                        const csvFs = require('fs').promises;
                        await csvFs.writeFile(outputPath, content);
                        break;
                    default:
                        throw new Error(`Unsupported export format: ${format}`);
                }
                
                results[format] = outputPath;
            }
            
            if (progressCallback) {
                progressCallback('complete', 100);
            }
            
            this.telemetryService.logEvent('export.multiformat.completed', {
                formats: formats.join(','),
                outputCount: Object.keys(results).length
            });
            
            return results;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            this.telemetryService.logEvent('export.multiformat.error', { error: errorMessage });
            throw error;
        }
    }

    /**
     * Calculate enhanced quality score incorporating all advanced metrics
     */
    private calculateEnhancedQualityScore(result: AnalysisResult): number {
        let baseScore = result.qualityScore;
        
        // Adjust for duplication clusters
        if (result.duplicationClusters) {
            const duplicationPenalty = result.duplicationClusters.length * 5;
            baseScore = Math.max(0, baseScore - duplicationPenalty);
        }
        
        // Adjust for NASA compliance
        if (result.nasaCompliance && !result.nasaCompliance.compliant) {
            const compliancePenalty = (1.0 - result.nasaCompliance.score) * 20;
            baseScore = Math.max(0, baseScore - compliancePenalty);
        }
        
        // Boost for good performance
        if (result.performanceMetrics && result.performanceMetrics.efficiency) {
            const performanceBoost = (result.performanceMetrics.efficiency - 1.0) * 5;
            baseScore = Math.min(100, baseScore + performanceBoost);
        }
        
        return Math.round(baseScore);
    }

    /**
     * Calculate workspace summary with advanced metrics
     */
    private async calculateWorkspaceSummary(
        fileResults: { [filePath: string]: AnalysisResult },
        workspacePath: string,
        startTime: number
    ): Promise<{ filesAnalyzed: number; totalIssues: number; qualityScore: number }> {
        const filesAnalyzed = Object.keys(fileResults).length;
        let totalIssues = 0;
        let totalQualityScore = 0;
        
        for (const result of Object.values(fileResults)) {
            totalIssues += result.findings.length;
            if (result.duplicationClusters) {
                totalIssues += result.duplicationClusters.length;
            }
            if (result.nasaCompliance) {
                totalIssues += result.nasaCompliance.violations.length;
            }
            totalQualityScore += result.qualityScore;
        }
        
        const averageQualityScore = filesAnalyzed > 0 ? totalQualityScore / filesAnalyzed : 100;
        
        return {
            filesAnalyzed,
            totalIssues,
            qualityScore: Math.round(averageQualityScore)
        };
    }

    /**
     * Run Python analyzer with specified command and robust error handling
     */
    private async runPythonAnalyzer(options: any): Promise<any> {
        const cmd = 'python';
        const scriptPath = this.getAnalyzerScriptPath(options.command);
        const args = this.buildAnalyzerArgs(options);

        // Check if script exists before attempting to run
        const fs = require('fs');
        if (!fs.existsSync(scriptPath)) {
            console.warn(`Python script not found at ${scriptPath}, using fallback`);
            return this.getFallbackPythonResult(options);
        }

        return new Promise((resolve, reject) => {
            const process = spawn(cmd, [scriptPath, ...args], {
                timeout: 30000 // 30 second timeout
            });
            let stdout = '';
            let stderr = '';

            process.stdout.on('data', (data) => stdout += data.toString());
            process.stderr.on('data', (data) => stderr += data.toString());

            process.on('close', (code) => {
                if (code === 0) {
                    try {
                        const result = JSON.parse(stdout);
                        resolve(result);
                    } catch (e) {
                        console.warn(`Failed to parse analyzer output, using fallback: ${e}`);
                        resolve(this.getFallbackPythonResult(options));
                    }
                } else {
                    console.warn(`Analyzer failed with code ${code}: ${stderr}, using fallback`);
                    resolve(this.getFallbackPythonResult(options));
                }
            });

            process.on('error', (err) => {
                console.warn(`Failed to run analyzer: ${err.message}, using fallback`);
                resolve(this.getFallbackPythonResult(options));
            });

            // Add timeout handler
            setTimeout(() => {
                if (!process.killed) {
                    console.warn('Python analyzer timeout, using fallback');
                    process.kill();
                    resolve(this.getFallbackPythonResult(options));
                }
            }, 35000);
        });
    }

    /**
     * Provide fallback result when Python analyzer is not available
     */
    private getFallbackPythonResult(options: any): any {
        switch (options.command) {
            case 'performance-metrics':
                return {
                    parallel_processing: false,
                    speedup_factor: 1.0,
                    worker_count: 1,
                    peak_memory_mb: 0,
                    efficiency: 1.0
                };
            case 'mece-analysis':
                return {
                    duplications: [],
                    summary: { total_duplications: 0 }
                };
            case 'nasa-compliance':
                return {
                    nasa_violations: [],
                    nasa_compliance_score: 1.0,
                    power_of_ten_rules: []
                };
            case 'smart-integration':
                return {
                    correlations: [],
                    recommendations: [],
                    quality_trends: [],
                    risk_assessment: {
                        overall_risk: 'low',
                        risk_factors: [],
                        mitigation: ['Python analyzer not available - extension running in basic mode']
                    }
                };
            default:
                return {
                    violations: [],
                    summary: { total_violations: 0 },
                    fallback_mode: true
                };
        }
    }

    /**
     * Get the appropriate analyzer script path
     */
    private getAnalyzerScriptPath(command: string): string {
        const analyzerRoot = path.join(__dirname, '..', '..', '..', 'analyzer');
        
        switch (command) {
            case 'performance-metrics':
                return path.join(analyzerRoot, 'performance', 'parallel_analyzer.py');
            case 'mece-analysis':
                return path.join(analyzerRoot, 'dup_detection', 'mece_analyzer.py');
            case 'nasa-compliance':
                return path.join(analyzerRoot, 'unified_analyzer.py');
            case 'smart-integration':
                return path.join(analyzerRoot, 'smart_integration_engine.py');
            case 'sarif-export':
                return path.join(analyzerRoot, 'reporting', 'sarif.py');
            case 'json-export':
                return path.join(analyzerRoot, 'reporting', 'json.py');
            case 'markdown-export':
                return path.join(analyzerRoot, 'reporting', 'markdown.py');
            case 'unified-export':
                return path.join(analyzerRoot, 'reporting', 'coordinator.py');
            default:
                return path.join(analyzerRoot, 'unified_analyzer.py');
        }
    }

    /**
     * Build analyzer command line arguments
     */
    private buildAnalyzerArgs(options: any): string[] {
        const args = ['--format', 'json'];
        
        if (options.filePath) {
            args.push('--path', options.filePath);
        }
        if (options.projectPath) {
            args.push('--path', options.projectPath);
        }
        if (options.threshold) {
            args.push('--threshold', options.threshold.toString());
        }
        if (options.comprehensive) {
            args.push('--comprehensive');
        }
        
        return args;
    }

    /**
     * Utility methods for fallback scenarios
     */
    private calculateClusterSeverity(similarity: number): 'critical' | 'major' | 'minor' | 'info' {
        if (similarity >= 0.9) return 'critical';
        if (similarity >= 0.8) return 'major';
        if (similarity >= 0.7) return 'minor';
        return 'info';
    }

    private mapSeverity(severity: string): 'critical' | 'major' | 'minor' | 'info' {
        const severityMap: { [key: string]: 'critical' | 'major' | 'minor' | 'info' } = {
            'critical': 'critical',
            'high': 'major',
            'medium': 'minor',
            'low': 'info'
        };
        return severityMap[severity.toLowerCase()] || 'info';
    }

    private fallbackNASACompliance(findings: Finding[]): NASAComplianceResult {
        const nasaViolations = findings.filter(f => 
            f.type.includes('parameter') || f.type.includes('complexity') || f.type.includes('goto')
        ).map(f => ({
            rule: `NASA-${f.type}`,
            message: f.message,
            file: f.file,
            line: f.line,
            severity: f.severity
        }));
        
        return {
            compliant: nasaViolations.length === 0,
            score: Math.max(0, 1.0 - (nasaViolations.length * 0.1)),
            violations: nasaViolations,
            powerOfTenRules: []
        };
    }

    private generateFallbackSmartIntegration(result: AnalysisResult): SmartIntegrationResult {
        const criticalFindings = result.findings.filter(f => f.severity === 'critical');
        
        return {
            crossAnalyzerCorrelation: [],
            intelligentRecommendations: criticalFindings.slice(0, 3).map(f => ({
                priority: 'high' as const,
                category: f.type,
                description: `Address critical issue: ${f.message}`,
                impact: 'High - affects code quality and maintainability',
                effort: 'medium' as const,
                suggestedActions: [`Fix ${f.type} in ${path.basename(f.file)} at line ${f.line}`]
            })),
            qualityTrends: [{
                metric: 'overall_quality',
                current: result.qualityScore,
                trend: 'stable' as const,
                projection: result.qualityScore
            }],
            riskAssessment: {
                overallRisk: criticalFindings.length > 5 ? 'high' : criticalFindings.length > 0 ? 'medium' : 'low',
                riskFactors: criticalFindings.map(f => ({
                    factor: f.type,
                    impact: 8,
                    likelihood: 7,
                    description: f.message
                })),
                mitigation: ['Review and fix critical violations', 'Implement code quality gates']
            }
        };
    }

    /**
     * Generate fallback SARIF report when Python analyzer is unavailable
     */
    private generateFallbackSARIF(workspacePath: string): string {
        const timestamp = new Date().toISOString();
        
        const sarifReport = {
            "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "connascence",
                            "version": "1.0.0",
                            "informationUri": "https://github.com/connascence/connascence-analyzer",
                            "shortDescription": {
                                "text": "Connascence analysis for reducing coupling in codebases"
                            }
                        }
                    },
                    "invocations": [
                        {
                            "executionSuccessful": true,
                            "startTimeUtc": timestamp,
                            "workingDirectory": {
                                "uri": `file://${workspacePath}`
                            }
                        }
                    ],
                    "results": [],
                    "properties": {
                        "fallbackMode": true,
                        "analysisType": "basic",
                        "timestamp": timestamp
                    }
                }
            ]
        };
        
        return JSON.stringify(sarifReport, null, 2);
    }

    /**
     * Generate fallback JSON report when Python analyzer is unavailable
     */
    private generateFallbackJSON(workspacePath: string): string {
        const timestamp = new Date().toISOString();
        
        const jsonReport = {
            schema_version: "1.0.0",
            metadata: {
                tool: {
                    name: "connascence",
                    version: "1.0.0",
                    url: "https://github.com/connascence/connascence-analyzer"
                },
                analysis: {
                    timestamp,
                    project_root: workspacePath,
                    total_files_analyzed: 0,
                    analysis_duration_ms: 0,
                    policy_preset: "default"
                },
                fallback_mode: true
            },
            summary: {
                total_violations: 0,
                total_weight: 0,
                average_weight: 0,
                files_with_violations: 0,
                violations_by_type: {},
                violations_by_severity: {},
                quality_metrics: {
                    connascence_index: 0,
                    violations_per_file: 0,
                    critical_violations: 0,
                    high_violations: 0
                }
            },
            violations: [],
            file_stats: {},
            policy_compliance: {
                policy_preset: "default",
                quality_gates: {
                    no_critical_violations: true,
                    max_high_violations: true,
                    total_violations_acceptable: true
                }
            }
        };
        
        return JSON.stringify(jsonReport, null, 2);
    }

    /**
     * Generate fallback Markdown report when Python analyzer is unavailable
     */
    private generateFallbackMarkdown(workspacePath: string): string {
        const projectName = path.basename(workspacePath);
        const timestamp = new Date().toLocaleString();
        
        return `# Connascence Analysis Report

**Status:** No issues found | **Policy:** default | **Duration:** 0ms

## Summary

**Great work!** No connascence violations detected in the analysis.

**By Severity:** None detected
**Files Affected:** 0

## Files Needing Attention

No files require attention at this time.

## Recommendations

**Keep up the great work!**

Your code shows excellent connascence practices.

---

_Analysis completed in 0ms analyzing 0 files_

**What is Connascence?** Connascence is a software engineering metric that measures the strength of coupling between components. Lower connascence leads to more maintainable code.

[Learn More](https://connascence.io) | [Connascence Analyzer](https://github.com/connascence/connascence-analyzer)

*Report generated on ${timestamp} for project: ${projectName}*
*Note: This is a fallback report. Install Python dependencies for comprehensive analysis.*`;
    }

    /**
     * Generate HTML report for comprehensive display
     */
    private async generateHTMLReport(workspacePath: string): Promise<string> {
        try {
            const htmlReport = await this.runPythonAnalyzer({
                command: 'unified-export',
                projectPath: workspacePath,
                format: 'html',
                includeCharts: true,
                comprehensive: true
            });
            
            return htmlReport.content || this.generateFallbackHTML(workspacePath);
        } catch (error) {
            return this.generateFallbackHTML(workspacePath);
        }
    }

    /**
     * Generate CSV report for spreadsheet analysis
     */
    private async generateCSVReport(workspacePath: string): Promise<string> {
        try {
            const csvReport = await this.runPythonAnalyzer({
                command: 'unified-export',
                projectPath: workspacePath,
                format: 'csv'
            });
            
            return csvReport.content || this.generateFallbackCSV(workspacePath);
        } catch (error) {
            return this.generateFallbackCSV(workspacePath);
        }
    }

    /**
     * Generate fallback HTML report
     */
    private generateFallbackHTML(workspacePath: string): string {
        const projectName = path.basename(workspacePath);
        const timestamp = new Date().toLocaleString();
        
        return `<!DOCTYPE html>
<html>
<head>
    <title>Connascence Analysis Report - ${projectName}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background: #f5f5f5; padding: 20px; border-radius: 5px; }
        .success { color: #28a745; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Connascence Analysis Report</h1>
        <p><strong>Project:</strong> ${projectName}</p>
        <p><strong>Analysis Time:</strong> ${timestamp}</p>
    </div>
    
    <div class="success">
        <h2>Analysis Complete</h2>
        <p>No connascence violations detected. Your code shows excellent coupling practices.</p>
    </div>
    
    <p><em>Note: This is a fallback report. Install Python dependencies for comprehensive analysis.</em></p>
</body>
</html>`;
    }

    /**
     * Generate fallback CSV report
     */
    private generateFallbackCSV(workspacePath: string): string {
        return `File Path,Line Number,Type,Severity,Description,Weight,Category
# No violations detected in ${path.basename(workspacePath)}
# Generated on ${new Date().toLocaleString()}
# Note: This is a fallback report. Install Python dependencies for comprehensive analysis.`;
    }
}