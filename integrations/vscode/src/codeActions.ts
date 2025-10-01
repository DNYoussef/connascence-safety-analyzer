import * as vscode from 'vscode';
import { ConnascenceAnalyzer } from './analyzer';

export class CodeActionProvider implements vscode.CodeActionProvider {
    private analyzer: ConnascenceAnalyzer;

    constructor(analyzer: ConnascenceAnalyzer) {
        this.analyzer = analyzer;
    }

    async provideCodeActions(
        document: vscode.TextDocument,
        range: vscode.Range | vscode.Selection,
        context: vscode.CodeActionContext,
        token: vscode.CancellationToken
    ): Promise<vscode.CodeAction[]> {
        const actions: vscode.CodeAction[] = [];

        // Get diagnostics for this range
        for (const diagnostic of context.diagnostics) {
            if (diagnostic.source !== 'connascence') {
                continue;
            }

            // Create quick fix action
            const fixAction = new vscode.CodeAction(
                `Fix ${diagnostic.code} violation`,
                vscode.CodeActionKind.QuickFix
            );
            fixAction.diagnostics = [diagnostic];
            fixAction.isPreferred = true;

            // Add command to fix
            fixAction.command = {
                title: 'Apply Fix',
                command: 'connascence.applyFix',
                arguments: [document.uri, diagnostic]
            };

            actions.push(fixAction);

            // Add explanation action
            const explainAction = new vscode.CodeAction(
                `Explain ${diagnostic.code}`,
                vscode.CodeActionKind.Empty
            );
            explainAction.command = {
                title: 'Explain',
                command: 'connascence.explain',
                arguments: [diagnostic.code]
            };
            actions.push(explainAction);
        }

        // Add refactoring actions
        const refactorAction = new vscode.CodeAction(
            'Refactor to reduce connascence',
            vscode.CodeActionKind.RefactorRewrite
        );
        refactorAction.command = {
            title: 'Refactor',
            command: 'connascence.refactor',
            arguments: [document.uri, range]
        };
        actions.push(refactorAction);

        return actions;
    }
}