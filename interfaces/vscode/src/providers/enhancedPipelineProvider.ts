/**
 * Enhanced Pipeline Provider for VSCode Extension
 * 
 * Integrates VSCode extension with enhanced analysis pipeline features:
 * - Cross-phase correlation analysis
 * - Audit trail visualization
 * - Smart recommendations
 * - Hotspot analysis
 */

import * as vscode from 'vscode';
import { spawn } from 'child_process';
import * as path from 'path';

export interface EnhancedAnalysisResult {
    // Standard analysis results
    connascence_violations: any[];
    duplication_clusters: any[];
    nasa_violations: any[];
    
    // Enhanced metadata
    audit_trail?: any[];
    correlations?: any[];
    smart_recommendations?: any[];
    cross_phase_analysis?: boolean;
    components_used?: Record<string, boolean>;
    canonical_policy?: string;
    policy_config?: Record<string, any>;
}

export interface CrossPhaseCorrelation {
    analyzer1: string;
    analyzer2: string;
    correlation_type: string;
    correlation_score: number;
    affected_files?: string[];
    description: string;
    priority: string;
    remediation_impact?: string;
}

export interface AuditTrailEntry {
    phase: string;
    started?: string;
    completed?: string;
    violations_found?: number;
    clusters_found?: number;
    correlations_found?: number;
}

export class EnhancedPipelineProvider {
    private static instance: EnhancedPipelineProvider;
    private outputChannel: vscode.OutputChannel;

    private constructor() {
        this.outputChannel = vscode.window.createOutputChannel('Connascence Enhanced Pipeline');
    }

    static getInstance(): EnhancedPipelineProvider {
        if (!EnhancedPipelineProvider.instance) {
            EnhancedPipelineProvider.instance = new EnhancedPipelineProvider();
        }
        return EnhancedPipelineProvider.instance;
    }

    /**
     * Resolve policy name using enhanced pipeline policy resolution
     */
    resolvePolicyName(vscodePolicy: string): string {
        // Map VSCode configuration to enhanced pipeline policy names
        const policyMapping: Record<string, string> = {
            'safety_level_1': 'nasa-compliance',
            'general_safety_strict': 'strict',
            'modern_general': 'standard',
            'safety_level_3': 'lenient',
            'none': 'lenient',
            // New unified names map to themselves
            'nasa-compliance': 'nasa-compliance',
            'strict': 'strict',
            'standard': 'standard', 
            'lenient': 'lenient'
        };

        return policyMapping[vscodePolicy] || 'standard';
    }

    /**
     * Run enhanced analysis using the enhanced pipeline
     */
    async runEnhancedAnalysis(
        filePath: string | vscode.Uri,
        policy?: string
    ): Promise<EnhancedAnalysisResult | null> {
        try {
            const config = vscode.workspace.getConfiguration('connascence');
            const enhancedConfig = config.get<any>('enhancedPipeline', {});
            
            // Resolve policy
            const vscodePolicy = policy || config.get<string>('safetyProfile', 'standard');
            const resolvedPolicy = this.resolvePolicyName(vscodePolicy);
            
            // Get file path
            const targetPath = filePath instanceof vscode.Uri ? filePath.fsPath : filePath;
            
            // Find analyzer path
            const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
            if (!workspaceRoot) {
                throw new Error('No workspace folder found');
            }
            
            const analyzerPath = path.join(workspaceRoot, 'analyzer', 'core.py');
            
            // Build analysis command with enhanced features
            const args = [
                analyzerPath,
                '--path', targetPath,
                '--policy', resolvedPolicy,
                '--format', 'json'
            ];

            // Add enhanced pipeline flags based on configuration
            if (enhancedConfig.enableCrossPhaseCorrelation) {
                args.push('--enable-correlations');
            }
            if (enhancedConfig.enableAuditTrail) {
                args.push('--enable-audit-trail');
            }
            if (enhancedConfig.enableSmartRecommendations) {
                args.push('--enable-smart-recommendations');
            }
            if (enhancedConfig.correlationThreshold) {
                args.push('--correlation-threshold', enhancedConfig.correlationThreshold.toString());
            }

            this.outputChannel.appendLine(`Running enhanced analysis: python ${args.join(' ')}`);

            return new Promise((resolve, reject) => {
                const process = spawn('python', args, {
                    cwd: workspaceRoot,
                    stdio: ['pipe', 'pipe', 'pipe']
                });

                let stdout = '';
                let stderr = '';

                process.stdout.on('data', (data) => {
                    stdout += data.toString();
                });

                process.stderr.on('data', (data) => {
                    stderr += data.toString();
                });

                process.on('close', (code) => {
                    if (code !== 0) {
                        this.outputChannel.appendLine(`Analysis failed with code ${code}`);
                        this.outputChannel.appendLine(`Error: ${stderr}`);
                        reject(new Error(`Analysis failed: ${stderr}`));
                        return;
                    }

                    try {
                        const result: EnhancedAnalysisResult = JSON.parse(stdout);
                        this.outputChannel.appendLine('Enhanced analysis completed successfully');
                        
                        // Log enhanced features found
                        if (result.correlations?.length) {
                            this.outputChannel.appendLine(`Found ${result.correlations.length} cross-phase correlations`);
                        }
                        if (result.audit_trail?.length) {
                            this.outputChannel.appendLine(`Audit trail: ${result.audit_trail.length} phase entries`);
                        }
                        if (result.smart_recommendations?.length) {
                            this.outputChannel.appendLine(`Generated ${result.smart_recommendations.length} smart recommendations`);
                        }

                        resolve(result);
                    } catch (parseError) {
                        this.outputChannel.appendLine(`Failed to parse analysis result: ${parseError}`);
                        this.outputChannel.appendLine(`Raw output: ${stdout}`);
                        reject(new Error(`Failed to parse analysis result: ${parseError}`));
                    }
                });

                process.on('error', (error) => {
                    this.outputChannel.appendLine(`Failed to start analysis process: ${error}`);
                    reject(error);
                });
            });

        } catch (error) {
            this.outputChannel.appendLine(`Enhanced analysis error: ${error}`);
            return null;
        }
    }

