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
exports.ConnascenceApiClient = void 0;
const vscode = __importStar(require("vscode"));
const path = __importStar(require("path"));
/**
 * Client for integrating with the main connascence analysis system
 */
class ConnascenceApiClient {
    constructor() {
        this.workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    }
    /**
     * Analyze a single file using the main connascence system
     */
    async analyzeFile(filePath) {
        try {
            // Import and use the existing analysis system from src/reports/
            const { generateConnascenceReport } = await this.loadConnascenceSystem();
            // Create a mock options object for single file analysis
            const options = {
                inputPath: filePath,
                outputPath: path.join(path.dirname(filePath), '.connascence-temp.json'),
                format: 'json',
                verbose: false,
                includeTests: false,
                safetyProfile: this.getSafetyProfile(),
                threshold: this.getThreshold(),
                exclude: this.getExcludePatterns()
            };
            // Generate the report
            const report = await generateConnascenceReport(options);
            // Convert to VS Code format
            return this.convertReportToAnalysisResult(report, filePath);
        }
        catch (error) {
            console.error('Failed to analyze file with main system:', error);
            // Fallback to simplified analysis
            return this.fallbackAnalyzeFile(filePath);
        }
    }
    /**
     * Analyze workspace using the main connascence system
     */
    async analyzeWorkspace(workspacePath) {
        try {
            const { generateConnascenceReport } = await this.loadConnascenceSystem();
            const options = {
                inputPath: workspacePath,
                outputPath: path.join(workspacePath, '.connascence-report.json'),
                format: 'json',
                verbose: false,
                includeTests: this.getIncludeTests(),
                safetyProfile: this.getSafetyProfile(),
                threshold: this.getThreshold(),
                exclude: this.getExcludePatterns()
            };
            const report = await generateConnascenceReport(options);
            return this.convertReportToWorkspaceResult(report);
        }
        catch (error) {
            console.error('Failed to analyze workspace with main system:', error);
            throw error;
        }
    }
    /**
     * Get safety validation using General Safety compliance
     */
    async validateSafety(filePath, profile) {
        try {
            const { validateSafetyCompliance } = await this.loadConnascenceSystem();
            const result = await validateSafetyCompliance({
                filePath,
                profile,
                strictMode: this.getStrictMode()
            });
            return {
                compliant: result.compliant,
                violations: result.violations.map((v) => ({
                    rule: v.rule || v.type,
                    message: v.message,
                    line: v.line,
                    severity: v.severity
                }))
            };
        }
        catch (error) {
            console.error('Safety validation failed:', error);
            throw error;
        }
    }
    /**
     * Get refactoring suggestions using the analysis engine
     */
    async suggestRefactoring(filePath, selection) {
        try {
            const { getRefactoringSuggestions } = await this.loadConnascenceSystem();
            const suggestions = await getRefactoringSuggestions({
                filePath,
                selection,
                maxSuggestions: 5
            });
            return suggestions.map((s) => ({
                technique: s.technique,
                description: s.description,
                confidence: s.confidence,
                preview: s.preview
            }));
        }
        catch (error) {
            console.error('Failed to get refactoring suggestions:', error);
            return [];
        }
    }
    /**
     * Get automated fixes for common violations
     */
    async getAutofixes(filePath) {
        try {
            const { getAutomatedFixes } = await this.loadConnascenceSystem();
            const fixes = await getAutomatedFixes({
                filePath,
                safeMode: this.getSafeMode()
            });
            return fixes.map((f) => ({
                line: f.line,
                column: f.column,
                endLine: f.endLine,
                endColumn: f.endColumn,
                issue: f.issue,
                description: f.description,
                replacement: f.replacement
            }));
        }
        catch (error) {
            console.error('Failed to get autofixes:', error);
            return [];
        }
    }
    /**
     * Generate comprehensive report
     */
    async generateReport(workspacePath) {
        try {
            const { generateConnascenceReport } = await this.loadConnascenceSystem();
            const options = {
                inputPath: workspacePath,
                outputPath: path.join(workspacePath, '.connascence-report.json'),
                format: 'json',
                verbose: true,
                includeTests: this.getIncludeTests(),
                safetyProfile: this.getSafetyProfile(),
                threshold: this.getThreshold(),
                exclude: this.getExcludePatterns(),
                generateMetrics: true,
                includeRecommendations: true
            };
            return await generateConnascenceReport(options);
        }
        catch (error) {
            console.error('Failed to generate report:', error);
            throw error;
        }
    }
    /**
     * Load the main connascence analysis system
     */
    async loadConnascenceSystem() {
        try {
            // Load from the consolidated enterprise system
            const analyzerPath = this.workspaceRoot ?
                path.join(this.workspaceRoot, 'analyzer', 'ast_engine', 'core_analyzer.py') :
                undefined;
            if (analyzerPath) {
                // Use Python subprocess to call our consolidated analyzer
                const { spawn } = require('child_process');
                return {
                    generateConnascenceReport: async (options) => {
                        return new Promise((resolve, reject) => {
                            const pythonProcess = spawn('python', [
                                '-c',
                                `
from analyzer.ast_engine.core_analyzer import ConnascenceASTAnalyzer
from pathlib import Path
import json

analyzer = ConnascenceASTAnalyzer()
result = analyzer.analyze_directory(Path('${options.inputPath}'))
violations = [{'type': v.type.value, 'severity': v.severity.value, 'file_path': v.file_path, 'line_number': v.line_number, 'description': v.description, 'recommendation': v.recommendation} for v in result.violations]
print(json.dumps({'violations': violations, 'summary': {'total_violations': len(violations)}}))
                                `.trim()
                            ], { cwd: this.workspaceRoot });
                            let output = '';
                            pythonProcess.stdout.on('data', (data) => {
                                output += data.toString();
                            });
                            pythonProcess.on('close', (code) => {
                                if (code === 0) {
                                    try {
                                        resolve(JSON.parse(output));
                                    }
                                    catch (e) {
                                        reject(new Error('Failed to parse analyzer output'));
                                    }
                                }
                                else {
                                    reject(new Error(`Python analyzer failed with code ${code}`));
                                }
                            });
                        });
                    }
                };
            }
            // Fallback: try to load from relative path
            const relativePath = path.join(__dirname, '..', '..', '..', 'src', 'reports', 'index.js');
            return require(relativePath);
        }
        catch (error) {
            console.error('Failed to load connascence system:', error);
            throw new Error('Main connascence analysis system not available');
        }
    }
    /**
     * Convert main system report to VS Code format
     */
    convertReportToAnalysisResult(report, filePath) {
        const findings = [];
        if (report.findings) {
            for (const finding of report.findings) {
                // Only include findings for the requested file
                if (finding.file && path.resolve(finding.file) === path.resolve(filePath)) {
                    findings.push({
                        id: finding.id || `${finding.type}_${finding.line}`,
                        type: finding.type,
                        severity: this.mapSeverity(finding.severity),
                        message: finding.message,
                        file: finding.file,
                        line: finding.line,
                        column: finding.column,
                        suggestion: finding.suggestion || finding.recommendation
                    });
                }
            }
        }
        return {
            findings,
            qualityScore: report.qualityScore || this.calculateQualityScore(findings),
            summary: {
                totalIssues: findings.length,
                issuesBySeverity: this.calculateSeverityBreakdown(findings)
            }
        };
    }
    /**
     * Convert report to workspace result format
     */
    convertReportToWorkspaceResult(report) {
        const fileResults = {};
        let totalIssues = 0;
        // Group findings by file
        if (report.findings) {
            const findingsByFile = new Map();
            for (const finding of report.findings) {
                const file = finding.file || 'unknown';
                if (!findingsByFile.has(file)) {
                    findingsByFile.set(file, []);
                }
                findingsByFile.get(file).push(finding);
            }
            // Convert each file's findings
            for (const [file, findings] of findingsByFile) {
                const convertedFindings = findings.map(f => ({
                    id: f.id || `${f.type}_${f.line}`,
                    type: f.type,
                    severity: this.mapSeverity(f.severity),
                    message: f.message,
                    file: f.file,
                    line: f.line,
                    column: f.column,
                    suggestion: f.suggestion || f.recommendation
                }));
                fileResults[file] = {
                    findings: convertedFindings,
                    qualityScore: this.calculateQualityScore(convertedFindings),
                    summary: {
                        totalIssues: convertedFindings.length,
                        issuesBySeverity: this.calculateSeverityBreakdown(convertedFindings)
                    }
                };
                totalIssues += convertedFindings.length;
            }
        }
        return {
            fileResults,
            summary: {
                filesAnalyzed: Object.keys(fileResults).length,
                totalIssues,
                qualityScore: report.overallQualityScore || this.calculateOverallQualityScore(fileResults)
            }
        };
    }
    /**
     * Fallback analysis when main system is not available
     */
    async fallbackAnalyzeFile(filePath) {
        const findings = [];
        try {
            const document = await vscode.workspace.openTextDocument(filePath);
            const text = document.getText();
            const lines = text.split('\\n');
            // Simple pattern matching for common issues
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i];
                const lineNumber = i + 1;
                // Magic numbers
                const magicNumbers = line.match(/\\b(\\d{2,})\\b/g);
                if (magicNumbers) {
                    findings.push({
                        id: `magic_number_${lineNumber}`,
                        type: 'magic_number',
                        severity: 'minor',
                        message: `Magic number found: ${magicNumbers[0]}`,
                        file: filePath,
                        line: lineNumber,
                        suggestion: 'Extract to a named constant'
                    });
                }
                // Long parameter lists
                if (line.includes('def ') && (line.match(/,/g) || []).length >= 4) {
                    findings.push({
                        id: `long_params_${lineNumber}`,
                        type: 'long_parameter_list',
                        severity: 'major',
                        message: 'Function has too many parameters',
                        file: filePath,
                        line: lineNumber,
                        suggestion: 'Consider using a parameter object or breaking down the function'
                    });
                }
            }
        }
        catch (error) {
            console.error('Fallback analysis failed:', error);
        }
        return {
            findings,
            qualityScore: this.calculateQualityScore(findings),
            summary: {
                totalIssues: findings.length,
                issuesBySeverity: this.calculateSeverityBreakdown(findings)
            }
        };
    }
    // Configuration helpers
    getSafetyProfile() {
        const config = vscode.workspace.getConfiguration('connascence');
        return config.get('safetyProfile', 'modern_general');
    }
    getThreshold() {
        const config = vscode.workspace.getConfiguration('connascence');
        return config.get('threshold', 0.8);
    }
    getIncludeTests() {
        const config = vscode.workspace.getConfiguration('connascence');
        return config.get('includeTests', false);
    }
    getStrictMode() {
        const config = vscode.workspace.getConfiguration('connascence');
        return config.get('strictMode', false);
    }
    getSafeMode() {
        const config = vscode.workspace.getConfiguration('connascence');
        return config.get('safeMode', true);
    }
    getExcludePatterns() {
        const config = vscode.workspace.getConfiguration('connascence');
        return config.get('exclude', [
            'node_modules/**',
            '.git/**',
            '__pycache__/**',
            '*.test.*',
            'test/**'
        ]);
    }
    // Utility methods
    mapSeverity(severity) {
        const severityMap = {
            'critical': 'critical',
            'high': 'major',
            'medium': 'minor',
            'low': 'info',
            'error': 'critical',
            'warning': 'major',
            'info': 'info'
        };
        return severityMap[severity.toLowerCase()] || 'info';
    }
    calculateQualityScore(findings) {
        if (findings.length === 0)
            return 100;
        const weights = { critical: 10, major: 5, minor: 2, info: 1 };
        const totalWeight = findings.reduce((sum, f) => sum + weights[f.severity], 0);
        return Math.max(0, 100 - totalWeight);
    }
    calculateSeverityBreakdown(findings) {
        return findings.reduce((acc, finding) => {
            acc[finding.severity]++;
            return acc;
        }, { critical: 0, major: 0, minor: 0, info: 0 });
    }
    calculateOverallQualityScore(fileResults) {
        const scores = Object.values(fileResults).map(r => r.qualityScore);
        return scores.length > 0 ? scores.reduce((sum, score) => sum + score, 0) / scores.length : 100;
    }
}
exports.ConnascenceApiClient = ConnascenceApiClient;
//# sourceMappingURL=connascenceApiClient.js.map