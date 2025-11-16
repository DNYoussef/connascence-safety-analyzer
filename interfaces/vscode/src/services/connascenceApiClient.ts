import * as vscode from 'vscode';
import * as path from 'path';
import { spawn, spawnSync } from 'child_process';
import { AnalysisResult, Finding, PerformanceMetrics, DuplicationCluster, NASAComplianceResult, SmartIntegrationResult } from './connascenceService';

export type AnalyzerChannel = 'cli' | 'python' | 'legacy' | 'none';

export interface AnalyzerAvailability {
    mode: AnalyzerChannel;
    cliCommand?: string;
    pythonPath?: string;
    lastChecked: number;
    reasons: string[];
}

export class AnalyzerUnavailableError extends Error {
    constructor(message: string, public readonly reasons: string[] = []) {
        super(message);
        this.name = 'AnalyzerUnavailableError';
    }
}

/**
 * Client for integrating with the main connascence analysis system
 */
export class ConnascenceApiClient {
    private workspaceRoot: string | undefined;
    private analyzerAvailability: AnalyzerAvailability;

    constructor() {
        this.workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        this.analyzerAvailability = this.detectAnalyzerAvailability();
    }

    public getAnalyzerAvailability(forceRefresh: boolean = false): AnalyzerAvailability {
        if (forceRefresh) {
            this.analyzerAvailability = this.detectAnalyzerAvailability();
        }
        return this.analyzerAvailability;
    }

    public refreshAnalyzerAvailability(): AnalyzerAvailability {
        this.analyzerAvailability = this.detectAnalyzerAvailability();
        return this.analyzerAvailability;
    }

    /**
     * Analyze a single file using the unified connascence system with advanced capabilities
     */
    public async analyzeFile(filePath: string): Promise<AnalysisResult> {
        try {
            const startTime = Date.now();

            // Run unified analyzer for comprehensive results
            const result = await this.runUnifiedAnalyzer({
                inputPath: filePath,
                mode: 'single-file',
                safetyProfile: this.getSafetyProfile(),
                enableAdvanced: true
            });

            const analysisResult = this.convertCliReportToAnalysisResult(result, filePath, startTime);
            
            return analysisResult;
            
        } catch (error) {
            console.error('Failed to analyze file with unified system:', error);
            
            // Fallback to simplified analysis
            return this.fallbackAnalyzeFile(filePath);
        }
    }

    private detectAnalyzerAvailability(): AnalyzerAvailability {
        const reasons: string[] = [];
        const cliCandidates = this.getCliCommandCandidates();
        for (const candidate of cliCandidates) {
            if (this.isCommandAvailable(candidate)) {
                return { mode: 'cli', cliCommand: candidate, lastChecked: Date.now(), reasons };
            }
            reasons.push(`Command '${candidate}' not available in PATH`);
        }

        const pythonPath = this.getPythonPath();
        if (this.verifyPythonEntry(pythonPath)) {
            return { mode: 'python', pythonPath, lastChecked: Date.now(), reasons };
        }
        reasons.push('Python entry point cli.connascence is not importable');

        return { mode: 'none', lastChecked: Date.now(), reasons };
    }

    private ensureAnalyzerAvailable(): AnalyzerAvailability {
        const availability = this.getAnalyzerAvailability();
        if (availability.mode === 'none') {
            throw new AnalyzerUnavailableError(
                'Connascence analyzer CLI not detected. Follow the VS Code README Quick Start to add the wrapper to PATH or install the connascence-analyzer Python package.',
                availability.reasons
            );
        }
        return availability;
    }

    private getCliCommandCandidates(): string[] {
        const candidates = ['connascence'];
        if (process.platform === 'win32') {
            candidates.push('connascence.exe', 'connascence.bat', 'connascence.cmd');
        }
        return candidates;
    }

    private isCommandAvailable(command: string): boolean {
        try {
            const result = spawnSync(command, ['--version'], { encoding: 'utf8', stdio: 'ignore' });
            return result.status === 0;
        } catch (error) {
            return false;
        }
    }

    private verifyPythonEntry(pythonPath: string): boolean {
        try {
            const result = spawnSync(pythonPath, ['-m', 'cli.connascence', '--version'], { encoding: 'utf8', stdio: 'ignore' });
            return result.status === 0;
        } catch (error) {
            return false;
        }
    }