    /**
     * Get cross-phase correlations for visualization
     */
    getCorrelationNetworkData(correlations: CrossPhaseCorrelation[]) {
        const nodes = new Map<string, { id: string; label: string; count: number }>();
        const edges: { source: string; target: string; weight: number; label: string; description: string }[] = [];

        correlations.forEach((correlation, index) => {
            const analyzer1 = correlation.analyzer1;
            const analyzer2 = correlation.analyzer2;

            // Add nodes
            if (!nodes.has(analyzer1)) {
                nodes.set(analyzer1, { id: analyzer1, label: analyzer1.replace('_', ' ').toUpperCase(), count: 0 });
            }
            if (!nodes.has(analyzer2)) {
                nodes.set(analyzer2, { id: analyzer2, label: analyzer2.replace('_', ' ').toUpperCase(), count: 0 });
            }

            nodes.get(analyzer1)!.count++;
            nodes.get(analyzer2)!.count++;

            // Add edge
            edges.push({
                source: analyzer1,
                target: analyzer2,
                weight: correlation.correlation_score,
                label: correlation.correlation_score.toFixed(2),
                description: correlation.description
            });
        });

        return {
            nodes: Array.from(nodes.values()),
            edges: edges
        };
    }

    /**
     * Get audit trail visualization data
     */
    getAuditTrailData(auditTrail: AuditTrailEntry[]) {
        const phases = auditTrail.filter(entry => entry.started && entry.completed);
        
        return phases.map(phase => {
            const startTime = new Date(phase.started!).getTime();
            const endTime = new Date(phase.completed!).getTime();
            const duration = endTime - startTime;

            return {
                phase: phase.phase.replace('_', ' ').toUpperCase(),
                duration: duration,
                violations: phase.violations_found || 0,
                clusters: phase.clusters_found || 0,
                correlations: phase.correlations_found || 0,
                started: phase.started,
                completed: phase.completed
            };
        });
    }

    /**
     * Format smart recommendations for display
     */
    formatSmartRecommendations(recommendations: any[]): vscode.QuickPickItem[] {
        return recommendations.map((rec, index) => ({
            label: `$(lightbulb) ${rec.type || 'Recommendation'}: ${rec.category || 'General'}`,
            description: rec.description,
            detail: `Impact: ${rec.impact || 'Unknown'} | Effort: ${rec.effort || 'Unknown'} | Priority: ${rec.priority || 'Medium'}`,
            rec: rec
        }));
    }

