#!/usr/bin/env python3
"""
Simple test script to verify MCP Gateway integration.
Run this to test the MCP Gateway connection before deploying.
"""

import os
import sys
import logging
from main import _create_agent_with_mcp_gateway, configure_logging

def test_mcp_gateway():
    """Test MCP Gateway connection and tool discovery."""
    
    # Configure logging
    configure_logging()
    logger = logging.getLogger(__name__)
    
    # Check environment variables
    use_mcp_gateway = os.getenv("USE_MCP_GATEWAY", "false").lower() == "true"
    mcp_gateway_url = os.getenv("MCP_GATEWAY_URL")
    
    logger.info("🧪 MCP Gateway Test Starting")
    logger.info(f"   • USE_MCP_GATEWAY: {use_mcp_gateway}")
    logger.info(f"   • MCP_GATEWAY_URL: {mcp_gateway_url}")
    
    if not use_mcp_gateway:
        logger.warning("⚠️ MCP Gateway is disabled. Set USE_MCP_GATEWAY=true to test.")
        return False
    
    if not mcp_gateway_url:
        logger.error("❌ MCP_GATEWAY_URL is not set. Please configure the gateway URL.")
        return False
    
    try:
        # Test agent creation with MCP Gateway
        logger.info("🤖 Testing agent creation with MCP Gateway...")
        agent = _create_agent_with_mcp_gateway("test_session")
        
        logger.info("✅ Agent created successfully!")
        logger.info(f"   • Agent type: {type(agent).__name__}")
        
        # Test a simple query
        logger.info("💬 Testing simple query...")
        response = agent("Hello, can you help me?")
        
        logger.info("✅ Query successful!")
        logger.info(f"   • Response length: {len(response.message)} characters")
        logger.info(f"   • Response preview: {response.message[:100]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ MCP Gateway test failed: {str(e)}")
        logger.error(f"   • Error type: {type(e).__name__}")
        
        # Log additional debug info
        import traceback
        logger.debug(f"Full traceback:\n{traceback.format_exc()}")
        
        return False

def test_local_tools():
    """Test local tools as fallback."""
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🔧 Testing local tools fallback...")
        
        # Temporarily disable MCP Gateway
        original_value = os.environ.get("USE_MCP_GATEWAY")
        os.environ["USE_MCP_GATEWAY"] = "false"
        
        from main import get_or_create_agent
        agent = get_or_create_agent("test_session_local")
        
        logger.info("✅ Local agent created successfully!")
        
        # Test a simple query
        response = agent("Hello, can you help me?")
        logger.info("✅ Local query successful!")
        logger.info(f"   • Response preview: {response.message[:100]}...")
        
        # Restore original value
        if original_value is not None:
            os.environ["USE_MCP_GATEWAY"] = original_value
        else:
            os.environ.pop("USE_MCP_GATEWAY", None)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Local tools test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Healthcare Agent MCP Gateway Test")
    print("=" * 50)
    
    # Test MCP Gateway if enabled
    mcp_success = test_mcp_gateway()
    
    # Test local tools as fallback
    local_success = test_local_tools()
    
    print("\n📊 Test Results:")
    print(f"   • MCP Gateway: {'✅ PASS' if mcp_success else '❌ FAIL'}")
    print(f"   • Local Tools: {'✅ PASS' if local_success else '❌ FAIL'}")
    
    if mcp_success or local_success:
        print("\n🎉 At least one configuration is working!")
        sys.exit(0)
    else:
        print("\n💥 All tests failed!")
        sys.exit(1)
