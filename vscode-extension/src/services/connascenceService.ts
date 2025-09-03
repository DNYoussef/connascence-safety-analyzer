import * as vscode from 'vscode';
import * as path from 'path';
import { spawn } from 'child_process';
import { ConfigurationService } from './configurationService';
import { TelemetryService } from './telemetryService';
import { ConnascenceApiClient } from './connascenceApiClient';

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

    constructor(
        private configService: ConfigurationService,
        private telemetryService: TelemetryService
    ) {
        this.apiClient = new ConnascenceApiClient();
    }

    async analyzeFile(filePath: string): Promise<AnalysisResult> {
        this.telemetryService.logEvent('file.analysis.started', { file: path.basename(filePath) });
        
        try {
            // Use the integrated API client
            return await this.apiClient.analyzeFile(filePath);
        } catch (error) {
            this.telemetryService.logEvent('file.analysis.error', { error: error.message });
            throw error;
        }
    }

    async analyzeWorkspace(workspacePath: string): Promise<WorkspaceAnalysisResult> {
        this.telemetryService.logEvent('workspace.analysis.started');
        
        try {
            return await this.apiClient.analyzeWorkspace(workspacePath);
        } catch (error) {
            this.telemetryService.logEvent('workspace.analysis.error', { error: error.message });
            throw error;
        }
    }

    async validateSafety(filePath: string, profile: string): Promise<SafetyValidationResult> {
        this.telemetryService.logEvent('safety.validation.started', { profile });
        
        try {
            return await this.apiClient.validateSafety(filePath, profile);
        } catch (error) {
            this.telemetryService.logEvent('safety.validation.error', { error: error.message });
            throw error;
        }
    }

    async suggestRefactoring(filePath: string, selection?: { start: { line: number; character: number }, end: { line: number; character: number } }): Promise<RefactoringSuggestion[]> {
        this.telemetryService.logEvent('refactoring.suggestion.requested');
        
        try {
            return await this.apiClient.suggestRefactoring(filePath, selection);
        } catch (error) {
            this.telemetryService.logEvent('refactoring.suggestion.error', { error: error.message });
            throw error;
        }
    }

    async getAutofixes(filePath: string): Promise<AutoFix[]> {
        this.telemetryService.logEvent('autofix.requested');
        
        try {
            return await this.apiClient.getAutofixes(filePath);
        } catch (error) {
            this.telemetryService.logEvent('autofix.error', { error: error.message });
            throw error;
        }
    }

    async generateReport(workspacePath: string): Promise<any> {
        this.telemetryService.logEvent('report.generation.started');
        
        try {
            return await this.apiClient.generateReport(workspacePath);
        } catch (error) {
            this.telemetryService.logEvent('report.generation.error', { error: error.message });
            throw error;
        }
    }

    // MCP implementations
    private async analyzeMCP(filePath: string): Promise<AnalysisResult> {
        // TODO: Implement MCP analysis
        throw new Error('MCP analysis not yet implemented');
    }

    private async analyzeWorkspaceMCP(workspacePath: string): Promise<WorkspaceAnalysisResult> {
        // TODO: Implement MCP workspace analysis
        throw new Error('MCP workspace analysis not yet implemented');
    }

    private async validateSafetyMCP(filePath: string, profile: string): Promise<SafetyValidationResult> {
        // TODO: Implement MCP safety validation
        throw new Error('MCP safety validation not yet implemented');
    }

    private async suggestRefactoringMCP(filePath: string, selection?: any): Promise<RefactoringSuggestion[]> {
        // TODO: Implement MCP refactoring suggestions
        throw new Error('MCP refactoring suggestions not yet implemented');
    }

    private async getAutofixesMCP(filePath: string): Promise<AutoFix[]> {
        // TODO: Implement MCP autofixes
        throw new Error('MCP autofixes not yet implemented');
    }

    private async generateReportMCP(workspacePath: string): Promise<any> {
        // TODO: Implement MCP report generation
        throw new Error('MCP report generation not yet implemented');
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
                        reject(new Error(`Failed to parse CLI output: ${e.message}`));
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
                        reject(new Error(`Failed to parse CLI output: ${e.message}`));
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
                    reject(new Error(`Failed to parse safety validation output: ${e.message}`));
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
                        reject(new Error(`Failed to parse refactoring suggestions: ${e.message}`));
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
                        reject(new Error(`Failed to parse autofix output: ${e.message}`));
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
                        reject(new Error(`Failed to parse report output: ${e.message}`));
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
}