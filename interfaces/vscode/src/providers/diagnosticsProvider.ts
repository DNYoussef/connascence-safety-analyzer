import * as vscode from 'vscode';
import {
    ConnascenceService,
    AnalysisResult,
    Finding,
    NormalizedAnalysisEvent,
    NormalizedFinding
} from '../services/connascenceService';
import { AnalysisCache } from '../utils/cache';

interface DiagnosticsCacheEntry {
    result: AnalysisResult;
    normalizedFindings: NormalizedFinding[];
}

export class ConnascenceDiagnosticsProvider {
    private diagnosticsCollection: vscode.DiagnosticCollection;
    private cache = new AnalysisCache();
    private disposables: vscode.Disposable[] = [];
    private suppressedEventFiles = new Set<string>();

    constructor(private connascenceService: ConnascenceService) {
        this.diagnosticsCollection = vscode.languages.createDiagnosticCollection('connascence');
        const subscription = this.connascenceService.onAnalysisCompleted(event => {
            if (this.suppressedEventFiles.has(event.filePath)) {
                return;
            }
            void this.handleAnalysisEvent(event);
        });
        this.disposables.push(subscription);
    }

    async updateDiagnostics(uri: vscode.Uri, results: AnalysisResult): Promise<void> {
        const normalized = this.connascenceService.getNormalizedFindings(uri.fsPath);
        if (normalized && normalized.length > 0) {
            await this.applyNormalizedDiagnostics(uri, normalized, results);
            return;
        }

        const fallback = this.buildFallbackNormalized(results.findings, uri);
        await this.applyNormalizedDiagnostics(uri, fallback, results);
    }

    async updateFile(document: vscode.TextDocument): Promise<void> {
        if (!this.isSupportedLanguage(document.languageId)) {
            return;
        }

        try {
            this.suppressedEventFiles.add(document.fileName);
            const results = await this.connascenceService.analyzeFile(document.fileName);
            const normalized = this.connascenceService.getNormalizedFindings(document.fileName)
                ?? this.buildFallbackNormalized(results.findings, document.uri);
            await this.applyNormalizedDiagnostics(document.uri, normalized, results);
        } catch (error) {
            console.error('Failed to update diagnostics:', error);
            // Clear diagnostics on error
            this.diagnosticsCollection.set(document.uri, []);
        } finally {
            this.suppressedEventFiles.delete(document.fileName);
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
        const entry = await this.cache.getCachedResult(uri.fsPath) as DiagnosticsCacheEntry | undefined;
        return entry?.result;
    }

    dispose(): void {
        this.diagnosticsCollection.dispose();
        this.cache.clear();
        for (const disposable of this.disposables) {
            disposable.dispose();
        }
        this.disposables = [];
    }

    private findingsToDiagnostics(findings: Finding[], uri: vscode.Uri): vscode.Diagnostic[] {
        return findings.map(finding => this.findingToDiagnostic(finding, uri));
    }

    private findingToDiagnostic(finding: Finding, uri: vscode.Uri): vscode.Diagnostic {
        const line = Math.max(0, finding.line - 1); // VS Code uses 0-based line numbers
        const character = Math.max(0, (finding.column || 1) - 1);

        // Create range - try to be smart about the end position
        const range = this.createDiagnosticRange(line, character, finding.type);

        const message = this.formatDiagnosticMessage(finding);

        const diagnostic = new vscode.Diagnostic(
            range,
            message,
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
            const normalized = this.connascenceService.getNormalizedFindings(uri.fsPath)
                ?? this.buildFallbackNormalized(results.findings, uri);
            const diagnostics = this.findingsToDiagnostics(normalized, uri);
            await this.cache.setCachedResult(uri.fsPath, {
                result: results,
                normalizedFindings: normalized
            });
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

        const entries = this.cache.values() as DiagnosticsCacheEntry[];
        for (const entry of entries) {
            totalFindings += entry.normalizedFindings.length;

            for (const finding of entry.normalizedFindings) {
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
            const entry = this.cache.get(filePath) as DiagnosticsCacheEntry | undefined;
            if (!entry) continue;

            const uri = vscode.Uri.file(filePath);
            let filteredFindings = entry.normalizedFindings;

            if (severityFilter && severityFilter.length > 0) {
                filteredFindings = filteredFindings.filter((f: Finding) =>
                    severityFilter.includes(f.severity)
                );
            }

            if (typeFilter && typeFilter.length > 0) {
                filteredFindings = filteredFindings.filter((f: Finding) =>
                    typeFilter.some(type => f.type.includes(type) || (f as NormalizedFinding).normalizedType?.includes(type))
                );
            }

            const diagnostics = this.findingsToDiagnostics(filteredFindings, uri);
            this.diagnosticsCollection.set(uri, diagnostics);
        }
    }

    private async handleAnalysisEvent(event: NormalizedAnalysisEvent): Promise<void> {
        try {
            const uri = vscode.Uri.file(event.filePath);
            await this.applyNormalizedDiagnostics(uri, event.normalizedFindings, event.result);
        } catch (error) {
            console.error('Failed to apply diagnostics from normalized findings:', error);
        }
    }

    private async applyNormalizedDiagnostics(
        uri: vscode.Uri,
        normalizedFindings: NormalizedFinding[],
        result: AnalysisResult
    ): Promise<void> {
        const diagnostics = this.findingsToDiagnostics(normalizedFindings, uri);
        this.diagnosticsCollection.set(uri, diagnostics);
        await this.cache.setCachedResult(uri.fsPath, {
            result,
            normalizedFindings
        });
    }

    private buildFallbackNormalized(findings: Finding[], uri: vscode.Uri): NormalizedFinding[] {
        const backend = this.connascenceService.getHealthStatus().backend;
        return findings.map(finding => ({
            ...finding,
            normalizedType: finding.type,
            emoji: '🔗',
            category: 'general',
            backend,
            fileUri: uri,
            rawSeverity: finding.severity
        }));
    }

    private formatDiagnosticMessage(finding: Finding): string {
        const normalized = finding as Partial<NormalizedFinding>;
        if (normalized.emoji) {
            return `${normalized.emoji} ${finding.message}`;
        }
        return finding.message;
    }
}