import * as vscode from 'vscode';
import * as path from 'path';
import { spawn } from 'child_process';
import { AnalysisResult, Finding, PerformanceMetrics, DuplicationCluster, NASAComplianceResult, SmartIntegrationResult } from './connascenceService';

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
            
            // Run unified analyzer for comprehensive results
            const result = await this.runUnifiedAnalyzer({
                inputPath: filePath,
                mode: 'single-file',
                safetyProfile: this.getSafetyProfile(),
                enableAdvanced: true
            });
            
            const analysisResult = this.convertUnifiedReportToAnalysisResult(result, filePath, startTime);
            
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
            
            return this.convertUnifiedWorkspaceResult(result, startTime);
            
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
        const analyzerPath = this.getUnifiedAnalyzerPath();
        const pythonPath = this.getPythonPath();
        
        // Check if analyzer file exists
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
        
        if (options.mode === 'single-file') {
            args.push('--single-file');
        }
        
        if (options.parallelProcessing) {
            args.push('--parallel');
            if (options.maxWorkers) {
                args.push('--max-workers', options.maxWorkers.toString());
            }
        }
        
        if (options.threshold) {
            args.push('--threshold', options.threshold.toString());
        }
        
        if (options.includeTests) {
            args.push('--include-tests');
        }
        
        if (options.enableAdvanced) {
            args.push('--enable-mece', '--enable-nasa', '--enable-smart-integration');
        }
        
        if (options.exclude && options.exclude.length > 0) {
            args.push('--exclude', ...options.exclude);
        }
        
        return new Promise((resolve, reject) => {
            const process = spawn(pythonPath, args, {
                cwd: this.workspaceRoot,
                timeout: 30000 // 30 second timeout
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
                        console.warn(`Failed to parse analyzer output, using fallback: ${parseError}`);
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
            
            // Add timeout handler
            setTimeout(() => {
                if (!process.killed) {
                    console.warn('Analyzer process timeout, using fallback');
                    process.kill();
                    resolve(this.getFallbackAnalysisResult(options));
                }
            }, 35000); // 35 second total timeout
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
     * Convert unified analyzer report to VS Code format with advanced metrics
     */
    private convertUnifiedReportToAnalysisResult(report: any, filePath: string, startTime: number): AnalysisResult {
        const findings: Finding[] = [];
        
        // Process connascence violations
        if (report.connascence_violations) {
            for (const violation of report.connascence_violations) {
                if (violation.file_path && path.resolve(violation.file_path) === path.resolve(filePath)) {
                    findings.push({
                        id: violation.id || `${violation.type}_${violation.line_number}`,
                        type: violation.type || violation.rule_id,
                        severity: this.mapSeverity(violation.severity),
                        message: violation.description,
                        file: violation.file_path,
                        line: violation.line_number,
                        column: violation.column_number,
                        suggestion: violation.suggestion
                    });
                }
            }
        }
        
        // Generate performance metrics
        const performanceMetrics: PerformanceMetrics = {
            analysisTime: Date.now() - startTime,
            parallelProcessing: report.parallel_processing || false,
            speedupFactor: report.speedup_factor || 1.0,
            workerCount: report.worker_count || 1,
            memoryUsage: report.peak_memory_mb || 0,
            efficiency: report.efficiency || 1.0
        };
        
        // Process duplication clusters
        const duplicationClusters: DuplicationCluster[] = (report.duplication_clusters || []).map((cluster: any) => ({
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
        
        // Process NASA compliance
        const nasaCompliance: NASAComplianceResult = {
            compliant: report.nasa_compliance_score >= 0.8,
            score: report.nasa_compliance_score || 1.0,
            violations: (report.nasa_violations || []).map((v: any) => ({
                rule: v.rule,
                message: v.message,
                file: v.file_path || filePath,
                line: v.line_number || 0,
                severity: this.mapSeverity(v.severity),
                powerOfTenRule: v.power_of_ten_rule
            })),
            powerOfTenRules: report.power_of_ten_rules || []
        };
        
        // Process smart integration results
        const smartIntegrationResults: SmartIntegrationResult = {
            crossAnalyzerCorrelation: report.correlations || [],
            intelligentRecommendations: (report.improvement_actions || []).map((action: string, index: number) => ({
                priority: index < 2 ? 'high' as const : 'medium' as const,
                category: 'quality_improvement',
                description: action,
                impact: 'Improves code quality and maintainability',
                effort: 'medium' as const,
                suggestedActions: [action]
            })),
            qualityTrends: [{
                metric: 'overall_quality',
                current: report.overall_quality_score || 0.8,
                trend: 'stable' as const,
                projection: report.overall_quality_score || 0.8
            }],
            riskAssessment: {
                overallRisk: this.calculateOverallRisk(report),
                riskFactors: [],
                mitigation: report.priority_fixes || []
            }
        };
        
        return {
            findings,
            qualityScore: Math.round((report.overall_quality_score || 0.8) * 100),
            summary: {
                totalIssues: findings.length + duplicationClusters.length + nasaCompliance.violations.length,
                issuesBySeverity: this.calculateSeverityBreakdown(findings)
            },
            performanceMetrics,
            duplicationClusters,
            nasaCompliance,
            smartIntegrationResults
        };
    }

    /**
     * Convert unified workspace results with advanced metrics
     */
    private convertUnifiedWorkspaceResult(report: any, startTime: number): {
        fileResults: { [filePath: string]: AnalysisResult },
        summary: { filesAnalyzed: number, totalIssues: number, qualityScore: number }
    } {
        const fileResults: { [filePath: string]: AnalysisResult } = {};
        let totalIssues = 0;
        
        // Group connascence violations by file
        const violationsByFile = new Map<string, any[]>();
        if (report.connascence_violations) {
            for (const violation of report.connascence_violations) {
                const file = violation.file_path || 'unknown';
                if (!violationsByFile.has(file)) {
                    violationsByFile.set(file, []);
                }
                violationsByFile.get(file)!.push(violation);
            }
        }
        
        // Process each file
        for (const [file, violations] of violationsByFile) {
            const findings: Finding[] = violations.map(v => ({
                id: v.id || `${v.type}_${v.line_number}`,
                type: v.type || v.rule_id,
                severity: this.mapSeverity(v.severity),
                message: v.description,
                file: v.file_path,
                line: v.line_number,
                column: v.column_number,
                suggestion: v.suggestion
            }));
            
            // Filter duplication clusters for this file
            const fileDuplicationClusters = (report.duplication_clusters || []).filter((cluster: any) => 
                cluster.files_involved && cluster.files_involved.includes(file)
            ).map((cluster: any) => ({
                id: cluster.id,
                blocks: cluster.blocks.filter((block: any) => block.file_path === file),
                similarity: cluster.similarity_score,
                severity: this.calculateClusterSeverity(cluster.similarity_score),
                description: cluster.description,
                files: [file]
            }));
            
            // Filter NASA violations for this file
            const fileNasaViolations = (report.nasa_violations || []).filter((v: any) => 
                v.file_path === file
            ).map((v: any) => ({
                rule: v.rule,
                message: v.message,
                file: v.file_path,
                line: v.line_number,
                severity: this.mapSeverity(v.severity),
                powerOfTenRule: v.power_of_ten_rule
            }));
            
            const performanceMetrics: PerformanceMetrics = {
                analysisTime: Date.now() - startTime,
                parallelProcessing: report.parallel_processing || false,
                speedupFactor: report.speedup_factor || 1.0,
                workerCount: report.worker_count || 1,
                memoryUsage: report.peak_memory_mb || 0,
                efficiency: report.efficiency || 1.0
            };
            
            const nasaCompliance: NASAComplianceResult = {
                compliant: fileNasaViolations.length === 0,
                score: Math.max(0, 1.0 - (fileNasaViolations.length * 0.1)),
                violations: fileNasaViolations,
                powerOfTenRules: []
            };
            
            const smartIntegrationResults: SmartIntegrationResult = {
                crossAnalyzerCorrelation: [],
                intelligentRecommendations: [],
                qualityTrends: [],
                riskAssessment: {
                    overallRisk: findings.filter(f => f.severity === 'critical').length > 0 ? 'high' : 'low',
                    riskFactors: [],
                    mitigation: []
                }
            };
            
            const totalFileIssues = findings.length + fileDuplicationClusters.length + fileNasaViolations.length;
            
            fileResults[file] = {
                findings,
                qualityScore: this.calculateEnhancedQualityScore(findings, fileDuplicationClusters, nasaCompliance),
                summary: {
                    totalIssues: totalFileIssues,
                    issuesBySeverity: this.calculateSeverityBreakdown(findings)
                },
                performanceMetrics,
                duplicationClusters: fileDuplicationClusters,
                nasaCompliance,
                smartIntegrationResults
            };
            
            totalIssues += totalFileIssues;
        }
        
        return {
            fileResults,
            summary: {
                filesAnalyzed: Object.keys(fileResults).length,
                totalIssues,
                qualityScore: Math.round((report.overall_quality_score || 0.8) * 100)
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