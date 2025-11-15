import * as vscode from 'vscode';
import WebSocket from 'ws';

interface PendingRequest {
    resolve: (message: any) => void;
    reject: (error: Error) => void;
    timeout: NodeJS.Timeout;
}

export class MCPClient {
    private ws: WebSocket | null = null;
    private context: vscode.ExtensionContext;
    private reconnectTimer: NodeJS.Timeout | null = null;
    private isConnected: boolean = false;
    private manualDisconnect: boolean = false;
    private pendingRequests: Map<string, PendingRequest> = new Map();

    constructor(context: vscode.ExtensionContext) {
        this.context = context;
    }

    async connect(): Promise<void> {
        if (this.ws && this.isConnected) {
            return;
        }

        const config = vscode.workspace.getConfiguration('connascence');
        const port = config.get('mcpServerPort', 8765);

        return new Promise((resolve, reject) => {
            try {
                this.manualDisconnect = false;
                this.ws = new WebSocket(`ws://localhost:${port}`);

                this.ws.on('open', () => {
                    console.log('Connected to MCP server');
                    this.isConnected = true;
                    (async () => {
                        try {
                            await this.registerClient();
                            await this.verifyServerHealth();
                            resolve();
                        } catch (error) {
                            reject(error as Error);
                            this.ws?.close();
                        }
                    })();
                });

                this.ws.on('message', (data: WebSocket.RawData) => {
                    const payload = typeof data === 'string' ? data : data.toString();
                    this.handleMessage(JSON.parse(payload));
                });

                this.ws.on('close', () => {
                    console.log('Disconnected from MCP server');
                    this.isConnected = false;
                    this.rejectAllPending(new Error('MCP connection closed'));
                    if (!this.manualDisconnect) {
                        this.scheduleReconnect();
                    }
                });

                this.ws.on('error', (error: Error) => {
                    console.error('MCP connection error:', error);
                    if (!this.isConnected) {
                        reject(error);
                    }
                    this.rejectAllPending(error);
                    if (!this.manualDisconnect) {
                        this.scheduleReconnect();
                    }
                });

            } catch (error) {
                reject(error);
            }
        });
    }

    private scheduleReconnect(): void {
        if (this.manualDisconnect) {
            return;
        }
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
        }

        this.reconnectTimer = setTimeout(() => {
            console.log('Attempting to reconnect to MCP server...');
            this.connect().catch(err => {
                console.error('Reconnection failed:', err);
            });
        }, 5000);
    }

    private handleMessage(message: any): void {
        this.resolvePending(message);

        switch (message.type) {
            case 'analysis_result':
                this.handleAnalysisResult(message.data);
                break;
            case 'notification':
                this.showNotification(message);
                break;
            case 'command':
                this.executeCommand(message.command, message.args);
                break;
            case 'health':
                this.handleHealthResponse(message);
                break;
            case 'registered':
                console.log('Registered with MCP backend');
                break;
            default:
                console.log('Unknown message type:', message.type);
        }
    }

    private handleAnalysisResult(data: any): void {
        // Emit analysis results to extension
        vscode.commands.executeCommand('connascence.updateResults', data);
    }

    private showNotification(message: any): void {
        const level = message.level || 'info';

        switch (level) {
            case 'error':
                vscode.window.showErrorMessage(message.text);
                break;
            case 'warning':
                vscode.window.showWarningMessage(message.text);
                break;
            default:
                vscode.window.showInformationMessage(message.text);
        }
    }

    private executeCommand(command: string, args: any[]): void {
        vscode.commands.executeCommand(command, ...args);
    }

    sendMessage(message: any): void {
        if (this.ws && this.isConnected) {
            this.ws.send(JSON.stringify(message));
        } else {
            console.error('Cannot send message: not connected to MCP server');
        }
    }

    async requestAnalysis(filePath: string, options: any = {}): Promise<any> {
        const requestId = Math.random().toString(36).substring(7);
        const responsePromise = this.waitForResponse(requestId, 30000, 'analysis');

        this.sendMessage({
            type: 'analyze',
            requestId,
            filePath,
            options
        });

        const response = await responsePromise;
        return response.data;
    }

    disconnect(): void {
        this.manualDisconnect = true;
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }

        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        this.isConnected = false;
        this.rejectAllPending(new Error('MCP client disconnected'));
    }

    dispose(): void {
        this.disconnect();
    }

    private async registerClient(): Promise<void> {
        const requestId = `register-${Date.now()}`;
        const responsePromise = this.waitForResponse(requestId, 5000, 'registration');
        this.sendMessage({
            type: 'register',
            requestId,
            client: 'vscode',
            capabilities: ['analyze', 'autofix', 'report']
        });
        await responsePromise;
    }

    private async verifyServerHealth(): Promise<void> {
        const requestId = `health-${Date.now()}`;
        const responsePromise = this.waitForResponse(requestId, 5000, 'health check');
        this.sendMessage({ type: 'health', requestId });
        const response = await responsePromise;
        if (response.status !== 'ok') {
            throw new Error('MCP server reported unhealthy status');
        }
    }

    private waitForResponse(requestId: string, timeoutMs: number, label: string): Promise<any> {
        return new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                this.pendingRequests.delete(requestId);
                reject(new Error(`${label} timed out after ${timeoutMs}ms`));
            }, timeoutMs);

            this.pendingRequests.set(requestId, {
                resolve: (message: any) => {
                    clearTimeout(timeout);
                    this.pendingRequests.delete(requestId);
                    resolve(message);
                },
                reject: (error: Error) => {
                    clearTimeout(timeout);
                    this.pendingRequests.delete(requestId);
                    reject(error);
                },
                timeout
            });
        });
    }

    private resolvePending(message: any): void {
        if (!message.requestId) {
            return;
        }
        const pending = this.pendingRequests.get(message.requestId);
        if (!pending) {
            return;
        }
        if (message.error) {
            pending.reject(new Error(message.error));
        } else {
            pending.resolve(message);
        }
    }

    private rejectAllPending(error: Error): void {
        this.pendingRequests.forEach((pending) => {
            pending.reject(error);
            clearTimeout(pending.timeout);
        });
        this.pendingRequests.clear();
    }

    private handleHealthResponse(message: any): void {
        if (message.status === 'ok') {
            vscode.window.setStatusBarMessage('Connascence MCP backend is healthy', 3000);
        } else {
            vscode.window.showWarningMessage('Connascence MCP backend reported an unhealthy status.');
        }
    }
}