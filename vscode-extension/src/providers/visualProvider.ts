import * as vscode from 'vscode';
import { AnalysisResult, Finding } from '../services/connascenceService';
import { ConfigurationService } from '../services/configurationService';

/**
 * Unified Visual Provider
 * 
 * MECE Responsibility: ALL visual feedback for violations
 * - VS Code diagnostics (Problems panel)
 * - Rich color-coded decorations (editor highlighting)
 * - Hover tooltips with contextual information
 * - Overview ruler markers
 */
export class VisualProvider implements vscode.Disposable {
    // Diagnostics for VS Code Problems panel
    private diagnosticsCollection: vscode.DiagnosticCollection;
    
    // Decorations for rich visual highlighting
    private decorationTypes: Map<string, vscode.TextEditorDecorationType> = new Map();
    private activeDecorations: Map<string, vscode.DecorationOptions[]> = new Map();
    
    // Cache for results
    private resultsCache = new Map<string, AnalysisResult>();

    constructor(private configService: ConfigurationService) {
        this.diagnosticsCollection = vscode.languages.createDiagnosticCollection('connascence');
        this.initializeDecorationTypes();
    }

    /**
     * Update visual feedback for a document
     */
    public updateVisuals(document: vscode.TextDocument, results: AnalysisResult): void {
        const uri = document.uri;
        
        // Cache results
        this.resultsCache.set(uri.toString(), results);

        // Update diagnostics (Problems panel)
        this.updateDiagnostics(uri, results);

        // Update decorations (visual highlighting) if enabled
        if (this.configService.get('enableVisualHighlighting', true)) {
            const activeEditor = this.findActiveEditor(uri);
            if (activeEditor) {
                this.updateDecorations(activeEditor, results);
            }
        }
    }

    /**
     * Update decorations for a specific editor (called when switching editors)
     */
    public updateEditorDecorations(editor: vscode.TextEditor): void {
        const results = this.resultsCache.get(editor.document.uri.toString());
        if (results && this.configService.get('enableVisualHighlighting', true)) {
            this.updateDecorations(editor, results);
        }
    }

    /**
     * Clear all visual feedback
     */
    public clearAll(): void {
        this.diagnosticsCollection.clear();
        this.clearAllDecorations();
        this.resultsCache.clear();
    }

    /**
     * Clear visual feedback for specific document
     */
    public clearDocument(uri: vscode.Uri): void {
        this.diagnosticsCollection.delete(uri);
        this.resultsCache.delete(uri.toString());
        
        const editor = this.findActiveEditor(uri);
        if (editor) {
            this.clearDecorations(editor);
        }
    }

    /**
     * Get cached results
     */
    public getCachedResults(uri: vscode.Uri): AnalysisResult | undefined {
        return this.resultsCache.get(uri.toString());
    }

    /**
     * Get visual statistics
     */
    public getStatistics(): {
        totalDiagnostics: number;
        totalDecorations: number;
        diagnosticsBySeverity: { [severity: string]: number };
        decorationsByType: { [type: string]: number };
    } {
        let totalDiagnostics = 0;
        const diagnosticsBySeverity: { [severity: string]: number } = {};

        // Count diagnostics
        vscode.languages.getDiagnostics().forEach(([, diagnostics]) => {
            totalDiagnostics += diagnostics.length;
            diagnostics.forEach(diag => {
                const severity = this.diagnosticSeverityToString(diag.severity);
                diagnosticsBySeverity[severity] = (diagnosticsBySeverity[severity] || 0) + 1;
            });
        });

        // Count decorations
        let totalDecorations = 0;
        const decorationsByType: { [type: string]: number } = {};
        for (const [type, decorations] of this.activeDecorations) {
            const count = decorations.length;
            totalDecorations += count;
            decorationsByType[type] = count;
        }

        return {
            totalDiagnostics,
            totalDecorations,
            diagnosticsBySeverity,
            decorationsByType
        };
    }

    // === PRIVATE METHODS ===

    private updateDiagnostics(uri: vscode.Uri, results: AnalysisResult): void {
        const diagnostics = results.findings.map(finding => this.findingToDiagnostic(finding, uri));
        this.diagnosticsCollection.set(uri, diagnostics);
    }

