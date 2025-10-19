/**
 * Configuration Service
 * Loads runtime configuration from the config API endpoint
 */

interface RuntimeConfig {
  apiBaseUrl: string;
  region?: string;
  error?: string;
}

class ConfigService {
  private config: RuntimeConfig | null = null;
  private loading: boolean = false;
  private error: string | null = null;

  /**
   * Load configuration from the config API endpoint
   */
  async loadConfig(): Promise<RuntimeConfig> {
    // Return cached config if already loaded
    if (this.config) {
      return this.config;
    }

    // Prevent multiple simultaneous loads
    if (this.loading) {
      // Wait for the current load to complete
      while (this.loading) {
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      if (this.config) {
        return this.config;
      }
      if (this.error) {
        throw new Error(this.error);
      }
    }

    this.loading = true;
    this.error = null;
    
    try {
      console.log('🔧 Loading configuration from API...');
      this.config = await this.fetchConfigFromAPI();
      
      if (this.config.error) {
        console.warn('⚠️ Configuration loaded with warning:', this.config.error);
      } else {
        console.log('✅ Configuration loaded successfully:', this.config);
      }
      
      return this.config;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error('❌ Failed to load configuration:', errorMessage);
      this.error = errorMessage;
      
      // Use fallback configuration
      console.log('🔄 Using fallback configuration');
      this.config = {
        apiBaseUrl: 'http://localhost:3000/v1',
        error: errorMessage
      };
      return this.config;
    } finally {
      this.loading = false;
    }
  }

  private async fetchConfigFromAPI(): Promise<RuntimeConfig> {
    // Try to get API base URL from Amplify configuration
    // This will be set by the main App component after Amplify is configured
    const amplifyConfig = (window as { amplifyConfig?: any }).amplifyConfig;
    const apiBaseUrl = amplifyConfig?.API?.REST?.HealthcareAPI?.endpoint;
    
    if (apiBaseUrl) {
      console.log('📍 Using API base URL from Amplify config:', apiBaseUrl);
      
      try {
        // Fetch config from the /config endpoint
        const configEndpoint = `${apiBaseUrl}/config`;
        console.log(`📡 Fetching config from: ${configEndpoint}`);
        
        const response = await fetch(configEndpoint, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          // Add timeout
          signal: AbortSignal.timeout(5000)
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const config = await response.json();
        
        if (!config.apiBaseUrl) {
          throw new Error('Invalid config response: missing apiBaseUrl');
        }

        console.log(`✅ Config loaded from API`);
        return config;

      } catch (error) {
        console.warn(`❌ Failed to fetch config from API:`, error);
        // Fall back to using the Amplify config directly
        console.log('🔄 Using Amplify config as fallback');
        return {
          apiBaseUrl,
          region: amplifyConfig?.API?.REST?.HealthcareAPI?.region || 'us-east-1'
        };
      }
    }

    // Final fallback for development
    console.log('🔄 Using localhost fallback');
    return {
      apiBaseUrl: 'http://localhost:3000/v1',
      region: 'us-east-1'
    };
  }

  /**
   * Get current configuration (returns null if not loaded)
   */
  getConfig(): RuntimeConfig | null {
    return this.config;
  }

  /**
   * Check if configuration is currently loading
   */
  isLoading(): boolean {
    return this.loading;
  }

  /**
   * Get any error that occurred during loading
   */
  getError(): string | null {
    return this.error;
  }

  /**
   * Clear cached configuration (force reload on next access)
   */
  clearCache(): void {
    this.config = null;
    this.error = null;
  }
}

export const configService = new ConfigService();
export type { RuntimeConfig };
