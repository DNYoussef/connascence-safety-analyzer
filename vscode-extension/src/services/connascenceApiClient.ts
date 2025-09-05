import * as vscode from 'vscode';
import * as path from 'path';
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
            // Import and use the existing analysis system from src/reports/
            const { generateConnascenceReport } = await this.loadConnascenceSystem();
            
            // Create a mock options object for single file analysis
            const options = {
                inputPath: filePath,
                outputPath: path.join(path.dirname(filePath), '.connascence-temp.json'),
                format: 'json' as const,
                verbose: false,
                includeTests: false,
                safetyProfile: this.getSafetyProfile(),
                threshold: this.getThreshold(),
                exclude: this.getExcludePatterns()
            };

            // Generate the report
            const report = await generateConnascenceReport(options);
            
            // Convert to VS Code format
            return this.convertReportToAnalysisResult(report, filePath);
            
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
     * Load the main connascence analysis system
     */
    private async loadConnascenceSystem(): Promise<any> {
        try {
            // Try to load from the main project
            const reportPath = this.workspaceRoot ? 
                path.join(this.workspaceRoot, 'src', 'reports', 'index.js') :
                undefined;
                
            if (reportPath) {
                return require(reportPath);
            }
            
            // Fallback: try to load from relative path
            const relativePath = path.join(__dirname, '..', '..', '..', 'src', 'reports', 'index.js');
            return require(relativePath);
            
        } catch (error) {
            console.error('Failed to load connascence system:', error);
            throw new Error('Main connascence analysis system not available');
        }
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
}