    private updateDecorations(editor: vscode.TextEditor, results: AnalysisResult): void {
        // Clear existing decorations
        this.clearDecorations(editor);

        // Group findings by decoration type
        const decorationsByType = this.groupFindingsByDecorationType(results.findings);

        // Apply new decorations
        for (const [decorationType, decorations] of decorationsByType) {
            const vscodeDecorationType = this.decorationTypes.get(decorationType);
            if (vscodeDecorationType && decorations.length > 0) {
                editor.setDecorations(vscodeDecorationType, decorations);
                this.activeDecorations.set(decorationType, decorations);
            }
        }
    }

    private findingToDiagnostic(finding: Finding, uri: vscode.Uri): vscode.Diagnostic {
        const line = Math.max(0, finding.line - 1);
        const character = Math.max(0, (finding.column || 1) - 1);
        const range = new vscode.Range(
            new vscode.Position(line, character),
            new vscode.Position(line, character + 15) // Default length
        );

        const diagnostic = new vscode.Diagnostic(
            range,
            finding.message,
            this.severityToVSCodeSeverity(finding.severity)
        );

        diagnostic.code = {
            value: finding.id,
            target: vscode.Uri.parse(`https://docs.connascence.io/types/${finding.type}`)
        };
        diagnostic.source = 'connascence';

        // Add contextual information
        if (finding.suggestion) {
            diagnostic.relatedInformation = [
                new vscode.DiagnosticRelatedInformation(
                    new vscode.Location(uri, range),
                    `💡 Suggestion: ${finding.suggestion}`
                )
            ];
        }

        return diagnostic;
    }

    private groupFindingsByDecorationType(findings: Finding[]): Map<string, vscode.DecorationOptions[]> {
        const decorationsByType = new Map<string, vscode.DecorationOptions[]>();

        for (const finding of findings) {
            const decorationType = this.getDecorationType(finding);
            
            if (!decorationsByType.has(decorationType)) {
                decorationsByType.set(decorationType, []);
            }

            const decoration = this.createDecorationOption(finding);
            decorationsByType.get(decorationType)!.push(decoration);
        }

        return decorationsByType;
    }

    private getDecorationType(finding: Finding): string {
        // Priority order: specific types first, then severity
        if (finding.type.includes('god_object') || finding.type.includes('large_class') || finding.type.includes('CoA')) {
            return 'god_object';
        } else if (finding.type.includes('magic') || finding.type.includes('literal') || finding.type.includes('CoM')) {
            return 'magic_literal';
        } else if (finding.type.includes('parameter') || finding.type.includes('coupling') || finding.type.includes('CoP')) {
            return 'parameter_coupling';
        } else if (finding.type.includes('name') || finding.type.includes('CoN')) {
            return 'naming';
        } else if (finding.type.includes('type') || finding.type.includes('CoT')) {
            return 'type_coupling';
        } else if (finding.type.includes('timing') || finding.type.includes('CoTi')) {
            return 'timing';
        } else if (finding.type.includes('execution') || finding.type.includes('order') || finding.type.includes('CoE')) {
            return 'execution_order';
        } else if (finding.type.includes('value') || finding.type.includes('CoV')) {
            return 'value_coupling';
        } else if (finding.type.includes('identity') || finding.type.includes('CoI')) {
            return 'identity';
        } else {
            // Fall back to severity
            return this.mapSeverityToDecorationType(finding.severity);
        }
    }

    private createDecorationOption(finding: Finding): vscode.DecorationOptions {
        const line = Math.max(0, finding.line - 1);
        const character = Math.max(0, (finding.column || 1) - 1);
        const endCharacter = character + this.getDecorationLength(finding.type);

        return {
            range: new vscode.Range(
                new vscode.Position(line, character),
                new vscode.Position(line, endCharacter)
            ),
            hoverMessage: this.createHoverMessage(finding)
        };
    }

