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
exports.OutputChannelManager = void 0;
const vscode = __importStar(require("vscode"));
class OutputChannelManager {
    constructor(channelName = 'Connascence') {
        this.isVisible = false;
        this.outputChannel = vscode.window.createOutputChannel(channelName);
    }
    appendLine(message) {
        const timestamp = new Date().toLocaleTimeString();
        this.outputChannel.appendLine(`[${timestamp}] ${message}`);
    }
    append(message) {
        this.outputChannel.append(message);
    }
    clear() {
        this.outputChannel.clear();
    }
    show(preserveFocus = true) {
        this.outputChannel.show(preserveFocus);
        this.isVisible = true;
    }
    hide() {
        this.outputChannel.hide();
        this.isVisible = false;
    }
    logInfo(message) {
        this.appendLine(`[INFO] ${message}`);
    }
    logWarning(message) {
        this.appendLine(`[WARN] ${message}`);
    }
    logError(message) {
        this.appendLine(`[ERROR] ${message}`);
    }
    logSuccess(message) {
        this.appendLine(`[SUCCESS] ${message}`);
    }
    logAnalysis(message) {
        this.appendLine(`[ANALYSIS] ${message}`);
    }
    logRefactoring(message) {
        this.appendLine(`[REFACTOR] ${message}`);
    }
    showProgress(message) {
        this.appendLine(`[PROGRESS] ${message}`);
    }
    dispose() {
        this.outputChannel.dispose();
    }
    get visible() {
        return this.isVisible;
    }
}
exports.OutputChannelManager = OutputChannelManager;
//# sourceMappingURL=outputChannelManager.js.map