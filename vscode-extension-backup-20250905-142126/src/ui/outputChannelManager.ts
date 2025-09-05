import * as vscode from 'vscode';

export class OutputChannelManager {
    private outputChannel: vscode.OutputChannel;
    private isVisible = false;

    constructor(channelName = 'Connascence') {
        this.outputChannel = vscode.window.createOutputChannel(channelName);
    }

    appendLine(message: string): void {
        const timestamp = new Date().toLocaleTimeString();
        this.outputChannel.appendLine(`[${timestamp}] ${message}`);
    }

    append(message: string): void {
        this.outputChannel.append(message);
    }

    clear(): void {
        this.outputChannel.clear();
    }

    show(preserveFocus = true): void {
        this.outputChannel.show(preserveFocus);
        this.isVisible = true;
    }

    hide(): void {
        this.outputChannel.hide();
        this.isVisible = false;
    }

    logInfo(message: string): void {
        this.appendLine(`[INFO] ${message}`);
    }

    logWarning(message: string): void {
        this.appendLine(`[WARN] ${message}`);
    }

    logError(message: string): void {
        this.appendLine(`[ERROR] ${message}`);
    }

    logSuccess(message: string): void {
        this.appendLine(`[SUCCESS] ${message}`);
    }

    logAnalysis(message: string): void {
        this.appendLine(`[ANALYSIS] ${message}`);
    }

    logRefactoring(message: string): void {
        this.appendLine(`[REFACTOR] ${message}`);
    }

    showProgress(message: string): void {
        this.appendLine(`[PROGRESS] ${message}`);
    }

    dispose(): void {
        this.outputChannel.dispose();
    }

    get visible(): boolean {
        return this.isVisible;
    }
}