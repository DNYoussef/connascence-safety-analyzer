import * as vscode from 'vscode';
import WebSocket from 'ws';

export class MCPClient {
    private ws: WebSocket | null = null;
    private context: vscode.ExtensionContext;
    private reconnectTimer: NodeJS.Timeout | null = null;
    private isConnected: boolean = false;

    constructor(context: vscode.ExtensionContext) {
        this.context = context;
    }

    async connect(): Promise<void> {
        const config = vscode.workspace.getConfiguration('connascence');
        const port = config.get('mcpServerPort', 8765);

        return new Promise((resolve, reject) => {
            try {
                this.ws = new WebSocket(`ws://localhost:${port}`);

                this.ws.on('open', () => {
                    console.log('Connected to MCP server');
                    this.isConnected = true;
                    this.sendMessage({
                        type: 'register',
                        client: 'vscode',
                        capabilities: ['analyze', 'autofix', 'report']
                    });
                    resolve();
                });

                this.ws.on('message', (data: string) => {
                    this.handleMessage(JSON.parse(data));
                });

                this.ws.on('close', () => {
                    console.log('Disconnected from MCP server');
                    this.isConnected = false;
                    this.scheduleReconnect();
                });

                this.ws.on('error', (error: Error) => {
                    console.error('MCP connection error:', error);
                    if (!this.isConnected) {
                        reject(error);
                    }
                });

            } catch (error) {
                reject(error);
            }
        });
    }

    private scheduleReconnect(): void {
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
        return new Promise((resolve, reject) => {
            const requestId = Math.random().toString(36).substring(7);

            const messageHandler = (data: string) => {
                const message = JSON.parse(data);
                if (message.requestId === requestId) {
                    this.ws?.off('message', messageHandler);
                    if (message.error) {
                        reject(new Error(message.error));
                    } else {
                        resolve(message.data);
                    }
                }
            };

            this.ws?.on('message', messageHandler);

            this.sendMessage({
                type: 'analyze',
                requestId,
                filePath,
                options
            });

            // Timeout after 30 seconds
            setTimeout(() => {
                this.ws?.off('message', messageHandler);
                reject(new Error('Analysis request timed out'));
            }, 30000);
        });
    }

    disconnect(): void {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }

        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        this.isConnected = false;
    }

    dispose(): void {
        this.disconnect();
    }
}