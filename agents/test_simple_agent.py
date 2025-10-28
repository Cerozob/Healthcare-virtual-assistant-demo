#!/usr/bin/env python3
"""
Test simple agent creation without session manager.
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_simple_agent():
    """Test creating a simple agent without session manager."""
    try:
        print("Testing simple agent creation...")
        
        from strands import Agent
        
        # Create a simple agent without session manager
        agent = Agent(
            system_prompt="You are a test agent.",
            callback_handler=None
        )
        
        # Try to set state
        agent.state.set("test_key", "test_value")
        print(f"✅ State set successfully: {agent.state.get('test_key')}")
        
        # Try to call the agent
        result = agent("Hello, this is a test")
        print(f"✅ Agent call successful: {result.message}")
        
        return True
        
    except Exception as e:
        print(f"❌ Simple agent test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_simple_agent()
