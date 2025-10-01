import * as vscode from 'vscode';
import { exec } from 'child_process';
import { promisify } from 'util';
import * as path from 'path';

const execAsync = promisify(exec);

export interface Violation {
    type: string;
    severity: 'critical' | 'high' | 'medium' | 'low';
    file: string;
    line: number;
    column?: number;
    message: string;
    recommendation?: string;
}

export interface AnalysisResult {
    violations: Violation[];
    nasaCompliance?: number;
    duplications?: number;
    godObjects?: number;
    timestamp: Date;
    metrics?: {
        quality_score?: number;
        total_violations?: number;
        files_analyzed?: number;
        nasa_compliance_score?: number;
        mece_score?: number;
    };
}

export class ConnascenceAnalyzer {
    private lastResults: Map<string, AnalysisResult> = new Map();
    private context: vscode.ExtensionContext;

    constructor(context: vscode.ExtensionContext) {
        this.context = context;
    }

    async analyzeDocument(document: vscode.TextDocument): Promise<AnalysisResult> {
        const config = vscode.workspace.getConfiguration('connascence');
        const policy = config.get('policy', 'standard');

        try {
            const workspaceFolder = vscode.workspace.getWorkspaceFolder(document.uri);
            const cwd = workspaceFolder ? workspaceFolder.uri.fsPath : path.dirname(document.uri.fsPath);

            const { stdout } = await execAsync(
                `connascence scan "${document.uri.fsPath}" --policy ${policy} --format json`,
                { cwd }
            );

            const result = JSON.parse(stdout);
            const analysisResult: AnalysisResult = {
                violations: this.parseViolations(result),
                nasaCompliance: result.nasa_compliance,
                duplications: result.duplications?.length || 0,
                godObjects: result.god_objects?.length || 0,
                timestamp: new Date()
            };

            this.lastResults.set(document.uri.toString(), analysisResult);
            return analysisResult;

        } catch (error) {
            console.error('Analysis failed:', error);
            return {
                violations: [],
                timestamp: new Date()
            };
        }
    }

    private parseViolations(result: any): Violation[] {
        const violations: Violation[] = [];

        // Parse connascence violations
        if (result.connascence_violations) {
            for (const [type, items] of Object.entries(result.connascence_violations)) {
                if (Array.isArray(items)) {
                    items.forEach(item => {
                        violations.push({
                            type: type,
                            severity: this.getSeverity(type, item),
                            file: item.file || item.path,
                            line: item.line || item.line_number || 1,
                            column: item.column || item.col,
                            message: item.message || item.description || `${type} violation detected`,
                            recommendation: item.recommendation
                        });
                    });
                }
            }
        }

        // Parse duplication violations
        if (result.duplications) {
            result.duplications.forEach((dup: any) => {
                violations.push({
                    type: 'duplication',
                    severity: dup.severity || 'medium',
                    file: dup.file,
                    line: dup.line || 1,
                    message: `Code duplication detected: ${dup.similarity}% similar`,
                    recommendation: 'Consider extracting common code into a shared function'
                });
            });
        }

        return violations;
    }

    private getSeverity(type: string, item: any): 'critical' | 'high' | 'medium' | 'low' {
        if (item.severity) {
            return item.severity.toLowerCase() as any;
        }

        // Default severity based on type
        const severityMap: { [key: string]: 'critical' | 'high' | 'medium' | 'low' } = {
            'identity': 'critical',
            'meaning': 'high',
            'algorithm': 'high',
            'position': 'medium',
            'execution': 'medium',
            'timing': 'high',
            'values': 'low',
            'type': 'low',
            'convention': 'low'
        };

        return severityMap[type.toLowerCase()] || 'medium';
    }

    async getLastResults(): Promise<AnalysisResult> {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            return { violations: [], timestamp: new Date() };
        }

        const uri = editor.document.uri.toString();
        return this.lastResults.get(uri) || { violations: [], timestamp: new Date() };
    }

    async getAvailableFixes(uri: vscode.Uri): Promise<Fix[]> {
        const results = this.lastResults.get(uri.toString());
        if (!results) {
            return [];
        }

        const fixes: Fix[] = [];

        // Generate fixes for each violation
        for (const violation of results.violations) {
            if (this.canAutoFix(violation)) {
                fixes.push({
                    title: `Fix ${violation.type} violation`,
                    description: violation.message,
                    violation: violation,
                    edits: await this.generateFix(violation)
                });
            }
        }

        return fixes;
    }

    private canAutoFix(violation: Violation): boolean {
        const autoFixableTypes = ['convention', 'values', 'type', 'position'];
        return autoFixableTypes.includes(violation.type.toLowerCase());
    }

    private async generateFix(violation: Violation): Promise<vscode.TextEdit[]> {
        // This would call the autofix API
        try {
            const { stdout } = await execAsync(
                `connascence autofix --violation-id ${violation.type}:${violation.line} --dry-run --format json`,
                { cwd: path.dirname(violation.file) }
            );

            const fix = JSON.parse(stdout);
            return fix.edits.map((edit: any) => {
                const range = new vscode.Range(
                    new vscode.Position(edit.start.line - 1, edit.start.column || 0),
                    new vscode.Position(edit.end.line - 1, edit.end.column || 0)
                );
                return vscode.TextEdit.replace(range, edit.newText);
            });
        } catch {
            return [];
        }
    }

    async applyFixes(fixes: Fix[]): Promise<void> {
        const edit = new vscode.WorkspaceEdit();

        for (const fix of fixes) {
            const uri = vscode.Uri.file(fix.violation.file);
            fix.edits.forEach(textEdit => {
                edit.replace(uri, textEdit.range, textEdit.newText);
            });
        }

        await vscode.workspace.applyEdit(edit);
    }

    async getSuggestedFix(violation: any): Promise<Fix | null> {
        // Check if violation has a fix recommendation
        if (!violation || !violation.recommendation) {
            return null;
        }

        // Create a simple fix based on the recommendation
        const fix: Fix = {
            title: `Fix ${violation.type}`,
            description: violation.recommendation,
            violation: violation,
            edits: []
        };

        // In a real implementation, this would generate actual code edits
        // For now, return null as we don't have automated fix generation
        return null;
    }
}

export interface Fix {
    title: string;
    description: string;
    violation: Violation;
    edits: vscode.TextEdit[];
}