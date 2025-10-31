/**
 * Configuration Service
 * Loads runtime configuration from generated config file
 */

interface RuntimeConfig {
  apiBaseUrl: string;
  s3BucketName: string;
  processedBucketName: string;
  region: string;
}

class ConfigService {
  private config: RuntimeConfig | null = null;

  /**
   * Get configuration - uses environment variables set in build environment
   * Falls back to development defaults if environment variables are not available
   */
  getConfig(): RuntimeConfig {
    // If already loaded, return it
    if (this.config) {
      return this.config;
    }

    // Load from environment variables (set in Amplify console)
    const config: RuntimeConfig = {
      apiBaseUrl: import.meta.env.VITE_API_BASE_URL,
      s3BucketName: import.meta.env.VITE_S3_BUCKET_NAME,
      processedBucketName: import.meta.env.VITE_S3_PROCESSED_BUCKET_NAME,
      region: import.meta.env.VITE_AWS_REGION

    };

    this.config = config;
    return config;
  }

  /**
   * Async method to load configuration (now synchronous since using env vars)
   * Kept for backward compatibility
   */
  async loadConfig(): Promise<RuntimeConfig> {
    return this.getConfig();
  }




  /**
   * Check if configuration is available
   */
  isConfigured(): boolean {
    const config = this.getConfig();
    return !!(config.apiBaseUrl && config.s3BucketName && config.processedBucketName);
  }
}

export const configService = new ConfigService();
export type { RuntimeConfig };
