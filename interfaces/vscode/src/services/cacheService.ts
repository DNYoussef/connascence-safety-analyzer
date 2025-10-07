/**
 * Cache Service for Analysis Results
 *
 * Provides intelligent caching of analysis results to improve performance
 * and reduce redundant analysis operations.
 */

import * as vscode from 'vscode';
import * as crypto from 'crypto';
import * as fs from 'fs';

export interface CacheEntry<T> {
    data: T;
    timestamp: number;
    contentHash: string;
    version: string;
}

export interface CacheOptions {
    ttl?: number;  // Time to live in milliseconds
    maxSize?: number;  // Maximum cache size
    persistent?: boolean;  // Store to disk
}

export class CacheService {
    private memoryCache: Map<string, CacheEntry<any>> = new Map();
    private readonly defaultTTL: number = 5 * 60 * 1000;  // 5 minutes
    private readonly maxCacheSize: number = 100;  // Maximum entries
    private readonly version: string = '2.0.2';
    private context: vscode.ExtensionContext;

    constructor(context: vscode.ExtensionContext) {
        this.context = context;
        this.loadPersistentCache();
        this.startCleanupTimer();
    }

    /**
     * Get cached data if valid, otherwise return null
     */
    async get<T>(key: string, contentHash?: string): Promise<T | null> {
        const entry = this.memoryCache.get(key);

        if (!entry) {
            return null;
        }

        // Check if cache is expired
        const now = Date.now();
        if (now - entry.timestamp > this.defaultTTL) {
            this.memoryCache.delete(key);
            return null;
        }

        // Check if content has changed
        if (contentHash && entry.contentHash !== contentHash) {
            this.memoryCache.delete(key);
            return null;
        }

        // Check version compatibility
        if (entry.version !== this.version) {
            this.memoryCache.delete(key);
            return null;
        }

        return entry.data as T;
    }

    /**
     * Store data in cache
     */
    async set<T>(key: string, data: T, contentHash: string, options?: CacheOptions): Promise<void> {
        // Enforce cache size limit
        if (this.memoryCache.size >= (options?.maxSize || this.maxCacheSize)) {
            this.evictOldest();
        }

        const entry: CacheEntry<T> = {
            data,
            timestamp: Date.now(),
            contentHash,
            version: this.version
        };

        this.memoryCache.set(key, entry);

        // Persist to disk if requested
        if (options?.persistent) {
            await this.persistToDisk(key, entry);
        }
    }

    /**
     * Check if key exists in cache and is valid
     */
    has(key: string, contentHash?: string): boolean {
        const entry = this.memoryCache.get(key);
        if (!entry) return false;

        const now = Date.now();
        const isExpired = now - entry.timestamp > this.defaultTTL;
        const hashMismatch = contentHash && entry.contentHash !== contentHash;
        const versionMismatch = entry.version !== this.version;

        return !isExpired && !hashMismatch && !versionMismatch;
    }

    /**
     * Invalidate cache entry
     */
    invalidate(key: string): void {
        this.memoryCache.delete(key);
        this.removePersistent(key);
    }

    /**
     * Clear all cache entries
     */
    clear(): void {
        this.memoryCache.clear();
        this.clearPersistentCache();
    }

    /**
     * Get cache statistics
     */
    getStats(): { size: number; keys: string[]; oldestEntry: number | null } {
        let oldestTimestamp: number | null = null;

        for (const entry of this.memoryCache.values()) {
            if (oldestTimestamp === null || entry.timestamp < oldestTimestamp) {
                oldestTimestamp = entry.timestamp;
            }
        }

        return {
            size: this.memoryCache.size,
            keys: Array.from(this.memoryCache.keys()),
            oldestEntry: oldestTimestamp
        };
    }

    /**
     * Generate content hash for file
     */
    static generateHash(content: string): string {
        return crypto.createHash('sha256').update(content).digest('hex').substring(0, 16);
    }

    /**
     * Generate cache key for file analysis
     */
    static generateFileKey(filePath: string, analysisType: string): string {
        return `file:${analysisType}:${filePath}`;
    }

    /**
     * Generate cache key for workspace analysis
     */
    static generateWorkspaceKey(workspacePath: string, analysisType: string): string {
        return `workspace:${analysisType}:${workspacePath}`;
    }

    /**
     * Evict oldest cache entry
     */
    private evictOldest(): void {
        let oldestKey: string | null = null;
        let oldestTimestamp = Date.now();

        for (const [key, entry] of this.memoryCache.entries()) {
            if (entry.timestamp < oldestTimestamp) {
                oldestTimestamp = entry.timestamp;
                oldestKey = key;
            }
        }

        if (oldestKey) {
            this.memoryCache.delete(oldestKey);
        }
    }