    private createHoverMessage(finding: Finding): vscode.MarkdownString {
        const message = new vscode.MarkdownString();
        message.isTrusted = true;

        // Header with icon and severity
        const icon = this.getConnascenceIcon(finding.type);
        const severityColor = this.getSeverityColor(finding.severity);
        
        message.appendMarkdown(`### ${icon} ${this.formatConnascenceType(finding.type)}\n`);
        message.appendMarkdown(`**Severity:** <span style="color: ${severityColor}">${finding.severity.toUpperCase()}</span>\n\n`);
        
        // Main message
        message.appendMarkdown(`**Issue:** ${finding.message}\n\n`);
        
        // Refactor suggestion
        if (finding.suggestion) {
            message.appendMarkdown(`💡 **Refactor Suggestion:**\n${finding.suggestion}\n\n`);
        }
        
        // Theory explanation
        message.appendMarkdown(this.getConnascenceExplanation(finding.type));
        
        // AI actions (if enabled)
        if (this.configService.get('aiIntegration', true)) {
            message.appendMarkdown(`\n---\n`);
            message.appendMarkdown(`[🔧 Apply AI Fix](command:connascence.requestAIFix?${encodeURIComponent(JSON.stringify({ finding }))}) | `);
            message.appendMarkdown(`[💡 Get AI Suggestions](command:connascence.getAISuggestions?${encodeURIComponent(JSON.stringify({ finding }))}) | `);
            message.appendMarkdown(`[📖 Learn More](https://docs.connascence.io/types/${finding.type})`);
        }

        return message;
    }

    private initializeDecorationTypes(): void {
        const showEmojis = this.configService.get('showEmojis', true);
        const intensity = this.configService.get('highlightingIntensity', 'normal');
        
        // Adjust colors based on intensity
        const alphaValues = { subtle: 0.1, normal: 0.2, bright: 0.3 };
        const alpha = alphaValues[intensity as keyof typeof alphaValues] || 0.2;

        // God Object (Purple)
        this.decorationTypes.set('god_object', vscode.window.createTextEditorDecorationType({
            backgroundColor: `rgba(148, 0, 211, ${alpha})`,
            border: '2px solid #9400d3',
            borderRadius: '4px',
            overviewRulerColor: '#9400d3',
            overviewRulerLane: vscode.OverviewRulerLane.Right,
            after: showEmojis ? { contentText: ' 🏛️', color: '#9400d3', fontWeight: 'bold' } : undefined
        }));

        // Magic Literal (Pink)
        this.decorationTypes.set('magic_literal', vscode.window.createTextEditorDecorationType({
            backgroundColor: `rgba(255, 20, 147, ${alpha})`,
            border: '1px solid #ff1493',
            borderRadius: '3px',
            overviewRulerColor: '#ff1493',
            overviewRulerLane: vscode.OverviewRulerLane.Right,
            after: showEmojis ? { contentText: ' ✨', color: '#ff1493', fontWeight: 'bold' } : undefined
        }));

        // Parameter Coupling (Orange)
        this.decorationTypes.set('parameter_coupling', vscode.window.createTextEditorDecorationType({
            backgroundColor: `rgba(255, 140, 0, ${alpha})`,
            border: '1px solid #ff8c00',
            borderRadius: '3px',
            overviewRulerColor: '#ff8c00',
            overviewRulerLane: vscode.OverviewRulerLane.Right,
            after: showEmojis ? { contentText: ' 🔗', color: '#ff8c00', fontWeight: 'bold' } : undefined
        }));

        // Add other decoration types...
        this.decorationTypes.set('critical', vscode.window.createTextEditorDecorationType({
            backgroundColor: `rgba(255, 0, 0, ${alpha + 0.1})`,
            border: '2px solid #ff0000',
            borderRadius: '4px',
            overviewRulerColor: '#ff0000',
            overviewRulerLane: vscode.OverviewRulerLane.Right
        }));

        this.decorationTypes.set('major', vscode.window.createTextEditorDecorationType({
            backgroundColor: `rgba(255, 165, 0, ${alpha})`,
            border: '1px solid #ffa500',
            borderRadius: '3px',
            overviewRulerColor: '#ffa500',
            overviewRulerLane: vscode.OverviewRulerLane.Right
        }));

        this.decorationTypes.set('minor', vscode.window.createTextEditorDecorationType({
            backgroundColor: `rgba(0, 150, 255, ${alpha - 0.05})`,
            border: '1px solid #0096ff',
            borderRadius: '3px',
            overviewRulerColor: '#0096ff',
            overviewRulerLane: vscode.OverviewRulerLane.Right
        }));
    }