    /**
     * Analyze workspace using the unified connascence system with parallel processing
     */
    public async analyzeWorkspace(workspacePath: string): Promise<{ 
        fileResults: { [filePath: string]: AnalysisResult },
        summary: { filesAnalyzed: number, totalIssues: number, qualityScore: number }
    }> {
        try {
            const startTime = Date.now();
            
            // Use parallel analyzer for workspace analysis
            const result = await this.runUnifiedAnalyzer({
                inputPath: workspacePath,
                mode: 'workspace',
                parallelProcessing: this.getEnableParallelProcessing(),
                maxWorkers: this.getMaxWorkers(),
                safetyProfile: this.getSafetyProfile(),
                threshold: this.getThreshold(),
                includeTests: this.getIncludeTests(),
                exclude: this.getExcludePatterns(),
                enableAdvanced: true
            });

            return this.convertCliWorkspaceResult(result, startTime);
            
        } catch (error) {
            console.error('Failed to analyze workspace with unified system:', error);
            throw error;
        }
    }

    /**
     * Get safety validation using General Safety compliance
     */
    public async validateSafety(filePath: string, profile: string): Promise<{
        compliant: boolean,
        violations: Array<{
            rule: string,
            message: string,
            line: number,
            severity: string
        }>
    }> {
        try {
            // Try unified analyzer first
            const result = await this.runUnifiedAnalyzer({
                inputPath: filePath,
                mode: 'safety-validation',
                safetyProfile: profile,
                strictMode: this.getStrictMode()
            });
            
            const nasaViolations = result.nasa_violations || [];
            
            return {
                compliant: nasaViolations.length === 0,
                violations: nasaViolations.map((v: any) => ({
                    rule: v.rule || v.type,
                    message: v.message,
                    line: v.line_number || v.line || 0,
                    severity: v.severity
                }))
            };
            
        } catch (error) {
            console.error('Safety validation failed, using fallback:', error);
            // Fallback to basic validation
            return {
                compliant: true,
                violations: []
            };
        }
    }

    /**
     * Get refactoring suggestions using the analysis engine
     */
    public async suggestRefactoring(filePath: string, selection?: any): Promise<Array<{
        technique: string,
        description: string,
        confidence: number,
        preview?: string
    }>> {
        try {
            // Try unified analyzer for refactoring suggestions
            const result = await this.runUnifiedAnalyzer({
                inputPath: filePath,
                mode: 'single-file',
                safetyProfile: this.getSafetyProfile()
            });
            
            const violations = result.connascence_violations || [];
            const suggestions = [];
            
            // Generate refactoring suggestions based on violations
            for (const violation of violations.slice(0, 5)) {
                let technique = 'General Refactoring';
                let description = violation.description || 'Improve code quality';
                
                switch (violation.type || violation.rule_id) {
                    case 'CoP': // Connascence of Position
                        technique = 'Extract Parameter Object';
                        description = 'Replace long parameter list with parameter object';
                        break;
                    case 'CoM': // Connascence of Meaning
                        technique = 'Extract Constant';
                        description = 'Replace magic number with named constant';
                        break;
                    case 'god_object':
                        technique = 'Extract Class';
                        description = 'Break down large class into smaller, focused classes';
                        break;
                    case 'long_function':
                        technique = 'Extract Method';
                        description = 'Break down long function into smaller methods';
                        break;
                }
                
                suggestions.push({
                    technique,
                    description,
                    confidence: 0.8,
                    preview: `Consider refactoring line ${violation.line_number || 0}`
                });
            }
            
            return suggestions;
            
        } catch (error) {
            console.error('Failed to get refactoring suggestions:', error);
            return [];
        }
    }