    /**
     * Show enhanced analysis results in Quick Pick
     */
    async showEnhancedAnalysisResults(result: EnhancedAnalysisResult) {
        const items: vscode.QuickPickItem[] = [];

        // Basic metrics
        items.push({
            label: `$(info) Analysis Summary`,
            description: `${result.connascence_violations.length} connascence, ${result.duplication_clusters.length} duplications, ${result.nasa_violations.length} NASA violations`,
            detail: `Policy: ${result.canonical_policy || 'unknown'} | Cross-phase: ${result.cross_phase_analysis ? 'enabled' : 'disabled'}`
        });

        // Correlations
        if (result.correlations?.length) {
            items.push({
                label: `$(git-branch) Cross-Phase Correlations (${result.correlations.length})`,
                description: 'View violation correlations across analyzers',
                detail: 'Click to visualize correlation network'
            });
        }

        // Smart recommendations
        if (result.smart_recommendations?.length) {
            items.push({
                label: `$(lightbulb) Smart Recommendations (${result.smart_recommendations.length})`,
                description: 'AI-powered architectural recommendations',
                detail: 'Based on cross-phase analysis'
            });
        }

        // Audit trail
        if (result.audit_trail?.length) {
            items.push({
                label: `$(history) Analysis Audit Trail (${result.audit_trail.length} phases)`,
                description: 'View detailed analysis phase information',
                detail: 'Performance timing and phase details'
            });
        }

        if (items.length === 1) {
            vscode.window.showInformationMessage('Enhanced analysis completed - no advanced features detected');
            return;
        }

        const selection = await vscode.window.showQuickPick(items, {
            title: 'Enhanced Connascence Analysis Results',
            placeHolder: 'Select a category to explore...'
        });

        if (selection) {
            if (selection.label.includes('Correlations')) {
                await this.showCorrelationDetails(result.correlations!);
            } else if (selection.label.includes('Recommendations')) {
                await this.showSmartRecommendations(result.smart_recommendations!);
            } else if (selection.label.includes('Audit Trail')) {
                await this.showAuditTrail(result.audit_trail!);
            }
        }
    }

    private async showCorrelationDetails(correlations: CrossPhaseCorrelation[]) {
        const items = correlations.map((correlation, index) => ({
            label: `$(git-branch) ${correlation.correlation_type}`,
            description: `${correlation.analyzer1} ↔ ${correlation.analyzer2} (${(correlation.correlation_score * 100).toFixed(1)}%)`,
            detail: `${correlation.description} | Priority: ${correlation.priority}`,
            correlation: correlation
        }));

        const selection = await vscode.window.showQuickPick(items, {
            title: 'Cross-Phase Correlations',
            placeHolder: 'Select correlation to view details...'
        });

        if (selection) {
            const correlation = selection.correlation;
            const message = `${correlation.description}\n\nCorrelation Score: ${(correlation.correlation_score * 100).toFixed(1)}%\nPriority: ${correlation.priority}`;
            
            if (correlation.affected_files?.length) {
                const fileList = correlation.affected_files.slice(0, 5).join('\n• ');
                const moreFiles = correlation.affected_files.length > 5 ? `\n... and ${correlation.affected_files.length - 5} more files` : '';
                vscode.window.showInformationMessage(
                    `${message}\n\nAffected Files:\n• ${fileList}${moreFiles}`
                );
            } else {
                vscode.window.showInformationMessage(message);
            }
        }
    }

    private async showSmartRecommendations(recommendations: any[]) {
        const items = this.formatSmartRecommendations(recommendations);

        const selection = await vscode.window.showQuickPick(items, {
            title: 'Smart Architectural Recommendations',
            placeHolder: 'Select recommendation to view details...'
        });

        if (selection) {
            const rec = (selection as any).rec;
            const message = `${rec.description}\n\nImpact: ${rec.impact}\nEffort: ${rec.effort}\nPriority: ${rec.priority}`;
            vscode.window.showInformationMessage(message);
        }
    }

    private async showAuditTrail(auditTrail: AuditTrailEntry[]) {
        const trailData = this.getAuditTrailData(auditTrail);
        
        const items = trailData.map(phase => ({
            label: `$(clock) ${phase.phase}`,
            description: `${phase.duration}ms`,
            detail: `Violations: ${phase.violations} | Clusters: ${phase.clusters} | Correlations: ${phase.correlations}`
        }));

        await vscode.window.showQuickPick(items, {
            title: 'Analysis Phase Audit Trail',
            placeHolder: 'Phase performance and timing details...'
        });
    }

    dispose() {
        this.outputChannel.dispose();
    }
}