import * as vscode from 'vscode';
import { ConnascenceService } from '../services/connascenceService';

export class ConnascenceHoverProvider implements vscode.HoverProvider {
    constructor(private connascenceService: ConnascenceService) {}

    async provideHover(
        document: vscode.TextDocument,
        position: vscode.Position,
        token: vscode.CancellationToken
    ): Promise<vscode.Hover | null> {
        // Check if there's a diagnostic at this position
        const diagnostics = vscode.languages.getDiagnostics(document.uri);
        const connascenceDiagnostics = diagnostics.filter(d => 
            d.source === 'connascence' && d.range.contains(position)
        );

        if (connascenceDiagnostics.length === 0) {
            return null;
        }

        const diagnostic = connascenceDiagnostics[0];
        const contents = await this.createHoverContent(diagnostic, document, position);
        
        return new vscode.Hover(contents, diagnostic.range);
    }

    private async createHoverContent(
        diagnostic: vscode.Diagnostic,
        document: vscode.TextDocument,
        position: vscode.Position
    ): Promise<vscode.MarkdownString[]> {
        const contents: vscode.MarkdownString[] = [];

        // Main diagnostic information
        const mainContent = new vscode.MarkdownString();
        mainContent.isTrusted = true;
        mainContent.supportHtml = true;

        // Header with severity
        const severityIcon = this.getSeverityIcon(diagnostic.severity);
        mainContent.appendMarkdown(`${severityIcon} **Connascence: ${diagnostic.code}**\n\n`);

        // Description
        mainContent.appendMarkdown(`${diagnostic.message}\n\n`);

        // Connascence type explanation
        const connascenceType = this.extractConnascenceType(diagnostic.code as string);
        const explanation = this.getConnascenceExplanation(connascenceType);
        if (explanation) {
            mainContent.appendMarkdown(`**What is ${connascenceType}?**\n\n${explanation}\n\n`);
        }

        // Refactoring suggestions
        try {
            const suggestions = await this.connascenceService.suggestRefactoring(
                document.fileName,
                {
                    start: { line: position.line, character: position.character },
                    end: { line: position.line, character: position.character }
                }
            );

            if (suggestions.length > 0) {
                mainContent.appendMarkdown(`**Refactoring Suggestions:**\n\n`);
                for (const suggestion of suggestions.slice(0, 3)) {
                    mainContent.appendMarkdown(`• **${suggestion.technique}**: ${suggestion.description} (${suggestion.confidence}% confidence)\n`);
                }
                mainContent.appendMarkdown(`\n`);
            }
        } catch (error) {
            // Silently handle refactoring suggestion errors
        }

        // Quick actions
        mainContent.appendMarkdown(`**Actions:**\n`);
        mainContent.appendMarkdown(`[$(lightbulb) Quick Fix](command:editor.action.quickFix) `);
        mainContent.appendMarkdown(`[$(gear) Refactor](command:editor.action.refactor) `);
        mainContent.appendMarkdown(`[$(book) Learn More](command:connascence.explainFinding?${encodeURIComponent(JSON.stringify({ code: diagnostic.code }))})`);

        contents.push(mainContent);

        // Additional related information
        if (diagnostic.relatedInformation && diagnostic.relatedInformation.length > 0) {
            const relatedContent = new vscode.MarkdownString();
            relatedContent.appendMarkdown(`**Related Information:**\n\n`);
            
            for (const info of diagnostic.relatedInformation) {
                relatedContent.appendMarkdown(`• ${info.message}\n`);
            }
            
            contents.push(relatedContent);
        }

        return contents;
    }

    private getSeverityIcon(severity: vscode.DiagnosticSeverity): string {
        switch (severity) {
            case vscode.DiagnosticSeverity.Error:
                return '$(error)';
            case vscode.DiagnosticSeverity.Warning:
                return '$(warning)';
            case vscode.DiagnosticSeverity.Information:
                return '$(info)';
            case vscode.DiagnosticSeverity.Hint:
            default:
                return '$(lightbulb)';
        }
    }

    private extractConnascenceType(code: string): string {
        // Extract connascence type from diagnostic code
        if (code.startsWith('CON_')) {
            return code.replace('CON_', '').replace(/_/g, ' ').toLowerCase();
        }
        return code;
    }

    private getConnascenceExplanation(type: string): string | null {
        const explanations: { [key: string]: string } = {
            'position': 'Elements must be in the same order. When the order of parameters, arguments, or array elements matters for correctness.',
            'name': 'Elements must agree on the name of something. Multiple components referring to the same entity by name.',
            'type': 'Elements must agree on the type of something. Multiple components that must share the same data type.',
            'meaning': 'Elements must agree on the meaning of particular values. Multiple components that must agree on the meaning of specific values.',
            'algorithm': 'Elements must agree on a particular algorithm. Multiple components that must use the same algorithm or approach.',
            'timing': 'Elements must be executed at certain times relative to each other. Components that depend on specific timing relationships.',
            'value': 'Elements must agree on particular values. Multiple components that must use the same literal values.',
            'identity': 'Elements must reference the same entity. Multiple components that must refer to the same object or entity.',
            'execution': 'The order of execution of elements is important. Components where execution order affects correctness.'
        };

        return explanations[type] || null;
    }
}