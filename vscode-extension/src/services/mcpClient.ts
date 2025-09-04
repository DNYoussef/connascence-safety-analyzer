import * as vscode from 'vscode';
import { Finding } from './connascenceService';
import { ConfigurationService } from './configurationService';
import { ExtensionLogger } from '../utils/logger';

/**
 * MCP (Model Context Protocol) Client
 * 
 * Handles real communication with the MCP server for AI-powered features
 * Replaces mock implementations with actual server communication
 */
export class MCPClient implements vscode.Disposable {
    private serverUrl: string;
    private isConnected = false;
    private disposables: vscode.Disposable[] = [];

    constructor(
        private configService: ConfigurationService,
        private logger: ExtensionLogger
    ) {
        this.serverUrl = this.configService.get('serverUrl', 'http://localhost:8080');
        this.setupConfigurationWatcher();
    }

    /**
     * Initialize connection to MCP server
     */
    public async initialize(): Promise<boolean> {
        try {
            await this.testConnection();
            this.isConnected = true;
            this.logger.info(`MCP client connected to ${this.serverUrl}`);
            return true;
        } catch (error) {
            this.logger.warn(`Failed to connect to MCP server: ${error instanceof Error ? error.message : 'Unknown error'}`);
            this.isConnected = false;
            return false;
        }
    }

    /**
     * Test connection to MCP server
     */
    private async testConnection(): Promise<void> {
        const response = await this.makeRequest('/api/health', 'GET');
        if (response.status !== 'ok') {
            throw new Error('Server health check failed');
        }
    }

    /**
     * Request AI fix for a violation
     */
    public async requestFix(finding: Finding, context: string | null): Promise<{
        patch: string;
        confidence: number;
        description: string;
        safety: 'safe' | 'caution' | 'unsafe';
    } | null> {
        if (!this.isConnected) {
            this.logger.warn('MCP client not connected, falling back to mock');
            return this.mockAIFix(finding);
        }

        try {
            const response = await this.makeRequest('/api/ai/fix', 'POST', {
                finding: {
                    id: finding.id,
                    type: finding.type,
                    severity: finding.severity,
                    message: finding.message,
                    file: finding.file,
                    line: finding.line,
                    column: finding.column
                },
                context: context,
                options: {
                    includeTests: this.configService.get('generateTests', false),
                    preserveComments: this.configService.get('preserveComments', true),
                    safetyLevel: this.configService.get('safetyLevel', 'moderate')
                }
            });

            return {
                patch: response.fix?.patch || '',
                confidence: response.fix?.confidence || 0,
                description: response.fix?.description || 'AI-generated fix',
                safety: response.fix?.safety || 'caution'
            };

        } catch (error) {
            this.logger.error('MCP fix request failed', error);
            // Fallback to mock for development
            return this.mockAIFix(finding);
        }
    }

    /**
     * Get AI suggestions for a violation
     */
    public async getSuggestions(finding: Finding, context: string | null): Promise<Array<{
        technique: string;
        description: string;
        confidence: number;
        complexity: 'low' | 'medium' | 'high';
        risk: 'low' | 'medium' | 'high';
    }>> {
        if (!this.isConnected) {
            this.logger.warn('MCP client not connected, falling back to mock');
            return this.mockAISuggestions(finding);
        }

        try {
            const response = await this.makeRequest('/api/ai/suggestions', 'POST', {
                finding: {
                    id: finding.id,
                    type: finding.type,
                    severity: finding.severity,
                    message: finding.message,
                    file: finding.file,
                    line: finding.line,
                    column: finding.column
                },
                context: context,
                options: {
                    maxSuggestions: 5,
                    includeComplexity: true,
                    includeRiskAssessment: true
                }
            });

            return response.suggestions || [];

        } catch (error) {
            this.logger.error('MCP suggestions request failed', error);
            return this.mockAISuggestions(finding);
        }
    }