    /**
     * Start periodic cleanup of expired entries
     */
    private startCleanupTimer(): void {
        setInterval(() => {
            this.cleanupExpired();
        }, 60000);  // Clean up every minute
    }

    /**
     * Remove expired cache entries
     */
    private cleanupExpired(): void {
        const now = Date.now();
        const keysToDelete: string[] = [];

        for (const [key, entry] of this.memoryCache.entries()) {
            if (now - entry.timestamp > this.defaultTTL) {
                keysToDelete.push(key);
            }
        }

        for (const key of keysToDelete) {
            this.memoryCache.delete(key);
        }

        if (keysToDelete.length > 0) {
            console.log(`[CacheService] Cleaned up ${keysToDelete.length} expired entries`);
        }
    }

    /**
     * Load persistent cache from disk
     */
    private loadPersistentCache(): void {
        try {
            const cachedData = this.context.globalState.get<Record<string, CacheEntry<any>>>('analysisCache');
            if (cachedData) {
                for (const [key, entry] of Object.entries(cachedData)) {
                    // Only load recent entries
                    if (Date.now() - entry.timestamp < this.defaultTTL) {
                        this.memoryCache.set(key, entry);
                    }
                }
                console.log(`[CacheService] Loaded ${this.memoryCache.size} cached entries from disk`);
            }
        } catch (error) {
            console.error('[CacheService] Failed to load persistent cache:', error);
        }
    }

    /**
     * Persist cache entry to disk
     */
    private async persistToDisk(key: string, entry: CacheEntry<any>): Promise<void> {
        try {
            const cachedData = this.context.globalState.get<Record<string, CacheEntry<any>>>('analysisCache', {});
            cachedData[key] = entry;
            await this.context.globalState.update('analysisCache', cachedData);
        } catch (error) {
            console.error('[CacheService] Failed to persist cache entry:', error);
        }
    }

    /**
     * Remove persistent cache entry
     */
    private removePersistent(key: string): void {
        try {
            const cachedData = this.context.globalState.get<Record<string, CacheEntry<any>>>('analysisCache', {});
            delete cachedData[key];
            this.context.globalState.update('analysisCache', cachedData);
        } catch (error) {
            console.error('[CacheService] Failed to remove persistent entry:', error);
        }
    }

    /**
     * Clear all persistent cache
     */
    private clearPersistentCache(): void {
        try {
            this.context.globalState.update('analysisCache', {});
        } catch (error) {
            console.error('[CacheService] Failed to clear persistent cache:', error);
        }
    }

    /**
     * Dispose and save cache
     */
    async dispose(): Promise<void> {
        // Save current cache state to disk
        try {
            const cacheObject: Record<string, CacheEntry<any>> = {};
            for (const [key, entry] of this.memoryCache.entries()) {
                cacheObject[key] = entry;
            }
            await this.context.globalState.update('analysisCache', cacheObject);
            console.log('[CacheService] Saved cache state on dispose');
        } catch (error) {
            console.error('[CacheService] Failed to save cache on dispose:', error);
        }
    }
}

/**
 * Incremental Analysis Tracker
 *
 * Tracks file modifications to enable incremental analysis
 */
export class IncrementalAnalysisTracker {
    private fileVersions: Map<string, number> = new Map();
    private modifiedFiles: Set<string> = new Set();

    /**
     * Track file modification
     */
    trackModification(filePath: string): void {
        const currentVersion = this.fileVersions.get(filePath) || 0;
        this.fileVersions.set(filePath, currentVersion + 1);
        this.modifiedFiles.add(filePath);
    }

    /**
     * Check if file has been modified since last analysis
     */
    isModified(filePath: string): boolean {
        return this.modifiedFiles.has(filePath);
    }

    /**
     * Get list of modified files
     */
    getModifiedFiles(): string[] {
        return Array.from(this.modifiedFiles);
    }

    /**
     * Mark file as analyzed
     */
    markAnalyzed(filePath: string): void {
        this.modifiedFiles.delete(filePath);
    }

    /**
     * Clear all tracking data
     */
    clear(): void {
        this.fileVersions.clear();
        this.modifiedFiles.clear();
    }

    /**
     * Get file version
     */
    getVersion(filePath: string): number {
        return this.fileVersions.get(filePath) || 0;
    }
}
