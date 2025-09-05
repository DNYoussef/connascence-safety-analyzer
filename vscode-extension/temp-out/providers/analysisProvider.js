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
exports.ConnascenceAnalysisProvider = void 0;
const vscode = __importStar(require("vscode"));
class ConnascenceAnalysisProvider {
    constructor(connascenceService) {
        this.connascenceService = connascenceService;
    }
    async analyzeDocument(document) {
        if (!this.isSupportedLanguage(document.languageId)) {
            throw new Error(`Language ${document.languageId} is not supported`);
        }
        return await this.connascenceService.analyzeFile(document.fileName);
    }
    async analyzeWorkspace() {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders || workspaceFolders.length === 0) {
            throw new Error('No workspace folder is open');
        }
        const workspaceRoot = workspaceFolders[0].uri.fsPath;
        return await this.connascenceService.analyzeWorkspace(workspaceRoot);
    }
    isSupportedLanguage(languageId) {
        return ['python', 'c', 'cpp', 'javascript', 'typescript'].includes(languageId);
    }
}
exports.ConnascenceAnalysisProvider = ConnascenceAnalysisProvider;
//# sourceMappingURL=analysisProvider.js.map