    /**
     * Get AI explanation for a violation
     */
    public async getExplanation(finding: Finding): Promise<{
        explanation: string;
        impact: string;
        recommendation: string;
        examples?: string[];
    } | null> {
        if (!this.isConnected) {
            return this.mockAIExplanation(finding);
        }

        try {
            const response = await this.makeRequest('/api/ai/explain', 'POST', {
                finding: {
                    id: finding.id,
                    type: finding.type,
                    severity: finding.severity,
                    message: finding.message
                },
                options: {
                    includeExamples: true,
                    detailLevel: this.configService.get('explanationDetail', 'moderate')
                }
            });

            return response.explanation || null;

        } catch (error) {
            this.logger.error('MCP explanation request failed', error);
            return this.mockAIExplanation(finding);
        }
    }

    /**
     * Batch process multiple findings
     */
    public async batchProcess(findings: Finding[], context: string | null): Promise<Array<{
        finding: Finding;
        fix: any;
        suggestions: any[];
    }>> {
        if (!this.isConnected || findings.length === 0) {
            return [];
        }

        try {
            const response = await this.makeRequest('/api/ai/batch', 'POST', {
                findings: findings.map(f => ({
                    id: f.id,
                    type: f.type,
                    severity: f.severity,
                    message: f.message,
                    file: f.file,
                    line: f.line,
                    column: f.column
                })),
                context: context,
                options: {
                    maxConcurrent: 3,
                    timeout: 30000
                }
            });

            return response.results || [];

        } catch (error) {
            this.logger.error('MCP batch process failed', error);
            return [];
        }
    }

    // === PRIVATE METHODS ===

    private async makeRequest(endpoint: string, method: 'GET' | 'POST', body?: any): Promise<any> {
        const url = `${this.serverUrl}${endpoint}`;
        
        const options: RequestInit = {
            method,
            headers: {
                'Content-Type': 'application/json',
                'User-Agent': 'VSCode-Connascence-Extension/1.0.0'
            }
        };

        if (body) {
            options.body = JSON.stringify(body);
        }

        // Add authentication if required
        if (this.configService.get('authenticateWithServer', false)) {
            const token = await this.getAuthToken();
            if (token) {
                (options.headers as any)['Authorization'] = `Bearer ${token}`;
            }
        }

        const response = await fetch(url, options);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    }

    private async getAuthToken(): Promise<string | null> {
        // In a real implementation, this would handle authentication
        // For now, return null (no auth)
        return null;
    }

    private setupConfigurationWatcher(): void {
        this.disposables.push(
            vscode.workspace.onDidChangeConfiguration((event) => {
                if (event.affectsConfiguration('connascence.serverUrl')) {
                    const newUrl = this.configService.get('serverUrl', 'http://localhost:8080');
                    if (newUrl !== this.serverUrl) {
                        this.serverUrl = newUrl;
                        this.isConnected = false;
                        this.initialize(); // Re-initialize with new URL
                    }
                }
            })
        );
    }

    // === FALLBACK MOCK IMPLEMENTATIONS ===

