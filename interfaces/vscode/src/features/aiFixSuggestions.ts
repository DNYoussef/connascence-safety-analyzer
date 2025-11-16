import * as vscode from 'vscode';
import { Finding } from '../services/connascenceService';

export interface FixSuggestion {
    title: string;
    description: string;
    kind: vscode.CodeActionKind;
    edit: vscode.WorkspaceEdit;
    isAIGenerated: boolean;
    confidence: number; // 0-1
    violationType: string;
}

export class AIFixSuggestionsProvider {
    private static instance: AIFixSuggestionsProvider;
    private activeFindings: Finding[] = [];

    private constructor() {}

    public static getInstance(): AIFixSuggestionsProvider {
        if (!AIFixSuggestionsProvider.instance) {
            AIFixSuggestionsProvider.instance = new AIFixSuggestionsProvider();
        }
        return AIFixSuggestionsProvider.instance;
    }

    public async generateFixSuggestions(finding: Finding, document: vscode.TextDocument): Promise<FixSuggestion[]> {
        const suggestions: FixSuggestion[] = [];
        
        // Add rule-based suggestions first
        suggestions.push(...this.getRuleBasedSuggestions(finding, document));
        
        // Add AI-generated suggestions if enabled
        const config = vscode.workspace.getConfiguration('connascence');
        const aiEnabled = config.get<boolean>('aiIntegration', true);
        
        if (aiEnabled) {
            const aiSuggestions = await this.getAISuggestions(finding, document);
            suggestions.push(...aiSuggestions);
        }
        
        return suggestions.sort((a, b) => b.confidence - a.confidence);
    }

    public updateActiveFindings(findings: Finding[]): void {
        this.activeFindings = findings;
    }

    private getRuleBasedSuggestions(finding: Finding, document: vscode.TextDocument): FixSuggestion[] {
        const suggestions: FixSuggestion[] = [];
        
        switch (finding.type) {
            case 'connascence_of_name':
                suggestions.push(...this.getNameCouplingFixes(finding, document));
                break;
            case 'connascence_of_type':
                suggestions.push(...this.getTypeCouplingFixes(finding, document));
                break;
            case 'connascence_of_meaning':
                suggestions.push(...this.getMeaningCouplingFixes(finding, document));
                break;
            case 'connascence_of_position':
                suggestions.push(...this.getPositionCouplingFixes(finding, document));
                break;
            case 'connascence_of_algorithm':
                suggestions.push(...this.getAlgorithmCouplingFixes(finding, document));
                break;
            case 'god_object':
            case 'god_class':
                suggestions.push(...this.getGodObjectFixes(finding, document));
                break;
            case 'god_function':
                suggestions.push(...this.getGodFunctionFixes(finding, document));
                break;
            default:
                suggestions.push(...this.getGenericFixes(finding, document));
        }
        
        return suggestions;
    }

    private getNameCouplingFixes(finding: Finding, document: vscode.TextDocument): FixSuggestion[] {
        const suggestions: FixSuggestion[] = [];
        
        // Suggest using constants for repeated names
        suggestions.push({
            title: '🔗💔 Extract to Constant',
            description: 'Break name coupling by extracting repeated names to constants',
            kind: vscode.CodeActionKind.RefactorExtract,
            edit: this.createConstantExtractionEdit(finding, document),
            isAIGenerated: false,
            confidence: 0.9,
            violationType: finding.type
        });

        // Suggest using enums for related names
        suggestions.push({
            title: '🔗✂️ Create Enum',
            description: 'Group related names into an enum to reduce coupling',
            kind: vscode.CodeActionKind.RefactorExtract,
            edit: this.createEnumExtractionEdit(finding, document),
            isAIGenerated: false,
            confidence: 0.8,
            violationType: finding.type
        });

        return suggestions;
    }

    private getTypeCouplingFixes(finding: Finding, document: vscode.TextDocument): FixSuggestion[] {
        const suggestions: FixSuggestion[] = [];
        
        // Suggest interface extraction
        suggestions.push({
            title: '⛓️💥 Extract Interface',
            description: 'Break type coupling by introducing an interface',
            kind: vscode.CodeActionKind.RefactorExtract,
            edit: this.createInterfaceExtractionEdit(finding, document),
            isAIGenerated: false,
            confidence: 0.85,
            violationType: finding.type
        });

        // Suggest generic types
        suggestions.push({
            title: '⛓️🔧 Add Generic Type',
            description: 'Use generic types to reduce specific type coupling',
            kind: vscode.CodeActionKind.RefactorRewrite,
            edit: this.createGenericTypeEdit(finding, document),
            isAIGenerated: false,
            confidence: 0.75,
            violationType: finding.type
        });

        return suggestions;
    }

