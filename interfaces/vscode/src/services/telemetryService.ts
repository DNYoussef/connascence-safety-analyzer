import * as vscode from 'vscode';

export interface TelemetryEvent {
    name: string;
    properties?: { [key: string]: any };
    measurements?: { [key: string]: number };
    timestamp: number;
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
        // In a real implementation, this would send the event to a telemetry service
        // For development, we can log to console or send to a local endpoint
        
        if (process.env.NODE_ENV === 'development') {
            console.log('Telemetry Event:', event);
        }
        
        // TODO: Implement actual telemetry endpoint
        // This could send to Application Insights, Google Analytics, or custom endpoint
    }

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