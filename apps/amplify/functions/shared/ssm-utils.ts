import { SSM } from 'aws-sdk';

const ssm = new SSM();

// Cache for SSM parameters to avoid repeated API calls
const parameterCache = new Map<string, { value: string; expiry: number }>();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

/**
 * Get parameter from SSM Parameter Store with caching
 */
export async function getSSMParameter(parameterName: string): Promise<string> {
  // Check cache first
  const cached = parameterCache.get(parameterName);
  if (cached && Date.now() < cached.expiry) {
    return cached.value;
  }

  try {
    const response = await ssm.getParameter({
      Name: parameterName,
      WithDecryption: true
    }).promise();

    const value = response.Parameter?.Value;
    if (!value) {
      throw new Error(`Parameter ${parameterName} not found or has no value`);
    }

    // Cache the value
    parameterCache.set(parameterName, {
      value,
      expiry: Date.now() + CACHE_TTL
    });

    return value;
  } catch (error) {
    console.error(`Error retrieving SSM parameter ${parameterName}:`, error);
    throw error;
  }
}

/**
 * Get multiple SSM parameters at once
 */
export async function getSSMParameters(parameterNames: string[]): Promise<Record<string, string>> {
  const results: Record<string, string> = {};
  
  // Check cache for all parameters
  const uncachedParams: string[] = [];
  for (const paramName of parameterNames) {
    const cached = parameterCache.get(paramName);
    if (cached && Date.now() < cached.expiry) {
      results[paramName] = cached.value;
    } else {
      uncachedParams.push(paramName);
    }
  }

  // Fetch uncached parameters
  if (uncachedParams.length > 0) {
    try {
      const response = await ssm.getParameters({
        Names: uncachedParams,
        WithDecryption: true
      }).promise();

      // Process successful parameters
      if (response.Parameters) {
        for (const param of response.Parameters) {
          if (param.Name && param.Value) {
            results[param.Name] = param.Value;
            
            // Cache the value
            parameterCache.set(param.Name, {
              value: param.Value,
              expiry: Date.now() + CACHE_TTL
            });
          }
        }
      }

      // Log any invalid parameters
      if (response.InvalidParameters && response.InvalidParameters.length > 0) {
        console.warn('Invalid SSM parameters:', response.InvalidParameters);
      }
    } catch (error) {
      console.error('Error retrieving SSM parameters:', error);
      throw error;
    }
  }

  return results;
}

/**
 * Healthcare-specific SSM parameter helpers
 */
export class HealthcareSSMConfig {
  private static instance: HealthcareSSMConfig;
  private configCache: Record<string, string> = {};
  private lastFetch = 0;
  private readonly CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

  static getInstance(): HealthcareSSMConfig {
    if (!HealthcareSSMConfig.instance) {
      HealthcareSSMConfig.instance = new HealthcareSSMConfig();
    }
    return HealthcareSSMConfig.instance;
  }

  async getConfig(): Promise<Record<string, string>> {
    const now = Date.now();
    
    // Return cached config if still valid
    if (this.configCache && (now - this.lastFetch) < this.CACHE_DURATION) {
      return this.configCache;
    }

    // Fetch all healthcare parameters
    const parameterNames = [
      '/healthcare/agents/orchestrator/agent-id',
      '/healthcare/agents/orchestrator/alias-id',
      '/healthcare/agents/scheduling/agent-id',
      '/healthcare/agents/scheduling/alias-id',
      '/healthcare/agents/information/agent-id',
      '/healthcare/agents/information/alias-id',
      '/healthcare/knowledge-base/id',
      '/healthcare/guardrail/id',
      '/healthcare/storage/knowledge-base-bucket',
      '/healthcare/storage/processed-bucket',
      '/healthcare/database/cluster-arn',
      '/healthcare/database/secret-arn',
      '/healthcare/database/name'
    ];

    try {
      this.configCache = await getSSMParameters(parameterNames);
      this.lastFetch = now;
      return this.configCache;
    } catch (error) {
      console.error('Error fetching healthcare SSM config:', error);
      // Return cached config if available, otherwise throw
      if (Object.keys(this.configCache).length > 0) {
        console.warn('Using cached SSM config due to fetch error');
        return this.configCache;
      }
      throw error;
    }
  }

  async getOrchestratorAgentId(): Promise<string> {
    const config = await this.getConfig();
    return config['/healthcare/agents/orchestrator/agent-id'] || '';
  }

  async getOrchestratorAliasId(): Promise<string> {
    const config = await this.getConfig();
    return config['/healthcare/agents/orchestrator/alias-id'] || '';
  }

  async getSchedulingAgentId(): Promise<string> {
    const config = await this.getConfig();
    return config['/healthcare/agents/scheduling/agent-id'] || '';
  }

  async getSchedulingAliasId(): Promise<string> {
    const config = await this.getConfig();
    return config['/healthcare/agents/scheduling/alias-id'] || '';
  }

  async getInformationAgentId(): Promise<string> {
    const config = await this.getConfig();
    return config['/healthcare/agents/information/agent-id'] || '';
  }

  async getInformationAliasId(): Promise<string> {
    const config = await this.getConfig();
    return config['/healthcare/agents/information/alias-id'] || '';
  }

  async getKnowledgeBaseId(): Promise<string> {
    const config = await this.getConfig();
    return config['/healthcare/knowledge-base/id'] || '';
  }

  async getGuardrailId(): Promise<string> {
    const config = await this.getConfig();
    return config['/healthcare/guardrail/id'] || '';
  }

  async getKnowledgeBaseBucket(): Promise<string> {
    const config = await this.getConfig();
    return config['/healthcare/storage/knowledge-base-bucket'] || '';
  }

  async getProcessedBucket(): Promise<string> {
    const config = await this.getConfig();
    return config['/healthcare/storage/processed-bucket'] || '';
  }

  async getDatabaseClusterArn(): Promise<string> {
    const config = await this.getConfig();
    return config['/healthcare/database/cluster-arn'] || '';
  }

  async getDatabaseSecretArn(): Promise<string> {
    const config = await this.getConfig();
    return config['/healthcare/database/secret-arn'] || '';
  }

  async getDatabaseName(): Promise<string> {
    const config = await this.getConfig();
    return config['/healthcare/database/name'] || 'healthcare';
  }
}
