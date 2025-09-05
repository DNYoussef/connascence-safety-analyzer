import * as vscode from 'vscode';
import { ConnascenceService, AnalysisResult, Finding } from '../services/connascenceService';
import { AnalysisCache } from '../utils/cache';

export class ConnascenceDiagnosticsProvider {
    private diagnosticsCollection: vscode.DiagnosticCollection;
    private cache = new AnalysisCache();

    constructor(private connascenceService: ConnascenceService) {
        this.diagnosticsCollection = vscode.languages.createDiagnosticCollection('connascence');
    }

    async updateDiagnostics(uri: vscode.Uri, results: AnalysisResult): Promise<void> {
        const diagnostics = this.findingsToDiagnostics(results.findings, uri);
        this.diagnosticsCollection.set(uri, diagnostics);
        await this.cache.setCachedResult(uri.fsPath, results);
    }

    async updateFile(document: vscode.TextDocument): Promise<void> {
        if (!this.isSupportedLanguage(document.languageId)) {
            return;
        }

        try {
            const results = await this.connascenceService.analyzeFile(document.fileName);
            await this.updateDiagnostics(document.uri, results);
        } catch (error) {
            console.error('Failed to update diagnostics:', error);
            // Clear diagnostics on error
            this.diagnosticsCollection.set(document.uri, []);
        }
    }

    clearDiagnostics(uri: vscode.Uri): void {
        this.diagnosticsCollection.delete(uri);
        this.cache.delete(uri.fsPath);
    }

    clearAllDiagnostics(): void {
        this.diagnosticsCollection.clear();
        this.cache.clear();
    }

    getDiagnostics(uri: vscode.Uri): readonly vscode.Diagnostic[] {
        return this.diagnosticsCollection.get(uri) || [];
    }

    async getCachedResults(uri: vscode.Uri): Promise<AnalysisResult | undefined> {
        return await this.cache.getCachedResult(uri.fsPath);
    }

    dispose(): void {
        this.diagnosticsCollection.dispose();
        this.cache.clear();
    }

    private findingsToDiagnostics(findings: Finding[], uri: vscode.Uri): vscode.Diagnostic[] {
        return findings.map(finding => this.findingToDiagnostic(finding, uri));
    }

    private findingToDiagnostic(finding: Finding, uri: vscode.Uri): vscode.Diagnostic {
        const line = Math.max(0, finding.line - 1); // VS Code uses 0-based line numbers
        const character = Math.max(0, (finding.column || 1) - 1);
        
        // Create range - try to be smart about the end position
        const range = this.createDiagnosticRange(line, character, finding.type);
        
        const diagnostic = new vscode.Diagnostic(
            range,
            finding.message,
            this.severityToVSCodeSeverity(finding.severity)
        );

        diagnostic.code = {
            value: finding.id,
            target: vscode.Uri.parse(`https://docs.connascence.io/types/${finding.type}`)
        };
        diagnostic.source = 'connascence';

        // Add tags based on severity and type
        diagnostic.tags = this.getDiagnosticTags(finding);

        // Add related information if suggestion is available
        if (finding.suggestion) {
            diagnostic.relatedInformation = [
                new vscode.DiagnosticRelatedInformation(
                    new vscode.Location(uri, range),
                    `Suggestion: ${finding.suggestion}`
                )
            ];
        }

        return diagnostic;
    }

    private createDiagnosticRange(line: number, character: number, findingType: string): vscode.Range {
        // Default range length based on finding type
        let endCharacter = character + this.getDefaultRangeLength(findingType);
        
        return new vscode.Range(
            new vscode.Position(line, character),
            new vscode.Position(line, endCharacter)
        );
    }

    private getDefaultRangeLength(findingType: string): number {
        // Different finding types might have different typical lengths
        const typeLengths: { [key: string]: number } = {
            'magic_number': 5,
            'long_parameter_list': 20,
            'large_class': 15,
            'duplicate_code': 30,
            'complex_method': 25,
            'deep_nesting': 10
        };

        return typeLengths[findingType] || 15;
    }

    private severityToVSCodeSeverity(severity: string): vscode.DiagnosticSeverity {
        switch (severity.toLowerCase()) {
            case 'critical':
                return vscode.DiagnosticSeverity.Error;
            case 'major':
            case 'high':
                return vscode.DiagnosticSeverity.Warning;
            case 'minor':
            case 'medium':
                return vscode.DiagnosticSeverity.Information;
            case 'info':
            case 'low':
            default:
                return vscode.DiagnosticSeverity.Hint;
        }
    }

    private getDiagnosticTags(finding: Finding): vscode.DiagnosticTag[] {
        const tags: vscode.DiagnosticTag[] = [];

        // Mark critical issues as deprecated to make them stand out
        if (finding.severity === 'critical') {
            tags.push(vscode.DiagnosticTag.Deprecated);
        }

        // Mark certain types as unnecessary
        if (finding.type.includes('unused') || finding.type.includes('duplicate')) {
            tags.push(vscode.DiagnosticTag.Unnecessary);
        }

        return tags;
    }

    private isSupportedLanguage(languageId: string): boolean {
        return ['python', 'c', 'cpp', 'javascript', 'typescript'].includes(languageId);
    }

    // Batch operations for performance
    async updateMultipleDiagnostics(updates: { uri: vscode.Uri; results: AnalysisResult }[]): Promise<void> {
        const batch = await Promise.all(updates.map(async ({ uri, results }) => {
            const diagnostics = this.findingsToDiagnostics(results.findings, uri);
            await this.cache.setCachedResult(uri.fsPath, results);
            return { uri, diagnostics };
        }));

        // Apply all updates at once
        for (const { uri, diagnostics } of batch) {
            this.diagnosticsCollection.set(uri, diagnostics);
        }
    }

    // Statistics and reporting
    getStatistics(): {
        totalFiles: number;
        totalFindings: number;
        findingsBySeverity: { [severity: string]: number };
        findingsByType: { [type: string]: number };
    } {
        let totalFindings = 0;
        const findingsBySeverity: { [severity: string]: number } = {};
        const findingsByType: { [type: string]: number } = {};

        for (const results of this.cache.values()) {
            totalFindings += results.findings.length;
            
            for (const finding of results.findings) {
                findingsBySeverity[finding.severity] = (findingsBySeverity[finding.severity] || 0) + 1;
                findingsByType[finding.type] = (findingsByType[finding.type] || 0) + 1;
            }
        }

        return {
            totalFiles: this.cache.size(),
            totalFindings,
            findingsBySeverity,
            findingsByType
        };
    }

    // Filter diagnostics based on configuration
    applyFilter(severityFilter?: string[], typeFilter?: string[]): void {
        const keys = this.cache.keys();
        
        for (const filePath of keys) {
            const results = this.cache.get(filePath);
            if (!results) continue;
            
            const uri = vscode.Uri.file(filePath);
            let filteredFindings = results.findings;

            if (severityFilter && severityFilter.length > 0) {
                filteredFindings = filteredFindings.filter((f: Finding) => 
                    severityFilter.includes(f.severity)
                );
            }

            if (typeFilter && typeFilter.length > 0) {
                filteredFindings = filteredFindings.filter((f: Finding) => 
                    typeFilter.some(type => f.type.includes(type))
                );
            }

            const diagnostics = this.findingsToDiagnostics(filteredFindings, uri);
            this.diagnosticsCollection.set(uri, diagnostics);
        }
    }
}