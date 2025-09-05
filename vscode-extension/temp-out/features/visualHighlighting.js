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
exports.VisualHighlightingManager = void 0;
const vscode = __importStar(require("vscode"));
class VisualHighlightingManager {
    constructor() {
        this.decorationTypes = new Map();
        this.activeDecorations = new Map();
        this.initializeDecorationTypes();
        // Listen for configuration changes
        vscode.workspace.onDidChangeConfiguration((event) => {
            if (event.affectsConfiguration('connascence.enableVisualHighlighting') ||
                event.affectsConfiguration('connascence.highlightingIntensity')) {
                this.updateDecorationTypes();
            }
        });
    }
    initializeDecorationTypes() {
        const config = vscode.workspace.getConfiguration('connascence');
        const enabled = config.get('enableVisualHighlighting', true);
        const intensity = config.get('highlightingIntensity', 'normal');
        if (!enabled) {
            return;
        }
        // Create decoration types for different connascence types with chain symbolism
        const decorationConfigs = this.getDecorationConfigs(intensity);
        for (const [type, config] of Object.entries(decorationConfigs)) {
            this.decorationTypes.set(type, vscode.window.createTextEditorDecorationType(config));
        }
    }
    getDecorationConfigs(intensity) {
        const baseOpacity = intensity === 'subtle' ? 0.3 : intensity === 'bright' ? 0.8 : 0.5;
        return {
            // === 9 CONNASCENCE TYPES (Chain Breaking Symbolism) ===
            // Static connascence types (compile-time chains)
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
            // === 10 NASA POWER OF TEN VIOLATIONS (Rocket/Space Symbolism) ===
            'nasa_rule_1': {
                backgroundColor: `rgba(220, 20, 60, ${baseOpacity})`, // Crimson for control flow
                border: '2px solid rgba(220, 20, 60, 0.9)',
                borderRadius: '4px',
                after: {
                    contentText: ' 🚀⚠️', // Rocket warning
                    color: 'rgba(220, 20, 60, 0.9)',
                    fontWeight: 'bold'
                },
                overviewRulerColor: 'rgba(220, 20, 60, 0.9)',
                overviewRulerLane: vscode.OverviewRulerLane.Left
            },
            'nasa_rule_2': {
                backgroundColor: `rgba(178, 34, 34, ${baseOpacity})`, // Fire brick
                border: '2px solid rgba(178, 34, 34, 0.9)',
                borderRadius: '4px',
                after: {
                    contentText: ' 🛰️🔄', // Satellite loop
                    color: 'rgba(178, 34, 34, 0.9)'
                },
                overviewRulerColor: 'rgba(178, 34, 34, 0.9)',
                overviewRulerLane: vscode.OverviewRulerLane.Left
            },
            'nasa_rule_3': {
                backgroundColor: `rgba(139, 0, 0, ${baseOpacity})`, // Dark red
                border: '2px solid rgba(139, 0, 0, 0.9)',
                borderRadius: '4px',
                after: {
                    contentText: ' 🚀💾', // Rocket memory
                    color: 'rgba(139, 0, 0, 0.9)'
                },
                overviewRulerColor: 'rgba(139, 0, 0, 0.9)',
                overviewRulerLane: vscode.OverviewRulerLane.Left
            },
            'nasa_rule_4': {
                backgroundColor: `rgba(255, 140, 0, ${baseOpacity})`, // Dark orange
                border: '2px solid rgba(255, 140, 0, 0.9)',
                borderRadius: '4px',
                after: {
                    contentText: ' 🌌📏', // Space ruler
                    color: 'rgba(255, 140, 0, 0.9)'
                },
                overviewRulerColor: 'rgba(255, 140, 0, 0.9)',
                overviewRulerLane: vscode.OverviewRulerLane.Left
            },
            'nasa_rule_5': {
                backgroundColor: `rgba(255, 215, 0, ${baseOpacity})`, // Gold
                border: '2px solid rgba(255, 215, 0, 0.9)',
                borderRadius: '4px',
                after: {
                    contentText: ' 🛸✅', // UFO check
                    color: 'rgba(218, 165, 32, 0.9)'
                },
                overviewRulerColor: 'rgba(255, 215, 0, 0.9)',
                overviewRulerLane: vscode.OverviewRulerLane.Left
            },
            'nasa_rule_6': {
                backgroundColor: `rgba(154, 205, 50, ${baseOpacity})`, // Yellow green
                border: '2px solid rgba(154, 205, 50, 0.9)',
                borderRadius: '4px',
                after: {
                    contentText: ' 🌠🔒', // Shooting star lock
                    color: 'rgba(154, 205, 50, 0.9)'
                },
                overviewRulerColor: 'rgba(154, 205, 50, 0.9)',
                overviewRulerLane: vscode.OverviewRulerLane.Left
            },
            'nasa_rule_7': {
                backgroundColor: `rgba(0, 191, 255, ${baseOpacity})`, // Deep sky blue
                border: '2px solid rgba(0, 191, 255, 0.9)',
                borderRadius: '4px',
                after: {
                    contentText: ' 🚀↩️', // Rocket return
                    color: 'rgba(0, 191, 255, 0.9)'
                },
                overviewRulerColor: 'rgba(0, 191, 255, 0.9)',
                overviewRulerLane: vscode.OverviewRulerLane.Left
            },
            'nasa_rule_8': {
                backgroundColor: `rgba(138, 43, 226, ${baseOpacity})`, // Blue violet
                border: '2px solid rgba(138, 43, 226, 0.9)',
                borderRadius: '4px',
                after: {
                    contentText: ' 🌌⚡', // Galaxy lightning
                    color: 'rgba(138, 43, 226, 0.9)'
                },
                overviewRulerColor: 'rgba(138, 43, 226, 0.9)',
                overviewRulerLane: vscode.OverviewRulerLane.Left
            },
            'nasa_rule_9': {
                backgroundColor: `rgba(75, 0, 130, ${baseOpacity})`, // Indigo
                border: '2px solid rgba(75, 0, 130, 0.9)',
                borderRadius: '4px',
                after: {
                    contentText: ' 🛰️👉', // Satellite pointer
                    color: 'rgba(75, 0, 130, 0.9)'
                },
                overviewRulerColor: 'rgba(75, 0, 130, 0.9)',
                overviewRulerLane: vscode.OverviewRulerLane.Left
            },
            'nasa_rule_10': {
                backgroundColor: `rgba(199, 21, 133, ${baseOpacity})`, // Medium violet red
                border: '2px solid rgba(199, 21, 133, 0.9)',
                borderRadius: '4px',
                after: {
                    contentText: ' 🚀🔍', // Rocket magnify
                    color: 'rgba(199, 21, 133, 0.9)'
                },
                overviewRulerColor: 'rgba(199, 21, 133, 0.9)',
                overviewRulerLane: vscode.OverviewRulerLane.Left
            },
            // === GOD OBJECT DETECTION (Divine/Mythological Symbolism) ===
            'god_object': {
                backgroundColor: `rgba(255, 215, 0, ${baseOpacity})`, // Gold for divine objects
                border: '3px solid rgba(255, 215, 0, 0.9)',
                borderRadius: '6px',
                after: {
                    contentText: ' 👑⚡', // Crown lightning - divine power
                    color: 'rgba(255, 215, 0, 0.9)',
                    fontWeight: 'bold'
                },
                overviewRulerColor: 'rgba(255, 215, 0, 0.9)',
                overviewRulerLane: vscode.OverviewRulerLane.Full
            },
            'god_class': {
                backgroundColor: `rgba(255, 20, 147, ${baseOpacity})`, // Deep pink
                border: '3px solid rgba(255, 20, 147, 0.9)',
                borderRadius: '6px',
                after: {
                    contentText: ' 🏛️⚠️', // Temple warning
                    color: 'rgba(255, 20, 147, 0.9)',
                    fontWeight: 'bold'
                },
                overviewRulerColor: 'rgba(255, 20, 147, 0.9)',
                overviewRulerLane: vscode.OverviewRulerLane.Full
            },
            'god_function': {
                backgroundColor: `rgba(128, 0, 128, ${baseOpacity})`, // Purple
                border: '3px solid rgba(128, 0, 128, 0.9)',
                borderRadius: '6px',
                after: {
                    contentText: ' ⚡🔥', // Lightning fire - powerful function
                    color: 'rgba(128, 0, 128, 0.9)',
                    fontWeight: 'bold'
                },
                overviewRulerColor: 'rgba(128, 0, 128, 0.9)',
                overviewRulerLane: vscode.OverviewRulerLane.Full
            },
            'large_class': {
                backgroundColor: `rgba(205, 92, 92, ${baseOpacity})`, // Indian red
                border: '2px solid rgba(205, 92, 92, 0.8)',
                borderRadius: '4px',
                after: {
                    contentText: ' 🏗️📈', // Building growing
                    color: 'rgba(205, 92, 92, 0.8)'
                },
                overviewRulerColor: 'rgba(205, 92, 92, 0.8)',
                overviewRulerLane: vscode.OverviewRulerLane.Center
            },
            'complex_method': {
                backgroundColor: `rgba(210, 180, 140, ${baseOpacity})`, // Tan
                border: '2px solid rgba(210, 180, 140, 0.8)',
                borderRadius: '4px',
                after: {
                    contentText: ' 🧩🔀', // Puzzle piece complexity
                    color: 'rgba(160, 82, 45, 0.8)'
                },
                overviewRulerColor: 'rgba(210, 180, 140, 0.8)',
                overviewRulerLane: vscode.OverviewRulerLane.Center
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
    updateDecorationTypes() {
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
    applyHighlighting(editor, findings) {
        const config = vscode.workspace.getConfiguration('connascence');
        const enabled = config.get('enableVisualHighlighting', true);
        const showEmojis = config.get('showEmojis', true);
        if (!enabled) {
            return;
        }
        // Clear existing decorations for this editor
        this.clearDecorations(editor);
        // Group findings by connascence type
        const findingsByType = new Map();
        for (const finding of findings) {
            const normalizedType = this.normalizeConnascenceType(finding.type);
            if (!findingsByType.has(normalizedType)) {
                findingsByType.set(normalizedType, []);
            }
            findingsByType.get(normalizedType).push(finding);
        }
        // Apply decorations for each type
        const appliedDecorations = [];
        for (const [type, typeFindings] of findingsByType) {
            const decorationType = this.decorationTypes.get(type) || this.decorationTypes.get('default');
            if (decorationType) {
                const ranges = typeFindings.map(finding => {
                    const line = Math.max(0, finding.line - 1); // Convert to 0-based
                    const col = Math.max(0, (finding.column || 1) - 1);
                    const endCol = col + 10; // Highlight ~10 characters
                    return new vscode.Range(new vscode.Position(line, col), new vscode.Position(line, endCol));
                });
                editor.setDecorations(decorationType, ranges);
                appliedDecorations.push(decorationType);
            }
        }
        // Track decorations for cleanup
        this.activeDecorations.set(editor.document.uri.toString(), appliedDecorations);
    }
    clearDecorations(editor) {
        const uri = editor.document.uri.toString();
        const decorations = this.activeDecorations.get(uri);
        if (decorations) {
            for (const decoration of decorations) {
                editor.setDecorations(decoration, []);
            }
            this.activeDecorations.delete(uri);
        }
    }
    clearAllDecorations() {
        for (const editor of vscode.window.visibleTextEditors) {
            this.clearDecorations(editor);
        }
    }
    refreshAllDecorations() {
        // This would be called by the diagnostics provider to reapply
        // decorations when settings change
        vscode.commands.executeCommand('connascence.refreshHighlighting');
    }
    normalizeConnascenceType(type) {
        // Normalize connascence type names to match our decoration types
        const normalized = type.toLowerCase()
            .replace(/\s+/g, '_')
            .replace(/[^a-z_]/g, '');
        // Map common variations
        const typeMap = {
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
    dispose() {
        for (const decoration of this.decorationTypes.values()) {
            decoration.dispose();
        }
        this.decorationTypes.clear();
        this.activeDecorations.clear();
    }
}
exports.VisualHighlightingManager = VisualHighlightingManager;
//# sourceMappingURL=visualHighlighting.js.map