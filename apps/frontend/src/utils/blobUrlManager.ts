/**
 * Blob URL Manager
 * Manages blob URLs for secure file access and proper cleanup
 */

export class BlobUrlManager {
  private static instance: BlobUrlManager;
  private blobUrls: Map<string, { url: string; createdAt: number; fileId: string }> = new Map();
  private readonly maxAge = 30 * 60 * 1000; // 30 minutes
  private cleanupInterval: number | null = null;

  private constructor() {
    this.startCleanupInterval();
  }

  static getInstance(): BlobUrlManager {
    if (!BlobUrlManager.instance) {
      BlobUrlManager.instance = new BlobUrlManager();
    }
    return BlobUrlManager.instance;
  }

  /**
   * Create a blob URL for a file
   */
  createBlobUrl(blob: Blob, fileId: string): string {
    // Clean up any existing URL for this file
    this.revokeBlobUrl(fileId);

    const url = URL.createObjectURL(blob);
    const key = this.generateKey(fileId);
    
    this.blobUrls.set(key, {
      url,
      createdAt: Date.now(),
      fileId,
    });

    console.log(`Created blob URL for file ${fileId}: ${url}`);
    return url;
  }

  /**
   * Get existing blob URL for a file
   */
  getBlobUrl(fileId: string): string | null {
    const key = this.generateKey(fileId);
    const entry = this.blobUrls.get(key);
    
    if (!entry) {
      return null;
    }

    // Check if URL has expired
    if (Date.now() - entry.createdAt > this.maxAge) {
      this.revokeBlobUrl(fileId);
      return null;
    }

    return entry.url;
  }

  /**
   * Revoke a blob URL for a specific file
   */
  revokeBlobUrl(fileId: string): void {
    const key = this.generateKey(fileId);
    const entry = this.blobUrls.get(key);
    
    if (entry) {
      URL.revokeObjectURL(entry.url);
      this.blobUrls.delete(key);
      console.log(`Revoked blob URL for file ${fileId}`);
    }
  }

  /**
   * Revoke all blob URLs
   */
  revokeAllBlobUrls(): void {
    for (const [, entry] of this.blobUrls.entries()) {
      URL.revokeObjectURL(entry.url);
      console.log(`Revoked blob URL for file ${entry.fileId}`);
    }
    this.blobUrls.clear();
  }

  /**
   * Get statistics about managed blob URLs
   */
  getStats(): {
    totalUrls: number;
    oldestUrl: number | null;
    newestUrl: number | null;
    memoryEstimate: string;
  } {
    const now = Date.now();
    let oldestUrl: number | null = null;
    let newestUrl: number | null = null;

    for (const entry of this.blobUrls.values()) {
      const age = now - entry.createdAt;
      if (oldestUrl === null || age > oldestUrl) {
        oldestUrl = age;
      }
      if (newestUrl === null || age < newestUrl) {
        newestUrl = age;
      }
    }

    // Rough memory estimate (blob URLs themselves are small, but they reference potentially large blobs)
    const memoryEstimate = `~${this.blobUrls.size * 50}KB (URL references only)`;

    return {
      totalUrls: this.blobUrls.size,
      oldestUrl,
      newestUrl,
      memoryEstimate,
    };
  }

  /**
   * Start automatic cleanup of expired URLs
   */
  private startCleanupInterval(): void {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
    }

    this.cleanupInterval = window.setInterval(() => {
      this.cleanupExpiredUrls();
    }, 5 * 60 * 1000); // Check every 5 minutes
  }

  /**
   * Clean up expired blob URLs
   */
  private cleanupExpiredUrls(): void {
    const now = Date.now();
    const expiredKeys: string[] = [];

    for (const [key, entry] of this.blobUrls.entries()) {
      if (now - entry.createdAt > this.maxAge) {
        expiredKeys.push(key);
      }
    }

    for (const key of expiredKeys) {
      const entry = this.blobUrls.get(key);
      if (entry) {
        URL.revokeObjectURL(entry.url);
        this.blobUrls.delete(key);
        console.log(`Cleaned up expired blob URL for file ${entry.fileId}`);
      }
    }

    if (expiredKeys.length > 0) {
      console.log(`Cleaned up ${expiredKeys.length} expired blob URLs`);
    }
  }

  /**
   * Generate a unique key for a file
   */
  private generateKey(fileId: string): string {
    return `blob_${fileId}`;
  }

  /**
   * Destroy the manager and clean up all resources
   */
  destroy(): void {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
      this.cleanupInterval = null;
    }
    this.revokeAllBlobUrls();
  }
}

// Export singleton instance
export const blobUrlManager = BlobUrlManager.getInstance();

// Cleanup on page unload
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    blobUrlManager.revokeAllBlobUrls();
  });
}
