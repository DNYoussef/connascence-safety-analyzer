import * as vscode from 'vscode';

export interface TelemetryEvent {
    name: string;
    properties?: { [key: string]: any };
    measurements?: { [key: string]: number };
    timestamp: number;
    sessionId?: string;
    userId?: string;
}

export class TelemetryService {
    private events: TelemetryEvent[] = [];
    private sessionId: string;
    private userId: string | undefined;
    private enabled: boolean;

    constructor() {
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

    logEvent(name: string, properties?: { [key: string]: any }, measurements?: { [key: string]: number }): void {
        if (!this.enabled) return;

        const event: TelemetryEvent = {
            name,
            properties: {
                ...properties,
                sessionId: this.sessionId,
                userId: this.userId,
                timestamp: Date.now()
            },
            measurements,
            timestamp: Date.now()
        };

        this.events.push(event);
        this.sendEvent(event);
    }

    logError(error: Error, context?: string): void {
        this.logEvent('error.occurred', {
            error: error.message,
            stack: error.stack,
            context,
            name: error.name
        });
    }

    logPerformance(operation: string, duration: number, success: boolean): void {
        this.logEvent('performance.operation', {
            operation,
            success
        }, {
            duration
        });
    }

    logFeatureUsage(feature: string, action: string, value?: any): void {
        this.logEvent('feature.used', {
            feature,
            action,
            value: typeof value === 'object' ? JSON.stringify(value) : String(value)
        });
    }

    logConfiguration(config: any): void {
        // Sanitize sensitive configuration data
        const sanitizedConfig = this.sanitizeConfig(config);
        
        this.logEvent('configuration.changed', {
            ...sanitizedConfig
        });
    }

    logAnalysisMetrics(metrics: {
        filesAnalyzed: number;
        issuesFound: number;
        criticalIssues: number;
        analysisTime: number;
        safetyProfile: string;
        qualityScore?: number;
    }): void {
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

    logExtensionUsage(command: string, duration?: number): void {
        this.logEvent('extension.command', {
            command
        }, duration ? { duration } : undefined);
    }

    async flush(): Promise<void> {
        if (this.events.length === 0) return;

        try {
            // In a real implementation, this would send events to a telemetry service
            // For now, we just log them locally
            console.log(`Flushing ${this.events.length} telemetry events`);
            
            // Clear events after successful flush
            this.events = [];
        } catch (error) {
            console.error('Failed to flush telemetry events:', error);
        }
    }

    getSessionSummary(): any {
        const now = Date.now();
        const sessionStart = this.events.find(e => e.name === 'session.started')?.timestamp || now;
        const sessionDuration = now - sessionStart;

        const eventCounts = this.events.reduce((acc, event) => {
            acc[event.name] = (acc[event.name] || 0) + 1;
            return acc;
        }, {} as { [key: string]: number });

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
                ? analyses.reduce((sum, a) => sum + (a.measurements?.analysisTime || 0), 0) / analyses.length
                : 0
        };
    }

    setUserId(userId: string): void {
        this.userId = userId;
        this.logEvent('user.identified', { userId });
    }

    setEnabled(enabled: boolean): void {
        const wasEnabled = this.enabled;
        this.enabled = enabled;
        
        if (enabled && !wasEnabled) {
            this.logEvent('telemetry.enabled');
        } else if (!enabled && wasEnabled) {
            this.logEvent('telemetry.disabled');
            this.flush(); // Flush any remaining events before disabling
        }
    }

    dispose(): void {
        this.logEvent('session.ended', {
            sessionDuration: Date.now() - (this.events.find(e => e.name === 'session.started')?.timestamp || Date.now())
        });
        
        this.flush();
    }

    // Private methods
    private generateSessionId(): string {
        return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }

    private isTelemetryEnabled(): boolean {
        // Check VS Code global telemetry settings
        const config = vscode.workspace.getConfiguration();
        const globalTelemetry = config.get('telemetry.enableTelemetry', true);
        
        // Check our extension-specific telemetry setting
        const extensionTelemetry = config.get('connascence.enableTelemetry', true);
        
        return globalTelemetry && extensionTelemetry;
    }

    private initializeUserId(): void {
        // In a real implementation, you might generate or retrieve a user ID
        // For privacy, this should be an anonymous identifier
        const config = vscode.workspace.getConfiguration('connascence');
        this.userId = config.get('userId') || this.generateAnonymousUserId();
    }

    private generateAnonymousUserId(): string {
        // Generate a stable but anonymous user ID based on machine characteristics
        const machineId = vscode.env.machineId;
        return `anon-${machineId.substr(0, 8)}`;
    }

    private getExtensionVersion(): string {
        try {
            const extension = vscode.extensions.getExtension('connascence-systems.connascence-safety-analyzer');
            return extension?.packageJSON.version || 'unknown';
        } catch (error) {
            return 'unknown';
        }
    }

    private sanitizeConfig(config: any): any {
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

    private sendEvent(event: TelemetryEvent): void {
        // Send to development console in dev mode
        if (process.env.NODE_ENV === 'development') {
            console.log('[Telemetry]', event);
        }

        // Production telemetry implementation
        try {
            // Option 1: Use VSCode's built-in telemetry reporter (requires vscode-extension-telemetry package)
            // This respects user's telemetry settings automatically
            // const reporter = new TelemetryReporter(extensionId, extensionVersion, key);
            // reporter.sendTelemetryEvent(event.name, event.properties, event.measurements);

            // Option 2: Custom endpoint for self-hosted telemetry
            const telemetryEndpoint = this.getTelemetryEndpoint();
            if (telemetryEndpoint) {
                this.sendToCustomEndpoint(telemetryEndpoint, event);
            }

            // Option 3: Local storage for offline-first telemetry
            this.storeEventLocally(event);

        } catch (error) {
            // Silently fail - telemetry should never crash the extension
            console.error('[Telemetry] Failed to send event:', error);
        }
    }

    private getTelemetryEndpoint(): string | null {
        // Check for custom telemetry endpoint in configuration
        try {
            const vscode = require('vscode');
            const config = vscode.workspace.getConfiguration('connascence');
            return config.get('telemetryEndpoint', null) as string | null;
        } catch {
            return null;
        }
    }

    private async sendToCustomEndpoint(endpoint: string, event: TelemetryEvent): Promise<void> {
        // Only send if user has explicitly configured an endpoint
        if (!endpoint) return;

        try {
            // Use fetch API (available in Node.js 18+)
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'User-Agent': 'Connascence-VSCode-Extension/2.0.2'
                },
                body: JSON.stringify({
                    timestamp: event.timestamp,
                    sessionId: event.sessionId || this.sessionId,
                    userId: event.userId || this.userId,
                    name: event.name,
                    properties: event.properties,
                    measurements: event.measurements
                }),
                signal: AbortSignal.timeout(5000) // 5 second timeout
            });

            if (!response.ok) {
                console.warn(`[Telemetry] Endpoint returned ${response.status}`);
            }
        } catch (error: any) {
            // Silent fail - network errors shouldn't break the extension
            if (error.name !== 'AbortError') {
                console.error('[Telemetry] Network error:', error.message);
            }
        }
    }

    private storeEventLocally(event: TelemetryEvent): void {
        // Store events locally for batch upload or analysis
        try {
            const storageKey = `telemetry_${event.timestamp}`;
            const eventData = JSON.stringify({
                name: event.name,
                properties: event.properties,
                measurements: event.measurements,
                timestamp: event.timestamp
            });

            // Use a simple in-memory cache (could be enhanced with file storage)
            if (this.eventCache.size > 100) {
                // Limit cache size to prevent memory bloat
                const oldestKey = this.eventCache.keys().next().value;
                if (oldestKey) {
                    this.eventCache.delete(oldestKey);
                }
            }
            this.eventCache.set(storageKey, eventData);
        } catch (error) {
            // Silent fail
            console.error('[Telemetry] Failed to cache event:', error);
        }
    }

    private eventCache: Map<string, string> = new Map();

    // Public methods for common telemetry scenarios
    trackCommand(command: string): { end: (success?: boolean) => void } {
        const startTime = Date.now();
        this.logEvent('command.started', { command });

        return {
            end: (success: boolean = true) => {
                const duration = Date.now() - startTime;
                this.logEvent('command.completed', { command, success }, { duration });
            }
        };
    }

    trackAnalysis(analysisType: string): { 
        end: (results: { 
            success: boolean; 
            issueCount: number; 
            fileCount?: number; 
            qualityScore?: number 
        }) => void 
    } {
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

    trackUserInteraction(action: string, element: string, value?: any): void {
        this.logEvent('user.interaction', {
            action,
            element,
            value: value !== undefined ? String(value) : undefined
        });
    }
}