import * as vscode from 'vscode';

export enum LogLevel {
    ERROR = 0,
    WARN = 1,
    INFO = 2,
    DEBUG = 3
}

/**
 * Professional logging utility for the Connascence extension
 */
export class ExtensionLogger {
    private outputChannel: vscode.OutputChannel;
    private logLevel: LogLevel;

    constructor(channelName: string, logLevel: LogLevel = LogLevel.INFO) {
        this.outputChannel = vscode.window.createOutputChannel(channelName);
        this.logLevel = logLevel;
    }

    private shouldLog(level: LogLevel): boolean {
        return level <= this.logLevel;
    }

    private formatMessage(level: string, message: string, data?: any): string {
        const timestamp = new Date().toISOString();
        const prefix = `[${timestamp}] [${level}]`;
        
        let fullMessage = `${prefix} ${message}`;
        
        if (data) {
            if (data instanceof Error) {
                fullMessage += `\nError: ${data.message}\nStack: ${data.stack}`;
            } else {
                try {
                    fullMessage += `\nData: ${JSON.stringify(data, null, 2)}`;
                } catch (e) {
                    const errorMessage = e instanceof Error ? e.message : String(e);
                    fullMessage += `\nData: [Unable to serialize: ${errorMessage}]`;
                }
            }
        }
        
        return fullMessage;
    }

    public error(message: string, data?: any): void {
        if (this.shouldLog(LogLevel.ERROR)) {
            const formatted = this.formatMessage('ERROR', message, data);
            this.outputChannel.appendLine(formatted);
            this.outputChannel.show(true);
        }
    }

    public warn(message: string, data?: any): void {
        if (this.shouldLog(LogLevel.WARN)) {
            const formatted = this.formatMessage('WARN', message, data);
            this.outputChannel.appendLine(formatted);
        }
    }

    public info(message: string, data?: any): void {
        if (this.shouldLog(LogLevel.INFO)) {
            const formatted = this.formatMessage('INFO', message, data);
            this.outputChannel.appendLine(formatted);
        }
    }

    public debug(message: string, data?: any): void {
        if (this.shouldLog(LogLevel.DEBUG)) {
            const formatted = this.formatMessage('DEBUG', message, data);
            this.outputChannel.appendLine(formatted);
        }
    }

    public setLogLevel(level: LogLevel): void {
        this.logLevel = level;
        this.info(`Log level changed to: ${LogLevel[level]}`);
    }

    public show(): void {
        this.outputChannel.show();
    }

    public dispose(): void {
        this.outputChannel.dispose();
    }
}