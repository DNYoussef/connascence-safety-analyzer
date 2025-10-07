/**
 * MCP (Model Context Protocol) Client for Connascence Analysis
 *
 * Handles communication with the connascence analyzer backend server
 * via WebSocket for real-time analysis and feedback.
 */

import * as vscode from 'vscode';

interface MCPMessage {
    type: string;
    requestId?: string;
    data?: any;
    error?: string;
}

interface MCPRequestOptions {
    timeout?: number;
    profile?: string;
    format?: string;
}

export class MCPClient implements vscode.Disposable {
    private ws: any = null; // WebSocket placeholder - will be dynamically imported
    private context: vscode.ExtensionContext;
    private reconnectTimer: NodeJS.Timeout | null = null;
    private isConnected: boolean = false;
    private pendingRequests: Map<string, { resolve: Function; reject: Function }> = new Map();

    constructor(context: vscode.ExtensionContext) {
        this.context = context;
    }

    /**
     * Connect to MCP server with automatic reconnection
     */
    async connect(): Promise<void> {
        const config = vscode.workspace.getConfiguration('connascence');
        const serverUrl = config.get('serverUrl', 'http://localhost:8080');
        const port = new URL(serverUrl).port || '8080';

        try {
            // Dynamic import of ws to avoid bundling issues
            const WebSocket = await this.loadWebSocket();

            return new Promise((resolve, reject) => {
                try {
                    this.ws = new WebSocket(`ws://localhost:${port}/ws`);

                    this.ws.on('open', () => {
                        console.log('[MCP] Connected to server');
                        this.isConnected = true;

                        // Register client capabilities
                        this.sendMessage({
                            type: 'register',
                            data: {
                                client: 'vscode-connascence',
                                version: '2.0.2',
                                capabilities: [
                                    'analyze',
                                    'workspace_analyze',
                                    'safety_validation',
                                    'refactoring_suggestions',
                                    'autofixes',
                                    'report_generation'
                                ]
                            }
                        });

                        resolve();
                    });

                    this.ws.on('message', (data: Buffer) => {
                        this.handleMessage(data.toString());
                    });

                    this.ws.on('close', () => {
                        console.log('[MCP] Disconnected from server');
                        this.isConnected = false;
                        this.scheduleReconnect();
                    });

                    this.ws.on('error', (error: Error) => {
                        console.error('[MCP] Connection error:', error);
                        if (!this.isConnected) {
                            // Initial connection failed - reject with graceful fallback
                            reject(new Error(`MCP server not available: ${error.message}`));
                        }
                    });

                } catch (error) {
                    reject(error);
                }
            });
        } catch (error) {
            // WebSocket not available - graceful degradation
            console.warn('[MCP] WebSocket not available, using CLI fallback');
            throw new Error('MCP server connection failed - using CLI fallback');
        }
    }

    /**
     * Load WebSocket library dynamically to avoid bundling issues
     */
    private async loadWebSocket(): Promise<any> {
        try {
            // Try to load ws module
            return require('ws');
        } catch {
            // Fallback - WebSocket not available
            throw new Error('WebSocket library not available');
        }
    }

    /**
     * Schedule automatic reconnection
     */
    private scheduleReconnect(): void {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
        }

