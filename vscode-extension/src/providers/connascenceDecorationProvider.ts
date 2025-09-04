import * as vscode from 'vscode';
import { AnalysisResult, Finding } from '../services/connascenceService';

/**
 * Enhanced visual decoration provider for connascence violations
 * 
 * Provides bright, color-coded highlighting for different violation types,
 * replacing plain VS Code squiggles with rich visual indicators.
 */
export class ConnascenceDecorationProvider {
    private decorationTypes: Map<string, vscode.TextEditorDecorationType> = new Map();
    private activeDecorations: Map<string, vscode.DecorationOptions[]> = new Map();

    constructor() {
        this.initializeDecorationTypes();
    }

    private initializeDecorationTypes(): void {
        // Severity-based decorations with bright colors
        this.decorationTypes.set('critical', vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(255, 0, 0, 0.25)',
            border: '2px solid #ff0000',
            borderRadius: '4px',
            overviewRulerColor: '#ff0000',
            overviewRulerLane: vscode.OverviewRulerLane.Right,
            isWholeLine: false,
            fontWeight: 'bold'
        }));

        this.decorationTypes.set('major', vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(255, 165, 0, 0.2)',
            border: '1px solid #ffa500',
            borderRadius: '3px',
            overviewRulerColor: '#ffa500',
            overviewRulerLane: vscode.OverviewRulerLane.Right,
            isWholeLine: false
        }));

        this.decorationTypes.set('minor', vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(0, 150, 255, 0.15)',
            border: '1px solid #0096ff',
            borderRadius: '3px',
            overviewRulerColor: '#0096ff',
            overviewRulerLane: vscode.OverviewRulerLane.Right,
            isWholeLine: false
        }));

        this.decorationTypes.set('info', vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(128, 128, 128, 0.1)',
            border: '1px dotted #808080',
            borderRadius: '3px',
            overviewRulerColor: '#808080',
            overviewRulerLane: vscode.OverviewRulerLane.Right,
            isWholeLine: false
        }));

        // Specific connascence type decorations with distinct visual treatment
        this.decorationTypes.set('god_object', vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(148, 0, 211, 0.2)',
            border: '2px solid #9400d3',
            borderRadius: '4px',
            overviewRulerColor: '#9400d3',
            overviewRulerLane: vscode.OverviewRulerLane.Right,
            after: {
                contentText: ' 🏛️',
                color: '#9400d3',
                fontWeight: 'bold'
            },
            isWholeLine: false
        }));

        this.decorationTypes.set('magic_literal', vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(255, 20, 147, 0.2)',
            border: '1px solid #ff1493',
            borderRadius: '3px',
            overviewRulerColor: '#ff1493',
            overviewRulerLane: vscode.OverviewRulerLane.Right,
            after: {
                contentText: ' ✨',
                color: '#ff1493',
                fontWeight: 'bold'
            },
            isWholeLine: false
        }));

        this.decorationTypes.set('parameter_coupling', vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(255, 140, 0, 0.2)',
            border: '1px solid #ff8c00',
            borderRadius: '3px',
            overviewRulerColor: '#ff8c00',
            overviewRulerLane: vscode.OverviewRulerLane.Right,
            after: {
                contentText: ' 🔗',
                color: '#ff8c00',
                fontWeight: 'bold'
            },
            isWholeLine: false
        }));

        this.decorationTypes.set('naming', vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(50, 205, 50, 0.15)',
            border: '1px solid #32cd32',
            borderRadius: '3px',
            overviewRulerColor: '#32cd32',
            overviewRulerLane: vscode.OverviewRulerLane.Right,
            after: {
                contentText: ' 📛',
                color: '#32cd32'
            },
            isWholeLine: false
        }));

        this.decorationTypes.set('type_coupling', vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(75, 0, 130, 0.2)',
            border: '1px solid #4b0082',
            borderRadius: '3px',
            overviewRulerColor: '#4b0082',
            overviewRulerLane: vscode.OverviewRulerLane.Right,
            after: {
                contentText: ' 🏷️',
                color: '#4b0082'
            },
            isWholeLine: false
        }));

        this.decorationTypes.set('timing', vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(255, 215, 0, 0.2)',
            border: '1px solid #ffd700',
            borderRadius: '3px',
            overviewRulerColor: '#ffd700',
            overviewRulerLane: vscode.OverviewRulerLane.Right,
            after: {
                contentText: ' ⏰',
                color: '#ffd700'
            },
            isWholeLine: false
        }));

        this.decorationTypes.set('execution_order', vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(220, 20, 60, 0.2)',
            border: '1px solid #dc143c',
            borderRadius: '3px',
            overviewRulerColor: '#dc143c',
            overviewRulerLane: vscode.OverviewRulerLane.Right,
            after: {
                contentText: ' 📝',
                color: '#dc143c'
            },
            isWholeLine: false
        }));

        this.decorationTypes.set('value_coupling', vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(30, 144, 255, 0.2)',
            border: '1px solid #1e90ff',
            borderRadius: '3px',
            overviewRulerColor: '#1e90ff',
            overviewRulerLane: vscode.OverviewRulerLane.Right,
            after: {
                contentText: ' 💎',
                color: '#1e90ff'
            },
            isWholeLine: false
        }));

        this.decorationTypes.set('identity', vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(138, 43, 226, 0.2)',
            border: '1px solid #8a2be2',
            borderRadius: '3px',
            overviewRulerColor: '#8a2be2',
            overviewRulerLane: vscode.OverviewRulerLane.Right,
            after: {
                contentText: ' 🆔',
                color: '#8a2be2'
            },
            isWholeLine: false
        }));
    }

    /**
     * Update decorations for the given editor with analysis results
     */
    updateDecorations(editor: vscode.TextEditor, results: AnalysisResult): void {
        if (!editor || !results) {
            return;
        }

        // Clear existing decorations
        this.clearDecorations(editor);

        // Group findings by decoration type
        const decorationsByType = this.groupFindingsByDecorationType(results.findings);

        // Apply decorations for each type
        for (const [decorationType, decorations] of decorationsByType) {
            const vscodeDecorationType = this.decorationTypes.get(decorationType);
            if (vscodeDecorationType && decorations.length > 0) {
                editor.setDecorations(vscodeDecorationType, decorations);
                this.activeDecorations.set(decorationType, decorations);
            }
        }
    }

    private groupFindingsByDecorationType(findings: Finding[]): Map<string, vscode.DecorationOptions[]> {
        const decorationsByType = new Map<string, vscode.DecorationOptions[]>();

        for (const finding of findings) {
            let decorationType: string;
            
            // Prioritize specific connascence types for distinct visual treatment
            if (finding.type.includes('god_object') || finding.type.includes('large_class') || finding.type.includes('CoA')) {
                decorationType = 'god_object';
            } else if (finding.type.includes('magic') || finding.type.includes('literal') || finding.type.includes('CoM')) {
                decorationType = 'magic_literal';
            } else if (finding.type.includes('parameter') || finding.type.includes('coupling') || finding.type.includes('CoP')) {
                decorationType = 'parameter_coupling';
            } else if (finding.type.includes('name') || finding.type.includes('CoN')) {
                decorationType = 'naming';
            } else if (finding.type.includes('type') || finding.type.includes('CoT')) {
                decorationType = 'type_coupling';
            } else if (finding.type.includes('timing') || finding.type.includes('CoTi')) {
                decorationType = 'timing';
            } else if (finding.type.includes('execution') || finding.type.includes('order') || finding.type.includes('CoE')) {
                decorationType = 'execution_order';
            } else if (finding.type.includes('value') || finding.type.includes('CoV')) {
                decorationType = 'value_coupling';
            } else if (finding.type.includes('identity') || finding.type.includes('CoI')) {
                decorationType = 'identity';
            } else {
                // Fall back to severity-based decoration
                decorationType = this.mapSeverityToDecorationType(finding.severity);
            }

            if (!decorationsByType.has(decorationType)) {
                decorationsByType.set(decorationType, []);
            }

            const decoration = this.createDecorationOption(finding);
            decorationsByType.get(decorationType)!.push(decoration);
        }

        return decorationsByType;
    }

    private createDecorationOption(finding: Finding): vscode.DecorationOptions {
        const line = Math.max(0, finding.line - 1);
        const character = Math.max(0, (finding.column || 1) - 1);
        const endCharacter = character + this.getDecorationLength(finding.type);

        const decoration: vscode.DecorationOptions = {
            range: new vscode.Range(
                new vscode.Position(line, character),
                new vscode.Position(line, endCharacter)
            ),
            hoverMessage: this.createEnhancedHoverMessage(finding)
        };

        return decoration;
    }

    private createEnhancedHoverMessage(finding: Finding): vscode.MarkdownString {
        const message = new vscode.MarkdownString();
        message.isTrusted = true;
        message.supportHtml = true;

        // Connascence type explanation with severity color
        const severityColor = this.getSeverityColor(finding.severity);
        const icon = this.getConnascenceIcon(finding.type);
        
        message.appendMarkdown(`### ${icon} ${this.formatConnascenceType(finding.type)}\n`);
        message.appendMarkdown(`**Severity:** <span style="color: ${severityColor}">${finding.severity.toUpperCase()}</span>\n\n`);
        
        // Main message
        message.appendMarkdown(`**Issue:** ${finding.message}\n\n`);
        
        // Refactor suggestion if available
        if (finding.suggestion) {
            message.appendMarkdown(`💡 **Refactor Suggestion:**\n${finding.suggestion}\n\n`);
        }
        
        // Add connascence theory explanation
        message.appendMarkdown(this.getConnascenceExplanation(finding.type));
        
        // Add quick action buttons
        message.appendMarkdown(`\n---\n`);
        message.appendMarkdown(`[🔧 Apply AI Fix](command:connascence.requestAIFix?${encodeURIComponent(JSON.stringify({
            finding: finding,
            type: 'fix'
        }))}) | `);
        message.appendMarkdown(`[💡 Get AI Suggestions](command:connascence.getAISuggestions?${encodeURIComponent(JSON.stringify({
            finding: finding,
            type: 'suggest'
        }))}) | `);
        message.appendMarkdown(`[📖 Learn More](https://docs.connascence.io/types/${finding.type})`);

        return message;
    }

    private getConnascenceIcon(type: string): string {
        const iconMap: { [key: string]: string } = {
            'god_object': '🏛️',
            'large_class': '🏛️', 
            'CoA': '🏛️',
            'magic_literal': '✨',
            'CoM': '✨',
            'parameter_coupling': '🔗',
            'CoP': '🔗',
            'naming': '📛',
            'CoN': '📛',
            'type_coupling': '🏷️',
            'CoT': '🏷️',
            'timing': '⏰',
            'CoTi': '⏰',
            'execution_order': '📝',
            'CoE': '📝',
            'value_coupling': '💎',
            'CoV': '💎',
            'identity': '🆔',
            'CoI': '🆔'
        };

        for (const [key, icon] of Object.entries(iconMap)) {
            if (type.includes(key)) {
                return icon;
            }
        }

        return '⚠️';
    }

    private formatConnascenceType(type: string): string {
        // Convert snake_case or other formats to readable format
        return type.split('_')
                  .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                  .join(' ')
                  .replace(/Co([A-Z])/g, 'Co$1 '); // Add space after Co prefix
    }

    private getSeverityColor(severity: string): string {
        switch (severity.toLowerCase()) {
            case 'critical': return '#ff0000';
            case 'major': case 'high': return '#ffa500';
            case 'minor': case 'medium': return '#0096ff';
            case 'info': case 'low': default: return '#808080';
        }
    }

    private getConnascenceExplanation(type: string): string {
        const explanations: { [key: string]: string } = {
            'god_object': `**Connascence of Algorithm (CoA)** - Classes that have too many responsibilities. This violates the Single Responsibility Principle and makes code harder to maintain and test.`,
            'large_class': `**Connascence of Algorithm (CoA)** - Classes that have grown too large and complex. Consider breaking into smaller, focused components.`,
            'magic_literal': `**Connascence of Meaning (CoM)** - Hard-coded values that have implicit meaning. These should be extracted into named constants for better maintainability.`,
            'parameter_coupling': `**Connascence of Position (CoP)** - Functions with too many parameters or parameters in wrong order. Consider parameter objects or builder patterns.`,
            'naming': `**Connascence of Name (CoN)** - Multiple components must agree on the name of an entity. Changes to names must be synchronized across the codebase.`,
            'type_coupling': `**Connascence of Type (CoT)** - Multiple components must agree on the type of an entity. Type changes require coordinated updates.`,
            'timing': `**Connascence of Timing (CoTi)** - Components that must execute in a specific time-based sequence. Consider using explicit coordination mechanisms.`,
            'execution_order': `**Connascence of Execution (CoE)** - Components where execution order affects correctness. Make dependencies explicit through design.`,
            'value_coupling': `**Connascence of Value (CoV)** - Components that must use the same specific values. Extract shared values to common constants.`,
            'identity': `**Connascence of Identity (CoI)** - Components that must reference the same object instance. Consider using dependency injection or service patterns.`
        };

        for (const [key, explanation] of Object.entries(explanations)) {
            if (type.includes(key)) {
                return explanation;
            }
        }

        return `**Connascence Violation** - This code exhibits coupling that may impact maintainability. Consider refactoring to reduce dependencies between components.`;
    }

    private mapSeverityToDecorationType(severity: string): string {
        switch (severity.toLowerCase()) {
            case 'critical': return 'critical';
            case 'major': case 'high': return 'major';
            case 'minor': case 'medium': return 'minor';
            case 'info': case 'low': default: return 'info';
        }
    }

    private getDecorationLength(findingType: string): number {
        const typeLengths: { [key: string]: number } = {
            'magic_literal': 8,
            'god_object': 25,
            'large_class': 25,
            'parameter_coupling': 15,
            'long_method': 20,
            'duplicate_code': 30
        };

        for (const [type, length] of Object.entries(typeLengths)) {
            if (findingType.includes(type)) {
                return length;
            }
        }

        return 12; // Default length
    }

    /**
     * Clear all decorations from the given editor
     */
    clearDecorations(editor: vscode.TextEditor): void {
        for (const decorationType of this.decorationTypes.values()) {
            editor.setDecorations(decorationType, []);
        }
        this.activeDecorations.clear();
    }

    /**
     * Get statistics about current decorations
     */
    getDecorationStats(): {
        totalDecorations: number;
        decorationsByType: { [type: string]: number };
    } {
        let totalDecorations = 0;
        const decorationsByType: { [type: string]: number } = {};

        for (const [type, decorations] of this.activeDecorations) {
            const count = decorations.length;
            totalDecorations += count;
            decorationsByType[type] = count;
        }

        return { totalDecorations, decorationsByType };
    }

    /**
     * Dispose all decoration types and clear active decorations
     */
    dispose(): void {
        for (const decorationType of this.decorationTypes.values()) {
            decorationType.dispose();
        }
        this.decorationTypes.clear();
        this.activeDecorations.clear();
    }
}