import * as vscode from 'vscode';
import * as path from 'path';
import { spawn } from 'child_process';
import { AnalysisResult, Finding } from './connascenceService';

/**
 * Client for integrating with the main connascence analysis system
 */
export class ConnascenceApiClient {
    private workspaceRoot: string | undefined;

    constructor() {
        this.workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    }

    /**
     * Analyze a single file using the main connascence system
     */
    public async analyzeFile(filePath: string): Promise<AnalysisResult> {
        try {
            const result = await this.runPythonAnalyzer({
                inputPath: filePath,
                mode: 'single-file',
                safetyProfile: this.getSafetyProfile()
            });
            
            return this.convertReportToAnalysisResult(result, filePath);
            
        } catch (error) {
            console.error('Failed to analyze file with main system:', error);
            
            // Fallback to simplified analysis
            return this.fallbackAnalyzeFile(filePath);
        }
    }

    /**
     * Analyze workspace using the main connascence system
     */
    public async analyzeWorkspace(workspacePath: string): Promise<{ 
        fileResults: { [filePath: string]: AnalysisResult },
        summary: { filesAnalyzed: number, totalIssues: number, qualityScore: number }
    }> {
        try {
            const { generateConnascenceReport } = await this.loadConnascenceSystem();
            
            const options = {
                inputPath: workspacePath,
                outputPath: path.join(workspacePath, '.connascence-report.json'),
                format: 'json' as const,
                verbose: false,
                includeTests: this.getIncludeTests(),
                safetyProfile: this.getSafetyProfile(),
                threshold: this.getThreshold(),
                exclude: this.getExcludePatterns()
            };

            const report = await generateConnascenceReport(options);
            return this.convertReportToWorkspaceResult(report);
            
        } catch (error) {
            console.error('Failed to analyze workspace with main system:', error);
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
            const { validateSafetyCompliance } = await this.loadConnascenceSystem();
            
            const result = await validateSafetyCompliance({
                filePath,
                profile,
                strictMode: this.getStrictMode()
            });
            
            return {
                compliant: result.compliant,
                violations: result.violations.map((v: any) => ({
                    rule: v.rule || v.type,
                    message: v.message,
                    line: v.line,
                    severity: v.severity
                }))
            };
            
        } catch (error) {
            console.error('Safety validation failed:', error);
            throw error;
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
            const { getRefactoringSuggestions } = await this.loadConnascenceSystem();
            
            const suggestions = await getRefactoringSuggestions({
                filePath,
                selection,
                maxSuggestions: 5
            });
            
            return suggestions.map((s: any) => ({
                technique: s.technique,
                description: s.description,
                confidence: s.confidence,
                preview: s.preview
            }));
            
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
            const { getAutomatedFixes } = await this.loadConnascenceSystem();
            
            const fixes = await getAutomatedFixes({
                filePath,
                safeMode: this.getSafeMode()
            });
            
            return fixes.map((f: any) => ({
                line: f.line,
                column: f.column,
                endLine: f.endLine,
                endColumn: f.endColumn,
                issue: f.issue,
                description: f.description,
                replacement: f.replacement
            }));
            
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
            const { generateConnascenceReport } = await this.loadConnascenceSystem();
            
            const options = {
                inputPath: workspacePath,
                outputPath: path.join(workspacePath, '.connascence-report.json'),
                format: 'json' as const,
                verbose: true,
                includeTests: this.getIncludeTests(),
                safetyProfile: this.getSafetyProfile(),
                threshold: this.getThreshold(),
                exclude: this.getExcludePatterns(),
                generateMetrics: true,
                includeRecommendations: true
            };

            return await generateConnascenceReport(options);
            
        } catch (error) {
            console.error('Failed to generate report:', error);
            throw error;
        }
    }

    /**
     * Load the main connascence analysis system via Python subprocess
     */
    private async loadConnascenceSystem(): Promise<any> {
        // Use Python subprocess to run the analyzer
        return {
            generateConnascenceReport: this.runPythonAnalyzer.bind(this),
            validateSafetyCompliance: this.runSafetyValidation.bind(this),
            getRefactoringSuggestions: this.getRefactoringSuggestions.bind(this),
            getAutomatedFixes: this.getAutomatedFixes.bind(this)
        };
    }

    /**
     * Convert main system report to VS Code format
     */
    private convertReportToAnalysisResult(report: any, filePath: string): AnalysisResult {
        const findings: Finding[] = [];
        
        if (report.findings) {
            for (const finding of report.findings) {
                // Only include findings for the requested file
                if (finding.file && path.resolve(finding.file) === path.resolve(filePath)) {
                    findings.push({
                        id: finding.id || `${finding.type}_${finding.line}`,
                        type: finding.type,
                        severity: this.mapSeverity(finding.severity),
                        message: finding.message,
                        file: finding.file,
                        line: finding.line,
                        column: finding.column,
                        suggestion: finding.suggestion || finding.recommendation
                    });
                }
            }
        }
        
        return {
            findings,
            qualityScore: report.qualityScore || this.calculateQualityScore(findings),
            summary: {
                totalIssues: findings.length,
                issuesBySeverity: this.calculateSeverityBreakdown(findings)
            }
        };
    }

    /**
     * Convert report to workspace result format
     */
    private convertReportToWorkspaceResult(report: any): {
        fileResults: { [filePath: string]: AnalysisResult },
        summary: { filesAnalyzed: number, totalIssues: number, qualityScore: number }
    } {
        const fileResults: { [filePath: string]: AnalysisResult } = {};
        let totalIssues = 0;
        
        // Group findings by file
        if (report.findings) {
            const findingsByFile = new Map<string, any[]>();
            
            for (const finding of report.findings) {
                const file = finding.file || 'unknown';
                if (!findingsByFile.has(file)) {
                    findingsByFile.set(file, []);
                }
                findingsByFile.get(file)!.push(finding);
            }
            
            // Convert each file's findings
            for (const [file, findings] of findingsByFile) {
                const convertedFindings: Finding[] = findings.map(f => ({
                    id: f.id || `${f.type}_${f.line}`,
                    type: f.type,
                    severity: this.mapSeverity(f.severity),
                    message: f.message,
                    file: f.file,
                    line: f.line,
                    column: f.column,
                    suggestion: f.suggestion || f.recommendation
                }));
                
                fileResults[file] = {
                    findings: convertedFindings,
                    qualityScore: this.calculateQualityScore(convertedFindings),
                    summary: {
                        totalIssues: convertedFindings.length,
                        issuesBySeverity: this.calculateSeverityBreakdown(convertedFindings)
                    }
                };
                
                totalIssues += convertedFindings.length;
            }
        }
        
        return {
            fileResults,
            summary: {
                filesAnalyzed: Object.keys(fileResults).length,
                totalIssues,
                qualityScore: report.overallQualityScore || this.calculateOverallQualityScore(fileResults)
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
     * Get the path to the Python analyzer
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