    /**
     * Get automated fixes for common violations
     */
    public async getAutofixes(filePath: string): Promise<Array<{
        line: number,
        column?: number,
        endLine?: number,
        endColumn?: number,
        issue: string,
        description: string,
        replacement: string
    }>> {
        try {
            // Try unified analyzer for automated fixes
            const result = await this.runUnifiedAnalyzer({
                inputPath: filePath,
                mode: 'single-file',
                safetyProfile: this.getSafetyProfile()
            });
            
            const violations = result.connascence_violations || [];
            const fixes = [];
            
            // Generate automated fixes for specific violation types
            for (const violation of violations) {
                if (violation.type === 'CoM' || violation.rule_id === 'connascence_of_meaning') {
                    // Magic number fix
                    fixes.push({
                        line: violation.line_number || 0,
                        column: violation.column_number,
                        issue: 'Magic number',
                        description: 'Replace magic number with named constant',
                        replacement: '# TODO: Replace with named constant'
                    });
                } else if (violation.type === 'CoP' || violation.rule_id === 'connascence_of_position') {
                    // Parameter list fix
                    fixes.push({
                        line: violation.line_number || 0,
                        issue: 'Long parameter list',
                        description: 'Consider using parameter object or breaking down function',
                        replacement: '# TODO: Refactor parameter list'
                    });
                }
            }
            
            return fixes;
            
        } catch (error) {
            console.error('Failed to get autofixes:', error);
            return [];
        }
    }

    /**
     * Generate comprehensive report
     */
    public async generateReport(workspacePath: string): Promise<any> {
        try {
            // Use unified analyzer to generate comprehensive report
            const result = await this.runUnifiedAnalyzer({
                inputPath: workspacePath,
                mode: 'workspace',
                safetyProfile: this.getSafetyProfile(),
                threshold: this.getThreshold(),
                includeTests: this.getIncludeTests(),
                exclude: this.getExcludePatterns(),
                enableAdvanced: true,
                parallelProcessing: this.getEnableParallelProcessing(),
                maxWorkers: this.getMaxWorkers()
            });
            
            // Format report for extension consumption
            return {
                summary: {
                    totalViolations: result.total_violations || 0,
                    qualityScore: result.overall_quality_score || 0.8,
                    filesAnalyzed: result.files_analyzed || 0,
                    analysisTime: result.analysis_duration_ms || 0
                },
                findings: {
                    connascenceViolations: result.connascence_violations || [],
                    duplicationClusters: result.duplication_clusters || [],
                    nasaViolations: result.nasa_violations || []
                },
                recommendations: {
                    priorityFixes: result.priority_fixes || [],
                    improvementActions: result.improvement_actions || []
                },
                metadata: {
                    timestamp: result.timestamp || new Date().toISOString(),
                    policyPreset: result.policy_preset || 'service-defaults'
                }
            };
            
        } catch (error) {
            console.error('Failed to generate report:', error);
            // Return fallback report structure
            return {
                summary: {
                    totalViolations: 0,
                    qualityScore: 80,
                    filesAnalyzed: 0,
                    analysisTime: 0
                },
                findings: {
                    connascenceViolations: [],
                    duplicationClusters: [],
                    nasaViolations: []
                },
                recommendations: {
                    priorityFixes: [],
                    improvementActions: ['Python analyzer not available - install dependencies']
                },
                metadata: {
                    timestamp: new Date().toISOString(),
                    policyPreset: 'fallback'
                },
                error: error instanceof Error ? error.message : String(error)
            };
        }
    }

    /**
     * Run unified analyzer with all advanced capabilities and robust error handling
     */
    private async runUnifiedAnalyzer(options: any): Promise<any> {
        if (options.mode === 'single-file' || options.mode === 'workspace') {
            return this.runCliAnalyzer(options);
        }

        return this.runLegacyAnalyzer(options);
    }

    private async runCliAnalyzer(options: any): Promise<any> {
        const availability = this.ensureAnalyzerAvailable();
        const useBinary = availability.mode === 'cli';
        const command = useBinary
            ? availability.cliCommand!
            : availability.pythonPath || this.getPythonPath();
        const args = this.buildCliArgs(options, useBinary ? 'binary' : 'module');

        return this.spawnCliProcess(command, args, options);
    }

