import * as vscode from 'vscode';
import { Finding } from '../services/connascenceService';

export class VisualHighlightingManager {
    private decorationTypes: Map<string, vscode.TextEditorDecorationType> = new Map();
    private activeDecorations: Map<string, vscode.TextEditorDecorationType[]> = new Map();

    constructor() {
        this.initializeDecorationTypes();
        
        // Listen for configuration changes
        vscode.workspace.onDidChangeConfiguration((event) => {
            if (event.affectsConfiguration('connascence.enableVisualHighlighting') || 
                event.affectsConfiguration('connascence.highlightingIntensity')) {
                this.updateDecorationTypes();
            }
        });
    }

    private initializeDecorationTypes() {
        const config = vscode.workspace.getConfiguration('connascence');
        const enabled = config.get<boolean>('enableVisualHighlighting', true);
        const intensity = config.get<string>('highlightingIntensity', 'normal');
        
        if (!enabled) {
            return;
        }

        // Create decoration types for different connascence types with chain symbolism
        const decorationConfigs = this.getDecorationConfigs(intensity);
        
        for (const [type, config] of Object.entries(decorationConfigs)) {
            this.decorationTypes.set(type, vscode.window.createTextEditorDecorationType(config));
        }
    }

    private getDecorationConfigs(intensity: string): { [key: string]: vscode.DecorationRenderOptions } {
        const baseOpacity = intensity === 'subtle' ? 0.3 : intensity === 'bright' ? 0.8 : 0.5;
        
        return {
            // Static connascence types (stronger chains = harder to break)
            'connascence_of_name': {
                backgroundColor: `rgba(255, 69, 0, ${baseOpacity})`, // Red-orange for naming coupling
                border: '1px solid rgba(255, 69, 0, 0.8)',
                borderRadius: '3px',
                after: {
                    contentText: ' 🔗💔', // Broken chain emoji
                    color: 'rgba(255, 69, 0, 0.8)',
                    fontWeight: 'bold'
                },
                overviewRulerColor: 'rgba(255, 69, 0, 0.8)',
                overviewRulerLane: vscode.OverviewRulerLane.Right
            },
            'connascence_of_type': {
                backgroundColor: `rgba(255, 165, 0, ${baseOpacity})`, // Orange for type coupling
                border: '1px solid rgba(255, 165, 0, 0.8)',
                borderRadius: '3px',
                after: {
                    contentText: ' ⛓️💥', // Chain breaking
                    color: 'rgba(255, 165, 0, 0.8)'
                },
                overviewRulerColor: 'rgba(255, 165, 0, 0.8)',
                overviewRulerLane: vscode.OverviewRulerLane.Right
            },
            'connascence_of_meaning': {
                backgroundColor: `rgba(255, 215, 0, ${baseOpacity})`, // Gold for magic values
                border: '1px solid rgba(255, 215, 0, 0.8)',
                borderRadius: '3px',
                after: {
                    contentText: ' 🔐💢', // Locked chain
                    color: 'rgba(255, 215, 0, 0.8)'
                },
                overviewRulerColor: 'rgba(255, 215, 0, 0.8)',
                overviewRulerLane: vscode.OverviewRulerLane.Right
            },
            'connascence_of_position': {
                backgroundColor: `rgba(173, 216, 230, ${baseOpacity})`, // Light blue for position
                border: '1px solid rgba(173, 216, 230, 0.8)',
                borderRadius: '3px',
                after: {
                    contentText: ' 🔗📍', // Chain with position
                    color: 'rgba(30, 144, 255, 0.8)'
                },
                overviewRulerColor: 'rgba(30, 144, 255, 0.8)',
                overviewRulerLane: vscode.OverviewRulerLane.Right
            },
            'connascence_of_algorithm': {
                backgroundColor: `rgba(138, 43, 226, ${baseOpacity})`, // Purple for algorithmic coupling
                border: '1px solid rgba(138, 43, 226, 0.8)',
                borderRadius: '3px',
                after: {
                    contentText: ' ⚙️🔗', // Gear chain
                    color: 'rgba(138, 43, 226, 0.8)'
                },
                overviewRulerColor: 'rgba(138, 43, 226, 0.8)',
                overviewRulerLane: vscode.OverviewRulerLane.Right
            },
            
            // Dynamic connascence types (runtime chains)
            'connascence_of_execution': {
                backgroundColor: `rgba(255, 20, 147, ${baseOpacity})`, // Deep pink for execution order
                border: '1px solid rgba(255, 20, 147, 0.8)',
                borderRadius: '3px',
                after: {
                    contentText: ' 🏃‍♂️🔗', // Running chain
                    color: 'rgba(255, 20, 147, 0.8)'
                },
                overviewRulerColor: 'rgba(255, 20, 147, 0.8)',
                overviewRulerLane: vscode.OverviewRulerLane.Right
            },
            'connascence_of_timing': {
                backgroundColor: `rgba(255, 0, 255, ${baseOpacity})`, // Magenta for timing
                border: '1px solid rgba(255, 0, 255, 0.8)',
                borderRadius: '3px',
                after: {
                    contentText: ' ⏰🔗', // Time chain
                    color: 'rgba(255, 0, 255, 0.8)'
                },
                overviewRulerColor: 'rgba(255, 0, 255, 0.8)',
                overviewRulerLane: vscode.OverviewRulerLane.Right
            },
            'connascence_of_value': {
                backgroundColor: `rgba(50, 205, 50, ${baseOpacity})`, // Lime green for value coupling
                border: '1px solid rgba(50, 205, 50, 0.8)',
                borderRadius: '3px',
                after: {
                    contentText: ' 💎🔗', // Valuable chain
                    color: 'rgba(34, 139, 34, 0.8)'
                },
                overviewRulerColor: 'rgba(50, 205, 50, 0.8)',
                overviewRulerLane: vscode.OverviewRulerLane.Right
            },
            'connascence_of_identity': {
                backgroundColor: `rgba(0, 191, 255, ${baseOpacity})`, // Deep sky blue for identity
                border: '1px solid rgba(0, 191, 255, 0.8)',
                borderRadius: '3px',
                after: {
                    contentText: ' 🆔🔗', // ID chain
                    color: 'rgba(0, 191, 255, 0.8)'
                },
                overviewRulerColor: 'rgba(0, 191, 255, 0.8)',
                overviewRulerLane: vscode.OverviewRulerLane.Right
            },
            
            // General violations
            'default': {
                backgroundColor: `rgba(255, 99, 71, ${baseOpacity})`, // Tomato for generic issues
                border: '1px solid rgba(255, 99, 71, 0.8)',
                borderRadius: '3px',
                after: {
                    contentText: ' 🚨🔗', // Alert chain
                    color: 'rgba(255, 99, 71, 0.8)'
                },
                overviewRulerColor: 'rgba(255, 99, 71, 0.8)',
                overviewRulerLane: vscode.OverviewRulerLane.Right
            }
        };
    }

