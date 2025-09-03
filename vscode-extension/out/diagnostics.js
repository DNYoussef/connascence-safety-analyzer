"use strict";
/**
 * Diagnostics provider for Connascence violations.
 *
 * Integrates with VS Code's diagnostic system to show connascence violations
 * as problems in the Problems panel and as squiggle underlines in the editor.
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
exports.ConnascenceDiagnostics = void 0;
const vscode = __importStar(require("vscode"));
const path = __importStar(require("path"));
const child_process_1 = require("child_process");
class ConnascenceDiagnostics {
    constructor(context) {
        this.context = context;
        this.scanPromises = new Map();
    }
    setCollection(collection) {
        this.diagnosticCollection = collection;
    }
    async scanFile(document) {
        if (document.languageId !== 'python')
            return;
        const filePath = document.uri.fsPath;
        try {
            const violations = await this.runConnascenceAnalysis(filePath);
            this.updateDiagnostics(document.uri, violations);
        }
        catch (error) {
            console.error(`Failed to scan ${filePath}:`, error);
        }
    }
    scanFileDebounced(document) {
        const config = vscode.workspace.getConfiguration('connascence');
        const debounceMs = config.get('debounceMs', 1000);
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }
        this.debounceTimer = setTimeout(() => {
            this.scanFile(document);
        }, debounceMs);
    }
    async scanWorkspace() {
        if (!vscode.workspace.workspaceFolders)
            return;
        vscode.window.withProgress({
            location: vscode.ProgressLocation.Window,
            title: 'Scanning workspace for connascence violations',
            cancellable: false
        }, async (progress) => {
            const workspaceRoot = vscode.workspace.workspaceFolders[0].uri.fsPath;
            try {
                const violations = await this.runConnascenceAnalysis(workspaceRoot, true);
                this.updateWorkspaceDiagnostics(violations);
                // Update context for when findings exist
                vscode.commands.executeCommand('setContext', 'connascence.hasFindings', violations.length > 0);
                vscode.window.showInformationMessage(`Connascence scan complete: ${violations.length} violations found`);
            }
            catch (error) {
                vscode.window.showErrorMessage(`Connascence scan failed: ${error}`);
            }
        });
    }
    async runConnascenceAnalysis(targetPath, isWorkspace = false) {
        const config = vscode.workspace.getConfiguration('connascence');
        const binaryPath = config.get('pathToBinary', 'connascence');
        const policyPreset = config.get('policyPreset', 'service-defaults');
        const useMCP = config.get('useMCP', false);
        if (useMCP) {
            return this.runMCPAnalysis(targetPath, isWorkspace);
        }
        else {
            return this.runCLIAnalysis(binaryPath, targetPath, policyPreset);
        }
    }
    async runCLIAnalysis(binaryPath, targetPath, policy) {
        return new Promise((resolve, reject) => {
            const args = ['scan', targetPath, '--format', 'json', '--policy', policy];
            const process = (0, child_process_1.spawn)(binaryPath, args);
            let stdout = '';
            let stderr = '';
            process.stdout.on('data', (data) => {
                stdout += data.toString();
            });
            process.stderr.on('data', (data) => {
                stderr += data.toString();
            });
            process.on('close', (code) => {
                if (code === 0) {
                    try {
                        const result = JSON.parse(stdout);
                        const violations = this.parseViolations(result);
                        resolve(violations);
                    }
                    catch (error) {
                        reject(new Error(`Failed to parse connascence output: ${error}`));
                    }
                }
                else {
                    reject(new Error(`Connascence CLI failed (code ${code}): ${stderr}`));
                }
            });
            process.on('error', (error) => {
                reject(new Error(`Failed to run connascence: ${error.message}`));
            });
        });
    }
    async runMCPAnalysis(targetPath, isWorkspace) {
        // TODO: Implement MCP client for VS Code
        // This would connect to the MCP server and use scan_path tool
        throw new Error('MCP analysis not yet implemented in VS Code extension');
    }
    parseViolations(result) {
        if (!result.violations || !Array.isArray(result.violations)) {
            return [];
        }
        const config = vscode.workspace.getConfiguration('connascence');
        const severityThreshold = config.get('severityThreshold', 'medium');
        const maxDiagnostics = config.get('maxDiagnostics', 1500);
        const severityOrder = { 'low': 1, 'medium': 2, 'high': 3, 'critical': 4 };
        const minSeverity = severityOrder[severityThreshold] || 2;
        return result.violations
            .filter((v) => severityOrder[v.severity] >= minSeverity)
            .slice(0, maxDiagnostics)
            .map((v) => ({
            id: v.id,
            ruleId: v.rule_id,
            severity: v.severity,
            connascenceType: v.connascence_type || v.rule_id.replace('CON_', ''),
            description: v.description,
            filePath: v.file_path,
            lineNumber: v.line_number,
            columnNumber: v.column_number,
            weight: v.weight || 1,
            recommendation: v.recommendation
        }));
    }
    updateDiagnostics(uri, violations) {
        if (!this.diagnosticCollection)
            return;
        const diagnostics = violations
            .filter(v => path.resolve(v.filePath) === uri.fsPath)
            .map(v => this.violationToDiagnostic(v));
        this.diagnosticCollection.set(uri, diagnostics);
    }
    updateWorkspaceDiagnostics(violations) {
        if (!this.diagnosticCollection)
            return;
        // Clear existing diagnostics
        this.diagnosticCollection.clear();
        // Group violations by file
        const violationsByFile = new Map();
        for (const violation of violations) {
            const filePath = path.resolve(violation.filePath);
            if (!violationsByFile.has(filePath)) {
                violationsByFile.set(filePath, []);
            }
            violationsByFile.get(filePath).push(violation);
        }
        // Set diagnostics for each file
        for (const [filePath, fileViolations] of violationsByFile) {
            const uri = vscode.Uri.file(filePath);
            const diagnostics = fileViolations.map(v => this.violationToDiagnostic(v));
            this.diagnosticCollection.set(uri, diagnostics);
        }
    }
    violationToDiagnostic(violation) {
        const line = Math.max(0, violation.lineNumber - 1); // VS Code uses 0-based line numbers
        const startChar = Math.max(0, (violation.columnNumber || 1) - 1);
        const range = new vscode.Range(new vscode.Position(line, startChar), new vscode.Position(line, startChar + 10) // Approximate end position
        );
        const diagnostic = new vscode.Diagnostic(range, violation.description, this.severityToVSCodeSeverity(violation.severity));
        diagnostic.code = violation.ruleId;
        diagnostic.source = 'connascence';
        // Add related information
        if (violation.recommendation) {
            diagnostic.relatedInformation = [
                new vscode.DiagnosticRelatedInformation(new vscode.Location(vscode.Uri.file(violation.filePath), range), `Recommendation: ${violation.recommendation}`)
            ];
        }
        // Add tags for certain violation types
        if (violation.severity === 'critical') {
            diagnostic.tags = [vscode.DiagnosticTag.Deprecated]; // Use deprecated tag for critical issues
        }
        return diagnostic;
    }
    severityToVSCodeSeverity(severity) {
        switch (severity) {
            case 'critical':
                return vscode.DiagnosticSeverity.Error;
            case 'high':
                return vscode.DiagnosticSeverity.Warning;
            case 'medium':
                return vscode.DiagnosticSeverity.Information;
            case 'low':
            default:
                return vscode.DiagnosticSeverity.Hint;
        }
    }
    clearFile(uri) {
        if (this.diagnosticCollection) {
            this.diagnosticCollection.delete(uri);
        }
    }
    clearAll() {
        if (this.diagnosticCollection) {
            this.diagnosticCollection.clear();
        }
    }
    refreshAll() {
        // Re-scan all open Python files
        vscode.workspace.textDocuments
            .filter(doc => doc.languageId === 'python')
            .forEach(doc => this.scanFileDebounced(doc));
    }
    dispose() {
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }
        // Cancel any running scan promises
        this.scanPromises.clear();
    }
}
exports.ConnascenceDiagnostics = ConnascenceDiagnostics;
//# sourceMappingURL=diagnostics.js.map