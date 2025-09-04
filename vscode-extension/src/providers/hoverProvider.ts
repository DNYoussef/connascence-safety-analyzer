import * as vscode from 'vscode';
import { ConnascenceService, Finding } from '../services/connascenceService';
import { ConfigurationService } from '../services/configurationService';
import { AIIntegrationService } from '../services/aiIntegrationService';

export class ConnascenceHoverProvider implements vscode.HoverProvider {
    constructor(
        private connascenceService: ConnascenceService,
        private configService: ConfigurationService,
        private aiIntegrationService: AIIntegrationService
    ) {}

    async provideHover(
        document: vscode.TextDocument,
        position: vscode.Position,
        token: vscode.CancellationToken
    ): Promise<vscode.Hover | null> {
        // Check if there's a diagnostic at this position
        const diagnostics = vscode.languages.getDiagnostics(document.uri);
        const connascenceDiagnostics = diagnostics.filter(d => 
            d.source === 'connascence' && d.range.contains(position)
        );

        if (connascenceDiagnostics.length === 0) {
            return null;
        }

        const diagnostic = connascenceDiagnostics[0];
        const contents = await this.createHoverContent(diagnostic, document, position);
        
        return new vscode.Hover(contents, diagnostic.range);
    }

    private async createHoverContent(
        diagnostic: vscode.Diagnostic,
        document: vscode.TextDocument,
        position: vscode.Position
    ): Promise<vscode.MarkdownString[]> {
        const contents: vscode.MarkdownString[] = [];

        // Convert diagnostic to Finding for AI integration
        const finding: Finding = this.diagnosticToFinding(diagnostic, document);

        // Main diagnostic information
        const mainContent = new vscode.MarkdownString();
        mainContent.isTrusted = true;
        mainContent.supportHtml = true;

        // Header with severity and connascence icon
        const severityIcon = this.getSeverityIcon(diagnostic.severity);
        const connascenceIcon = this.getConnascenceIcon(diagnostic.code as string);
        mainContent.appendMarkdown(`${connascenceIcon} ${severityIcon} **${this.formatConnascenceType(diagnostic.code as string)}**\n`);
        mainContent.appendMarkdown(`*Severity: ${diagnostic.severity === vscode.DiagnosticSeverity.Error ? 'Critical' : 
            diagnostic.severity === vscode.DiagnosticSeverity.Warning ? 'Major' : 
            diagnostic.severity === vscode.DiagnosticSeverity.Information ? 'Minor' : 'Info'}*\n\n`);

        // Description
        mainContent.appendMarkdown(`**Issue:** ${diagnostic.message}\n\n`);

        // Connascence type explanation
        const connascenceType = this.extractConnascenceType(diagnostic.code as string);
        const explanation = this.getConnascenceExplanation(connascenceType);
        if (explanation) {
            mainContent.appendMarkdown(`**Theory:** ${explanation}\n\n`);
        }

        // Get AI-powered refactoring suggestions with confidence scores
        try {
            const suggestions = await this.getEnhancedSuggestions(finding, document);
            
            if (suggestions.length > 0) {
                mainContent.appendMarkdown(`**🤖 AI Refactoring Suggestions:**\n\n`);
                for (const suggestion of suggestions.slice(0, 3)) {
                    const confidenceBar = this.createConfidenceBar(suggestion.confidence);
                    const riskLevel = suggestion.confidence >= 80 ? '🟢' : suggestion.confidence >= 60 ? '🟡' : '🔴';
                    mainContent.appendMarkdown(`${riskLevel} **${suggestion.technique}** ${confidenceBar}\n`);
                    mainContent.appendMarkdown(`   *${suggestion.description}*\n`);
                    mainContent.appendMarkdown(`   [$(zap) Apply Fix](command:connascence.applySuggestion?${encodeURIComponent(JSON.stringify({ finding, suggestion }))}) | `);
                    mainContent.appendMarkdown(`[$(eye) Preview](command:connascence.previewSuggestion?${encodeURIComponent(JSON.stringify({ finding, suggestion }))})\n\n`);
                }
            }
        } catch (error) {
            // Show fallback suggestions
            const fallbackSuggestions = this.getFallbackSuggestions(connascenceType);
            if (fallbackSuggestions.length > 0) {
                mainContent.appendMarkdown(`**💡 Standard Refactoring Approaches:**\n\n`);
                for (const suggestion of fallbackSuggestions) {
                    mainContent.appendMarkdown(`• **${suggestion.technique}**: ${suggestion.description}\n`);
                }
                mainContent.appendMarkdown(`\n`);
            }
        }

        // Enhanced AI Actions Section
        if (this.configService.get('aiIntegration', true)) {
            mainContent.appendMarkdown(`---\n**🤖 AI Actions:**\n\n`);
            mainContent.appendMarkdown(`[$(robot) Auto-Fix](command:connascence.requestAIFix?${encodeURIComponent(JSON.stringify({ finding }))}) `);
            mainContent.appendMarkdown(`[$(lightbulb) Get Suggestions](command:connascence.getAISuggestions?${encodeURIComponent(JSON.stringify({ finding }))}) `);
            mainContent.appendMarkdown(`[$(comment-discussion) Explain](command:connascence.aiExplain?${encodeURIComponent(JSON.stringify({ finding }))}) `);
            mainContent.appendMarkdown(`[$(book) Learn More](https://docs.connascence.io/types/${connascenceType})\n\n`);
        } else {
            // Standard actions when AI is disabled
            mainContent.appendMarkdown(`**Actions:**\n`);
            mainContent.appendMarkdown(`[$(lightbulb) Quick Fix](command:editor.action.quickFix) `);
            mainContent.appendMarkdown(`[$(gear) Refactor](command:editor.action.refactor) `);
            mainContent.appendMarkdown(`[$(book) Learn More](command:connascence.explainFinding?${encodeURIComponent(JSON.stringify({ code: diagnostic.code }))})\n\n`);
        }

        // Performance and impact metrics
        const impactMetrics = this.calculateImpactMetrics(finding);
        if (impactMetrics) {
            mainContent.appendMarkdown(`**📊 Impact Analysis:**\n`);
            mainContent.appendMarkdown(`• Maintainability: ${impactMetrics.maintainability}\n`);
            mainContent.appendMarkdown(`• Testability: ${impactMetrics.testability}\n`);
            mainContent.appendMarkdown(`• Coupling Score: ${impactMetrics.couplingScore}/10\n\n`);
        }

        contents.push(mainContent);

        // Additional context from related information
        if (diagnostic.relatedInformation && diagnostic.relatedInformation.length > 0) {
            const relatedContent = new vscode.MarkdownString();
            relatedContent.isTrusted = true;
            relatedContent.appendMarkdown(`**🔍 Related Context:**\n\n`);
            
            for (const info of diagnostic.relatedInformation) {
                relatedContent.appendMarkdown(`• ${info.message}\n`);
            }
            
            contents.push(relatedContent);
        }

        return contents;
    }