    private updateDecorationTypes() {
        // Dispose old decorations
        for (const decoration of this.decorationTypes.values()) {
            decoration.dispose();
        }
        this.decorationTypes.clear();
        
        // Create new ones
        this.initializeDecorationTypes();
        
        // Reapply to active editors
        this.refreshAllDecorations();
    }

    public applyHighlighting(editor: vscode.TextEditor, findings: Finding[]) {
        const config = vscode.workspace.getConfiguration('connascence');
        const enabled = config.get<boolean>('enableVisualHighlighting', true);
        const showEmojis = config.get<boolean>('showEmojis', true);
        
        if (!enabled) {
            return;
        }

        // Clear existing decorations for this editor
        this.clearDecorations(editor);
        
        // Group findings by connascence type
        const findingsByType = new Map<string, Finding[]>();
        
        for (const finding of findings) {
            const normalizedType = this.normalizeConnascenceType(finding.type);
            if (!findingsByType.has(normalizedType)) {
                findingsByType.set(normalizedType, []);
            }
            findingsByType.get(normalizedType)!.push(finding);
        }

        // Apply decorations for each type
        const appliedDecorations: vscode.TextEditorDecorationType[] = [];
        
        for (const [type, typeFindings] of findingsByType) {
            const decorationType = this.decorationTypes.get(type) || this.decorationTypes.get('default');
            
            if (decorationType) {
                const ranges = typeFindings.map(finding => {
                    const line = Math.max(0, finding.line - 1); // Convert to 0-based
                    const col = Math.max(0, finding.column - 1);
                    const endCol = col + 10; // Highlight ~10 characters
                    
                    return new vscode.Range(
                        new vscode.Position(line, col),
                        new vscode.Position(line, endCol)
                    );
                });

                editor.setDecorations(decorationType, ranges);
                appliedDecorations.push(decorationType);
            }
        }

        // Track decorations for cleanup
        this.activeDecorations.set(editor.document.uri.toString(), appliedDecorations);
    }

    public clearDecorations(editor: vscode.TextEditor) {
        const uri = editor.document.uri.toString();
        const decorations = this.activeDecorations.get(uri);
        
        if (decorations) {
            for (const decoration of decorations) {
                editor.setDecorations(decoration, []);
            }
            this.activeDecorations.delete(uri);
        }
    }

    public clearAllDecorations() {
        for (const editor of vscode.window.visibleTextEditors) {
            this.clearDecorations(editor);
        }
    }

    private refreshAllDecorations() {
        // This would be called by the diagnostics provider to reapply
        // decorations when settings change
        vscode.commands.executeCommand('connascence.refreshHighlighting');
    }

    private normalizeConnascenceType(type: string): string {
        // Normalize connascence type names to match our decoration types
        const normalized = type.toLowerCase()
            .replace(/\s+/g, '_')
            .replace(/[^a-z_]/g, '');
        
        // Map common variations
        const typeMap: { [key: string]: string } = {
            'name': 'connascence_of_name',
            'type': 'connascence_of_type', 
            'meaning': 'connascence_of_meaning',
            'position': 'connascence_of_position',
            'algorithm': 'connascence_of_algorithm',
            'execution': 'connascence_of_execution',
            'timing': 'connascence_of_timing',
            'value': 'connascence_of_value',
            'identity': 'connascence_of_identity',
            'con_name': 'connascence_of_name',
            'con_type': 'connascence_of_type',
            'con_meaning': 'connascence_of_meaning',
            'con_position': 'connascence_of_position',
            'con_algorithm': 'connascence_of_algorithm',
            'con_execution': 'connascence_of_execution',
            'con_timing': 'connascence_of_timing',
            'con_value': 'connascence_of_value',
            'con_identity': 'connascence_of_identity'
        };
        
        return typeMap[normalized] || normalized;
    }

    public dispose() {
        for (const decoration of this.decorationTypes.values()) {
            decoration.dispose();
        }
        this.decorationTypes.clear();
        this.activeDecorations.clear();
    }
}