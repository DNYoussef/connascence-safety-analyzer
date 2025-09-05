/**
 * Output Channel Logger - VS Code logging utility
 */

import * as vscode from 'vscode';

export class OutputChannelLogger {
    private static instance: OutputChannelLogger;
    private outputChannel: vscode.OutputChannel;

    private constructor() {
        this.outputChannel = vscode.window.createOutputChannel('Connascence Safety Analyzer');
    }

    public static getInstance(): OutputChannelLogger {
        if (!OutputChannelLogger.instance) {
            OutputChannelLogger.instance = new OutputChannelLogger();
        }
        return OutputChannelLogger.instance;
    }

    public info(message: string): void {
        this.outputChannel.appendLine(`[INFO] ${message}`);
    }

    public warn(message: string): void {
        this.outputChannel.appendLine(`[WARN] ${message}`);
    }

    public error(message: string): void {
        this.outputChannel.appendLine(`[ERROR] ${message}`);
    }

    public debug(message: string): void {
        this.outputChannel.appendLine(`[DEBUG] ${message}`);
    }

    public show(): void {
        this.outputChannel.show();
    }

    public dispose(): void {
        this.outputChannel.dispose();
    }
}