#!/usr/bin/env python3
"""
Direct endpoint testing without running server.
"""

import os
import sys
import asyncio
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_ping_endpoint():
    """Test ping endpoint directly."""
    try:
        print("Testing ping endpoint...")
        
        # Import the app
        from main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        response = client.get("/ping")
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if "status" in data and "time_of_last_update" in data:
                print("✅ Ping endpoint format compliant")
                return True
            else:
                print("❌ Ping endpoint missing required fields")
                return False
        else:
            print("❌ Ping endpoint returned non-200 status")
            return False
            
    except Exception as e:
        print(f"❌ Ping endpoint test failed: {str(e)}")
        return False


async def test_invocations_endpoint():
    """Test invocations endpoint directly."""
    try:
        print("\nTesting invocations endpoint...")
        
        # Import the app
        from main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Test with the new format
        test_payload = {
            "prompt": "Hello, this is a test message"
        }
        
        response = client.post("/invocations", json=test_payload)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            
            if "message" in data:
                print("✅ Invocations endpoint format compliant")
                print(f"Message preview: {data['message'][:100]}...")
                return True
            else:
                print("❌ Invocations endpoint missing 'message' field")
                print(f"Full response: {data}")
                return False
        else:
            print("❌ Invocations endpoint returned non-200 status")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Invocations endpoint test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all endpoint tests."""
    print("🔍 Testing Endpoints Directly")
    print("=" * 50)
    
    # Set environment variables for testing
    os.environ["SESSION_BUCKET"] = "test-bucket"
    os.environ["AWS_REGION"] = "us-east-1"
    os.environ["LOG_LEVEL"] = "INFO"
    
    ping_ok = await test_ping_endpoint()
    invocations_ok = await test_invocations_endpoint()
    
    print("\n" + "=" * 50)
    if ping_ok and invocations_ok:
        print("✅ All endpoint tests passed!")
        return 0
    else:
        print("❌ Some endpoint tests failed.")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
