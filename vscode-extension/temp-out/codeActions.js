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
        const ruleId = typeof diagnostic.code === 'string' ? diagnostic.code :
            (typeof diagnostic.code === 'object' && diagnostic.code !== null && 'value' in diagnostic.code)
                ? String(diagnostic.code.value) : String(diagnostic.code);
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
        return actions;
    }
    createMagicLiteralActions(violation, document, diagnostic) {
        const actions = [];
        // Extract magic literal action
        const extractAction = new vscode.CodeAction('Extract magic literal to constant', vscode.CodeActionKind.RefactorExtract);
        extractAction.diagnostics = [diagnostic];
        extractAction.isPreferred = true;
        const line = document.lineAt(diagnostic.range.start.line);
        const lineText = line.text;
        // Simple regex to find numeric literals
        const numberMatch = lineText.match(/\b(\d+(?:\.\d+)?)\b/);
        const stringMatch = lineText.match(/["'](.*?)["']/);
        if (numberMatch || stringMatch) {
            const literal = numberMatch ? numberMatch[1] : stringMatch ? stringMatch[0] : '';
            const constantName = this.generateConstantName(literal, violation);
            extractAction.edit = new vscode.WorkspaceEdit();
            // Add constant definition at top of file
            const insertPos = new vscode.Position(0, 0);
            const constantDef = `${constantName} = ${literal}\n`;
            extractAction.edit.insert(document.uri, insertPos, constantDef);
            // Replace literal with constant reference
            extractAction.edit.replace(document.uri, diagnostic.range, constantName);
        }
        actions.push(extractAction);
        return actions;
    }
    createParameterActions(violation, document, diagnostic) {
        const actions = [];
        // Convert to keyword arguments
        const keywordAction = new vscode.CodeAction('Convert to keyword arguments', vscode.CodeActionKind.RefactorRewrite);
        keywordAction.diagnostics = [diagnostic];
        keywordAction.isPreferred = true;
        // This would require more sophisticated parsing
        // For now, just add a command to trigger autofix
        keywordAction.command = {
            title: 'Apply parameter refactoring',
            command: 'connascence.autofixCurrent'
        };
        actions.push(keywordAction);
        return actions;
    }
    createTypeHintActions(violation, document, diagnostic) {
        const actions = [];
        // Add type hints action
        const typeAction = new vscode.CodeAction('Add type hints', vscode.CodeActionKind.QuickFix);
        typeAction.diagnostics = [diagnostic];
        typeAction.isPreferred = true;
        const line = document.lineAt(diagnostic.range.start.line);
        const lineText = line.text;
        // Simple function parameter detection
        const functionMatch = lineText.match(/def\s+(\w+)\s*\(([^)]*)\)/);
        if (functionMatch) {
            const [, functionName, params] = functionMatch;
            // Add basic type hints
            const typedParams = params.split(',').map(p => {
                const paramName = p.trim();
                if (paramName === 'self' || paramName === 'cls')
                    return paramName;
                return `${paramName}: Any`;
            }).join(', ');
            const newSignature = `def ${functionName}(${typedParams}) -> Any:`;
            typeAction.edit = new vscode.WorkspaceEdit();
            // Add import for Any at top of file
            const importPos = new vscode.Position(0, 0);
            typeAction.edit.insert(document.uri, importPos, 'from typing import Any\n');
            // Replace function signature
            const sigRange = new vscode.Range(diagnostic.range.start, line.range.end);
            typeAction.edit.replace(document.uri, sigRange, newSignature);
        }
        actions.push(typeAction);
        return actions;
    }
    createComplexityActions(violation, document, diagnostic) {
        const actions = [];
        // Extract method action
        const extractAction = new vscode.CodeAction('Extract method to reduce complexity', vscode.CodeActionKind.RefactorExtract);
        extractAction.diagnostics = [diagnostic];
        // This would require sophisticated analysis
        // For now, trigger autofix
        extractAction.command = {
            title: 'Apply complexity refactoring',
            command: 'connascence.autofixCurrent'
        };
        actions.push(extractAction);
        return actions;
    }
    createExplainAction(violation, diagnostic) {
        const explainAction = new vscode.CodeAction(`Explain ${violation.connascenceType} violation`, vscode.CodeActionKind.Empty);
        explainAction.diagnostics = [diagnostic];
        explainAction.command = {
            title: 'Explain violation',
            command: 'connascence.explainFinding',
            arguments: [{ finding: violation }]
        };
        return explainAction;
    }
    createIgnoreAction(violation, document, diagnostic) {
        const ignoreAction = new vscode.CodeAction('Ignore this violation', vscode.CodeActionKind.Empty);
        ignoreAction.diagnostics = [diagnostic];
        // Add ignore comment
        const line = document.lineAt(diagnostic.range.start.line);
        const comment = `  # connascence: ignore ${violation.ruleId}`;
        ignoreAction.edit = new vscode.WorkspaceEdit();
        ignoreAction.edit.insert(document.uri, line.range.end, comment);
        return ignoreAction;
    }
    generateConstantName(literal, violation) {
        // Generate appropriate constant name based on literal and context
        if (/^\d+$/.test(literal)) {
            // Integer literal
            const num = parseInt(literal);
            if (num >= 100 && num <= 999) {
                return `HTTP_STATUS_${num}`;
            }
            return `DEFAULT_VALUE_${num}`;
        }
        if (/^\d+\.\d+$/.test(literal)) {
            // Float literal
            return `DEFAULT_RATE_${literal.replace('.', '_')}`;
        }
        // String literal - clean up for constant name
        const cleaned = literal.replace(/["']/g, '').replace(/[^\w]/g, '_').toUpperCase();
        return `DEFAULT_${cleaned}`;
    }
    async autofixFile(document) {
        const config = vscode.workspace.getConfiguration('connascence');
        const binaryPath = config.get('pathToBinary', 'connascence');
        try {
            // Run autofix command
            const { spawn } = require('child_process');
            const process = spawn(binaryPath, ['autofix', '--preview', document.uri.fsPath]);
            let output = '';
            process.stdout.on('data', (data) => {
                output += data.toString();
            });
            process.on('close', (code) => {
                if (code === 0) {
                    vscode.window.showInformationMessage('Autofix preview ready');
                    // Could show preview in a new document or panel
                }
                else {
                    vscode.window.showErrorMessage('Autofix failed');
                }
            });
        }
        catch (error) {
            vscode.window.showErrorMessage(`Autofix error: ${error}`);
        }
    }
}
exports.ConnascenceCodeActions = ConnascenceCodeActions;
//# sourceMappingURL=codeActions.js.map