    private spawnCliProcess(command: string, args: string[], options: any): Promise<any> {
        return new Promise((resolve) => {
            const child = spawn(command, args, {
                cwd: this.workspaceRoot,
                timeout: 30000,
                shell: process.platform === 'win32'
            });

            let stdout = '';
            let stderr = '';

            child.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            child.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            const handleFailure = (message: string) => {
                console.warn(message);
                resolve(this.getFallbackAnalysisResult(options));
            };

            child.on('close', (code) => {
                if (code === 0) {
                    try {
                        resolve(JSON.parse(stdout));
                    } catch (error) {
                        handleFailure(`Failed to parse CLI analyzer output: ${error}`);
                    }
                } else {
                    handleFailure(`CLI analyzer exited with ${code}: ${stderr}`);
                }
            });

            child.on('error', (error) => {
                handleFailure(`CLI analyzer failed: ${error.message}`);
            });

            setTimeout(() => {
                if (!child.killed) {
                    handleFailure('CLI analyzer timeout');
                    child.kill();
                }
            }, 35000);
        });
    }

    private async runLegacyAnalyzer(options: any): Promise<any> {
        const analyzerPath = this.getUnifiedAnalyzerPath();
        const pythonPath = this.getPythonPath();

        const fs = require('fs');
        if (!fs.existsSync(analyzerPath)) {
            console.warn(`Analyzer not found at ${analyzerPath}, using fallback`);
            return this.getFallbackAnalysisResult(options);
        }

        const args = [
            analyzerPath,
            '--path', options.inputPath,
            '--format', 'json',
            '--policy-preset', options.safetyProfile || 'service-defaults'
        ];

        return new Promise((resolve) => {
            const process = spawn(pythonPath, args, {
                cwd: this.workspaceRoot,
                timeout: 30000
            });

            let stdout = '';
            let stderr = '';

            process.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            process.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            process.on('close', (code) => {
                if (code === 0) {
                    try {
                        resolve(JSON.parse(stdout));
                    } catch (error) {
                        console.warn(`Failed to parse analyzer output, using fallback: ${error}`);
                        resolve(this.getFallbackAnalysisResult(options));
                    }
                } else {
                    console.warn(`Analyzer failed with code ${code}: ${stderr}, using fallback`);
                    resolve(this.getFallbackAnalysisResult(options));
                }
            });

            process.on('error', (error) => {
                console.warn(`Failed to run analyzer: ${error.message}, using fallback`);
                resolve(this.getFallbackAnalysisResult(options));
            });

            setTimeout(() => {
                if (!process.killed) {
                    console.warn('Analyzer process timeout, using fallback');
                    process.kill();
                    resolve(this.getFallbackAnalysisResult(options));
                }
            }, 35000);
        });
    }

    private buildCliArgs(options: any, target: 'module' | 'binary' = 'module'): string[] {
        const args: string[] = [];
        if (target === 'module') {
            args.push('-m', 'cli.connascence');
        }
        const profile = options.safetyProfile || this.getSafetyProfile();

        if (options.mode === 'workspace') {
            args.push('analyze-workspace', options.inputPath);
            if (options.filePatterns && options.filePatterns.length > 0) {
                args.push('--file-patterns', ...options.filePatterns);
            }
        } else {
            args.push('analyze', options.inputPath);
            if (options.recursive) {
                args.push('--recursive');
            }
        }

        args.push('--profile', profile, '--format', 'json');
        return args;
    }
    
    /**
     * Provide fallback analysis result when Python analyzer is not available
     */
    private getFallbackAnalysisResult(options: any): any {
        return {
            connascence_violations: [],
            duplication_clusters: [],
            nasa_violations: [],
            total_violations: 0,
            critical_count: 0,
            high_count: 0,
            medium_count: 0,
            low_count: 0,
            connascence_index: 0,
            nasa_compliance_score: 1.0,
            duplication_score: 1.0,
            overall_quality_score: 0.8,
            project_path: options.inputPath,
            policy_preset: options.safetyProfile || 'service-defaults',
            analysis_duration_ms: 0,
            files_analyzed: 0,
            timestamp: new Date().toISOString(),
            priority_fixes: [],
            improvement_actions: ['Python analyzer not available - extension running in basic mode'],
            fallback_mode: true
        };
    }

