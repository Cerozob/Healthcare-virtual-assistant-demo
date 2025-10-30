# AgentCore IAM-Based Authentication

This document explains the simplified IAM-based authentication approach for Bedrock AgentCore Gateway access.

## Overview

Instead of using complex OAuth flows, we use AWS IAM credentials for authentication with AgentCore Gateway. This is simpler, more secure, and follows AWS best practices.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   AgentCore      │    │   Lambda        │
│   (Amplify)     │◄───┤   Runtime        │◄───┤   Functions     │
│                 │    │                  │    │                 │
│ • IAM Creds     │    │ • IAM Auth       │    │ • Healthcare    │
│ • Via Cognito   │    │ • Gateway Access │    │ • Tools         │
│ • Direct Access │    │ • MCP Protocol   │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Required IAM Permissions

### For AgentCore Runtime Role
The AgentCore Runtime execution role includes:
- `BedrockAgentCoreFullAccess` (managed policy)
- `bedrock-agentcore:InvokeGateway` for gateway access
- `bedrock-agentcore:InvokeAgentRuntime` for runtime invocation
- `bedrock:*` for model access
- Lambda invoke permissions for healthcare tools

### For Frontend Users
Frontend users (through Amplify Auth) need:
- `bedrock-agentcore:InvokeAgentRuntime` 
- `bedrock-agentcore-control:GetAgentRuntime`
- `bedrock-agentcore-control:ListAgentRuntimes`

### For Testing/Development Users
Users testing the system directly need:
- `BedrockAgentCoreFullAccess` (managed policy) OR
- Specific permissions:
  - `bedrock-agentcore:InvokeAgentRuntime`
  - `bedrock-agentcore-control:GetAgentRuntime`
  - `bedrock-agentcore-control:GetGateway`
  - `bedrock-agentcore-control:ListAgentRuntimes`
  - `bedrock-agentcore-control:ListGateways`

## Configuration

### CDK Stack Configuration
```python
# AgentCore Gateway with IAM authorization
self.agentcore_gateway = agentcore.CfnGateway(
    self,
    "Agentcoregateway",
    authorizer_type="AWS_IAM",  # Simple IAM-based auth
    name="agentcoregateway",
    protocol_type="MCP",
    role_arn=agentcore_gateway_role.role_arn
    protocol_configuration=bedrockagentcore.CfnGateway.GatewayProtocolConfigurationProperty(
        mcp=bedrockagentcore.CfnGateway.MCPGatewayConfigurationProperty(
   
          search_type="SEMANTIC"
        ))
)

# AgentCore Runtime with IAM authorization
self.agent_runtime = agentcore_alpha.Runtime(
    self,
    "HealthcareAssistantRuntime",
    runtime_name="healthcare_assistant",
    agent_runtime_artifact=self.agent_runtime_artifact,
    authorizer_configuration=agentcore_alpha.RuntimeAuthorizerConfiguration.using_iam(),
    execution_role=agent_runtime_role,
    # ... other config
)
```

### Frontend Integration
```typescript
// AgentCore client uses Amplify Auth credentials automatically
const client = new BedrockAgentCoreClient({
  region: AWS_REGION,
  credentials  // From fetchAuthSession()
});

// Direct invocation with IAM auth (data plane)
// JavaScript SDK parameters (different from boto3)
const response = await client.send(new InvokeAgentRuntimeCommand({
  agentRuntimeArn: runtimeArn,              // Required: Runtime ARN (JavaScript SDK)
  runtimeSessionId: sessionId,              // Required: Session ID (JavaScript SDK)
  payload: new TextEncoder().encode(JSON.stringify({
    prompt: message,
    timestamp: new Date().toISOString()
  }))                                       // Required: Encoded payload (JavaScript SDK)
}));

// Handle streaming response
const responseText = await response.response.transformToString();
```

### Python/Boto3 Integration
```python
# Boto3 uses different parameter names than JavaScript SDK
response = data_client.invoke_agent_runtime(
    agentRuntimeArn=runtime_arn,     # ARN required (boto3)
    runtimeSessionId=session_id,     # runtimeSessionId (boto3)
    payload=encoded_payload          # payload (boto3)
)
```

