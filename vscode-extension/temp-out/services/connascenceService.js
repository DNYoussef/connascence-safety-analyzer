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
exports.ConnascenceService = void 0;
const path = __importStar(require("path"));
const child_process_1 = require("child_process");
const connascenceApiClient_1 = require("./connascenceApiClient");
class ConnascenceService {
    constructor(configService, telemetryService) {
        this.configService = configService;
        this.telemetryService = telemetryService;
        this.apiClient = new connascenceApiClient_1.ConnascenceApiClient();
    }
    async analyzeFile(filePath) {
        this.telemetryService.logEvent('file.analysis.started', { file: path.basename(filePath) });
        try {
            // Use the integrated API client
            return await this.apiClient.analyzeFile(filePath);
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            this.telemetryService.logEvent('file.analysis.error', { error: errorMessage });
            throw error;
        }
    }
    async analyzeWorkspace(workspacePath) {
        this.telemetryService.logEvent('workspace.analysis.started');
        try {
            return await this.apiClient.analyzeWorkspace(workspacePath);
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            this.telemetryService.logEvent('workspace.analysis.error', { error: errorMessage });
            throw error;
        }
    }
    async validateSafety(filePath, profile) {
        this.telemetryService.logEvent('safety.validation.started', { profile });
        try {
            return await this.apiClient.validateSafety(filePath, profile);
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            this.telemetryService.logEvent('safety.validation.error', { error: errorMessage });
            throw error;
        }
    }
    async suggestRefactoring(filePath, selection) {
        this.telemetryService.logEvent('refactoring.suggestion.requested');
        try {
            return await this.apiClient.suggestRefactoring(filePath, selection);
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            this.telemetryService.logEvent('refactoring.suggestion.error', { error: errorMessage });
            throw error;
        }
    }
    async getAutofixes(filePath) {
        this.telemetryService.logEvent('autofix.requested');
        try {
            return await this.apiClient.getAutofixes(filePath);
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            this.telemetryService.logEvent('autofix.error', { error: errorMessage });
            throw error;
        }
    }
    async generateReport(workspacePath) {
        this.telemetryService.logEvent('report.generation.started');
        try {
            return await this.apiClient.generateReport(workspacePath);
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            this.telemetryService.logEvent('report.generation.error', { error: errorMessage });
            throw error;
        }
    }
    // MCP implementations
    async analyzeMCP(filePath) {
        // TODO: Implement MCP analysis
        throw new Error('MCP analysis not yet implemented');
    }
    async analyzeWorkspaceMCP(workspacePath) {
        // TODO: Implement MCP workspace analysis
        throw new Error('MCP workspace analysis not yet implemented');
    }
    async validateSafetyMCP(filePath, profile) {
        // TODO: Implement MCP safety validation
        throw new Error('MCP safety validation not yet implemented');
    }
    async suggestRefactoringMCP(filePath, selection) {
        // TODO: Implement MCP refactoring suggestions
        throw new Error('MCP refactoring suggestions not yet implemented');
    }
    async getAutofixesMCP(filePath) {
        // TODO: Implement MCP autofixes
        throw new Error('MCP autofixes not yet implemented');
    }
    async generateReportMCP(workspacePath) {
        // TODO: Implement MCP report generation
        throw new Error('MCP report generation not yet implemented');
    }
    // CLI implementations
    async analyzeCLI(filePath) {
        const safetyProfile = this.configService.getSafetyProfile();
        const cmd = 'connascence';
        const args = ['analyze', filePath, '--profile', safetyProfile, '--format', 'json'];
        return new Promise((resolve, reject) => {
            const process = (0, child_process_1.spawn)(cmd, args);
            let stdout = '';
            let stderr = '';
            process.stdout.on('data', (data) => stdout += data.toString());
            process.stderr.on('data', (data) => stderr += data.toString());
            process.on('close', (code) => {
                if (code === 0) {
                    try {
                        const result = JSON.parse(stdout);
                        resolve(this.transformCLIResult(result));
                    }
                    catch (e) {
                        const errorMessage = e instanceof Error ? e.message : String(e);
                        reject(new Error(`Failed to parse CLI output: ${errorMessage}`));
                    }
                }
                else {
                    reject(new Error(`CLI failed with code ${code}: ${stderr}`));
                }
            });
            process.on('error', (err) => {
                reject(new Error(`Failed to run CLI: ${err.message}`));
            });
        });
    }
    async analyzeWorkspaceCLI(workspacePath) {
        const safetyProfile = this.configService.getSafetyProfile();
        const cmd = 'connascence';
        const args = ['analyze', workspacePath, '--profile', safetyProfile, '--format', 'json', '--recursive'];
        return new Promise((resolve, reject) => {
            const process = (0, child_process_1.spawn)(cmd, args);
            let stdout = '';
            let stderr = '';
            process.stdout.on('data', (data) => stdout += data.toString());
            process.stderr.on('data', (data) => stderr += data.toString());
            process.on('close', (code) => {
                if (code === 0) {
                    try {
                        const result = JSON.parse(stdout);
                        resolve(this.transformWorkspaceResult(result));
                    }
                    catch (e) {
                        const errorMessage = e instanceof Error ? e.message : String(e);
                        reject(new Error(`Failed to parse CLI output: ${errorMessage}`));
                    }
                }
                else {
                    reject(new Error(`CLI failed with code ${code}: ${stderr}`));
                }
            });
            process.on('error', (err) => {
                reject(new Error(`Failed to run CLI: ${err.message}`));
            });
        });
    }
    async validateSafetyCLI(filePath, profile) {
        const cmd = 'connascence';
        const args = ['validate-safety', filePath, '--profile', profile, '--format', 'json'];
        return new Promise((resolve, reject) => {
            const process = (0, child_process_1.spawn)(cmd, args);
            let stdout = '';
            let stderr = '';
            process.stdout.on('data', (data) => stdout += data.toString());
            process.stderr.on('data', (data) => stderr += data.toString());
            process.on('close', (code) => {
                try {
                    const result = JSON.parse(stdout || '{}');
                    resolve({
                        compliant: code === 0,
                        violations: result.violations || []
                    });
                }
                catch (e) {
                    const errorMessage = e instanceof Error ? e.message : String(e);
                    reject(new Error(`Failed to parse safety validation output: ${errorMessage}`));
                }
            });
            process.on('error', (err) => {
                reject(new Error(`Failed to run safety validation: ${err.message}`));
            });
        });
    }
    async suggestRefactoringCLI(filePath, selection) {
        const cmd = 'connascence';
        const args = ['suggest-refactoring', filePath, '--format', 'json'];
        if (selection) {
            args.push('--line', selection.start.line.toString());
        }
        return new Promise((resolve, reject) => {
            const process = (0, child_process_1.spawn)(cmd, args);
            let stdout = '';
            let stderr = '';
            process.stdout.on('data', (data) => stdout += data.toString());
            process.stderr.on('data', (data) => stderr += data.toString());
            process.on('close', (code) => {
                if (code === 0) {
                    try {
                        const result = JSON.parse(stdout);
                        resolve(result.suggestions || []);
                    }
                    catch (e) {
                        const errorMessage = e instanceof Error ? e.message : String(e);
                        reject(new Error(`Failed to parse refactoring suggestions: ${errorMessage}`));
                    }
                }
                else {
                    reject(new Error(`Refactoring suggestion failed: ${stderr}`));
                }
            });
            process.on('error', (err) => {
                reject(new Error(`Failed to run refactoring suggestion: ${err.message}`));
            });
        });
    }
    async getAutofixesCLI(filePath) {
        const cmd = 'connascence';
        const args = ['autofix', filePath, '--dry-run', '--format', 'json'];
        return new Promise((resolve, reject) => {
            const process = (0, child_process_1.spawn)(cmd, args);
            let stdout = '';
            let stderr = '';
            process.stdout.on('data', (data) => stdout += data.toString());
            process.stderr.on('data', (data) => stderr += data.toString());
            process.on('close', (code) => {
                if (code === 0) {
                    try {
                        const result = JSON.parse(stdout);
                        resolve(result.fixes || []);
                    }
                    catch (e) {
                        const errorMessage = e instanceof Error ? e.message : String(e);
                        reject(new Error(`Failed to parse autofix output: ${errorMessage}`));
                    }
                }
                else {
                    reject(new Error(`Autofix failed: ${stderr}`));
                }
            });
            process.on('error', (err) => {
                reject(new Error(`Failed to run autofix: ${err.message}`));
            });
        });
    }
    async generateReportCLI(workspacePath) {
        const cmd = 'connascence';
        const args = ['report', workspacePath, '--format', 'json'];
        return new Promise((resolve, reject) => {
            const process = (0, child_process_1.spawn)(cmd, args);
            let stdout = '';
            let stderr = '';
            process.stdout.on('data', (data) => stdout += data.toString());
            process.stderr.on('data', (data) => stderr += data.toString());
            process.on('close', (code) => {
                if (code === 0) {
                    try {
                        const result = JSON.parse(stdout);
                        resolve(result);
                    }
                    catch (e) {
                        const errorMessage = e instanceof Error ? e.message : String(e);
                        reject(new Error(`Failed to parse report output: ${errorMessage}`));
                    }
                }
                else {
                    reject(new Error(`Report generation failed: ${stderr}`));
                }
            });
            process.on('error', (err) => {
                reject(new Error(`Failed to generate report: ${err.message}`));
            });
        });
    }
    transformCLIResult(result) {
        const findings = result.findings || result.violations || [];
        return {
            findings: findings.map((f) => ({
                id: f.id || `${f.type}_${f.line}`,
                type: f.type || f.rule_id,
                severity: f.severity || 'info',
                message: f.message || f.description,
                file: f.file || f.file_path,
                line: f.line || f.line_number,
                column: f.column || f.column_number,
                suggestion: f.suggestion || f.recommendation
            })),
            qualityScore: result.quality_score || result.score || 0,
            summary: {
                totalIssues: findings.length,
                issuesBySeverity: this.calculateSeveritySummary(findings)
            }
        };
    }
    transformWorkspaceResult(result) {
        const fileResults = {};
        if (result.files) {
            for (const [filePath, fileResult] of Object.entries(result.files)) {
                fileResults[filePath] = this.transformCLIResult(fileResult);
            }
        }
        return {
            fileResults,
            summary: {
                filesAnalyzed: Object.keys(fileResults).length,
                totalIssues: Object.values(fileResults).reduce((total, fr) => total + fr.findings.length, 0),
                qualityScore: result.overall_score || 0
            }
        };
    }
    calculateSeveritySummary(findings) {
        return findings.reduce((acc, finding) => {
            switch (finding.severity) {
                case 'critical':
                    acc.critical++;
                    break;
                case 'major':
                case 'high':
                    acc.major++;
                    break;
                case 'minor':
                case 'medium':
                    acc.minor++;
                    break;
                default:
                    acc.info++;
            }
            return acc;
        }, { critical: 0, major: 0, minor: 0, info: 0 });
    }
}
exports.ConnascenceService = ConnascenceService;
//# sourceMappingURL=connascenceService.js.map