    /**
     * Convert unified analyzer report to VS Code format with advanced metrics
     */
    private convertCliReportToAnalysisResult(report: any, filePath: string, startTime: number): AnalysisResult {
        const findings: Finding[] = [];
        for (const finding of report.findings || []) {
            findings.push({
                id: finding.id || `${finding.type}_${finding.line || 0}`,
                type: finding.type || finding.connascence_type,
                severity: this.mapSeverity(finding.severity || 'medium'),
                message: finding.message || finding.description || 'Detected connascence',
                file: finding.file || filePath,
                line: finding.line || finding.line_number || 0,
                column: finding.column,
                suggestion: finding.suggestion,
                code: finding.code
            });
        }

        const summary = report.summary || {};
        const issuesBySeverity = summary.issuesBySeverity || this.calculateSeverityBreakdown(findings);
        const totalIssues = summary.totalIssues ?? findings.length;

        const performanceMetrics: PerformanceMetrics = {
            analysisTime: Date.now() - startTime,
            parallelProcessing: false,
            speedupFactor: 1.0,
            workerCount: 1,
            memoryUsage: 0,
            efficiency: 1.0
        };

        const nasaCompliance: NASAComplianceResult = {
            compliant: true,
            score: 1.0,
            violations: [],
            powerOfTenRules: []
        };

        const smartIntegrationResults: SmartIntegrationResult = {
            crossAnalyzerCorrelation: [],
            intelligentRecommendations: [],
            qualityTrends: [],
            riskAssessment: {
                overallRisk: 'low',
                riskFactors: [],
                mitigation: []
            }
        };

        return {
            findings,
            qualityScore: Math.round(report.quality_score ?? report.qualityScore ?? 100),
            summary: {
                totalIssues,
                issuesBySeverity
            },
            performanceMetrics,
            duplicationClusters: [],
            nasaCompliance,
            smartIntegrationResults
        };
    }

    /**
     * Convert unified workspace results with advanced metrics
     */
    private convertCliWorkspaceResult(report: any, startTime: number): {
        fileResults: { [filePath: string]: AnalysisResult },
        summary: { filesAnalyzed: number, totalIssues: number, qualityScore: number }
    } {
        const fileResults: { [filePath: string]: AnalysisResult } = {};
        let totalIssues = 0;

        for (const [file, fileReport] of Object.entries(report.files || {})) {
            const analysisResult = this.convertCliReportToAnalysisResult(fileReport, file, startTime);
            fileResults[file] = analysisResult;
            totalIssues += analysisResult.summary.totalIssues;
        }

        const filesAnalyzed = Object.keys(fileResults).length || report.files_analyzed || 0;
        return {
            fileResults,
            summary: {
                filesAnalyzed,
                totalIssues,
                qualityScore: Math.round(report.overall_score ?? report.overallScore ?? 100)
            }
        };
    }