    private getSeverityIcon(severity: vscode.DiagnosticSeverity): string {
        switch (severity) {
            case vscode.DiagnosticSeverity.Error:
                return '$(error)';
            case vscode.DiagnosticSeverity.Warning:
                return '$(warning)';
            case vscode.DiagnosticSeverity.Information:
                return '$(info)';
            case vscode.DiagnosticSeverity.Hint:
            default:
                return '$(lightbulb)';
        }
    }

    private extractConnascenceType(code: string): string {
        // Extract connascence type from diagnostic code
        if (code.startsWith('CON_')) {
            return code.replace('CON_', '').replace(/_/g, ' ').toLowerCase();
        }
        return code;
    }

    private getConnascenceExplanation(type: string): string | null {
        const explanations: { [key: string]: string } = {
            'position': 'Elements must be in the same order. When the order of parameters, arguments, or array elements matters for correctness.',
            'name': 'Elements must agree on the name of something. Multiple components referring to the same entity by name.',
            'type': 'Elements must agree on the type of something. Multiple components that must share the same data type.',
            'meaning': 'Elements must agree on the meaning of particular values. Multiple components that must agree on the meaning of specific values.',
            'algorithm': 'Elements must agree on a particular algorithm. Multiple components that must use the same algorithm or approach.',
            'timing': 'Elements must be executed at certain times relative to each other. Components that depend on specific timing relationships.',
            'value': 'Elements must agree on particular values. Multiple components that must use the same literal values.',
            'identity': 'Elements must reference the same entity. Multiple components that must refer to the same object or entity.',
            'execution': 'The order of execution of elements is important. Components where execution order affects correctness.'
        };

        return explanations[type] || null;
    }

    // === ENHANCED AI INTEGRATION METHODS ===

    private diagnosticToFinding(diagnostic: vscode.Diagnostic, document: vscode.TextDocument): Finding {
        return {
            id: (diagnostic.code as any)?.value || 'unknown',
            type: this.extractConnascenceType(diagnostic.code as string),
            severity: this.diagnosticSeverityToString(diagnostic.severity),
            message: diagnostic.message,
            file: document.fileName,
            line: diagnostic.range.start.line + 1,
            column: diagnostic.range.start.character + 1,
            suggestion: diagnostic.relatedInformation?.[0]?.message
        };
    }

    private diagnosticSeverityToString(severity: vscode.DiagnosticSeverity): 'critical' | 'major' | 'minor' | 'info' {
        switch (severity) {
            case vscode.DiagnosticSeverity.Error: return 'critical';
            case vscode.DiagnosticSeverity.Warning: return 'major';
            case vscode.DiagnosticSeverity.Information: return 'minor';
            default: return 'info';
        }
    }

    private async getEnhancedSuggestions(finding: Finding, document: vscode.TextDocument): Promise<any[]> {
        try {
            // Try to get AI-powered suggestions
            return await this.aiIntegrationService.getAISuggestionsData(finding, document);
        } catch (error) {
            // Fall back to standard suggestions
            return await this.connascenceService.suggestRefactoring(
                document.fileName,
                {
                    start: { line: finding.line - 1, character: (finding.column ?? 1) - 1 },
                    end: { line: finding.line - 1, character: (finding.column ?? 1) - 1 }
                }
            );
        }
    }

