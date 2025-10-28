# MCP Gateway Integration Guide

This guide shows how to integrate with AWS Bedrock AgentCore Gateway for MCP tools.

## Prerequisites

- AWS Bedrock AgentCore Gateway deployed
- IAM authentication configured (recommended)
- Gateway URL

## IAM Authentication (Recommended)

For production deployments, use IAM authentication instead of client credentials:

## Required IAM Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowGatewayInvocation",
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:InvokeGateway"
      ],
      "Resource": [
        "arn:aws:bedrock-agentcore:us-east-1:123456789012:gateway/my-gateway-12345"
      ]
    }
  ]
}
```

## Integration Example

```python
from strands import Agent
import logging
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
import os
import requests
import json

# Configuration
CLIENT_ID = os.getenv("MCP_CLIENT_ID")
CLIENT_SECRET = os.getenv("MCP_CLIENT_SECRET")
TOKEN_URL = os.getenv("MCP_TOKEN_URL")
GATEWAY_URL = os.getenv("MCP_GATEWAY_URL")

def fetch_access_token(client_id: str, client_secret: str, token_url: str) -> str:
    """
    Fetch OAuth2 access token for MCP Gateway authentication.
    
    Args:
        client_id: OAuth2 client ID
        client_secret: OAuth2 client secret
        token_url: Token endpoint URL
        
    Returns:
        Access token string
    """
    response = requests.post(
        token_url,
        data=f"grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}",
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    response.raise_for_status()
    return response.json()['access_token']


def create_streamable_http_transport(mcp_url: str, access_token: str):
    """
    Create HTTP transport for MCP client with authentication.
    
    Args:
        mcp_url: MCP Gateway URL
        access_token: OAuth2 access token
        
    Returns:
        Streamable HTTP transport
    """
    return streamablehttp_client(
        mcp_url,
        headers={"Authorization": f"Bearer {access_token}"}
    )


def get_full_tools_list(client: MCPClient) -> list:
    """
    List all tools with pagination support.
    
    Args:
        client: MCP client instance
        
    Returns:
        List of all available tools
    """
    more_tools = True
    tools = []
    pagination_token = None
    
    while more_tools:
        tmp_tools = client.list_tools_sync(pagination_token=pagination_token)
        tools.extend(tmp_tools)
        
        if tmp_tools.pagination_token is None:
            more_tools = False
        else:
            pagination_token = tmp_tools.pagination_token
    
    return tools


def create_agent_with_mcp_tools(mcp_url: str, access_token: str) -> Agent:
    """
    Create Strands Agent with MCP Gateway tools.
    
    Args:
        mcp_url: MCP Gateway URL
        access_token: OAuth2 access token
        
    Returns:
        Configured Agent instance
    """
    # Create MCP client
    mcp_client = MCPClient(
        lambda: create_streamable_http_transport(mcp_url, access_token)
    )
    
    with mcp_client:
        # Get all available tools
        tools = get_full_tools_list(mcp_client)
        logging.info(f"Found {len(tools)} tools: {[tool.tool_name for tool in tools]}")
        
        # Create agent with MCP tools
        agent = Agent(
            name="Healthcare Assistant with MCP Gateway",
            model=BedrockModel(model_id="anthropic.claude-3-5-sonnet-20241022-v2:0"),
            tools=tools,
            instructions="You are a healthcare assistant with access to patient management tools via MCP Gateway."
        )
        
        return agent


# Usage example
if __name__ == "__main__":
    # Fetch access token
    access_token = fetch_access_token(CLIENT_ID, CLIENT_SECRET, TOKEN_URL)
    
    # Create agent with MCP tools
    agent = create_agent_with_mcp_tools(GATEWAY_URL, access_token)
    
    # Use the agent
    response = agent("List recent patients")
    print(response.message)
```

## Environment Variables

### For IAM Authentication (Recommended)

Set these environment variables for your deployment:

```bash
export USE_MCP_GATEWAY="true"
export MCP_GATEWAY_URL="https://agentcoregateway-xxx.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
```

### For OAuth2 Client Credentials (Alternative)

```bash
export USE_MCP_GATEWAY="true"
export MCP_CLIENT_ID="your-client-id"
export MCP_CLIENT_SECRET="your-client-secret"
export MCP_TOKEN_URL="https://your-token-endpoint/oauth2/token"
export MCP_GATEWAY_URL="https://agentcoregateway-xxx.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
```

## Integration with FastAPI

The main.py file is already configured to use MCP Gateway when enabled:

```python
# The agent creation automatically detects MCP Gateway configuration
def get_or_create_agent(session_id: str) -> Agent:
    use_mcp_gateway = os.getenv("USE_MCP_GATEWAY", "false").lower() == "true"
    
    if use_mcp_gateway:
        logger.info("Using MCP Gateway for tools")
        agent = _create_agent_with_mcp_gateway(session_id)
    else:
        logger.info("Using local tools")
        agent = Agent(
            system_prompt=HEALTHCARE_SYSTEM_PROMPT,
            tools=["tools/patient_lookup.py"],
            callback_handler=None
        )
    
    return agent
```

## Quick Setup

1. **Set environment variables:**
   ```bash
   export USE_MCP_GATEWAY="true"
   export MCP_GATEWAY_URL="https://agentcoregateway-xxx.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
   ```

2. **Ensure IAM permissions are configured for the agent's execution role:**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "bedrock-agentcore:InvokeGateway"
         ],
         "Resource": [
           "arn:aws:bedrock-agentcore:us-east-1:123456789012:gateway/your-gateway-id"
         ]
       }
     ]
   }
   ```

3. **Test the configuration:**
   ```bash
   cd agents
   python test_mcp_gateway.py
   ```

4. **Deploy and restart the agent service**

The agent will automatically connect to the MCP Gateway and load all available tools.

## Troubleshooting

### Test Script Output
The test script will show detailed logs:
```
🧪 Healthcare Agent MCP Gateway Test
==================================================
🔧 Agent Configuration:
   • MCP Gateway: true
   • Gateway URL: https://your-gateway-url/mcp
🤖 Testing agent creation with MCP Gateway...
✅ Agent created successfully!
💬 Testing simple query...
✅ Query successful!
```

### Common Issues

1. **Gateway URL not accessible:**
   - Verify the gateway URL is correct
   - Check network connectivity from agent environment
   - Ensure gateway is deployed and running

2. **IAM permission denied:**
   - Verify the execution role has `bedrock-agentcore:InvokeGateway` permission
   - Check the resource ARN matches your gateway
   - Ensure AWS credentials are available in the environment

3. **Tool discovery fails:**
   - Check gateway logs in CloudWatch
   - Verify MCP servers are properly configured in the gateway
   - Test gateway connectivity directly

### Fallback Behavior
If MCP Gateway fails, the agent automatically falls back to local tools:
```
❌ MCP Gateway test failed: Connection timeout
🔧 Testing local tools fallback...
✅ Local agent created successfully!
```

## Security Best Practices

1. **Never commit credentials**: Use AWS Secrets Manager or environment variables
2. **Rotate tokens**: Implement token refresh logic for long-running services
3. **Least privilege**: Grant only necessary IAM permissions
4. **Audit logging**: Enable CloudTrail for gateway invocations
5. **Network security**: Use VPC endpoints when possible

## Troubleshooting

### Authentication Errors
- Verify CLIENT_ID and CLIENT_SECRET are correct
- Check token endpoint URL is accessible
- Ensure IAM permissions are properly configured

### Tool Discovery Issues
- Verify gateway URL is correct
- Check network connectivity
- Review gateway logs in CloudWatch

### Performance Optimization
- Cache access tokens (they're typically valid for 1 hour)
- Implement connection pooling for HTTP requests
- Use pagination efficiently for large tool lists
