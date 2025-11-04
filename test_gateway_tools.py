#!/usr/bin/env python3
"""
Quick test script to list all tools in the AgentCore Gateway.
This script connects to the AgentCore Gateway and displays all available tools.
"""

import os
import sys
import asyncio
import json
from typing import List, Dict, Any
import argparse
from dotenv import load_dotenv

# Add the agents directory to the path so we can import shared modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))

from agents.shared.mcp_client import create_agentcore_mcp_client
from agents.shared.utils import get_logger

logger = get_logger(__name__)


def load_environment():
    """Load environment variables from .env file."""
    env_path = os.path.join('agents', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        logger.info(f"✅ Loaded environment from {env_path}")
    else:
        logger.warning(f"⚠️ No .env file found at {env_path}")
        logger.info("Using environment variables from system")


def get_config():
    """Get configuration from environment variables."""
    config = {
        'gateway_url': os.getenv('MCP_GATEWAY_URL'),
        'aws_region': os.getenv('AWS_REGION', 'us-east-1'),
        'gateway_id': os.getenv('GATEWAY_ID')
    }
    
    logger.info("🔧 Configuration:")
    logger.info(f"   Gateway URL: {config['gateway_url']}")
    logger.info(f"   AWS Region: {config['aws_region']}")
    logger.info(f"   Gateway ID: {config['gateway_id']}")
    
    if not config['gateway_url']:
        raise ValueError("MCP_GATEWAY_URL environment variable is required")
    
    return config


def format_tool_info(tool) -> Dict[str, Any]:
    """Format tool information for display."""
    info = {
        'name': getattr(tool, 'tool_name', 'Unknown'),
        'description': getattr(tool, 'description', 'No description available')
    }
    
    # Try to get input schema information
    if hasattr(tool, 'input_schema'):
        schema = getattr(tool, 'input_schema', {})
        if isinstance(schema, dict):
            # Extract key information from schema
            properties = schema.get('properties', {})
            required = schema.get('required', [])
            
            info['parameters'] = {
                'total_properties': len(properties),
                'required_properties': len(required),
                'properties': list(properties.keys())[:10],  # Show first 10 properties
                'required': required
            }
            
            # Get action enum if available
            if 'action' in properties and 'enum' in properties['action']:
                info['actions'] = properties['action']['enum']
    
    return info


def test_semantic_search(client, query: str = "healthcare management tools"):
    """Test semantic search functionality."""
    logger.info(f"🔍 Testing semantic search with query: '{query}'")
    
    try:
        tools = client.get_semantic_tools(query, "test")
        logger.info(f"✅ Semantic search returned {len(tools)} tools")
        return tools
    except Exception as e:
        logger.error(f"❌ Semantic search failed: {e}")
        return []


def list_all_gateway_tools():
    """List all tools available in the AgentCore Gateway."""
    logger.info("🚀 Starting AgentCore Gateway Tools Test")
    
    try:
        # Load configuration
        load_environment()
        config = get_config()
        
        # Create MCP client
        logger.info("🔗 Creating AgentCore MCP client...")
        client = create_agentcore_mcp_client(
            gateway_url=config['gateway_url'],
            aws_region=config['aws_region']
        )
        
        # Get MCP client and list tools
        logger.info("📋 Listing all available tools...")
        mcp_client = client.get_mcp_client()
        
        with mcp_client:
            tools = client.list_all_tools(mcp_client)
            
            if not tools:
                logger.warning("⚠️ No tools found in the gateway")
                return
            
            logger.info(f"✅ Found {len(tools)} tools in AgentCore Gateway")
            
            # Format and display tools
            print("\n" + "="*80)
            print(f"AGENTCORE GATEWAY TOOLS ({len(tools)} total)")
            print("="*80)
            
            for i, tool in enumerate(tools, 1):
                tool_info = format_tool_info(tool)
                
                print(f"\n{i}. {tool_info['name']}")
                print(f"   Description: {tool_info['description']}")
                
                if 'actions' in tool_info:
                    print(f"   Available Actions: {', '.join(tool_info['actions'])}")
                
                if 'parameters' in tool_info:
                    params = tool_info['parameters']
                    print(f"   Parameters: {params['total_properties']} total, {params['required_properties']} required")
                    if params['required']:
                        print(f"   Required: {', '.join(params['required'])}")
                    if params['properties']:
                        print(f"   Properties: {', '.join(params['properties'])}")
                        if len(params['properties']) == 10:
                            print("   (showing first 10 properties)")
            
            print("\n" + "="*80)
            
            # Test semantic search if requested
            if len(sys.argv) > 1 and '--test-semantic-search' in sys.argv:
                print("\n🔍 TESTING SEMANTIC SEARCH")
                print("="*80)
                
                test_queries = [
                    "patient management and lookup",
                    "appointment scheduling",
                    "medical records and files",
                    "doctor and medic information"
                ]
                
                for query in test_queries:
                    print(f"\nQuery: '{query}'")
                    semantic_tools = test_semantic_search(client, query)
                    if semantic_tools:
                        tool_names = [getattr(t, 'tool_name', 'Unknown') for t in semantic_tools]
                        print(f"Results: {', '.join(tool_names)}")
                    else:
                        print("Results: No tools found")
            
            return tools
            
    except Exception as e:
        logger.error(f"❌ Failed to list gateway tools: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return None


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Test AgentCore Gateway tools')
    parser.add_argument('--test-semantic-search', action='store_true',
                       help='Also test semantic search functionality')
    parser.add_argument('--json', action='store_true',
                       help='Output results in JSON format')
    
    args = parser.parse_args()
    
    tools = list_all_gateway_tools()
    
    if args.json and tools:
        # Output JSON format
        tools_data = []
        for tool in tools:
            tools_data.append(format_tool_info(tool))
        
        print(json.dumps({
            'total_tools': len(tools),
            'tools': tools_data
        }, indent=2))


if __name__ == '__main__':
    main()