    private createConfidenceBar(confidence: number): string {
        const filled = Math.round(confidence / 20); // 0-5 filled squares
        const empty = 5 - filled;
        return '▓'.repeat(filled) + '░'.repeat(empty) + ` ${confidence}%`;
    }

    private getFallbackSuggestions(connascenceType: string): Array<{technique: string, description: string}> {
        const fallbackMap: { [key: string]: Array<{technique: string, description: string}> } = {
            'position': [
                { technique: 'Named Parameters', description: 'Use named parameters instead of positional' },
                { technique: 'Parameter Object', description: 'Group related parameters into an object' },
                { technique: 'Builder Pattern', description: 'Use builder pattern for complex construction' }
            ],
            'meaning': [
                { technique: 'Extract Constant', description: 'Move magic literal to named constant' },
                { technique: 'Enum/Constants Class', description: 'Create enum or constants class' },
                { technique: 'Configuration', description: 'Move to configuration file' }
            ],
            'name': [
                { technique: 'Rename Symbol', description: 'Use consistent naming across components' },
                { technique: 'Interface Abstraction', description: 'Define common interface' },
                { technique: 'Facade Pattern', description: 'Create unified naming facade' }
            ],
            'type': [
                { technique: 'Generic Types', description: 'Use generics for type flexibility' },
                { technique: 'Interface Segregation', description: 'Split into focused interfaces' },
                { technique: 'Type Adapter', description: 'Create type adaptation layer' }
            ],
            'algorithm': [
                { technique: 'Extract Method', description: 'Move algorithm to separate method' },
                { technique: 'Strategy Pattern', description: 'Encapsulate algorithm variations' },
                { technique: 'Single Responsibility', description: 'Split class responsibilities' }
            ]
        };

        return fallbackMap[connascenceType] || [
            { technique: 'Refactor', description: 'Consider refactoring to reduce coupling' }
        ];
    }

    private calculateImpactMetrics(finding: Finding): {
        maintainability: string;
        testability: string;
        couplingScore: number;
    } | null {
        // Simplified impact calculation based on finding type and severity
        const severityWeight = {
            'critical': 4,
            'major': 3,
            'minor': 2,
            'info': 1
        };

        const typeWeight = {
            'algorithm': 4,    // God objects are high impact
            'meaning': 3,      // Magic literals moderate-high impact
            'position': 2,     // Parameter order moderate impact
            'name': 1,         // Naming low-moderate impact
            'type': 2          // Type coupling moderate impact
        };

        const severity = severityWeight[finding.severity as keyof typeof severityWeight] || 1;
        const type = typeWeight[finding.type as keyof typeof typeWeight] || 2;
        const couplingScore = Math.min(10, severity + type);

        const maintainability = couplingScore >= 7 ? '🔴 High Impact' : 
                               couplingScore >= 5 ? '🟡 Medium Impact' : '🟢 Low Impact';

        const testability = couplingScore >= 7 ? '🔴 Hard to Test' : 
                          couplingScore >= 5 ? '🟡 Moderate' : '🟢 Easy to Test';

        return {
            maintainability,
            testability,
            couplingScore
        };
    }

    private getConnascenceIcon(code: string): string {
        const iconMap: { [key: string]: string } = {
            'god_object': '🏛️', 'large_class': '🏛️', 'algorithm': '🏛️', 'CoA': '🏛️',
            'magic_literal': '✨', 'meaning': '✨', 'CoM': '✨',
            'parameter_coupling': '🔗', 'position': '🔗', 'CoP': '🔗',
            'naming': '📛', 'name': '📛', 'CoN': '📛',
            'type_coupling': '🏷️', 'type': '🏷️', 'CoT': '🏷️',
            'timing': '⏰', 'CoTi': '⏰',
            'execution_order': '📝', 'execution': '📝', 'CoE': '📝',
            'value_coupling': '💎', 'value': '💎', 'CoV': '💎',
            'identity': '🆔', 'CoI': '🆔'
        };

        const codeStr = code?.toString().toLowerCase() || '';
        for (const [key, icon] of Object.entries(iconMap)) {
            if (codeStr.includes(key)) return icon;
        }
        return '⚠️';
    }

    private formatConnascenceType(code: string): string {
        const typeMap: { [key: string]: string } = {
            'CoN': 'Connascence of Name',
            'CoT': 'Connascence of Type', 
            'CoM': 'Connascence of Meaning',
            'CoP': 'Connascence of Position',
            'CoA': 'Connascence of Algorithm',
            'CoE': 'Connascence of Execution',
            'CoTi': 'Connascence of Timing',
            'CoV': 'Connascence of Value',
            'CoI': 'Connascence of Identity'
        };

        const codeStr = code?.toString() || '';
        for (const [key, formatted] of Object.entries(typeMap)) {
            if (codeStr.includes(key)) return formatted;
        }

        // Fallback formatting
        return codeStr.replace(/_/g, ' ')
                     .split(' ')
                     .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                     .join(' ') || 'Connascence Violation';
    }
}