    private clearDecorations(editor: vscode.TextEditor): void {
        for (const decorationType of this.decorationTypes.values()) {
            editor.setDecorations(decorationType, []);
        }
        this.activeDecorations.clear();
    }

    private clearAllDecorations(): void {
        for (const editor of vscode.window.visibleTextEditors) {
            this.clearDecorations(editor);
        }
    }

    private findActiveEditor(uri: vscode.Uri): vscode.TextEditor | undefined {
        return vscode.window.visibleTextEditors.find(editor => 
            editor.document.uri.toString() === uri.toString()
        );
    }

    // Utility methods
    private severityToVSCodeSeverity(severity: string): vscode.DiagnosticSeverity {
        switch (severity.toLowerCase()) {
            case 'critical': return vscode.DiagnosticSeverity.Error;
            case 'major': case 'high': return vscode.DiagnosticSeverity.Warning;
            case 'minor': case 'medium': return vscode.DiagnosticSeverity.Information;
            default: return vscode.DiagnosticSeverity.Hint;
        }
    }

    private mapSeverityToDecorationType(severity: string): string {
        switch (severity.toLowerCase()) {
            case 'critical': return 'critical';
            case 'major': case 'high': return 'major';
            default: return 'minor';
        }
    }

    private diagnosticSeverityToString(severity: vscode.DiagnosticSeverity): string {
        switch (severity) {
            case vscode.DiagnosticSeverity.Error: return 'critical';
            case vscode.DiagnosticSeverity.Warning: return 'major';
            case vscode.DiagnosticSeverity.Information: return 'minor';
            default: return 'info';
        }
    }

    private getConnascenceIcon(type: string): string {
        const iconMap: { [key: string]: string } = {
            'god_object': '🏛️', 'large_class': '🏛️', 'CoA': '🏛️',
            'magic_literal': '✨', 'CoM': '✨',
            'parameter_coupling': '🔗', 'CoP': '🔗',
            'naming': '📛', 'CoN': '📛',
            'type_coupling': '🏷️', 'CoT': '🏷️',
            'timing': '⏰', 'CoTi': '⏰',
            'execution_order': '📝', 'CoE': '📝',
            'value_coupling': '💎', 'CoV': '💎',
            'identity': '🆔', 'CoI': '🆔'
        };

        for (const [key, icon] of Object.entries(iconMap)) {
            if (type.includes(key)) return icon;
        }
        return '⚠️';
    }

    private formatConnascenceType(type: string): string {
        return type.split('_')
                  .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                  .join(' ');
    }

    private getSeverityColor(severity: string): string {
        const colors = {
            critical: '#ff0000', major: '#ffa500', high: '#ffa500',
            minor: '#0096ff', medium: '#0096ff', info: '#808080', low: '#808080'
        };
        return colors[severity.toLowerCase() as keyof typeof colors] || '#808080';
    }

    private getConnascenceExplanation(type: string): string {
        const explanations: { [key: string]: string } = {
            'god_object': '**Connascence of Algorithm (CoA)** - Classes with too many responsibilities.',
            'magic_literal': '**Connascence of Meaning (CoM)** - Hard-coded values with implicit meaning.',
            'parameter_coupling': '**Connascence of Position (CoP)** - Parameter order dependencies.',
            'naming': '**Connascence of Name (CoN)** - Name agreement requirements.',
            'type_coupling': '**Connascence of Type (CoT)** - Type agreement requirements.'
        };

        for (const [key, explanation] of Object.entries(explanations)) {
            if (type.includes(key)) return explanation;
        }
        return '**Connascence Violation** - Code coupling that may impact maintainability.';
    }

    private getDecorationLength(findingType: string): number {
        const lengths: { [key: string]: number } = {
            'magic_literal': 8, 'god_object': 25, 'parameter_coupling': 15,
            'long_method': 20, 'duplicate_code': 30
        };
        
        for (const [type, length] of Object.entries(lengths)) {
            if (findingType.includes(type)) return length;
        }
        return 12;
    }

    dispose(): void {
        this.diagnosticsCollection.dispose();
        for (const decorationType of this.decorationTypes.values()) {
            decorationType.dispose();
        }
        this.decorationTypes.clear();
        this.activeDecorations.clear();
        this.resultsCache.clear();
    }
}