"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.ConnascenceCodeActionProvider = void 0;
const vscode = __importStar(require("vscode"));
class ConnascenceCodeActionProvider {
    constructor(connascenceService) {
        this.connascenceService = connascenceService;
    }
    async provideCodeActions(document, range, context, token) {
        const actions = [];
        // Get connascence diagnostics in this range
        const connascenceDiagnostics = context.diagnostics.filter(d => d.source === 'connascence');
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
    async createQuickFix(document, diagnostic) {
        if (!diagnostic.code)
            return null;
        const action = new vscode.CodeAction(`Fix: ${diagnostic.message}`, vscode.CodeActionKind.QuickFix);
        action.diagnostics = [diagnostic];
        action.isPreferred = true;
        try {
            const fixes = await this.connascenceService.getAutofixes(document.fileName);
            const relevantFix = fixes.find(fix => fix.line === diagnostic.range.start.line + 1 &&
                fix.issue.includes(diagnostic.code));
            if (relevantFix) {
                const edit = new vscode.WorkspaceEdit();
                const range = new vscode.Range(relevantFix.line - 1, relevantFix.column || 0, relevantFix.endLine ? relevantFix.endLine - 1 : relevantFix.line - 1, relevantFix.endColumn || Number.MAX_SAFE_INTEGER);
                edit.replace(document.uri, range, relevantFix.replacement);
                action.edit = edit;
            }
        }
        catch (error) {
            console.error('Failed to get autofix:', error);
            return null;
        }
        return action;
    }
    async createRefactorActions(document, diagnostic, range) {
        const actions = [];
        try {
            const suggestions = await this.connascenceService.suggestRefactoring(document.fileName, {
                start: { line: range.start.line, character: range.start.character },
                end: { line: range.end.line, character: range.end.character }
            });
            for (const suggestion of suggestions) {
                const action = new vscode.CodeAction(`Refactor: ${suggestion.technique}`, vscode.CodeActionKind.Refactor);
                // Tooltip not supported in VS Code API - description provides similar info
                // Create command to show refactoring preview
                action.command = {
                    command: 'connascence.previewRefactoring',
                    title: 'Preview Refactoring',
                    arguments: [document.uri, suggestion]
                };
                actions.push(action);
            }
        }
        catch (error) {
            console.error('Failed to get refactoring suggestions:', error);
        }
        return actions;
    }
}
exports.ConnascenceCodeActionProvider = ConnascenceCodeActionProvider;
//# sourceMappingURL=codeActionProvider.js.map