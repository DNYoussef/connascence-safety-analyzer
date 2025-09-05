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
exports.TelemetryReporter = void 0;
const vscode = __importStar(require("vscode"));
/**
 * Professional telemetry reporter for analytics and debugging
 */
class TelemetryReporter {
    constructor(context, logger) {
        this.context = context;
        this.logger = logger;
        this.isEnabled = true;
        // Check if telemetry is enabled
        const config = vscode.workspace.getConfiguration('connascence');
        this.isEnabled = config.get('enableTelemetry', true);
        if (!this.isEnabled) {
            this.logger.info('Telemetry disabled by user configuration');
        }
    }
    logEvent(eventName, properties) {
        if (!this.isEnabled) {
            return;
        }
        try {
            const event = {
                name: `connascence.${eventName}`,
                timestamp: new Date().toISOString(),
                properties: {
                    ...properties,
                    sessionId: this.getSessionId(),
                    extensionVersion: this.getExtensionVersion()
                }
            };
            // Log to debug channel in development
            this.logger.debug(`Telemetry event: ${event.name}`, event.properties);
            // Store for later analysis
            this.storeEvent(event);
        }
        catch (error) {
            this.logger.error('Failed to log telemetry event', error);
        }
    }
    logError(error, context) {
        this.logEvent('error', {
            message: error.message,
            stack: error.stack,
            context: context || 'unknown'
        });
    }
    logPerformance(operationName, duration, success) {
        this.logEvent('performance', {
            operation: operationName,
            duration,
            success
        });
    }
    logUsage(feature, action, metadata) {
        this.logEvent('usage', {
            feature,
            action,
            ...metadata
        });
    }
    getSessionId() {
        const SESSION_KEY = 'connascence.sessionId';
        let sessionId = this.context.globalState.get(SESSION_KEY);
        if (!sessionId) {
            sessionId = this.generateId();
            this.context.globalState.update(SESSION_KEY, sessionId);
        }
        return sessionId;
    }
    getExtensionVersion() {
        const extension = vscode.extensions.getExtension('connascence-systems.connascence-safety-analyzer');
        return extension?.packageJSON?.version || 'unknown';
    }
    generateId() {
        return Math.random().toString(36).substr(2, 9);
    }
    storeEvent(event) {
        try {
            const EVENTS_KEY = 'connascence.telemetryEvents';
            const events = this.context.globalState.get(EVENTS_KEY) || [];
            // Keep only last 1000 events to prevent storage bloat
            if (events.length >= 1000) {
                events.shift();
            }
            events.push(event);
            this.context.globalState.update(EVENTS_KEY, events);
        }
        catch (error) {
            this.logger.error('Failed to store telemetry event', error);
        }
    }
    getStoredEvents() {
        const EVENTS_KEY = 'connascence.telemetryEvents';
        return this.context.globalState.get(EVENTS_KEY) || [];
    }
    clearStoredEvents() {
        const EVENTS_KEY = 'connascence.telemetryEvents';
        this.context.globalState.update(EVENTS_KEY, []);
        this.logger.info('Cleared stored telemetry events');
    }
    generateUsageReport() {
        const events = this.getStoredEvents();
        const now = new Date();
        const last30Days = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        const recentEvents = events.filter(e => new Date(e.timestamp) >= last30Days);
        const report = {
            generatedAt: now.toISOString(),
            totalEvents: events.length,
            recentEvents: recentEvents.length,
            mostUsedFeatures: this.getMostUsedFeatures(recentEvents),
            errorRate: this.getErrorRate(recentEvents),
            performanceMetrics: this.getPerformanceMetrics(recentEvents)
        };
        return report;
    }
    getMostUsedFeatures(events) {
        const featureUsage = new Map();
        events.filter(e => e.name === 'connascence.usage')
            .forEach(e => {
            const feature = e.properties?.feature || 'unknown';
            featureUsage.set(feature, (featureUsage.get(feature) || 0) + 1);
        });
        return Array.from(featureUsage.entries())
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10)
            .map(([feature, count]) => ({ feature, count }));
    }
    getErrorRate(events) {
        const totalEvents = events.length;
        const errorEvents = events.filter(e => e.name === 'connascence.error').length;
        return totalEvents > 0 ? (errorEvents / totalEvents) * 100 : 0;
    }
    getPerformanceMetrics(events) {
        const perfEvents = events.filter(e => e.name === 'connascence.performance');
        if (perfEvents.length === 0) {
            return { averageResponseTime: 0, operationCount: 0 };
        }
        const totalDuration = perfEvents.reduce((sum, e) => sum + (e.properties?.duration || 0), 0);
        return {
            averageResponseTime: totalDuration / perfEvents.length,
            operationCount: perfEvents.length,
            successRate: perfEvents.filter(e => e.properties?.success).length / perfEvents.length * 100
        };
    }
    dispose() {
        // Optionally upload final batch of events before disposal
        this.logger.info('Telemetry reporter disposed');
    }
}
exports.TelemetryReporter = TelemetryReporter;
//# sourceMappingURL=telemetry.js.map