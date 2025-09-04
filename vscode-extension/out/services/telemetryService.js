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
exports.TelemetryService = void 0;
const vscode = __importStar(require("vscode"));
class TelemetryService {
    constructor() {
        this.events = [];
        this.sessionId = this.generateSessionId();
        this.enabled = this.isTelemetryEnabled();
        this.initializeUserId();
        // Log session start
        this.logEvent('session.started', {
            version: this.getExtensionVersion(),
            platform: process.platform,
            nodeVersion: process.version
        });
    }
    logEvent(name, properties, measurements) {
        if (!this.enabled)
            return;
        const event = {
            name,
            properties: {
                ...properties,
                sessionId: this.sessionId,
                userId: this.userId,
                timestamp: Date.now()
            },
            ...(measurements && { measurements }),
            timestamp: Date.now()
        };
        this.events.push(event);
        this.sendEvent(event);
    }
    logError(error, context) {
        this.logEvent('error.occurred', {
            error: error.message,
            stack: error.stack,
            context,
            name: error.name
        });
    }
    logPerformance(operation, duration, success) {
        this.logEvent('performance.operation', {
            operation,
            success
        }, {
            duration
        });
    }
    logFeatureUsage(feature, action, value) {
        this.logEvent('feature.used', {
            feature,
            action,
            value: typeof value === 'object' ? JSON.stringify(value) : String(value)
        });
    }
    logConfiguration(config) {
        // Sanitize sensitive configuration data
        const sanitizedConfig = this.sanitizeConfig(config);
        this.logEvent('configuration.changed', {
            ...sanitizedConfig
        });
    }
    logAnalysisMetrics(metrics) {
        this.logEvent('analysis.completed', {
            safetyProfile: metrics.safetyProfile
        }, {
            filesAnalyzed: metrics.filesAnalyzed,
            issuesFound: metrics.issuesFound,
            criticalIssues: metrics.criticalIssues,
            analysisTime: metrics.analysisTime,
            qualityScore: metrics.qualityScore || 0
        });
    }
    logExtensionUsage(command, duration) {
        this.logEvent('extension.command', {
            command
        }, duration ? { duration } : undefined);
    }
    async flush() {
        if (this.events.length === 0)
            return;
        try {
            // In a real implementation, this would send events to a telemetry service
            // For now, we just log them locally
            console.log(`Flushing ${this.events.length} telemetry events`);
            // Clear events after successful flush
            this.events = [];
        }
        catch (error) {
            console.error('Failed to flush telemetry events:', error);
        }
    }
    getSessionSummary() {
        const now = Date.now();
        const sessionStart = this.events.find(e => e.name === 'session.started')?.timestamp || now;
        const sessionDuration = now - sessionStart;
        const eventCounts = this.events.reduce((acc, event) => {
            acc[event.name] = (acc[event.name] || 0) + 1;
            return acc;
        }, {});
        const errors = this.events.filter(e => e.name === 'error.occurred');
        const analyses = this.events.filter(e => e.name === 'analysis.completed');
        return {
            sessionId: this.sessionId,
            sessionDuration,
            totalEvents: this.events.length,
            eventCounts,
            errorCount: errors.length,
            analysisCount: analyses.length,
            averageAnalysisTime: analyses.length > 0
                ? analyses.reduce((sum, a) => sum + (a.measurements?.['analysisTime'] || 0), 0) / analyses.length
                : 0
        };
    }
    setUserId(userId) {
        this.userId = userId;
        this.logEvent('user.identified', { userId });
    }
    setEnabled(enabled) {
        const wasEnabled = this.enabled;
        this.enabled = enabled;
        if (enabled && !wasEnabled) {
            this.logEvent('telemetry.enabled');
        }
        else if (!enabled && wasEnabled) {
            this.logEvent('telemetry.disabled');
            this.flush(); // Flush any remaining events before disabling
        }
    }
    dispose() {
        this.logEvent('session.ended', {
            sessionDuration: Date.now() - (this.events.find(e => e.name === 'session.started')?.timestamp || Date.now())
        });
        this.flush();
    }
    // Private methods
    generateSessionId() {
        return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }
    isTelemetryEnabled() {
        // Check VS Code global telemetry settings
        const config = vscode.workspace.getConfiguration();
        const globalTelemetry = config.get('telemetry.enableTelemetry', true);
        // Check our extension-specific telemetry setting
        const extensionTelemetry = config.get('connascence.enableTelemetry', true);
        return globalTelemetry && extensionTelemetry;
    }
    initializeUserId() {
        // In a real implementation, you might generate or retrieve a user ID
        // For privacy, this should be an anonymous identifier
        const config = vscode.workspace.getConfiguration('connascence');
        this.userId = config.get('userId') || this.generateAnonymousUserId();
    }
    generateAnonymousUserId() {
        // Generate a stable but anonymous user ID based on machine characteristics
        const machineId = vscode.env.machineId;
        return `anon-${machineId.substr(0, 8)}`;
    }
    getExtensionVersion() {
        try {
            const extension = vscode.extensions.getExtension('connascence-systems.connascence-safety-analyzer');
            return extension?.packageJSON.version || 'unknown';
        }
        catch (error) {
            return 'unknown';
        }
    }
    sanitizeConfig(config) {
        const sanitized = { ...config };
        // Remove sensitive keys
        const sensitiveKeys = ['serverUrl', 'apiKey', 'token', 'password', 'userId'];
        sensitiveKeys.forEach(key => {
            if (sanitized[key]) {
                sanitized[key] = '[REDACTED]';
            }
        });
        return sanitized;
    }
    sendEvent(event) {
        // In a real implementation, this would send the event to a telemetry service
        // For development, we can log to console or send to a local endpoint
        if (process.env['NODE_ENV'] === 'development') {
            console.log('Telemetry Event:', event);
        }
        // TODO: Implement actual telemetry endpoint
        // This could send to Application Insights, Google Analytics, or custom endpoint
    }
    // Public methods for common telemetry scenarios
    trackCommand(command) {
        const startTime = Date.now();
        this.logEvent('command.started', { command });
        return {
            end: (success = true) => {
                const duration = Date.now() - startTime;
                this.logEvent('command.completed', { command, success }, { duration });
            }
        };
    }
    trackAnalysis(analysisType) {
        const startTime = Date.now();
        this.logEvent('analysis.started', { analysisType });
        return {
            end: (results) => {
                const duration = Date.now() - startTime;
                this.logEvent('analysis.completed', {
                    analysisType,
                    success: results.success
                }, {
                    duration,
                    issueCount: results.issueCount,
                    fileCount: results.fileCount || 1,
                    qualityScore: results.qualityScore || 0
                });
            }
        };
    }
    trackUserInteraction(action, element, value) {
        this.logEvent('user.interaction', {
            action,
            element,
            value: value !== undefined ? String(value) : undefined
        });
    }
}
exports.TelemetryService = TelemetryService;
//# sourceMappingURL=telemetryService.js.map