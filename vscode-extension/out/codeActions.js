"use strict";
/**
 * Code actions provider for Connascence violations.
 *
 * Provides quick fixes and refactoring actions for common connascence
 * violations, integrating with VS Code's light bulb interface.
 */
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
exports.ConnascenceCodeActions = void 0;
const vscode = __importStar(require("vscode"));
class ConnascenceCodeActions {
    constructor(context) {
        this.context = context;
    }
    provideCodeActions(document, range, context, token) {
        const actions = [];
        // Process each diagnostic in the current range
        for (const diagnostic of context.diagnostics) {
            if (diagnostic.source !== 'connascence')
                continue;
            const violation = this.diagnosticToViolation(diagnostic, document);
            if (violation) {
                actions.push(...this.createActionsForViolation(violation, document, diagnostic));
            }
        }
        return actions;
    }
    diagnosticToViolation(diagnostic, document) {
        // Extract violation info from diagnostic
        const ruleId = typeof diagnostic.code === 'string' ? diagnostic.code : diagnostic.code?.value;
        if (!ruleId)
            return null;
        return {
            id: `${document.uri.fsPath}:${diagnostic.range.start.line}`,
            ruleId,
            severity: this.vsCodeSeverityToString(diagnostic.severity),
            connascenceType: ruleId.replace('CON_', ''),
            description: diagnostic.message,
            filePath: document.uri.fsPath,
            lineNumber: diagnostic.range.start.line + 1, // Convert to 1-based
            columnNumber: diagnostic.range.start.character + 1,
            weight: 1
        };
    }
    vsCodeSeverityToString(severity) {
        switch (severity) {
            case vscode.DiagnosticSeverity.Error:
                return 'critical';
            case vscode.DiagnosticSeverity.Warning:
                return 'high';
            case vscode.DiagnosticSeverity.Information:
                return 'medium';
            case vscode.DiagnosticSeverity.Hint:
            default:
                return 'low';
        }
    }
    createActionsForViolation(violation, document, diagnostic) {
        const actions = [];
        // Add violation-specific quick fixes
        switch (violation.connascenceType) {
            case 'CoM': // Connascence of Meaning (Magic literals)
                actions.push(...this.createMagicLiteralActions(violation, document, diagnostic));
                break;
            case 'CoP': // Connascence of Position (Parameter order)
                actions.push(...this.createParameterActions(violation, document, diagnostic));
                break;
            case 'CoT': // Connascence of Type (Missing type hints)
                actions.push(...this.createTypeHintActions(violation, document, diagnostic));
                break;
            case 'CoA': // Connascence of Algorithm (Complexity)
                actions.push(...this.createComplexityActions(violation, document, diagnostic));
                break;
        }
        // Add general actions
        actions.push(this.createExplainAction(violation, diagnostic));
        actions.push(this.createIgnoreAction(violation, document, diagnostic));
        n;
        n;
        return actions;
    }
    createMagicLiteralActions(violation, document, diagnostic) {
        const actions = [];
        // Extract magic literal action
        const extractAction = new vscode.CodeAction(n, 'Extract magic literal to constant', n, vscode.CodeActionKind.RefactorExtract);
        extractAction.diagnostics = [diagnostic];
        extractAction.isPreferred = true;
        const line = document.lineAt(diagnostic.range.start.line);
        const lineText = line.text;
        // Simple regex to find numeric literals
        const numberMatch = lineText.match(/\\b(\\d+(?:\\.\\d+)?)\\b/);
        const stringMatch = lineText.match(/[\"'](.*?)[\"']/);
        if (numberMatch || stringMatch) {
            const literal = numberMatch ? numberMatch[1] : stringMatch ? stringMatch[0] : '';
            const constantName = this.generateConstantName(literal, violation);
            extractAction.edit = new vscode.WorkspaceEdit();
            // Add constant definition at top of file
            const insertPos = new vscode.Position(0, 0);
            const constantDef = `${constantName} = ${literal}\\n`;
            n;
            extractAction.edit.insert(document.uri, insertPos, constantDef);
            n;
            n;
        }
    }
} // Replace literal with constant reference\n            extractAction.edit.replace(document.uri, diagnostic.range, constantName);\n        }\n        \n        actions.push(extractAction);\n        \n        return actions;\n    }\n    \n    private createParameterActions(\n        violation: ConnascenceViolation,\n        document: vscode.TextDocument,\n        diagnostic: vscode.Diagnostic\n    ): vscode.CodeAction[] {\n        const actions: vscode.CodeAction[] = [];\n        \n        // Convert to keyword arguments\n        const keywordAction = new vscode.CodeAction(\n            'Convert to keyword arguments',\n            vscode.CodeActionKind.RefactorRewrite\n        );\n        keywordAction.diagnostics = [diagnostic];\n        keywordAction.isPreferred = true;\n        \n        // This would require more sophisticated parsing\n        // For now, just add a command to trigger autofix\n        keywordAction.command = {\n            title: 'Apply parameter refactoring',\n            command: 'connascence.autofixCurrent'\n        };\n        \n        actions.push(keywordAction);\n        \n        return actions;\n    }\n    \n    private createTypeHintActions(\n        violation: ConnascenceViolation,\n        document: vscode.TextDocument,\n        diagnostic: vscode.Diagnostic\n    ): vscode.CodeAction[] {\n        const actions: vscode.CodeAction[] = [];\n        \n        // Add type hints action\n        const typeAction = new vscode.CodeAction(\n            'Add type hints',\n            vscode.CodeActionKind.QuickFix\n        );\n        typeAction.diagnostics = [diagnostic];\n        typeAction.isPreferred = true;\n        \n        const line = document.lineAt(diagnostic.range.start.line);\n        const lineText = line.text;\n        \n        // Simple function parameter detection\n        const functionMatch = lineText.match(/def\\s+(\\w+)\\s*\\(([^)]*)\\)/);\n        if (functionMatch) {\n            const [, functionName, params] = functionMatch;\n            \n            // Add basic type hints\n            const typedParams = params.split(',').map(p => {\n                const paramName = p.trim();\n                if (paramName === 'self' || paramName === 'cls') return paramName;\n                return `${paramName}: Any`;\n            }).join(', ');\n            \n            const newSignature = `def ${functionName}(${typedParams}) -> Any:`;\n            \n            typeAction.edit = new vscode.WorkspaceEdit();\n            \n            // Add import for Any at top of file\n            const importPos = new vscode.Position(0, 0);\n            typeAction.edit.insert(document.uri, importPos, 'from typing import Any\\n');\n            \n            // Replace function signature\n            const sigRange = new vscode.Range(\n                diagnostic.range.start,\n                line.range.end\n            );\n            typeAction.edit.replace(document.uri, sigRange, newSignature);\n        }\n        \n        actions.push(typeAction);\n        \n        return actions;\n    }\n    \n    private createComplexityActions(\n        violation: ConnascenceViolation,\n        document: vscode.TextDocument,\n        diagnostic: vscode.Diagnostic\n    ): vscode.CodeAction[] {\n        const actions: vscode.CodeAction[] = [];\n        \n        // Extract method action\n        const extractAction = new vscode.CodeAction(\n            'Extract method to reduce complexity',\n            vscode.CodeActionKind.RefactorExtract\n        );\n        extractAction.diagnostics = [diagnostic];\n        \n        // This would require sophisticated analysis\n        // For now, trigger autofix\n        extractAction.command = {\n            title: 'Apply complexity refactoring',\n            command: 'connascence.autofixCurrent'\n        };\n        \n        actions.push(extractAction);\n        \n        return actions;\n    }\n    \n    private createExplainAction(violation: ConnascenceViolation, diagnostic: vscode.Diagnostic): vscode.CodeAction {\n        const explainAction = new vscode.CodeAction(\n            `Explain ${violation.connascenceType} violation`,\n            vscode.CodeActionKind.Empty\n        );\n        explainAction.diagnostics = [diagnostic];\n        \n        explainAction.command = {\n            title: 'Explain violation',\n            command: 'connascence.explainFinding',\n            arguments: [{ finding: violation }]\n        };\n        \n        return explainAction;\n    }\n    \n    private createIgnoreAction(\n        violation: ConnascenceViolation,\n        document: vscode.TextDocument,\n        diagnostic: vscode.Diagnostic\n    ): vscode.CodeAction {\n        const ignoreAction = new vscode.CodeAction(\n            'Ignore this violation',\n            vscode.CodeActionKind.Empty\n        );\n        ignoreAction.diagnostics = [diagnostic];\n        \n        // Add ignore comment\n        const line = document.lineAt(diagnostic.range.start.line);\n        const comment = `  # connascence: ignore ${violation.ruleId}`;\n        \n        ignoreAction.edit = new vscode.WorkspaceEdit();\n        ignoreAction.edit.insert(\n            document.uri,\n            line.range.end,\n            comment\n        );\n        \n        return ignoreAction;\n    }\n    \n    private generateConstantName(literal: string, violation: ConnascenceViolation): string {\n        // Generate appropriate constant name based on literal and context\n        if (/^\\d+$/.test(literal)) {\n            // Integer literal\n            const num = parseInt(literal);\n            if (num >= 100 && num <= 999) {\n                return `HTTP_STATUS_${num}`;\n            }\n            return `DEFAULT_VALUE_${num}`;\n        }\n        \n        if (/^\\d+\\.\\d+$/.test(literal)) {\n            // Float literal\n            return `DEFAULT_RATE_${literal.replace('.', '_')}`;\n        }\n        \n        // String literal - clean up for constant name\n        const cleaned = literal.replace(/[\"']/g, '').replace(/[^\\w]/g, '_').toUpperCase();\n        return `DEFAULT_${cleaned}`;\n    }\n    \n    async autofixFile(document: vscode.TextDocument): Promise<void> {\n        const config = vscode.workspace.getConfiguration('connascence');\n        const binaryPath = config.get<string>('pathToBinary', 'connascence');\n        \n        try {\n            // Run autofix command\n            const { spawn } = require('child_process');\n            const process = spawn(binaryPath, ['autofix', '--preview', document.uri.fsPath]);\n            \n            let output = '';\n            process.stdout.on('data', (data: Buffer) => {\n                output += data.toString();\n            });\n            \n            process.on('close', (code: number) => {\n                if (code === 0) {\n                    vscode.window.showInformationMessage('Autofix preview ready');\n                    // Could show preview in a new document or panel\n                } else {\n                    vscode.window.showErrorMessage('Autofix failed');\n                }\n            });\n        } catch (error) {\n            vscode.window.showErrorMessage(`Autofix error: ${error}`);\n        }\n    }\n}
exports.ConnascenceCodeActions = ConnascenceCodeActions;
//# sourceMappingURL=codeActions.js.map