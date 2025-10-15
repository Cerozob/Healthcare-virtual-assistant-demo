"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.HealthcareSSMConfig = void 0;
exports.getSSMParameter = getSSMParameter;
exports.getSSMParameters = getSSMParameters;
const aws_sdk_1 = require("aws-sdk");
const ssm = new aws_sdk_1.SSM();
// Cache for SSM parameters to avoid repeated API calls
const parameterCache = new Map();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes
/**
 * Get parameter from SSM Parameter Store with caching
 */
async function getSSMParameter(parameterName) {
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
    }
    catch (error) {
        console.error(`Error retrieving SSM parameter ${parameterName}:`, error);
        throw error;
    }
}
/**
 * Get multiple SSM parameters at once
 */
async function getSSMParameters(parameterNames) {
    const results = {};
    // Check cache for all parameters
    const uncachedParams = [];
    for (const paramName of parameterNames) {
        const cached = parameterCache.get(paramName);
        if (cached && Date.now() < cached.expiry) {
            results[paramName] = cached.value;
        }
        else {
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
        }
        catch (error) {
            console.error('Error retrieving SSM parameters:', error);
            throw error;
        }
    }
    return results;
}
/**
 * Healthcare-specific SSM parameter helpers
 */
class HealthcareSSMConfig {
    constructor() {
        this.configCache = {};
        this.lastFetch = 0;
        this.CACHE_DURATION = 5 * 60 * 1000; // 5 minutes
    }
    static getInstance() {
        if (!HealthcareSSMConfig.instance) {
            HealthcareSSMConfig.instance = new HealthcareSSMConfig();
        }
        return HealthcareSSMConfig.instance;
    }
    async getConfig() {
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
        }
        catch (error) {
            console.error('Error fetching healthcare SSM config:', error);
            // Return cached config if available, otherwise throw
            if (Object.keys(this.configCache).length > 0) {
                console.warn('Using cached SSM config due to fetch error');
                return this.configCache;
            }
            throw error;
        }
    }
    async getOrchestratorAgentId() {
        const config = await this.getConfig();
        return config['/healthcare/agents/orchestrator/agent-id'] || '';
    }
    async getOrchestratorAliasId() {
        const config = await this.getConfig();
        return config['/healthcare/agents/orchestrator/alias-id'] || '';
    }
    async getSchedulingAgentId() {
        const config = await this.getConfig();
        return config['/healthcare/agents/scheduling/agent-id'] || '';
    }
    async getSchedulingAliasId() {
        const config = await this.getConfig();
        return config['/healthcare/agents/scheduling/alias-id'] || '';
    }
    async getInformationAgentId() {
        const config = await this.getConfig();
        return config['/healthcare/agents/information/agent-id'] || '';
    }
    async getInformationAliasId() {
        const config = await this.getConfig();
        return config['/healthcare/agents/information/alias-id'] || '';
    }
    async getKnowledgeBaseId() {
        const config = await this.getConfig();
        return config['/healthcare/knowledge-base/id'] || '';
    }
    async getGuardrailId() {
        const config = await this.getConfig();
        return config['/healthcare/guardrail/id'] || '';
    }
    async getKnowledgeBaseBucket() {
        const config = await this.getConfig();
        return config['/healthcare/storage/knowledge-base-bucket'] || '';
    }
    async getProcessedBucket() {
        const config = await this.getConfig();
        return config['/healthcare/storage/processed-bucket'] || '';
    }
    async getDatabaseClusterArn() {
        const config = await this.getConfig();
        return config['/healthcare/database/cluster-arn'] || '';
    }
    async getDatabaseSecretArn() {
        const config = await this.getConfig();
        return config['/healthcare/database/secret-arn'] || '';
    }
    async getDatabaseName() {
        const config = await this.getConfig();
        return config['/healthcare/database/name'] || 'healthcare';
    }
}
exports.HealthcareSSMConfig = HealthcareSSMConfig;
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoic3NtLXV0aWxzLmpzIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXMiOlsic3NtLXV0aWxzLnRzIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiI7OztBQVdBLDBDQTZCQztBQUtELDRDQWdEQztBQTdGRCxxQ0FBOEI7QUFFOUIsTUFBTSxHQUFHLEdBQUcsSUFBSSxhQUFHLEVBQUUsQ0FBQztBQUV0Qix1REFBdUQ7QUFDdkQsTUFBTSxjQUFjLEdBQUcsSUFBSSxHQUFHLEVBQTZDLENBQUM7QUFDNUUsTUFBTSxTQUFTLEdBQUcsQ0FBQyxHQUFHLEVBQUUsR0FBRyxJQUFJLENBQUMsQ0FBQyxZQUFZO0FBRTdDOztHQUVHO0FBQ0ksS0FBSyxVQUFVLGVBQWUsQ0FBQyxhQUFxQjtJQUN6RCxvQkFBb0I7SUFDcEIsTUFBTSxNQUFNLEdBQUcsY0FBYyxDQUFDLEdBQUcsQ0FBQyxhQUFhLENBQUMsQ0FBQztJQUNqRCxJQUFJLE1BQU0sSUFBSSxJQUFJLENBQUMsR0FBRyxFQUFFLEdBQUcsTUFBTSxDQUFDLE1BQU0sRUFBRSxDQUFDO1FBQ3pDLE9BQU8sTUFBTSxDQUFDLEtBQUssQ0FBQztJQUN0QixDQUFDO0lBRUQsSUFBSSxDQUFDO1FBQ0gsTUFBTSxRQUFRLEdBQUcsTUFBTSxHQUFHLENBQUMsWUFBWSxDQUFDO1lBQ3RDLElBQUksRUFBRSxhQUFhO1lBQ25CLGNBQWMsRUFBRSxJQUFJO1NBQ3JCLENBQUMsQ0FBQyxPQUFPLEVBQUUsQ0FBQztRQUViLE1BQU0sS0FBSyxHQUFHLFFBQVEsQ0FBQyxTQUFTLEVBQUUsS0FBSyxDQUFDO1FBQ3hDLElBQUksQ0FBQyxLQUFLLEVBQUUsQ0FBQztZQUNYLE1BQU0sSUFBSSxLQUFLLENBQUMsYUFBYSxhQUFhLDRCQUE0QixDQUFDLENBQUM7UUFDMUUsQ0FBQztRQUVELGtCQUFrQjtRQUNsQixjQUFjLENBQUMsR0FBRyxDQUFDLGFBQWEsRUFBRTtZQUNoQyxLQUFLO1lBQ0wsTUFBTSxFQUFFLElBQUksQ0FBQyxHQUFHLEVBQUUsR0FBRyxT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QUFLLENBQUM7UUFDZCxDQUFDO0lBQ0gsQ0FBQztJQUVELEtBQUssQ0FBQyxzQkFBc0I7UUFDMUIsTUFBTSxNQUFNLEdBQUcsTUFBTSxJQUFJLENBQUMsU0FBUyxFQUFFLENBQUM7UUFDdEMsT0FBTyxNQUFNLENBQUMsMENBQTBDLENBQUMsSUFBSSxFQUFFLENBQUM7SUFDbEUsQ0FBQztJQUVELEtBQUssQ0FBQyxzQkFBc0I7UUFDMUIsTUFBTSxNQUFNLEdBQUcsTUFBTSxJQUFJLENBQUMsU0FBUyxFQUFFLENBQUM7UUFDdEMsT0FBTyxNQUFNLENBQUMsMENBQTBDLENBQUMsSUFBSSxFQUFFLENBQUM7SUFDbEUsQ0FBQztJQUVELEtBQUssQ0FBQyxvQkFBb0I7UUFDeEIsTUFBTSxNQUFNLEdBQUcsTUFBTSxJQUFJLENBQUMsU0FBUyxFQUFFLENBQUM7UUFDdEMsT0FBTyxNQUFNLENBQUMsd0NBQXdDLENBQUMsSUFBSSxFQUFFLENBQUM7SUFDaEUsQ0FBQztJQUVELEtBQUssQ0FBQyxvQkFBb0I7UUFDeEIsTUFBTSxNQUFNLEdBQUcsTUFBTSxJQUFJLENBQUMsU0FBUyxFQUFFLENBQUM7UUFDdEMsT0FBTyxNQUFNLENBQUMsd0NBQXdDLENBQUMsSUFBSSxFQUFFLENBQUM7SUFDaEUsQ0FBQztJQUVELEtBQUssQ0FBQyxxQkFBcUI7UUFDekIsTUFBTSxNQUFNLEdBQUcsTUFBTSxJQUFJLENBQUMsU0FBUyxFQUFFLENBQUM7UUFDdEMsT0FBTyxNQUFNLENBQUMseUNBQXlDLENBQUMsSUFBSSxFQUFFLENBQUM7SUFDakUsQ0FBQztJQUVELEtBQUssQ0FBQyxxQkFBcUI7UUFDekIsTUFBTSxNQUFNLEdBQUcsTUFBTSxJQUFJLENBQUMsU0FBUyxFQUFFLENBQUM7UUFDdEMsT0FBTyxNQUFNLENBQUMseUNBQXlDLENBQUMsSUFBSSxFQUFFLENBQUM7SUFDakUsQ0FBQztJQUVELEtBQUssQ0FBQyxrQkFBa0I7UUFDdEIsTUFBTSxNQUFNLEdBQUcsTUFBTSxJQUFJLENBQUMsU0FBUyxFQUFFLENBQUM7UUFDdEMsT0FBTyxNQUFNLENBQUMsK0JBQStCLENBQUMsSUFBSSxFQUFFLENBQUM7SUFDdkQsQ0FBQztJQUVELEtBQUssQ0FBQyxjQUFjO1FBQ2xCLE1BQU0sTUFBTSxHQUFHLE1BQU0sSUFBSSxDQUFDLFNBQVMsRUFBRSxDQUFDO1FBQ3RDLE9BQU8sTUFBTSxDQUFDLDBCQUEwQixDQUFDLElBQUksRUFBRSxDQUFDO0lBQ2xELENBQUM7SUFFRCxLQUFLLENBQUMsc0JBQXNCO1FBQzFCLE1BQU0sTUFBTSxHQUFHLE1BQU0sSUFBSSxDQUFDLFNBQVMsRUFBRSxDQUFDO1FBQ3RDLE9BQU8sTUFBTSxDQUFDLDJDQUEyQyxDQUFDLElBQUksRUFBRSxDQUFDO0lBQ25FLENBQUM7SUFFRCxLQUFLLENBQUMsa0JBQWtCO1FBQ3RCLE1BQU0sTUFBTSxHQUFHLE1BQU0sSUFBSSxDQUFDLFNBQVMsRUFBRSxDQUFDO1FBQ3RDLE9BQU8sTUFBTSxDQUFDLHNDQUFzQyxDQUFDLElBQUksRUFBRSxDQUFDO0lBQzlELENBQUM7SUFFRCxLQUFLLENBQUMscUJBQXFCO1FBQ3pCLE1BQU0sTUFBTSxHQUFHLE1BQU0sSUFBSSxDQUFDLFNBQVMsRUFBRSxDQUFDO1FBQ3RDLE9BQU8sTUFBTSxDQUFDLGtDQUFrQyxDQUFDLElBQUksRUFBRSxDQUFDO0lBQzFELENBQUM7SUFFRCxLQUFLLENBQUMsb0JBQW9CO1FBQ3hCLE1BQU0sTUFBTSxHQUFHLE1BQU0sSUFBSSxDQUFDLFNBQVMsRUFBRSxDQUFDO1FBQ3RDLE9BQU8sTUFBTSxDQUFDLGlDQUFpQyxDQUFDLElBQUksRUFBRSxDQUFDO0lBQ3pELENBQUM7SUFFRCxLQUFLLENBQUMsZUFBZTtRQUNuQixNQUFNLE1BQU0sR0FBRyxNQUFNLElBQUksQ0FBQyxTQUFTLEVBQUUsQ0FBQztRQUN0QyxPQUFPLE1BQU0sQ0FBQywyQkFBMkIsQ0FBQyxJQUFJLFlBQVksQ0FBQztJQUM3RCxDQUFDO0NBQ0Y7QUFySEQsa0RBcUhDIiwic291cmNlc0NvbnRlbnQiOlsiaW1wb3J0IHsgU1NNIH0gZnJvbSAnYXdzLXNkayc7XG5cbmNvbnN0IHNzbSA9IG5ldyBTU00oKTtcblxuLy8gQ2FjaGUgZm9yIFNTTSBwYXJhbWV0ZXJzIHRvIGF2b2lkIHJlcGVhdGVkIEFQSSBjYWxsc1xuY29uc3QgcGFyYW1ldGVyQ2FjaGUgPSBuZXcgTWFwPHN0cmluZywgeyB2YWx1ZTogc3RyaW5nOyBleHBpcnk6IG51bWJlciB9PigpO1xuY29uc3QgQ0FDSEVfVFRMID0gNSAqIDYwICogMTAwMDsgLy8gNSBtaW51dGVzXG5cbi8qKlxuICogR2V0IHBhcmFtZXRlciBmcm9tIFNTTSBQYXJhbWV0ZXIgU3RvcmUgd2l0aCBjYWNoaW5nXG4gKi9cbmV4cG9ydCBhc3luYyBmdW5jdGlvbiBnZXRTU01QYXJhbWV0ZXIocGFyYW1ldGVyTmFtZTogc3RyaW5nKTogUHJvbWlzZTxzdHJpbmc+IHtcbiAgLy8gQ2hlY2sgY2FjaGUgZmlyc3RcbiAgY29uc3QgY2FjaGVkID0gcGFyYW1ldGVyQ2FjaGUuZ2V0KHBhcmFtZXRlck5hbWUpO1xuICBpZiAoY2FjaGVkICYmIERhdGUubm93KCkgPCBjYWNoZWQuZXhwaXJ5KSB7XG4gICAgcmV0dXJuIGNhY2hlZC52YWx1ZTtcbiAgfVxuXG4gIHRyeSB7XG4gICAgY29uc3QgcmVzcG9uc2UgPSBhd2FpdCBzc20uZ2V0UGFyYW1ldGVyKHtcbiAgICAgIE5hbWU6IHBhcmFtZXRlck5hbWUsXG4gICAgICBXaXRoRGVjcnlwdGlvbjogdHJ1ZVxuICAgIH0pLnByb21pc2UoKTtcblxuICAgIGNvbnN0IHZhbHVlID0gcmVzcG9uc2UuUGFyYW1ldGVyPy5WYWx1ZTtcbiAgICBpZiAoIXZhbHVlKSB7XG4gICAgICB0aHJvdyBuZXcgRXJyb3IoYFBhcmFtZXRlciAke3BhcmFtZXRlck5hbWV9IG5vdCBmb3VuZCBvciBoYXMgbm8gdmFsdWVgKTtcbiAgICB9XG5cbiAgICAvLyBDYWNoZSB0aGUgdmFsdWVcbiAgICBwYXJhbWV0ZXJDYWNoZS5zZXQocGFyYW1ldGVyTmFtZSwge1xuICAgICAgdmFsdWUsXG4gICAgICBleHBpcnk6IERhdGUubm93KCkgKyBDQUNIRV9UVExcbiAgICB9KTtcblxuICAgIHJldHVybiB2YWx1ZTtcbiAgfSBjYXRjaCAoZXJyb3IpIHtcbiAgICBjb25zb2xlLmVycm9yKGBFcnJvciByZXRyaWV2aW5nIFNTTSBwYXJhbWV0ZXIgJHtwYXJhbWV0ZXJOYW1lfTpgLCBlcnJvcik7XG4gICAgdGhyb3cgZXJyb3I7XG4gIH1cbn1cblxuLyoqXG4gKiBHZXQgbXVsdGlwbGUgU1NNIHBhcmFtZXRlcnMgYXQgb25jZVxuICovXG5leHBvcnQgYXN5bmMgZnVuY3Rpb24gZ2V0U1NNUGFyYW1ldGVycyhwYXJhbWV0ZXJOYW1lczogc3RyaW5nW10pOiBQcm9taXNlPFJlY29yZDxzdHJpbmcsIHN0cmluZz4+IHtcbiAgY29uc3QgcmVzdWx0czogUmVjb3JkPHN0cmluZywgc3RyaW5nPiA9IHt9O1xuICBcbiAgLy8gQ2hlY2sgY2FjaGUgZm9yIGFsbCBwYXJhbWV0ZXJzXG4gIGNvbnN0IHVuY2FjaGVkUGFyYW1zOiBzdHJpbmdbXSA9IFtdO1xuICBmb3IgKGNvbnN0IHBhcmFtTmFtZSBvZiBwYXJhbWV0ZXJOYW1lcykge1xuICAgIGNvbnN0IGNhY2hlZCA9IHBhcmFtZXRlckNhY2hlLmdldChwYXJhbU5hbWUpO1xuICAgIGlmIChjYWNoZWQgJiYgRGF0ZS5ub3coKSA8IGNhY2hlZC5leHBpcnkpIHtcbiAgICAgIHJlc3VsdHNbcGFyYW1OYW1lXSA9IGNhY2hlZC52YWx1ZTtcbiAgICB9IGVsc2Uge1xuICAgICAgdW5jYWNoZWRQYXJhbXMucHVzaChwYXJhbU5hbWUpO1xuICAgIH1cbiAgfVxuXG4gIC8vIEZldGNoIHVuY2FjaGVkIHBhcmFtZXRlcnNcbiAgaWYgKHVuY2FjaGVkUGFyYW1zLmxlbmd0aCA+IDApIHtcbiAgICB0cnkge1xuICAgICAgY29uc3QgcmVzcG9uc2UgPSBhd2FpdCBzc20uZ2V0UGFyYW1ldGVycyh7XG4gICAgICAgIE5hbWVzOiB1bmNhY2hlZFBhcmFtcyxcbiAgICAgICAgV2l0aERlY3J5cHRpb246IHRydWVcbiAgICAgIH0pLnByb21pc2UoKTtcblxuICAgICAgLy8gUHJvY2VzcyBzdWNjZXNzZnVsIHBhcmFtZXRlcnNcbiAgICAgIGlmIChyZXNwb25zZS5QYXJhbWV0ZXJzKSB7XG4gICAgICAgIGZvciAoY29uc3QgcGFyYW0gb2YgcmVzcG9uc2UuUGFyYW1ldGVycykge1xuICAgICAgICAgIGlmIChwYXJhbS5OYW1lICYmIHBhcmFtLlZhbHVlKSB7XG4gICAgICAgICAgICByZXN1bHRzW3BhcmFtLk5hbWVdID0gcGFyYW0uVmFsdWU7XG4gICAgICAgICAgICBcbiAgICAgICAgICAgIC8vIENhY2hlIHRoZSB2YWx1ZVxuICAgICAgICAgICAgcGFyYW1ldGVyQ2FjaGUuc2V0KHBhcmFtLk5hbWUsIHtcbiAgICAgICAgICAgICAgdmFsdWU6IHBhcmFtLlZhbHVlLFxuICAgICAgICAgICAgICBleHBpcnk6IERhdGUubm93KCkgKyBDQUNIRV9UVExcbiAgICAgICAgICAgIH0pO1xuICAgICAgICAgIH1cbiAgICAgICAgfVxuICAgICAgfVxuXG4gICAgICAvLyBMb2cgYW55IGludmFsaWQgcGFyYW1ldGVyc1xuICAgICAgaWYgKHJlc3BvbnNlLkludmFsaWRQYXJhbWV0ZXJzICYmIHJlc3BvbnNlLkludmFsaWRQYXJhbWV0ZXJzLmxlbmd0aCA+IDApIHtcbiAgICAgICAgY29uc29sZS53YXJuKCdJbnZhbGlkIFNTTSBwYXJhbWV0ZXJzOicsIHJlc3BvbnNlLkludmFsaWRQYXJhbWV0ZXJzKTtcbiAgICAgIH1cbiAgICB9IGNhdGNoIChlcnJvcikge1xuICAgICAgY29uc29sZS5lcnJvcignRXJyb3IgcmV0cmlldmluZyBTU00gcGFyYW1ldGVyczonLCBlcnJvcik7XG4gICAgICB0aHJvdyBlcnJvcjtcbiAgICB9XG4gIH1cblxuICByZXR1cm4gcmVzdWx0cztcbn1cblxuLyoqXG4gKiBIZWFsdGhjYXJlLXNwZWNpZmljIFNTTSBwYXJhbWV0ZXIgaGVscGVyc1xuICovXG5leHBvcnQgY2xhc3MgSGVhbHRoY2FyZVNTTUNvbmZpZyB7XG4gIHByaXZhdGUgc3RhdGljIGluc3RhbmNlOiBIZWFsdGhjYXJlU1NNQ29uZmlnO1xuICBwcml2YXRlIGNvbmZpZ0NhY2hlOiBSZWNvcmQ8c3RyaW5nLCBzdHJpbmc+ID0ge307XG4gIHByaXZhdGUgbGFzdEZldGNoID0gMDtcbiAgcHJpdmF0ZSByZWFkb25seSBDQUNIRV9EVVJBVElPTiA9IDUgKiA2MCAqIDEwMDA7IC8vIDUgbWludXRlc1xuXG4gIHN0YXRpYyBnZXRJbnN0YW5jZSgpOiBIZWFsdGhjYXJlU1NNQ29uZmlnIHtcbiAgICBpZiAoIUhlYWx0aGNhcmVTU01Db25maWcuaW5zdGFuY2UpIHtcbiAgICAgIEhlYWx0aGNhcmVTU01Db25maWcuaW5zdGFuY2UgPSBuZXcgSGVhbHRoY2FyZVNTTUNvbmZpZygpO1xuICAgIH1cbiAgICByZXR1cm4gSGVhbHRoY2FyZVNTTUNvbmZpZy5pbnN0YW5jZTtcbiAgfVxuXG4gIGFzeW5jIGdldENvbmZpZygpOiBQcm9taXNlPFJlY29yZDxzdHJpbmcsIHN0cmluZz4+IHtcbiAgICBjb25zdCBub3cgPSBEYXRlLm5vdygpO1xuICAgIFxuICAgIC8vIFJldHVybiBjYWNoZWQgY29uZmlnIGlmIHN0aWxsIHZhbGlkXG4gICAgaWYgKHRoaXMuY29uZmlnQ2FjaGUgJiYgKG5vdyAtIHRoaXMubGFzdEZldGNoKSA8IHRoaXMuQ0FDSEVfRFVSQVRJT04pIHtcbiAgICAgIHJldHVybiB0aGlzLmNvbmZpZ0NhY2hlO1xuICAgIH1cblxuICAgIC8vIEZldGNoIGFsbCBoZWFsdGhjYXJlIHBhcmFtZXRlcnNcbiAgICBjb25zdCBwYXJhbWV0ZXJOYW1lcyA9IFtcbiAgICAgICcvaGVhbHRoY2FyZS9hZ2VudHMvb3JjaGVzdHJhdG9yL2FnZW50LWlkJyxcbiAgICAgICcvaGVhbHRoY2FyZS9hZ2VudHMvb3JjaGVzdHJhdG9yL2FsaWFzLWlkJyxcbiAgICAgICcvaGVhbHRoY2FyZS9hZ2VudHMvc2NoZWR1bGluZy9hZ2VudC1pZCcsXG4gICAgICAnL2hlYWx0aGNhcmUvYWdlbnRzL3NjaGVkdWxpbmcvYWxpYXMtaWQnLFxuICAgICAgJy9oZWFsdGhjYXJlL2FnZW50cy9pbmZvcm1hdGlvbi9hZ2VudC1pZCcsXG4gICAgICAnL2hlYWx0aGNhcmUvYWdlbnRzL2luZm9ybWF0aW9uL2FsaWFzLWlkJyxcbiAgICAgICcvaGVhbHRoY2FyZS9rbm93bGVkZ2UtYmFzZS9pZCcsXG4gICAgICAnL2hlYWx0aGNhcmUvZ3VhcmRyYWlsL2lkJyxcbiAgICAgICcvaGVhbHRoY2FyZS9zdG9yYWdlL2tub3dsZWRnZS1iYXNlLWJ1Y2tldCcsXG4gICAgICAnL2hlYWx0aGNhcmUvc3RvcmFnZS9wcm9jZXNzZWQtYnVja2V0JyxcbiAgICAgICcvaGVhbHRoY2FyZS9kYXRhYmFzZS9jbHVzdGVyLWFybicsXG4gICAgICAnL2hlYWx0aGNhcmUvZGF0YWJhc2Uvc2VjcmV0LWFybicsXG4gICAgICAnL2hlYWx0aGNhcmUvZGF0YWJhc2UvbmFtZSdcbiAgICBdO1xuXG4gICAgdHJ5IHtcbiAgICAgIHRoaXMuY29uZmlnQ2FjaGUgPSBhd2FpdCBnZXRTU01QYXJhbWV0ZXJzKHBhcmFtZXRlck5hbWVzKTtcbiAgICAgIHRoaXMubGFzdEZldGNoID0gbm93O1xuICAgICAgcmV0dXJuIHRoaXMuY29uZmlnQ2FjaGU7XG4gICAgfSBjYXRjaCAoZXJyb3IpIHtcbiAgICAgIGNvbnNvbGUuZXJyb3IoJ0Vycm9yIGZldGNoaW5nIGhlYWx0aGNhcmUgU1NNIGNvbmZpZzonLCBlcnJvcik7XG4gICAgICAvLyBSZXR1cm4gY2FjaGVkIGNvbmZpZyBpZiBhdmFpbGFibGUsIG90aGVyd2lzZSB0aHJvd1xuICAgICAgaWYgKE9iamVjdC5rZXlzKHRoaXMuY29uZmlnQ2FjaGUpLmxlbmd0aCA+IDApIHtcbiAgICAgICAgY29uc29sZS53YXJuKCdVc2luZyBjYWNoZWQgU1NNIGNvbmZpZyBkdWUgdG8gZmV0Y2ggZXJyb3InKTtcbiAgICAgICAgcmV0dXJuIHRoaXMuY29uZmlnQ2FjaGU7XG4gICAgICB9XG4gICAgICB0aHJvdyBlcnJvcjtcbiAgICB9XG4gIH1cblxuICBhc3luYyBnZXRPcmNoZXN0cmF0b3JBZ2VudElkKCk6IFByb21pc2U8c3RyaW5nPiB7XG4gICAgY29uc3QgY29uZmlnID0gYXdhaXQgdGhpcy5nZXRDb25maWcoKTtcbiAgICByZXR1cm4gY29uZmlnWycvaGVhbHRoY2FyZS9hZ2VudHMvb3JjaGVzdHJhdG9yL2FnZW50LWlkJ10gfHwgJyc7XG4gIH1cblxuICBhc3luYyBnZXRPcmNoZXN0cmF0b3JBbGlhc0lkKCk6IFByb21pc2U8c3RyaW5nPiB7XG4gICAgY29uc3QgY29uZmlnID0gYXdhaXQgdGhpcy5nZXRDb25maWcoKTtcbiAgICByZXR1cm4gY29uZmlnWycvaGVhbHRoY2FyZS9hZ2VudHMvb3JjaGVzdHJhdG9yL2FsaWFzLWlkJ10gfHwgJyc7XG4gIH1cblxuICBhc3luYyBnZXRTY2hlZHVsaW5nQWdlbnRJZCgpOiBQcm9taXNlPHN0cmluZz4ge1xuICAgIGNvbnN0IGNvbmZpZyA9IGF3YWl0IHRoaXMuZ2V0Q29uZmlnKCk7XG4gICAgcmV0dXJuIGNvbmZpZ1snL2hlYWx0aGNhcmUvYWdlbnRzL3NjaGVkdWxpbmcvYWdlbnQtaWQnXSB8fCAnJztcbiAgfVxuXG4gIGFzeW5jIGdldFNjaGVkdWxpbmdBbGlhc0lkKCk6IFByb21pc2U8c3RyaW5nPiB7XG4gICAgY29uc3QgY29uZmlnID0gYXdhaXQgdGhpcy5nZXRDb25maWcoKTtcbiAgICByZXR1cm4gY29uZmlnWycvaGVhbHRoY2FyZS9hZ2VudHMvc2NoZWR1bGluZy9hbGlhcy1pZCddIHx8ICcnO1xuICB9XG5cbiAgYXN5bmMgZ2V0SW5mb3JtYXRpb25BZ2VudElkKCk6IFByb21pc2U8c3RyaW5nPiB7XG4gICAgY29uc3QgY29uZmlnID0gYXdhaXQgdGhpcy5nZXRDb25maWcoKTtcbiAgICByZXR1cm4gY29uZmlnWycvaGVhbHRoY2FyZS9hZ2VudHMvaW5mb3JtYXRpb24vYWdlbnQtaWQnXSB8fCAnJztcbiAgfVxuXG4gIGFzeW5jIGdldEluZm9ybWF0aW9uQWxpYXNJZCgpOiBQcm9taXNlPHN0cmluZz4ge1xuICAgIGNvbnN0IGNvbmZpZyA9IGF3YWl0IHRoaXMuZ2V0Q29uZmlnKCk7XG4gICAgcmV0dXJuIGNvbmZpZ1snL2hlYWx0aGNhcmUvYWdlbnRzL2luZm9ybWF0aW9uL2FsaWFzLWlkJ10gfHwgJyc7XG4gIH1cblxuICBhc3luYyBnZXRLbm93bGVkZ2VCYXNlSWQoKTogUHJvbWlzZTxzdHJpbmc+IHtcbiAgICBjb25zdCBjb25maWcgPSBhd2FpdCB0aGlzLmdldENvbmZpZygpO1xuICAgIHJldHVybiBjb25maWdbJy9oZWFsdGhjYXJlL2tub3dsZWRnZS1iYXNlL2lkJ10gfHwgJyc7XG4gIH1cblxuICBhc3luYyBnZXRHdWFyZHJhaWxJZCgpOiBQcm9taXNlPHN0cmluZz4ge1xuICAgIGNvbnN0IGNvbmZpZyA9IGF3YWl0IHRoaXMuZ2V0Q29uZmlnKCk7XG4gICAgcmV0dXJuIGNvbmZpZ1snL2hlYWx0aGNhcmUvZ3VhcmRyYWlsL2lkJ10gfHwgJyc7XG4gIH1cblxuICBhc3luYyBnZXRLbm93bGVkZ2VCYXNlQnVja2V0KCk6IFByb21pc2U8c3RyaW5nPiB7XG4gICAgY29uc3QgY29uZmlnID0gYXdhaXQgdGhpcy5nZXRDb25maWcoKTtcbiAgICByZXR1cm4gY29uZmlnWycvaGVhbHRoY2FyZS9zdG9yYWdlL2tub3dsZWRnZS1iYXNlLWJ1Y2tldCddIHx8ICcnO1xuICB9XG5cbiAgYXN5bmMgZ2V0UHJvY2Vzc2VkQnVja2V0KCk6IFByb21pc2U8c3RyaW5nPiB7XG4gICAgY29uc3QgY29uZmlnID0gYXdhaXQgdGhpcy5nZXRDb25maWcoKTtcbiAgICByZXR1cm4gY29uZmlnWycvaGVhbHRoY2FyZS9zdG9yYWdlL3Byb2Nlc3NlZC1idWNrZXQnXSB8fCAnJztcbiAgfVxuXG4gIGFzeW5jIGdldERhdGFiYXNlQ2x1c3RlckFybigpOiBQcm9taXNlPHN0cmluZz4ge1xuICAgIGNvbnN0IGNvbmZpZyA9IGF3YWl0IHRoaXMuZ2V0Q29uZmlnKCk7XG4gICAgcmV0dXJuIGNvbmZpZ1snL2hlYWx0aGNhcmUvZGF0YWJhc2UvY2x1c3Rlci1hcm4nXSB8fCAnJztcbiAgfVxuXG4gIGFzeW5jIGdldERhdGFiYXNlU2VjcmV0QXJuKCk6IFByb21pc2U8c3RyaW5nPiB7XG4gICAgY29uc3QgY29uZmlnID0gYXdhaXQgdGhpcy5nZXRDb25maWcoKTtcbiAgICByZXR1cm4gY29uZmlnWycvaGVhbHRoY2FyZS9kYXRhYmFzZS9zZWNyZXQtYXJuJ10gfHwgJyc7XG4gIH1cblxuICBhc3luYyBnZXREYXRhYmFzZU5hbWUoKTogUHJvbWlzZTxzdHJpbmc+IHtcbiAgICBjb25zdCBjb25maWcgPSBhd2FpdCB0aGlzLmdldENvbmZpZygpO1xuICAgIHJldHVybiBjb25maWdbJy9oZWFsdGhjYXJlL2RhdGFiYXNlL25hbWUnXSB8fCAnaGVhbHRoY2FyZSc7XG4gIH1cbn1cbiJdfQ==