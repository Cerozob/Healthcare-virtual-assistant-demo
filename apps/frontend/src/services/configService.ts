/**
 * Configuration Service
 * Loads runtime configuration from generated config file
 */

interface RuntimeConfig {
  apiBaseUrl: string;
  s3BucketName: string;
  region: string;
}

class ConfigService {
  private config: RuntimeConfig | null = null;
  private configPromise: Promise<RuntimeConfig> | null = null;

  /**
   * Get configuration - loads from runtime-config.json generated at build time
   * Falls back to development defaults if config file is not available
   */
  getConfig(): RuntimeConfig {
    // If already loaded synchronously, return it
    if (this.config) {
      return this.config;
    }

    // Try to load synchronously from window object (if pre-loaded)
    if (typeof window !== 'undefined' && (window as any).__RUNTIME_CONFIG__) {
      const config = (window as any).__RUNTIME_CONFIG__ as RuntimeConfig;
      this.config = config;
      return config;
    }

    // Fallback to development defaults
    console.warn('Runtime config not loaded, using development defaults');
    return {
      apiBaseUrl: 'http://localhost:3000/v1',
      s3BucketName: 'dev-bucket',
      region: 'us-east-1'
    };
  }

  /**
   * Async method to load configuration from runtime-config.json
   * Should be called during app initialization
   */
  async loadConfig(): Promise<RuntimeConfig> {
    if (this.config) {
      return this.config;
    }

    if (this.configPromise) {
      return this.configPromise;
    }

    this.configPromise = fetch('/runtime-config.json')
      .then(response => {
        if (!response.ok) {
          throw new Error(`Failed to load config: ${response.status}`);
        }
        return response.json();
      })
      .then(config => {
        this.config = config;
        // Store in window for synchronous access
        if (typeof window !== 'undefined') {
          (window as any).__RUNTIME_CONFIG__ = config;
        }
        return config;
      })
      .catch(error => {
        console.error('Failed to load runtime config:', error);
        // Use development defaults
        const defaultConfig: RuntimeConfig = {
          apiBaseUrl: 'http://localhost:3000/v1',
          s3BucketName: 'dev-bucket',
          region: 'us-east-1'
        };
        this.config = defaultConfig;
        return defaultConfig;
      });

    return this.configPromise;
  }

  /**
   * Check if configuration is available
   */
  isConfigured(): boolean {
    const config = this.getConfig();
    return !!(config.apiBaseUrl && config.s3BucketName);
  }
}

export const configService = new ConfigService();
export type { RuntimeConfig };