    private getMeaningCouplingFixes(finding: Finding, document: vscode.TextDocument): FixSuggestion[] {
        const suggestions: FixSuggestion[] = [];
        
        // Suggest extracting magic numbers/strings
        suggestions.push({
            title: '🔐💢 Extract Magic Value',
            description: 'Replace magic values with named constants',
            kind: vscode.CodeActionKind.RefactorExtract,
            edit: this.createMagicValueExtractionEdit(finding, document),
            isAIGenerated: false,
            confidence: 0.95,
            violationType: finding.type
        });

        return suggestions;
    }

    private getPositionCouplingFixes(finding: Finding, document: vscode.TextDocument): FixSuggestion[] {
        const suggestions: FixSuggestion[] = [];
        
        // Suggest using named parameters
        suggestions.push({
            title: '🔗📍 Use Named Parameters',
            description: 'Replace positional parameters with named ones',
            kind: vscode.CodeActionKind.RefactorRewrite,
            edit: this.createNamedParametersEdit(finding, document),
            isAIGenerated: false,
            confidence: 0.9,
            violationType: finding.type
        });

        return suggestions;
    }

    private getAlgorithmCouplingFixes(finding: Finding, document: vscode.TextDocument): FixSuggestion[] {
        const suggestions: FixSuggestion[] = [];
        
        // Suggest strategy pattern
        suggestions.push({
            title: '⚙️🔗 Apply Strategy Pattern',
            description: 'Extract algorithm to separate strategy classes',
            kind: vscode.CodeActionKind.RefactorExtract,
            edit: this.createStrategyPatternEdit(finding, document),
            isAIGenerated: false,
            confidence: 0.8,
            violationType: finding.type
        });

        return suggestions;
    }

    private getGodObjectFixes(finding: Finding, document: vscode.TextDocument): FixSuggestion[] {
        const suggestions: FixSuggestion[] = [];
        
        // Suggest splitting the class
        suggestions.push({
            title: '👑⚡ Split God Class',
            description: 'Break down the god class into smaller, focused classes',
            kind: vscode.CodeActionKind.RefactorExtract,
            edit: this.createClassSplittingEdit(finding, document),
            isAIGenerated: false,
            confidence: 0.85,
            violationType: finding.type
        });

        // Suggest extracting responsibilities
        suggestions.push({
            title: '🏛️⚠️ Extract Responsibilities',
            description: 'Move related methods to separate classes',
            kind: vscode.CodeActionKind.RefactorMove,
            edit: this.createResponsibilityExtractionEdit(finding, document),
            isAIGenerated: false,
            confidence: 0.8,
            violationType: finding.type
        });

        return suggestions;
    }

    private getGodFunctionFixes(finding: Finding, document: vscode.TextDocument): FixSuggestion[] {
        const suggestions: FixSuggestion[] = [];
        
        // Suggest function splitting
        suggestions.push({
            title: '⚡🔥 Split Function',
            description: 'Break down the large function into smaller functions',
            kind: vscode.CodeActionKind.RefactorExtract,
            edit: this.createFunctionSplittingEdit(finding, document),
            isAIGenerated: false,
            confidence: 0.9,
            violationType: finding.type
        });

        return suggestions;
    }

    private getGenericFixes(finding: Finding, document: vscode.TextDocument): FixSuggestion[] {
        const suggestions: FixSuggestion[] = [];
        
        // Suggest adding documentation
        suggestions.push({
            title: '📚 Add Documentation',
            description: 'Document the violation to help future maintainers',
            kind: vscode.CodeActionKind.Source,
            edit: this.createDocumentationEdit(finding, document),
            isAIGenerated: false,
            confidence: 0.6,
            violationType: finding.type
        });

        return suggestions;
    }

    private async getAISuggestions(finding: Finding, document: vscode.TextDocument): Promise<FixSuggestion[]> {
        try {
            // Simulate AI-generated suggestions
            // In a real implementation, this would call an AI service
            const context = this.extractContext(finding, document);
            const aiSuggestion = await this.callAIService(finding, context);
            
            if (aiSuggestion) {
                return [{
                    title: `🤖 AI: ${aiSuggestion.title}`,
                    description: aiSuggestion.description,
                    kind: vscode.CodeActionKind.RefactorRewrite,
                    edit: aiSuggestion.edit,
                    isAIGenerated: true,
                    confidence: aiSuggestion.confidence,
                    violationType: finding.type
                }];
            }
        } catch (error) {
            console.error('AI suggestion generation failed:', error);
        }
        
        return [];
    }

    private extractContext(finding: Finding, document: vscode.TextDocument): string {
        const line = finding.line - 1;
        const startLine = Math.max(0, line - 5);
        const endLine = Math.min(document.lineCount - 1, line + 5);
        
        let context = '';
        for (let i = startLine; i <= endLine; i++) {
            const prefix = i === line ? '>>> ' : '    ';
            context += `${prefix}${document.lineAt(i).text}\n`;
        }
        
        return context;
    }

