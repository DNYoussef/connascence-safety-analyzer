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
exports.ExtensionLogger = exports.LogLevel = void 0;
const vscode = __importStar(require("vscode"));
var LogLevel;
(function (LogLevel) {
    LogLevel[LogLevel["ERROR"] = 0] = "ERROR";
    LogLevel[LogLevel["WARN"] = 1] = "WARN";
    LogLevel[LogLevel["INFO"] = 2] = "INFO";
    LogLevel[LogLevel["DEBUG"] = 3] = "DEBUG";
})(LogLevel || (exports.LogLevel = LogLevel = {}));
/**
 * Professional logging utility for the Connascence extension
 */
class ExtensionLogger {
    constructor(channelName, logLevel = LogLevel.INFO) {
        this.outputChannel = vscode.window.createOutputChannel(channelName);
        this.logLevel = logLevel;
    }
    shouldLog(level) {
        return level <= this.logLevel;
    }
    formatMessage(level, message, data) {
        const timestamp = new Date().toISOString();
        const prefix = `[${timestamp}] [${level}]`;
        let fullMessage = `${prefix} ${message}`;
        if (data) {
            if (data instanceof Error) {
                fullMessage += `\nError: ${data.message}\nStack: ${data.stack}`;
            }
            else {
                try {
                    fullMessage += `\nData: ${JSON.stringify(data, null, 2)}`;
                }
                catch (e) {
                    fullMessage += `\nData: [Unable to serialize: ${e.message}]`;
                }
            }
        }
        return fullMessage;
    }
    error(message, data) {
        if (this.shouldLog(LogLevel.ERROR)) {
            const formatted = this.formatMessage('ERROR', message, data);
            this.outputChannel.appendLine(formatted);
            this.outputChannel.show(true);
        }
    }
    warn(message, data) {
        if (this.shouldLog(LogLevel.WARN)) {
            const formatted = this.formatMessage('WARN', message, data);
            this.outputChannel.appendLine(formatted);
        }
    }
    info(message, data) {
        if (this.shouldLog(LogLevel.INFO)) {
            const formatted = this.formatMessage('INFO', message, data);
            this.outputChannel.appendLine(formatted);
        }
    }
    debug(message, data) {
        if (this.shouldLog(LogLevel.DEBUG)) {
            const formatted = this.formatMessage('DEBUG', message, data);
            this.outputChannel.appendLine(formatted);
        }
    }
    setLogLevel(level) {
        this.logLevel = level;
        this.info(`Log level changed to: ${LogLevel[level]}`);
    }
    show() {
        this.outputChannel.show();
    }
    dispose() {
        this.outputChannel.dispose();
    }
}
exports.ExtensionLogger = ExtensionLogger;
//# sourceMappingURL=logger.js.map