        this.reconnectTimer = setTimeout(() => {
            console.log('[MCP] Attempting to reconnect...');
            this.connect().catch(err => {
                console.error('[MCP] Reconnection failed:', err);
            });
        }, 5000);
    }

    /**
     * Handle incoming messages from MCP server
     */
    private handleMessage(dataString: string): void {
        try {
            const message: MCPMessage = JSON.parse(dataString);

            // Handle response to pending request
            if (message.requestId && this.pendingRequests.has(message.requestId)) {
                const { resolve, reject } = this.pendingRequests.get(message.requestId)!;
                this.pendingRequests.delete(message.requestId);

                if (message.error) {
                    reject(new Error(message.error));
                } else {
                    resolve(message.data);
                }
                return;
            }

            // Handle server-initiated messages
            switch (message.type) {
                case 'notification':
                    this.showNotification(message.data);
                    break;
                case 'progress':
                    this.handleProgress(message.data);
                    break;
                default:
                    console.log('[MCP] Unknown message type:', message.type);
            }
        } catch (error) {
            console.error('[MCP] Error handling message:', error);
        }
    }

    /**
     * Show notification from server
     */
    private showNotification(data: any): void {
        const level = data.level || 'info';
        const text = data.message || data.text;

        switch (level) {
            case 'error':
                vscode.window.showErrorMessage(`Connascence: ${text}`);
                break;
            case 'warning':
                vscode.window.showWarningMessage(`Connascence: ${text}`);
                break;
            default:
                vscode.window.showInformationMessage(`Connascence: ${text}`);
        }
    }

    /**
     * Handle progress updates
     */
    private handleProgress(data: any): void {
        // Could integrate with VSCode progress API
        console.log('[MCP] Progress:', data);
    }

    /**
     * Send message to MCP server
     */
    private sendMessage(message: MCPMessage): void {
        if (this.ws && this.isConnected) {
            this.ws.send(JSON.stringify(message));
        } else {
            console.error('[MCP] Cannot send message: not connected');
        }
    }

    /**
     * Make a request to MCP server with timeout
     */
    async request(type: string, data: any, options: MCPRequestOptions = {}): Promise<any> {
        if (!this.isConnected) {
            throw new Error('MCP server not connected');
        }

        return new Promise((resolve, reject) => {
            const requestId = this.generateRequestId();
            const timeout = options.timeout || 30000;

            // Store pending request
            this.pendingRequests.set(requestId, { resolve, reject });

            // Send request
            this.sendMessage({
                type,
                requestId,
                data
            });

            // Setup timeout
            setTimeout(() => {
                if (this.pendingRequests.has(requestId)) {
                    this.pendingRequests.delete(requestId);
                    reject(new Error('Request timed out'));
                }
            }, timeout);
        });
    }

    /**
     * Generate unique request ID
     */
    private generateRequestId(): string {
        return `req_${Date.now()}_${Math.random().toString(36).substring(7)}`;
    }

    /**
     * Analyze a file
     */
    async analyzeFile(filePath: string, options: any = {}): Promise<any> {
        return this.request('analyze', {
            filePath,
            options
        });
    }

    /**
     * Analyze workspace
     */
    async analyzeWorkspace(workspacePath: string, options: any = {}): Promise<any> {
        return this.request('workspace_analyze', {
            workspacePath,
            options
        });
    }

    /**
     * Validate safety compliance
     */
    async validateSafety(filePath: string, profile: string): Promise<any> {
        return this.request('safety_validation', {
            filePath,
            profile
        });
    }

    /**
     * Get refactoring suggestions
     */
    async getRefactoringSuggestions(filePath: string, selection?: any): Promise<any> {
        return this.request('refactoring_suggestions', {
            filePath,
            selection
        });
    }

    /**
     * Get autofixes
     */
    async getAutofixes(filePath: string): Promise<any> {
        return this.request('autofixes', {
            filePath
        });
    }

    /**
     * Generate report
     */
    async generateReport(workspacePath: string, format: string = 'json'): Promise<any> {
        return this.request('report_generation', {
            workspacePath,
            format
        });
    }

    /**
     * Check if connected
     */
    isServerConnected(): boolean {
        return this.isConnected;
    }

    /**
     * Disconnect from server
     */
    disconnect(): void {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }

        // Reject all pending requests
        for (const [requestId, { reject }] of this.pendingRequests) {
            reject(new Error('Client disconnected'));
        }
        this.pendingRequests.clear();

        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        this.isConnected = false;
    }

    /**
     * Dispose resources
     */
    dispose(): void {
        this.disconnect();
    }
}
