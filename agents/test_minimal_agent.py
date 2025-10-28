#!/usr/bin/env python3
"""
Minimal agent test to isolate the state assignment issue.
"""

import os
import sys
import traceback

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_minimal_agent():
    """Test creating a minimal agent step by step."""
    try:
        print("Step 1: Import Agent...")
        from strands import Agent
        print("✅ Agent imported successfully")
        
        print("Step 2: Create basic agent...")
        agent = Agent(
            system_prompt="You are a test agent.",
            callback_handler=None
        )
        print("✅ Basic agent created successfully")
        
        print("Step 3: Test state operations...")
        agent.state.set("test_key", "test_value")
        print(f"✅ State set successfully: {agent.state.get('test_key')}")
        
        print("Step 4: Test agent call...")
        result = agent("Hello")
        print(f"✅ Agent call successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed at step: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_minimal_agent()
