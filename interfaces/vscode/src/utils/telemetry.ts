import * as vscode from 'vscode';
import { ExtensionLogger } from './logger';

/**
 * Professional telemetry reporter for analytics and debugging
 */
export class TelemetryReporter {
    private isEnabled: boolean = true;
    
    constructor(
        private context: vscode.ExtensionContext,
        private logger: ExtensionLogger
    ) {
        // Check if telemetry is enabled
        const config = vscode.workspace.getConfiguration('connascence');
        this.isEnabled = config.get('enableTelemetry', true);
        
        if (!this.isEnabled) {
            this.logger.info('Telemetry disabled by user configuration');
        }
    }

    public logEvent(eventName: string, properties?: { [key: string]: any }): void {
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
            
        } catch (error) {
            this.logger.error('Failed to log telemetry event', error);
        }
    }

    public logError(error: Error, context?: string): void {
        this.logEvent('error', {
            message: error.message,
            stack: error.stack,
            context: context || 'unknown'
        });
    }

    public logPerformance(operationName: string, duration: number, success: boolean): void {
        this.logEvent('performance', {
            operation: operationName,
            duration,
            success
        });
    }

    public logUsage(feature: string, action: string, metadata?: any): void {
        this.logEvent('usage', {
            feature,
            action,
            ...metadata
        });
    }

    private getSessionId(): string {
        const SESSION_KEY = 'connascence.sessionId';
        let sessionId = this.context.globalState.get<string>(SESSION_KEY);
        
        if (!sessionId) {
            sessionId = this.generateId();
            this.context.globalState.update(SESSION_KEY, sessionId);
        }
        
        return sessionId;
    }

    private getExtensionVersion(): string {
        const extension = vscode.extensions.getExtension('connascence-systems.connascence-safety-analyzer');
        return extension?.packageJSON?.version || 'unknown';
    }

    private generateId(): string {
        return Math.random().toString(36).substr(2, 9);
    }

    private storeEvent(event: any): void {
        try {
            const EVENTS_KEY = 'connascence.telemetryEvents';
            const events = this.context.globalState.get<any[]>(EVENTS_KEY) || [];
            
            // Keep only last 1000 events to prevent storage bloat
            if (events.length >= 1000) {
                events.shift();
            }
            
            events.push(event);
            this.context.globalState.update(EVENTS_KEY, events);
            
        } catch (error) {
            this.logger.error('Failed to store telemetry event', error);
        }
    }

    public getStoredEvents(): any[] {
        const EVENTS_KEY = 'connascence.telemetryEvents';
        return this.context.globalState.get<any[]>(EVENTS_KEY) || [];
    }

    public clearStoredEvents(): void {
        const EVENTS_KEY = 'connascence.telemetryEvents';
        this.context.globalState.update(EVENTS_KEY, []);
        this.logger.info('Cleared stored telemetry events');
    }

    public generateUsageReport(): any {
        const events = this.getStoredEvents();
        const now = new Date();
        const last30Days = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        
        const recentEvents = events.filter(e => 
            new Date(e.timestamp) >= last30Days
        );
        
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

    private getMostUsedFeatures(events: any[]): any[] {
        const featureUsage = new Map<string, number>();
        
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

    private getErrorRate(events: any[]): number {
        const totalEvents = events.length;
        const errorEvents = events.filter(e => e.name === 'connascence.error').length;
        
        return totalEvents > 0 ? (errorEvents / totalEvents) * 100 : 0;
    }

    private getPerformanceMetrics(events: any[]): any {
        const perfEvents = events.filter(e => e.name === 'connascence.performance');
        
        if (perfEvents.length === 0) {
            return { averageResponseTime: 0, operationCount: 0 };
        }
        
        const totalDuration = perfEvents.reduce((sum, e) => 
            sum + (e.properties?.duration || 0), 0
        );
        
        return {
            averageResponseTime: totalDuration / perfEvents.length,
            operationCount: perfEvents.length,
            successRate: perfEvents.filter(e => e.properties?.success).length / perfEvents.length * 100
        };
    }

    public dispose(): void {
        // Optionally upload final batch of events before disposal
        this.logger.info('Telemetry reporter disposed');
    }
}