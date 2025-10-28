#!/usr/bin/env python3
"""
Detailed error testing for the healthcare agent.
"""

import requests
import json
import traceback

def test_invocations_detailed():
    """Test invocations endpoint with detailed error reporting."""
    try:
        print("Testing invocations endpoint with detailed error reporting...")
        
        # Test request format as specified in documentation
        test_payload = {
            "prompt": "Hello, this is a test message for AgentCore compliance"
        }
        
        response = requests.post(
            "http://localhost:8080/invocations",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            print(f"❌ Invocations endpoint returned status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error Response: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Raw Response: {response.text}")
            return False
        
        # Check if response is valid JSON
        try:
            data = response.json()
            print(f"✅ Success! Response keys: {list(data.keys())}")
            print(f"Message preview: {data.get('message', 'No message field')[:200]}...")
            return True
        except json.JSONDecodeError as e:
            print(f"❌ Response is not valid JSON: {e}")
            print(f"Raw response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_invocations_detailed()
