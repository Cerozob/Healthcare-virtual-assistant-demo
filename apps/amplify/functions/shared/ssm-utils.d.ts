/**
 * Get parameter from SSM Parameter Store with caching
 */
export declare function getSSMParameter(parameterName: string): Promise<string>;
/**
 * Get multiple SSM parameters at once
 */
export declare function getSSMParameters(parameterNames: string[]): Promise<Record<string, string>>;
/**
 * Healthcare-specific SSM parameter helpers
 */
export declare class HealthcareSSMConfig {
    private static instance;
    private configCache;
    private lastFetch;
    private readonly CACHE_DURATION;
    static getInstance(): HealthcareSSMConfig;
    getConfig(): Promise<Record<string, string>>;
    getOrchestratorAgentId(): Promise<string>;
    getOrchestratorAliasId(): Promise<string>;
    getSchedulingAgentId(): Promise<string>;
    getSchedulingAliasId(): Promise<string>;
    getInformationAgentId(): Promise<string>;
    getInformationAliasId(): Promise<string>;
    getKnowledgeBaseId(): Promise<string>;
    getGuardrailId(): Promise<string>;
    getKnowledgeBaseBucket(): Promise<string>;
    getProcessedBucket(): Promise<string>;
    getDatabaseClusterArn(): Promise<string>;
    getDatabaseSecretArn(): Promise<string>;
    getDatabaseName(): Promise<string>;
}
