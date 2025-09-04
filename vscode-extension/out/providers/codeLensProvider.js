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
exports.ConnascenceCodeLensProvider = void 0;
const vscode = __importStar(require("vscode"));
/**
 * Code lens provider for displaying connascence metrics inline
 */
class ConnascenceCodeLensProvider {
    constructor(connascenceService) {
        this.connascenceService = connascenceService;
        this._onDidChangeCodeLenses = new vscode.EventEmitter();
        this.onDidChangeCodeLenses = this._onDidChangeCodeLenses.event;
    }
    async provideCodeLenses(document, token) {
        if (token.isCancellationRequested) {
            return [];
        }
        const config = vscode.workspace.getConfiguration('connascence');
        if (!config.get('enableCodeLens', true)) {
            return [];
        }
        const codeLenses = [];
        try {
            // Add file-level metrics at the top
            const fileMetrics = await this.getFileMetrics(document);
            if (fileMetrics) {
                const range = new vscode.Range(0, 0, 0, 0);
                codeLenses.push(new vscode.CodeLens(range, fileMetrics));
            }
            // Add function-level metrics
            const functionMetrics = await this.getFunctionMetrics(document);
            codeLenses.push(...functionMetrics);
            // Add class-level metrics
            const classMetrics = await this.getClassMetrics(document);
            codeLenses.push(...classMetrics);
            // Add high-impact violation warnings
            const violationWarnings = await this.getViolationWarnings(document);
            codeLenses.push(...violationWarnings);
            return codeLenses;
        }
        catch (error) {
            console.error('Error providing code lenses:', error);
            return [];
        }
    }
    resolveCodeLens(codeLens, token) {
        // Code lens is already resolved in provideCodeLenses
        return codeLens;
    }
    async getFileMetrics(document) {
        try {
            // This would typically call the connascence service
            // For now, we'll simulate the metrics
            const analysis = await this.analyzeDocument(document);
            const totalViolations = analysis.violations.length;
            const criticalViolations = analysis.violations.filter((v) => v.severity === 'critical').length;
            const qualityScore = this.calculateQualityScore(analysis);
            let title = `📊 Connascence: ${totalViolations} issues`;
            if (criticalViolations > 0) {
                title += ` (${criticalViolations} critical)`;
            }
            title += ` | Quality: ${qualityScore}%`;
            return {
                title,
                command: 'connascence.showFileReport',
                arguments: [document.uri, analysis]
            };
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            return {
                title: '❌ Connascence analysis failed',
                command: 'connascence.showError',
                arguments: [errorMessage]
            };
        }
    }
    async getFunctionMetrics(document) {
        const codeLenses = [];
        const text = document.getText();
        // Find function definitions
        const functionRegex = /^[\s]*(?:async\s+)?(?:def|function)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(/gm;
        let match;
        while ((match = functionRegex.exec(text)) !== null) {
            const functionName = match[1];
            const startPos = document.positionAt(match.index);
            const line = document.lineAt(startPos);
            // Analyze function complexity
            const functionAnalysis = await this.analyzeFunctionAtPosition(document, startPos);
            if (functionAnalysis && functionAnalysis.hasIssues) {
                const range = new vscode.Range(startPos, line.range.end);
                const command = {
                    title: this.formatFunctionMetrics(functionAnalysis),
                    command: 'connascence.showFunctionDetails',
                    arguments: [document.uri, functionName, functionAnalysis]
                };
                codeLenses.push(new vscode.CodeLens(range, command));
            }
        }
        return codeLenses;
    }
    async getClassMetrics(document) {
        const codeLenses = [];
        const text = document.getText();
        // Find class definitions
        const classRegex = /^[\s]*class\s+([a-zA-Z_][a-zA-Z0-9_]*)/gm;
        let match;
        while ((match = classRegex.exec(text)) !== null) {
            const className = match[1];
            const startPos = document.positionAt(match.index);
            const line = document.lineAt(startPos);
            // Analyze class coupling
            const classAnalysis = await this.analyzeClassAtPosition(document, startPos);
            if (classAnalysis && classAnalysis.hasIssues) {
                const range = new vscode.Range(startPos, line.range.end);
                const command = {
                    title: this.formatClassMetrics(classAnalysis),
                    command: 'connascence.showClassDetails',
                    arguments: [document.uri, className, classAnalysis]
                };
                codeLenses.push(new vscode.CodeLens(range, command));
            }
        }
        return codeLenses;
    }
    async getViolationWarnings(document) {
        const codeLenses = [];
        // Get diagnostics for this document
        const diagnostics = vscode.languages.getDiagnostics(document.uri)
            .filter(d => d.source === 'connascence' && d.severity === vscode.DiagnosticSeverity.Error);
        // Group critical violations and show summary
        const criticalLines = new Set();
        for (const diagnostic of diagnostics) {
            const lineNumber = diagnostic.range.start.line;
            if (criticalLines.has(lineNumber)) {
                continue; // Already have a lens for this line
            }
            criticalLines.add(lineNumber);
            const range = new vscode.Range(lineNumber, 0, lineNumber, 0);
            const command = {
                title: `🚨 Critical connascence violation - Click to fix`,
                command: 'connascence.quickFix',
                arguments: [document.uri, diagnostic.range]
            };
            codeLenses.push(new vscode.CodeLens(range, command));
        }
        return codeLenses;
    }
    async analyzeDocument(document) {
        // Simulate analysis - in real implementation, this would call the connascence service
        const text = document.getText();
        const lines = text.split('\n');
        const violations = [];
        // Simple heuristic analysis
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            // Check for magic numbers
            const magicNumberRegex = /\b(\d{2,})\b/g;
            let match;
            while ((match = magicNumberRegex.exec(line)) !== null) {
                violations.push({
                    type: 'magic_number',
                    severity: 'medium',
                    line: i + 1,
                    message: `Magic number: ${match[1]}`
                });
            }
            // Check for long parameter lists
            if (line.includes('def ') && (line.match(/,/g) || []).length >= 4) {
                violations.push({
                    type: 'long_parameter_list',
                    severity: 'high',
                    line: i + 1,
                    message: 'Function has too many parameters'
                });
            }
            // Check for string literals
            const stringLiteralRegex = /['"][^'"]{4,}['"]/g;
            if (stringLiteralRegex.test(line)) {
                violations.push({
                    type: 'magic_string',
                    severity: 'low',
                    line: i + 1,
                    message: 'Consider extracting string literal to constant'
                });
            }
        }
        return { violations, lineCount: lines.length };
    }
    async analyzeFunctionAtPosition(document, position) {
        // Get function body (simplified)
        const text = document.getText();
        const lines = text.split('\n');
        const startLine = position.line;
        let endLine = startLine + 1;
        let indentLevel = 0;
        let foundBody = false;
        // Find function end (simplified Python parsing)
        for (let i = startLine; i < lines.length; i++) {
            const line = lines[i];
            if (i === startLine) {
                // Determine initial indent
                const match = line.match(/^(\s*)/);
                indentLevel = match ? match[1].length : 0;
                continue;
            }
            if (line.trim() === '')
                continue;
            const currentIndent = line.match(/^(\s*)/);
            const currentIndentLevel = currentIndent ? currentIndent[1].length : 0;
            if (currentIndentLevel <= indentLevel && foundBody) {
                endLine = i;
                break;
            }
            if (currentIndentLevel > indentLevel) {
                foundBody = true;
            }
        }
        const functionLines = lines.slice(startLine, endLine);
        const parameterCount = (lines[startLine].match(/,/g) || []).length + 1;
        const complexity = this.calculateCyclomaticComplexity(functionLines);
        return {
            hasIssues: parameterCount >= 4 || complexity >= 10,
            parameterCount,
            complexity,
            lineCount: functionLines.length
        };
    }
    async analyzeClassAtPosition(document, position) {
        // Simplified class analysis
        const text = document.getText();
        const lines = text.split('\n');
        const startLine = position.line;
        // Count methods in class
        let methodCount = 0;
        let dependencyCount = 0;
        for (let i = startLine + 1; i < lines.length && i < startLine + 100; i++) {
            const line = lines[i];
            if (line.includes('def '))
                methodCount++;
            if (line.includes('import ') || line.includes('from '))
                dependencyCount++;
            if (line.match(/^class\s+/) && i > startLine)
                break; // Next class
        }
        return {
            hasIssues: methodCount >= 10 || dependencyCount >= 5,
            methodCount,
            dependencyCount
        };
    }
    calculateCyclomaticComplexity(lines) {
        let complexity = 1; // Base complexity
        for (const line of lines) {
            // Count decision points
            if (line.includes('if '))
                complexity++;
            if (line.includes('elif '))
                complexity++;
            if (line.includes('for '))
                complexity++;
            if (line.includes('while '))
                complexity++;
            if (line.includes('except '))
                complexity++;
            if (line.includes('and ') || line.includes('or '))
                complexity++;
        }
        return complexity;
    }
    calculateQualityScore(analysis) {
        const { violations, lineCount } = analysis;
        if (lineCount === 0)
            return 100;
        const violationWeight = violations.reduce((sum, v) => {
            switch (v.severity) {
                case 'critical': return sum + 10;
                case 'high': return sum + 5;
                case 'medium': return sum + 2;
                default: return sum + 1;
            }
        }, 0);
        const violationRatio = violationWeight / lineCount;
        const score = Math.max(0, Math.round(100 - (violationRatio * 100)));
        return score;
    }
    formatFunctionMetrics(analysis) {
        const { parameterCount, complexity, lineCount } = analysis;
        const parts = [];
        if (parameterCount >= 4) {
            parts.push(`${parameterCount} params`);
        }
        if (complexity >= 10) {
            parts.push(`complexity: ${complexity}`);
        }
        if (lineCount >= 50) {
            parts.push(`${lineCount} lines`);
        }
        return `⚠️ ${parts.join(', ')}`;
    }
    formatClassMetrics(analysis) {
        const { methodCount, dependencyCount } = analysis;
        const parts = [];
        if (methodCount >= 10) {
            parts.push(`${methodCount} methods`);
        }
        if (dependencyCount >= 5) {
            parts.push(`${dependencyCount} deps`);
        }
        return `📊 ${parts.join(', ')}`;
    }
    refresh() {
        this._onDidChangeCodeLenses.fire();
    }
}
exports.ConnascenceCodeLensProvider = ConnascenceCodeLensProvider;
//# sourceMappingURL=codeLensProvider.js.map