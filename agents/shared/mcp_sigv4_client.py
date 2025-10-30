"""
MCP Client with AWS SigV4 Authentication
Custom HTTP client for MCP that signs requests with AWS SigV4
"""

import logging
import json
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import requests
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth

from shared.utils import get_logger

logger = get_logger(__name__)


class SigV4MCPClient:
    """MCP Client with AWS SigV4 authentication for AgentCore Gateway."""
    
    def __init__(self, gateway_url: str, aws_region: str):
        """Initialize the SigV4 MCP client.
        
        Args:
            gateway_url: The AgentCore Gateway URL
            aws_region: AWS region for SigV4 signing
        """
        self.gateway_url = gateway_url.rstrip('/')
        self.aws_region = aws_region
        
        # Parse the gateway URL to get the host
        parsed_url = urlparse(gateway_url)
        self.host = parsed_url.netloc
        
        # Initialize the SigV4 auth using boto utils
        self.auth = BotoAWSRequestsAuth(
            aws_host=self.host,
            aws_region=aws_region,
            aws_service='bedrock-agentcore'  # AgentCore Gateway uses bedrock-agentcore service
        )
        
        logger.info(f"🔐 SigV4 MCP Client initialized for {self.host} in {aws_region}")
    
    def list_tools(self) -> list:
        """List available tools from the MCP Gateway using JSON-RPC 2.0."""
        try:
            url = f"{self.gateway_url}/mcp"
            logger.info(f"📋 Listing tools from: {url}")
            
            # JSON-RPC 2.0 request payload
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }
            
            response = requests.post(
                url, 
                json=payload, 
                auth=self.auth,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            
            response_data = response.json()
            
            # Check for JSON-RPC error
            if 'error' in response_data:
                error = response_data['error']
                raise Exception(f"JSON-RPC error {error.get('code')}: {error.get('message')}")
            
            # Extract tools from JSON-RPC result
            result = response_data.get('result', {})
            tools = result.get('tools', [])
            
            logger.info(f"✅ Retrieved {len(tools)} tools from MCP Gateway")
            return tools
            
        except Exception as e:
            logger.error(f"❌ Failed to list tools: {e}")
            raise
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool on the MCP Gateway using JSON-RPC 2.0.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            
        Returns:
            Tool execution result
        """
        try:
            url = f"{self.gateway_url}/mcp"
            logger.info(f"🔧 Calling tool {tool_name}")
            logger.debug(f"Arguments: {arguments}")
            
            # JSON-RPC 2.0 request payload for tools/call
            payload = {
                "jsonrpc": "2.0",
                "id": 2,  # Use different ID for tool calls
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            response = requests.post(
                url, 
                json=payload, 
                auth=self.auth,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            
            response_data = response.json()
            
            # Check for JSON-RPC error
            if 'error' in response_data:
                error = response_data['error']
                raise Exception(f"JSON-RPC error {error.get('code')}: {error.get('message')}")
            
            # Extract result from JSON-RPC response
            result = response_data.get('result', {})
            logger.info(f"✅ Tool {tool_name} executed successfully")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to call tool {tool_name}: {e}")
            raise
    



class SigV4MCPTool:
    """Wrapper for MCP tools that handles SigV4 authentication."""
    
    def __init__(self, tool_name: str, tool_schema: Dict[str, Any], client: SigV4MCPClient):
        """Initialize the SigV4 MCP tool.
        
        Args:
            tool_name: Name of the tool
            tool_schema: Tool schema from the gateway
            client: SigV4 MCP client instance
        """
        self.name = tool_name
        self.schema = tool_schema
        self.client = client
        self.description = tool_schema.get('description', f'MCP tool: {tool_name}')
        
        logger.info(f"🔧 SigV4 MCP Tool initialized: {tool_name}")
    
    def __call__(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with the given arguments."""
        return self.client.call_tool(self.name, kwargs)
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool schema."""
        return self.schema


def create_sigv4_mcp_tools(gateway_url: str, aws_region: str) -> list:
    """Create a list of SigV4-authenticated MCP tools.
    
    Args:
        gateway_url: The AgentCore Gateway URL
        aws_region: AWS region for SigV4 signing
        
    Returns:
        List of SigV4MCPTool instances
    """
    try:
        logger.info(f"🔐 Creating SigV4 MCP tools for {gateway_url}")
        
        # Create the SigV4 client
        client = SigV4MCPClient(gateway_url, aws_region)
        
        # List available tools
        tools_list = client.list_tools()
        
        # Create tool instances
        tools = []
        for tool_info in tools_list:
            tool_name = tool_info.get('name')
            if not tool_name:
                logger.warning(f"⚠️ Tool missing name: {tool_info}")
                continue
            
            try:
                # Use the schema from the tools/list response
                tool_schema = tool_info
                
                # Create the tool wrapper
                tool = SigV4MCPTool(tool_name, tool_schema, client)
                tools.append(tool)
                
                logger.info(f"✅ Created SigV4 tool: {tool_name}")
                
            except Exception as e:
                logger.error(f"❌ Failed to create tool {tool_name}: {e}")
                continue
        
        logger.info(f"🎉 Created {len(tools)} SigV4 MCP tools")
        return tools
        
    except Exception as e:
        logger.error(f"❌ Failed to create SigV4 MCP tools: {e}")
        logger.error("   This will cause the healthcare agent to fail startup")
        raise


def test_sigv4_connection(gateway_url: str, aws_region: str) -> bool:
    """Test the SigV4 connection to the MCP Gateway.
    
    Args:
        gateway_url: The AgentCore Gateway URL
        aws_region: AWS region for SigV4 signing
        
    Returns:
        True if connection successful, False otherwise
    """
    try:
        logger.info(f"🧪 Testing SigV4 connection to {gateway_url}")
        
        client = SigV4MCPClient(gateway_url, aws_region)
        tools = client.list_tools()
        
        logger.info(f"✅ SigV4 connection test successful - found {len(tools)} tools")
        for tool in tools:
            logger.info(f"  - {tool.get('name')}: {tool.get('description', 'No description')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ SigV4 connection test failed: {e}")
        return False