    private async callAIService(finding: Finding, context: string): Promise<{
        title: string,
        description: string,
        edit: vscode.WorkspaceEdit,
        confidence: number
    } | null> {
        // Simulate AI processing delay
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Mock AI response based on violation type
        const mockResponses = {
            'connascence_of_name': {
                title: 'Introduce Symbolic Constants',
                description: 'AI suggests creating a constants module to centralize name definitions',
                confidence: 0.85
            },
            'god_object': {
                title: 'Apply Single Responsibility Principle',
                description: 'AI recommends splitting this class based on cohesive method groups',
                confidence: 0.9
            }
        };
        
        const response = mockResponses[finding.type as keyof typeof mockResponses];
        if (response) {
            return {
                ...response,
                edit: new vscode.WorkspaceEdit() // Mock empty edit
            };
        }
        
        return null;
    }

    // Edit creation helpers
    private createConstantExtractionEdit(finding: Finding, document: vscode.TextDocument): vscode.WorkspaceEdit {
        const edit = new vscode.WorkspaceEdit();
        
        // Add a comment suggesting constant extraction
        const line = Math.max(0, finding.line - 2);
        const position = new vscode.Position(line, 0);
        edit.insert(document.uri, position, `# TODO: Extract repeated name to constant\n`);
        
        return edit;
    }

    private createEnumExtractionEdit(finding: Finding, document: vscode.TextDocument): vscode.WorkspaceEdit {
        const edit = new vscode.WorkspaceEdit();
        
        const line = Math.max(0, finding.line - 2);
        const position = new vscode.Position(line, 0);
        edit.insert(document.uri, position, `# TODO: Consider using enum for related names\n`);
        
        return edit;
    }

    private createInterfaceExtractionEdit(finding: Finding, document: vscode.TextDocument): vscode.WorkspaceEdit {
        const edit = new vscode.WorkspaceEdit();
        
        const line = Math.max(0, finding.line - 2);
        const position = new vscode.Position(line, 0);
        edit.insert(document.uri, position, `# TODO: Extract interface to reduce type coupling\n`);
        
        return edit;
    }

    private createGenericTypeEdit(finding: Finding, document: vscode.TextDocument): vscode.WorkspaceEdit {
        const edit = new vscode.WorkspaceEdit();
        
        const line = Math.max(0, finding.line - 2);
        const position = new vscode.Position(line, 0);
        edit.insert(document.uri, position, `# TODO: Consider using generic types\n`);
        
        return edit;
    }

    private createMagicValueExtractionEdit(finding: Finding, document: vscode.TextDocument): vscode.WorkspaceEdit {
        const edit = new vscode.WorkspaceEdit();
        
        const line = Math.max(0, finding.line - 2);
        const position = new vscode.Position(line, 0);
        edit.insert(document.uri, position, `# TODO: Extract magic value to named constant\n`);
        
        return edit;
    }

    private createNamedParametersEdit(finding: Finding, document: vscode.TextDocument): vscode.WorkspaceEdit {
        const edit = new vscode.WorkspaceEdit();
        
        const line = Math.max(0, finding.line - 2);
        const position = new vscode.Position(line, 0);
        edit.insert(document.uri, position, `# TODO: Use named parameters instead of positional\n`);
        
        return edit;
    }

    private createStrategyPatternEdit(finding: Finding, document: vscode.TextDocument): vscode.WorkspaceEdit {
        const edit = new vscode.WorkspaceEdit();
        
        const line = Math.max(0, finding.line - 2);
        const position = new vscode.Position(line, 0);
        edit.insert(document.uri, position, `# TODO: Apply Strategy pattern to decouple algorithm\n`);
        
        return edit;
    }

    private createClassSplittingEdit(finding: Finding, document: vscode.TextDocument): vscode.WorkspaceEdit {
        const edit = new vscode.WorkspaceEdit();
        
        const line = Math.max(0, finding.line - 2);
        const position = new vscode.Position(line, 0);
        edit.insert(document.uri, position, `# TODO: Split this god class into smaller, focused classes\n`);
        
        return edit;
    }

    private createResponsibilityExtractionEdit(finding: Finding, document: vscode.TextDocument): vscode.WorkspaceEdit {
        const edit = new vscode.WorkspaceEdit();
        
        const line = Math.max(0, finding.line - 2);
        const position = new vscode.Position(line, 0);
        edit.insert(document.uri, position, `# TODO: Extract responsibilities to separate classes\n`);
        
        return edit;
    }

    private createFunctionSplittingEdit(finding: Finding, document: vscode.TextDocument): vscode.WorkspaceEdit {
        const edit = new vscode.WorkspaceEdit();
        
        const line = Math.max(0, finding.line - 2);
        const position = new vscode.Position(line, 0);
        edit.insert(document.uri, position, `# TODO: Break down this large function into smaller functions\n`);
        
        return edit;
    }

    private createDocumentationEdit(finding: Finding, document: vscode.TextDocument): vscode.WorkspaceEdit {
        const edit = new vscode.WorkspaceEdit();
        
        const line = Math.max(0, finding.line - 2);
        const position = new vscode.Position(line, 0);
        edit.insert(document.uri, position, `# NOTE: ${finding.message}\n`);
        
        return edit;
    }
}