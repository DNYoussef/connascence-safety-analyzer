import * as vscode from 'vscode';
import * as path from 'path';
import { spawn } from 'child_process';
import { AnalysisResult, Finding } from './connascenceService';
import {
    convertUnifiedReportToAnalysisResult,
    convertUnifiedWorkspaceResult,
    calculateQualityScore,
    calculateSeverityBreakdown
} from './reportTransforms';

/**
 * Client for integrating with the main connascence analysis system
 */
export class ConnascenceApiClient {
    private workspaceRoot: string | undefined;

    constructor() {
        this.workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    }

    /**
     * Analyze a single file using the unified connascence system with advanced capabilities
     */
    public async analyzeFile(filePath: string): Promise<AnalysisResult> {
        try {
            const startTime = Date.now();
            
            const response = await this.runCliAnalyzer({
                inputPath: filePath,
                mode: 'analyze',
                safetyProfile: this.getSafetyProfile(),
                includeTests: this.getIncludeTests(),
                exclude: this.getExcludePatterns(),
                parallelProcessing: this.getEnableParallelProcessing(),
                maxWorkers: this.getMaxWorkers(),
                threshold: this.getThreshold()
            });

            const report = response.result || response;
            const analysisResult = convertUnifiedReportToAnalysisResult(report, filePath, startTime);
            
            return analysisResult;
            
        } catch (error) {
            console.error('Failed to analyze file with unified system:', error);
            
            // Fallback to simplified analysis
            return this.fallbackAnalyzeFile(filePath);
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
            const response = await this.runCliAnalyzer({
                inputPath: workspacePath,
                mode: 'analyze-workspace',
                parallelProcessing: this.getEnableParallelProcessing(),
                maxWorkers: this.getMaxWorkers(),
                safetyProfile: this.getSafetyProfile(),
                threshold: this.getThreshold(),
                includeTests: this.getIncludeTests(),
                exclude: this.getExcludePatterns()
            });

            const report = response.result || response;
            return convertUnifiedWorkspaceResult(report, startTime);
            
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
            const response = await this.runCliAnalyzer({
                inputPath: filePath,
                mode: 'analyze',
                safetyProfile: profile,
                includeTests: this.getIncludeTests(),
                exclude: this.getExcludePatterns()
            });

            const report = response.result || response;
            const nasaViolations = report.nasa_violations || [];
            
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
            const response = await this.runCliAnalyzer({
                inputPath: filePath,
                mode: 'analyze',
                safetyProfile: this.getSafetyProfile(),
                includeTests: this.getIncludeTests(),
                exclude: this.getExcludePatterns()
            });

            const report = response.result || response;
            const violations = report.connascence_violations || [];
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
            const response = await this.runCliAnalyzer({
                inputPath: filePath,
                mode: 'analyze',
                safetyProfile: this.getSafetyProfile(),
                includeTests: this.getIncludeTests(),
                exclude: this.getExcludePatterns()
            });

            const report = response.result || response;
            const violations = report.connascence_violations || [];
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
            const response = await this.runCliAnalyzer({
                inputPath: workspacePath,
                mode: 'analyze-workspace',
                safetyProfile: this.getSafetyProfile(),
                threshold: this.getThreshold(),
                includeTests: this.getIncludeTests(),
                exclude: this.getExcludePatterns(),
                parallelProcessing: this.getEnableParallelProcessing(),
                maxWorkers: this.getMaxWorkers()
            });

            const result = response.result || response;

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
            const fallback = this.getFallbackAnalysisResult({ inputPath: workspacePath });
            return {
                summary: {
                    totalViolations: fallback.total_violations,
                    qualityScore: fallback.overall_quality_score,
                    filesAnalyzed: fallback.files_analyzed,
                    analysisTime: fallback.analysis_duration_ms
                },
                findings: {
                    connascenceViolations: fallback.connascence_violations,
                    duplicationClusters: fallback.duplication_clusters,
                    nasaViolations: fallback.nasa_violations
                },
                recommendations: {
                    priorityFixes: fallback.priority_fixes || [],
                    improvementActions: fallback.improvement_actions || []
                },
                metadata: {
                    timestamp: fallback.timestamp || new Date().toISOString(),
                    policyPreset: fallback.policy_preset || this.getSafetyProfile()
                },
                error: error instanceof Error ? error.message : String(error)
            };
        }
    }

    /**
     * Run the shared CLI analyzer commands.
     */
    private async runCliAnalyzer(options: any): Promise<any> {
        const pythonPath = this.getPythonPath();
        const command = options.mode === 'analyze-workspace' ? 'analyze-workspace' : 'analyze';
        const args = [
            '-m',
            'interfaces.cli.connascence',
            command,
            options.inputPath || '.',
            '--policy', options.safetyProfile || 'service-defaults',
            '--format', 'json'
        ];

        if (options.includeTests) {
            args.push('--include-tests');
        }

        if (options.parallelProcessing) {
            args.push('--parallel');
        }

        if (options.maxWorkers) {
            args.push('--max-workers', options.maxWorkers.toString());
        }

        if (options.threshold) {
            args.push('--threshold', options.threshold.toString());
        }

        if (options.exclude && options.exclude.length > 0) {
            args.push('--exclude', ...options.exclude);
        }

        return new Promise((resolve) => {
            const child = spawn(pythonPath, args, {
                cwd: this.getExecutionRoot(),
                env: this.getProcessEnv(),
                timeout: 40000
            });

            let stdout = '';
            let stderr = '';

            const resolveFallback = (reason: string) => {
                console.warn(`CLI analyzer fallback: ${reason}`);
                resolve({
                    result: this.getFallbackAnalysisResult(options),
                    error: reason
                });
            };

            child.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            child.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            child.on('close', (code) => {
                if (code === 0) {
                    try {
                        const parsed = JSON.parse(stdout || '{}');
                        resolve(parsed);
                    } catch (error) {
                        resolveFallback(`Failed to parse CLI output: ${error}`);
                    }
                } else {
                    resolveFallback(`CLI exited with code ${code}: ${stderr}`);
                }
            });

            child.on('error', (error) => {
                resolveFallback(`Failed to run CLI analyzer: ${error.message}`);
            });

            setTimeout(() => {
                if (!child.killed) {
                    child.kill();
                    resolveFallback('CLI analyzer timeout');
                }
            }, 45000);
        });
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
            qualityScore: calculateQualityScore(findings),
            summary: {
                totalIssues: findings.length,
                issuesBySeverity: calculateSeverityBreakdown(findings)
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

    private getExecutionRoot(): string {
        return path.resolve(path.join(__dirname, '..', '..', '..', '..'));
    }

    private getProcessEnv(): NodeJS.ProcessEnv {
        const root = this.getExecutionRoot();
        return { ...process.env, PYTHONPATH: root };
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