## Testing

### Test IAM Access
```bash
# Test AgentCore access with current AWS credentials
python scripts/test_iam_agentcore.py --stack-name AWSomeBuilder2-VirtualAssistantStack

# Get access information
python scripts/test_iam_agentcore.py --stack-name AWSomeBuilder2-VirtualAssistantStack --info-only
```

### Manual Testing with AWS CLI
```bash
# Test gateway access (control plane)
aws bedrock-agentcore-control get-gateway --gateway-identifier <gateway-id>

# Test runtime access (control plane)
aws bedrock-agentcore-control get-agent-runtime --agent-runtime-id <runtime-id>

# Test runtime invocation (data plane)
aws bedrock-agentcore invoke-agent-runtime --agent-runtime-id <runtime-id> --session-id test-session --input-text "Hello"
```

## Benefits of IAM-Based Approach

1. **Simplicity**: No OAuth flows, tokens, or complex authentication logic
2. **Security**: Uses existing AWS IAM security model
3. **Integration**: Works seamlessly with existing Amplify Auth
4. **Maintenance**: No additional authentication infrastructure to maintain
5. **Auditing**: Full AWS CloudTrail integration for access logging
6. **Scalability**: Leverages AWS IAM's proven scalability

## Troubleshooting

### Common Issues

1. **Access Denied Errors**
   - Check IAM permissions for `bedrock-agentcore:InvokeAgentRuntime`
   - Verify the user has access to the specific runtime ARN
   - Ensure Amplify Auth is properly configured

2. **Runtime Not Found**
   - Verify the runtime ID is correct
   - Check if the runtime is in the same region
   - Ensure the runtime is deployed and active

3. **JavaScript SDK Issues**
   - Ensure you're using the correct parameter names for JavaScript SDK
   - Check browser console for detailed error messages
   - Use the debug utility to test your setup

4. **Gateway Connection Issues**
   - Verify gateway is deployed and active
   - Check network connectivity
   - Ensure proper AWS credentials are configured

### JavaScript SDK Debugging

Use the debug utility to test your setup:
```typescript
import { debugAgentCoreSetup, logEnvironmentInfo } from '../utils/agentCoreDebug';

// Log environment info
logEnvironmentInfo();

// Test setup
const debugInfo = await debugAgentCoreSetup();
console.log('Debug info:', debugInfo);
```

### Debug Commands
```bash
# Check current AWS identity
aws sts get-caller-identity

# List available runtimes (control plane)
aws bedrock-agentcore-control list-agent-runtimes

# List available gateways (control plane)
aws bedrock-agentcore-control list-gateways

# Check specific runtime
aws bedrock-agentcore-control get-agent-runtime --agent-runtime-id <runtime-id>

# Check specific gateway
aws bedrock-agentcore-control get-gateway --gateway-identifier <gateway-id>
```

## Migration from OAuth

If migrating from OAuth-based authentication:

1. Remove Cognito OAuth constructs from CDK
2. Update gateway `authorizer_type` to `"AWS_IAM"`
3. Update runtime `authorizer_configuration` to use IAM
4. Remove OAuth token handling from frontend
5. Ensure Amplify Auth provides proper IAM credentials

The frontend AgentCore service will automatically use IAM credentials from Amplify Auth, requiring no code changes.

## Security Considerations

1. **Least Privilege**: Grant only necessary permissions
2. **Resource Scoping**: Scope permissions to specific gateway/runtime ARNs
3. **Credential Rotation**: Use temporary credentials (STS tokens)
4. **Monitoring**: Enable CloudTrail for access auditing
5. **Network Security**: Use VPC endpoints if needed for private access

## Performance

IAM-based authentication provides:
- **Lower Latency**: No additional token exchange
- **Higher Reliability**: No dependency on external OAuth services
- **Better Caching**: AWS SDK handles credential caching automatically
- **Reduced Complexity**: Fewer moving parts and failure points
