import * as vscode from 'vscode';
import { AnalysisResult, Violation } from './analyzer';

export class DiagnosticProvider implements vscode.Disposable {
    private diagnosticCollection: vscode.DiagnosticCollection;
    private analyzer: any;

    constructor(analyzer: any) {
        this.analyzer = analyzer;
        this.diagnosticCollection = vscode.languages.createDiagnosticCollection('connascence');
    }

    updateDiagnostics(uri: vscode.Uri, results: AnalysisResult): void {
        const diagnostics: vscode.Diagnostic[] = [];

        for (const violation of results.violations) {
            const diagnostic = this.createDiagnostic(violation);
            if (diagnostic) {
                diagnostics.push(diagnostic);
            }
        }

        this.diagnosticCollection.set(uri, diagnostics);
    }

    private createDiagnostic(violation: Violation): vscode.Diagnostic | null {
        try {
            const range = new vscode.Range(
                new vscode.Position(Math.max(0, violation.line - 1), violation.column || 0),
                new vscode.Position(Math.max(0, violation.line - 1), 999)
            );

            const diagnostic = new vscode.Diagnostic(
                range,
                violation.message,
                this.getSeverityLevel(violation.severity)
            );

            diagnostic.code = violation.type;
            diagnostic.source = 'connascence';

            if (violation.recommendation) {
                diagnostic.relatedInformation = [
                    new vscode.DiagnosticRelatedInformation(
                        new vscode.Location(vscode.Uri.file(violation.file), range),
                        `Recommendation: ${violation.recommendation}`
                    )
                ];
            }

            return diagnostic;
        } catch (error) {
            console.error('Failed to create diagnostic:', error);
            return null;
        }
    }

    private getSeverityLevel(severity: string): vscode.DiagnosticSeverity {
        switch (severity.toLowerCase()) {
            case 'critical':
            case 'error':
                return vscode.DiagnosticSeverity.Error;
            case 'high':
            case 'warning':
                return vscode.DiagnosticSeverity.Warning;
            case 'medium':
            case 'info':
                return vscode.DiagnosticSeverity.Information;
            case 'low':
            case 'hint':
                return vscode.DiagnosticSeverity.Hint;
            default:
                return vscode.DiagnosticSeverity.Information;
        }
    }

    clear(uri?: vscode.Uri): void {
        if (uri) {
            this.diagnosticCollection.delete(uri);
        } else {
            this.diagnosticCollection.clear();
        }
    }

    dispose(): void {
        this.diagnosticCollection.dispose();
    }
}