/**
 * Configuration Service
 * Simple service to access Amplify custom outputs
 */

import outputs from '../../amplify_outputs.json';

interface RuntimeConfig {
  apiBaseUrl?: string;
  s3BucketName?: string;
  region?: string;
}

class ConfigService {
  /**
   * Get configuration from Amplify outputs
   */
  getConfig(): RuntimeConfig {
    // Access custom outputs that Amplify will populate from secrets
    const customOutputs = (outputs as { custom?: Record<string, unknown> }).custom || {};
    
    return {
      apiBaseUrl: customOutputs.api_endpoint as string,
      s3BucketName: customOutputs.s3_bucket_name as string,
      region: (customOutputs.aws_region as string) || 'us-east-1'
    };
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
