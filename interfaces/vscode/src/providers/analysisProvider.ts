import * as vscode from 'vscode';
import { ConnascenceService } from '../services/connascenceService';

export class ConnascenceAnalysisProvider {
    constructor(private connascenceService: ConnascenceService) {}

    async analyzeDocument(document: vscode.TextDocument): Promise<any> {
        if (!this.isSupportedLanguage(document.languageId)) {
            throw new Error(`Language ${document.languageId} is not supported`);
        }

        return await this.connascenceService.analyzeFile(document.fileName);
    }

    async analyzeWorkspace(): Promise<any> {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders || workspaceFolders.length === 0) {
            throw new Error('No workspace folder is open');
        }

        const workspaceRoot = workspaceFolders[0].uri.fsPath;
        return await this.connascenceService.analyzeWorkspace(workspaceRoot);
    }

    private isSupportedLanguage(languageId: string): boolean {
        return ['python', 'c', 'cpp', 'javascript', 'typescript'].includes(languageId);
    }
}