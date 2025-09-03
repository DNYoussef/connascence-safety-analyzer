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
exports.ConnascenceDiagnosticsProvider = void 0;
const vscode = __importStar(require("vscode"));
class ConnascenceDiagnosticsProvider {
    constructor(connascenceService) {
        this.connascenceService = connascenceService;
        this.cache = new Map();
        this.diagnosticsCollection = vscode.languages.createDiagnosticCollection('connascence');
    }
    async updateDiagnostics(uri, results) {
        const diagnostics = this.findingsToDiagnostics(results.findings, uri);
        this.diagnosticsCollection.set(uri, diagnostics);
        this.cache.set(uri.toString(), results);
    }
    async updateFile(document) {
        if (!this.isSupportedLanguage(document.languageId)) {
            return;
        }
        try {
            const results = await this.connascenceService.analyzeFile(document.fileName);
            await this.updateDiagnostics(document.uri, results);
        }
        catch (error) {
            console.error('Failed to update diagnostics:', error);
            // Clear diagnostics on error
            this.diagnosticsCollection.set(document.uri, []);
        }
    }
    clearDiagnostics(uri) {
        this.diagnosticsCollection.delete(uri);
        this.cache.delete(uri.toString());
    }
    clearAllDiagnostics() {
        this.diagnosticsCollection.clear();
        this.cache.clear();
    }
    getDiagnostics(uri) {
        return this.diagnosticsCollection.get(uri) || [];
    }
    getCachedResults(uri) {
        return this.cache.get(uri.toString());
    }
    dispose() {
        this.diagnosticsCollection.dispose();
        this.cache.clear();
    }
    findingsToDiagnostics(findings, uri) {
        return findings.map(finding => this.findingToDiagnostic(finding, uri));
    }
    findingToDiagnostic(finding, uri) {
        const line = Math.max(0, finding.line - 1); // VS Code uses 0-based line numbers
        const character = Math.max(0, (finding.column || 1) - 1);
        // Create range - try to be smart about the end position
        const range = this.createDiagnosticRange(line, character, finding.type);
        const diagnostic = new vscode.Diagnostic(range, finding.message, this.severityToVSCodeSeverity(finding.severity));
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
                new vscode.DiagnosticRelatedInformation(new vscode.Location(uri, range), `Suggestion: ${finding.suggestion}`)
            ];
        }
        return diagnostic;
    }
    createDiagnosticRange(line, character, findingType) {
        // Default range length based on finding type
        let endCharacter = character + this.getDefaultRangeLength(findingType);
        return new vscode.Range(new vscode.Position(line, character), new vscode.Position(line, endCharacter));
    }
    getDefaultRangeLength(findingType) {
        // Different finding types might have different typical lengths
        const typeLengths = {
            'magic_number': 5,
            'long_parameter_list': 20,
            'large_class': 15,
            'duplicate_code': 30,
            'complex_method': 25,
            'deep_nesting': 10
        };
        return typeLengths[findingType] || 15;
    }
    severityToVSCodeSeverity(severity) {
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
    getDiagnosticTags(finding) {
        const tags = [];
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
    isSupportedLanguage(languageId) {
        return ['python', 'c', 'cpp', 'javascript', 'typescript'].includes(languageId);
    }
    // Batch operations for performance
    async updateMultipleDiagnostics(updates) {
        const batch = updates.map(({ uri, results }) => {
            const diagnostics = this.findingsToDiagnostics(results.findings, uri);
            this.cache.set(uri.toString(), results);
            return { uri, diagnostics };
        });
        // Apply all updates at once
        for (const { uri, diagnostics } of batch) {
            this.diagnosticsCollection.set(uri, diagnostics);
        }
    }
    // Statistics and reporting
    getStatistics() {
        let totalFindings = 0;
        const findingsBySeverity = {};
        const findingsByType = {};
        for (const results of this.cache.values()) {
            totalFindings += results.findings.length;
            for (const finding of results.findings) {
                findingsBySeverity[finding.severity] = (findingsBySeverity[finding.severity] || 0) + 1;
                findingsByType[finding.type] = (findingsByType[finding.type] || 0) + 1;
            }
        }
        return {
            totalFiles: this.cache.size,
            totalFindings,
            findingsBySeverity,
            findingsByType
        };
    }
    // Filter diagnostics based on configuration
    applyFilter(severityFilter, typeFilter) {
        for (const [uriString, results] of this.cache.entries()) {
            const uri = vscode.Uri.parse(uriString);
            let filteredFindings = results.findings;
            if (severityFilter && severityFilter.length > 0) {
                filteredFindings = filteredFindings.filter(f => severityFilter.includes(f.severity));
            }
            if (typeFilter && typeFilter.length > 0) {
                filteredFindings = filteredFindings.filter(f => typeFilter.some(type => f.type.includes(type)));
            }
            const diagnostics = this.findingsToDiagnostics(filteredFindings, uri);
            this.diagnosticsCollection.set(uri, diagnostics);
        }
    }
}
exports.ConnascenceDiagnosticsProvider = ConnascenceDiagnosticsProvider;
//# sourceMappingURL=diagnosticsProvider.js.map