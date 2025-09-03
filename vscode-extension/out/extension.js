"use strict";
/**
 * VS Code Extension for Connascence Analysis
 *
 * Provides real-time diagnostics, quick fixes, and dashboard integration
 * for connascence analysis in Python codebases.
 */
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
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const ConnascenceExtension_1 = require("./core/ConnascenceExtension");
const logger_1 = require("./utils/logger");
const telemetry_1 = require("./utils/telemetry");
let extension;
let logger;
let telemetry;
function activate(context) {
    // Initialize logger and telemetry
    logger = new logger_1.ExtensionLogger('Connascence');
    telemetry = new telemetry_1.TelemetryReporter(context, logger);
    logger.info('Connascence Analyzer extension activating...');
    telemetry.logEvent('extension.activate.start');
    try {
        // Initialize main extension class
        extension = new ConnascenceExtension_1.ConnascenceExtension(context, logger, telemetry);
        // Activate all components
        extension.activate();
        telemetry.logEvent('extension.activate.success');
        logger.info('Connascence Analyzer extension activated successfully');
    }
    catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        logger.error('Failed to activate extension', error);
        telemetry.logEvent('extension.activate.error', { error: errorMessage });
        vscode.window.showErrorMessage(`Connascence extension failed to activate: ${errorMessage}`);
        throw error;
    }
}
function deactivate() {
    logger?.info('Connascence Analyzer extension deactivating...');
    telemetry?.logEvent('extension.deactivate.start');
    try {
        // Clean up extension resources
        if (extension) {
            extension.dispose();
        }
        if (telemetry) {
            telemetry.dispose();
        }
        logger?.info('Connascence Analyzer extension deactivated successfully');
    }
    catch (error) {
        logger?.error('Error during deactivation', error);
    }
}
//# sourceMappingURL=extension.js.map