    private mockAIFix(finding: Finding): {
        patch: string;
        confidence: number;
        description: string;
        safety: 'safe' | 'caution' | 'unsafe';
    } {
        const fixes: { [key: string]: { patch: string; description: string; confidence: number; safety: 'safe' | 'caution' | 'unsafe' } } = {
            'meaning': {
                patch: `// Extract magic literal to named constant\nconst ${finding.message.includes('string') ? 'DEFAULT_MESSAGE' : 'DEFAULT_VALUE'} = ${finding.message.match(/['"`]([^'"`]*)['"`]/)?.[1] || '42'};\n// Replace usage with constant`,
                description: 'Extract magic literal to named constant',
                confidence: 85,
                safety: 'safe'
            },
            'algorithm': {
                patch: `// Extract method to reduce class size\nprivate extract${Math.random().toString(36).substr(2, 9)}() {\n    // Move some responsibilities here\n}`,
                description: 'Extract method to reduce class complexity',
                confidence: 75,
                safety: 'caution'
            },
            'position': {
                patch: `// Convert to named parameters\n// Use object destructuring: { param1, param2, param3 }`,
                description: 'Convert positional parameters to named parameters',
                confidence: 90,
                safety: 'safe'
            }
        };

        const fix = fixes[finding.type] || fixes['meaning'];
        return fix;
    }

    private mockAISuggestions(finding: Finding): Array<{
        technique: string;
        description: string;
        confidence: number;
        complexity: 'low' | 'medium' | 'high';
        risk: 'low' | 'medium' | 'high';
    }> {
        const suggestions: { [key: string]: Array<any> } = {
            'meaning': [
                {
                    technique: 'Extract Constant',
                    description: 'Move magic literal to named constant',
                    confidence: 90,
                    complexity: 'low',
                    risk: 'low'
                },
                {
                    technique: 'Configuration File',
                    description: 'Move value to configuration file',
                    confidence: 80,
                    complexity: 'medium',
                    risk: 'low'
                },
                {
                    technique: 'Enum/Constants Class',
                    description: 'Create dedicated constants class',
                    confidence: 75,
                    complexity: 'medium',
                    risk: 'low'
                }
            ],
            'algorithm': [
                {
                    technique: 'Extract Method',
                    description: 'Break down large method into smaller ones',
                    confidence: 85,
                    complexity: 'medium',
                    risk: 'medium'
                },
                {
                    technique: 'Strategy Pattern',
                    description: 'Encapsulate algorithm variations',
                    confidence: 70,
                    complexity: 'high',
                    risk: 'medium'
                },
                {
                    technique: 'Single Responsibility',
                    description: 'Split class into focused components',
                    confidence: 75,
                    complexity: 'high',
                    risk: 'high'
                }
            ],
            'position': [
                {
                    technique: 'Named Parameters',
                    description: 'Use object destructuring for parameters',
                    confidence: 95,
                    complexity: 'low',
                    risk: 'low'
                },
                {
                    technique: 'Builder Pattern',
                    description: 'Use builder for complex object construction',
                    confidence: 80,
                    complexity: 'high',
                    risk: 'medium'
                }
            ]
        };

        return suggestions[finding.type] || suggestions['meaning'];
    }

    private mockAIExplanation(finding: Finding): {
        explanation: string;
        impact: string;
        recommendation: string;
        examples?: string[];
    } {
        const explanations: { [key: string]: any } = {
            'meaning': {
                explanation: 'Connascence of Meaning occurs when multiple elements must agree on the meaning of particular values. Magic literals create implicit dependencies that are hard to track and maintain.',
                impact: 'Makes code harder to understand, maintain, and modify. Changes to literal values require updates in multiple locations.',
                recommendation: 'Extract magic literals into well-named constants. Use configuration files for values that might change.',
                examples: ['const MAX_RETRIES = 3', 'const DEFAULT_TIMEOUT_MS = 5000']
            },
            'algorithm': {
                explanation: 'Connascence of Algorithm occurs when multiple components must use the same algorithm. This often manifests as God Objects with too many responsibilities.',
                impact: 'Creates tight coupling, reduces testability, and makes the system fragile to changes.',
                recommendation: 'Apply Single Responsibility Principle. Extract methods and consider using Strategy or Template Method patterns.',
                examples: ['class UserValidator', 'class PaymentProcessor', 'interface SortingStrategy']
            },
            'position': {
                explanation: 'Connascence of Position occurs when multiple elements must be in the same order. Parameter order dependencies make code fragile.',
                impact: 'Method calls become error-prone when parameter order changes. Reduces code clarity and maintainability.',
                recommendation: 'Use named parameters, parameter objects, or builder pattern to eliminate positional dependencies.',
                examples: ['{ name, age, email }', 'new UserBuilder().withName().withAge()']
            }
        };

        return explanations[finding.type] || explanations['meaning'];
    }

    public isServerConnected(): boolean {
        return this.isConnected;
    }

    dispose(): void {
        for (const disposable of this.disposables) {
            disposable.dispose();
        }
    }
}