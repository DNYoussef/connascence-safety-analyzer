/**
 * LRU Cache implementation with TTL support for analysis results
 */
import { CacheEntry, LRUCacheOptions } from '../types';

export class LRUCache<K, V> {
    private cache = new Map<K, CacheEntry<V>>();
    private accessOrder: K[] = [];
    private options: LRUCacheOptions;

    constructor(options: LRUCacheOptions) {
        this.options = options;
    }

    get(key: K): V | undefined {
        const entry = this.cache.get(key);
        if (!entry) {
            return undefined;
        }

        // Check TTL
        if (Date.now() - entry.timestamp > this.options.ttlMs) {
            this.delete(key);
            return undefined;
        }

        // Move to end (most recently accessed)
        this.moveToEnd(key);
        return entry.data;
    }

    set(key: K, value: V, fileHash?: string, dependencies?: string[]): void {
        const entry: CacheEntry<V> = {
            data: value,
            timestamp: Date.now(),
            fileHash: fileHash || '',
            dependencies: dependencies || []
        };

        if (this.cache.has(key)) {
            this.cache.set(key, entry);
            this.moveToEnd(key);
        } else {
            // Check if we need to evict
            if (this.cache.size >= this.options.maxSize) {
                this.evictOldest();
            }
            
            this.cache.set(key, entry);
            this.accessOrder.push(key);
        }
    }

    delete(key: K): boolean {
        if (this.cache.has(key)) {
            this.cache.delete(key);
            const index = this.accessOrder.indexOf(key);
            if (index > -1) {
                this.accessOrder.splice(index, 1);
            }
            return true;
        }
        return false;
    }

    clear(): void {
        this.cache.clear();
        this.accessOrder = [];
    }

    has(key: K): boolean {
        const entry = this.cache.get(key);
        if (!entry) {
            return false;
        }

        // Check TTL
        if (Date.now() - entry.timestamp > this.options.ttlMs) {
            this.delete(key);
            return false;
        }

        return true;
    }

    size(): number {
        this.cleanupExpired();
        return this.cache.size;
    }

    keys(): K[] {
        this.cleanupExpired();
        return Array.from(this.cache.keys());
    }

    values(): V[] {
        this.cleanupExpired();
        return Array.from(this.cache.values()).map(entry => entry.data);
    }

    // Check if cached entry is still valid based on file hash
    isValid(key: K, currentFileHash: string): boolean {
        const entry = this.cache.get(key);
        if (!entry) {
            return false;
        }

        // Check TTL
        if (Date.now() - entry.timestamp > this.options.ttlMs) {
            return false;
        }

        // Check file hash
        return entry.fileHash === currentFileHash;
    }

    // Invalidate entries that depend on a changed file
    invalidateDependencies(changedFile: string): void {
        const toDelete: K[] = [];
        
        for (const [key, entry] of this.cache.entries()) {
            if (entry.dependencies.includes(changedFile)) {
                toDelete.push(key);
            }
        }
        
        for (const key of toDelete) {
            this.delete(key);
        }
    }

    // Get cache statistics
    getStats() {
        this.cleanupExpired();
        return {
            size: this.cache.size,
            maxSize: this.options.maxSize,
            ttlMs: this.options.ttlMs,
            hitRate: this.calculateHitRate(),
            oldestEntry: this.getOldestTimestamp(),
            newestEntry: this.getNewestTimestamp()
        };
    }

    private moveToEnd(key: K): void {
        const index = this.accessOrder.indexOf(key);
        if (index > -1) {
            this.accessOrder.splice(index, 1);
            this.accessOrder.push(key);
        }
    }

    private evictOldest(): void {
        if (this.accessOrder.length > 0) {
            const oldest = this.accessOrder[0];
            this.delete(oldest);
        }
    }

    private cleanupExpired(): void {
        const now = Date.now();
        const toDelete: K[] = [];

        for (const [key, entry] of this.cache.entries()) {
            if (now - entry.timestamp > this.options.ttlMs) {
                toDelete.push(key);
            }
        }

        for (const key of toDelete) {
            this.delete(key);
        }
    }

    private hitCount = 0;
    private accessCount = 0;

    private calculateHitRate(): number {
        return this.accessCount > 0 ? (this.hitCount / this.accessCount) * 100 : 0;
    }

    private getOldestTimestamp(): number | null {
        let oldest = Number.MAX_SAFE_INTEGER;
        let hasEntries = false;
        
        for (const entry of this.cache.values()) {
            hasEntries = true;
            oldest = Math.min(oldest, entry.timestamp);
        }
        
        return hasEntries ? oldest : null;
    }

    private getNewestTimestamp(): number | null {
        let newest = 0;
        let hasEntries = false;
        
        for (const entry of this.cache.values()) {
            hasEntries = true;
            newest = Math.max(newest, entry.timestamp);
        }
        
        return hasEntries ? newest : null;
    }
}

/**
 * Specialized cache for analysis results
 */
export class AnalysisCache extends LRUCache<string, any> {
    constructor() {
        super({
            maxSize: 500,
            ttlMs: 5 * 60 * 1000 // 5 minutes
        });
    }

    // Get file hash for cache validation
    static async getFileHash(filePath: string): Promise<string> {
        try {
            const fs = require('fs').promises;
            const crypto = require('crypto');
            const content = await fs.readFile(filePath, 'utf8');
            return crypto.createHash('md5').update(content).digest('hex');
        } catch (error) {
            return Date.now().toString(); // Fallback to timestamp
        }
    }

    async getCachedResult(filePath: string): Promise<any | undefined> {
        const fileHash = await AnalysisCache.getFileHash(filePath);
        
        if (this.isValid(filePath, fileHash)) {
            return this.get(filePath);
        }
        
        return undefined;
    }

    async setCachedResult(filePath: string, result: any, dependencies: string[] = []): Promise<void> {
        const fileHash = await AnalysisCache.getFileHash(filePath);
        this.set(filePath, result, fileHash, dependencies);
    }
}