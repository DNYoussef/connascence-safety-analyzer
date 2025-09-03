import * as vscode from 'vscode';
import { ConnascenceService } from '../services/connascenceService';

export class ConnascenceCodeActionProvider implements vscode.CodeActionProvider {
    constructor(private connascenceService: ConnascenceService) {}

    async provideCodeActions(
        document: vscode.TextDocument,
        range: vscode.Range | vscode.Selection,
        context: vscode.CodeActionContext,
        token: vscode.CancellationToken
    ): Promise<vscode.CodeAction[]> {
        const actions: vscode.CodeAction[] = [];

        // Get connascence diagnostics in this range
        const connascenceDiagnostics = context.diagnostics.filter(
            d => d.source === 'connascence'
        );

        for (const diagnostic of connascenceDiagnostics) {
            // Quick fix actions
            const quickFix = await this.createQuickFix(document, diagnostic);
            if (quickFix) {
                actions.push(quickFix);
            }

            // Refactoring actions
            const refactorActions = await this.createRefactorActions(document, diagnostic, range);
            actions.push(...refactorActions);
        }

        return actions;
    }

    private async createQuickFix(document: vscode.TextDocument, diagnostic: vscode.Diagnostic): Promise<vscode.CodeAction | null> {
        if (!diagnostic.code) return null;

        const action = new vscode.CodeAction(
            `Fix: ${diagnostic.message}`,
            vscode.CodeActionKind.QuickFix
        );

        action.diagnostics = [diagnostic];
        action.isPreferred = true;

        try {
            const fixes = await this.connascenceService.getAutofixes(document.fileName);
            const relevantFix = fixes.find(fix => 
                fix.line === diagnostic.range.start.line + 1 &&
                fix.issue.includes(diagnostic.code as string)
            );

            if (relevantFix) {
                const edit = new vscode.WorkspaceEdit();
                const range = new vscode.Range(
                    relevantFix.line - 1, relevantFix.column || 0,
                    relevantFix.endLine ? relevantFix.endLine - 1 : relevantFix.line - 1,
                    relevantFix.endColumn || Number.MAX_SAFE_INTEGER
                );
                edit.replace(document.uri, range, relevantFix.replacement);
                action.edit = edit;
            }
        } catch (error) {
            console.error('Failed to get autofix:', error);
            return null;
        }

        return action;
    }

    private async createRefactorActions(
        document: vscode.TextDocument, 
        diagnostic: vscode.Diagnostic, 
        range: vscode.Range
    ): Promise<vscode.CodeAction[]> {
        const actions: vscode.CodeAction[] = [];

        try {
            const suggestions = await this.connascenceService.suggestRefactoring(
                document.fileName,
                {
                    start: { line: range.start.line, character: range.start.character },
                    end: { line: range.end.line, character: range.end.character }
                }
            );

            for (const suggestion of suggestions) {
                const action = new vscode.CodeAction(
                    `Refactor: ${suggestion.technique}`,
                    vscode.CodeActionKind.Refactor
                );

                action.tooltip = suggestion.description;
                
                // Create command to show refactoring preview
                action.command = {
                    command: 'connascence.previewRefactoring',
                    title: 'Preview Refactoring',
                    arguments: [document.uri, suggestion]
                };

                actions.push(action);
            }
        } catch (error) {
            console.error('Failed to get refactoring suggestions:', error);
        }

        return actions;
    }
}