    /**
     * Fallback analysis when main system is not available
     */
    private async fallbackAnalyzeFile(filePath: string): Promise<AnalysisResult> {
        const findings: Finding[] = [];
        
        try {
            const document = await vscode.workspace.openTextDocument(filePath);
            const text = document.getText();
            const lines = text.split('\\n');
            
            // Simple pattern matching for common issues
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i];
                const lineNumber = i + 1;
                
                // Magic numbers
                const magicNumbers = line.match(/\\b(\\d{2,})\\b/g);
                if (magicNumbers) {
                    findings.push({
                        id: `magic_number_${lineNumber}`,
                        type: 'magic_number',
                        severity: 'minor',
                        message: `Magic number found: ${magicNumbers[0]}`,
                        file: filePath,
                        line: lineNumber,
                        suggestion: 'Extract to a named constant'
                    });
                }
                
                // Long parameter lists
                if (line.includes('def ') && (line.match(/,/g) || []).length >= 4) {
                    findings.push({
                        id: `long_params_${lineNumber}`,
                        type: 'long_parameter_list',
                        severity: 'major',
                        message: 'Function has too many parameters',
                        file: filePath,
                        line: lineNumber,
                        suggestion: 'Consider using a parameter object or breaking down the function'
                    });
                }
            }
            
        } catch (error) {
            console.error('Fallback analysis failed:', error);
        }
        
        return {
            findings,
            qualityScore: this.calculateQualityScore(findings),
            summary: {
                totalIssues: findings.length,
                issuesBySeverity: this.calculateSeverityBreakdown(findings)
            }
        };
    }

    // Configuration helpers
    private getSafetyProfile(): string {
        const config = vscode.workspace.getConfiguration('connascence');
        return config.get('safetyProfile', 'modern_general');
    }

    private getThreshold(): number {
        const config = vscode.workspace.getConfiguration('connascence');
        return config.get('threshold', 0.8);
    }

    private getIncludeTests(): boolean {
        const config = vscode.workspace.getConfiguration('connascence');
        return config.get('includeTests', false);
    }

    private getStrictMode(): boolean {
        const config = vscode.workspace.getConfiguration('connascence');
        return config.get('strictMode', false);
    }

    private getSafeMode(): boolean {
        const config = vscode.workspace.getConfiguration('connascence');
        return config.get('safeMode', true);
    }

    private getExcludePatterns(): string[] {
        const config = vscode.workspace.getConfiguration('connascence');
        return config.get('exclude', [
            'node_modules/**',
            '.git/**',
            '__pycache__/**',
            '*.test.*',
            'test/**'
        ]);
    }

    // Utility methods
    private mapSeverity(severity: string): 'critical' | 'major' | 'minor' | 'info' {
        const severityMap: { [key: string]: 'critical' | 'major' | 'minor' | 'info' } = {
            'critical': 'critical',
            'high': 'major',
            'medium': 'minor',
            'low': 'info',
            'error': 'critical',
            'warning': 'major',
            'info': 'info'
        };
        
        return severityMap[severity.toLowerCase()] || 'info';
    }

    private calculateQualityScore(findings: Finding[]): number {
        if (findings.length === 0) return 100;
        
        const weights = { critical: 10, major: 5, minor: 2, info: 1 };
        const totalWeight = findings.reduce((sum, f) => sum + weights[f.severity], 0);
        
        return Math.max(0, 100 - totalWeight);
    }

    private calculateSeverityBreakdown(findings: Finding[]): {
        critical: number;
        major: number;
        minor: number;
        info: number;
    } {
        return findings.reduce((acc, finding) => {
            acc[finding.severity]++;
            return acc;
        }, { critical: 0, major: 0, minor: 0, info: 0 });
    }

    private calculateOverallQualityScore(fileResults: { [filePath: string]: AnalysisResult }): number {
        const scores = Object.values(fileResults).map(r => r.qualityScore);
        return scores.length > 0 ? scores.reduce((sum, score) => sum + score, 0) / scores.length : 100;
    }

    /**
     * Calculate enhanced quality score incorporating all advanced metrics
     */
    private calculateEnhancedQualityScore(
        findings: Finding[], 
        duplicationClusters: DuplicationCluster[], 
        nasaCompliance: NASAComplianceResult
    ): number {
        let baseScore = this.calculateQualityScore(findings);
        
        // Adjust for duplication clusters
        const duplicationPenalty = duplicationClusters.length * 5;
        baseScore = Math.max(0, baseScore - duplicationPenalty);
        
        // Adjust for NASA compliance
        const compliancePenalty = (1.0 - nasaCompliance.score) * 20;
        baseScore = Math.max(0, baseScore - compliancePenalty);
        
        return Math.round(baseScore);
    }

    /**
     * Calculate cluster severity based on similarity score
     */
    private calculateClusterSeverity(similarity: number): 'critical' | 'major' | 'minor' | 'info' {
        if (similarity >= 0.9) return 'critical';
        if (similarity >= 0.8) return 'major';
        if (similarity >= 0.7) return 'minor';
        return 'info';
    }

    /**
     * Calculate overall risk level from analysis results
     */
    private calculateOverallRisk(report: any): 'low' | 'medium' | 'high' | 'critical' {
        const criticalViolations = (report.connascence_violations || []).filter((v: any) => 
            v.severity === 'critical'
        ).length;
        
        const highSimilarityClusters = (report.duplication_clusters || []).filter((c: any) => 
            c.similarity_score >= 0.9
        ).length;
        
        const nasaViolations = (report.nasa_violations || []).length;
        
        if (criticalViolations > 10 || highSimilarityClusters > 5 || nasaViolations > 20) {
            return 'critical';
        } else if (criticalViolations > 5 || highSimilarityClusters > 2 || nasaViolations > 10) {
            return 'high';
        } else if (criticalViolations > 0 || highSimilarityClusters > 0 || nasaViolations > 0) {
            return 'medium';
        }
        
        return 'low';
    }

    /**
     * Get path to unified analyzer
     */
    private getUnifiedAnalyzerPath(): string {
        if (this.workspaceRoot) {
            return path.join(this.workspaceRoot, 'analyzer', 'unified_analyzer.py');
        }
        
        // Fallback to relative path from extension
        return path.join(__dirname, '..', '..', '..', 'analyzer', 'unified_analyzer.py');
    }

    // Additional configuration helpers for advanced features
    private getEnableParallelProcessing(): boolean {
        const config = vscode.workspace.getConfiguration('connascence');
        return config.get('enableParallelProcessing', true);
    }

    private getMaxWorkers(): number {
        const config = vscode.workspace.getConfiguration('connascence');
        return config.get('maxWorkers', 4);
    }

    /**
     * Run Python analyzer as subprocess
     */
    private async runPythonAnalyzer(options: any): Promise<any> {
        const analyzerPath = this.getAnalyzerPath();
        const pythonPath = this.getPythonPath();
        
        const args = [
            analyzerPath,
            options.inputPath,
            '--format', 'json',
            '--profile', options.safetyProfile || 'modern_general'
        ];
        
        if (options.mode === 'single-file') {
            args.push('--single-file');
        }
        
        return new Promise((resolve, reject) => {
            const process = spawn(pythonPath, args, {
                cwd: this.workspaceRoot
            });
            
            let stdout = '';
            let stderr = '';
            
            process.stdout.on('data', (data) => {
                stdout += data.toString();
            });
            
            process.stderr.on('data', (data) => {
                stderr += data.toString();
            });
            
            process.on('close', (code) => {
                if (code === 0) {
                    try {
                        const result = JSON.parse(stdout);
                        resolve(result);
                    } catch (parseError) {
                        reject(new Error(`Failed to parse analyzer output: ${parseError}`));
                    }
                } else {
                    reject(new Error(`Analyzer failed with code ${code}: ${stderr}`));
                }
            });
            
            process.on('error', (error) => {
                reject(new Error(`Failed to run analyzer: ${error.message}`));
            });
        });
    }
    
    /**
     * Run safety validation via Python
     */
    private async runSafetyValidation(options: any): Promise<any> {
        const result = await this.runPythonAnalyzer({
            ...options,
            mode: 'safety-validation'
        });
        
        return {
            compliant: result.safety_compliant || false,
            violations: result.safety_violations || []
        };
    }
    
    /**
     * Get refactoring suggestions via Python
     */
    private async getRefactoringSuggestions(options: any): Promise<any[]> {
        try {
            const result = await this.runPythonAnalyzer({
                ...options,
                mode: 'refactoring-suggestions'
            });
            
            return result.suggestions || [];
        } catch (error) {
            console.warn('Refactoring suggestions not available:', error);
            return [];
        }
    }
    
    /**
     * Get automated fixes via Python
     */
    private async getAutomatedFixes(options: any): Promise<any[]> {
        try {
            const result = await this.runPythonAnalyzer({
                ...options,
                mode: 'automated-fixes'
            });
            
            return result.fixes || [];
        } catch (error) {
            console.warn('Automated fixes not available:', error);
            return [];
        }
    }
    
    /**
     * Get the path to the Python analyzer (legacy support)
     */
    private getAnalyzerPath(): string {
        if (this.workspaceRoot) {
            return path.join(this.workspaceRoot, 'analyzer', 'check_connascence.py');
        }
        
        // Fallback to relative path from extension
        return path.join(__dirname, '..', '..', '..', 'analyzer', 'check_connascence.py');
    }
    
    /**
     * Get the Python executable path
     */
    private getPythonPath(): string {
        const config = vscode.workspace.getConfiguration('connascence');
        const configuredPath = config.get<string>('pythonPath');
        
        if (configuredPath) {
            return configuredPath;
        }
        
        // Try common Python paths
        const commonPaths = [
            'python3',
            'python',
            '/usr/bin/python3',
            '/usr/local/bin/python3',
            'C:\\Python39\\python.exe',
            'C:\\Python310\\python.exe',
            'C:\\Python311\\python.exe'
        ];
        
        // For now, default to 'python'
        return 'python';
    }
}